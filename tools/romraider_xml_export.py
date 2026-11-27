#!/usr/bin/env python3
"""
Milestone 4 Confidence/Evidence Resolver & Preview-First RomRaider XML Generator
(`tools/romraider_xml_export.py`)

Implements WO70036 (4-dimension confidence resolver) & WO70037 (preview-first XML
generator & structural validator) plus Manager Refinements C and D:
  1. Separates every candidate's confidence into 4 independent dimensions:
       - structural_confidence (bounds, geometry consistency)
       - crossref_confidence   (code twin, XML/A2L, exact donor payload, conflict)
       - runtime_confidence    (helper call-site backing)
       - semantic_confidence   (target_verified vs provisional_donor_lead vs unknown_raw_only)
     plus explicit `export_eligibility`.
  2. Preview-first export bundle (atomically written only after XML build):
       - `<stem>.preview.xml`
       - `<stem>.provenance.json`
       - `<stem>.validation.json`
       - `<stem>.unresolved.json`
  3. Tier D unidentified/raw objects are exported with raw placeholder names and raw identity
     scalings—never silently borrowing donor names, units, or scaling expressions.
  4. Implicit fixed-grid axes (`2D_IMPL`/`3D_IMPL`) emit `Static Y Axis` labeled as
     computed stub grids (never represented as proven physical runtime axes).
  5. Protected baseline guard refuses in-place writes into `CALIBRATIONS/`.
"""
import argparse
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from nissan_sh705x_workbench import load_any_rom, parse_nissan_metadata  # noqa: E402
from romraider_ref_index import match_target_against_index  # noqa: E402
from sh7058_cross_rom_scanner import (  # noqa: E402
    _address_hex,
    build_scan_export,
    discover_helpers,
    extract_calls,
)
from sh705x_discovery_v2 import (  # noqa: E402
    DATA_MODEL_VERSION,
    atomic_write_json,
    atomic_write_text,
    extract_implicit_grids,
    to_per_address_catalogue,
)

SCHEMA_RESOLUTION_V1 = "sh705x-evidence-resolution-v1"
SCHEMA_VALIDATION_V1 = "sh705x-xml-validation-v1"
SCHEMA_UNRESOLVED_V1 = "sh705x-unresolved-report-v1"

RAW_SCALINGS = {
    "uint8": {"name": "Raw_UBYTE", "units": "raw", "expression": "x", "to_byte": "x", "format": "0", "fineincrement": "1", "coarseincrement": "5", "storagetype": "uint8", "endian": "big"},
    "int8": {"name": "Raw_SBYTE", "units": "raw signed", "expression": "x", "to_byte": "x", "format": "0", "fineincrement": "1", "coarseincrement": "5", "storagetype": "int8", "endian": "big"},
    "uint16": {"name": "Raw_UWORD", "units": "raw", "expression": "x", "to_byte": "x", "format": "0", "fineincrement": "1", "coarseincrement": "5", "storagetype": "uint16", "endian": "big"},
    "int16": {"name": "Raw_SWORD", "units": "raw signed", "expression": "x", "to_byte": "x", "format": "0", "fineincrement": "1", "coarseincrement": "5", "storagetype": "int16", "endian": "big"},
}


# ---------------------------------------------------------------------------
# 1. Four-Dimension Confidence & Export-Eligibility Resolver (WO70036)
# ---------------------------------------------------------------------------

def resolve_candidate_evidence(
    catalogue: dict,
    crossref_matches: Optional[dict] = None,
    *,
    implicit_grids: Optional[Dict[str, dict]] = None,
    target_verified_semantics: Optional[Dict[str, dict]] = None,
) -> dict:
    """
    Resolve per-candidate confidence cleanly across four independent dimensions.
    Donor hits alone NEVER promote `semantic_confidence` to `target_verified`.
    """
    xref_cands = (crossref_matches or {}).get("candidates", {})
    code_twins = (crossref_matches or {}).get("code_twin_matches", [])
    has_code_twin = bool(code_twins)
    verified_map = {k.upper(): v for k, v in (target_verified_semantics or {}).items()}
    impl_grids = implicit_grids or catalogue.get("implicit_grids") or {}

    # Build quick lookup from axis_id -> axis metadata and detect shared-axis usage
    axes_by_id = {ax["axis_id"]: ax for ax in catalogue.get("axes", [])}
    resolved_rows: List[dict] = []

    for cand in sorted(catalogue.get("candidates", []), key=lambda c: c["base"]):
        addr_hex = cand["base_hex"]
        addr_key = addr_hex.upper()
        variants = cand.get("geometry_variants", [])
        geom_conflict = bool(cand.get("geometry_conflict"))
        ax_conflict = bool(cand.get("axis1_conflict") or cand.get("axis2_conflict"))
        in_bounds_variants = [v for v in variants if v.get("in_bounds")]

        # 1) Structural confidence
        if not variants:
            structural_conf = "unknown_geometry"
        elif geom_conflict:
            structural_conf = "conflicting_geometry"
        elif not in_bounds_variants:
            structural_conf = "out_of_bounds"
        elif ax_conflict:
            structural_conf = "conflicting_axes"
        else:
            structural_conf = "verified_in_bounds"

        # 2) Runtime confidence (call-site backing)
        n_calls = len(cand.get("call_pcs", []))
        if n_calls >= 2:
            runtime_conf = "multi_call_backed"
        elif n_calls == 1:
            runtime_conf = "helper_call_backed"
        else:
            runtime_conf = "literal_only"

        # 3) Cross-reference confidence (donor / twin matching only)
        xh = xref_cands.get(addr_hex, {})
        xml_hits = xh.get("xml_address_hits", [])
        a2l_hits = xh.get("a2l_same_address_hits", [])
        pay_hits = xh.get("payload_hits", [])
        x_conflicts = xh.get("conflicts", [])
        nontriv_pay = [p for p in pay_hits if p.get("nontrivial")]

        if x_conflicts:
            crossref_conf = "donor_conflict"
        elif has_code_twin and (xml_hits or pay_hits):
            crossref_conf = "exact_code_twin_with_refs"
        elif has_code_twin:
            crossref_conf = "exact_code_twin"
        elif nontriv_pay and (xml_hits or a2l_hits):
            crossref_conf = "donor_payload_and_symbol"
        elif nontriv_pay:
            crossref_conf = "exact_payload_donor"
        elif xml_hits or a2l_hits:
            crossref_conf = "single_source_donor"
        else:
            crossref_conf = "none"

        # 4) Semantic confidence (STRICT barrier: donor hits never equal target verification)
        verified_entry = verified_map.get(addr_key)
        donor_names = sorted({h.get("name") for h in xml_hits + a2l_hits if h.get("name")})
        if verified_entry is not None:
            semantic_conf = "target_verified"
        elif donor_names or nontriv_pay:
            semantic_conf = "provisional_donor_lead"
        else:
            semantic_conf = "unknown_raw_only"

        # Export eligibility
        if structural_conf in ("unknown_geometry", "out_of_bounds"):
            export_elig = "excluded_invalid_span"
        elif structural_conf in ("conflicting_geometry", "conflicting_axes"):
            export_elig = "hold_for_conflict"
        elif semantic_conf == "target_verified":
            export_elig = "eligible_verified"
        elif crossref_conf == "donor_conflict":
            export_elig = "eligible_raw_with_conflict_note"
        elif semantic_conf == "provisional_donor_lead":
            export_elig = "eligible_raw_or_provisional"
        else:
            export_elig = "eligible_raw_only"

        # Determine primary variant (only unambiguous when not geom_conflict)
        primary_var = variants[0] if len(variants) == 1 else (in_bounds_variants[0] if in_bounds_variants else (variants[0] if variants else None))

        # Resolve axis provenance (explicit ROM axis vs computed implicit stub grid)
        axis_descriptors = []
        for link in cand.get("axis_links", []):
            ax_obj = axes_by_id.get(link["axis_id"])
            if ax_obj:
                axis_descriptors.append({
                    "role": link["role"],
                    "axis_origin": "explicit_rom_axis",
                    "axis_id": ax_obj["axis_id"],
                    "address": ax_obj["address"],
                    "address_hex": ax_obj["address_hex"],
                    "axis_type": ax_obj["axis_type"],
                    "count": ax_obj["count"],
                    "shared_consumers": ax_obj["shared_count"],
                    "orientation_proven": False,
                })
        # Check implicit stub grids via associated helper addresses
        if not axis_descriptors and primary_var and primary_var.get("helper_kind", "").endswith("_IMPL"):
            for h_addr in cand.get("helper_addresses", []):
                h_hex = _address_hex(h_addr)
                ginfo = impl_grids.get(h_hex) or impl_grids.get(h_addr)
                if ginfo:
                    for role_key, label in (("axis1_grid", "axis1"), ("axis2_grid", "axis2")):
                        g = ginfo.get(role_key)
                        if g:
                            axis_descriptors.append({
                                "role": label,
                                "axis_origin": g["axis_source"],
                                "query_domain": g["query_domain"],
                                "axis_start": g["axis_start"],
                                "axis_step": g["axis_step"],
                                "count": g["axis_count"],
                                "grid_max_raw": g["grid_max_raw"],
                                "step_verified_from_clamp": g["step_verified_from_clamp"],
                                "orientation_proven": False,
                            })
                    break

        resolved_rows.append({
            "candidate_id": cand["candidate_id"],
            "address": cand["base"],
            "address_hex": addr_hex,
            "address_space": cand["address_space"],
            "structural_confidence": structural_conf,
            "crossref_confidence": crossref_conf,
            "runtime_confidence": runtime_conf,
            "semantic_confidence": semantic_conf,
            "export_eligibility": export_elig,
            "primary_geometry": primary_var,
            "all_geometry_variants": variants,
            "axes": axis_descriptors,
            "call_pcs": cand.get("call_pcs", []),
            "target_verified": verified_entry,
            "donor_leads": {
                "xml_hits": xml_hits,
                "a2l_hits": a2l_hits,
                "payload_hits": pay_hits,
                "conflicts": x_conflicts,
            },
        })

    return {
        "schema": SCHEMA_RESOLUTION_V1,
        "output_schema_version": DATA_MODEL_VERSION,
        "target_rom_sha256": catalogue.get("manifest", {}).get("input", {}).get("decoded_rom_sha256"),
        "code_twin_matches": code_twins,
        "resolved_candidates": resolved_rows,
    }


# ---------------------------------------------------------------------------
# 2. Preview-First RomRaider XML Emitter & Validator (WO70037)
# ---------------------------------------------------------------------------

def _indent_xml(elem: ET.Element, level: int = 0) -> None:
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        for child in elem:
            _indent_xml(child, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


def _table_type_for_helper_kind(kind: str, dim1: int, dim2: int) -> str:
    if kind.startswith("3D") or (dim1 > 1 and dim2 > 1):
        return "3D"
    return "2D"


def generate_romraider_preview(
    catalogue: dict,
    resolution: dict,
    *,
    rom_bytes: Optional[bytes] = None,
    romid_override: Optional[dict] = None,
    allow_provisional_donor_names: bool = False,
    skip_trivial: bool = False,
) -> Tuple[str, dict, dict, dict]:
    """
    Generate the 4 preview artifacts in memory:
      1. `xml_text` (RomRaider XML preview string)
      2. `provenance_report`
      3. `validation_report`
      4. `unresolved_report`
    """
    manifest = catalogue.get("manifest", {})
    inp = manifest.get("input", {})
    decoded_sha = inp.get("decoded_rom_sha256")
    decoded_size = inp.get("decoded_rom_size_bytes") or (len(rom_bytes) if rom_bytes is not None else 0)
    meta = parse_nissan_metadata(rom_bytes) if rom_bytes is not None else {}

    ecuid = (romid_override or {}).get("ecuid") or meta.get("fid") or "UNKNOWN_ECU"
    memmodel = (romid_override or {}).get("memmodel") or meta.get("fid_cpu") or manifest.get("processor_profile") or "SH7058"
    xmlid = (romid_override or {}).get("xmlid") or f"PREVIEW_{ecuid}_{(decoded_sha or '00000000')[:8]}"

    root = ET.Element("roms")
    rom_el = ET.SubElement(root, "rom")
    romid_el = ET.SubElement(rom_el, "romid")
    romid_fields = {
        "xmlid": xmlid,
        "internalidaddress": (romid_override or {}).get("internalidaddress") or (_address_hex(meta["fid_addr"]) if meta.get("fid_addr") else "0x00000"),
        "internalidstring": (romid_override or {}).get("internalidstring") or ecuid,
        "ecuid": ecuid,
        "make": (romid_override or {}).get("make") or "Nissan",
        "model": (romid_override or {}).get("model") or "SH705x_Target",
        "memmodel": memmodel,
        "endian": "Big",
        "filesize": f"{decoded_size // 1024}kb" if decoded_size else "0kb",
    }
    for k, v in romid_fields.items():
        child = ET.SubElement(romid_el, k)
        child.text = str(v)

    rom_el.append(ET.Comment(
        f" PREVIEW-ONLY GENERATED DEFINITION ({DATA_MODEL_VERSION}) | "
        f"decoded_sha256={decoded_sha} | NOT A VERIFIED RELEASE BASELINE "
    ))

    # Declare standard raw identity scalings up front
    declared_scalings: Dict[str, dict] = {}
    for sspec in RAW_SCALINGS.values():
        declared_scalings[sspec["name"]] = dict(sspec)
        ET.SubElement(rom_el, "scaling", sspec)

    # Track optional target-verified custom scalings
    used_names: Dict[str, int] = defaultdict(int)
    emitted_records: List[dict] = []
    unresolved_objects: List[dict] = []

    for entry in resolution.get("resolved_candidates", []):
        addr_hex = entry["address_hex"]
        elig = entry["export_eligibility"]
        geom = entry.get("primary_geometry")

        if elig in ("excluded_invalid_span", "hold_for_conflict") or geom is None:
            unresolved_objects.append({
                "reason": elig,
                "address": entry["address"],
                "address_hex": addr_hex,
                "structural_confidence": entry["structural_confidence"],
                "crossref_confidence": entry["crossref_confidence"],
                "runtime_confidence": entry["runtime_confidence"],
                "semantic_confidence": entry["semantic_confidence"],
                "geometry_variants": entry["all_geometry_variants"],
                "donor_conflicts": entry["donor_leads"].get("conflicts", []),
            })
            continue

        distinct_vals = geom.get("distinct_byte_values")
        if skip_trivial and distinct_vals is not None and distinct_vals <= 2:
            unresolved_objects.append({
                "reason": "skipped_trivial_constant_payload",
                "address": entry["address"],
                "address_hex": addr_hex,
                "distinct_byte_values": distinct_vals,
            })
            continue

        etype = geom.get("element_type", "uint16")
        raw_sc = RAW_SCALINGS.get(etype, RAW_SCALINGS["uint16"])
        scaling_name = raw_sc["name"]

        # Strict naming & scaling gate:
        # Target-verified objects may use verified name & verified scaling.
        # Tier D / unknown objects strictly use raw names & Raw_* scaling.
        # Even if allow_provisional_donor_names=True, donor hypotheses use [PROVISIONAL] tag and STILL keep Raw_* scaling!
        v_sem = entry.get("target_verified")
        name_source = "raw_placeholder"
        if v_sem is not None:
            base_name = v_sem.get("name") or f"VERIFIED_{addr_hex}"
            category = v_sem.get("category") or "Verified Target Tables"
            name_source = "target_verified"
            custom_sc = v_sem.get("scaling")
            if isinstance(custom_sc, dict) and custom_sc.get("name"):
                scaling_name = custom_sc["name"]
                if scaling_name not in declared_scalings:
                    declared_scalings[scaling_name] = dict(custom_sc)
                    ET.SubElement(rom_el, "scaling", {k: str(v) for k, v in custom_sc.items()})
        elif allow_provisional_donor_names and entry["semantic_confidence"] == "provisional_donor_lead":
            xh = entry["donor_leads"]
            cand_names = [h["name"] for h in xh.get("xml_hits", []) if h.get("name")] + [
                h.get("name") for h in xh.get("a2l_hits", []) if h.get("name")
            ]
            if cand_names and not xh.get("conflicts"):
                base_name = f"{cand_names[0]} [PROVISIONAL {addr_hex}]"
                category = "Provisional Donor Leads (Unverified Scaling)"
                name_source = "provisional_donor_name_with_raw_scaling"
            else:
                base_name = f"RAW_{addr_hex}_{geom.get('helper_kind', 'TBL')}_{etype}_{geom.get('dim1')}x{geom.get('dim2')}"
                category = "Raw Discovered Tables (Conflicting Donor Leads)" if xh.get("conflicts") else "Raw Discovered Tables"
        else:
            base_name = f"RAW_{addr_hex}_{geom.get('helper_kind', 'TBL')}_{etype}_{geom.get('dim1')}x{geom.get('dim2')}"
            category = "Raw Discovered Tables"

        # Flag shared-axis linkage clearly on category
        if any((ax.get("shared_consumers") or 0) > 1 for ax in entry.get("axes", [])):
            base_name = f"{base_name} [SHARED_AXIS]"

        used_names[base_name] += 1
        final_name = base_name if used_names[base_name] == 1 else f"{base_name} #{used_names[base_name]}"

        dim1 = int(geom.get("dim1") or 1)
        dim2 = int(geom.get("dim2") or 1)
        t_type = _table_type_for_helper_kind(geom.get("helper_kind", ""), dim1, dim2)

        t_attrs = {
            "name": final_name,
            "category": category,
            "type": t_type,
            "scaling": scaling_name,
            "storageaddress": addr_hex,
            "storagetype": etype if etype in RAW_SCALINGS else "uint16",
            "endian": "big",
        }
        if t_type == "3D":
            t_attrs["sizex"] = str(dim1)
            t_attrs["sizey"] = str(dim2)
        else:
            t_attrs["sizey"] = str(dim1 * dim2)

        tbl_el = ET.SubElement(rom_el, "table", t_attrs)

        # Emit axis children cleanly preserving explicit vs computed implicit-grid distinction
        for ax in entry.get("axes", []):
            if ax.get("axis_origin") == "explicit_rom_axis":
                ax_etype = ax.get("axis_type") if ax.get("axis_type") in RAW_SCALINGS else "uint8"
                ax_sc = RAW_SCALINGS[ax_etype]["name"]
                ax_role_tag = "X Axis" if (t_type == "3D" and ax["role"] == "axis1") else "Y Axis"
                ET.SubElement(tbl_el, "table", {
                    "name": f"AXIS_{ax['address_hex']}",
                    "type": ax_role_tag,
                    "scaling": ax_sc,
                    "storageaddress": ax["address_hex"],
                    "storagetype": ax_etype,
                    "endian": "big",
                    "sizey" if ax_role_tag == "Y Axis" else "sizex": str(ax.get("count") or 1),
                })
            elif ax.get("axis_origin") == "computed_implicit_grid_stub":
                cnt = int(ax.get("count") or 1)
                step = ax.get("axis_step") or 1
                start = int(ax.get("axis_start") or 0)
                st_type = "Static X Axis" if (t_type == "3D" and ax["role"] == "axis1") else "Static Y Axis"
                ax_el = ET.SubElement(tbl_el, "table", {
                    "name": f"Implicit Grid (computed stub, orientation unverified)",
                    "type": st_type,
                    "scaling": "Raw_UWORD",
                    "storagetype": "uint16",
                    "endian": "big",
                    "sizey" if st_type == "Static Y Axis" else "sizex": str(cnt),
                })
                for idx in range(cnt):
                    d_el = ET.SubElement(ax_el, "data")
                    d_el.text = str(start + idx * step)

        emitted_records.append({
            "xml_name": final_name,
            "address": entry["address"],
            "address_hex": addr_hex,
            "byte_length": geom.get("byte_length"),
            "end_exclusive": geom.get("end_exclusive"),
            "name_source": name_source,
            "scaling": scaling_name,
            "structural_confidence": entry["structural_confidence"],
            "crossref_confidence": entry["crossref_confidence"],
            "runtime_confidence": entry["runtime_confidence"],
            "semantic_confidence": entry["semantic_confidence"],
            "export_eligibility": elig,
            "axes_origin": [ax.get("axis_origin") for ax in entry.get("axes", [])],
        })

    # Include unresolved call observations & scalar candidates in the unresolved report
    for obs in catalogue.get("observations", []):
        if obs.get("base") is None:
            unresolved_objects.append({
                "reason": obs.get("resolution_status") or "unresolved_call_base",
                "call_pc": obs.get("call_pc"),
                "call_pc_hex": obs.get("call_pc_hex"),
                "helper_hex": obs.get("helper_hex"),
                "helper_kind": obs.get("helper_kind"),
            })

    _indent_xml(root)
    xml_text = '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="unicode") + "\n"

    provenance_report = {
        "schema": SCHEMA_RESOLUTION_V1,
        "output_schema_version": DATA_MODEL_VERSION,
        "target_rom_sha256": decoded_sha,
        "ecuid": ecuid,
        "xmlid": xmlid,
        "preview_only": True,
        "emitted_tables": emitted_records,
        "code_twin_matches": resolution.get("code_twin_matches", []),
    }
    unresolved_report = {
        "schema": SCHEMA_UNRESOLVED_V1,
        "output_schema_version": DATA_MODEL_VERSION,
        "target_rom_sha256": decoded_sha,
        "unresolved_count": len(unresolved_objects),
        "unresolved_items": unresolved_objects,
        "unpromoted_scalar_candidates": catalogue.get("scalar_candidates", []),
    }
    validation_report = validate_romraider_xml(
        xml_text,
        rom_size=decoded_size or None,
        emitted_records=emitted_records,
    )
    return xml_text, provenance_report, validation_report, unresolved_report


def validate_romraider_xml(
    xml_text: str,
    *,
    rom_size: Optional[int] = None,
    emitted_records: Optional[List[dict]] = None,
) -> dict:
    """Validate structure, scaling references, unique names, bounds, and byte overlaps."""
    errors: List[dict] = []
    warnings: List[dict] = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        return {
            "schema": SCHEMA_VALIDATION_V1,
            "valid": False,
            "errors": [{"code": "xml_parse_error", "message": str(exc)}],
            "warnings": [],
            "summary": {"table_count": 0},
        }

    rom_el = root.find(".//rom")
    if rom_el is None:
        errors.append({"code": "missing_rom_element", "message": "Missing <rom> root element"})
        return {"schema": SCHEMA_VALIDATION_V1, "valid": False, "errors": errors, "warnings": warnings, "summary": {"table_count": 0}}

    romid = rom_el.find("./romid")
    if romid is None or romid.findtext("./ecuid") is None:
        errors.append({"code": "missing_romid_ecuid", "message": "Missing <romid>/<ecuid>"})

    declared_scalings = {s.attrib.get("name") for s in rom_el.findall("./scaling") if s.attrib.get("name")}
    seen_names: Dict[str, int] = defaultdict(int)
    spans: List[Tuple[int, int, str]] = []
    top_tables = rom_el.findall("./table")

    for tbl in top_tables:
        tname = tbl.attrib.get("name", "")
        seen_names[tname] += 1
        sc_ref = tbl.attrib.get("scaling", "")
        if sc_ref and sc_ref not in declared_scalings:
            errors.append({"code": "missing_scaling_ref", "table": tname, "scaling": sc_ref})

        sa_s = tbl.attrib.get("storageaddress", "")
        st = tbl.attrib.get("storagetype", "uint16")
        width = {"uint8": 1, "int8": 1, "uint16": 2, "int16": 2}.get(st, 0)
        try:
            sa = int(sa_s, 16)
        except ValueError:
            errors.append({"code": "invalid_storageaddress", "table": tname, "storageaddress": sa_s})
            continue
        sx = int(tbl.attrib.get("sizex", "1") or "1")
        sy = int(tbl.attrib.get("sizey", "1") or "1")
        if width <= 0 or sx <= 0 or sy <= 0:
            errors.append({"code": "invalid_table_geometry", "table": tname, "storagetype": st, "sizex": sx, "sizey": sy})
            continue
        end_ex = sa + sx * sy * width
        if rom_size is not None and end_ex > rom_size:
            errors.append({"code": "out_of_rom_bounds", "table": tname, "storageaddress": sa_s, "end_exclusive": end_ex, "rom_size": rom_size})
        spans.append((sa, end_ex, tname))

        for ch in tbl.findall("./table"):
            csc = ch.attrib.get("scaling", "")
            if csc and csc not in declared_scalings:
                errors.append({"code": "missing_axis_scaling_ref", "table": tname, "axis": ch.attrib.get("name", ""), "scaling": csc})

    for tname, cnt in sorted(seen_names.items()):
        if cnt > 1:
            errors.append({"code": "duplicate_table_name", "table": tname, "count": cnt})

    # Detect overlapping table extents
    spans_sorted = sorted(spans, key=lambda x: (x[0], x[1]))
    for idx in range(len(spans_sorted) - 1):
        s1, e1, n1 = spans_sorted[idx]
        s2, e2, n2 = spans_sorted[idx + 1]
        if s2 < e1:
            warnings.append({"code": "overlapping_table_extents", "table_a": n1, "span_a": [s1, e1], "table_b": n2, "span_b": [s2, e2]})

    raw_count = sum(1 for r in (emitted_records or []) if r.get("semantic_confidence") == "unknown_raw_only")
    prov_count = sum(1 for r in (emitted_records or []) if r.get("semantic_confidence") == "provisional_donor_lead")
    ver_count = sum(1 for r in (emitted_records or []) if r.get("semantic_confidence") == "target_verified")

    return {
        "schema": SCHEMA_VALIDATION_V1,
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "summary": {
            "table_count": len(top_tables),
            "declared_scaling_count": len(declared_scalings),
            "overlap_warning_count": len(warnings),
            "target_verified_count": ver_count,
            "provisional_donor_lead_count": prov_count,
            "unknown_raw_only_count": raw_count,
        },
    }


def _assert_safe_output_dir(out_dir: Path) -> None:
    resolved_parts = [p.upper() for p in Path(out_dir).resolve().parts]
    if "CALIBRATIONS" in resolved_parts:
        raise ValueError(f"Refusing to write preview exports into protected CALIBRATIONS directory: {out_dir}")


def write_preview_bundle(
    out_dir: Path,
    stem: str,
    catalogue: dict,
    resolution: dict,
    *,
    rom_bytes: Optional[bytes] = None,
    allow_provisional_donor_names: bool = False,
    skip_trivial: bool = False,
    strict: bool = True,
) -> dict:
    """Build and validate in memory, then atomically write all 4 preview artifacts."""
    out_p = Path(out_dir)
    _assert_safe_output_dir(out_p)
    xml_text, prov, val, unres = generate_romraider_preview(
        catalogue,
        resolution,
        rom_bytes=rom_bytes,
        allow_provisional_donor_names=allow_provisional_donor_names,
        skip_trivial=skip_trivial,
    )
    if strict and not val["valid"]:
        raise ValueError(f"Preview XML failed strict validation: {val['errors']}")

    xml_path = out_p / f"{stem}.preview.xml"
    prov_path = out_p / f"{stem}.provenance.json"
    val_path = out_p / f"{stem}.validation.json"
    unres_path = out_p / f"{stem}.unresolved.json"

    atomic_write_text(xml_path, xml_text)
    atomic_write_json(prov_path, prov)
    atomic_write_json(val_path, val)
    atomic_write_json(unres_path, unres)
    return {
        "xml_path": str(xml_path),
        "provenance_path": str(prov_path),
        "validation_path": str(val_path),
        "unresolved_path": str(unres_path),
        "validation": val,
    }


# ---------------------------------------------------------------------------
# Standalone CLI
# ---------------------------------------------------------------------------

def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="SH705x Milestone 4 resolver & preview-first RomRaider XML exporter")
    ap.add_argument("--catalogue", help="Milestone 2 per-address catalogue JSON path")
    ap.add_argument("--rom", help="Optional target ROM (.bin/.zip/.s19/.hex/.dat) to scan directly or enrich <romid>")
    ap.add_argument("--ref-index", help="Optional Milestone 3 reference index JSON path")
    ap.add_argument("--out-dir", required=True, help="Output directory (never CALIBRATIONS/)")
    ap.add_argument("--stem", required=True, help="Filename stem for preview bundle")
    ap.add_argument("--allow-provisional-donor-names", action="store_true", help="Include [PROVISIONAL] donor table names (still keeps Raw scaling)")
    ap.add_argument("--skip-trivial", action="store_true", help="Move <=2-distinct-byte constant blobs to unresolved report")
    ap.add_argument("--no-strict", action="store_true", help="Write preview bundle even if validation reports errors")
    args = ap.parse_args(argv)

    if not args.catalogue and not args.rom:
        ap.error("Supply at least one of --catalogue or --rom")

    rom_bytes = load_any_rom(Path(args.rom)) if args.rom else None
    if args.catalogue:
        catalogue = json.loads(Path(args.catalogue).read_text(encoding="utf-8"))
    else:
        assert rom_bytes is not None
        helpers = discover_helpers(rom_bytes)
        calls = extract_calls(rom_bytes, helpers)
        scan_doc = build_scan_export(args.rom, rom_bytes, helpers, calls)
        catalogue = to_per_address_catalogue(scan_doc)
        catalogue["implicit_grids"] = {f"0x{k:05X}": v for k, v in extract_implicit_grids(rom_bytes, helpers).items()}

    crossref = None
    if args.ref_index:
        ref_idx = json.loads(Path(args.ref_index).read_text(encoding="utf-8"))
        crossref = match_target_against_index(catalogue, ref_idx, target_rom=rom_bytes)

    resolution = resolve_candidate_evidence(catalogue, crossref)
    result = write_preview_bundle(
        Path(args.out_dir),
        args.stem,
        catalogue,
        resolution,
        rom_bytes=rom_bytes,
        allow_provisional_donor_names=args.allow_provisional_donor_names,
        skip_trivial=args.skip_trivial,
        strict=not args.no_strict,
    )
    print(
        f"Exported preview XML ({result['validation']['summary']['table_count']} tables, "
        f"valid={result['validation']['valid']}) -> {result['xml_path']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
