#!/usr/bin/env python3
"""Exact-image helper-profile resolver for SH705x Reader Trace v0.1.

This module does not decode instructions. It attaches previously documented
helper contracts only when processor family, decoded ROM SHA-256 and helper EA
all match exactly. Profile evidence remains report-sourced, never silently
promoted to direct instruction observations.
"""
from __future__ import annotations

import copy
import re
from typing import Any, Dict, Mapping, Optional, Tuple


class HelperProfileError(ValueError):
    """Invalid helper-profile request or graph provenance."""


ROM_SHA256 = "bfe037e8e6c389e2a90214047058eb6dc3bcaaaac5b5931bf98a3f5d9f64fd6a"
PROCESSOR_FAMILY = "SH7058"

# Keyed by exact processor + decoded artifact identity + helper EA.
# Every mechanic below is transcribed from the cited report/finding, not
# inferred from the helper name or a fuzzy address/function-name match.
_PROFILES = {
    (PROCESSOR_FAMILY, ROM_SHA256, 0x22E10): {
        "profile_id": "EL19A-F501-sub_22E10-implicit-u8-16-v1",
        "helper_symbol": "sub_22E10",
        "source_evidence_refs": ["ev:wo70013", "ev:fnd-000026"],
        "source_listing_sha256": None,
        "evidence_basis": "reported_observation",
        "evidence_grade": "reader-verified as reported in WO70013/FND-000026; listing identity hash absent",
        "mechanics": {
            "lookup_kind": "implicit_uniform_1d",
            "values_pointer_register": "R4",
            "query_register": "R5",
            "query_type": {"storage": "uint8", "signed": False},
            "point_count": 16,
            "implicit_axis": {"start": 0, "step": 16},
            "search": {"kind": "uniform_interval_index_and_fraction"},
            "interpolation": {"method": "linear_between_adjacent_values", "helper": "sub_231C8"},
            "upper_boundary": {
                "operator": ">=",
                "query": 240,
                "action": "return_last_element",
                "element_index": 15,
            },
            "return_register": "R0",
        },
        "limitations": [
            "Reported implicit-grid endpoint text says 224, while 16 points at step 16 yield 240; keep this discrepancy unresolved until exact helper instructions are re-read.",
            "This profile records the closed report's mechanic description; it is not an independent instruction decode.",
        ],
    },
    (PROCESSOR_FAMILY, ROM_SHA256, 0x22FAC): {
        "profile_id": "EL19A-F501-sub_22FAC-explicit-u16-32-v1",
        "helper_symbol": "sub_22FAC",
        "source_evidence_refs": ["ev:wo70014", "ev:fnd-000014"],
        "source_listing_sha256": None,
        "evidence_basis": "reported_observation",
        "evidence_grade": "reader-verified as reported in WO70014/FND-000014; exact listing hash not recorded in those source records",
        "mechanics": {
            "lookup_kind": "explicit_axis_1d",
            "values_pointer_register": "R4",
            "axis_pointer_register": "R5",
            "query_register": "R6",
            "query_type": {"storage": "uint16", "signed": False},
            "point_count": 32,
            "axis_storage": "uint16",
            "search": {"kind": "explicit_axis_search", "helper": "sub_2340C"},
            "fraction": {"helper": "sub_23700"},
            "interpolation": {"method": "UWORD value interpolation", "helper": "sub_231C8"},
            "return_register": "R0",
        },
        "limitations": [
            "The cited report does not pin the exact Stage-16 listing hash for this helper window.",
            "Out-of-range axis policy is not promoted beyond what the report explicitly records.",
        ],
    },
    (PROCESSOR_FAMILY, ROM_SHA256, 0x22B44): {
        "profile_id": "EL19A-F501-sub_22B44-two-axis-u8-map-v1",
        "helper_symbol": "sub_22B44",
        "source_evidence_refs": ["ev:wo70033", "ev:fnd-000028", "ev:lst-stage16"],
        "source_listing_sha256": "148385bbec91f6a491dcaa403962836f709c2f273df9a17ec51f1dea5f7f4549",
        "evidence_basis": "reported_observation",
        "evidence_grade": "reader-verified as reported in WO70033/FND-000028 against the pinned Stage-16 listing",
        "mechanics": {
            "lookup_kind": "two_axis_map",
            "values_pointer_register": "R4",
            "axis1_pointer_register": "R5",
            "axis2_pointer_register": "R6",
            "query_register": "R7",
            "query_type": {"storage": "uint8", "signed": False},
            "same_query_for_both_axes": True,
            "axis_search": {"helper": "sub_233CC", "calls_per_lookup": 2},
            "cell_offset": "4*row_index + column_index",
            "corner_interpolation": {"helper": "sub_231C8"},
            "return_register": "R0",
        },
        "limitations": [
            "This is an exact-image helper contract copied from a closed trace report, not a new disassembly pass.",
            "The reported 4x4 map is all zero; geometry evidence does not establish a physical signal or unit.",
            "The exact endpoint behavior of each sub_233CC axis search is not stated in the source report.",
        ],
    },
    (PROCESSOR_FAMILY, ROM_SHA256, 0x22DF8): {
        "profile_id": "EL19A-F501-sub_22DF8-implicit-u8-8-v1",
        "helper_symbol": "sub_22DF8",
        "source_evidence_refs": ["ev:wo70033", "ev:fnd-000028", "ev:lst-stage16"],
        "source_listing_sha256": "148385bbec91f6a491dcaa403962836f709c2f273df9a17ec51f1dea5f7f4549",
        "evidence_basis": "reported_observation",
        "evidence_grade": "reader-verified as reported in WO70033/FND-000028 against the pinned Stage-16 listing",
        "mechanics": {
            "lookup_kind": "implicit_uniform_1d",
            "values_pointer_register": "R4",
            "query_register": "R5",
            "query_type": {"storage": "uint8", "signed": False},
            "point_count": 8,
            "implicit_axis": {"start": 0, "step": 32},
            "search": {"kind": "uniform_interval_index_and_fraction"},
            "interpolation": {"method": "8-point UBYTE interpolation", "helper": "sub_23508"},
            "upper_boundary": {
                "operator": ">=",
                "query": 224,
                "action": "return_last_element",
                "element_index": 7,
            },
            "return_register": "R0",
        },
        "limitations": [
            "The caller's shift/clamp query construction is separate from this helper profile.",
            "Donor labels mTDATDDS/mTDATDPRE remain unpromoted physical-name hypotheses.",
        ],
    },
}


def _parse_helper_ea(value: Any) -> int:
    if isinstance(value, int) and value >= 0:
        return value
    if isinstance(value, str):
        token = value.strip()
        try:
            return int(token, 16) if token.lower().startswith("0x") else int(token, 16)
        except ValueError:
            pass
    raise HelperProfileError(f"invalid helper EA: {value!r}")


def resolve_helper_profile(
    processor_family: str,
    decoded_sha256: str,
    helper_ea: Any,
) -> Optional[Dict[str, Any]]:
    """Return a deep-copied profile only for an exact processor/ROM/EA match."""
    if processor_family not in {"SH7055", "SH7058"}:
        raise HelperProfileError(f"unsupported processor family: {processor_family!r}")
    if not isinstance(decoded_sha256, str) or re.fullmatch(r"[0-9a-fA-F]{64}", decoded_sha256) is None:
        raise HelperProfileError("decoded_sha256 must be a 64-character hexadecimal digest")
    ea = _parse_helper_ea(helper_ea)
    profile = _PROFILES.get((processor_family, decoded_sha256.lower(), ea))
    return copy.deepcopy(profile) if profile is not None else None


def attach_helper_profile(graph: Mapping[str, Any]) -> Dict[str, Any]:
    """Attach the exact helper profile to one matching lookup_helper node.

    If no exact profile exists, the graph is returned unchanged. If a profile
    exists but its report evidence is not already present in the graph, fail
    rather than attaching unsupported provenance.
    """
    if not isinstance(graph, Mapping):
        raise HelperProfileError("graph must be a mapping")
    artifact = graph.get("artifact")
    call = graph.get("call_ref")
    if not isinstance(artifact, Mapping) or not isinstance(call, Mapping):
        raise HelperProfileError("graph artifact and call_ref are required")
    profile = resolve_helper_profile(
        artifact.get("processor_family"),
        artifact.get("decoded_sha256"),
        call.get("helper_ea"),
    )
    out = copy.deepcopy(dict(graph))
    if profile is None:
        return out

    evidence_ids = {
        ev.get("evidence_id")
        for ev in out.get("evidence", [])
        if isinstance(ev, Mapping)
    }
    missing = sorted(set(profile["source_evidence_refs"]) - evidence_ids)
    if missing:
        raise HelperProfileError(
            "exact helper profile matched but required report evidence is missing: "
            + ", ".join(missing)
        )

    helper_ea = _parse_helper_ea(call.get("helper_ea"))
    candidates = [
        node for node in out.get("nodes", [])
        if node.get("kind") == "lookup_helper"
        and isinstance(node.get("address"), Mapping)
        and node["address"].get("value") == helper_ea
    ]
    if len(candidates) != 1:
        raise HelperProfileError(
            f"exact helper profile matched, but graph has {len(candidates)} matching lookup_helper nodes"
        )

    properties = candidates[0].setdefault("properties", {})
    existing = properties.get("recognized_profile")
    if existing and existing != profile["profile_id"]:
        raise HelperProfileError("helper node already has a conflicting recognized profile")
    properties["recognized_profile"] = profile["profile_id"]
    properties["profile_basis"] = profile["evidence_basis"]
    properties["profile_evidence_refs"] = list(profile["source_evidence_refs"])
    properties["source_listing_sha256"] = profile["source_listing_sha256"]
    properties["mechanics"] = copy.deepcopy(profile["mechanics"])
    properties["profile_limitations"] = list(profile["limitations"])

    extension_id = f"helper-profile-{helper_ea:08X}"
    extensions = out.setdefault("analysis_extensions", [])
    extension = {
        "extension_id": extension_id,
        "adapter": "reader-trace-helper-profile-resolver-v0.1",
        "match_status": "exact_processor_rom_sha256_helper_ea",
        "profile_id": profile["profile_id"],
        "basis": "reported_observation",
        "evidence_refs": list(profile["source_evidence_refs"]),
    }
    old = [item for item in extensions if item.get("extension_id") == extension_id]
    if old and old[0] != extension:
        raise HelperProfileError("conflicting helper profile extension already exists")
    if not old:
        extensions.append(extension)
    return out


def list_profile_keys() -> Tuple[Tuple[str, str, int], ...]:
    """Return stable exact-match profile keys for diagnostics/tests."""
    return tuple(sorted(_PROFILES.keys(), key=lambda row: (row[0], row[1], row[2])))
