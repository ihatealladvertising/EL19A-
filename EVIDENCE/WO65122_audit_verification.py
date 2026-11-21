"""WO65122 — independent reproduction audit of four branch-only indexes.

Stdlib only. For WO65116, WO65117, WO65119 and WO65120 this script reads the
generator and every committed TSV from canonical Git blobs on the respective
branch, executes the unmodified generator against the pinned ROM/listing,
compares all regenerated TSVs byte-for-byte, and re-derives the published
counts, distributions, anchors and gates from the regenerated rows.

Usage:
    python EVIDENCE/WO65122_audit_verification.py --listing <pinned .lst>

Log: EVIDENCE/WO65122_audit_log.txt. No source or artifact is modified.
"""
import argparse
import collections
import hashlib
import os
import re
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

COMMON = {
    "rom_md5": "46991697c502052752a2cabcb84c9e27",
    "rom_sha256": "bfe037e8e6c389e2a90214047058eb6dc3bcaaaac5b5931bf98a3f5d9f64fd6a",
    "rom_bytes": 1048576,
    "listing_sha256": "148385bbec91f6a491dcaa403962836f709c2f273df9a17ec51f1dea5f7f4549",
    "listing_bytes": 27045080,
    "pc_checked": 306688,
    "pc_matched": 306688,
    "header_comment_lines": 14,
    "header_total_lines": 15,
}

# name -> (branch ref, generator relative path, generator blob, version, artifacts)
# artifact tuple: (key, relative path, blob oid, output CLI flag)
PACKAGES = {
    "WO65116": {
        "ref": "origin/wo65116-function-gbr-map",
        "gen": ("EVIDENCE/WO65116_function_gbr_map_generator.py",
                "ef6ea07f97fe6ed0115940d5b8dbcc8b16977016"),
        "version": "WO65116-GBRMAP-1.3.0",
        "artifacts": [
            ("main", "EVIDENCE/WO65116_function_gbr_map.tsv",
             "907a27e201884b7df7477aeacc1beb604e8cdcf3", "--out"),
            ("unresolved", "EVIDENCE/WO65116_function_gbr_map_unresolved.tsv",
             "ca553fe9fda70643f7e5eabfda88b61980981aa8", "--unresolved"),
        ],
        "rows": {"main": 1877, "unresolved": 615},
    },
    "WO65117": {
        "ref": "origin/wo65117-ea-dictionary",
        "gen": ("EVIDENCE/WO65117_effective_address_dictionary_generator.py",
                "09ebede0b2f8871c467a41a2ed9747288af74dff"),
        "version": "WO65117-EADICT-1.2.0",
        "artifacts": [
            ("main", "EVIDENCE/WO65117_effective_address_dictionary.tsv",
             "8e6045463ab6cb976d184fee3efbbe62b2217093", "--out"),
            ("unresolved", "EVIDENCE/WO65117_effective_address_dictionary_unresolved.tsv",
             "6e8a565468845c4f135b2a7e7a41fdb7f0acf051", "--unresolved"),
        ],
        "rows": {"main": 7731, "unresolved": 45105},
    },
    "WO65119": {
        "ref": "origin/wo65119-false-alias-register",
        "gen": ("EVIDENCE/WO65119_false_alias_register_generator.py",
                "302a2ec083173574cb3934564e174d8aad710858"),
        "version": "WO65119-FAREG-1.1.0",
        "artifacts": [
            ("register", "EVIDENCE/WO65119_false_alias_register.tsv",
             "fe8c727affbd6400aa2349a45f04eea0e9b88336", "--register"),
            ("checks", "EVIDENCE/WO65119_false_alias_checks.tsv",
             "b9372c9505f71251fd22c70a9ece074e07d23e4b", "--checks"),
        ],
        "rows": {"register": 14, "checks": 13},
    },
    "WO65120": {
        "ref": "origin/wo65120-callgraph-scheduler",
        "gen": ("EVIDENCE/WO65120_call_graph_generator.py",
                "4ac92933268c843a0c4b84701463568d3542bc3f"),
        "version": "WO65120-CALLGRAPH-1.1.0",
        "artifacts": [
            ("edges", "EVIDENCE/WO65120_call_graph.tsv",
             "9753731619af9c5b7c14fdb23b1b898f4a89186e", "--edges"),
            ("summary", "EVIDENCE/WO65120_function_call_summary.tsv",
             "1bd318b15fa540ed5b629723c7f4618517db302f", "--summary"),
            ("tables", "EVIDENCE/WO65120_dispatch_tables.tsv",
             "d04e206ba998d4671924c43b2f475607737fa92c", "--tables"),
            ("isr", "EVIDENCE/WO65120_isr_dispatch_map.tsv",
             "c98819a2bdf434224706affa479493c723d83b0d", "--isr"),
            ("unresolved", "EVIDENCE/WO65120_call_graph_unresolved.tsv",
             "7e42529410fa8026b9e9440e7073369148af7060", "--unresolved"),
        ],
        "rows": {"edges": 6118, "summary": 1862, "tables": 17,
                 "isr": 342, "unresolved": 233},
    },
}

LINES = []
RESULTS = []


class _Sink:
    def append(self, item):
        pass


def emit(text=""):
    LINES.append(text)
    print(text)


def check(label, ok, detail=""):
    RESULTS.append((label, bool(ok)))
    emit("%s %s%s" % ("PASS" if ok else "FAIL", label, (" | " + detail) if detail else ""))
    return bool(ok)


def git(*args):
    return subprocess.check_output(["git", *args], cwd=REPO)


def blob_bytes(ref, path):
    tree = git("ls-tree", ref, "--", path).decode().strip()
    if not tree:
        raise RuntimeError("missing %s on %s" % (path, ref))
    oid = tree.split()[2]
    return oid, git("cat-file", "blob", oid)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def parse_tsv(data):
    lines = data.decode("utf-8").split("\n")
    headers = [ln for ln in lines if ln.startswith("# ")]
    body = [ln for ln in lines if ln and not ln.startswith("#")]
    cols = body[0].split("\t")
    rows = [dict(zip(cols, ln.split("\t"))) for ln in body[1:] if ln]
    return headers, cols, rows


def header_value(headers, key):
    prefix = "# " + key + ": "
    for h in headers:
        if h.startswith(prefix):
            return h[len(prefix):]
    return None


def common_header_checks(label, headers):
    check("header_comment_lines_%s" % label,
          len(headers) == COMMON["header_comment_lines"], str(len(headers)))
    check("header_total_lines_%s" % label,
          len(headers) + 1 == COMMON["header_total_lines"])
    check("header_rom_md5_%s" % label, header_value(headers, "rom_md5") == COMMON["rom_md5"])
    check("header_rom_sha256_%s" % label, header_value(headers, "rom_sha256") == COMMON["rom_sha256"])
    check("header_listing_sha256_%s" % label,
          header_value(headers, "listing_sha256") == COMMON["listing_sha256"])
    check("header_listing_bytes_%s" % label,
          header_value(headers, "listing_bytes") == str(COMMON["listing_bytes"]))
    check("header_pc_checked_%s" % label,
          int(header_value(headers, "pc_concordance_rows_checked")) == COMMON["pc_checked"])
    check("header_pc_matched_%s" % label,
          int(header_value(headers, "pc_concordance_rows_matched")) == COMMON["pc_matched"])
    check("header_target_na_%s" % label,
          header_value(headers, "target_file_sha256").startswith("N/A"))


def audit_65116(parsed, results):
    rows = parsed["main"][2]
    unres = parsed["unresolved"][2]
    states = collections.Counter(r["gbr_state"] for r in rows)
    emit("GBR_STATES " + repr(dict(sorted(states.items()))))
    check("65116_gbr_state_distribution", dict(states) == {
        "established_full": 667, "established_partial": 341, "none": 815,
        "multiple_values": 50, "restored_only": 3, "inherited_only": 1})
    uses_sum = sum(int(r["gbr_uses"]) for r in rows)
    check("65116_gbr_uses_sum", uses_sum == 8158, "artifact_sum=%d" % uses_sum)
    emit("ERRATUM_WO65116_SECTION_4_1: record states 8,155 GBR operand uses; "
         "sum of gbr_uses in the committed map is 8,158 (3 outside-extent uses are "
         "separate unresolved rows). Artifact reproduces byte-identically; prose "
         "correction belongs to the WO65116 owner/coordinator.")
    check("65116_functions_with_uses", sum(1 for r in rows if int(r["gbr_uses"]) > 0) == 694)
    by_start = {r["start_pc"]: r for r in rows}
    for pc, value, src in (("000403D8", "FFFF1028", "000403EA"),
                           ("0003BA88", "FFFF1E54", "0003BA9A"),
                           ("00046E3E", "0000821E", "00046E50")):
        r = by_start.get(pc)
        check("65116_anchor_%s" % pc,
              bool(r) and r["gbr_value"].lower() == value.lower()
              and r["gbr_source_pc"] == src,
              repr((r["gbr_value"], r["gbr_source_pc"]) if r else None))
    reasons = collections.Counter(r["reason"] for r in unres)
    emit("UNRES_REASONS_65116 " + repr(dict(sorted(reasons.items()))))
    check("65116_unresolved_reasons", dict(reasons) == {
        "ldc_value_not_provable": 382, "multiple_distinct_gbr_values": 141,
        "no_return_site": 87, "gbr_use_outside_function_extent": 3,
        "gbr_use_without_local_establishment": 2})
    check("65116_pkior_not_code_start", not any(r["label"] == "PKIOR_W" for r in rows))
    check("65116_no_pkior_gbr_value", not any(r["gbr_value"] == "FFFFF770" for r in rows))


def audit_65117(parsed, results):
    rows = parsed["main"][2]
    unres = parsed["unresolved"][2]
    forms = collections.Counter(r["form"] for r in rows)
    widths = collections.Counter(r["width"] for r in rows)
    accesses = collections.Counter(r["access"] for r in rows)
    emit("FORMS_65117 " + repr(dict(sorted(forms.items()))))
    emit("WIDTHS_65117 " + repr(dict(sorted(widths.items()))))
    emit("ACCESS_65117 " + repr(dict(sorted(accesses.items()))))
    check("65117_form_distribution", dict(forms) == {
        "gbr_disp": 5162, "base_disp": 2567, "gbr_r0": 2})
    check("65117_width_distribution", dict(widths) == {"b": 5804, "w": 1450, "l": 477})
    check("65117_access_distribution", dict(accesses) == {"read": 5189, "write": 2542})
    check("65117_distinct_bases", len(set(r["base_value"] for r in rows)) == 410)
    check("65117_distinct_effective_addresses",
          len(set(r["effective_address"] for r in rows)) == 2087)
    check("65117_distinct_pcs", len(set(r["pc"] for r in rows)) == 7731)
    arith_bad = [r for r in rows
                 if (int(r["base_value"], 16) + int(r["offset"], 16)) & 0xFFFFFFFF
                 != int(r["effective_address"], 16)]
    check("65117_arithmetic_all_rows", not arith_bad, "violations=%d" % len(arith_bad))
    over = [r for r in rows if r["base_value"] == "0000821E"
            and r["effective_address"].startswith("FFFF8")]
    check("65117_no_rom_gbr_overreach", not over, "rows=%d" % len(over))
    check("65117_ffff85c4_coverage_gap_reproduced",
          not any(r["base_value"] == "FFFF85C4" for r in rows))
    reasons = collections.Counter(r["reason"] for r in unres)
    emit("UNRES_REASONS_65117 " + repr(dict(sorted(reasons.items()))))
    check("65117_unresolved_reasons", dict(reasons) == {
        "index_not_provable": 24727, "base_not_provable": 9878,
        "gbr_not_provable": 6811, "displacement_not_provable": 3689})


def audit_65119(parsed, results):
    reg = parsed["register"][2]
    checks = parsed["checks"][2]
    ids = [r["alias_id"] for r in reg]
    check("65119_register_sorted", ids == sorted(ids))
    check("65119_no_blank_status", all(r["verification_status"] for r in reg))
    statuses = collections.Counter(r["verification_status"] for r in reg)
    tiers = collections.Counter(r["verification_tier"] for r in reg)
    emit("STATUS_65119 " + repr(dict(sorted(statuses.items()))))
    emit("TIERS_65119 " + repr(dict(sorted(tiers.items()))))
    check("65119_status_distribution",
          statuses.get("PASS", 0) == 5 and statuses.get("FAIL", 0) == 0
          and statuses.get("NOT_RECHECKED", 0) == 9)
    check("65119_tier_distribution", dict(tiers) == {
        "ROM_BYTE": 1, "LISTING_PC": 2, "ARITHMETIC": 2, "DOCUMENTED": 9})
    check("65119_checks_all_pass",
          all(r["pass"] == "PASS" for r in checks) and len(checks) == 13)
    check("65119_no_fail_status", not any(r["verification_status"] == "FAIL" for r in reg))
    fa001 = next((r for r in reg if r["alias_id"] == "FA001"), None)
    check("65119_fa001_contract",
          bool(fa001) and "FFFFF770" in fa001["addresses_pcs"]
          and fa001["verification_tier"] == "LISTING_PC")


def audit_65120(parsed, results):
    edges = parsed["edges"][2]
    summary = parsed["summary"][2]
    tables = parsed["tables"][2]
    isr = parsed["isr"][2]
    unres = parsed["unresolved"][2]
    forms = collections.Counter(r["form"] for r in edges)
    emit("FORMS_65120 " + repr(dict(sorted(forms.items()))))
    check("65120_form_distribution", dict(forms) == {
        "jsr_reg_ann": 4133, "bsr_direct": 1985})
    check("65120_no_duplicate_edges",
          len({(r["caller"], r["call_pc"], r["callee_pc"]) for r in edges}) == len(edges))
    check("65120_distinct_callers", len(set(r["caller"] for r in edges)) == 1024)
    check("65120_distinct_callees", len(set(r["callee"] for r in edges)) == 1838)
    check("65120_summary_rows", len(summary) == 1862)

    by_table = collections.defaultdict(list)
    for r in tables:
        by_table[r["table"]].append(r)
    a64 = sorted(by_table["dword_21A64"], key=lambda r: int(r["index"]))
    aec = sorted(by_table["dword_216EC"], key=lambda r: int(r["index"]))
    check("65120_R1_table_21A64_9_slots", len(a64) == 9)
    check("65120_R2_table_216EC_8_slots", len(aec) == 8)
    check("65120_tables_rom_and_code",
          all(r["in_rom"] == "yes" and r["code_start"] == "yes" for r in tables))
    order = ["00034464", "0004D02C", "0003C45E", "00059CAE", "00047276",
             "0005F81E", "000500EC", "000951E0", "000C29A2"]
    check("65120_R4_nine_entry_order", [r["target_pc"] for r in a64] == order)
    check("65120_R5_no_ram_dispatch_target",
          not any(r["target_pc"].startswith("FFFF") for r in tables))

    called = [r["isr_label"] for r in isr if r["calls_dispatcher"] == "yes"]
    emit("ISR_DISPATCH_CALLERS " + repr(sorted(set(called))))
    check("65120_R3_known_isr_callers",
          set(called) == {"INT_ATU02_ICI0A", "INT_ATU12_IMI1AE"}, repr(sorted(set(called))))
    check("65120_isr_vector_rows", len(isr) == 342)
    check("65120_no_pkior_call_edge",
          not any(r["callee_pc"] == "FFFFF770" or "FFFFF770" in r["callee"] for r in edges))

    reasons = collections.Counter(r["reason"] for r in unres)
    emit("UNRES_REASONS_65120 " + repr(dict(sorted(reasons.items()))))
    check("65120_unresolved_reasons", dict(reasons) == {
        "jsr_target_not_provable": 229, "bsr_target_not_code_label": 3,
        "annotation_not_code_label": 1})


PACKAGE_AUDITS = {
    "WO65116": audit_65116,
    "WO65117": audit_65117,
    "WO65119": audit_65119,
    "WO65120": audit_65120,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--listing", required=True)
    ap.add_argument("--rom", default=os.path.join(REPO, "EVIDENCE", "VERSA f501.bin"))
    args = ap.parse_args()
    results = _Sink()

    emit("WO65122 independent reproduction audit (four packages)")
    emit("")

    emit("=== 1. Pinned inputs (shared) ===")
    rom = open(args.rom, "rb").read()
    lst = open(args.listing, "rb").read()
    check("rom_bytes", len(rom) == COMMON["rom_bytes"], str(len(rom)))
    check("rom_md5", hashlib.md5(rom).hexdigest() == COMMON["rom_md5"])
    check("rom_sha256", sha256(rom) == COMMON["rom_sha256"])
    check("listing_bytes", len(lst) == COMMON["listing_bytes"], str(len(lst)))
    check("listing_sha256", sha256(lst) == COMMON["listing_sha256"])
    emit("")

    with tempfile.TemporaryDirectory(prefix="wo65122_audit_") as td:
        for pkg, cfg in PACKAGES.items():
            emit("=" * 70)
            emit("=== PACKAGE %s  ref=%s ===" % (pkg, cfg["ref"]))
            gen_path, gen_oid = cfg["gen"]
            committed = {}
            oid, data = blob_bytes(cfg["ref"], gen_path)
            committed["generator"] = data
            emit("BLOB generator oid=%s sha256=%s" % (oid, sha256(data)))
            check("%s_generator_blob" % pkg, oid == gen_oid)

            for key, path, exp_oid, flag in cfg["artifacts"]:
                oid, data = blob_bytes(cfg["ref"], path)
                committed[key] = data
                emit("BLOB %-10s oid=%s sha256=%s" % (key, oid, sha256(data)))
                check("%s_blob_%s" % (pkg, key), oid == exp_oid)

            emit("--- generator execution ---")
            script = os.path.join(td, pkg + "_generator.py")
            with open(script, "wb") as f:
                f.write(committed["generator"])
            out_paths = {}
            cmd = [sys.executable, script, "--rom", args.rom, "--listing", args.listing]
            for key, path, exp_oid, flag in cfg["artifacts"]:
                out_paths[key] = os.path.join(td, pkg + "_" + key + ".tsv")
                cmd += [flag, out_paths[key]]
            proc = subprocess.run(cmd, capture_output=True, text=True)
            check("%s_generator_exit" % pkg, proc.returncode == 0, "rc=%d" % proc.returncode)
            for ln in proc.stdout.splitlines():
                emit("  " + ln)
            if proc.stderr.strip():
                emit("  STDERR: " + proc.stderr.strip().replace("\n", " | "))

            emit("--- byte-for-byte comparison ---")
            for key in out_paths:
                regen = open(out_paths[key], "rb").read()
                emit("COMPARE %s %-10s bytes=%d sha256=%s" %
                     (pkg, key, len(regen), sha256(regen)))
                check("%s_byte_identical_%s" % (pkg, key), regen == committed[key])

            emit("--- row-level invariant audit ---")
            parsed = {}
            for key in out_paths:
                headers, cols, rows = parse_tsv(open(out_paths[key], "rb").read())
                parsed[key] = (headers, cols, rows)
                common_header_checks("%s_%s" % (pkg, key), headers)
                check("%s_header_version_%s" % (pkg, key),
                      header_value(headers, "generator_version") == cfg["version"])
                check("%s_row_count_%s" % (pkg, key),
                      len(rows) == cfg["rows"][key],
                      "expected=%d actual=%d" % (cfg["rows"][key], len(rows)))
                emit("ROWS %s %-10s %d" % (pkg, key, len(rows)))

            PACKAGE_AUDITS[pkg](parsed, results)
            emit("")

        emit("=" * 70)
        emit("=== 2. Independent PC/ROM concordance re-derivation (shared) ===")
        code_line = re.compile(r"^([0-9A-F]{8})\s+([0-9A-F]{2}(?:\s+[0-9A-F]{2})*)\s+CODE\s+(\S+)")
        checked = matched = 0
        mismatches = []
        for line in lst.decode("utf-8", "replace").splitlines():
            m = code_line.match(line)
            if not m:
                continue
            pc = int(m.group(1), 16)
            bs = bytes.fromhex(m.group(2))
            checked += 1
            if pc + len(bs) <= len(rom) and rom[pc:pc + len(bs)] == bs:
                matched += 1
            else:
                mismatches.append("%08X" % pc)
        emit("INDEPENDENT_PC_CONCORDANCE checked=%d matched=%d mismatches=%d" %
             (checked, matched, len(mismatches)))
        check("independent_pc_concordance_checked", checked == COMMON["pc_checked"])
        check("independent_pc_concordance_matched", matched == COMMON["pc_matched"])
        check("independent_pc_concordance_exact", matched == checked and not mismatches)

    emit("")
    emit("=== SUMMARY ===")
    failures = [label for label, ok in RESULTS if not ok]
    per_pkg = {}
    for pkg in PACKAGES:
        bad = [l for l, ok in RESULTS if l.startswith(pkg + "_") and not ok]
        per_pkg[pkg] = "REPRODUCED_AND_VERIFIED" if not bad else "DISCREPANCY_FOUND:" + repr(bad)
        emit("PACKAGE %s %s" % (pkg, per_pkg[pkg]))
    emit("checks_total=%d checks_passed=%d checks_failed=%d" %
         (len(RESULTS), len(RESULTS) - len(failures), len(failures)))
    if failures:
        emit("FAILED_CHECK_IDS " + repr(failures))
    emit("AUDIT_DISPOSITION " + ("ALL_REPRODUCED_AND_VERIFIED" if not failures else "DISCREPANCY_FOUND"))

    log_path = os.path.join(REPO, "EVIDENCE", "WO65122_audit_log.txt")
    with open(log_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(LINES) + "\n")
    print("log written:", log_path)
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
