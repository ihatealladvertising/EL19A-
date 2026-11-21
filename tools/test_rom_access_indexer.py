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


if __name__ == "__main__":
    unittest.main(verbosity=2)
