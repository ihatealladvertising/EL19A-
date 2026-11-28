#!/usr/bin/env python3
"""Synthetic tests for the pinned Stage-16 listing text extractor."""
from __future__ import annotations

import hashlib
import pathlib
import sys
import tempfile
import unittest
import zipfile

TOOLS_DIR = pathlib.Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from reader_trace_listing_source import (
    ListingSourceError,
    extract_verified_member,
    parse_listing_records,
    extract_helper_and_call_windows,
)


MEMBER = "synthetic_stage16.lst"


def make_listing():
    lines = []
    helpers = ("sub_22E10", "sub_22FAC", "sub_22B44", "sub_22DF8")
    for index, helper in enumerate(helpers):
        start = 0x22000 + (index * 0x100)
        lines.append(f"{helper}:")
        lines.append(f"{start:08X}  2F 26  CODE  mov.l @r2,r15 ; synthetic helper")
        lines.append(f"{start + 2:08X}  65 2F  CODE  mov.l @r2,r5 ; synthetic helper")
    call_pcs = (0x85B2E, 0x648D8, 0x5B3C0)
    for pc in call_pcs:
        lines.append("sub_90000:")
        lines.append(f"{pc - 2:08X}  60 53  CODE  mov r5,r0")
        lines.append(f"{pc:08X}  42 0B  CODE  jsr @r2")
        lines.append(f"{pc + 2:08X}  65 5C  CODE  extu.b r5,r5")
        lines.append(f"{pc + 4:08X}  00 09  CODE  nop")
    return ("\n".join(lines) + "\n").encode("utf-8")


class ListingSourceTests(unittest.TestCase):
    def make_archive(self, temp_dir, payload=None):
        data = payload if payload is not None else make_listing()
        path = pathlib.Path(temp_dir) / "source.zip"
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr(MEMBER, data)
        return path, data

    def test_extract_verifies_archive_and_member_hash(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path, data = self.make_archive(temp_dir)
            archive_bytes = path.read_bytes()
            member, metadata = extract_verified_member(
                path,
                member_name=MEMBER,
                expected_archive_sha256=hashlib.sha256(archive_bytes).hexdigest(),
                expected_member_sha256=hashlib.sha256(data).hexdigest(),
            )
            self.assertEqual(member, data)
            self.assertEqual(metadata["member_name"], MEMBER)
            self.assertEqual(metadata["member_sha256"], hashlib.sha256(data).hexdigest())

    def test_archive_hash_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path, data = self.make_archive(temp_dir)
            with self.assertRaises(ListingSourceError):
                extract_verified_member(
                    path, member_name=MEMBER,
                    expected_archive_sha256="0" * 64,
                    expected_member_sha256=hashlib.sha256(data).hexdigest(),
                )

    def test_member_hash_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path, data = self.make_archive(temp_dir)
            with self.assertRaises(ListingSourceError):
                extract_verified_member(
                    path, member_name=MEMBER,
                    expected_archive_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                    expected_member_sha256="0" * 64,
                )

    def test_missing_member_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path, data = self.make_archive(temp_dir)
            with self.assertRaises(ListingSourceError):
                extract_verified_member(
                    path, member_name="not_present.lst",
                    expected_archive_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                    expected_member_sha256=hashlib.sha256(data).hexdigest(),
                )

    def test_helper_functions_and_callsite_windows_are_selected(self):
        records = parse_listing_records(make_listing())
        windows = extract_helper_and_call_windows(records)
        self.assertEqual(set(windows["helper_functions"]), {
            "sub_22E10", "sub_22FAC", "sub_22B44", "sub_22DF8"
        })
        self.assertEqual(set(windows["call_sites"]), {"0x85B2E", "0x648D8", "0x5B3C0"})
        self.assertEqual(windows["helper_functions"]["sub_22B44"]["instruction_count"], 2)
        call = windows["call_sites"]["0x5B3C0"]
        self.assertEqual(call["call_instruction"]["assembly"], "jsr @r2")
        self.assertTrue(any(item["assembly"] == "extu.b r5,r5" for item in call["instructions"]))

    def test_missing_helper_function_is_rejected(self):
        lines = make_listing().decode("utf-8").replace("sub_22DF8:", "sub_missing:").encode("utf-8")
        records = parse_listing_records(lines)
        with self.assertRaises(ListingSourceError):
            extract_helper_and_call_windows(records)

    def test_missing_callsite_is_rejected(self):
        lines = make_listing().decode("utf-8").replace("0005B3C0  42 0B  CODE  jsr @r2\n", "").encode("utf-8")
        records = parse_listing_records(lines)
        with self.assertRaises(ListingSourceError):
            extract_helper_and_call_windows(records)

    def test_duplicate_code_pc_is_rejected(self):
        payload = make_listing() + b"00022E10  2F 26  CODE  mov.l @r2,r15\n"
        records = parse_listing_records(payload)
        with self.assertRaises(ListingSourceError):
            extract_helper_and_call_windows(records)


if __name__ == "__main__":
    unittest.main()
