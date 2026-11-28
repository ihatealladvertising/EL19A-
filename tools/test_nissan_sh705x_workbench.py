#!/usr/bin/env python3
"""Synthetic regression tests for tools/nissan_sh705x_workbench.py.

Uses only in-memory/temporary synthetic fixtures (never real ROMs) so this suite
runs fast and deterministically in ordinary CI on Python 3.11+.
"""

import contextlib
import csv
import io
import json
import struct
import subprocess
import sys
import tempfile
import unittest
import zipfile
from argparse import Namespace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import nissan_sh705x_workbench as wb


def _encrypt_consult_dat_word(p: int) -> int:
    """Exact inverse of wb.decrypt_consult_dat_word for building synthetic .dat fixtures."""
    l0, r0 = (p >> 16) & 0xFFFF, p & 0xFFFF
    b = (r0 + 0x124D) & 0xFFFF
    f1 = (b + wb._rol16(b, 2) + 0xFFFF) & 0xFFFF
    cl = l0 ^ f1
    a = (cl + 0xCA1B) & 0xFFFF
    z = (a + wb._rol16(a, 1) + 0xFFFF) & 0xFFFF
    ch = r0 ^ (z ^ wb._rol16(z, 4))
    return (ch << 16) | cl


def _encode_s3_record(addr: int, data: bytes) -> str:
    cnt = 4 + len(data) + 1
    body = bytes([cnt]) + addr.to_bytes(4, "big") + data
    chk = (~sum(body)) & 0xFF
    return f"S3{body.hex().upper()}{chk:02X}"


def _encode_ihex_record(rec_type: int, addr: int, data: bytes) -> str:
    body = bytes([len(data), (addr >> 8) & 0xFF, addr & 0xFF, rec_type]) + data
    chk = ((-sum(body)) & 0xFF)
    return f":{body.hex().upper()}{chk:02X}"


def _build_dat_0x8015_frames(chunks: list[tuple[int, bytes]]) -> bytes:
    out = bytearray(b"SYNTHETIC KWP8015 DAT HEADER\r\n\x00\x00")
    for addr, payload in chunks:
        assert len(payload) % 4 == 0
        enc = bytearray(len(payload))
        for off in range(0, len(payload), 4):
            w = struct.unpack_from(">I", payload, off)[0]
            struct.pack_into(">I", enc, off, _encrypt_consult_dat_word(w))
        kwp_len = 6 + len(enc)
        body = bytes([0x80, 0x15, 0xFC, kwp_len, 0x34, 0x82]) + addr.to_bytes(3, "big") + bytes([len(enc)]) + enc
        out.extend(body)
        out.append(sum(body) & 0xFF)
    return bytes(out)


def _build_dat_percent6_frames(chunks: list[tuple[int, bytes]], sbl_count: int = 1) -> bytes:
    out = bytearray(b"SYNTHETIC PERCENT6 DAT\x00\x00")
    for idx in range(sbl_count):
        body = b"%6" + (0x800000 + idx).to_bytes(3, "big") + bytes([4]) + b"\x11\x22\x33\x44"
        out.extend(body)
        out.append(sum(body) & 0xFF)
    for rom_off, payload in chunks:
        assert rom_off % 32 == 0 and len(payload) % 4 == 0
        idx = 0x820000 + (rom_off // 32)
        enc = bytearray(len(payload))
        for off in range(0, len(payload), 4):
            w = struct.unpack_from(">I", payload, off)[0]
            struct.pack_into(">I", enc, off, _encrypt_consult_dat_word(w))
        body = b"%6" + idx.to_bytes(3, "big") + bytes([len(enc)]) + enc
        out.extend(body)
        out.append(sum(body) & 0xFF)
    return bytes(out)


def _install_synthetic_pattern_b_rom(size: int = 0x24000) -> bytearray:
    """Create a small synthetic SH-2 ROM containing a Pattern B 2D_AXIS helper and caller."""
    rom = bytearray([0xFF] * size)
    # Minimal IVT reset vector + a couple unique handlers
    struct.pack_into(">4I", rom, 0x0000, 0x00000400, 0xFFFFB000, 0x00000410, 0x00000420)

    # Sub-search stub @ 0x20800 with indexed byte read (0x000C shape)
    struct.pack_into(">2H", rom, 0x20800, 0x000C, 0x000B)

    # Pattern B 2D_AXIS helper @ 0x20000:
    # 4F22; 2F46; 6053; 656C (uint8 axis); D702 (mov.l pool -> 0x20800); 470B (jsr @r7); E403 (4 pts)
    # Body includes mov.w @(0,r6),r0 (0x8560) and RTS (0x000B)
    helper_words = [0x4F22, 0x2F46, 0x6053, 0x656C, 0xD702, 0x470B, 0xE403, 0x8560, 0x000B, 0x0009]
    for idx, word in enumerate(helper_words):
        struct.pack_into(">H", rom, 0x20000 + idx * 2, word)
    # D702 at pc=0x20008 -> ea = (0x20008 & ~3) + 4 + 2*4 = 0x20014
    struct.pack_into(">I", rom, 0x20014, 0x00020800)

    # Table data @ 0x09000 (4 x uint16 = 8B) and Axis data @ 0x09100 (4 x uint8)
    for idx, val in enumerate((100, 200, 300, 400)):
        struct.pack_into(">H", rom, 0x09000 + idx * 2, val)
    rom[0x09100:0x09104] = bytes((10, 20, 30, 40))

    # Scalar & RAM pointer inside caller function @ 0x21000..0x21030
    struct.pack_into(">H", rom, 0x05000, 0x1234)
    struct.pack_into(">H", rom, 0x21000, 0x4F22)  # prologue
    # Call site @ 0x21010:
    # 0x21004: D404 (r4 = @0x21018 = 0x00009000)
    # 0x21006: D504 (r5 = @0x2101C = 0x00009100)
    # 0x21008: D105 (r1 = @0x21020 = 0x00005000 scalar)
    # 0x2100A: D205 (r2 = @0x21024 = 0xFFFF1234 RAM)
    # 0x2100C: D706 (r7 = @0x21028 = 0x00020000 helper)
    # 0x2100E: 0009 (nop)
    # 0x21010: 470B (jsr @r7)
    # 0x21012: 0009 (nop)
    # 0x21014: 000B (rts)
    caller_words = [
        (0x21004, 0xD404),  # -> 0x21018
        (0x21006, 0xD505),  # -> 0x2101C
        (0x21008, 0xD105),  # -> 0x21020
        (0x2100A, 0xD206),  # -> 0x21024
        (0x2100C, 0xD706),  # -> 0x21028
        (0x2100E, 0x0009),
        (0x21010, 0x470B),
        (0x21012, 0x0009),
        (0x21014, 0x000B),
    ]
    for pc, word in caller_words:
        struct.pack_into(">H", rom, pc, word)
    struct.pack_into(">5I", rom, 0x21018, 0x00009000, 0x00009100, 0x00005000, 0xFFFF1234, 0x00020000)
    return rom


def _build_signed_512k_image() -> bytes:
    """Build a synthetic 512 KiB ROM with LOADER80, FID, RAMF, ck_std, ck_alt2, cal16, and main16."""
    rom = bytearray([0xFF] * 0x80000)
    # Bootloader tag @ 0x00100
    loader_tag = b"LOADER80\x00\x00DATABASE\x00SH7058"
    rom[0x00100 : 0x00100 + len(loader_tag)] = loader_tag

    # Application FID @ 0x08300 (with room for sumt/xort @ FID-8 / FID-4)
    fa = 0x08300
    fid_hdr = b"1EL19T00\x00\x00DATABASE\x00SH705822N"
    rom[fa : fa + len(fid_hdr)] = fid_hdr
    # Populate 3 RAMF pointers in [FID+0x3C .. FID+0x94) and zero unused slots
    rom[fa + 0x3C : fa + 0x94] = b"\x00" * (0x94 - 0x3C)
    struct.pack_into(">3I", rom, fa + 0x3C, 0xFFFF1000, 0xFFFF2000, 0xFFFF85DC)
    # ck_alt2 range [0x08204 .. 0x09000) (non-overlapping with cal16 @ 0x08200)
    alt_start, alt_end = 0x08204, 0x09000
    struct.pack_into(">2I", rom, fa + 0x94, alt_start, alt_end)

    # Put deterministic sample pattern into [0x08204 .. 0x08300) and [0x20004 .. 0x20100)
    for off in range(0x08204, 0x08280, 4):
        struct.pack_into(">I", rom, off, 0x11223344 + off)
    for off in range(0x20004, 0x20100, 4):
        struct.pack_into(">I", rom, off, 0x55667788 ^ off)

    # 1. Compute ck_alt2 @ (fa - 8, fa - 4) over [alt_start .. alt_end]
    # Keep rom[fa - 1] (low byte of xort) == 0x00 so regex does not merge it into FID tag
    x_pre_fix = 0
    for off in range(alt_start, alt_end + 1, 4):
        if off in (fa - 8, fa - 4, 0x08280):
            continue
        x_pre_fix ^= struct.unpack_from(">I", rom, off)[0]
    struct.pack_into(">I", rom, 0x08280, x_pre_fix & 0xFF)

    s_alt, x_alt = 0, 0
    for off in range(alt_start, alt_end + 1, 4):
        if off in (fa - 8, fa - 4):
            continue
        w = struct.unpack_from(">I", rom, off)[0]
        s_alt = (s_alt + w) & 0xFFFFFFFF
        x_alt ^= w
    struct.pack_into(">2I", rom, fa - 8, s_alt, x_alt)

    # 2. Compute cal16 @ 0x08200 over [0x08202 .. 0x10000) (after ck_alt2 words are written)
    cal16 = sum(struct.unpack_from(f">{(0x10000 - 0x08202) // 2}H", rom, 0x08202)) & 0xFFFF
    struct.pack_into(">H", rom, 0x08200, cal16)

    # 3. Compute main16 @ 0x10000 (split is 0x10000 for 512 KiB ROMs) over [0x10002 .. 0x80000)
    main16 = sum(struct.unpack_from(f">{(0x80000 - 0x10002) // 2}H", rom, 0x10002)) & 0xFFFF
    struct.pack_into(">H", rom, 0x10000, main16)

    # 4. Compute ck_std @ (0x00200 sumt, 0x00208 xort) over full 512 KiB ROM skipping self
    n_words = len(rom) // 4
    struct.pack_into(">I", rom, 0x00200, 0)
    struct.pack_into(">I", rom, 0x00208, 0)
    words = struct.unpack_from(f">{n_words}I", rom, 0)
    sum_all = sum(words) & 0xFFFFFFFF
    xor_all = 0
    for w in words:
        xor_all ^= w
    struct.pack_into(">I", rom, 0x00200, sum_all)
    struct.pack_into(">I", rom, 0x00208, xor_all)
    return bytes(rom)


class WorkbenchLoaderTests(unittest.TestCase):
    def test_load_s19_and_hex_bytes_place_records_and_pad_ff(self):
        s19_text = "\n".join([
            "S00600004844521B",
            _encode_s3_record(0x000010, bytes.fromhex("11223344")),
            _encode_s3_record(0x008020, bytes.fromhex("AABBCCDD")),
            "S70500000000FA",
        ]).encode("ascii")
        s19_rom = wb.load_s19_bytes(s19_text)
        self.assertEqual(len(s19_rom), 0x100000)
        self.assertEqual(s19_rom[0x10:0x14], bytes.fromhex("11223344"))
        self.assertEqual(s19_rom[0x8020:0x8024], bytes.fromhex("AABBCCDD"))
        self.assertEqual(s19_rom[0x0:0x4], b"\xFF\xFF\xFF\xFF")

        hex_text = "\n".join([
            _encode_ihex_record(4, 0, bytes.fromhex("0002")),  # upper = 0x00020000
            _encode_ihex_record(0, 0x1000, bytes.fromhex("DEADBEEF")),
            _encode_ihex_record(1, 0, b""),
        ]).encode("ascii")
        hex_rom = wb.load_hex_bytes(hex_text)
        self.assertEqual(len(hex_rom), 0x100000)
        self.assertEqual(hex_rom[0x21000:0x21004], bytes.fromhex("DEADBEEF"))
        self.assertEqual(hex_rom[0:4], b"\xFF\xFF\xFF\xFF")

    def test_consult_dat_feistel_0x8015_and_percent6_roundtrip(self):
        for sample in (0x00000000, 0x12345678, 0xDEADBEEF, 0xFFFFFFFF):
            enc = _encrypt_consult_dat_word(sample)
            self.assertEqual(wb.decrypt_consult_dat_word(enc), sample)

        pay_a = bytes(range(16))
        pay_b = bytes(range(16, 48))
        dat_a = _build_dat_0x8015_frames([(0x08200, pay_a)])
        img_a = wb.load_dat_bytes(dat_a)
        self.assertEqual(len(img_a), 0x80000)
        self.assertEqual(img_a[0x08200 : 0x08200 + len(pay_a)], pay_a)
        self.assertEqual(img_a[:0x08200], b"\xFF" * 0x08200)

        dat_b = _build_dat_percent6_frames([(0x09000, pay_b)], sbl_count=2)
        img_b = wb.load_dat_bytes(dat_b)
        self.assertEqual(len(img_b), 0x80000)
        self.assertEqual(img_b[0x09000 : 0x09000 + len(pay_b)], pay_b)

        # Corrupt trailing checksum in 0x8015 frame -> must raise ValueError
        bad_dat = bytearray(dat_a)
        bad_dat[-1] ^= 0x01
        with self.assertRaises(ValueError):
            wb.load_dat_bytes(bytes(bad_dat))

    def test_load_any_rom_zip_and_nonflat_container_rejections(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # Zip selects largest ROM file rather than small README
            dat = _build_dat_0x8015_frames([(0x08200, b"TESTDATA")])
            zpath = root / "bundle.zip"
            with zipfile.ZipFile(zpath, "w") as zf:
                zf.writestr("readme.txt", "ignored")
                zf.writestr("firmware.dat", dat)
            loaded = wb.load_any_rom(zpath)
            self.assertEqual(loaded[0x08200:0x08208], b"TESTDATA")

            # Known non-flat / media containers must fail with explicit errors
            cases = [
                ("osiris.bin", b"UpRev Osiris ROM File Ver 1.00  " + b"\x00" * 64 + b"AITuneDesc" + struct.pack("<III", 12, 32, 0) + b"\x00" * 64),
                ("winols.bin", b"WinOLS File" + b"\x00" * 32),
                ("image.png", b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\x0DIHDR" + struct.pack(">II", 640, 480)),
                ("doc.pdf", b"%PDF-1.4\n"),
                ("pic.jpg", b"\xff\xd8\xff\xe0"),
                ("tcm.dat", b"HDR\x80\x19\xfc\x08\x34\x82\x01\x00\x00\x02\xaa\xbb" + bytes([sum(b"\x80\x19\xfc\x08\x34\x82\x01\x00\x00\x02\xaa\xbb") & 0xFF])),
                ("kwp.dat", b"HDR\xb8\x15\xf1\x08\x00\x00\x00\x01\x02\x03" + bytes([sum(b"\xb8\x15\xf1\x08\x00\x00\x00\x01\x02\x03") & 0xFF])),
            ]
            for name, content in cases:
                p = root / name
                p.write_bytes(content)
                with self.subTest(container=name):
                    with self.assertRaises(ValueError):
                        wb.load_any_rom(p)


class WorkbenchMetadataAndChecksumTests(unittest.TestCase):
    def test_nissan_metadata_and_all_four_checksum_engines(self):
        rom = _build_signed_512k_image()
        fp = wb.rom_fingerprint(rom)
        meta = fp["nissan_meta"]
        self.assertEqual(meta["loader"], "LOADER80")
        self.assertEqual(meta["loader_addr"], 0x00100)
        self.assertEqual(meta["fid"], "1EL19T00")
        self.assertEqual(meta["fid_addr"], 0x08300)
        self.assertEqual(meta["fid_cpu"], "SH705822N")
        self.assertEqual(meta["ramf_ptrs"], 3)
        self.assertFalse(meta["bootblock_ff"])

        cks = fp["checksums"]
        self.assertIsNotNone(cks["ck_std"])
        self.assertEqual(cks["ck_std"]["status"], "OK")
        self.assertEqual((cks["ck_std"]["sumt"], cks["ck_std"]["xort"]), (0x00200, 0x00208))
        self.assertEqual(cks["ck_alt2"]["status"], "OK")
        self.assertEqual(cks["cal16"]["status"], "OK")
        self.assertEqual(cks["main16"]["status"], "OK")

        tags = wb.checksum_byte_tags(rom)
        self.assertEqual(tags[0x00200], "ck_std sumt")
        self.assertEqual(tags[0x08200], "LOADER80 cal16 [OK]")
        self.assertEqual(tags[0x10000], "LOADER80 main16 [OK]")

        # Mutate bytes inside cal16 and main16 spans and ensure failures are caught
        mutated = bytearray(rom)
        mutated[0x08206] ^= 0xFF
        mutated[0x20010] ^= 0xFF
        bad_cks = wb.verify_checksums(bytes(mutated))
        self.assertIsNone(bad_cks["ck_std"])
        self.assertEqual(bad_cks["ck_alt2"]["status"], "BAD")
        self.assertEqual(bad_cks["cal16"]["status"], "BAD")
        self.assertEqual(bad_cks["main16"]["status"], "BAD")


class WorkbenchParsersAndAnalysisTests(unittest.TestCase):
    def test_parse_a2l_rich_and_load_csv_addr_map(self):
        a2l_text = "\n".join([
            '/begin COMPU_METHOD COMP_HALF "" RAT_FUNC "%6.2f" "deg"',
            '  COEFFS 0 2 -10 0 0 1',
            '/end COMPU_METHOD',
            '/begin CHARACTERISTIC mT_IGN_MAIN "Main ignition" MAP 0x09000 REC 0 COMP_HALF 0 100',
            '/end CHARACTERISTIC',
            '/begin AXIS_PTS aX_RPM "Engine speed axis" 0x09100 S 0 COMP_HALF 4 0 8000',
            '/end AXIS_PTS',
            '/begin MEASUREMENT v_ECT "Coolant temp" UWORD COMP_HALF 1 100 -40 200',
            '  ECU_ADDRESS 0xFFFF1234',
            '/end MEASUREMENT',
        ])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a2l_p = root / "donor.a2l"
            a2l_p.write_bytes(a2l_text.encode("cp932"))
            parsed = wb.parse_a2l_rich(a2l_p)
            self.assertEqual(parsed["syms"][0x09000]["name"], "mT_IGN_MAIN")
            self.assertEqual(parsed["syms"][0x09000]["unit"], "deg")
            self.assertEqual(parsed["syms"][0x09000]["scale"], "x*0.5+5")
            self.assertEqual(parsed["syms"][0x09100]["kind"], "AXIS_PTS")
            self.assertEqual(parsed["meas"][0xFFFF1234]["name"], "v_ECT")

            csv_p = root / "cat.csv"
            csv_p.write_text("Address,Name\n0x09000,Spark_Main\n0X09100,Axis_RPM\n", encoding="utf-8")
            cmap = wb.load_csv_addr_map(csv_p)
            self.assertEqual(cmap[0x09000]["Name"], "Spark_Main")
            self.assertEqual(cmap[0x09100]["Name"], "Axis_RPM")
            self.assertEqual(wb.load_csv_addr_map(root / "missing.csv"), {})

    def test_summarize_tables_shared_axes_and_decode_rom_values(self):
        rom = bytearray(0xA000)
        struct.pack_into(">4h", rom, 0x9000, -10, 0, 250, -300)
        rom[0x9100:0x9104] = bytes((10, 20, 30, 40))

        # Reciprocal pair: 0x9000 uses 0x9100 as axis1 AND 0x9100 uses 0x9000 as axis1
        calls = [
            {
                "call_pc": 0x21000, "helper": 0x20000, "kind": "2D_AXIS",
                "elem_type": "int16", "dim1": 4, "dim2": 1,
                "axis1_type": "uint8", "axis2_type": "",
                "table": 0x9000, "axis1": 0x9100, "axis2": None,
            },
            {
                "call_pc": 0x21100, "helper": 0x20000, "kind": "2D_AXIS",
                "elem_type": "uint8", "dim1": 4, "dim2": 1,
                "axis1_type": "int16", "axis2_type": "",
                "table": 0x9100, "axis1": 0x9000, "axis2": None,
            },
        ]
        summary = wb.summarize_tables(bytes(rom), calls)
        self.assertEqual(summary[0x9000]["end"], 0x9007)  # pinned current inclusive end
        self.assertEqual(summary[0x9000]["shared_as_axis_of"], [0x9100])
        self.assertEqual(summary[0x9000]["reciprocal_with"], [0x9100])
        self.assertTrue(summary[0x9000]["nontrivial"])

        self.assertEqual(wb.decode_rom_values(bytes(rom), 0x9000, 4, 1, "int16"), [-10, 0, 250, -300])
        self.assertEqual(wb.decode_rom_values(bytes(rom), 0x9000, 0x1000, 1, "int16"), [])
        self.assertEqual(wb.norm_sym("mTTIGN_S#1"), "mTIGN_S")
        self.assertEqual(wb.norm_sym("mTTIGN_2"), "mTIGN")

    def test_func_profile_a2l_leads_and_raw_diff_clustering(self):
        rom = _install_synthetic_pattern_b_rom()
        helpers = wb.discover_helpers(bytes(rom))
        calls = wb.extract_calls(bytes(rom), helpers)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["table"], 0x09000)
        self.assertEqual(calls[0]["axis1"], 0x09100)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # Build donor HEX + S19 + matching A2Ls carrying identical signature & payload
            v6_hex = root / "v6.hex"
            jk_s19 = root / "jk.s19"
            v6_a2l = root / "v6.a2l"
            jk_a2l = root / "jk.a2l"

            # Encode synthetic Pattern B ROM chunks into HEX & S19
            hex_lines = [_encode_ihex_record(4, 0, b"\x00\x00")]
            for off in (0x05000, 0x09000, 0x09100):
                hex_lines.append(_encode_ihex_record(0, off, bytes(rom[off : off + 16])))
            for base in (0x20000, 0x20800, 0x21000):
                hex_lines.append(_encode_ihex_record(4, 0, (base >> 16).to_bytes(2, "big")))
                hex_lines.append(_encode_ihex_record(0, base & 0xFFFF, bytes(rom[base : base + 0x40])))
            hex_lines.append(_encode_ihex_record(1, 0, b""))
            v6_hex.write_text("\n".join(hex_lines), encoding="ascii")

            s19_lines = [
                _encode_s3_record(off, bytes(rom[off : off + 0x40]))
                for off in (0x05000, 0x09000, 0x09100, 0x20000, 0x20800, 0x21000)
            ]
            jk_s19.write_text("\n".join(s19_lines), encoding="ascii")

            for sym, p in (("mTT_SPARK", v6_a2l), ("mT_SPARK", jk_a2l)):
                p.write_text(
                    f'/begin CHARACTERISTIC {sym} "Spark" MAP 0x09000 R 0 COMP_X 0 90\n/end CHARACTERISTIC\n'
                    '/begin MEASUREMENT r_ECT "Temp" UWORD COMP_X 1 1 0 100\n  ECU_ADDRESS 0xFFFF1234\n/end MEASUREMENT\n',
                    encoding="ascii",
                )

            leads = wb.build_a2l_table_leads(bytes(rom), calls, v6_hex, v6_a2l, jk_s19, jk_a2l)
            self.assertTrue(leads["available"])
            self.assertIn(0x09000, leads["by_table"])
            self.assertTrue(leads["by_table"][0x09000][0]["consensus"])
            self.assertEqual(leads["by_table"][0x09000][0]["ram_leads"][:2], ["r_ECT", "r_ECT"])

            unavail = wb.build_a2l_table_leads(bytes(rom), calls, root / "missing.hex", v6_a2l, jk_s19, jk_a2l)
            self.assertFalse(unavail["available"])

        # Raw diff clustering + formatting
        ra = bytearray(64)
        rb = bytearray(64)
        ra[10], rb[10] = 5, 12
        ra[12], rb[12] = 7, 9
        ra[40:44], rb[40:44] = b"TUNE", b"MODS"
        covered = bytearray(64)
        clusters = wb._cluster_raw_diffs(bytes(ra), bytes(rb), 0, 64, covered, gap=2)
        self.assertEqual(clusters, [(10, 12), (40, 43)])
        self.assertEqual(wb._format_cluster_values(b"\x05", b"\x0C", 10), "u8 5 -> 12 (+7)")
        self.assertIn('ASCII "TUNE" -> "MODS"', wb._format_cluster_values(b"TUNE", b"MODS", 40))


class WorkbenchCliSmokeTests(unittest.TestCase):
    def test_scan_diff_inspect_and_audit_subcommands_on_synthetic_fixtures(self):
        rom_a = _install_synthetic_pattern_b_rom()
        rom_b = bytearray(rom_a)
        rom_b[0x09002] = 0x55  # modify inside discovered table 0x09000..0x09007
        rom_b[0x0A000] = 0x77  # modify raw byte outside discovered tables

        xml_text = (
            "<rom><table name=\"SynthSpark\" type=\"2D\" storagetype=\"uint16\" "
            "storageaddress=\"0x09000\" sizex=\"4\" sizey=\"1\">"
            "<table type=\"Y Axis\" storageaddress=\"0x09100\"/></table></rom>"
        )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pa = root / "synth_a.bin"
            pb = root / "synth_b.bin"
            xml_p = root / "synth.xml"
            cat_p = root / "cat.csv"
            mat_p = root / "mat.csv"
            tsv_scan = root / "scan.tsv"
            json_scan = root / "scan.json"
            tsv_audit = root / "audit.tsv"

            pa.write_bytes(rom_a)
            pb.write_bytes(rom_b)
            xml_p.write_text(xml_text, encoding="utf-8")
            cat_p.write_text("Address,Name\n0x09000,SynthSpark\n", encoding="utf-8")
            mat_p.write_text("Address,InScope\n0x09000,YES\n", encoding="utf-8")

            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                wb.cmd_scan(Namespace(rom=str(pa), tsv=str(tsv_scan), json=str(json_scan)))
            scan_out = buf.getvalue()
            self.assertIn("1 resolved -> 1 unique tables", scan_out)
            scan_json = json.loads(json_scan.read_text(encoding="utf-8"))
            self.assertIn("0x09000", scan_json["tables"])
            with tsv_scan.open(encoding="utf-8") as f:
                scan_rows = list(csv.DictReader(f, delimiter="\t"))
            self.assertEqual(len(scan_rows), 1)
            self.assertEqual(scan_rows[0]["table"], "0x09000")

            diff_buf = io.StringIO()
            with contextlib.redirect_stdout(diff_buf):
                wb.cmd_diff(Namespace(rom_a=str(pa), rom_b=str(pb), xml=str(xml_p), raw_limit=10))
            diff_out = diff_buf.getvalue()
            self.assertIn("Same-addr + DIFFERING payload: 1", diff_out)
            self.assertIn("0x0A000", diff_out)

            for target in ("0x09000", "0x21000", "0xFFFF1234"):
                ins_buf = io.StringIO()
                with contextlib.redirect_stdout(ins_buf):
                    wb.cmd_inspect(Namespace(
                        target=target, rom=str(pa), xml=str(xml_p),
                        catalog=str(cat_p), matrix=str(mat_p),
                        v6_hex=str(root / "no.hex"), v6_a2l=str(root / "no.a2l"),
                        juke_s19=str(root / "no.s19"), juke_a2l=str(root / "no.a2l"),
                    ))
                self.assertTrue(ins_buf.getvalue().strip())

            aud_buf = io.StringIO()
            with contextlib.redirect_stdout(aud_buf):
                wb.cmd_audit(Namespace(
                    el19a=str(pa), xml=str(xml_p), catalog=str(cat_p), matrix=str(mat_p),
                    el13a=str(root / "no1.bin"), w83b=str(root / "no2.bin"), ee310=str(root / "no3.bin"),
                    v6_hex=str(root / "no.hex"), v6_a2l=str(root / "no.a2l"),
                    juke_s19=str(root / "no.s19"), juke_a2l=str(root / "no.a2l"),
                    tsv=str(tsv_audit),
                ))
            self.assertIn("Overlap: 1 in XML", aud_buf.getvalue())
            with tsv_audit.open(encoding="utf-8") as f:
                audit_rows = list(csv.DictReader(f, delimiter="\t"))
            self.assertEqual(len(audit_rows), 1)
            self.assertEqual(audit_rows[0]["xml_name"], "SynthSpark")


class Milestone5IntegrationTests(unittest.TestCase):
    def test_scan_catalogue_manifest_and_export_xml_subcommands(self):
        import hashlib
        import xml.etree.ElementTree as ET

        rom = bytes(_install_synthetic_pattern_b_rom())
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rom_p = root / "synth.bin"
            cat_p = root / "synth_cat.json"
            man_p = root / "synth_man.json"
            idx_p = root / "synth_ref.json"
            xml_p = root / "donor.xml"
            out_dir = root / "xml_out"

            rom_p.write_bytes(rom)
            xml_p.write_text(
                '<roms><rom><romid><ecuid>1SYNTH</ecuid></romid>'
                '<table name="Donor_Spark" type="2D" storageaddress="0x09000" storagetype="uint16" sizey="4"/>'
                '</rom></roms>',
                encoding="utf-8",
            )

            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                wb.cmd_scan(Namespace(
                    rom=str(rom_p), tsv=None, json=None,
                    catalogue=str(cat_p), manifest=str(man_p),
                    enhanced_window=128, include_scalars=True,
                ))
                wb.cmd_ref_index(Namespace(
                    action="build", out=str(idx_p),
                    a2l=[], tsv=[], xml=[str(xml_p)], rom=[str(rom_p)],
                ))
                wb.cmd_export_xml(Namespace(
                    rom=str(rom_p), catalogue=None, ref_index=str(idx_p),
                    out_dir=str(out_dir), stem="wb_synth",
                    enhanced_window=128, include_scalars=True,
                    allow_provisional_donor_names=False,
                    skip_trivial=False, no_strict=False,
                    index_dir=None, expected_el19a_sha256=wb.EL19A_PINNED_SHA256,
                ))

            cat = json.loads(cat_p.read_text(encoding="utf-8"))
            man = json.loads(man_p.read_text(encoding="utf-8"))
            self.assertEqual(len(cat["candidates"]), 1)
            self.assertIn("scalar_candidates", cat)
            self.assertEqual(man["outputs"][0]["sha256"], hashlib.sha256(cat_p.read_bytes()).hexdigest())

            prev_xml = out_dir / "wb_synth.preview.xml"
            val_doc = json.loads((out_dir / "wb_synth.validation.json").read_text(encoding="utf-8"))
            self.assertTrue(val_doc["valid"])
            self.assertEqual(val_doc["summary"]["table_count"], 1)
            el = ET.fromstring(prev_xml.read_text(encoding="utf-8")).find("./rom/table")
            self.assertTrue(el.attrib["name"].startswith("RAW_0x09000"))

    def test_hash_validated_el19a_index_and_dual_matrix_reconciliation(self):
        import hashlib

        rom = bytes(_install_synthetic_pattern_b_rom())
        rom_sha = hashlib.sha256(rom).hexdigest()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            idx_dir = root / "INDEX"
            idx_dir.mkdir()
            (idx_dir / "catalog_179_consumer_summary.tsv").write_text(
                "address\tdimensions\tstorage\tevidence_tier\ttraced_query_inputs\tcatalog_dest_ram\n"
                "0x09000\t4x1\tUWORD\tQuery-Traced\tr5<-FFFF1234\tFFFF1054\n",
                encoding="utf-8",
            )
            (idx_dir / "function_gbr_map.tsv").write_text(
                "function\tpc\tgbr_base\tspace\n"
                "sub_21000\t0x21002\tFFFF8200\tRAM\n",
                encoding="utf-8",
            )
            (idx_dir / "obd_mode01_pid_map.tsv").write_text(
                "pid_hex\tsae_name\tkline_ram_sources\tcan_ram_sources\n"
                "0x0C\tEngineRPM\tFFFF1234\t-\n",
                encoding="utf-8",
            )

            # Matching SHA succeeds
            ok_ctx = wb.load_hash_validated_el19a_context(rom, expected_rom_sha256=rom_sha, index_dir=idx_dir)
            self.assertEqual(ok_ctx["status"], "available")
            self.assertIn(0x09000, ok_ctx["catalog_by_addr"])
            self.assertIn(0x21000, ok_ctx["gbr_by_func"])
            self.assertIn("FFFF1234", ok_ctx["ram_to_diag"])

            # Mismatched SHA refuses index silently and reports unavailable
            bad_ctx = wb.load_hash_validated_el19a_context(rom, expected_rom_sha256="0" * 64, index_dir=idx_dir)
            self.assertEqual(bad_ctx["status"], "unavailable")
            self.assertEqual(bad_ctx["reason"], "rom_hash_mismatch")

            # Dual-matrix & dual-XML reconciliation preserves conflicts
            x1 = root / "r1.xml"
            x2 = root / "best.xml"
            m1 = root / "m_r1.csv"
            m2 = root / "m_raw.csv"
            cand = root / "cand.csv"
            x1.write_text('<rom><table name="RawTbl" type="2D" scaling="Raw_UWORD" storageaddress="0x09000" storagetype="uint16" sizey="4"/></rom>', encoding="utf-8")
            x2.write_text('<rom><table name="BestSpark" type="2D" scaling="DegScale" storageaddress="0x09000" storagetype="uint16" sizey="4"/></rom>', encoding="utf-8")
            m1.write_text("address,baseline_name,current_scaling,release_disposition\n0x09000,Tbl,DegScale,INCLUDE — PROVISIONAL\n", encoding="utf-8")
            m2.write_text("address,baseline_name,current_scaling,release_disposition\n0x09000,Tbl,Raw_UWORD,INCLUDE — RAW/PROVISIONAL\n", encoding="utf-8")
            cand.write_text("address,candidate_name,dimensions,storage,conversion,status\n9000,SparkCand,4,UWORD,x*0.5,THEORY\n", encoding="utf-8")

            rec = wb.reconcile_definition_sources(
                xml_paths=[x1, x2],
                matrix_paths=[m1, m2],
                candidate_path=cand,
                scanner_tables={0x09000: {"dim1": 4, "dim2": 1, "elem_type": "uint16", "kind": "2D_AXIS"}},
            )
            self.assertEqual(rec["address_count"], 1)
            conflicts = rec["records"][0]["conflicts"]
            self.assertIn("xml_name_conflict", conflicts)
            self.assertIn("scaling_conflict", conflicts)
            self.assertIn("disposition_conflict", conflicts)
            self.assertIn("candidate_register", rec["records"][0]["sources"])

    def test_direct_cli_invocation_avoids_circular_import(self):
        import subprocess
        import sys

        wb_path = Path(__file__).resolve().parent / "nissan_sh705x_workbench.py"
        with tempfile.TemporaryDirectory() as tmp:
            idx_p = Path(tmp) / "idx.json"
            idx_p.write_text(json.dumps({
                "lookups": {
                    "xml_by_addr": {"0x09000": [{"name": "SynthTbl"}]},
                    "a2l_by_addr": {},
                    "xml_by_ecuid": {"1SYNTH": ["xml0"]},
                }
            }), encoding="utf-8")
            proc = subprocess.run(
                [sys.executable, str(wb_path), "ref-index", "query", "--index", str(idx_p), "--ecuid", "1SYNTH", "--addr", "0x09000"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, msg=proc.stderr)
            out = json.loads(proc.stdout)
            self.assertEqual(out["ecuid"], "1SYNTH")
            self.assertEqual(out["address_hex"], "0x09000")
            self.assertEqual(out["xml_hits"][0]["name"], "SynthTbl")


class RomIndexCliRegistrationTests(unittest.TestCase):
    def test_rom_index_build_and_query_commands_are_registered(self):
        wb_path = Path(__file__).resolve().parent / "nissan_sh705x_workbench.py"
        proc = subprocess.run(
            [sys.executable, str(wb_path), "--help"],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("rom-index", proc.stdout)
        sub = subprocess.run(
            [sys.executable, str(wb_path), "rom-index", "--help"],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(sub.returncode, 0, sub.stderr)
        self.assertIn("build", sub.stdout)
        self.assertIn("query", sub.stdout)


if __name__ == "__main__":
    unittest.main()
