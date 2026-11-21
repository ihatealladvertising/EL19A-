import re
import os
import sys

ROM_PATH = "/home/vivian/.gemini/antigravity/scratch/EL19A-/EVIDENCE/VERSA f501.bin"
LST_PATH = "/tmp/EL19A_NEXT6_16.lst"

with open(ROM_PATH, "rb") as f:
    rom = f.read()

re_code = re.compile(r'^([0-9A-Fa-f]{8})\s+([0-9A-Fa-f\s]{2,20})\s+CODE\s+([^\r\n;]+)(?:;\s*(.*))?$')
re_label = re.compile(r'^([a-zA-Z_][a-zA-Z0-9_]*):')

code_lines = []
labels_by_pc = {}

print("Reading listing...")
with open(LST_PATH, "r", encoding="utf-8", errors="replace") as f:
    current_func = "unknown"
    current_label = "unknown"
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

targets = [
    ("FFFF85DF", "ram", 0xFFFF85DF),
    ("FFFF85E0", "ram", 0xFFFF85E0),
    ("FFFF1DB4", "ram", 0xFFFF1DB4),
    ("0x8550", "rom", 0x8550),
    ("0x388AC", "rom", 0x388AC),
    ("0xED64", "rom", 0xED64),
    ("0xEDA0", "rom", 0xEDA0),
    ("0xEE68", "rom", 0xEE68),
    ("0xF01C", "rom", 0xF01C),
    ("FFFF84BA", "ram", 0xFFFF84BA),
]
target_vals = {t[2]: t for t in targets}

hits = []
unresolved = []

regs = [None] * 16
gbr = None
gbr_func = None
in_delay_slot = False
delay_slot_type = None
prev_label = None

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
        in_delay_slot = False
        prev_label = current_label

    # Label boundary within function (if not in delay slot)
    elif current_label != prev_label and not in_delay_slot:
        prev_label = current_label
        # Invalidate scratch registers r0-r7 across labels
        for r in range(8):
            regs[r] = None

    mem_access = None

    # Base + R0
    if hi == 0x0:
        if disp4 == 0xC: # mov.b @(r0, Rm), Rn
            ea = (regs[m] + regs[0]) & 0xFFFFFFFF if (regs[m] is not None and regs[0] is not None) else None
            mem_access = ("read", "b", "base_r0", m, regs[m], ea, None, f"mov.b @(r0,r{m})")
        elif disp4 == 0xD: # mov.w @(r0, Rm), Rn
            ea = (regs[m] + regs[0]) & 0xFFFFFFFF if (regs[m] is not None and regs[0] is not None) else None
            mem_access = ("read", "w", "base_r0", m, regs[m], ea, None, f"mov.w @(r0,r{m})")
        elif disp4 == 0xE: # mov.l @(r0, Rm), Rn
            ea = (regs[m] + regs[0]) & 0xFFFFFFFF if (regs[m] is not None and regs[0] is not None) else None
            mem_access = ("read", "l", "base_r0", m, regs[m], ea, None, f"mov.l @(r0,r{m})")
        elif disp4 == 0x4: # mov.b Rm, @(r0, Rn)
            ea = (regs[n] + regs[0]) & 0xFFFFFFFF if (regs[n] is not None and regs[0] is not None) else None
            mem_access = ("write", "b", "base_r0", n, regs[n], ea, None, f"mov.b r{m}, @(r0,r{n})")
        elif disp4 == 0x5: # mov.w Rm, @(r0, Rn)
            ea = (regs[n] + regs[0]) & 0xFFFFFFFF if (regs[n] is not None and regs[0] is not None) else None
            mem_access = ("write", "w", "base_r0", n, regs[n], ea, None, f"mov.w r{m}, @(r0,r{n})")
        elif disp4 == 0x6: # mov.l Rm, @(r0, Rn)
            ea = (regs[n] + regs[0]) & 0xFFFFFFFF if (regs[n] is not None and regs[0] is not None) else None
            mem_access = ("write", "l", "base_r0", n, regs[n], ea, None, f"mov.l r{m}, @(r0,r{n})")

    # Base + disp
    elif hi == 0x1: # mov.l Rm, @(disp*4, Rn)
        d = disp4 * 4
        ea = (regs[n] + d) & 0xFFFFFFFF if regs[n] is not None else None
        mem_access = ("write", "l", "base_disp", n, regs[n], ea, None, f"mov.l r{m}, @(0x{d:X},r{n})")
    elif hi == 0x5: # mov.l @(disp*4, Rm), Rn
        d = disp4 * 4
        ea = (regs[m] + d) & 0xFFFFFFFF if regs[m] is not None else None
        mem_access = ("read", "l", "base_disp", m, regs[m], ea, None, f"mov.l @(0x{d:X},r{m}), r{n}")
    elif hi == 0x8:
        disp_4 = op & 0xF
        reg_4 = (op >> 4) & 0xF
        if (op >> 8) & 0xF == 0x0: # mov.b r0, @(disp, Rn)
            ea = (regs[reg_4] + disp_4) & 0xFFFFFFFF if regs[reg_4] is not None else None
            mem_access = ("write", "b", "base_disp", reg_4, regs[reg_4], ea, None, f"mov.b r0, @(0x{disp_4:X},r{reg_4})")
        elif (op >> 8) & 0xF == 0x1: # mov.w r0, @(disp*2, Rn)
            ea = (regs[reg_4] + disp_4*2) & 0xFFFFFFFF if regs[reg_4] is not None else None
            mem_access = ("write", "w", "base_disp", reg_4, regs[reg_4], ea, None, f"mov.w r0, @(0x{disp_4*2:X},r{reg_4})")
        elif (op >> 8) & 0xF == 0x4: # mov.b @(disp, Rm), r0
            ea = (regs[reg_4] + disp_4) & 0xFFFFFFFF if regs[reg_4] is not None else None
            mem_access = ("read", "b", "base_disp", reg_4, regs[reg_4], ea, None, f"mov.b @(0x{disp_4:X},r{reg_4}), r0")
        elif (op >> 8) & 0xF == 0x5: # mov.w @(disp*2, Rm), r0
            ea = (regs[reg_4] + disp_4*2) & 0xFFFFFFFF if regs[reg_4] is not None else None
            mem_access = ("read", "w", "base_disp", reg_4, regs[reg_4], ea, None, f"mov.w @(0x{disp_4*2:X},r{reg_4}), r0")

    # Direct register indirect @Rn
    elif hi == 0x2:
        if disp4 == 0:
            ea = regs[n]
            mem_access = ("write", "b", "base_disp", n, regs[n], ea, None, f"mov.b r{m}, @r{n}")
        elif disp4 == 1:
            ea = regs[n]
            mem_access = ("write", "w", "base_disp", n, regs[n], ea, None, f"mov.w r{m}, @r{n}")
        elif disp4 == 2:
            ea = regs[n]
            mem_access = ("write", "l", "base_disp", n, regs[n], ea, None, f"mov.l r{m}, @r{n}")
    elif hi == 0x6:
        if disp4 == 0:
            ea = regs[m]
            mem_access = ("read", "b", "base_disp", m, regs[m], ea, None, f"mov.b @r{m}, r{n}")
        elif disp4 == 1:
            ea = regs[m]
            mem_access = ("read", "w", "base_disp", m, regs[m], ea, None, f"mov.w @r{m}, r{n}")
        elif disp4 == 2:
            ea = regs[m]
            mem_access = ("read", "l", "base_disp", m, regs[m], ea, None, f"mov.l @r{m}, r{n}")

    # GBR relative
    elif hi == 0xC:
        sub_op = (op >> 8) & 0xF
        if sub_op == 0x0:
            ea = (gbr + disp) & 0xFFFFFFFF if gbr is not None else None
            mem_access = ("write", "b", "gbr_disp", "gbr", gbr, ea, None, f"mov.b r0, @(0x{disp:X},gbr)")
        elif sub_op == 0x1:
            ea = (gbr + disp*2) & 0xFFFFFFFF if gbr is not None else None
            mem_access = ("write", "w", "gbr_disp", "gbr", gbr, ea, None, f"mov.w r0, @(0x{disp*2:X},gbr)")
        elif sub_op == 0x2:
            ea = (gbr + disp*4) & 0xFFFFFFFF if gbr is not None else None
            mem_access = ("write", "l", "gbr_disp", "gbr", gbr, ea, None, f"mov.l r0, @(0x{disp*4:X},gbr)")
        elif sub_op == 0x4:
            ea = (gbr + disp) & 0xFFFFFFFF if gbr is not None else None
            mem_access = ("read", "b", "gbr_disp", "gbr", gbr, ea, None, f"mov.b @(0x{disp:X},gbr), r0")
        elif sub_op == 0x5:
            ea = (gbr + disp*2) & 0xFFFFFFFF if gbr is not None else None
            mem_access = ("read", "w", "gbr_disp", "gbr", gbr, ea, None, f"mov.w @(0x{disp*2:X},gbr), r0")
        elif sub_op == 0x6:
            ea = (gbr + disp*4) & 0xFFFFFFFF if gbr is not None else None
            mem_access = ("read", "l", "gbr_disp", "gbr", gbr, ea, None, f"mov.l @(0x{disp*4:X},gbr), r0")
        elif sub_op == 0xC:
            ea = (gbr + regs[0]) & 0xFFFFFFFF if (gbr is not None and regs[0] is not None) else None
            mem_access = ("read", "b", "gbr_r0", "gbr", gbr, ea, f"0x{disp:02X}", f"tst.b #0x{disp:02X}, @(r0,gbr)")
        elif sub_op == 0xD:
            ea = (gbr + regs[0]) & 0xFFFFFFFF if (gbr is not None and regs[0] is not None) else None
            mem_access = ("rmw", "b", "gbr_r0", "gbr", gbr, ea, f"0x{disp:02X}", f"and.b #0x{disp:02X}, @(r0,gbr)")
        elif sub_op == 0xE:
            ea = (gbr + regs[0]) & 0xFFFFFFFF if (gbr is not None and regs[0] is not None) else None
            mem_access = ("rmw", "b", "gbr_r0", "gbr", gbr, ea, f"0x{disp:02X}", f"xor.b #0x{disp:02X}, @(r0,gbr)")
        elif sub_op == 0xF:
            ea = (gbr + regs[0]) & 0xFFFFFFFF if (gbr is not None and regs[0] is not None) else None
            mem_access = ("rmw", "b", "gbr_r0", "gbr", gbr, ea, f"0x{disp:02X}", f"or.b #0x{disp:02X}, @(r0,gbr)")

    # Literal pool loads
    if hi == 0x9: # mov.w @(disp*2, PC), Rn
        pool_ea = pc + 4 + disp * 2
        val = int.from_bytes(rom[pool_ea:pool_ea+2], "big")
        if val & 0x8000:
            val |= 0xFFFF0000
        if pool_ea in target_vals:
            t_name, t_space, t_val = target_vals[pool_ea]
            hits.append((t_name, t_space, f"0x{pc:X}", current_func, "constant", "w", "pool", f"0x{pool_ea:X}", "full", "-", f"pool_ea match: val=0x{val:X}"))
        if val in target_vals and target_vals[val][1] == "rom":
            t_name, t_space, t_val = target_vals[val]
            hits.append((t_name, t_space, f"0x{pc:X}", current_func, "dereferenced", "w", "pool", f"0x{val:X}", "full", "-", f"pool value: 0x{val:X}"))

    elif hi == 0xD: # mov.l @(disp*4, PC), Rn
        pool_ea = ((pc + 4) & ~3) + disp * 4
        val = int.from_bytes(rom[pool_ea:pool_ea+4], "big")
        if pool_ea in target_vals:
            t_name, t_space, t_val = target_vals[pool_ea]
            hits.append((t_name, t_space, f"0x{pc:X}", current_func, "constant", "l", "pool", f"0x{pool_ea:X}", "full", "-", f"pool_ea match: val=0x{val:X}"))
        if val in target_vals and target_vals[val][1] == "rom":
            t_name, t_space, t_val = target_vals[val]
            hits.append((t_name, t_space, f"0x{pc:X}", current_func, "dereferenced", "l", "pool", f"0x{val:X}", "full", "-", f"pool value: 0x{val:X}"))

    # Memory access check
    if mem_access:
        acc_type, width, form, base_reg, base_val, ea, mask, note = mem_access
        mask_str = mask if mask else "-"
        base_str = hex(base_val) if base_val is not None else "?"
        base_res = "full" if base_val is not None else "none"
        if ea is not None and ea in target_vals:
            t_name, t_space, t_val = target_vals[ea]
            hits.append((t_name, t_space, f"0x{pc:X}", current_func, acc_type, width, form, base_str, base_res, mask_str, note))

    # Register updates
    if hi == 0x9:
        pool_ea = pc + 4 + disp * 2
        val = int.from_bytes(rom[pool_ea:pool_ea+2], "big")
        if val & 0x8000:
            val |= 0xFFFF0000
        regs[n] = val
    elif hi == 0xD:
        pool_ea = ((pc + 4) & ~3) + disp * 4
        val = int.from_bytes(rom[pool_ea:pool_ea+4], "big")
        regs[n] = val
    elif hi == 0xE:
        imm = op & 0xFF
        val = (imm | 0xFFFFFF00) if (imm & 0x80) else imm
        regs[n] = val
    elif hi == 0x6:
        if disp4 == 3:
            regs[n] = regs[m]
        elif disp4 == 0xC:
            regs[n] = (regs[m] & 0xFF) if regs[m] is not None else None
        elif disp4 == 0xD:
            regs[n] = (regs[m] & 0xFFFF) if regs[m] is not None else None
        elif disp4 == 0xE:
            if regs[m] is not None:
                b = regs[m] & 0xFF
                regs[n] = (b | 0xFFFFFF00) if (b & 0x80) else b
            else:
                regs[n] = None
        elif disp4 == 0xF:
            if regs[m] is not None:
                w = regs[m] & 0xFFFF
                regs[n] = (w | 0xFFFF0000) if (w & 0x8000) else w
            else:
                regs[n] = None
        else:
            regs[n] = None
    elif hi == 0x7:
        imm = op & 0xFF
        imm_val = (imm | 0xFFFFFF00) if (imm & 0x80) else imm
        if regs[n] is not None:
            regs[n] = (regs[n] + imm_val) & 0xFFFFFFFF
    elif hi == 0x3:
        if disp4 == 0xC:
            if regs[n] is not None and regs[m] is not None:
                regs[n] = (regs[n] + regs[m]) & 0xFFFFFFFF
            else:
                regs[n] = None
        elif disp4 == 0x8:
            if regs[n] is not None and regs[m] is not None:
                regs[n] = (regs[n] - regs[m]) & 0xFFFFFFFF
            else:
                regs[n] = None
    elif hi == 0x4:
        if (op & 0xFF) == 0x1E:
            gbr = regs[m]
        elif (op & 0xFF) == 0x17:
            gbr = None
    elif hi == 0x5:
        regs[n] = None
    elif hi == 0x0 and disp4 in (0xC, 0xD, 0xE):
        regs[n] = None
    elif hi == 0x8 and (op >> 8) & 0xF in (0x4, 0x5):
        regs[0] = None
    elif hi == 0xC and (op >> 8) & 0xF in (0x4, 0x5, 0x6):
        regs[0] = None

    # Handle control transfer instructions / delay slots
    is_branch_delay = False
    is_branch_no_delay = False
    is_call = False
    is_ret = False

    if op in (0x000B, 0x002B): # rts, rte
        is_branch_delay = True
        is_ret = True
    elif hi in (0xA, 0xB): # bra, bsr
        is_branch_delay = True
        if hi == 0xB:
            is_call = True
    elif hi == 0x4 and (op & 0xFF) in (0x2B, 0x0B): # jmp, jsr
        is_branch_delay = True
        if (op & 0xFF) == 0x0B:
            is_call = True
    elif hi == 0x0 and (op & 0xFF) in (0x23, 0x03): # braf, bsrf
        is_branch_delay = True
        if (op & 0xFF) == 0x03:
            is_call = True
    elif hi == 0x8 and (op >> 8) & 0xF in (0xD, 0xF): # bt/s, bf/s
        is_branch_delay = True
    elif hi == 0x8 and (op >> 8) & 0xF in (0x9, 0xB): # bt, bf
        is_branch_no_delay = True

    if in_delay_slot:
        if delay_slot_type == "ret":
            regs = [None] * 16
        elif delay_slot_type == "call":
            for r in range(8):
                regs[r] = None
        elif delay_slot_type == "bra":
            for r in range(8):
                regs[r] = None
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
        for r in range(8):
            regs[r] = None

print("\nHits found:")
for t in targets:
    t_hits = [h for h in hits if h[0] == t[0]]
    print(f"Target {t[0]} ({len(t_hits)} hits):")
    for h in t_hits:
        print(f"  PC={h[2]} func={h[3]} acc={h[4]} width={h[5]} form={h[6]} base={h[7]} note={h[10]}")
