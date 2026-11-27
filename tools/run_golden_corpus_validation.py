#!/usr/bin/env python3
"""
Milestone 5 Explicit Opt-In Golden Corpus Validation & Definition Comparison Runner
(`tools/run_golden_corpus_validation.py`)

NOTE: This runner validates real ROMs from `EVIDENCE/` and MUST NOT run inside
ordinary CI (`.github/workflows/sh7058-scanner-tests.yml`). Invoke explicitly:
    python3 tools/run_golden_corpus_validation.py --out-dir /tmp/sh705x_golden
"""
import argparse
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from nissan_sh705x_workbench import (  # noqa: E402
    EL19A_PINNED_SHA256,
    load_any_rom,
    load_hash_validated_el19a_context,
    parse_nissan_metadata,
    reconcile_definition_sources,
)
from romraider_ref_index import build_reference_index, match_target_against_index  # noqa: E402
from romraider_xml_export import resolve_candidate_evidence, write_preview_bundle  # noqa: E402
from sh7058_cross_rom_scanner import (  # noqa: E402
    build_scan_export,
    discover_helpers,
    extract_calls,
    load_xml_tables,
)
from sh705x_discovery_v2 import (  # noqa: E402
    atomic_write_json,
    compare_call_extractions,
    discover_cal_scalars,
    extract_calls_enhanced,
    extract_implicit_grids,
    to_per_address_catalogue,
)


@dataclass(frozen=True)
class GoldenSpec:
    stem: str
    path: str
    expected_raw_sha256: str
    expected_decoded_sha256: str
    expected_size: int
    reference_xml: Optional[str] = None
    is_el19a: bool = False


GOLDEN_CORPUS: List[GoldenSpec] = [
    GoldenSpec(
        stem="el19a_versa_f501",
        path="EVIDENCE/VERSA f501.bin",
        expected_raw_sha256="bfe037e8e6c389e2a90214047058eb6dc3bcaaaac5b5931bf98a3f5d9f64fd6a",
        expected_decoded_sha256="bfe037e8e6c389e2a90214047058eb6dc3bcaaaac5b5931bf98a3f5d9f64fd6a",
        expected_size=1048576,
        reference_xml="CALIBRATIONS/EL19A_release1_conservative.xml",
        is_el19a=True,
    ),
    GoldenSpec(
        stem="el13a_cvt",
        path="EVIDENCE/23710-EL13A-08-C11-MR18DE-CVT.bin",
        expected_raw_sha256="50acb08f0e913a048d96846b0a87da633e787627b33dfea29110bd8b5d1af54a",
        expected_decoded_sha256="50acb08f0e913a048d96846b0a87da633e787627b33dfea29110bd8b5d1af54a",
        expected_size=1048576,
    ),
    GoldenSpec(
        stem="cf48d_350z",
        path="EVIDENCE/CF48D.bin",
        expected_raw_sha256="fceae3e61f6517b1eb287c4938984498bfa5164688c3985d98baeeaaf52b04f1",
        expected_decoded_sha256="fceae3e61f6517b1eb287c4938984498bfa5164688c3985d98baeeaaf52b04f1",
        expected_size=1048576,
        reference_xml="EVIDENCE/CF48D.xml",
    ),
    GoldenSpec(
        stem="tiida_3dd9a",
        path="EVIDENCE/Nissan Tiida_C12W_3DD9A_705828N.bin",
        expected_raw_sha256="28119daaca1a0641e739ed85d74eacc134988dace10bf00a09875196c9186d42",
        expected_decoded_sha256="28119daaca1a0641e739ed85d74eacc134988dace10bf00a09875196c9186d42",
        expected_size=1048576,
    ),
    GoldenSpec(
        stem="consult_e1br20e_dat",
        path="EVIDENCE/E1BR20E.dat",
        expected_raw_sha256="53c9d50edbb9ef50d6d97c04f655a0e93d455f520bf9be053bc8988c8c297d8c",
        expected_decoded_sha256="c70ff595bb0215ae9ffeb86ccc300dff6ab7764d7f55c3a9f86da669fe8b60ab",
        expected_size=524288,
    ),
    GoldenSpec(
        stem="qashqai_2m_zip",
        path="EVIDENCE/Nissan_Qashqai_2006_2.0i_140_hp_Hitachi_BEDxxx_MECxxx_OBD_NR.zip",
        expected_raw_sha256="26199e277156bbc7a4834d32c3125db6f0748a974e71e760c7c8d78341b6bace",
        expected_decoded_sha256="6c8073482993f55cb9821b94be08b95cd8d2a53243db79c018ced6b61f8448d2",
        expected_size=2097152,
    ),
    GoldenSpec(
        stem="em62b_sh7055_zip",
        path="EVIDENCE/unknown_EM62B_SH7055.bin.zip",
        expected_raw_sha256="b5231ec0acfb6180b102e92189b2d1001c550c920a64e5e663e599f2ce795f49",
        expected_decoded_sha256="67af622b358cbac25f9c8a4fd5fbcb9a04b37c98fe110dfe8f111450f2636495",
        expected_size=524288,
    ),
]


def compare_generated_vs_reference_xml(preview_xml_path: Path, ref_xml_path: Path) -> dict:
    """Compare generated preview XML against a reference XML by storageaddress and extents."""
    gen_root = ET.fromstring(preview_xml_path.read_text(encoding="utf-8"))
    gen_by_addr: Dict[int, dict] = {}
    for tbl in gen_root.findall("./rom/table"):
        sa = tbl.attrib.get("storageaddress")
        if not sa:
            continue
        addr = int(sa, 16)
        gen_by_addr[addr] = {
            "name": tbl.attrib.get("name"),
            "type": tbl.attrib.get("type"),
            "storagetype": tbl.attrib.get("storagetype"),
            "sizex": int(tbl.attrib.get("sizex", "1") or "1"),
            "sizey": int(tbl.attrib.get("sizey", "1") or "1"),
        }

    ref_root = ET.fromstring(ref_xml_path.read_text(encoding="utf-8"))
    ref_rom_el = ref_root if ref_root.tag == "rom" else ref_root.find("./rom")
    ref_base = ref_rom_el.attrib.get("base") if ref_rom_el is not None else None
    ref_explicit_dims: Dict[int, bool] = {}
    if ref_rom_el is not None:
        for tbl in ref_rom_el.findall("./table"):
            sa = tbl.attrib.get("storageaddress")
            if not sa:
                continue
            try:
                addr = int(sa, 16)
            except ValueError:
                continue
            has_dim = any(k in tbl.attrib for k in ("sizex", "sizey", "type"))
            ref_explicit_dims[addr] = has_dim

    ref_by_addr = load_xml_tables(ref_xml_path)
    overlap = sorted(set(gen_by_addr) & set(ref_by_addr))
    gen_only = sorted(set(gen_by_addr) - set(ref_by_addr))
    ref_only = sorted(set(ref_by_addr) - set(gen_by_addr))
    geom_diffs = []
    inherited_dim_skipped = 0
    for a in overlap:
        if not ref_explicit_dims.get(a, False) and ref_base:
            inherited_dim_skipped += 1
            continue
        gt = gen_by_addr[a]
        rt = ref_by_addr[a]
        g_pts = gt["sizex"] * gt["sizey"]
        r_pts = rt["sizex"] * rt["sizey"]
        if g_pts != r_pts:
            geom_diffs.append({
                "address_hex": f"0x{a:05X}",
                "gen_dims": f"{gt['sizex']}x{gt['sizey']}",
                "ref_dims": f"{rt['sizex']}x{rt['sizey']}",
                "ref_name": rt["name"],
            })

    return {
        "reference_xml": str(ref_xml_path),
        "reference_base": ref_base,
        "generated_table_count": len(gen_by_addr),
        "reference_table_count": len(ref_by_addr),
        "overlap_count": len(overlap),
        "generated_not_in_ref_count": len(gen_only),
        "ref_not_in_generated_count": len(ref_only),
        "inherited_dim_overlap_count": inherited_dim_skipped,
        "geometry_disagreement_count": len(geom_diffs),
        "geometry_disagreements_sample": geom_diffs[:25],
    }


def run_golden_validation(out_dir: Path, *, repo_root: Path = Path(".")) -> dict:
    if "CALIBRATIONS" in [p.upper() for p in Path(out_dir).resolve().parts]:
        raise ValueError(f"Refusing to write golden validation outputs into CALIBRATIONS: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Verify pinned SHA-256 hashes on all golden ROMs first
    for spec in GOLDEN_CORPUS:
        rp = repo_root / spec.path
        if not rp.exists():
            raise FileNotFoundError(f"Missing golden ROM: {rp}")
        raw_sha = hashlib.sha256(rp.read_bytes()).hexdigest()
        if raw_sha != spec.expected_raw_sha256:
            raise ValueError(f"Pinned raw SHA-256 mismatch for {rp}: got {raw_sha}, expected {spec.expected_raw_sha256}")
        dec = load_any_rom(rp)
        dec_sha = hashlib.sha256(dec).hexdigest()
        if dec_sha != spec.expected_decoded_sha256 or len(dec) != spec.expected_size:
            raise ValueError(
                f"Pinned decoded ROM mismatch for {rp}: sha={dec_sha} size={len(dec)}, "
                f"expected sha={spec.expected_decoded_sha256} size={spec.expected_size}"
            )

    # 2. Build rebuildable standalone reference index across A2L/TSV/XML/ROM sources
    a2l_inputs = [
        p for p in (
            repo_root / "EVIDENCE/side project/64811000p2_m.a2l",
            repo_root / "EVIDENCE/Nissan Juke 1.6-dig-T S19 (9APCTDEM06)/RFCC_2XHK19BDF1.a2l",
        )
        if p.exists()
    ]
    wo70017_path = repo_root / "CONTROL/WO70017_DONOR_METADATA.tsv"
    xml_inputs = [
        p for p in (
            repo_root / "CALIBRATIONS/EL19A_release1_conservative.xml",
            repo_root / "EVIDENCE/CF48D.xml",
        )
        if p.exists()
    ]
    rom_inputs = [repo_root / s.path for s in GOLDEN_CORPUS]
    ref_idx = build_reference_index(
        a2l_paths=a2l_inputs,
        xml_inputs=xml_inputs,
        rom_paths=rom_inputs,
        wo70017_tsv=wo70017_path if wo70017_path.exists() else None,
    )
    ref_idx_path = out_dir / "golden_ref_index.json"
    atomic_write_json(ref_idx_path, ref_idx)

    # 3. Scan, resolve, preview-export, validate, and compare every golden ROM
    rom_reports: List[dict] = []
    el19a_reconciliation = None
    for spec in GOLDEN_CORPUS:
        rp = repo_root / spec.path
        rom = load_any_rom(rp)
        meta = parse_nissan_metadata(rom)
        helpers = discover_helpers(rom)
        calls = extract_calls(rom, helpers)
        enh_calls = extract_calls_enhanced(rom, helpers, window_bytes=128)
        enh_cmp = compare_call_extractions(calls, enh_calls)
        scalars = discover_cal_scalars(rom, helpers, calls=calls)
        scan_doc = build_scan_export(str(rp), rom, helpers, calls)
        cat = to_per_address_catalogue(scan_doc)
        cat["implicit_grids"] = {f"0x{k:05X}": v for k, v in extract_implicit_grids(rom, helpers).items()}
        cat["scalar_candidates"] = scalars
        cat["enhanced_call_comparison"] = enh_cmp

        xref = match_target_against_index(cat, ref_idx, target_rom=rom)
        el_ctx = load_hash_validated_el19a_context(
            rom,
            expected_rom_sha256=EL19A_PINNED_SHA256,
            index_dir=repo_root / "INDEX",
        )

        # On EL19A itself, require exact match; non-EL19A ROMs MUST report rom_hash_mismatch
        if spec.is_el19a and el_ctx["status"] != "available":
            raise RuntimeError(f"Expected EL19A INDEX adapter available, got {el_ctx['status']} ({el_ctx['reason']})")
        if not spec.is_el19a and el_ctx["reason"] != "rom_hash_mismatch":
            raise RuntimeError(f"Non-EL19A {spec.stem} failed hash-validation gate: {el_ctx}")

        res = resolve_candidate_evidence(cat, xref)
        bundle = write_preview_bundle(
            out_dir,
            spec.stem,
            cat,
            res,
            rom_bytes=rom,
            allow_provisional_donor_names=False,
            skip_trivial=True,
            strict=True,
        )

        # Verify strict semantic barrier: with no target_verified_semantics, zero tables emitted as target_verified
        val_doc = bundle["validation"]
        if val_doc["summary"]["target_verified_count"] != 0:
            raise RuntimeError(f"Donor evidence leaked into target_verified for {spec.stem}")

        def_cmp = None
        if spec.reference_xml and (repo_root / spec.reference_xml).exists():
            def_cmp = compare_generated_vs_reference_xml(Path(bundle["xml_path"]), repo_root / spec.reference_xml)

        if spec.is_el19a:
            # Reconcile all EL19A XMLs & both scope matrices preserving conflicts
            from sh705x_discovery_v2 import SCHEMA_CATALOGUE_V1  # noqa: F401
            from nissan_sh705x_workbench import summarize_tables

            el19a_reconciliation = reconcile_definition_sources(
                xml_paths=[
                    repo_root / "CALIBRATIONS/EL19A_release1_conservative.xml",
                    repo_root / "CALIBRATIONS/EL19A_WO65325_provisional_tiered_v1.xml",
                    repo_root / "CALIBRATIONS/EL19A_best_guess_provisional_full_definition.xml",
                ],
                matrix_paths=[
                    repo_root / "CALIBRATIONS/RELEASE1_SCOPE_MATRIX_R1.csv",
                    repo_root / "CALIBRATIONS/RELEASE1_SCOPE_MATRIX.csv",
                ],
                catalog_path=repo_root / "CALIBRATIONS/discovered_tables_catalog.csv",
                candidate_path=repo_root / "CALIBRATIONS/candidate_register.csv",
                scanner_tables=summarize_tables(rom, calls),
            )
            atomic_write_json(out_dir / "el19a_reconciliation.json", el19a_reconciliation)

        rom_reports.append({
            "stem": spec.stem,
            "path": spec.path,
            "decoded_sha256": spec.expected_decoded_sha256,
            "size_bytes": spec.expected_size,
            "fid": meta.get("fid"),
            "cpu": meta.get("fid_cpu"),
            "helpers_count": len(helpers),
            "baseline_calls_count": len(calls),
            "enhanced_newly_resolved_count": len(enh_cmp["newly_resolved"]),
            "catalogue_candidates_count": len(cat["candidates"]),
            "scalar_candidates_count": len(scalars),
            "code_twin_matches_count": len(xref.get("code_twin_matches", [])),
            "el19a_index_status": el_ctx["status"],
            "el19a_index_reason": el_ctx["reason"],
            "xml_valid": val_doc["valid"],
            "xml_table_count": val_doc["summary"]["table_count"],
            "provisional_donor_lead_count": val_doc["summary"]["provisional_donor_lead_count"],
            "unknown_raw_only_count": val_doc["summary"]["unknown_raw_only_count"],
            "overlap_warnings": val_doc["summary"]["overlap_warning_count"],
            "definition_comparison": def_cmp,
        })

    sources = ref_idx.get("sources", {})
    lookups = ref_idx.get("lookups", {})
    summary = {
        "schema": "sh705x-golden-validation-v1",
        "golden_rom_count": len(rom_reports),
        "reference_index_summary": {
            "a2l_files": len(sources.get("a2l_files", [])),
            "xml_documents": len(sources.get("xml_documents", [])),
            "donor_roms": len(sources.get("donor_roms", [])),
            "wo70017_rows": (sources.get("wo70017_tsv") or {}).get("row_count", 0),
            "xml_addrs": len(lookups.get("xml_by_addr", {})),
            "a2l_addrs": len(lookups.get("a2l_by_addr", {})),
            "payload_hashes": len(lookups.get("payload_index", {})),
            "code_hashes": len(lookups.get("code_hash_index", {})),
        },
        "el19a_reconciliation_summary": {
            "address_count": el19a_reconciliation["address_count"],
            "conflict_counts": el19a_reconciliation["conflict_counts"],
        } if el19a_reconciliation else None,
        "roms": rom_reports,
    }
    atomic_write_json(out_dir / "golden_validation_summary.json", summary)
    return summary


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Explicit opt-in golden ROM corpus validation (not for ordinary CI)")
    ap.add_argument("--out-dir", default="/tmp/sh705x_golden_validation", help="Output directory (never CALIBRATIONS/)")
    args = ap.parse_args(argv)
    summary = run_golden_validation(Path(args.out_dir))
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
