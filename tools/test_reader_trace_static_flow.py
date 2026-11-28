#!/usr/bin/env python3
"""Synthetic tests for the existing SH-2 static RAM/query/result tracker."""
from __future__ import annotations

import pathlib
import sys
import unittest

TOOLS_DIR = pathlib.Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import build_static_indices as static_indices


class StaticFlowTests(unittest.TestCase):
    def make_lookup_fixture(self):
        rom = bytearray(0x2040)
        instructions = [
            (0x2000, 0xD405, "mov.l @(0x14,pc),r4", "", "sub_2000", "loc_2000"),
            (0x2002, 0xD906, "mov.l @(0x18,pc),r9", "", "sub_2000", "loc_2000"),
            (0x2004, 0xD107, "mov.l @(0x1C,pc),r1", "", "sub_2000", "loc_2000"),
            (0x2006, 0x6510, "mov.b @r1,r5", "", "sub_2000", "loc_2000"),
            (0x2008, 0x655C, "extu.b r5,r5", "", "sub_2000", "loc_2000"),
            (0x200A, 0x420B, "jsr @r2", "sub_22E10", "sub_2000", "loc_2000"),
            (0x200C, 0x6653, "mov r5,r6", "", "sub_2000", "loc_2000"),
            (0x200E, 0x2900, "mov.b r0,@r9", "", "sub_2000", "loc_2000"),
            (0x2010, 0x6290, "mov.b @r9,r2", "", "sub_2000", "loc_2000"),
            (0x2012, 0x0009, "nop", "", "sub_2000", "loc_2000"),
        ]
        for pc, opcode, *_ in instructions:
            rom[pc:pc + 2] = opcode.to_bytes(2, "big")

        # PC-relative literal pools: table pointer, output RAM base, query RAM base.
        rom[0x2018:0x201C] = (0x0000F10E).to_bytes(4, "big")
        rom[0x201C:0x2020] = (0xFFFF29F6).to_bytes(4, "big")
        rom[0x2024:0x2028] = (0xFFFF84B8).to_bytes(4, "big")
        code_lines = [
            (pc, opcode.to_bytes(2, "big"), asm, comment, func, label)
            for pc, opcode, asm, comment, func, label in instructions
        ]
        catalog_rows = [{"address": "0x0F10E"}]
        return bytes(rom), code_lines, catalog_rows

    def test_call_delay_slot_query_copy_and_unsigned_transform(self):
        rom, code_lines, catalog_rows = self.make_lookup_fixture()
        _, _, _, calls = static_indices.full_rom_analysis(
            code_lines, rom, catalog_rows, mmio_addrs=[]
        )
        call = calls[0x0F10E][0]
        self.assertEqual(call["reader_pc"], 0x200A)
        self.assertEqual(call["helper"], "sub_22E10")
        self.assertEqual(call["q_inputs"], ["r5<-FFFF84B8", "r6<-FFFF84B8"])

    def test_call_result_taint_survives_call_clobber_into_preserved_r9_store(self):
        rom, code_lines, catalog_rows = self.make_lookup_fixture()
        _, readers, writers, calls = static_indices.full_rom_analysis(
            code_lines, rom, catalog_rows, mmio_addrs=[]
        )
        dests = calls[0x0F10E][0]["dests"]
        self.assertEqual(dests, [(0xFFFF29F6, "b", 0x200E, "mov.b r0,@r9", True)])
        self.assertIn((0x200E, "sub_2000"), writers[0xFFFF29F6])
        self.assertIn((0x2010, "sub_2000"), readers[0xFFFF29F6])

    def test_query_load_and_downstream_ram_read_are_separately_indexed(self):
        rom, code_lines, catalog_rows = self.make_lookup_fixture()
        _, readers, _, _ = static_indices.full_rom_analysis(
            code_lines, rom, catalog_rows, mmio_addrs=[]
        )
        self.assertIn((0x2006, "sub_2000"), readers[0xFFFF84B8])
        self.assertIn((0x2010, "sub_2000"), readers[0xFFFF29F6])
        self.assertNotEqual(readers[0xFFFF84B8], readers[0xFFFF29F6])

    def test_unfamiliar_helper_comment_is_recorded_without_semantic_interpretation(self):
        rom, code_lines, catalog_rows = self.make_lookup_fixture()
        revised = []
        for pc, hb, asm, comment, func, label in code_lines:
            if pc == 0x200A:
                comment = "commentless_helper"
            revised.append((pc, hb, asm, comment, func, label))
        _, _, _, calls = static_indices.full_rom_analysis(
            revised, rom, catalog_rows, mmio_addrs=[]
        )
        self.assertEqual(calls[0x0F10E][0]["helper"], "commentless_helper")
        self.assertEqual(calls[0x0F10E][0]["dests"][0][4], True)


if __name__ == "__main__":
    unittest.main()
