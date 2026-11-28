#!/usr/bin/env python3
"""Thin evidence adapter from existing SH-2 indexes into Reader Trace Graphs.

Consumes only rows already emitted by tools/rom_access_indexer.py and
build_static_indices.py. It contains no instruction decoder, register emulator,
or opcode logic.
"""
from __future__ import annotations

import copy
import re
from typing import Any, Dict, List, Mapping, MutableMapping, Sequence


class AdapterError(ValueError):
    """Malformed or insufficient indexed evidence."""


_HEX_EA = re.compile(r"^(?:0x)?([0-9A-Fa-f]{1,8})$")
_QUERY = re.compile(r"^r(?P<reg>\d+)\s*<-\s*(?P<ea>FFFF[0-9A-Fa-f]{4})$")
_DEST = re.compile(
    r"^(?P<ea>FFFF[0-9A-Fa-f]{4}):(?P<width>[bwl])@(?P<pc>(?:0x)?[0-9A-Fa-f]+)\((?P<kind>taint|near)\)$"
)
_DOWNSTREAM = re.compile(
    r"^(?P<ea>FFFF[0-9A-Fa-f]{4})@(?P<pc>(?:0x)?[0-9A-Fa-f]+)\((?P<func>[^()]*)\)$"
)


def _parse_hex(value: Any, field: str) -> int:
    if not isinstance(value, str):
        raise AdapterError(f"{field} must be hexadecimal text")
    match = _HEX_EA.fullmatch(value.strip())
    if not match:
        raise AdapterError(f"{field} is not a valid hexadecimal address: {value!r}")
    return int(match.group(1), 16)


def _append_unique(items: List[Dict[str, Any]], item: Dict[str, Any], key: str) -> None:
    if not any(existing.get(key) == item.get(key) for existing in items):
        items.append(item)


def _node(graph: MutableMapping[str, Any], node: Dict[str, Any]) -> None:
    _append_unique(graph.setdefault("nodes", []), node, "node_id")


def _edge(graph: MutableMapping[str, Any], edge: Dict[str, Any]) -> None:
    _append_unique(graph.setdefault("edges", []), edge, "edge_id")


def _boundary(graph: MutableMapping[str, Any], boundary: Dict[str, Any]) -> None:
    _append_unique(graph.setdefault("unresolved_boundaries", []), boundary, "boundary_id")


def _split_semicolon(value: Any) -> List[str]:
    if not isinstance(value, str) or not value.strip() or value.strip() == "-":
        return []
    return [part.strip() for part in value.split(";") if part.strip() and part.strip() != "-"]


_INDEXER_HIT_FIELDS = (
    "target", "space", "pc", "function", "access", "width",
    "form", "base", "base_resolved", "mask", "note",
)


def _normalize_hit_row(row: Any) -> Dict[str, Any]:
    """Accept either a named row or the exact 11-field tuple returned by run_indexer."""
    if isinstance(row, Mapping):
        return dict(row)
    if isinstance(row, Sequence) and not isinstance(row, (str, bytes, bytearray)):
        if len(row) != len(_INDEXER_HIT_FIELDS):
            raise AdapterError(
                f"indexer hit tuple must have {len(_INDEXER_HIT_FIELDS)} fields, got {len(row)}"
            )
        return dict(zip(_INDEXER_HIT_FIELDS, row))
    raise AdapterError("each hit row must be a mapping or an 11-field run_indexer tuple")


def _target_node_id(graph: Mapping[str, Any], target_ea: int) -> str:
    for node in graph.get("nodes", []):
        address = node.get("address")
        if (
            node.get("kind") == "rom_object"
            and isinstance(address, Mapping)
            and address.get("value") == target_ea
        ):
            return node["node_id"]
    raise AdapterError("no rom_object node matches target_object.ea")


def merge_indexed_reader_evidence(
    graph: Mapping[str, Any],
    hit_rows: Sequence[Any],
    catalogue_summary: Mapping[str, Any],
    *,
    indexer_evidence_ref: str,
    static_index_evidence_ref: str,
    concordance_matched: int,
    concordance_checked: int,
) -> Dict[str, Any]:
    """Return an enriched graph without mutating the input.

    hit_rows must be the validated valid_hits result from
    rom_access_indexer.run_indexer (not the unresolved output).
    Query/destination paths from the summary are derived from the static
    tracker. Fallback near stores remain heuristic. Downstream RAM reads
    are direct observations of read sites, not proof of value causality.
    """
    if not isinstance(graph, Mapping):
        raise AdapterError("graph must be a mapping")
    if (
        not isinstance(concordance_matched, int)
        or not isinstance(concordance_checked, int)
        or concordance_checked <= 0
        or concordance_matched <= 0
        or concordance_matched > concordance_checked
    ):
        raise AdapterError("invalid concordance counters")
    evidence_ids = {
        ev.get("evidence_id")
        for ev in graph.get("evidence", [])
        if isinstance(ev, Mapping)
    }
    if indexer_evidence_ref not in evidence_ids:
        raise AdapterError(f"unknown indexer evidence reference {indexer_evidence_ref!r}")
    if static_index_evidence_ref not in evidence_ids:
        raise AdapterError(f"unknown static-index evidence reference {static_index_evidence_ref!r}")

    target = graph.get("target_object")
    if not isinstance(target, Mapping) or not isinstance(target.get("ea"), int):
        raise AdapterError("graph target_object.ea is missing")
    target_ea = target["ea"]
    target_hex = f"0x{target_ea:X}"
    table_node = _target_node_id(graph, target_ea)
    out: Dict[str, Any] = copy.deepcopy(dict(graph))
    analysis_ext = out.setdefault("analysis_extensions", [])
    if not isinstance(analysis_ext, list):
        raise AdapterError("analysis_extensions must be a list when present")

    matched_hits = []
    for raw_row in hit_rows:
        row = _normalize_hit_row(raw_row)
        try:
            row_ea = _parse_hex(str(row.get("target", "")), "hit.target")
        except AdapterError:
            continue
        if row.get("space") != "rom" or row.get("access") != "read" or row_ea != target_ea:
            continue
        pc = _parse_hex(str(row.get("pc", "")), "hit.pc")
        matched_hits.append((pc, row))
    if not matched_hits:
        raise AdapterError(f"no byte-concordant ROM read hit for target {target_hex}")

    matched_hits.sort(key=lambda item: item[0])
    reader_node_ids = []
    for pc, row in matched_hits:
        site_id = f"indexer-read-{pc:08X}"
        reader_node_ids.append(site_id)
        _node(out, {
            "node_id": site_id,
            "kind": "code_site",
            "label": f"ROM read of {target_hex} at 0x{pc:X}",
            "address": {"space": "rom_ea", "value": pc},
            "confidence": "high",
            "evidence_refs": [indexer_evidence_ref],
            "properties": {
                "function": row.get("function", "unknown"),
                "access": row.get("access"),
                "width": row.get("width"),
                "form": row.get("form"),
                "base": row.get("base"),
                "base_resolved": row.get("base_resolved"),
                "note": row.get("note", ""),
                "pc_concordance": "present in validated valid_hits output",
            },
        })
        _edge(out, {
            "edge_id": f"indexer-table-read-{pc:08X}",
            "from_node": table_node,
            "to_node": site_id,
            "relation": "byte_concordant_ROM_read_at_PC",
            "basis": "direct_observation",
            "confidence": "high",
            "evidence_refs": [indexer_evidence_ref],
        })

    summary_ea = _parse_hex(str(catalogue_summary.get("address", "")), "catalogue_summary.address")
    if summary_ea != target_ea:
        raise AdapterError("catalogue summary row address does not match graph target")
    if len(reader_node_ids) > 1:
        _boundary(out, {
            "boundary_id": f"multiple-reader-sites-{target_ea:08X}",
            "at_node": table_node,
            "reason": "The static index summary may combine multiple call sites; each reader is represented independently, but query/result attribution remains per-call.",
            "required_evidence": "Per-call reader/query/result separation from a pinned full trace or independently decoded call-site windows.",
        })

    for query in _split_semicolon(catalogue_summary.get("traced_query_inputs", "")):
        match = _QUERY.fullmatch(query)
        if not match:
            _boundary(out, {
                "boundary_id": f"unparsed-query-{target_ea:08X}-{len(out['unresolved_boundaries'])+1}",
                "at_node": reader_node_ids[0],
                "reason": f"Static-index query token was not recognized: {query}",
                "required_evidence": "Preserve the original summary row and inspect the field format before interpreting it.",
            })
            continue
        reg = int(match.group("reg"))
        ram = match.group("ea").upper()
        ram_id = f"indexer-query-{ram}"
        reg_id = f"indexer-query-r{reg}-{target_ea:08X}"
        _node(out, {
            "node_id": ram_id, "kind": "ram_cell", "label": f"Query RAM source {ram}",
            "address": {"space": "ram_ea", "value": ram}, "confidence": "medium",
            "evidence_refs": [static_index_evidence_ref],
            "properties": {"role": "query_source_candidate", "source_register": f"R{reg}"},
        })
        _node(out, {
            "node_id": reg_id, "kind": "register", "label": f"R{reg} query provenance candidate",
            "address": None, "confidence": "medium",
            "evidence_refs": [static_index_evidence_ref],
            "properties": {"register": f"R{reg}", "source_ram": ram, "trace_origin": "static_index_query_inputs"},
        })
        _edge(out, {
            "edge_id": f"indexer-query-load-{target_ea:08X}-r{reg}-{ram[4:]}",
            "from_node": ram_id, "to_node": reg_id,
            "relation": f"query_value_loaded_into_R{reg}", "basis": "derived", "confidence": "medium",
            "evidence_refs": [static_index_evidence_ref],
        })
        if len(reader_node_ids) == 1:
            site_id = reader_node_ids[0]
            _edge(out, {
                "edge_id": f"indexer-query-arg-{target_ea:08X}-{site_id}-r{reg}-{ram[4:]}",
                "from_node": reg_id, "to_node": site_id,
                "relation": f"R{reg}_reported_as_lookup_query_input", "basis": "derived", "confidence": "medium",
                "evidence_refs": [static_index_evidence_ref],
            })

    for destination in _split_semicolon(catalogue_summary.get("traced_dest_ram", "")):
        match = _DEST.fullmatch(destination)
        if not match:
            _boundary(out, {
                "boundary_id": f"unparsed-destination-{target_ea:08X}-{len(out['unresolved_boundaries'])+1}",
                "at_node": reader_node_ids[0],
                "reason": f"Static-index destination token was not recognized: {destination}",
                "required_evidence": "Preserve the original summary row and inspect the field format before interpreting it.",
            })
            continue
        ea = match.group("ea").upper()
        width = match.group("width")
        pc = _parse_hex(match.group("pc"), "destination.pc")
        kind = match.group("kind")
        ram_id = f"indexer-dest-{ea}"
        site_id = f"indexer-store-{pc:08X}"
        _node(out, {
            "node_id": ram_id, "kind": "ram_cell", "label": f"Indexed result destination {ea}",
            "address": {"space": "ram_ea", "value": ea}, "confidence": "medium" if kind == "taint" else "low",
            "evidence_refs": [static_index_evidence_ref],
            "properties": {"role": "lookup_result_destination_candidate", "width": width, "taint_class": kind},
        })
        _node(out, {
            "node_id": site_id, "kind": "code_site", "label": f"Indexed RAM write at 0x{pc:X}",
            "address": {"space": "rom_ea", "value": pc}, "confidence": "medium" if kind == "taint" else "low",
            "evidence_refs": [static_index_evidence_ref],
            "properties": {"operation": "write", "destination": ea, "taint_class": kind},
        })
        if len(reader_node_ids) == 1:
            _edge(out, {
                "edge_id": f"indexer-result-write-{target_ea:08X}-{pc:08X}",
                "from_node": reader_node_ids[0], "to_node": ram_id,
                "relation": "tainted_lookup_result_written_to_RAM" if kind == "taint" else "near_call_RAM_write_candidate",
                "basis": "derived" if kind == "taint" else "heuristic",
                "confidence": "medium" if kind == "taint" else "low",
                "evidence_refs": [static_index_evidence_ref],
            })
        else:
            _boundary(out, {
                "boundary_id": f"aggregate-result-attribution-{target_ea:08X}-{pc:08X}",
                "at_node": site_id,
                "reason": "The per-address summary aggregates multiple reader call sites, so this destination cannot be attributed to one specific call from the available row.",
                "required_evidence": "Per-call lookup-result provenance linking a specific helper call to this RAM write.",
            })
        _edge(out, {
            "edge_id": f"indexer-store-site-{target_ea:08X}-{pc:08X}",
            "from_node": site_id, "to_node": ram_id,
            "relation": "writes_RAM_destination", "basis": "direct_observation", "confidence": "high",
            "evidence_refs": [static_index_evidence_ref],
        })
        if kind == "near":
            _boundary(out, {
                "boundary_id": f"near-store-not-tainted-{target_ea:08X}-{pc:08X}",
                "at_node": site_id,
                "reason": "Static-index fallback classified this store as near-call, not taint-proven lookup-result flow.",
                "required_evidence": "A precise producer-to-store value-flow trace proving the lookup result reaches this write.",
            })

    for downstream in _split_semicolon(catalogue_summary.get("dest_downstream_sample", "")):
        match = _DOWNSTREAM.fullmatch(downstream)
        if not match:
            continue
        ea = match.group("ea").upper()
        pc = _parse_hex(match.group("pc"), "downstream.pc")
        func = match.group("func")
        ram_id = f"indexer-dest-{ea}"
        if not any(node.get("node_id") == ram_id for node in out["nodes"]):
            _node(out, {
                "node_id": ram_id, "kind": "ram_cell", "label": f"Downstream RAM cell {ea}",
                "address": {"space": "ram_ea", "value": ea}, "confidence": "medium",
                "evidence_refs": [static_index_evidence_ref],
                "properties": {"role": "indexed_downstream_read_source"},
            })
        consumer_id = f"indexer-downstream-read-{pc:08X}"
        _node(out, {
            "node_id": consumer_id, "kind": "consumer", "label": f"Indexed RAM read at 0x{pc:X}",
            "address": {"space": "rom_ea", "value": pc}, "confidence": "high",
            "evidence_refs": [static_index_evidence_ref],
            "properties": {"function": func, "read_source": ea, "consumer_semantics": "unresolved"},
        })
        _edge(out, {
            "edge_id": f"indexer-downstream-read-{target_ea:08X}-{pc:08X}",
            "from_node": ram_id, "to_node": consumer_id,
            "relation": "RAM_cell_read_at_PC_no_value_causality_claimed",
            "basis": "direct_observation", "confidence": "high",
            "evidence_refs": [static_index_evidence_ref],
        })
        _boundary(out, {
            "boundary_id": f"downstream-value-causality-{target_ea:08X}-{pc:08X}",
            "at_node": consumer_id,
            "reason": "A static downstream read of the destination RAM cell is present, but this alone does not prove that it consumes the specific lookup result or establish physical meaning.",
            "required_evidence": "Path-sensitive per-call value provenance from lookup return through the RAM cell to this consumer.",
        })

    _append_unique(analysis_ext, {
        "extension_id": f"rom-access-indexer-bridge-{target_ea:08X}",
        "adapter": "reader-trace-indexer-adapter-v0.1",
        "target_ea": target_hex,
        "reader_hit_count": len(matched_hits),
        "concordance_matched": concordance_matched,
        "concordance_checked": concordance_checked,
        "limitations": [
            "Consumes existing index rows; no SH-2 opcodes decoded here.",
            "Static query/destination fields are derived from the existing tracker.",
            "Near-call stores remain heuristic.",
            "Downstream RAM read sites do not establish lookup-result value causality.",
        ],
    }, "extension_id")
    return out
