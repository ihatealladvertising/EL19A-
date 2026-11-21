"""WO65116 structural function/GBR evidence-map generator.

Python 3 standard library only. Produces the two committed TSV evidence files.
The 27 MB listing is read from an extract path outside version control.
"""
import argparse
import bisect
import datetime
import hashlib
import os
import re

VERSION = "WO65116-GBRMAP-1.3.0"
MEMBER = "EL19A_Complete_Disassembly_ANNOTATED_V3_NEXT6_16_ALL_PENDING_ANNOTATIONS(1).lst"
ROM_PATH = LST_PATH = OUT_MAIN = OUT_UNRES = None

LABEL_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_@]*):\s*$")
CODE_RE = re.compile(r"^([0-9A-F]{8})\s+([0-9A-F]{2}(?:\s+[0-9A-F]{2})*)\s+CODE\s+(\S+)(?:\s+(.*))?$")
DATA_RE = re.compile(r"^([0-9A-F]{8})\s+([0-9A-F]{2}(?:\s+[0-9A-F]{2})*)\s+DATA\b")
ANN_RE = re.compile(r";\s*h'([0-9A-Fa-f]{1,8})")
BRANCH = {"bt", "bf", "bt/s", "bf/s", "bra", "bra/s", "jmp", "jsr", "bsr", "rts", "rte", "trapa"}
GBR_OPERAND_RE = re.compile(r"@\([^)]*\bgbr\b[^)]*\)", re.I)


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
            comment = ops.split(";", 1)[1].strip() if ";" in ops else ""
            code.append({
                "pc": pc, "bytes": bs, "mnem": mnem, "ops": ops,
                "instr": clean(mnem + " " + ops), "ann": ann.group(1).upper() if ann else None,
                "comment": comment, "concordant": None,
            })
            continue
        if re.match(r"^[0-9A-F]{8}\s", ln):
            m2 = re.match(r"^([0-9A-F]{8})\s", ln)
            for name in pending:
                labels.setdefault(name, int(m2.group(1), 16))
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
        # Short pool annotations (e.g. h'821E) are resolved from the four
        # actual ROM bytes at the labelled pool address, never by guesswork.
        target = rec["ops"].split(";")[0].split(",")[0].strip()
        target = target.strip("@()").split(",")[0].strip()
        if target in labels:
            addr = labels[target]
            if 0 <= addr and addr + 4 <= len(rom):
                return rom[addr:addr + 4].hex().upper(), "full"
        return None, None
    if m == "mov.w" and a and len(a) == 4:
        return a, "partial"
    if m == "mov" and a and len(a) <= 2:
        return a, "partial"
    return None, None


def resolve_back(pc, reg, recs, pcs, by_pc, label_pcs, rom, labels):
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


def fmt(val):
    if val is None:
        return "?"
    return val.lower().zfill(8)


def main():
    global ROM_PATH, LST_PATH, OUT_MAIN, OUT_UNRES
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rom", default=os.path.join(here, "VERSA f501.bin"))
    ap.add_argument("--listing", required=True, help="extracted V3_NEXT6_16 .lst path (outside version control)")
    ap.add_argument("--out", default=os.path.join(here, "WO65116_function_gbr_map.tsv"))
    ap.add_argument("--unresolved", default=os.path.join(here, "WO65116_function_gbr_map_unresolved.tsv"))
    args = ap.parse_args()
    ROM_PATH, LST_PATH, OUT_MAIN, OUT_UNRES = args.rom, args.listing, args.out, args.unresolved

    rom = open(ROM_PATH, "rb").read()
    rom_md5, rom_sha = hashlib.md5(rom).hexdigest(), hashlib.sha256(rom).hexdigest()
    lst_bytes = open(LST_PATH, "rb").read()
    lst_sha = hashlib.sha256(lst_bytes).hexdigest()
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

    rows, unres = [], []

    def add_unres(label, pc, reason, instr, note):
        unres.append([label, ("%08X" % pc) if isinstance(pc, int) else pc, reason, clean(instr), clean(note)])

    covered_pcs = set()
    subs = sorted((pc, name) for name, pc in labels.items()
                  if label_kind.get(name) == "code" and not name.startswith(("loc_", "locret_")))
    for i, (start, label) in enumerate(subs):
        nxt = subs[i + 1][0] if i + 1 < len(subs) else max(pcs) + 4
        lo = bisect.bisect_left(pcs, start)
        hi = bisect.bisect_left(pcs, nxt)
        cand = code[lo:hi]
        rets = [r for r in cand if r["concordant"] and r["mnem"].lower() in ("rts", "rte")]
        if rets:
            last = rets[-1]
            # rts/rte execute their following delay slot; include it.
            end_pc = last["pc"] + len(last["bytes"]) + 2
            ret_pc = "%08X" % last["pc"]
        else:
            end_pc, ret_pc = nxt, ""
            add_unres(label, start, "no_return_site", "", "extent bounded by next code-start label")
        ext = [r for r in cand if r["pc"] < end_pc]
        covered_pcs.update(r["pc"] for r in ext)

        gbr_sets, restores, uses = [], [], []
        for r in ext:
            if not r["concordant"]:
                add_unres(label, r["pc"], "pc_concordance_mismatch", r["instr"], "row dropped from map")
                continue
            m, o = r["mnem"].lower(), r["ops"].lower()
            if GBR_OPERAND_RE.search(o):
                uses.append(r)
            if m == "ldc" and re.match(r"^\s*r(\d+)\s*,\s*gbr\s*$", o):
                reg = "r" + re.match(r"^\s*r(\d+)\s*,\s*gbr\s*$", o).group(1)
                val, conf, why, srcpc = resolve_back(r["pc"], reg, code, pcs, by_pc, label_pcs, rom, labels)
                gbr_sets.append({"pc": r["pc"], "instr": r["instr"], "val": val,
                                 "conf": conf, "why": why, "srcpc": srcpc, "reg": reg})
            elif m == "ldc.l" and "@r15+" in o and "gbr" in o:
                restores.append(r)

        distinct = sorted({g["val"] for g in gbr_sets if g["conf"] == "full"})
        full_sets = [g for g in gbr_sets if g["conf"] == "full"]
        partial_sets = [g for g in gbr_sets if g["conf"] == "partial"]
        if len(distinct) > 1:
            state, value, src, instr, note = "multiple_values", "?", "", "", "distinct=" + ",".join(fmt(v) for v in distinct)
            for g in gbr_sets:
                add_unres(label, g["pc"], "multiple_distinct_gbr_values", g["instr"], "value=" + fmt(g["val"]))
        elif full_sets:
            g = full_sets[0]
            state, value = "established_full", fmt(g["val"])
            src, instr = "%08X" % g["pc"], g["instr"]
            note = "source=%s via %s" % (g["reg"], ("%08X" % g["srcpc"]) if g["srcpc"] else "?")
            for extra in full_sets[1:] + partial_sets:
                add_unres(label, extra["pc"], "ldc_value_not_provable" if extra["conf"] != "full" else "multiple_distinct_gbr_values",
                          extra["instr"], "value=" + fmt(extra["val"]))
        elif partial_sets:
            g = partial_sets[0]
            state, value, src, instr = "established_partial", "?", "%08X" % g["pc"], g["instr"]
            note = "16-bit/immediate source=" + fmt(g["val"]) + " reason=" + str(g["why"])
            for extra in partial_sets:
                add_unres(label, extra["pc"], "ldc_value_not_provable", extra["instr"], "reason=" + str(extra["why"]))
        elif gbr_sets:
            g = gbr_sets[0]
            state, value, src, instr = "established_partial", "?", "%08X" % g["pc"], g["instr"]
            note = "reason=" + str(g["why"])
            for extra in gbr_sets:
                add_unres(label, extra["pc"], "ldc_value_not_provable", extra["instr"], "reason=" + str(extra["why"]))
        elif restores:
            state, value, src, instr, note = "restored_only", "?", "", "", "caller GBR restored; no local ldc"
        else:
            state, value, src, instr, note = "none", "?", "", "", "no local GBR establishment"

        if uses and state in ("restored_only", "none"):
            state = "inherited_only" if not restores else "restored_only"
            add_unres(label, uses[0]["pc"], "gbr_use_without_local_establishment", uses[0]["instr"],
                      "%d GBR operand use(s) in extent" % len(uses))

        rows.append([label, "%08X" % start, "%08X" % end_pc, ret_pc, value, src, instr,
                     state, str(len(uses)), note])

    # GBR operands in code that no function extent covers are reported, not dropped.
    for rec in code:
        if rec["concordant"] and GBR_OPERAND_RE.search(rec["ops"].lower()) and rec["pc"] not in covered_pcs:
            add_unres("unknown", rec["pc"], "gbr_use_outside_function_extent", rec["instr"],
                      "post-return or unlabelled code; no enclosing code-start label")

    def write(path, header, cols, data):
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            for line in header:
                f.write("# " + line + "\n")
            f.write("\t".join(cols) + "\n")
            for row in data:
                f.write("\t".join(str(x) for x in row) + "\n")

    common = [
        "WO65116 verified function/GBR evidence map",
        "generator_version: " + VERSION,
        "rom_path: EVIDENCE/VERSA f501.bin",
        "rom_md5: " + rom_md5,
        "rom_sha256: " + rom_sha,
        "listing_member: " + MEMBER,
        "listing_sha256: " + lst_sha,
        "listing_bytes: " + str(len(lst_bytes)),
        "run_date: " + datetime.date.today().isoformat(),
        "target_file_sha256: N/A (structural map; no supplied target addresses)",
        "pc_concordance_rows_checked: " + str(checked),
        "pc_concordance_rows_matched: " + str(matched),
        "method_limits: computed pointers, pointer tables, block-copy and movca.l transport are not modelled; GBR is inherited across calls and is not attributed to a callee without a local ldc",
        "classification: gbr_value '?' / state partial|inherited|restored|multiple is a lead, not a confirmed base",
    ]
    write(OUT_MAIN, common,
          ["label", "start_pc", "end_pc", "ret_pc", "gbr_value", "gbr_source_pc", "gbr_instruction", "gbr_state", "gbr_uses", "note"], rows)
    write(OUT_UNRES, common,
          ["label", "pc", "reason", "instruction", "note"], unres)

    print("VERSION", VERSION)
    print("CODE_LINES_CONCORDANCE", matched, "/", checked)
    print("CODE_START_LABELS", len(rows))
    print("UNRESOLVED_ROWS", len(unres))
    from collections import Counter
    print("GBR_STATES", Counter(r[7] for r in rows).most_common())
    print("UNRES_REASONS", Counter(r[2] for r in unres).most_common())
    for anchor in ("sub_403D8", "sub_3BA88", "calculate_state_dependent_correction_1992"):
        print("ANCHOR", [r for r in rows if r[0] == anchor])
    # Negative control: PKIOR_W is a RAM data label; the stale-register alias must not
    # become an established GBR value in any function that references it.
    pkiors = [r for r in code if "PKIOR_W" in r["comment"].upper()]
    print("PKIOR_W_CODE_SITES", ["%08X" % r["pc"] for r in pkiors])
    for site in pkiors:
        containing = [r for r in rows if int(r[1], 16) <= site["pc"] < int(r[2], 16)]
        print("PKIOR_W_CONTROL", "%08X" % site["pc"],
              [(r[0], r[4], r[7], r[5]) for r in containing])
    bad = [r[0] for r in rows if r[7].startswith("established") and not r[5]]
    print("ESTABLISHED_WITHOUT_LOCAL_LDC", bad)
    bad2 = [r[0] for r in rows if r[7].startswith("established")
            and not (int(r[1], 16) <= int(r[5], 16) < int(r[2], 16))]
    print("ESTABLISHED_SOURCE_OUTSIDE_EXTENT", bad2)


if __name__ == "__main__":
    main()
