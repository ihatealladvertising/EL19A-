#!/usr/bin/env python3
"""Per-call static-flow adapter for SH705x Reader Trace v0.1.

Consumes raw per-call records emitted by build_static_indices.full_rom_analysis.
It does not decode SH-2 instructions, execute control flow, or duplicate the
existing register/RAM tracker. All flow edges remain derived or heuristic.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence, Tuple

SCHEMA = "sh705x-static-reader-calls-v0.1"
_QUERY_RE = re.compile(r"^r(?P<reg>\d+)\s*<-\s*(?P<ea>FFFF[0-9A-Fa-f]{4})$")
_HELPER_RE = re.compile(r"^sub_(?P<ea>[0-9A-Fa-f]{4,8})$")
_HEX_RE = re.compile(r"^(?:0x)?([0-9A-Fa-f]{1,8})$")
_WIDTHS = {"b", "w", "l"}


class StaticFlowAdapterError(ValueError):
    """Invalid or insufficient per-call static-flow evidence."""


def _parse_ea(value: Any, field: str) -> int:
    if isinstance(value, bool):
        raise StaticFlowAdapterError(f"{field} must be an address, not boolean")
    if isinstance(value, int) and value >= 0:
        return value
    if isinstance(value, str):
        match = _HEX_RE.fullmatch(value.strip())
        if match:
            return int(match.group(1), 16)
    raise StaticFlowAdapterError(f"{field} is not a valid hexadecimal address: {value!r}")


def _require_sha256(value: Any, field: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-fA-F]{64}", value) is None:
        raise StaticFlowAdapterError(f"{field} must be a 64-character SHA-256 digest")
    return value.lower()


def _helper_ea(symbol: Any) -> int | None:
    if not isinstance(symbol, str):
        return None
    match = _HELPER_RE.fullmatch(symbol.strip())
    return int(match.group("ea"), 16) if match else None


def _store_source_register(instruction: str) -> str | None:
    """Return the explicit register operand of a parsed MOV store, if recognized."""
    match = re.search(r"\bmov\.[bwl]\s+(r\d+)\s*,\s*@", instruction, re.IGNORECASE)
    return match.group(1).lower() if match else None


def _normalise_destination(raw: Any, where: str) -> Dict[str, Any]:
    if isinstance(raw, Mapping):
        get = lambda key: raw.get(key)
        ea = get("ram_ea")
        width = get("width")
        pc = get("write_pc")
        instruction = get("instruction")
        tainted = get("is_tainted")
    elif isinstance(raw, Sequence) and not isinstance(raw, (str, bytes, bytearray)) and len(raw) == 5:
        ea, width, pc, instruction, tainted = raw
    else:
        raise StaticFlowAdapterError(f"{where} must be a destination mapping or 5-field tuple")

    ea_value = _parse_ea(ea, f"{where}.ram_ea")
    pc_value = _parse_ea(pc, f"{where}.write_pc")
    if width not in _WIDTHS:
        raise StaticFlowAdapterError(f"{where}.width must be one of b/w/l")
    if not isinstance(instruction, str) or not instruction.strip():
        raise StaticFlowAdapterError(f"{where}.instruction must be non-empty text")
    if not isinstance(tainted, bool):
        raise StaticFlowAdapterError(f"{where}.is_tainted must be boolean")
    if not (0xFFFF0000 <= ea_value <= 0xFFFFD7FF):
        raise StaticFlowAdapterError(f"{where}.ram_ea is outside the tracked RAM range")
    return {
        "ram_ea": ea_value,
        "width": width,
        "write_pc": pc_value,
        "instruction": instruction.strip(),
        "is_tainted": tainted,
    }


def build_static_flow_call_document(
    cat_calls: Mapping[Any, Sequence[Mapping[str, Any]]],
    *,
    artifact_sha256: str,
    source_listing_sha256: str,
    source_listing_path: str,
) -> Dict[str, Any]:
    """Convert raw full_rom_analysis cat_calls into a deterministic JSON document.

    Input call rows are kept separate by (table EA, reader PC); no per-address
    aggregation of query inputs or destination stores is performed.
    """
    artifact_hash = _require_sha256(artifact_sha256, "artifact_sha256")
    listing_hash = _require_sha256(source_listing_sha256, "source_listing_sha256")
    if not isinstance(source_listing_path, str) or not source_listing_path.strip():
        raise StaticFlowAdapterError("source_listing_path must be non-empty")

    rows: List[Dict[str, Any]] = []
    seen = set()
    for raw_target, raw_calls in cat_calls.items():
        target_ea = _parse_ea(raw_target, "cat_calls target EA")
        if not isinstance(raw_calls, Sequence) or isinstance(raw_calls, (str, bytes, bytearray)):
            raise StaticFlowAdapterError(f"cat_calls[{raw_target!r}] must be a sequence")
        for i, call in enumerate(raw_calls):
            where = f"cat_calls[{raw_target!r}][{i}]"
            if not isinstance(call, Mapping):
                raise StaticFlowAdapterError(f"{where} must be a mapping")
            reader_pc = _parse_ea(call.get("reader_pc"), f"{where}.reader_pc")
            function = call.get("func")
            helper = call.get("helper")
            q_inputs = call.get("q_inputs", [])
            dests = call.get("dests", [])
            if not isinstance(function, str) or not function.strip():
                raise StaticFlowAdapterError(f"{where}.func must be non-empty text")
            if not isinstance(helper, str) or not helper.strip():
                raise StaticFlowAdapterError(f"{where}.helper must be non-empty text")
            if not isinstance(q_inputs, Sequence) or isinstance(q_inputs, (str, bytes, bytearray)):
                raise StaticFlowAdapterError(f"{where}.q_inputs must be a sequence")
            if not isinstance(dests, Sequence) or isinstance(dests, (str, bytes, bytearray)):
                raise StaticFlowAdapterError(f"{where}.dests must be a sequence")
            identity = (target_ea, reader_pc)
            if identity in seen:
                raise StaticFlowAdapterError(
                    f"duplicate per-call record for target 0x{target_ea:X} at PC 0x{reader_pc:X}"
                )
            seen.add(identity)
            rows.append({
                "target_ea": target_ea,
                "reader_pc": reader_pc,
                "function": function.strip(),
                "helper_symbol": helper.strip(),
                "helper_ea": _helper_ea(helper),
                "q_inputs": [
                    item.strip() if isinstance(item, str) else item
                    for item in q_inputs
                ],
                "dests": [
                    _normalise_destination(item, f"{where}.dests[{j}]")
                    for j, item in enumerate(dests)
                ],
            })

    if not rows:
        raise StaticFlowAdapterError("cat_calls contains no per-call records")
    rows.sort(key=lambda row: (row["target_ea"], row["reader_pc"], row["function"], row["helper_symbol"]))
    return {
        "schema": SCHEMA,
        "artifact_sha256": artifact_hash,
        "source_listing_sha256": listing_hash,
        "source_listing_path": source_listing_path.strip(),
        "calls": rows,
    }


def validate_static_flow_call_document(document: Mapping[str, Any]) -> None:
    if not isinstance(document, Mapping) or document.get("schema") != SCHEMA:
        raise StaticFlowAdapterError(f"static-flow document must use schema {SCHEMA}")
    _require_sha256(document.get("artifact_sha256"), "document.artifact_sha256")
    _require_sha256(document.get("source_listing_sha256"), "document.source_listing_sha256")
    if not isinstance(document.get("source_listing_path"), str) or not document["source_listing_path"].strip():
        raise StaticFlowAdapterError("document.source_listing_path must be non-empty")
    calls = document.get("calls")
    if not isinstance(calls, list) or not calls:
        raise StaticFlowAdapterError("document.calls must be a non-empty list")
    seen = set()
    for i, call in enumerate(calls):
        if not isinstance(call, Mapping):
            raise StaticFlowAdapterError(f"document.calls[{i}] must be a mapping")
        target = _parse_ea(call.get("target_ea"), f"document.calls[{i}].target_ea")
        pc = _parse_ea(call.get("reader_pc"), f"document.calls[{i}].reader_pc")
        if (target, pc) in seen:
            raise StaticFlowAdapterError(f"duplicate target/call pair at 0x{target:X}/0x{pc:X}")
        seen.add((target, pc))
        if not isinstance(call.get("function"), str) or not call["function"].strip():
            raise StaticFlowAdapterError(f"document.calls[{i}].function is required")
        if not isinstance(call.get("helper_symbol"), str) or not call["helper_symbol"].strip():
            raise StaticFlowAdapterError(f"document.calls[{i}].helper_symbol is required")
        expected_helper = _helper_ea(call["helper_symbol"])
        declared_helper = call.get("helper_ea")
        if declared_helper is not None and declared_helper != expected_helper:
            raise StaticFlowAdapterError(f"document.calls[{i}].helper_ea conflicts with helper_symbol")
        if not isinstance(call.get("q_inputs"), list) or not isinstance(call.get("dests"), list):
            raise StaticFlowAdapterError(f"document.calls[{i}] requires q_inputs and dests lists")
        for j, dest in enumerate(call["dests"]):
            _normalise_destination(dest, f"document.calls[{i}].dests[{j}]")

    call_validation = document.get("call_site_validation")
    if call_validation is not None:
        if not isinstance(call_validation, Mapping):
            raise StaticFlowAdapterError("document.call_site_validation must be a mapping")
        if not isinstance(call_validation.get("instruction_bytes"), str):
            raise StaticFlowAdapterError("call_site_validation.instruction_bytes must be hex text")
        try:
            instruction_bytes = bytes.fromhex(call_validation["instruction_bytes"])
        except ValueError as exc:
            raise StaticFlowAdapterError("call_site_validation.instruction_bytes is invalid hex") from exc
        assembly = str(call_validation.get("assembly", "")).strip().lower()
        if len(instruction_bytes) != 2 or not assembly.startswith("jsr @"):
            raise StaticFlowAdapterError("call_site_validation must identify one 16-bit indirect JSR")
        if call_validation.get("listing_rom_byte_concordant") is not True:
            raise StaticFlowAdapterError("call_site_validation lacks positive listing/ROM byte concordance")
        if call_validation.get("validator") != "build_static_indices.parse_listing":
            raise StaticFlowAdapterError("call_site_validation must name the existing parse_listing validator")
        _require_sha256(call_validation.get("source_listing_sha256"), "call_site_validation.source_listing_sha256")
        if str(call_validation["source_listing_sha256"]).lower() != str(document["source_listing_sha256"]).lower():
            raise StaticFlowAdapterError("call_site_validation listing hash conflicts with document")


def canonical_static_flow_json(document: Mapping[str, Any]) -> str:
    validate_static_flow_call_document(document)
    return json.dumps(document, sort_keys=True, indent=2, ensure_ascii=False) + "\n"


def static_flow_document_sha256(document: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_static_flow_json(document).encode("utf-8")).hexdigest()


def write_static_flow_call_document(path: os.PathLike[str] | str, document: Mapping[str, Any]) -> str:
    """Atomically write a deterministic per-call evidence document and return its SHA-256."""
    destination = Path(path)
    payload = canonical_static_flow_json(document)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{destination.name}.", suffix=".tmp", dir=str(destination.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, destination)
    except Exception:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise
    return digest


def _append_node(out: Dict[str, Any], node: Dict[str, Any]) -> None:
    existing = [item for item in out.setdefault("nodes", []) if item.get("node_id") == node["node_id"]]
    if existing:
        if existing[0] != node:
            raise StaticFlowAdapterError(f"conflicting node identity {node['node_id']!r}")
        return
    out["nodes"].append(node)


def _append_edge(out: Dict[str, Any], edge: Dict[str, Any]) -> None:
    existing = [item for item in out.setdefault("edges", []) if item.get("edge_id") == edge["edge_id"]]
    if existing:
        if existing[0] != edge:
            raise StaticFlowAdapterError(f"conflicting edge identity {edge['edge_id']!r}")
        return
    out["edges"].append(edge)


def _append_boundary(out: Dict[str, Any], boundary: Dict[str, Any]) -> None:
    existing = [item for item in out.setdefault("unresolved_boundaries", []) if item.get("boundary_id") == boundary["boundary_id"]]
    if existing:
        if existing[0] != boundary:
            raise StaticFlowAdapterError(f"conflicting boundary identity {boundary['boundary_id']!r}")
        return
    out["unresolved_boundaries"].append(boundary)


def _call_node_id(graph: Mapping[str, Any], call_pc: int, helper_ea: int) -> str:
    matches = [
        node["node_id"] for node in graph.get("nodes", [])
        if node.get("kind") == "code_site"
        and isinstance(node.get("address"), Mapping)
        and node["address"].get("space") == "rom_ea"
        and node["address"].get("value") == call_pc
    ]
    if len(matches) <= 1:
        return matches[0] if matches else f"static-flow-call-{call_pc:08X}"

    # The existing graph can contain both its original call node and a
    # separate byte-concordant indexer read-site node at the same PC. Prefer
    # the node already connected to the exact helper through a "calls" edge.
    helper_ids = {
        node.get("node_id") for node in graph.get("nodes", [])
        if node.get("kind") == "lookup_helper"
        and isinstance(node.get("address"), Mapping)
        and node["address"].get("value") == helper_ea
    }
    linked = [
        edge.get("from_node") for edge in graph.get("edges", [])
        if edge.get("relation") == "calls"
        and edge.get("to_node") in helper_ids
        and edge.get("from_node") in matches
    ]
    if len(set(linked)) == 1:
        return linked[0]

    canonical = f"code-{call_pc:05x}".lower()
    if canonical in matches:
        return canonical
    raise StaticFlowAdapterError(
        f"graph has multiple code-site nodes for call PC 0x{call_pc:X} and no unique helper-call edge"
    )


def merge_per_call_static_flow(
    graph: Mapping[str, Any],
    document: Mapping[str, Any],
    *,
    static_flow_evidence_ref: str,
) -> Dict[str, Any]:
    """Attach exactly one raw per-call cat_calls row to the graph's call_ref.

    Evidence basis remains derived/heuristic. The input graph and document are
    never mutated. The JSON evidence hash must match the serialized document.
    """
    validate_static_flow_call_document(document)
    if not isinstance(graph, Mapping):
        raise StaticFlowAdapterError("graph must be a mapping")
    target = graph.get("target_object")
    call_ref = graph.get("call_ref")
    if not isinstance(target, Mapping) or not isinstance(call_ref, Mapping):
        raise StaticFlowAdapterError("graph requires target_object and call_ref")
    target_ea = target.get("ea")
    call_pc = call_ref.get("call_pc")
    helper_ea = call_ref.get("helper_ea")
    if not isinstance(target_ea, int) or not isinstance(call_pc, int) or not isinstance(helper_ea, int):
        raise StaticFlowAdapterError("graph target EA, call PC and helper EA must be integers")
    if document["artifact_sha256"].lower() != str(graph.get("artifact", {}).get("decoded_sha256", "")).lower():
        raise StaticFlowAdapterError("static-flow artifact SHA-256 does not match graph ROM")
    coverage = graph.get("coverage", {})
    pinned_listing = coverage.get("source_listing_sha256") if isinstance(coverage, Mapping) else None
    listing_sha = document["source_listing_sha256"].lower()
    if pinned_listing and str(pinned_listing).lower() != listing_sha:
        raise StaticFlowAdapterError("static-flow listing SHA-256 conflicts with graph coverage")

    evidence_rows = [
        row for row in graph.get("evidence", [])
        if isinstance(row, Mapping) and row.get("evidence_id") == static_flow_evidence_ref
    ]
    if len(evidence_rows) != 1:
        raise StaticFlowAdapterError(f"expected one graph evidence row {static_flow_evidence_ref!r}")
    evidence = evidence_rows[0]
    if evidence.get("hash_algorithm") != "sha256":
        raise StaticFlowAdapterError("static-flow JSON evidence must use sha256")
    expected_doc_sha = static_flow_document_sha256(document)
    if str(evidence.get("source_hash", "")).lower() != expected_doc_sha:
        raise StaticFlowAdapterError("static-flow JSON evidence hash does not match the document")
    if not evidence.get("source_path"):
        raise StaticFlowAdapterError("static-flow JSON evidence requires source_path")

    matches = [
        row for row in document["calls"]
        if row.get("target_ea") == target_ea and row.get("reader_pc") == call_pc
    ]
    if len(matches) != 1:
        raise StaticFlowAdapterError(
            f"expected one per-call row for target 0x{target_ea:X} at PC 0x{call_pc:X}; found {len(matches)}"
        )
    selected = matches[0]
    if selected.get("helper_ea") != helper_ea:
        raise StaticFlowAdapterError(
            f"per-call helper {selected.get('helper_symbol')!r} does not match graph helper EA 0x{helper_ea:X}"
        )

    call_validation = document.get("call_site_validation")
    if call_validation is not None:
        validation_target = _parse_ea(call_validation.get("target_ea"), "call_site_validation.target_ea")
        validation_pc = _parse_ea(call_validation.get("reader_pc"), "call_site_validation.reader_pc")
        if validation_target != target_ea or validation_pc != call_pc:
            raise StaticFlowAdapterError("call_site_validation target/call PC does not match graph.call_ref")

    out = copy.deepcopy(dict(graph))
    source_listing_ref = "ev:static-flow-stage16-listing"
    listing_evidence = {
        "evidence_id": source_listing_ref,
        "source_path": document["source_listing_path"],
        "hash_algorithm": "sha256",
        "source_hash": listing_sha,
        "anchor": "Stage-16 listing identity used to produce this static per-call flow document",
        "evidence_class": "target_disassembly_listing",
        "extraction_method": "Listing member SHA-256 supplied by the pinned reader_trace_listing_source extraction; this adapter does not decode instructions",
        "status": "identity_pinned_not_instruction_redecoded",
    }
    existing_listing = [
        row for row in out.get("evidence", [])
        if isinstance(row, Mapping) and row.get("evidence_id") == source_listing_ref
    ]
    if existing_listing and existing_listing[0] != listing_evidence:
        raise StaticFlowAdapterError("conflicting Stage-16 listing evidence already exists")
    if not existing_listing:
        out["evidence"].append(listing_evidence)
    out["coverage"]["source_listing_sha256"] = listing_sha
    # This is an identity/provenance link only, not a new instruction decode.
    out["coverage"]["independent_redecode_performed"] = bool(
        out["coverage"].get("independent_redecode_performed", False)
    )

    resolved_boundary_ids = []
    if (
        call_validation is not None
        and target_ea == 0x10F8A
        and call_pc == 0x648D8
    ):
        prior_resolved = [
            row for row in out.get("resolved_boundaries", [])
            if row.get("boundary_id") == "listing-provenance-10f8a"
        ]
        for row in prior_resolved:
            if (
                str(row.get("source_listing_sha256", "")).lower() != listing_sha
                or row.get("static_flow_evidence_ref") != static_flow_evidence_ref
            ):
                raise StaticFlowAdapterError("conflicting prior resolution for listing-provenance-10f8a")
            resolved_boundary_ids.append("listing-provenance-10f8a")
        retained_boundaries = []
        for boundary in out.get("unresolved_boundaries", []):
            if boundary.get("boundary_id") == "listing-provenance-10f8a":
                node = next(
                    (item for item in out.get("nodes", []) if item.get("node_id") == boundary.get("at_node")),
                    None,
                )
                address = node.get("address") if isinstance(node, Mapping) else None
                value = address.get("value") if isinstance(address, Mapping) else None
                try:
                    node_pc = int(value, 0) if isinstance(value, str) else int(value)
                except (TypeError, ValueError):
                    node_pc = None
                if node_pc == call_pc:
                    resolved_boundary_ids.append(boundary["boundary_id"])
                    out.setdefault("resolved_boundaries", []).append({
                        "boundary_id": boundary["boundary_id"],
                        "at_node": boundary["at_node"],
                        "resolution": (
                            "Pinned Stage-16 archive/member identity, parsed the exact listing CODE row "
                            "with ROM-byte concordance, and verified the graph's exact indirect-JSR call PC."
                        ),
                        "source_listing_sha256": listing_sha,
                        "static_flow_evidence_ref": static_flow_evidence_ref,
                        "evidence_refs": [static_flow_evidence_ref, source_listing_ref],
                        "independent_redecode_performed": False,
                    })
                    continue
            retained_boundaries.append(boundary)
        out["unresolved_boundaries"] = retained_boundaries

    call_node = _call_node_id(out, call_pc, helper_ea)
    if not any(node.get("node_id") == call_node for node in out["nodes"]):
        _append_node(out, {
            "node_id": call_node,
            "kind": "code_site",
            "label": f"Static-flow call site 0x{call_pc:X}",
            "address": {"space": "rom_ea", "value": call_pc},
            "confidence": "medium",
            "evidence_refs": [static_flow_evidence_ref, source_listing_ref],
            "properties": {"function": selected["function"], "helper_symbol": selected["helper_symbol"]},
        })

    for index, query in enumerate(selected["q_inputs"]):
        if not isinstance(query, str):
            _append_boundary(out, {
                "boundary_id": f"static-flow-query-unparsed-{target_ea:08X}-{call_pc:08X}-{index}",
                "at_node": call_node,
                "reason": "Per-call tracker query origin is not text and was not interpreted.",
                "required_evidence": "A recognized raw rN<-FFFFxxxx query-origin token from the per-call static tracker.",
            })
            continue
        match = _QUERY_RE.fullmatch(query.strip())
        if not match:
            _append_boundary(out, {
                "boundary_id": f"static-flow-query-unparsed-{target_ea:08X}-{call_pc:08X}-{index}",
                "at_node": call_node,
                "reason": f"Per-call tracker query origin is not recognized: {query}",
                "required_evidence": "Inspect the original tracker token and preserve its exact register/RAM origin before interpretation.",
            })
            continue
        reg = int(match.group("reg"))
        ram = int(match.group("ea"), 16)
        ram_node = f"static-flow-query-ram-{ram:08X}"
        reg_node = f"static-flow-query-r{reg}-{call_pc:08X}"
        _append_node(out, {
            "node_id": ram_node,
            "kind": "ram_cell",
            "label": f"Per-call query source FFFF{ram & 0xFFFF:04X}",
            "address": {"space": "ram_ea", "value": f"0x{ram:08X}"},
            "confidence": "medium",
            "evidence_refs": [static_flow_evidence_ref, source_listing_ref],
            "properties": {"role": "query_origin_from_per_call_tracker"},
        })
        _append_node(out, {
            "node_id": reg_node,
            "kind": "register",
            "label": f"R{reg} per-call query origin at 0x{call_pc:X}",
            "address": None,
            "confidence": "medium",
            "evidence_refs": [static_flow_evidence_ref],
            "properties": {"register": f"R{reg}", "origin_ram": f"0x{ram:08X}", "transform_unresolved": True},
        })
        _append_edge(out, {
            "edge_id": f"static-flow-query-load-{target_ea:08X}-{call_pc:08X}-{reg}-{ram:08X}",
            "from_node": ram_node,
            "to_node": reg_node,
            "relation": f"RAM_origin_for_R{reg}_reported_by_per_call_tracker",
            "basis": "derived",
            "confidence": "medium",
            "evidence_refs": [static_flow_evidence_ref, source_listing_ref],
        })
        _append_edge(out, {
            "edge_id": f"static-flow-query-arg-{target_ea:08X}-{call_pc:08X}-{reg}-{ram:08X}",
            "from_node": reg_node,
            "to_node": call_node,
            "relation": f"R{reg}_query_origin_at_exact_lookup_call",
            "basis": "derived",
            "confidence": "medium",
            "evidence_refs": [static_flow_evidence_ref, source_listing_ref],
        })

    for index, destination in enumerate(selected["dests"]):
        ea = int(destination["ram_ea"])
        width = destination["width"]
        pc = int(destination["write_pc"])
        tainted = bool(destination["is_tainted"])
        source_register = _store_source_register(destination["instruction"]) if tainted else None
        store_node = f"static-flow-store-{pc:08X}-{ea:08X}"
        ram_node = f"static-flow-dest-ram-{ea:08X}"
        _append_node(out, {
            "node_id": store_node,
            "kind": "code_site",
            "label": f"Static-flow RAM store {width} to 0x{ea:08X} at 0x{pc:X}",
            "address": {"space": "rom_ea", "value": pc},
            "confidence": "medium" if tainted else "low",
            "evidence_refs": [static_flow_evidence_ref, source_listing_ref],
            "properties": {
                "function": selected["function"],
                "instruction": destination["instruction"],
                "width": width,
                "taint_class": "taint" if tainted else "near",
                "source_register": source_register.upper() if source_register else None,
            },
        })
        _append_node(out, {
            "node_id": ram_node,
            "kind": "ram_cell",
            "label": f"Static-flow destination RAM 0x{ea:08X}",
            "address": {"space": "ram_ea", "value": f"0x{ea:08X}"},
            "confidence": "medium" if tainted else "low",
            "evidence_refs": [static_flow_evidence_ref],
            "properties": {"role": "per_call_lookup_result_destination", "width": width},
        })
        if tainted:
            if source_register is None:
                _append_boundary(out, {
                    "boundary_id": f"static-flow-tainted-source-unparsed-{target_ea:08X}-{call_pc:08X}-{pc:08X}-{index}",
                    "at_node": store_node,
                    "reason": (
                        "The existing static tracker marks this store value as lookup-tainted, "
                        "but the instruction text does not expose a recognized MOV source register."
                    ),
                    "required_evidence": (
                        "A byte-concordant store instruction and exact source-register operand; "
                        "do not substitute R0 or another assumed return register."
                    ),
                })
            else:
                source_node = (
                    f"static-flow-store-source-{source_register}-"
                    f"{target_ea:08X}-{call_pc:08X}"
                )
                _append_node(out, {
                    "node_id": source_node,
                    "kind": "register",
                    "label": f"{source_register.upper()} tainted store source for exact lookup call 0x{call_pc:X}",
                    "address": None,
                    "confidence": "medium",
                    "evidence_refs": [static_flow_evidence_ref, source_listing_ref],
                    "properties": {
                        "register": source_register.upper(),
                        "target_ea": f"0x{target_ea:08X}",
                        "call_pc": f"0x{call_pc:X}",
                        "taint_proven_by_static_tracker": True,
                        "intermediate_copy_transform_path_reconstructed": False,
                    },
                })
                _append_edge(out, {
                    "edge_id": f"static-flow-result-taint-{source_register}-{target_ea:08X}-{call_pc:08X}",
                    "from_node": call_node,
                    "to_node": source_node,
                    "relation": (
                        f"lookup_result_taint_reaches_{source_register.upper()}_"
                        "store_source_per_static_tracker"
                    ),
                    "basis": "derived",
                    "confidence": "medium",
                    "evidence_refs": [static_flow_evidence_ref],
                })
                _append_edge(out, {
                    "edge_id": (
                        f"static-flow-tainted-store-{source_register}-"
                        f"{target_ea:08X}-{call_pc:08X}-{pc:08X}-{index}"
                    ),
                    "from_node": source_node,
                    "to_node": store_node,
                    "relation": "tainted_store_source_register_used_by_store_instruction",
                    "basis": "derived",
                    "confidence": "medium",
                    "evidence_refs": [static_flow_evidence_ref, source_listing_ref],
                })
        else:
            _append_edge(out, {
                "edge_id": f"static-flow-near-store-{target_ea:08X}-{call_pc:08X}-{pc:08X}-{index}",
                "from_node": call_node,
                "to_node": store_node,
                "relation": "near_call_RAM_write_candidate_without_result_taint",
                "basis": "heuristic",
                "confidence": "low",
                "evidence_refs": [static_flow_evidence_ref],
            })
            _append_boundary(out, {
                "boundary_id": f"static-flow-near-boundary-{target_ea:08X}-{call_pc:08X}-{pc:08X}-{index}",
                "at_node": store_node,
                "reason": "The existing tracker classified this write as near-call, not lookup-result-tainted; the adapter does not promote it to a result store.",
                "required_evidence": "A path-sensitive value-flow trace proving the lookup return reaches this RAM write.",
            })
        _append_edge(out, {
            "edge_id": f"static-flow-store-target-{target_ea:08X}-{call_pc:08X}-{pc:08X}-{index}",
            "from_node": store_node,
            "to_node": ram_node,
            "relation": "static_tracker_store_targets_RAM_cell",
            "basis": "derived",
            "confidence": "medium" if tainted else "low",
            "evidence_refs": [static_flow_evidence_ref, source_listing_ref],
        })

    extension_id = f"per-call-static-flow-{target_ea:08X}-{call_pc:08X}"
    extension = {
        "extension_id": extension_id,
        "adapter": "reader-trace-static-flow-adapter-v0.1",
        "target_ea": f"0x{target_ea:08X}",
        "call_pc": f"0x{call_pc:X}",
        "helper_ea": f"0x{helper_ea:X}",
        "helper_symbol": selected["helper_symbol"],
        "function": selected["function"],
        "evidence_ref": static_flow_evidence_ref,
        "source_listing_sha256": listing_sha,
        "instruction_decode_performed": False,
        "semantics_promoted": False,
    }
    if resolved_boundary_ids:
        extension["resolved_boundary_ids"] = resolved_boundary_ids
    extensions = out.setdefault("analysis_extensions", [])
    old = [item for item in extensions if item.get("extension_id") == extension_id]
    if old and old[0] != extension:
        raise StaticFlowAdapterError("conflicting per-call static-flow extension already exists")
    if not old:
        extensions.append(extension)

    for boundary in out.get("unresolved_boundaries", []):
        if boundary.get("boundary_id") == f"multiple-reader-sites-{target_ea:08X}":
            boundary["reason"] = (
                f"The per-address summary aggregates reader calls. Exact per-call static flow is attached "
                f"for 0x{call_pc:X}; the remaining call-site query/result paths are still unattributed."
            )
            boundary["required_evidence"] = (
                "A separate exact per-call static-flow document for each additional reader PC."
            )
    return out
