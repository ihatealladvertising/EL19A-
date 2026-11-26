#!/usr/bin/env python3
"""
SH7058/SH7055 Nissan/Hitachi Lookup-Helper & Calibration Table Auto-Scanner
Read-only cross-ROM analysis tool:
  1. Auto-discovers 2D/3D ROM-axis and implicit-grid lookup helpers in Nissan/Hitachi SH7055/SH7058 ROMs (.bin or .zip),
     covering both modern post-cal (`mov.l` >= 0x15000) and earlier pre-cal (`mov.w` < 0x10000) helper layouts.
  2. Extracts every call-site (table_addr, axis1_addr, axis2_addr, dims, widths) via local SH-2 register tracking.
  3. Compares extracted tables across EL19A, EL13A, 8W83B, C12W 3DD9A, Qashqai 1TRKH1HN, EE310, EM62B, and CF48D,
     and audits EL19A (and optionally CF48D) against RomRaider XML definitions.
"""
import argparse
import csv
import hashlib
import json
import sys
import struct
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def read_rom_bytes(path: Path) -> bytes:
    """Load a raw ROM binary from .bin or the largest member inside a .zip archive."""
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as zf:
            members = [info for info in zf.infolist() if not info.is_dir()]
            if not members:
                raise ValueError(f"Empty zip archive: {path}")
            bin_members = [m for m in members if m.filename.lower().endswith(".bin")]
            target = max(bin_members or members, key=lambda m: m.file_size)
            return zf.read(target.filename)
    return path.read_bytes()


def u16(rom: bytes, pc: int) -> int:
    return struct.unpack(">H", rom[pc : pc + 2])[0]


def s16(rom: bytes, pc: int) -> int:
    return struct.unpack(">h", rom[pc : pc + 2])[0]


def u32(rom: bytes, pc: int) -> int:
    return struct.unpack(">I", rom[pc : pc + 4])[0]


def s8(v: int) -> int:
    return v - 256 if v >= 128 else v


def s12(v: int) -> int:
    return v - 4096 if v >= 2048 else v


def resolve_pc_pool(rom: bytes, pc: int, insn: int) -> Optional[int]:
    """Resolve `mov.l @(d,PC),rN` (0xDNxx) or `mov.w @(d,PC),rN` (0x9Nxx) to its 32-bit loaded value."""
    top = (insn >> 12) & 0xF
    if top == 0xD:
        ea = (pc & ~3) + 4 + (insn & 0xFF) * 4
        if ea + 4 <= len(rom):
            return u32(rom, ea)
    elif top == 0x9:
        ea = pc + 4 + (insn & 0xFF) * 2
        if ea + 2 <= len(rom):
            return s16(rom, ea) & 0xFFFFFFFF
    return None


@dataclass
class HelperSpec:
    addr: int
    kind: str          # "2D_IMPL", "2D_AXIS", "3D_IMPL", "3D_AXIS"
    elem_type: str     # "uint8", "int8", "uint16", "int16", "unknown"
    dim1: int
    dim2: int
    axis1_type: str    # "uint8", "uint16", "implicit_u8", "implicit_u16", "unknown"
    axis2_type: str    # "", "uint8", "uint16", "implicit_u8", "implicit_u16", "unknown"
    sub_search1: int = 0
    sub_search2: int = 0


def classify_search_sub(rom: bytes, sub_addr: int) -> Tuple[str, str]:
    """Classify an axis-search or interp sub-helper."""
    if not (0x02000 <= sub_addr < len(rom) - 32):
        return ("unknown", "unknown")
    insns = [u16(rom, sub_addr + 2 * i) for i in range(28)]
    has_mov_b_idx = any((w & 0xF00F) == 0x000C or (w & 0xFF00) == 0x8400 for w in insns)
    has_mov_w_idx = any((w & 0xF00F) == 0x000D or (w & 0xFF00) == 0x8500 for w in insns)
    has_exts = any((w & 0xF00E) == 0x600E for w in insns)
    if any((w & 0xF0FF) == 0x4000 for w in insns[:8]):
        return ("uint16", "signed" if has_exts else "unsigned")
    if has_mov_b_idx and not has_mov_w_idx:
        return ("uint8", "signed" if has_exts else "unsigned")
    if has_mov_w_idx:
        return ("uint16", "signed" if has_exts else "unsigned")
    return ("unknown", "signed" if has_exts else "unsigned")


def discover_helpers(rom: bytes, search_lo: int = 0x04000, search_hi: int = 0x80000) -> Dict[int, HelperSpec]:
    """
    Auto-locate Nissan/Hitachi lookup helpers by matching the 4 structural stub idioms
    across pre-cal (0x05xxx..0x07xxx, `mov.w` 0x97xx/0x96xx) and post-cal (0x15xxx..0x27xxx, `mov.l` 0xD7xx/0xD6xx) layouts.
    """
    helpers: Dict[int, HelperSpec] = {}
    n = min(search_hi, len(rom) - 64)

    for pc in range(search_lo, n, 2):
        w0 = u16(rom, pc)
        w1 = u16(rom, pc + 2)
        w2 = u16(rom, pc + 4)
        w3 = u16(rom, pc + 6)
        w4 = u16(rom, pc + 8)
        w5 = u16(rom, pc + 10)

        # Pattern A: 2D implicit fixed-grid stub
        # 90xx/D0xx; 655C/655D (extu.b/w r5,r5); 3502 (cmp/hs r0,r5); 8902 (bt +4); D6xx/96xx; 462B (jmp @r6)
        if (w0 & 0xFF00) in (0x9000, 0xD000) and w1 in (0x655C, 0x655D) and w2 == 0x3502 and w3 == 0x8902 and (w4 & 0xFF00) in (0xD600, 0x9600) and w5 == 0x462B:
            max_val = u16(rom, pc + 4 + (w0 & 0xFF) * 2) if (w0 & 0xFF00) == 0x9000 else u32(rom, (pc & ~3) + 4 + (w0 & 0xFF) * 4)
            tail = resolve_pc_pool(rom, pc + 8, w4) or 0
            w7 = u16(rom, pc + 14)
            w8 = u16(rom, pc + 16)
            w9 = u16(rom, pc + 18)
            is_u8_query = (w1 == 0x655C)
            ax_t = "implicit_u8" if is_u8_query else "implicit_u16"

            # Determine element type from clamp return instruction (844x / 854x or 74xx + 000B + 6040/6041)
            is_word_elem = False
            elem_t = "unknown"
            if (w8 & 0xFF00) == 0x8400:
                is_word_elem = False
                elem_t = "int8" if (0x02000 <= tail < len(rom) - 36 and any((u16(rom, tail + 2 * i) & 0xF00F) == 0x600E for i in range(18))) else "uint8"
            elif (w8 & 0xFF00) == 0x8500:
                is_word_elem = True
                elem_t = "int16" if (0x02000 <= tail < len(rom) - 36 and any((u16(rom, tail + 2 * i) & 0xF00F) == 0x600F for i in range(18))) else "uint16"
            elif (w7 & 0xFF00) == 0x7400 and w8 == 0x000B and w9 in (0x6040, 0x6041):
                is_word_elem = (w9 == 0x6041)
                if is_word_elem:
                    elem_t = "int16" if (0x02000 <= tail < len(rom) - 36 and any((u16(rom, tail + 2 * i) & 0xF00F) == 0x600F for i in range(18))) else "uint16"
                else:
                    elem_t = "int8" if (0x02000 <= tail < len(rom) - 36 and any((u16(rom, tail + 2 * i) & 0xF00F) == 0x600E for i in range(18))) else "uint8"

            # Determine point count cleanly: exact clamp offset if 74xx, else canonical grid step, else 844d/854d offset
            pts = 0
            if (w7 & 0xFF00) == 0x7400 and w8 == 0x000B and w9 in (0x6040, 0x6041):
                clamp_bytes = w7 & 0xFF
                pts = (clamp_bytes // 2 + 1) if is_word_elem else (clamp_bytes + 1)
            if pts == 0:
                if is_u8_query:
                    step = 256 - max_val if 0 < max_val < 256 else 0
                    pts = (max_val // step + 1) if step and max_val % step == 0 else 0
                else:
                    step = 65536 - max_val if 0 < max_val < 65536 else 0
                    pts = (max_val // step + 1) if step and max_val % step == 0 else 0
            if pts == 0 and (w8 & 0xFF00) in (0x8400, 0x8500):
                pts = (w8 & 0xF) + 1

            helpers[pc] = HelperSpec(pc, "2D_IMPL", elem_t, pts, 1, ax_t, "", tail, 0)
            continue

        # Pattern B: 2D ROM-axis stub
        # 4F22; 2F46; 6053; 656C/656D; D7xx/97xx; 470B (jsr @r7); E4xx
        if w0 == 0x4F22 and w1 == 0x2F46 and w2 == 0x6053 and w3 in (0x656C, 0x656D) and (w4 & 0xFF00) in (0xD700, 0x9700) and w5 == 0x470B:
            w6 = u16(rom, pc + 12)
            if (w6 & 0xFF00) == 0xE400:
                n_imm = w6 & 0xFF
                sub_s = resolve_pc_pool(rom, pc + 8, w4) or 0
                body = [u16(rom, pc + 14 + 2 * i) for i in range(16)]
                has_mov_b_r6 = any((w & 0xFF00) == 0x8400 and (w & 0x00F0) == 0x0060 for w in body) or any((w & 0xF00F) == 0x600C for w in body)
                has_mov_w_r6 = any((w & 0xFF00) == 0x8500 and (w & 0x00F0) == 0x0060 for w in body)
                has_exts_b = any((w & 0xF00F) == 0x600E for w in body)
                has_exts_w = any((w & 0xF00F) == 0x600F for w in body)
                signed_hint = has_exts_b or has_exts_w
                for i, bw in enumerate(body):
                    if (bw & 0xFF00) in (0xD600, 0x9600):
                        interp_fn = resolve_pc_pool(rom, pc + 14 + 2 * i, bw) or 0
                        if 0x02000 <= interp_fn < len(rom) - 36:
                            if any((u16(rom, interp_fn + 2 * k) & 0xF00E) == 0x600E for k in range(16)):
                                signed_hint = True
                ax_t = "uint8" if w3 == 0x656C else "uint16"
                pts = (n_imm // 2 + 1) if ax_t == "uint16" else (n_imm + 1)
                if has_mov_b_r6 and not has_mov_w_r6:
                    elem_t = "int8" if signed_hint else "uint8"
                else:
                    elem_t = "int16" if signed_hint else "uint16"
                helpers[pc] = HelperSpec(pc, "2D_AXIS", elem_t, pts, 1, ax_t, "", sub_s, 0)
                continue

        # Pattern C: 3D ROM-axis stub
        # 4F22; 2F46; 677C/677D; 6053; 6573; D7xx/97xx; 470B; E4xx
        if w0 == 0x4F22 and w1 == 0x2F46 and w2 in (0x677C, 0x677D) and w3 == 0x6053 and w4 == 0x6573 and (w5 & 0xFF00) in (0xD700, 0x9700):
            w6 = u16(rom, pc + 12)
            w7 = u16(rom, pc + 14)
            if w6 == 0x470B and (w7 & 0xFF00) == 0xE400:
                n1 = w7 & 0xFF
                sub1 = resolve_pc_pool(rom, pc + 10, w5) or 0
                ax1_word_tbl = any((u16(rom, sub1 + 2 * k) & 0xF00F) == 0x000D for k in range(18) if 0x02000 <= sub1 < len(rom) - 36)
                ax1_t = "uint16" if ax1_word_tbl else "uint8"
                dim1 = (n1 // 2 + 1) if ax1_word_tbl else (n1 + 1)

                body = [u16(rom, pc + 16 + 2 * i) for i in range(28)]
                dim2, ax2_t, sub2 = dim1, ax1_t, sub1
                interp_tail = 0
                for i, bw in enumerate(body):
                    bpc = pc + 16 + 2 * i
                    if (bw & 0xFF00) in (0xD700, 0x9700):
                        cand = resolve_pc_pool(rom, bpc, bw) or 0
                        if i + 1 < len(body) and body[i + 1] == 0x470B:
                            sub2 = cand
                        elif i + 1 < len(body) and body[i + 1] == 0x472B:
                            interp_tail = cand
                    if (bw & 0xFF00) == 0xE400 and i > 0 and body[i - 1] == 0x470B:
                        n2 = bw & 0xFF
                        ax2_word_tbl = any((u16(rom, sub2 + 2 * k) & 0xF00F) == 0x000D for k in range(18) if 0x02000 <= sub2 < len(rom) - 36)
                        ax2_t = "uint16" if ax2_word_tbl else "uint8"
                        dim2 = (n2 // 2 + 1) if ax2_word_tbl else (n2 + 1)
                    if bw == 0x472B and i + 1 < len(body) and (body[i + 1] & 0xFF00) == 0xE500:
                        dim2 = body[i + 1] & 0xFF
                        break

                elem_t = "uint8"
                if 0x02000 <= interp_tail < len(rom) - 64:
                    t_insns = [u16(rom, interp_tail + 2 * k) for k in range(24)]
                    if any((tw & 0xFF00) == 0x8500 for tw in t_insns):
                        elem_t = "int16" if any((tw & 0xF00F) == 0x600F for tw in t_insns) else "uint16"
                    else:
                        elem_t = "int8" if any((tw & 0xF00F) == 0x600E for tw in t_insns) else "uint8"
                helpers[pc] = HelperSpec(pc, "3D_AXIS", elem_t, dim1, dim2, ax1_t, ax2_t, sub1, sub2)
                continue

        # Pattern D: 3D implicit fixed-grid stub
        # 4F22; 2F86; 2F46; 636C/636D; D7xx/97xx; 645C/645D; 470B; E500
        if w0 == 0x4F22 and w1 == 0x2F86 and w2 == 0x2F46 and w3 in (0x636C, 0x636D) and (w4 & 0xFF00) in (0xD700, 0x9700) and w5 in (0x645C, 0x645D):
            w6 = u16(rom, pc + 12)
            w7 = u16(rom, pc + 14)
            if w6 == 0x470B and w7 == 0xE500:
                is_u8 = (w3 == 0x636C)
                elem_t = "uint8" if is_u8 else "uint16"
                ax_t = "implicit_u8" if is_u8 else "implicit_u16"
                dim = 16
                for k in range(8, 28):
                    bw = u16(rom, pc + 2 * k)
                    if bw == 0x472B and (u16(rom, pc + 2 * (k + 1)) & 0xFF00) == 0xE500:
                        dim = u16(rom, pc + 2 * (k + 1)) & 0xFF
                        break
                helpers[pc] = HelperSpec(pc, "3D_IMPL", elem_t, dim, dim, ax_t, ax_t, 0, 0)
                continue

    return helpers


def infer_layout(rom: bytes, helpers: Dict[int, HelperSpec]) -> Tuple[int, int, int]:
    """Infer (code_start, cal_lo, cal_hi) from discovered helper band."""
    if not helpers:
        return (0x20000, 0x04000, 0x20000)
    min_h = min(helpers)
    max_h = max(helpers)
    if min_h < 0x10000:
        # Early pre-cal helper layout (e.g., EE310 / CF48D): helpers ~0x05xxx-0x07xxx, cal right after, callers mostly >= 0x10000
        return (max_h + 0x200, max_h + 0x200, 0x14000)
    if min_h < 0x20000:
        # SH7055 mid-ROM layout (e.g., EM62B): helpers ~0x15xxx
        return (min_h & ~0xFFF, 0x04000, min_h & ~0xFFF)
    return (0x20000, 0x04000, 0x20000)


def extract_calls(rom: bytes, helpers: Dict[int, HelperSpec], code_start: Optional[int] = None) -> List[dict]:
    """
    Scan executable code for calls to any discovered helper.
    Tracks simple forward register state (mov.l/mov.w PC-rel, mov #imm, mov Rm,Rn, add #imm, extu/exts, clear on prior call).
    """
    if not helpers:
        return []
    inferred_code_start, cal_lo, cal_hi = infer_layout(rom, helpers)
    scan_start = code_start if code_start is not None else inferred_code_start
    calls = []
    code_end = len(rom) - 2
    min_h, max_h = min(helpers), max(helpers)

    def eval_window(call_pc: int, delay_insn: Optional[int], target_reg: Optional[int]) -> Dict[int, Optional[int]]:
        win_start = max(scan_start, call_pc - 56)
        for p in range(call_pc - 2, win_start - 2, -2):
            if u16(rom, p) == 0x000B:
                win_start = p + 4
                break
        st: Dict[int, Optional[int]] = {i: None for i in range(16)}
        for p in range(win_start, call_pc, 2):
            w = u16(rom, p)
            n = (w >> 8) & 0xF
            m = (w >> 4) & 0xF
            top = (w >> 12) & 0xF
            if top == 0xD:
                ea = (p & ~3) + 4 + (w & 0xFF) * 4
                if ea + 4 <= len(rom):
                    st[n] = u32(rom, ea)
            elif top == 0x9:
                ea = p + 4 + (w & 0xFF) * 2
                if ea + 2 <= len(rom):
                    v = u16(rom, ea)
                    st[n] = v - 65536 if v >= 32768 else v
            elif top == 0xE:
                st[n] = s8(w & 0xFF) & 0xFFFFFFFF
            elif (w & 0xF00F) == 0x6003:
                st[n] = st[m]
            elif (w & 0xF00F) == 0x600C:
                st[n] = (st[m] & 0xFF) if st[m] is not None else None
            elif (w & 0xF00F) == 0x600D:
                st[n] = (st[m] & 0xFFFF) if st[m] is not None else None
            elif (w & 0xF00F) == 0x600E:
                st[n] = s8(st[m] & 0xFF) & 0xFFFFFFFF if st[m] is not None else None
            elif (w & 0xF00F) == 0x600F:
                v = st[m] & 0xFFFF if st[m] is not None else None
                st[n] = ((v - 65536) if v >= 32768 else v) & 0xFFFFFFFF if v is not None else None
            elif top == 0x7:
                if st[n] is not None:
                    st[n] = (st[n] + s8(w & 0xFF)) & 0xFFFFFFFF
            elif top == 0xB or (w & 0xF0FF) == 0x400B:
                for r in range(8):
                    if r != target_reg:
                        st[r] = None
            elif (w & 0xF0FF) in (0x0023, 0x4008, 0x4018, 0x4028):
                st[n] = None
        if delay_insn is not None:
            w = delay_insn
            n = (w >> 8) & 0xF
            m = (w >> 4) & 0xF
            top = (w >> 12) & 0xF
            if top == 0xD:
                ea = ((call_pc + 2) & ~3) + 4 + (w & 0xFF) * 4
                if ea + 4 <= len(rom):
                    st[n] = u32(rom, ea)
            elif top == 0x9:
                ea = (call_pc + 2) + 4 + (w & 0xFF) * 2
                if ea + 2 <= len(rom):
                    v = u16(rom, ea)
                    st[n] = v - 65536 if v >= 32768 else v
            elif top == 0xE:
                st[n] = s8(w & 0xFF) & 0xFFFFFFFF
            elif (w & 0xF00F) == 0x6003:
                st[n] = st[m]
            elif (w & 0xF00F) == 0x600C:
                st[n] = (st[m] & 0xFF) if st[m] is not None else None
            elif (w & 0xF00F) == 0x600D:
                st[n] = (st[m] & 0xFFFF) if st[m] is not None else None
            elif (w & 0xF00F) == 0x600E:
                st[n] = s8(st[m] & 0xFF) & 0xFFFFFFFF if st[m] is not None else None
            elif (w & 0xF00F) == 0x600F:
                v = st[m] & 0xFFFF if st[m] is not None else None
                st[n] = ((v - 65536) if v >= 32768 else v) & 0xFFFFFFFF if v is not None else None
            elif top == 0x7 and st[n] is not None:
                st[n] = (st[n] + s8(w & 0xFF)) & 0xFFFFFFFF
        return st

    helper_set = set(helpers.keys())
    for pc in range(scan_start, code_end, 2):
        w = u16(rom, pc)
        target = None
        call_pc = None
        delay = None
        treg = None
        call_form = None
        top = w >> 12

        if top in (0xD, 0x9):  # mov.l or mov.w @(d,PC),rN
            val = resolve_pc_pool(rom, pc, w)
            if val is not None and val in helper_set:
                rn = (w >> 8) & 0xF
                for k in range(1, 21):
                    cpc = pc + 2 * k
                    if cpc >= code_end:
                        break
                    cw = u16(rom, cpc)
                    if cw in (0x400B | (rn << 8), 0x402B | (rn << 8)):
                        target = val
                        call_pc = cpc
                        delay = u16(rom, cpc + 2)
                        treg = rn
                        call_form = "indirect_jsr" if cw == (0x400B | (rn << 8)) else "indirect_jmp"
                        break
                    if cw == 0x000B:  # rts before call
                        break
                    if (cw >> 12) in (0xD, 0x9, 0xE) and ((cw >> 8) & 0xF) == rn:
                        break
        elif top == 0xB:  # bsr
            tgt = pc + 4 + s12(w & 0xFFF) * 2
            if tgt in helper_set:
                target = tgt
                call_pc = pc
                delay = u16(rom, pc + 2)
                call_form = "bsr"

        if target is not None and call_pc is not None:
            if min_h <= call_pc <= max_h + 0x100:
                continue
            st = eval_window(call_pc, delay, treg)
            h = helpers[target]
            r4, r5, r6 = st.get(4), st.get(5), st.get(6)

            def is_rom_cal(x):
                return x is not None and cal_lo <= x < cal_hi and not (min_h - 0x200 <= x <= max_h + 0x200)

            tbl = r4 if is_rom_cal(r4) else None
            ax1 = r5 if (h.kind in ("2D_AXIS", "3D_AXIS") and is_rom_cal(r5)) else None
            ax2 = r6 if (h.kind == "3D_AXIS" and is_rom_cal(r6)) else None
            calls.append({
                "call_pc": call_pc,
                "call_form": call_form,
                "target_load_pc": None if treg is None else pc,
                "target_register": treg,
                "call_instruction": u16(rom, call_pc),
                "delay_slot": delay,
                "scan_start": scan_start,
                "helper": target,
                "kind": h.kind,
                "elem_type": h.elem_type,
                "dim1": h.dim1,
                "dim2": h.dim2,
                "axis1_type": h.axis1_type,
                "axis2_type": h.axis2_type,
                "table": tbl,
                "axis1": ax1,
                "axis2": ax2,
                "raw_r4": r4,
                "raw_r5": r5,
                "raw_r6": r6,
            })
    return calls


def load_xml_tables(xml_path: Path) -> Dict[int, dict]:
    tree = ET.parse(xml_path)
    out = {}
    for t in tree.getroot().findall(".//table"):
        sa = t.attrib.get("storageaddress")
        tp = t.attrib.get("type", "")
        if not sa or tp in ("X Axis", "Y Axis"):
            continue
        addr = int(sa, 16)
        axes = {}
        for ch in t.findall("./table"):
            atp = ch.attrib.get("type", "")
            asa = ch.attrib.get("storageaddress")
            axes[atp] = int(asa, 16) if asa else None
        out[addr] = {
            "name": t.attrib.get("name", ""),
            "type": tp,
            "storagetype": t.attrib.get("storagetype", ""),
            "sizex": int(t.attrib.get("sizex", "1")),
            "sizey": int(t.attrib.get("sizey", "1")),
            "axes": axes,
        }
    return out



def _element_width(elem_type: str) -> Optional[int]:
    """Return storage width in bytes for a recognized scalar element type."""
    if elem_type in ("uint8", "int8"):
        return 1
    if elem_type in ("uint16", "int16"):
        return 2
    return None


def _address_hex(value: Optional[int]) -> Optional[str]:
    return None if value is None else f"0x{value:05X}"


def _export_span(rom: bytes, addr: Optional[int], count: int, elem_type: str) -> dict:
    """Describe an exclusive-end ROM span; never silently truncate an invalid extent."""
    width = _element_width(elem_type)
    if addr is None or width is None or count <= 0:
        status = "unresolved_address" if addr is None else ("unknown_element_width" if width is None else "invalid_element_count")
        return {
            "start": addr, "start_hex": _address_hex(addr), "count": count,
            "element_type": elem_type, "element_width_bytes": width,
            "byte_length": None, "end_exclusive": None, "end_exclusive_hex": None,
            "in_bounds": False, "status": status, "sha256": None, "distinct_byte_values": None,
        }
    end = addr + count * width
    in_bounds = 0 <= addr < end <= len(rom)
    payload = rom[addr:end] if in_bounds else None
    return {
        "start": addr, "start_hex": _address_hex(addr), "count": count,
        "element_type": elem_type, "element_width_bytes": width,
        "byte_length": count * width, "end_exclusive": end,
        "end_exclusive_hex": _address_hex(end), "in_bounds": in_bounds,
        "status": "in_bounds" if in_bounds else "out_of_bounds",
        "sha256": hashlib.sha256(payload).hexdigest() if payload is not None else None,
        "distinct_byte_values": len(set(payload)) if payload is not None else None,
    }


def _call_context(rom: bytes, call_pc: int, scan_start: int) -> dict:
    """Preserve the exact bounded instruction words used for the register-window audit."""
    window_start = max(scan_start, call_pc - 56)
    for p in range(call_pc - 2, window_start - 2, -2):
        if 0 <= p <= len(rom) - 2 and u16(rom, p) == 0x000B:
            window_start = p + 4
            break
    window_end = min(len(rom) - (len(rom) % 2), call_pc + 4)
    words = [
        {"pc": p, "pc_hex": _address_hex(p), "word": u16(rom, p), "word_hex": f"0x{u16(rom, p):04X}"}
        for p in range(window_start, window_end, 2)
        if 0 <= p <= len(rom) - 2
    ]
    caller_candidate = None
    caller_floor = max(scan_start, call_pc - 0x800)
    for p in range(call_pc - 2, caller_floor - 2, -2):
        if 0 <= p <= len(rom) - 2 and u16(rom, p) == 0x4F22:
            caller_candidate = p
            break
    return {
        "window_start": window_start,
        "window_start_hex": _address_hex(window_start),
        "window_end_exclusive": window_end,
        "window_end_exclusive_hex": _address_hex(window_end),
        "instruction_words": words,
        "caller_start_candidate": caller_candidate,
        "caller_start_candidate_hex": _address_hex(caller_candidate),
        "caller_boundary_method": "nearest_0x4F22_within_0x800_bytes_heuristic" if caller_candidate is not None else "not_found",
    }


def build_scan_export(input_path: str, rom: bytes, helpers: Dict[int, HelperSpec], calls: List[dict],
                      xml_path: Optional[str] = None, xml_tables: Optional[Dict[int, dict]] = None) -> dict:
    """Build a complete, JSON-safe per-helper, per-call and per-table audit record."""
    code_start, cal_lo, cal_hi = infer_layout(rom, helpers)
    call_rows = []
    table_groups = {}

    for call in calls:
        helper = helpers[call["helper"]]
        width = _element_width(call["elem_type"])
        point_count = call["dim1"] * call["dim2"] if call["dim1"] > 0 and call["dim2"] > 0 else 0
        data_span = _export_span(rom, call["table"], point_count, call["elem_type"])
        axis1_span = _export_span(rom, call["axis1"], call["dim1"], call["axis1_type"]) if call["axis1"] is not None else None
        axis2_span = _export_span(rom, call["axis2"], call["dim2"], call["axis2_type"]) if call["axis2"] is not None else None

        raw_regs = {}
        for reg in (4, 5, 6):
            value = call.get(f"raw_r{reg}")
            raw_regs[f"r{reg}"] = {"value": value, "hex": _address_hex(value)}

        context = _call_context(rom, call["call_pc"], code_start)
        if call["table"] is not None:
            resolution = ("candidate_r4_pointer_inside_inferred_calibration_window_and_extent_in_bounds"
                          if data_span["status"] == "in_bounds"
                          else "candidate_r4_pointer_inside_inferred_calibration_window_but_extent_unverified")
        elif call.get("raw_r4") is None:
            resolution = "unresolved_r4_in_bounded_register_window"
        else:
            resolution = "r4_value_outside_inferred_calibration_window_or_excluded_helper_band"

        row = {
            "call_pc": call["call_pc"], "call_pc_hex": _address_hex(call["call_pc"]),
            "call_instruction": call["call_instruction"], "call_instruction_hex": f"0x{call['call_instruction']:04X}",
            "call_form": call["call_form"], "target_load_pc": call["target_load_pc"],
            "target_load_pc_hex": _address_hex(call["target_load_pc"]), "target_register": call["target_register"],
            "delay_slot": call["delay_slot"],
            "delay_slot_hex": None if call["delay_slot"] is None else f"0x{call['delay_slot']:04X}",
            "helper": call["helper"], "helper_hex": _address_hex(call["helper"]),
            "helper_kind": call["kind"], "element_type": call["elem_type"], "element_width_bytes": width,
            "dim1": call["dim1"], "dim2": call["dim2"],
            "axis1_type": call["axis1_type"], "axis2_type": call["axis2_type"],
            "table": call["table"], "table_hex": _address_hex(call["table"]),
            "axis1": call["axis1"], "axis1_hex": _address_hex(call["axis1"]),
            "axis2": call["axis2"], "axis2_hex": _address_hex(call["axis2"]),
            "raw_registers": raw_regs,
            "caller_start_candidate": context["caller_start_candidate"],
            "caller_start_candidate_hex": context["caller_start_candidate_hex"],
            "resolution_status": resolution,
            "table_span": data_span, "axis1_span": axis1_span, "axis2_span": axis2_span,
            "argument_evidence_method": "bounded_linear_register_window_56_bytes_plus_call_delay_slot",
            "argument_evidence_limits": [
                "register values are static-window candidates, not full control-flow/data-flow proofs",
                "instruction words are supplied for independent caller-side review",
                "caller_start_candidate is a nearest-prologue heuristic, not a proven function boundary",
                "query register/source, signedness and downstream consumer are not inferred by this export",
            ],
            "instruction_context": context,
        }
        call_rows.append(row)

        if call["table"] is not None:
            group = table_groups.setdefault(call["table"], {
                "table": call["table"], "table_hex": _address_hex(call["table"]),
                "call_pcs": [], "helper_addresses": [], "helper_kinds": [],
                "geometry_variants": [], "axis1_variants": [], "axis2_variants": [],
            })
            group["call_pcs"].append(call["call_pc"])
            group["helper_addresses"].append(call["helper"])
            group["helper_kinds"].append(call["kind"])
            variant = {
                "helper_kind": call["kind"], "element_type": call["elem_type"],
                "element_width_bytes": width, "dim1": call["dim1"], "dim2": call["dim2"],
                "byte_length": data_span["byte_length"], "end_exclusive": data_span["end_exclusive"],
                "end_exclusive_hex": data_span["end_exclusive_hex"], "in_bounds": data_span["in_bounds"],
                "payload_sha256": data_span["sha256"],
                "distinct_byte_values": data_span["distinct_byte_values"],
            }
            if variant not in group["geometry_variants"]:
                group["geometry_variants"].append(variant)
            if axis1_span is not None:
                av = {"address": call["axis1"], "type": call["axis1_type"], "count": call["dim1"],
                      "end_exclusive": axis1_span["end_exclusive"], "sha256": axis1_span["sha256"]}
                if av not in group["axis1_variants"]:
                    group["axis1_variants"].append(av)
            if axis2_span is not None:
                av = {"address": call["axis2"], "type": call["axis2_type"], "count": call["dim2"],
                      "end_exclusive": axis2_span["end_exclusive"], "sha256": axis2_span["sha256"]}
                if av not in group["axis2_variants"]:
                    group["axis2_variants"].append(av)

    tables = []
    for _, group in sorted(table_groups.items()):
        group["call_pcs"] = sorted(set(group["call_pcs"]))
        group["helper_addresses"] = sorted(set(group["helper_addresses"]))
        group["helper_kinds"] = sorted(set(group["helper_kinds"]))
        group["geometry_conflict"] = len(group["geometry_variants"]) > 1
        group["axis1_conflict"] = len(group["axis1_variants"]) > 1
        group["axis2_conflict"] = len(group["axis2_variants"]) > 1
        tables.append(group)

    helper_rows = []
    for addr, helper in sorted(helpers.items()):
        helper_rows.append({
            "address": addr, "address_hex": _address_hex(addr), "kind": helper.kind,
            "element_type": helper.elem_type, "dim1": helper.dim1, "dim2": helper.dim2,
            "axis1_type": helper.axis1_type, "axis2_type": helper.axis2_type,
            "sub_search1": helper.sub_search1, "sub_search1_hex": _address_hex(helper.sub_search1),
            "sub_search2": helper.sub_search2, "sub_search2_hex": _address_hex(helper.sub_search2),
        })

    input_file_hash = None
    input_file_size = None
    selected_archive_member = None
    if Path(input_path).suffix.lower() == ".zip":
        try:
            with zipfile.ZipFile(input_path) as zf:
                members = [info for info in zf.infolist() if not info.is_dir()]
                bin_members = [m for m in members if m.filename.lower().endswith(".bin")]
                target_member = max(bin_members or members, key=lambda m: m.file_size) if members else None
                selected_archive_member = target_member.filename if target_member else None
        except (OSError, zipfile.BadZipFile):
            selected_archive_member = None
    try:
        source_bytes = Path(input_path).read_bytes()
        input_file_hash = hashlib.sha256(source_bytes).hexdigest()
        input_file_size = len(source_bytes)
    except OSError:
        pass

    xml_addrs = set((xml_tables or {}).keys())
    resolved_addrs = set(table_groups.keys())
    return {
        "schema": "sh7058-cross-rom-scan-v1",
        "input": {
            "path": input_path, "container_size_bytes": input_file_size, "container_sha256": input_file_hash,
            "selected_archive_member": selected_archive_member,
            "decoded_rom_size_bytes": len(rom), "decoded_rom_sha256": hashlib.sha256(rom).hexdigest(),
        },
        "tool": {
            "name": "sh7058_cross_rom_scanner.py",
            "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "python_version": sys.version.split()[0], "command_line": list(sys.argv),
        },
        "layout": {
            "code_start": code_start, "code_start_hex": _address_hex(code_start),
            "calibration_start": cal_lo, "calibration_start_hex": _address_hex(cal_lo),
            "calibration_end_exclusive": cal_hi, "calibration_end_exclusive_hex": _address_hex(cal_hi),
            "inference_method": "infer_layout_heuristic",
        },
        "summary": {
            "helper_count": len(helpers), "helper_counts_by_kind": dict(Counter(h.kind for h in helpers.values())),
            "call_count": len(call_rows), "call_counts_by_kind": dict(Counter(row["helper_kind"] for row in call_rows)),
            "transfer_counts_by_form": dict(Counter(row["call_form"] for row in call_rows)),
            "resolved_call_count": sum(1 for row in call_rows if row["table"] is not None),
            "unresolved_call_count": sum(1 for row in call_rows if row["table"] is None),
            "resolved_calls_with_unverified_extent": sum(1 for row in call_rows if row["table"] is not None and row["table_span"]["status"] != "in_bounds"),
            "unique_resolved_table_bases": len(tables),
            "tables_with_geometry_conflicts": sum(1 for row in tables if row["geometry_conflict"]),
        },
        "xml_comparison": None if xml_path is None else {
            "path": xml_path, "xml_table_count": len(xml_tables or {}),
            "scanner_bases_in_xml": len(resolved_addrs & xml_addrs),
            "scanner_bases_missing_from_xml": sorted(resolved_addrs - xml_addrs),
            "xml_table_bases_absent_from_scanner": sorted(xml_addrs - resolved_addrs),
        },
        "helpers": helper_rows, "calls": call_rows, "tables": tables,
    }



def build_cross_rom_comparisons(scans: List[dict]) -> List[dict]:
    """Compare exported unique table bases by address/kind and exact payload hash+length."""
    if len(scans) < 2:
        return []
    target = scans[0]
    target_tables = target["tables"]
    target_by_addr = {row["table"]: row for row in target_tables}
    comparisons = []
    for sibling in scans[1:]:
        same_address_kind = 0
        exact_matches = []
        nontrivial_matches = 0
        for sibling_table in sibling["tables"]:
            target_at_address = target_by_addr.get(sibling_table["table"])
            if target_at_address and set(target_at_address["helper_kinds"]) & set(sibling_table["helper_kinds"]):
                same_address_kind += 1

            pairs = []
            for sibling_variant in sibling_table["geometry_variants"]:
                shash = sibling_variant["payload_sha256"]
                ssize = sibling_variant["byte_length"]
                if shash is None or ssize is None:
                    continue
                for target_table in target_tables:
                    for target_variant in target_table["geometry_variants"]:
                        if target_variant["byte_length"] == ssize and target_variant["payload_sha256"] == shash:
                            pairs.append({
                                "target_table": target_table["table"],
                                "target_table_hex": target_table["table_hex"],
                                "sibling_table": sibling_table["table"],
                                "sibling_table_hex": sibling_table["table_hex"],
                                "byte_length": ssize,
                                "payload_sha256": shash,
                                "distinct_byte_values": sibling_variant["distinct_byte_values"],
                            })
            if pairs:
                exact_matches.append({
                    "sibling_table": sibling_table["table"],
                    "sibling_table_hex": sibling_table["table_hex"],
                    "target_matches": pairs,
                })
                if any(pair["distinct_byte_values"] is not None and pair["distinct_byte_values"] > 2 for pair in pairs):
                    nontrivial_matches += 1

        exact_bases = {row["sibling_table"] for row in exact_matches}
        relocated_bases = {
            addr for addr in exact_bases
            if not (addr in target_by_addr and set(target_by_addr[addr]["helper_kinds"]) &
                    set(next((t["helper_kinds"] for t in sibling["tables"] if t["table"] == addr), [])))
        }
        comparisons.append({
            "target_rom": target["input"]["path"],
            "target_rom_sha256": target["input"]["decoded_rom_sha256"],
            "sibling_rom": sibling["input"]["path"],
            "sibling_rom_sha256": sibling["input"]["decoded_rom_sha256"],
            "comparison_method": "same-address+shared-helper-kind; exact-payload SHA-256 plus byte-length; unique sibling table bases",
            "target_unique_table_bases": len(target_tables),
            "sibling_unique_table_bases": len(sibling["tables"]),
            "same_address_and_helper_kind_count": same_address_kind,
            "exact_payload_match_count": len(exact_bases),
            "nontrivial_exact_payload_match_count": nontrivial_matches,
            "relocated_exact_payload_match_count": len(relocated_bases),
            "exact_payload_matches": exact_matches,
        })
    return comparisons



def write_machine_exports(json_path: Optional[Path], tsv_dir: Optional[Path], scans: List[dict]) -> None:
    """Write one combined JSON evidence file and optional per-ROM TSV companions."""
    if json_path is not None:
        json_path.parent.mkdir(parents=True, exist_ok=True)
        with json_path.open("w", encoding="utf-8", newline="\n") as stream:
            json.dump({
                "schema": "sh7058-cross-rom-batch-v1",
                "scans": scans,
                "cross_rom_comparisons": build_cross_rom_comparisons(scans),
            }, stream, indent=2, sort_keys=True)
            stream.write("\n")
    if tsv_dir is None:
        return
    tsv_dir.mkdir(parents=True, exist_ok=True)
    for scan in scans:
        stem = Path(scan["input"]["path"]).stem
        suffix = scan["input"]["decoded_rom_sha256"][:8]
        prefix = f"{stem}_{suffix}"
        outputs = (
            ("calls", scan["calls"], [
                "call_pc_hex", "call_form", "target_load_pc_hex", "target_register", "caller_start_candidate_hex",
                "helper_hex", "helper_kind", "table_hex", "element_type", "dim1", "dim2",
                "axis1_hex", "axis1_type", "axis2_hex", "axis2_type", "resolution_status",
                "table_span", "axis1_span", "axis2_span", "raw_registers", "instruction_context",
            ]),
            ("tables", scan["tables"], [
                "table_hex", "call_pcs", "helper_addresses", "helper_kinds", "geometry_variants",
                "geometry_conflict", "axis1_variants", "axis1_conflict", "axis2_variants", "axis2_conflict",
            ]),
            ("helpers", scan["helpers"], [
                "address_hex", "kind", "element_type", "dim1", "dim2", "axis1_type", "axis2_type",
                "sub_search1_hex", "sub_search2_hex",
            ]),
        )
        for name, rows, fields in outputs:
            path = tsv_dir / f"{prefix}.{name}.tsv"
            with path.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=fields, delimiter="\t", lineterminator="\n")
                writer.writeheader()
                for row in rows:
                    flat = {}
                    for field in fields:
                        value = row.get(field)
                        flat[field] = json.dumps(value, sort_keys=True) if isinstance(value, (dict, list)) else value
                    writer.writerow(flat)



def main():
    ap = argparse.ArgumentParser(description="SH7055/SH7058 Nissan/Hitachi lookup-helper & table scanner")
    ap.add_argument("--el19a", default="EVIDENCE/VERSA f501.bin")
    ap.add_argument("--xml", default="CALIBRATIONS/EL19A_release1_conservative.xml")
    ap.add_argument("--cf48d-xml", default="EVIDENCE/CF48D.xml")
    ap.add_argument("--siblings", nargs="*", default=[
        "EVIDENCE/23710-EL13A-08-C11-MR18DE-CVT.bin",
        "EVIDENCE/23710-8W83B-08-C11-MR18DE-AT.bin",
        "EVIDENCE/23710-EE310-07-C11-MR18DE-MT.bin",
        "EVIDENCE/unknown_EM62B_SH7055.bin.zip",
        "EVIDENCE/CF48D.bin",
        "EVIDENCE/Nissan Tiida_C12W_3DD9A_705828N.bin",
        "EVIDENCE/Nissan_Qashqai_2006_2.0i_140_hp_Hitachi_BEDxxx_MECxxx_OBD_NR.zip",
    ])
    ap.add_argument("--json-out", type=Path, help="Write a combined JSON export with all helpers, calls, unresolved calls, table groups and ROM hashes")
    ap.add_argument("--tsv-dir", type=Path, help="Write per-ROM calls/tables/helpers TSV companions into this directory")
    args = ap.parse_args()

    el_path = Path(args.el19a)
    el_rom = read_rom_bytes(el_path)
    el_helpers = discover_helpers(el_rom)
    el_calls = extract_calls(el_rom, el_helpers)
    xml_tables = load_xml_tables(Path(args.xml))
    cf_xml_tables = load_xml_tables(Path(args.cf48d_xml)) if Path(args.cf48d_xml).exists() else {}
    machine_scans = [build_scan_export(str(el_path), el_rom, el_helpers, el_calls, str(Path(args.xml)), xml_tables)]

    print(f"=== {el_path.name} (SHA256 {hashlib.sha256(el_rom).hexdigest()[:12]}) ===")
    print(f"Auto-discovered helpers: {len(el_helpers)} (2D_IMPL={sum(1 for h in el_helpers.values() if h.kind=='2D_IMPL')}, "
          f"2D_AXIS={sum(1 for h in el_helpers.values() if h.kind=='2D_AXIS')}, "
          f"3D_IMPL={sum(1 for h in el_helpers.values() if h.kind=='3D_IMPL')}, "
          f"3D_AXIS={sum(1 for h in el_helpers.values() if h.kind=='3D_AXIS')})")
    resolved_el = [c for c in el_calls if c["table"] is not None]
    uniq_el_tables = sorted({c["table"] for c in resolved_el})
    print(f"Call sites to lookup helpers: {len(el_calls)} total, {len(resolved_el)} with resolved ROM table pointer ({len(uniq_el_tables)} unique table addrs)")

    xml_addrs = set(xml_tables.keys())
    in_xml = [a for a in uniq_el_tables if a in xml_addrs]
    missing_from_xml = [a for a in uniq_el_tables if a not in xml_addrs]
    print(f"Overlap with Release 1 XML ({len(xml_addrs)} tables): {len(in_xml)} in XML, {len(missing_from_xml)} caller-backed tables NOT in Release 1 XML")

    by_addr = defaultdict(list)
    for c in resolved_el:
        by_addr[c["table"]].append(c)
    if missing_from_xml:
        kind_cnt = Counter(by_addr[a][0]["kind"] for a in missing_from_xml)
        print(f"  Missing-from-XML breakdown by kind: {dict(kind_cnt)}")

    mismatches = []
    for a in in_xml:
        xt = xml_tables[a]
        c = by_addr[a][0]
        x_pts = xt["sizex"] * xt["sizey"]
        c_pts = c["dim1"] * c["dim2"]
        if x_pts != c_pts or (xt["storagetype"] != c["elem_type"] and not (xt["storagetype"].startswith("int") and c["elem_type"].startswith("uint"))):
            mismatches.append((a, xt, c))
    print(f"Scanner vs XML geometry/type disagreements on matched tables: {len(mismatches)}")
    for a, xt, c in mismatches[:15]:
        print(f"  DIFF 0x{a:05X}: XML={xt['type']} {xt['storagetype']} {xt['sizex']}x{xt['sizey']} | Code={c['kind']} {c['elem_type']} {c['dim1']}x{c['dim2']} @ 0x{c['call_pc']:05X}")

    el_by_sig = {}
    for a in uniq_el_tables:
        c = by_addr[a][0]
        sz = c["dim1"] * c["dim2"] * (2 if "16" in c["elem_type"] else 1)
        el_by_sig.setdefault(el_rom[a : a + sz], []).append((a, c))

    for spath_str in args.siblings:
        spath = Path(spath_str)
        if not spath.exists():
            continue
        srom = read_rom_bytes(spath)
        s_helpers = discover_helpers(srom)
        s_calls = extract_calls(srom, s_helpers)
        s_res = [c for c in s_calls if c["table"] is not None]
        s_uniq = sorted({c["table"] for c in s_res})
        s_by_addr = defaultdict(list)
        for c in s_res:
            s_by_addr[c["table"]].append(c)
        sibling_xml_path = args.cf48d_xml if "CF48D" in spath.name and Path(args.cf48d_xml).exists() else None
        sibling_xml_tables = cf_xml_tables if sibling_xml_path else None
        machine_scans.append(build_scan_export(str(spath), srom, s_helpers, s_calls, sibling_xml_path, sibling_xml_tables))

        same_addr = 0
        payload_match = 0
        nontriv_match = 0
        for sa in s_uniq:
            sc = s_by_addr[sa][0]
            if sa in by_addr and by_addr[sa][0]["kind"] == sc["kind"]:
                same_addr += 1
            sz = sc["dim1"] * sc["dim2"] * (2 if "16" in sc["elem_type"] else 1)
            blob = srom[sa : sa + sz]
            if blob in el_by_sig:
                payload_match += 1
                if len(set(blob)) > 2:
                    nontriv_match += 1

        print(f"\n=== Sibling: {spath.name} (SHA256 {hashlib.sha256(srom).hexdigest()[:12]}) ===")
        print(f"  Auto-discovered helpers: {len(s_helpers)} (2D_IMPL={sum(1 for h in s_helpers.values() if h.kind=='2D_IMPL')}, "
              f"2D_AXIS={sum(1 for h in s_helpers.values() if h.kind=='2D_AXIS')}, "
              f"3D_IMPL={sum(1 for h in s_helpers.values() if h.kind=='3D_IMPL')}, "
              f"3D_AXIS={sum(1 for h in s_helpers.values() if h.kind=='3D_AXIS')})")
        print(f"  Helper call sites: {len(s_calls)} total, {len(s_res)} with resolved table ptr ({len(s_uniq)} unique tables)")
        print(f"  EL19A cross-match: {same_addr} same-addr+kind, {payload_match} exact-payload match ({nontriv_match} non-trivial)")
        if "CF48D" in spath.name and cf_xml_tables:
            cf_in = [a for a in s_uniq if a in cf_xml_tables]
            cf_miss = [a for a in s_uniq if a not in cf_xml_tables]
            cf_explicit_diffs = []
            cf_inherited = 0
            for a in cf_in:
                xt = cf_xml_tables[a]
                c = s_by_addr[a][0]
                if xt["sizex"] == 1 and xt["sizey"] == 1 and not xt["type"]:
                    cf_inherited += 1
                elif xt["sizex"] * xt["sizey"] != c["dim1"] * c["dim2"]:
                    cf_explicit_diffs.append((a, xt, c))
            print(f"  CF48D.xml ({len(cf_xml_tables)} tables) check: {len(cf_in)} matched ({cf_inherited} base-inherited dims), {len(cf_miss)} caller-backed outside XML, {len(cf_explicit_diffs)} explicit geometry diffs")
            for a, xt, c in cf_explicit_diffs[:10]:
                print(f"    CF48D DIFF 0x{a:05X}: XML={xt['sizex']}x{xt['sizey']} | Code={c['dim1']}x{c['dim2']} ({xt['name']})")

    if args.json_out is not None or args.tsv_dir is not None:
        write_machine_exports(args.json_out, args.tsv_dir, machine_scans)
        if args.json_out is not None:
            print(f"Machine-readable JSON written: {args.json_out}")
        if args.tsv_dir is not None:
            print(f"Per-ROM TSV exports written under: {args.tsv_dir}")


if __name__ == "__main__":
    main()
