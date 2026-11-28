#!/usr/bin/env python3
"""Read-only validator/serializer for SH705x Reader Trace Graph v0.1.

This is an additive extension to sh705x-datamodel-v1.0.0. It does not decode
SH-2 instructions or replace the existing scanner/indexer. Stdlib only.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any, List, Mapping

SCHEMA_VERSION = "sh705x-reader-trace-graph-v0.1"
DATA_MODEL_VERSION = "sh705x-datamodel-v1.0.0"
NODE_KINDS = {
    "rom_object", "rom_literal_pool", "code_site", "lookup_helper",
    "ram_cell", "register", "branch_condition", "consumer",
    "unresolved_boundary",
}
EDGE_BASES = {
    "direct_observation", "reported_observation", "derived",
    "heuristic", "unresolved",
}
CONFIDENCE = {"high", "medium", "low", "unknown"}
HASH_LENGTHS = {"sha256": 64, "git_blob_sha1": 40}


class TraceValidationError(ValueError):
    """Reader trace graph contract violation."""


def _fail(message: str) -> None:
    raise TraceValidationError(message)


def _hex_digest(value: Any, length: int) -> bool:
    return (
        isinstance(value, str)
        and len(value) == length
        and re.fullmatch(r"[0-9a-fA-F]+", value) is not None
    )


def validate_trace_graph(document: Mapping[str, Any]) -> List[str]:
    """Validate graph structure/provenance; return non-fatal reconciliation warnings."""
    if not isinstance(document, Mapping):
        _fail("trace graph must be a JSON object")
    warnings: List[str] = []
    required = {
        "schema_version", "data_model_version", "trace_id", "artifact",
        "target_object", "call_ref", "nodes", "edges", "evidence",
        "lookup_contract", "unresolved_boundaries", "coverage",
        "semantic_disposition",
    }
    missing = sorted(required - set(document))
    if missing:
        _fail("missing top-level fields: " + ", ".join(missing))
    if document["schema_version"] != SCHEMA_VERSION:
        _fail("unsupported schema_version")
    if document["data_model_version"] != DATA_MODEL_VERSION:
        _fail("unsupported data_model_version")
    if not isinstance(document["trace_id"], str) or not document["trace_id"].strip():
        _fail("trace_id must be non-empty")

    artifact = document["artifact"]
    if not isinstance(artifact, Mapping):
        _fail("artifact must be an object")
    if artifact.get("processor_family") not in {"SH7055", "SH7058"}:
        _fail("artifact.processor_family must be SH7055 or SH7058")
    if not _hex_digest(artifact.get("decoded_sha256"), 64):
        _fail("artifact.decoded_sha256 must be SHA-256")
    if not artifact.get("artifact_id") or not artifact.get("source_path"):
        _fail("artifact_id and source_path are required")
    if artifact.get("md5") is not None and not _hex_digest(artifact["md5"], 32):
        _fail("artifact.md5 must be 32 hexadecimal characters")

    call = document["call_ref"]
    if not isinstance(call, Mapping):
        _fail("call_ref must be an object")
    if not isinstance(call.get("call_id"), str) or not call["call_id"].strip():
        _fail("call_ref.call_id is required")
    for key in ("call_pc", "helper_ea"):
        if not isinstance(call.get(key), int) or call[key] < 0:
            _fail(f"call_ref.{key} must be a non-negative integer")
    if not isinstance(call.get("call_form"), str) or not call["call_form"].strip():
        _fail("call_ref.call_form is required")

    target = document["target_object"]
    if not isinstance(target, Mapping):
        _fail("target_object must be an object")
    if not isinstance(target.get("ea"), int) or target["ea"] < 0:
        _fail("target_object.ea must be a non-negative integer")
    extent = target.get("byte_extent")
    dims = target.get("dimensions")
    widths = {"uint8": 1, "int8": 1, "uint16": 2, "int16": 2, "uint32": 4, "int32": 4}
    storage = target.get("storage_type")
    if not isinstance(extent, int) or extent <= 0:
        _fail("target_object.byte_extent must be positive")
    if not isinstance(dims, list) or len(dims) not in (1, 2, 3):
        _fail("target_object.dimensions must be a one-to-three element list")
    if any(not isinstance(n, int) or n <= 0 for n in dims):
        _fail("target_object dimensions must be positive integers")
    if storage not in widths:
        _fail("target_object.storage_type is unsupported")
    expected_extent = widths[storage]
    for n in dims:
        expected_extent *= n
    if extent != expected_extent:
        _fail(f"target_object extent mismatch: expected {expected_extent}, got {extent}")
    payload_sha = target.get("payload_sha256")
    if not _hex_digest(payload_sha, 64):
        _fail("target_object.payload_sha256 must be SHA-256")
    payload_hex = target.get("payload_hex")
    if payload_hex is not None:
        if not isinstance(payload_hex, str):
            _fail("target_object.payload_hex must be a string")
        try:
            payload = bytes.fromhex(payload_hex)
        except ValueError as exc:
            _fail(f"target_object.payload_hex invalid: {exc}")
        if len(payload) != extent:
            _fail(f"payload length mismatch: expected {extent}, got {len(payload)}")
        if hashlib.sha256(payload).hexdigest() != payload_sha.lower():
            _fail("payload_hex does not match payload_sha256")

    evidence = document["evidence"]
    if not isinstance(evidence, list) or not evidence:
        _fail("evidence must be a non-empty list")
    evidence_ids = set()
    for i, ev in enumerate(evidence):
        if not isinstance(ev, Mapping):
            _fail(f"evidence[{i}] must be an object")
        ev_id = ev.get("evidence_id")
        if not isinstance(ev_id, str) or not ev_id.strip() or ev_id in evidence_ids:
            _fail(f"evidence[{i}] requires a unique evidence_id")
        evidence_ids.add(ev_id)
        algorithm = ev.get("hash_algorithm")
        digest_len = HASH_LENGTHS.get(algorithm)
        if digest_len is None or not _hex_digest(ev.get("source_hash"), digest_len):
            _fail(f"evidence[{i}] has invalid explicit hash algorithm/digest")
        for key in ("source_path", "anchor", "evidence_class", "status", "extraction_method"):
            if not ev.get(key):
                _fail(f"evidence[{i}].{key} is required")

    nodes = document["nodes"]
    if not isinstance(nodes, list) or not nodes:
        _fail("nodes must be a non-empty list")
    node_ids = set()
    for i, node in enumerate(nodes):
        if not isinstance(node, Mapping):
            _fail(f"nodes[{i}] must be an object")
        node_id = node.get("node_id")
        if not isinstance(node_id, str) or not node_id.strip() or node_id in node_ids:
            _fail(f"nodes[{i}] requires a unique node_id")
        node_ids.add(node_id)
        if node.get("kind") not in NODE_KINDS:
            _fail(f"nodes[{i}] has invalid kind")
        refs = node.get("evidence_refs", [])
        if not isinstance(refs, list) or any(ref not in evidence_ids for ref in refs):
            _fail(f"nodes[{i}] contains unknown evidence_refs")
        if node.get("confidence", "unknown") not in CONFIDENCE:
            _fail(f"nodes[{i}] has invalid confidence")

    edges = document["edges"]
    if not isinstance(edges, list) or not edges:
        _fail("edges must be a non-empty list")
    edge_ids = set()
    for i, edge in enumerate(edges):
        if not isinstance(edge, Mapping):
            _fail(f"edges[{i}] must be an object")
        edge_id = edge.get("edge_id")
        if not isinstance(edge_id, str) or not edge_id.strip() or edge_id in edge_ids:
            _fail(f"edges[{i}] requires a unique edge_id")
        edge_ids.add(edge_id)
        if edge.get("from_node") not in node_ids or edge.get("to_node") not in node_ids:
            _fail(f"edges[{i}] has an unknown endpoint")
        if not isinstance(edge.get("relation"), str) or not edge["relation"].strip():
            _fail(f"edges[{i}].relation is required")
        if edge.get("basis") not in EDGE_BASES:
            _fail(f"edges[{i}] has invalid basis")
        if edge.get("confidence", "unknown") not in CONFIDENCE:
            _fail(f"edges[{i}] has invalid confidence")
        refs = edge.get("evidence_refs", [])
        if not isinstance(refs, list) or any(ref not in evidence_ids for ref in refs):
            _fail(f"edges[{i}] contains unknown evidence_refs")
        if edge["basis"] != "unresolved" and not refs:
            _fail(f"edges[{i}] asserted relationship requires evidence_refs")

    boundaries = document["unresolved_boundaries"]
    if not isinstance(boundaries, list):
        _fail("unresolved_boundaries must be a list")
    boundary_ids = set()
    for i, boundary in enumerate(boundaries):
        if not isinstance(boundary, Mapping):
            _fail(f"unresolved_boundaries[{i}] must be an object")
        bid = boundary.get("boundary_id")
        if not isinstance(bid, str) or not bid.strip() or bid in boundary_ids:
            _fail(f"unresolved_boundaries[{i}] requires a unique boundary_id")
        boundary_ids.add(bid)
        if boundary.get("at_node") is not None and boundary["at_node"] not in node_ids:
            _fail(f"unresolved_boundaries[{i}] has an unknown at_node")
        if not boundary.get("reason") or not boundary.get("required_evidence"):
            _fail(f"unresolved_boundaries[{i}] requires reason and required_evidence")

    lookup = document["lookup_contract"]
    if not isinstance(lookup, Mapping):
        _fail("lookup_contract must be an object")
    if lookup.get("query_source_node") not in node_ids or lookup.get("helper_node") not in node_ids:
        _fail("lookup_contract references unknown query/helper nodes")
    for key in ("query_type", "axis_model", "interpolation", "upper_boundary"):
        if key not in lookup:
            _fail(f"lookup_contract.{key} is required")
    axis = lookup["axis_model"]
    if isinstance(axis, Mapping):
        start, step, count = axis.get("start"), axis.get("step"), axis.get("point_count")
        reported_last = axis.get("reported_last_coordinate")
        if all(isinstance(x, int) for x in (start, step, count)) and count > 0:
            derived = start + step * (count - 1)
            if reported_last is not None and reported_last != derived:
                warnings.append(
                    f"implicit-grid endpoint conflict: reported {reported_last}, derived {derived}; retain unresolved"
                )

    coverage = document["coverage"]
    if not isinstance(coverage, Mapping) or not coverage.get("start") or not coverage.get("stop"):
        _fail("coverage.start and coverage.stop are required")
    listing_hash = coverage.get("source_listing_sha256")
    if listing_hash is not None and not _hex_digest(listing_hash, 64):
        _fail("coverage.source_listing_sha256 must be SHA-256 or null")
    if not isinstance(coverage.get("independent_redecode_performed"), bool):
        _fail("coverage.independent_redecode_performed must be boolean")

    semantic = document["semantic_disposition"]
    if not isinstance(semantic, Mapping):
        _fail("semantic_disposition must be an object")
    for key in ("physical_identity", "promotion", "evidence_grade"):
        if not isinstance(semantic.get(key), str) or not semantic[key].strip():
            _fail(f"semantic_disposition.{key} is required")
    if semantic["physical_identity"] == "unresolved" and semantic["promotion"] not in {"not_supported", "deferred"}:
        warnings.append("physical identity unresolved but promotion is not withheld")
    return warnings


def canonical_json(document: Mapping[str, Any]) -> str:
    validate_trace_graph(document)
    return json.dumps(document, sort_keys=True, indent=2, ensure_ascii=False) + "\n"


def trace_sha256(document: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json(document).encode("utf-8")).hexdigest()


def write_trace_graph(path: os.PathLike[str] | str, document: Mapping[str, Any]) -> str:
    """Validate and atomically write deterministic JSON; return file SHA-256."""
    destination = Path(path)
    text = canonical_json(document)
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{destination.name}.", suffix=".tmp", dir=str(destination.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
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
