#!/usr/bin/env python3
"""Single-entry composition for the additive SH705x Reader Trace pipeline.

This module orchestrates existing indexes, optional per-call static-flow
records, exact helper profiles and graph validation. It does not decode SH-2
instructions.
"""
from __future__ import annotations

import copy
from typing import Any, Dict, Mapping, Sequence

from reader_trace_graph import validate_trace_graph
from reader_trace_helper_profiles import attach_helper_profile
from reader_trace_indexer_adapter import merge_indexed_reader_evidence
from reader_trace_static_flow_adapter import merge_per_call_static_flow


def enrich_reader_trace(
    graph: Mapping[str, Any],
    hit_rows: Sequence[Any],
    catalogue_summary: Mapping[str, Any],
    *,
    indexer_evidence_ref: str,
    static_index_evidence_ref: str,
    concordance_matched: int,
    concordance_checked: int,
    per_call_static_flow_document: Mapping[str, Any] | None = None,
    per_call_static_flow_evidence_ref: str | None = None,
) -> Dict[str, Any]:
    """Merge validated index evidence and optionally exact per-call flow evidence.

    When a per-call document is supplied, aggregate query/result fields are
    deliberately withheld from the per-address summary adapter. The raw
    per-call record is then attached only to graph.call_ref's exact target EA,
    call PC and helper EA. Downstream reads remain observations, not causal
    proof. Unknown helper EAs remain unprofiled.

    Returns the enriched graph, warnings, profile/decode/promotion flags and
    whether a per-call static-flow record was attached.
    """
    has_static_document = per_call_static_flow_document is not None
    if has_static_document != (per_call_static_flow_evidence_ref is not None):
        raise ValueError(
            "per_call_static_flow_document and per_call_static_flow_evidence_ref must be supplied together"
        )

    summary_for_indexer = copy.deepcopy(dict(catalogue_summary))
    if has_static_document:
        # Do not duplicate or distribute aggregate query/store values when
        # the exact per-call tracker record is available.
        summary_for_indexer["traced_query_inputs"] = "-"
        summary_for_indexer["traced_dest_ram"] = "-"

    indexed = merge_indexed_reader_evidence(
        graph,
        hit_rows,
        summary_for_indexer,
        indexer_evidence_ref=indexer_evidence_ref,
        static_index_evidence_ref=static_index_evidence_ref,
        concordance_matched=concordance_matched,
        concordance_checked=concordance_checked,
    )
    profiled = attach_helper_profile(indexed)
    if has_static_document:
        profiled = merge_per_call_static_flow(
            profiled,
            per_call_static_flow_document,
            static_flow_evidence_ref=per_call_static_flow_evidence_ref,
        )
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
    if has_static_document:
        pipeline_record["per_call_static_flow_attached"] = True
        pipeline_record["per_call_static_flow_evidence_ref"] = per_call_static_flow_evidence_ref
    existing = [item for item in extensions if item.get("extension_id") == run_id]
    if existing and existing[0] != pipeline_record:
        raise ValueError("conflicting reader-trace pipeline run record already exists")
    if not existing:
        extensions.append(pipeline_record)

    warnings = validate_trace_graph(profiled)
    return {
        "graph": profiled,
        "warnings": warnings,
        "helper_profile_attached": attached,
        "per_call_static_flow_attached": has_static_document,
        "instruction_decode_performed": False,
        "semantics_promoted": False,
    }
