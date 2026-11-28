#!/usr/bin/env python3
"""Synthetic tests for exact per-call static-flow graph enrichment."""
from __future__ import annotations

import copy
import hashlib
import json
import pathlib
import sys
import tempfile
import unittest

TOOLS_DIR = pathlib.Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from reader_trace_graph import validate_trace_graph
from reader_trace_static_flow_adapter import (
    StaticFlowAdapterError,
    build_static_flow_call_document,
    canonical_static_flow_json,
    merge_per_call_static_flow,
    static_flow_document_sha256,
    write_static_flow_call_document,
)

REPO_ROOT = TOOLS_DIR.parent
FIXTURE = REPO_ROOT / "EVIDENCE" / "READER_TRACE_V0_1" / "EL19A_F501_0F10E.reader_trace.json"
ROM_SHA = "bfe037e8e6c389e2a90214047058eb6dc3bcaaaac5b5931bf98a3f5d9f64fd6a"
LISTING_SHA = "148385bbec91f6a491dcaa403962836f709c2f273df9a17ec51f1dea5f7f4549"
LISTING_PATH = (
    "EVIDENCE/EL19A_Complete_Disassembly_ANNOTATED_V3_NEXT6_14_GBR_BASE_RESOLVED.zip"
    "#EL19A_Complete_Disassembly_ANNOTATED_V3_NEXT6_16_ALL_PENDING_ANNOTATIONS(1).lst"
)


def load_graph(name="EL19A_F501_0F10E.reader_trace.json"):
    return json.loads((FIXTURE.parent / name).read_text(encoding="utf-8"))


def raw_calls(*, first_tainted=True, second_call=True, first_helper="sub_22E10"):
    calls = [{
        "reader_pc": 0x85B2E,
        "func": "sub_85AF4",
        "helper": first_helper,
        "q_inputs": ["r5<-FFFF84B8", "r6<-FFFF84B8"],
        "dests": [
            (0xFFFF29F6, "b", 0x85B34, "mov.b r0,@r9", first_tainted),
            (0xFFFF37AE, "b", 0x85B38, "mov.b r0,@r9", first_tainted),
        ],
    }]
    if second_call:
        calls.append({
            "reader_pc": 0x86000,
            "func": "sub_85F00",
            "helper": "sub_22E10",
            "q_inputs": ["r6<-FFFF84BA"],
            "dests": [(0xFFFF2910, "b", 0x86008, "mov.b r0,@r8", True)],
        })
    return {0x0F10E: calls}


def make_document(**kwargs):
    return build_static_flow_call_document(
        raw_calls(**kwargs),
        artifact_sha256=ROM_SHA,
        source_listing_sha256=LISTING_SHA,
        source_listing_path=LISTING_PATH,
    )


def add_document_evidence(graph, document, *, evidence_ref="ev:static-flow-calls", digest=None):
    actual = static_flow_document_sha256(document)
    graph["evidence"].append({
        "evidence_id": evidence_ref,
        "source_path": "EVIDENCE/READER_TRACE_V0_1/synthetic_static_flow_calls.json",
        "hash_algorithm": "sha256",
        "source_hash": digest or actual,
        "anchor": (
            "Exact per-call raw cat_calls record for target 0x%X and reader PC 0x%X"
            % (document["calls"][0]["target_ea"], document["calls"][0]["reader_pc"])
        ),
        "evidence_class": "per_call_static_reader_flow",
        "extraction_method": "Synthetic test document built from full_rom_analysis cat_calls shape",
        "status": "synthetic_test_input",
    })
    return evidence_ref


class StaticFlowAdapterTests(unittest.TestCase):
    def merge(self, *, graph=None, document=None, evidence_ref="ev:static-flow-calls"):
        graph = graph or load_graph()
        document = document or make_document()
        add_document_evidence(graph, document, evidence_ref=evidence_ref)
        return merge_per_call_static_flow(graph, document, static_flow_evidence_ref=evidence_ref)

    def test_two_calls_for_one_table_attach_only_exact_graph_call(self):
        graph = load_graph()
        document = make_document()
        result = self.merge(graph=graph, document=document)
        node_ids = {node["node_id"] for node in result["nodes"]}
        self.assertIn("static-flow-store-00085B34-FFFF29F6", node_ids)
        self.assertIn("static-flow-store-00085B38-FFFF37AE", node_ids)
        self.assertNotIn("static-flow-store-00086008-FFFF2910", node_ids)
        self.assertTrue(any(
            item.get("extension_id") == "per-call-static-flow-0000F10E-00085B2E"
            for item in result["analysis_extensions"]
        ))
        self.assertFalse(any(
            edge["edge_id"].startswith("static-flow-") and "00086000" in edge["edge_id"]
            for edge in result["edges"]
        ))

    def test_query_origin_becomes_call_scoped_derived_path(self):
        result = self.merge()
        self.assertTrue(any(
            edge["edge_id"] == "static-flow-query-load-0000F10E-00085B2E-5-FFFF84B8"
            and edge["basis"] == "derived"
            for edge in result["edges"]
        ))
        self.assertTrue(any(
            edge["edge_id"] == "static-flow-query-arg-0000F10E-00085B2E-5-FFFF84B8"
            and edge["basis"] == "derived"
            for edge in result["edges"]
        ))
        self.assertTrue(any(
            node.get("properties", {}).get("transform_unresolved")
            for node in result["nodes"] if node["kind"] == "register"
        ))

    def test_taint_proven_stores_use_their_explicit_r0_source_operand(self):
        result = self.merge()
        store_edge_ids = {
            edge["edge_id"] for edge in result["edges"]
            if edge["edge_id"].startswith("static-flow-tainted-store-")
        }
        self.assertEqual(len(store_edge_ids), 2)
        self.assertTrue(all("00085B2E" in edge_id for edge_id in store_edge_ids))
        self.assertTrue(all("r0" in edge_id for edge_id in store_edge_ids))
        self.assertTrue(any(
            edge["edge_id"] == "static-flow-result-taint-r0-0000F10E-00085B2E"
            and edge["basis"] == "derived"
            for edge in result["edges"]
        ))

    def test_tainted_store_uses_r2_when_that_is_the_observed_instruction_source(self):
        document = make_document(second_call=False)
        for dest in document["calls"][0]["dests"]:
            dest["instruction"] = "mov.b   r2, @(r0,r6)"
        graph = load_graph()
        add_document_evidence(graph, document)
        result = merge_per_call_static_flow(
            graph, document, static_flow_evidence_ref="ev:static-flow-calls"
        )
        r2_nodes = [
            node for node in result["nodes"]
            if node.get("properties", {}).get("register") == "R2"
            and node.get("properties", {}).get("taint_proven_by_static_tracker")
        ]
        self.assertEqual(len(r2_nodes), 1)
        self.assertFalse(any(
            node.get("node_id", "").startswith("static-flow-r0-result-")
            for node in result["nodes"]
        ))
        self.assertTrue(any(
            edge["edge_id"] == "static-flow-result-taint-r2-0000F10E-00085B2E"
            and edge["basis"] == "derived"
            for edge in result["edges"]
        ))
        store_edges = [
            edge for edge in result["edges"]
            if edge["edge_id"].startswith("static-flow-tainted-store-r2-")
        ]
        self.assertEqual(len(store_edges), 2)

    def test_near_call_store_is_heuristic_and_never_linked_from_r0(self):
        result = self.merge(document=make_document(first_tainted=False, second_call=False))
        self.assertTrue(any(
            edge["edge_id"].startswith("static-flow-near-store-")
            and edge["basis"] == "heuristic"
            for edge in result["edges"]
        ))
        self.assertFalse(any(
            edge["edge_id"].startswith("static-flow-tainted-store-")
            for edge in result["edges"]
        ))
        self.assertTrue(any(
            boundary["boundary_id"].startswith("static-flow-near-boundary-")
            for boundary in result["unresolved_boundaries"]
        ))

    def test_listing_identity_is_added_without_claiming_instruction_redecode(self):
        result = self.merge()
        self.assertEqual(result["coverage"]["source_listing_sha256"], LISTING_SHA)
        self.assertFalse(result["coverage"]["independent_redecode_performed"])
        listing = next(
            row for row in result["evidence"]
            if row["evidence_id"] == "ev:static-flow-stage16-listing"
        )
        self.assertEqual(listing["source_hash"], LISTING_SHA)
        self.assertEqual(listing["evidence_class"], "target_disassembly_listing")

    def test_production_callsite_validation_resolves_only_10f8a_listing_provenance(self):
        graph = load_graph("EL19A_F501_10F8A_32PT_UWORD.reader_trace.json")
        document = build_static_flow_call_document(
            {0x10F8A: [{
                "reader_pc": 0x648D8,
                "func": "sub_648A6",
                "helper": "sub_22FAC",
                "q_inputs": ["r6<-FFFF1064"],
                "dests": [(0xFFFF10E2, "w", 0x648DA, "mov.w r0,@(h'8e,gbr)", True)],
            }]},
            artifact_sha256=ROM_SHA,
            source_listing_sha256=LISTING_SHA,
            source_listing_path=LISTING_PATH,
        )
        document["call_site_validation"] = {
            "target_ea": 0x10F8A,
            "reader_pc": 0x648D8,
            "instruction_bytes": "42 0B",
            "assembly": "jsr @r2",
            "source_listing_sha256": LISTING_SHA,
            "listing_rom_byte_concordant": True,
            "validator": "build_static_indices.parse_listing",
        }
        add_document_evidence(graph, document)
        result = merge_per_call_static_flow(
            graph, document, static_flow_evidence_ref="ev:static-flow-calls"
        )
        unresolved = {row["boundary_id"] for row in result["unresolved_boundaries"]}
        self.assertNotIn("listing-provenance-10f8a", unresolved)
        self.assertIn("forward-query-operand-identity", unresolved)
        self.assertIn("physical-input-output-domain", unresolved)
        resolved = next(
            row for row in result["resolved_boundaries"]
            if row["boundary_id"] == "listing-provenance-10f8a"
        )
        self.assertEqual(resolved["source_listing_sha256"], LISTING_SHA)
        self.assertFalse(resolved["independent_redecode_performed"])
        extension = next(
            row for row in result["analysis_extensions"]
            if row.get("extension_id") == "per-call-static-flow-00010F8A-000648D8"
        )
        self.assertEqual(extension["resolved_boundary_ids"], ["listing-provenance-10f8a"])

    def test_callsite_validation_rejects_wrong_call_pc_or_unconcordant_listing(self):
        document = build_static_flow_call_document(
            {0x10F8A: [{
                "reader_pc": 0x648D8,
                "func": "sub_648A6",
                "helper": "sub_22FAC",
                "q_inputs": [],
                "dests": [],
            }]},
            artifact_sha256=ROM_SHA,
            source_listing_sha256=LISTING_SHA,
            source_listing_path=LISTING_PATH,
        )
        document["call_site_validation"] = {
            "target_ea": 0x10F8A,
            "reader_pc": 0x648D9,
            "instruction_bytes": "42 0B",
            "assembly": "jsr @r2",
            "source_listing_sha256": LISTING_SHA,
            "listing_rom_byte_concordant": True,
            "validator": "build_static_indices.parse_listing",
        }
        graph = load_graph("EL19A_F501_10F8A_32PT_UWORD.reader_trace.json")
        add_document_evidence(graph, document)
        with self.assertRaises(StaticFlowAdapterError):
            merge_per_call_static_flow(
                graph, document, static_flow_evidence_ref="ev:static-flow-calls"
            )

        document["call_site_validation"]["reader_pc"] = 0x648D8
        document["call_site_validation"]["listing_rom_byte_concordant"] = False
        with self.assertRaises(StaticFlowAdapterError):
            static_flow_document_sha256(document)

    def test_graph_and_document_are_not_mutated(self):
        graph = load_graph()
        document = make_document()
        add_document_evidence(graph, document)
        before_graph = copy.deepcopy(graph)
        before_document = copy.deepcopy(document)
        merge_per_call_static_flow(
            graph, document, static_flow_evidence_ref="ev:static-flow-calls"
        )
        self.assertEqual(graph, before_graph)
        self.assertEqual(document, before_document)

    def test_enriched_graph_passes_core_validator_with_only_expected_warning(self):
        result = self.merge()
        warnings = validate_trace_graph(result)
        self.assertEqual(len(warnings), 1)
        self.assertIn("derived 240", warnings[0])

    def test_document_rom_must_match_graph_rom(self):
        document = make_document()
        document["artifact_sha256"] = "0" * 64
        graph = load_graph()
        add_document_evidence(graph, document)
        with self.assertRaises(StaticFlowAdapterError):
            merge_per_call_static_flow(graph, document, static_flow_evidence_ref="ev:static-flow-calls")

    def test_target_and_call_pc_must_match_exactly(self):
        for target_ea, reader_pc in ((0x0F200, 0x85B2E), (0x0F10E, 0x85B2F)):
            document = make_document(second_call=False)
            document["calls"][0]["target_ea"] = target_ea
            document["calls"][0]["reader_pc"] = reader_pc
            graph = load_graph()
            add_document_evidence(graph, document)
            with self.assertRaises(StaticFlowAdapterError):
                merge_per_call_static_flow(graph, document, static_flow_evidence_ref="ev:static-flow-calls")

    def test_helper_ea_must_match_exact_graph_call_helper(self):
        document = make_document(first_helper="sub_22E11", second_call=False)
        graph = load_graph()
        add_document_evidence(graph, document)
        with self.assertRaises(StaticFlowAdapterError):
            merge_per_call_static_flow(graph, document, static_flow_evidence_ref="ev:static-flow-calls")

    def test_evidence_hash_must_match_serialized_static_flow_document(self):
        graph = load_graph()
        document = make_document()
        add_document_evidence(graph, document, digest="0" * 64)
        with self.assertRaises(StaticFlowAdapterError):
            merge_per_call_static_flow(graph, document, static_flow_evidence_ref="ev:static-flow-calls")

    def test_missing_evidence_reference_is_rejected(self):
        with self.assertRaises(StaticFlowAdapterError):
            merge_per_call_static_flow(load_graph(), make_document(), static_flow_evidence_ref="missing")

    def test_existing_listing_hash_conflict_is_rejected(self):
        graph = load_graph()
        graph["coverage"]["source_listing_sha256"] = "0" * 64
        document = make_document()
        add_document_evidence(graph, document)
        with self.assertRaises(StaticFlowAdapterError):
            merge_per_call_static_flow(graph, document, static_flow_evidence_ref="ev:static-flow-calls")

    def test_unparsed_query_origin_is_preserved_as_unresolved(self):
        document = make_document(second_call=False)
        document["calls"][0]["q_inputs"] = ["r5<-not-a-ram-cell"]
        graph = load_graph()
        add_document_evidence(graph, document)
        result = merge_per_call_static_flow(graph, document, static_flow_evidence_ref="ev:static-flow-calls")
        self.assertTrue(any(
            boundary["boundary_id"].startswith("static-flow-query-unparsed-")
            for boundary in result["unresolved_boundaries"]
        ))

    def test_duplicate_call_pc_for_same_target_is_rejected(self):
        calls = raw_calls(second_call=False)[0x0F10E]
        calls.append(copy.deepcopy(calls[0]))
        with self.assertRaises(StaticFlowAdapterError):
            build_static_flow_call_document(
                {0x0F10E: calls},
                artifact_sha256=ROM_SHA,
                source_listing_sha256=LISTING_SHA,
                source_listing_path=LISTING_PATH,
            )

    def test_export_writer_hash_matches_exact_file_bytes(self):
        document = make_document()
        with tempfile.TemporaryDirectory() as temp_dir:
            path = pathlib.Path(temp_dir) / "nested" / "static_flow.json"
            digest = write_static_flow_call_document(path, document)
            self.assertEqual(digest, hashlib.sha256(path.read_bytes()).hexdigest())
            reread = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(canonical_static_flow_json(reread), path.read_text(encoding="utf-8"))

    def test_canonical_export_is_deterministic(self):
        one = make_document()
        two = make_document()
        self.assertEqual(canonical_static_flow_json(one), canonical_static_flow_json(two))
        self.assertEqual(static_flow_document_sha256(one), static_flow_document_sha256(two))

    def test_adapter_is_idempotent(self):
        graph = load_graph()
        document = make_document()
        add_document_evidence(graph, document)
        once = merge_per_call_static_flow(graph, document, static_flow_evidence_ref="ev:static-flow-calls")
        twice = merge_per_call_static_flow(once, document, static_flow_evidence_ref="ev:static-flow-calls")
        self.assertEqual(once, twice)


if __name__ == "__main__":
    unittest.main()
