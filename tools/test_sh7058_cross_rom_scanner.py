#!/usr/bin/env python3
"""Synthetic regression tests for the cross-ROM scanner's machine export layer."""

import json
import struct
import tempfile
import unittest
from pathlib import Path

from sh7058_cross_rom_scanner import HelperSpec, _export_span, build_scan_export, write_machine_exports


def make_call(helper, pc, table, axis1, dim1, dim2, raw_r4, raw_r5):
    return {
        "call_pc": pc,
        "call_form": "indirect_jsr",
        "target_load_pc": pc - 8,
        "target_register": 3,
        "call_instruction": 0x430B,
        "delay_slot": 0x654C,
        "scan_start": 0x5200,
        "helper": helper,
        "kind": "2D_AXIS",
        "elem_type": "uint16",
        "dim1": dim1,
        "dim2": dim2,
        "axis1_type": "uint8",
        "axis2_type": "",
        "table": table,
        "axis1": axis1,
        "axis2": None,
        "raw_r4": raw_r4,
        "raw_r5": raw_r5,
        "raw_r6": None,
    }


class ScannerExportTests(unittest.TestCase):
    def test_span_uses_exclusive_end_and_hashes_full_payload(self):
        rom = bytes(range(32))
        span = _export_span(rom, 4, 4, "uint16")
        self.assertEqual(span["byte_length"], 8)
        self.assertEqual(span["end_exclusive"], 12)
        self.assertTrue(span["in_bounds"])
        self.assertEqual(span["sha256"], __import__("hashlib").sha256(rom[4:12]).hexdigest())

    def test_span_marks_truncated_payload_without_partial_hash(self):
        span = _export_span(bytes(range(8)), 4, 3, "uint16")
        self.assertEqual(span["end_exclusive"], 10)
        self.assertFalse(span["in_bounds"])
        self.assertIsNone(span["sha256"])

    def test_export_preserves_unresolved_calls_and_geometry_conflicts(self):
        rom = bytearray(0x8000)
        struct.pack_into(">H", rom, 0x52F0, 0x4F22)
        rom[0x6000:0x6010] = bytes(range(16))
        rom[0x6100:0x6104] = bytes(range(4))

        helpers = {
            0x5000: HelperSpec(0x5000, "2D_AXIS", "uint16", 4, 1, "uint8", "", 0, 0),
            0x5010: HelperSpec(0x5010, "2D_AXIS", "uint16", 2, 2, "uint8", "", 0, 0),
        }
        calls = [
            make_call(0x5000, 0x5300, 0x6000, 0x6100, 4, 1, 0x6000, 0x6100),
            make_call(0x5010, 0x5310, 0x6000, 0x6100, 2, 2, 0x6000, 0x6100),
            make_call(0x5000, 0x5320, None, None, 4, 1, None, None),
        ]
        report = build_scan_export("synthetic-not-on-disk.bin", bytes(rom), helpers, calls)

        self.assertEqual(report["summary"]["call_count"], 3)
        self.assertEqual(report["summary"]["resolved_call_count"], 2)
        self.assertEqual(report["summary"]["unresolved_call_count"], 1)
        self.assertEqual(report["summary"]["unique_resolved_table_bases"], 1)
        self.assertEqual(len(report["calls"]), 3)
        self.assertIsNone(report["calls"][2]["table"])
        self.assertEqual(report["calls"][0]["delay_slot"], 0x654C)
        self.assertIn("instruction_words", report["calls"][0]["instruction_context"])
        self.assertEqual(report["calls"][0]["caller_start_candidate"], 0x52F0)
        self.assertTrue(report["tables"][0]["geometry_conflict"])
        self.assertEqual(report["tables"][0]["call_pcs"], [0x5300, 0x5310])

    def test_json_and_tsv_exports_are_written(self):
        rom = bytearray(0x8000)
        helper = HelperSpec(0x5000, "2D_AXIS", "uint16", 4, 1, "uint8", "", 0, 0)
        calls = [make_call(0x5000, 0x5300, 0x6000, 0x6100, 4, 1, 0x6000, 0x6100)]
        report = build_scan_export("synthetic-not-on-disk.bin", bytes(rom), {0x5000: helper}, calls)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            json_path = root / "export" / "scan.json"
            tsv_dir = root / "tsv"
            write_machine_exports(json_path, tsv_dir, [report])
            payload = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["schema"], "sh7058-cross-rom-batch-v1")
            self.assertEqual(payload["scans"][0]["summary"]["call_count"], 1)
            self.assertEqual(len(list(tsv_dir.glob("*.calls.tsv"))), 1)
            self.assertEqual(len(list(tsv_dir.glob("*.tables.tsv"))), 1)
            self.assertEqual(len(list(tsv_dir.glob("*.helpers.tsv"))), 1)


if __name__ == "__main__":
    unittest.main()
