#!/usr/bin/env python3
"""Synthetic regression tests for tools/romraider_ref_index.py (Milestone 3).

Uses strictly synthetic A2L, XML, ZIP, TSV, and SH-2 binary fixtures. Zero real ROMs.
"""

import contextlib
import io
import json
import struct
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import romraider_ref_index as ridx
import sh705x_discovery_v2 as d2
from sh7058_cross_rom_scanner import build_scan_export, discover_helpers, extract_calls


def _synth_sh2_rom(table_bytes: bytes, *, table_addr: int = 0x09000, extra_byte: int = 0xAA) -> bytes:
    rom = bytearray([0xFF] * 0x24000)
    # Tag metadata
    hdr = b"1SYNTH00\x00\x00DATABASE\x00SH705822N"
    rom[0x08300 : 0x08300 + len(hdr)] = hdr
    # Sub-search stub @ 0x20800
    struct.pack_into(">2H", rom, 0x20800, 0x000C, 0x000B)
    # Pattern B 2D_AXIS helper @ 0x20000 (4 x uint16 + uint8 axis)
    for idx, w in enumerate([0x4F22, 0x2F46, 0x6053, 0x656C, 0xD702, 0x470B, 0xE403, 0x8560, 0x000B, 0x0009]):
        struct.pack_into(">H", rom, 0x20000 + idx * 2, w)
    struct.pack_into(">I", rom, 0x20014, 0x00020800)

    rom[table_addr : table_addr + len(table_bytes)] = table_bytes
    rom[0x09100:0x09104] = bytes((10, 20, 30, 40))
    rom[0x0A000] = extra_byte

    struct.pack_into(">H", rom, 0x21000, 0x4F22)
    struct.pack_into(">H", rom, 0x21004, 0xD404)  # r4 = table_addr (@0x21018)
    struct.pack_into(">H", rom, 0x21006, 0xD505)  # r5 = 0x09100 (@0x2101C)
    struct.pack_into(">H", rom, 0x2100C, 0xD706)  # r7 = 0x20000 (@0x21028)
    struct.pack_into(">H", rom, 0x21010, 0x470B)
    struct.pack_into(">H", rom, 0x21012, 0x0009)
    struct.pack_into(">H", rom, 0x21014, 0x000B)
    struct.pack_into(">I", rom, 0x21018, table_addr)
    struct.pack_into(">I", rom, 0x2101C, 0x00009100)
    struct.pack_into(">I", rom, 0x21028, 0x00020000)
    return bytes(rom)


class RelationalA2lAndTsvTests(unittest.TestCase):
    def test_a2l_relational_preserves_duplicates_compu_tab_and_links(self):
        a2l = "\n".join([
            '/begin COMPU_METHOD COMP_IGN "Ign deg" RAT_FUNC "%6.2f" "deg"',
            '  COEFFS 0 2 -20 0 0 1',
            '/end COMPU_METHOD',
            '/begin COMPU_METHOD COMP_FLAG "Gear enum" TAB_VERB "%s" ""',
            '  COMPU_TAB_REF VTAB_GEAR',
            '/end COMPU_METHOD',
            '/begin COMPU_VTAB VTAB_GEAR "Gear text" TAB_VERB 2',
            '  0 "Neutral"',
            '  1 "First"',
            '/end COMPU_VTAB',
            '/begin RECORD_LAYOUT REC_U16_MAP',
            '  FNC_VALUES 1 UWORD ROW_DIR DIRECT',
            '  AXIS_PTS_X 2 UBYTE INDEX_INCR DIRECT',
            '/end RECORD_LAYOUT',
            '/begin CHARACTERISTIC mT_IGN_MAIN "Main timing" CURVE 0x09000 REC_U16_MAP 0 COMP_IGN -20 60',
            '  /begin AXIS_DESCR STD_AXIS r_RPM COMP_IGN 4 0 8000',
            '    AXIS_PTS_REF aX_RPM',
            '  /end AXIS_DESCR',
            '/end CHARACTERISTIC',
            '/begin CHARACTERISTIC mT_IGN_ALIAS "Duplicate addr decl" CURVE 0x09000 REC_U16_MAP 0 COMP_FLAG 0 10',
            '  /begin AXIS_DESCR FIX_AXIS r_LOAD COMP_IGN 4 0 100',
            '    FIX_AXIS_PAR 0 4 4',
            '  /end AXIS_DESCR',
            '/end CHARACTERISTIC',
            '/begin AXIS_PTS aX_RPM "RPM axis" 0x09100 r_RPM REC_U16_MAP 0 COMP_IGN 4 0 8000',
            '/end AXIS_PTS',
            '/begin MEASUREMENT r_RPM "Engine RPM" UWORD COMP_IGN 1 1 0 8000',
            '  ECU_ADDRESS 0xFFFF2000',
            '/end MEASUREMENT',
            '/begin FUNCTION FN_IGN "Ignition control"',
            '  /begin DEF_CHARACTERISTIC mT_IGN_MAIN /end DEF_CHARACTERISTIC',
            '  /begin IN_MEASUREMENT r_RPM /end IN_MEASUREMENT',
            '/end FUNCTION',
            '/begin GROUP GRP_SPARK "Spark group"',
            '  /begin REF_CHARACTERISTIC mT_IGN_MAIN mT_IGN_ALIAS /end REF_CHARACTERISTIC',
            '/end GROUP',
        ]).encode("cp932")

        parsed = ridx.parse_a2l_bytes_relational(a2l, source_path="synth.a2l")
        # Both duplicate symbols at 0x09000 retained!
        at_9000 = [s for s in parsed["symbols"] if s["address"] == 0x09000]
        self.assertEqual([s["name"] for s in at_9000], ["mT_IGN_MAIN", "mT_IGN_ALIAS"])
        self.assertIn("0x09000", parsed["duplicate_addresses"])
        self.assertEqual(at_9000[0]["unit"], "deg")
        self.assertEqual(at_9000[0]["linear_formula"], "x*0.5+10")
        self.assertEqual(at_9000[0]["datatype_hint"], "UWORD")
        self.assertEqual(at_9000[0]["axes"][0]["axis_pts_ref"], "aX_RPM")
        self.assertEqual(at_9000[0]["functions"], ["FN_IGN"])
        self.assertEqual(at_9000[0]["groups"], ["GRP_SPARK"])
        self.assertEqual(at_9000[1]["compu_tab_ref"], "VTAB_GEAR")
        self.assertEqual(parsed["compu_tabs"]["VTAB_GEAR"]["entries"][1]["out"], "First")
        meas = [s for s in parsed["symbols"] if s["record_kind"] == "MEASUREMENT"][0]
        self.assertEqual(meas["address_space"], "ram_ea")
        self.assertEqual(meas["functions"], ["FN_IGN"])

    def test_load_wo70017_metadata_tsv(self):
        tsv = (
            "donor_rom\tdonor_a2l_or_xml\tsource_hash\tobject_name\tobject_kind\taddress\tstorage_type\trecord_layout\tdimensions\tbyte_extent\taxis_1_ref\taxis_1_type\taxis_1_conversion\taxis_1_units\taxis_1_limits\taxis_2_ref\taxis_2_type\taxis_2_conversion\taxis_2_units\taxis_2_limits\tvalue_conversion\tvalue_units\traw_formula\tfunction_group\tparse_status\tunresolved_fields\n"
            "V6\tdonor.a2l\tabc\tmONE\tMAP\t0x00009000\tUWORD\tREC\t4x1\t8\tFIX_AXIS\tFIX_AXIS\tC\tRPM\t0..3\t\t\t\t\t\tC2\tdeg\tCOEFFS 0 1 0 0 0 1\tFN1\tOK\t\n"
            "V6\tdonor.a2l\tabc\tmTWO\tMAP\t0x00009000\tUWORD\tREC\t4x1\t8\tFIX_AXIS\tFIX_AXIS\tC\tRPM\t0..3\t\t\t\t\t\tC2\tdeg\tCOEFFS 0 1 0 0 0 1\tFN2\tOK\t\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "meta.tsv"
            p.write_text(tsv, encoding="utf-8")
            rows = ridx.load_wo70017_metadata_tsv(p)
            self.assertEqual(len(rows), 2)
            self.assertEqual([r["name"] for r in rows], ["mONE", "mTWO"])
            self.assertFalse(rows[0]["is_target_proof"])


class XmlCorpusCodeTwinAndMatcherTests(unittest.TestCase):
    def test_xml_zip_directory_conflicts_and_malformed_tolerance(self):
        xml_good_a = """<?xml version="1.0"?>
        <roms><rom><romid><ecuid>1SYNTH00</ecuid><xmlid>DEF_A</xmlid></romid>
        <scaling name="DegS" units="deg" expression="x*0.5" storagetype="uint16" endian="big"/>
        <table name="Spark_A" type="2D" storageaddress="0x09000" storagetype="uint16" scaling="DegS" sizey="4">
          <table type="Y Axis" storageaddress="0x09100" sizey="4"/>
        </table></rom></roms>"""
        xml_good_b = """<?xml version="1.0"?>
        <roms><rom><romid><ecuid>1SYNTH01</ecuid><xmlid>DEF_B</xmlid></romid>
        <table name="Spark_B_Alt" type="2D" storageaddress="0x09000" storagetype="uint8" sizey="8">
          <table type="Static Y Axis" sizey="8"><data>0</data><data>10</data></table>
        </table></rom></roms>"""
        xml_broken = "<roms><rom><unclosed>"

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            zpath = root / "defs.zip"
            with zipfile.ZipFile(zpath, "w") as zf:
                zf.writestr("sub/a.xml", xml_good_a)
                zf.writestr("sub/broken.xml", xml_broken)
            dir_p = root / "extra_xmls"
            dir_p.mkdir()
            (dir_p / "b.xml").write_text(xml_good_b, encoding="utf-8")

            docs = ridx.collect_xml_documents([zpath, dir_p])
            self.assertEqual(len(docs), 3)
            statuses = {Path(d["archive_member"] or d["source_path"]).name: d["status"] for d in docs}
            self.assertEqual(statuses["a.xml"], "ok")
            self.assertEqual(statuses["b.xml"], "ok")
            self.assertEqual(statuses["broken.xml"], "parse_error")

    def test_code_twin_relocated_payload_and_conflict_matching(self):
        payload = struct.pack(">4H", 111, 222, 333, 444)
        target_rom = _synth_sh2_rom(payload, table_addr=0x09000, extra_byte=0x01)
        # Code twin has identical code section (>=0x20000) & moved calibration table at 0x0B000
        donor_rom = _synth_sh2_rom(payload, table_addr=0x0B000, extra_byte=0x02)
        # Keep donor code section identical to target code section? Actually changing table_addr changed one pool word in 0x21018!
        # Let's build an exact code twin too (identical code section, only calibration byte at 0x0A000 differs)
        twin_rom = _synth_sh2_rom(payload, table_addr=0x09000, extra_byte=0x99)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            donor_p = root / "donor_reloc.bin"
            twin_p = root / "donor_twin.bin"
            donor_p.write_bytes(donor_rom)
            twin_p.write_bytes(twin_rom)

            x1 = root / "d1.xml"
            x2 = root / "d2.xml"
            x1.write_text('<roms><rom><romid><ecuid>1SYNTH00</ecuid></romid><table name="Ign_Main" type="2D" storageaddress="0x09000" storagetype="uint16" sizey="4"/></rom></roms>', encoding="utf-8")
            x2.write_text('<roms><rom><romid><ecuid>1SYNTH02</ecuid></romid><table name="Ign_AltName" type="2D" storageaddress="0x09000" storagetype="uint8" sizey="8"/></rom></roms>', encoding="utf-8")

            a2l_p = root / "donor.a2l"
            a2l_p.write_text('/begin CHARACTERISTIC mIGN "Ign" CURVE 0x09000 R 0 C 0 10\n/end CHARACTERISTIC\n', encoding="utf-8")

            ref_idx = ridx.build_reference_index(
                a2l_paths=[a2l_p],
                xml_inputs=[x1, x2],
                rom_paths=[donor_p, twin_p],
            )

            # Scan target ROM via Milestone 2 pipeline
            t_helpers = discover_helpers(target_rom)
            t_calls = extract_calls(target_rom, t_helpers)
            t_scan = build_scan_export("target.bin", target_rom, t_helpers, t_calls)
            t_cat = d2.to_per_address_catalogue(t_scan)

            matches = ridx.match_target_against_index(t_cat, ref_idx, target_rom=target_rom)
            # Twin ROM matched on exact code-region hash!
            self.assertEqual(len(matches["code_twin_matches"]), 1)
            self.assertEqual(matches["code_twin_matches"][0]["source_path"], str(twin_p))
            self.assertFalse(matches["code_twin_matches"][0]["is_target_proof"])

            cand_hits = matches["candidates"]["0x09000"]
            # Payload matched both at relocated 0x0B000 (donor) and same addr 0x09000 (twin)
            hit_addrs = sorted({p["address"] for p in cand_hits["payload_hits"]})
            self.assertEqual(hit_addrs, [0x09000, 0x0B000])
            # XML name + geometry conflicts surfaced explicitly without choosing a winner
            conflict_kinds = {c["kind"] for c in cand_hits["conflicts"]}
            self.assertIn("xml_name_conflict", conflict_kinds)
            self.assertIn("xml_geometry_conflict", conflict_kinds)

            # CLI build + query + determinism check
            idx_json_a = root / "idx_a.json"
            idx_json_b = root / "idx_b.json"
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc1 = ridx.main(["build", "--out", str(idx_json_a), "--a2l", str(a2l_p), "--xml", str(x1), "--rom", str(twin_p)])
                rc2 = ridx.main(["build", "--out", str(idx_json_b), "--a2l", str(a2l_p), "--xml", str(x1), "--rom", str(twin_p)])
            self.assertEqual((rc1, rc2), (0, 0))
            self.assertEqual(idx_json_a.read_text(encoding="utf-8"), idx_json_b.read_text(encoding="utf-8"))

            qbuf = io.StringIO()
            with contextlib.redirect_stdout(qbuf):
                rcq = ridx.main(["query", "--index", str(idx_json_a), "--addr", "0x09000", "--ecuid", "1SYNTH00"])
            self.assertEqual(rcq, 0)
            qres = json.loads(qbuf.getvalue())
            self.assertEqual(len(qres["xml_hits"]), 1)
            self.assertEqual(len(qres["a2l_hits"]), 1)
            self.assertEqual(len(qres["xml_doc_ids"]), 1)


if __name__ == "__main__":
    unittest.main()
