"""WO65120 call graph and ISR/dispatcher scheduler map generator.

Python 3 standard library only. Emits direct call edges, per-function call
summary, the two dispatcher task tables and the vector -> ISR -> dispatcher
map. No function extents or GBR values are republished (WO65116 owns them).

No tools/ entry, no semantic naming, no reader/writer resolution.
"""
import argparse
import bisect
import datetime
import hashlib
import os
import re
from collections import Counter, defaultdict

VERSION = "WO65120-CALLGRAPH-1.1.0"
MEMBER = "EL19A_Complete_Disassembly_ANNOTATED_V3_NEXT6_16_ALL_PENDING_ANNOTATIONS(1).lst"
ROM_PATH = LST_PATH = None
OUT_EDGES = OUT_SUMMARY = OUT_TABLES = OUT_ISR = OUT_UNRES = None

LABEL_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_@]*):\s*$")
CODE_RE = re.compile(r"^([0-9A-F]{8})\s+([0-9A-F]{2}(?:\s+[0-9A-F]{2})*)\s+CODE\s+(\S+)(?:\s+(.*))?$")
DATA_RE = re.compile(r"^([0-9A-F]{8})\s+([0-9A-F]{2}(?:\s+[0-9A-F]{2})*)\s+DATA\s+(.*)$")
ADDR_RE = re.compile(r"^([0-9A-F]{8})\s")
REG_RE = re.compile(r"^@\s*(r\d+)$", re.I)
ANN_RE = re.compile(r";\s*([A-Za-z_][A-Za-z0-9_@]*)\s*$")
POOL_ANN_RE = re.compile(r";\s*h'([0-9A-Fa-f]{8})\s*$")

TABLES = [
    ("dword_21A64", 0x21A64, 9, 0x20986, "r13", 9),
    ("dword_216EC", 0x216EC, 8, 0x20A12, "r14", 8),
]
DISPATCHER = "sub_2088C"
KNOWN_CALLERS = ("INT_ATU02_ICI0A", "INT_ATU12_IMI1AE")
EXPECTED_21A64 = ["00034464", "0004D02C", "0003C45E", "00059CAE", "00047276",
                  "0005F81E", "000500EC", "000951E0", "000C29A2"]


def clean(t):
    return "" if not t else re.sub(r"\s+", " ", t.replace("\t", " ")).replace("|", "/").strip()


def parse_listing():
    lines = open(LST_PATH, "rb").read().decode("utf-8", "replace").splitlines()
    labels, label_kind, code, data, pending = {}, {}, [], [], []
    for ln in lines:
        m = LABEL_RE.match(ln)
        if m:
            pending.append(m.group(1))
            continue
        m = CODE_RE.match(ln)
        if m:
            pc = int(m.group(1), 16)
            for name in pending:
                labels.setdefault(name, pc)
                label_kind[name] = "code"
            pending = []
            ops = m.group(4) or ""
            code.append(dict(pc=pc, bytes=bytes.fromhex(m.group(2)), mnem=m.group(3),
                             ops=ops, instr=clean(m.group(3) + " " + ops)))
            continue
        m = DATA_RE.match(ln)
        if m:
            pc = int(m.group(1), 16)
            for name in pending:
                labels.setdefault(name, pc)
                label_kind[name] = "data"
            pending = []
            data.append(dict(pc=pc, bytes=bytes.fromhex(m.group(2)), text=m.group(3)))
            continue
        m = ADDR_RE.match(ln)
        if m:
            for name in pending:
                labels.setdefault(name, int(m.group(1), 16))
                label_kind[name] = "addr"
            pending = []
    code.sort(key=lambda r: r["pc"])
    return code, data, labels, label_kind


def main():
    global ROM_PATH, LST_PATH, OUT_EDGES, OUT_SUMMARY, OUT_TABLES, OUT_ISR, OUT_UNRES
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rom", default=os.path.join(here, "VERSA f501.bin"))
    ap.add_argument("--listing", required=True)
    ap.add_argument("--edges", default=os.path.join(here, "WO65120_call_graph.tsv"))
    ap.add_argument("--summary", default=os.path.join(here, "WO65120_function_call_summary.tsv"))
    ap.add_argument("--tables", default=os.path.join(here, "WO65120_dispatch_tables.tsv"))
    ap.add_argument("--isr", default=os.path.join(here, "WO65120_isr_dispatch_map.tsv"))
    ap.add_argument("--unresolved", default=os.path.join(here, "WO65120_call_graph_unresolved.tsv"))
    args = ap.parse_args()
    ROM_PATH, LST_PATH = args.rom, args.listing
    OUT_EDGES, OUT_SUMMARY, OUT_TABLES, OUT_ISR, OUT_UNRES = (
        args.edges, args.summary, args.tables, args.isr, args.unresolved)

    rom = open(ROM_PATH, "rb").read()
    rom_md5, rom_sha = hashlib.md5(rom).hexdigest(), hashlib.sha256(rom).hexdigest()
    lst_bytes = open(LST_PATH, "rb").read()
    lst_sha = hashlib.sha256(lst_bytes).hexdigest()
    code, data, labels, label_kind = parse_listing()
    by_pc = {r["pc"]: r for r in code}
    pcs = [r["pc"] for r in code]
    label_pcs = set(labels.values())
    starts = sorted((pc, name) for name, pc in labels.items()
                    if label_kind[name] == "code" and not name.startswith(("loc_", "locret_")))
    func_starts = [s for s, _ in starts]
    start_name = {}
    for s, n in starts:
        start_name.setdefault(s, n)

    checked = matched = 0
    for r in code:
        end = r["pc"] + len(r["bytes"])
        r["ok"] = bool(0 <= r["pc"] < end <= len(rom) and rom[r["pc"]:end] == r["bytes"])
        checked += 1
        matched += int(r["ok"])

    def owner(pc):
        i = bisect.bisect_right(func_starts, pc) - 1
        return start_name.get(func_starts[i], "unknown") if i >= 0 else "unknown"

    edges, unres = [], []
    seen_edges = set()
    seen_unres = set()

    def add_unres(pc, reason, instr, note):
        key = ("%08X" % pc, reason, clean(instr), clean(note))
        if key not in seen_unres:
            seen_unres.add(key)
            unres.append(list(key))

    for r in code:
        if not r["ok"]:
            add_unres(r["pc"], "pc_concordance_mismatch", r["instr"], "row dropped")
            continue
        mnem, ops = r["mnem"].lower(), r["ops"]
        callee = callee_pc = ann = form = ""
        if mnem == "bsr":
            tok = ops.split(";")[0].strip()
            if tok in labels and label_kind[tok] == "code":
                callee, callee_pc, form = tok, labels[tok], "bsr_direct"
                ann = tok
            else:
                add_unres(r["pc"], "bsr_target_not_code_label", r["instr"], "target=" + tok)
                continue
        elif mnem == "jsr":
            am = ANN_RE.search(ops)
            rm = REG_RE.match(ops.split(";")[0].strip())
            if am:
                ann = am.group(1)
                if ann in labels and label_kind[ann] == "code":
                    callee, callee_pc, form = ann, labels[ann], "jsr_reg_ann"
                else:
                    add_unres(r["pc"], "annotation_not_code_label", r["instr"], "ann=" + ann)
                    continue
            elif rm:
                # Try a nearby full pool load into this register.
                reg = rm.group(1).lower()
                i = bisect.bisect_left(pcs, r["pc"]) - 1
                val = None
                while i >= 0:
                    p = by_pc[pcs[i]]
                    if p["mnem"].lower().startswith("mov"):
                        dest = [x.strip() for x in p["ops"].split(";")[0].split(",")][-1].lower()
                        if dest == reg:
                            pm = POOL_ANN_RE.search(p["ops"])
                            if pm:
                                val = int(pm.group(1), 16)
                            break
                    if r["pc"] - p["pc"] > 32:
                        break
                    i -= 1
                if val is not None and val in label_pcs:
                    callee_pc = val
                    callee = next((n for n, v in labels.items() if v == val), "")
                    form = "jsr_reg_ann"
                    ann = "%08X" % val
                else:
                    add_unres(r["pc"], "jsr_target_not_provable", r["instr"], "reg=" + reg)
                    continue
            else:
                add_unres(r["pc"], "jsr_form_unhandled", r["instr"], "")
                continue
        else:
            continue

        caller = owner(r["pc"])
        key = (caller, "%08X" % r["pc"], callee, "%08X" % callee_pc)
        if key in seen_edges:
            continue
        seen_edges.add(key)
        edges.append([caller, "%08X" % r["pc"], form, callee, "%08X" % callee_pc,
                      ann, r["instr"], "base=" + ("%08X" % callee_pc if callee_pc else "?")])

    edges.sort(key=lambda e: (e[0], e[1], e[3]))
    callees = defaultdict(set)
    callers = defaultdict(set)
    calls_out = Counter()
    calls_in = Counter()
    out_pc = defaultdict(list)
    for e in edges:
        callees[e[0]].add(e[3])
        callers[e[3]].add(e[0])
        calls_out[e[0]] += 1
        calls_in[e[3]] += 1
        out_pc[e[0]].append(e[1])
    summary = []
    for f in sorted(set(callees) | set(callers)):
        summary.append([f, "%08X" % labels.get(f, 0),
                        ",".join(sorted(x for x in callees[f] if x)),
                        ",".join(sorted(x for x in callers[f] if x)),
                        str(calls_out[f]), str(calls_in[f]),
                        min(out_pc[f]) if out_pc[f] else "", max(out_pc[f]) if out_pc[f] else ""])

    # Dispatch tables, read from ROM bytes.
    tables = []
    table_targets = {}
    for name, addr, slots, load_pc, ctr_reg, count in TABLES:
        targets = []
        for k in range(slots):
            v = int.from_bytes(rom[addr + 4 * k:addr + 4 * k + 4], "big")
            targets.append(v)
            in_rom = 0 <= v < len(rom)
            cs = bool(v in by_pc and by_pc[v]["ok"])
            lab = next((n for n, x in labels.items() if x == v), "")
            tables.append([name, "%08X" % addr, str(k), "%08X" % v, lab,
                           "yes" if in_rom else "no", "yes" if cs else "no",
                           "%08X" % load_pc,
                           "count_reg=%s=%d; code_pc_concordant (label may be absent)" % (ctr_reg, count)])
        table_targets[name] = targets

    # ISR vector map: .data.l entries in the vector region whose value is a code label.
    isr_rows = []
    dispatcher_callers = set()
    for d in data:
        if not (0x20000 <= d["pc"] < 0x21A64):
            continue
        if len(d["bytes"]) != 4:
            continue
        v = int.from_bytes(d["bytes"], "big")
        nm = ""
        m = re.search(r"\.data\.l\s+([A-Za-z_][A-Za-z0-9_@]*)", d["text"])
        if m:
            nm = m.group(1)
        if not nm or nm not in labels or label_kind[nm] != "code":
            continue
        if v != labels[nm]:
            continue
        calls = DISPATCHER in callees.get(nm, set())
        if calls:
            dispatcher_callers.add(nm)
        isr_rows.append(["%08X" % d["pc"], "%08X" % v, nm, "%08X" % labels[nm],
                         "yes" if calls else "no",
                         "vector entry -> ISR; call edge to %s from static graph" % DISPATCHER])
    isr_rows.sort(key=lambda r: r[0])

    # Add the dispatcher map rows explicitly.
    isr_rows.append(["N/A", "N/A", DISPATCHER, "%08X" % labels.get(DISPATCHER, 0), "N/A",
                     "callers=" + ",".join(sorted(dispatcher_callers))
                     + "; dispatch dword_21A64 order="
                     + ",".join("%08X" % x for x in table_targets["dword_21A64"])])

    common = [
        "WO65120 call graph and ISR/dispatcher scheduler map",
        "generator_version: " + VERSION,
        "rom_path: EVIDENCE/VERSA f501.bin",
        "rom_md5: " + rom_md5,
        "rom_sha256: " + rom_sha,
        "listing_member: " + MEMBER,
        "listing_sha256: " + lst_sha,
        "listing_bytes: " + str(len(lst_bytes)),
        "run_date: " + datetime.date.today().isoformat(),
        "pc_concordance_rows_checked: " + str(checked),
        "pc_concordance_rows_matched: " + str(matched),
        "target_file_sha256: N/A (static graph; no supplied targets)",
        "method_limits: static direct calls only; computed/indirect targets and runtime pointer tables not modelled; unresolved sites are listed, never treated as absence; function extents and GBR values are not republished (WO65116)",
        "classification: structural call facts only; no semantic, physical or unit naming",
    ]

    def write(path, cols, rows):
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            for line in common:
                f.write("# " + line + "\n")
            f.write("\t".join(cols) + "\n")
            for row in rows:
                f.write("\t".join(str(x) for x in row) + "\n")

    write(OUT_EDGES, ["caller", "call_pc", "form", "callee", "callee_pc", "ann",
                      "instruction", "note"], edges)
    write(OUT_SUMMARY, ["function", "start_pc", "callees", "callers", "calls_out",
                        "calls_in", "first_call_pc", "last_call_pc"], summary)
    write(OUT_TABLES, ["table", "table_addr", "index", "target_pc", "target_label",
                       "in_rom", "code_start", "source_pc", "note"], tables)
    write(OUT_ISR, ["vector_addr", "vector_value", "isr_label", "isr_pc",
                    "calls_dispatcher", "note"], isr_rows)
    write(OUT_UNRES, ["pc", "reason", "instruction", "note"], unres)

    print("VERSION", VERSION)
    print("PC_CONCORDANCE", matched, "/", checked)
    print("EDGES", len(edges), "SUMMARY_ROWS", len(summary),
          "TABLE_ROWS", len(tables), "ISR_ROWS", len(isr_rows), "UNRESOLVED", len(unres))
    print("FORMS", Counter(e[2] for e in edges).most_common())
    print("UNRES_REASONS", Counter(u[1] for u in unres).most_common())

    def concordant_pc(x):
        return 0 <= x < len(rom) and x in by_pc and by_pc[x]["ok"]

    t1 = table_targets["dword_21A64"]
    print("R1_21A64_SLOTS", len(t1), "ALL_CONCORDANT_CODE_PCS",
          all(concordant_pc(x) for x in t1))
    print("R1_PASS", len(t1) == 9 and all(concordant_pc(x) for x in t1))
    t2 = table_targets["dword_216EC"]
    print("R2_216EC_SLOTS", len(t2), "ALL_CONCORDANT_CODE_PCS",
          all(concordant_pc(x) for x in t2))
    print("R2_PASS", len(t2) == 8 and all(concordant_pc(x) for x in t2))
    print("R3_DISPATCHER_CALLERS", sorted(dispatcher_callers))
    print("R3_PASS", all(c in dispatcher_callers for c in KNOWN_CALLERS))
    print("R4_21A64_ORDER", ",".join("%08X" % x for x in t1))
    print("R4_PASS", ["%08X" % x for x in t1] == EXPECTED_21A64)
    pk = [e for e in edges if e[3] == "FFFFF770" or e[4] == "FFFFF770"]
    all_targets = t1 + t2
    ram_targets = [x for x in all_targets if x >= 0xFFFF0000]
    print("R5_PKIORW_CALLEE_EDGES", len(pk), "RAM_DISPATCH_TARGETS", len(ram_targets))
    print("R5_PASS", not pk and not ram_targets)
    print("CMP_DISTINCT_CALLERS", len({e[0] for e in edges}),
          "DISTINCT_CALLEES", len({e[3] for e in edges if e[3]}))


if __name__ == "__main__":
    main()
