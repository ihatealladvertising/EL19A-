"""WO65121 — independent reproduction audit of the WO65118 RAM byte/bit cross-reference.

Stdlib only. Reads the WO65118 generator and its three committed TSVs directly
from canonical Git blobs on the audit ref, executes the unmodified generator
against the pinned ROM/listing, compares regenerated outputs byte-for-byte, and
re-derives the published counts, enumerations, page-index consistency and hard
gates R1-R5 from the regenerated rows instead of trusting generator stdout.

Usage:
    python EVIDENCE/WO65121_audit_verification.py --listing <path-to-pinned.lst>

No source or artifact is modified. Audit log is written to
EVIDENCE/WO65121_audit_log.txt next to this script.
"""
import argparse
import collections
import hashlib
import os
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIT_REF = "origin/wo65118-ram-byte-bit-xref"

ARTIFACTS = {
    "generator": "EVIDENCE/WO65118_ram_byte_bit_xref_generator.py",
    "main": "EVIDENCE/WO65118_ram_byte_bit_xref.tsv",
    "pages": "EVIDENCE/WO65118_ram_byte_bit_xref_page_index.tsv",
    "unresolved": "EVIDENCE/WO65118_ram_byte_bit_xref_unresolved.tsv",
}

EXPECTED = {
    "rom_md5": "46991697c502052752a2cabcb84c9e27",
    "rom_sha256": "bfe037e8e6c389e2a90214047058eb6dc3bcaaaac5b5931bf98a3f5d9f64fd6a",
    "rom_bytes": 1048576,
    "listing_sha256": "148385bbec91f6a491dcaa403962836f709c2f273df9a17ec51f1dea5f7f4549",
    "listing_bytes": 27045080,
    "generator_blob": "8668f0b0ff5234fdaeac678c252d86f6b0c27ced",
    "generator_version": "WO65118-RAMXREF-1.5.0",
    "main_blob": "2665ee62669ddcc141c1f659c0a1d4ac2cdaf423",
    "pages_blob": "ae4fc310b2ad260c15d8b19ac70eba5fa2c30d1d",
    "unresolved_blob": "9561c1abb75e213815a2efaab115e1ecf945930b",
    "header_comment_lines": 14,
    "header_total_lines": 15,
    "main_rows": 22308,
    "page_rows": 100,
    "unresolved_rows": 43530,
    "pc_checked": 306688,
    "pc_matched": 306688,
    "access_values": {"read", "write"},
    "width_values": {"b", "w", "l"},
    "bit_action_values": {"", "tested", "set", "cleared", "toggled"},
    "form_values": {"gbr_disp", "gbr_r0", "base_disp", "base_r0", "base_indirect"},
    "unresolved_reasons": {
        "base_not_provable": 20840,
        "index_not_provable": 16755,
        "displacement_not_provable": 3689,
        "gbr_not_provable": 2246,
    },
}

LINES = []
RESULTS = []


class _Sink:
    """Backward-compatible no-op sink; check() records into RESULTS."""

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
        raise RuntimeError("missing path %s on %s" % (path, ref))
    oid = tree.split()[2]
    return oid, git("cat-file", "blob", oid)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def md5(data):
    return hashlib.md5(data).hexdigest()


def parse_tsv(data):
    text = data.decode("utf-8")
    lines = text.split("\n")
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--listing", required=True)
    ap.add_argument("--rom", default=os.path.join(REPO, "EVIDENCE", "VERSA f501.bin"))
    args = ap.parse_args()

    results = _Sink()

    emit("WO65121 independent reproduction audit")
    emit("audit_ref: " + AUDIT_REF)
    emit("generator_version_expected: " + EXPECTED["generator_version"])
    emit("")

    emit("=== 1. Canonical Git blobs ===")
    committed = {}
    for name, path in ARTIFACTS.items():
        oid, data = blob_bytes(AUDIT_REF, path)
        committed[name] = data
        emit("BLOB %-10s oid=%s bytes=%d sha256=%s" % (name, oid, len(data), sha256(data)))
        results.append(check("blob_oid_%s" % name, oid == EXPECTED[name + "_blob"], oid))
    emit("")

    emit("=== 2. Pinned inputs ===")
    rom = open(args.rom, "rb").read()
    lst = open(args.listing, "rb").read()
    results.append(check("rom_bytes", len(rom) == EXPECTED["rom_bytes"], str(len(rom))))
    results.append(check("rom_md5", md5(rom) == EXPECTED["rom_md5"], md5(rom)))
    results.append(check("rom_sha256", sha256(rom) == EXPECTED["rom_sha256"], sha256(rom)))
    results.append(check("listing_bytes", len(lst) == EXPECTED["listing_bytes"], str(len(lst))))
    results.append(check("listing_sha256", sha256(lst) == EXPECTED["listing_sha256"], sha256(lst)))
    emit("")

    emit("=== 3. Generator execution (unmodified blob) ===")
    with tempfile.TemporaryDirectory(prefix="wo65121_audit_") as td:
        gen_path = os.path.join(td, "wo65118_generator.py")
        with open(gen_path, "wb") as f:
            f.write(committed["generator"])
        out_main = os.path.join(td, "main.tsv")
        out_pages = os.path.join(td, "pages.tsv")
        out_unres = os.path.join(td, "unresolved.tsv")
        cmd = [sys.executable, gen_path, "--rom", args.rom, "--listing", args.listing,
               "--out", out_main, "--pages", out_pages, "--unresolved", out_unres]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        results.append(check("generator_exit", proc.returncode == 0, "rc=%d" % proc.returncode))
        emit("--- generator stdout ---")
        for ln in proc.stdout.splitlines():
            emit(ln)
        if proc.stderr.strip():
            emit("--- generator stderr ---")
            for ln in proc.stderr.splitlines():
                emit(ln)
        emit("")

        emit("=== 4. Byte-for-byte artifact reproduction ===")
        regenerated = {}
        for name, out_path in (("main", out_main), ("pages", out_pages), ("unresolved", out_unres)):
            data = open(out_path, "rb").read()
            regenerated[name] = data
            identical = data == committed[name]
            emit("COMPARE %-10s regenerated_bytes=%d committed_bytes=%d sha256=%s" %
                 (name, len(data), len(committed[name]), sha256(data)))
            results.append(check("byte_identical_%s" % name, identical))
        emit("")

        emit("=== 5. Independent invariant audit (from regenerated rows) ===")
        parsed = {}
        for name in ("main", "pages", "unresolved"):
            parsed[name] = parse_tsv(regenerated[name])

        for name in ("main", "pages", "unresolved"):
            headers, cols, rows = parsed[name]
            check("header_comment_lines_%s" % name,
                  len(headers) == EXPECTED["header_comment_lines"], str(len(headers)))
            check("header_total_lines_%s" % name,
                  len(headers) + 1 == EXPECTED["header_total_lines"],
                  "%d comment + 1 column header" % len(headers))
            for key in ("generator_version", "rom_md5", "rom_sha256", "listing_sha256",
                        "listing_bytes", "run_date", "pc_concordance_rows_checked",
                        "pc_concordance_rows_matched", "target_file_sha256"):
                emit("HEADER %-10s %s = %s" % (name, key, header_value(headers, key)))

        hm = parsed["main"][0]
        results.append(check("header_generator_version",
                             header_value(hm, "generator_version") == EXPECTED["generator_version"]))
        results.append(check("header_rom_md5", header_value(hm, "rom_md5") == EXPECTED["rom_md5"]))
        results.append(check("header_rom_sha256", header_value(hm, "rom_sha256") == EXPECTED["rom_sha256"]))
        results.append(check("header_listing_sha256",
                             header_value(hm, "listing_sha256") == EXPECTED["listing_sha256"]))
        results.append(check("header_listing_bytes",
                             header_value(hm, "listing_bytes") == str(EXPECTED["listing_bytes"])))
        results.append(check("header_pc_checked",
                             int(header_value(hm, "pc_concordance_rows_checked")) == EXPECTED["pc_checked"]))
        results.append(check("header_pc_matched",
                             int(header_value(hm, "pc_concordance_rows_matched")) == EXPECTED["pc_matched"]))

        main_rows = parsed["main"][2]
        page_rows = parsed["pages"][2]
        unres_rows = parsed["unresolved"][2]

        results.append(check("main_row_count", len(main_rows) == EXPECTED["main_rows"], str(len(main_rows))))
        results.append(check("page_row_count", len(page_rows) == EXPECTED["page_rows"], str(len(page_rows))))
        results.append(check("unresolved_row_count", len(unres_rows) == EXPECTED["unresolved_rows"],
                             str(len(unres_rows))))

        bad_addr = [r["address"] for r in main_rows
                    if len(r["address"]) != 8 or int(r["address"], 16) < 0xFFFF0000
                    or r["address"] != r["address"].lower()]
        results.append(check("address_range_and_format", not bad_addr, "violations=%d" % len(bad_addr)))

        bad_pc = [r["pc"] for r in main_rows if len(r["pc"]) != 8 or int(r["pc"], 16) < 0]
        results.append(check("pc_format", not bad_pc, "violations=%d" % len(bad_pc)))

        for col, allowed in (("access", EXPECTED["access_values"]),
                             ("width", EXPECTED["width_values"]),
                             ("bit_action", EXPECTED["bit_action_values"]),
                             ("form", EXPECTED["form_values"])):
            seen = set(r[col] for r in main_rows)
            emit("ENUM %-11s %s" % (col, sorted(seen)))
            results.append(check("enum_%s" % col, seen <= allowed))

        tuple_rows = [tuple(r.values()) for r in main_rows]
        results.append(check("no_duplicate_rows", len(tuple_rows) == len(set(tuple_rows))))

        sorted_ok = all((main_rows[i]["page"], main_rows[i]["address"], main_rows[i]["pc"]) <=
                        (main_rows[i + 1]["page"], main_rows[i + 1]["address"], main_rows[i + 1]["pc"])
                        for i in range(len(main_rows) - 1))
        results.append(check("main_sorted_by_page_address_pc", sorted_ok))

        page_sum = sum(int(r["accesses"]) for r in page_rows)
        results.append(check("page_index_access_sum", page_sum == len(main_rows),
                             "sum=%d main_rows=%d" % (page_sum, len(main_rows))))
        page_keys = set(r["page"] for r in page_rows)
        main_pages = set(r["page"] for r in main_rows)
        results.append(check("page_index_page_set", page_keys == main_pages,
                             "pages_idx=%d pages_main=%d" % (len(page_keys), len(main_pages))))

        per_page_counts = collections.Counter(r["page"] for r in main_rows)
        mismatch = [p for p in page_keys if per_page_counts[p] != int(next(
            r["accesses"] for r in page_rows if r["page"] == p))]
        results.append(check("page_index_per_page_counts", not mismatch, "mismatches=%d" % len(mismatch)))

        reasons = collections.Counter(r["reason"] for r in unres_rows)
        emit("UNRESOLVED_REASONS " + repr(dict(sorted(reasons.items()))))
        results.append(check("unresolved_reason_distribution", dict(reasons) == EXPECTED["unresolved_reasons"]))

        emit("")

        emit("=== 6. Hard regression gates recomputed from rows ===")
        by_addr = collections.defaultdict(list)
        for r in main_rows:
            by_addr[r["address"]].append(r)

        r1_readers = sorted(r["pc"].lower() for r in by_addr["ffff85df"] if r["access"] == "read")
        results.append(check("R1_FFFF85DF_readers", r1_readers == ["00046bde", "00047014"],
                             repr(r1_readers)))
        results.append(check("R2_FFFF85E0_zero_rows", len(by_addr["ffff85e0"]) == 0,
                             str(len(by_addr["ffff85e0"]))))
        r3 = [(r["pc"].lower(), r["access"]) for r in by_addr["ffff1db4"]]
        results.append(check("R3_FFFF1DB4_reader_writer",
                             ("0004042c", "read") in r3 and ("0004044a", "write") in r3,
                             repr([x for x in r3 if x[0] in ("0004042c", "0004044a")])))
        results.append(check("R4_PKIORW_zero_rows", len(by_addr["fffff770"]) == 0,
                             str(len(by_addr["fffff770"]))))
        over = [r for r in main_rows if "base=0000821e" in r["note"] and r["address"].startswith("ffff8")]
        results.append(check("R5_no_rom_gbr_overreach", not over, "rows=%d" % len(over)))

        d860d = [r for r in by_addr["ffff860d"]
                 if ("bit_tested=h'08" in r["note"] or "bit_tested=h'20" in r["note"]
                     or r["bit_mask"] in ("00000008", "00000020"))]
        emit("CMP FFFF860D bit3/5 rows=%d distinct_pcs=%d all_address_rows=%d bit_noted=%d" %
             (len(d860d), len(set(r["pc"] for r in d860d)), len(by_addr["ffff860d"]),
              sum(1 for r in by_addr["ffff860d"] if "bit_" in r["note"])))
        d84ba = by_addr["ffff84ba"]
        emit("CMP FFFF84BA readers=%d writers=%d" %
             (sum(1 for r in d84ba if r["access"] == "read"),
              sum(1 for r in d84ba if r["access"] == "write")))

    emit("")
    emit("=== 7. Independent PC/ROM concordance re-derivation ===")
    # Separate implementation from the generator's parse_listing(): scan listing
    # CODE lines with an independent pattern and compare raw bytes to the ROM.
    import re
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
    if mismatches:
        emit("FIRST_MISMATCH_PCS " + repr(mismatches[:10]))
    check("independent_pc_concordance_checked", checked == EXPECTED["pc_checked"], str(checked))
    check("independent_pc_concordance_matched", matched == EXPECTED["pc_matched"], str(matched))
    check("independent_pc_concordance_exact", matched == checked and not mismatches)

    emit("")
    emit("=== SUMMARY ===")
    failures = [label for label, ok in RESULTS if not ok]
    emit("checks_total=%d checks_passed=%d checks_failed=%d" %
         (len(RESULTS), len(RESULTS) - len(failures), len(failures)))
    if failures:
        emit("FAILED_CHECK_IDS " + repr(failures))
    emit("AUDIT_DISPOSITION " + ("REPRODUCED_AND_VERIFIED" if not failures else "DISCREPANCY_FOUND"))

    log_path = os.path.join(REPO, "EVIDENCE", "WO65121_audit_log.txt")
    with open(log_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(LINES) + "\n")
    print("log written:", log_path)
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
