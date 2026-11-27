#!/usr/bin/env python3
"""
Nissan SH7055 / SH7058 Reverse-Engineering Workbench (`tools/nissan_sh705x_workbench.py`)

Unified, read-only CLI combining:
  1. Universal ROM loader (.bin, .zip, .s19, .hex, Consult .dat) + MCU/FID fingerprinting
  2. Cross-generation SH-2 lookup-helper discovery & call-site extraction
     (pre-cal mov.w <0x10000, SH7055 mid-ROM ~0x15xxx, SH7058 post-cal >=0x20000)
  3. EL19A audit against Release 1 XML, discovered_tables_catalog.csv, and RELEASE1_SCOPE_MATRIX_R1.csv
     (flagging geometry/extent mismatches, shared-storage links, and reciprocal inverse pairs)
  4. Variant-isolation & raw scalar/byte diffing across any two ROMs (.bin/.zip/.s19/.hex/.dat)
  5. Structural function-signature + A2L (CHARACTERISTIC / AXIS_PTS / COMPU_METHOD / MEASUREMENT) lead matching
     against `64810223F121200000.hex` (SH705822N) + `64811000p2_m.a2l` and `9APCTDEM06.s19` + `RFCC_2XHK19BDF1.a2l`.

Evidence boundary:
  Cross-ROM and A2L outputs are comparative *leads* only, never target-side proof on EL19A.
"""
import argparse
import bisect
import csv
import hashlib
import json
import re
import struct
import sys
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from sh705x_rom_loader import (  # noqa: E402
    _check_nonflat_container,
    _load_dat_percent6,
    _rol16,
    decrypt_consult_dat_word,
    load_any_rom,
    load_dat_bytes,
    load_hex_bytes,
    load_s19_bytes,
    parse_nissan_metadata,
)
sys.modules.setdefault("nissan_sh705x_workbench", sys.modules[__name__])
from sh7058_cross_rom_scanner import build_scan_export, discover_helpers, extract_calls, load_xml_tables  # noqa: E402
from sh705x_discovery_v2 import (  # noqa: E402
    atomic_write_json,
    build_run_manifest,
    compare_call_extractions,
    discover_cal_scalars,
    extract_calls_enhanced,
    extract_implicit_grids,
    to_per_address_catalogue,
)
from romraider_ref_index import (  # noqa: E402
    build_reference_index,
    match_target_against_index,
)
from romraider_xml_export import (  # noqa: E402
    resolve_candidate_evidence,
    write_preview_bundle,
)

EL19A_PINNED_SHA256 = "bfe037e8e6c389e2a90214047058eb6dc3bcaaaac5b5931bf98a3f5d9f64fd6a"


# ---------------------------------------------------------------------------
# Nissan Checksums, Fingerprinting, & A2L / Repository Metadata Loaders
# ---------------------------------------------------------------------------


def verify_checksums(rom: bytes, meta: Optional[dict] = None) -> dict:
    """
    Verify Nissan SH705x checksums:
      - ck_std: full-ROM 32-bit (sumt, xort) skipping self (O(N) auto-detection in 0..0x40000)
      - ck_alt2: LOADER80 512 KiB split 32-bit (sumt=FID-8, xort=FID-4) over [FID+0x94..FID+0x98]
      - sum16: LOADER80 16-bit block checksums cal16@0x08200 & main16@(0x10000 or 0x20000)
    """
    if meta is None:
        meta = parse_nissan_metadata(rom)
    res: Dict[str, Optional[dict]] = {"ck_std": None, "ck_alt2": None, "cal16": None, "main16": None}
    n_words = len(rom) // 4
    if n_words < 0x1000:
        return res

    words = struct.unpack_from(f">{n_words}I", rom, 0)
    full_sum = sum(words) & 0xFFFFFFFF
    full_xor = 0
    for w in words:
        full_xor ^= w

    # 1. ck_std: full-ROM sumt/xort separated by 1 or 2 dwords inside 0..0x40000
    # Note: full_xor = excl_xor ^ sumt ^ xort = sumt (since xort == excl_xor); full_sum = 2*sumt + xort
    scan_w = min(n_words - 2, 0x10000)
    for i in range(scan_w):
        for step in (2, 1):
            j = i + step
            if j >= n_words:
                continue
            wi, wj = words[i], words[j]
            if wi == full_xor and ((wi * 2 + wj) & 0xFFFFFFFF) == full_sum:
                res["ck_std"] = {"status": "OK", "sumt": i * 4, "xort": j * 4, "sum": wi, "xor": wj}
                break
            if wj == full_xor and ((wj * 2 + wi) & 0xFFFFFFFF) == full_sum:
                res["ck_std"] = {"status": "OK", "sumt": j * 4, "xort": i * 4, "sum": wj, "xor": wi}
                break
        if res["ck_std"] is not None:
            break

    # 2. ck_alt2: FID-8 (sumt) / FID-4 (xort) over [FID+0x94 .. FID+0x98] inclusive
    fa = meta.get("fid_addr")
    if fa is not None and fa >= 0x8000 and fa + 0x9C <= len(rom):
        st, en = struct.unpack_from(">II", rom, fa + 0x94)
        if 0x4000 <= st < en < len(rom) and st % 4 == 0 and (en % 4 in (0, 3)):
            end_inc = en if en % 4 == 0 else (en - 3)
            s_pre, x_pre = struct.unpack_from(">II", rom, fa - 8)
            s_c, x_c = 0, 0
            for off in range(st, end_inc + 1, 4):
                if off in (fa - 8, fa - 4):
                    continue
                w = struct.unpack_from(">I", rom, off)[0]
                s_c = (s_c + w) & 0xFFFFFFFF
                x_c ^= w
            ok = (s_c == s_pre and x_c == x_pre)
            res["ck_alt2"] = {
                "status": "OK" if ok else "BAD",
                "sumt": fa - 8,
                "xort": fa - 4,
                "start": st,
                "end": en,
                "stored_sum": s_pre,
                "calc_sum": s_c,
                "stored_xor": x_pre,
                "calc_xor": x_c,
            }

    # 3. LOADER80 16-bit split checksums: cal16@0x08200 & main16@(0x10000 | 0x20000)
    is_l80 = meta.get("loader") == "LOADER80" or (meta.get("bootblock_ff") and len(rom) in (0x80000, 0x100000))
    if len(rom) >= 0x80000 and len(rom) % 2 == 0:
        split = 0x10000 if len(rom) <= 0x80000 else 0x20000
        if len(rom) > split + 2:
            m_stored = struct.unpack_from(">H", rom, split)[0]
            m_calc = sum(struct.unpack_from(f">{(len(rom) - split - 2) // 2}H", rom, split + 2)) & 0xFFFF
            if is_l80 or m_stored == m_calc:
                res["main16"] = {
                    "status": "OK" if m_stored == m_calc else "BAD",
                    "addr": split,
                    "stored": m_stored,
                    "calc": m_calc,
                }
        c_stored = struct.unpack_from(">H", rom, 0x8200)[0]
        c_calc = sum(struct.unpack_from(f">{(split - 0x8202) // 2}H", rom, 0x8202)) & 0xFFFF
        if (is_l80 and c_stored != 0xFFFF) or c_stored == c_calc:
            res["cal16"] = {
                "status": "OK" if c_stored == c_calc else "BAD",
                "addr": 0x8200,
                "end": split,
                "stored": c_stored,
                "calc": c_calc,
            }

    return res


def checksum_byte_tags(rom: bytes) -> Dict[int, str]:
    """Map byte offsets belonging to verified/located checksums -> human tag for cmd_diff."""
    tags: Dict[int, str] = {}
    cks = verify_checksums(rom)
    if cks["ck_std"]:
        cs = cks["ck_std"]
        for a, lbl in ((cs["sumt"], "ck_std sumt"), (cs["xort"], "ck_std xort")):
            for k in range(4):
                tags[a + k] = lbl
    if cks["ck_alt2"]:
        ca = cks["ck_alt2"]
        for a, lbl in ((ca["sumt"], f"ck_alt2 sumt [{ca['status']}]"), (ca["xort"], f"ck_alt2 xort [{ca['status']}]")):
            for k in range(4):
                tags[a + k] = lbl
    if cks["cal16"]:
        c16 = cks["cal16"]
        for k in range(2):
            tags[c16["addr"] + k] = f"LOADER80 cal16 [{c16['status']}]"
    if cks["main16"]:
        m16 = cks["main16"]
        for k in range(2):
            tags[m16["addr"] + k] = f"LOADER80 main16 [{m16['status']}]"
    return tags


def rom_fingerprint(rom: bytes) -> dict:
    reset_pc = struct.unpack_from(">I", rom, 0)[0] if len(rom) >= 8 else 0
    reset_sp = struct.unpack_from(">I", rom, 4)[0] if len(rom) >= 8 else 0
    cpu_tags = sorted({m.group().decode() for m in re.finditer(rb"SH70[0-9A-Z]{2,6}", rom)})
    fid_tags = []
    for m in re.finditer(rb"[0-9][A-Z0-9]{7}", rom[: min(len(rom), 0x40000)]):
        s = m.group().decode()
        if any(c.isalpha() for c in s) and not s.startswith("SH70") and s not in fid_tags:
            fid_tags.append(s)
    active_end = len(rom)
    while active_end > 0x10000 and rom[active_end - 0x10000 : active_end] == b"\xff" * 0x10000:
        active_end -= 0x10000
    meta = parse_nissan_metadata(rom)
    cks = verify_checksums(rom, meta)
    return {
        "size": len(rom),
        "active_end": active_end,
        "md5": hashlib.md5(rom).hexdigest(),
        "sha256": hashlib.sha256(rom).hexdigest(),
        "reset_pc": reset_pc,
        "reset_sp": reset_sp,
        "cpu_tags": cpu_tags[:6],
        "fid_tags": fid_tags[:8],
        "nissan_meta": meta,
        "checksums": cks,
    }


def parse_a2l_rich(path: Path) -> dict:
    txt = path.read_bytes().decode("cp932", errors="replace")
    compu: Dict[str, dict] = {}
    for blk in txt.split("/begin COMPU_METHOD ")[1:]:
        end = blk.find("/end COMPU_METHOD")
        body = (blk[:end] if end != -1 else blk).lstrip()
        m = re.match(r"(\S+)\s+\"([^\"]*)\"\s+\S+\s+\"([^\"]*)\"\s+\"([^\"]*)\"", body)
        if not m:
            continue
        name, desc, fmt, unit = m.groups()
        cm = re.search(r"COEFFS\s+([-\deE.+]+)\s+([-\deE.+]+)\s+([-\deE.+]+)\s+([-\deE.+]+)\s+([-\deE.+]+)\s+([-\deE.+]+)", body)
        scale_note = ""
        if cm:
            a, b, c, d, e, f = [float(x) for x in cm.groups()]
            if a == 0 and d == 0 and e == 0 and b != 0:
                scale = f / b
                off = -c / b
                scale_note = f"x*{scale:g}" + (f"{off:+g}" if off else "")
        compu[name] = {"desc": desc, "unit": unit, "scale": scale_note}

    syms: Dict[int, dict] = {}
    for kind in ("CHARACTERISTIC", "AXIS_PTS"):
        for blk in txt.split(f"/begin {kind} ")[1:]:
            end = blk.find(f"/end {kind}")
            body = (blk[:end] if end != -1 else blk).lstrip()
            hm = re.match(r"(\S+)\s+\"([^\"]*)\"", body)
            am = re.search(r"\b0x([0-9A-Fa-f]+)\b", body)
            if not (hm and am):
                continue
            addr = int(am.group(1), 16)
            # Find first COMP_ token
            cm = re.search(r"\b(COMP_\S+)\b", body)
            cm_info = compu.get(cm.group(1), {}) if cm else {}
            syms[addr] = {
                "name": hm.group(1),
                "desc": hm.group(2),
                "kind": kind,
                "unit": cm_info.get("unit", ""),
                "scale": cm_info.get("scale", ""),
            }

    meas: Dict[int, dict] = {}
    for blk in txt.split("/begin MEASUREMENT ")[1:]:
        end = blk.find("/end MEASUREMENT")
        body = (blk[:end] if end != -1 else blk).lstrip()
        hm = re.match(r"(\S+)\s+\"([^\"]*)\"", body)
        am = re.search(r"ECU_ADDRESS\s+0x([0-9A-Fa-f]+)", body)
        if not (hm and am):
            continue
        cm = re.search(r"\b(COMP_\S+)\b", body)
        cm_info = compu.get(cm.group(1), {}) if cm else {}
        meas[int(am.group(1), 16)] = {
            "name": hm.group(1),
            "desc": hm.group(2),
            "unit": cm_info.get("unit", ""),
        }
    return {"syms": syms, "meas": meas, "compu": compu}


def load_csv_addr_map(path: Path, addr_keys=("Address", "address", "ROM Address", "storageaddress")) -> Dict[int, dict]:
    if not path.exists():
        return {}
    out: Dict[int, dict] = {}
    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            addr = None
            for k in addr_keys:
                v = (row.get(k) or "").strip()
                if v.startswith("0x") or v.startswith("0X"):
                    try:
                        addr = int(v, 16)
                        break
                    except ValueError:
                        pass
            if addr is None:
                for v in row.values():
                    vs = (v or "").strip()
                    if vs.startswith("0x") or vs.startswith("0X"):
                        try:
                            addr = int(vs, 16)
                            break
                        except ValueError:
                            pass
            if addr is not None:
                out[addr] = row
    return out


# ---------------------------------------------------------------------------
# Analysis Helpers (Tables, Links, Function Profiles, Structural Matching)
# ---------------------------------------------------------------------------

ELEM_WIDTH = {"uint8": 1, "int8": 1, "uint16": 2, "int16": 2}


def elem_width(elem_type: str) -> int:
    return ELEM_WIDTH.get(elem_type, 1)


def summarize_tables(rom: bytes, calls: List[dict]) -> Dict[int, dict]:
    by_addr: Dict[int, dict] = {}
    ax1_consumers = defaultdict(set)
    ax2_consumers = defaultdict(set)
    for c in calls:
        t = c["table"]
        if t is None:
            continue
        if c["axis1"] is not None:
            ax1_consumers[c["axis1"]].add(t)
        if c["axis2"] is not None:
            ax2_consumers[c["axis2"]].add(t)
        ent = by_addr.get(t)
        w = elem_width(c["elem_type"])
        sz = c["dim1"] * c["dim2"] * w
        if ent is None:
            blob = rom[t : t + sz]
            by_addr[t] = {
                "table": t,
                "end": t + sz - 1,
                "bytes": sz,
                "kind": c["kind"],
                "elem_type": c["elem_type"],
                "dim1": c["dim1"],
                "dim2": c["dim2"],
                "axis1_type": c["axis1_type"],
                "axis2_type": c["axis2_type"],
                "payload": blob,
                "nontrivial": len(set(blob)) > 2,
                "call_pcs": [c["call_pc"]],
                "helpers": [c["helper"]],
                "axis1s": [c["axis1"]] if c["axis1"] else [],
                "axis2s": [c["axis2"]] if c["axis2"] else [],
                "shared_as_axis_of": [],
                "reciprocal_with": [],
            }
        else:
            ent["call_pcs"].append(c["call_pc"])
            if c["helper"] not in ent["helpers"]:
                ent["helpers"].append(c["helper"])
            if c["axis1"] and c["axis1"] not in ent["axis1s"]:
                ent["axis1s"].append(c["axis1"])
            if c["axis2"] and c["axis2"] not in ent["axis2s"]:
                ent["axis2s"].append(c["axis2"])

    for t, ent in by_addr.items():
        parents = sorted((ax1_consumers[t] | ax2_consumers[t]) - {t})
        ent["shared_as_axis_of"] = parents
        recip = [p for p in parents if p in ent["axis1s"] or p in ent["axis2s"]]
        ent["reciprocal_with"] = recip
    return by_addr


def norm_sym(name: str) -> str:
    s = re.sub(r"(_S|_2|#\d+)$", "", name or "")
    if s.startswith("mTT"):
        s = "mT" + s[3:]
    return s


def build_func_profiles(rom: bytes, calls: List[dict], a2l: Optional[dict] = None) -> Dict[int, dict]:
    if not calls:
        return {}
    scan_lo = min(0x20000, min(c["call_pc"] for c in calls) & ~0xFFF)
    prologues = [pc for pc in range(scan_lo, len(rom) - 2, 2) if struct.unpack_from(">H", rom, pc)[0] == 0x4F22]
    by_fn = defaultdict(list)
    for c in calls:
        idx = bisect.bisect_right(prologues, c["call_pc"]) - 1
        fn_start = prologues[idx] if idx >= 0 and (c["call_pc"] - prologues[idx]) < 0x1000 else (c["call_pc"] & ~0xFF)
        by_fn[fn_start].append(c)

    syms = a2l["syms"] if a2l else {}
    meas = a2l["meas"] if a2l else {}
    profiles: Dict[int, dict] = {}
    for fn_start, cs in by_fn.items():
        cs_sorted = sorted(cs, key=lambda x: x["call_pc"])
        idx = bisect.bisect_right(prologues, fn_start)
        fn_end = min(fn_start + 0xB00, prologues[idx] if idx < len(prologues) else len(rom))
        tbl_set = {c["table"] for c in cs_sorted if c["table"]} | {c["axis1"] for c in cs_sorted if c["axis1"]} | {c["axis2"] for c in cs_sorted if c["axis2"]}

        ram_refs: List[int] = []
        cal_vals = set()
        imms = set()
        for pc in range(fn_start, fn_end, 2):
            w = struct.unpack_from(">H", rom, pc)[0]
            top = w >> 12
            if top == 0xD:
                ea = (pc & ~3) + 4 + (w & 0xFF) * 4
                if ea + 4 <= len(rom):
                    v = struct.unpack_from(">I", rom, ea)[0]
                    if 0xFFFF0000 <= v <= 0xFFFFFFFF:
                        ram_refs.append(v)
                    elif 0x04000 <= v < 0x20000 and v not in tbl_set:
                        cal_vals.add(struct.unpack_from(">H", rom, v)[0])
            elif top in (0xE, 0xC):
                imms.add((top, w & 0xFF))

        sig = tuple((c["kind"], c["dim1"], c["dim2"], c["elem_type"]) for c in cs_sorted)
        payloads = []
        for c in cs_sorted:
            t = c["table"]
            if t is not None:
                sz = c["dim1"] * c["dim2"] * elem_width(c["elem_type"])
                b = rom[t : t + sz]
                payloads.append(b if len(set(b)) > 2 else None)
            else:
                payloads.append(None)

        tbl_entries = []
        for c in cs_sorted:
            t = c["table"]
            sym_d = syms.get(t) if t is not None else None
            tbl_entries.append({
                "table": t,
                "sym": sym_d["name"] if sym_d else None,
                "desc": sym_d["desc"] if sym_d else "",
                "unit": sym_d["unit"] if sym_d else "",
                "scale": sym_d["scale"] if sym_d else "",
                "sig": (c["kind"], c["dim1"], c["dim2"], c["elem_type"]),
            })

        profiles[fn_start] = {
            "start": fn_start,
            "end": fn_end,
            "len": fn_end - fn_start,
            "calls": cs_sorted,
            "sig": sig,
            "sig_bag": tuple(sorted(sig)),
            "payloads": payloads,
            "cal_vals": cal_vals,
            "imms": imms,
            "ram_names": [meas[r]["name"] for r in dict.fromkeys(ram_refs) if r in meas],
            "tbl_entries": tbl_entries,
        }
    return profiles


def score_func_pair(el_pr: dict, cand: dict) -> Tuple[int, dict]:
    exact_order = el_pr["sig"] == cand["sig"]
    n_pay = 0
    for eb, cb in zip(el_pr["payloads"], cand["payloads"]):
        if eb is not None and eb == cb:
            n_pay += 1
    if not n_pay:
        el_set = {b for b in el_pr["payloads"] if b is not None}
        c_set = {b for b in cand["payloads"] if b is not None}
        n_pay = len(el_set & c_set)
    cal_ov = len(el_pr["cal_vals"] & cand["cal_vals"])
    imm_ov = len(el_pr["imms"] & cand["imms"])
    len_diff = abs(el_pr["len"] - cand["len"])
    score = (20 * n_pay) + (5 if exact_order else 0) + (3 * cal_ov) + imm_ov - (len_diff // 128)
    return score, {"n_pay": n_pay, "exact_order": exact_order, "cal_ov": cal_ov, "imm_ov": imm_ov}


def build_a2l_table_leads(el_rom: bytes, el_calls: List[dict], v6_hex: Path, v6_a2l_p: Path, jk_s19: Path, jk_a2l_p: Path) -> dict:
    """Compute per-EL19A-function and per-EL19A-table structural A2L leads."""
    if not (v6_hex.exists() and v6_a2l_p.exists() and jk_s19.exists() and jk_a2l_p.exists()):
        return {"by_table": {}, "by_func": {}, "available": False}

    v6 = load_any_rom(v6_hex)
    jk = load_any_rom(jk_s19)
    v6_a2l = parse_a2l_rich(v6_a2l_p)
    jk_a2l = parse_a2l_rich(jk_a2l_p)

    v6_c = extract_calls(v6, discover_helpers(v6))
    jk_c = extract_calls(jk, discover_helpers(jk))

    el_p = build_func_profiles(el_rom, el_calls)
    v6_p = build_func_profiles(v6, v6_c, v6_a2l)
    jk_p = build_func_profiles(jk, jk_c, jk_a2l)

    v6_by_bag = defaultdict(list)
    for pr in v6_p.values():
        v6_by_bag[pr["sig_bag"]].append(pr)
    jk_by_bag = defaultdict(list)
    for pr in jk_p.values():
        jk_by_bag[pr["sig_bag"]].append(pr)

    # Also payload lookup
    v6_pay = defaultdict(list)
    jk_pay = defaultdict(list)
    for pr in v6_p.values():
        for c, te in zip(pr["calls"], pr["tbl_entries"]):
            if c["table"] is not None and te["sym"]:
                sz = c["dim1"] * c["dim2"] * elem_width(c["elem_type"])
                b = v6[c["table"] : c["table"] + sz]
                if len(set(b)) > 2:
                    v6_pay[b].append(te)
    for pr in jk_p.values():
        for c, te in zip(pr["calls"], pr["tbl_entries"]):
            if c["table"] is not None and te["sym"]:
                sz = c["dim1"] * c["dim2"] * elem_width(c["elem_type"])
                b = jk[c["table"] : c["table"] + sz]
                if len(set(b)) > 2:
                    jk_pay[b].append(te)

    by_func = {}
    by_table = defaultdict(list)
    for fn, pr in sorted(el_p.items()):
        bag = pr["sig_bag"]
        vm = sorted([(score_func_pair(pr, x)[0], score_func_pair(pr, x)[1], x) for x in v6_by_bag.get(bag, [])], key=lambda t: -t[0])
        jm = sorted([(score_func_pair(pr, x)[0], score_func_pair(pr, x)[1], x) for x in jk_by_bag.get(bag, [])], key=lambda t: -t[0])
        is_multi = len(bag) >= 2
        rare_v = 0 < len(vm) <= 3
        rare_j = 0 < len(jm) <= 3
        has_pay = (vm and vm[0][1]["n_pay"] > 0) or (jm and jm[0][1]["n_pay"] > 0)
        high_spec = (is_multi and (rare_v or rare_j)) or (not is_multi and ((len(vm) == 1) or (0 < len(jm) <= 2))) or has_pay

        v_top = vm[0] if vm else None
        j_top = jm[0] if jm else None
        consensus = False
        if v_top and j_top:
            vr = {norm_sym(e["sym"]) for e in v_top[2]["tbl_entries"] if e["sym"]}
            jr = {norm_sym(e["sym"]) for e in j_top[2]["tbl_entries"] if e["sym"]}
            consensus = bool(vr & jr)

        by_func[fn] = {
            "fn": fn,
            "profile": pr,
            "high_spec": high_spec,
            "consensus": consensus,
            "v_matches": vm,
            "j_matches": jm,
        }

        if high_spec:
            for idx, c in enumerate(pr["calls"]):
                t = c["table"]
                if t is None:
                    continue
                v_te = v_top[2]["tbl_entries"][idx] if (v_top and v_top[1]["exact_order"] and idx < len(v_top[2]["tbl_entries"])) else None
                j_te = j_top[2]["tbl_entries"][idx] if (j_top and j_top[1]["exact_order"] and idx < len(j_top[2]["tbl_entries"])) else None
                by_table[t].append({
                    "fn": fn,
                    "consensus": consensus,
                    "v_sym": v_te["sym"] if v_te else None,
                    "v_unit": v_te["unit"] if v_te else "",
                    "v_scale": v_te["scale"] if v_te else "",
                    "j_sym": j_te["sym"] if j_te else None,
                    "j_unit": j_te["unit"] if j_te else "",
                    "j_scale": j_te["scale"] if j_te else "",
                    "ram_leads": (v_top[2]["ram_names"] if v_top else [])[:4] + (j_top[2]["ram_names"] if j_top else [])[:4],
                })

    return {
        "available": True,
        "by_func": by_func,
        "by_table": by_table,
        "v6_pay": v6_pay,
        "jk_pay": jk_pay,
        "v6_a2l": v6_a2l,
        "jk_a2l": jk_a2l,
    }


def decode_rom_values(rom: bytes, addr: int, dim1: int, dim2: int, etype: str) -> List[int]:
    w = elem_width(etype)
    fmt = {
        "uint8": f">{dim1 * dim2}B",
        "int8": f">{dim1 * dim2}b",
        "uint16": f">{dim1 * dim2}H",
        "int16": f">{dim1 * dim2}h",
    }.get(etype, f">{dim1 * dim2}B")
    if addr + dim1 * dim2 * w > len(rom):
        return []
    return list(struct.unpack_from(fmt, rom, addr))


def _parse_hex_addr_flex(val: str) -> Optional[int]:
    s = (val or "").strip()
    if not s:
        return None
    if s.startswith(("0x", "0X")):
        s = s[2:]
    if not re.fullmatch(r"[0-9A-Fa-f]{1,8}", s):
        return None
    return int(s, 16)


def load_hash_validated_el19a_context(
    rom: bytes,
    *,
    expected_rom_sha256: str = EL19A_PINNED_SHA256,
    index_dir: Optional[Path] = Path("INDEX"),
) -> dict:
    """
    Hash-validated adapter for prebuilt EL19A `INDEX/*.tsv` datasets
    (catalog consumers, GBR map, OBD Mode 01, Consult Mode 22, DTC writers, EL13A diff blocks).
    Treats mismatched ROM hashes or absent directories/files as explicitly unavailable.
    """
    observed_sha = hashlib.sha256(rom).hexdigest()
    if index_dir is None:
        return {
            "status": "unavailable",
            "reason": "index_dir_not_configured",
            "expected_rom_sha256": expected_rom_sha256,
            "observed_rom_sha256": observed_sha,
            "sources": {},
        }
    idx_path = Path(index_dir)
    if observed_sha.lower() != expected_rom_sha256.lower():
        return {
            "status": "unavailable",
            "reason": "rom_hash_mismatch",
            "expected_rom_sha256": expected_rom_sha256,
            "observed_rom_sha256": observed_sha,
            "sources": {},
        }
    if not idx_path.exists():
        return {
            "status": "unavailable",
            "reason": "index_dir_missing",
            "expected_rom_sha256": expected_rom_sha256,
            "observed_rom_sha256": observed_sha,
            "sources": {},
        }

    def _read_tsv(fname: str) -> Tuple[Optional[dict], List[dict]]:
        fp = idx_path / fname
        if not fp.exists():
            return {"status": "unavailable", "reason": "missing", "path": str(fp)}, []
        raw_b = fp.read_bytes()
        with fp.open("r", newline="", encoding="utf-8", errors="replace") as fh:
            rows = list(csv.DictReader(fh, delimiter="\t"))
        return {
            "status": "available",
            "path": str(fp),
            "sha256": hashlib.sha256(raw_b).hexdigest(),
            "row_count": len(rows),
        }, rows

    sources: Dict[str, dict] = {}
    meta, cat_rows = _read_tsv("catalog_179_consumer_summary.tsv")
    sources["catalog_179_consumer_summary"] = meta
    catalog_by_addr: Dict[int, dict] = {}
    for row in cat_rows:
        addr = _parse_hex_addr_flex(row.get("address", ""))
        if addr is not None:
            catalog_by_addr[addr] = row

    meta, gbr_rows = _read_tsv("function_gbr_map.tsv")
    sources["function_gbr_map"] = meta
    gbr_by_func: Dict[int, List[dict]] = defaultdict(list)
    for row in gbr_rows:
        fn = row.get("function", "")
        if fn.startswith("sub_"):
            fa = _parse_hex_addr_flex(fn[4:])
            if fa is not None:
                gbr_by_func[fa].append(row)

    meta, obd_rows = _read_tsv("obd_mode01_pid_map.tsv")
    sources["obd_mode01_pid_map"] = meta
    meta, cid_rows = _read_tsv("consult_mode22_pid_map.tsv")
    sources["consult_mode22_pid_map"] = meta
    meta, dtc_rows = _read_tsv("dtc_198_and_writers.tsv")
    sources["dtc_198_and_writers"] = meta
    meta, diff_rows = _read_tsv("el19a_vs_el13a_diff_blocks.tsv")
    sources["el19a_vs_el13a_diff_blocks"] = meta

    ram_to_diag: Dict[str, List[str]] = defaultdict(list)
    for r in obd_rows:
        for col in ("kline_ram_sources", "can_ram_sources"):
            txt = r.get(col) or ""
            for m in re.finditer(r"FFFF[0-9A-Fa-f]{4}", txt):
                ram_to_diag[m.group(0).upper()].append(f"OBD_0x{r.get('pid_hex', '').lstrip('0x') or '00'}:{r.get('sae_name', '')}")
    for r in cid_rows:
        for col in ("ptr1_addr", "ptr2_addr"):
            v = (r.get(col) or "").strip().upper()
            if v.startswith("FFFF"):
                ram_to_diag[v].append(f"CID_{r.get('cid_hex', '')}:{r.get('mode01_cross_match', '')}")
    for r in dtc_rows:
        v = (r.get("target_ram") or "").strip().upper()
        if v.startswith("FFFF"):
            ram_to_diag[v].append(f"DTC_{r.get('pcode', '')}({r.get('access_kind', '')})")

    avail_count = sum(1 for s in sources.values() if s["status"] == "available")
    return {
        "status": "available" if avail_count > 0 else "unavailable",
        "reason": "ok" if avail_count > 0 else "no_index_files_found",
        "expected_rom_sha256": expected_rom_sha256,
        "observed_rom_sha256": observed_sha,
        "sources": sources,
        "catalog_by_addr": catalog_by_addr,
        "gbr_by_func": dict(gbr_by_func),
        "ram_to_diag": {k: list(dict.fromkeys(v)) for k, v in ram_to_diag.items()},
        "diff_blocks_count": len(diff_rows),
    }


def reconcile_definition_sources(
    *,
    xml_paths: Optional[List[Path]] = None,
    matrix_paths: Optional[List[Path]] = None,
    catalog_path: Optional[Path] = None,
    candidate_path: Optional[Path] = None,
    scanner_tables: Optional[Dict[int, dict]] = None,
) -> dict:
    """
    Source-by-source multi-definition & dual-scope-matrix reconciliation preserving every
    source SHA-256 and surfacing disagreements without silently discarding any source.
    """
    source_manifest: List[dict] = []
    by_addr: Dict[int, Dict[str, dict]] = defaultdict(dict)

    for xp in (xml_paths or []):
        p = Path(xp)
        if not p.exists():
            source_manifest.append({"source_id": p.name, "kind": "xml", "path": str(p), "status": "unavailable"})
            continue
        sha = hashlib.sha256(p.read_bytes()).hexdigest()
        xtbls = load_xml_tables(p)
        sid = f"xml:{p.name}"
        source_manifest.append({"source_id": sid, "kind": "xml", "path": str(p), "sha256": sha, "status": "available", "count": len(xtbls)})
        for addr, ent in xtbls.items():
            by_addr[addr][sid] = {
                "source_id": sid,
                "name": ent.get("name"),
                "geometry": f"{ent.get('sizex')}x{ent.get('sizey')}",
                "storage_type": ent.get("storagetype"),
                "scaling": ent.get("scaling"),
                "disposition": "IN_XML",
            }

    for mp in (matrix_paths or []):
        p = Path(mp)
        if not p.exists():
            source_manifest.append({"source_id": p.name, "kind": "scope_matrix", "path": str(p), "status": "unavailable"})
            continue
        sha = hashlib.sha256(p.read_bytes()).hexdigest()
        sid = f"matrix:{p.name}"
        row_cnt = 0
        with p.open(newline="", encoding="utf-8", errors="replace") as fh:
            for row in csv.DictReader(fh):
                addr = _parse_hex_addr_flex(row.get("address") or row.get("Address") or "")
                if addr is None:
                    continue
                row_cnt += 1
                by_addr[addr][sid] = {
                    "source_id": sid,
                    "name": row.get("baseline_name") or row.get("name"),
                    "geometry": row.get("geometry_orientation"),
                    "storage_type": row.get("storage_type"),
                    "scaling": row.get("current_scaling"),
                    "disposition": row.get("release_disposition") or row.get("InScope") or "",
                }
        source_manifest.append({"source_id": sid, "kind": "scope_matrix", "path": str(p), "sha256": sha, "status": "available", "count": row_cnt})

    for label, cp in (("catalog", catalog_path), ("candidate_register", candidate_path)):
        if cp is None:
            continue
        p = Path(cp)
        if not p.exists():
            source_manifest.append({"source_id": label, "kind": "csv", "path": str(p), "status": "unavailable"})
            continue
        sha = hashlib.sha256(p.read_bytes()).hexdigest()
        cnt = 0
        with p.open(newline="", encoding="utf-8", errors="replace") as fh:
            for row in csv.DictReader(fh):
                addr = None
                for k in ("Address", "address", "ROM Address", "storageaddress"):
                    addr = _parse_hex_addr_flex(row.get(k) or "")
                    if addr is not None:
                        break
                if addr is None:
                    continue
                cnt += 1
                by_addr[addr][label] = {
                    "source_id": label,
                    "name": row.get("candidate_name") or row.get("Name") or row.get("name"),
                    "geometry": row.get("dimensions"),
                    "storage_type": row.get("storage"),
                    "scaling": row.get("conversion"),
                    "disposition": row.get("status") or "CATALOG_ROW",
                }
        source_manifest.append({"source_id": label, "kind": "csv", "path": str(p), "sha256": sha, "status": "available", "count": cnt})

    if scanner_tables:
        for addr, ent in scanner_tables.items():
            by_addr[addr]["scanner"] = {
                "source_id": "scanner",
                "name": None,
                "geometry": f"{ent['dim1']}x{ent['dim2']}",
                "storage_type": ent["elem_type"],
                "scaling": None,
                "disposition": ent["kind"],
            }

    records: List[dict] = []
    conflict_counts: Dict[str, int] = defaultdict(int)
    for addr in sorted(by_addr):
        src_map = by_addr[addr]
        statuses: List[str] = []
        xml_entries = [v for k, v in src_map.items() if k.startswith("xml:")]
        mat_entries = [v for k, v in src_map.items() if k.startswith("matrix:")]
        if len({e["name"] for e in xml_entries if e.get("name")}) > 1:
            statuses.append("xml_name_conflict")
        if len({e["scaling"] for e in xml_entries + mat_entries if e.get("scaling")}) > 1:
            statuses.append("scaling_conflict")
        if len({e["disposition"] for e in mat_entries if e.get("disposition")}) > 1:
            statuses.append("disposition_conflict")
        if "scanner" in src_map and xml_entries:
            sc_g = src_map["scanner"]["geometry"]
            for xe in xml_entries:
                if xe.get("geometry") and xe["geometry"] != sc_g:
                    try:
                        x1, x2 = [int(p) for p in xe["geometry"].split("x")]
                        s1, s2 = [int(p) for p in sc_g.split("x")]
                        if x1 * x2 != s1 * s2:
                            statuses.append("geometry_conflict")
                            break
                    except ValueError:
                        pass
        for st in statuses:
            conflict_counts[st] += 1
        records.append({
            "address": addr,
            "address_hex": f"0x{addr:05X}",
            "conflicts": sorted(set(statuses)),
            "sources": src_map,
        })

    return {
        "schema": "sh705x-definition-reconciliation-v1",
        "sources": source_manifest,
        "address_count": len(records),
        "conflict_counts": dict(sorted(conflict_counts.items())),
        "records": records,
    }


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------

def cmd_scan(args):
    p = Path(args.rom)
    rom = load_any_rom(p)
    fp = rom_fingerprint(rom)
    helpers = discover_helpers(rom)
    calls = extract_calls(rom, helpers)
    tables = summarize_tables(rom, calls)

    print(f"=== SCAN: {p} ===")
    print(f"Size: {fp['size']:,} B (active end 0x{fp['active_end']:X}) | MD5: {fp['md5']} | SHA256: {fp['sha256'][:16]}...")
    boot_note = " (bootblock 0x00000-0x081FF 0xFF-padded / .dat)" if (fp["reset_pc"] == 0xFFFFFFFF and len(rom) >= 0x8200 and rom[:0x8200] == b"\xff" * 0x8200) else ""
    print(f"Reset PC: 0x{fp['reset_pc']:08X} | SP: 0x{fp['reset_sp']:08X}{boot_note} | CPU: {fp['cpu_tags']} | FIDs: {fp['fid_tags']}")
    meta = fp["nissan_meta"]
    meta_parts = []
    if meta["loader"]:
        meta_parts.append(f"Loader={meta['loader']}@0x{meta['loader_addr']:04X}")
    if meta["fid"]:
        meta_parts.append(f"FID={meta['fid']}@0x{meta['fid_addr']:05X} ({meta['fid_cpu']})")
    if meta["ramf_ptrs"]:
        meta_parts.append(f"RAMF_ptrs={meta['ramf_ptrs']}")
    if meta["ivt_unique"]:
        meta_parts.append(f"IVT_handlers={meta['ivt_unique']}")
    if meta_parts:
        print("Nissan Struct: " + " | ".join(meta_parts))
    cks = fp["checksums"]
    ck_parts = []
    if cks["ck_std"]:
        cs = cks["ck_std"]
        ck_parts.append(f"ck_std={cs['status']}(sumt@0x{cs['sumt']:05X},xort@0x{cs['xort']:05X})")
    if cks["ck_alt2"]:
        ca = cks["ck_alt2"]
        ck_parts.append(f"ck_alt2={ca['status']}(0x{ca['start']:05X}..0x{ca['end']:05X},sumt@0x{ca['sumt']:05X})")
    if cks["cal16"]:
        c16 = cks["cal16"]
        ck_parts.append(f"cal16@0x{c16['addr']:05X}={c16['status']}(0x{c16['stored']:04X}/0x{c16['calc']:04X})")
    if cks["main16"]:
        m16 = cks["main16"]
        ck_parts.append(f"main16@0x{m16['addr']:05X}={m16['status']}(0x{m16['stored']:04X}/0x{m16['calc']:04X})")
    if ck_parts:
        print("Checksums: " + " | ".join(ck_parts))
    print(f"Helpers: {len(helpers)} ({dict(Counter(h.kind for h in helpers.values()))})")
    resolved = sum(1 for c in calls if c["table"] is not None)
    shared_axes = sum(1 for t in tables.values() if t["shared_as_axis_of"])
    recip_pairs = sum(1 for t in tables.values() if t["reciprocal_with"])
    print(f"Call sites: {len(calls)} total, {resolved} resolved -> {len(tables)} unique tables ({shared_axes} dual-used as axis, {recip_pairs} reciprocal-pair endpoints)")

    if args.tsv:
        out_p = Path(args.tsv)
        with out_p.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, delimiter="\t")
            w.writerow(["table", "end", "bytes", "kind", "elem_type", "dim1", "dim2", "axis1", "axis2", "n_calls", "call_pcs", "shared_as_axis_of", "reciprocal_with", "nontrivial"])
            for a, t in sorted(tables.items()):
                w.writerow([
                    f"0x{a:05X}", f"0x{t['end']:05X}", t["bytes"], t["kind"], t["elem_type"], t["dim1"], t["dim2"],
                    ",".join(f"0x{x:05X}" for x in t["axis1s"]),
                    ",".join(f"0x{x:05X}" for x in t["axis2s"]),
                    len(t["call_pcs"]),
                    ",".join(f"0x{pc:05X}" for pc in t["call_pcs"]),
                    ",".join(f"0x{x:05X}" for x in t["shared_as_axis_of"]),
                    ",".join(f"0x{x:05X}" for x in t["reciprocal_with"]),
                    int(t["nontrivial"]),
                ])
        print(f"Wrote TSV inventory -> {out_p}")

    if args.json:
        out_j = Path(args.json)
        payload = {
            "file": str(p),
            "fingerprint": fp,
            "helpers": {f"0x{k:05X}": vars(v) for k, v in sorted(helpers.items())},
            "tables": {
                f"0x{a:05X}": {k: v for k, v in t.items() if k != "payload"}
                for a, t in sorted(tables.items())
            },
        }
        out_j.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"Wrote JSON summary -> {out_j}")

    cat_out = getattr(args, "catalogue", None)
    man_out = getattr(args, "manifest", None)
    enh_win = getattr(args, "enhanced_window", 0) or 0
    inc_scalars = bool(getattr(args, "include_scalars", False))
    if cat_out or man_out:
        scan_doc = build_scan_export(str(p), rom, helpers, calls)
        cat = to_per_address_catalogue(scan_doc)
        cat["implicit_grids"] = {f"0x{k:05X}": v for k, v in extract_implicit_grids(rom, helpers).items()}
        if enh_win > 0:
            enh_calls = extract_calls_enhanced(rom, helpers, window_bytes=enh_win)
            cat["enhanced_call_comparison"] = compare_call_extractions(calls, enh_calls)
        if inc_scalars:
            cat["scalar_candidates"] = discover_cal_scalars(rom, helpers, calls=calls)
        written_paths: List[Path] = []
        if cat_out:
            cat_p = Path(cat_out)
            atomic_write_json(cat_p, cat)
            written_paths.append(cat_p)
            print(f"Wrote lossless catalogue ({len(cat['candidates'])} candidates) -> {cat_p}")
        if man_out:
            man_p = Path(man_out)
            man = build_run_manifest(
                Path(__file__),
                input_path=p,
                decoded_rom=rom,
                command_args=sys.argv,
                exit_status=0,
                output_paths=written_paths,
            )
            atomic_write_json(man_p, man)
            print(f"Wrote run manifest -> {man_p}")


def cmd_audit(args):
    el_p = Path(args.el19a)
    el_rom = load_any_rom(el_p)
    el_helpers = discover_helpers(el_rom)
    el_calls = extract_calls(el_rom, el_helpers)
    tables = summarize_tables(el_rom, el_calls)

    xml_tables = load_xml_tables(Path(args.xml))
    cat_map = load_csv_addr_map(Path(args.catalog))
    mat_map = load_csv_addr_map(Path(args.matrix))

    # Load variant payload sets if present
    variants = {}
    for label, vpath in [("EL13A_CVT", args.el13a), ("8W83B_AT", args.w83b), ("EE310_MT07", args.ee310)]:
        vp = Path(vpath)
        if vp.exists():
            vrom = load_any_rom(vp)
            vc = extract_calls(vrom, discover_helpers(vrom))
            vt = summarize_tables(vrom, vc)
            variants[label] = {
                "rom": vrom,
                "tables": vt,
                "payloads": {t["payload"] for t in vt.values()},
            }

    a2l_leads = build_a2l_table_leads(
        el_rom, el_calls,
        Path(args.v6_hex), Path(args.v6_a2l),
        Path(args.juke_s19), Path(args.juke_a2l),
    )

    in_xml = [a for a in sorted(tables) if a in xml_tables]
    missing_xml = [a for a in sorted(tables) if a not in xml_tables]
    xml_only = [a for a in sorted(xml_tables) if a not in tables]

    print(f"=== EL19A UNIFIED AUDIT ({el_p}) ===")
    print(f"Caller-backed tables: {len(tables)} | XML tables: {len(xml_tables)} | Catalog rows: {len(cat_map)} | Scope matrix rows: {len(mat_map)}")
    print(f"Overlap: {len(in_xml)} in XML, {len(missing_xml)} caller-backed NOT in XML ({sum(1 for a in missing_xml if a not in cat_map and a not in mat_map)} also absent from catalog & scope matrix)")
    print(f"XML-only (scalars / non-helper / non-base): {len(xml_only)}")

    # Geometry disagreements
    diffs = []
    for a in in_xml:
        xt = xml_tables[a]
        t = tables[a]
        if xt["sizex"] * xt["sizey"] != t["dim1"] * t["dim2"]:
            diffs.append((a, xt, t))
    print(f"\nGeometry disagreements (XML vs SH-2 helper): {len(diffs)}")
    for a, xt, t in diffs:
        print(f"  0x{a:05X}: XML={xt['type']} {xt['storagetype']} {xt['sizex']}x{xt['sizey']} ({xt['name']}) | Helper={t['kind']} {t['elem_type']} {t['dim1']}x{t['dim2']} (0x{a:05X}-0x{t['end']:05X})")

    # Linked / reciprocal storage
    print("\nLinked axis / reciprocal-pair relationships:")
    for a, t in sorted(tables.items()):
        if t["shared_as_axis_of"] or t["reciprocal_with"]:
            print(f"  0x{a:05X} ({t['kind']} {t['dim1']}x{t['dim2']}): axis_of={[f'0x{x:05X}' for x in t['shared_as_axis_of']]} reciprocal={[f'0x{x:05X}' for x in t['reciprocal_with']]}")

    # Missing high-value 3D or A2L-supported objects
    print("\nMissing-from-XML 3D tables & dual-consensus A2L leads:")
    for a in missing_xml:
        t = tables[a]
        leads = a2l_leads["by_table"].get(a, [])
        cons = [l for l in leads if l["consensus"]]
        v_p = sorted({x["sym"] for x in a2l_leads.get("v6_pay", {}).get(t["payload"], [])})
        j_p = sorted({x["sym"] for x in a2l_leads.get("jk_pay", {}).get(t["payload"], [])})
        if t["kind"].startswith("3D") or cons or v_p or j_p:
            var_flags = []
            if "EL13A_CVT" in variants:
                v_ent = variants["EL13A_CVT"]["tables"].get(a)
                if v_ent and v_ent["payload"] != t["payload"]:
                    var_flags.append("DIFF_EL13A")
            if "8W83B_AT" in variants and t["payload"] not in variants["8W83B_AT"]["payloads"]:
                var_flags.append("DIFF_8W83B")
            lead_txt = ""
            if cons:
                lead_txt = f"CONSENSUS V6={cons[0]['v_sym']} Juke={cons[0]['j_sym']}"
            elif leads:
                lead_txt = f"FUNC_LEAD V6={leads[0]['v_sym']} Juke={leads[0]['j_sym']}"
            if v_p or j_p:
                lead_txt += f" | PAYLOAD V6={v_p[:2]} Juke={j_p[:2]}"
            print(f"  0x{a:05X} ({t['kind']} {t['elem_type']} {t['dim1']}x{t['dim2']} @ {[f'0x{x:05X}' for x in t['call_pcs'][:2]]}) {var_flags} -> {lead_txt or 'no A2L lead'}")

    if args.tsv:
        out_p = Path(args.tsv)
        with out_p.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, delimiter="\t")
            w.writerow([
                "address", "end", "bytes", "kind", "elem_type", "dim1", "dim2", "axis1", "axis2",
                "in_r1_xml", "xml_name", "xml_dims", "in_catalog", "in_scope_matrix",
                "el13a_same_payload", "w83b_has_payload", "ee310_has_payload",
                "shared_as_axis_of", "reciprocal_with", "a2l_consensus", "a2l_v6_lead", "a2l_juke_lead", "a2l_ram_leads",
            ])
            for a, t in sorted(tables.items()):
                xt = xml_tables.get(a)
                leads = a2l_leads["by_table"].get(a, [])
                best = sorted(leads, key=lambda l: (not l["consensus"], not l["v_sym"]))[0] if leads else None
                v_pay = sorted({x["sym"] for x in a2l_leads.get("v6_pay", {}).get(t["payload"], [])})
                j_pay = sorted({x["sym"] for x in a2l_leads.get("jk_pay", {}).get(t["payload"], [])})
                el13a_same = ""
                if "EL13A_CVT" in variants:
                    ve = variants["EL13A_CVT"]["tables"].get(a)
                    el13a_same = "YES" if (ve and ve["payload"] == t["payload"]) else "DIFF"
                w.writerow([
                    f"0x{a:05X}", f"0x{t['end']:05X}", t["bytes"], t["kind"], t["elem_type"], t["dim1"], t["dim2"],
                    ",".join(f"0x{x:05X}" for x in t["axis1s"]),
                    ",".join(f"0x{x:05X}" for x in t["axis2s"]),
                    int(a in xml_tables), xt["name"] if xt else "", f"{xt['sizex']}x{xt['sizey']}" if xt else "",
                    int(a in cat_map), int(a in mat_map),
                    el13a_same,
                    int(t["payload"] in variants["8W83B_AT"]["payloads"]) if "8W83B_AT" in variants else "",
                    int(t["payload"] in variants["EE310_MT07"]["payloads"]) if "EE310_MT07" in variants else "",
                    ",".join(f"0x{x:05X}" for x in t["shared_as_axis_of"]),
                    ",".join(f"0x{x:05X}" for x in t["reciprocal_with"]),
                    int(best["consensus"]) if best else 0,
                    best["v_sym"] or (v_pay[0] if v_pay else "") if best else (v_pay[0] if v_pay else ""),
                    best["j_sym"] or (j_pay[0] if j_pay else "") if best else (j_pay[0] if j_pay else ""),
                    ",".join(dict.fromkeys(best["ram_leads"])) if best else "",
                ])
        print(f"\nWrote enriched EL19A audit TSV -> {out_p}")

    # Optional multi-definition reconciliation & hash-validated EL19A INDEX context
    matrix_r1 = getattr(args, "matrix_r1", None)
    extra_xmls = getattr(args, "extra_xml", None) or []
    cand_csv = getattr(args, "candidate_csv", None)
    idx_dir_arg = getattr(args, "index_dir", None)
    rec_json_arg = getattr(args, "reconcile_json", None)
    if matrix_r1 or extra_xmls or cand_csv or rec_json_arg or idx_dir_arg:
        xml_list = [Path(args.xml)] + [Path(x) for x in extra_xmls]
        mat_list = [Path(args.matrix)]
        if matrix_r1 and Path(matrix_r1) not in mat_list:
            mat_list.append(Path(matrix_r1))
        rec = reconcile_definition_sources(
            xml_paths=xml_list,
            matrix_paths=mat_list,
            catalog_path=Path(args.catalog),
            candidate_path=Path(cand_csv) if cand_csv else None,
            scanner_tables=tables,
        )
        print(f"\nMulti-source reconciliation: {rec['address_count']} addrs | conflicts={rec['conflict_counts']}")
        if idx_dir_arg:
            exp_sha = getattr(args, "expected_el19a_sha256", EL19A_PINNED_SHA256) or EL19A_PINNED_SHA256
            el_ctx = load_hash_validated_el19a_context(el_rom, expected_rom_sha256=exp_sha, index_dir=Path(idx_dir_arg))
            print(f"EL19A INDEX adapter: status={el_ctx['status']} ({el_ctx['reason']})")
            rec["el19a_index_adapter"] = {k: v for k, v in el_ctx.items() if k not in ("catalog_by_addr", "gbr_by_func", "ram_to_diag")}
        if rec_json_arg:
            atomic_write_json(Path(rec_json_arg), rec)
            print(f"Wrote reconciliation JSON -> {rec_json_arg}")


def cmd_inspect(args):
    addr = int(args.target, 16)
    p = Path(args.rom)
    rom = load_any_rom(p)
    helpers = discover_helpers(rom)
    calls = extract_calls(rom, helpers)
    tables = summarize_tables(rom, calls)
    xml_tables = load_xml_tables(Path(args.xml)) if Path(args.xml).exists() else {}
    cat_map = load_csv_addr_map(Path(args.catalog))
    mat_map = load_csv_addr_map(Path(args.matrix))

    a2l_leads = build_a2l_table_leads(
        rom, calls,
        Path(args.v6_hex), Path(args.v6_a2l),
        Path(args.juke_s19), Path(args.juke_a2l),
    )

    if addr in tables:
        t = tables[addr]
        print(f"=== TABLE 0x{addr:05X} (0x{addr:05X}-0x{t['end']:05X}, {t['bytes']} B) ===")
        print(f"Helper geometry: {t['kind']} {t['elem_type']} {t['dim1']}x{t['dim2']} | axis1={[f'0x{x:05X}' for x in t['axis1s']]} ({t['axis1_type']}) axis2={[f'0x{x:05X}' for x in t['axis2s']]} ({t['axis2_type']})")
        print(f"Call PCs: {[f'0x{x:05X}' for x in t['call_pcs']]} via helpers {[f'0x{x:05X}' for x in t['helpers']]}")
        if addr in xml_tables:
            xt = xml_tables[addr]
            print(f"Release 1 XML: {xt['name']} | {xt['type']} {xt['storagetype']} {xt['sizex']}x{xt['sizey']}")
        else:
            print(f"Release 1 XML: ABSENT (in_catalog={addr in cat_map}, in_scope_matrix={addr in mat_map})")
        if t["shared_as_axis_of"] or t["reciprocal_with"]:
            print(f"Links: shared_as_axis_of={[f'0x{x:05X}' for x in t['shared_as_axis_of']]} reciprocal_with={[f'0x{x:05X}' for x in t['reciprocal_with']]}")
        vals = decode_rom_values(rom, addr, t["dim1"], t["dim2"], t["elem_type"])
        if len(vals) <= 32:
            print(f"Values ({len(vals)}): {vals}")
        else:
            print(f"Values ({len(vals)}): head={vals[:10]} ... tail={vals[-10:]}")

        for fn, info in sorted(a2l_leads.get("by_func", {}).items()):
            if any(c["table"] == addr for c in info["profile"]["calls"]):
                print(f"Caller fn 0x{fn:05X}: sig={info['profile']['sig']} consensus={info['consensus']}")
                if info["v_matches"]:
                    vt = info["v_matches"][0]
                    print(f"  V6 top 0x{vt[2]['start']:05X} (score={vt[0]}, pay={vt[1]['n_pay']}): {[(e['sym'], e['unit'], e['scale']) for e in vt[2]['tbl_entries']]} | RAM={vt[2]['ram_names'][:8]}")
                if info["j_matches"]:
                    jt = info["j_matches"][0]
                    print(f"  Juke top 0x{jt[2]['start']:05X} (score={jt[0]}, pay={jt[1]['n_pay']}): {[(e['sym'], e['unit'], e['scale']) for e in jt[2]['tbl_entries']]} | RAM={jt[2]['ram_names'][:8]}")
        idx_dir_arg = getattr(args, "index_dir", None)
        if idx_dir_arg:
            exp_sha = getattr(args, "expected_el19a_sha256", EL19A_PINNED_SHA256) or EL19A_PINNED_SHA256
            el_ctx = load_hash_validated_el19a_context(rom, expected_rom_sha256=exp_sha, index_dir=Path(idx_dir_arg))
            if el_ctx["status"] == "available":
                cat_row = el_ctx["catalog_by_addr"].get(addr)
                if cat_row:
                    print(f"EL19A INDEX consumer: tier={cat_row.get('evidence_tier')} query={cat_row.get('traced_query_inputs')} dest={cat_row.get('catalog_dest_ram')}")
                for fn in [fn for fn, info in sorted(a2l_leads.get("by_func", {}).items()) if any(c["table"] == addr for c in info["profile"]["calls"])]:
                    gbrs = el_ctx["gbr_by_func"].get(fn, [])
                    if gbrs:
                        print(f"  GBR map sub_{fn:X}: {[(g.get('gbr_base'), g.get('space')) for g in gbrs[:4]]}")
            else:
                print(f"EL19A INDEX adapter: unavailable ({el_ctx['reason']})")
        return

    # Function inspect
    by_fn = a2l_leads.get("by_func", {})
    if addr in by_fn:
        info = by_fn[addr]
        pr = info["profile"]
        print(f"=== FUNCTION 0x{addr:05X}-0x{pr['end']:05X} ({pr['len']} B) ===")
        for c in pr["calls"]:
            tbl_s = f"0x{c['table']:05X}" if c["table"] is not None else "None"
            ax1_s = f"0x{c['axis1']:05X}" if c["axis1"] is not None else "None"
            ax2_s = f"0x{c['axis2']:05X}" if c["axis2"] is not None else "None"
            print(f"  @0x{c['call_pc']:05X}: table={tbl_s} ({c['kind']} {c['dim1']}x{c['dim2']} {c['elem_type']}) ax1={ax1_s} ax2={ax2_s}")
        if info["v_matches"]:
            for sc_v, det, cand in info["v_matches"][:2]:
                print(f"  V6 match 0x{cand['start']:05X} (score={sc_v}, {det}): {[(e['sym'], e['unit'], e['scale']) for e in cand['tbl_entries']]} | RAM={cand['ram_names'][:10]}")
        if info["j_matches"]:
            for sc_j, det, cand in info["j_matches"][:2]:
                print(f"  Juke match 0x{cand['start']:05X} (score={sc_j}, {det}): {[(e['sym'], e['unit'], e['scale']) for e in cand['tbl_entries']]} | RAM={cand['ram_names'][:10]}")
        return

    # Raw ROM literal search for target (RAM or scalar)
    pat = struct.pack(">I", addr)
    hits = [i for i in range(0, len(rom) - 4, 4) if rom[i : i + 4] == pat]
    print(f"=== RAW LITERAL SEARCH 0x{addr:08X} ===")
    print(f"Aligned 32-bit pool occurrences ({len(hits)}): {[f'0x{h:05X}' for h in hits[:30]]}")
    v6_meas = a2l_leads.get("v6_a2l", {}).get("meas", {})
    jk_meas = a2l_leads.get("jk_a2l", {}).get("meas", {})
    if addr in v6_meas or addr in jk_meas:
        v_m = v6_meas.get(addr)
        j_m = jk_meas.get(addr)
        print(f"Direct same-address A2L MEASUREMENT (unverified lead): V6={v_m} | Juke={j_m}")
    idx_dir_arg = getattr(args, "index_dir", None)
    if idx_dir_arg:
        exp_sha = getattr(args, "expected_el19a_sha256", EL19A_PINNED_SHA256) or EL19A_PINNED_SHA256
        el_ctx = load_hash_validated_el19a_context(rom, expected_rom_sha256=exp_sha, index_dir=Path(idx_dir_arg))
        diag_hits = el_ctx.get("ram_to_diag", {}).get(f"{addr:08X}", [])
        if diag_hits:
            print(f"EL19A INDEX diagnostic links: {diag_hits}")
    fn_starts = sorted(by_fn)
    seen_fns = set()
    for h in hits[:30]:
        idx = bisect.bisect_right(fn_starts, h) - 1
        if idx >= 0:
            fn = fn_starts[idx]
            if h <= by_fn[fn]["profile"]["end"] + 0x200 and fn not in seen_fns:
                seen_fns.add(fn)
                info = by_fn[fn]
                v_top = info["v_matches"][0][2]["tbl_entries"][0]["sym"] if (info["v_matches"] and info["v_matches"][0][2]["tbl_entries"]) else None
                j_top = info["j_matches"][0][2]["tbl_entries"][0]["sym"] if (info["j_matches"] and info["j_matches"][0][2]["tbl_entries"]) else None
                print(f"  Near matched lookup fn 0x{fn:05X} (literal @0x{h:05X}): V6_lead={v_top} Juke_lead={j_top}")


def _format_cluster_values(ba: bytes, bb: bytes, start: int) -> str:
    n = len(ba)
    # Check if purely printable ASCII (e.g. FID/CALID changes)
    if n >= 2 and all((32 <= x < 127) or x == 0 for x in ba + bb) and any(48 <= x < 127 for x in ba + bb):
        sa = ba.decode("ascii", errors="replace").replace("\x00", "\\0")
        sb = bb.decode("ascii", errors="replace").replace("\x00", "\\0")
        return f'ASCII "{sa}" -> "{sb}"'
    if n == 1:
        va, vb = ba[0], bb[0]
        return f"u8 {va} -> {vb} ({vb - va:+d})"
    if n == 2 and start % 2 == 0:
        va, vb = struct.unpack_from(">H", ba)[0], struct.unpack_from(">H", bb)[0]
        return f"u16 0x{va:04X} ({va}) -> 0x{vb:04X} ({vb})"
    if n == 4 and start % 4 == 0:
        va, vb = struct.unpack_from(">I", ba)[0], struct.unpack_from(">I", bb)[0]
        return f"u32 0x{va:08X} -> 0x{vb:08X}"
    if n <= 12:
        return f"{ba.hex()} -> {bb.hex()}"
    return f"{ba[:8].hex()}... ({n}B) -> {bb[:8].hex()}..."


def _build_pool32_index(rom: bytes) -> Dict[int, List[int]]:
    idx: Dict[int, List[int]] = defaultdict(list)
    for off in range(0, len(rom) - 3, 4):
        v = struct.unpack_from(">I", rom, off)[0]
        if 0 < v < len(rom):
            idx[v].append(off)
    return idx


def _cluster_raw_diffs(ra: bytes, rb: bytes, start: int, end: int, covered_mask: bytearray, gap: int = 2) -> List[Tuple[int, int]]:
    clusters: List[List[int]] = []
    for i in range(start, end):
        if ra[i] != rb[i] and not covered_mask[i]:
            if clusters and i <= clusters[-1][1] + gap:
                clusters[-1][1] = i
            else:
                clusters.append([i, i])
    return [(s, e) for s, e in clusters]


def cmd_diff(args):
    pa, pb = Path(args.rom_a), Path(args.rom_b)
    ra, rb = load_any_rom(pa), load_any_rom(pb)
    ca = extract_calls(ra, discover_helpers(ra))
    cb = extract_calls(rb, discover_helpers(rb))
    ta, tb = summarize_tables(ra, ca), summarize_tables(rb, cb)
    xml_tables = load_xml_tables(Path(args.xml)) if Path(args.xml).exists() else {}

    pb_blobs = defaultdict(list)
    for addr, ent in tb.items():
        pb_blobs[ent["payload"]].append(addr)

    same_addr_same_bytes = []
    same_addr_diff_bytes = []
    relocated_exact_bytes = []
    unmatched = []
    for a, ent in sorted(ta.items()):
        if a in tb and tb[a]["kind"] == ent["kind"] and tb[a]["bytes"] == ent["bytes"]:
            if tb[a]["payload"] == ent["payload"]:
                same_addr_same_bytes.append(a)
            else:
                same_addr_diff_bytes.append(a)
        elif ent["payload"] in pb_blobs:
            relocated_exact_bytes.append((a, pb_blobs[ent["payload"]]))
        else:
            unmatched.append(a)

    print(f"=== DIFF: {pa.name} ({len(ta)} tables) vs {pb.name} ({len(tb)} tables) ===")
    print(f"Same-addr + identical payload: {len(same_addr_same_bytes)}")
    print(f"Same-addr + DIFFERING payload: {len(same_addr_diff_bytes)}")
    print(f"Relocated exact-payload match: {len(relocated_exact_bytes)} ({sum(1 for a,_ in relocated_exact_bytes if ta[a]['nontrivial'])} non-trivial)")
    print(f"Unmatched / variant-specific:  {len(unmatched)} ({sum(1 for a in unmatched if ta[a]['nontrivial'])} non-trivial)")

    if same_addr_diff_bytes:
        print("\nSame-address tables with DIFFERING payloads:")
        for a in same_addr_diff_bytes:
            ent = ta[a]
            xn = xml_tables[a]["name"] if a in xml_tables else "(NOT in R1 XML)"
            print(f"  0x{a:05X} ({ent['kind']} {ent['dim1']}x{ent['dim2']} {ent['elem_type']}): {xn}")

    nt_unmatched = [a for a in unmatched if ta[a]["nontrivial"]]
    if nt_unmatched:
        print(f"\nNon-trivial unmatched tables in ROM A ({len(nt_unmatched)} total, showing up to 40 — candidate variant/changed calibrations):")
        for a in nt_unmatched[:40]:
            ent = ta[a]
            xn = xml_tables[a]["name"] if a in xml_tables else "(NOT in R1 XML)"
            print(f"  0x{a:05X} ({ent['kind']} {ent['dim1']}x{ent['dim2']} {ent['elem_type']}): {xn}")

    # Raw byte/scalar diff fallback when both ROMs share size
    if len(ra) != len(rb):
        print(f"\nRaw byte/scalar diff: skipped (ROM sizes differ: {len(ra):,} B vs {len(rb):,} B)")
        return

    covered = bytearray(len(ra))
    for a in same_addr_diff_bytes:
        ent = ta[a]
        end_b = min(len(ra), ent["end"] + 1)
        covered[a:end_b] = b"\x01" * (end_b - a)

    # Detect unpopulated 0x00000..0x081FF bootblock in unpacked Consult .dat files
    scan_start = 0
    boot_note = ""
    if len(ra) >= 0x8200:
        a_ff = ra[:0x8200] == b"\xff" * 0x8200
        b_ff = rb[:0x8200] == b"\xff" * 0x8200
        if a_ff != b_ff:
            scan_start = 0x8200
            who = pa.name if a_ff else pb.name
            boot_note = f" (bootblock 0x00000-0x081FF omitted: 0xFF-padded in {who})"

    raw_total = sum(1 for i in range(scan_start, len(ra)) if ra[i] != rb[i])
    clusters = _cluster_raw_diffs(ra, rb, scan_start, len(ra), covered, gap=2)
    outside_bytes = sum(sum(1 for i in range(s, e + 1) if ra[i] != rb[i]) for s, e in clusters)

    print(f"\nRaw byte/scalar diff (same size {len(ra):,} B){boot_note}: {raw_total:,} differing bytes ({outside_bytes:,} outside same-addr diff tables, {len(clusters)} clusters)")
    if not clusters:
        return

    # Annotate clusters using table/axis spans, checksum fields, and 32-bit literal pool references
    table_ranges = [(a, ent["end"], ent) for a, ent in sorted(ta.items())]
    axis_addrs: Dict[int, List[int]] = {}
    for a, ent in ta.items():
        for ax in ent["axis1s"] + ent["axis2s"]:
            axis_addrs.setdefault(ax, []).append(a)
    pool32 = _build_pool32_index(ra)
    ck_tags_a = checksum_byte_tags(ra)
    ck_tags_b = checksum_byte_tags(rb)

    max_show = len(clusters) if args.raw_limit == 0 else args.raw_limit
    print(f"Non-table raw diff clusters (showing {min(len(clusters), max_show)}/{len(clusters)}):")
    for s, e in clusters[:max_show]:
        ba, bb = ra[s : e + 1], rb[s : e + 1]
        val_txt = _format_cluster_values(ba, bb, s)
        notes = []
        # Checksums touched in either ROM A or ROM B
        ck_lbls = []
        for off in range(s, e + 1):
            if off in ck_tags_a:
                ck_lbls.append(f"A:{ck_tags_a[off]}")
            if off in ck_tags_b:
                ck_lbls.append(f"B:{ck_tags_b[off]}")
        if ck_lbls:
            notes.append(f"checksum={list(dict.fromkeys(ck_lbls))}")
        # Check enclosing table or axis
        for ts, te, ent in table_ranges:
            if ts <= s <= te or ts <= e <= te:
                notes.append(f"in table 0x{ts:05X} ({ent['kind']} {ent['dim1']}x{ent['dim2']})")
                break
        ax_hits = [ax for ax in axis_addrs if ax <= s <= ax + 64]
        if ax_hits:
            notes.append(f"near axis 0x{ax_hits[0]:05X} (of {[f'0x{t:05X}' for t in axis_addrs[ax_hits[0]][:2]]})")
        # Check exact/near 32-bit pool pointers (e.g. checksum/scalar descriptors)
        hits = []
        for probe in range(s & ~3, e + 1):
            if probe in pool32:
                for p in pool32[probe]:
                    hits.append(f"0x{p:05X}->0x{probe:05X}")
        if hits:
            notes.append(f"pool32={hits[:4]}")
        if s in xml_tables:
            notes.append(f"XML:{xml_tables[s]['name']}")
        note_str = f" | {'; '.join(notes)}" if notes else ""
        addr_str = f"0x{s:05X}" if s == e else f"0x{s:05X}..0x{e:05X}"
        print(f"  {addr_str:16s} ({e - s + 1:3d}B): {val_txt}{note_str}")

    json_out = getattr(args, "json_out", None)
    if json_out:
        atomic_write_json(Path(json_out), {
            "rom_a": str(pa),
            "rom_b": str(pb),
            "same_addr_same_bytes": [f"0x{a:05X}" for a in same_addr_same_bytes],
            "same_addr_diff_bytes": [f"0x{a:05X}" for a in same_addr_diff_bytes],
            "relocated_exact_bytes": [{"from": f"0x{a:05X}", "to": [f"0x{x:05X}" for x in xs]} for a, xs in relocated_exact_bytes],
            "unmatched_nontrivial": [f"0x{a:05X}" for a in nt_unmatched],
            "raw_clusters": [{"start": f"0x{s:05X}", "end": f"0x{e:05X}", "bytes": e - s + 1} for s, e in clusters],
        })
        print(f"Wrote diff JSON -> {json_out}")


def cmd_ref_index(args):
    if args.action == "build":
        tsv_list = [Path(p) for p in getattr(args, "tsv", []) if p]
        idx = build_reference_index(
            a2l_paths=[Path(p) for p in args.a2l],
            xml_inputs=[Path(p) for p in args.xml],
            rom_paths=[Path(p) for p in args.rom],
            wo70017_tsv=tsv_list[0] if tsv_list else None,
        )
        atomic_write_json(Path(args.out), idx)
        print(f"Wrote reference index -> {args.out}")
    elif args.action == "query":
        idx = json.loads(Path(args.index).read_text(encoding="utf-8"))
        lookups = idx.get("lookups", {})
        res: Dict[str, object] = {}
        if args.addr:
            addr_int = _parse_hex_addr_flex(args.addr)
            norm = f"0x{addr_int:05X}" if addr_int is not None else args.addr
            res["address_hex"] = norm
            res["xml_hits"] = lookups.get("xml_by_addr", {}).get(norm, [])
            res["a2l_hits"] = lookups.get("a2l_by_addr", {}).get(norm, [])
        if args.ecuid:
            res["ecuid"] = args.ecuid
            res["xml_doc_ids"] = lookups.get("xml_by_ecuid", {}).get(args.ecuid, [])
        print(json.dumps(res, indent=2, sort_keys=True))


def cmd_export_xml(args):
    rom_bytes = load_any_rom(Path(args.rom)) if args.rom else None
    if args.catalogue:
        catalogue = json.loads(Path(args.catalogue).read_text(encoding="utf-8"))
    elif rom_bytes is not None:
        helpers = discover_helpers(rom_bytes)
        calls = extract_calls(rom_bytes, helpers)
        scan_doc = build_scan_export(args.rom, rom_bytes, helpers, calls)
        catalogue = to_per_address_catalogue(scan_doc)
        catalogue["implicit_grids"] = {f"0x{k:05X}": v for k, v in extract_implicit_grids(rom_bytes, helpers).items()}
        if args.enhanced_window > 0:
            enh_calls = extract_calls_enhanced(rom_bytes, helpers, window_bytes=args.enhanced_window)
            catalogue["enhanced_call_comparison"] = compare_call_extractions(calls, enh_calls)
        if args.include_scalars:
            catalogue["scalar_candidates"] = discover_cal_scalars(rom_bytes, helpers, calls=calls)
    else:
        raise ValueError("Supply --rom or --catalogue")

    crossref = None
    if args.ref_index:
        ref_idx = json.loads(Path(args.ref_index).read_text(encoding="utf-8"))
        crossref = match_target_against_index(catalogue, ref_idx, target_rom=rom_bytes)

    el_ctx = None
    if args.index_dir and rom_bytes is not None:
        el_ctx = load_hash_validated_el19a_context(
            rom_bytes,
            expected_rom_sha256=args.expected_el19a_sha256,
            index_dir=Path(args.index_dir),
        )

    resolution = resolve_candidate_evidence(catalogue, crossref)
    result = write_preview_bundle(
        Path(args.out_dir),
        args.stem,
        catalogue,
        resolution,
        rom_bytes=rom_bytes,
        allow_provisional_donor_names=args.allow_provisional_donor_names,
        skip_trivial=args.skip_trivial,
        strict=not args.no_strict,
    )
    if el_ctx is not None:
        print(f"EL19A INDEX adapter: status={el_ctx['status']} ({el_ctx['reason']})")
    print(
        f"Exported preview XML ({result['validation']['summary']['table_count']} tables, "
        f"valid={result['validation']['valid']}) -> {result['xml_path']}"
    )


def main():
    ap = argparse.ArgumentParser(description="Nissan SH7055/SH7058 Reverse-Engineering Workbench")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_scan = sub.add_parser("scan", help="Scan any .bin/.zip/.s19/.hex/.dat ROM for lookup helpers and tables")
    p_scan.add_argument("rom")
    p_scan.add_argument("--tsv", help="Optional output TSV path")
    p_scan.add_argument("--json", help="Optional output JSON path")
    p_scan.add_argument("--catalogue", help="Optional Milestone 2 lossless per-address catalogue JSON path")
    p_scan.add_argument("--manifest", help="Optional Milestone 2 run-manifest JSON path")
    p_scan.add_argument("--enhanced-window", type=int, default=0, help="Opt-in enhanced call extraction window (bytes)")
    p_scan.add_argument("--include-scalars", action="store_true", help="Include separate scalar calibration candidate discovery")
    p_scan.set_defaults(func=cmd_scan)

    for name in ("audit", "inspect"):
        p_sub = sub.add_parser(name, help="Audit EL19A or inspect a table/function/RAM address")
        if name == "audit":
            p_sub.add_argument("--el19a", default="EVIDENCE/VERSA f501.bin")
            p_sub.add_argument("--tsv", help="Optional enriched TSV export path")
            p_sub.add_argument("--matrix-r1", help="Optional additional scope matrix CSV for dual-matrix reconciliation")
            p_sub.add_argument("--extra-xml", nargs="*", default=[], help="Optional extra XML definitions to reconcile")
            p_sub.add_argument("--candidate-csv", help="Optional candidate_register.csv path")
            p_sub.add_argument("--reconcile-json", help="Optional atomic multi-source reconciliation JSON path")
        else:
            p_sub.add_argument("target", help="Hex address of table (0x0FEE0), function (0x6B168), or RAM (0xFFFF85DA)")
            p_sub.add_argument("--rom", default="EVIDENCE/VERSA f501.bin")
        p_sub.add_argument("--index-dir", help="Optional hash-validated prebuilt EL19A INDEX directory")
        p_sub.add_argument("--expected-el19a-sha256", default=EL19A_PINNED_SHA256)
        p_sub.add_argument("--xml", default="CALIBRATIONS/EL19A_release1_conservative.xml")
        p_sub.add_argument("--catalog", default="CALIBRATIONS/discovered_tables_catalog.csv")
        p_sub.add_argument("--matrix", default="CALIBRATIONS/RELEASE1_SCOPE_MATRIX_R1.csv")
        p_sub.add_argument("--el13a", default="EVIDENCE/23710-EL13A-08-C11-MR18DE-CVT.bin")
        p_sub.add_argument("--w83b", default="EVIDENCE/23710-8W83B-08-C11-MR18DE-AT.bin")
        p_sub.add_argument("--ee310", default="EVIDENCE/23710-EE310-07-C11-MR18DE-MT.bin")
        p_sub.add_argument("--v6-hex", default="EVIDENCE/side project/64810223F121200000.hex")
        p_sub.add_argument("--v6-a2l", default="EVIDENCE/side project/64811000p2_m.a2l")
        p_sub.add_argument("--juke-s19", default="EVIDENCE/Nissan Juke 1.6-dig-T S19 (9APCTDEM06)/9APCTDEM06.s19")
        p_sub.add_argument("--juke-a2l", default="EVIDENCE/Nissan Juke 1.6-dig-T S19 (9APCTDEM06)/RFCC_2XHK19BDF1.a2l")
        p_sub.set_defaults(func=cmd_audit if name == "audit" else cmd_inspect)

    p_diff = sub.add_parser("diff", help="Diff lookup tables and raw scalars across two ROMs (.bin/.zip/.s19/.hex/.dat)")
    p_diff.add_argument("rom_a")
    p_diff.add_argument("rom_b")
    p_diff.add_argument("--xml", default="CALIBRATIONS/EL19A_release1_conservative.xml")
    p_diff.add_argument("--raw-limit", type=int, default=40, help="Max non-table raw diff clusters to display (0 = all)")
    p_diff.add_argument("--json-out", help="Optional structured diff JSON output path")
    p_diff.set_defaults(func=cmd_diff)

    p_ref = sub.add_parser("ref-index", help="Build or query standalone A2L/XML/ROM reference index")
    p_ref.add_argument("action", choices=["build", "query"])
    p_ref.add_argument("--out", help="Output reference index JSON path (build)")
    p_ref.add_argument("--index", help="Input reference index JSON path (query)")
    p_ref.add_argument("--a2l", nargs="*", default=[])
    p_ref.add_argument("--tsv", nargs="*", default=[])
    p_ref.add_argument("--xml", nargs="*", default=[])
    p_ref.add_argument("--rom", nargs="*", default=[])
    p_ref.add_argument("--addr", help="Target hex address to query")
    p_ref.add_argument("--ecuid", help="Target ECU ID to query")
    p_ref.set_defaults(func=cmd_ref_index)

    p_exp = sub.add_parser("export-xml", help="Resolve evidence and export preview-first RomRaider XML bundle")
    p_exp.add_argument("--rom", help="Target ROM path (.bin/.zip/.s19/.hex/.dat)")
    p_exp.add_argument("--catalogue", help="Precomputed Milestone 2 per-address catalogue JSON")
    p_exp.add_argument("--ref-index", help="Optional Milestone 3 reference index JSON")
    p_exp.add_argument("--out-dir", required=True, help="Output directory (never CALIBRATIONS/)")
    p_exp.add_argument("--stem", required=True, help="Output filename stem")
    p_exp.add_argument("--enhanced-window", type=int, default=0)
    p_exp.add_argument("--include-scalars", action="store_true")
    p_exp.add_argument("--allow-provisional-donor-names", action="store_true")
    p_exp.add_argument("--skip-trivial", action="store_true")
    p_exp.add_argument("--no-strict", action="store_true")
    p_exp.add_argument("--index-dir", help="Optional hash-validated prebuilt EL19A INDEX directory")
    p_exp.add_argument("--expected-el19a-sha256", default=EL19A_PINNED_SHA256)
    p_exp.set_defaults(func=cmd_export_xml)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
