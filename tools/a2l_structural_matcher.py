#!/usr/bin/env python3
"""
Structural Function, Helper-Signature & A2L RAM/Table Matcher for Nissan SH7058 ROMs.

Compares EL19A caller subroutines (`VERSA f501.bin`) against two A2L-backed ROM pairs
already in EVIDENCE/:
  - V6 `64810223F121200000.hex` + `64811000p2_m.a2l` (SH705822N — same core generation as EL19A)
  - Juke `9APCTDEM06.s19` + `RFCC_2XHK19BDF1.a2l` (SH705828N)

IMPORTANT EVIDENCE POLICY:
  A2L matches (table CHARACTERISTICs/AXIS_PTS and RAM MEASUREMENTs) are *structural leads*
  only, never target-side proof. Every lead still requires EL19A reader/consumer verification.
"""
import argparse
import bisect
import hashlib
import re
import struct
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from sh7058_cross_rom_scanner import discover_helpers, extract_calls, load_xml_tables


def load_s19(path: Path) -> bytes:
    buf = bytearray([0xFF] * 0x100000)
    for line in path.read_text(errors="ignore").splitlines():
        if len(line) >= 4 and line[0] == "S" and line[1] in ("1", "2", "3"):
            alen = {"1": 4, "2": 6, "3": 8}[line[1]]
            cnt = int(line[2:4], 16)
            addr = int(line[4 : 4 + alen], 16)
            data = bytes.fromhex(line[4 + alen : 2 + cnt * 2])
            if addr + len(data) <= len(buf):
                buf[addr : addr + len(data)] = data
    return bytes(buf)


def load_hex(path: Path) -> bytes:
    buf = bytearray([0xFF] * 0x100000)
    upper = 0
    for line in path.read_text(errors="ignore").splitlines():
        if not line.startswith(":"):
            continue
        cnt = int(line[1:3], 16)
        addr = int(line[3:7], 16)
        rt = int(line[7:9], 16)
        data = bytes.fromhex(line[9 : 9 + 2 * cnt])
        if rt == 0 and upper + addr + len(data) <= len(buf):
            buf[upper + addr : upper + addr + len(data)] = data
        elif rt == 4:
            upper = int.from_bytes(data, "big") << 16
        elif rt == 2:
            upper = int.from_bytes(data, "big") << 4
    return bytes(buf)


def parse_a2l(path: Path) -> Tuple[Dict[int, Tuple[str, str, str]], Dict[int, Tuple[str, str]]]:
    txt = path.read_bytes().decode("cp932", errors="replace")
    syms: Dict[int, Tuple[str, str, str]] = {}
    for kind in ("CHARACTERISTIC", "AXIS_PTS"):
        for blk in txt.split(f"/begin {kind} ")[1:]:
            end = blk.find(f"/end {kind}")
            body = (blk[:end] if end != -1 else blk).lstrip()
            hm = re.match(r"(\S+)\s+\"([^\"]*)\"", body)
            am = re.search(r"\b0x([0-9A-Fa-f]+)\b", body)
            if hm and am:
                syms[int(am.group(1), 16)] = (hm.group(1), hm.group(2), kind)
    meas: Dict[int, Tuple[str, str]] = {}
    for blk in txt.split("/begin MEASUREMENT ")[1:]:
        end = blk.find("/end MEASUREMENT")
        body = (blk[:end] if end != -1 else blk).lstrip()
        hm = re.match(r"(\S+)\s+\"([^\"]*)\"", body)
        am = re.search(r"ECU_ADDRESS\s+0x([0-9A-Fa-f]+)", body)
        if hm and am:
            meas[int(am.group(1), 16)] = (hm.group(1), hm.group(2))
    return syms, meas


def norm_sym(name: str) -> str:
    """Normalize minor variant suffixes (e.g. mTQH0ST_S vs mTTQH0ST) for consensus comparison."""
    s = re.sub(r"(_S|_2|#\d+)$", "", name or "")
    if s.startswith("mTT"):
        s = "mT" + s[3:]
    return s


def build_func_profiles(rom: bytes, calls: List[dict], syms=None, meas=None) -> Dict[int, dict]:
    prologues = [pc for pc in range(0x20000, len(rom) - 2, 2) if struct.unpack_from(">H", rom, pc)[0] == 0x4F22]
    by_fn = defaultdict(list)
    for c in calls:
        idx = bisect.bisect_right(prologues, c["call_pc"]) - 1
        fn_start = prologues[idx] if idx >= 0 and (c["call_pc"] - prologues[idx]) < 0x1000 else (c["call_pc"] & ~0xFF)
        by_fn[fn_start].append(c)

    profiles = {}
    for fn_start, cs in by_fn.items():
        cs_sorted = sorted(cs, key=lambda x: x["call_pc"])
        idx = bisect.bisect_right(prologues, fn_start)
        fn_end = min(fn_start + 0xB00, prologues[idx] if idx < len(prologues) else len(rom))
        tbl_set = {c["table"] for c in cs_sorted if c["table"]} | {c["axis1"] for c in cs_sorted if c["axis1"]} | {c["axis2"] for c in cs_sorted if c["axis2"]}

        ram_refs: List[int] = []
        cal_vals = set()
        imms = set()
        sub_calls = 0
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
            elif top == 0xB or (w & 0xF0FF) == 0x400B:
                sub_calls += 1

        sig = tuple((c["kind"], c["dim1"], c["dim2"], c["elem_type"]) for c in cs_sorted)
        payloads = []
        for c in cs_sorted:
            t = c["table"]
            if t is not None:
                sz = c["dim1"] * c["dim2"] * (2 if "16" in c["elem_type"] else 1)
                b = rom[t : t + sz]
                payloads.append(b if len(set(b)) > 2 else None)
            else:
                payloads.append(None)

        tbl_entries = []
        for c in cs_sorted:
            t = c["table"]
            sym = syms[t][0] if (syms and t in syms) else None
            ax1_sym = syms[c["axis1"]][0] if (syms and c["axis1"] in syms) else None
            ax2_sym = syms[c["axis2"]][0] if (syms and c["axis2"] in syms) else None
            tbl_entries.append({
                "table": t,
                "sym": sym,
                "ax1_sym": ax1_sym,
                "ax2_sym": ax2_sym,
                "sig": (c["kind"], c["dim1"], c["dim2"], c["elem_type"]),
            })

        profiles[fn_start] = {
            "start": fn_start,
            "len": fn_end - fn_start,
            "calls": cs_sorted,
            "sig": sig,
            "sig_bag": tuple(sorted(sig)),
            "payloads": payloads,
            "cal_vals": cal_vals,
            "imms": imms,
            "sub_calls": sub_calls,
            "ram_names": [meas[r][0] for r in dict.fromkeys(ram_refs) if meas and r in meas],
            "tbl_entries": tbl_entries,
        }
    return profiles


def score_pair(el_pr: dict, cand: dict) -> Tuple[int, dict]:
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
    return score, {"n_pay": n_pay, "exact_order": exact_order, "cal_ov": cal_ov, "imm_ov": imm_ov, "len_diff": len_diff}


def main():
    ap = argparse.ArgumentParser(description="Structural function & A2L RAM/table matcher for EL19A")
    ap.add_argument("--el19a", default="EVIDENCE/VERSA f501.bin")
    ap.add_argument("--xml", default="CALIBRATIONS/EL19A_release1_conservative.xml")
    ap.add_argument("--v6-hex", default="EVIDENCE/side project/64810223F121200000.hex")
    ap.add_argument("--v6-a2l", default="EVIDENCE/side project/64811000p2_m.a2l")
    ap.add_argument("--juke-s19", default="EVIDENCE/Nissan Juke 1.6-dig-T S19 (9APCTDEM06)/9APCTDEM06.s19")
    ap.add_argument("--juke-a2l", default="EVIDENCE/Nissan Juke 1.6-dig-T S19 (9APCTDEM06)/RFCC_2XHK19BDF1.a2l")
    args = ap.parse_args()

    el = Path(args.el19a).read_bytes()
    v6 = load_hex(Path(args.v6_hex))
    jk = load_s19(Path(args.juke_s19))
    xml_tables = load_xml_tables(Path(args.xml))

    v6_syms, v6_meas = parse_a2l(Path(args.v6_a2l))
    jk_syms, jk_meas = parse_a2l(Path(args.juke_a2l))

    el_c = extract_calls(el, discover_helpers(el))
    v6_c = extract_calls(v6, discover_helpers(v6))
    jk_c = extract_calls(jk, discover_helpers(jk))

    el_p = build_func_profiles(el, el_c)
    v6_p = build_func_profiles(v6, v6_c, v6_syms, v6_meas)
    jk_p = build_func_profiles(jk, jk_c, jk_syms, jk_meas)

    v6_by_bag = defaultdict(list)
    for pr in v6_p.values():
        v6_by_bag[pr["sig_bag"]].append(pr)
    jk_by_bag = defaultdict(list)
    for pr in jk_p.values():
        jk_by_bag[pr["sig_bag"]].append(pr)

    # Also build per-table non-trivial payload A2L index for 1-call / fallback cross-reference
    v6_pay = defaultdict(list)
    jk_pay = defaultdict(list)
    for pr in v6_p.values():
        for c, te in zip(pr["calls"], pr["tbl_entries"]):
            if c["table"]:
                sz = c["dim1"] * c["dim2"] * (2 if "16" in c["elem_type"] else 1)
                b = v6[c["table"] : c["table"] + sz]
                if len(set(b)) > 2 and te["sym"]:
                    v6_pay[b].append((te["sym"], pr["start"]))
    for pr in jk_p.values():
        for c, te in zip(pr["calls"], pr["tbl_entries"]):
            if c["table"]:
                sz = c["dim1"] * c["dim2"] * (2 if "16" in c["elem_type"] else 1)
                b = jk[c["table"] : c["table"] + sz]
                if len(set(b)) > 2 and te["sym"]:
                    jk_pay[b].append((te["sym"], pr["start"]))

    print(f"=== Structural A2L Matcher Summary ===")
    print(f"EL19A: {len(el_p)} caller functions | V6 (SH705822N): {len(v6_p)} functions, {len(v6_syms)} syms, {len(v6_meas)} RAM | Juke (SH705828N): {len(jk_p)} functions, {len(jk_syms)} syms, {len(jk_meas)} RAM")

    high_conf_fn = []
    for fn, pr in sorted(el_p.items()):
        bag = pr["sig_bag"]
        vm = sorted([(score_pair(pr, x)[0], score_pair(pr, x)[1], x) for x in v6_by_bag.get(bag, [])], key=lambda t: -t[0])
        jm = sorted([(score_pair(pr, x)[0], score_pair(pr, x)[1], x) for x in jk_by_bag.get(bag, [])], key=lambda t: -t[0])

        # Strong structural match criteria:
        #   - unique or low-multiplicity bag (len(vm) <= 3 or len(jm) <= 3) with >=2 calls, OR
        #   - unique 1-call rare signature (<=3 hits in V6/Juke), OR
        #   - at least one non-trivial payload match inside matching bag
        is_multi = len(bag) >= 2
        rare_v = 0 < len(vm) <= 3
        rare_j = 0 < len(jm) <= 3
        has_pay = (vm and vm[0][1]["n_pay"] > 0) or (jm and jm[0][1]["n_pay"] > 0)
        if (is_multi and (rare_v or rare_j)) or (not is_multi and ((len(vm) == 1) or (0 < len(jm) <= 2))) or has_pay:
            high_conf_fn.append((fn, pr, vm, jm))

    print(f"\nHigh-specificity structural function matches: {len(high_conf_fn)} / {len(el_p)} EL19A functions\n")

    dual_consensus = []
    uncat_leads = []
    for fn, pr, vm, jm in high_conf_fn:
        v_top = vm[0] if vm else None
        j_top = jm[0] if jm else None
        # Check if V6 and Juke agree on table symbol roots (positional or multiset)
        consensus = False
        if v_top and j_top:
            v_roots = {norm_sym(e["sym"]) for e in v_top[2]["tbl_entries"] if e["sym"]}
            j_roots = {norm_sym(e["sym"]) for e in j_top[2]["tbl_entries"] if e["sym"]}
            if v_roots & j_roots:
                consensus = True
        el_tbls = [f"0x{c['table']:05X}{'*' if c['table'] not in xml_tables else ''}" if c["table"] else "None" for c in pr["calls"]]
        has_uncat = any(c["table"] and c["table"] not in xml_tables for c in pr["calls"])
        if consensus:
            dual_consensus.append((fn, pr, v_top, j_top, el_tbls))
        if has_uncat:
            uncat_leads.append((fn, pr, v_top, j_top, el_tbls, consensus))

    print(f"--- Dual V6 (SH705822N) + Juke (SH705828N) Symbol-Root Consensus Functions: {len(dual_consensus)} ---")
    for fn, pr, v_top, j_top, el_tbls in dual_consensus:
        v_syms_str = [f"{e['sym'] or '?'}" for e in v_top[2]["tbl_entries"]]
        j_syms_str = [f"{e['sym'] or '?'}" for e in j_top[2]["tbl_entries"]]
        rams = (v_top[2]["ram_names"] + [r for r in j_top[2]["ram_names"] if r not in v_top[2]["ram_names"]])[:6]
        print(f"  EL19A fn 0x{fn:05X} tbls={el_tbls} (*=not in R1 XML)")
        print(f"    sig={pr['sig']}")
        print(f"    V6   fn 0x{v_top[2]['start']:05X} (score={v_top[0]}, pay={v_top[1]['n_pay']}, cal_ov={v_top[1]['cal_ov']}): {v_syms_str}")
        print(f"    Juke fn 0x{j_top[2]['start']:05X} (score={j_top[0]}, pay={j_top[1]['n_pay']}, cal_ov={j_top[1]['cal_ov']}): {j_syms_str}")
        if rams:
            print(f"    RAM leads: {rams}")

    print(f"\n--- Single-Source / Rare Structural Leads for Functions Containing Uncatalogued EL19A Tables (*): {len([x for x in uncat_leads if not x[5]])} ---")
    for fn, pr, v_top, j_top, el_tbls, cons in uncat_leads:
        if cons:
            continue
        print(f"  EL19A fn 0x{fn:05X} tbls={el_tbls} sig={pr['sig']}")
        if v_top:
            print(f"    V6   0x{v_top[2]['start']:05X} (n={len(v6_by_bag.get(pr['sig_bag'], []))}, pay={v_top[1]['n_pay']}, cal_ov={v_top[1]['cal_ov']}): {[e['sym'] or '?' for e in v_top[2]['tbl_entries']]} ram={v_top[2]['ram_names'][:5]}")
        if j_top:
            print(f"    Juke 0x{j_top[2]['start']:05X} (n={len(jk_by_bag.get(pr['sig_bag'], []))}, pay={j_top[1]['n_pay']}, cal_ov={j_top[1]['cal_ov']}): {[e['sym'] or '?' for e in j_top[2]['tbl_entries']]} ram={j_top[2]['ram_names'][:5]}")

    # Summary of table-level payload + helper matches not covered above
    seen_tbl = set()
    pay_rows = []
    for c in el_c:
        t = c["table"]
        if t is None or t in seen_tbl:
            continue
        seen_tbl.add(t)
        sz = c["dim1"] * c["dim2"] * (2 if "16" in c["elem_type"] else 1)
        b = el[t : t + sz]
        if len(set(b)) <= 2:
            continue
        vh = sorted({s for s, _ in v6_pay.get(b, [])})
        jh = sorted({s for s, _ in jk_pay.get(b, [])})
        if vh or jh:
            pay_rows.append((t, t not in xml_tables, f"{c['kind']} {c['dim1']}x{c['dim2']} {c['elem_type']}", vh, jh))
    print(f"\n--- Non-trivial EL19A caller-backed tables with exact V6/Juke payload+helper match: {len(pay_rows)} (uncatalogued={sum(1 for r in pay_rows if r[1])}) ---")
    for t, uncat, desc, vh, jh in pay_rows:
        if uncat:
            print(f"  0x{t:05X}* ({desc}): V6={vh[:3]} Juke={jh[:3]}")


if __name__ == "__main__":
    main()
