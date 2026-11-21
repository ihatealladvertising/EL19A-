#!/usr/bin/env python3
"""Focused stdlib tests for WO65115 resolver mechanics.

These tests do not replace the ROM/listing acceptance regressions. The five
repository-address regressions and PKIOR_W negative control still require the
pinned ROM plus extracted V3_NEXT6_16 listing.
"""

import importlib.util
import os
import tempfile
import unittest

MODULE_PATH = os.path.join(os.path.dirname(__file__), "rom_access_indexer.py")
SPEC = importlib.util.spec_from_file_location("rom_access_indexer", MODULE_PATH)
resolver = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(resolver)


class ResolverMechanicsTests(unittest.TestCase):

    def test_flow_boundary_invalidates_all_sixteen_registers(self):
        regs = [0x1000 + i for i in range(16)]
        provenance = [0x2000 + i for i in range(16)]
        active = {3: 1, 12: 2}
        resolver.invalidate_general_registers(regs, provenance, active)
        self.assertEqual(regs, [None] * 16)
        self.assertEqual(provenance, [None] * 16)
        self.assertEqual(active, {})

    def test_pool_pointer_reports_actual_dereference_pc(self):
        hits = [
            ("0x8550", "rom", "0x40436", "sub_403D8", "constant", "l",
             "pool", "0x8550", "full", "-", "mov.l pool value 0x8550")
        ]
        active = {3: 0}
        changed = resolver.promote_pool_pointer_to_dereference(
            hits, active, 3, 0x4043A, "sub_403D8",
            "read", "b", "base_disp", "0x8550", "full", "-",
            "mov.b @r3, r2"
        )
        self.assertTrue(changed)
        self.assertEqual(hits[0][2], "0x4043A")
        self.assertEqual(hits[0][4], "read")
        self.assertIn("pointer loaded at 0x40436", hits[0][10])
        self.assertEqual(active, {})

    def test_untracked_pointer_does_not_promote(self):
        hits = []
        active = {}
        changed = resolver.promote_pool_pointer_to_dereference(
            hits, active, 4, 0x48930, "sub_488BA",
            "read", "l", "base_disp", "0xED64", "full", "-",
            "mov.l @r4, r0"
        )
        self.assertFalse(changed)
        self.assertEqual(hits, [])

    def test_target_parser_keeps_rom_and_ram_spaces_distinct(self):
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as f:
            f.write("FFFF85DF\n0x8550\n388AC\n")
            target_path = f.name
        try:
            targets = resolver.parse_targets(target_path)
        finally:
            os.unlink(target_path)
        self.assertEqual(
            [(t["norm"], t["space"], t["val"]) for t in targets],
            [
                ("FFFF85DF", "ram", 0xFFFF85DF),
                ("0x8550", "rom", 0x8550),
                ("0x388AC", "rom", 0x388AC),
            ],
        )

    def test_pc_concordance_requires_exact_in_range_bytes(self):
        rom = bytes.fromhex("00 09 12 34 56 78")
        self.assertTrue(resolver.pc_bytes_match(rom, 0, bytes.fromhex("00 09")))
        self.assertTrue(resolver.pc_bytes_match(rom, 2, bytes.fromhex("12 34")))
        self.assertFalse(resolver.pc_bytes_match(rom, 2, bytes.fromhex("12 35")))
        self.assertFalse(resolver.pc_bytes_match(rom, 5, bytes.fromhex("78 90")))
        self.assertFalse(resolver.pc_bytes_match(rom, -1, bytes.fromhex("00 09")))


    def test_second_register_alias_gets_a_separate_access_row(self):
        hits = [
            ("0x8550", "rom", "0x40436", "sub_403D8", "constant", "l",
             "pool", "0x8550", "full", "-", "mov.l pool value 0x8550")
        ]
        active = {3: 0, 4: 0}
        self.assertTrue(resolver.promote_pool_pointer_to_dereference(
            hits, active, 3, 0x4043A, "sub_403D8",
            "read", "b", "base_disp", "0x8550", "full", "-",
            "mov.b @r3, r2"
        ))
        self.assertTrue(resolver.promote_pool_pointer_to_dereference(
            hits, active, 4, 0x40444, "sub_403D8",
            "read", "b", "base_disp", "0x8550", "full", "-",
            "mov.b @r4, r1"
        ))
        self.assertEqual([row[2] for row in hits], ["0x4043A", "0x40444"])

    def test_invalid_target_width_is_rejected(self):
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as f:
            f.write("000085DF\\n")
            target_path = f.name
        try:
            with self.assertRaises(ValueError):
                resolver.parse_targets(target_path)
        finally:
            os.unlink(target_path)

    def test_real_rom_regressions_when_tsv_is_supplied(self):
        import csv
        output_path = os.environ.get("WO65115_REGRESSION_TSV")
        if not output_path:
            self.skipTest("set WO65115_REGRESSION_TSV to a production regression-run TSV")
        with open(output_path, "r", encoding="utf-8", newline="") as f:
            content = [line for line in f if not line.startswith("#")]
        rows = list(csv.DictReader(content, delimiter="\\t"))
        by_target = {}
        for row in rows:
            by_target.setdefault(row["target"], []).append(row)

        reads_85df = {
            row["pc"].upper() for row in by_target.get("FFFF85DF", [])
            if row["access"] == "read"
        }
        self.assertEqual(reads_85df, {"0x46BDE", "0x47014", "0x59CA2"})

        reads_85e0 = [
            row for row in by_target.get("FFFF85E0", [])
            if row["access"] == "read"
        ]
        self.assertEqual(reads_85e0, [])

        rows_1db4 = by_target.get("FFFF1DB4", [])
        self.assertTrue(any(row["pc"].upper() == "0X4042C" and row["access"] == "read" for row in rows_1db4))
        self.assertTrue(any(row["pc"].upper() == "0X4044A" and row["access"] == "write" for row in rows_1db4))

        rows_8550 = by_target.get("0x8550", [])
        self.assertEqual(len(rows_8550), 1)
        self.assertEqual(rows_8550[0]["pc"].upper(), "0X4043A")
        self.assertEqual(rows_8550[0]["function"], "sub_403D8")
        self.assertEqual(rows_8550[0]["access"], "read")

        rows_388ac = by_target.get("0x388AC", [])
        self.assertEqual(len(rows_388ac), 1)
        self.assertEqual(rows_388ac[0]["pc"].upper(), "0X38806")
        self.assertEqual(rows_388ac[0]["access"], "constant")

    def test_pkior_negative_control_when_false_positive_pc_is_known(self):
        false_pc = os.environ.get("WO65115_PKIOR_FALSE_HIT_PC")
        output_path = os.environ.get("WO65115_REGRESSION_TSV")
        if not false_pc or not output_path:
            self.skipTest("PKIOR_W historic false-positive PC not recovered in WO65061")
        import csv
        with open(output_path, "r", encoding="utf-8", newline="") as f:
            content = [line for line in f if not line.startswith("#")]
        rows = list(csv.DictReader(content, delimiter="\\t"))
        self.assertFalse(any(row["pc"].upper() == false_pc.upper() for row in rows))


if __name__ == "__main__":
    unittest.main(verbosity=2)
