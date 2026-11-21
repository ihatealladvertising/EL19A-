"""WO65119 false-alias and verified-facts register generator.

Python 3 standard library only. Publishes a curated register of known false
aliases / corrected facts drawn from closed work orders, and mechanically
re-verifies the tractable subset against the pinned ROM and listing.

No new alias search, no semantic naming, no tools/ entry. Curated rows that
cannot be mechanically re-derived are marked DOCUMENTED / NOT_RECHECKED.
"""
import argparse
import datetime
import hashlib
import os
import re

VERSION = "WO65119-FAREG-1.1.0"
MEMBER = "EL19A_Complete_Disassembly_ANNOTATED_V3_NEXT6_16_ALL_PENDING_ANNOTATIONS(1).lst"
ROM_PATH = LST_PATH = OUT_REG = OUT_CHK = None

CODE_RE = re.compile(r"^([0-9A-F]{8})\s+([0-9A-F]{2}(?:\s+[0-9A-F]{2})*)\s+CODE\s+(\S+)(?:\s+(.*))?$")
DATA_RE = re.compile(r"^([0-9A-F]{8})\s+([0-9A-F]{2}(?:\s+[0-9A-F]{2})*)\s+DATA\s+(.*)$")
LABEL_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_@]*):\s*$")
ADDR_RE = re.compile(r"^([0-9A-F]{8})\s")
GBR_RE = re.compile(r"@\(\s*([^,()]+)\s*,\s*gbr\s*\)", re.I)

# Curated from closed work orders. tier: ROM_BYTE | LISTING_PC | ARITHMETIC | DOCUMENTED.
# Only the listed mechanical checks are re-run; DOCUMENTED rows are carried verbatim.
CASES = [
    dict(id="FA001", category="stale_gbr",
         false_claim="PKIOR_W at FFFFF770 reached via a stale GBR in an INT_ATU routine",
         correct_fact="PKIOR_W is a RAM word at FFFFF770; no provable GBR access resolves to it",
         addresses="FFFFF770; 0x2869A/0x286A4/0x286E4/0x2870E/0x28738",
         tier="LISTING_PC", evidence="confirmed", source="WO65061, WO65062, playbook",
         negative="bounded stale-GBR/resolver search; exact-literal and GBR forms; false origin unrecovered",
         notes="Mechanical check covers label mapping and the five annotation forms (address loads, not accesses); stale-GBR non-derivation remains documented-only."),
    dict(id="FA002", category="pool_label",
         false_claim="byte_85DF in a .data.l pool refers to RAM FFFF85DF",
         correct_fact="the pool value is 0x000085DF, a ROM address; ROM[0x85DF]=01 6E FE 16",
         addresses="0x38084; ROM 0x85DF",
         tier="ROM_BYTE", evidence="confirmed", source="playbook, WO65061",
         negative="exact .data.l value search over the listing; ROM byte read at the label target",
         notes="A 32-bit pool value below 0x100000 is a ROM pointer, not a RAM address."),
    dict(id="FA003", category="over_reach",
         false_claim="a 0x55xxx displacement with GBR reaches RAM FFFF8AF0",
         correct_fact="no concordant @(disp,GBR) operand with the known GBR values yields FFFF8AF0",
         addresses="FFFF8AF0; GBR FFFF1028/FFFF1E54/0000821E",
         tier="ARITHMETIC", evidence="confirmed", source="playbook, index item 5, WO65116/WO65117",
         negative="scan every concordant @(disp,GBR) operand against each known GBR; width scaling b/w/l applied",
         notes="FFFF8AF0 exists only as an undefined .res.b reservation in the listing."),
    dict(id="FA004", category="false_base",
         false_claim="0x96A4A with offset 0x5F4 targets FFFF1648",
         correct_fact="base FFFF2150 + 0x5F4 = FFFF2744 (a different word)",
         addresses="0x96A4A; FFFF2150+0x5F4",
         tier="ARITHMETIC", evidence="confirmed", source="WO65101",
         negative="exact-base arithmetic and fixed-offset restriction; no FFFF1648 derivation",
         notes="Listing line at 0x96A4A carries the h'5F4 annotation."),
    dict(id="FA005", category="pointer_table",
         false_claim="FFFF8234 is an HCAN mailbox payload destination",
         correct_fact="FFFF8234 is a four-byte pointer table staged by sub_2BD74",
         addresses="FFFF8234; 0x4D74; 0x2CA1E",
         tier="DOCUMENTED", evidence="confirmed", source="WO65102, WO65108",
         negative="mailbox config/ID/DLC census; pointer-assembly and dereference chain; no MB payload role found",
         notes="Not re-derived here; use the source WO's reader/producer evidence."),
    dict(id="FA006", category="stale_annotation",
         false_claim="@(h'14,r2) at 0x41196 and @(h'14,r5) at 0x41204 read FFFF1014",
         correct_fact="r2/r5 = FFFF1000, word displacement 0x14 scaled x2 -> FFFF1028",
         addresses="0x41196; 0x41204; FFFF1000+0x28",
         tier="LISTING_PC", evidence="confirmed", source="WO65097, WO65012 errata",
         negative="proven base plus SH-2 word-displacement scaling; listing B5/B6 correction comments",
         notes="The V32 Batch-6 comments at both PCs repeat the withdrawn FFFF1014 claim."),
    dict(id="FA007", category="role_correction",
         false_claim="FFFF33E6/FFFF33E8 and FFFF3368 are MMIO registers",
         correct_fact="they are RAM staging in the timer/APC output loop",
         addresses="FFFF33E6; FFFF33E8; FFFF3368",
         tier="DOCUMENTED", evidence="confirmed", source="WO65106 (corrects WO65074/WO65087)",
         negative="peripheral write census and port-mux search; no hardware register write proven",
         notes="Not re-derived here."),
    dict(id="FA008", category="data_class",
         false_claim="FFFF8518-FFFF851B is an analog input stage",
         correct_fact="it is one four-byte RAM vector-table slot initialized at FFFF8500",
         addresses="FFFF8518-FFFF851B; FFFF8500",
         tier="DOCUMENTED", evidence="confirmed", source="WO65105",
         negative="startup vector-table initialization trace; ADC2 callsite census (only 0x1B/0x1F)",
         notes="Not re-derived here."),
    dict(id="FA009", category="role_correction",
         false_claim="sub_25D36 is a flag helper",
         correct_fact="sub_25D36 is a divide-by-10 helper",
         addresses="sub_25D36",
         tier="DOCUMENTED", evidence="confirmed", source="playbook",
         negative="helper body decode; division sequence identified",
         notes="Not re-derived here."),
    dict(id="FA010", category="width_mismatch",
         false_claim="a label named byte_* implies a byte-width access",
         correct_fact="the cited register was accessed as a word; width comes from the mnemonic, not the label",
         addresses="listing labels",
         tier="DOCUMENTED", evidence="confirmed", source="playbook",
         negative="mnemonic-width audit against label names",
         notes="Not re-derived here."),
    dict(id="FA011", category="role_correction",
         false_claim="INT_TRAPA62 is a periodic scheduler tick",
         correct_fact="it is a bit0-gated software trap with event-gated dispatch",
         addresses="INT_TRAPA62",
         tier="DOCUMENTED", evidence="confirmed", source="WO65104, WO65094",
         negative="gate-bit trace and cadence search; no fixed period proven",
         notes="Not re-derived here."),
    dict(id="FA012", category="data_class",
         false_claim="the 197-record DTC code table is read in the R14=1 DTC path",
         correct_fact="the 198-pointer dword_13780 scan does not read the 197-record DTC table",
         addresses="dword_13780; 197-record DTC table",
         tier="DOCUMENTED", evidence="bounded", source="WO65107",
         negative="pointer-array census and record-table reader search; no ordinal pairing assumed",
         notes="Not re-derived here."),
    dict(id="FA013", category="data_class",
         false_claim="0xE904 is a catalogue gap absent from XML v3",
         correct_fact="0xE904 is already declared in XML v3 (Barometric Pressure Correction [S] mTHOSNTP)",
         addresses="0xE904",
         tier="DOCUMENTED", evidence="confirmed", source="WO65110",
         negative="XML v3 declaration search and byte comparison",
         notes="Not re-derived here; no XML edit made by this WO."),
    dict(id="FA014", category="role_correction",
         false_claim="FFFF85E4 is ICR0A/TCNT0",
         correct_fact="FFFF85E4 consumes RAM FFFF14E0; no proven bridge to ICR0A capture",
         addresses="FFFF85E4; FFFF14E0; FFFF1A64",
         tier="DOCUMENTED", evidence="bounded", source="WO65104",
         negative="timer-register write/read census; observed ICR0A handler writes FFFF1A64",
         notes="Not re-derived here."),
]


def parse_listing():
    lines = open(LST_PATH, "rb").read().decode("utf-8", "replace").splitlines()
    code, data = {}, {}
    label_next = {}
    pending = []
    for idx, ln in enumerate(lines, 1):
        m = LABEL_RE.match(ln)
        if m:
            pending.append(m.group(1))
            continue
        m = CODE_RE.match(ln)
        if m:
            pc = int(m.group(1), 16)
            rec = dict(pc=pc, line=idx, bytes=bytes.fromhex(m.group(2)),
                       mnem=m.group(3), ops=m.group(4) or "", text=ln)
            code[pc] = rec
            for name in pending:
                label_next[name] = ("CODE", pc, idx)
            pending = []
            continue
        m = DATA_RE.match(ln)
        if m:
            pc = int(m.group(1), 16)
            data[pc] = dict(pc=pc, line=idx, bytes=bytes.fromhex(m.group(2)), text=ln)
            for name in pending:
                label_next[name] = ("DATA", pc, idx)
            pending = []
            continue
        m = ADDR_RE.match(ln)
        if m:
            for name in pending:
                label_next[name] = ("ADDR", int(m.group(1), 16), idx)
            pending = []
    return lines, code, data, label_next


def clean(text):
    return re.sub(r"\s+", " ", text.replace("\t", " ")).replace("|", "/").strip()


def run_checks(rom, lines, code, data, label_next):
    """Return check rows: (alias_id, check, expected, observed, pass)."""
    out = []

    def add(aid, name, expected, observed, ok):
        out.append((aid, name, str(expected), str(observed), "PASS" if ok else "FAIL"))

    # --- FA001: PKIOR_W label -> FFFFF770; annotations are address loads, not GBR accesses.
    aid = "FA001"
    loc = label_next.get("PKIOR_W")
    observed = "%s@%08X" % (loc[0], loc[1]) if loc else "MISSING"
    add(aid, "PKIOR_W label maps to FFFFF770", "ADDR@FFFFF770", observed,
        bool(loc and loc[0] == "ADDR" and loc[1] == 0xFFFFF770))
    pk_lines = [r for r in code.values() if "PKIOR_W" in r["text"].upper()]
    forms = set(r["mnem"].lower() for r in pk_lines)
    bad = [r for r in pk_lines if "gbr" in r["text"].lower() and "mov.w" not in r["mnem"].lower()]
    add(aid, "PKIOR_W annotations are mov.w address loads, not GBR accesses",
        "5 mov.w loads; 0 gbr accesses",
        "%d loads; forms=%s; gbr_accesses=%d" % (len(pk_lines), sorted(forms), len(bad)),
        len(pk_lines) == 5 and forms == {"mov.w"} and not bad)

    # --- FA002: .data.l byte_85DF == 0x000085DF; ROM bytes at 0x85DF.
    aid = "FA002"
    hits = [(pc, r) for pc, r in data.items() if "byte_85DF" in r["text"]]
    val = hits[0][1]["bytes"].hex().upper() if hits else "MISSING"
    add(aid, ".data.l byte_85DF value", "000085DF", val, val == "000085DF")
    rom85df = rom[0x85DF:0x85E3].hex().upper()
    add(aid, "ROM bytes at 0x85DF", "016EFE16", rom85df, rom85df == "016EFE16")

    # --- FA003: no concordant @(disp,GBR) operand yields FFFF8AF0 for known GBRs.
    aid = "FA003"
    gbrs = [0xFFFF1028, 0xFFFF1E54, 0x0000821E]
    hits = []
    for r in code.values():
        if not (0 <= r["pc"] < r["pc"] + len(r["bytes"]) <= len(rom)):
            continue
        if rom[r["pc"]:r["pc"] + len(r["bytes"])] != r["bytes"]:
            continue
        m = re.search(r"\.(b|w|l)\b", r["mnem"], re.I)
        scale = {"b": 1, "w": 2, "l": 4}.get(m.group(1).lower(), 4) if m else 4
        for dm in GBR_RE.finditer(r["ops"]):
            tok = dm.group(1).strip()
            num = re.match(r"^h'([0-9A-Fa-f]+)$", tok, re.I)
            if not num:
                continue
            disp = int(num.group(1), 16) * scale
            for g in gbrs:
                if (g + disp) & 0xFFFFFFFF == 0xFFFF8AF0:
                    hits.append("%08X:%08X+%X" % (r["pc"], g, disp))
    add(aid, "no GBR+disp resolves to FFFF8AF0", "0 hits", "%d hits" % len(hits), not hits)
    code_ann = [r for r in code.values() if "FFFF8AF0" in r["text"].upper()]
    add(aid, "FFFF8AF0 appears only as data reservation", "0 code annotations",
        "%d code annotations" % len(code_ann), not code_ann)

    # --- FA004: 0x96A4A carries h'5F4; FFFF2150+0x5F4 == FFFF2744 != FFFF1648.
    aid = "FA004"
    r = code.get(0x96A4A)
    ok = bool(r and "H'5F4" in r["ops"].upper() and r["mnem"].lower() == "mov.w")
    add(aid, "0x96A4A annotation h'5F4", "mov.w with h'5F4",
        r["text"].strip() if r else "MISSING", ok)
    ea = (0xFFFF2150 + 0x5F4) & 0xFFFFFFFF
    add(aid, "FFFF2150+0x5F4", "FFFF2744", "%08X" % ea, ea == 0xFFFF2744)

    # --- FA006: 0x41196/0x41204 word displacement 0x14 scaled x2 -> FFFF1028.
    aid = "FA006"
    for pc, reg in ((0x41196, "r2"), (0x41204, "r5")):
        r = code.get(pc)
        ok = bool(r and "@(h'14,%s)" % reg in r["ops"].lower() and r["mnem"].lower() == "mov.w")
        add(aid, "0x%X instruction @(h'14,%s)" % (pc, reg), "mov.w @(h'14,%s)" % reg,
            r["text"].strip() if r else "MISSING", ok)
        ea = (0xFFFF1000 + 0x14 * 2) & 0xFFFFFFFF
        add(aid, "base FFFF1000 + 0x14 x2", "FFFF1028", "%08X" % ea, ea == 0xFFFF1028)
    comment_ok = any("FFFF1028, not FFFF1014" in ln for ln in lines)
    add(aid, "listing carries B5/B6 correction comment", "present",
        "present" if comment_ok else "absent", comment_ok)

    return out


def main():
    global ROM_PATH, LST_PATH, OUT_REG, OUT_CHK
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rom", default=os.path.join(here, "VERSA f501.bin"))
    ap.add_argument("--listing", required=True)
    ap.add_argument("--register", default=os.path.join(here, "WO65119_false_alias_register.tsv"))
    ap.add_argument("--checks", default=os.path.join(here, "WO65119_false_alias_checks.tsv"))
    args = ap.parse_args()
    ROM_PATH, LST_PATH, OUT_REG, OUT_CHK = args.rom, args.listing, args.register, args.checks

    rom = open(ROM_PATH, "rb").read()
    rom_md5, rom_sha = hashlib.md5(rom).hexdigest(), hashlib.sha256(rom).hexdigest()
    lst_bytes = open(LST_PATH, "rb").read()
    lst_sha = hashlib.sha256(lst_bytes).hexdigest()
    lines, code, data, label_next = parse_listing()

    checked = matched = 0
    for r in code.values():
        end = r["pc"] + len(r["bytes"])
        ok = 0 <= r["pc"] < end <= len(rom) and rom[r["pc"]:end] == r["bytes"]
        checked += 1
        matched += int(ok)

    checks = run_checks(rom, lines, code, data, label_next)
    fail_ids = set(c[0] for c in checks if c[4] == "FAIL")

    by_id = {}
    for c in checks:
        by_id.setdefault(c[0], []).append(c)

    reg_rows = []
    for case in CASES:
        cs = by_id.get(case["id"], [])
        if cs:
            status = "FAIL" if any(c[4] == "FAIL" for c in cs) else "PASS"
        else:
            status = "NOT_RECHECKED"
        reg_rows.append([
            case["id"], case["category"], clean(case["false_claim"]), clean(case["correct_fact"]),
            clean(case["addresses"]), case["tier"], status, clean(case["negative"]),
            case["evidence"], clean(case["source"]), clean(case["notes"]),
        ])

    common = [
        "WO65119 false-alias and verified-facts register",
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
        "target_file_sha256: N/A (curated register; no supplied targets)",
        "method_limits: curated from closed work orders; DOCUMENTED rows are not re-derived here; mechanical checks cover only the stated tiers; no new alias search or semantic naming",
        "classification: structural and negative-claim facts only; PASS on a mechanical check does not promote a DOCUMENTED conclusion",
    ]

    def write(path, header, cols, rows):
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            for line in header:
                f.write("# " + line + "\n")
            f.write("\t".join(cols) + "\n")
            for row in rows:
                f.write("\t".join(str(x) for x in row) + "\n")

    write(OUT_REG, common,
          ["alias_id", "category", "false_claim", "correct_fact", "addresses_pcs",
           "verification_tier", "verification_status", "negative_search_method",
           "evidence_level", "source_wo", "notes"], reg_rows)
    write(OUT_CHK, common,
          ["alias_id", "check", "expected", "observed", "pass"], checks)

    print("VERSION", VERSION)
    print("PC_CONCORDANCE", matched, "/", checked)
    print("REGISTER_ROWS", len(reg_rows), "CHECKS", len(checks))
    print("STATUS", {s: sum(1 for r in reg_rows if r[6] == s)
                     for s in ("PASS", "FAIL", "NOT_RECHECKED")})
    print("FAILED_IDS", sorted(fail_ids))
    anchors = ("FA001", "FA002", "FA003", "FA004")
    print("HARD_ANCHORS", {a: ("FAIL" if a in fail_ids else "PASS") for a in anchors})
    print("HARD_ANCHORS_PASS", not (fail_ids & set(anchors)))


if __name__ == "__main__":
    main()
