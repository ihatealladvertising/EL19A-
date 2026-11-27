# SH705x Tool Rollout Status (`tools/ROLLOUT_STATUS.md`)

**Authoritative Progress Tracker** — Last updated: `2026-11-27`  
**Controlling Plans:** `CONTROL/SH705X_ROM_TOOL_PLAN.md`, `CONTROL/SH705X_DATA_MODEL_SPEC.md`, `CONTROL/WO70020.md`–`WO70023.md`, plus Manager Refinements (A–E + Checkpoint Protocol).  
**Environment Note:** Workspace is a direct snapshot without `.git` history; source state is tracked via exact SHA-256 hashes below. Runtime verified on `Python 3.11.2`.

---

## Controlling Engineering Rules

1. **No real ROMs in ordinary CI:** CI executes strictly against generated synthetic fixtures (`tools/test_sh7058_cross_rom_scanner.py`, `tools/test_nissan_sh705x_workbench.py`). Golden ROM integration runs are manual/explicit with pinned ROM SHA-256 digests.
2. **Preserve proven `extract_calls()` behavior:** New discovery paths (wider register tracking, 1D/scalar `pool32` discovery, implicit fixed-grid axis math) are added as separate opt-in providers/functions and compared against the baseline before promotion.
3. **Separate independent confidence dimensions:** Every discovered object tracks Structural, Cross-Reference, Runtime, and Semantic confidence plus Export Eligibility separately—never collapse a donor payload match into semantic proof.
4. **Preview-first XML generation:** Export emits preview XML + provenance, validation, and unresolved reports via temp files renamed atomically only after validation passes; never overwrite `CALIBRATIONS/` baselines or last known-good exports in place.
5. **Rebuildable, separate reference index:** `romraider_ref_index.py` (Milestone 3) must store container/decoded SHA-256s, schema/parser versions, match basis, and all conflicts without silently discarding hits.
6. **Lossless scanner core (`WO70023`):** Future catalogue emission wraps `sh7058_cross_rom_scanner.build_scan_export()` via `to_per_address_catalogue()` rather than `workbench.summarize_tables()`.

---

## Milestone Progress Checklists

### Milestone 0 — Architecture Baseline (`ESTABLISHED`)
- [x] Reconciled repo architecture (`CONTROL/SH705X_ROM_TOOL_PLAN.md`, `SH705X_WORKBENCH_INTEGRATION_PLAN.md`, `SH705X_DATA_MODEL_SPEC.md`, `WO70020`–`WO70023`).
- [x] Pinned baseline tool SHA-256 hashes prior to any functional edits (`Python 3.11.2`):
  - `tools/sh7058_cross_rom_scanner.py`: `ec0ba0d40a7c4a444b94a123be8426584724453a394ed8e8097f3d123982532d`
  - `tools/nissan_sh705x_workbench.py`: `2cd08b89c766f59b923670f5b851e51dc418e090529046d6519705a00c7ee90c`
  - `tools/a2l_structural_matcher.py`: `452af3d0c877554a8e70ed670ab8675b86cb2fd5a490ad6f598e79524dcf7ee2`
  - `tools/rom_access_indexer.py`: `56a31c2138885fa99c8df0a5e56b26964c827ec6266956e9bacb33d669c049d6`
  - `tools/build_static_indices.py`: `f609dcef877c3aa99b5e3758242c43cf892545374700d988b4b520a0e7a72be`
  - `tools/extract_diagnostic_rosetta.py`: `3c89603095e2f432e97feb1b36fa5b873f96301741e803420138c807f8c56eff`
  - `tools/analyze_el19a_el13a_diff.py`: `5b230d95e81b850ad73863ce79702705a2323fd70bb675565a8c14be209ec39f`
  - `tools/test_sh7058_cross_rom_scanner.py`: `26bcfc323e9a95c405aaad5dd609be1852a9c5226e3e8c4a495841a64d81ee87`
- [x] Verified baseline test suite status before edits:
  - `tools/test_sh7058_cross_rom_scanner.py`: **8/8 OK**.
  - Pre-existing unrelated test status noted (not modified in Milestone 1): `tools/test_rom_access_indexer.py` (24 tests: 20 OK, 2 skipped needing env TSVs, 2 pre-existing errors from escaped `\\n` literals at L437/L448); `tools/test_wo_registry.py` (fails on legacy `CONTROL/WO*.md` missing `<!-- WO_META_START -->`).

### Milestone 1 — Workbench Regression Safety Net & CI (`COMPLETE — VERIFIED 2026-11-27`)
- [x] Zero functional modifications made to `tools/nissan_sh705x_workbench.py` or `tools/sh7058_cross_rom_scanner.py`.
- [x] Created `tools/test_nissan_sh705x_workbench.py` (SHA-256: `0401d64838d1056fc04b24a8ad12a39e91390f8604da691338296d6ed1de6c6e`, 8 synthetic test methods):
  - Loaders: `.s19`, `.hex`, Consult `.dat` (`0x8015` Feistel roundtrip + checksum failure + `%6` SBL/ROM frames), `.zip` preference, non-flat/media container rejections (Osiris, WinOLS, PNG, PDF, JPEG, TCM `0x8019`, partial KWP2000 `0xB8 0x15 0xF1`).
  - Metadata & Checksums: `LOADER80`/`FID`/`RAMF`/IVT parsing and all 4 checksums (`ck_std`, `ck_alt2`, `cal16`, `main16`) plus tamper detection and `checksum_byte_tags()`.
  - Parsers & Analysis: `parse_a2l_rich()`, `load_csv_addr_map()`, `summarize_tables()` (shared-axis & reciprocal pairs, inclusive end pinned), `decode_rom_values()`, `build_func_profiles()` + `build_a2l_table_leads()` consensus/unavailable handling, `_cluster_raw_diffs()`, and `_format_cluster_values()`.
  - End-to-end CLI smoke tests (`cmd_scan` TSV/JSON, `cmd_diff`, `cmd_inspect`, `cmd_audit`).
- [x] Updated `.github/workflows/sh7058-scanner-tests.yml` (SHA-256: `4af488f15438ae7d478372dbdbb71b74f6bb292cea6e7b5ca56668d195090a81`) to compile and execute both `tools/test_sh7058_cross_rom_scanner.py` and `tools/test_nissan_sh705x_workbench.py` on Python 3.11 without real ROMs.
- [x] Created `tools/ROLLOUT_STATUS.md`.
- **Verification Command & Result:**
  - `python3 -m py_compile tools/sh7058_cross_rom_scanner.py tools/test_sh7058_cross_rom_scanner.py tools/nissan_sh705x_workbench.py tools/test_nissan_sh705x_workbench.py && python3 -m unittest -v tools/test_sh7058_cross_rom_scanner.py tools/test_nissan_sh705x_workbench.py`
  - Result: **Ran 16 tests in 2.505s — OK** (exit code 0).

### Milestone 2 — Lossless Catalogue Wrapper, Implicit-Axis Metadata & Opt-In Enhanced Discovery (`COMPLETE — VERIFIED 2026-11-27`)
- [x] Baseline `tools/sh7058_cross_rom_scanner.py` (`ec0ba0d4...`) and `tools/nissan_sh705x_workbench.py` (`2cd08b89...`) left **100% unchanged** (`extract_calls()` and `summarize_tables()` untouched).
- [x] Created `tools/sh705x_discovery_v2.py` (SHA-256: `ca72e863b7960c7608b25f1b57225b3c46c2f57efedbf1025ef0584ba600533a`):
  - `to_per_address_catalogue()` + `build_run_manifest()` lossless wrapper over `build_scan_export()` (`WO70023` + `WO70021` `sh705x-datamodel-v1.0.0`), retaining conflicts, overlapping spans, first-class shared axes, explicit `address_space`, unavailable optional indices, and typed donor leads.
  - `extract_implicit_grids()` deriving `(axis_start, axis_step, axis_count, grid_max_raw)` for `2D_IMPL` and `3D_IMPL` stubs with `orientation_proven=False`.
  - Opt-in `extract_calls_enhanced(..., window_bytes=128)` + `compare_call_extractions()`.
  - Separate `discover_cal_scalars()` provider scanning PC-relative calibration pointers outside lookup tables/axes with conservative deref-width hints.
  - Crash-safe `atomic_write_text()` / `atomic_write_json()` (temp file + `fsync` + `os.replace`).
- [x] Created `tools/test_sh705x_discovery_v2.py` (SHA-256: `51434c8e9fe96562bf6f4aad36a2e85b1938829a09a127f84840b8add9b3926f`, 6 synthetic test suites covering `WO70023` `accept.T1`–`accept.T10`, implicit grids, enhanced window diff vs untouched baseline, scalar discovery, and atomic manifest CLI).
- [x] Updated `.github/workflows/sh7058-scanner-tests.yml` (SHA-256: `3b76af75dbf5156333c9581fabf9ac3fd931994e7805818be9e3902ae0388108`).
- **Verification Command & Result:**
  - `python3 -m py_compile tools/sh7058_cross_rom_scanner.py tools/test_sh7058_cross_rom_scanner.py tools/nissan_sh705x_workbench.py tools/test_nissan_sh705x_workbench.py tools/sh705x_discovery_v2.py tools/test_sh705x_discovery_v2.py && python3 -m unittest -v tools/test_sh7058_cross_rom_scanner.py tools/test_nissan_sh705x_workbench.py tools/test_sh705x_discovery_v2.py`
  - Result: **Ran 22 tests in 3.315s — OK** (exit code 0).

### Milestone 3 — Standalone A2L/XML/ROM Reference Index (`COMPLETE — VERIFIED 2026-11-27`)
- [x] Created standalone rebuildable `tools/romraider_ref_index.py` (SHA-256: `206f99ff2ea8f3c9e961353a0cd94059d22be9b62d9ea4a0ac97547de2f12f1e`):
  - Unified relational ASAP2 parser (`parse_a2l_bytes_relational` / `parse_a2l_relational`) indexing `COMPU_METHOD`, `COMPU_TAB`, `COMPU_VTAB`, `COMPU_VTAB_RANGE`, `RECORD_LAYOUT`, `FUNCTION`, `GROUP`, `AXIS_PTS`, `CHARACTERISTIC` (with `AXIS_DESCR` & `FIX_AXIS_PAR`), and `MEASUREMENT` (`ram_ea`), retaining duplicate declarations at shared addresses.
  - Pre-parsed `CONTROL/WO70017_DONOR_METADATA.tsv` loader (`load_wo70017_metadata_tsv`).
  - RomRaider XML corpus collector (`collect_xml_documents`) handling loose `.xml`, directories, and `.zip` archives while tolerating individual malformed XMLs (`parse_error`).
  - Metadata-bounded ROM signature & payload indexer (`index_rom_signature`) deriving explicit `[code_start, code_end_exclusive)` boundaries from `infer_layout()` + `parse_nissan_metadata()` + `active_end`.
  - Conflict-preserving cross-reference matcher (`match_target_against_index`) reporting code twins, relocated/same-address payloads, XML/A2L hits, and explicit conflicts—all typed `evidence_class="donor"` (`is_target_proof=False`).
  - Standalone `build` (atomic JSON) and `query` CLI entry points.
- [x] Created `tools/test_romraider_ref_index.py` (SHA-256: `801e7de0ab4ffbe670c5392a5249447684021bc817e867d772cc443fffb8d290`, 4 synthetic test methods).
- [x] Updated `.github/workflows/sh7058-scanner-tests.yml` (SHA-256: `0123c36e82c8f2bb62f617ab985d36ebea825296e1d1a0a571a722e0c31e690e`).
- **Verification Command & Result:**
  - `python3 -m py_compile tools/sh7058_cross_rom_scanner.py tools/test_sh7058_cross_rom_scanner.py tools/nissan_sh705x_workbench.py tools/test_nissan_sh705x_workbench.py tools/sh705x_discovery_v2.py tools/test_sh705x_discovery_v2.py tools/romraider_ref_index.py tools/test_romraider_ref_index.py && python3 -m unittest -v tools/test_sh7058_cross_rom_scanner.py tools/test_nissan_sh705x_workbench.py tools/test_sh705x_discovery_v2.py tools/test_romraider_ref_index.py`
  - Result: **Ran 26 tests in 4.212s — OK** (exit code 0).

### Milestone 4 — Confidence/Evidence Resolver & Preview-First RomRaider XML Generator (`COMPLETE — VERIFIED 2026-11-27`)
- [x] Baseline `tools/sh7058_cross_rom_scanner.py` (`ec0ba0d4...`) and `tools/nissan_sh705x_workbench.py` (`2cd08b89...`) remain **100% unchanged**.
- [x] Created standalone `tools/romraider_xml_export.py` (SHA-256: `fd62b47fb870b17e8fbe54c7653d6623f1af262db6156b01c917b52b27c6a3b6`):
  - `resolve_candidate_evidence()` implementing the 4 independent confidence dimensions (`structural_confidence`, `crossref_confidence`, `runtime_confidence`, `semantic_confidence`) plus explicit `export_eligibility`, enforcing strict donor-to-target barrier (`provisional_donor_lead` never promoted to `target_verified` without verified target semantics).
  - `generate_romraider_preview()` emitting preview-only RomRaider XML + `provenance`, `validation`, and `unresolved` JSON reports: Tier D raw objects strictly keep `RAW_*` names and `Raw_*` identity scalings (opt-in `--allow-provisional-donor-names` adds `[PROVISIONAL]` labels without donor conflicts while keeping `Raw_*` scaling); explicit ROM axes emit `X Axis`/`Y Axis` (shared axes tagged `[SHARED_AXIS]`), while implicit fixed-grid stubs emit `Static X Axis`/`Static Y Axis` labeled `(computed stub, orientation unverified)` with `<data>` points and `orientation_proven=False`.
  - `validate_romraider_xml()` verifying well-formed XML, `<romid>/<ecuid>`, scaling declarations, hex `storageaddress`, ROM bounds, duplicate table names, and overlapping table extent warnings.
  - `write_preview_bundle()` blocking writes inside protected `CALIBRATIONS/` directories and atomically writing all 4 preview artifacts only after `--strict` validation passes.
- [x] Created `tools/test_romraider_xml_export.py` (SHA-256: `5a92275983aeec2230f49a5cea08e5c6b043ca8d32792a40c0e878e15793ddc2`, 4 synthetic test methods covering confidence barrier, conflict/OOB routing, Tier D raw scaling gate, shared vs computed implicit grid axes, validator checks, `CALIBRATIONS/` guard, strict overwrite protection, and end-to-end CLI bundle export).
- [x] Updated `.github/workflows/sh7058-scanner-tests.yml` (SHA-256: `00e481a14b2bc6c8cb93dabab3b0c785bcfb24d53be1f0b3e83427d9f1fe4295`) to compile and test `tools/romraider_xml_export.py` and `tools/test_romraider_xml_export.py` on Python 3.11 without real ROMs.
- **Verification Command & Result:**
  - `python3 -m py_compile tools/sh7058_cross_rom_scanner.py tools/test_sh7058_cross_rom_scanner.py tools/nissan_sh705x_workbench.py tools/test_nissan_sh705x_workbench.py tools/sh705x_discovery_v2.py tools/test_sh705x_discovery_v2.py tools/romraider_ref_index.py tools/test_romraider_ref_index.py tools/romraider_xml_export.py tools/test_romraider_xml_export.py && python3 -m unittest -v tools/test_sh7058_cross_rom_scanner.py tools/test_nissan_sh705x_workbench.py tools/test_sh705x_discovery_v2.py tools/test_romraider_ref_index.py tools/test_romraider_xml_export.py`
  - Result: **Ran 30 tests in 4.744s — OK** (exit code 0).

### Milestone 5 — Workbench Integration & Controlled Golden Corpus Validation (`COMPLETE — VERIFIED 2026-11-27`)
- [x] Baseline `tools/sh7058_cross_rom_scanner.py` (`ec0ba0d40a7c4a444b94a123be8426584724453a394ed8e8097f3d123982532d`) and Milestone 2–4 standalone modules (`sh705x_discovery_v2.py` `ca72e863...`, `romraider_ref_index.py` `206f99ff...`, `romraider_xml_export.py` `fd62b47f...`) remain **100% unchanged**.
- [x] Extracted shared pure ROM container & Nissan metadata parser into `tools/sh705x_rom_loader.py` (SHA-256: `34d343f0aef64590a6b36930d008c659e1a1b901b7be254fd3b4fcde29147098`) and registered `__main__` module alias so both imported and direct CLI invocations work without circular imports.
- [x] Updated `tools/nissan_sh705x_workbench.py` (SHA-256: `30e39d0774d144dd3d8fe7d9b5b95ed118fb9e785a05d51b138b1a13b0f4076a`):
  - Preserved all existing `scan`/`audit`/`inspect`/`diff` flags and default outputs backwards-compatibly.
  - Added lossless catalogue + run-manifest + opt-in enhanced window + scalar flags to `scan` (`--catalogue`, `--manifest`, `--enhanced-window`, `--include-scalars`).
  - Added hash-validated optional EL19A `INDEX/` + diagnostic PID adapter (`load_hash_validated_el19a_context`, pinned SHA-256 `bfe037e8e6c389e2a90214047058eb6dc3bcaaaac5b5931bf98a3f5d9f64fd6a`; refuses with `rom_hash_mismatch` on non-EL19A ROMs).
  - Added multi-XML / dual scope matrix / catalog / `candidate_register.csv` reconciliation (`reconcile_definition_sources`) surfacing `xml_name_conflict`, `scaling_conflict`, `disposition_conflict`, and `geometry_conflict`.
  - Added `ref-index build|query` and preview-first `export-xml` subcommands plus structured `--json-out` on `diff`.
- [x] Extended `tools/test_nissan_sh705x_workbench.py` (SHA-256: `bdfa62500a3ffa39d9b0dbc2d727133f805f20a86ed023baf71b7dc75c5f3f4e`, 11 test methods including `Milestone5IntegrationTests`: CLI bundle export, hash-validated EL19A adapter gate, dual-matrix reconciliation, and direct CLI subprocess execution).
- [x] Updated `.github/workflows/sh7058-scanner-tests.yml` (SHA-256: `513c3d42dd79de65691ebde755f1c081433db8b5fd37177d1f57f1694bbed911`) to compile `tools/sh705x_rom_loader.py` alongside all synthetic modules/tests (zero real ROMs or `run_golden_corpus_validation.py` in CI).
- [x] Created explicit opt-in `tools/run_golden_corpus_validation.py` (SHA-256: `b21fbd766e48b4712ef606c2996aec557eebbb77b2fe88960aae523a5e97c4c2`) pinning raw + decoded SHA-256 hashes across 7 real ROMs in `EVIDENCE/`.
- **Synthetic CI Verification Command & Result:**
  - `python3 -m py_compile tools/sh7058_cross_rom_scanner.py tools/test_sh7058_cross_rom_scanner.py tools/sh705x_rom_loader.py tools/nissan_sh705x_workbench.py tools/test_nissan_sh705x_workbench.py tools/sh705x_discovery_v2.py tools/test_sh705x_discovery_v2.py tools/romraider_ref_index.py tools/test_romraider_ref_index.py tools/romraider_xml_export.py tools/test_romraider_xml_export.py && python3 -m unittest -v tools/test_sh7058_cross_rom_scanner.py tools/test_nissan_sh705x_workbench.py tools/test_sh705x_discovery_v2.py tools/test_romraider_ref_index.py tools/test_romraider_xml_export.py`
  - Result: **Ran 33 tests in 5.059s — OK** (exit code 0).
- **Controlled Golden Corpus Verification Command & Result (`/tmp/sh705x_golden_validation`, zero workspace writes):**
  - `python3 tools/run_golden_corpus_validation.py --out-dir /tmp/sh705x_golden_validation` (exit code 0):
    - Reference index built from 2 A2Ls + 2 XMLs + 7 donor ROMs + `WO70017_DONOR_METADATA.tsv` (`24,965` A2L addresses, `448` XML addresses, `12,555` WO70017 rows, `998` payload hashes, `6` code hashes).
    - All 7 pinned golden ROMs passed strict preview XML validation (`xml_valid=True`, `target_verified_count=0`):
      - `VERSA f501.bin` (`8CMCKRN5`/`SH705822N`): `34` helpers, `377` baseline calls (`+3` enhanced), `2,739` scalar candidates, `183` XML tables, `2` code twins, EL19A `INDEX/` `available`, `168` overlaps vs `EL19A_release1_conservative.xml` with **0 geometry disagreements**; multi-source EL19A reconciliation surfaced `374` addresses (`95` XML name, `249` disposition, `1` geometry conflicts).
      - `23710-EL13A-08-C11-MR18DE-CVT.bin` (`8CMCKRN5`/`SH705822N`): `34` helpers, `377` calls, `185` XML tables, `2` code twins, `INDEX/` gated (`rom_hash_mismatch`).
      - `CF48D.bin` (`6ZV5UN11`/`SH705823N`): `34` helpers, `375` calls (`+4` enh), `170` XML tables, `45` address overlaps vs `EVIDENCE/CF48D.xml` (inherited `<rom base="A2L">` child XML), `INDEX/` gated (`rom_hash_mismatch`).
      - `Nissan Tiida_C12W_3DD9A_705828N.bin` (`0KHDCFDZ7`/`SH705828N`): `37` helpers, `753` calls (`+1` enh), `300` XML tables, `INDEX/` gated (`rom_hash_mismatch`).
      - `E1BR20E.dat` (`9CMCVAPD31`/`SH705520N`): `36` helpers, `347` calls (`+3` enh), `148` XML tables, `INDEX/` gated (`rom_hash_mismatch`).
      - `Nissan_Qashqai_...zip` (`1TRKH1HN6`/`SH705828N`, 2 MiB): `37` helpers, `603` calls (`+2` enh), `240` XML tables, `INDEX/` gated (`rom_hash_mismatch`).
      - `unknown_EM62B_SH7055.bin.zip` (`1CMC7QPD401`/`SH705519N`): `34` helpers, `338` calls, `152` XML tables, `INDEX/` gated (`rom_hash_mismatch`).

---

## Known Limitations & Operational Notes
- Generated preview XML bundles (`*.preview.xml`) conservatively assign `Raw_*` identity scalings and `provisional_donor_lead` / `unknown_raw_only` semantic confidence unless explicit target-side proof exists; manual RomRaider review is still required before promoting definitions into `CALIBRATIONS/`.
- Child RomRaider XML definitions (`<rom base="A2L">`, e.g., `EVIDENCE/CF48D.xml`) inherit table geometry/scaling from their base XML and do not repeat dimensions inline.
- Unrelated legacy test files outside CI (`tools/test_rom_access_indexer.py`, `tools/test_wo_registry.py`) and queued `WO70022` in `CONTROL/active_work_orders.md` remain untouched.

## Rollout Complete
All planned rollout milestones (**Milestones 0–5**) are complete and verified. To re-run ordinary synthetic CI checks locally, run the CI command above; to run full real-ROM golden corpus verification into a scratch directory outside `CALIBRATIONS/`, run:
`python3 tools/run_golden_corpus_validation.py --out-dir /tmp/sh705x_golden_validation`
