#!/usr/bin/env python3
"""Focused stdlib tests for WO65115 resolver mechanics.

These tests do not replace the ROM/listing acceptance regressions. The five
repository-address regressions and PKIOR_W negative control still require the
pinned ROM plus extracted V3_NEXT6_16 listing.
"""

import importlib.util
import hashlib
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
            f.write("000085DF\n")
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
        rows = list(csv.DictReader(content, delimiter="\t"))
        by_target = {}
        for row in rows:
            by_target.setdefault(row["target"], []).append(row)

        reads_85df = {
            row["pc"].upper() for row in by_target.get("FFFF85DF", [])
            if row["access"] == "read"
        }
        self.assertTrue({"0X46BDE", "0X47014", "0X59CA2"}.issubset(reads_85df))
        writes_85df = {
            row["pc"].upper() for row in by_target.get("FFFF85DF", [])
            if row["access"] == "write"
        }
        self.assertTrue({"0X59BF2", "0X59C02", "0X59C04"}.issubset(writes_85df))

        reads_85e0 = [
            row for row in by_target.get("FFFF85E0", [])
            if row["access"] == "read"
        ]
        self.assertEqual(reads_85e0, [])
        writes_85e0 = [
            row for row in by_target.get("FFFF85E0", [])
            if row["access"] == "write"
        ]
        self.assertEqual(len(writes_85e0), 1)
        self.assertEqual(writes_85e0[0]["pc"].upper(), "0X59CA6")

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
        control_path = os.environ.get("WO65115_PKIOR_CONTROL_TSV")
        if not false_pc or not control_path:
            self.skipTest("PKIOR_W historic false-positive PC and dedicated control TSV not recovered")
        import csv
        with open(control_path, "r", encoding="utf-8", newline="") as f:
            content = [line for line in f if not line.startswith("#")]
        rows = list(csv.DictReader(content, delimiter="\t"))
        self.assertFalse(any(row["pc"].upper() == false_pc.upper() for row in rows))


    def test_ldc_gbr_decodes_register_from_bits_8_to_11(self):
        self.assertEqual(resolver.ldc_gbr_source_register(0x401E), 0)
        self.assertEqual(resolver.ldc_gbr_source_register(0x4B1E), 11)
        self.assertEqual(resolver.ldc_gbr_source_register(0x4917), 9)
        self.assertIsNone(resolver.ldc_gbr_source_register(0x401A))


    def _run_synthetic_gbr_path(self, transfer_opcode):
        with tempfile.TemporaryDirectory() as tmp:
            rom = bytearray(14)
            instructions = [
                (0x0000, 0x9004, "mov.w @(4,pc),r0"),
                (0x0002, 0x401E, "ldc r0,gbr"),
                (0x0004, transfer_opcode, "control transfer"),
                (0x0006, 0x0009, "nop"),
                (0x0008, 0xC41B, "mov.b @(0x1B,gbr),r0"),
                (0x000A, 0x0009, "nop"),
            ]
            listing_lines = ["sub_0000:"]
            for pc, opcode, assembly in instructions:
                encoded = opcode.to_bytes(2, "big")
                rom[pc:pc + 2] = encoded
                listing_lines.append(f"{pc:08X} {opcode:04X} CODE {assembly}")
            # PC-relative MOV.W at 0x0000: pool EA = 0 + 4 + 4*2 = 0x000C.
            rom[0x000C:0x000E] = bytes.fromhex("85 C4")
            listing_text = "\n".join(listing_lines) + "\n"

            rom_path = os.path.join(tmp, "fixture.bin")
            listing_path = os.path.join(tmp, "fixture.lst")
            targets_path = os.path.join(tmp, "targets.txt")
            hits_path = os.path.join(tmp, "hits.tsv")
            unresolved_path = os.path.join(tmp, "unresolved.tsv")
            with open(rom_path, "wb") as f:
                f.write(rom)
            with open(listing_path, "w", encoding="utf-8") as f:
                f.write(listing_text)
            with open(targets_path, "w", encoding="utf-8") as f:
                f.write("FFFF85DF\n")

            old_md5 = resolver.EXPECTED_ROM_MD5
            old_listing_sha = resolver.EXPECTED_LISTING_SHA256
            resolver.EXPECTED_ROM_MD5 = hashlib.md5(rom).hexdigest()
            resolver.EXPECTED_LISTING_SHA256 = hashlib.sha256(
                listing_text.encode("utf-8")
            ).hexdigest()
            try:
                result = resolver.run_indexer(
                    rom_path, listing_path, targets_path,
                    hits_path, unresolved_path
                )
            finally:
                resolver.EXPECTED_ROM_MD5 = old_md5
                resolver.EXPECTED_LISTING_SHA256 = old_listing_sha
            return result

    def test_synthetic_ldc_gbr_read_is_resolved(self):
        hits, unresolved, matched, checked = self._run_synthetic_gbr_path(0x0009)
        self.assertEqual([row[2] for row in hits], ["0x8"])
        self.assertEqual(hits[0][4], "read")
        self.assertEqual(hits[0][7], "FFFF85C4")
        self.assertEqual(unresolved, [])
        self.assertEqual((matched, checked), (1, 1))

    def test_synthetic_bra_preserves_gbr_to_branch_target(self):
        hits, unresolved, matched, checked = self._run_synthetic_gbr_path(0xA000)
        self.assertEqual([row[2] for row in hits], ["0x8"])
        self.assertEqual(hits[0][4], "read")
        self.assertEqual(unresolved, [])
        self.assertEqual((matched, checked), (1, 1))

    def test_synthetic_bsr_invalidates_gbr_at_callee_boundary(self):
        hits, unresolved, matched, checked = self._run_synthetic_gbr_path(0xB000)
        self.assertEqual(hits, [])
        self.assertEqual(len(unresolved), 1)
        self.assertEqual(unresolved[0][2], "0x8")
        self.assertEqual(unresolved[0][11], "unresolved GBR register")
        self.assertEqual((matched, checked), (1, 1))


    def test_synthetic_rts_and_rte_invalidate_gbr(self):
        for opcode in (0x000B, 0x002B):
            with self.subTest(opcode=hex(opcode)):
                hits, unresolved, matched, checked = self._run_synthetic_gbr_path(opcode)
                self.assertEqual(hits, [])
                self.assertEqual(len(unresolved), 1)
                self.assertEqual(unresolved[0][2], "0x8")
                self.assertEqual(unresolved[0][11], "unresolved GBR register")
                self.assertEqual((matched, checked), (1, 1))


    def test_sub22e10_r4_argument_is_promoted_at_helper_call_pc(self):
        hits = [
            ("0xED64", "rom", "0x48930", "sub_488BA", "constant", "l",
             "pool", "0xED64", "full", "-", "mov.l pool value 0xED64")
        ]
        active = {4: 0}
        changed = resolver.promote_sub22e10_r4_argument(
            hits, active, 0x4893A, "sub_488BA", "sub_22E10"
        )
        self.assertTrue(changed)
        self.assertEqual(hits[0][2], "0x4893A")
        self.assertEqual(hits[0][4], "read")
        self.assertEqual(hits[0][5], "b")
        self.assertIn("query-dependent", hits[0][10])
        self.assertEqual(active, {})

    def test_unverified_helper_or_wrong_argument_register_is_not_promoted(self):
        for active, comment in (({4: 0}, "sub_23000"), ({3: 0}, "sub_22E10")):
            with self.subTest(active=active, comment=comment):
                hits = [
                    ("0xED64", "rom", "0x48930", "sub_488BA", "constant", "l",
                     "pool", "0xED64", "full", "-", "mov.l pool value 0xED64")
                ]
                self.assertFalse(resolver.promote_sub22e10_r4_argument(
                    hits, dict(active), 0x4893A, "sub_488BA", comment
                ))
                self.assertEqual(hits[0][4], "constant")


    def _run_synthetic_access_case(self, instructions, pool_bytes, target):
        with tempfile.TemporaryDirectory() as tmp:
            rom = bytearray(16)
            listing_lines = ["sub_0000:"]
            for pc, opcode, assembly in instructions:
                encoded = opcode.to_bytes(2, "big")
                rom[pc:pc + 2] = encoded
                listing_lines.append(f"{pc:08X} {opcode:04X} CODE {assembly}")
            for pool_pc, data in pool_bytes:
                rom[pool_pc:pool_pc + len(data)] = data
            listing_text = "\n".join(listing_lines) + "\n"

            rom_path = os.path.join(tmp, "fixture.bin")
            listing_path = os.path.join(tmp, "fixture.lst")
            targets_path = os.path.join(tmp, "targets.txt")
            hits_path = os.path.join(tmp, "hits.tsv")
            unresolved_path = os.path.join(tmp, "unresolved.tsv")
            with open(rom_path, "wb") as f:
                f.write(rom)
            with open(listing_path, "w", encoding="utf-8") as f:
                f.write(listing_text)
            with open(targets_path, "w", encoding="utf-8") as f:
                f.write(target + "\n")

            old_md5 = resolver.EXPECTED_ROM_MD5
            old_listing_sha = resolver.EXPECTED_LISTING_SHA256
            resolver.EXPECTED_ROM_MD5 = hashlib.md5(rom).hexdigest()
            resolver.EXPECTED_LISTING_SHA256 = hashlib.sha256(
                listing_text.encode("utf-8")
            ).hexdigest()
            try:
                result = resolver.run_indexer(
                    rom_path, listing_path, targets_path,
                    hits_path, unresolved_path
                )
            finally:
                resolver.EXPECTED_ROM_MD5 = old_md5
                resolver.EXPECTED_LISTING_SHA256 = old_listing_sha
            return result

    def test_synthetic_base_disp_read_and_write_direction(self):
        instructions = [
            (0x0000, 0xD202, "mov.l @(2,pc),r2"),
            (0x0002, 0x8420, "mov.b @(0,r2),r0"),
            (0x0004, 0x8020, "mov.b r0,@(0,r2)"),
            (0x0006, 0x0009, "nop"),
        ]
        hits, unresolved, matched, checked = self._run_synthetic_access_case(
            instructions, [(0x000C, bytes.fromhex("FFFF1DB4"))], "FFFF1DB4"
        )
        self.assertEqual(
            [(row[2], row[4], row[5], row[7]) for row in hits],
            [
                ("0x2", "read", "b", "FFFF1DB4"),
                ("0x4", "write", "b", "FFFF1DB4"),
            ],
        )
        self.assertEqual(unresolved, [])
        self.assertEqual((matched, checked), (2, 2))

    def test_synthetic_base_r0_reader_with_signed_movw_pointer(self):
        instructions = [
            (0x0000, 0x9C04, "mov.w @(4,pc),r12"),
            (0x0002, 0xE01B, "mov #0x1B,r0"),
            (0x0004, 0x02CC, "mov.b @(r0,r12),r2"),
            (0x0006, 0x0009, "nop"),
        ]
        hits, unresolved, matched, checked = self._run_synthetic_access_case(
            instructions, [(0x000C, bytes.fromhex("85C4"))], "FFFF85DF"
        )
        self.assertEqual(len(hits), 1)
        self.assertEqual(
            (hits[0][2], hits[0][4], hits[0][6], hits[0][7]),
            ("0x4", "read", "base_r0", "FFFF85C4"),
        )
        self.assertEqual(unresolved, [])
        self.assertEqual((matched, checked), (1, 1))


    def test_synthetic_conditional_join_preserves_unchanged_r13_base(self):
        with tempfile.TemporaryDirectory() as tmp:
            rom = bytearray(20)
            instructions = [
                (0x0000, 0xDD03, "mov.l @(3,pc),r13"),
                (0x0002, 0x8D02, "bt/s loc_000A"),
                (0x0004, 0x0009, "nop"),
                (0x0006, 0x0009, "nop"),
                (0x0008, 0x0009, "nop"),
                (0x000A, 0x60D0, "mov.b @r13,r0"),
            ]
            listing_lines = ["sub_0000:"]
            for pc, opcode, assembly in instructions:
                rom[pc:pc + 2] = opcode.to_bytes(2, "big")
                if pc == 0x0006:
                    listing_lines.append("loc_0006:")
                if pc == 0x000A:
                    listing_lines.append("loc_000A:")
                listing_lines.append(f"{pc:08X} {opcode:04X} CODE {assembly}")
            rom[0x0010:0x0014] = bytes.fromhex("FFFF1DB4")
            listing_text = "\n".join(listing_lines) + "\n"
            rom_path = os.path.join(tmp, "fixture.bin")
            listing_path = os.path.join(tmp, "fixture.lst")
            targets_path = os.path.join(tmp, "targets.txt")
            hits_path = os.path.join(tmp, "hits.tsv")
            unresolved_path = os.path.join(tmp, "unresolved.tsv")
            with open(rom_path, "wb") as f:
                f.write(rom)
            with open(listing_path, "w", encoding="utf-8") as f:
                f.write(listing_text)
            with open(targets_path, "w", encoding="utf-8") as f:
                f.write("FFFF1DB4\n")
            old_md5 = resolver.EXPECTED_ROM_MD5
            old_listing_sha = resolver.EXPECTED_LISTING_SHA256
            resolver.EXPECTED_ROM_MD5 = hashlib.md5(rom).hexdigest()
            resolver.EXPECTED_LISTING_SHA256 = hashlib.sha256(listing_text.encode("utf-8")).hexdigest()
            try:
                hits, unresolved, matched, checked = resolver.run_indexer(
                    rom_path, listing_path, targets_path, hits_path, unresolved_path
                )
            finally:
                resolver.EXPECTED_ROM_MD5 = old_md5
                resolver.EXPECTED_LISTING_SHA256 = old_listing_sha
            self.assertEqual(len(hits), 1)
            self.assertEqual((hits[0][2], hits[0][4], hits[0][7]), ("0xA", "read", "FFFF1DB4"))
            self.assertEqual(unresolved, [])
            self.assertEqual((matched, checked), (1, 1))

    def _run_synthetic_call_preservation(self, call_comment):
        with tempfile.TemporaryDirectory() as tmp:
            rom = bytearray(16)
            instructions = [
                (0x0000, 0xDD02, "mov.l @(2,pc),r13", ""),
                (0x0002, 0x420B, "jsr @r2", call_comment),
                (0x0004, 0x0009, "nop", ""),
                (0x0006, 0x60D0, "mov.b @r13,r0", ""),
            ]
            listing_lines = ["sub_0000:"]
            for pc, opcode, assembly, comment in instructions:
                rom[pc:pc + 2] = opcode.to_bytes(2, "big")
                suffix = f" ; {comment}" if comment else ""
                listing_lines.append(f"{pc:08X} {opcode:04X} CODE {assembly}{suffix}")
            rom[0x000C:0x0010] = bytes.fromhex("FFFF1DB4")
            listing_text = "\n".join(listing_lines) + "\n"
            rom_path = os.path.join(tmp, "fixture.bin")
            listing_path = os.path.join(tmp, "fixture.lst")
            targets_path = os.path.join(tmp, "targets.txt")
            hits_path = os.path.join(tmp, "hits.tsv")
            unresolved_path = os.path.join(tmp, "unresolved.tsv")
            with open(rom_path, "wb") as f:
                f.write(rom)
            with open(listing_path, "w", encoding="utf-8") as f:
                f.write(listing_text)
            with open(targets_path, "w", encoding="utf-8") as f:
                f.write("FFFF1DB4\n")
            old_md5 = resolver.EXPECTED_ROM_MD5
            old_listing_sha = resolver.EXPECTED_LISTING_SHA256
            resolver.EXPECTED_ROM_MD5 = hashlib.md5(rom).hexdigest()
            resolver.EXPECTED_LISTING_SHA256 = hashlib.sha256(listing_text.encode("utf-8")).hexdigest()
            try:
                result = resolver.run_indexer(rom_path, listing_path, targets_path, hits_path, unresolved_path)
            finally:
                resolver.EXPECTED_ROM_MD5 = old_md5
                resolver.EXPECTED_LISTING_SHA256 = old_listing_sha
            return result

    def test_synthetic_sub22e10_call_preserves_r13_base(self):
        hits, unresolved, matched, checked = self._run_synthetic_call_preservation("sub_22E10")
        self.assertEqual(len(hits), 1)
        self.assertEqual((hits[0][2], hits[0][4], hits[0][7]), ("0x6", "read", "FFFF1DB4"))
        self.assertEqual(unresolved, [])
        self.assertEqual((matched, checked), (1, 1))

    def test_synthetic_unknown_jsr_does_not_preserve_r13(self):
        hits, unresolved, matched, checked = self._run_synthetic_call_preservation("sub_23000")
        self.assertEqual(hits, [])
        self.assertEqual(len(unresolved), 1)
        self.assertEqual(unresolved[0][2], "0x6")
        self.assertEqual(unresolved[0][11], "unresolved base register")
        self.assertEqual((matched, checked), (1, 1))


    def test_synthetic_mac_test_and_shift_preserve_unrelated_r13_base(self):
        instructions = [
            (0x0000, 0xDD02, "mov.l @(2,pc),r13"),
            (0x0002, 0x0477, "mul.l r7,r4"),
            (0x0004, 0x021A, "sts macl,r2"),
            (0x0006, 0x2668, "tst r6,r6"),
            (0x0008, 0x4221, "shar r2"),
            (0x000A, 0x60D0, "mov.b @r13,r0"),
        ]
        hits, unresolved, matched, checked = self._run_synthetic_access_case(
            instructions, [(0x000C, bytes.fromhex("FFFF1DB4"))], "FFFF1DB4"
        )
        self.assertEqual(len(hits), 1)
        self.assertEqual((hits[0][2], hits[0][4], hits[0][7]), ("0xA", "read", "FFFF1DB4"))
        self.assertEqual(unresolved, [])
        self.assertEqual((matched, checked), (1, 1))


    def test_synthetic_nested_branch_retains_prior_conditional_target_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            rom = bytearray(0x20)
            instructions = [
                (0x0000, 0xD605, "mov.l @(5,pc),r6"),
                (0x0002, 0xE01B, "mov #0x1B,r0"),
                (0x0004, 0x8F02, "bf/s loc_000C"),
                (0x0006, 0x0009, "nop"),
                (0x0008, 0xA001, "bra loc_000E"),
                (0x000A, 0x0009, "nop"),
                (0x000C, 0x0654, "mov.b r5,@(r0,r6)"),
                (0x000E, 0x0009, "nop"),
            ]
            listing_lines = ["sub_0000:"]
            for pc, opcode, assembly in instructions:
                rom[pc:pc + 2] = opcode.to_bytes(2, "big")
                if pc == 0x000C:
                    listing_lines.append("loc_000C:")
                if pc == 0x000E:
                    listing_lines.append("loc_000E:")
                listing_lines.append(f"{pc:08X} {opcode:04X} CODE {assembly}")
            rom[0x0018:0x001C] = bytes.fromhex("FFFF85C4")
            listing_text = "\n".join(listing_lines) + "\n"
            rom_path = os.path.join(tmp, "fixture.bin")
            listing_path = os.path.join(tmp, "fixture.lst")
            targets_path = os.path.join(tmp, "targets.txt")
            hits_path = os.path.join(tmp, "hits.tsv")
            unresolved_path = os.path.join(tmp, "unresolved.tsv")
            with open(rom_path, "wb") as f:
                f.write(rom)
            with open(listing_path, "w", encoding="utf-8") as f:
                f.write(listing_text)
            with open(targets_path, "w", encoding="utf-8") as f:
                f.write("FFFF85DF\n")
            old_md5 = resolver.EXPECTED_ROM_MD5
            old_listing_sha = resolver.EXPECTED_LISTING_SHA256
            resolver.EXPECTED_ROM_MD5 = hashlib.md5(rom).hexdigest()
            resolver.EXPECTED_LISTING_SHA256 = hashlib.sha256(listing_text.encode("utf-8")).hexdigest()
            try:
                hits, unresolved, matched, checked = resolver.run_indexer(
                    rom_path, listing_path, targets_path, hits_path, unresolved_path
                )
            finally:
                resolver.EXPECTED_ROM_MD5 = old_md5
                resolver.EXPECTED_LISTING_SHA256 = old_listing_sha
            self.assertEqual(len(hits), 1)
            self.assertEqual((hits[0][2], hits[0][4], hits[0][7]), ("0xC", "write", "FFFF85C4"))
            self.assertEqual(unresolved, [])
            self.assertEqual((matched, checked), (1, 1))

    def test_unresolved_site_is_emitted_once_for_multiple_targets(self):
        with tempfile.TemporaryDirectory() as tmp:
            rom = bytearray.fromhex("6020 0009")
            listing_text = "sub_0000:\n00000000 6020 CODE mov.b @r2,r0\n00000002 0009 CODE nop\n"
            rom_path = os.path.join(tmp, "fixture.bin")
            listing_path = os.path.join(tmp, "fixture.lst")
            targets_path = os.path.join(tmp, "targets.txt")
            hits_path = os.path.join(tmp, "hits.tsv")
            unresolved_path = os.path.join(tmp, "unresolved.tsv")
            with open(rom_path, "wb") as f:
                f.write(rom)
            with open(listing_path, "w", encoding="utf-8") as f:
                f.write(listing_text)
            with open(targets_path, "w", encoding="utf-8") as f:
                f.write("FFFF85DF\nFFFF1DB4\n0x8550\n")
            old_md5 = resolver.EXPECTED_ROM_MD5
            old_listing_sha = resolver.EXPECTED_LISTING_SHA256
            resolver.EXPECTED_ROM_MD5 = hashlib.md5(rom).hexdigest()
            resolver.EXPECTED_LISTING_SHA256 = hashlib.sha256(listing_text.encode("utf-8")).hexdigest()
            try:
                hits, unresolved, matched, checked = resolver.run_indexer(
                    rom_path, listing_path, targets_path, hits_path, unresolved_path
                )
            finally:
                resolver.EXPECTED_ROM_MD5 = old_md5
                resolver.EXPECTED_LISTING_SHA256 = old_listing_sha
            self.assertEqual(hits, [])
            self.assertEqual(len(unresolved), 1)
            self.assertEqual(unresolved[0][0:2], ("UNRESOLVED", "unknown"))
            self.assertIn("FFFF85DF;FFFF1DB4;0x8550", unresolved[0][10])
            self.assertEqual((matched, checked), (1, 1))


if __name__ == "__main__":
    unittest.main(verbosity=2)
