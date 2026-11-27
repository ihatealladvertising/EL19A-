#!/usr/bin/env python3
"""Synthetic regression tests for tools/sh705x_discovery_v2.py (Milestone 2).

Covers all 10 WO70023 adversarial acceptance criteria, implicit fixed-grid
axis metadata, opt-in enhanced call extraction (preserving baseline extract_calls),
separate scalar calibration discovery, and atomic JSON output / run manifests.
Zero real ROM dependencies.
"""

import contextlib
import hashlib
import io
import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sh7058_cross_rom_scanner import (
    HelperSpec,
    build_scan_export,
    discover_helpers,
    extract_calls,
)
import sh705x_discovery_v2 as d2


def _make_raw_call(
    helper: int,
    pc: int,
    table,
    axis1,
    dim1: int,
    dim2: int,
    raw_r4,
    raw_r5,
    kind: str = "2D_AXIS",
    elem_type: str = "uint16",
    axis1_type: str = "uint8",
) -> dict:
    return {
        "call_pc": pc,
        "call_form": "indirect_jsr",
        "target_load_pc": pc - 8,
        "target_register": 3,
        "target_register_moves": [],
        "call_instruction": 0x430B,
        "delay_slot": 0x0009,
        "scan_start": 0x20000,
        "helper": helper,
        "kind": kind,
        "elem_type": elem_type,
        "dim1": dim1,
        "dim2": dim2,
        "axis1_type": axis1_type,
        "axis2_type": "",
        "table": table,
        "axis1": axis1,
        "axis2": None,
        "raw_r4": raw_r4,
        "raw_r5": raw_r5,
        "raw_r6": None,
    }


class Wo70023AdversarialCatalogueTests(unittest.TestCase):
    def test_accept_t1_to_t4_multi_call_shared_axis_conflict_and_overlap(self):
        rom = bytearray(0x28000)
        struct.pack_into(">H", rom, 0x20000, 0x4F22)
        struct.pack_into(">H", rom, 0x21000, 0x4F22)
        rom[0x09000:0x09010] = bytes(range(16))
        rom[0x09004:0x09014] = bytes(range(10, 26))
        rom[0x09500:0x09504] = bytes((1, 2, 3, 4))

        helpers = {
            0x20000: HelperSpec(0x20000, "2D_AXIS", "uint16", 4, 1, "uint8", "", 0, 0),
            0x20020: HelperSpec(0x20020, "2D_AXIS", "uint8", 8, 1, "uint8", "", 0, 0),
        }
        calls = [
            # accept.T1 + T3: two calls to 0x09000 with conflicting geometry
            _make_raw_call(0x20000, 0x22010, 0x09000, 0x09500, 4, 1, 0x09000, 0x09500, elem_type="uint16"),
            _make_raw_call(0x20020, 0x22040, 0x09000, 0x09500, 8, 1, 0x09000, 0x09500, elem_type="uint8"),
            # accept.T2 + T4: overlapping table at 0x09004 sharing axis 0x09500 (dim=4 uint8)
            _make_raw_call(0x20000, 0x22080, 0x09004, 0x09500, 4, 1, 0x09004, 0x09500, elem_type="uint16"),
        ]
        scan_doc = build_scan_export("synth.bin", bytes(rom), helpers, calls)
        cat = d2.to_per_address_catalogue(scan_doc)

        self.assertEqual(cat["schema"], d2.SCHEMA_CATALOGUE_V1)
        self.assertEqual(cat["output_schema_version"], d2.DATA_MODEL_VERSION)
        # Overlapping spans at 0x09000 and 0x09004 stay separate candidates
        cands = {c["base"]: c for c in cat["candidates"]}
        self.assertEqual(sorted(cands), [0x09000, 0x09004])
        # T1 & T3: both PCs & conflicting geometry variants preserved without choosing a winner
        c0 = cands[0x09000]
        self.assertEqual(c0["call_pcs"], [0x22010, 0x22040])
        self.assertTrue(c0["geometry_conflict"])
        self.assertEqual(len(c0["geometry_variants"]), 2)
        self.assertEqual(len(c0["spans"]), 2)
        # T2: shared axis lifted as first-class object linked to both consumers
        shared_axes = [ax for ax in cat["axes"] if ax["address"] == 0x09500 and ax["count"] == 4]
        self.assertEqual(len(shared_axes), 1)
        self.assertEqual(shared_axes[0]["consumer_tables"], [0x09000, 0x09004])
        self.assertEqual(shared_axes[0]["shared_count"], 2)

    def test_accept_t5_to_t10_unresolved_oob_determinism_donor_addrspace_and_indices(self):
        rom = bytearray(0x24000)
        # truncated table base near end of ROM inside helper band? place helper pre-cal so cal_hi includes near end
        helpers = {0x05000: HelperSpec(0x05000, "2D_IMPL", "uint16", 8, 1, "implicit_u8", "", 0, 0)}
        calls = [
            _make_raw_call(0x05000, 0x22020, None, None, 8, 1, None, None, kind="2D_IMPL", axis1_type="implicit_u8"),
            _make_raw_call(0x05000, 0x22050, 0x23FFC, None, 8, 1, 0x23FFC, None, kind="2D_IMPL", axis1_type="implicit_u8"),
        ]
        # Force table row with out-of-bounds span (0x23FFC + 16 > 0x24000)
        scan_doc = build_scan_export("synth_oob.bin", bytes(rom), helpers, calls)
        cat_a = d2.to_per_address_catalogue(
            scan_doc,
            address_space="file_offset",
            donor_leads=[{
                "target_base": 0x23FFC,
                "source_path": "donor.a2l",
                "source_sha256": "d" * 64,
                "symbol_kind": "CHARACTERISTIC",
                "symbol_name": "DonorOnlyGuess",
                "match_basis": "symbol_only",
            }],
            optional_indices={"static_rosetta": None, "el_access_index": {"status": "stale", "reason": "hash_mismatch"}},
        )
        cat_b = d2.to_per_address_catalogue(
            scan_doc,
            address_space="file_offset",
            donor_leads=[{
                "target_base": 0x23FFC,
                "source_path": "donor.a2l",
                "source_sha256": "d" * 64,
                "symbol_kind": "CHARACTERISTIC",
                "symbol_name": "DonorOnlyGuess",
                "match_basis": "symbol_only",
            }],
            optional_indices={"static_rosetta": None, "el_access_index": {"status": "stale", "reason": "hash_mismatch"}},
        )
        # accept.T7 determinism
        self.assertEqual(json.dumps(cat_a, sort_keys=True), json.dumps(cat_b, sort_keys=True))
        self.assertEqual(cat_a["deterministic_id"], cat_b["deterministic_id"])
        # accept.T5 unresolved call retained in observations[] with base=None
        self.assertEqual(len(cat_a["observations"]), 2)
        self.assertIsNone(cat_a["observations"][0]["base"])
        # accept.T6 OOB candidate retained with null payload sha256
        oob_cand = cat_a["candidates"][0]
        self.assertFalse(oob_cand["geometry_variants"][0]["in_bounds"])
        self.assertIsNone(oob_cand["geometry_variants"][0]["payload_sha256"])
        # accept.T8 donor lead never promoted to target proof
        self.assertEqual(cat_a["leads"][0]["evidence_class"], "donor")
        self.assertFalse(cat_a["leads"][0]["is_target_proof"])
        # accept.T9 address_space kept explicit
        self.assertEqual(oob_cand["address_space"], "file_offset")
        self.assertEqual(oob_cand["file_offset"], 0x23FFC)
        self.assertIsNone(oob_cand["ea"])
        # accept.T10 unavailable optional indices reported explicitly
        self.assertEqual(cat_a["manifest"]["optional_indices"]["static_rosetta"]["status"], "unavailable")
        self.assertEqual(cat_a["manifest"]["optional_indices"]["el_access_index"]["status"], "unavailable")


class ImplicitGridAndEnhancedDiscoveryTests(unittest.TestCase):
    def test_extract_implicit_grids_2d_and_3d(self):
        rom = bytearray(0x28000)
        # Pattern A 2D_IMPL u8 @ 0x20000:
        # 9006 (mov.w @(6*2, PC), r0 -> 0x20010); 655C (extu.b r5, r5); 3502; 8902; D603; 462B
        # 741E (+30 -> 16 pts of u16); 000B; 6041
        stub_2d = [0x9006, 0x655C, 0x3502, 0x8902, 0xD603, 0x462B, 0x0009, 0x741E, 0x000B, 0x6041]
        for i, w in enumerate(stub_2d):
            struct.pack_into(">H", rom, 0x20000 + i * 2, w)
        # Pool for 9006 at pc=0x20000 -> 0x20004 + 12 = 0x20010: max_val = 240 -> step = 16, pts = 16
        struct.pack_into(">H", rom, 0x20010, 240)
        # Pool for D603 at pc=0x20008 -> 0x2000C + 12 = 0x20018: tail @ 0x20800
        struct.pack_into(">I", rom, 0x20018, 0x00020800)

        # Pattern D 3D_IMPL u16 @ 0x20100: 4F22; 2F86; 2F46; 636D; D704; 645D; 470B; E500; ... 472B; E510
        stub_3d = [0x4F22, 0x2F86, 0x2F46, 0x636D, 0xD704, 0x645D, 0x470B, 0xE500, 0x0009, 0x472B, 0xE510, 0x000B]
        for i, w in enumerate(stub_3d):
            struct.pack_into(">H", rom, 0x20100 + i * 2, w)

        helpers = discover_helpers(bytes(rom))
        self.assertIn(0x20000, helpers)
        self.assertIn(0x20100, helpers)
        grids = d2.extract_implicit_grids(bytes(rom), helpers)

        g2 = grids[0x20000]
        self.assertEqual(g2["axis1_grid"]["query_domain"], "uint8")
        self.assertEqual(g2["axis1_grid"]["axis_start"], 0)
        self.assertEqual(g2["axis1_grid"]["axis_step"], 16)
        self.assertEqual(g2["axis1_grid"]["axis_count"], 16)
        self.assertEqual(g2["axis1_grid"]["grid_max_raw"], 240)
        self.assertTrue(g2["axis1_grid"]["step_verified_from_clamp"])
        self.assertFalse(g2["axis1_grid"]["orientation_proven"])

        g3 = grids[0x20100]
        self.assertEqual(g3["axis1_grid"]["query_domain"], "uint16")
        self.assertEqual(g3["axis1_grid"]["axis_count"], 16)
        self.assertEqual(g3["axis1_grid"]["axis_step"], 4096)
        self.assertFalse(g3["axis1_grid"]["orientation_proven"])

    def test_opt_in_enhanced_call_window_vs_untouched_baseline(self):
        rom = bytearray(0x28000)
        # Pattern B helper @ 0x20000
        for i, w in enumerate([0x4F22, 0x2F46, 0x6053, 0x656C, 0xD702, 0x470B, 0xE403, 0x8560, 0x000B, 0x0009]):
            struct.pack_into(">H", rom, 0x20000 + i * 2, w)
        struct.pack_into(">I", rom, 0x20014, 0x00020800)
        struct.pack_into(">2H", rom, 0x20800, 0x000C, 0x000B)

        # Function @ 0x21000 loads r4/r5 at 0x21004/0x21006, 84 bytes before call @ 0x21058!
        struct.pack_into(">H", rom, 0x21000, 0x4F22)
        struct.pack_into(">H", rom, 0x21004, 0xD41A)  # @ 0x21070 = 0x09000
        struct.pack_into(">H", rom, 0x21006, 0xD51B)  # @ 0x21074 = 0x09100
        struct.pack_into(">H", rom, 0x21052, 0xD709)  # @ 0x21078 = 0x20000
        struct.pack_into(">H", rom, 0x21058, 0x470B)  # jsr @r7 (delay @ 0x2105A)
        struct.pack_into(">H", rom, 0x2105A, 0x0009)
        struct.pack_into(">H", rom, 0x2105C, 0x000B)
        struct.pack_into(">3I", rom, 0x21070, 0x00009000, 0x00009100, 0x00020000)

        helpers = discover_helpers(bytes(rom))
        base_calls = extract_calls(bytes(rom), helpers)
        enh_calls = d2.extract_calls_enhanced(bytes(rom), helpers, window_bytes=128)
        cmp_rep = d2.compare_call_extractions(base_calls, enh_calls)

        # Baseline MUST remain unresolved (>56B window) while opt-in enhanced resolves it
        self.assertEqual(len(base_calls), 1)
        self.assertIsNone(base_calls[0]["table"])
        self.assertEqual(enh_calls[0]["table"], 0x09000)
        self.assertEqual(enh_calls[0]["axis1"], 0x09100)
        self.assertEqual(len(cmp_rep["newly_resolved"]), 1)
        self.assertEqual(cmp_rep["newly_resolved"][0]["table"], 0x09000)

    def test_discover_cal_scalars_excludes_tables_and_tracks_derefs(self):
        rom = bytearray(0x28000)
        for i, w in enumerate([0x4F22, 0x2F46, 0x6053, 0x656C, 0xD702, 0x470B, 0xE403, 0x8560, 0x000B, 0x0009]):
            struct.pack_into(">H", rom, 0x20000 + i * 2, w)
        struct.pack_into(">I", rom, 0x20014, 0x00020800)

        # Table @ 0x09000 (8B), Axis @ 0x09100 (4B), standalone uint16 scalar @ 0x05200 (= 0x1A2B)
        struct.pack_into(">H", rom, 0x05200, 0x1A2B)
        struct.pack_into(">H", rom, 0x21000, 0x4F22)
        struct.pack_into(">H", rom, 0x21004, 0xD406)  # -> 0x09000
        struct.pack_into(">H", rom, 0x21006, 0xD507)  # -> 0x09100
        struct.pack_into(">H", rom, 0x21008, 0xD707)  # -> 0x20000
        struct.pack_into(">H", rom, 0x2100A, 0x470B)  # call helper
        struct.pack_into(">H", rom, 0x2100C, 0x0009)
        struct.pack_into(">H", rom, 0x21010, 0xD106)  # r1 = @0x2102C = 0x05200
        struct.pack_into(">H", rom, 0x21012, 0x6211)  # mov.w @r1, r2 -> hints uint16
        struct.pack_into(">H", rom, 0x21014, 0x000B)
        struct.pack_into(">4I", rom, 0x21020, 0x00009000, 0x00009100, 0x00020000, 0x00005200)

        helpers = discover_helpers(bytes(rom))
        calls = extract_calls(bytes(rom), helpers)
        scalars = d2.discover_cal_scalars(bytes(rom), helpers, calls=calls)
        addrs = {s["address"]: s for s in scalars}
        self.assertNotIn(0x09000, addrs)
        self.assertNotIn(0x09100, addrs)
        self.assertIn(0x05200, addrs)
        self.assertEqual(addrs[0x05200]["deref_hints"], ["uint16"])
        self.assertEqual(addrs[0x05200]["u16_preview"], 0x1A2B)
        self.assertEqual(addrs[0x05200]["span"]["byte_length"], 2)


class AtomicOutputAndManifestCliTests(unittest.TestCase):
    def test_atomic_write_and_cli_catalogue_manifest_generation(self):
        rom = bytearray(0x24000)
        for i, w in enumerate([0x4F22, 0x2F46, 0x6053, 0x656C, 0xD702, 0x470B, 0xE403, 0x8560, 0x000B, 0x0009]):
            struct.pack_into(">H", rom, 0x20000 + i * 2, w)
        struct.pack_into(">I", rom, 0x20014, 0x00020800)
        struct.pack_into(">H", rom, 0x05200, 0x0042)
        struct.pack_into(">H", rom, 0x21000, 0x4F22)
        struct.pack_into(">H", rom, 0x21004, 0xD406)
        struct.pack_into(">H", rom, 0x21006, 0xD507)
        struct.pack_into(">H", rom, 0x21008, 0xD707)
        struct.pack_into(">H", rom, 0x2100A, 0x470B)
        struct.pack_into(">H", rom, 0x2100C, 0x0009)
        struct.pack_into(">H", rom, 0x21010, 0xD106)
        struct.pack_into(">H", rom, 0x21012, 0x6211)
        struct.pack_into(">4I", rom, 0x21020, 0x00009000, 0x00009100, 0x00020000, 0x00005200)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rom_p = root / "synth.bin"
            out_p = root / "cat.json"
            man_p = root / "manifest.json"
            rom_p.write_bytes(rom)

            # Seed existing output and check failed write does not clobber valid artifact
            d2.atomic_write_text(out_p, "VALID_PREVIOUS")
            orig_replace = d2.os.replace
            try:
                def _boom(_s, _d):
                    raise OSError("simulated interruption")
                d2.os.replace = _boom
                with self.assertRaises(OSError):
                    d2.atomic_write_text(out_p, "CORRUPT_PARTIAL")
            finally:
                d2.os.replace = orig_replace
            self.assertEqual(out_p.read_text(encoding="utf-8"), "VALID_PREVIOUS")

            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = d2.main([
                    str(rom_p),
                    "--out", str(out_p),
                    "--manifest", str(man_p),
                    "--enhanced-window", "128",
                    "--include-scalars",
                ])
            self.assertEqual(rc, 0)
            cat = json.loads(out_p.read_text(encoding="utf-8"))
            man = json.loads(man_p.read_text(encoding="utf-8"))
            self.assertEqual(cat["schema"], d2.SCHEMA_CATALOGUE_V1)
            self.assertEqual(len(cat["candidates"]), 1)
            self.assertIn("scalar_candidates", cat)
            self.assertIn("enhanced_call_comparison", cat)
            self.assertEqual(man["outputs"][0]["sha256"], hashlib.sha256(out_p.read_bytes()).hexdigest())
            self.assertEqual(man["input"]["decoded_rom_sha256"], hashlib.sha256(rom).hexdigest())


if __name__ == "__main__":
    unittest.main()
