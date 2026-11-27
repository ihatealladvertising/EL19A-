#!/usr/bin/env python3
"""Synthetic regression tests for tools/romraider_xml_export.py (Milestone 4).

Tests 4-dimension confidence resolution, strict Tier D raw naming/scaling barriers,
explicit shared axes vs computed implicit grid stubs (`Static Y Axis`), XML validation,
CALIBRATIONS/ write protection, strict atomic preview preservation, and end-to-end
CLI execution on strictly synthetic fixtures (zero real ROMs).
"""

import contextlib
import io
import json
import struct
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import romraider_ref_index as ridx
import romraider_xml_export as rxml
import sh705x_discovery_v2 as d2
from sh7058_cross_rom_scanner import (
    HelperSpec,
    build_scan_export,
    discover_helpers,
    extract_calls,
)


def _synth_multi_helper_rom() -> bytes:
    """Build a synthetic SH-2 ROM containing Pattern B (2D_AXIS) + Pattern A (2D_IMPL)."""
    rom = bytearray([0xFF] * 0x24000)
    hdr = b"1SYNTHM4\x00\x00DATABASE\x00SH705822N"
    rom[0x08300 : 0x08300 + len(hdr)] = hdr
    # Tag FID pointer metadata? Not strictly needed, parse_nissan_metadata handles gracefully

    # Sub-search stub @ 0x20800
    struct.pack_into(">2H", rom, 0x20800, 0x000C, 0x000B)

    # 1) Pattern B 2D_AXIS helper @ 0x20000 (4 x uint16 + uint8 axis)
    for idx, w in enumerate([0x4F22, 0x2F46, 0x6053, 0x656C, 0xD702, 0x470B, 0xE403, 0x8560, 0x000B, 0x0009]):
        struct.pack_into(">H", rom, 0x20000 + idx * 2, w)
    struct.pack_into(">I", rom, 0x20014, 0x00020800)

    # 2) Pattern A 2D_IMPL u8 helper @ 0x20040 (16 x uint16, max_val=240 @ 0x20056 -> step 16)
    stub_impl = [0x9009, 0x655C, 0x3502, 0x8902, 0xD603, 0x462B, 0x0009, 0x741E, 0x000B, 0x6041]
    for idx, w in enumerate(stub_impl):
        struct.pack_into(">H", rom, 0x20040 + idx * 2, w)
    struct.pack_into(">H", rom, 0x20056, 240)
    struct.pack_into(">I", rom, 0x20058, 0x00020800)

    # Non-trivial payloads in cal region (< 0x20000)
    # 0x09000: shared-axis 2D table #1 (4 x u16)
    struct.pack_into(">4H", rom, 0x09000, 100, 200, 300, 400)
    # 0x09020: shared-axis 2D table #2 (4 x u16)
    struct.pack_into(">4H", rom, 0x09020, 111, 222, 333, 444)
    # 0x09100: shared uint8 axis (4 pts)
    rom[0x09100:0x09104] = bytes((10, 20, 30, 40))
    # 0x09200: 2D_IMPL table (16 x u16 = 32B)
    for i in range(16):
        struct.pack_into(">H", rom, 0x09200 + i * 2, 1000 + i * 50)
    # 0x09300: trivial constant 2D_AXIS table (all zeros -> <=2 distinct byte values)
    rom[0x09300:0x09308] = b"\x00" * 8

    # Caller @ 0x21000 invokes Pattern B on 0x09000 (shared axis 0x09100)
    struct.pack_into(">H", rom, 0x21000, 0x4F22)
    struct.pack_into(">H", rom, 0x21004, 0xD404)  # r4 = 0x09000 (@ 0x21018)
    struct.pack_into(">H", rom, 0x21006, 0xD505)  # r5 = 0x09100 (@ 0x2101C)
    struct.pack_into(">H", rom, 0x2100C, 0xD706)  # r7 = 0x20000 (@ 0x21028)
    struct.pack_into(">H", rom, 0x21010, 0x470B)
    struct.pack_into(">H", rom, 0x21012, 0x0009)
    struct.pack_into(">H", rom, 0x21014, 0x000B)
    struct.pack_into(">I", rom, 0x21018, 0x00009000)
    struct.pack_into(">I", rom, 0x2101C, 0x00009100)
    struct.pack_into(">I", rom, 0x21028, 0x00020000)

    # Caller @ 0x21040 invokes Pattern B on 0x09020 (same shared axis 0x09100)
    struct.pack_into(">H", rom, 0x21040, 0x4F22)
    struct.pack_into(">H", rom, 0x21044, 0xD404)  # r4 = 0x09020 (@ 0x21058)
    struct.pack_into(">H", rom, 0x21046, 0xD505)  # r5 = 0x09100 (@ 0x2105C)
    struct.pack_into(">H", rom, 0x2104C, 0xD706)  # r7 = 0x20000 (@ 0x21068)
    struct.pack_into(">H", rom, 0x21050, 0x470B)
    struct.pack_into(">H", rom, 0x21052, 0x0009)
    struct.pack_into(">H", rom, 0x21054, 0x000B)
    struct.pack_into(">I", rom, 0x21058, 0x00009020)
    struct.pack_into(">I", rom, 0x2105C, 0x00009100)
    struct.pack_into(">I", rom, 0x21068, 0x00020000)

    # Caller @ 0x21080 invokes Pattern B on trivial 0x09300 (same axis 0x09100)
    struct.pack_into(">H", rom, 0x21080, 0x4F22)
    struct.pack_into(">H", rom, 0x21084, 0xD404)  # r4 = 0x09300 (@ 0x21098)
    struct.pack_into(">H", rom, 0x21086, 0xD505)  # r5 = 0x09100 (@ 0x2109C)
    struct.pack_into(">H", rom, 0x2108C, 0xD706)  # r7 = 0x20000 (@ 0x210A8)
    struct.pack_into(">H", rom, 0x21090, 0x470B)
    struct.pack_into(">H", rom, 0x21092, 0x0009)
    struct.pack_into(">H", rom, 0x21094, 0x000B)
    struct.pack_into(">I", rom, 0x21098, 0x00009300)
    struct.pack_into(">I", rom, 0x2109C, 0x00009100)
    struct.pack_into(">I", rom, 0x210A8, 0x00020000)

    # Caller @ 0x210C0 invokes Pattern A 2D_IMPL on 0x09200
    struct.pack_into(">H", rom, 0x210C0, 0x4F22)
    struct.pack_into(">H", rom, 0x210C4, 0xD404)  # r4 = 0x09200 (@ 0x210D8)
    struct.pack_into(">H", rom, 0x210CC, 0xD705)  # r7 = 0x20040 (@ 0x210E4)
    struct.pack_into(">H", rom, 0x210D0, 0x470B)
    struct.pack_into(">H", rom, 0x210D2, 0x0009)
    struct.pack_into(">H", rom, 0x210D4, 0x000B)
    struct.pack_into(">I", rom, 0x210D8, 0x00009200)
    struct.pack_into(">I", rom, 0x210E4, 0x00020040)

    return bytes(rom)


def _synthetic_catalogue_and_xref():
    """Minimal structured catalogue exercising all 4 confidence dimensions."""
    cat = {
        "schema": d2.SCHEMA_CATALOGUE_V1,
        "output_schema_version": d2.DATA_MODEL_VERSION,
        "manifest": {"input": {"decoded_rom_sha256": "a" * 64, "decoded_rom_size_bytes": 0x24000}},
        "axes": [
            {
                "axis_id": "ax1",
                "address": 0x09100,
                "address_hex": "0x09100",
                "axis_type": "uint8",
                "count": 4,
                "shared_count": 2,
            }
        ],
        "observations": [
            {"call_pc": 0x22999, "call_pc_hex": "0x22999", "base": None, "resolution_status": "unresolved_base", "helper_hex": "0x20000", "helper_kind": "2D_AXIS"}
        ],
        "scalar_candidates": [{"address": 0x05200, "address_hex": "0x05200"}],
        "candidates": [
            {
                "candidate_id": "c1",
                "base": 0x09000,
                "base_hex": "0x09000",
                "address_space": "rom_ea",
                "call_pcs": [0x21010, 0x21020],
                "helper_addresses": [0x20000],
                "geometry_conflict": False,
                "axis1_conflict": False,
                "axis2_conflict": False,
                "axis_links": [{"role": "axis1", "axis_id": "ax1"}],
                "geometry_variants": [{
                    "helper_kind": "2D_AXIS",
                    "element_type": "uint16",
                    "dim1": 4,
                    "dim2": 1,
                    "byte_length": 8,
                    "end_exclusive": 0x09008,
                    "in_bounds": True,
                    "distinct_byte_values": 6,
                }],
            },
            {
                "candidate_id": "c2_conflict_geom",
                "base": 0x09400,
                "base_hex": "0x09400",
                "address_space": "rom_ea",
                "call_pcs": [0x21100],
                "helper_addresses": [0x20000],
                "geometry_conflict": True,
                "axis1_conflict": False,
                "axis2_conflict": False,
                "axis_links": [],
                "geometry_variants": [
                    {"helper_kind": "2D_AXIS", "element_type": "uint16", "dim1": 4, "dim2": 1, "byte_length": 8, "end_exclusive": 0x09408, "in_bounds": True},
                    {"helper_kind": "2D_AXIS", "element_type": "uint8", "dim1": 8, "dim2": 1, "byte_length": 8, "end_exclusive": 0x09408, "in_bounds": True},
                ],
            },
            {
                "candidate_id": "c3_oob",
                "base": 0x23FFC,
                "base_hex": "0x23FFC",
                "address_space": "rom_ea",
                "call_pcs": [],
                "helper_addresses": [0x20000],
                "geometry_conflict": False,
                "axis1_conflict": False,
                "axis2_conflict": False,
                "axis_links": [],
                "geometry_variants": [
                    {"helper_kind": "2D_AXIS", "element_type": "uint16", "dim1": 4, "dim2": 1, "byte_length": 8, "end_exclusive": 0x24004, "in_bounds": False},
                ],
            },
            {
                "candidate_id": "c4_verified",
                "base": 0x09600,
                "base_hex": "0x09600",
                "address_space": "rom_ea",
                "call_pcs": [0x21200],
                "helper_addresses": [0x20000],
                "geometry_conflict": False,
                "axis1_conflict": False,
                "axis2_conflict": False,
                "axis_links": [{"role": "axis1", "axis_id": "ax1"}],
                "geometry_variants": [
                    {"helper_kind": "2D_AXIS", "element_type": "uint16", "dim1": 4, "dim2": 1, "byte_length": 8, "end_exclusive": 0x09608, "in_bounds": True, "distinct_byte_values": 8},
                ],
            },
        ],
    }
    xref = {
        "code_twin_matches": [{"source_path": "twin.bin", "code_sha256": "b" * 64, "is_target_proof": False}],
        "candidates": {
            "0x09000": {
                "xml_address_hits": [{"name": "Donor_Spark_Main", "source_path": "d.xml"}],
                "a2l_same_address_hits": [{"name": "mT_SPARK", "source_path": "d.a2l"}],
                "payload_hits": [{"address": 0x0B000, "nontrivial": True}],
                "conflicts": [],
            },
            "0x09600": {
                "xml_address_hits": [{"name": "Donor_Fuel_Main"}],
                "a2l_same_address_hits": [],
                "payload_hits": [],
                "conflicts": [{"kind": "xml_name_conflict"}],
            },
        },
    }
    return cat, xref


class ConfidenceBarrierAndPreviewExportTests(unittest.TestCase):
    def test_four_dimension_confidence_barrier_and_conflict_routing(self):
        cat, xref = _synthetic_catalogue_and_xref()
        res = rxml.resolve_candidate_evidence(
            cat,
            xref,
            target_verified_semantics={
                "0x09600": {
                    "name": "Target_Verified_Fuel",
                    "category": "Verified Target Tables",
                    "scaling": {
                        "name": "Fuel_Ms",
                        "units": "ms",
                        "expression": "x*0.01",
                        "to_byte": "x/0.01",
                        "format": "0.00",
                        "storagetype": "uint16",
                        "endian": "big",
                    },
                }
            },
        )
        by_addr = {r["address_hex"]: r for r in res["resolved_candidates"]}

        # Exact code twin + XML + A2L + nontrivial payload STILL yields provisional_donor_lead!
        c1 = by_addr["0x09000"]
        self.assertEqual(c1["structural_confidence"], "verified_in_bounds")
        self.assertEqual(c1["crossref_confidence"], "exact_code_twin_with_refs")
        self.assertEqual(c1["runtime_confidence"], "multi_call_backed")
        self.assertEqual(c1["semantic_confidence"], "provisional_donor_lead")
        self.assertEqual(c1["export_eligibility"], "eligible_raw_or_provisional")

        # Conflicting geometry held cleanly
        c2 = by_addr["0x09400"]
        self.assertEqual(c2["structural_confidence"], "conflicting_geometry")
        self.assertEqual(c2["runtime_confidence"], "helper_call_backed")
        self.assertEqual(c2["export_eligibility"], "hold_for_conflict")

        # OOB excluded cleanly
        c3 = by_addr["0x23FFC"]
        self.assertEqual(c3["structural_confidence"], "out_of_bounds")
        self.assertEqual(c3["runtime_confidence"], "literal_only")
        self.assertEqual(c3["export_eligibility"], "excluded_invalid_span")

        # Only explicit target_verified_semantics reaches target_verified
        c4 = by_addr["0x09600"]
        self.assertEqual(c4["crossref_confidence"], "donor_conflict")
        self.assertEqual(c4["semantic_confidence"], "target_verified")
        self.assertEqual(c4["export_eligibility"], "eligible_verified")

        # Default preview keeps 0x09000 as RAW_* with Raw_UWORD, routes 0x09400 + 0x23FFC + obs base=None to unresolved
        xml_def, prov_def, val_def, unres_def = rxml.generate_romraider_preview(cat, res)
        self.assertTrue(val_def["valid"], val_def)
        emitted_def = {t["address_hex"]: t for t in prov_def["emitted_tables"]}
        self.assertEqual(emitted_def["0x09000"]["name_source"], "raw_placeholder")
        self.assertEqual(emitted_def["0x09000"]["scaling"], "Raw_UWORD")
        self.assertTrue(emitted_def["0x09000"]["xml_name"].startswith("RAW_0x09000"))
        self.assertIn("[SHARED_AXIS]", emitted_def["0x09000"]["xml_name"])
        self.assertEqual(emitted_def["0x09600"]["xml_name"], "Target_Verified_Fuel [SHARED_AXIS]")
        self.assertEqual(emitted_def["0x09600"]["scaling"], "Fuel_Ms")
        reasons = [u["reason"] for u in unres_def["unresolved_items"]]
        self.assertEqual(sorted(reasons), ["excluded_invalid_span", "hold_for_conflict", "unresolved_base"])
        self.assertEqual(len(unres_def["unpromoted_scalar_candidates"]), 1)

        # Opt-in provisional donor names: uses [PROVISIONAL] label ONLY, STILL keeps Raw_UWORD!
        xml_opt, prov_opt, val_opt, _ = rxml.generate_romraider_preview(cat, res, allow_provisional_donor_names=True)
        self.assertTrue(val_opt["valid"])
        emitted_opt = {t["address_hex"]: t for t in prov_opt["emitted_tables"]}
        self.assertEqual(emitted_opt["0x09000"]["xml_name"], "Donor_Spark_Main [PROVISIONAL 0x09000] [SHARED_AXIS]")
        self.assertEqual(emitted_opt["0x09000"]["scaling"], "Raw_UWORD")
        self.assertEqual(emitted_opt["0x09000"]["name_source"], "provisional_donor_name_with_raw_scaling")

    def test_explicit_axis_vs_computed_implicit_grid_stub_export(self):
        rom = _synth_multi_helper_rom()
        helpers = discover_helpers(rom)
        calls = extract_calls(rom, helpers)
        scan_doc = build_scan_export("synth_m4.bin", rom, helpers, calls)
        cat = d2.to_per_address_catalogue(scan_doc)
        impl = {f"0x{k:05X}": v for k, v in d2.extract_implicit_grids(rom, helpers).items()}
        cat["implicit_grids"] = impl

        res = rxml.resolve_candidate_evidence(cat)
        xml_txt, prov, val, unres = rxml.generate_romraider_preview(
            cat, res, rom_bytes=rom, skip_trivial=True
        )
        self.assertTrue(val["valid"], val)
        # 0x09300 trivial payload moved to unresolved
        self.assertIn("skipped_trivial_constant_payload", [u["reason"] for u in unres["unresolved_items"]])

        root = ET.fromstring(xml_txt)
        tables = {t.attrib["storageaddress"]: t for t in root.findall("./rom/table")}
        self.assertIn("0x09000", tables)
        self.assertIn("0x09020", tables)
        self.assertIn("0x09200", tables)
        self.assertNotIn("0x09300", tables)

        # Explicit shared Y Axis
        y_ax = tables["0x09000"].find("./table")
        self.assertIsNotNone(y_ax)
        self.assertEqual(y_ax.attrib["type"], "Y Axis")
        self.assertEqual(y_ax.attrib["storageaddress"], "0x09100")

        # Computed implicit stub grid for 2D_IMPL @ 0x09200
        st_ax = tables["0x09200"].find("./table")
        self.assertIsNotNone(st_ax)
        self.assertEqual(st_ax.attrib["type"], "Static Y Axis")
        self.assertIn("unverified", st_ax.attrib["name"])
        pts = [int(d.text) for d in st_ax.findall("./data")]
        self.assertEqual(pts, [i * 16 for i in range(16)])

        # Provenance marks orientation_proven=False
        by_addr = {r["address_hex"]: r for r in res["resolved_candidates"]}
        self.assertFalse(by_addr["0x09200"]["axes"][0]["orientation_proven"])


class ValidatorSafetyAndCliTests(unittest.TestCase):
    def test_validator_errors_warnings_calibrations_guard_and_strict_preserve(self):
        bad_xml = """<?xml version="1.0"?>
        <roms><rom><romid><ecuid>1TEST</ecuid></romid>
          <scaling name="Raw_UWORD" storagetype="uint16" endian="big"/>
          <table name="Dup" type="2D" scaling="MissingScale" storageaddress="0x09000" storagetype="uint16" sizey="4"/>
          <table name="Dup" type="2D" scaling="Raw_UWORD" storageaddress="0x09004" storagetype="uint16" sizey="4"/>
          <table name="BadHex" type="2D" scaling="Raw_UWORD" storageaddress="NOTHEX" storagetype="uint16" sizey="2"/>
          <table name="OOB" type="2D" scaling="Raw_UWORD" storageaddress="0x23FFE" storagetype="uint16" sizey="4">
            <table name="Ax" type="Y Axis" scaling="BadAxisScale" sizey="4"/>
          </table>
        </rom></roms>"""
        val = rxml.validate_romraider_xml(bad_xml, rom_size=0x24000)
        self.assertFalse(val["valid"])
        err_codes = {e["code"] for e in val["errors"]}
        self.assertEqual(
            err_codes,
            {
                "missing_scaling_ref",
                "duplicate_table_name",
                "invalid_storageaddress",
                "out_of_rom_bounds",
                "missing_axis_scaling_ref",
            },
        )
        self.assertEqual([w["code"] for w in val["warnings"]], ["overlapping_table_extents"])

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # Guard rejects CALIBRATIONS/ output directories
            cal_dir = root / "CALIBRATIONS" / "nested"
            cat, xref = _synthetic_catalogue_and_xref()
            res = rxml.resolve_candidate_evidence(cat, xref)
            with self.assertRaises(ValueError):
                rxml.write_preview_bundle(cal_dir, "test", cat, res)

            # Strict pre-write validation prevents clobbering prior valid preview
            out_dir = root / "preview_out"
            out_dir.mkdir()
            prev_xml = out_dir / "keep.preview.xml"
            prev_xml.write_text("KEEP_PRIOR_VALID_XML", encoding="utf-8")
            bad_cat = json.loads(json.dumps(cat))
            bad_cat["candidates"][0]["base_hex"] = "BADADDR"  # invalid hex causes validate error
            bad_res = rxml.resolve_candidate_evidence(bad_cat)
            with self.assertRaises(ValueError):
                rxml.write_preview_bundle(out_dir, "keep", bad_cat, bad_res, strict=True)
            self.assertEqual(prev_xml.read_text(encoding="utf-8"), "KEEP_PRIOR_VALID_XML")

    def test_end_to_end_cli_bundle_with_ref_index(self):
        rom = _synth_multi_helper_rom()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rom_p = root / "target.bin"
            donor_p = root / "donor_twin.bin"
            # Identical code section twin, different cal byte at 0x0A000
            donor = bytearray(rom)
            donor[0x0A000] = 0x55
            rom_p.write_bytes(rom)
            donor_p.write_bytes(donor)

            x_p = root / "donor.xml"
            x_p.write_text(
                '<roms><rom><romid><ecuid>1SYNTHM4</ecuid></romid>'
                '<table name="Donor_Ign_Lead" type="2D" storageaddress="0x09000" storagetype="uint16" sizey="4"/>'
                '</rom></roms>',
                encoding="utf-8",
            )
            idx_p = root / "ref_index.json"
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc_idx = ridx.main(["build", "--out", str(idx_p), "--xml", str(x_p), "--rom", str(donor_p)])
            self.assertEqual(rc_idx, 0)

            out_dir = root / "out"
            with contextlib.redirect_stdout(buf):
                rc_exp = rxml.main([
                    "--rom", str(rom_p),
                    "--ref-index", str(idx_p),
                    "--out-dir", str(out_dir),
                    "--stem", "synth",
                    "--skip-trivial",
                ])
            self.assertEqual(rc_exp, 0)

            for suffix in (".preview.xml", ".provenance.json", ".validation.json", ".unresolved.json"):
                self.assertTrue((out_dir / f"synth{suffix}").exists(), suffix)

            val_doc = json.loads((out_dir / "synth.validation.json").read_text(encoding="utf-8"))
            prov_doc = json.loads((out_dir / "synth.provenance.json").read_text(encoding="utf-8"))
            unres_doc = json.loads((out_dir / "synth.unresolved.json").read_text(encoding="utf-8"))
            self.assertTrue(val_doc["valid"])
            self.assertEqual(val_doc["summary"]["table_count"], 3)
            self.assertEqual(len(prov_doc["code_twin_matches"]), 1)
            self.assertTrue(prov_doc["preview_only"])
            self.assertGreaterEqual(unres_doc["unresolved_count"], 1)
            # Confirm XML parses and keeps Tier D raw naming/scaling by default
            xml_root = ET.fromstring((out_dir / "synth.preview.xml").read_text(encoding="utf-8"))
            names = [t.attrib["name"] for t in xml_root.findall("./rom/table")]
            self.assertTrue(all(n.startswith("RAW_") for n in names))


if __name__ == "__main__":
    unittest.main()
