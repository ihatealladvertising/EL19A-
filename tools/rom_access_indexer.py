#!/usr/bin/env python3
"""
rom_access_indexer.py — Static reader/writer indexer for supplied target addresses
Part of Nissan EL19A ECU reverse-engineering project (WO65115).
Pure Python 3 standard library only.
"""

import argparse
import hashlib
import os
import re
import sys
from datetime import datetime

VERSION = "1.2.0"
EXPECTED_ROM_MD5 = "46991697c502052752a2cabcb84c9e27"
EXPECTED_LISTING_MEMBER = "EL19A_Complete_Disassembly_ANNOTATED_V3_NEXT6_16_ALL_PENDING_ANNOTATIONS(1).lst"
EXPECTED_LISTING_SHA256 = "148385bbec91f6a491dcaa403962836f709c2f273df9a17ec51f1dea5f7f4549"

METHOD_LIMITS = "computed pointers, pointer tables, block-copy and movca.l transport are not modelled"


def parse_targets(targets_file, space_override="auto"):
    """
    Parse targets file.
    No ranges, wildcards, or pages allowed.
    Returns list of dicts:
      {
        'raw': raw_str,
        'space': 'ram' | 'rom',
        'val': integer_address,
        'norm': formatted_string
      }
    """
    targets = []
    with open(targets_file, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Strip inline comments
            if "#" in line:
                line = line.split("#")[0].strip()
            if not line:
                continue

            # Wildcard / range validation
            if any(c in line for c in ["*", "?", "..", "-", "/", ":"]):
                raise ValueError(
                    f"Line {line_num}: Ranges, blocks, and wildcards are forbidden: {line}"
                )

            token = line.strip()
            # Accepted forms are explicit: 1-6 hex digits for ROM, or
            # exactly FFFFxxxx for RAM. Reject ambiguous widths early.
            if not re.fullmatch(r"(?:0[xX])?(?:[0-9a-fA-F]{1,6}|[fF]{4}[0-9a-fA-F]{4})", token):
                raise ValueError(
                    f"Line {line_num}: expected a 1-6 digit ROM address or FFFFxxxx RAM address: {token}"
                )
            clean_hex = token.lower()
            if clean_hex.startswith("0x"):
                clean_hex = clean_hex[2:]
            val = int(clean_hex, 16)

            if space_override == "auto":
                if len(clean_hex) == 8 and clean_hex.startswith("ffff"):
                    space = "ram"
                elif val >= 0xFFFF0000:
                    space = "ram"
                else:
                    space = "rom"
            elif space_override in ("rom", "ram"):
                space = space_override
                if space == "ram" and val < 0x10000:
                    val |= 0xFFFF0000
            else:
                raise ValueError(f"Unknown space override: {space_override}")

            if space == "ram":
                norm_str = f"FFFF{val & 0xFFFF:04X}"
            else:
                norm_str = f"0x{val:X}"

            targets.append({
                "raw": token,
                "space": space,
                "val": val,
                "norm": norm_str,
            })

    return targets


def compute_file_hash(path, algo="sha256"):
    h = hashlib.new(algo)
    with open(path, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()




def invalidate_general_registers(regs, reg_provenance, active_rom_pool_loads):
    """Invalidate all tracked GPRs and pointer provenance at a flow boundary."""
    for reg in range(16):
        regs[reg] = None
        reg_provenance[reg] = None
    active_rom_pool_loads.clear()


def ldc_gbr_source_register(op):
    """Return the encoded GPR index for LDC/LDC.L to GBR, else None."""
    if (op & 0xF0FF) in (0x401E, 0x4017):
        return (op >> 8) & 0x0F
    return None


def pc_bytes_match(rom, pc, expected_bytes):
    """Return True only when listing bytes exactly match ROM bytes at pc."""
    return (
        pc >= 0
        and pc + len(expected_bytes) <= len(rom)
        and rom[pc:pc + len(expected_bytes)] == expected_bytes
    )


def promote_pool_pointer_to_dereference(
    hits, active_rom_pool_loads, base_reg, pc, function,
    access, width, form, base, base_resolved, mask, note
):
    """
    Convert a prior pointer-constant row into the actual data access row.
    The reported PC is the dereference instruction, never the earlier pool load.
    Returns True when a tracked ROM pool pointer was consumed.
    """
    if not isinstance(base_reg, int) or base_reg not in active_rom_pool_loads:
        return False
    hit_index = active_rom_pool_loads.pop(base_reg)
    original = hits[hit_index]
    pool_load_pc = original[2]
    dereference_row = (
        original[0], original[1], f"0x{pc:X}", function,
        access, width, form, base, base_resolved, mask,
        f"{note}; pointer loaded at {pool_load_pc}"
    )
    if original[4] == "constant":
        # First observed consumer replaces the provisional pointer-constant row.
        hits[hit_index] = dereference_row
    else:
        # Another register alias to the same pointer has its own access site.
        hits.append(dereference_row)
    return True


def run_indexer(rom_path, listing_path, targets_path, out_path, unres_path, space_override="auto"):
    # 1. ROM integrity
    rom_md5 = compute_file_hash(rom_path, "md5")
    if rom_md5.lower() != EXPECTED_ROM_MD5.lower():
        raise ValueError(f"ROM MD5 mismatch: expected {EXPECTED_ROM_MD5}, got {rom_md5}")
    rom_sha256 = compute_file_hash(rom_path, "sha256")

    # 2. Listing integrity
    listing_sha256 = compute_file_hash(listing_path, "sha256")
    if EXPECTED_LISTING_SHA256 and listing_sha256.lower() != EXPECTED_LISTING_SHA256.lower():
        raise ValueError(
            f"Listing SHA-256 mismatch: expected {EXPECTED_LISTING_SHA256}, got {listing_sha256}"
        )

    # 3. Targets
    targets_sha256 = compute_file_hash(targets_path, "sha256")
    targets_list = parse_targets(targets_path, space_override)
    if not targets_list:
        raise ValueError("Targets file contains no valid targets.")

    targets_by_val = {}
    for t in targets_list:
        targets_by_val[t["val"]] = t

    # Read ROM bytes
    with open(rom_path, "rb") as f:
        rom = f.read()

    # 4. Parse listing lines
    re_code = re.compile(
        r"^([0-9A-Fa-f]{8})\s+([0-9A-Fa-f\s]{2,20})\s+CODE\s+([^\r\n;]+)(?:;\s*(.*))?$"
    )
    re_label = re.compile(r"^([a-zA-Z_][a-zA-Z0-9_]*):")

    code_lines = []
    current_func = "unknown"
    current_label = "unknown"

    with open(listing_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            m_lab = re_label.match(line)
            if m_lab:
                lbl = m_lab.group(1)
                current_label = lbl
                if lbl.startswith("sub_"):
                    current_func = lbl
                continue

            m_code = re_code.match(line)
            if m_code:
                pc = int(m_code.group(1), 16)
                hex_bytes = bytes.fromhex(m_code.group(2).strip())
                instr_text = m_code.group(3).strip()
                comment = m_code.group(4).strip() if m_code.group(4) else ""
                code_lines.append((pc, hex_bytes, instr_text, comment, current_func, current_label))

    # 5. Analysis Pass
    hits = []
    unresolved = []

    regs = [None] * 16
    reg_provenance = [None] * 16  # PC where register was defined
    gbr = None
    gbr_func = None
    in_delay_slot = False
    delay_slot_type = None
    prev_label = None

    # Track pool loads of ROM targets in the current basic block to link dereferences
    # reg_idx -> (target_dict, load_pc, pool_ea)
    active_rom_pool_loads = {}

    for idx, (pc, hex_bytes, instr_text, comment, current_func, current_label) in enumerate(code_lines):
        op = int.from_bytes(hex_bytes[:2], "big")
        hi = (op >> 12) & 0xF
        n = (op >> 8) & 0xF
        m = (op >> 4) & 0xF
        disp = op & 0xFF
        disp4 = op & 0xF

        # Function boundary
        if current_func != gbr_func:
            gbr = None
            gbr_func = current_func
            regs = [None] * 16
            reg_provenance = [None] * 16
            active_rom_pool_loads.clear()
            in_delay_slot = False
            prev_label = current_label

        # Label boundary within function (if not in delay slot)
        elif current_label != prev_label and not in_delay_slot:
            prev_label = current_label
            # A label boundary is treated conservatively as a possible join.
            # Preserve GBR here; it is separately invalidated at calls/returns.
            invalidate_general_registers(regs, reg_provenance, active_rom_pool_loads)

        mem_access = None
        unresolved_access = None

        # Base + R0 forms
        if hi == 0x0:
            if disp4 in (0xC, 0xD, 0xE):  # mov.x @(r0, Rm), Rn
                width = "b" if disp4 == 0xC else ("w" if disp4 == 0xD else "l")
                if regs[m] is not None and regs[0] is not None:
                    ea = (regs[m] + regs[0]) & 0xFFFFFFFF
                    mem_access = ("read", width, "base_r0", m, regs[m], ea, None, f"mov.{width} @(r0,r{m})")
                else:
                    unresolved_access = ("read", width, "base_r0", m, regs[m], None, f"mov.{width} @(r0,r{m})",
                                         "unresolved base" if regs[m] is None else "unresolved r0 index")
            elif disp4 in (0x4, 0x5, 0x6):  # mov.x Rm, @(r0, Rn)
                width = "b" if disp4 == 0x4 else ("w" if disp4 == 0x5 else "l")
                if regs[n] is not None and regs[0] is not None:
                    ea = (regs[n] + regs[0]) & 0xFFFFFFFF
                    mem_access = ("write", width, "base_r0", n, regs[n], ea, None, f"mov.{width} r{m}, @(r0,r{n})")
                else:
                    unresolved_access = ("write", width, "base_r0", n, regs[n], None, f"mov.{width} r{m}, @(r0,r{n})",
                                         "unresolved base" if regs[n] is None else "unresolved r0 index")

        # Base + displacement forms
        elif hi == 0x1:  # mov.l Rm, @(disp*4, Rn)
            d = disp4 * 4
            if regs[n] is not None:
                ea = (regs[n] + d) & 0xFFFFFFFF
                mem_access = ("write", "l", "base_disp", n, regs[n], ea, None, f"mov.l r{m}, @(0x{d:X},r{n})")
            else:
                unresolved_access = ("write", "l", "base_disp", n, None, None, f"mov.l r{m}, @(0x{d:X},r{n})", "unresolved base register")

        elif hi == 0x5:  # mov.l @(disp*4, Rm), Rn
            d = disp4 * 4
            if regs[m] is not None:
                ea = (regs[m] + d) & 0xFFFFFFFF
                mem_access = ("read", "l", "base_disp", m, regs[m], ea, None, f"mov.l @(0x{d:X},r{m}), r{n}")
            else:
                unresolved_access = ("read", "l", "base_disp", m, None, None, f"mov.l @(0x{d:X},r{m}), r{n}", "unresolved base register")

        elif hi == 0x8:
            disp_4 = op & 0xF
            reg_4 = (op >> 4) & 0xF
            sub_op = (op >> 8) & 0xF
            if sub_op == 0x0:  # mov.b r0, @(disp, Rn)
                if regs[reg_4] is not None:
                    ea = (regs[reg_4] + disp_4) & 0xFFFFFFFF
                    mem_access = ("write", "b", "base_disp", reg_4, regs[reg_4], ea, None, f"mov.b r0, @(0x{disp_4:X},r{reg_4})")
                else:
                    unresolved_access = ("write", "b", "base_disp", reg_4, None, None, f"mov.b r0, @(0x{disp_4:X},r{reg_4})", "unresolved base register")
            elif sub_op == 0x1:  # mov.w r0, @(disp*2, Rn)
                if regs[reg_4] is not None:
                    ea = (regs[reg_4] + disp_4 * 2) & 0xFFFFFFFF
                    mem_access = ("write", "w", "base_disp", reg_4, regs[reg_4], ea, None, f"mov.w r0, @(0x{disp_4*2:X},r{reg_4})")
                else:
                    unresolved_access = ("write", "w", "base_disp", reg_4, None, None, f"mov.w r0, @(0x{disp_4*2:X},r{reg_4})", "unresolved base register")
            elif sub_op == 0x4:  # mov.b @(disp, Rm), r0
                if regs[reg_4] is not None:
                    ea = (regs[reg_4] + disp_4) & 0xFFFFFFFF
                    mem_access = ("read", "b", "base_disp", reg_4, regs[reg_4], ea, None, f"mov.b @(0x{disp_4:X},r{reg_4}), r0")
                else:
                    unresolved_access = ("read", "b", "base_disp", reg_4, None, None, f"mov.b @(0x{disp_4:X},r{reg_4}), r0", "unresolved base register")
            elif sub_op == 0x5:  # mov.w @(disp*2, Rm), r0
                if regs[reg_4] is not None:
                    ea = (regs[reg_4] + disp_4 * 2) & 0xFFFFFFFF
                    mem_access = ("read", "w", "base_disp", reg_4, regs[reg_4], ea, None, f"mov.w @(0x{disp_4*2:X},r{reg_4}), r0")
                else:
                    unresolved_access = ("read", "w", "base_disp", reg_4, None, None, f"mov.w @(0x{disp_4*2:X},r{reg_4}), r0", "unresolved base register")

        # Direct register indirect @Rn
        elif hi == 0x2:
            if disp4 in (0, 1, 2):
                width = "b" if disp4 == 0 else ("w" if disp4 == 1 else "l")
                if regs[n] is not None:
                    ea = regs[n]
                    mem_access = ("write", width, "base_disp", n, regs[n], ea, None, f"mov.{width} r{m}, @r{n}")
                else:
                    unresolved_access = ("write", width, "base_disp", n, None, None, f"mov.{width} r{m}, @r{n}", "unresolved base register")
        elif hi == 0x6:
            if disp4 in (0, 1, 2):
                width = "b" if disp4 == 0 else ("w" if disp4 == 1 else "l")
                if regs[m] is not None:
                    ea = regs[m]
                    mem_access = ("read", width, "base_disp", m, regs[m], ea, None, f"mov.{width} @r{m}, r{n}")
                else:
                    unresolved_access = ("read", width, "base_disp", m, None, None, f"mov.{width} @r{m}, r{n}", "unresolved base register")

        # GBR relative
        elif hi == 0xC:
            sub_op = (op >> 8) & 0xF
            if sub_op in (0x0, 0x1, 0x2):
                width = "b" if sub_op == 0x0 else ("w" if sub_op == 0x1 else "l")
                scale = 1 if sub_op == 0x0 else (2 if sub_op == 0x1 else 4)
                if gbr is not None:
                    ea = (gbr + disp * scale) & 0xFFFFFFFF
                    mem_access = ("write", width, "gbr_disp", "gbr", gbr, ea, None, f"mov.{width} r0, @(0x{disp*scale:X},gbr)")
                else:
                    unresolved_access = ("write", width, "gbr_disp", "gbr", None, None, f"mov.{width} r0, @(0x{disp*scale:X},gbr)", "unresolved GBR register")
            elif sub_op in (0x4, 0x5, 0x6):
                width = "b" if sub_op == 0x4 else ("w" if sub_op == 0x5 else "l")
                scale = 1 if sub_op == 0x4 else (2 if sub_op == 0x5 else 4)
                if gbr is not None:
                    ea = (gbr + disp * scale) & 0xFFFFFFFF
                    mem_access = ("read", width, "gbr_disp", "gbr", gbr, ea, None, f"mov.{width} @(0x{disp*scale:X},gbr), r0")
                else:
                    unresolved_access = ("read", width, "gbr_disp", "gbr", None, None, f"mov.{width} @(0x{disp*scale:X},gbr), r0", "unresolved GBR register")
            elif sub_op in (0xC, 0xD, 0xE, 0xF):
                acc = "read" if sub_op == 0xC else "rmw"
                mnem = "tst.b" if sub_op == 0xC else ("and.b" if sub_op == 0xD else ("xor.b" if sub_op == 0xE else "or.b"))
                mask_hex = f"0x{disp:02X}"
                if gbr is not None and regs[0] is not None:
                    ea = (gbr + regs[0]) & 0xFFFFFFFF
                    mem_access = (acc, "b", "gbr_r0", "gbr", gbr, ea, mask_hex, f"{mnem} #{mask_hex}, @(r0,gbr)")
                else:
                    unresolved_access = (acc, "b", "gbr_r0", "gbr", gbr, None, f"{mnem} #{mask_hex}, @(r0,gbr)",
                                         "unresolved GBR" if gbr is None else "unresolved r0 index")

        # Check direct memory access against target
        if mem_access:
            acc_type, width, form, base_reg, base_val, ea, mask, note = mem_access
            mask_str = mask if mask else "-"
            base_str = f"0x{base_val:X}" if base_val is not None and base_val < 0x100000 else (f"FFFF{base_val & 0xFFFF:04X}" if base_val is not None else "?")
            base_res = "full" if base_val is not None else "none"

            if ea is not None and ea in targets_by_val:
                t = targets_by_val[ea]
                # A pool-loaded ROM pointer is promoted to the actual access PC.
                # The pool load itself is not a table read.
                promoted = False
                if t["space"] == "rom":
                    promoted = promote_pool_pointer_to_dereference(
                        hits, active_rom_pool_loads, base_reg, pc, current_func,
                        acc_type, width, form, base_str, base_res, mask_str, note
                    )
                if not promoted:
                    hits.append((t["norm"], t["space"], f"0x{pc:X}", current_func, acc_type, width, form, base_str, base_res, mask_str, note))

        elif unresolved_access:
            acc_type, width, form, base_reg, base_val, ea, note, reason = unresolved_access
            base_str = (
                f"0x{base_val:X}" if base_val is not None and base_val < 0x100000
                else (f"FFFF{base_val & 0xFFFF:04X}" if base_val is not None else "?")
            )
            base_resolved = "partial" if base_val is not None else "none"
            for t in targets_list:
                # The exact target is unknown at this site; record the uncertainty
                # against each supplied target without presenting it as a hit.
                unresolved.append((t["norm"], t["space"], f"0x{pc:X}", current_func, acc_type, width, form, base_str, base_resolved, "-", note, reason))

        # A pointer passed to a helper is not labelled dereferenced here.
        # Without an interprocedural summary, that is only an unresolved consumer.
        if (hi == 0x4 and (op & 0xFF) == 0x0B) or (hi == 0xB):
            callee = comment.lower() if comment else ""
            if ("sub_22e10" in callee or "loc_2350c" in callee) and 4 in active_rom_pool_loads:
                pool_hit_idx = active_rom_pool_loads[4]
                pool_hit = hits[pool_hit_idx]
                unresolved.append((
                    pool_hit[0], pool_hit[1], f"0x{pc:X}", current_func,
                    "unknown", "?", "pool", pool_hit[7], "partial", "-",
                    f"ROM pointer from {pool_hit[2]} passed in r4 to table helper",
                    "callee-side dereference not resolved interprocedurally"
                ))

        # Literal pool loads
        if hi == 0x9:  # mov.w @(disp*2, PC), Rn
            active_rom_pool_loads.pop(n, None)
            pool_ea = pc + 4 + disp * 2
            val = int.from_bytes(rom[pool_ea:pool_ea+2], "big")
            if val & 0x8000:
                val |= 0xFFFF0000
            regs[n] = val
            reg_provenance[n] = pc

            # Target match against pool address itself
            if pool_ea in targets_by_val:
                t = targets_by_val[pool_ea]
                hits.append((t["norm"], t["space"], f"0x{pc:X}", current_func, "constant", "w", "pool", f"0x{pool_ea:X}", "full", "-", f"pool_ea match: val=0x{val:X}"))

            # Target match against pool value (ROM)
            # A signed mov.w pool value is a sign-extended immediate, not a
            # full-width ROM pointer. Do not classify it as a ROM table address.
            if val in targets_by_val and targets_by_val[val]["space"] == "rom" and val >= 0:
                t = targets_by_val[val]
                hits.append((t["norm"], t["space"], f"0x{pc:X}", current_func, "constant", "w", "pool", f"0x{val:X}", "full", "-", f"mov.w pool value 0x{val:X}"))
                active_rom_pool_loads[n] = len(hits) - 1

        elif hi == 0xD:  # mov.l @(disp*4, PC), Rn
            active_rom_pool_loads.pop(n, None)
            pool_ea = ((pc + 4) & ~3) + disp * 4
            val = int.from_bytes(rom[pool_ea:pool_ea+4], "big")
            regs[n] = val
            reg_provenance[n] = pc

            # Target match against pool address itself (e.g. 0x388AC)
            if pool_ea in targets_by_val:
                t = targets_by_val[pool_ea]
                hits.append((t["norm"], t["space"], f"0x{pc:X}", current_func, "constant", "l", "pool", f"0x{pool_ea:X}", "full", "-", f"pool_ea match: val=0x{val:X}"))

            # Target match against pool value (ROM target, e.g. 0xED64, 0x8550)
            if val in targets_by_val and targets_by_val[val]["space"] == "rom":
                t = targets_by_val[val]
                # Default to dereferenced if later dereferenced/called; initial placeholder
                hits.append((t["norm"], t["space"], f"0x{pc:X}", current_func, "constant", "l", "pool", f"0x{val:X}", "full", "-", f"mov.l pool value 0x{val:X}"))
                active_rom_pool_loads[n] = len(hits) - 1

        # Immediate loads
        elif hi == 0xE:  # mov #imm, Rn
            imm = op & 0xFF
            val = (imm | 0xFFFFFF00) if (imm & 0x80) else imm
            regs[n] = val
            reg_provenance[n] = pc
            active_rom_pool_loads.pop(n, None)

        # Register updates
        elif hi == 0x6:
            if disp4 == 3:  # mov Rm, Rn
                regs[n] = regs[m]
                reg_provenance[n] = pc
                if m in active_rom_pool_loads:
                    active_rom_pool_loads[n] = active_rom_pool_loads[m]
                else:
                    active_rom_pool_loads.pop(n, None)
            elif disp4 == 0xC:  # extu.b Rm, Rn
                regs[n] = (regs[m] & 0xFF) if regs[m] is not None else None
                reg_provenance[n] = pc
                active_rom_pool_loads.pop(n, None)
            elif disp4 == 0xD:  # extu.w Rm, Rn
                regs[n] = (regs[m] & 0xFFFF) if regs[m] is not None else None
                reg_provenance[n] = pc
                active_rom_pool_loads.pop(n, None)
            elif disp4 == 0xE:  # exts.b Rm, Rn
                if regs[m] is not None:
                    b = regs[m] & 0xFF
                    regs[n] = (b | 0xFFFFFF00) if (b & 0x80) else b
                else:
                    regs[n] = None
                reg_provenance[n] = pc
                active_rom_pool_loads.pop(n, None)
            elif disp4 == 0xF:  # exts.w Rm, Rn
                if regs[m] is not None:
                    w = regs[m] & 0xFFFF
                    regs[n] = (w | 0xFFFF0000) if (w & 0x8000) else w
                else:
                    regs[n] = None
                reg_provenance[n] = pc
                active_rom_pool_loads.pop(n, None)
            else:
                regs[n] = None
                reg_provenance[n] = None
                active_rom_pool_loads.pop(n, None)

        elif hi == 0x7:  # add #imm, Rn
            imm = op & 0xFF
            imm_val = (imm | 0xFFFFFF00) if (imm & 0x80) else imm
            if regs[n] is not None:
                regs[n] = (regs[n] + imm_val) & 0xFFFFFFFF
            reg_provenance[n] = pc
            active_rom_pool_loads.pop(n, None)

        elif hi == 0x3:
            if disp4 == 0xC:  # add Rm, Rn
                if regs[n] is not None and regs[m] is not None:
                    regs[n] = (regs[n] + regs[m]) & 0xFFFFFFFF
                else:
                    regs[n] = None
                reg_provenance[n] = pc
                active_rom_pool_loads.pop(n, None)
            elif disp4 == 0x8:  # sub Rm, Rn
                if regs[n] is not None and regs[m] is not None:
                    regs[n] = (regs[n] - regs[m]) & 0xFFFFFFFF
                else:
                    regs[n] = None
                reg_provenance[n] = pc
                active_rom_pool_loads.pop(n, None)
            else:
                # Other SH-2 group-3 ALU operations may write Rn.
                regs[n] = None
                reg_provenance[n] = None
                active_rom_pool_loads.pop(n, None)

        elif hi == 0x4:
            ldc_reg = ldc_gbr_source_register(op)
            if ldc_reg is not None and (op & 0xFF) == 0x1E:  # ldc Rm, gbr
                gbr = regs[ldc_reg]
            elif ldc_reg is not None and (op & 0xFF) == 0x17:  # ldc.l @Rm+, gbr
                gbr = None
                regs[ldc_reg] = None
                reg_provenance[ldc_reg] = None
                active_rom_pool_loads.pop(ldc_reg, None)
            elif (op & 0xFF) not in (0x2B, 0x0B):  # jmp/jsr do not write a GPR
                # Unmodelled group-4 instructions can read/write GPRs or GBR.
                invalidate_general_registers(regs, reg_provenance, active_rom_pool_loads)
                gbr = None

        elif hi == 0x5:
            regs[n] = None
            reg_provenance[n] = None
            active_rom_pool_loads.pop(n, None)
        elif hi == 0x0 and disp4 in (0xC, 0xD, 0xE):
            regs[n] = None
            reg_provenance[n] = None
            active_rom_pool_loads.pop(n, None)
        elif hi == 0x0 and disp4 in (0x4, 0x5, 0x6):
            # Indexed stores use the tracked base/index but do not write a GPR.
            pass
        elif hi == 0x0 and (op & 0xFF) not in (0x23, 0x03):
            # Other unmodelled group-0 operations may write a GPR (or change GBR).
            invalidate_general_registers(regs, reg_provenance, active_rom_pool_loads)
            gbr = None
        elif hi == 0x2 and disp4 not in (0, 1, 2):
            # Non-basic group-2 addressing/transport is not resolved here.
            invalidate_general_registers(regs, reg_provenance, active_rom_pool_loads)
        elif hi == 0x8 and (op >> 8) & 0xF in (0x4, 0x5):
            regs[0] = None
            reg_provenance[0] = None
            active_rom_pool_loads.pop(0, None)
        elif hi == 0xC and (op >> 8) & 0xF in (0x4, 0x5, 0x6):
            regs[0] = None
            reg_provenance[0] = None
            active_rom_pool_loads.pop(0, None)

        # Control transfers and delay slots
        is_branch_delay = False
        is_branch_no_delay = False
        is_call = False
        is_ret = False

        if op in (0x000B, 0x002B):  # rts, rte
            is_branch_delay = True
            is_ret = True
        elif hi in (0xA, 0xB):  # bra, bsr
            is_branch_delay = True
            if hi == 0xB:
                is_call = True
        elif hi == 0x4 and (op & 0xFF) in (0x2B, 0x0B):  # jmp, jsr
            is_branch_delay = True
            if (op & 0xFF) == 0x0B:
                is_call = True
        elif hi == 0x0 and (op & 0xFF) in (0x23, 0x03):  # braf, bsrf
            is_branch_delay = True
            if (op & 0xFF) == 0x03:
                is_call = True
        elif hi == 0x8 and (op >> 8) & 0xF in (0xD, 0xF):  # bt/s, bf/s
            is_branch_delay = True
        elif hi == 0x8 and (op >> 8) & 0xF in (0x9, 0xB):  # bt, bf
            is_branch_no_delay = True

        if in_delay_slot:
            if delay_slot_type == "ret":
                invalidate_general_registers(regs, reg_provenance, active_rom_pool_loads)
                gbr = None
            elif delay_slot_type == "call":
                invalidate_general_registers(regs, reg_provenance, active_rom_pool_loads)
                # The callee may alter GBR; do not propagate a caller value blindly.
                gbr = None
            elif delay_slot_type == "bra":
                invalidate_general_registers(regs, reg_provenance, active_rom_pool_loads)
            in_delay_slot = False
            delay_slot_type = None
        elif is_branch_delay:
            in_delay_slot = True
            if is_ret:
                delay_slot_type = "ret"
            elif is_call:
                delay_slot_type = "call"
            else:
                delay_slot_type = "bra"
        elif is_branch_no_delay:
            invalidate_general_registers(regs, reg_provenance, active_rom_pool_loads)

    # 6. PC Concordance verification for both output files
    valid_hits = []
    concordance_matched = 0
    concordance_checked = 0
    unresolved_sites = list(unresolved)
    unresolved = []

    code_dict = {item[0]: item for item in code_lines}

    for h in hits:
        t_norm, t_space, pc_str, func, acc, width, form, base, base_res, mask, note = h
        pc = int(pc_str, 16)
        concordance_checked += 1
        if pc in code_dict and pc_bytes_match(rom, pc, code_dict[pc][1]):
            concordance_matched += 1
            valid_hits.append(h)
        else:
            reason = (
                "PC opcode byte mismatch with ROM"
                if pc in code_dict else "PC not found in listing CODE records"
            )
            unresolved.append((t_norm, t_space, pc_str, func, acc, width, form, base, "none", mask, note, reason))

    # Unresolved sites are still emitted only with a byte-concordant listing PC.
    # They remain unresolved as to effective address; this check does not promote them.
    for row in unresolved_sites:
        pc = int(row[2], 16)
        concordance_checked += 1
        if pc in code_dict and pc_bytes_match(rom, pc, code_dict[pc][1]):
            concordance_matched += 1
            unresolved.append(row)
        else:
            reason = (
                "PC opcode byte mismatch with ROM"
                if pc in code_dict else "PC not found in listing CODE records"
            )
            unresolved.append(row[:11] + (reason,))

    # Sort outputs: by target, then by PC
    valid_hits.sort(key=lambda x: (x[0], int(x[2], 16)))
    unresolved.sort(key=lambda x: (x[0], int(x[2], 16)))

    run_date = datetime.now().strftime("%Y-%m-%d")

    # Header block
    header = [
        f"# ROM MD5: {rom_md5}",
        f"# ROM SHA-256: {rom_sha256}",
        f"# Listing member: {EXPECTED_LISTING_MEMBER}",
        f"# Listing SHA-256: {listing_sha256}",
        f"# Resolver version: {VERSION}",
        f"# Target file hash: {targets_sha256}",
        f"# Run date: {run_date}",
        f"# Method limits: {METHOD_LIMITS}",
        f"# Concordance: rows_checked={concordance_checked} rows_matched={concordance_matched}",
    ]

    # Write output TSV
    columns_out = ["target", "space", "pc", "function", "access", "width", "form", "base", "base_resolved", "mask", "note"]
    with open(out_path, "w", encoding="utf-8") as f:
        for hline in header:
            f.write(hline + "\n")
        f.write("\t".join(columns_out) + "\n")
        for row in valid_hits:
            f.write("\t".join(str(c) for c in row) + "\n")

    # Write unresolved TSV
    columns_unres = ["target", "space", "pc", "function", "access", "width", "form", "base", "base_resolved", "mask", "note", "reason"]
    with open(unres_path, "w", encoding="utf-8") as f:
        for hline in header:
            f.write(hline + "\n")
        f.write("\t".join(columns_unres) + "\n")
        for row in unresolved:
            f.write("\t".join(str(c) for c in row) + "\n")

    print(f"Index complete: {len(valid_hits)} hits written to {out_path}")
    print(f"Unresolved log: {len(unresolved)} rows written to {unres_path}")
    print(f"PC Concordance: {concordance_matched}/{concordance_checked}")

    return valid_hits, unresolved, concordance_matched, concordance_checked


def main():
    parser = argparse.ArgumentParser(description="ROM static access resolver (SH-2)")
    parser.add_argument("--version", action="version", version=f"rom_access_indexer {VERSION}")
    parser.add_argument("--rom", help="Path to ROM binary")
    parser.add_argument("--listing", help="Path to disassembled listing file (.lst)")
    parser.add_argument("--targets", help="Path to target addresses text file")
    parser.add_argument("--out", help="Path to output TSV file")
    parser.add_argument("--unresolved", help="Path to unresolved output TSV file")
    parser.add_argument("--space", choices=["auto", "rom", "ram"], default="auto", help="Address space normalisation override")

    args = parser.parse_args()

    if not all([args.rom, args.listing, args.targets, args.out, args.unresolved]):
        parser.error("All arguments --rom, --listing, --targets, --out, and --unresolved are required.")

    run_indexer(args.rom, args.listing, args.targets, args.out, args.unresolved, args.space)


if __name__ == "__main__":
    main()
