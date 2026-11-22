#!/usr/bin/env python3
"""
extract_diagnostic_rosetta.py
Builds four machine-verified static reference tables in INDEX/ from the
EL19A ROM binary and V3_NEXT6_16 disassembly listing:
  1. INDEX/obd_mode01_pid_map.tsv      (K-line sub_31DAA + CAN sub_B8A8C + 0xDFC0/0xDFD0 masks)
  2. INDEX/consult_mode22_pid_map.tsv  (Consult-II Mode $22 CID tables 0x11xx..0x16xx)
  3. INDEX/dtc_198_and_writers.tsv     (198-slot 0x12E38/dword_13780/FFFFA074 crosswalk + writers)
  4. INDEX/sh7058_mmio_census.tsv      (Dereferenced SH7058 MMIO register census 0xFFFFD800+)

Pure Python 3 stdlib only. Verifies ROM MD5, listing SHA-256, and ROM-byte PC concordance.
"""

import argparse
import csv
import hashlib
import os
import re
import struct
import sys

EXPECTED_ROM_MD5 = "46991697c502052752a2cabcb84c9e27"
EXPECTED_LST_SHA256 = "148385bbec91f6a491dcaa403962836f709c2f273df9a17ec51f1dea5f7f4549"

SAE_MODE01_PIDS = {
    0x00: ("Supported PIDs [01-20]", "4B bitmask", "bitmask"),
    0x01: ("Monitor status since DTCs cleared (MIL + readiness)", "4B bitfield", "bitfield"),
    0x03: ("Fuel system status", "2B enum", "A=B1, B=B2"),
    0x04: ("Calculated engine load", "%", "A*100/255"),
    0x05: ("Engine coolant temperature (ECT)", "degC", "A-40"),
    0x06: ("Short term fuel trim - Bank 1", "%", "(A-128)*100/128"),
    0x07: ("Long term fuel trim - Bank 1", "%", "(A-128)*100/128"),
    0x08: ("Short term fuel trim - Bank 2", "%", "(A-128)*100/128"),
    0x09: ("Long term fuel trim - Bank 2", "%", "(A-128)*100/128"),
    0x0B: ("Intake manifold absolute pressure (MAP)", "kPa", "A"),
    0x0C: ("Engine speed (RPM)", "rpm", "(256*A+B)/4"),
    0x0D: ("Vehicle speed (VSS)", "km/h", "A"),
    0x0E: ("Timing advance", "deg BTDC", "A/2-64"),
    0x0F: ("Intake air temperature (IAT)", "degC", "A-40"),
    0x10: ("Mass air flow rate (MAF)", "g/s", "(256*A+B)/100"),
    0x11: ("Throttle position (TPS)", "%", "A*100/255"),
    0x13: ("Oxygen sensors present (2 banks)", "1B bitmask", "bitmask"),
    0x14: ("Oxygen sensor 1 (S11) voltage & STFT", "V / %", "A/200, (B-128)*100/128"),
    0x15: ("Oxygen sensor 2 (S12) voltage & STFT", "V / %", "A/200, (B-128)*100/128"),
    0x16: ("Oxygen sensor 3 (S13) voltage & STFT", "V / %", "A/200, (B-128)*100/128"),
    0x18: ("Oxygen sensor 5 (S21) voltage & STFT", "V / %", "A/200, (B-128)*100/128"),
    0x19: ("Oxygen sensor 6 (S22) voltage & STFT", "V / %", "A/200, (B-128)*100/128"),
    0x1A: ("Oxygen sensor 7 (S23) voltage & STFT", "V / %", "A/200, (B-128)*100/128"),
    0x1C: ("OBD standards conformance", "1B enum", "enum"),
    0x1F: ("Run time since engine start", "s", "256*A+B"),
    0x20: ("Supported PIDs [21-40]", "4B bitmask", "bitmask"),
    0x21: ("Distance traveled with MIL on", "km", "256*A+B"),
    0x24: ("O2 Sensor 1 AFR equivalence ratio & voltage", "lambda / V", "2*(256*A+B)/65536, 8*(256*C+D)/65536"),
    0x2C: ("Commanded EGR", "%", "A*100/255"),
    0x2D: ("EGR Error", "%", "(A-128)*100/128"),
    0x2E: ("Commanded evaporative purge", "%", "A*100/255"),
    0x2F: ("Fuel tank level input", "%", "A*100/255"),
    0x30: ("Warm-ups since codes cleared", "count", "A"),
    0x31: ("Distance traveled since codes cleared", "km", "256*A+B"),
    0x32: ("Evap system vapor pressure", "Pa", "s16(A,B)/4"),
    0x33: ("Absolute barometric pressure", "kPa", "A"),
    0x3C: ("Catalyst temperature Bank 1 Sensor 1", "degC", "(256*A+B)/10-40"),
    0x3D: ("Catalyst temperature Bank 2 Sensor 1", "degC", "(256*A+B)/10-40"),
    0x40: ("Supported PIDs [41-60]", "4B bitmask", "bitmask"),
    0x41: ("Monitor status this drive cycle", "4B bitfield", "bitfield"),
    0x42: ("Control module voltage", "V", "(256*A+B)/1000"),
    0x43: ("Absolute load value", "%", "(256*A+B)*100/255"),
    0x44: ("Commanded air-fuel equivalence ratio", "lambda", "(256*A+B)/32768"),
    0x45: ("Relative throttle position", "%", "A*100/255"),
    0x47: ("Absolute throttle position B", "%", "A*100/255"),
    0x49: ("Accelerator pedal position D", "%", "A*100/255"),
    0x4A: ("Accelerator pedal position E", "%", "A*100/255"),
    0x4B: ("Accelerator pedal position F", "%", "A*100/255"),
    0x4C: ("Commanded throttle actuator", "%", "A*100/255"),
    0x4E: ("Time since trouble codes cleared", "min", "256*A+B"),
}

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


def verify_pc_concordance(rom, items, pc_key="pc"):
    mismatches = 0
    for item in items:
        pc_str = item[pc_key]
        if not pc_str or pc_str == "-":
            continue
        pc = int(pc_str, 16)
        if pc < 0 or pc + 2 > len(rom):
            mismatches += 1
            continue
        if "bytes_expected" in item:
            if rom[pc : pc + len(item["bytes_expected"])] != item["bytes_expected"]:
                mismatches += 1
    return mismatches


def parse_listing_and_mmio_symbols(lst_path, rom):
    """Single-pass parse of listing code lines + bottom MMIO hardware symbol table."""
    code_lines = []
    mmio_symbols = {}
    current_func = "unknown"
    current_label = "unknown"
    pending_label = None
    in_high_segment = False
    concordance_failures = 0

    with open(lst_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            s = line.strip()
            if not s:
                continue
            if not in_high_segment and s.startswith("FFFF"):
                in_high_segment = True

            if in_high_segment:
                if s.endswith(":") and not s.startswith(";"):
                    lbl = s[:-1]
                    if not lbl.startswith(("unk_", "byte_", "word_", "dword_", "loc_", "off_")):
                        pending_label = lbl
                elif pending_label and len(s) >= 8 and all(c in HEX_CHARS for c in s[:8]):
                    addr = int(s[:8], 16)
                    if addr >= 0xFFFFD800:
                        mmio_symbols[addr] = pending_label
                    pending_label = None
                elif len(s) >= 8 and all(c in HEX_CHARS for c in s[:8]):
                    pending_label = None
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
                hex_bytes = bytes.fromhex(m_code.group(2).strip())
                if pc + len(hex_bytes) <= len(rom):
                    if rom[pc : pc + len(hex_bytes)] != hex_bytes:
                        concordance_failures += 1
                instr_text = m_code.group(3).strip()
                comment = m_code.group(4).strip() if m_code.group(4) else ""
                code_lines.append((pc, hex_bytes, instr_text, comment, current_func, current_label))

    if concordance_failures:
        raise RuntimeError(f"Listing/ROM byte concordance failure count: {concordance_failures}")
    return code_lines, mmio_symbols


def decode_bitmask_pids(mask_bytes):
    pids = set()
    for byte_idx, b in enumerate(mask_bytes):
        for bit in range(8):
            if b & (0x80 >> bit):
                pid = byte_idx * 8 + bit + 1
                pids.add(pid)
    return pids


def trace_pid_blocks(code_lines, rom, start_pc, end_pc, initial_gbr=None):
    """
    Traces cmp/eq #PID blocks inside a Mode $01 handler (sub_31DAA or sub_B8A8C)
    to extract exact RAM/ROM addresses and math/scaling helpers touched per PID.
    """
    block_code = [c for c in code_lines if start_pc <= c[0] <= end_pc]
    regs = [None] * 16
    gbr = initial_gbr
    prev_label = None
    in_delay = False
    pending_call_clobber = False

    # Identify PID dispatch anchors: cmp/eq #imm, r0 -> 0x88xx
    # Track active PID once cmp/eq #PID, r0 is followed by bf/bt until next cmp/eq #PID, r0 or exit
    pid_blocks = {}  # pid -> dict
    current_pid = None
    pending_pid = None

    def ensure_pid(p):
        if p not in pid_blocks:
            pid_blocks[p] = {
                "start_pc": None,
                "ram_reads": [],
                "rom_reads": [],
                "helpers": [],
                "notes": [],
            }
        return pid_blocks[p]

    for pc, hb, instr, comment, func, lbl in block_code:
        op = int.from_bytes(hb[:2], "big")
        hi = (op >> 12) & 0xF
        n = (op >> 8) & 0xF
        m = (op >> 4) & 0xF
        disp = op & 0xFF
        disp4 = op & 0xF

        if lbl != prev_label and not in_delay:
            prev_label = lbl
            for r in range(8):
                regs[r] = None

        # Detect cmp/eq #imm, r0 (0x88xx) for PID selection
        if (op & 0xFF00) == 0x8800:
            imm = op & 0xFF
            # Filter sentinel comparisons like 0xFF
            if 0x01 <= imm <= 0x60 and ("r0" in instr):
                pending_pid = imm

        # Check branch after cmp/eq
        if (op & 0xFB00) in (0x8900, 0x8B00, 0x8D00, 0x8F00) and pending_pid is not None:
            current_pid = pending_pid
            pending_pid = None
            info = ensure_pid(current_pid)
            if info["start_pc"] is None:
                info["start_pc"] = pc
            # Note: bt/bf delay slot may already belong to PID or fallthrough

        # Handle PID 0x01 which sits right after bitmask check in sub_31DAA / sub_B8A8C
        # Check memory reads while in a PID block
        if current_pid is not None:
            info = ensure_pid(current_pid)
            ea = None
            width = None
            form = None
            if hi == 0x0 and disp4 in (0xC, 0xD, 0xE):
                width = "b" if disp4 == 0xC else ("w" if disp4 == 0xD else "l")
                if regs[m] is not None and regs[0] is not None:
                    ea = (regs[m] + regs[0]) & 0xFFFFFFFF
                    form = f"@(r0+{fmt_addr(regs[m])})"
            elif hi == 0x5:
                width = "l"
                if regs[m] is not None:
                    ea = (regs[m] + disp4 * 4) & 0xFFFFFFFF
                    form = f"@(0x{disp4*4:X}+{fmt_addr(regs[m])})"
            elif hi == 0x8 and ((op >> 8) & 0xF) in (0x4, 0x5):
                sub_op = (op >> 8) & 0xF
                reg_4 = (op >> 4) & 0xF
                scale = 1 if sub_op == 0x4 else 2
                width = "b" if sub_op == 0x4 else "w"
                if regs[reg_4] is not None:
                    ea = (regs[reg_4] + disp4 * scale) & 0xFFFFFFFF
                    form = f"@(0x{disp4*scale:X}+{fmt_addr(regs[reg_4])})"
            elif hi == 0x6 and disp4 in (0, 1, 2):
                width = "b" if disp4 == 0 else ("w" if disp4 == 1 else "l")
                if regs[m] is not None:
                    ea = regs[m]
                    form = f"@{fmt_addr(regs[m])}"
            elif hi == 0xC and ((op >> 8) & 0xF) in (0x4, 0x5, 0x6, 0xC):
                sub_op = (op >> 8) & 0xF
                if gbr is not None:
                    if sub_op in (0x4, 0x5, 0x6):
                        scale = 1 if sub_op == 0x4 else (2 if sub_op == 0x5 else 4)
                        width = "b" if sub_op == 0x4 else ("w" if sub_op == 0x5 else "l")
                        ea = (gbr + disp * scale) & 0xFFFFFFFF
                        form = f"@(0x{disp*scale:X}+GBR:{fmt_addr(gbr)})"
                    elif sub_op == 0xC and regs[0] is not None:
                        width = "b"
                        ea = (gbr + regs[0]) & 0xFFFFFFFF
                        form = f"@(r0+GBR:{fmt_addr(gbr)})"

            if ea is not None:
                # Filter out response buffer FFFF2F00..FFFF30FF and stack FFFFxxxx only if real
                tag = f"{fmt_addr(ea)}:{width}@{pc:05X}"
                if ea >= 0xFFFF0000:
                    if not (0xFFFF2F00 <= ea <= 0xFFFF3100):
                        if tag not in info["ram_reads"]:
                            info["ram_reads"].append(tag)
                elif ea < len(rom):
                    val = rom[ea] if width == "b" else (
                        struct.unpack(">H", rom[ea:ea+2])[0] if width == "w" else struct.unpack(">I", rom[ea:ea+4])[0]
                    )
                    rtag = f"0x{ea:05X}:{width}={val:#x}@{pc:05X}"
                    if rtag not in info["rom_reads"]:
                        info["rom_reads"].append(rtag)

            # Record math / helper calls
            if (hi == 0x4 and (op & 0xFF) == 0x0B) or hi == 0xB:
                if comment:
                    hname = comment.split()[0]
                    if hname not in ("sub_33E18", "sub_33CD4", "sub_33D04") and hname not in info["helpers"]:
                        info["helpers"].append(hname)
            elif hi == 0x0 and disp4 == 0x7:  # mul.l
                if "mul.l" not in info["notes"]:
                    info["notes"].append("mul.l")
            elif (op & 0xF00F) in (0x200E, 0x200F):  # mulu.w / muls.w
                if "mul.w" not in info["notes"]:
                    info["notes"].append("mul.w")
            elif hi == 0x4 and (op & 0xFF) in (0x00, 0x01, 0x08, 0x09, 0x18, 0x19, 0x28, 0x29):
                pass

        # Update register state
        in_delay = False
        if (op & 0xF0FF) == 0x401E:  # ldc Rm, gbr
            gbr = regs[n]
        elif (op & 0xF0FF) == 0x0012:  # stc gbr, Rn
            regs[n] = gbr
        elif hi == 0x9:  # mov.w @(disp, pc), Rn
            pool_ea = pc + 4 + disp * 2
            val = struct.unpack(">H", rom[pool_ea : pool_ea + 2])[0]
            regs[n] = sext16(val)
        elif hi == 0xD:  # mov.l @(disp, pc), Rn
            pool_ea = ((pc + 4) & ~3) + disp * 4
            regs[n] = struct.unpack(">I", rom[pool_ea : pool_ea + 4])[0]
        elif hi == 0xE:  # mov #imm, Rn
            regs[n] = sext8(disp)
        elif (op & 0xF00F) == 0x6003:  # mov Rm, Rn
            regs[n] = regs[m]
        elif (op & 0xF00F) == 0x600C:  # extu.b Rm, Rn
            regs[n] = (regs[m] & 0xFF) if regs[m] is not None else None
        elif (op & 0xF00F) == 0x600D:  # extu.w Rm, Rn
            regs[n] = (regs[m] & 0xFFFF) if regs[m] is not None else None
        elif (op & 0xF00F) == 0x600E:
            regs[n] = sext8(regs[m] & 0xFF) if regs[m] is not None else None
        elif (op & 0xF00F) == 0x600F:
            regs[n] = sext16(regs[m] & 0xFFFF) if regs[m] is not None else None
        elif hi == 0x7:  # add #imm, Rn
            if regs[n] is not None:
                regs[n] = (regs[n] + sext8(disp)) & 0xFFFFFFFF
        elif (op & 0xF00F) == 0x300C:  # add Rm, Rn
            if regs[n] is not None and regs[m] is not None:
                regs[n] = (regs[n] + regs[m]) & 0xFFFFFFFF
            else:
                regs[n] = None
        elif (op & 0xF0FF) == 0x4000 and regs[n] is not None:
            regs[n] = (regs[n] << 1) & 0xFFFFFFFF
        elif (op & 0xF0FF) == 0x4008 and regs[n] is not None:
            regs[n] = (regs[n] << 2) & 0xFFFFFFFF
        elif (op & 0xF0FF) == 0x4018 and regs[n] is not None:
            regs[n] = (regs[n] << 8) & 0xFFFFFFFF
        elif (op & 0xF0FF) == 0x4001 and regs[n] is not None:
            regs[n] = (regs[n] >> 1) & 0xFFFFFFFF
        elif (op & 0xF0FF) == 0x4009 and regs[n] is not None:
            regs[n] = (regs[n] >> 2) & 0xFFFFFFFF
        elif (op & 0xF0FF) == 0x4019 and regs[n] is not None:
            regs[n] = (regs[n] >> 8) & 0xFFFFFFFF
        elif hi in (0x5, 0x6, 0x8) and not (hi == 0x8 and ((op >> 8) & 0xF) in (0x0, 0x1, 0x8, 0x9, 0xB, 0xD, 0xF)):
            if hi == 0x8:
                regs[0] = None
            else:
                regs[n] = None
        elif hi == 0x0 and disp4 in (0xC, 0xD, 0xE):
            regs[n] = None
        elif hi == 0x3 and disp4 in (0x8, 0xA, 0xE, 0xF):
            regs[n] = None
        elif hi == 0x2 and disp4 in (0x9, 0xA, 0xB):
            regs[n] = None
        elif hi == 0xC and ((op >> 8) & 0xF) in (0x4, 0x5, 0x6, 0x7, 0x8, 0x9, 0xA, 0xB):
            regs[0] = None
        elif hi == 0x4 and (op & 0xFF) == 0x10:  # dt
            regs[n] = None

        if (hi == 0xB) or (hi == 0x4 and (op & 0xFF) in (0x0B, 0x2B)) or (hi == 0xA) or ((op & 0xFF00) in (0x8D00, 0x8F00)):
            in_delay = True
            if (hi == 0xB) or (hi == 0x4 and (op & 0xFF) == 0x0B):
                pending_call_clobber = True
        elif pending_call_clobber:
            pending_call_clobber = False
            for r in range(8):
                regs[r] = None

    return pid_blocks


def build_obd_mode01(code_lines, rom, out_path):
    kline_mask_bytes = rom[0xDFC0:0xDFD0]
    can_mask_bytes = rom[0xDFD0:0xDFE0]
    kline_supported = decode_bitmask_pids(kline_mask_bytes)
    can_supported = decode_bitmask_pids(can_mask_bytes)

    kline_blocks = trace_pid_blocks(code_lines, rom, 0x31E80, 0x32468, initial_gbr=0x12844)
    can_blocks = trace_pid_blocks(code_lines, rom, 0xB8CD6, 0xB9E20, initial_gbr=0xFFFF33DC)

    all_pids = sorted(set(SAE_MODE01_PIDS.keys()) | kline_supported | can_supported | set(kline_blocks.keys()) | set(can_blocks.keys()))

    rows = []
    for pid in all_pids:
        name, unit, sae_formula = SAE_MODE01_PIDS.get(pid, ("Unknown / OEM PID", "-", "-"))
        in_kl_mask = "Y" if pid in kline_supported else "N"
        in_can_mask = "Y" if pid in can_supported else "N"

        kl = kline_blocks.get(pid, {})
        cn = can_blocks.get(pid, {})
        kl_pc = f"0x{kl['start_pc']:05X}" if kl.get("start_pc") else ("0x31DDE" if pid == 0x00 else ("0x31E82" if pid == 0x01 else "-"))
        cn_pc = f"0x{cn['start_pc']:05X}" if cn.get("start_pc") else ("0xB8C54" if pid == 0x00 else ("0xB8CD6" if pid == 0x01 else "-"))

        if pid == 0x00:
            kl_ram = "0x0DFC0:4B"
            cn_ram = "0x0DFD0:4B"
        elif pid == 0x01:
            kl_ram = "FFFFA074+1/+2 (198-slot loop)"
            cn_ram = "FFFFB36C+0xE6 (FFFFB452), FFFFA074+1/+2, FFFF35AE, FFFF35CB, FFFF3628"
        elif pid == 0x20:
            kl_ram = "0x0DFC4:4B"
            cn_ram = "0x0DFD4:4B"
        elif pid == 0x40:
            kl_ram = "unsupported"
            cn_ram = "0x0DFD8:4B"
        else:
            kl_ram = "; ".join(kl.get("ram_reads", [])) or "-"
            cn_ram = "; ".join(cn.get("ram_reads", [])) or "-"

        rom_consts = "; ".join(sorted(set(kl.get("rom_reads", []) + cn.get("rom_reads", [])))) or "-"
        helpers = "; ".join(sorted(set(kl.get("helpers", []) + cn.get("helpers", [])))) or "-"
        notes = "; ".join(sorted(set(kl.get("notes", []) + cn.get("notes", [])))) or "-"

        rows.append({
            "pid_hex": f"0x{pid:02X}",
            "sae_name": name,
            "unit": unit,
            "sae_formula": sae_formula,
            "kline_mask_0xDFC0": in_kl_mask,
            "can_mask_0xDFD0": in_can_mask,
            "kline_handler_pc": kl_pc,
            "kline_ram_sources": kl_ram,
            "can_handler_pc": cn_pc,
            "can_ram_sources": cn_ram,
            "rom_constants": rom_consts,
            "math_helpers": helpers,
            "notes": notes,
        })

    fieldnames = list(rows[0].keys())
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        w.writeheader()
        w.writerows(rows)
    return rows


def build_consult_mode22(rom, catalog_csv, cand_csv, mode01_rows, out_path):
    # Index known Mode 01 RAM addresses -> semantic tag
    ram_to_mode01 = {}
    for r in mode01_rows:
        for col in ("kline_ram_sources", "can_ram_sources"):
            for m in re.finditer(r"(FFFF[0-9A-F]{4})", r[col]):
                addr = m.group(1)
                if addr != "FFFFA074":
                    ram_to_mode01.setdefault(addr, []).append(f"OBD_{r['pid_hex']}:{r['sae_name']}")

    # Index catalog destination RAM mentions
    ram_to_cat = {}
    if os.path.exists(catalog_csv):
        with open(catalog_csv, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                dest = row.get("destination_ram", "")
                for m in re.finditer(r"FFFF([0-9A-F]{4})(?:\+0x([0-9A-F]+))?", dest):
                    base = int(m.group(1), 16)
                    off = int(m.group(2), 16) if m.group(2) else 0
                    ea = f"FFFF{(base + off) & 0xFFFF:04X}"
                    ram_to_cat.setdefault(ea, []).append(row["address"])

    groups = [
        (0x11, 0x13E94, 0x14084, 4, "1B (0x*00=4B mask)"),
        (0x12, 0x14084, 0x141E0, 4, "1B (0x1200=4B mask; check handler for 2B)"),
        (0x13, 0x141E0, 0x14288, 8, "paired_2x1B (RAM+ROM mask)"),
        (0x14, 0x14288, 0x1430C, 4, "1B (0x1400=4B mask)"),
        (0x15, 0x1430C, 0x143B0, 8, "paired_2x1B (RAM+ROM mask)"),
        (0x16, 0x143B0, 0x144B0, 4, "1B (0x1600/20=4B mask; bitfields)"),
    ]

    rows = []
    for grp, start, end, step, fmt_desc in groups:
        slots = (end - start) // step
        for idx in range(slots):
            off = start + idx * step
            p1 = struct.unpack(">I", rom[off : off + 4])[0]
            p2 = struct.unpack(">I", rom[off + 4 : off + 8])[0] if step == 8 else None
            if p1 == 0xFFFFFFFF and (p2 is None or p2 == 0xFFFFFFFF):
                continue

            cid = (grp << 8) | idx
            p1_str = fmt_addr(p1) if p1 != 0xFFFFFFFF else "FFFFFFFF"
            p2_str = fmt_addr(p2) if (p2 is not None and p2 != 0xFFFFFFFF) else ("-" if step == 4 else "FFFFFFFF")

            if p1 >= 0xFFFF0000:
                kind = "RAM"
            elif p1 < len(rom):
                kind = "ROM_mask" if idx in (0x00, 0x20, 0x40, 0x60) else "ROM_const"
            else:
                kind = "other"

            rom_preview = "-"
            if p1 < len(rom):
                nbytes = 4 if idx in (0x00, 0x20, 0x40, 0x60) else 1
                rom_preview = rom[p1 : p1 + nbytes].hex().upper()
            if p2 is not None and p2 < len(rom):
                rom_preview += f" | p2={rom[p2]:02X}"

            m01 = sorted(set(ram_to_mode01.get(p1_str, [])))
            cat = sorted(set(ram_to_cat.get(p1_str, [])))

            rows.append({
                "cid_hex": f"0x{cid:04X}",
                "group_hex": f"0x{grp:02X}",
                "sub_id_hex": f"0x{idx:02X}",
                "table_entry_rom": f"0x{off:05X}",
                "entry_stride_bytes": step,
                "ptr1_addr": p1_str,
                "ptr2_addr": p2_str,
                "ptr1_space": kind,
                "rom_value_hex": rom_preview,
                "mode01_cross_match": "; ".join(m01) if m01 else "-",
                "catalog_dest_match": "; ".join(cat) if cat else "-",
                "handler_format": fmt_desc,
            })

    fieldnames = list(rows[0].keys())
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        w.writeheader()
        w.writerows(rows)
    return rows


def decode_j2012(code_u16):
    letter = ["P", "C", "B", "U"][(code_u16 >> 14) & 0x3]
    d1 = (code_u16 >> 12) & 0x3
    d2 = (code_u16 >> 8) & 0xF
    d3 = (code_u16 >> 4) & 0xF
    d4 = code_u16 & 0xF
    return f"{letter}{d1}{d2:X}{d3:X}{d4:X}"


def build_dtc_198_and_writers(code_lines, rom, out_slots_path, out_writers_path):
    # 1. Decode all 198 DTC slots
    slots = []
    for i in range(198):
        rec_off = 0x12E38 + 12 * i
        rec = rom[rec_off : rec_off + 12]
        w0, w1, w2, w3, w4, w5 = struct.unpack(">6H", rec)
        pcode = decode_j2012(w3) if w3 != 0 else "NONE"
        ptr_off = 0x13780 + 4 * i
        ptr = struct.unpack(">I", rom[ptr_off : ptr_off + 4])[0]
        ptr_byte = rom[ptr] if ptr < len(rom) else -1
        ram_slot = 0xFFFFA074 + 3 * i
        slots.append({
            "slot_idx": i,
            "pcode": pcode,
            "dtc_u16_hex": f"0x{w3:04X}",
            "ram_slot_base": f"FFFF{ram_slot & 0xFFFF:04X}",
            "ram_slot_end": f"FFFF{(ram_slot + 2) & 0xFFFF:04X}",
            "rec_rom_addr": f"0x{rec_off:05X}",
            "rec_hex_12B": rec.hex().upper(),
            "w0_prefix": f"0x{w0:04X}",
            "w1_flags": f"0x{w1:04X}",
            "w2_hi": f"0x{w2:04X}",
            "w4_flags": f"0x{w4:04X}",
            "dword_13780_ptr": f"0x{ptr:05X}",
            "flag_byte_at_ptr": f"0x{ptr_byte:02X}" if ptr_byte >= 0 else "-",
            "writers": [],
            "readers": [],
            "helper_callers": [],
        })

    # 2. Trace FFFFA074 accesses across the entire listing
    # Note: track per-function registers and GBR, plus direct calls to central helpers
    central_write_helpers = {
        "sub_71F74": ("write_helper_fault_trip", 1),
        "sub_802BE": ("write_helper_fault_active", 1),
        "sub_80334": ("write_helper_pass_clear_b80", 1),
        "sub_A6E1C": ("write_helper_monitor_complete", 1),
        "sub_72884": ("write_helper_latch_dtc", 2),
        "sub_72A2A": ("write_helper_pending_latch", 2),
        "sub_8081C": ("write_helper_confirm_mil", 2),
        "sub_8085E": ("write_helper_set_b2_48", 2),
        "sub_80884": ("write_helper_set_b2_10", 2),
    }
    central_read_helpers = {
        "sub_224EC": ("read_helper_bits40_20", 2),
        "sub_2270A": ("read_helper_bit01", 2),
        "sub_2272E": ("read_helper_inv_bit20", 2),
        "sub_227E4": ("read_helper_bit02_b2", 2),
        "sub_228F0": ("read_helper_inv_bit80_b1", 1),
        "sub_22986": ("read_helper_inv_bit80_b1", 1),
        "sub_229AA": ("read_helper_inv_bit80_b1", 1),
    }
    internal_dtc_funcs = set(central_write_helpers) | set(central_read_helpers) | {
        "sub_2B306", "sub_2E97C", "sub_2EF6C", "sub_2F324", "sub_31DAA", "sub_32678", "sub_331E8", "sub_B8A8C"
    }

    for s in slots:
        s["write_helpers"] = []

    writer_events = []
    regs = [None] * 16
    gbr = None
    cur_func = None
    prev_label = None
    in_delay = False
    pending_call_clobber = False
    pending_helper_call = None

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
            gbr = None
            prev_label = lbl
            in_delay = False
            pending_call_clobber = False
            pending_helper_call = None
        elif lbl != prev_label and not in_delay:
            prev_label = lbl
            for r in range(8):
                regs[r] = None

        # Detect memory accesses to 0xFFFFA074 .. 0xFFFFA2E0
        ea = None
        acc = None
        mask_str = "-"
        base_used = None
        if hi == 0x0 and disp4 in (0xC, 0xD, 0xE) and regs[m] is not None and regs[0] is not None:
            ea = (regs[m] + regs[0]) & 0xFFFFFFFF
            acc = "read"
            base_used = regs[m]
        elif hi == 0x0 and disp4 in (0x4, 0x5, 0x6) and regs[n] is not None and regs[0] is not None:
            ea = (regs[n] + regs[0]) & 0xFFFFFFFF
            acc = "write"
            base_used = regs[n]
        elif hi == 0x8:
            sub_op = (op >> 8) & 0xF
            reg_4 = (op >> 4) & 0xF
            if sub_op in (0x0, 0x1, 0x4, 0x5) and regs[reg_4] is not None:
                scale = 1 if sub_op in (0x0, 0x4) else 2
                ea = (regs[reg_4] + disp4 * scale) & 0xFFFFFFFF
                acc = "write" if sub_op in (0x0, 0x1) else "read"
                base_used = regs[reg_4]
        elif hi == 0x2 and disp4 in (0, 1, 2) and regs[n] is not None:
            ea = regs[n]
            acc = "write"
            base_used = regs[n]
        elif hi == 0x6 and disp4 in (0, 1, 2) and regs[m] is not None:
            ea = regs[m]
            acc = "read"
            base_used = regs[m]
        elif hi == 0xC:
            sub_op = (op >> 8) & 0xF
            if gbr is not None:
                if sub_op in (0x0, 0x1, 0x2):
                    scale = 1 if sub_op == 0 else (2 if sub_op == 1 else 4)
                    ea = (gbr + disp * scale) & 0xFFFFFFFF
                    acc = "write"
                    base_used = gbr
                elif sub_op in (0x4, 0x5, 0x6):
                    scale = 1 if sub_op == 4 else (2 if sub_op == 5 else 4)
                    ea = (gbr + disp * scale) & 0xFFFFFFFF
                    acc = "read"
                    base_used = gbr
                elif sub_op in (0xC, 0xD, 0xE, 0xF) and regs[0] is not None:
                    ea = (gbr + regs[0]) & 0xFFFFFFFF
                    acc = "read" if sub_op == 0xC else "rmw"
                    mask_str = f"0x{disp:02X}"
                    base_used = gbr

        if ea is not None and 0xFFFFA074 <= ea <= 0xFFFFA2DF:
            off = ea - 0xFFFFA074
            # Ignore internal loops inside central helpers & OBD/Consult readers (2B306, 2E97C, 2EF6C, 2F324, 31DAA, 32678, 331E8, B8A8C)
            if off < 198 * 3:
                slot_i, byte_off = divmod(off, 3)
                pcode = slots[slot_i]["pcode"]
                region = "slot_array"
            else:
                slot_i, byte_off = -1, off
                pcode = f"POST_TABLE+0x{off - 594:X}"
                region = "post_slot_flags"

            # Check if previous instruction or same basic block had literal mask for or/and? Keep instr_text
            evt = {
                "pc": f"0x{pc:05X}",
                "function": cur_func,
                "access_kind": acc,
                "via": "helper_or_direct",
                "target_ram": f"FFFF{ea & 0xFFFF:04X}",
                "offset_from_A074": f"0x{off:X}",
                "slot_idx": slot_i,
                "byte_in_slot": byte_off,
                "pcode": pcode,
                "mask": mask_str,
                "region": region,
                "instruction": instr,
            }
            writer_events.append(evt)
            if slot_i >= 0 and cur_func not in internal_dtc_funcs:
                tag = f"{cur_func}@{pc:05X}[b+{byte_off}{' '+mask_str if mask_str!='-' else ''}]"
                if acc in ("write", "rmw"):
                    if tag not in slots[slot_i]["writers"]:
                        slots[slot_i]["writers"].append(tag)
                else:
                    if tag not in slots[slot_i]["readers"]:
                        slots[slot_i]["readers"].append(tag)

        # Detect calls to central DTC write/read helpers; resolve r4 after delay slot executes!
        called_helper = None
        if (hi == 0xB) or (hi == 0x4 and (op & 0xFF) == 0x0B):
            if cur_func not in internal_dtc_funcs:
                for hname in (*central_write_helpers, *central_read_helpers):
                    if hname in comment:
                        called_helper = hname
                        break
        if called_helper:
            pending_helper_call = (pc, cur_func, called_helper, instr)

        # Update register / GBR tracking
        in_delay = False
        if (op & 0xF0FF) == 0x401E:
            gbr = regs[n]
        elif (op & 0xF0FF) == 0x0012:
            regs[n] = gbr
        elif hi == 0x9:
            pool_ea = pc + 4 + disp * 2
            regs[n] = sext16(struct.unpack(">H", rom[pool_ea : pool_ea + 2])[0])
        elif hi == 0xD:
            pool_ea = ((pc + 4) & ~3) + disp * 4
            regs[n] = struct.unpack(">I", rom[pool_ea : pool_ea + 4])[0]
        elif hi == 0xE:
            regs[n] = sext8(disp)
        elif (op & 0xF00F) == 0x6003:
            regs[n] = regs[m]
        elif (op & 0xF00F) == 0x600C:
            regs[n] = (regs[m] & 0xFF) if regs[m] is not None else None
        elif (op & 0xF00F) == 0x600D:
            regs[n] = (regs[m] & 0xFFFF) if regs[m] is not None else None
        elif (op & 0xF00F) == 0x600E:
            regs[n] = sext8(regs[m] & 0xFF) if regs[m] is not None else None
        elif (op & 0xF00F) == 0x600F:
            regs[n] = sext16(regs[m] & 0xFFFF) if regs[m] is not None else None
        elif hi == 0x7:
            if regs[n] is not None:
                regs[n] = (regs[n] + sext8(disp)) & 0xFFFFFFFF
        elif (op & 0xF00F) == 0x300C:
            if regs[n] is not None and regs[m] is not None:
                regs[n] = (regs[n] + regs[m]) & 0xFFFFFFFF
            else:
                regs[n] = None
        elif (op & 0xF0FF) == 0x4000 and regs[n] is not None:
            regs[n] = (regs[n] << 1) & 0xFFFFFFFF
        elif (op & 0xF0FF) == 0x4008 and regs[n] is not None:
            regs[n] = (regs[n] << 2) & 0xFFFFFFFF
        elif (op & 0xF0FF) == 0x4018 and regs[n] is not None:
            regs[n] = (regs[n] << 8) & 0xFFFFFFFF
        elif hi in (0x5, 0x6, 0x8) and not (hi == 0x8 and ((op >> 8) & 0xF) in (0x0, 0x1, 0x8, 0x9, 0xB, 0xD, 0xF)):
            if hi == 0x8:
                regs[0] = None
            else:
                regs[n] = None
        elif hi == 0x0 and disp4 in (0xC, 0xD, 0xE):
            regs[n] = None
        elif hi == 0x3 and disp4 in (0x8, 0xA, 0xE, 0xF):
            regs[n] = None
        elif hi == 0x2 and disp4 in (0x9, 0xA, 0xB):
            regs[n] = None
        elif hi == 0xC and ((op >> 8) & 0xF) in (0x4, 0x5, 0x6, 0x7, 0x8, 0x9, 0xA, 0xB):
            regs[0] = None
        elif hi == 0x4 and (op & 0xFF) == 0x10:
            regs[n] = None

        if (hi == 0xB) or (hi == 0x4 and (op & 0xFF) in (0x0B, 0x2B)) or (hi == 0xA) or ((op & 0xFF00) in (0x8D00, 0x8F00)):
            in_delay = True
            if (hi == 0xB) or (hi == 0x4 and (op & 0xFF) == 0x0B):
                pending_call_clobber = True
        else:
            if pending_helper_call is not None:
                cpc, cfunc, chname, cinstr = pending_helper_call
                pending_helper_call = None
                slot_arg = regs[4]
                if slot_arg is not None and 0 <= slot_arg < 198:
                    is_writer = chname in central_write_helpers
                    htype, b_off = central_write_helpers[chname] if is_writer else central_read_helpers[chname]
                    tag = f"{cfunc}@{cpc:05X}->{chname}"
                    if is_writer:
                        if tag not in slots[slot_arg]["write_helpers"]:
                            slots[slot_arg]["write_helpers"].append(tag)
                    else:
                        if tag not in slots[slot_arg]["helper_callers"]:
                            slots[slot_arg]["helper_callers"].append(tag)
                    writer_events.append({
                        "pc": f"0x{cpc:05X}",
                        "function": cfunc,
                        "access_kind": "write_helper" if is_writer else "read_helper",
                        "via": chname,
                        "target_ram": slots[slot_arg]["ram_slot_base"],
                        "offset_from_A074": f"0x{3*slot_arg + b_off:X}",
                        "slot_idx": slot_arg,
                        "byte_in_slot": b_off,
                        "pcode": slots[slot_arg]["pcode"],
                        "mask": "-",
                        "region": "slot_array",
                        "instruction": f"{cinstr} ; {htype}(slot={slot_arg})",
                    })
            if pending_call_clobber:
                pending_call_clobber = False
                for r in range(8):
                    regs[r] = None

    # Write 198-slot crosswalk TSV
    slot_rows = []
    for s in slots:
        slot_rows.append({
            "slot_idx": s["slot_idx"],
            "pcode": s["pcode"],
            "dtc_u16_hex": s["dtc_u16_hex"],
            "ram_slot_base": s["ram_slot_base"],
            "ram_slot_end": s["ram_slot_end"],
            "rec_rom_addr": s["rec_rom_addr"],
            "dword_13780_ptr": s["dword_13780_ptr"],
            "flag_byte_at_ptr": s["flag_byte_at_ptr"],
            "w0_prefix": s["w0_prefix"],
            "w1_flags": s["w1_flags"],
            "w4_flags": s["w4_flags"],
            "writer_count": len(s["writers"]) + len(s["write_helpers"]),
            "direct_writer_count": len(s["writers"]),
            "write_helper_count": len(s["write_helpers"]),
            "direct_writers": "; ".join(s["writers"]) or "-",
            "write_helper_callers": "; ".join(s["write_helpers"]) or "-",
            "direct_readers": "; ".join(s["readers"]) or "-",
            "read_helper_count": len(s["helper_callers"]),
            "read_helper_callers_sample": "; ".join(s["helper_callers"][:6]) or "-",
        })
    with open(out_slots_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(slot_rows[0].keys()), delimiter="\t")
        w.writeheader()
        w.writerows(slot_rows)

    with open(out_writers_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(writer_events[0].keys()), delimiter="\t")
        w.writeheader()
        w.writerows(writer_events)

    return slot_rows, writer_events


def classify_mmio_subsystem(addr, sym_name):
    if 0xFFFFD800 <= addr <= 0xFFFFDBFF:
        return "HCAN1 (CAN0)"
    if 0xFFFFDC00 <= addr <= 0xFFFFDFFF:
        return "HCAN2 (CAN1)"
    if sym_name.startswith("HCAN"):
        return sym_name.split("_")[0]
    if sym_name.startswith(("ADDR", "ADCSR", "ADCR")):
        return "ADC"
    if sym_name.startswith("SCI"):
        return "SCI"
    if sym_name.startswith("MTAD"):
        return "ATU-II / MTAD"
    if 0xFFFFF400 <= addr <= 0xFFFFF6FF:
        return "ATU-II"
    if 0xFFFFF700 <= addr <= 0xFFFFF7FF:
        return "Ports / PFC"
    if 0xFFFFF000 <= addr <= 0xFFFFF1FF:
        return "SCI"
    if 0xFFFFF800 <= addr <= 0xFFFFF8FF:
        return "ADC / Timer"
    if 0xFFFFEC00 <= addr <= 0xFFFFEFFF:
        return "BSC / INTC / DMAC / CPU"
    if 0xFFFFFA00 <= addr <= 0xFFFFFCFF:
        return "WDT / CMT / Flash / CPG"
    return "Other SH7058 Periph"


def build_sh7058_mmio_census(code_lines, mmio_symbols, rom, out_path):
    """
    Finds all dereferenced accesses to SH7058 MMIO registers (0xFFFFD800..0xFFFFFCFF,
    or any address present in mmio_symbols). Tracks r0..r14 and gbr per function.
    """
    regs = [None] * 16
    gbr = None
    cur_func = None
    prev_label = None
    in_delay = False
    pending_call_clobber = False

    # reg_addr -> stats
    reg_hits = {}

    for pc, hb, instr, comment, func, lbl in code_lines:
        op = int.from_bytes(hb[:2], "big")
        hi = (op >> 12) & 0xF
        n = (op >> 8) & 0xF
        m = (op >> 4) & 0xF
        disp = op & 0xFF
        disp4 = op & 0xF

        if func != cur_func:
            cur_func = func
            regs = [None] * 16
            gbr = None
            prev_label = lbl
            in_delay = False
            pending_call_clobber = False
        elif lbl != prev_label and not in_delay:
            prev_label = lbl
            for r in range(8):
                regs[r] = None

        ea = None
        acc = None
        width = None
        if hi == 0x0 and disp4 in (0xC, 0xD, 0xE) and regs[m] is not None and regs[0] is not None:
            ea = (regs[m] + regs[0]) & 0xFFFFFFFF
            acc, width = "read", ("b" if disp4 == 0xC else ("w" if disp4 == 0xD else "l"))
        elif hi == 0x0 and disp4 in (0x4, 0x5, 0x6) and regs[n] is not None and regs[0] is not None:
            ea = (regs[n] + regs[0]) & 0xFFFFFFFF
            acc, width = "write", ("b" if disp4 == 0x4 else ("w" if disp4 == 0x5 else "l"))
        elif hi == 0x1 and regs[n] is not None:
            ea = (regs[n] + disp4 * 4) & 0xFFFFFFFF
            acc, width = "write", "l"
        elif hi == 0x5 and regs[m] is not None:
            ea = (regs[m] + disp4 * 4) & 0xFFFFFFFF
            acc, width = "read", "l"
        elif hi == 0x8:
            sub_op = (op >> 8) & 0xF
            reg_4 = (op >> 4) & 0xF
            if sub_op in (0x0, 0x1, 0x4, 0x5) and regs[reg_4] is not None:
                scale = 1 if sub_op in (0x0, 0x4) else 2
                ea = (regs[reg_4] + disp4 * scale) & 0xFFFFFFFF
                acc = "write" if sub_op in (0x0, 0x1) else "read"
                width = "b" if scale == 1 else "w"
        elif hi == 0x2 and disp4 in (0, 1, 2) and regs[n] is not None:
            ea = regs[n]
            acc, width = "write", ("b" if disp4 == 0 else ("w" if disp4 == 1 else "l"))
        elif hi == 0x6 and disp4 in (0, 1, 2) and regs[m] is not None:
            ea = regs[m]
            acc, width = "read", ("b" if disp4 == 0 else ("w" if disp4 == 1 else "l"))
        elif hi == 0xC and gbr is not None:
            sub_op = (op >> 8) & 0xF
            if sub_op in (0x0, 0x1, 0x2):
                scale = 1 if sub_op == 0 else (2 if sub_op == 1 else 4)
                ea = (gbr + disp * scale) & 0xFFFFFFFF
                acc, width = "write", ("b" if scale == 1 else ("w" if scale == 2 else "l"))
            elif sub_op in (0x4, 0x5, 0x6):
                scale = 1 if sub_op == 4 else (2 if sub_op == 5 else 4)
                ea = (gbr + disp * scale) & 0xFFFFFFFF
                acc, width = "read", ("b" if scale == 1 else ("w" if scale == 2 else "l"))
            elif sub_op in (0xC, 0xD, 0xE, 0xF) and regs[0] is not None:
                ea = (gbr + regs[0]) & 0xFFFFFFFF
                acc, width = ("read" if sub_op == 0xC else "rmw"), "b"

        if ea is not None and (0xFFFFD800 <= ea <= 0xFFFFFCFF or ea in mmio_symbols):
            rec = reg_hits.setdefault(ea, {
                "read": 0, "write": 0, "rmw": 0, "widths": set(), "funcs": set(), "sample_pcs": []
            })
            rec[acc] += 1
            rec["widths"].add(width)
            rec["funcs"].add(cur_func)
            if len(rec["sample_pcs"]) < 6:
                rec["sample_pcs"].append(f"0x{pc:05X}({cur_func}:{acc}.{width})")

        # Update registers
        in_delay = False
        if (op & 0xF0FF) == 0x401E:
            gbr = regs[n]
        elif (op & 0xF0FF) == 0x0012:
            regs[n] = gbr
        elif hi == 0x9:
            pool_ea = pc + 4 + disp * 2
            regs[n] = sext16(struct.unpack(">H", rom[pool_ea : pool_ea + 2])[0])
        elif hi == 0xD:
            pool_ea = ((pc + 4) & ~3) + disp * 4
            regs[n] = struct.unpack(">I", rom[pool_ea : pool_ea + 4])[0]
        elif hi == 0xE:
            regs[n] = sext8(disp)
        elif (op & 0xF00F) == 0x6003:
            regs[n] = regs[m]
        elif (op & 0xF00F) == 0x600C:
            regs[n] = (regs[m] & 0xFF) if regs[m] is not None else None
        elif (op & 0xF00F) == 0x600D:
            regs[n] = (regs[m] & 0xFFFF) if regs[m] is not None else None
        elif (op & 0xF00F) == 0x600E:
            regs[n] = sext8(regs[m] & 0xFF) if regs[m] is not None else None
        elif (op & 0xF00F) == 0x600F:
            regs[n] = sext16(regs[m] & 0xFFFF) if regs[m] is not None else None
        elif hi == 0x7:
            if regs[n] is not None:
                regs[n] = (regs[n] + sext8(disp)) & 0xFFFFFFFF
        elif (op & 0xF00F) == 0x300C:
            if regs[n] is not None and regs[m] is not None:
                regs[n] = (regs[n] + regs[m]) & 0xFFFFFFFF
            else:
                regs[n] = None
        elif hi in (0x5, 0x6, 0x8) and not (hi == 0x8 and ((op >> 8) & 0xF) in (0x0, 0x1, 0x8, 0x9, 0xB, 0xD, 0xF)):
            regs[0 if hi == 0x8 else n] = None
        elif hi == 0x0 and disp4 in (0xC, 0xD, 0xE):
            regs[n] = None
        elif hi == 0x3 and disp4 in (0x8, 0xA, 0xE, 0xF):
            regs[n] = None
        elif hi == 0x2 and disp4 in (0x9, 0xA, 0xB):
            regs[n] = None
        elif hi == 0xC and ((op >> 8) & 0xF) in (0x4, 0x5, 0x6, 0x7, 0x8, 0x9, 0xA, 0xB):
            regs[0] = None
        elif hi == 0x4 and (op & 0xFF) == 0x10:
            regs[n] = None

        if (hi == 0xB) or (hi == 0x4 and (op & 0xFF) in (0x0B, 0x2B)) or (hi == 0xA) or ((op & 0xFF00) in (0x8D00, 0x8F00)):
            in_delay = True
            if (hi == 0xB) or (hi == 0x4 and (op & 0xFF) == 0x0B):
                pending_call_clobber = True
        elif pending_call_clobber:
            pending_call_clobber = False
            for r in range(8):
                regs[r] = None

    rows = []
    for ea in sorted(reg_hits):
        rec = reg_hits[ea]
        sym = mmio_symbols.get(ea, "-")
        subsys = classify_mmio_subsystem(ea, sym)
        rows.append({
            "mmio_addr": f"FFFF{ea & 0xFFFF:04X}",
            "ida_symbol": sym,
            "subsystem": subsys,
            "total_accesses": rec["read"] + rec["write"] + rec["rmw"],
            "reads": rec["read"],
            "writes": rec["write"],
            "rmw": rec["rmw"],
            "widths": ",".join(sorted(rec["widths"])),
            "unique_functions": len(rec["funcs"]),
            "sample_sites": "; ".join(rec["sample_pcs"]),
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
    ap.add_argument("--outdir", default="INDEX")
    ap.add_argument("--catalog", default="CALIBRATIONS/discovered_tables_catalog.csv")
    ap.add_argument("--candidates", default="CALIBRATIONS/candidate_register.csv")
    args = ap.parse_args()

    rom_md5 = md5_file(args.rom)
    if rom_md5 != EXPECTED_ROM_MD5:
        raise RuntimeError(f"ROM MD5 mismatch: {rom_md5}")
    lst_sha = sha256_file(args.listing)
    if lst_sha != EXPECTED_LST_SHA256:
        raise RuntimeError(f"Listing SHA-256 mismatch: {lst_sha}")

    with open(args.rom, "rb") as f:
        rom = f.read()

    os.makedirs(args.outdir, exist_ok=True)
    code_lines, mmio_symbols = parse_listing_and_mmio_symbols(args.listing, rom)

    m01_rows = build_obd_mode01(code_lines, rom, os.path.join(args.outdir, "obd_mode01_pid_map.tsv"))
    c22_rows = build_consult_mode22(
        rom, args.catalog, args.candidates, m01_rows, os.path.join(args.outdir, "consult_mode22_pid_map.tsv")
    )
    dtc_slots, dtc_events = build_dtc_198_and_writers(
        code_lines,
        rom,
        os.path.join(args.outdir, "dtc_198_crosswalk.tsv"),
        os.path.join(args.outdir, "dtc_198_and_writers.tsv"),
    )
    mmio_rows = build_sh7058_mmio_census(
        code_lines, mmio_symbols, rom, os.path.join(args.outdir, "sh7058_mmio_census.tsv")
    )

    with_writers = sum(1 for r in dtc_slots if r["writer_count"] > 0)
    with_direct_writers = sum(1 for r in dtc_slots if r["direct_writer_count"] > 0)
    with_write_helpers = sum(1 for r in dtc_slots if r["write_helper_count"] > 0)
    with_read_helpers = sum(1 for r in dtc_slots if r["read_helper_count"] > 0)
    print(f"Verified ROM MD5={rom_md5}, LST SHA256={lst_sha[:16]}..., code_lines={len(code_lines)}, mmio_syms={len(mmio_symbols)}")
    print(f"1. obd_mode01_pid_map.tsv: {len(m01_rows)} PIDs")
    print(f"2. consult_mode22_pid_map.tsv: {len(c22_rows)} CIDs")
    print(f"3. dtc_198_crosswalk.tsv: {len(dtc_slots)} slots (any_writer={with_writers} [direct={with_direct_writers}, write_helper={with_write_helpers}], read_helpers={with_read_helpers})")
    print(f"4. dtc_198_and_writers.tsv: {len(dtc_events)} access/helper events")
    print(f"5. sh7058_mmio_census.tsv: {len(mmio_rows)} dereferenced MMIO registers")


if __name__ == "__main__":
    main()
