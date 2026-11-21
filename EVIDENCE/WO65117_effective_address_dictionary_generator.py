"""WO65117 aggregate effective-address dictionary generator.

Python 3 standard library only. Converts resolved GBR/base provenance into
arithmetic effective addresses for the SH-2 displaced and r0-indexed operand
forms found in the V3_NEXT6_16 listing. No target list, no per-target
reader/writer claim, no tools/ entry.
"""
import argparse
import bisect
import datetime
import hashlib
import os
import re
from collections import Counter

VERSION = "WO65117-EADICT-1.2.0"
MEMBER = "EL19A_Complete_Disassembly_ANNOTATED_V3_NEXT6_16_ALL_PENDING_ANNOTATIONS(1).lst"
ROM_PATH = LST_PATH = OUT_MAIN = OUT_UNRES = None

LABEL_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_@]*):\s*$")
CODE_RE = re.compile(r"^([0-9A-F]{8})\s+([0-9A-F]{2}(?:\s+[0-9A-F]{2})*)\s+CODE\s+(\S+)(?:\s+(.*))?$")
ADDR_RE = re.compile(r"^([0-9A-F]{8})\s")
ANN_RE = re.compile(r";\s*h'([0-9A-Fa-f]{1,8})")
BRANCH = {"bt", "bf", "bt/s", "bf/s", "bra", "bra/s", "jmp", "jsr", "bsr", "rts", "rte", "trapa"}
MEM_OPERAND_RE = re.compile(r"@\(\s*((?:[^,()]|\([^)]*\))+?)\s*,\s*(gbr|r\d+)\s*\)", re.I)
WIDTH_RE = re.compile(r"\.(b|w|l)$", re.I)
SCALE = {"b": 1, "w": 2, "l": 4}


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
    if m == "mov.l":
        if a and len(a) == 8:
            return a, "full"
        target = rec["ops"].split(";")[0].split(",")[0].strip().strip("@()").split(",")[0].strip()
        if target in labels:
            addr = labels[target]
            if 0 <= addr and addr + 4 <= len(rom):
                return rom[addr:addr + 4].hex().upper(), "full"
        return None, None
    if m == "mov.w" and a and len(a) == 4:
        return a, "partial"
    if m == "mov" and a and len(a) <= 2:
        v = int(a, 16)
        return ("%08X" % (v if v < 0x80 else (0xFFFFFF00 | v))), "full"
    return None, None


def resolve_back(pc, reg, pcs, by_pc, label_pcs, rom, labels):
    i = bisect.bisect_left(pcs, pc) - 1
    while i >= 0:
        rec = by_pc[pcs[i]]
        if writes_reg(rec, reg):
            val, conf = source_value(rec, rom, labels)
            if val:
                return val, conf, None, rec["pc"]
            return None, None, "unprovable_source", rec["pc"]
        if rec["pc"] in label_pcs or rec["mnem"].lower() in BRANCH:
            return None, None, "control_flow_boundary", None
        i -= 1
    return None, None, "no_source_in_extent", None


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
    """Evaluate a signed displacement expression such as
    ``(word_82DC - h'821E)`` or ``(dword_821C+2 - h'821E)``.

    Every atom must be a known listing label, a decimal, ``h'..`` or ``0x..``.
    An unknown atom makes the whole expression unresolved (never zero).
    """
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


def access_of(mnem, ops):
    m, o = mnem.lower(), ops.strip()
    mem_first = o.startswith("@")
    mem_last = o.split(",")[-1].strip().startswith("@")
    if m.startswith(("and.", "or.", "xor.")) and mem_last:
        return "rmw"
    if m.startswith("mov"):
        return "read" if mem_first else "write"
    if m.startswith("tst"):
        return "read"
    if mem_first:
        return "read"
    if mem_last:
        return "write"
    return "read"


def fmt(v):
    return "?" if v is None else ("%08X" % (v & 0xFFFFFFFF)).lower()


def main():
    global ROM_PATH, LST_PATH, OUT_MAIN, OUT_UNRES
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rom", default=os.path.join(here, "VERSA f501.bin"))
    ap.add_argument("--listing", required=True)
    ap.add_argument("--out", default=os.path.join(here, "WO65117_effective_address_dictionary.tsv"))
    ap.add_argument("--unresolved", default=os.path.join(here, "WO65117_effective_address_dictionary_unresolved.tsv"))
    args = ap.parse_args()
    ROM_PATH, LST_PATH, OUT_MAIN, OUT_UNRES = args.rom, args.listing, args.out, args.unresolved

    rom = open(ROM_PATH, "rb").read()
    rom_md5, rom_sha = hashlib.md5(rom).hexdigest(), hashlib.sha256(rom).hexdigest()
    lst = open(LST_PATH, "rb").read()
    lst_sha = hashlib.sha256(lst).hexdigest()
    labels, label_kind, code = parse_listing()
    code.sort(key=lambda r: r["pc"])
    pcs = [r["pc"] for r in code]
    by_pc = {r["pc"]: r for r in code}
    label_pcs = set(labels.values())

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
        if rets:
            end_pc = rets[-1]["pc"] + len(rets[-1]["bytes"]) + 2
        else:
            end_pc = nxt
        ext = [r for r in cand if r["pc"] < end_pc]
        gbrs = []
        for r in ext:
            o = r["ops"].lower()
            m = re.match(r"^\s*r(\d+)\s*,\s*gbr\s*$", o)
            if r["mnem"].lower() == "ldc" and m:
                val, conf, _, _ = resolve_back(r["pc"], "r" + m.group(1), pcs, by_pc, label_pcs, rom, labels)
                if val and conf == "full":
                    gbrs.append(int(val, 16))
        distinct = sorted(set(gbrs))
        gbr = distinct[0] if len(distinct) == 1 else None
        funcs.append({"start": start, "end": end_pc, "label": label, "gbr": gbr,
                      "gbr_count": len(distinct)})
    func_starts = [f["start"] for f in funcs]

    rows, unres = [], []
    seen = set()

    def add_unres(base, pc, reason, instr, note):
        key = (fmt(base), "%08X" % pc, reason, clean(instr), clean(note))
        if key not in seen:
            seen.add(key)
            unres.append(list(key))

    for rec in code:
        if not rec["concordant"]:
            add_unres(None, rec["pc"], "pc_concordance_mismatch", rec["instr"], "row dropped")
            continue
        fi = bisect.bisect_right(func_starts, rec["pc"]) - 1
        fn = funcs[fi] if fi >= 0 else {"label": "unknown", "gbr": None, "gbr_count": 0}
        wm = WIDTH_RE.search(rec["mnem"])
        width = wm.group(1).lower() if wm else "l"
        scale = SCALE[width]
        acc = access_of(rec["mnem"], rec["ops"])
        for dm in MEM_OPERAND_RE.finditer(rec["ops"]):
            disp_txt, reg = dm.group(1).strip(), dm.group(2).lower()
            is_gbr = reg == "gbr"
            base = fn["gbr"] if is_gbr else None
            base_reason = "gbr_not_provable" if is_gbr else "base_not_provable"
            if not is_gbr:
                val, conf, _, _ = resolve_back(rec["pc"], reg, pcs, by_pc, label_pcs, rom, labels)
                if val and conf == "full":
                    base = int(val, 16)
            disp = parse_disp(disp_txt, labels)
            if disp == "r0":
                r0val, conf, _, _ = resolve_back(rec["pc"], "r0", pcs, by_pc, label_pcs, rom, labels)
                if not (r0val and conf == "full"):
                    add_unres(base, rec["pc"], "index_not_provable", rec["instr"],
                              "base=%s function=%s" % (fmt(base), fn["label"]))
                    continue
                idx = int(r0val, 16)
                offset, form = idx, ("gbr_r0" if is_gbr else "base_r0")
                note = "r0 from provable source"
            else:
                if disp is None:
                    add_unres(base, rec["pc"], "displacement_not_provable", rec["instr"],
                              "base=%s function=%s disp=%s" % (fmt(base), fn["label"], disp_txt))
                    continue
                offset, form = disp * scale, ("gbr_disp" if is_gbr else "base_disp")
                note = "disp*%d" % scale if disp else "disp=0"
            if base is None:
                add_unres(None, rec["pc"], base_reason, rec["instr"],
                          "function=%s gbr_distinct=%d" % (fn["label"], fn.get("gbr_count", 0)))
                continue
            ea = (base + offset) & 0xFFFFFFFF
            key = (fmt(base), fmt(offset), fmt(ea), width, acc, form,
                   "%08X" % rec["pc"], fn["label"], rec["instr"], note)
            if key not in seen:
                seen.add(key)
                rows.append(list(key))

    rows.sort(key=lambda r: (r[0], r[2], r[6]))
    unres.sort(key=lambda r: (r[0], r[1]))

    def write(path, header, cols, data):
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            for line in header:
                f.write("# " + line + "\n")
            f.write("\t".join(cols) + "\n")
            for row in data:
                f.write("\t".join(str(x) for x in row) + "\n")

    common = [
        "WO65117 aggregate effective-address dictionary",
        "generator_version: " + VERSION,
        "rom_path: EVIDENCE/VERSA f501.bin",
        "rom_md5: " + rom_md5,
        "rom_sha256: " + rom_sha,
        "listing_member: " + MEMBER,
        "listing_sha256: " + lst_sha,
        "listing_bytes: " + str(len(lst)),
        "run_date: " + datetime.date.today().isoformat(),
        "target_file_sha256: N/A (aggregate structural map; no supplied target addresses)",
        "pc_concordance_rows_checked: " + str(checked),
        "pc_concordance_rows_matched: " + str(matched),
        "method_limits: computed pointers, pointer tables, block-copy and movca.l transport are not modelled; inherited GBR and unprovable bases are reported as unresolved, never as address zero or as absence",
        "classification: no reader/writer claim per supplied target; rows are structural effective-address facts only",
    ]
    write(OUT_MAIN, common,
          ["base_value", "offset", "effective_address", "width", "access", "form", "pc", "function", "instruction", "note"], rows)
    write(OUT_UNRES, common,
          ["base_value", "pc", "reason", "instruction", "note"], unres)

    print("VERSION", VERSION)
    print("PC_CONCORDANCE", matched, "/", checked)
    print("FUNCTIONS", len(funcs), "FULL_GBR_FUNCTIONS", sum(1 for f in funcs if f["gbr"] is not None))
    print("RESOLVED_ROWS", len(rows), "UNRESOLVED_ROWS", len(unres))
    print("FORMS", Counter(r[5] for r in rows).most_common())
    print("TOP_BASES", Counter(r[0] for r in rows).most_common(12))
    print("UNRES_REASONS", Counter(r[2] for r in unres).most_common())
    for fn in ("sub_403D8", "sub_3BA88", "calculate_state_dependent_correction_1992"):
        sample = [r for r in rows if r[7] == fn]
        print("ANCHOR", fn, "ROWS", len(sample), sample[:4])
    bad = [r for r in rows if r[0] == "0000821e" and r[2].startswith("ffff8")]
    print("ROM_GBR_FALSE_RAM_ATTRIBUTION", bad[:5], "COUNT", len(bad))
    # Acceptance check: complex ``label - h'821E`` expressions must evaluate
    # to the label address when GBR is the ROM value 0000821E.
    complex_rows = [r for r in rows if r[0] == "0000821e"
                    and re.search(r"-\s*h'821e", r[8], re.I)]
    print("COMPLEX_821E_ROWS", len(complex_rows))
    for r in complex_rows:
        print("  COMPLEX", r[6], "EA", r[2], r[8])
    print("COMPLEX_821E_UNRESOLVED", sum(
        1 for u in unres if u[0] == "0000821e" and u[2] == "displacement_not_provable"))


if __name__ == "__main__":
    main()
