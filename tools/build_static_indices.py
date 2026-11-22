#!/usr/bin/env python3
"""
build_static_indices.py
Generates three machine-verified static indices in INDEX/ without modifying any immutable files:
  1. INDEX/wo65115_validation.tsv          (regression check against rom_access_indexer.py)
  2. INDEX/function_gbr_map.tsv            (all ldc Rm, gbr sites and resolved GBR bases per function)
  3. INDEX/catalog_179_consumer_summary.tsv (all 179 discovered_tables_catalog.csv rows -> query RAM,
                                             destination RAM, Mode $01 / Consult $22 cross-links,
                                             and downstream RAM readers)

Pure Python 3 stdlib only.
"""

import argparse
import csv
import hashlib
import os
import re
import struct
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import rom_access_indexer

EXPECTED_ROM_MD5 = "46991697c502052752a2cabcb84c9e27"
EXPECTED_LST_SHA256 = "148385bbec91f6a491dcaa403962836f709c2f273df9a17ec51f1dea5f7f4549"
HEX_CHARS = set("0123456789ABCDEFabcdef")
RE_CODE = re.compile(r"^([0-9A-Fa-f]{8})\s+([0-9A-Fa-f\s]{2,20})\s+CODE\s+([^\r\n;]+)(?:;\s*(.*))?$")
RE_LABEL = re.compile(r"^([a-zA-Z_][a-zA-Z0-9_]*):")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(1 << 20):
            h.update(chunk)
    return h.hexdigest()


def md5_file(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        while chunk := f.read(1 << 20):
            h.update(chunk)
    return h.hexdigest()


def sext8(v):
    return (v | 0xFFFFFF00) if (v & 0x80) else v


def sext16(v):
    return (v | 0xFFFF0000) if (v & 0x8000) else v


def fmt_addr(addr):
    if addr >= 0xFFFF0000:
        return f"FFFF{addr & 0xFFFF:04X}"
    return f"0x{addr:05X}"


def parse_listing(lst_path, rom):
    code_lines = []
    current_func = "unknown"
    current_label = "unknown"
    concordance_failures = 0

    with open(lst_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith("FFFF"):
                if s.startswith("FFFF"):
                    break
                continue
            m_lab = RE_LABEL.match(line)
            if m_lab:
                lbl = m_lab.group(1)
                current_label = lbl
                if lbl.startswith("sub_"):
                    current_func = lbl
                continue
            m_code = RE_CODE.match(line)
            if m_code:
                pc = int(m_code.group(1), 16)
                hb = bytes.fromhex(m_code.group(2).strip())
                if pc + len(hb) <= len(rom) and rom[pc : pc + len(hb)] != hb:
                    concordance_failures += 1
                instr = m_code.group(3).strip()
                comment = m_code.group(4).strip() if m_code.group(4) else ""
                code_lines.append((pc, hb, instr, comment, current_func, current_label))

    if concordance_failures:
        raise RuntimeError(f"Listing/ROM byte concordance failure count: {concordance_failures}")
    return code_lines


def run_wo65115_validation(rom_path, lst_path, out_path):
    targets = [
        ("0x388AC", "exact == 1"),
        ("0x8550", "exact == 1"),
        ("0xED64", "exact == 1"),
        ("0xEDA0", "exact == 1"),
        ("0xEE68", "exact == 1"),
        ("0xF01C", "exact == 1"),
        ("FFFF1DB4", "exact == 3 (r@4042C, w@4044A, r@4054A in sub_403D8)"),
        ("FFFF84BA", "exact == 129"),
        ("FFFF85DF", "exact == 3"),
        ("FFFF85E0", "exact == 0"),
    ]
    tfile = "/tmp/wo65115_val_targets.txt"
    hfile = "/tmp/wo65115_val_hits.tsv"
    ufile = "/tmp/wo65115_val_unres.tsv"
    with open(tfile, "w", encoding="utf-8") as f:
        for t, _ in targets:
            f.write(t + "\n")

    valid_hits, _, matched, checked = rom_access_indexer.run_indexer(rom_path, lst_path, tfile, hfile, ufile)
    by_target = {}
    for row in valid_hits:
        by_target.setdefault(row[0], []).append(row)

    out_rows = []
    all_pass = True
    expected_counts = {
        "0x388AC": 1, "0x8550": 1, "0xED64": 1, "0xEDA0": 1, "0xEE68": 1, "0xF01C": 1,
        "FFFF1DB4": 3, "FFFF84BA": 129, "FFFF85DF": 3, "FFFF85E0": 0,
    }
    for t, rule in targets:
        hits = by_target.get(t, [])
        ok = (len(hits) == expected_counts[t])
        if t == "FFFF1DB4" and ok:
            sig = {(h[2], h[3], h[4]) for h in hits}
            ok = sig == {("0x4042C", "sub_403D8", "read"), ("0x4044A", "sub_403D8", "write"), ("0x4054A", "sub_403D8", "read")}
        if not ok:
            all_pass = False
        sample = "; ".join(f"{h[2]}({h[3]}:{h[4]})" for h in hits[:6]) or "-"
        out_rows.append({
            "target": t,
            "expected_rule": rule,
            "actual_hits": len(hits),
            "status": "PASS" if ok else "FAIL",
            "concordance": f"{matched}/{checked}",
            "sample_hits": sample,
        })

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()), delimiter="\t")
        w.writeheader()
        w.writerows(out_rows)
    if not all_pass:
        raise RuntimeError(f"WO65115 validation failed! Check {out_path}")
    return out_rows


def build_semantics_map(outdir):
    """Loads proven Mode $01 + Consult $22 + verified core RAM semantics."""
    ram_sem = {
        "FFFF85DA": ["OBD_0x0C:RPM(12.5/LSB)"],
        "FFFF85B2": ["RPM_mirror(12.5/LSB)"],
        "FFFF8591": ["OBD_0x0D:VSS(km/h)"],
        "FFFF85CB": ["OBD_0x0E:Timing(deg)"],
        "FFFF99A4": ["OBD_0x0F:IAT(degC)"],
        "FFFF84A8": ["OBD_0x10:MAF(g/s)"],
        "FFFF84BD": ["OBD_0x11/0x45:TPS(%)"],
        "FFFF99B4": ["OBD_0x11(CAN):TPS_16b"],
        "FFFF99B8": ["OBD_0x47:TPS_B_16b"],
        "FFFF9932": ["OBD_0x49:APP_D_16b"],
        "FFFF9936": ["OBD_0x4A:APP_E_16b"],
        "FFFF3478": ["OBD_0x04(K):CalcLoad(%)"],
        "FFFF341C": ["OBD_0x04(CAN):CalcLoad(%)"],
        "FFFF349E": ["OBD_0x05(K):ECT(degC)"],
        "FFFF3442": ["OBD_0x05(CAN):ECT(degC)"],
        "FFFF84B8": ["NTC_AN27_rescaled(ECT)"],
        "FFFF84BF": ["NTC_AN31_rescaled(IAT)"],
        "FFFF13AA": ["OBD_0x0B:MAP(kPa)"],
        "FFFF1C6C": ["OBD_0x06/0x14:STFT_B1"],
        "FFFF1C82": ["OBD_0x07:LTFT_B1"],
        "FFFF1C6E": ["OBD_0x08/0x18:STFT_B2"],
        "FFFF1C84": ["OBD_0x09:LTFT_B2"],
        "FFFF847C": ["OBD_0x14/0x24:O2S11_V"],
        "FFFF85E8": ["OBD_0x14(CAN):O2S11_8b"],
        "FFFF858E": ["OBD_0x15:O2S12_8b"],
        "FFFF858A": ["OBD_0x42:BattV"],
        "FFFFB47A": ["OBD_0x33:Baro_kPa"],
        "FFFF1CC8": ["OBD_0x2E:EvapPurge(%)"],
        "FFFF33DE": ["OBD_0x44:CmdLambda"],
        "FFFF33E2": ["OBD_0x4C:CmdThrottleActuator"],
        "FFFF33FA": ["OBD_0x24:WBO2_Lambda"],
        "FFFF2832": ["OBD_0x3C:CatTemp_B1S1"],
        "FFFFA360": ["OBD_0x32:EvapVaporPress"],
        "FFFF8554": ["OBD_0x32:EvapVaporPress_alt"],
        "FFFF860D": ["OBD_0x43:AbsLoad_hi"],
        "FFFF84A4": ["OBD_0x43:AbsLoad_lo"],
    }

    m01_path = os.path.join(outdir, "obd_mode01_pid_map.tsv")
    if os.path.exists(m01_path):
        with open(m01_path, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f, delimiter="\t"):
                for col in ("kline_ram_sources", "can_ram_sources"):
                    for m in re.finditer(r"(FFFF[0-9A-F]{4})", r[col]):
                        a = m.group(1)
                        if a != "FFFFA074":
                            tag = f"OBD_{r['pid_hex']}:{r['sae_name']}"
                            ram_sem.setdefault(a, [])
                            if tag not in ram_sem[a]:
                                ram_sem[a].append(tag)

    c22_path = os.path.join(outdir, "consult_mode22_pid_map.tsv")
    if os.path.exists(c22_path):
        with open(c22_path, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f, delimiter="\t"):
                p1 = r["ptr1_addr"]
                if p1.startswith("FFFF") and p1 != "FFFFFFFF":
                    tag = f"C22_{r['cid_hex']}"
                    ram_sem.setdefault(p1, [])
                    if tag not in ram_sem[p1]:
                        ram_sem[p1].append(tag)
    return ram_sem


def full_rom_analysis(code_lines, rom, catalog_rows, mmio_addrs):
    """
    Single full-pass SH-2 tracker collecting:
      1. function_gbr_map events (ldc Rm, gbr)
      2. ram_readers[ea] / ram_writers[ea] for downstream consumer counting
      3. catalog_trace[table_addr] -> query_inputs, dest_ram writes (tainted r0 propagation)
    """
    cat_addrs = {int(r["address"], 16) for r in catalog_rows}

    gbr_events = []
    ram_readers = {}   # ea -> set of (pc, func)
    ram_writers = {}   # ea -> set of (pc, func)
    cat_calls = {}     # table_addr -> list of dicts

    regs = [None] * 16
    reg_mem_src = [None] * 16   # last RAM ea loaded into reg[i]
    reg_taint = [None] * 16     # None or (table_addr, call_pc)
    gbr = None
    cur_func = None
    prev_label = None
    in_delay = False
    pending_call_clobber = False
    active_lookup_call = None   # (table_addr, call_pc, helper_name, q_inputs, ttl)

    for idx, (pc, hb, instr, comment, func, lbl) in enumerate(code_lines):
        op = int.from_bytes(hb[:2], "big")
        hi = (op >> 12) & 0xF
        n = (op >> 8) & 0xF
        m = (op >> 4) & 0xF
        disp = op & 0xFF
        disp4 = op & 0xF

        if func != cur_func:
            cur_func = func
            regs = [None] * 16
            reg_mem_src = [None] * 16
            reg_taint = [None] * 16
            gbr = None
            prev_label = lbl
            in_delay = False
            pending_call_clobber = False
            active_lookup_call = None
        elif lbl != prev_label and not in_delay:
            prev_label = lbl
            for r in range(8):
                regs[r] = None
                reg_mem_src[r] = None

        # 1. Detect GBR loads: ldc Rm, gbr -> 0x4m1E (opcode bits: 0100 mmmm 0001 1110 -> n holds Rm in SH encoding!)
        if (op & 0xF0FF) == 0x401E:
            base_val = regs[n]
            space = "UNRESOLVED"
            if base_val is not None:
                if base_val >= 0xFFFFD800:
                    space = "MMIO"
                elif base_val >= 0xFFFF0000:
                    space = "RAM"
                elif base_val < len(rom):
                    space = "ROM"
                else:
                    space = "OTHER"
            gbr_events.append({
                "function": cur_func,
                "pc": f"0x{pc:05X}",
                "src_reg": f"r{n}",
                "gbr_base": fmt_addr(base_val) if base_val is not None else "UNRESOLVED",
                "space": space,
                "instruction": instr,
            })

        # 2. Decode memory access (read or write) and src value register if write
        ea = None
        acc = None
        width = None
        val_reg = None

        if hi == 0x0:
            if disp4 in (0xC, 0xD, 0xE) and regs[m] is not None and regs[0] is not None:
                ea = (regs[m] + regs[0]) & 0xFFFFFFFF
                acc = "read"
                width = "b" if disp4 == 0xC else ("w" if disp4 == 0xD else "l")
            elif disp4 in (0x4, 0x5, 0x6) and regs[n] is not None and regs[0] is not None:
                ea = (regs[n] + regs[0]) & 0xFFFFFFFF
                acc = "write"
                width = "b" if disp4 == 0x4 else ("w" if disp4 == 0x5 else "l")
                val_reg = m
        elif hi == 0x1 and regs[n] is not None:
            ea = (regs[n] + disp4 * 4) & 0xFFFFFFFF
            acc, width, val_reg = "write", "l", m
        elif hi == 0x5 and regs[m] is not None:
            ea = (regs[m] + disp4 * 4) & 0xFFFFFFFF
            acc, width = "read", "l"
        elif hi == 0x8:
            sub_op = (op >> 8) & 0xF
            reg_4 = (op >> 4) & 0xF
            if sub_op in (0x0, 0x1) and regs[reg_4] is not None:
                scale = 1 if sub_op == 0 else 2
                ea = (regs[reg_4] + disp4 * scale) & 0xFFFFFFFF
                acc, width, val_reg = "write", ("b" if scale == 1 else "w"), 0
            elif sub_op in (0x4, 0x5) and regs[reg_4] is not None:
                scale = 1 if sub_op == 4 else 2
                ea = (regs[reg_4] + disp4 * scale) & 0xFFFFFFFF
                acc, width = "read", ("b" if scale == 1 else "w")
        elif hi == 0x2 and disp4 in (0, 1, 2) and regs[n] is not None:
            ea = regs[n]
            acc = "write"
            width = "b" if disp4 == 0 else ("w" if disp4 == 1 else "l")
            val_reg = m
        elif hi == 0x6 and disp4 in (0, 1, 2) and regs[m] is not None:
            ea = regs[m]
            acc = "read"
            width = "b" if disp4 == 0 else ("w" if disp4 == 1 else "l")
        elif hi == 0xC and gbr is not None:
            sub_op = (op >> 8) & 0xF
            if sub_op in (0x0, 0x1, 0x2):
                scale = 1 if sub_op == 0 else (2 if sub_op == 1 else 4)
                ea = (gbr + disp * scale) & 0xFFFFFFFF
                acc, width, val_reg = "write", ("b" if scale == 1 else ("w" if scale == 2 else "l")), 0
            elif sub_op in (0x4, 0x5, 0x6):
                scale = 1 if sub_op == 4 else (2 if sub_op == 5 else 4)
                ea = (gbr + disp * scale) & 0xFFFFFFFF
                acc, width = "read", ("b" if scale == 1 else ("w" if scale == 2 else "l"))
            elif sub_op in (0xC, 0xD, 0xE, 0xF) and regs[0] is not None:
                ea = (gbr + regs[0]) & 0xFFFFFFFF
                acc = "read" if sub_op == 0xC else "rmw"
                width = "b"

        if ea is not None and 0xFFFF0000 <= ea <= 0xFFFFD7FF:
            if acc == "read":
                ram_readers.setdefault(ea, []).append((pc, cur_func))
            else:
                ram_writers.setdefault(ea, []).append((pc, cur_func))

            # If storing a tainted lookup value (or first RAM write shortly after lookup), record destination!
            if acc in ("write", "rmw") and active_lookup_call is not None:
                t_addr, c_pc, h_name, q_inputs, ttl = active_lookup_call
                is_tainted = (val_reg is not None and reg_taint[val_reg] == (t_addr, c_pc))
                if is_tainted:
                    cat_calls[t_addr][-1]["dests"].append((ea, width, pc, instr, True))
                elif not cat_calls[t_addr][-1]["dests"] and ttl >= 22:
                    # Fallback if helper value flowed through unmodeled op (e.g. clamp call)
                    cat_calls[t_addr][-1]["dests"].append((ea, width, pc, instr, False))

        # Inline ROM table read: mov.x @(r0, Rm), Rn where regs[m] in cat_addrs
        if hi == 0x0 and disp4 in (0xC, 0xD, 0xE) and regs[m] in cat_addrs:
            t_addr = regs[m]
            q_in = []
            if reg_mem_src[0] is not None:
                q_in.append(f"r0<-{fmt_addr(reg_mem_src[0])}")
            rec = {
                "reader_pc": pc,
                "func": cur_func,
                "helper": "inline",
                "q_inputs": q_in,
                "dests": [],
            }
            cat_calls.setdefault(t_addr, []).append(rec)
            active_lookup_call = (t_addr, pc, "inline", q_in, 28)
            reg_taint[n] = (t_addr, pc)

        # Detect table lookup call (jsr @Rm or bsr) when r4 holds a catalog table address
        called_lookup = False
        if (hi == 0xB) or (hi == 0x4 and (op & 0xFF) == 0x0B):
            if regs[4] in cat_addrs:
                h_name = comment.split()[0] if comment else "helper"
                # Wait 1 delay slot so r5/r6 loaded in delay slot are captured!
                called_lookup = (regs[4], pc, h_name)

        if active_lookup_call is not None:
            t_addr, c_pc, h_name, q_inputs, ttl = active_lookup_call
            if ttl <= 1 or op in (0x000B, 0x002B):
                active_lookup_call = None
            else:
                active_lookup_call = (t_addr, c_pc, h_name, q_inputs, ttl - 1)

        # Track register state + memory-source provenance + taint propagation
        in_delay = False
        src_mem = None
        if acc == "read" and ea is not None and 0xFFFF0000 <= ea <= 0xFFFFD7FF:
            src_mem = ea

        if (op & 0xF0FF) == 0x401E:
            gbr = regs[n]
        elif (op & 0xF0FF) == 0x0012:
            regs[n] = gbr
            reg_mem_src[n] = None
            reg_taint[n] = None
        elif hi == 0x9:
            pool_ea = pc + 4 + disp * 2
            regs[n] = sext16(struct.unpack(">H", rom[pool_ea : pool_ea + 2])[0])
            reg_mem_src[n] = None
            reg_taint[n] = None
        elif hi == 0xD:
            pool_ea = ((pc + 4) & ~3) + disp * 4
            regs[n] = struct.unpack(">I", rom[pool_ea : pool_ea + 4])[0]
            reg_mem_src[n] = None
            reg_taint[n] = None
        elif hi == 0xE:
            regs[n] = sext8(disp)
            reg_mem_src[n] = None
            reg_taint[n] = None
        elif (op & 0xF00F) == 0x6003:
            regs[n] = regs[m]
            reg_mem_src[n] = reg_mem_src[m]
            reg_taint[n] = reg_taint[m]
        elif (op & 0xF00F) == 0x600C:
            regs[n] = (regs[m] & 0xFF) if regs[m] is not None else None
            reg_mem_src[n] = reg_mem_src[m]
            reg_taint[n] = reg_taint[m]
        elif (op & 0xF00F) == 0x600D:
            regs[n] = (regs[m] & 0xFFFF) if regs[m] is not None else None
            reg_mem_src[n] = reg_mem_src[m]
            reg_taint[n] = reg_taint[m]
        elif (op & 0xF00F) == 0x600E:
            regs[n] = sext8(regs[m] & 0xFF) if regs[m] is not None else None
            reg_mem_src[n] = reg_mem_src[m]
            reg_taint[n] = reg_taint[m]
        elif (op & 0xF00F) == 0x600F:
            regs[n] = sext16(regs[m] & 0xFFFF) if regs[m] is not None else None
            reg_mem_src[n] = reg_mem_src[m]
            reg_taint[n] = reg_taint[m]
        elif hi == 0x7:
            if regs[n] is not None:
                regs[n] = (regs[n] + sext8(disp)) & 0xFFFFFFFF
            reg_mem_src[n] = None
        elif (op & 0xF00F) == 0x300C:
            if regs[n] is not None and regs[m] is not None:
                regs[n] = (regs[n] + regs[m]) & 0xFFFFFFFF
            else:
                regs[n] = None
            reg_taint[n] = reg_taint[n] or reg_taint[m]
            reg_mem_src[n] = reg_mem_src[n] or reg_mem_src[m]
        elif (op & 0xF00F) == 0x3008:  # sub Rm, Rn
            regs[n] = None
            reg_taint[n] = reg_taint[n] or reg_taint[m]
        elif hi == 0x4 and (op & 0xFF) in (0x00, 0x01, 0x08, 0x09, 0x18, 0x19, 0x28, 0x29):
            shift_map = {0x00: 1, 0x08: 2, 0x18: 8, 0x28: 16}
            rshift_map = {0x01: 1, 0x09: 2, 0x19: 8, 0x29: 16}
            if regs[n] is not None:
                if (op & 0xFF) in shift_map:
                    regs[n] = (regs[n] << shift_map[op & 0xFF]) & 0xFFFFFFFF
                else:
                    regs[n] = (regs[n] >> rshift_map[op & 0xFF]) & 0xFFFFFFFF
        elif (hi == 0x5) or (hi == 0x6 and disp4 in (0, 1, 2)) or (hi == 0x0 and disp4 in (0xC, 0xD, 0xE)):
            if not (hi == 0x0 and disp4 in (0xC, 0xD, 0xE) and regs[m] in cat_addrs):
                regs[n] = None
                reg_mem_src[n] = src_mem
                reg_taint[n] = None
        elif hi == 0x8 and ((op >> 8) & 0xF) in (0x4, 0x5):
            regs[0] = None
            reg_mem_src[0] = src_mem
            reg_taint[0] = None
        elif hi == 0xC and ((op >> 8) & 0xF) in (0x4, 0x5, 0x6):
            regs[0] = None
            reg_mem_src[0] = src_mem
            reg_taint[0] = None
        elif hi == 0xC and ((op >> 8) & 0xF) in (0x8, 0x9, 0xA, 0xB):
            regs[0] = None
            reg_mem_src[0] = None
        elif hi == 0x2 and disp4 in (0x9, 0xA, 0xB):  # and/xor/or Rm, Rn
            regs[n] = None
        elif (op & 0xF0FF) == 0x000A:  # sts macl, Rn
            regs[n] = None
            reg_mem_src[n] = None

        # Handle control flow & pending lookup/clobber after delay slot
        if (hi == 0xB) or (hi == 0x4 and (op & 0xFF) in (0x0B, 0x2B)) or (hi == 0xA) or ((op & 0xFF00) in (0x8D00, 0x8F00)):
            in_delay = True
            if (hi == 0xB) or (hi == 0x4 and (op & 0xFF) == 0x0B):
                pending_call_clobber = (called_lookup if called_lookup else True)
        elif pending_call_clobber:
            if isinstance(pending_call_clobber, tuple):
                t_addr, c_pc, h_name = pending_call_clobber
                q_inputs = []
                if reg_mem_src[5] is not None:
                    q_inputs.append(f"r5<-{fmt_addr(reg_mem_src[5])}")
                if reg_mem_src[6] is not None:
                    q_inputs.append(f"r6<-{fmt_addr(reg_mem_src[6])}")
                rec = {
                    "reader_pc": c_pc,
                    "func": cur_func,
                    "helper": h_name,
                    "q_inputs": q_inputs,
                    "dests": [],
                }
                cat_calls.setdefault(t_addr, []).append(rec)
                active_lookup_call = (t_addr, c_pc, h_name, q_inputs, 32)
            pending_call_clobber = False
            for r in range(8):
                regs[r] = None
                reg_mem_src[r] = None
                reg_taint[r] = None
            if active_lookup_call is not None:
                # Callee return value in r0 is tainted by active lookup
                reg_taint[0] = (active_lookup_call[0], active_lookup_call[1])

    return gbr_events, ram_readers, ram_writers, cat_calls


def write_function_gbr_map(gbr_events, out_path):
    # Summarize per-function + keep every ldc Rm, gbr site
    by_func_cnt = {}
    for e in gbr_events:
        by_func_cnt[e["function"]] = by_func_cnt.get(e["function"], 0) + 1
    rows = []
    for e in gbr_events:
        rows.append({
            "function": e["function"],
            "pc": e["pc"],
            "gbr_base": e["gbr_base"],
            "space": e["space"],
            "src_reg": e["src_reg"],
            "func_gbr_load_count": by_func_cnt[e["function"]],
            "instruction": e["instruction"],
        })
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), delimiter="\t")
        w.writeheader()
        w.writerows(rows)
    return rows


def extract_ram_tokens(text):
    """Extracts canonical FFFFxxxx addresses from CSV text (handles FFFF1054+0x34 etc.)."""
    res = []
    if not text:
        return res
    for m in re.finditer(r"FFFF([0-9A-Fa-f]{4})(?:\+0x([0-9A-Fa-f]+)|-0x([0-9A-Fa-f]+))?", text):
        base = 0xFFFF0000 | int(m.group(1), 16)
        if m.group(2):
            ea = (base + int(m.group(2), 16)) & 0xFFFFFFFF
        elif m.group(3):
            ea = (base - int(m.group(3), 16)) & 0xFFFFFFFF
        else:
            ea = base
        res.append(ea)
    return res


def write_catalog_summary(catalog_rows, cat_calls, ram_readers, ram_writers, ram_sem, out_path):
    rows = []
    for r in catalog_rows:
        t_addr = int(r["address"], 16)
        calls = cat_calls.get(t_addr, [])

        reader_pcs = [f"0x{c['reader_pc']:05X}({c['func']}:{c['helper']})" for c in calls]
        q_inputs_traced = []
        dest_list = []
        for c in calls:
            for q in c["q_inputs"]:
                if q not in q_inputs_traced:
                    q_inputs_traced.append(q)
            # Take first tainted write (or first fallback write) per call
            tainted_d = [d for d in c["dests"] if d[4]]
            chosen = tainted_d[:2] if tainted_d else c["dests"][:1]
            for ea, width, wpc, winstr, is_t in chosen:
                dest_list.append((ea, width, wpc, c["func"], is_t))

        # Gather all relevant RAM addresses for semantics + downstream readers
        csv_dest_eas = extract_ram_tokens(r.get("destination_ram", ""))
        csv_q_eas = extract_ram_tokens(r.get("query_expression", ""))
        traced_dest_eas = [d[0] for d in dest_list]
        traced_q_eas = []
        for q in q_inputs_traced:
            traced_q_eas.extend(extract_ram_tokens(q))

        all_dest_eas = []
        for ea in traced_dest_eas + csv_dest_eas:
            if ea not in all_dest_eas:
                all_dest_eas.append(ea)
        all_q_eas = []
        for ea in traced_q_eas + csv_q_eas:
            if ea not in all_q_eas:
                all_q_eas.append(ea)

        # Downstream readers of destination RAM (all code reads across the ROM)
        ds_readers = []
        ds_funcs = []
        for dea in all_dest_eas:
            for rpc, rfunc in ram_readers.get(dea, []):
                tag = f"{fmt_addr(dea)}@{rpc:05X}({rfunc})"
                if tag not in ds_readers:
                    ds_readers.append(tag)
                if rfunc not in ds_funcs:
                    ds_funcs.append(rfunc)

        q_sem = []
        for qea in all_q_eas:
            for s in ram_sem.get(fmt_addr(qea), []):
                tag = f"{fmt_addr(qea)}={s}"
                if tag not in q_sem:
                    q_sem.append(tag)

        d_sem = []
        for dea in all_dest_eas:
            for s in ram_sem.get(fmt_addr(dea), []):
                tag = f"{fmt_addr(dea)}={s}"
                if tag not in d_sem:
                    d_sem.append(tag)

        dest_str = "; ".join(
            f"{fmt_addr(ea)}:{w}@{wpc:05X}({'taint' if it else 'near'})" for ea, w, wpc, _, it in dest_list
        ) or "-"

        rows.append({
            "address": r["address"],
            "dimensions": r["dimensions"],
            "storage": r["storage"],
            "evidence_tier": r["evidence_tier"],
            "catalog_helper_or_reader": r["helper_or_reader"],
            "traced_reader_sites": "; ".join(reader_pcs) or "-",
            "traced_query_inputs": "; ".join(q_inputs_traced) or "-",
            "catalog_query_expr": r.get("query_expression", "") or "-",
            "traced_dest_ram": dest_str,
            "catalog_dest_ram": r.get("destination_ram", "") or "-",
            "query_pid_semantics": "; ".join(q_sem) or "-",
            "dest_pid_semantics": "; ".join(d_sem) or "-",
            "dest_downstream_read_count": len(ds_readers),
            "dest_downstream_funcs": "; ".join(ds_funcs[:8]) or "-",
            "dest_downstream_sample": "; ".join(ds_readers[:6]) or "-",
            "catalog_consumer_notes": r.get("consumer_or_notes", "") or "-",
        })

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), delimiter="\t")
        w.writeheader()
        w.writerows(rows)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rom", default="EVIDENCE/VERSA f501.bin")
    ap.add_argument("--listing", default="/tmp/EL19A_NEXT6_16.lst")
    ap.add_argument("--catalog", default="CALIBRATIONS/discovered_tables_catalog.csv")
    ap.add_argument("--outdir", default="INDEX")
    args = ap.parse_args()

    rom_md5 = md5_file(args.rom)
    if rom_md5 != EXPECTED_ROM_MD5:
        raise RuntimeError(f"ROM MD5 mismatch: {rom_md5}")
    lst_sha = sha256_file(args.listing)
    if lst_sha != EXPECTED_LST_SHA256:
        raise RuntimeError(f"Listing SHA-256 mismatch: {lst_sha}")

    with open(args.rom, "rb") as f:
        rom = f.read()
    with open(args.catalog, newline="", encoding="utf-8") as f:
        catalog_rows = list(csv.DictReader(f))

    os.makedirs(args.outdir, exist_ok=True)

    # 1. WO65115 Regression Validation
    val_rows = run_wo65115_validation(args.rom, args.listing, os.path.join(args.outdir, "wo65115_validation.tsv"))

    # 2. Full ROM pass -> GBR map + Catalog 179 consumer trace
    code_lines = parse_listing(args.listing, rom)
    ram_sem = build_semantics_map(args.outdir)
    gbr_events, ram_readers, ram_writers, cat_calls = full_rom_analysis(code_lines, rom, catalog_rows, set())

    gbr_rows = write_function_gbr_map(gbr_events, os.path.join(args.outdir, "function_gbr_map.tsv"))
    cat_rows = write_catalog_summary(
        catalog_rows, cat_calls, ram_readers, ram_writers, ram_sem,
        os.path.join(args.outdir, "catalog_179_consumer_summary.tsv"),
    )

    traced_readers = sum(1 for r in cat_rows if r["traced_reader_sites"] != "-")
    traced_dests = sum(1 for r in cat_rows if r["traced_dest_ram"] != "-")
    with_ds = sum(1 for r in cat_rows if r["dest_downstream_read_count"] > 0)
    with_sem = sum(1 for r in cat_rows if r["query_pid_semantics"] != "-" or r["dest_pid_semantics"] != "-")
    gbr_resolved = sum(1 for r in gbr_rows if r["gbr_base"] != "UNRESOLVED")

    print(f"1. wo65115_validation.tsv: {len(val_rows)}/10 checks PASS")
    print(f"2. function_gbr_map.tsv: {len(gbr_rows)} ldc-gbr sites ({gbr_resolved} resolved)")
    print(f"3. catalog_179_consumer_summary.tsv: {len(cat_rows)} tables (traced_readers={traced_readers}, traced_dest={traced_dests}, downstream_readers={with_ds}, pid_sem={with_sem})")


if __name__ == "__main__":
    main()
