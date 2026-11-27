#!/usr/bin/env python3
"""
Milestone 3 Standalone Relational A2L / XML / ROM Reference Indexer (`tools/romraider_ref_index.py`)

Independently executable, rebuildable reference database builder and matcher.
Implements Milestone 3 (WO70034 + WO70035) and Manager Refinement E:
  1. Relational A2L parser (`CHARACTERISTIC`, `AXIS_PTS`, `MEASUREMENT`, `COMPU_METHOD`,
     `COMPU_TAB`, `COMPU_VTAB`, `RECORD_LAYOUT`, `FUNCTION`, `GROUP`), retaining duplicate
     address declarations, raw formulas, and source SHA-256 hashes.
  2. Ingestion of `CONTROL/WO70017_DONOR_METADATA.tsv`.
  3. Multi-source RomRaider XML corpus indexer (`.xml`, directories, and `.zip` archives),
     recording `<romid>`, `<scaling>`, `<table>` + nested axes, and parse errors without failing.
  4. Metadata-bounded ROM signature indexer (code-window hashes bounded by discovered
     layout/FID/active_end — never a single hardcoded split) + non-trivial payload hashes.
  5. Cross-reference matcher preserving all conflicts and keeping every donor lead typed as
     `evidence_class="donor"` (`is_target_proof=False`).
"""
import argparse
import csv
import hashlib
import io
import json
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from nissan_sh705x_workbench import load_any_rom, parse_nissan_metadata  # noqa: E402
from sh7058_cross_rom_scanner import (  # noqa: E402
    _address_hex,
    discover_helpers,
    extract_calls,
    infer_layout,
)
from sh705x_discovery_v2 import DATA_MODEL_VERSION, atomic_write_json  # noqa: E402

SCHEMA_REF_INDEX_V1 = "sh705x-ref-index-v1"
INDEX_SCHEMA_VERSION = "1.0.0"
PARSER_VERSION = "1.0.0"


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


# ---------------------------------------------------------------------------
# 1. Relational A2L Parser (Preserves Duplicates & Full Relation Graph)
# ---------------------------------------------------------------------------

def _iter_a2l_blocks(txt: str, keyword: str) -> Iterable[str]:
    marker_begin = f"/begin {keyword}"
    marker_end = f"/end {keyword}"
    pos = 0
    while True:
        idx = txt.find(marker_begin, pos)
        if idx == -1:
            break
        start_body = idx + len(marker_begin)
        # Ensure word boundary after keyword
        if start_body < len(txt) and not txt[start_body].isspace():
            pos = start_body
            continue
        end = txt.find(marker_end, start_body)
        if end == -1:
            yield txt[start_body:].strip()
            break
        yield txt[start_body:end].strip()
        pos = end + len(marker_end)


def _strip_subblocks(body: str, sub_kw: str) -> Tuple[str, List[str]]:
    subs: List[str] = []
    out_parts: List[str] = []
    mb = f"/begin {sub_kw}"
    me = f"/end {sub_kw}"
    pos = 0
    while True:
        idx = body.find(mb, pos)
        if idx == -1:
            out_parts.append(body[pos:])
            break
        out_parts.append(body[pos:idx])
        sb = idx + len(mb)
        end = body.find(me, sb)
        if end == -1:
            subs.append(body[sb:].strip())
            break
        subs.append(body[sb:end].strip())
        pos = end + len(me)
    return "".join(out_parts), subs


def _compute_linear_formula(coeffs: Optional[List[float]]) -> Optional[str]:
    if not coeffs or len(coeffs) != 6:
        return None
    a, b, c, d, e, f = coeffs
    if a == 0.0 and d == 0.0 and e == 0.0 and b != 0.0:
        scale = f / b
        off = -c / b
        if off == 0.0:
            return f"x*{scale:g}"
        return f"x*{scale:g}{off:+g}"
    return None


def parse_a2l_bytes_relational(raw: bytes, source_path: str = "<memory>") -> dict:
    """
    Parse ASAP2 A2L bytes relationally without collapsing duplicate addresses.
    Retains COMPU_METHOD, COMPU_TAB, COMPU_VTAB, RECORD_LAYOUT, AXIS_PTS,
    CHARACTERISTIC (with AXIS_DESCR), MEASUREMENT, FUNCTION, and GROUP.
    """
    txt = raw.decode("cp932", errors="replace")
    src_sha = _sha256_bytes(raw)
    source_id = f"a2l:{Path(source_path).name}#{src_sha[:12]}"

    compu_methods: Dict[str, dict] = {}
    for blk in _iter_a2l_blocks(txt, "COMPU_METHOD"):
        m = re.match(r'^(\S+)\s+"([^"]*)"\s+(\S+)\s+"([^"]*)"\s+"([^"]*)"', blk)
        if not m:
            continue
        name, desc, conv_type, fmt, unit = m.groups()
        cm = re.search(
            r"\bCOEFFS\s+([-\deE.+]+)\s+([-\deE.+]+)\s+([-\deE.+]+)\s+([-\deE.+]+)\s+([-\deE.+]+)\s+([-\deE.+]+)",
            blk,
        )
        coeffs = [float(x) for x in cm.groups()] if cm else None
        ref_tab = re.search(r"\bCOMPU_TAB_REF\s+(\S+)", blk)
        compu_methods[name] = {
            "name": name,
            "desc": desc,
            "conversion_type": conv_type,
            "format": fmt,
            "unit": unit,
            "coeffs": coeffs,
            "raw_coeffs": cm.group(0) if cm else None,
            "linear_formula": _compute_linear_formula(coeffs),
            "compu_tab_ref": ref_tab.group(1) if ref_tab else None,
        }

    compu_tabs: Dict[str, dict] = {}
    for kw in ("COMPU_TAB", "COMPU_VTAB", "COMPU_VTAB_RANGE"):
        for blk in _iter_a2l_blocks(txt, kw):
            m = re.match(r'^(\S+)\s+"([^"]*)"\s+(\S+)\s+(\d+)', blk)
            if not m:
                continue
            name, desc, conv_type, count_s = m.groups()
            pairs: List[dict] = []
            tail = blk[m.end():]
            if kw == "COMPU_TAB":
                for pm in re.finditer(r"^\s*([-\deE.+]+)\s+([-\deE.+]+)", tail, re.MULTILINE):
                    pairs.append({"in": pm.group(1), "out": pm.group(2)})
            elif kw == "COMPU_VTAB":
                for pm in re.finditer(r'^\s*([-\deE.+]+)\s+"([^"]*)"', tail, re.MULTILINE):
                    pairs.append({"in": pm.group(1), "out": pm.group(2)})
            else:
                for pm in re.finditer(r'^\s*([-\deE.+]+)\s+([-\deE.+]+)\s+"([^"]*)"', tail, re.MULTILINE):
                    pairs.append({"in_min": pm.group(1), "in_max": pm.group(2), "out": pm.group(3)})
            compu_tabs[name] = {
                "kind": kw,
                "name": name,
                "desc": desc,
                "conversion_type": conv_type,
                "declared_count": int(count_s),
                "entries": pairs,
            }

    record_layouts: Dict[str, dict] = {}
    for blk in _iter_a2l_blocks(txt, "RECORD_LAYOUT"):
        tokens = blk.split()
        if not tokens:
            continue
        name = tokens[0]
        fnc_m = re.search(r"\bFNC_VALUES\s+\d+\s+(\S+)\s+(\S+)", blk)
        ax_x_m = re.search(r"\bAXIS_PTS_X\s+\d+\s+(\S+)\s+(\S+)", blk)
        ax_y_m = re.search(r"\bAXIS_PTS_Y\s+\d+\s+(\S+)\s+(\S+)", blk)
        record_layouts[name] = {
            "name": name,
            "fnc_datatype": fnc_m.group(1) if fnc_m else None,
            "fnc_index_mode": fnc_m.group(2) if fnc_m else None,
            "axis_x_datatype": ax_x_m.group(1) if ax_x_m else None,
            "axis_y_datatype": ax_y_m.group(1) if ax_y_m else None,
            "raw_block": blk,
        }

    functions: Dict[str, dict] = {}
    char_to_functions: Dict[str, List[str]] = defaultdict(list)
    meas_to_functions: Dict[str, List[str]] = defaultdict(list)
    for blk in _iter_a2l_blocks(txt, "FUNCTION"):
        hm = re.match(r'^(\S+)\s+"([^"]*)"', blk)
        if not hm:
            continue
        fn_name, fn_desc = hm.groups()
        _, def_chars = _strip_subblocks(blk, "DEF_CHARACTERISTIC")
        _, ref_chars = _strip_subblocks(blk, "REF_CHARACTERISTIC")
        _, in_meas = _strip_subblocks(blk, "IN_MEASUREMENT")
        _, out_meas = _strip_subblocks(blk, "OUT_MEASUREMENT")
        _, loc_meas = _strip_subblocks(blk, "LOC_MEASUREMENT")
        _, sub_fns = _strip_subblocks(blk, "SUB_FUNCTION")

        def_list = [tok for sb in def_chars for tok in sb.split()]
        ref_list = [tok for sb in ref_chars for tok in sb.split()]
        meas_list = [tok for sb in (in_meas + out_meas + loc_meas) for tok in sb.split()]
        sub_list = [tok for sb in sub_fns for tok in sb.split()]
        for ch in def_list + ref_list:
            if fn_name not in char_to_functions[ch]:
                char_to_functions[ch].append(fn_name)
        for ms in meas_list:
            if fn_name not in meas_to_functions[ms]:
                meas_to_functions[ms].append(fn_name)
        functions[fn_name] = {
            "name": fn_name,
            "desc": fn_desc,
            "def_characteristics": def_list,
            "ref_characteristics": ref_list,
            "measurements": meas_list,
            "sub_functions": sub_list,
        }

    groups: Dict[str, dict] = {}
    char_to_groups: Dict[str, List[str]] = defaultdict(list)
    for blk in _iter_a2l_blocks(txt, "GROUP"):
        hm = re.match(r'^(\S+)\s+"([^"]*)"', blk)
        if not hm:
            continue
        g_name, g_desc = hm.groups()
        _, ref_chars = _strip_subblocks(blk, "REF_CHARACTERISTIC")
        _, ref_meas = _strip_subblocks(blk, "REF_MEASUREMENT")
        _, sub_grps = _strip_subblocks(blk, "SUB_GROUP")
        chars = [tok for sb in ref_chars for tok in sb.split()]
        for ch in chars:
            if g_name not in char_to_groups[ch]:
                char_to_groups[ch].append(g_name)
        groups[g_name] = {
            "name": g_name,
            "desc": g_desc,
            "ref_characteristics": chars,
            "ref_measurements": [tok for sb in ref_meas for tok in sb.split()],
            "sub_groups": [tok for sb in sub_grps for tok in sb.split()],
        }

    symbols: List[dict] = []
    # AXIS_PTS
    for idx, blk in enumerate(_iter_a2l_blocks(txt, "AXIS_PTS")):
        hm = re.match(
            r'^(\S+)\s+"([^"]*)"\s+0x([0-9A-Fa-f]+)\s+(\S+)\s+(\S+)\s+([-\deE.+]+)\s+(\S+)\s+(\d+)\s+([-\deE.+]+)\s+([-\deE.+]+)',
            blk,
        )
        if hm:
            (
                name, desc, addr_hex, input_qty, deposit, max_diff,
                cm_name, max_pts_s, low_s, high_s,
            ) = hm.groups()
            addr = int(addr_hex, 16)
            max_pts = int(max_pts_s)
        else:
            hm2 = re.match(r'^(\S+)\s+"([^"]*)"', blk)
            am = re.search(r"\b0x([0-9A-Fa-f]+)\b", blk)
            if not (hm2 and am):
                continue
            name, desc = hm2.groups()
            addr = int(am.group(1), 16)
            input_qty = deposit = cm_name = low_s = high_s = None
            max_diff = None
            max_pts = None

        cm_info = compu_methods.get(cm_name or "", {})
        rec_info = record_layouts.get(deposit or "", {})
        symbols.append({
            "symbol_id": f"{source_id}:AXIS_PTS:{idx}:{name}",
            "record_kind": "AXIS_PTS",
            "char_type": "AXIS_PTS",
            "name": name,
            "desc": desc,
            "address": addr,
            "address_hex": _address_hex(addr),
            "address_space": "rom_ea",
            "input_quantity": input_qty,
            "record_layout": deposit,
            "datatype_hint": rec_info.get("axis_x_datatype") or rec_info.get("fnc_datatype"),
            "compu_method": cm_name,
            "unit": cm_info.get("unit", ""),
            "linear_formula": cm_info.get("linear_formula"),
            "max_points": max_pts,
            "lower_limit": low_s,
            "upper_limit": high_s,
            "axes": [],
            "functions": sorted(char_to_functions.get(name, [])),
            "groups": sorted(char_to_groups.get(name, [])),
            "source_path": source_path,
            "source_sha256": src_sha,
            "evidence_class": "donor",
            "is_target_proof": False,
        })

    # CHARACTERISTIC (with nested AXIS_DESCR)
    for idx, blk in enumerate(_iter_a2l_blocks(txt, "CHARACTERISTIC")):
        head_txt, ax_blocks = _strip_subblocks(blk, "AXIS_DESCR")
        hm = re.match(
            r'^(\S+)\s+"([^"]*)"\s+(\S+)\s+0x([0-9A-Fa-f]+)\s+(\S+)\s+([-\deE.+]+)\s+(\S+)\s+([-\deE.+]+)\s+([-\deE.+]+)',
            head_txt,
        )
        if hm:
            name, desc, ch_type, addr_hex, deposit, max_diff, cm_name, low_s, high_s = hm.groups()
            addr = int(addr_hex, 16)
        else:
            hm2 = re.match(r'^(\S+)\s+"([^"]*)"', head_txt)
            am = re.search(r"\b0x([0-9A-Fa-f]+)\b", head_txt)
            if not (hm2 and am):
                continue
            name, desc = hm2.groups()
            ch_type = "UNKNOWN"
            addr = int(am.group(1), 16)
            deposit = None
            cm_match = re.search(r"\b(COMP_\S+|NO_COMPU_METHOD)\b", head_txt)
            cm_name = cm_match.group(1) if cm_match else None
            low_s = high_s = None

        num_m = re.search(r"\bNUMBER\s+(\d+)", head_txt)
        parsed_axes = []
        for ax_idx, ablk in enumerate(ax_blocks):
            am = re.match(r"^(\S+)\s+(\S+)\s+(\S+)\s+(\d+)\s+([-\deE.+]+)\s+([-\deE.+]+)", ablk)
            ax_ref_m = re.search(r"\bAXIS_PTS_REF\s+(\S+)", ablk)
            fix_m = re.search(r"\bFIX_AXIS_PAR\s+([-\d]+)\s+([-\d]+)\s+(\d+)", ablk)
            if am:
                ax_attr, ax_qty, ax_cm, ax_pts_s, ax_lo, ax_hi = am.groups()
                parsed_axes.append({
                    "axis_index": ax_idx,
                    "attribute": ax_attr,
                    "input_quantity": ax_qty,
                    "compu_method": ax_cm,
                    "unit": compu_methods.get(ax_cm, {}).get("unit", ""),
                    "linear_formula": compu_methods.get(ax_cm, {}).get("linear_formula"),
                    "max_points": int(ax_pts_s),
                    "lower_limit": ax_lo,
                    "upper_limit": ax_hi,
                    "axis_pts_ref": ax_ref_m.group(1) if ax_ref_m else None,
                    "fix_axis_par": [int(fix_m.group(1)), int(fix_m.group(2)), int(fix_m.group(3))] if fix_m else None,
                })

        cm_info = compu_methods.get(cm_name or "", {})
        rec_info = record_layouts.get(deposit or "", {})
        symbols.append({
            "symbol_id": f"{source_id}:CHARACTERISTIC:{idx}:{name}",
            "record_kind": "CHARACTERISTIC",
            "char_type": ch_type,
            "name": name,
            "desc": desc,
            "address": addr,
            "address_hex": _address_hex(addr),
            "address_space": "rom_ea",
            "record_layout": deposit,
            "datatype_hint": rec_info.get("fnc_datatype"),
            "compu_method": cm_name,
            "unit": cm_info.get("unit", ""),
            "linear_formula": cm_info.get("linear_formula"),
            "compu_tab_ref": cm_info.get("compu_tab_ref"),
            "number": int(num_m.group(1)) if num_m else None,
            "lower_limit": low_s,
            "upper_limit": high_s,
            "axes": parsed_axes,
            "functions": sorted(char_to_functions.get(name, [])),
            "groups": sorted(char_to_groups.get(name, [])),
            "source_path": source_path,
            "source_sha256": src_sha,
            "evidence_class": "donor",
            "is_target_proof": False,
        })

    # MEASUREMENT
    for idx, blk in enumerate(_iter_a2l_blocks(txt, "MEASUREMENT")):
        hm = re.match(r'^(\S+)\s+"([^"]*)"\s+(\S+)\s+(\S+)', blk)
        if not hm:
            continue
        name, desc, dtype, cm_name = hm.groups()
        am = re.search(r"\bECU_ADDRESS\s+0x([0-9A-Fa-f]+)", blk)
        addr = int(am.group(1), 16) if am else None
        cm_info = compu_methods.get(cm_name, {})
        symbols.append({
            "symbol_id": f"{source_id}:MEASUREMENT:{idx}:{name}",
            "record_kind": "MEASUREMENT",
            "char_type": "MEASUREMENT",
            "name": name,
            "desc": desc,
            "address": addr,
            "address_hex": _address_hex(addr) if addr is not None else None,
            "address_space": "ram_ea",
            "record_layout": None,
            "datatype_hint": dtype,
            "compu_method": cm_name,
            "unit": cm_info.get("unit", ""),
            "linear_formula": cm_info.get("linear_formula"),
            "axes": [],
            "functions": sorted(meas_to_functions.get(name, [])),
            "groups": [],
            "source_path": source_path,
            "source_sha256": src_sha,
            "evidence_class": "donor",
            "is_target_proof": False,
        })

    # Retain duplicates by mapping address_hex -> list of indices/names
    dup_by_addr: Dict[str, List[str]] = defaultdict(list)
    for s in symbols:
        if s["address_hex"]:
            dup_by_addr[s["address_hex"]].append(s["symbol_id"])

    return {
        "source_id": source_id,
        "source_path": source_path,
        "source_sha256": src_sha,
        "compu_methods": compu_methods,
        "compu_tabs": compu_tabs,
        "record_layouts": record_layouts,
        "functions": functions,
        "groups": groups,
        "symbols": symbols,
        "duplicate_addresses": {k: v for k, v in sorted(dup_by_addr.items()) if len(v) > 1},
    }


def parse_a2l_relational(path: Path) -> dict:
    p = Path(path)
    return parse_a2l_bytes_relational(p.read_bytes(), source_path=str(p))


def load_wo70017_metadata_tsv(path: Path) -> List[dict]:
    """Load pre-parsed CONTROL/WO70017_DONOR_METADATA.tsv rows cleanly preserving duplicates."""
    p = Path(path)
    if not p.exists():
        return []
    rows: List[dict] = []
    with p.open("r", encoding="utf-8", errors="replace", newline="") as fh:
        for idx, row in enumerate(csv.DictReader(fh, delimiter="\t")):
            addr_s = (row.get("address") or "").strip()
            addr = None
            if addr_s.lower().startswith("0x"):
                try:
                    addr = int(addr_s, 16)
                except ValueError:
                    addr = None
            rows.append({
                "row_index": idx,
                "donor_rom": row.get("donor_rom", ""),
                "source_path": row.get("donor_a2l_or_xml", ""),
                "source_sha256": row.get("source_hash", ""),
                "name": row.get("object_name", ""),
                "record_kind": row.get("object_kind", ""),
                "address": addr,
                "address_hex": _address_hex(addr) if addr is not None else addr_s,
                "storage_type": row.get("storage_type", ""),
                "record_layout": row.get("record_layout", ""),
                "dimensions": row.get("dimensions", ""),
                "byte_extent": row.get("byte_extent", ""),
                "axis_1_ref": row.get("axis_1_ref", ""),
                "axis_1_type": row.get("axis_1_type", ""),
                "axis_1_conversion": row.get("axis_1_conversion", ""),
                "axis_1_units": row.get("axis_1_units", ""),
                "axis_2_ref": row.get("axis_2_ref", ""),
                "axis_2_type": row.get("axis_2_type", ""),
                "axis_2_conversion": row.get("axis_2_conversion", ""),
                "axis_2_units": row.get("axis_2_units", ""),
                "compu_method": row.get("value_conversion", ""),
                "unit": row.get("value_units", ""),
                "raw_formula": row.get("raw_formula", ""),
                "function_group": row.get("function_group", ""),
                "parse_status": row.get("parse_status", ""),
                "unresolved_fields": row.get("unresolved_fields", ""),
                "evidence_class": "donor",
                "is_target_proof": False,
            })
    return rows


# ---------------------------------------------------------------------------
# 2. RomRaider XML Corpus Indexer (.xml, directories, .zip archives)
# ---------------------------------------------------------------------------

def _parse_hex_int(val: Optional[str]) -> Optional[int]:
    if not val:
        return None
    s = val.strip()
    try:
        return int(s, 16) if s.lower().startswith("0x") else int(s, 16)
    except ValueError:
        return None


def _parse_int_opt(val: Optional[str]) -> Optional[int]:
    if not val:
        return None
    try:
        return int(val.strip())
    except ValueError:
        return None


def parse_romraider_xml_bytes(raw: bytes, source_path: str, archive_member: Optional[str] = None) -> dict:
    """Parse one RomRaider XML document without flattening conflicts or failing hard on malformed XML."""
    src_sha = _sha256_bytes(raw)
    doc_id = f"xml:{Path(archive_member or source_path).name}#{src_sha[:12]}"
    try:
        root = ET.parse(io.BytesIO(raw)).getroot()
    except ET.ParseError as exc:
        return {
            "doc_id": doc_id,
            "source_path": source_path,
            "archive_member": archive_member,
            "source_sha256": src_sha,
            "status": "parse_error",
            "error": str(exc),
            "romid": {},
            "scalings": {},
            "tables": [],
        }

    romid: Dict[str, str] = {}
    rid_el = root.find(".//romid")
    if rid_el is not None:
        for ch in rid_el:
            if ch.text is not None:
                romid[ch.tag] = ch.text.strip()

    scalings: Dict[str, dict] = {}
    for sc in root.findall(".//scaling"):
        sname = sc.attrib.get("name")
        if sname and sname not in scalings:
            scalings[sname] = dict(sc.attrib)

    tables: List[dict] = []
    # Index top-level / rom tables; avoid double counting nested X/Y/Static axis tables
    rom_el = root.find(".//rom") or root
    for t_idx, tbl in enumerate(rom_el.findall("./table")):
        sa = tbl.attrib.get("storageaddress")
        addr = _parse_hex_int(sa)
        tp = tbl.attrib.get("type", "")
        child_axes = []
        for ch in tbl.findall("./table"):
            asa = ch.attrib.get("storageaddress")
            child_axes.append({
                "name": ch.attrib.get("name", ""),
                "type": ch.attrib.get("type", ""),
                "storageaddress": _parse_hex_int(asa),
                "storageaddress_raw": asa,
                "storagetype": ch.attrib.get("storagetype", ""),
                "scaling": ch.attrib.get("scaling", ""),
                "sizex": _parse_int_opt(ch.attrib.get("sizex")),
                "sizey": _parse_int_opt(ch.attrib.get("sizey")),
                "static_values": [d.text.strip() for d in ch.findall("./data") if d.text is not None],
            })
        sc_name = tbl.attrib.get("scaling", "")
        sc_meta = scalings.get(sc_name, {})
        tables.append({
            "doc_id": doc_id,
            "table_index": t_idx,
            "name": tbl.attrib.get("name", ""),
            "category": tbl.attrib.get("category", ""),
            "type": tp,
            "storageaddress": addr,
            "storageaddress_raw": sa,
            "storageaddress_hex": _address_hex(addr) if addr is not None else None,
            "storagetype": tbl.attrib.get("storagetype", "") or sc_meta.get("storagetype", ""),
            "endian": tbl.attrib.get("endian", "") or sc_meta.get("endian", ""),
            "sizex": _parse_int_opt(tbl.attrib.get("sizex")) or 1,
            "sizey": _parse_int_opt(tbl.attrib.get("sizey")) or 1,
            "scaling": sc_name,
            "scaling_units": sc_meta.get("units", ""),
            "scaling_expression": sc_meta.get("expression", ""),
            "axes": child_axes,
            "ecuid": romid.get("ecuid", ""),
            "xmlid": romid.get("xmlid", ""),
            "source_path": source_path,
            "archive_member": archive_member,
            "source_sha256": src_sha,
            "evidence_class": "donor",
            "is_target_proof": False,
        })

    return {
        "doc_id": doc_id,
        "source_path": source_path,
        "archive_member": archive_member,
        "source_sha256": src_sha,
        "status": "ok",
        "error": None,
        "romid": romid,
        "scalings": scalings,
        "tables": tables,
    }


def collect_xml_documents(inputs: List[Path]) -> List[dict]:
    """Collect and parse RomRaider XMLs from .xml files, directories, and .zip archives."""
    docs: List[dict] = []
    for raw_p in sorted(inputs, key=lambda x: str(x)):
        p = Path(raw_p)
        if not p.exists():
            continue
        if p.is_dir():
            for child in sorted(p.rglob("*.xml")):
                docs.append(parse_romraider_xml_bytes(child.read_bytes(), source_path=str(child)))
        elif p.suffix.lower() == ".zip":
            with zipfile.ZipFile(p) as zf:
                members = sorted(
                    [m for m in zf.infolist() if not m.is_dir() and m.filename.lower().endswith(".xml")],
                    key=lambda m: m.filename,
                )
                for m in members:
                    docs.append(parse_romraider_xml_bytes(zf.read(m.filename), source_path=str(p), archive_member=m.filename))
        else:
            docs.append(parse_romraider_xml_bytes(p.read_bytes(), source_path=str(p)))
    return docs


# ---------------------------------------------------------------------------
# 3. Metadata-Bounded ROM Signature & Payload Indexing (Code-Twin Fast Path)
# ---------------------------------------------------------------------------

def index_rom_signature(
    rom_path: Path,
    *,
    a2l_source_sha256: Optional[str] = None,
    xml_doc_id: Optional[str] = None,
) -> dict:
    """
    Build a signature & payload hash entry for one donor/reference ROM image.
    Code-region boundary is derived from discovered `infer_layout(rom, helpers)` and
    `parse_nissan_metadata(rom)` — never a single hardcoded universal offset split.
    """
    p = Path(rom_path)
    container_raw = p.read_bytes()
    rom = load_any_rom(p)
    meta = parse_nissan_metadata(rom)
    helpers = discover_helpers(rom)
    calls = extract_calls(rom, helpers)
    code_start, cal_lo, cal_hi = infer_layout(rom, helpers)

    active_end = len(rom)
    while active_end > 0x10000 and rom[active_end - 0x10000 : active_end] == b"\xff" * 0x10000:
        active_end -= 0x10000

    # Derive explicit code window from layout + bootblock state
    if active_end > code_start:
        code_region_hash = _sha256_bytes(rom[code_start:active_end])
        code_end = active_end
    else:
        code_region_hash = None
        code_end = code_start

    # Index non-trivial and trivial resolved table payloads
    payload_entries: List[dict] = []
    seen_tbls = set()
    for c in sorted(calls, key=lambda x: (x["call_pc"], x.get("table") or -1)):
        t = c.get("table")
        if t is None or t in seen_tbls:
            continue
        seen_tbls.add(t)
        w = {"uint8": 1, "int8": 1, "uint16": 2, "int16": 2}.get(c["elem_type"], 0)
        sz = c["dim1"] * c["dim2"] * w
        if w == 0 or sz <= 0 or t + sz > len(rom):
            continue
        blob = rom[t : t + sz]
        payload_entries.append({
            "address": t,
            "address_hex": _address_hex(t),
            "helper": c["helper"],
            "helper_kind": c["kind"],
            "element_type": c["elem_type"],
            "dim1": c["dim1"],
            "dim2": c["dim2"],
            "byte_length": sz,
            "payload_sha256": _sha256_bytes(blob),
            "distinct_byte_values": len(set(blob)),
        })

    return {
        "rom_id": f"rom:{p.name}#{_sha256_bytes(rom)[:12]}",
        "source_path": str(p),
        "container_sha256": _sha256_bytes(container_raw),
        "decoded_rom_sha256": _sha256_bytes(rom),
        "decoded_size_bytes": len(rom),
        "fid": meta.get("fid"),
        "fid_addr": meta.get("fid_addr"),
        "fid_cpu": meta.get("fid_cpu"),
        "loader": meta.get("loader"),
        "bootblock_ff": meta.get("bootblock_ff"),
        "layout": {
            "code_start": code_start,
            "code_end_exclusive": code_end,
            "cal_lo": cal_lo,
            "cal_hi": cal_hi,
            "boundary_method": "infer_layout_plus_active_end_and_nissan_meta",
        },
        "code_region_sha256": code_region_hash,
        "a2l_source_sha256": a2l_source_sha256,
        "xml_doc_id": xml_doc_id,
        "table_count": len(payload_entries),
        "table_payloads": payload_entries,
    }


# ---------------------------------------------------------------------------
# 4. Reference Index Assembly & Cross-Reference Matcher
# ---------------------------------------------------------------------------

def build_reference_index(
    *,
    a2l_paths: Optional[List[Path]] = None,
    xml_inputs: Optional[List[Path]] = None,
    rom_paths: Optional[List[Path]] = None,
    wo70017_tsv: Optional[Path] = None,
) -> dict:
    """Assemble a rebuildable, deterministic JSON reference database preserving conflicts."""
    a2l_records = [parse_a2l_relational(Path(p)) for p in sorted(a2l_paths or [], key=str) if Path(p).exists()]
    xml_docs = collect_xml_documents(list(xml_inputs or []))
    rom_sigs = [index_rom_signature(Path(p)) for p in sorted(rom_paths or [], key=str) if Path(p).exists()]
    wo70017_rows = load_wo70017_metadata_tsv(Path(wo70017_tsv)) if wo70017_tsv else []

    # Fast lookup lookup tables (stored as sorted multi-value lists so conflicts are preserved)
    xml_by_ecuid: Dict[str, List[str]] = defaultdict(list)
    xml_by_addr: Dict[str, List[dict]] = defaultdict(list)
    for doc in xml_docs:
        if doc["status"] != "ok":
            continue
        ecuid = doc["romid"].get("ecuid")
        if ecuid:
            xml_by_ecuid[ecuid].append(doc["doc_id"])
        for tbl in doc["tables"]:
            if tbl["storageaddress_hex"]:
                xml_by_addr[tbl["storageaddress_hex"]].append({
                    "doc_id": doc["doc_id"],
                    "ecuid": tbl["ecuid"],
                    "name": tbl["name"],
                    "type": tbl["type"],
                    "storagetype": tbl["storagetype"],
                    "sizex": tbl["sizex"],
                    "sizey": tbl["sizey"],
                    "scaling": tbl["scaling"],
                    "scaling_units": tbl["scaling_units"],
                    "scaling_expression": tbl["scaling_expression"],
                    "source_path": tbl["source_path"],
                    "archive_member": tbl["archive_member"],
                    "source_sha256": tbl["source_sha256"],
                })

    a2l_by_addr: Dict[str, List[dict]] = defaultdict(list)
    for a2l in a2l_records:
        for sym in a2l["symbols"]:
            if sym["address_hex"]:
                a2l_by_addr[sym["address_hex"]].append(sym)
    for row in wo70017_rows:
        if row["address_hex"]:
            a2l_by_addr[row["address_hex"]].append(row)

    payload_index: Dict[str, List[dict]] = defaultdict(list)
    code_hash_index: Dict[str, List[dict]] = defaultdict(list)
    for rs in rom_sigs:
        if rs["code_region_sha256"]:
            code_hash_index[rs["code_region_sha256"]].append({
                "rom_id": rs["rom_id"],
                "source_path": rs["source_path"],
                "decoded_rom_sha256": rs["decoded_rom_sha256"],
                "fid": rs["fid"],
                "code_start": rs["layout"]["code_start"],
                "code_end_exclusive": rs["layout"]["code_end_exclusive"],
            })
        for tp in rs["table_payloads"]:
            key = f"{tp['payload_sha256']}:{tp['byte_length']}"
            # Enrich with any A2L symbols sharing same ROM address when linked
            payload_index[key].append({
                "rom_id": rs["rom_id"],
                "source_path": rs["source_path"],
                "decoded_rom_sha256": rs["decoded_rom_sha256"],
                "address": tp["address"],
                "address_hex": tp["address_hex"],
                "helper_kind": tp["helper_kind"],
                "element_type": tp["element_type"],
                "dim1": tp["dim1"],
                "dim2": tp["dim2"],
                "byte_length": tp["byte_length"],
                "distinct_byte_values": tp["distinct_byte_values"],
            })

    return {
        "schema": SCHEMA_REF_INDEX_V1,
        "index_schema_version": INDEX_SCHEMA_VERSION,
        "parser_version": PARSER_VERSION,
        "output_schema_version": DATA_MODEL_VERSION,
        "sources": {
            "a2l_files": [
                {"source_id": a["source_id"], "path": a["source_path"], "sha256": a["source_sha256"], "symbol_count": len(a["symbols"])}
                for a in a2l_records
            ],
            "xml_documents": [
                {
                    "doc_id": d["doc_id"],
                    "path": d["source_path"],
                    "archive_member": d["archive_member"],
                    "sha256": d["source_sha256"],
                    "status": d["status"],
                    "ecuid": d["romid"].get("ecuid", ""),
                    "table_count": len(d["tables"]),
                }
                for d in xml_docs
            ],
            "donor_roms": [
                {
                    "rom_id": r["rom_id"],
                    "path": r["source_path"],
                    "container_sha256": r["container_sha256"],
                    "decoded_rom_sha256": r["decoded_rom_sha256"],
                    "fid": r["fid"],
                    "layout": r["layout"],
                    "code_region_sha256": r["code_region_sha256"],
                    "table_count": r["table_count"],
                }
                for r in rom_sigs
            ],
            "wo70017_tsv": {
                "path": str(wo70017_tsv) if wo70017_tsv else None,
                "sha256": _sha256_bytes(Path(wo70017_tsv).read_bytes()) if (wo70017_tsv and Path(wo70017_tsv).exists()) else None,
                "row_count": len(wo70017_rows),
            },
        },
        "a2l": a2l_records,
        "xml": xml_docs,
        "wo70017_rows": wo70017_rows,
        "lookups": {
            "xml_by_ecuid": {k: sorted(v) for k, v in sorted(xml_by_ecuid.items())},
            "xml_by_addr": dict(sorted(xml_by_addr.items())),
            "a2l_by_addr": dict(sorted(a2l_by_addr.items())),
            "payload_index": dict(sorted(payload_index.items())),
            "code_hash_index": dict(sorted(code_hash_index.items())),
        },
    }


def match_target_against_index(
    target_catalogue: dict,
    ref_index: dict,
    *,
    target_rom: Optional[bytes] = None,
) -> dict:
    """
    Cross-reference a Milestone 2 `to_per_address_catalogue()` output against a built
    reference index. Keeps donor matches strictly typed and preserves all conflicts.
    """
    lookups = ref_index.get("lookups", {})
    payload_idx = lookups.get("payload_index", {})
    xml_by_addr = lookups.get("xml_by_addr", {})
    a2l_by_addr = lookups.get("a2l_by_addr", {})
    code_hash_idx = lookups.get("code_hash_index", {})

    manifest = target_catalogue.get("manifest", {})
    layout = manifest.get("layout", {})
    target_ecuid = None
    code_twin_hits: List[dict] = []

    if target_rom is not None:
        meta = parse_nissan_metadata(target_rom)
        target_ecuid = meta.get("fid")
        c_start = layout.get("code_start")
        active_end = len(target_rom)
        while active_end > 0x10000 and target_rom[active_end - 0x10000 : active_end] == b"\xff" * 0x10000:
            active_end -= 0x10000
        if c_start is not None and active_end > c_start:
            c_sha = _sha256_bytes(target_rom[c_start:active_end])
            for hit in code_hash_idx.get(c_sha, []):
                code_twin_hits.append({
                    **hit,
                    "target_code_start": c_start,
                    "target_code_end_exclusive": active_end,
                    "match_basis": "exact_code_region_sha256",
                    "evidence_class": "donor",
                    "is_target_proof": False,
                })

    per_candidate_matches: Dict[str, dict] = {}
    for cand in target_catalogue.get("candidates", []):
        addr_hex = cand["base_hex"]
        xml_hits = [
            {**h, "match_basis": "xml_same_address", "evidence_class": "donor", "is_target_proof": False}
            for h in xml_by_addr.get(addr_hex, [])
        ]
        a2l_same_addr_hits = [
            {**s, "match_basis": "a2l_same_address_unverified", "evidence_class": "donor", "is_target_proof": False}
            for s in a2l_by_addr.get(addr_hex, [])
        ]

        payload_hits: List[dict] = []
        for gv in cand.get("geometry_variants", []):
            psha = gv.get("payload_sha256")
            blen = gv.get("byte_length")
            if psha and blen:
                for pmatch in payload_idx.get(f"{psha}:{blen}", []):
                    payload_hits.append({
                        **pmatch,
                        "nontrivial": (pmatch.get("distinct_byte_values") or 0) > 2,
                        "match_basis": "exact_payload_sha256_and_length",
                        "evidence_class": "donor",
                        "is_target_proof": False,
                    })

        # Explicitly surface any conflicting donor names / geometries rather than picking a winner
        conflicts: List[dict] = []
        distinct_xml_names = sorted({h["name"] for h in xml_hits if h.get("name")})
        if len(distinct_xml_names) > 1:
            conflicts.append({"kind": "xml_name_conflict", "values": distinct_xml_names})
        distinct_xml_dims = sorted({(h["sizex"], h["sizey"], h["storagetype"]) for h in xml_hits})
        if len(distinct_xml_dims) > 1:
            conflicts.append({"kind": "xml_geometry_conflict", "values": [list(x) for x in distinct_xml_dims]})
        distinct_a2l_names = sorted({h.get("name", "") for h in a2l_same_addr_hits if h.get("name")})
        if len(distinct_a2l_names) > 1:
            conflicts.append({"kind": "a2l_same_address_homonym_conflict", "values": distinct_a2l_names})

        per_candidate_matches[addr_hex] = {
            "candidate_id": cand["candidate_id"],
            "address": cand["base"],
            "address_hex": addr_hex,
            "xml_address_hits": xml_hits,
            "a2l_same_address_hits": a2l_same_addr_hits,
            "payload_hits": payload_hits,
            "conflicts": conflicts,
        }

    return {
        "schema": "sh705x-crossref-match-v1",
        "output_schema_version": DATA_MODEL_VERSION,
        "target_rom_sha256": manifest.get("input", {}).get("decoded_rom_sha256"),
        "target_fid": target_ecuid,
        "code_twin_matches": code_twin_hits,
        "candidates": per_candidate_matches,
    }


# ---------------------------------------------------------------------------
# Standalone CLI
# ---------------------------------------------------------------------------

def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="SH705x Milestone 3 standalone relational reference indexer")
    sub = ap.add_subparsers(dest="cmd", required=True)

    pb = sub.add_parser("build", help="Build rebuildable JSON reference index atomically")
    pb.add_argument("--out", required=True, help="Output index JSON path")
    pb.add_argument("--a2l", action="append", default=[], help="A2L donor file path (repeatable)")
    pb.add_argument("--xml", action="append", default=[], help="RomRaider XML file, directory, or .zip (repeatable)")
    pb.add_argument("--rom", action="append", default=[], help="Donor ROM file (.bin/.s19/.hex/.dat/.zip, repeatable)")
    pb.add_argument("--wo70017-tsv", help="Optional CONTROL/WO70017_DONOR_METADATA.tsv path")

    pq = sub.add_parser("query", help="Query a built reference index by --addr or --ecuid")
    pq.add_argument("--index", required=True, help="Built reference index JSON path")
    pq.add_argument("--addr", help="Hex address to query (e.g. 0x09000)")
    pq.add_argument("--ecuid", help="ECUID string to query")

    args = ap.parse_args(argv)
    if args.cmd == "build":
        idx = build_reference_index(
            a2l_paths=[Path(x) for x in args.a2l],
            xml_inputs=[Path(x) for x in args.xml],
            rom_paths=[Path(x) for x in args.rom],
            wo70017_tsv=Path(args.wo70017_tsv) if args.wo70017_tsv else None,
        )
        out_p = Path(args.out)
        atomic_write_json(out_p, idx)
        print(
            f"Built ref index ({len(idx['sources']['a2l_files'])} A2L, "
            f"{len(idx['sources']['xml_documents'])} XMLs, "
            f"{len(idx['sources']['donor_roms'])} ROMs) -> {out_p}"
        )
        return 0

    idx_data = json.loads(Path(args.index).read_text(encoding="utf-8"))
    lookups = idx_data.get("lookups", {})
    result: Dict[str, Any] = {}
    if args.addr:
        norm = _address_hex(_parse_hex_int(args.addr))
        result["address_hex"] = norm
        result["xml_hits"] = lookups.get("xml_by_addr", {}).get(norm, [])
        result["a2l_hits"] = lookups.get("a2l_by_addr", {}).get(norm, [])
    if args.ecuid:
        result["ecuid"] = args.ecuid
        result["xml_doc_ids"] = lookups.get("xml_by_ecuid", {}).get(args.ecuid, [])
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
