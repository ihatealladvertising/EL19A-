#!/usr/bin/env python3
"""Synthetic tests for exact-image, evidence-linked helper profile resolution."""
from __future__ import annotations

import copy
import json
import pathlib
import sys
import unittest

TOOLS_DIR = pathlib.Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from reader_trace_graph import validate_trace_graph
from reader_trace_helper_profiles import (
    HelperProfileError,
    attach_helper_profile,
    list_profile_keys,
    resolve_helper_profile,
)

REPO_ROOT = TOOLS_DIR.parent
FIXTURES = REPO_ROOT / "EVIDENCE" / "READER_TRACE_V0_1"


def load_graph(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class HelperProfileTests(unittest.TestCase):
    def test_exact_22e10_profile_includes_implicit_u8_clamp(self):
        profile = resolve_helper_profile(
            "SH7058",
            "bfe037e8e6c389e2a90214047058eb6dc3bcaaaac5b5931bf98a3f5d9f64fd6a",
            0x22E10,
        )
        self.assertIsNotNone(profile)
        self.assertEqual(profile["mechanics"]["point_count"], 16)
        self.assertEqual(profile["mechanics"]["query_register"], "R5")
        self.assertEqual(profile["mechanics"]["upper_boundary"]["query"], 240)
        self.assertEqual(profile["evidence_basis"], "reported_observation")

    def test_exact_22fac_profile_includes_32_point_uword_axis_search(self):
        profile = resolve_helper_profile(
            "SH7058",
            "bfe037e8e6c389e2a90214047058eb6dc3bcaaaac5b5931bf98a3f5d9f64fd6a",
            "0x22FAC",
        )
        self.assertEqual(profile["mechanics"]["point_count"], 32)
        self.assertEqual(profile["mechanics"]["query_register"], "R6")
        self.assertEqual(profile["mechanics"]["axis_search"]["helper"], "sub_2340C")
        self.assertEqual(profile["mechanics"]["interpolation"]["helper"], "sub_231C8")

    def test_exact_22b44_profile_preserves_two_axis_register_roles(self):
        profile = resolve_helper_profile(
            "SH7058",
            "bfe037e8e6c389e2a90214047058eb6dc3bcaaaac5b5931bf98a3f5d9f64fd6a",
            0x22B44,
        )
        mechanics = profile["mechanics"]
        self.assertEqual(mechanics["axis1_pointer_register"], "R5")
        self.assertEqual(mechanics["axis2_pointer_register"], "R6")
        self.assertEqual(mechanics["query_register"], "R7")
        self.assertTrue(mechanics["same_query_for_both_axes"])
        self.assertEqual(profile["source_listing_sha256"], "148385bbec91f6a491dcaa403962836f709c2f273df9a17ec51f1dea5f7f4549")

    def test_exact_22df8_profile_includes_eight_point_endpoint(self):
        profile = resolve_helper_profile(
            "SH7058",
            "bfe037e8e6c389e2a90214047058eb6dc3bcaaaac5b5931bf98a3f5d9f64fd6a",
            0x22DF8,
        )
        self.assertEqual(profile["mechanics"]["point_count"], 8)
        self.assertEqual(profile["mechanics"]["upper_boundary"]["query"], 224)
        self.assertEqual(profile["mechanics"]["upper_boundary"]["element_index"], 7)

    def test_unknown_helper_ea_does_not_match_by_symbol_or_nearness(self):
        self.assertIsNone(resolve_helper_profile(
            "SH7058",
            "bfe037e8e6c389e2a90214047058eb6dc3bcaaaac5b5931bf98a3f5d9f64fd6a",
            0x22E11,
        ))

    def test_different_rom_sha_does_not_reuse_profile(self):
        self.assertIsNone(resolve_helper_profile(
            "SH7058", "0" * 64, 0x22E10
        ))

    def test_other_processor_profile_does_not_reuse_sh7058_contract(self):
        self.assertIsNone(resolve_helper_profile(
            "SH7055",
            "bfe037e8e6c389e2a90214047058eb6dc3bcaaaac5b5931bf98a3f5d9f64fd6a",
            0x22E10,
        ))

    def test_attach_profile_is_non_mutating_and_keeps_graph_valid(self):
        graph = load_graph("EL19A_F501_0F10E.reader_trace.json")
        before = copy.deepcopy(graph)
        enriched = attach_helper_profile(graph)
        self.assertEqual(graph, before)
        helper = next(n for n in enriched["nodes"] if n["node_id"] == "helper-22e10")
        self.assertEqual(helper["properties"]["recognized_profile"], "EL19A-F501-sub_22E10-implicit-u8-16-v1")
        self.assertEqual(helper["properties"]["profile_basis"], "reported_observation")
        self.assertTrue(any(x["extension_id"] == "helper-profile-00022E10" for x in enriched["analysis_extensions"]))
        self.assertEqual(len(validate_trace_graph(enriched)), 1)

    def test_attach_profile_to_32_point_and_two_axis_fixtures(self):
        curve = attach_helper_profile(load_graph("EL19A_F501_10F8A_32PT_UWORD.reader_trace.json"))
        matrix = attach_helper_profile(load_graph("EL19A_F501_0AFF2_2AXIS.reader_trace.json"))
        curve_helper = next(n for n in curve["nodes"] if n["kind"] == "lookup_helper")
        matrix_helper = next(n for n in matrix["nodes"] if n["kind"] == "lookup_helper")
        self.assertEqual(curve_helper["properties"]["mechanics"]["point_count"], 32)
        self.assertEqual(matrix_helper["properties"]["mechanics"]["lookup_kind"], "two_axis_map")
        self.assertEqual(validate_trace_graph(curve), [])
        self.assertEqual(validate_trace_graph(matrix), [])

    def test_missing_profile_evidence_is_rejected_not_silently_attached(self):
        graph = load_graph("EL19A_F501_0AFF2_2AXIS.reader_trace.json")
        graph["evidence"] = [e for e in graph["evidence"] if e["evidence_id"] != "ev:lst-stage16"]
        with self.assertRaises(HelperProfileError):
            attach_helper_profile(graph)

    def test_pinned_listing_sha_must_match_cited_listing_evidence(self):
        graph = load_graph("EL19A_F501_0AFF2_2AXIS.reader_trace.json")
        listing = next(ev for ev in graph["evidence"] if ev["evidence_id"] == "ev:lst-stage16")
        listing["source_hash"] = "0" * 64
        with self.assertRaises(HelperProfileError):
            attach_helper_profile(graph)

    def test_pinned_listing_evidence_must_use_sha256(self):
        graph = load_graph("EL19A_F501_0AFF2_2AXIS.reader_trace.json")
        listing = next(ev for ev in graph["evidence"] if ev["evidence_id"] == "ev:lst-stage16")
        listing["hash_algorithm"] = "git_blob_sha1"
        listing["source_hash"] = "a" * 40
        with self.assertRaises(HelperProfileError):
            attach_helper_profile(graph)

    def test_profile_inventory_has_only_exact_pinned_keys(self):
        keys = list_profile_keys()
        self.assertEqual(len(keys), 4)
        self.assertEqual({ea for _, _, ea in keys}, {0x22E10, 0x22FAC, 0x22B44, 0x22DF8})


if __name__ == "__main__":
    unittest.main()
