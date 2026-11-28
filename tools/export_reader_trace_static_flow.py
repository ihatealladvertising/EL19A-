#!/usr/bin/env python3
"""Export hash-pinned production per-call static-flow documents for selected EL19A targets.

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
    merge_per_call_static_flow,
    static_flow_document_sha256,
    write_static_flow_call_document,
)
from reader_trace_graph import validate_trace_graph, write_trace_graph

EXPECTED_ROM_MD5 = "46991697c502052752a2cabcb84c9e27"
EXPECTED_ROM_SHA256 = "bfe037e8e6c389e2a90214047058eb6dc3bcaaaac5b5931bf98a3f5d9f64fd6a"
EXPECTED_CATALOG_GIT_BLOB = "e8ee9f257e4cd114624cfc26dd08caecccdd59f7"

DEFAULT_TARGET_EA = 0x0F10E
DEFAULT_REQUIRED_CALL_PC = 0x85B2E
DEFAULT_REQUIRED_HELPER = "sub_22E10"
DEFAULT_REQUIRED_QUERY_ORIGIN = "r5<-FFFF84B8"
DEFAULT_EXPECTED_CALL_BYTES = bytes.fromhex("42 0B")


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
    header = b"blob " + str(len(payload)).encode("ascii") + bytes([0])
    return hashlib.sha1(header + payload).hexdigest()


def _target_catalogue_rows(catalogue_path: pathlib.Path, target_ea: int) -> tuple[List[Dict[str, str]], bool]:
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
            if value == target_ea:
                rows.append(row)
    if rows:
        return rows, True

    # The golden graph/WO identifies this target, but the current broad
    # discovery catalogue does not contain it. Seed only the address required
    # by full_rom_analysis; do not fabricate geometry or semantic metadata.
    return [{"address": f"0x{target_ea:X}"}], False


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
    target_ea: int = DEFAULT_TARGET_EA,
    required_call_pc: int = DEFAULT_REQUIRED_CALL_PC,
    required_helper: str = DEFAULT_REQUIRED_HELPER,
    required_query_origin: str | None = DEFAULT_REQUIRED_QUERY_ORIGIN,
    expected_call_bytes: bytes | None = DEFAULT_EXPECTED_CALL_BYTES,
    base_graph_name: str | None = None,
    output_prefix: str | None = None,
    work_order_id: str = "WO70043",
    record_call_site_validation: bool = False,
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
            if pc == required_call_pc
        ]
        if len(call_rows) != 1:
            raise ProductionExportError(
                f"expected exactly one Stage-16 CODE record at 0x{required_call_pc:X}; found {len(call_rows)}"
            )
        call_pc, call_bytes, assembly, comment, function, label = call_rows[0]
        normalized_assembly = " ".join(assembly.split())
        if len(call_bytes) != 2 or not normalized_assembly.lower().startswith("jsr @"):
            raise ProductionExportError(
                f"expected one 16-bit indirect JSR at 0x{call_pc:X}: {call_bytes.hex()} {assembly!r}"
            )
        if expected_call_bytes is not None and call_bytes != expected_call_bytes:
            raise ProductionExportError(
                f"call-site byte mismatch at 0x{call_pc:X}: expected {expected_call_bytes.hex()}, "
                f"got {call_bytes.hex()} ({assembly!r})"
            )

        catalogue_rows, catalogue_target_row_present = _target_catalogue_rows(catalogue_path, target_ea)
        _, _, _, cat_calls = build_static_indices.full_rom_analysis(
            code_lines, rom, catalogue_rows, set()
        )
        target_calls = cat_calls.get(target_ea, [])
        if not target_calls:
            raise ProductionExportError(f"static tracker found no per-call rows for 0x{target_ea:X}")

        selected = [
            row for row in target_calls
            if row.get("reader_pc") == required_call_pc
        ]
        if len(selected) != 1:
            raise ProductionExportError(
                f"expected exactly one tracker row for target 0x{target_ea:X} at "
                f"0x{required_call_pc:X}; found {len(selected)}"
            )
        call_record = selected[0]
        if call_record.get("helper") != required_helper:
            raise ProductionExportError(
                f"helper mismatch at 0x{required_call_pc:X}: {call_record.get('helper')!r}"
            )
        q_inputs = call_record.get("q_inputs", [])
        if required_query_origin is not None and required_query_origin not in q_inputs:
            raise ProductionExportError(
                f"required query origin {required_query_origin!r} missing; observed {q_inputs!r}"
            )

        document = build_static_flow_call_document(
            {target_ea: target_calls},
            artifact_sha256=rom_sha256,
            source_listing_sha256=listing_source["member_sha256"],
            source_listing_path=(
                f"{listing_source['archive_path']}#{listing_source['member_name']}"
            ),
        )

    if record_call_site_validation:
        document["call_site_validation"] = {
            "target_ea": target_ea,
            "reader_pc": call_pc,
            "instruction_bytes": call_bytes.hex(" ").upper(),
            "assembly": normalized_assembly,
            "source_listing_sha256": listing_source["member_sha256"],
            "listing_rom_byte_concordant": True,
            "validator": "build_static_indices.parse_listing",
        }

    output_dir.mkdir(parents=True, exist_ok=True)
    prefix = output_prefix or f"EL19A_F501_{target_ea:05X}"
    json_path = output_dir / f"{prefix}_static_flow_calls.json"
    manifest_path = output_dir / f"{prefix}_static_flow_manifest.json"
    document_sha256 = write_static_flow_call_document(json_path, document)
    if document_sha256 != static_flow_document_sha256(document):
        raise ProductionExportError("written per-call document SHA-256 does not match canonical document hash")

    base_graph_path = output_dir / (base_graph_name or f"{prefix}.reader_trace.json")
    enriched_graph_path = output_dir / f"{prefix}.reader_trace.production_enriched.json"
    if not base_graph_path.is_file():
        raise ProductionExportError(f"golden graph fixture not found: {base_graph_path}")
    base_graph = json.loads(base_graph_path.read_text(encoding="utf-8"))
    static_flow_evidence_ref = f"ev:static-flow-production-{target_ea:05X}"
    if any(
        row.get("evidence_id") == static_flow_evidence_ref
        for row in base_graph.get("evidence", [])
        if isinstance(row, dict)
    ):
        raise ProductionExportError("golden graph unexpectedly already contains production per-call evidence")
    base_graph.setdefault("evidence", []).append({
        "evidence_id": static_flow_evidence_ref,
        "source_path": json_path.as_posix(),
        "hash_algorithm": "sha256",
        "source_hash": document_sha256,
        "anchor": f"Production full_rom_analysis cat_calls row for target 0x{target_ea:X}, call PC 0x{required_call_pc:X} and helper {required_helper}",
        "evidence_class": "per_call_static_reader_flow",
        "extraction_method": (
            "Production build_static_indices.full_rom_analysis() after pinned Stage-16 "
            "member extraction and parse_listing() ROM-byte concordance"
        ),
        "status": "production_byte_concordant_tracker_output",
    })
    enriched_graph = merge_per_call_static_flow(
        base_graph,
        document,
        static_flow_evidence_ref=static_flow_evidence_ref,
    )
    graph_warnings = validate_trace_graph(enriched_graph)
    resolved_boundary_ids = [
        row["boundary_id"] for row in enriched_graph.get("resolved_boundaries", [])
    ]
    if record_call_site_validation and target_ea == 0x10F8A and "listing-provenance-10f8a" not in resolved_boundary_ids:
        raise ProductionExportError("10F8A production call-site validation did not resolve listing-provenance-10f8a")
    graph_sha256 = write_trace_graph(enriched_graph_path, enriched_graph)

    manifest: Dict[str, Any] = {
        "schema": "reader-trace-static-flow-production-manifest-v0.1",
        "status": "PASS",
        "target_ea": f"0x{target_ea:08X}",
        "required_call_pc": f"0x{required_call_pc:X}",
        "required_helper": required_helper,
        "required_query_origin": required_query_origin,
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
            "target_catalogue_row_present": catalogue_target_row_present,
            "tracker_seed": (
                "existing_catalogue_row"
                if catalogue_target_row_present
                else f"explicit_address_only_seed_from_{work_order_id}; no geometry or semantic metadata fabricated"
            ),
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
            "production_enriched_graph_path": enriched_graph_path.as_posix(),
            "production_enriched_graph_bytes": enriched_graph_path.stat().st_size,
            "production_enriched_graph_sha256": graph_sha256,
        },
        "graph_validation": {
            "warning_count": len(graph_warnings),
            "warnings": graph_warnings,
            "base_fixture_preserved": True,
            "static_flow_evidence_ref": static_flow_evidence_ref,
            "resolved_boundary_ids": resolved_boundary_ids,
            "call_site_validation_recorded": record_call_site_validation,
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
        "production_enriched_graph_path": enriched_graph_path,
        "production_enriched_graph_sha256": graph_sha256,
        "graph_warnings": graph_warnings,
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
    parser.add_argument("--target-ea", type=lambda value: int(value, 0), default=DEFAULT_TARGET_EA)
    parser.add_argument("--required-call-pc", type=lambda value: int(value, 0), default=DEFAULT_REQUIRED_CALL_PC)
    parser.add_argument("--required-helper", default=DEFAULT_REQUIRED_HELPER)
    parser.add_argument("--required-query-origin", default=DEFAULT_REQUIRED_QUERY_ORIGIN)
    parser.add_argument("--no-required-query-origin", action="store_true")
    parser.add_argument("--expected-call-bytes", default="42 0B")
    parser.add_argument("--no-fixed-call-bytes", action="store_true")
    parser.add_argument("--base-graph", dest="base_graph_name")
    parser.add_argument("--output-prefix")
    parser.add_argument("--work-order", default="WO70043")
    parser.add_argument("--record-call-site-validation", action="store_true")
    args = parser.parse_args(argv)
    result = run_export(
        rom_path=args.rom,
        archive_path=args.listing_archive,
        catalogue_path=args.catalogue,
        output_dir=args.output_dir,
        target_ea=args.target_ea,
        required_call_pc=args.required_call_pc,
        required_helper=args.required_helper,
        required_query_origin=None if args.no_required_query_origin else args.required_query_origin,
        expected_call_bytes=None if args.no_fixed_call_bytes else bytes.fromhex(args.expected_call_bytes),
        base_graph_name=args.base_graph_name,
        output_prefix=args.output_prefix,
        work_order_id=args.work_order,
        record_call_site_validation=args.record_call_site_validation,
    )
    print(json.dumps({
        "status": "PASS",
        "target_ea": f"0x{args.target_ea:08X}",
        "selected_call": result["selected_call"],
        "target_per_call_row_count": result["target_per_call_row_count"],
        "per_call_json_sha256": result["per_call_json_sha256"],
        "manifest_file_sha256": result["manifest_file_sha256"],
        "per_call_json_path": result["per_call_json_path"].as_posix(),
        "manifest_path": result["manifest_path"].as_posix(),
        "production_enriched_graph_path": result["production_enriched_graph_path"].as_posix(),
        "production_enriched_graph_sha256": result["production_enriched_graph_sha256"],
        "graph_warnings": result["graph_warnings"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
