"""WO65803 corrected global RAM byte/bit cross-reference generator.

Python 3 standard library only. Additive successor to
EVIDENCE/WO65118_ram_byte_bit_xref_generator.py (which is preserved unchanged).

Fix mechanism:
  In WO65118-RAMXREF-1.5.0 line 359, displacements parsed from IDA's LST
  annotations for @(disp, gbr) and @(disp, rN) were multiplied a second time by
  access-width scale (`disp * scale`). Because IDA's LST already displays byte
  displacements (pre-scaled by 1/2/4 from the raw SH7058 opcode field), that
  produced `base + scale * already_scaled_byte_offset` for non-byte accesses.

This generator:
  1. Preserves 100% of WO65118's historical row identity, deduplication key,
     sort order, provenance columns, and historical `address`/`page` values.
  2. Adds separate `corrected_page`, `corrected_ea`, `access_span`,
     `corrected_end_ea`, `ea_changed`, `ea_delta_bytes`, `raw_opcode_hex`,
     `opcode_validation`, `correction_status`, and `correction_reason` columns.
  3. Independently validates every single row against the raw 16-bit big-endian
     SH7058 opcode in EVIDENCE/VERSA f501.bin.
"""
import argparse
import bisect
import datetime
import hashlib
import os
import re
import zipfile
from collections import Counter

VERSION = "WO65803-RAMXREF-CORRECTED-1.0.0"
BASE_VERSION = "WO65118-RAMXREF-1.5.0"
DEFAULT_MEMBER = "EL19A_Complete_Disassembly_ANNOTATED_V3_NEXT6_16_ALL_PENDING_ANNOTATIONS(1).lst"

LABEL_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_@]*):\s*$")
CODE_RE = re.compile(r"^([0-9A-F]{8})\s+([0-9A-F]{2}(?:\s+[0-9A-F]{2})*)\s+CODE\s+(\S+)(?:\s+(.*))?$")
ADDR_RE = re.compile(r"^([0-9A-F]{8})\s")
ANN_RE = re.compile(r";\s*h'([0-9A-Fa-f]{1,8})")
BRANCH = {"bt", "bf", "bt/s", "bf/s", "bra", "bra/s", "jmp", "jsr", "bsr", "rts", "rte", "trapa"}
MEM_OPERAND_RE = re.compile(r"@\(\s*((?:[^,()]|\([^)]*\))+?)\s*,\s*(gbr|r\d+|pc)\s*\)", re.I)
SIMPLE_MEM_RE = re.compile(r"@\s*(r\d+)", re.I)
WIDTH_RE = re.compile(r"\.(b|w|l)$", re.I)
SCALE = {"b": 1, "w": 2, "l": 4}
IMM_RE = re.compile(r"^#h'([0-9A-Fa-f]+)$", re.I)
REG_RE = re.compile(r"^r(\d+)$", re.I)
BIT_ACTION = {"and": "cleared", "or": "set", "xor": "toggled"}


def clean(text):
    return "" if not text else re.sub(r"\s+", " ", text.replace("\t", " ")).replace("|", "/").strip()


def fmt(v):
    return "?" if v is None else ("%08X" % (v & 0xFFFFFFFF)).lower()


def parse_listing_bytes(lst_bytes):
    lines = lst_bytes.decode("utf-8", "replace").splitlines()
    pending, labels, label_kind, code = [], {}, {}, []
    for ln in lines:
        m = LABEL_RE.match(ln)
        if m:
            pending.append(m.group(1))
            continue
        m = CODE_RE.match(ln)
        if m:
            pc, bs, mnem, ops = int(m.group(1), 16), bytes.fromhex(m.group(2)), m.group(3), m.group(4) or ""
            for name in pending:
                labels.setdefault(name, pc)
                label_kind[name] = "code"
            pending = []
            ann = ANN_RE.search(ops)
            code.append({
                "pc": pc,
                "bytes": bs,
                "mnem": mnem,
                "ops": ops,
                "instr": clean(mnem + " " + ops),
                "ann": ann.group(1).upper() if ann else None,
                "concordant": None,
            })
            continue
        m = ADDR_RE.match(ln)
        if m:
            for name in pending:
                labels.setdefault(name, int(m.group(1), 16))
                label_kind[name] = "data"
            pending = []
    return labels, label_kind, code


def imm_from(ops):
    parts = [p.strip() for p in ops.split(";")[0].split(",")]
    if parts:
        m = IMM_RE.match(parts[0])
        if m:
            return int(m.group(1), 16) & 0xFF
    return None


def writes_reg(rec, reg):
    parts = [p.strip() for p in rec["ops"].split(";")[0].split(",")]
    return bool(parts) and parts[-1].lower() == reg.lower()


def source_value(rec, rom, labels):
    a, m = rec["ann"], rec["mnem"].lower()
    if m in ("mov.l", "mov.w"):
        if a and len(a) == 8:
            return a, "full"
        if m == "mov.l":
            target = rec["ops"].split(";")[0].split(",")[0].strip().strip("@()").split(",")[0].strip()
            if target in labels:
                addr = labels[target]
                if 0 <= addr and addr + 4 <= len(rom):
                    return rom[addr:addr + 4].hex().upper(), "full"
            return None, None
        if a and len(a) == 4:
            return a, "partial"
        return None, None
    if m == "mov":
        imm = imm_from(rec["ops"])
        if a and len(a) <= 2:
            imm = int(a, 16)
        if imm is not None:
            return ("%08X" % (imm if imm < 0x80 else (0xFFFFFF00 | imm))), "full"
    return None, None


def resolve_back(pc, reg, pcs, by_pc, rom, labels, call_pcs, sorted_label_pcs, target_to_branches):
    i = bisect.bisect_left(pcs, pc) - 1
    found = None
    while i >= 0:
        rec = by_pc[pcs[i]]
        if rec["pc"] in call_pcs:
            return None, None, "call_boundary", None
        if writes_reg(rec, reg):
            found = rec
            break
        i -= 1
    if found is None:
        return None, None, "no_source_in_extent", None
    d = found["pc"]
    lo = bisect.bisect_right(sorted_label_pcs, d)
    hi = bisect.bisect_right(sorted_label_pcs, pc)
    for lab in sorted_label_pcs[lo:hi]:
        if any(b < d for b in target_to_branches.get(lab, ())):
            return None, None, "control_flow_boundary", None
    val, conf = source_value(found, rom, labels)
    if val:
        return val, conf, None, d
    return None, None, "unprovable_source", d


def parse_atom(atom, labels):
    m = re.match(r"^h'([0-9A-Fa-f]+)$", atom, re.I)
    if m:
        return int(m.group(1), 16)
    m = re.match(r"^0x([0-9A-Fa-f]+)$", atom, re.I)
    if m:
        return int(m.group(1), 16)
    if re.fullmatch(r"\d+", atom):
        return int(atom)
    if atom in labels:
        return labels[atom]
    return None


def parse_disp(text, labels):
    t = text.strip()
    while t.startswith("(") and t.endswith(")"):
        t = t[1:-1].strip()
    t = t.replace(" ", "")
    if t.lower() == "r0":
        return "r0"
    total = 0
    for token in re.findall(r"[+-]?[^+-]+", t):
        sign = 1
        if token[0] in "+-":
            sign = 1 if token[0] == "+" else -1
            token = token[1:]
        if not token:
            return None
        value = parse_atom(token, labels)
        if value is None:
            return None
        total += sign * value
    return total


def direction(mnem, ops):
    m, o = mnem.lower(), ops.strip()
    mem_first = o.startswith("@")
    mem_last = o.split(",")[-1].strip().startswith("@")
    base = m.split(".")[0]
    if base in BIT_ACTION and imm_from(ops) is not None and mem_last:
        return "rmw"
    if m.startswith("mov"):
        return "read" if mem_first else "write"
    if m.startswith("tst") or base == "tst":
        return "read"
    if mem_first:
        return "read"
    if mem_last:
        return "write"
    return "read"


def bit_meta(mnem, ops):
    base = mnem.lower().split(".")[0]
    imm = imm_from(ops)
    if imm is None:
        return None, "", ""
    parts = [p.strip() for p in ops.split(";")[0].split(",")]
    if len(parts) < 2:
        return None, "", ""
    mem_pos = any(p.startswith("@") for p in parts[1:])
    reg_m = REG_RE.match(parts[1])
    if base == "tst":
        if mem_pos:
            return "mem", imm, "tested"
        if reg_m:
            return "reg", imm, "tested"
    elif base in BIT_ACTION:
        action = BIT_ACTION[base]
        mask = (~imm & 0xFF) if base == "and" else imm
        if mem_pos:
            return "mem", mask, action
        if reg_m:
            return "reg", mask, action
    return None, "", ""


def decode_sh7058_opcode(op):
    """Independently decode SH7058 big-endian 16-bit memory/indirect opcode."""
    hi = (op >> 8) & 0xFF
    hi4 = (op >> 12) & 0xF
    lo4 = op & 0xF
    d8 = op & 0xFF
    d4 = op & 0xF
    if hi == 0xC4:
        return ("gbr_disp", "b", "read", d8, 1)
    if hi == 0xC5:
        return ("gbr_disp", "w", "read", d8, 2)
    if hi == 0xC6:
        return ("gbr_disp", "l", "read", d8, 4)
    if hi == 0xC0:
        return ("gbr_disp", "b", "write", d8, 1)
    if hi == 0xC1:
        return ("gbr_disp", "w", "write", d8, 2)
    if hi == 0xC2:
        return ("gbr_disp", "l", "write", d8, 4)
    if hi == 0x80:
        return ("base_disp", "b", "write", d4, 1)
    if hi == 0x84:
        return ("base_disp", "b", "read", d4, 1)
    if hi == 0x81:
        return ("base_disp", "w", "write", d4, 2)
    if hi == 0x85:
        return ("base_disp", "w", "read", d4, 2)
    if hi4 == 0x1:
        return ("base_disp", "l", "write", d4, 4)
    if hi4 == 0x5:
        return ("base_disp", "l", "read", d4, 4)
    if hi in (0xCC, 0xCD, 0xCE, 0xCF):
        return ("gbr_r0", "b", "read", None, 1)
    if hi4 == 0x0 and lo4 in (0x4, 0x5, 0x6, 0xC, 0xD, 0xE):
        w = {4: "b", 5: "w", 6: "l", 0xC: "b", 0xD: "w", 0xE: "l"}[lo4]
        acc = "write" if lo4 in (4, 5, 6) else "read"
        return ("base_r0", w, acc, None, 1)
    if hi4 == 0x2 and lo4 in (0, 1, 2):
        return ("base_indirect", {0: "b", 1: "w", 2: "l"}[lo4], "write", None, 1)
    if hi4 == 0x6 and lo4 in (0, 1, 2, 4, 5, 6):
        return ("base_indirect", {0: "b", 1: "w", 2: "l", 4: "b", 5: "w", 6: "l"}[lo4], "read", None, 1)
    if hi4 == 0x4 and (op & 0xFF) in (0x0B, 0x2B):
        return ("base_indirect_branch", "l", "read", None, 1)
    return ("other", None, None, None, None)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rom", default=os.path.join(here, "VERSA f501.bin"))
    ap.add_argument("--listing", default=None, help="Optional extracted .lst path")
    ap.add_argument("--listing-zip", default=os.path.join(
        here, "EL19A_Complete_Disassembly_ANNOTATED_V3_NEXT6_14_GBR_BASE_RESOLVED.zip"))
    ap.add_argument("--listing-member", default=DEFAULT_MEMBER)
    ap.add_argument("--verify-wo65118", default=os.path.join(here, "WO65118_ram_byte_bit_xref.tsv"))
    ap.add_argument("--out", default=os.path.join(here, "WO65803_ram_byte_bit_xref_corrected.tsv"))
    args = ap.parse_args()

    rom = open(args.rom, "rb").read()
    rom_md5, rom_sha = hashlib.md5(rom).hexdigest(), hashlib.sha256(rom).hexdigest()

    if args.listing:
        lst_bytes = open(args.listing, "rb").read()
        lst_source = args.listing
    else:
        with zipfile.ZipFile(args.listing_zip, "r") as zf:
            lst_bytes = zf.read(args.listing_member)
        lst_source = os.path.basename(args.listing_zip) + "::" + args.listing_member
    lst_md5, lst_sha = hashlib.md5(lst_bytes).hexdigest(), hashlib.sha256(lst_bytes).hexdigest()

    labels, label_kind, code = parse_listing_bytes(lst_bytes)
    code.sort(key=lambda r: r["pc"])
    pcs = [r["pc"] for r in code]
    by_pc = {r["pc"]: r for r in code}
    label_pcs = set(labels.values())
    sorted_label_pcs = sorted(label_pcs)

    call_pcs = set()
    target_to_branches = {}
    for rec in code:
        m = rec["mnem"].lower()
        if m in ("jsr", "bsr", "jmp", "rts", "rte", "trapa"):
            call_pcs.add(rec["pc"])
        if m in ("bt", "bf", "bt/s", "bf/s", "bra", "bra/s", "jsr", "bsr", "jmp"):
            tok = rec["ops"].split(";")[0].strip().split(",")[-1].strip()
            if tok in labels:
                target_to_branches.setdefault(labels[tok], []).append(rec["pc"])

    checked = matched = 0
    for r in code:
        end = r["pc"] + len(r["bytes"])
        r["concordant"] = bool(0 <= r["pc"] < end <= len(rom) and rom[r["pc"]:end] == r["bytes"])
        checked += 1
        matched += int(r["concordant"])

    starts = sorted((pc, name) for name, pc in labels.items()
                    if label_kind.get(name) == "code" and not name.startswith(("loc_", "locret_")))
    funcs = []
    for i, (start, label) in enumerate(starts):
        nxt = starts[i + 1][0] if i + 1 < len(starts) else max(pcs) + 4
        cand = code[bisect.bisect_left(pcs, start):bisect.bisect_left(pcs, nxt)]
        rets = [r for r in cand if r["concordant"] and r["mnem"].lower() in ("rts", "rte")]
        end_pc = rets[-1]["pc"] + len(rets[-1]["bytes"]) + 2 if rets else nxt
        ext = [r for r in cand if r["pc"] < end_pc]
        gbrs = []
        for r in ext:
            m = re.match(r"^\s*r(\d+)\s*,\s*gbr\s*$", r["ops"].lower())
            if r["mnem"].lower() == "ldc" and m:
                val, conf, _, _ = resolve_back(
                    r["pc"], "r" + m.group(1), pcs, by_pc, rom, labels,
                    call_pcs, sorted_label_pcs, target_to_branches)
                if val and conf == "full":
                    gbrs.append(int(val, 16))
        distinct = sorted(set(gbrs))
        funcs.append({"start": start, "end": end_pc, "label": label,
                      "gbr": distinct[0] if len(distinct) == 1 else None})
    func_starts = [f["start"] for f in funcs]

    rows = []
    extra_by_idx = []
    seen = set()
    row_index = {}
    last_ram_load = {}
    unres_count = 0
    unres_seen = set()

    def track_unres(pc, reason, instr, note):
        nonlocal unres_count
        k = ("%08X" % pc, reason, clean(instr), clean(note))
        if k not in unres_seen:
            unres_seen.add(k)
            unres_count += 1

    for rec in code:
        if rec["pc"] in label_pcs or rec["mnem"].lower() in BRANCH:
            last_ram_load.clear()
        if not rec["concordant"]:
            track_unres(rec["pc"], "pc_concordance_mismatch", rec["instr"], "row dropped")
            continue

        fi = bisect.bisect_right(func_starts, rec["pc"]) - 1
        fn = funcs[fi] if fi >= 0 else {"label": "unknown", "gbr": None}
        wm = WIDTH_RE.search(rec["mnem"])
        width = wm.group(1).lower() if wm else "l"
        scale = SCALE[width]
        acc = direction(rec["mnem"], rec["ops"])
        kind, mask, action = bit_meta(rec["mnem"], rec["ops"])

        if kind == "reg":
            reg_name = "r" + REG_RE.match(
                [p.strip() for p in rec["ops"].split(";")[0].split(",")][1]).group(1).lower()
            target = last_ram_load.get(reg_name)
            if target is not None:
                idx = row_index.get(target)
                if idx is not None:
                    rows[idx][10] += " bit_%s=h'%02X@%08X" % (action, mask, rec["pc"])

        written = None
        parts = [p.strip() for p in rec["ops"].split(";")[0].split(",")]
        if parts:
            wm2 = REG_RE.match(parts[-1])
            if wm2 and rec["mnem"].lower().split(".")[0] not in ("tst", "cmp", "bt", "bf"):
                written = "r" + wm2.group(1).lower()
        if written:
            last_ram_load.pop(written, None)

        operands = [(dm.group(1).strip(), dm.group(2).lower(), False)
                    for dm in MEM_OPERAND_RE.finditer(rec["ops"])]
        operands += [("0", sm.group(1).lower(), True)
                     for sm in SIMPLE_MEM_RE.finditer(rec["ops"])]

        for disp_txt, reg, simple in operands:
            base = fn["gbr"] if reg == "gbr" else None
            reason_unres = "gbr_not_provable" if reg == "gbr" else "base_not_provable"
            if reg == "pc":
                base = None
                reason_unres = "pool_relative_rom"
            elif reg != "gbr":
                val, conf, _, _ = resolve_back(
                    rec["pc"], reg, pcs, by_pc, rom, labels,
                    call_pcs, sorted_label_pcs, target_to_branches)
                if val and conf == "full":
                    base = int(val, 16)
            disp = parse_disp(disp_txt, labels)
            if disp == "r0":
                r0val, conf, _, _ = resolve_back(
                    rec["pc"], "r0", pcs, by_pc, rom, labels,
                    call_pcs, sorted_label_pcs, target_to_branches)
                if not (r0val and conf == "full"):
                    track_unres(rec["pc"], "index_not_provable", rec["instr"],
                                "base=%s function=%s" % (fmt(base), fn["label"]))
                    continue
                off_hist = int(r0val, 16)
                off_corr = off_hist
                form = "gbr_r0" if reg == "gbr" else "base_r0"
            else:
                if simple:
                    off_hist = 0
                    off_corr = 0
                    form = "base_indirect"
                else:
                    if disp is None:
                        track_unres(rec["pc"], "displacement_not_provable", rec["instr"],
                                    "base=%s function=%s disp=%s" % (fmt(base), fn["label"], disp_txt))
                        continue
                    # Historical bug in WO65118 line 359: disp * scale applied to already-byte-scaled LST disp.
                    off_hist = disp * scale
                    # Corrected byte offset: IDA LST displacement is already in bytes.
                    off_corr = disp
                    form = "gbr_disp" if reg == "gbr" else "base_disp"

            if base is None:
                track_unres(rec["pc"], reason_unres, rec["instr"], "function=%s" % fn["label"])
                continue

            ea_hist = (base + off_hist) & 0xFFFFFFFF
            if ea_hist < 0xFFFF0000:
                continue  # preserve exact WO65118 filter and row universe

            ea_corr = (base + off_corr) & 0xFFFFFFFF
            note = "base=" + fmt(base)
            bmask, baction = (("%08X" % mask), action) if kind == "mem" else ("", "")

            # Exact original WO65118 deduplication key — NEVER re-keyed by corrected EA
            key = (fmt(ea_hist & 0xFFFFFF00), fmt(ea_hist), "%08X" % rec["pc"], fn["label"], acc,
                   width, bmask, baction, form, rec["instr"], note)
            if key in seen:
                continue
            seen.add(key)

            # Independent ROM opcode validation
            op = int.from_bytes(rom[rec["pc"]:rec["pc"] + 2], "big")
            op_hex = "%04X" % op
            dec_form, dec_w, dec_acc, raw_disp, op_scale = decode_sh7058_opcode(op)
            if form in ("gbr_disp", "base_disp"):
                assert dec_form == form and dec_w == width and dec_acc == acc, (
                    f"Opcode mismatch at {rec['pc']:08X}: {op_hex} vs {(form, width, acc)}")
                expected_byte_off = raw_disp * op_scale
                assert disp == expected_byte_off, (
                    f"Disp mismatch at {rec['pc']:08X}: lst={disp} vs raw {raw_disp}*{op_scale}")
                op_val = "PASS_ROM"
            elif form == "gbr_r0":
                assert dec_form == "gbr_r0" and dec_w == width, f"Opcode mismatch at {rec['pc']:08X}"
                op_val = "PASS_ROM"
            elif form == "base_r0":
                assert dec_form == "base_r0" and dec_w == width and dec_acc == acc, f"Opcode mismatch at {rec['pc']:08X}"
                op_val = "PASS_ROM"
            elif form == "base_indirect":
                if dec_form == "base_indirect_branch":
                    assert width == "l" and acc == "read", f"Branch indirect mismatch at {rec['pc']:08X}"
                    op_val = "PASS_ROM_BR"
                else:
                    assert dec_form == "base_indirect" and dec_w == width and dec_acc == acc, (
                        f"Indirect opcode mismatch at {rec['pc']:08X}: {op_hex}")
                    op_val = "PASS_ROM"
            else:
                raise AssertionError(f"Unexpected form {form}")

            ea_changed = 1 if ea_corr != ea_hist else 0
            delta_bytes = ea_corr - ea_hist
            corr_end = (ea_corr + scale - 1) & 0xFFFFFFFF

            if form in ("gbr_disp", "base_disp"):
                if width in ("w", "l") and ea_changed:
                    c_status = "corrected_double_scale"
                    c_reason = f"0x{raw_disp:02X}*x{op_scale}=+0x{off_corr:X};old=+0x{off_hist:X}"
                elif width in ("w", "l") and not ea_changed:
                    c_status = "unchanged_nonbyte_zero_disp"
                    c_reason = f"0x00*x{op_scale}=+0x0"
                else:
                    c_status = "unchanged_byte_scale1"
                    c_reason = f"0x{raw_disp:02X}"
            elif form in ("gbr_r0", "base_r0"):
                c_status = "unchanged_unscaled_form"
                c_reason = "r0"
            else:
                c_status = "unchanged_unscaled_form"
                c_reason = "@rN_br" if dec_form == "base_indirect_branch" else "@rN"

            idx_row = len(rows)
            row_index[(rec["pc"], ea_hist)] = idx_row
            rows.append(list(key))
            extra_by_idx.append({
                "sort_key": (key[0], key[1], key[2]),
                "corrected_page": fmt(ea_corr & 0xFFFFFF00),
                "corrected_ea": fmt(ea_corr),
                "access_span": scale,
                "corrected_end_ea": fmt(corr_end),
                "ea_changed": ea_changed,
                "ea_delta_bytes": delta_bytes,
                "raw_opcode_hex": op_hex,
                "opcode_validation": op_val,
                "correction_status": c_status,
                "correction_reason": c_reason,
            })

            if acc == "read":
                dest = [p.strip().lower() for p in rec["ops"].split(";")[0].split(",")][-1]
                if REG_RE.match(dest):
                    last_ram_load[dest] = (rec["pc"], ea_hist)

    # Sort together preserving EXACT historical WO65118 row order
    paired = list(zip(rows, extra_by_idx))
    paired.sort(key=lambda item: (item[0][0], item[0][1], item[0][2]))

    # Verify 100% parity against original WO65118_ram_byte_bit_xref.tsv (read-only)
    wo65118_sha = "N/A"
    parity_ok = None
    if args.verify_wo65118 and os.path.exists(args.verify_wo65118):
        w_bytes = open(args.verify_wo65118, "rb").read()
        wo65118_sha = hashlib.sha256(w_bytes).hexdigest()
        orig_rows = [
            ln.rstrip("\n").split("\t")
            for ln in w_bytes.decode("utf-8").splitlines()
            if not ln.startswith("#") and not ln.startswith("page\t")
        ]
        gen_orig = [p[0] for p in paired]
        assert gen_orig == orig_rows, (
            f"Historical parity mismatch: {len(gen_orig)} vs {len(orig_rows)}")
        parity_ok = True

    status_counts = Counter(p[1]["correction_status"] for p in paired)
    changed_counts = Counter((p[0][8], p[0][5]) for p in paired if p[1]["ea_changed"])
    affected_path_nonbyte = sum(
        1 for p in paired if p[0][8] in ("gbr_disp", "base_disp") and p[0][5] in ("w", "l")
    )
    page_changed = sum(1 for p in paired if p[0][0] != p[1]["corrected_page"])
    below_ram = sum(1 for p in paired if int(p[1]["corrected_ea"], 16) < 0xFFFF0000)
    assert below_ram == 0, f"Unexpected non-RAM corrected EA count: {below_ram}"

    header = [
        "WO65803 corrected global RAM byte/bit cross-reference (additive successor to WO65118)",
        "generator_version: " + VERSION,
        "historical_baseline_version: " + BASE_VERSION,
        "rom_path: EVIDENCE/VERSA f501.bin",
        "rom_md5: " + rom_md5,
        "rom_sha256: " + rom_sha,
        "listing_source: " + lst_source,
        "listing_md5: " + lst_md5,
        "listing_sha256: " + lst_sha,
        "listing_bytes: " + str(len(lst_bytes)),
        "wo65118_tsv_sha256: " + wo65118_sha,
        "run_date: " + datetime.date.today().isoformat(),
        "pc_concordance_rows_checked: " + str(checked),
        "pc_concordance_rows_matched: " + str(matched),
        "total_rows_preserved: " + str(len(paired)),
        "affected_path_nonbyte_disp_rows: " + str(affected_path_nonbyte),
        "ea_changed_rows: " + str(sum(changed_counts.values())),
        "zero_disp_nonbyte_invariant_rows: " + str(status_counts["unchanged_nonbyte_zero_disp"]),
        "page_changed_rows: " + str(page_changed),
        "opcode_validation_passed: " + str(len(paired)) + " / " + str(len(paired)),
        "unresolved_sites_invariant: " + str(unres_count),
        "historical_row_parity_verified: " + str(parity_ok),
        "classification: structural access facts only; historical address/page columns preserved unchanged; no semantic, physical or unit naming",
    ]

    cols = [
        "page", "address", "pc", "function", "access", "width", "bit_mask", "bit_action",
        "form", "instruction", "note",
        "row_id", "corrected_page", "corrected_ea", "access_span", "corrected_end_ea",
        "ea_changed", "ea_delta_bytes", "raw_opcode_hex", "opcode_validation",
        "correction_status", "correction_reason",
    ]

    with open(args.out, "w", encoding="utf-8", newline="\n") as f:
        for h in header:
            f.write("# " + h + "\n")
        f.write("\t".join(cols) + "\n")
        for idx, (orig, ext) in enumerate(paired, start=1):
            out_row = list(orig) + [
                idx,
                ext["corrected_page"],
                ext["corrected_ea"],
                ext["access_span"],
                ext["corrected_end_ea"],
                ext["ea_changed"],
                ext["ea_delta_bytes"],
                ext["raw_opcode_hex"],
                ext["opcode_validation"],
                ext["correction_status"],
                ext["correction_reason"],
            ]
            f.write("\t".join(str(x) for x in out_row) + "\n")

    print("VERSION", VERSION)
    print("PC_CONCORDANCE", matched, "/", checked)
    print("HISTORICAL_PARITY_PASS", parity_ok)
    print("TOTAL_ROWS", len(paired))
    print("AFFECTED_PATH_NONBYTE_DISP", affected_path_nonbyte)
    print("EA_CHANGED_TOTAL", sum(changed_counts.values()), sorted(changed_counts.items()))
    print("STATUS_COUNTS", sorted(status_counts.items()))
    print("PAGE_CHANGED", page_changed, "BELOW_FFFF0000", below_ram, "UNRESOLVED_INVARIANT", unres_count)

    # Independent anchor self-tests (WO65674, WO65686, WO65698, WO65791, WO65493)
    by_pc_row = {}
    for orig, ext in paired:
        by_pc_row.setdefault(orig[2], []).append((orig, ext))

    def check_anchor(pc_hex, exp_old, exp_corr, exp_span):
        matches = by_pc_row.get(pc_hex, [])
        assert len(matches) == 1, f"Anchor {pc_hex} count={len(matches)}"
        o, e = matches[0]
        assert o[1] == exp_old, f"Anchor {pc_hex} old={o[1]} != {exp_old}"
        assert e["corrected_ea"] == exp_corr, f"Anchor {pc_hex} corr={e['corrected_ea']} != {exp_corr}"
        assert e["access_span"] == exp_span, f"Anchor {pc_hex} span={e['access_span']} != {exp_span}"

    check_anchor("00091402", "ffff99e4", "ffff97c8", 4)  # WO65674
    check_anchor("00091404", "ffff974e", "ffff974e", 1)  # WO65674
    check_anchor("0009140E", "ffff9814", "ffff9754", 4)  # WO65686
    check_anchor("00091410", "ffff9754", "ffff9724", 4)  # WO65686
    check_anchor("00091412", "ffff9744", "ffff9720", 4)  # WO65686
    check_anchor("00091414", "ffff97e0", "ffff977a", 2)  # WO65698
    check_anchor("00091416", "ffff975c", "ffff9738", 2)  # WO65698
    check_anchor("00091418", "ffff9944", "ffff97a0", 4)  # WO65698
    check_anchor("000914BA", "ffff9984", "ffff97b0", 4)  # WO65791 (carried double-scaled FFFF9984)
    check_anchor("000292DC", "ffff1820", "ffff181e", 2)  # WO65493
    check_anchor("00037154", "ffff1818", "ffff1812", 2)  # WO65493
    check_anchor("0007B2D8", "ffff1820", "ffff17e4", 4)  # WO65493
    print("ANCHOR_CHECKS_PASS", 12, "/", 12)


if __name__ == "__main__":
    main()
