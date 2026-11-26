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

from sh7058_cross_rom_scanner import discover_helpers, extract_calls, load_xml_tables  # noqa: E402


# ---------------------------------------------------------------------------
# Unified ROM & A2L / Repository Metadata Loaders
# ---------------------------------------------------------------------------

def load_s19_bytes(raw: bytes) -> bytes:
    max_addr = 0x100000
    recs = []
    for line in raw.decode("ascii", errors="ignore").splitlines():
        if len(line) >= 4 and line[0] == "S" and line[1] in ("1", "2", "3"):
            alen = {"1": 4, "2": 6, "3": 8}[line[1]]
            cnt = int(line[2:4], 16)
            addr = int(line[4 : 4 + alen], 16)
            data = bytes.fromhex(line[4 + alen : 2 + cnt * 2])
            if addr + len(data) <= 0x200000:
                max_addr = max(max_addr, addr + len(data))
                recs.append((addr, data))
    buf = bytearray([0xFF] * max_addr)
    for addr, data in recs:
        buf[addr : addr + len(data)] = data
    return bytes(buf)


def load_hex_bytes(raw: bytes) -> bytes:
    buf = bytearray([0xFF] * 0x100000)
    upper = 0
    for line in raw.decode("ascii", errors="ignore").splitlines():
        if not line.startswith(":"):
            continue
        cnt = int(line[1:3], 16)
        addr = int(line[3:7], 16)
        rt = int(line[7:9], 16)
        data = bytes.fromhex(line[9 : 9 + 2 * cnt])
        if rt == 0:
            full = upper + addr
            if full + len(data) <= len(buf):
                buf[full : full + len(data)] = data
        elif rt == 4:
            upper = int.from_bytes(data, "big") << 16
        elif rt == 2:
            upper = int.from_bytes(data, "big") << 4
    return bytes(buf)


def _rol16(v: int, k: int) -> int:
    return ((v << k) | (v >> (16 - k))) & 0xFFFF


def decrypt_consult_dat_word(c: int) -> int:
    """Invert Nissan Consult .dat 2-round 16-bit Feistel ECB cipher on one 32-bit BE word."""
    ch, cl = (c >> 16) & 0xFFFF, c & 0xFFFF
    a = (cl + 0xCA1B) & 0xFFFF
    z = (a + _rol16(a, 1) + 0xFFFF) & 0xFFFF
    r0 = ch ^ (z ^ _rol16(z, 4))
    b = (r0 + 0x124D) & 0xFFFF
    f1 = (b + _rol16(b, 2) + 0xFFFF) & 0xFFFF
    l0 = cl ^ f1
    return (l0 << 16) | r0


def load_dat_bytes(raw: bytes) -> bytes:
    """Unpack and decrypt a Nissan Consult .dat reprogramming container into a raw SH705x image."""
    pos = raw.find(b"\x80\x15\xfc", 0, 0x200)
    if pos == -1:
        pos = 0x43
    recs: List[Tuple[int, bytes]] = []
    max_end = 0x80000
    n_frames = 0
    while pos + 11 <= len(raw) and raw[pos : pos + 2] == b"\x80\x15":
        kwp_len = raw[pos + 3]
        frame_len = 4 + kwp_len + 1
        if pos + frame_len > len(raw):
            raise ValueError(f"Truncated Consult .dat frame at 0x{pos:X}")
        blk = raw[pos : pos + frame_len]
        if (sum(blk[:-1]) & 0xFF) != blk[-1]:
            raise ValueError(f"Consult .dat frame checksum mismatch at 0x{pos:X}")
        if blk[4:6] != b"\x34\x82":
            raise ValueError(f"Unexpected Consult .dat frame command {blk[4:6].hex()} at 0x{pos:X}")
        addr = int.from_bytes(blk[6:9], "big")
        plen = blk[9]
        if plen % 4 != 0 or 10 + plen > frame_len - 1:
            raise ValueError(f"Invalid Consult .dat payload length {plen} at 0x{pos:X}")
        enc = blk[10 : 10 + plen]
        dec = bytearray(plen)
        for off in range(0, plen, 4):
            w = struct.unpack_from(">I", enc, off)[0]
            struct.pack_into(">I", dec, off, decrypt_consult_dat_word(w))
        recs.append((addr, bytes(dec)))
        if addr + plen > max_end:
            max_end = 0x100000 if addr + plen <= 0x100000 else addr + plen
        pos += frame_len
        n_frames += 1
    if n_frames == 0:
        raise ValueError("No valid Consult .dat 0x8015 transfer frames found")
    buf = bytearray([0xFF] * max_end)
    for addr, dec in recs:
        buf[addr : addr + len(dec)] = dec
    return bytes(buf)


def load_any_rom(path: Path) -> bytes:
    suf = path.suffix.lower()
    if suf == ".zip":
        with zipfile.ZipFile(path) as zf:
            members = [m for m in zf.infolist() if not m.is_dir()]
            if not members:
                raise ValueError(f"Empty zip archive: {path}")
            pref = [m for m in members if m.filename.lower().endswith((".bin", ".s19", ".hex", ".dat"))]
            target = max(pref or members, key=lambda m: m.file_size)
            raw = zf.read(target.filename)
            inner_suf = Path(target.filename).suffix.lower()
            if inner_suf == ".s19":
                return load_s19_bytes(raw)
            if inner_suf == ".hex":
                return load_hex_bytes(raw)
            if inner_suf == ".dat":
                return load_dat_bytes(raw)
            return raw
    raw = path.read_bytes()
    if suf == ".s19":
        return load_s19_bytes(raw)
    if suf == ".hex":
        return load_hex_bytes(raw)
    if suf == ".dat":
        return load_dat_bytes(raw)
    return raw


def rom_fingerprint(rom: bytes) -> dict:
    reset_pc = struct.unpack_from(">I", rom, 0)[0] if len(rom) >= 8 else 0
    reset_sp = struct.unpack_from(">I", rom, 4)[0] if len(rom) >= 8 else 0
    cpu_tags = sorted({m.group().decode() for m in re.finditer(rb"SH70[0-9A-Z]{2,6}", rom)})
    # Common Nissan FID tags (8 hex/alpha starting with digit, near ASCII strings)
    fid_tags = []
    for m in re.finditer(rb"[0-9][A-Z0-9]{7}", rom[: min(len(rom), 0x40000)]):
        s = m.group().decode()
        if any(c.isalpha() for c in s) and not s.startswith("SH70") and s not in fid_tags:
            fid_tags.append(s)
    # Trim trailing 0xFF region end
    active_end = len(rom)
    while active_end > 0x10000 and rom[active_end - 0x10000 : active_end] == b"\xff" * 0x10000:
        active_end -= 0x10000
    return {
        "size": len(rom),
        "active_end": active_end,
        "md5": hashlib.md5(rom).hexdigest(),
        "sha256": hashlib.sha256(rom).hexdigest(),
        "reset_pc": reset_pc,
        "reset_sp": reset_sp,
        "cpu_tags": cpu_tags[:6],
        "fid_tags": fid_tags[:8],
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

    # Annotate clusters using table/axis spans and 32-bit literal pool references
    table_ranges = [(a, ent["end"], ent) for a, ent in sorted(ta.items())]
    axis_addrs: Dict[int, List[int]] = {}
    for a, ent in ta.items():
        for ax in ent["axis1s"] + ent["axis2s"]:
            axis_addrs.setdefault(ax, []).append(a)
    pool32 = _build_pool32_index(ra)

    max_show = len(clusters) if args.raw_limit == 0 else args.raw_limit
    print(f"Non-table raw diff clusters (showing {min(len(clusters), max_show)}/{len(clusters)}):")
    for s, e in clusters[:max_show]:
        ba, bb = ra[s : e + 1], rb[s : e + 1]
        val_txt = _format_cluster_values(ba, bb, s)
        notes = []
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


def main():
    ap = argparse.ArgumentParser(description="Nissan SH7055/SH7058 Reverse-Engineering Workbench")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_scan = sub.add_parser("scan", help="Scan any .bin/.zip/.s19/.hex/.dat ROM for lookup helpers and tables")
    p_scan.add_argument("rom")
    p_scan.add_argument("--tsv", help="Optional output TSV path")
    p_scan.add_argument("--json", help="Optional output JSON path")
    p_scan.set_defaults(func=cmd_scan)

    for name in ("audit", "inspect"):
        p_sub = sub.add_parser(name, help="Audit EL19A or inspect a table/function/RAM address")
        if name == "audit":
            p_sub.add_argument("--el19a", default="EVIDENCE/VERSA f501.bin")
            p_sub.add_argument("--tsv", help="Optional enriched TSV export path")
        else:
            p_sub.add_argument("target", help="Hex address of table (0x0FEE0), function (0x6B168), or RAM (0xFFFF85DA)")
            p_sub.add_argument("--rom", default="EVIDENCE/VERSA f501.bin")
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
    p_diff.set_defaults(func=cmd_diff)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
