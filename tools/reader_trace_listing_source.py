#!/usr/bin/env python3
"""Verify and extract bounded helper/caller windows from the pinned Stage-16 LST.

This is a read-only text extractor. It consumes IDA's existing CODE listing
records using the same line grammar as rom_access_indexer.py; it does not
decode opcodes, infer control flow, or reinterpret instruction semantics.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Sequence, Tuple

DEFAULT_ARCHIVE = Path(
    "EVIDENCE/EL19A_Complete_Disassembly_ANNOTATED_V3_NEXT6_14_GBR_BASE_RESOLVED.zip"
)
DEFAULT_MEMBER = (
    "EL19A_Complete_Disassembly_ANNOTATED_V3_NEXT6_16_ALL_PENDING_ANNOTATIONS(1).lst"
)
EXPECTED_ARCHIVE_SHA256 = "8f88f711a585afd56d0541f56c4bc6bb0a4c57a0d58016258fde5c2f1916cc42"
EXPECTED_MEMBER_SHA256 = "148385bbec91f6a491dcaa403962836f709c2f273df9a17ec51f1dea5f7f4549"

HELPER_FUNCTIONS = ("sub_22E10", "sub_22FAC", "sub_22B44", "sub_22DF8", "sub_233CC", "sub_2340C", "sub_231C8")
HELPER_ENTRY_POINTS = {"loc_23508": 0x23508, "loc_2350C": 0x2350C}
ENTRY_POINT_WINDOW_BYTES = 0x40
CALL_SITES = (0x85B2E, 0x648D8, 0x5B3C0)

_CODE_RE = re.compile(
    r"^([0-9A-Fa-f]{8})\s+([0-9A-Fa-f\s]{2,20})\s+CODE\s+([^\r\n;]+)(?:;\s*(.*))?$"
)
_LABEL_RE = re.compile(r"^([a-zA-Z_][a-zA-Z0-9_]*):")


class ListingSourceError(ValueError):
    """Pinned source archive/member integrity or selection failure."""


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def extract_verified_member(
    archive_path: Path,
    *,
    member_name: str = DEFAULT_MEMBER,
    expected_archive_sha256: str = EXPECTED_ARCHIVE_SHA256,
    expected_member_sha256: str = EXPECTED_MEMBER_SHA256,
) -> Tuple[bytes, Dict[str, str]]:
    """Read one exact ZIP member after verifying archive and member SHA-256."""
    archive_bytes = archive_path.read_bytes()
    archive_sha = sha256_bytes(archive_bytes)
    if archive_sha.lower() != expected_archive_sha256.lower():
        raise ListingSourceError(
            f"archive SHA-256 mismatch: expected {expected_archive_sha256}, got {archive_sha}"
        )
    try:
        with zipfile.ZipFile(archive_path, "r") as archive:
            names = archive.namelist()
            matches = [name for name in names if name == member_name]
            if len(matches) != 1:
                raise ListingSourceError(
                    f"expected exactly one ZIP member {member_name!r}, found {len(matches)}"
                )
            info = archive.getinfo(member_name)
            listing_bytes = archive.read(info)
    except zipfile.BadZipFile as exc:
        raise ListingSourceError(f"source archive is not a valid ZIP: {exc}") from exc

    member_sha = sha256_bytes(listing_bytes)
    if member_sha.lower() != expected_member_sha256.lower():
        raise ListingSourceError(
            f"extracted listing SHA-256 mismatch: expected {expected_member_sha256}, got {member_sha}"
        )
    metadata = {
        "archive_path": archive_path.as_posix(),
        "archive_sha256": archive_sha,
        "member_name": member_name,
        "member_sha256": member_sha,
        "member_bytes": str(len(listing_bytes)),
    }
    return listing_bytes, metadata


def parse_listing_records(listing_bytes: bytes) -> List[Dict[str, object]]:
    """Parse existing CODE/label text records; do not decode instruction bytes."""
    text = listing_bytes.decode("utf-8", errors="replace")
    records: List[Dict[str, object]] = []
    current_function = "unknown"
    current_label = "unknown"
    for line_number, line in enumerate(text.splitlines(), 1):
        label_match = _LABEL_RE.match(line)
        if label_match:
            label = label_match.group(1)
            current_label = label
            if label.startswith("sub_"):
                current_function = label
            continue
        code_match = _CODE_RE.match(line)
        if not code_match:
            continue
        pc = int(code_match.group(1), 16)
        raw_bytes = bytes.fromhex(code_match.group(2).strip())
        records.append({
            "pc": pc,
            "bytes_hex": raw_bytes.hex(" ").upper(),
            "assembly": code_match.group(3).strip(),
            "comment": code_match.group(4).strip() if code_match.group(4) else "",
            "function": current_function,
            "label": current_label,
            "source_line": line_number,
        })
    if not records:
        raise ListingSourceError("no CODE records parsed from the pinned listing")
    return records


def extract_helper_and_call_windows(
    records: Sequence[Mapping[str, object]],
    *,
    helper_functions: Sequence[str] = HELPER_FUNCTIONS,
    call_sites: Sequence[int] = CALL_SITES,
    call_context_bytes: int = 0x10,
) -> Dict[str, object]:
    """Select only full named helper functions and bounded caller PC windows."""
    helper_windows: Dict[str, object] = {}
    by_function: Dict[str, List[Mapping[str, object]]] = {}
    by_pc: Dict[int, Mapping[str, object]] = {}
    for record in records:
        function = str(record["function"])
        by_function.setdefault(function, []).append(record)
        pc = int(record["pc"])
        if pc in by_pc:
            raise ListingSourceError(f"duplicate CODE PC 0x{pc:X} in listing")
        by_pc[pc] = record

    missing_helpers = [name for name in helper_functions if name not in by_function]
    if missing_helpers:
        raise ListingSourceError("helper labels not found: " + ", ".join(missing_helpers))

    for helper in helper_functions:
        selected = by_function[helper]
        helper_windows[helper] = {
            "instruction_count": len(selected),
            "start_pc": min(int(record["pc"]) for record in selected),
            "end_pc": max(int(record["pc"]) for record in selected),
            "instructions": list(selected),
        }

    entry_windows: Dict[str, object] = {}
    for label, entry_pc in HELPER_ENTRY_POINTS.items():
        found = by_pc.get(entry_pc)
        if found is None:
            raise ListingSourceError(f"helper entry PC 0x{entry_pc:X} ({label}) not found in listing")
        selected = [
            record for record in records
            if entry_pc <= int(record["pc"]) < entry_pc + ENTRY_POINT_WINDOW_BYTES
        ]
        selected.sort(key=lambda record: int(record["pc"]))
        entry_windows[label] = {
            "entry_pc": entry_pc,
            "window_end": entry_pc + ENTRY_POINT_WINDOW_BYTES,
            "instructions": list(selected),
        }

    caller_windows: Dict[str, object] = {}
    for call_pc in call_sites:
        found = by_pc.get(call_pc)
        if found is None:
            raise ListingSourceError(f"call-site PC 0x{call_pc:X} not found in listing")
        lo = max(0, call_pc - call_context_bytes)
        hi = call_pc + call_context_bytes
        selected = [
            record for record in records
            if lo <= int(record["pc"]) <= hi
        ]
        selected.sort(key=lambda record: int(record["pc"]))
        caller_windows[f"0x{call_pc:X}"] = {
            "context_start": lo,
            "context_end": hi,
            "call_instruction": dict(found),
            "instructions": list(selected),
        }

    return {
        "helper_functions": helper_windows,
        "helper_entry_points": entry_windows,
        "call_sites": caller_windows,
        "selection_policy": {
            "helper_functions": list(helper_functions),
            "helper_entry_points": {label: f"0x{pc:X}" for label, pc in HELPER_ENTRY_POINTS.items()},
            "entry_point_window_bytes": ENTRY_POINT_WINDOW_BYTES,
            "call_sites": [f"0x{pc:X}" for pc in call_sites],
            "call_context_bytes": call_context_bytes,
            "instruction_decoder_used": False,
            "source_line_grammar": "rom_access_indexer.py CODE record regex",
        },
    }


def build_source_report(
    archive_path: Path = DEFAULT_ARCHIVE,
    *,
    out_path: Path | None = None,
) -> Dict[str, object]:
    listing_bytes, source_metadata = extract_verified_member(archive_path)
    records = parse_listing_records(listing_bytes)
    windows = extract_helper_and_call_windows(records)
    report: Dict[str, object] = {
        "schema": "reader-trace-pinned-listing-windows-v0.1",
        "source": source_metadata,
        "listing_record_count": len(records),
        "windows": windows,
    }
    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    report = build_source_report(args.archive, out_path=args.out)
    print(json.dumps({
        "archive_sha256": report["source"]["archive_sha256"],
        "member_sha256": report["source"]["member_sha256"],
        "member_bytes": report["source"]["member_bytes"],
        "listing_record_count": report["listing_record_count"],
        "helper_instruction_counts": {
            name: data["instruction_count"]
            for name, data in report["windows"]["helper_functions"].items()
        },
        "helper_entry_point_instruction_counts": {
            name: len(data["instructions"])
            for name, data in report["windows"]["helper_entry_points"].items()
        },
        "call_sites": list(report["windows"]["call_sites"]),
        "output": args.out.as_posix(),
        "instruction_decoder_used": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
