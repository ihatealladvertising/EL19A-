#!/usr/bin/env python3
"""Export one hash-pinned production per-call static-flow document for EL19A 0x0F10E.

This orchestrates existing read-only components:
  - reader_trace_listing_source.extract_verified_member
  - build_static_indices.parse_listing
  - build_static_indices.full_rom_analysis
  - reader_trace_static_flow_adapter.build_static_flow_call_document

It does not implement or decode SH-2 instructions.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import pathlib
import tempfile
from typing import Any, Dict, List

import build_static_indices
from reader_trace_listing_source import (
    DEFAULT_ARCHIVE,
    DEFAULT_MEMBER,
    EXPECTED_ARCHIVE_SHA256,
    EXPECTED_MEMBER_SHA256,
    extract_verified_member,
)
from reader_trace_static_flow_adapter import (
    build_static_flow_call_document,
    static_flow_document_sha256,
    write_static_flow_call_document,
)

EXPECTED_ROM_MD5 = "46991697c502052752a2cabcb84c9e27"
EXPECTED_ROM_SHA256 = "bfe037e8e6c389e2a90214047058eb6dc3bcaaaac5b5931bf98a3f5d9f64fd6a"
EXPECTED_CATALOG_GIT_BLOB = "e8ee9f257e4cd114624cfc26dd08caecccdd59f7"

TARGET_EA = 0x0F10E
REQUIRED_CALL_PC = 0x85B2E
REQUIRED_HELPER = "sub_22E10"
REQUIRED_QUERY_ORIGIN = "r5<-FFFF84B8"
REQUIRED_CALL_BYTES = bytes.fromhex("42 0B")


class ProductionExportError(RuntimeError):
    """The pinned production per-call export failed an acceptance assertion."""


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _hash_file(path: pathlib.Path, algorithm: str) -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_blob_sha1(payload: bytes) -> str:
    header = f"blob {len(payload)}\\0".encode("ascii")
    return hashlib.sha1(header + payload).hexdigest()


def _target_catalogue_rows(catalogue_path: pathlib.Path) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    with catalogue_path.open("r", newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            address = str(row.get("address", "")).strip()
            if not address:
                continue
            try:
                value = int(address, 16)
            except ValueError:
                continue
            if value == TARGET_EA:
                rows.append(row)
    if not rows:
        raise ProductionExportError(f"catalogue contains no address row for 0x{TARGET_EA:X}")
    return rows


def _write_json(path: pathlib.Path, document: Dict[str, Any]) -> str:
    payload = json.dumps(document, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8", newline="\n")
    return _sha256_bytes(payload.encode("utf-8"))


def run_export(
    *,
    rom_path: pathlib.Path,
    archive_path: pathlib.Path,
    catalogue_path: pathlib.Path,
    output_dir: pathlib.Path,
) -> Dict[str, Any]:
    if not rom_path.is_file():
        raise ProductionExportError(f"ROM file not found: {rom_path}")
    if not catalogue_path.is_file():
        raise ProductionExportError(f"catalogue file not found: {catalogue_path}")

    rom_md5 = _hash_file(rom_path, "md5")
    rom_sha256 = _hash_file(rom_path, "sha256")
    if rom_md5.lower() != EXPECTED_ROM_MD5:
        raise ProductionExportError(f"ROM MD5 mismatch: {rom_md5}")
    if rom_sha256.lower() != EXPECTED_ROM_SHA256:
        raise ProductionExportError(f"ROM SHA-256 mismatch: {rom_sha256}")

    catalogue_bytes = catalogue_path.read_bytes()
    catalogue_sha256 = _sha256_bytes(catalogue_bytes)
    catalogue_blob_sha1 = _git_blob_sha1(catalogue_bytes)
    if catalogue_blob_sha1.lower() != EXPECTED_CATALOG_GIT_BLOB.lower():
        raise ProductionExportError(
            f"catalogue Git blob SHA-1 mismatch: expected {EXPECTED_CATALOG_GIT_BLOB}, got {catalogue_blob_sha1}"
        )
    with rom_path.open("rb") as stream:
        rom = stream.read()

    listing_bytes, listing_source = extract_verified_member(
        archive_path,
        member_name=DEFAULT_MEMBER,
        expected_archive_sha256=EXPECTED_ARCHIVE_SHA256,
        expected_member_sha256=EXPECTED_MEMBER_SHA256,
    )

    with tempfile.TemporaryDirectory(prefix="reader-trace-0f10e-") as temp_dir:
        listing_path = pathlib.Path(temp_dir) / "stage16.lst"
        listing_path.write_bytes(listing_bytes)

        # Reuse the existing parser's byte-concordance check for all parsed CODE records.
        code_lines = build_static_indices.parse_listing(str(listing_path), rom)
        call_rows = [
            (pc, hb, instr, comment, func, label)
            for pc, hb, instr, comment, func, label in code_lines
            if pc == REQUIRED_CALL_PC
        ]
        if len(call_rows) != 1:
            raise ProductionExportError(
                f"expected exactly one Stage-16 CODE record at 0x{REQUIRED_CALL_PC:X}; found {len(call_rows)}"
            )
        call_pc, call_bytes, assembly, comment, function, label = call_rows[0]
        if call_bytes != REQUIRED_CALL_BYTES or assembly.strip() != "jsr @r2":
            raise ProductionExportError(
                f"call-site instruction mismatch at 0x{call_pc:X}: {call_bytes.hex()} {assembly!r}"
            )

        catalogue_rows = _target_catalogue_rows(catalogue_path)
        _, _, _, cat_calls = build_static_indices.full_rom_analysis(
            code_lines, rom, catalogue_rows, set()
        )
        target_calls = cat_calls.get(TARGET_EA, [])
        if not target_calls:
            raise ProductionExportError(f"static tracker found no per-call rows for 0x{TARGET_EA:X}")

        selected = [
            row for row in target_calls
            if row.get("reader_pc") == REQUIRED_CALL_PC
        ]
        if len(selected) != 1:
            raise ProductionExportError(
                f"expected exactly one tracker row for target 0x{TARGET_EA:X} at "
                f"0x{REQUIRED_CALL_PC:X}; found {len(selected)}"
            )
        call_record = selected[0]
        if call_record.get("helper") != REQUIRED_HELPER:
            raise ProductionExportError(
                f"helper mismatch at 0x{REQUIRED_CALL_PC:X}: {call_record.get('helper')!r}"
            )
        q_inputs = call_record.get("q_inputs", [])
        if REQUIRED_QUERY_ORIGIN not in q_inputs:
            raise ProductionExportError(
                f"required query origin {REQUIRED_QUERY_ORIGIN!r} missing; observed {q_inputs!r}"
            )

        document = build_static_flow_call_document(
            {TARGET_EA: target_calls},
            artifact_sha256=rom_sha256,
            source_listing_sha256=listing_source["member_sha256"],
            source_listing_path=(
                f"{listing_source['archive_path']}#{listing_source['member_name']}"
            ),
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "EL19A_F501_0F10E_static_flow_calls.json"
    manifest_path = output_dir / "EL19A_F501_0F10E_static_flow_manifest.json"
    document_sha256 = write_static_flow_call_document(json_path, document)
    if document_sha256 != static_flow_document_sha256(document):
        raise ProductionExportError("written per-call document SHA-256 does not match canonical document hash")

    manifest: Dict[str, Any] = {
        "schema": "reader-trace-static-flow-production-manifest-v0.1",
        "status": "PASS",
        "target_ea": f"0x{TARGET_EA:08X}",
        "required_call_pc": f"0x{REQUIRED_CALL_PC:X}",
        "required_helper": REQUIRED_HELPER,
        "required_query_origin": REQUIRED_QUERY_ORIGIN,
        "rom": {
            "path": rom_path.as_posix(),
            "bytes": len(rom),
            "md5": rom_md5,
            "sha256": rom_sha256,
        },
        "listing": listing_source,
        "catalogue": {
            "path": catalogue_path.as_posix(),
            "bytes": catalogue_path.stat().st_size,
            "git_blob_sha1_expected": catalogue_blob_sha1,
            "sha256": catalogue_sha256,
            "target_rows_used": len(catalogue_rows),
        },
        "static_tracker": {
            "module": "tools/build_static_indices.py",
            "functions": ["parse_listing", "full_rom_analysis"],
            "parsed_code_line_count": len(code_lines),
            "target_per_call_row_count": len(target_calls),
            "matching_call_count": len(selected),
            "selected_call": {
                "reader_pc": f"0x{call_pc:X}",
                "instruction_bytes": call_bytes.hex(" ").upper(),
                "assembly": assembly,
                "function": function,
                "label": label,
                "helper": call_record.get("helper"),
                "q_inputs": q_inputs,
                "dests": [
                    {
                        "ram_ea": f"0x{int(dest[0]):08X}",
                        "width": dest[1],
                        "write_pc": f"0x{int(dest[2]):X}",
                        "instruction": dest[3],
                        "is_tainted": bool(dest[4]),
                    }
                    for dest in call_record.get("dests", [])
                ],
            },
        },
        "output": {
            "per_call_json_path": json_path.as_posix(),
            "per_call_json_bytes": json_path.stat().st_size,
            "per_call_json_sha256": document_sha256,
            "manifest_path": manifest_path.as_posix(),
        },
        "analysis_boundary": {
            "instruction_decoder_implemented_here": False,
            "existing_static_tracker_reused": True,
            "independent_redecode_claimed": False,
            "query_transform_and_consumer_semantics_promoted": False,
        },
    }
    # The manifest intentionally contains the per-call JSON hash but not its
    # own hash, avoiding a recursive/self-referential digest.
    manifest_sha256 = _write_json(manifest_path, manifest)
    return {
        "manifest": manifest,
        "per_call_json_path": json_path,
        "manifest_path": manifest_path,
        "per_call_json_sha256": document_sha256,
        "manifest_file_sha256": manifest_sha256,
        "target_per_call_row_count": len(target_calls),
        "selected_call": manifest["static_tracker"]["selected_call"],
    }


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=pathlib.Path, default=pathlib.Path("EVIDENCE/VERSA f501.bin"))
    parser.add_argument(
        "--listing-archive",
        type=pathlib.Path,
        default=DEFAULT_ARCHIVE,
    )
    parser.add_argument(
        "--catalogue",
        type=pathlib.Path,
        default=pathlib.Path("CALIBRATIONS/discovered_tables_catalog.csv"),
    )
    parser.add_argument(
        "--output-dir",
        type=pathlib.Path,
        default=pathlib.Path("EVIDENCE/READER_TRACE_V0_1"),
    )
    args = parser.parse_args(argv)
    result = run_export(
        rom_path=args.rom,
        archive_path=args.listing_archive,
        catalogue_path=args.catalogue,
        output_dir=args.output_dir,
    )
    print(json.dumps({
        "status": "PASS",
        "target_ea": f"0x{TARGET_EA:08X}",
        "selected_call": result["selected_call"],
        "target_per_call_row_count": result["target_per_call_row_count"],
        "per_call_json_sha256": result["per_call_json_sha256"],
        "manifest_file_sha256": result["manifest_file_sha256"],
        "per_call_json_path": result["per_call_json_path"].as_posix(),
        "manifest_path": result["manifest_path"].as_posix(),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
