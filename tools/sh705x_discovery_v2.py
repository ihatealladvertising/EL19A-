#!/usr/bin/env python3
"""
Milestone 2 Standalone Discovery & Lossless Catalogue Providers (`tools/sh705x_discovery_v2.py`)

Additive, read-only modules complying with CONTROL/WO70021, CONTROL/WO70023,
and Milestone 2 constraints:
  1. `to_per_address_catalogue(scan_document)` + `build_run_manifest(...)`:
     Lossless thin adapter over `sh7058_cross_rom_scanner.build_scan_export()`.
     Preserves all calls, unresolved rows, geometry/axis conflicts, overlapping spans,
     first-class shared axes, explicit address domains, and separated donor leads.
  2. `extract_implicit_grids(rom, helpers)`:
     Derives implicit fixed-grid `(start, step, count, max_raw)` metadata for
     `2D_IMPL` and `3D_IMPL` lookup stubs without claiming axis orientation proof.
  3. `extract_calls_enhanced(rom, helpers, ...)`:
     Opt-in enhanced caller analysis with configurable wider register window
     (default 128B vs baseline 56B) and comparison helper against baseline `extract_calls()`.
     Leaves baseline `extract_calls()` completely untouched.
  4. `discover_cal_scalars(rom, ...)`:
     Separate scalar / 1D-array provider scanning `mov.l`/`mov.w` literal pool loads
     into the inferred calibration band outside discovered helper tables and axes.
"""
import argparse
import hashlib
import json
import os
import struct
import sys
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from nissan_sh705x_workbench import load_any_rom  # noqa: E402
from sh7058_cross_rom_scanner import (  # noqa: E402
    HelperSpec,
    _address_hex,
    _export_span,
    build_scan_export,
    discover_helpers,
    extract_calls,
    infer_layout,
    resolve_pc_pool,
    s8,
    u16,
    u32,
)

SCHEMA_CATALOGUE_V1 = "sh705x-per-address-catalogue-v1"
DATA_MODEL_VERSION = "sh705x-datamodel-v1.0.0"
VALID_ADDRESS_SPACES = ("file_offset", "rom_ea", "ram_ea")


# ---------------------------------------------------------------------------
# Atomic File Output Helpers
# ---------------------------------------------------------------------------

def atomic_write_text(dest: Path, text: str, encoding: str = "utf-8") -> Path:
    """Write text to a sibling temporary file, fsync, and atomically rename."""
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{dest.name}.", suffix=".tmp", dir=str(dest.parent))
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding=encoding, newline="\n") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_path, dest)
    except Exception:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        raise
    return dest


def atomic_write_json(dest: Path, obj: Any) -> Path:
    """Serialize deterministic sorted JSON and atomically replace destination."""
    payload = json.dumps(obj, indent=2, sort_keys=True) + "\n"
    return atomic_write_text(dest, payload)


# ---------------------------------------------------------------------------
# 1. Lossless Scanner-to-Catalogue Adapter & Run Manifest (WO70021 / WO70023)
# ---------------------------------------------------------------------------

def _make_artifact_id(input_block: dict) -> str:
    base = Path(input_block.get("path") or "unknown.bin").name.replace(" ", "_")
    sha = input_block.get("decoded_rom_sha256") or "unknown"
    return f"rom:{base}#{sha[:16]}"


def _normalize_optional_index_state(optional_indices: Optional[Dict[str, Optional[dict]]]) -> Dict[str, dict]:
    if optional_indices is None:
        return {}
    normalized: Dict[str, dict] = {}
    for name, state in sorted(optional_indices.items()):
        if not state or state.get("status") in (None, "unavailable", "missing", "stale"):
            normalized[name] = {
                "status": "unavailable",
                "reason": (state or {}).get("reason", "optional_index_not_supplied_or_stale"),
                "expected_hash": (state or {}).get("expected_hash"),
                "observed_hash": (state or {}).get("observed_hash"),
            }
        else:
            normalized[name] = dict(state)
    return normalized


def to_per_address_catalogue(
    scan_document: dict,
    *,
    address_space: str = "rom_ea",
    processor_profile: str = "SH7058",
    donor_leads: Optional[List[dict]] = None,
    optional_indices: Optional[Dict[str, Optional[dict]]] = None,
) -> dict:
    """
    Transform `sh7058_cross_rom_scanner.build_scan_export()` output into a lossless,
    deterministic per-address calibration candidate catalogue per WO70023 & WO70021.

    - Never collapses geometry conflicts or drops unresolved calls.
    - Lifts shared axes into deduplicated first-class `axes[]` objects.
    - Preserves overlapping non-identical spans separately.
    - Keeps `address_space` explicit (`file_offset` | `rom_ea` | `ram_ea`).
    - Strictly segregates donor leads from target facts.
    """
    if address_space not in VALID_ADDRESS_SPACES:
        raise ValueError(f"Unsupported address_space {address_space!r}; expected one of {VALID_ADDRESS_SPACES}")

    inp = scan_document.get("input", {})
    decoded_sha = inp.get("decoded_rom_sha256") or ""
    artifact_id = _make_artifact_id(inp)

    # Index raw calls by base table address and build lossless observations[]
    calls_by_table: Dict[int, List[dict]] = defaultdict(list)
    observations: List[dict] = []
    sorted_raw_calls = sorted(scan_document.get("calls", []), key=lambda c: (c["call_pc"], c.get("helper", 0)))

    # First pass to deduplicate axes cleanly and assign stable axis IDs
    axis_registry: Dict[Tuple[Any, ...], dict] = {}
    axis_links_by_table: Dict[int, List[dict]] = defaultdict(list)

    def _register_axis(role: str, variant: dict) -> str:
        addr = variant.get("address")
        atype = variant.get("type", "")
        cnt = variant.get("count")
        end_ex = variant.get("end_exclusive")
        asha = variant.get("sha256")
        key = (address_space, addr, atype, cnt, end_ex, asha)
        if key not in axis_registry:
            ax_id = f"axis:{artifact_id}#{address_space}:0x{(addr or 0):05X}:{atype}:{cnt}"
            axis_registry[key] = {
                "axis_id": ax_id,
                "artifact_id": artifact_id,
                "address_space": address_space,
                "address": addr,
                "address_hex": _address_hex(addr),
                "axis_type": atype,
                "count": cnt,
                "end_exclusive": end_ex,
                "end_exclusive_hex": _address_hex(end_ex),
                "sha256": asha,
                "consumer_tables": [],
            }
        return axis_registry[key]["axis_id"]

    for call in sorted_raw_calls:
        tbl = call.get("table")
        obs = {
            "call_id": f"call:{artifact_id}#0x{call['call_pc']:05X}",
            "call_pc": call["call_pc"],
            "call_pc_hex": call.get("call_pc_hex") or _address_hex(call["call_pc"]),
            "call_form": call.get("call_form"),
            "call_instruction": call.get("call_instruction"),
            "target_load_pc": call.get("target_load_pc"),
            "target_register": call.get("target_register"),
            "target_register_moves": list(call.get("target_register_moves", [])),
            "delay_slot": call.get("delay_slot"),
            "helper": call.get("helper"),
            "helper_hex": call.get("helper_hex"),
            "helper_kind": call.get("helper_kind"),
            "element_type": call.get("element_type"),
            "element_width_bytes": call.get("element_width_bytes"),
            "dim1": call.get("dim1"),
            "dim2": call.get("dim2"),
            "axis1_type": call.get("axis1_type"),
            "axis2_type": call.get("axis2_type"),
            "base": tbl,
            "base_hex": _address_hex(tbl),
            "address_space": address_space,
            "axis1": call.get("axis1"),
            "axis2": call.get("axis2"),
            "raw_registers": dict(call.get("raw_registers", {})),
            "caller_start_candidate": call.get("caller_start_candidate"),
            "resolution_status": call.get("resolution_status"),
            "table_span": call.get("table_span"),
            "axis1_span": call.get("axis1_span"),
            "axis2_span": call.get("axis2_span"),
            "argument_evidence_method": call.get("argument_evidence_method"),
            "argument_evidence_limits": list(call.get("argument_evidence_limits", [])),
            "instruction_context": call.get("instruction_context"),
        }
        observations.append(obs)
        if tbl is not None:
            calls_by_table[tbl].append(obs)

    candidates: List[dict] = []
    for tbl_row in sorted(scan_document.get("tables", []), key=lambda t: t["table"]):
        base = tbl_row["table"]
        g_variants = sorted(
            tbl_row.get("geometry_variants", []),
            key=lambda v: (
                v.get("helper_kind", ""),
                v.get("element_type", ""),
                v.get("dim1") or 0,
                v.get("dim2") or 0,
                v.get("byte_length") or 0,
            ),
        )
        ax1_variants = sorted(
            tbl_row.get("axis1_variants", []),
            key=lambda a: (a.get("address") or 0, a.get("type", ""), a.get("count") or 0),
        )
        ax2_variants = sorted(
            tbl_row.get("axis2_variants", []),
            key=lambda a: (a.get("address") or 0, a.get("type", ""), a.get("count") or 0),
        )

        links: List[dict] = []
        for av in ax1_variants:
            ax_id = _register_axis("axis1", av)
            links.append({"role": "axis1", "axis_id": ax_id})
            for reg_ax in axis_registry.values():
                if reg_ax["axis_id"] == ax_id and base not in reg_ax["consumer_tables"]:
                    reg_ax["consumer_tables"].append(base)
        for av in ax2_variants:
            ax_id = _register_axis("axis2", av)
            links.append({"role": "axis2", "axis_id": ax_id})
            for reg_ax in axis_registry.values():
                if reg_ax["axis_id"] == ax_id and base not in reg_ax["consumer_tables"]:
                    reg_ax["consumer_tables"].append(base)

        obs_for_base = calls_by_table.get(base, [])
        # Build explicit span objects; if conflict exists keep all variant spans distinct
        spans = []
        seen_spans = set()
        for o in obs_for_base:
            ts = o.get("table_span")
            if ts is not None:
                sk = (ts.get("start"), ts.get("end_exclusive"), ts.get("element_type"), ts.get("in_bounds"), ts.get("sha256"))
                if sk not in seen_spans:
                    seen_spans.add(sk)
                    spans.append(ts)

        cand_id = f"cand:{artifact_id}#{processor_profile}:{address_space}:0x{base:05X}"
        candidates.append({
            "candidate_id": cand_id,
            "identity_key": {
                "decoded_rom_sha256": decoded_sha,
                "address_space": address_space,
                "base_address": base,
                "processor_profile": processor_profile,
            },
            "artifact_id": artifact_id,
            "base": base,
            "base_hex": _address_hex(base),
            "address_space": address_space,
            "ea": base if address_space == "rom_ea" else None,
            "file_offset": base if address_space == "file_offset" else None,
            "call_pcs": sorted(set(tbl_row.get("call_pcs", []))),
            "helper_addresses": sorted(set(tbl_row.get("helper_addresses", []))),
            "helper_kinds": sorted(set(tbl_row.get("helper_kinds", []))),
            "geometry_variants": g_variants,
            "geometry_conflict": bool(tbl_row.get("geometry_conflict", len(g_variants) > 1)),
            "axis1_variants": ax1_variants,
            "axis2_variants": ax2_variants,
            "axis1_conflict": bool(tbl_row.get("axis1_conflict", len(ax1_variants) > 1)),
            "axis2_conflict": bool(tbl_row.get("axis2_conflict", len(ax2_variants) > 1)),
            "axis_links": links,
            "spans": spans,
            "resolution_statuses": sorted({o["resolution_status"] for o in obs_for_base if o.get("resolution_status")}),
            "evidence_class": "target",
            "donor_hypotheses_count": 0,  # kept separate in `leads[]`
        })

    # Normalize shared axes list deterministically
    axes_list: List[dict] = []
    for ax in sorted(axis_registry.values(), key=lambda a: (a["address"] or 0, a["axis_type"], a["axis_id"])):
        ax_copy = dict(ax)
        ax_copy["consumer_tables"] = sorted(ax["consumer_tables"])
        ax_copy["shared_count"] = len(ax_copy["consumer_tables"])
        axes_list.append(ax_copy)

    # Strictly type all donor leads as non-target hypotheses preserving source hashes
    typed_leads: List[dict] = []
    for lead in sorted(
        donor_leads or [],
        key=lambda l: (
            l.get("target_base") or 0,
            str(l.get("source_sha256") or ""),
            str(l.get("symbol_name") or ""),
            str(l.get("match_basis") or ""),
        ),
    ):
        typed_leads.append({
            "target_base": lead.get("target_base"),
            "target_base_hex": _address_hex(lead.get("target_base")),
            "source_path": lead.get("source_path"),
            "source_sha256": lead.get("source_sha256"),
            "target_rom_sha256": decoded_sha,
            "symbol_kind": lead.get("symbol_kind"),
            "symbol_name": lead.get("symbol_name"),
            "match_basis": lead.get("match_basis"),
            "confidence_tier": lead.get("confidence_tier", "unverified_donor"),
            "evidence_class": "donor",
            "is_target_proof": False,
        })

    # Wire lead counts cleanly without importing donor semantics into candidates
    lead_counts: Dict[int, int] = defaultdict(int)
    for tl in typed_leads:
        if tl["target_base"] is not None:
            lead_counts[tl["target_base"]] += 1
    for c in candidates:
        c["donor_hypotheses_count"] = lead_counts.get(c["base"], 0)

    xml_cmp = scan_document.get("xml_comparison")
    source_reconciliation = None if xml_cmp is None else {
        "sources": {
            "scanner": {"candidate_bases": [c["base"] for c in candidates]},
            "xml": {
                "path": xml_cmp.get("path"),
                "table_count": xml_cmp.get("xml_table_count"),
                "in_xml_count": xml_cmp.get("scanner_bases_in_xml"),
                "missing_from_xml": list(xml_cmp.get("scanner_bases_missing_from_xml", [])),
                "absent_from_scanner": list(xml_cmp.get("xml_table_bases_absent_from_scanner", [])),
            },
        },
        "reconciled_truth": None,  # never flattens multiple sources into one boolean
    }

    body = {
        "schema": SCHEMA_CATALOGUE_V1,
        "output_schema_version": DATA_MODEL_VERSION,
        "manifest": {
            "scanner_schema": scan_document.get("schema"),
            "input": dict(inp),
            "tool": dict(scan_document.get("tool", {})),
            "layout": dict(scan_document.get("layout", {})),
            "summary": dict(scan_document.get("summary", {})),
            "address_space": address_space,
            "processor_profile": processor_profile,
            "optional_indices": _normalize_optional_index_state(optional_indices),
        },
        "helpers": sorted(scan_document.get("helpers", []), key=lambda h: h["address"]),
        "candidates": candidates,
        "observations": observations,
        "axes": axes_list,
        "leads": typed_leads,
        "source_reconciliation": source_reconciliation,
    }
    det_digest = hashlib.sha256(
        json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    body["deterministic_id"] = det_digest
    return body


def build_run_manifest(
    tool_path: Path,
    *,
    input_path: Optional[Path] = None,
    decoded_rom: Optional[bytes] = None,
    command_args: Optional[List[str]] = None,
    exit_status: int = 0,
    output_paths: Optional[List[Path]] = None,
    logs: Optional[List[str]] = None,
) -> dict:
    """Build attributable run manifest per WO70006 & Gate 2 requirements."""
    tool_p = Path(tool_path)
    tool_sha = hashlib.sha256(tool_p.read_bytes()).hexdigest() if tool_p.exists() else None
    container_sha = None
    container_size = None
    if input_path is not None and Path(input_path).exists():
        raw_in = Path(input_path).read_bytes()
        container_sha = hashlib.sha256(raw_in).hexdigest()
        container_size = len(raw_in)
    decoded_sha = hashlib.sha256(decoded_rom).hexdigest() if decoded_rom is not None else None
    decoded_size = len(decoded_rom) if decoded_rom is not None else None

    outputs = []
    for op in sorted(output_paths or [], key=lambda x: str(x)):
        p = Path(op)
        outputs.append({
            "path": str(p),
            "exists": p.exists(),
            "size_bytes": p.stat().st_size if p.exists() else None,
            "sha256": hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None,
        })

    return {
        "schema": "sh705x-run-manifest-v1",
        "output_schema_version": DATA_MODEL_VERSION,
        "tool": {
            "name": tool_p.name,
            "path": str(tool_p),
            "source_sha256": tool_sha,
            "python_version": sys.version.split()[0],
        },
        "input": {
            "path": str(input_path) if input_path is not None else None,
            "container_size_bytes": container_size,
            "container_sha256": container_sha,
            "decoded_rom_size_bytes": decoded_size,
            "decoded_rom_sha256": decoded_sha,
        },
        "command_line": list(command_args) if command_args is not None else list(sys.argv),
        "exit_status": exit_status,
        "logs": list(logs or []),
        "outputs": outputs,
    }


# ---------------------------------------------------------------------------
# 2. Implicit Fixed-Grid Axis Metadata Provider
# ---------------------------------------------------------------------------

def extract_implicit_grids(rom: bytes, helpers: Dict[int, HelperSpec]) -> Dict[int, dict]:
    """
    Extract implicit fixed-grid `(start, step, count, max_raw)` metadata from
    `2D_IMPL` (Pattern A) and `3D_IMPL` (Pattern D) stubs without mutating `HelperSpec`.

    Note: A uniform grid spacing in a stub does NOT prove physical orientation or runtime units.
    """
    grids: Dict[int, dict] = {}
    for addr, h in sorted(helpers.items()):
        if h.kind == "2D_IMPL" and addr + 12 <= len(rom):
            w0 = u16(rom, addr)
            w1 = u16(rom, addr + 2)
            max_val = None
            if (w0 & 0xFF00) == 0x9000:
                ea = addr + 4 + (w0 & 0xFF) * 2
                if ea + 2 <= len(rom):
                    max_val = u16(rom, ea)
            elif (w0 & 0xFF00) == 0xD000:
                ea = (addr & ~3) + 4 + (w0 & 0xFF) * 4
                if ea + 4 <= len(rom):
                    max_val = u32(rom, ea)

            is_u8 = (w1 == 0x655C or h.axis1_type == "implicit_u8")
            domain_ceiling = 256 if is_u8 else 65536
            step = None
            step_verified = False
            if max_val is not None and 0 < max_val < domain_ceiling:
                cand_step = domain_ceiling - max_val
                if cand_step > 0 and max_val % cand_step == 0:
                    step = cand_step
                    expected_pts = (max_val // cand_step) + 1
                    step_verified = (h.dim1 == 0 or h.dim1 == expected_pts)

            grids[addr] = {
                "helper": addr,
                "helper_hex": _address_hex(addr),
                "kind": "2D_IMPL",
                "axis1_grid": {
                    "axis_source": "computed_implicit_grid_stub",
                    "query_domain": "uint8" if is_u8 else "uint16",
                    "axis_start": 0,
                    "axis_step": step,
                    "axis_count": h.dim1,
                    "grid_max_raw": max_val,
                    "step_verified_from_clamp": step_verified,
                    "orientation_proven": False,
                },
                "axis2_grid": None,
            }
        elif h.kind == "3D_IMPL":
            is_u8 = (h.axis1_type == "implicit_u8")
            ceil_v = 256 if is_u8 else 65536
            inferred_step1 = (ceil_v // h.dim1) if h.dim1 > 0 and ceil_v % h.dim1 == 0 else None
            inferred_step2 = (ceil_v // h.dim2) if h.dim2 > 0 and ceil_v % h.dim2 == 0 else None
            grids[addr] = {
                "helper": addr,
                "helper_hex": _address_hex(addr),
                "kind": "3D_IMPL",
                "axis1_grid": {
                    "axis_source": "computed_implicit_grid_stub",
                    "query_domain": "uint8" if is_u8 else "uint16",
                    "axis_start": 0,
                    "axis_step": inferred_step1,
                    "axis_count": h.dim1,
                    "grid_max_raw": (ceil_v - inferred_step1) if inferred_step1 else None,
                    "step_verified_from_clamp": False,
                    "orientation_proven": False,
                },
                "axis2_grid": {
                    "axis_source": "computed_implicit_grid_stub",
                    "query_domain": "uint8" if is_u8 else "uint16",
                    "axis_start": 0,
                    "axis_step": inferred_step2,
                    "axis_count": h.dim2,
                    "grid_max_raw": (ceil_v - inferred_step2) if inferred_step2 else None,
                    "step_verified_from_clamp": False,
                    "orientation_proven": False,
                },
            }
    return grids


# ---------------------------------------------------------------------------
# 3. Opt-In Enhanced Call Scanner + Baseline Comparison
# ---------------------------------------------------------------------------

def extract_calls_enhanced(
    rom: bytes,
    helpers: Dict[int, HelperSpec],
    *,
    code_start: Optional[int] = None,
    window_bytes: int = 128,
) -> List[dict]:
    """
    Opt-in enhanced call extractor preserving identical schema to `extract_calls()`,
    using a wider linear register window (`window_bytes`, default 128B) that stops at
    `rts`/`rte`/`0x4F22` function boundaries and tracks extended reg-copy chains.

    Kept separate from `sh7058_cross_rom_scanner.extract_calls()` so baseline behavior
    is never silently altered.
    """
    if not helpers:
        return []
    inferred_code_start, cal_lo, cal_hi = infer_layout(rom, helpers)
    scan_start = code_start if code_start is not None else inferred_code_start
    calls: List[dict] = []
    code_end = len(rom) - 2
    min_h, max_h = min(helpers), max(helpers)
    helper_set = set(helpers.keys())

    def eval_window_wide(call_pc: int, delay_insn: Optional[int], target_reg: Optional[int]) -> Tuple[Dict[int, Optional[int]], int]:
        win_start = max(scan_start, call_pc - window_bytes)
        for p in range(call_pc - 2, win_start - 2, -2):
            insn = u16(rom, p)
            if insn in (0x000B, 0x002B):  # rts / rte (include delay slot boundary)
                win_start = p + 4
                break
            if insn == 0x4F22 and p < call_pc - 2:  # prior function prologue
                win_start = p
                break
        st: Dict[int, Optional[int]] = {i: None for i in range(16)}
        for p in range(win_start, call_pc, 2):
            w = u16(rom, p)
            n = (w >> 8) & 0xF
            m = (w >> 4) & 0xF
            top = (w >> 12) & 0xF
            if top == 0xD:
                ea = (p & ~3) + 4 + (w & 0xFF) * 4
                if ea + 4 <= len(rom):
                    st[n] = u32(rom, ea)
            elif top == 0x9:
                ea = p + 4 + (w & 0xFF) * 2
                if ea + 2 <= len(rom):
                    v = u16(rom, ea)
                    st[n] = v - 65536 if v >= 32768 else v
            elif top == 0xE:
                st[n] = s8(w & 0xFF) & 0xFFFFFFFF
            elif (w & 0xF00F) == 0x6003:
                st[n] = st[m]
            elif (w & 0xF00F) == 0x600C:
                st[n] = (st[m] & 0xFF) if st[m] is not None else None
            elif (w & 0xF00F) == 0x600D:
                st[n] = (st[m] & 0xFFFF) if st[m] is not None else None
            elif (w & 0xF00F) == 0x600E:
                st[n] = s8(st[m] & 0xFF) & 0xFFFFFFFF if st[m] is not None else None
            elif (w & 0xF00F) == 0x600F:
                v = st[m] & 0xFFFF if st[m] is not None else None
                st[n] = ((v - 65536) if v >= 32768 else v) & 0xFFFFFFFF if v is not None else None
            elif top == 0x7:
                if st[n] is not None:
                    st[n] = (st[n] + s8(w & 0xFF)) & 0xFFFFFFFF
            elif top == 0xB or (w & 0xF0FF) == 0x400B:
                for r in range(8):
                    if r != target_reg:
                        st[r] = None
            elif (w & 0xF0FF) in (0x0023, 0x4008, 0x4018, 0x4028):
                st[n] = None
        if delay_insn is not None:
            w = delay_insn
            n = (w >> 8) & 0xF
            m = (w >> 4) & 0xF
            top = (w >> 12) & 0xF
            if top == 0xD:
                ea = ((call_pc + 2) & ~3) + 4 + (w & 0xFF) * 4
                if ea + 4 <= len(rom):
                    st[n] = u32(rom, ea)
            elif top == 0x9:
                ea = (call_pc + 2) + 4 + (w & 0xFF) * 2
                if ea + 2 <= len(rom):
                    v = u16(rom, ea)
                    st[n] = v - 65536 if v >= 32768 else v
            elif top == 0xE:
                st[n] = s8(w & 0xFF) & 0xFFFFFFFF
            elif (w & 0xF00F) == 0x6003:
                st[n] = st[m]
            elif (w & 0xF00F) == 0x600C:
                st[n] = (st[m] & 0xFF) if st[m] is not None else None
            elif (w & 0xF00F) == 0x600D:
                st[n] = (st[m] & 0xFFFF) if st[m] is not None else None
            elif (w & 0xF00F) == 0x600E:
                st[n] = s8(st[m] & 0xFF) & 0xFFFFFFFF if st[m] is not None else None
            elif (w & 0xF00F) == 0x600F:
                v = st[m] & 0xFFFF if st[m] is not None else None
                st[n] = ((v - 65536) if v >= 32768 else v) & 0xFFFFFFFF if v is not None else None
            elif top == 0x7 and st[n] is not None:
                st[n] = (st[n] + s8(w & 0xFF)) & 0xFFFFFFFF
        return st, win_start

    for pc in range(scan_start, code_end, 2):
        w = u16(rom, pc)
        target = None
        call_pc = None
        delay = None
        treg = None
        call_form = None
        target_reg_moves: List[dict] = []
        top = w >> 12

        if top in (0xD, 0x9):
            val = resolve_pc_pool(rom, pc, w)
            if val is not None and val in helper_set:
                rn = (w >> 8) & 0xF
                for k in range(1, 21):
                    cpc = pc + 2 * k
                    if cpc >= code_end:
                        break
                    cw = u16(rom, cpc)
                    if cw in (0x400B | (rn << 8), 0x402B | (rn << 8)):
                        target = val
                        call_pc = cpc
                        delay = u16(rom, cpc + 2)
                        treg = rn
                        call_form = "indirect_jsr" if cw == (0x400B | (rn << 8)) else "indirect_jmp"
                        break
                    if (cw & 0xF00F) == 0x6003:
                        dst = (cw >> 8) & 0xF
                        src = (cw >> 4) & 0xF
                        if src == rn and dst != rn:
                            target_reg_moves.append({"pc": cpc, "word": cw, "from_register": src, "to_register": dst})
                            rn = dst
                            continue
                        if dst == rn and src != rn:
                            break
                    if cw in (0x000B, 0x002B) or (cw >> 12) in (0xA, 0xB):
                        break
                    if (cw & 0xFF00) in (0x8900, 0x8B00, 0x8D00, 0x8F00):
                        break
                    if (cw & 0xF0FF) in (0x400B, 0x402B):
                        break
                    if ((cw >> 12) in (0xD, 0x9, 0xE, 0x7, 0x6) and ((cw >> 8) & 0xF) == rn):
                        break
        elif top == 0xB:
            tgt = pc + 4 + ((w & 0xFFF) - 4096 if (w & 0xFFF) >= 2048 else (w & 0xFFF)) * 2
            if tgt in helper_set:
                target = tgt
                call_pc = pc
                delay = u16(rom, pc + 2)
                call_form = "bsr"

        if target is not None and call_pc is not None:
            if min_h <= call_pc <= max_h + 0x100:
                continue
            st, win_start = eval_window_wide(call_pc, delay, treg)
            h = helpers[target]
            r4, r5, r6 = st.get(4), st.get(5), st.get(6)

            def is_rom_cal(x: Optional[int]) -> bool:
                return x is not None and cal_lo <= x < cal_hi and not (min_h - 0x200 <= x <= max_h + 0x200)

            tbl = r4 if is_rom_cal(r4) else None
            ax1 = r5 if (h.kind in ("2D_AXIS", "3D_AXIS") and is_rom_cal(r5)) else None
            ax2 = r6 if (h.kind == "3D_AXIS" and is_rom_cal(r6)) else None
            calls.append({
                "call_pc": call_pc,
                "call_form": call_form,
                "target_load_pc": None if treg is None else pc,
                "target_register": treg,
                "target_register_moves": target_reg_moves if treg is not None else [],
                "call_instruction": u16(rom, call_pc),
                "delay_slot": delay,
                "scan_start": scan_start,
                "window_start": win_start,
                "window_bytes": window_bytes,
                "helper": target,
                "kind": h.kind,
                "elem_type": h.elem_type,
                "dim1": h.dim1,
                "dim2": h.dim2,
                "axis1_type": h.axis1_type,
                "axis2_type": h.axis2_type,
                "table": tbl,
                "axis1": ax1,
                "axis2": ax2,
                "raw_r4": r4,
                "raw_r5": r5,
                "raw_r6": r6,
            })
    return calls


def compare_call_extractions(baseline_calls: List[dict], enhanced_calls: List[dict]) -> dict:
    """Compare baseline vs opt-in enhanced call extraction without altering either output."""
    base_by_pc = {c["call_pc"]: c for c in baseline_calls}
    enh_by_pc = {c["call_pc"]: c for c in enhanced_calls}
    newly_resolved = []
    changed_fields = []
    identical = 0

    for pc in sorted(set(base_by_pc) | set(enh_by_pc)):
        bc = base_by_pc.get(pc)
        ec = enh_by_pc.get(pc)
        if bc is None and ec is not None:
            newly_resolved.append({"call_pc": pc, "reason": "new_call_site", "table": ec.get("table")})
        elif bc is not None and ec is not None:
            diffs = {}
            for fld in ("table", "axis1", "axis2", "raw_r4", "raw_r5", "raw_r6"):
                if bc.get(fld) != ec.get(fld):
                    diffs[fld] = {"baseline": bc.get(fld), "enhanced": ec.get(fld)}
            if not diffs:
                identical += 1
            else:
                changed_fields.append({"call_pc": pc, "diffs": diffs})
                if bc.get("table") is None and ec.get("table") is not None:
                    newly_resolved.append({"call_pc": pc, "reason": "resolved_table", "table": ec.get("table")})

    return {
        "baseline_call_count": len(baseline_calls),
        "enhanced_call_count": len(enhanced_calls),
        "identical_call_count": identical,
        "newly_resolved": newly_resolved,
        "changed_fields": changed_fields,
    }


# ---------------------------------------------------------------------------
# 4. Separate Calibration Scalar / 1D-Array Discovery Provider
# ---------------------------------------------------------------------------

def _classify_scalar_deref(rom: bytes, load_pc: int, reg: int, code_end: int) -> Tuple[Optional[str], Optional[int]]:
    """
    Inspect instructions shortly after `mov.l/w @(d,PC),rN` (up to 6 instructions)
    for direct dereference width hints (`uint8`, `uint16`, `uint32`). Conservative only.
    """
    end_scan = min(code_end, load_pc + 14)
    for p in range(load_pc + 2, end_scan, 2):
        w = u16(rom, p)
        if w in (0x000B, 0x002B):
            break
        n = (w >> 8) & 0xF
        m = (w >> 4) & 0xF
        # If reg is overwritten, stop
        if (w >> 12) in (0xD, 0x9, 0xE) and n == reg:
            break
        # mov.[bwl] @Rm, Rn -> 0x6nm0 (b), 0x6nm1 (w), 0x6nm2 (l)
        if (w & 0xF00F) in (0x6000, 0x6001, 0x6002) and m == reg:
            return ({0: "uint8", 1: "uint16", 2: "uint32"}[w & 0xF], p)
        # mov.b @(disp, Rm), r0 (0x84md) / mov.w @(disp, Rm), r0 (0x85md)
        if (w & 0xFF00) == 0x8400 and m == reg:
            return ("uint8", p)
        if (w & 0xFF00) == 0x8500 and m == reg:
            return ("uint16", p)
        # mov.l @(disp, Rm), Rn (0x5nmd)
        if (w >> 12) == 0x5 and m == reg:
            return ("uint32", p)
        # indexed @ (r0, reg) -> 0x0nmC/D/E
        if (w & 0xF00F) in (0x000C, 0x000D, 0x000E) and m == reg:
            return ({0xC: "uint8_array", 0xD: "uint16_array", 0xE: "uint32_array"}[w & 0xF], p)
    return (None, None)


def discover_cal_scalars(
    rom: bytes,
    helpers: Optional[Dict[int, HelperSpec]] = None,
    *,
    excluded_spans: Optional[List[Tuple[int, int]]] = None,
    calls: Optional[List[dict]] = None,
    code_start: Optional[int] = None,
    cal_lo: Optional[int] = None,
    cal_hi: Optional[int] = None,
) -> List[dict]:
    """
    Separate calibration scalar & non-helper pointer discovery provider.
    Scans executable code (`code_start..len(rom)`) for PC-relative `mov.l`/`mov.w`
    pool loads targeting `(cal_lo..cal_hi)` outside excluded lookup-table/axis spans.
    """
    if helpers is None:
        helpers = discover_helpers(rom)
    inf_cs, inf_lo, inf_hi = infer_layout(rom, helpers)
    c_start = inf_cs if code_start is None else code_start
    lo = inf_lo if cal_lo is None else cal_lo
    hi = inf_hi if cal_hi is None else cal_hi

    spans: List[Tuple[int, int]] = list(excluded_spans or [])
    if calls:
        for c in calls:
            t = c.get("table")
            if t is not None:
                w = {"uint8": 1, "int8": 1, "uint16": 2, "int16": 2}.get(c.get("elem_type", ""), 1)
                sz = max(1, (c.get("dim1") or 1) * (c.get("dim2") or 1) * w)
                spans.append((t, t + sz))
            if c.get("axis1") is not None:
                aw = 2 if "16" in str(c.get("axis1_type", "")) else 1
                spans.append((c["axis1"], c["axis1"] + max(1, (c.get("dim1") or 1) * aw)))
            if c.get("axis2") is not None:
                aw = 2 if "16" in str(c.get("axis2_type", "")) else 1
                spans.append((c["axis2"], c["axis2"] + max(1, (c.get("dim2") or 1) * aw)))

    excluded_addrs: Set[int] = set(helpers.keys())
    helper_lo = min(helpers) - 0x200 if helpers else -1
    helper_hi = max(helpers) + 0x200 if helpers else -1

    def _inside_excluded_span(addr: int) -> bool:
        if addr in excluded_addrs:
            return True
        if helpers and helper_lo <= addr <= helper_hi:
            return True
        for s, e in spans:
            if s <= addr < e:
                return True
        return False

    by_target: Dict[int, dict] = {}
    code_end = len(rom) - 2
    for pc in range(c_start, code_end, 2):
        w = u16(rom, pc)
        top = (w >> 12) & 0xF
        if top not in (0xD, 0x9):
            continue
        target = resolve_pc_pool(rom, pc, w)
        if target is None or not (lo <= target < hi):
            continue
        if _inside_excluded_span(target):
            continue
        reg = (w >> 8) & 0xF
        deref_hint, deref_pc = _classify_scalar_deref(rom, pc, reg, len(rom))
        ent = by_target.setdefault(target, {
            "address": target,
            "address_hex": _address_hex(target),
            "address_space": "rom_ea",
            "ref_pcs": [],
            "load_forms": set(),
            "deref_hints": set(),
            "deref_pcs": [],
            "u8_preview": rom[target] if target < len(rom) else None,
            "u16_preview": struct.unpack_from(">H", rom, target)[0] if target + 2 <= len(rom) else None,
            "u32_preview": struct.unpack_from(">I", rom, target)[0] if target + 4 <= len(rom) else None,
            "evidence_class": "target",
            "provider": "discover_cal_scalars_v1",
        })
        ent["ref_pcs"].append(pc)
        ent["load_forms"].add("mov.l" if top == 0xD else "mov.w")
        if deref_hint:
            ent["deref_hints"].add(deref_hint)
        if deref_pc is not None:
            ent["deref_pcs"].append(deref_pc)

    results: List[dict] = []
    for addr in sorted(by_target):
        ent = by_target[addr]
        hints = sorted(ent["deref_hints"])
        # Determine conservative span preview based on deref hints only
        span_elem = "uint16" if hints == ["uint16"] else ("uint8" if hints == ["uint8"] else "unknown")
        span = _export_span(rom, addr, 1, span_elem) if span_elem != "unknown" else _export_span(rom, addr, 1, "unknown")
        results.append({
            "address": addr,
            "address_hex": ent["address_hex"],
            "address_space": ent["address_space"],
            "ref_count": len(ent["ref_pcs"]),
            "ref_pcs": sorted(set(ent["ref_pcs"])),
            "load_forms": sorted(ent["load_forms"]),
            "deref_hints": hints,
            "deref_pcs": sorted(set(ent["deref_pcs"])),
            "u8_preview": ent["u8_preview"],
            "u16_preview": ent["u16_preview"],
            "u32_preview": ent["u32_preview"],
            "span": span,
            "evidence_class": "target",
            "provider": ent["provider"],
        })
    return results


# ---------------------------------------------------------------------------
# Standalone CLI Entry Point
# ---------------------------------------------------------------------------

def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="SH705x Milestone 2 standalone lossless catalogue & opt-in discovery CLI")
    ap.add_argument("rom", help="Path to target ROM (.bin/.zip/.s19/.hex/.dat)")
    ap.add_argument("--out", required=True, help="Output catalogue JSON path (written atomically)")
    ap.add_argument("--manifest", help="Optional output run-manifest JSON path")
    ap.add_argument("--profile", default="SH7058", help="Processor profile label (default: SH7058)")
    ap.add_argument("--address-space", default="rom_ea", choices=VALID_ADDRESS_SPACES)
    ap.add_argument("--enhanced-window", type=int, default=0, help="If >0, run opt-in extract_calls_enhanced(window_bytes=N) comparison")
    ap.add_argument("--include-scalars", action="store_true", help="Include separate discover_cal_scalars() provider output")
    args = ap.parse_args(argv)

    rom_path = Path(args.rom)
    rom = load_any_rom(rom_path)
    helpers = discover_helpers(rom)
    calls = extract_calls(rom, helpers)
    scan_doc = build_scan_export(str(rom_path), rom, helpers, calls)
    catalogue = to_per_address_catalogue(
        scan_doc,
        address_space=args.address_space,
        processor_profile=args.profile,
    )
    catalogue["implicit_grids"] = {f"0x{k:05X}": v for k, v in extract_implicit_grids(rom, helpers).items()}

    if args.enhanced_window > 0:
        enh_calls = extract_calls_enhanced(rom, helpers, window_bytes=args.enhanced_window)
        catalogue["enhanced_call_comparison"] = compare_call_extractions(calls, enh_calls)

    if args.include_scalars:
        catalogue["scalar_candidates"] = discover_cal_scalars(rom, helpers, calls=calls)

    out_path = Path(args.out)
    atomic_write_json(out_path, catalogue)
    written = [out_path]

    if args.manifest:
        man_path = Path(args.manifest)
        man = build_run_manifest(
            Path(__file__),
            input_path=rom_path,
            decoded_rom=rom,
            command_args=argv or sys.argv,
            exit_status=0,
            output_paths=[out_path],
        )
        atomic_write_json(man_path, man)
        written.append(man_path)

    print(
        f"Wrote lossless catalogue ({len(catalogue['candidates'])} candidates, "
        f"{len(catalogue['observations'])} observations, {len(catalogue['axes'])} axes) -> {out_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
