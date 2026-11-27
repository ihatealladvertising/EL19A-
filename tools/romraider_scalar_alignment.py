"""Target-side audit of donor-aligned scalar TSV/XML evidence."""
from __future__ import annotations

import csv
import hashlib
import json
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Optional


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _address(value: str) -> int:
    value = value.strip()
    return int(value, 16 if value.lower().startswith("0x") else 10)


def _xml_address_hits(path: Optional[Path]) -> Dict[int, List[dict]]:
    hits: Dict[int, List[dict]] = defaultdict(list)
    if path is None:
        return hits
    root = ET.parse(path).getroot()
    for node in root.iter():
        raw_addr = node.attrib.get("storageaddress") or node.attrib.get("address")
        if not raw_addr:
            continue
        try:
            addr = _address(raw_addr)
        except ValueError:
            continue
        hits[addr].append({
            "name": node.attrib.get("name"),
            "type": node.attrib.get("type"),
            "storage_type": node.attrib.get("storagetype"),
            "scaling": node.attrib.get("scaling"),
            "category": node.attrib.get("category"),
        })
    return hits


def audit_scalar_alignment(
    rom: bytes,
    alignment_tsv: Path,
    *,
    xml_fragment: Optional[Path] = None,
    catalogue: Optional[dict] = None,
    catalogue_path: Optional[Path] = None,
) -> tuple[List[dict], dict]:
    """Join aligned declarations to target bytes, scanner spans, and optional XML.

    Donor symbol names, tiers, conversions, units, and XML scaling are copied as
    source hypotheses. Only unsigned 1/2-byte byte comparisons are evaluated.
    """
    xml_hits = _xml_address_hits(xml_fragment)
    scanner_by_addr: Dict[int, List[dict]] = defaultdict(list)
    for item in (catalogue or {}).get("scalar_candidates", []):
        try:
            scanner_by_addr[int(item["address"])].append(item)
        except (KeyError, TypeError, ValueError):
            continue

    rows: List[dict] = []
    counts: Counter = Counter()
    with alignment_tsv.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        required = {"symbol", "size", "el19a_addr", "el19a_value", "tier", "conversion"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Alignment TSV missing required columns: {sorted(missing)}")
        for row_number, source in enumerate(reader, start=2):
            record = dict(source)
            record["source_row"] = row_number
            try:
                addr = _address(source["el19a_addr"])
                size = int(source["size"], 10)
                declared = int(source["el19a_value"], 0)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Invalid address/size/value on TSV row {row_number}: {exc}") from exc
            record["target_address"] = f"0x{addr:05X}"
            record["target_size_bytes"] = size
            record["target_extent_in_bounds"] = size > 0 and 0 <= addr <= len(rom) - size
            raw = rom[addr:addr + size] if record["target_extent_in_bounds"] else b""
            record["target_bytes_hex"] = raw.hex().upper() if raw else None
            record["target_unsigned_be"] = int.from_bytes(raw, "big", signed=False) if raw else None
            if not record["target_extent_in_bounds"]:
                comparison = "OUT_OF_BOUNDS"
            elif size in (1, 2):
                comparison = "MATCH" if record["target_unsigned_be"] == declared else "MISMATCH"
            elif size == 4:
                comparison = "UNRESOLVED_SIZE4_TYPE_CONVERSION"
            else:
                comparison = "UNRESOLVED_UNSUPPORTED_WIDTH"
            record["target_unsigned_comparison"] = comparison

            scan_rows = scanner_by_addr.get(addr, [])
            compatible = []
            for candidate in scan_rows:
                span = candidate.get("span") or {}
                if span.get("element_width_bytes") == size and span.get("in_bounds") is True:
                    compatible.append(candidate)
            record["scanner_candidate_count_at_address"] = len(scan_rows)
            record["scanner_exact_width_match_count"] = len(compatible)
            record["scanner_candidates"] = [{
                "element_type": (item.get("span") or {}).get("element_type"),
                "element_width_bytes": (item.get("span") or {}).get("element_width_bytes"),
                "status": (item.get("span") or {}).get("status"),
            } for item in scan_rows]
            record["xml_fragment_hits"] = xml_hits.get(addr, [])
            record["xml_fragment_hit_count"] = len(record["xml_fragment_hits"])
            record["xml_labels_are_hypotheses"] = bool(record["xml_fragment_hits"])
            rows.append(record)
            counts[comparison] += 1
            counts["scanner_exact_width_match"] += bool(compatible)
            counts["xml_exact_address_hit"] += bool(record["xml_fragment_hits"])

    address_counts = Counter(row["target_address"] for row in rows)
    repeated = {addr: count for addr, count in address_counts.items() if count > 1}
    summary = {
        "schema": "sh705x-scalar-alignment-audit-v1",
        "row_count": len(rows),
        "unique_target_addresses": len(address_counts),
        "repeated_target_address_count": len(repeated),
        "repeated_target_address_extra_rows": sum(n - 1 for n in repeated.values()),
        "counts": dict(sorted(counts.items())),
        "input_sha256": {
            "alignment_tsv": _sha256(alignment_tsv),
            "xml_fragment": _sha256(xml_fragment) if xml_fragment else None,
            "scan_catalogue": _sha256(catalogue_path) if catalogue_path else None,
        },
        "target_rom_sha256": hashlib.sha256(rom).hexdigest(),
        "interpretation_boundary": (
            "A2L names, tiers, conversions and XML scaling are hypotheses. "
            "Four-byte comparisons remain unresolved without a verified target type/conversion."
        ),
    }
    return rows, summary


def write_audit_outputs(rows: List[dict], summary: dict, out_prefix: Path) -> tuple[Path, Path]:
    out_prefix.parent.mkdir(parents=True, exist_ok=True)
    json_path = out_prefix.with_suffix(".json")
    tsv_path = out_prefix.with_suffix(".tsv")
    summary["row_output"] = tsv_path.name
    json_path.write_text(json.dumps({"summary": summary, "rows": rows}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    columns = ["source_row", "symbol", "description", "v6_addr", "size", "el19a_addr", "el19a_value", "tier", "conversion", "function_group", "target_address", "target_size_bytes", "target_extent_in_bounds", "target_bytes_hex", "target_unsigned_be", "target_unsigned_comparison", "scanner_candidate_count_at_address", "scanner_exact_width_match_count", "xml_fragment_hit_count", "xml_fragment_hits"]
    with tsv_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, delimiter="\t", extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            out = dict(row)
            out["xml_fragment_hits"] = json.dumps(out["xml_fragment_hits"], sort_keys=True, separators=(",", ":"))
            writer.writerow(out)
    return json_path, tsv_path
