# SH705x ROM Tool — Existing Workbench Integration Plan

**Status:** Planning update v0.1 — reuse and integration requirements identified; implementation not authorized  
**Date:** 2026-11-26  
**Parent plan:** [SH705X_ROM_TOOL_PLAN.md](SH705X_ROM_TOOL_PLAN.md)  
**Operational authority:** `CONTROL/active_work_orders.md`, `CONTROL/WORKER_PROTOCOL.md`, `CONTROL/INTEGRATION_STATUS.md`

## 1. Purpose and architectural decision

Increase the value of the existing `tools/nissan_sh705x_workbench.py` by connecting repository capabilities already built and used for EL19A analysis. Do not create duplicate scanners, reader indexers, diagnostic analyzers or calibration inventories.

The workbench should evolve toward a thin command layer over reusable analysis modules and evidence adapters. It should not become the location where every capability is reimplemented. Existing standalone tools remain independently usable during incremental migration.

The five workstreams below are planning priorities. The current architecture work orders WO70020–WO70022 remain unchanged and retain their FIFO positions. This document does not authorize code or artifact edits.

## 2. Verified existing capabilities and exact integration points

### 2.1 Workbench entry points

Current `tools/nissan_sh705x_workbench.py` is 1,023 lines and exposes four main commands:

| Function | Current role | Integration role |
|---|---|---|
| `load_any_rom()` (around line 137) | Loads BIN, ZIP, S19, Intel HEX and Nissan Consult DAT | Retain as a candidate format-loader source; migrate/centralize only after behavior and integrity rules are tested |
| `rom_fingerprint()` (around line 165) | Size, hashes, reset vector, CPU/FID tags | Shared ROM identity service |
| `parse_a2l_rich()` (around line 191) | Limited A2L symbol/measurement/conversion extraction | Replace or wrap with the planned relational A2L parser; avoid address-only symbol dictionaries |
| `load_csv_addr_map()` (around line 250) | Address-keyed CSV rows | Generic input adapter with duplicate-address/conflict preservation |
| `summarize_tables()` (around line 290) | Aggregates helper calls by table address | Keep as a derived view, not the canonical per-call evidence record |
| `cmd_scan()` (around line 562) | Scans and emits aggregated table TSV/JSON | Reuse scanner per-call export, run manifest and optional evidence providers |
| `cmd_audit()` (around line 613) | Compares reader-backed tables with one XML, catalogue and one scope matrix; loads selected variants/A2L leads | Multi-definition reconciliation and optional static/variant/diagnostic adapters |
| `cmd_inspect()` (around line 734) | Inspects a table/function/RAM address; performs aligned 32-bit literal search | Add indexed RAM/ROM access, GBR and downstream-consumer context |
| `cmd_diff()` (around line 865) | Same-address/relocated table comparisons and raw byte clusters | Optional variant-specific evidence and structured output |
| `main()` (around line 980) | Defines command-line interfaces | Add explicit optional inputs/output paths without making external evidence mandatory |

The current command implementations are useful orchestration boundaries. Avoid expanding all logic inside these functions.

### 2.2 Existing scanner export — reuse, do not duplicate

`tools/sh7058_cross_rom_scanner.py` already contains:

- `build_scan_export()` (around line 546), which builds JSON-safe helper, per-call and per-table records.
- `write_machine_exports()` (around line 786), which writes a combined JSON evidence record and per-ROM calls/tables/helpers TSV companions.
- CLI flags `--json-out` and `--tsv-dir` (around lines 848–849).

The call-level record includes exact call PC, call instruction/form, helper, helper kind, candidate table and axes, data type/width, dimensions, raw R4/R5/R6 values, target register/load/delay-slot context, table/axis span and hash information, resolution status, and bounded instruction context. It also stores argument-evidence limitations.

**Known limitations must remain explicit:** the caller start is a nearest-prologue heuristic, not a proven function boundary; register values come from a bounded linear window and delay slot, not full control-flow analysis; query source/register/width/signedness, complete pre-call transform, interpolation/clamp contract, result register and downstream consumer are not established by this exporter.

The scanner JSON run metadata already records container and decoded-ROM hashes, scanner source hash, Python version and command line. It does not yet constitute the complete external run manifest required for WO70006: output hashes, complete stdout/stderr capture and a stable report of all generated artifact identities still need to be added or wrapped.

**Decision:** workbench `scan` and `audit` should call or consume this existing exporter through a stable interface. Do not build a second per-call scanner. Enhance the current export only where a specific WO70006 field or tested consumer needs it.

### 2.3 Static access and index resources

Existing resources:

- `tools/rom_access_indexer.py` — `run_indexer()` (around line 175), returns resolved and unresolved access rows and PC-concordance metrics. It verifies a fixed EL19A ROM MD5 and exact listing SHA-256 before analysis.
- `tools/build_static_indices.py` — `parse_listing()` (around line 65), `full_rom_analysis()` (around line 225), `write_function_gbr_map()` (around line 524), `write_catalog_summary()` (around line 564), and CLI `main()` (around line 655). It creates function/GBR and 179-table consumer indices. It also enforces fixed EL19A ROM/listing identities.
- Existing generated datasets include `INDEX/function_gbr_map.tsv` and `INDEX/catalog_179_consumer_summary.tsv`.

These are valuable EL19A evidence sources but are not yet generic SH705x backends. They depend on a pinned ROM/listing and EL19A catalogue semantics.

**Integration requirements:**

1. Add optional access-index and static-index adapters to `inspect` and `audit`.
2. Support reuse of already-built indices only after validating their ROM hash, listing hash, catalogue hash where applicable, schema/version and generation command.
3. Treat absent or stale indices as unavailable; never silently reuse them or make ordinary `inspect` unexpectedly run an expensive full analysis.
4. Preserve unresolved access rows and method limitations alongside resolved accesses.
5. Refactor hard-coded EL19A integrity expectations into an explicit project/profile validation layer only in a separately authorized implementation task; do not weaken identity checks merely to make the tools appear generic.
6. Distinguish raw access xrefs, GBR mapping, semantic RAM labels and catalogue consumer summaries. They are complementary evidence, not interchangeable proofs.

High-value initial consumers include the bidirectional transfer pairs at `0x0F712/0x10F8A`, the candidate `0x0AFF2/0x0E5E8` pair, and investigations that need to connect table lookups to downstream RAM readers. Their use is as investigation context, not automatic semantic promotion.

### 2.4 Calibration-definition and scope reconciliation

Current available sources include:

- `CALIBRATIONS/EL19A_release1_conservative.xml`
- `CALIBRATIONS/RELEASE1_SCOPE_MATRIX_R1.csv`
- `CALIBRATIONS/RELEASE1_SCOPE_MATRIX.csv`
- `CALIBRATIONS/EL19A_WO65325_provisional_tiered_v1.xml`
- `CALIBRATIONS/EL19A_best_guess_provisional_full_definition.xml`
- `CALIBRATIONS/discovered_tables_catalog.csv`
- `CALIBRATIONS/candidate_register.csv`

The two scope matrix files are not interchangeable or byte-identical. They contain differing dispositions and interpretation text for multiple addresses, including `0x0848A`, `0x08550`, `0x0F3D6` and `0x0B012`. For example, R1 records the provisional working-label/conversion approach selected for the current successor while the other matrix contains raw/provisional or corrective recommendations. The audit must preserve this discrepancy and must not assume a source precedence solely from the filename.

**Decision:** create a source-by-source object reconciliation view. Do not combine all inputs into one boolean `in_scope` or let a later file silently overwrite an earlier decision.

Suggested per-object fields:

`address, source_id, source_path, source_hash, object_name, geometry, storage_type, extent, axis, scaling, disposition, evidence_links, source_status, conflict_group, reconciliation_status`.

Required comparison statuses include: present, absent, geometry conflict, type/extent conflict, conversion conflict, axis conflict, disposition conflict, candidate-only, and unresolved.

Preserve owner-directed presentation exceptions such as provisional `Rpm_x25` as separately tagged display decisions. Do not reinterpret them as proof of firmware query source or physical units. Preserve the distinction between selected best-guess working definitions, conservative Release 1 decisions, tiered definitions and candidate hypotheses.

### 2.5 Diagnostic and variant evidence adapters

Existing diagnostic script:

`tools/extract_diagnostic_rosetta.py` includes:

- `build_obd_mode01()` (around line 399)
- `build_consult_mode22()` (around line 465)
- `build_dtc_198_and_writers()` (around line 559)
- `build_sh7058_mmio_census()` (around line 902)

It is tied to the pinned EL19A ROM/listing, hard-coded memory regions, DTC structures, helper addresses and Nissan-specific data conventions. Reuse its verified outputs/functions through a diagnostic provider, not as a generic processor backend.

Existing variant script:

`tools/analyze_el19a_el13a_diff.py` contains `scan_listing_references()` (around line 94), `classify_variant_pattern()` (around line 174) and a main analysis pipeline. Its current checks enforce exact EL19A/EL13A identities, 1 MiB equal image sizes, expected checksum validity and a fixed 3,708-byte difference count/range. This is a valuable EL19A-vs-EL13A analysis, not a general arbitrary-ROM differ.

**Integration requirements:**

- Offer optional diagnostic and variant context in `audit`, `inspect` and `diff`.
- Preserve each provider's own source ROM hash, listing hash, code version, assumptions and output artifact identities.
- Show variant differences as candidate leads only. A changed address, differing payload, diagnostic label or donor symbol does not prove calibration semantics on EL19A.
- Keep OBD PID, Consult CID, DTC, MMIO, calibration and variant-diff domains separately typed.
- Missing optional inputs should result in an explicit unavailable status, not failure of ordinary core commands.

### 2.6 Regression-test resources

Existing tests:

- `tools/test_rom_access_indexer.py` has synthetic instruction/branch/pointer tests and optional real-ROM regression checks.
- `tools/test_sh7058_cross_rom_scanner.py` exercises helper-call extraction, per-call JSON export, exact payload cross-ROM comparison and generated TSV outputs.
- `tools/test_wo_registry.py` tests work-order governance; it is not a substitute for ROM-workbench behavior tests.

Add a dedicated workbench suite, proposed name `tools/test_nissan_sh705x_workbench.py`, before or alongside integration. It should use small in-memory ROM slices and temporary XML/CSV/A2L fixtures. Do not require protected project ROM/LST/A2L files for ordinary unit tests.

Minimum test topics:

- Existing ROM loader and fingerprint behavior on synthetic inputs, including invalid/truncated containers.
- `cmd_scan` per-call export wiring and unresolved/null serialization.
- Run-manifest source and output hashes, deterministic serialization and captured stdout/stderr.
- Multiple calls to one base, conflicting geometry for one base, duplicate symbol/definition addresses.
- Multiple scope matrices and definitions with deliberate disagreement.
- Static-index hash mismatch rejection, stale/missing-index behavior and unavailable optional provider behavior.
- Diagnostic and variant evidence remains explicitly typed and cannot overwrite target evidence.
- Workbench behavior remains consistent with the cross-rom scanner tests and access-indexer tests.

Tests should assert both positive and negative controls: a donor-only or variant-only match must not be labelled target semantic proof.

## 3. Recommended implementation sequence

This order is the integration sequence, not new work-order allocation. Detailed implementation WOs should be generated after WO70020–WO70022 are reconciled.

| Sequence | Upgrade | Priority / gate |
|---|---|---|
| 0 | Establish dedicated workbench synthetic fixtures and baseline regression tests | Prerequisite before refactoring |
| 1 | Reuse scanner per-call exports in workbench `scan`/`audit`; complete the attributable run manifest | Highest functional priority; WO70006 raw-output acceptance gate |
| 2 | Add optional, hash-validated RAM/ROM access-index and static-index adapters to `inspect`/`audit` | High value; existing EL19A indices first |
| 3 | Add multi-definition / dual-scope-matrix reconciliation | High value; preserve conflicts and owner display exceptions |
| 4 | Add optional diagnostic-rosetta and variant-diff evidence providers | Later integration; candidate-generation only |

Testing can begin in parallel with architecture work, but source integration must wait for a specific implementation WO and the shared data/interface decision.

## 4. WO70006 interaction

WO70006 remains BLOCKED until its required complete raw artifacts are supplied and read back. The separate scanner's existing per-call exporter materially reduces the work needed, but its presence alone does not satisfy the gate.

A WO70006-capable package should include:

- Per-input JSON export with helpers, every call row (resolved and unresolved), unique tables and cross-ROM comparison details where applicable.
- Calls/tables/helpers TSV companions, with unresolved values left null rather than guessed.
- A run manifest that pins the original input file and decoded image hashes, tool source hash/version, command line, Python/runtime version and generated artifact hashes.
- Complete stdout/stderr or a captured command log with explicit exit status.
- Reproducible reconciliation from call rows to unique table inventory and the selected XML/scope/catalogue inventories.
- An explicit field-level statement of what remains heuristic or unresolved: caller boundaries, query provenance, pre-call transforms, interpolation/clamp behavior, result registers and downstream consumers.

Do not unblock WO70006 merely because aggregate reports or the scanner's current JSON exist. The exact required artifacts and reconciliation still need to satisfy its registered acceptance conditions.

## 5. Architectural constraints and non-authorizations

- Keep the modular direction: standalone commands over shared libraries and optional evidence adapters.
- Do not import EL19A-specific hard-coded addresses, expected hashes or Nissan semantic labels into generic SH705x core logic.
- Do not remove fixed identity validation from existing tools without a profile-based replacement and regression coverage.
- Do not run heavyweight static-index generation automatically as a side effect of interactive inspection.
- Do not collapse donor A2L, exact-payload, variant-difference, diagnostic, screenshot and target-reader evidence into a single confidence or semantic field.
- No implementation, dependency installation, ROM/LST/A2L modification, calibration XML/workbook/catalogue/scope-matrix edits, Findings changes, patching or flashing is authorized by this plan.

## 6. Source anchors reviewed

- `tools/nissan_sh705x_workbench.py` — `load_any_rom`, `rom_fingerprint`, `parse_a2l_rich`, `load_csv_addr_map`, `summarize_tables`, `cmd_scan`, `cmd_audit`, `cmd_inspect`, `cmd_diff`, `main`.
- `tools/sh7058_cross_rom_scanner.py` — `build_scan_export`, `write_machine_exports`, `extract_calls`, scanner CLI.
- `tools/rom_access_indexer.py` — `run_indexer`, fixed ROM/listing identity validation.
- `tools/build_static_indices.py` — `full_rom_analysis`, `write_function_gbr_map`, `write_catalog_summary`, fixed identity validation.
- `tools/extract_diagnostic_rosetta.py` — OBD, Consult, DTC/writer and MMIO builders.
- `tools/analyze_el19a_el13a_diff.py` — fixed-pair variant analysis.
- `tools/test_rom_access_indexer.py`, `tools/test_sh7058_cross_rom_scanner.py`, `tools/test_wo_registry.py`.
- `CALIBRATIONS/RELEASE1_SCOPE_MATRIX.csv`, `CALIBRATIONS/RELEASE1_SCOPE_MATRIX_R1.csv`, `CALIBRATIONS/EL19A_WO65325_provisional_tiered_v1.xml`, `CALIBRATIONS/EL19A_best_guess_provisional_full_definition.xml`, `CALIBRATIONS/candidate_register.csv`.
