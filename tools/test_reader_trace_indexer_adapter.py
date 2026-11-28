#!/usr/bin/env python3
"""Synthetic tests for the thin existing-indexer -> reader-graph adapter."""
from __future__ import annotations

import json
import pathlib
import sys
import unittest

TOOLS_DIR = pathlib.Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from reader_trace_graph import validate_trace_graph
from reader_trace_indexer_adapter import AdapterError, merge_indexed_reader_evidence

REPO_ROOT = TOOLS_DIR.parent
REPO_FIXTURE = REPO_ROOT / "EVIDENCE" / "READER_TRACE_V0_1" / "EL19A_F501_0F10E.reader_trace.json"
LOCAL_FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "el19a_0f10e.reader_trace.json"
FIXTURE = REPO_FIXTURE if REPO_FIXTURE.exists() else LOCAL_FIXTURE


def base_graph():
    graph = json.loads(FIXTURE.read_text(encoding="utf-8"))
    graph["evidence"].extend([
        {
            "evidence_id": "ev:indexer",
            "source_path": "INDEX/rom_access_hits.tsv",
            "hash_algorithm": "sha256",
            "source_hash": "1" * 64,
            "anchor": "Header metadata and target hit row; synthetic fixture",
            "evidence_class": "byte_concordant_access_index",
            "extraction_method": "Existing rom_access_indexer valid_hits output",
            "status": "synthetic_test_input",
        },
        {
            "evidence_id": "ev:static-index",
            "source_path": "INDEX/rom_catalog_trace_summary.tsv",
            "hash_algorithm": "sha256",
            "source_hash": "2" * 64,
            "anchor": "One target-address summary row; synthetic fixture",
            "evidence_class": "static_register_and_ram_flow_summary",
            "extraction_method": "Existing build_static_indices output",
            "status": "synthetic_test_input",
        },
    ])
    return graph


def hit_rows():
    return [{
        "target": "0xF10E", "space": "rom", "pc": "0x85B2E",
        "function": "sub_85AF4", "access": "read", "width": "b",
        "form": "pool", "base": "0xF10E", "base_resolved": "full",
        "mask": "-", "note": "sub_22E10 fixed-grid UBYTE lookup via R4",
    }]


def summary_row():
    return {
        "address": "0x0F10E",
        "traced_reader_sites": "0x85B2E(sub_85AF4:sub_22E10)",
        "traced_query_inputs": "r5<-FFFF84B8",
        "traced_dest_ram": "FFFF29F6:b@85B34(taint); FFFF37AE:b@85B38(taint)",
        "dest_downstream_sample": "FFFF37AE@85B4A(sub_85AF4)",
    }


class ReaderTraceIndexerAdapterTests(unittest.TestCase):
    def merge(self, graph=None, hits=None, summary=None):
        return merge_indexed_reader_evidence(
            graph or base_graph(), hits if hits is not None else hit_rows(),
            summary if summary is not None else summary_row(),
            indexer_evidence_ref="ev:indexer",
            static_index_evidence_ref="ev:static-index",
            concordance_matched=10,
            concordance_checked=10,
        )

    def test_byte_concordant_rom_hit_becomes_direct_read_edge(self):
        result = self.merge()
        edge = next(e for e in result["edges"] if e["edge_id"] == "indexer-table-read-00085B2E")
        self.assertEqual(edge["basis"], "direct_observation")
        self.assertEqual(edge["relation"], "byte_concordant_ROM_read_at_PC")
        self.assertEqual(edge["evidence_refs"], ["ev:indexer"])

    def test_raw_run_indexer_hit_tuple_is_accepted(self):
        row = hit_rows()[0]
        raw_tuple = (
            row["target"], row["space"], row["pc"], row["function"],
            row["access"], row["width"], row["form"], row["base"],
            row["base_resolved"], row["mask"], row["note"],
        )
        result = self.merge(hits=[raw_tuple])
        self.assertTrue(any(
            edge["edge_id"] == "indexer-table-read-00085B2E"
            for edge in result["edges"]
        ))

    def test_aggregate_summary_does_not_fanout_to_multiple_reader_calls(self):
        hits = hit_rows() + [dict(hit_rows()[0], pc="0x86000", function="sub_86000")]
        result = self.merge(hits=hits)
        self.assertFalse(any(
            edge["edge_id"].startswith("indexer-query-arg-")
            for edge in result["edges"]
        ))
        self.assertFalse(any(
            edge["edge_id"] == "indexer-result-write-0000F10E-00085B34"
            for edge in result["edges"]
        ))
        self.assertTrue(any(
            boundary["boundary_id"] == "aggregate-result-attribution-0000F10E-000085B34"
            for boundary in result["unresolved_boundaries"]
        ))

    def test_zero_concordance_is_rejected(self):
        with self.assertRaises(AdapterError):
            merge_indexed_reader_evidence(
                base_graph(), hit_rows(), summary_row(),
                indexer_evidence_ref="ev:indexer", static_index_evidence_ref="ev:static-index",
                concordance_matched=0, concordance_checked=0,
            )

    def test_query_source_flow_is_derived_not_direct(self):
        result = self.merge()
        edge = next(e for e in result["edges"] if e["edge_id"].startswith("indexer-query-arg-"))
        self.assertEqual(edge["basis"], "derived")
        self.assertIn("R5", edge["relation"])
        self.assertTrue(any(n["node_id"] == "indexer-query-FFFF84B8" for n in result["nodes"]))

    def test_tainted_result_store_is_derived(self):
        result = self.merge()
        edge = next(e for e in result["edges"] if e["edge_id"] == "indexer-result-write-0000F10E-00085B34")
        self.assertEqual(edge["basis"], "derived")
        self.assertEqual(edge["relation"], "tainted_lookup_result_written_to_RAM")

    def test_near_call_store_remains_heuristic_and_unresolved(self):
        summary = summary_row()
        summary["traced_dest_ram"] = "FFFF29F6:b@85B34(near)"
        result = self.merge(summary=summary)
        edge = next(e for e in result["edges"] if e["edge_id"] == "indexer-result-write-0000F10E-00085B34")
        self.assertEqual(edge["basis"], "heuristic")
        self.assertTrue(any(b["boundary_id"] == "near-store-not-tainted-0000F10E-00085B34" for b in result["unresolved_boundaries"]))

    def test_downstream_read_site_does_not_claim_value_causality(self):
        result = self.merge()
        edge = next(e for e in result["edges"] if e["edge_id"] == "indexer-downstream-read-0000F10E-00085B4A")
        self.assertEqual(edge["basis"], "direct_observation")
        self.assertIn("no_value_causality", edge["relation"])
        self.assertTrue(any(b["boundary_id"] == "downstream-value-causality-0000F10E-00085B4A" for b in result["unresolved_boundaries"]))

    def test_wrong_target_hit_is_not_accepted(self):
        with self.assertRaises(AdapterError):
            self.merge(hits=[dict(hit_rows()[0], target="0x8550")])

    def test_ram_write_is_not_accepted_as_table_reader_hit(self):
        with self.assertRaises(AdapterError):
            self.merge(hits=[dict(hit_rows()[0], access="write")])

    def test_unknown_evidence_reference_is_rejected(self):
        with self.assertRaises(AdapterError):
            merge_indexed_reader_evidence(
                base_graph(), hit_rows(), summary_row(),
                indexer_evidence_ref="missing", static_index_evidence_ref="ev:static-index",
                concordance_matched=1, concordance_checked=1,
            )

    def test_invalid_concordance_totals_are_rejected(self):
        with self.assertRaises(AdapterError):
            merge_indexed_reader_evidence(
                base_graph(), hit_rows(), summary_row(),
                indexer_evidence_ref="ev:indexer", static_index_evidence_ref="ev:static-index",
                concordance_matched=11, concordance_checked=10,
            )

    def test_adapter_is_idempotent_by_stable_node_and_edge_ids(self):
        first = self.merge()
        second = merge_indexed_reader_evidence(
            first, hit_rows(), summary_row(),
            indexer_evidence_ref="ev:indexer", static_index_evidence_ref="ev:static-index",
            concordance_matched=10, concordance_checked=10,
        )
        self.assertEqual(len(first["nodes"]), len(second["nodes"]))
        self.assertEqual(len(first["edges"]), len(second["edges"]))

    def test_enriched_graph_still_passes_core_contract_validation(self):
        result = self.merge()
        warnings = validate_trace_graph(result)
        self.assertTrue(any("derived 240" in warning for warning in warnings))


if __name__ == "__main__":
    unittest.main()
