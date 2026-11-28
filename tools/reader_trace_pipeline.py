#!/usr/bin/env python3
"""Single-entry composition for the additive SH705x Reader Trace pipeline.

This module orchestrates existing index outputs, graph validation and exact
helper-profile attachment. It does not decode SH-2 instructions.
"""
from __future__ import annotations

import copy
from typing import Any, Dict, Mapping, Sequence

from reader_trace_graph import validate_trace_graph
from reader_trace_helper_profiles import attach_helper_profile
from reader_trace_indexer_adapter import merge_indexed_reader_evidence


def enrich_reader_trace(
    graph: Mapping[str, Any],
    hit_rows: Sequence[Any],
    catalogue_summary: Mapping[str, Any],
    *,
    indexer_evidence_ref: str,
    static_index_evidence_ref: str,
    concordance_matched: int,
    concordance_checked: int,
) -> Dict[str, Any]:
    """Merge existing index evidence, attach exact profile if pinned, validate.

    Returns a mapping with:
      graph: enriched graph (input graph is never mutated)
      warnings: non-fatal core graph validation warnings
      helper_profile_attached: whether an exact image+CPU+EA profile matched

    Unknown helper EAs are valid and remain without a helper profile.
    """
    indexed = merge_indexed_reader_evidence(
        graph,
        hit_rows,
        catalogue_summary,
        indexer_evidence_ref=indexer_evidence_ref,
        static_index_evidence_ref=static_index_evidence_ref,
        concordance_matched=concordance_matched,
        concordance_checked=concordance_checked,
    )
    profiled = attach_helper_profile(indexed)
    warnings = validate_trace_graph(profiled)

    call = profiled.get("call_ref", {})
    helper_ea = call.get("helper_ea")
    helper_id = None
    for node in profiled.get("nodes", []):
        address = node.get("address")
        if (
            node.get("kind") == "lookup_helper"
            and isinstance(address, Mapping)
            and address.get("value") == helper_ea
        ):
            helper_id = node.get("node_id")
            break
    attached = False
    if helper_id is not None:
        helper = next(node for node in profiled["nodes"] if node.get("node_id") == helper_id)
        attached = bool(helper.get("properties", {}).get("recognized_profile"))

    extensions = profiled.setdefault("analysis_extensions", [])
    run_id = "reader-trace-pipeline-v0.1"
    pipeline_record = {
        "extension_id": run_id,
        "adapter": "reader-trace-pipeline-v0.1",
        "indexer_evidence_ref": indexer_evidence_ref,
        "static_index_evidence_ref": static_index_evidence_ref,
        "pc_concordance": {
            "matched": concordance_matched,
            "checked": concordance_checked,
        },
        "helper_profile_attached": attached,
        "semantics_promoted": False,
        "instruction_decode_performed": False,
    }
    existing = [item for item in extensions if item.get("extension_id") == run_id]
    if existing and existing[0] != pipeline_record:
        raise ValueError("conflicting reader-trace pipeline run record already exists")
    if not existing:
        extensions.append(pipeline_record)

    # Validate after adding the pipeline status record as a final postcondition.
    warnings = validate_trace_graph(profiled)
    return {
        "graph": profiled,
        "warnings": warnings,
        "helper_profile_attached": attached,
        "instruction_decode_performed": False,
        "semantics_promoted": False,
    }
