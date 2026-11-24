#!/usr/bin/env python3
"""
analyze_el19a_el13a_diff.py
Complete deterministic calibration diff & cross-reference analyzer comparing:
  - EL19A: EVIDENCE/VERSA f501.bin
  - EL13A: EVIDENCE/23710-EL13A-08-C11-MR18DE-CVT.bin

Both ROMs share identical FID 8CMCKRN5 and 100% byte-identical machine code
outside 0x08200..0x12E37. This script partitions all 3,708 differing bytes
against XML definitions, the 179-table catalog, explicit axes, newly resolved
uncatalogued tables/structs from the disassembly listing, option byte 0x08CD3,
CALID strings, and verified sub_BE352 ROM checksums.

Pure Python 3 standard library only.
Outputs:
  - INDEX/el19a_vs_el13a_diff_blocks.tsv
  - INDEX/el19a_vs_el13a_unmapped_targets.tsv
"""

import argparse
import csv
import hashlib
import re
import struct
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

EXPECTED_EL19A_MD5 = "46991697c502052752a2cabcb84c9e27"
EXPECTED_EL19A_SHA256 = "bfe037e8e6c389e2a90214047058eb6dc3bcaaaac5b5931bf98a3f5d9f64fd6a"
EXPECTED_EL13A_MD5 = "9839331b4e47fcbcee28b28bca47d80b"
EXPECTED_EL13A_SHA256 = "50acb08f0e913a048d96846b0a87da633e787627b33dfea29110bd8b5d1af54a"
EXPECTED_LST_MEMBER = "EL19A_Complete_Disassembly_ANNOTATED_V3_NEXT6_16_ALL_PENDING_ANNOTATIONS(1).lst"
EXPECTED_LST_SHA256 = "148385bbec91f6a491dcaa403962836f709c2f273df9a17ec51f1dea5f7f4549"

STOR_BYTES = {
    "uint8": 1,
    "int8": 1,
    "uint16": 2,
    "int16": 2,
    "uint32": 4,
    "int32": 4,
    "float": 4,
}

RE_LST_LINE = re.compile(r"^([0-9A-Fa-f]{8})\s+([0-9A-Fa-f\s]+?)\s+(CODE|DATA)\s+(.+)$")
RE_LABEL = re.compile(r"^([a-zA-Z_][a-zA-Z0-9_]*):")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def md5_bytes(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


def verify_nissan_checksums(rom: bytes, label: str) -> tuple[int, int]:
    """Verify sub_BE352 32-bit XOR (0x099DC) and ADD (0x099E4) checksums over 0x08200..0xFFFFF."""
    stored_xor = struct.unpack(">I", rom[0x099DC:0x099E0])[0]
    stored_sum = struct.unpack(">I", rom[0x099E4:0x099E8])[0]
    calc_xor = 0
    calc_sum = 0
    for off in range(0x08200, len(rom), 4):
        if off in (0x08200, 0x099DC, 0x099E4, 0x20000):
            continue
        w = struct.unpack(">I", rom[off:off + 4])[0]
        calc_xor ^= w
        calc_sum = (calc_sum + w) & 0xFFFFFFFF
    if calc_xor != stored_xor or calc_sum != stored_sum:
        raise ValueError(
            f"{label} checksum mismatch: xor 0x{calc_xor:08X}!=0x{stored_xor:08X} "
            f"sum 0x{calc_sum:08X}!=0x{stored_sum:08X}"
        )
    return stored_xor, stored_sum


def load_listing_lines(lst_path: Path, zip_path: Path) -> list[str]:
    if lst_path.exists():
        raw = lst_path.read_bytes()
        if sha256_bytes(raw) != EXPECTED_LST_SHA256:
            raise ValueError(f"Listing SHA-256 mismatch at {lst_path}")
        return raw.decode("utf-8", errors="replace").splitlines()
    if not zip_path.exists():
        raise FileNotFoundError(f"Neither {lst_path} nor {zip_path} exists")
    with zipfile.ZipFile(zip_path, "r") as zf:
        raw = zf.read(EXPECTED_LST_MEMBER)
    if sha256_bytes(raw) != EXPECTED_LST_SHA256:
        raise ValueError(f"Listing SHA-256 mismatch inside {zip_path}")
    return raw.decode("utf-8", errors="replace").splitlines()


def scan_listing_references(lst_lines: list[str]):
    """
    Scan disassembly listing for:
      - CODE mov.l @(disp, PC), Rn -> pool DATA word pointing into 0x08200..0x12E37
      - Fallback literal DATA words in >=0x12E38 pointing into 0x08200..0x12E37
    Returns:
      pool_loads: target_addr -> list of (code_pc, func, rn, ctx_summary)
      literal_refs: target_addr -> list of (pool_pc, func, asm_body)
    """
    by_pc = {}
    order = []
    cur_func = "unknown"
    for ln in lst_lines:
        ml = RE_LABEL.match(ln)
        if ml:
            lbl = ml.group(1)
            if lbl.startswith("sub_"):
                cur_func = lbl
            continue
        m = RE_LST_LINE.match(ln)
        if not m:
            continue
        pc = int(m.group(1), 16)
        hx = m.group(2).replace(" ", "")
        by_pc[pc] = (hx, m.group(3), m.group(4).strip(), cur_func)
        order.append(pc)

    literal_refs = {}
    for pc in order:
        if 0x08200 <= pc <= 0x12E37:
            continue
        hx, kind, body, fn = by_pc[pc]
        if kind == "DATA" and len(hx) == 8:
            val = int(hx, 16)
            if 0x08200 <= val <= 0x12E37:
                literal_refs.setdefault(val, []).append((pc, fn, body))

    pool_loads = {}
    for idx, pc in enumerate(order):
        hx, kind, body, fn = by_pc[pc]
        if kind != "CODE" or len(hx) != 4:
            continue
        op = int(hx, 16)
        if (op & 0xF000) == 0xD000:
            rn = (op >> 8) & 0x0F
            disp = op & 0xFF
            pool_ea = (pc & ~3) + 4 + disp * 4
            if pool_ea in by_pc and by_pc[pool_ea][1] == "DATA" and len(by_pc[pool_ea][0]) == 8:
                val = int(by_pc[pool_ea][0], 16)
                if 0x08200 <= val <= 0x12E37:
                    ctx = []
                    for k in range(1, 9):
                        if idx + k < len(order):
                            npc = order[idx + k]
                            if by_pc[npc][1] == "CODE":
                                ctx.append(by_pc[npc][2].split(";")[0].strip())
                                if len(ctx) >= 4:
                                    break
                    pool_loads.setdefault(val, []).append((pc, fn, rn, " | ".join(ctx)))

    return pool_loads, literal_refs


def load_wo65117_ea_dict(ea_path: Path):
    ea_map = {}
    if not ea_path.exists():
        return ea_map
    with ea_path.open(encoding="utf-8") as f:
        for line in f:
            if line.startswith("#") or line.startswith("base_value"):
                continue
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 9:
                continue
            ea = int(parts[2], 16)
            if 0x08200 <= ea <= 0x12E37:
                ea_map.setdefault(ea, []).append((parts[6], parts[7], parts[5], parts[8]))
    return ea_map


def classify_variant_pattern(b19: bytes, b13: bytes, category: str) -> str:
    if category == "checksum_32bit":
        return "checksum"
    if category == "calid_header":
        return "calid_string"
    if category == "option_byte":
        return "bitflag_flip"
    all_19_zero = all(x == 0x00 for x in b19)
    all_13_zero = all(x == 0x00 for x in b13)
    all_19_ff = all(x == 0xFF for x in b19)
    all_13_ff = all(x == 0xFF for x in b13)
    if all_19_zero and not all_13_zero:
        return "el19a_zeroed"
    if all_13_zero and not all_19_zero:
        return "el13a_zeroed"
    if all_19_ff and not all_13_ff:
        return "el19a_ff_disabled"
    if all_13_ff and not all_19_ff:
        return "el13a_ff_disabled"
    # Check partial-run zeroing (e.g. 0x10286 has prefix shared, tail zeroed in 13A)
    diff_19 = [b19[i] for i in range(len(b19)) if b19[i] != b13[i]]
    diff_13 = [b13[i] for i in range(len(b13)) if b19[i] != b13[i]]
    if diff_19 and all(x == 0x00 for x in diff_19):
        return "el19a_diff_bytes_zeroed"
    if diff_13 and all(x == 0x00 for x in diff_13):
        return "el13a_diff_bytes_zeroed"
    return "calibrated_diff"


def format_hex_sample(data: bytes, max_bytes: int = 16) -> str:
    if len(data) <= max_bytes:
        return data.hex(" ")
    return f"{data[:8].hex(' ')} .. {data[-4:].hex(' ')}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze EL19A vs EL13A calibration diffs")
    parser.add_argument("--el19a", type=Path, default=Path("EVIDENCE/VERSA f501.bin"))
    parser.add_argument("--el13a", type=Path, default=Path("EVIDENCE/23710-EL13A-08-C11-MR18DE-CVT.bin"))
    parser.add_argument("--lst", type=Path, default=Path("/tmp/EL19A_NEXT6_16.lst"))
    parser.add_argument(
        "--lst-zip",
        type=Path,
        default=Path("EVIDENCE/EL19A_Complete_Disassembly_ANNOTATED_V3_NEXT6_14_GBR_BASE_RESOLVED.zip"),
    )
    parser.add_argument("--out-blocks", type=Path, default=Path("INDEX/el19a_vs_el13a_diff_blocks.tsv"))
    parser.add_argument("--out-unmapped", type=Path, default=Path("INDEX/el19a_vs_el13a_unmapped_targets.tsv"))
    args = parser.parse_args()

    r19 = args.el19a.read_bytes()
    r13 = args.el13a.read_bytes()

    if md5_bytes(r19) != EXPECTED_EL19A_MD5 or sha256_bytes(r19) != EXPECTED_EL19A_SHA256:
        raise ValueError(f"EL19A ROM integrity check failed: {args.el19a}")
    if md5_bytes(r13) != EXPECTED_EL13A_MD5 or sha256_bytes(r13) != EXPECTED_EL13A_SHA256:
        raise ValueError(f"EL13A ROM integrity check failed: {args.el13a}")
    if len(r19) != len(r13) or len(r19) != 0x100000:
        raise ValueError("ROM size mismatch")

    if r19[:0x08200] != r13[:0x08200] or r19[0x12E38:] != r13[0x12E38:]:
        raise ValueError("Unexpected diff outside 0x08200..0x12E37")

    verify_nissan_checksums(r19, "EL19A")
    verify_nissan_checksums(r13, "EL13A")

    diff_set = {i for i in range(len(r19)) if r19[i] != r13[i]}
    if len(diff_set) != 3708:
        raise ValueError(f"Expected 3708 diff bytes, got {len(diff_set)}")

    lst_lines = load_listing_lines(args.lst, args.lst_zip)
    pool_loads, literal_refs = scan_listing_references(lst_lines)
    ea_map = load_wo65117_ea_dict(Path("EVIDENCE/WO65117_effective_address_dictionary.tsv"))

    # Load Catalog 179 consumer summary
    cat_summary = {}
    sum_path = Path("INDEX/catalog_179_consumer_summary.tsv")
    if sum_path.exists():
        with sum_path.open(encoding="utf-8") as f:
            for row in csv.DictReader(f, delimiter="\t"):
                cat_summary[int(row["address"], 16)] = row

    # Registry of structured objects (highest-authority source first; non-overlapping primary byte ownership)
    claimed_bytes = set()
    blocks = []

    def add_block(
        start: int,
        end: int,
        category: str,
        storage: str,
        dimensions: str,
        name: str,
        consumers: str,
        twin_notes: str,
        helper: str = "-",
    ) -> int:
        span_set = set(range(start, end + 1))
        overlap = span_set & claimed_bytes
        if overlap:
            raise ValueError(
                f"Overlapping partition at 0x{start:05X}..0x{end:05X} ({name}): "
                f"{len(overlap)} bytes already claimed (e.g. 0x{min(overlap):05X})"
            )
        diffs = sum(1 for b in span_set if b in diff_set)
        if diffs == 0:
            return 0
        claimed_bytes.update(span_set)
        b19 = r19[start:end + 1]
        b13 = r13[start:end + 1]
        blocks.append({
            "start": start,
            "end": end,
            "extent": end - start + 1,
            "diffs": diffs,
            "pct_diff": f"{100.0 * diffs / (end - start + 1):.1f}%",
            "category": category,
            "storage": storage,
            "dimensions": dimensions,
            "name": name,
            "consumers": consumers or "-",
            "pattern": classify_variant_pattern(b19, b13, category),
            "el19a_hex": format_hex_sample(b19),
            "el13a_hex": format_hex_sample(b13),
            "twin_notes": twin_notes or "-",
            "helper": helper,
        })
        return diffs

    # 1. XML definitions
    xml_sources = [
        Path("public/assets/aistudio/EL19A_merged_definition_v3_08a300db.xml"),
        Path("public/assets/aistudio/EL19A_ignition_decoded_fragment_33ea8e67.xml"),
        Path("EVIDENCE/EL19A_ETC_Dashpot_Limiters_fragment-2.xml"),
    ]
    xml_entries = {}
    for xf in xml_sources:
        if not xf.exists():
            continue
        for t in ET.parse(xf).getroot().iter("table"):
            sa = t.attrib.get("storageaddress") or t.attrib.get("address")
            if not sa:
                continue
            addr = int(sa, 16)
            st = (t.attrib.get("storagetype") or t.attrib.get("storage_type") or "uint8").lower()
            sx = int(t.attrib.get("sizex") or "1")
            sy = int(t.attrib.get("sizey") or "1")
            elems = int(t.attrib.get("elements") or (sx * sy))
            sz = elems * STOR_BYTES.get(st, 1)
            end = addr + sz - 1
            if any(b in diff_set for b in range(addr, end + 1)):
                xml_entries.setdefault((addr, end), []).append((xf.name, t.attrib.get("name", ""), st, sx, sy))

    for (s, e), infos in sorted(xml_entries.items()):
        # Prefer merged v3 name, append fragment alias if distinct
        names = []
        for fn, nm, _, _, _ in infos:
            clean_nm = nm.split(" | ")[0].strip()
            if clean_nm and clean_nm not in names:
                names.append(clean_nm)
        _, _, st, sx, sy = infos[0]
        dims = f"{sx}x{sy}" if (sx > 1 or sy > 1) else "1D"
        stor = {"uint8": "UBYTE", "int8": "SBYTE", "uint16": "UWORD_BE", "int16": "SWORD_BE"}.get(st, st.upper())
        # Collect consumers from pool_loads / literal_refs if any
        refs = pool_loads.get(s) or literal_refs.get(s) or []
        cons = "; ".join(f"{fn}@0x{pc:X}" for pc, fn, *_ in refs[:4])
        add_block(s, e, "xml_table", stor, dims, " / ".join(names[:2]), cons, f"XML ({infos[0][0]})")

    # 2. Catalog 179 tables + axes
    cat_twin_map = {
        0x0D456: "Normal-path twin of Trustful 0x121C4 (both diff 403/512B)",
        0x121C4: "Trustful twin of Normal 0x0D456 (both diff 403/512B)",
        0x0D656: "Normal-path twin of Trustful 0x123C4 (both diff 399/512B)",
        0x123C4: "Trustful twin of Normal 0x0D656 (both diff 399/512B)",
        0x10CE2: "Normal-path twin of Trustful 0x12A6E / 0x12D38 (all diff 14/32B)",
        0x12A6E: "Trustful twin of Normal 0x10CE2 / 0x12D38 (all diff 14/32B)",
        0x12D38: "Trustful twin of Normal 0x10CE2 / 0x12A6E (all diff 14/32B)",
    }
    cat_axis_candidates = {}
    with open("CALIBRATIONS/discovered_tables_catalog.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            addr = int(row["address"], 16)
            m = re.match(r"0x([0-9A-Fa-f]+)-0x([0-9A-Fa-f]+)", row["extent_hex"])
            end = int(m.group(2), 16) if m else addr
            srow = cat_summary.get(addr, {})
            cons = srow.get("traced_reader_sites") or row.get("helper_or_reader") or "-"
            dest = srow.get("catalog_dest_ram") or row.get("destination_ram") or ""
            notes = cat_twin_map.get(addr, row.get("notes", "")[:90])
            if dest and dest != "-":
                notes = f"{notes}; dest={dest}" if notes else f"dest={dest}"
            add_block(
                addr,
                end,
                "cat179_table",
                row["storage"].replace(" ", "_"),
                row["dimensions"],
                f"Cat179_{row['address']} ({row['source_wo']})",
                cons,
                notes,
                row.get("helper_or_reader", "-"),
            )
            # Extract explicit ROM axis only for helpers that actually take an explicit ROM axis
            helper_str = row.get("helper_or_reader", "")
            explicit_axis_helpers = (
                "sub_22CF8", "sub_22D30", "sub_22D68", "sub_22EFC",
                "sub_22F28", "sub_22F54", "sub_22F80", "sub_22FAC",
                "sub_230B0", "sub_23170", "sub_2319C",
            )
            if not any(h in helper_str for h in explicit_axis_helpers):
                continue
            mx = re.match(r"(\d+)x(\d+)", row["dimensions"])
            nx, ny = (int(mx.group(1)), int(mx.group(2))) if mx else (1, 1)
            for ax_col, ax_len in (("axis1", nx), ("axis2", ny)):
                ax_val = row.get(ax_col, "").strip()
                for am in re.finditer(r"0x([0-9A-Fa-f]{4,5})\b", ax_val):
                    ax_addr = int(am.group(1), 16)
                    if ax_addr == 0x08CD3:
                        continue
                    w = 2 if ("UWORD" in ax_val or "U16" in ax_val or "S16" in ax_val or "SWORD" in ax_val or (ax_addr >= 0xF500 and "UBYTE" not in ax_val and "U8" not in ax_val)) else 1
                    sm = re.search(r"\((\d+)x1\b", ax_val)
                    cnt = int(sm.group(1)) if sm else ax_len
                    if "3-thresh" in ax_val:
                        cnt, w = 3, 1
                    ax_end = ax_addr + cnt * w - 1
                    cat_axis_candidates.setdefault((ax_addr, ax_end, w, cnt), []).append(f"{row['address']}.{ax_col}")

    axis_twin_notes = {
        0x0F6F2: "Normal axis of 0x0D456/0x0D656; Trustful twin of 0x128DE (both diff 19/32B)",
        0x128DE: "Trustful axis of 0x121C4/0x123C4; twin of 0x0F6F2 (both diff 19/32B)",
        0x1133A: "Normal axis of 0x0D456/0x0D656; Trustful twin of 0x12E18 (both diff 19/32B)",
        0x12E18: "Trustful axis of 0x121C4/0x123C4; twin of 0x1133A (both diff 19/32B)",
        0x109B4: "Axis of 0x10206 & 0x10226 (16x1 UWORD BE)",
        0x0FCFC: "Axis of Cat179 8x8 table 0x0B756",
    }
    for (ax_s, ax_e, w, cnt), parents in sorted(cat_axis_candidates.items()):
        stor = "UWORD_BE" if w == 2 else "UBYTE"
        refs = pool_loads.get(ax_s) or literal_refs.get(ax_s) or []
        cons = "; ".join(f"{fn}@0x{pc:X}" for pc, fn, *_ in refs[:4])
        add_block(
            ax_s,
            ax_e,
            "cat179_axis",
            stor,
            f"{cnt}x1",
            f"Axis_0x{ax_s:05X} (for {', '.join(parents[:3])})",
            cons,
            axis_twin_notes.get(ax_s, f"Explicit Cat179 axis ({', '.join(parents[:3])})"),
            "axis_lookup",
        )

    # 3. Newly discovered structured tables, axes, option byte, CALIDs, checksums
    curated_discoveries = [
        (0x08200, 0x08201, "calid_header", "UWORD_BE", "1D", "CAL_Zone_Header_Word_0x08200 (skipped by sub_BE352)", "sub_BE352 (skipped)", "0x0D03 (EL19A) vs 0x7F5F (EL13A)", "header_word"),
        (0x08204, 0x08219, "calid_header", "ASCII", "22B", "Dual_CALID_Strings ('1EL19A00000' vs '1EL13A00000')", "sub_226E@0x232C (GBR=0x8204)", "Bytes 0x08208 & 0x08213 ('9' vs '3')", "gbr_disp"),
        (0x0DE85, 0x0DE89, "calid_header", "ASCII", "5B", "CALID_String_2 ('EL19A' vs 'EL13A')", "sub_B57D8; sub_B862C", "Byte 0x0DE89 ('9' vs '3')", "ascii_id"),
        (0x0DF46, 0x0DF4B, "calid_header", "ASCII", "6B", "CALID_String_3 ('1EL19A' vs '1EL13A')", "sub_2F470@0x2F5C0; sub_2DE1C; sub_333D4", "Byte 0x0DF4A ('9' vs '3')", "ascii_id"),
        (0x08CD3, 0x08CD3, "option_byte", "UBYTE", "1D", "Master_Option_Bitflag_0x08CD3 (bit7=1 EL19A vs bit3,2=1 EL13A)", "107 CODE pool loads (74x bit7, 5x bit4, 1x bit3, 1x bit2)", "EL19A=0x80 vs EL13A=0x0C; gates 0x0A0F2/sub_2DE1C/sub_333D4", "tst_bitflag"),
        (0x09392, 0x0939F, "uncatalogued_table", "UWORD_BE", "7x1", "7_UWORD_Ratio_And_Threshold_Array_0x09392", "sub_BF34C@0xBF550..0xBF56C", "5 words flat 0x64AB in EL19A vs ramped 0x20BE..0x8665 in EL13A", "direct_uword_loads"),
        (0x099DC, 0x099DF, "checksum_32bit", "UINT32_BE", "1D", "ROM_Checksum_XOR32_0x099DC", "sub_BE352@0xBE782; sub_20FEA@0x213A0", "Verified exact XOR32 over 0x08200..0xFFFFF excl {0x8200,0x99DC,0x99E4,0x20000}", "sub_BE352"),
        (0x099E4, 0x099E7, "checksum_32bit", "UINT32_BE", "1D", "ROM_Checksum_ADD32_0x099E4", "sub_BE352@0xBE788", "Verified exact ADD32 over 0x08200..0xFFFFF excl {0x8200,0x99DC,0x99E4,0x20000}", "sub_BE352"),
        (0x099F0, 0x09A1C, "variant_struct", "UBYTE", "5x9", "Gear_Or_Range_Gate_Matrix_A_0x099F0", "sub_6664A@0x6688C; sub_664B2@0x665FA", "Paired with 0x0B6A2; EL13A active only on slot 3 vs EL19A multi-slot", "5x9_matrix"),
        (0x09A1D, 0x09A49, "variant_struct", "UBYTE", "5x9", "Gear_Or_Range_Gate_Matrix_B_0x09A1D", "sub_28C36@0x291F4; sub_664B2@0x66540", "Paired with 0x0B6FC; mirror of 0x099F0", "5x9_matrix"),
        (0x09A66, 0x09A91, "variant_struct", "STRUCT", "11x4B", "Monitor_Descriptor_Table_0x09A66", "sub_841C8 (22 CODE loads)", "3 slots (0x09A66,0x09A6A,0x09A8E) disabled 05 00 00 00 in EL19A vs active in EL13A", "4B_slot_table"),
        (0x0AFF2, 0x0B001, "uncatalogued_table", "UBYTE", "4x4", "Uncatalogued_4x4_UBYTE_Table_0x0AFF2", "sub_5B336@0x5B3AE", "All 0x00 in EL19A vs populated (03..06) in EL13A", "sub_5B336"),
        (0x0B002, 0x0B011, "uncatalogued_table", "UBYTE", "4x4", "Uncatalogued_4x4_UBYTE_Table_0x0B002", "sub_5B336@0x5B3A2", "Paired with 0x0AFF2; 3 bytes nonzero in EL13A vs 0x00 in EL19A", "sub_5B336"),
        (0x0B6A2, 0x0B6FB, "variant_struct", "UWORD_BE", "5x9", "Gear_Or_Range_Matrix_A_UWORD_0x0B6A2", "sub_6664A@0x66888; sub_664B2@0x665C2", "Twin of 0x0B6FC; EL13A populates only index 3 (+row2 0x8000) for CVT D-range", "5x9_matrix"),
        (0x0B6FC, 0x0B755, "variant_struct", "UWORD_BE", "5x9", "Gear_Or_Range_Matrix_B_UWORD_0x0B6FC", "sub_28C36@0x28F84; sub_664B2@0x66508", "Twin of 0x0B6A2; identically structured 5x9 UWORD matrix", "5x9_matrix"),
        (0x0E5CE, 0x0E5CF, "uncatalogued_table", "UBYTE", "2B", "Header_Or_Scalar_0x0E5CE_Before_0x0E5D0", "sub_5B336@0x5B458 (dword_E5CC)", "0x60 0x88 (EL19A) vs 0x44 0x88 (EL13A)", "sub_5B336"),
        (0x0E5D0, 0x0E5D7, "uncatalogued_table", "UBYTE", "8x1", "Uncatalogued_8x1_UBYTE_Curve_0x0E5D0", "sub_5B336@0x5B576 (sub_22DF8)", "All 0x00 in EL19A vs populated in EL13A", "sub_22DF8"),
        (0x0E5D8, 0x0E5DF, "uncatalogued_table", "UBYTE", "8x1", "Uncatalogued_8x1_UBYTE_Curve_0x0E5D8", "sub_5B336@0x5B56A (sub_22DF8)", "All 0x00 in EL19A vs populated in EL13A", "sub_22DF8"),
        (0x0E5E0, 0x0E5E7, "uncatalogued_table", "UBYTE", "8x1", "Uncatalogued_8x1_UBYTE_Curve_0x0E5E0", "sub_5B336@0x5B56E (sub_22DF8)", "All 0x00 in EL19A vs populated in EL13A", "sub_22DF8"),
        (0x0E5E8, 0x0E5EF, "uncatalogued_table", "UBYTE", "8x1", "Uncatalogued_8x1_UBYTE_Curve_0x0E5E8", "sub_5B336@0x5B57A (sub_22DF8)", "All 0x00 in EL19A vs populated in EL13A", "sub_22DF8"),
        (0x0E5F0, 0x0E5FA, "uncatalogued_table", "UBYTE", "11x1", "Uncatalogued_Array_0x0E5F0", "sub_5B336@0x5B4B0; sub_5B336@0x5B500", "EL19A zeroed around FF block vs populated 09 0D 04..09 0D 04 in EL13A", "sub_5B336"),
        (0x0E658, 0x0E65F, "uncatalogued_table", "UBYTE", "8x1", "Uncatalogued_8x1_UBYTE_Curve_0x0E658", "sub_5A48C@0x5A6C8 (sub_22DF8)", "Flat 0x00 in EL19A vs flat 0x1B in EL13A", "sub_22DF8"),
        (0x0E848, 0x0E84F, "uncatalogued_table", "UBYTE", "8x1", "Uncatalogued_8x1_UBYTE_Curve_0x0E848", "sub_441B0@0x443C0", "Monotonic 8-pt curve shifted between EL19A and EL13A", "sub_441B0"),
        (0x0E858, 0x0E85F, "uncatalogued_table", "UBYTE", "8x1", "Uncatalogued_8x1_UBYTE_Curve_0x0E858", "sub_441B0@0x443BC", "Diff at indices 1..2 (0x85 -> 0x86)", "sub_441B0"),
        (0x0ED2E, 0x0ED33, "uncatalogued_table", "UBYTE", "6B", "Uncatalogued_Paired_Params_0x0ED2E_0x0ED31", "sub_491BC@0x49420, 0x49424", "Two 3-byte records loaded in sub_491BC", "sub_491BC"),
        (0x0ED8C, 0x0ED9B, "uncatalogued_table", "UBYTE", "16x1", "Uncatalogued_16x1_UBYTE_Curve_0x0ED8C", "sub_3BC68@0x3BF54", "Tail 11 bytes (0x0ED91..0x0ED9B) 0x00 in EL19A vs active in EL13A", "sub_3BC68"),
        (0x0EE48, 0x0EE57, "uncatalogued_table", "UBYTE", "16x1", "Uncatalogued_16x1_UBYTE_Curve_0x0EE48", "sub_40790@0x40C40", "Tail 11 bytes (0x0EE4D..0x0EE57) 0x00 in EL19A vs active in EL13A", "sub_40790"),
        (0x0F0C2, 0x0F0C9, "uncatalogued_table", "UBYTE", "8x1", "Uncatalogued_8x1_UBYTE_Curve_0x0F0C2 (axis 0xE3B3)", "sub_40790@0x40AD6 (sub_22EFC)", "All 0x00 in EL19A vs monotonic 0x80..0xC0 in EL13A", "sub_22EFC"),
        (0x0F136, 0x0F13D, "uncatalogued_table", "UBYTE", "8x1", "Uncatalogued_8x1_UBYTE_Curve_0x0F136", "sub_346E0@0x34AF2 (sub_22DF8)", "All 0x00 in EL19A vs 0x05*8 in EL13A", "sub_22DF8"),
        (0x0F13E, 0x0F145, "uncatalogued_table", "UBYTE", "8x1", "Uncatalogued_8x1_UBYTE_Curve_0x0F13E", "sub_346E0@0x34B48 (sub_22DF8)", "All 0x00 in EL19A vs 0x05*8 in EL13A", "sub_22DF8"),
        (0x0F146, 0x0F14D, "uncatalogued_table", "UBYTE", "8x1", "Uncatalogued_8x1_UBYTE_Curve_0x0F146", "sub_3D9FC@0x3DA0E (sub_22DF8)", "All 0x00 in EL19A vs 0x06*8 in EL13A", "sub_22DF8"),
        (0x0F16E, 0x0F175, "uncatalogued_table", "UBYTE", "8x1", "Uncatalogued_8x1_UBYTE_Curve_0x0F16E", "sub_5ADE8@0x5AE70 (sub_22EFC)", "Plateau 0x4D in EL19A vs 0x31..0x8D in EL13A", "sub_22EFC"),
        (0x0F176, 0x0F17D, "uncatalogued_table", "UBYTE", "8x1", "Uncatalogued_8x1_UBYTE_Curve_0x0F176", "sub_5ADE8@0x5AF70 (sub_22EFC)", "Plateau 0x4D in EL19A vs 0x40..0x73 in EL13A", "sub_22EFC"),
        (0x0F17E, 0x0F185, "uncatalogued_table", "UBYTE", "8x1", "Uncatalogued_8x1_UBYTE_Curve_0x0F17E", "sub_5ADE8@0x5AF6C (sub_22EFC)", "Plateau 0x4D in EL19A vs 0x40..0x8D in EL13A", "sub_22EFC"),
        (0x0F186, 0x0F18D, "uncatalogued_table", "UBYTE", "8x1", "Uncatalogued_8x1_UBYTE_Curve_0x0F186", "sub_5ADE8@0x5AF74 (sub_22EFC)", "Differs at index 2 (0x34 in EL19A vs 0x30 in EL13A)", "sub_22EFC"),
        (0x0F18E, 0x0F195, "uncatalogued_table", "UBYTE", "8x1", "Uncatalogued_8x1_UBYTE_Curve_0x0F18E", "sub_5ADE8@0x5AF5C (sub_22EFC)", "Plateau 0x4D in EL19A vs 0x31..0x8D in EL13A", "sub_22EFC"),
        (0x0F196, 0x0F19D, "uncatalogued_table", "UBYTE", "8x1", "Uncatalogued_8x1_UBYTE_Curve_0x0F196", "sub_5ADE8@0x5AF64 (sub_22EFC)", "Plateau 0x4D in EL19A vs 0x40..0x73 in EL13A", "sub_22EFC"),
        (0x0F19E, 0x0F1A5, "uncatalogued_table", "UBYTE", "8x1", "Uncatalogued_8x1_UBYTE_Curve_0x0F19E", "sub_5ADE8@0x5AF60 (sub_22EFC)", "Plateau 0x4D in EL19A vs 0x40..0x8D in EL13A", "sub_22EFC"),
        (0x0F1AA, 0x0F1B1, "uncatalogued_table", "UBYTE", "8x1", "Uncatalogued_8x1_UBYTE_Curve_0x0F1AA", "sub_5B124@0x5B194 (sub_22DF8)", "All 0x00 in EL19A vs 0x1A in EL13A", "sub_22DF8"),
        (0x0F1B2, 0x0F1B9, "uncatalogued_table", "UBYTE", "8x1", "Uncatalogued_8x1_UBYTE_Curve_0x0F1B2", "sub_5B124@0x5B198 (sub_22DF8)", "Flat 0x1A in EL19A vs flat 0x26 in EL13A", "sub_22DF8"),
        (0x0F1BA, 0x0F1C1, "uncatalogued_table", "UBYTE", "8x1", "Uncatalogued_8x1_UBYTE_Curve_0x0F1BA", "sub_5B124@0x5B18C (sub_22DF8)", "All 0x00 in EL19A vs flat 0x1A in EL13A", "sub_22DF8"),
        (0x0F1C2, 0x0F1C9, "uncatalogued_table", "UBYTE", "8x1", "Uncatalogued_8x1_UBYTE_Curve_0x0F1C2", "sub_5B124@0x5B190 (sub_22DF8)", "Flat 0x1A in EL19A vs 0x13..0x26 in EL13A", "sub_22DF8"),
        (0x0F1CA, 0x0F1D1, "uncatalogued_table", "UBYTE", "8x1", "Uncatalogued_8x1_UBYTE_Curve_0x0F1CA", "sub_5ADE8@0x5AF1C (sub_22EFC)", "00 + 85*7 in EL19A vs 40..99 in EL13A (mirrors 0x0F1E2)", "sub_22EFC"),
        (0x0F1D2, 0x0F1D9, "uncatalogued_table", "UBYTE", "8x1", "Uncatalogued_8x1_UBYTE_Curve_0x0F1D2", "sub_5ADE8@0x5AF28 (sub_22EFC)", "00 + 85*7 in EL19A vs 26..B3 in EL13A (mirrors 0x0F1EA)", "sub_22EFC"),
        (0x0F1DA, 0x0F1E1, "uncatalogued_table", "UBYTE", "8x1", "Uncatalogued_8x1_UBYTE_Curve_0x0F1DA", "sub_5ADE8@0x5AF36 (sub_22EFC)", "00 + 85*7 in EL19A vs 26..40 in EL13A (mirrors 0x0F1F2)", "sub_22EFC"),
        (0x0F1E2, 0x0F1E9, "uncatalogued_table", "UBYTE", "8x1", "Uncatalogued_8x1_UBYTE_Curve_0x0F1E2", "sub_5ADE8@0x5AEF8 (sub_22EFC)", "00 + 85*7 in EL19A vs 40..99 in EL13A (mirrors 0x0F1CA)", "sub_22EFC"),
        (0x0F1EA, 0x0F1F1, "uncatalogued_table", "UBYTE", "8x1", "Uncatalogued_8x1_UBYTE_Curve_0x0F1EA", "sub_5ADE8@0x5AF04 (sub_22EFC)", "00 + 85*7 in EL19A vs 26..B3 in EL13A (mirrors 0x0F1D2)", "sub_22EFC"),
        (0x0F1F2, 0x0F1F9, "uncatalogued_table", "UBYTE", "8x1", "Uncatalogued_8x1_UBYTE_Curve_0x0F1F2 (0x0F1EA+8)", "sub_5ADE8@0x5AF12..0x5AF16 (sub_22EFC)", "00 + 85*7 in EL19A vs 26..40 in EL13A (mirrors 0x0F1DA)", "sub_22EFC"),
        (0x0F276, 0x0F27D, "uncatalogued_table", "UBYTE", "8x1", "Uncatalogued_8x1_UBYTE_Curve_0x0F276 (axis 0xE2C1)", "sub_40790@0x40B4A (sub_22EFC)", "All 0x00 in EL19A vs monotonic 0x0E..0x08 in EL13A", "sub_22EFC"),
        (0x0F316, 0x0F31D, "uncatalogued_table", "UBYTE", "8x1", "Uncatalogued_8x1_UBYTE_Curve_0x0F316", "sub_45AB6@0x45BFC", "Paired with 0x0F322 in sub_45AB6", "sub_45AB6"),
        (0x0F322, 0x0F325, "uncatalogued_table", "UBYTE", "4x1", "Uncatalogued_4x1_UBYTE_Curve_0x0F322", "sub_45AB6@0x45C88", "Paired with 0x0F316 in sub_45AB6", "sub_45AB6"),
        (0x0F326, 0x0F32D, "uncatalogued_table", "UBYTE", "8x1", "Uncatalogued_8x1_UBYTE_Curve_0x0F326", "sub_40790@0x40C80", "Tail 0x0F32A..0x0F32D is 0x00 in EL19A vs 09 15 24 37 in EL13A", "sub_40790"),
        (0x10146, 0x10155, "uncatalogued_table", "UWORD_BE", "8x1", "Uncatalogued_8x1_UWORD_Curve_0x10146", "sub_416E4@0x41714 (sub_22E60)", "All 0xFFFF in EL19A vs flat 0x027C (636) in EL13A", "sub_22E60"),
        (0x10BAE, 0x10BB7, "uncatalogued_table", "UWORD_BE", "5x1", "Uncatalogued_5x1_UWORD_Vector_0x10BAE", "sub_5C91A@0x5CAA0", "5 UWORDs differing across EL19A vs EL13A", "sub_5C91A"),
        (0x10BD8, 0x10BDB, "uncatalogued_table", "UWORD_BE", "2x1", "Uncatalogued_2x1_UWORD_Pair_0x10BD8", "sub_BF814@0xC0960", "[100, 300] (EL19A) vs [200, 400] (EL13A)", "sub_BF814"),
        (0x10CC2, 0x10CE1, "uncatalogued_axis", "UWORD_BE", "16x1", "Axis_0x10CC2 (for Cat179 0x10CE2)", "sub_6F5E8@0x6F6F4 (sub_22F80)", "Twin of Trustful axes 0x12A4E & 0x12D18 (all diff 13/32B)", "sub_22F80"),
        (0x12A4E, 0x12A6D, "uncatalogued_axis", "UWORD_BE", "16x1", "Axis_0x12A4E (for Cat179 0x12A6E)", "sub_6F8EC@0x6F920 (sub_23170)", "Trustful twin of 0x10CC2 & 0x12D18 (all diff 13/32B)", "sub_23170"),
        (0x12D18, 0x12D37, "uncatalogued_axis", "UWORD_BE", "16x1", "Axis_0x12D18 (for Cat179 0x12D38)", "sub_6F8EC@0x6F90A (sub_23170)", "Trustful twin of 0x10CC2 & 0x12A4E (all diff 13/32B)", "sub_23170"),
        (0x113C4, 0x113C7, "uncatalogued_table", "UWORD_BE", "2x1", "Trustful_Pair_0x113C4 (twin of 0x091EE)", "sub_67D0C@0x68014, 0x68018", "0x015E 0x02FC (EL19A) vs 0x0000 0x0000 (EL13A); exact twin of 0x091EE", "sub_67D0C"),
        (0x091EE, 0x091F1, "uncatalogued_table", "UWORD_BE", "2x1", "Normal_Pair_0x091EE (twin of 0x113C4)", "sub_66CDC@0x67060, 0x67064", "0x015E 0x02FC (EL19A) vs 0x0000 0x0000 (EL13A); exact twin of 0x113C4", "sub_66CDC"),
        (0x095A6, 0x095A7, "uncatalogued_table", "UWORD_BE", "1D", "Normal_Scalar_0x095A6 (twin of 0x11714+0)", "sub_28C36@0x29B10; sub_6ABAA (4 refs)", "0x0FA7 (4007) -> 0x0C04 (3076); matches upper half of 0x11714", "scalar_pair"),
        (0x095B4, 0x095B5, "uncatalogued_table", "UWORD_BE", "1D", "Normal_Scalar_0x095B4 (twin of 0x11714+2)", "sub_831DC@0x8344C", "0x0315 (789) -> 0x02A7 (679); matches lower half of 0x11714", "scalar_pair"),
        (0x11714, 0x11717, "uncatalogued_table", "UWORD_BE", "2x1", "Trustful_Pair_0x11714 (twin of 0x095A6 & 0x095B4)", "sub_69D1C@0x69FFC", "0x0FA7 0x0315 -> 0x0C04 0x02A7; exact concatenation of 0x095A6 & 0x095B4", "sub_69D1C"),
        (0x0971A, 0x0971B, "uncatalogued_table", "UWORD_BE", "1D", "Normal_Scalar_0x0971A (twin of 0x11722)", "sub_6A9E8; sub_6B0EC; sub_6BFE4 (4 refs)", "0x2D42 -> 0x2ED6; exact twin of Trustful 0x11722", "scalar_pair"),
        (0x11722, 0x11723, "uncatalogued_table", "UWORD_BE", "1D", "Trustful_Scalar_0x11722 (twin of 0x0971A)", "sub_6A0D4@0x6A1A0; sub_6A42C@0x6A4A0", "0x2D42 -> 0x2ED6; exact twin of Normal 0x0971A", "scalar_pair"),
    ]
    for s, e, cat, stor, dims, name, cons, notes, helper in curated_discoveries:
        add_block(s, e, cat, stor, dims, name, cons, notes, helper)

    # 4. Remaining diff bytes -> cluster (gap <= 2) as scalar_or_flag_run with pool/EA provenance
    rem = sorted(diff_set - claimed_bytes)
    clusters = []
    for b in rem:
        if not clusters or b - clusters[-1][-1] > 2:
            clusters.append([b])
        else:
            clusters[-1].append(b)

    for cl in clusters:
        s, e = cl[0], cl[-1]
        refs = []
        for b in range(s, e + 1):
            for pc, fn, rn, ctx in pool_loads.get(b, []):
                refs.append(f"{fn}@0x{pc:X}(0x{b:X})")
            for pc, fn, body in literal_refs.get(b, []):
                tag = f"{fn}@0x{pc:X}(0x{b:X})"
                if tag not in refs:
                    refs.append(tag)
            for pc, fn, form, note in ea_map.get(b, []):
                tag = f"{fn}@0x{pc}({form}:0x{b:X})"
                if tag not in refs:
                    refs.append(tag)
        # Also look for nearby base pointer within -4 bytes for UWORD/DWORD alignment
        if not refs:
            for base_off in range(max(0x08200, s - 3), s):
                for pc, fn, rn, ctx in pool_loads.get(base_off, []):
                    refs.append(f"{fn}@0x{pc:X}(base=0x{base_off:X})")
        cons = "; ".join(refs[:5]) if refs else "-"
        stor = "UWORD_BE" if (e - s + 1) == 2 else ("UBYTE" if s == e else "RAW_BYTES")
        add_block(
            s,
            e,
            "scalar_or_flag_run",
            stor,
            "1D" if (e - s + 1) <= 2 else f"{e - s + 1}B",
            f"Scalar_Or_Flag_0x{s:05X}",
            cons,
            f"Direct scalar/flag/struct diff ({len(cl)}/{e - s + 1} bytes)",
            "pool_or_gbr",
        )

    # Strict verification
    total_claimed_diffs = sum(b["diffs"] for b in blocks)
    if total_claimed_diffs != len(diff_set):
        raise AssertionError(f"Partition sum mismatch: {total_claimed_diffs} != {len(diff_set)}")

    blocks.sort(key=lambda b: b["start"])

    # Write INDEX/el19a_vs_el13a_diff_blocks.tsv
    args.out_blocks.parent.mkdir(parents=True, exist_ok=True)
    block_cols = [
        "block_id",
        "start_addr",
        "end_addr",
        "extent_bytes",
        "diff_bytes",
        "pct_diff",
        "category",
        "storage",
        "dimensions",
        "name_or_label",
        "consumer_funcs",
        "variant_pattern",
        "el19a_sample_hex",
        "el13a_sample_hex",
        "twin_or_notes",
    ]
    with args.out_blocks.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(block_cols)
        for idx, b in enumerate(blocks, 1):
            w.writerow([
                f"BLK_{idx:03d}",
                f"0x{b['start']:05X}",
                f"0x{b['end']:05X}",
                b["extent"],
                b["diffs"],
                b["pct_diff"],
                b["category"],
                b["storage"],
                b["dimensions"],
                b["name"],
                b["consumers"],
                b["pattern"],
                b["el19a_hex"],
                b["el13a_hex"],
                b["twin_notes"],
            ])

    # Write INDEX/el19a_vs_el13a_unmapped_targets.tsv (everything NOT xml_table / cat179_table)
    unmapped = [b for b in blocks if b["category"] not in ("xml_table", "cat179_table")]
    unm_cols = [
        "target_id",
        "start_addr",
        "end_addr",
        "extent_bytes",
        "diff_bytes",
        "classification",
        "storage",
        "dimensions",
        "variant_pattern",
        "helper_or_access",
        "code_ref_count",
        "reader_pcs_and_funcs",
        "el19a_hex",
        "el13a_hex",
        "evidence_notes",
    ]
    with args.out_unmapped.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(unm_cols)
        for idx, b in enumerate(unmapped, 1):
            # count exact refs across start..end
            ref_count = sum(
                len(pool_loads.get(addr, [])) or len(literal_refs.get(addr, []))
                for addr in range(b["start"], b["end"] + 1)
            )
            w.writerow([
                f"UNM_{idx:03d}",
                f"0x{b['start']:05X}",
                f"0x{b['end']:05X}",
                b["extent"],
                b["diffs"],
                b["category"],
                b["storage"],
                b["dimensions"],
                b["pattern"],
                b["helper"],
                ref_count,
                b["consumers"],
                b["el19a_hex"],
                b["el13a_hex"],
                b["twin_notes"],
            ])

    # Print crisp summary
    by_cat = {}
    for b in blocks:
        c = b["category"]
        cnt, db = by_cat.get(c, (0, 0))
        by_cat[c] = (cnt + 1, db + b["diffs"])

    print(f"Verified EL19A vs EL13A diff partition: {len(blocks)} blocks, {total_claimed_diffs}/3708 diff bytes")
    for c, (cnt, db) in sorted(by_cat.items(), key=lambda kv: -kv[1][1]):
        print(f"  {c:20s}: {cnt:3d} blocks, {db:4d} diff bytes ({100.0 * db / 3708:5.1f}%)")
    print(f"Wrote {args.out_blocks} and {args.out_unmapped} ({len(unmapped)} non-XML/non-Cat179 targets)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
