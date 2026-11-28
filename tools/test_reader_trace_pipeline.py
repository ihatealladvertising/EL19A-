#!/usr/bin/env python3
"""Synthetic tests for the composed Reader Trace enrichment pipeline."""
from __future__ import annotations

import copy
import json
import pathlib
import sys
import unittest

TOOLS_DIR = pathlib.Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from reader_trace_pipeline import enrich_reader_trace
from reader_trace_static_flow_adapter import (
    build_static_flow_call_document,
    static_flow_document_sha256,
)

REPO_ROOT = TOOLS_DIR.parent
FIXTURES = REPO_ROOT / "EVIDENCE" / "READER_TRACE_V0_1"


def fixture(name):
    graph = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    graph["evidence"].extend([
        {
            "evidence_id": "ev:indexer",
            "source_path": "INDEX/rom_access_hits.tsv",
            "hash_algorithm": "sha256",
            "source_hash": "1" * 64,
            "anchor": "Target PC concordance row in synthetic pipeline test",
            "evidence_class": "byte_concordant_access_index",
            "extraction_method": "Existing rom_access_indexer valid_hits output",
            "status": "synthetic_test_input",
        },
        {
            "evidence_id": "ev:static-index",
            "source_path": "INDEX/rom_catalog_trace_summary.tsv",
            "hash_algorithm": "sha256",
            "source_hash": "2" * 64,
            "anchor": "Target per-address static summary row in synthetic pipeline test",
            "evidence_class": "static_register_and_ram_flow_summary",
            "extraction_method": "Existing build_static_indices output",
            "status": "synthetic_test_input",
        },
    ])
    return graph


def common_call(graph):
    call = graph["call_ref"]["call_pc"]
    target = graph["target_object"]["ea"]
    helper = graph["call_ref"]["helper_ea"]
    return call, target, helper


def run_pipeline(graph, *, target, helper=None, query_register="R5", query_ram="FFFF84B8", per_call_static_flow=False):
    call, _, existing_helper = common_call(graph)
    if helper is None:
        helper = existing_helper
    graph["call_ref"]["helper_ea"] = helper
    hit = {
        "target": f"0x{target:X}",
        "space": "rom",
        "pc": f"0x{call:X}",
        "function": "synthetic_function",
        "access": "read",
        "width": "b",
        "form": "pool",
        "base": f"0x{target:X}",
        "base_resolved": "full",
        "mask": "-",
        "note": "synthetic byte-concordant reader hit",
    }
    summary = {
        "address": f"0x{target:X}",
        "traced_reader_sites": f"0x{call:X}(synthetic_function:helper)",
        "traced_query_inputs": f"{query_register.lower()}<-{query_ram}",
        "traced_dest_ram": "FFFF29F6:b@85B34(taint)",
        "dest_downstream_sample": "FFFF29F6@85B4A(synthetic_consumer)",
    }
    flow_document = None
    flow_evidence_ref = None
    if per_call_static_flow:
        flow_document = build_static_flow_call_document(
            {
                target: [{
                    "reader_pc": call,
                    "func": "synthetic_function",
                    "helper": f"sub_{helper:X}",
                    "q_inputs": [f"{query_register.lower()}<-{query_ram}"],
                    "dests": [(0xFFFF29F6, "b", 0x85B34, "mov.b r0,@r9", True)],
                }]
            },
            artifact_sha256=graph["artifact"]["decoded_sha256"],
            source_listing_sha256="148385bbec91f6a491dcaa403962836f709c2f273df9a17ec51f1dea5f7f4549",
            source_listing_path="synthetic-stage16.lst",
        )
        flow_evidence_ref = "ev:per-call-static-flow"
        graph["evidence"].append({
            "evidence_id": flow_evidence_ref,
            "source_path": "EVIDENCE/READER_TRACE_V0_1/synthetic_static_flow_calls.json",
            "hash_algorithm": "sha256",
            "source_hash": static_flow_document_sha256(flow_document),
            "anchor": "Exact per-call raw cat_calls row for this graph call",
            "evidence_class": "per_call_static_reader_flow",
            "extraction_method": "Synthetic full_rom_analysis cat_calls fixture",
            "status": "synthetic_test_input",
        })
    return enrich_reader_trace(
        graph, [hit], summary,
        indexer_evidence_ref="ev:indexer",
        static_index_evidence_ref="ev:static-index",
        concordance_matched=1,
        concordance_checked=1,
        per_call_static_flow_document=flow_document,
        per_call_static_flow_evidence_ref=flow_evidence_ref,
    )


class ReaderTracePipelineTests(unittest.TestCase):
    def test_0f10e_pipeline_attaches_exact_profile_and_merges_index_evidence(self):
        graph = fixture("EL19A_F501_0F10E.reader_trace.json")
        original = copy.deepcopy(graph)
        result = run_pipeline(graph, target=0x0F10E)
        self.assertEqual(graph, original)
        self.assertTrue(result["helper_profile_attached"])
        self.assertFalse(result["instruction_decode_performed"])
        self.assertFalse(result["semantics_promoted"])
        enriched = result["graph"]
        helper = next(n for n in enriched["nodes"] if n["node_id"] == "helper-22e10")
        self.assertEqual(helper["properties"]["recognized_profile"], "EL19A-F501-sub_22E10-implicit-u8-16-v1")
        self.assertTrue(any(e["edge_id"] == "indexer-table-read-00085B2E" for e in enriched["edges"]))
        self.assertTrue(any(x["extension_id"] == "reader-trace-pipeline-v0.1" for x in enriched["analysis_extensions"]))

    def test_32_point_curve_pipeline_attaches_explicit_axis_contract(self):
        graph = fixture("EL19A_F501_10F8A_32PT_UWORD.reader_trace.json")
        result = run_pipeline(
            graph, target=0x10F8A, query_register="R6", query_ram="FFFF1064"
        )
        self.assertTrue(result["helper_profile_attached"])
        helper = next(n for n in result["graph"]["nodes"] if n["kind"] == "lookup_helper")
        self.assertEqual(helper["properties"]["mechanics"]["axis_search"]["helper"], "sub_2340C")

    def test_two_axis_map_pipeline_attaches_two_axis_contract(self):
        graph = fixture("EL19A_F501_0AFF2_2AXIS.reader_trace.json")
        result = run_pipeline(
            graph, target=0x0AFF2, query_register="R7", query_ram="FFFF85A4"
        )
        self.assertTrue(result["helper_profile_attached"])
        helper = next(n for n in result["graph"]["nodes"] if n["kind"] == "lookup_helper")
        self.assertTrue(helper["properties"]["mechanics"]["same_query_for_both_axes"])
        self.assertEqual(helper["properties"]["source_listing_sha256"], "148385bbec91f6a491dcaa403962836f709c2f273df9a17ec51f1dea5f7f4549")

    def test_unrecognized_helper_stays_unprofiled_without_failing_graph(self):
        graph = fixture("EL19A_F501_0F10E.reader_trace.json")
        result = run_pipeline(graph, target=0x0F10E, helper=0x22E11)
        self.assertFalse(result["helper_profile_attached"])
        self.assertFalse(result["instruction_decode_performed"])
        self.assertFalse(result["semantics_promoted"])
        self.assertFalse(any(
            node.get("properties", {}).get("recognized_profile")
            for node in result["graph"]["nodes"]
            if node["kind"] == "lookup_helper"
        ))

    def test_rom_sha_mismatch_prevents_profile_attach(self):
        graph = fixture("EL19A_F501_0F10E.reader_trace.json")
        graph["artifact"]["decoded_sha256"] = "0" * 64
        result = run_pipeline(graph, target=0x0F10E)
        self.assertFalse(result["helper_profile_attached"])

    def test_aggregate_multiple_readers_stay_unattributed_in_pipeline(self):
        graph = fixture("EL19A_F501_0F10E.reader_trace.json")
        call, target, _ = common_call(graph)
        hit1 = {
            "target": f"0x{target:X}", "space": "rom", "pc": f"0x{call:X}",
            "function": "one", "access": "read", "width": "b", "form": "pool",
            "base": f"0x{target:X}", "base_resolved": "full", "mask": "-", "note": "hit1",
        }
        hit2 = dict(hit1, pc="0x86000", function="two")
        summary = {
            "address": f"0x{target:X}",
            "traced_reader_sites": f"0x{call:X}(one:helper); 0x86000(two:helper)",
            "traced_query_inputs": "r5<-FFFF84B8",
            "traced_dest_ram": "FFFF29F6:b@85B34(taint)",
            "dest_downstream_sample": "-",
        }
        result = enrich_reader_trace(
            graph, [hit1, hit2], summary,
            indexer_evidence_ref="ev:indexer",
            static_index_evidence_ref="ev:static-index",
            concordance_matched=2, concordance_checked=2,
        )
        self.assertTrue(result["helper_profile_attached"])
        self.assertFalse(any(e["edge_id"].startswith("indexer-query-arg-") for e in result["graph"]["edges"]))
        self.assertFalse(any(e["edge_id"] == "indexer-result-write-0000F10E-000085B34" for e in result["graph"]["edges"]))

    def test_pipeline_attaches_exact_per_call_flow_and_withholds_aggregate_query_results(self):
        graph = fixture("EL19A_F501_0F10E.reader_trace.json")
        call, target, helper = common_call(graph)
        hit1 = {
            "target": f"0x{target:X}", "space": "rom", "pc": f"0x{call:X}",
            "function": "one", "access": "read", "width": "b", "form": "pool",
            "base": f"0x{target:X}", "base_resolved": "full", "mask": "-", "note": "hit1",
        }
        hit2 = dict(hit1, pc="0x86000", function="two")
        summary = {
            "address": f"0x{target:X}",
            "traced_reader_sites": f"0x{call:X}(one:helper); 0x86000(two:helper)",
            "traced_query_inputs": "r5<-FFFF84B8; r6<-FFFF84BA",
            "traced_dest_ram": "FFFF29F6:b@85B34(taint); FFFF2910:b@86008(taint)",
            "dest_downstream_sample": "-",
        }
        document = build_static_flow_call_document(
            {
                target: [
                    {
                        "reader_pc": call, "func": "one", "helper": f"sub_{helper:X}",
                        "q_inputs": ["r5<-FFFF84B8"],
                        "dests": [(0xFFFF29F6, "b", 0x85B34, "mov.b r0,@r9", True)],
                    },
                    {
                        "reader_pc": 0x86000, "func": "two", "helper": f"sub_{helper:X}",
                        "q_inputs": ["r6<-FFFF84BA"],
                        "dests": [(0xFFFF2910, "b", 0x86008, "mov.b r0,@r8", True)],
                    },
                ]
            },
            artifact_sha256=graph["artifact"]["decoded_sha256"],
            source_listing_sha256="148385bbec91f6a491dcaa403962836f709c2f273df9a17ec51f1dea5f7f4549",
            source_listing_path="synthetic-stage16.lst",
        )
        graph["evidence"].append({
            "evidence_id": "ev:per-call-static-flow",
            "source_path": "EVIDENCE/READER_TRACE_V0_1/synthetic_static_flow_calls.json",
            "hash_algorithm": "sha256",
            "source_hash": static_flow_document_sha256(document),
            "anchor": "Two raw per-call tracker rows for one target, including the selected call",
            "evidence_class": "per_call_static_reader_flow",
            "extraction_method": "Synthetic full_rom_analysis cat_calls fixture",
            "status": "synthetic_test_input",
        })
        result = enrich_reader_trace(
            graph, [hit1, hit2], summary,
            indexer_evidence_ref="ev:indexer",
            static_index_evidence_ref="ev:static-index",
            concordance_matched=2, concordance_checked=2,
            per_call_static_flow_document=document,
            per_call_static_flow_evidence_ref="ev:per-call-static-flow",
        )
        self.assertTrue(result["per_call_static_flow_attached"])
        self.assertFalse(any(
            edge["edge_id"].startswith("indexer-query-arg-")
            or edge["edge_id"].startswith("indexer-result-write-")
            for edge in result["graph"]["edges"]
        ))
        self.assertTrue(any(
            edge["edge_id"] == f"static-flow-query-arg-{target:08X}-{call:08X}-5-FFFF84B8"
            for edge in result["graph"]["edges"]
        ))
        self.assertFalse(any(
            "000086000" in edge["edge_id"]
            for edge in result["graph"]["edges"]
            if edge["edge_id"].startswith("static-flow-")
        ))
        boundary = next(
            item for item in result["graph"]["unresolved_boundaries"]
            if item["boundary_id"] == f"multiple-reader-sites-{target:08X}"
        )
        self.assertIn("Exact per-call static flow is attached", boundary["reason"])
        self.assertFalse(result["instruction_decode_performed"])
        self.assertFalse(result["semantics_promoted"])

    def test_pipeline_is_deterministic_for_identical_inputs(self):
        graph = fixture("EL19A_F501_0F10E.reader_trace.json")
        one = run_pipeline(copy.deepcopy(graph), target=0x0F10E)
        two = run_pipeline(copy.deepcopy(graph), target=0x0F10E)
        self.assertEqual(one["graph"], two["graph"])
        self.assertEqual(one["warnings"], two["warnings"])


if __name__ == "__main__":
    unittest.main()
