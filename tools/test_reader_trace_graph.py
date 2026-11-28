#!/usr/bin/env python3
"""Synthetic tests for the additive SH705x reader-trace graph contract."""
from __future__ import annotations

import copy
import json
import pathlib
import sys
import tempfile
import unittest

TOOLS_DIR = pathlib.Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from reader_trace_graph import (
    TraceValidationError,
    canonical_json,
    trace_sha256,
    validate_trace_graph,
    write_trace_graph,
)

REPO_ROOT = TOOLS_DIR.parent
REPO_FIXTURE = REPO_ROOT / "EVIDENCE" / "READER_TRACE_V0_1" / "EL19A_F501_0F10E.reader_trace.json"
LOCAL_FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "el19a_0f10e.reader_trace.json"
FIXTURE = REPO_FIXTURE if REPO_FIXTURE.exists() else LOCAL_FIXTURE


def load_fixture():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


class ReaderTraceGraphTests(unittest.TestCase):
    def test_golden_trace_fixture_is_structurally_valid(self):
        graph = load_fixture()
        warnings = validate_trace_graph(graph)
        self.assertEqual(len(graph["nodes"]), 23)
        self.assertEqual(len(graph["edges"]), 24)
        self.assertEqual(len(graph["evidence"]), 3)
        self.assertEqual(len(graph["unresolved_boundaries"]), 5)
        self.assertEqual(len(warnings), 1)

    def test_all_edge_endpoints_exist(self):
        graph = load_fixture()
        node_ids = {node["node_id"] for node in graph["nodes"]}
        for edge in graph["edges"]:
            self.assertIn(edge["from_node"], node_ids)
            self.assertIn(edge["to_node"], node_ids)

    def test_unknown_edge_endpoint_is_rejected(self):
        graph = load_fixture()
        graph["edges"][0]["to_node"] = "absent-node"
        with self.assertRaises(TraceValidationError):
            validate_trace_graph(graph)

    def test_asserted_edge_requires_evidence(self):
        graph = load_fixture()
        graph["edges"][0]["evidence_refs"] = []
        with self.assertRaises(TraceValidationError):
            validate_trace_graph(graph)

    def test_duplicate_node_ids_are_rejected(self):
        graph = load_fixture()
        graph["nodes"].append(copy.deepcopy(graph["nodes"][0]))
        with self.assertRaises(TraceValidationError):
            validate_trace_graph(graph)

    def test_duplicate_evidence_ids_are_rejected(self):
        graph = load_fixture()
        graph["evidence"].append(copy.deepcopy(graph["evidence"][0]))
        with self.assertRaises(TraceValidationError):
            validate_trace_graph(graph)

    def test_hash_algorithm_is_explicit_and_length_checked(self):
        graph = load_fixture()
        graph["evidence"][1]["hash_algorithm"] = "sha256"
        with self.assertRaises(TraceValidationError):
            validate_trace_graph(graph)

    def test_object_byte_extent_must_match_shape_and_storage(self):
        graph = load_fixture()
        graph["target_object"]["byte_extent"] = 15
        with self.assertRaises(TraceValidationError):
            validate_trace_graph(graph)

    def test_payload_hex_must_match_payload_hash(self):
        graph = load_fixture()
        graph["target_object"]["payload_hex"] = "00 " * 16
        with self.assertRaises(TraceValidationError):
            validate_trace_graph(graph)

    def test_missing_call_reference_is_rejected(self):
        graph = load_fixture()
        del graph["call_ref"]
        with self.assertRaises(TraceValidationError):
            validate_trace_graph(graph)

    def test_missing_semantic_disposition_is_rejected(self):
        graph = load_fixture()
        del graph["semantic_disposition"]
        with self.assertRaises(TraceValidationError):
            validate_trace_graph(graph)

    def test_reported_observations_stay_distinct_from_direct_observations(self):
        graph = load_fixture()
        self.assertEqual({edge["basis"] for edge in graph["edges"]}, {"reported_observation"})
        self.assertFalse(graph["coverage"]["independent_redecode_performed"])

    def test_grid_endpoint_conflict_is_warning_not_silent_resolution(self):
        warnings = validate_trace_graph(load_fixture())
        self.assertTrue(any("derived 240" in warning for warning in warnings))

    def test_unresolved_boundaries_and_semantic_stop_are_preserved(self):
        graph = load_fixture()
        self.assertEqual(len(graph["unresolved_boundaries"]), 5)
        self.assertEqual(graph["semantic_disposition"]["physical_identity"], "unresolved")
        self.assertEqual(graph["semantic_disposition"]["promotion"], "not_supported")

    def test_serialization_is_deterministic(self):
        graph = load_fixture()
        self.assertEqual(canonical_json(graph), canonical_json(graph))
        self.assertEqual(trace_sha256(graph), trace_sha256(graph))

    def test_atomic_writer_writes_valid_json_and_returns_digest(self):
        graph = load_fixture()
        with tempfile.TemporaryDirectory() as temp_dir:
            output = pathlib.Path(temp_dir) / "subdir" / "trace.json"
            digest = write_trace_graph(output, graph)
            reread = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(digest, trace_sha256(reread))
            self.assertEqual(reread["trace_id"], graph["trace_id"])


if __name__ == "__main__":
    unittest.main()
