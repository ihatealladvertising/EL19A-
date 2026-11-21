"""WO65118 global RAM byte/bit cross-reference generator.

Python 3 standard library only. Produces a RAM-only cross-reference with
bit-mask metadata, a per-page slice guide and a mandatory unresolved list.
No supplied target list, no semantic naming, no tools/ entry.
"""
import argparse
import bisect
import datetime
import hashlib
import os
import re
from collections import Counter, defaultdict

VERSION = "WO65118-RAMXREF-1.5.0"
MEMBER = "EL19A_Complete_Disassembly_ANNOTATED_V3_NEXT6_16_ALL_PENDING_ANNOTATIONS(1).lst"
ROM_PATH = LST_PATH = OUT_MAIN = OUT_PAGES = OUT_UNRES = None
TARGET_TO_BRANCHES = {}
CALL_PCS = set()
SORTED_LABEL_PCS = []

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


def parse_listing():
    lines = open(LST_PATH, "rb").read().decode("utf-8", "replace").splitlines()
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
            code.append({"pc": pc, "bytes": bs, "mnem": mnem, "ops": ops,
                         "instr": clean(mnem + " " + ops),
                         "ann": ann.group(1).upper() if ann else None, "concordant": None})
            continue
        m = ADDR_RE.match(ln)
        if m:
            for name in pending:
                labels.setdefault(name, int(m.group(1), 16))
                label_kind[name] = "data"
            pending = []
    return labels, label_kind, code


def writes_reg(rec, reg):
    parts = [p.strip() for p in rec["ops"].split(";")[0].split(",")]
    return bool(parts) and parts[-1].lower() == reg.lower()


def source_value(rec, rom, labels):
    a, m = rec["ann"], rec["mnem"].lower()
    if m in ("mov.l", "mov.w"):
        if a and len(a) == 8:
            return a, "full"          # sign-extended 16-bit or full 32-bit pool value
        if m == "mov.l":
            target = rec["ops"].split(";")[0].split(",")[0].strip().strip("@()").split(",")[0].strip()
            if target in labels:
                addr = labels[target]
                if 0 <= addr and addr + 4 <= len(rom):
                    return rom[addr:addr + 4].hex().upper(), "full"
            return None, None
        if a and len(a) == 4:
            return a, "partial"       # 16-bit literal; extension not provable
        return None, None
    if m == "mov":
        # mov #imm,Rn carries the immediate in the operand, not in a ';' annotation.
        imm = imm_from(rec["ops"])
        if a and len(a) <= 2:
            imm = int(a, 16)
        if imm is not None:
            return ("%08X" % (imm if imm < 0x80 else (0xFFFFFF00 | imm))), "full"
    return None, None


def resolve_back(pc, reg, pcs, by_pc, label_pcs, rom, labels):
    """Find the nearest earlier definition of reg and validate that every
    label crossed after it is dominated by that definition (dominance-lite).
    Calls/returns always invalidate; a branch arriving before the definition
    at a label after it makes the value unprovable on that path.
    """
    i = bisect.bisect_left(pcs, pc) - 1
    found = None
    while i >= 0:
        rec = by_pc[pcs[i]]
        if rec["pc"] in CALL_PCS:
            return None, None, "call_boundary", None
        if writes_reg(rec, reg):
            found = rec
            break
        i -= 1
    if found is None:
        return None, None, "no_source_in_extent", None
    d = found["pc"]
    lo = bisect.bisect_right(SORTED_LABEL_PCS, d)
    hi = bisect.bisect_right(SORTED_LABEL_PCS, pc)
    for lab in SORTED_LABEL_PCS[lo:hi]:
        if any(b < d for b in TARGET_TO_BRANCHES.get(lab, ())):
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
    if m.startswith("tst"):
        return "read"
    if base == "tst":
        return "read"
    if mem_first:
        return "read"
    if mem_last:
        return "write"
    return "read"


def imm_from(ops):
    parts = [p.strip() for p in ops.split(";")[0].split(",")]
    if parts:
        m = IMM_RE.match(parts[0])
        if m:
            return int(m.group(1), 16) & 0xFF
    return None


def bit_meta(mnem, ops):
    """Return (kind, mask, action) where kind is 'mem', 'reg' or None."""
    m, base = mnem.lower(), mnem.lower().split(".")[0]
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


def fmt(v):
    return "?" if v is None else ("%08X" % (v & 0xFFFFFFFF)).lower()


def main():
    global ROM_PATH, LST_PATH, OUT_MAIN, OUT_PAGES, OUT_UNRES
    global TARGET_TO_BRANCHES, CALL_PCS, SORTED_LABEL_PCS
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rom", default=os.path.join(here, "VERSA f501.bin"))
    ap.add_argument("--listing", required=True)
    ap.add_argument("--out", default=os.path.join(here, "WO65118_ram_byte_bit_xref.tsv"))
    ap.add_argument("--pages", default=os.path.join(here, "WO65118_ram_byte_bit_xref_page_index.tsv"))
    ap.add_argument("--unresolved", default=os.path.join(here, "WO65118_ram_byte_bit_xref_unresolved.tsv"))
    args = ap.parse_args()
    ROM_PATH, LST_PATH, OUT_MAIN, OUT_PAGES, OUT_UNRES = args.rom, args.listing, args.out, args.pages, args.unresolved

    rom = open(ROM_PATH, "rb").read()
    rom_md5, rom_sha = hashlib.md5(rom).hexdigest(), hashlib.sha256(rom).hexdigest()
    lst = open(LST_PATH, "rb").read()
    lst_sha = hashlib.sha256(lst).hexdigest()
    labels, label_kind, code = parse_listing()
    code.sort(key=lambda r: r["pc"])
    pcs = [r["pc"] for r in code]
    by_pc = {r["pc"]: r for r in code}
    label_pcs = set(labels.values())
    SORTED_LABEL_PCS = sorted(label_pcs)
    for rec in code:
        m = rec["mnem"].lower()
        if m in ("jsr", "bsr", "jmp", "rts", "rte", "trapa"):
            CALL_PCS.add(rec["pc"])
        if m in ("bt", "bf", "bt/s", "bf/s", "bra", "bra/s", "jsr", "bsr", "jmp"):
            tok = rec["ops"].split(";")[0].strip().split(",")[-1].strip()
            if tok in labels:
                TARGET_TO_BRANCHES.setdefault(labels[tok], []).append(rec["pc"])

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
                val, conf, _, _ = resolve_back(r["pc"], "r" + m.group(1), pcs, by_pc, label_pcs, rom, labels)
                if val and conf == "full":
                    gbrs.append(int(val, 16))
        distinct = sorted(set(gbrs))
        funcs.append({"start": start, "end": end_pc, "label": label,
                      "gbr": distinct[0] if len(distinct) == 1 else None})
    func_starts = [f["start"] for f in funcs]

    rows, unres = [], []
    seen = set()
    row_index = {}
    last_ram_load = {}

    def add_unres(pc, reason, instr, note):
        key = ("%08X" % pc, reason, clean(instr), clean(note))
        if key not in seen:
            seen.add(key)
            unres.append(list(key))

    for rec in code:
        if rec["pc"] in label_pcs or rec["mnem"].lower() in BRANCH:
            last_ram_load.clear()
        if not rec["concordant"]:
            add_unres(rec["pc"], "pc_concordance_mismatch", rec["instr"], "row dropped")
            continue

        fi = bisect.bisect_right(func_starts, rec["pc"]) - 1
        fn = funcs[fi] if fi >= 0 else {"label": "unknown", "gbr": None}
        wm = WIDTH_RE.search(rec["mnem"])
        width = wm.group(1).lower() if wm else "l"
        scale = SCALE[width]
        acc = direction(rec["mnem"], rec["ops"])
        kind, mask, action = bit_meta(rec["mnem"], rec["ops"])

        # Register-based bit test on a value loaded from RAM in this straight-line region.
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
            reason = "gbr_not_provable" if reg == "gbr" else "base_not_provable"
            if reg == "pc":
                base = None
                reason = "pool_relative_rom"
            elif reg != "gbr":
                val, conf, _, _ = resolve_back(rec["pc"], reg, pcs, by_pc, label_pcs, rom, labels)
                if val and conf == "full":
                    base = int(val, 16)
            disp = parse_disp(disp_txt, labels)
            if disp == "r0":
                r0val, conf, _, _ = resolve_back(rec["pc"], "r0", pcs, by_pc, label_pcs, rom, labels)
                if not (r0val and conf == "full"):
                    add_unres(rec["pc"], "index_not_provable", rec["instr"],
                              "base=%s function=%s" % (fmt(base), fn["label"]))
                    continue
                offset, form = int(r0val, 16), ("gbr_r0" if reg == "gbr" else "base_r0")
            else:
                if simple:
                    offset, form = 0, "base_indirect"
                else:
                    if disp is None:
                        add_unres(rec["pc"], "displacement_not_provable", rec["instr"],
                                  "base=%s function=%s disp=%s" % (fmt(base), fn["label"], disp_txt))
                        continue
                    offset, form = disp * scale, ("gbr_disp" if reg == "gbr" else "base_disp")
            if base is None:
                add_unres(rec["pc"], reason, rec["instr"], "function=%s" % fn["label"])
                continue
            ea = (base + offset) & 0xFFFFFFFF
            if ea < 0xFFFF0000:
                continue                      # RAM-only index
            note = "base=" + fmt(base)
            bmask, baction = ("", "")
            if kind == "mem":
                bmask, baction = ("%08X" % mask), action
            key = (fmt(ea & 0xFFFFFF00), fmt(ea), "%08X" % rec["pc"], fn["label"], acc,
                   width, bmask, baction, form, rec["instr"], note)
            if key in seen:
                continue
            seen.add(key)
            row_index[(rec["pc"], ea)] = len(rows)
            rows.append(list(key))
            if acc == "read":
                dest = [p.strip().lower() for p in rec["ops"].split(";")[0].split(",")][-1]
                if REG_RE.match(dest):
                    last_ram_load[dest] = (rec["pc"], ea)

    rows.sort(key=lambda r: (r[0], r[1], r[2]))
    unres.sort(key=lambda r: (r[0], r[1]))

    pages = defaultdict(lambda: [0, set(), 0, 0, 0, None, None])
    for r in rows:
        p = pages[r[0]]
        p[0] += 1
        p[1].add(r[1])
        p[2 + {"read": 0, "write": 1, "rmw": 2}[r[4]]] += 1
        p[5] = r[2] if p[5] is None else min(p[5], r[2])
        p[6] = r[2] if p[6] is None else max(p[6], r[2])
    page_rows = [[k, str(v[0]), str(len(v[1])), str(v[2]), str(v[3]), str(v[4]), v[5], v[6]]
                 for k, v in sorted(pages.items())]

    def write(path, header, cols, data):
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            for line in header:
                f.write("# " + line + "\n")
            f.write("\t".join(cols) + "\n")
            for row in data:
                f.write("\t".join(str(x) for x in row) + "\n")

    common = [
        "WO65118 global RAM byte/bit cross-reference",
        "generator_version: " + VERSION,
        "rom_path: EVIDENCE/VERSA f501.bin",
        "rom_md5: " + rom_md5,
        "rom_sha256: " + rom_sha,
        "listing_member: " + MEMBER,
        "listing_sha256: " + lst_sha,
        "listing_bytes: " + str(len(lst)),
        "run_date: " + datetime.date.today().isoformat(),
        "pc_concordance_rows_checked: " + str(checked),
        "pc_concordance_rows_matched: " + str(matched),
        "target_file_sha256: N/A (global index; no supplied targets)",
        "method_limits: computed pointers, pointer tables, block-copy and movca.l transport are not modelled; unresolved sites are listed, never treated as absence",
        "classification: structural access facts only; no semantic, physical or unit naming; tst #imm sets T when the tested bit is clear (playbook)",
    ]
    write(OUT_MAIN, common,
          ["page", "address", "pc", "function", "access", "width", "bit_mask", "bit_action",
           "form", "instruction", "note"], rows)
    write(OUT_PAGES, common,
          ["page", "accesses", "distinct_addresses", "readers", "writers", "rmw", "first_pc", "last_pc"], page_rows)
    write(OUT_UNRES, common,
          ["pc", "reason", "instruction", "note"], unres)

    def at(addr):
        return [r for r in rows if r[1] == addr]

    print("VERSION", VERSION)
    print("PC_CONCORDANCE", matched, "/", checked)
    print("RAM_ROWS", len(rows), "PAGES", len(pages), "UNRESOLVED", len(unres))
    print("ACCESS", Counter(r[4] for r in rows).most_common())
    print("FORMS", Counter(r[8] for r in rows).most_common())
    print("BIT_ACTIONS", Counter(r[7] for r in rows if r[7]).most_common())
    print("UNRES_REASONS", Counter(r[1] for r in unres).most_common())

    r1 = at("ffff85df")
    print("R1_FFFF85DF_READERS", sorted((r[2], r[8]) for r in r1 if r[4] == "read"))
    r1pcs = sorted(r[2].lower() for r in r1 if r[4] == "read")
    print("R1_PASS", r1pcs == ["00046bde", "00047014"])
    print("R2_FFFF85E0_ROWS", len(at("ffff85e0")), "PASS", len(at("ffff85e0")) == 0)
    r3 = at("ffff1db4")
    r3pcs = [(r[2].lower(), r[4]) for r in r3]
    print("R3_FFFF1DB4", [x for x in r3pcs if x[0] in ("0004042c", "0004044a")])
    print("R3_PASS", ("0004042c", "read") in r3pcs and ("0004044a", "write") in r3pcs)
    print("R4_PKIORW_ROWS", len(at("fffff770")))
    print("R4_PASS", len(at("fffff770")) == 0)
    over = [r for r in rows if "base=0000821e" in r[10] and r[1].startswith("ffff8")]
    print("R5_ROM_GBR_OVERREACH", len(over), "PASS", len(over) == 0)
    d860d = [r for r in rows if r[1] == "ffff860d"
             and ("bit_tested=h'08" in r[10] or "bit_tested=h'20" in r[10]
                  or r[6] in ("00000008", "00000020"))]
    print("CMP_FFFF860D_BIT3_5_ROWS", len(d860d), "DISTINCT_PCS", len(set(r[2] for r in d860d)),
          "ALL_ADDRESS_ROWS", len(at("ffff860d")),
          "ALL_BIT_NOTED", sum(1 for r in at("ffff860d") if "bit_" in r[10]))
    d84ba = at("ffff84ba")
    print("CMP_FFFF84BA_READERS", sum(1 for r in d84ba if r[4] == "read"),
          "WRITERS", sum(1 for r in d84ba if r[4] == "write"))


if __name__ == "__main__":
    main()
