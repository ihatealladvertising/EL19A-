#!/usr/bin/env python3
"""Unit and integration tests for tools/wo_registry.py."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import pathlib
import sys
import tempfile
import unittest

TOOLS_DIR = pathlib.Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import wo_registry as wr


def write_sample_pins(control_dir: pathlib.Path) -> pathlib.Path:
    pins = {
        "schema_version": 4,
        "repository": "ihatealladvertising/EL19A-",
        "authority_branch": "main",
        "current_workbook": "WORKBOOK/V58.xlsx",
        "current_workbook_sheets": 149,
        "current_xml_baseline": "XML_v3.xml",
        "current_xml_fragment": "IGN_frag.xml",
        "discovery_staging": "CALIBRATIONS/discovered_tables_catalog.csv",
        "legacy_cutoff_id": 65163,
        "default_lease_hours": 24,
        "protected_generated_files": [
            "CONTROL/active_work_orders.md",
            "CONTROL/WO_LIVE_INDEX.md",
        ],
        "lanes": {
            "git-1": {"min_id": 65200, "max_id": 69999, "description": "Git 1"},
            "aistudio": {"min_id": 70000, "max_id": 79999, "description": "AI Studio"},
            "git-2": {"min_id": 80000, "max_id": 89999, "description": "Git 2"},
        },
        "banned_owner_tokens": ["current session", "this session", "tbd", "unknown"],
    }
    p = control_dir / "registry_pins.json"
    p.write_text(json.dumps(pins, indent=2), encoding="utf-8")
    return p


class TestWoRegistry(unittest.TestCase):
    def test_scope_normalization_and_overlap(self) -> None:
        a = wr.normalize_scope_token("0xE904")
        b = wr.normalize_scope_token("0x0000e904")
        c = wr.normalize_scope_token("0x0E900-0x0E910")
        d = wr.normalize_scope_token("0x0E920-0x0E930")
        self.assertEqual(a.canonical, "0x0000E904")
        self.assertEqual(b.canonical, "0x0000E904")
        self.assertTrue(wr.scopes_overlap(a, b))
        self.assertTrue(wr.scopes_overlap(a, c))
        self.assertFalse(wr.scopes_overlap(a, d))
        self.assertFalse(
            wr.scopes_overlap(wr.normalize_scope_token("docs-only"), wr.normalize_scope_token("docs-only"))
        )

    def test_rejects_ambiguous_owner_and_wrong_lane(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cdir = pathlib.Path(tmp) / "CONTROL"
            cdir.mkdir()
            pins = wr.load_pins(write_sample_pins(cdir))

            (cdir / "WO70001.md").write_text(
                wr.render_init_wo(
                    wo_id="WO70001",
                    title="Bad owner and lane",
                    lane="git-1",
                    owner="current session",
                    priority="P1",
                    scope=["0x0E904"],
                    depends_on=[],
                    branch="b1",
                    claimed_at="2026-11-21T19:00:00Z",
                ),
                encoding="utf-8",
            )
            errs = wr.validate_repo(cdir, pins)
            joined = "\n".join(errs)
            self.assertIn("outside lane `git-1`", joined)
            self.assertIn("ambiguous or missing `owner`", joined)

    def test_detects_target_scope_collision_and_allows_depends_on(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cdir = pathlib.Path(tmp) / "CONTROL"
            cdir.mkdir()
            pins = wr.load_pins(write_sample_pins(cdir))

            (cdir / "WO70001.md").write_text(
                wr.render_init_wo(
                    wo_id="WO70001",
                    title="Trace E904",
                    lane="aistudio",
                    owner="aistudio-s1",
                    priority="P1",
                    scope=["0xE904", "FFFF84FE"],
                    depends_on=[],
                    branch="b1",
                    claimed_at="2026-11-21T19:00:00Z",
                ),
                encoding="utf-8",
            )
            (cdir / "WO80001.md").write_text(
                wr.render_init_wo(
                    wo_id="WO80001",
                    title="Overlap E904",
                    lane="git-2",
                    owner="git-kilo-2",
                    priority="P1",
                    scope=["0x0000E904"],
                    depends_on=[],
                    branch="b2",
                    claimed_at="2026-11-21T19:10:00Z",
                ),
                encoding="utf-8",
            )
            errs = wr.validate_repo(cdir, pins)
            self.assertTrue(any("Target-scope lock collision" in e for e in errs))

            # Linking via depends_on resolves the collision cleanly
            (cdir / "WO80001.md").write_text(
                wr.render_init_wo(
                    wo_id="WO80001",
                    title="Follow-on E904",
                    lane="git-2",
                    owner="git-kilo-2",
                    priority="P1",
                    scope=["0x0000E904"],
                    depends_on=["WO70001"],
                    branch="b2",
                    claimed_at="2026-11-21T19:10:00Z",
                ),
                encoding="utf-8",
            )
            self.assertEqual(wr.validate_repo(cdir, pins), [])

    def test_forbids_worker_register_edit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cdir = pathlib.Path(tmp) / "CONTROL"
            cdir.mkdir()
            pins = wr.load_pins(write_sample_pins(cdir))
            errs = wr.validate_repo(
                cdir,
                pins,
                changed_files=["CONTROL/active_work_orders.md"],
                forbid_register_edit=True,
            )
            self.assertEqual(len(errs), 1)
            self.assertIn("protected auto-generated file", errs[0])

    def test_rebuild_stale_lease_unblocking_and_injection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cdir = pathlib.Path(tmp) / "CONTROL"
            cdir.mkdir()
            pins = wr.load_pins(write_sample_pins(cdir))

            # Closed prerequisite
            (cdir / "WO65200.md").write_text(
                wr.render_init_wo(
                    wo_id="WO65200",
                    title="Prerequisite trace",
                    lane="git-1",
                    owner="git-worker-1",
                    priority="P1",
                    scope=["0x9000"],
                    depends_on=[],
                    branch="b0",
                    claimed_at="2026-11-20T00:00:00Z",
                    status="CLOSED",
                ),
                encoding="utf-8",
            )
            # Stale claimed (>24h)
            (cdir / "WO70001.md").write_text(
                wr.render_init_wo(
                    wo_id="WO70001",
                    title="Stale task",
                    lane="aistudio",
                    owner="aistudio-s1",
                    priority="P1",
                    scope=["FFFF1234"],
                    depends_on=[],
                    branch="b1",
                    claimed_at="2026-11-20T00:00:00Z",
                    status="CLAIMED",
                ),
                encoding="utf-8",
            )
            # Blocked task whose prereq is CLOSED -> should surface READY
            (cdir / "WO80001.md").write_text(
                wr.render_init_wo(
                    wo_id="WO80001",
                    title="Downstream synthesis",
                    lane="git-2",
                    owner="unclaimed",
                    priority="P2",
                    scope=["0x9000"],
                    depends_on=["WO65200"],
                    branch="b2",
                    claimed_at="",
                    status="BLOCKED",
                ),
                encoding="utf-8",
            )
            now = datetime(2026, 11, 21, 12, 0, tzinfo=timezone.utc)
            dash = wr.build_dashboard_markdown(cdir, pins, now_dt=now)
            self.assertIn("STALE (36.0h > 24h)", dash)
            self.assertIn("**READY (deps CLOSED)**", dash)
            self.assertIn("`0xFFFF1234`", dash)
            self.assertIn("`WO70002`", dash)

            # Injection preserves surrounding coordinator text and is idempotent
            reg = cdir / "active_work_orders.md"
            reg.write_text("# Header\n\nIntro\n\n## Legacy Section\nKeep me.\n", encoding="utf-8")
            once = wr.inject_dashboard_into_register(reg, dash)
            reg.write_text(once, encoding="utf-8")
            twice = wr.inject_dashboard_into_register(reg, dash)
            self.assertEqual(once, twice)
            self.assertIn("## Legacy Section\nKeep me.", twice)

    def test_migration_cutoff_grandfathers_only_existing_unstructured_work_orders(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cdir = pathlib.Path(tmp) / "CONTROL"
            cdir.mkdir()
            pins = wr.load_pins(write_sample_pins(cdir))
            pins["legacy_cutoff_id"] = 70038

            historical = cdir / "WO70038.md"
            historical.write_text(
                "# WO70038 — Historical report\\n\\n"
                "**Status:** CLOSED\\n**Priority:** P1\\n**Owner:** legacy-owner\\n",
                encoding="utf-8",
            )
            new_unstructured = cdir / "WO70039.md"
            new_unstructured.write_text(
                "# WO70039 — New report missing metadata\\n\\n"
                "**Status:** CLOSED\\n**Priority:** P1\\n**Owner:** new-owner\\n",
                encoding="utf-8",
            )

            errs = wr.validate_repo(cdir, pins)
            self.assertFalse(any("WO70038.md" in e for e in errs), msg="Existing baseline WO should remain legacy")
            self.assertTrue(
                any("WO70039.md: missing required" in e for e in errs),
                msg=f"New unstructured WO must fail strict validation: {errs}",
            )

            forced = wr.validate_repo(cdir, pins, changed_files=["WO70038.md"])
            self.assertTrue(
                any("WO70038.md: missing required" in e for e in forced),
                msg="Editing a grandfathered legacy WO must force v4 metadata validation",
            )

    def test_real_repository_wos_parse_and_validate_cleanly(self) -> None:
        real_control = wr.DEFAULT_CONTROL_DIR
        real_pins = wr.load_pins(wr.DEFAULT_PINS_PATH)
        errs = wr.validate_repo(real_control, real_pins)
        self.assertEqual(errs, [], msg=f"Unexpected validation errors: {errs}")
        d1 = wr.build_dashboard_markdown(real_control, real_pins)
        d2 = wr.build_dashboard_markdown(real_control, real_pins)
        self.assertEqual(d1, d2)


if __name__ == "__main__":
    unittest.main()
