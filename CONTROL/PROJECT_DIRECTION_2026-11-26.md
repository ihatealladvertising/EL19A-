# EL19A Project Direction and Priority Plan — 2026-11-26

**Status:** Current project guidance; not a work-order queue and not a substitute for individual evidence records.  
**Repository:** `ihatealladvertising/EL19A-`, branch `main`  
**Source snapshot reviewed:** `0f5e21718d17655a01c57d2bb24e499ea1232d60`  
**Authority:** `CONTROL/active_work_orders.md` controls WO lifecycle and assignments; `CONTROL/WORKER_PROTOCOL.md` controls worker execution; `CONTROL/INTEGRATION_STATUS.md` controls shared-main publication.

## Objective

Finish a useful, conservative RomRaider definition for the EL19A / MR18DE MT ROM by translating reliable target-ROM structure into definitions without making physical names, units or conversions a prerequisite for every entry. Publish reader-verified geometry and non-misleading raw/provisional representations where appropriate. Reserve stronger semantic claims for target-side evidence that actually supports them.

The definition should become more complete and more accurate in small verifiable releases. Avoid endless investigations into internal status networks when those paths have no demonstrated calibration or actuator consequence.

## Current execution — preserve the live queue

At the reviewed repository snapshot, the live register showed no ACTIVE WO and these five READY assignments:

| Lane | FIFO |
|---|---|
| Worker 1 | `WO70008` |
| Worker 2 | `WO70007 → WO70010` |
| Worker 3 | `WO70009 → WO70011` |

These assignments are already registered. Do not reassign, reorder, duplicate or pause them to implement this plan. Workers may start their assigned work immediately; a publication lock only pauses writes to shared `main`, not technical work or local pending preparation.

- **WO70007:** correct the Release 1 `0x0FEE0` object to the target-required 64 UWORD big-endian entries / 128-byte extent and verify the complete payload. Preserve the unresolved query grid. A 0–63 sample-index display is safer than an unverified physical breakpoint grid.
- **WO70008:** target-side validation of the dual-donor `mQTBL` structural lead at `0x0FEE0`; donor identity remains a hypothesis.
- **WO70009:** verify target-side geometry, axes and caller constellation for the `0x0D856` and `0x0C2D6` 8×8 UWORD maps; donor names remain hypotheses.
- **WO70010:** verify the `0x0F3EE` 16-point UBYTE curve and its reader/query/axis before considering the `mTTWISC` donor candidate.
- **WO70011:** reconstruct the six-call constellation around `0x77616`. Its report's initial five-address list conflicts with the workbench documentation's six-address list, which includes `0x0ECEE`; reconcile from target code rather than forcing a one-to-one mapping.

Do not create placeholder work merely to keep lanes occupied. Create the next WO only after a lane becomes available and a distinct, bounded payoff and dependency are clear.

## Next priority after the five allocated WOs

### 1. Consolidate proven corrections into a controlled Release 1.1

This is the shortest route to making the current definition more accurate using evidence already in the Findings system. Reconcile each item against the actual current XML, scope matrix, catalogue and manifest before editing; do not infer that a particular file is still stale without checking it.

- **`0x0FEE0`:** WO70007 owns the immediate XML/Release 1 correction. Integration must verify 64 UWORD cells and extent `0x0FEE0–0x0FF5F`. Do not publish the old `fixed_0_2048_63488` axis as established; exact breakpoints remain unresolved. The complete second half of the ROM payload had not been independently read in FND-000021.
- **`0x0ED64` / `0x0EDA0`:** FND-000018 and REC-000022 establish two 16×1 UBYTE thresholds using the same rescaled coolant-temperature query `U8[FFFF84B8]`, fixed raw query grid `0,16,…,224`, and clamp at query 240. There is no RPM operand. Reconcile the axis/query metadata and any remaining misleading RPM labelling. Keep raw values; do not invent °C or physical threshold units.
- **`0x0EE68` / `0x0F01C`:** FND-000019 and REC-000023 establish two 16×1 UBYTE curves on the same `FFFF84B8` coolant-temperature query and no RPM operand. Row 029's axis/query description is affected. Important exception: REC-000023 expressly distinguishes the unsupported physical RPM interpretation from the owner-directed provisional `Rpm_x25` display choice. Do not silently remove or change that presentation choice; flag it for explicit owner decision while correcting factual query metadata.
- **`0x0F02C`:** FND-000019 establishes a separate four-entry UBYTE bin-floor table, values 38/48/54/62, indexed 0–3. It is not a continuation of `0x0F01C`. It has no current XML/scope/catalogue object; consider a separate raw/provisional entry with an explicit bin-index axis.
- **`0x0DE6E` / `0x0E2ED`:** FND-000022 and REC-000025 establish two separate 16-point UBYTE vectors that each act as the other's axis/data through reciprocal calls. If included, preserve both objects, cross-reference the other vector as the axis and visibly mark them linked/edit-coupled. Do not assign permanent data-vs-axis roles, physical units or names. Treat the outside caller claim `0x05AB5A` as unverified; the recorded target callers are `0x05B23A` and `0x05B26A`. This pair is a later-release candidate, not a reason to delay correction of Release 1.

The known evidence is in `FINDINGS/records/FND-000018.md` through `FND-000022.md` and `FINDINGS/reconciliations/REC-000022.md` through `REC-000025.md`. Preserve their distinctions between target fact, owner presentation decision and unresolved physical meaning.

### 2. Unblock WO70006 only with complete, attributable raw outputs

WO70006 remains BLOCKED at its raw-output gate. The unified workbench is useful but does not, as documented, export complete per-call register/argument reconstruction: `scan --tsv/--json` gives table summaries with aggregated call PCs and axes; `audit --tsv` gives table-level rows; the A2L structural matcher writes console output and has no structured export flags. Do not treat aggregate metrics (293 bases, 115 reported omissions, 76 XML-only objects, cross-ROM counts) as a verified census without the underlying rows.

A sufficient follow-on package should preserve:
- full per-call rows: ROM hash, helper, exact call PC, enclosing function, data base, geometry, element type/width, byte extent, axis argument(s), query source/register/width/signedness, pre-call transform, interpolation/clamp contract, result register and any actually traced immediate consumer;
- explicit unresolved/null fields where the current implementation cannot reconstruct a value—never guessed register provenance;
- a per-input provenance manifest: repository path, exact ROM/A2L/tool hashes, command line, runtime version, output file names and hashes, and complete stdout/stderr;
- a reproducible cross-check from per-call rows to unique table inventory and to the XML, scope matrix and catalogue.

If a full exporter is too large, define the smallest complete bounded output that satisfies WO70006's acceptance gate, then continue manual bounded verification where necessary. Keep WO70006 BLOCKED until its required artifacts exist and can be read back.

### 3. Verify the next strong dual-donor lead: `0x0AFF2` / `0x0E5E8`

The workbench documentation reports a dual V6/Juke structural lead linking `0x0AFF2` (4×4 UBYTE) and `0x0E5E8` (8×1 UBYTE) to donor symbols `mTDATDDS` / `mTDATDPRE`. This is a high-value candidate for a new bounded target-side investigation after the current lane work. First confirm the exact source inputs and declarations; then verify target readers, query/axis roles, extent, and first consumer. Do not promote donor names or units from consensus alone.

### 4. Pivot toward fuel/air and physical outputs

The `0x0F712` / `0x10F8A` pair is reader-verified as a bidirectional 32×1 UWORD transfer pair (FND-000014 / REC-000016), but the MAF/airflow physical interpretation and capture provenance remain unresolved. `FFFF1066` is a computed internal result, not an established physical measurement. The next productive investigation should connect this input-side path toward load/fuel calculation and, separately, work backward from concrete injector, ignition-coil or other physical output writes to their calibration inputs.

Prioritize a bounded chain with a real endpoint over another open-ended survey of internal flags. Do not claim injector pulse width, AFR, trims, true ignition degrees, knock retard or actuator control until target code establishes it. A proven generic/raw calibration object can still be useful before all those physical questions are solved.

### 5. Variant differences are a candidate generator, not semantic evidence

The current workbench documentation reports 37 same-address payload differences between EL19A and EL13A and multiple relocated/non-trivial differences versus 8W83B. Treat those counts as tool-summary leads until per-table provenance is available. Candidate addresses reported outside the current WOs include `0x0AFF2`, `0x0E5E8`, `0x0E658`, `0x0ED8C`, `0x0EE48`, `0x10CC2`, `0x12A4E` and `0x12D18`. A difference is not automatically variant-specific or meaningful; verify helper geometry, payload and target-side use before prioritizing it.


## Tooling integration clarification — 2026-11-26

The current workbench and the separate cross-ROM scanner must be distinguished when assessing WO70006 and future tool work.

- `tools/nissan_sh705x_workbench.py` remains aggregate-oriented at `cmd_scan()` and `cmd_audit()`: its TSVs summarize unique tables and aggregate call PCs. It does not yet expose the scanner's complete call-level records through the workbench interface.
- `tools/sh7058_cross_rom_scanner.py` already implements `build_scan_export()` and `write_machine_exports()`, including per-call, per-table and per-helper JSON/TSV outputs plus source/tool metadata. This is reusable capability and should be wired into the workbench instead of duplicated.
- The scanner export does not prove every call's semantics. Its caller-start field is a nearest-prologue candidate; register reconstruction is a bounded linear-window heuristic; query source, signedness, full transform, interpolation/clamp contract, result register and downstream consumer are not all established by that export.
- The output package still needs a complete external run manifest with hashes of all generated artifacts, complete command/log details and exit status. Merely finding the exporter in source does not satisfy WO70006's required raw-output gate. **WO70006 remains BLOCKED** until its actual registered artifacts and reconciliation are produced and verified.
- `rom_access_indexer.py` and `build_static_indices.py` can supply valuable RAM/ROM access, GBR and consumer context, but their current run paths verify a fixed EL19A ROM and listing. Use hash-validated cached indices or explicitly invoked EL19A providers; do not run full static analysis implicitly from every inspection command and do not present these tools as generic SH705x modules.
- `extract_diagnostic_rosetta.py` and `analyze_el19a_el13a_diff.py` are useful diagnostic/variant evidence providers, but their fixed addresses, pinned source identities and assumptions make them EL19A-specific today. Their outputs should be optional, separately typed candidate context, not target calibration proof.
- Reconcile `RELEASE1_SCOPE_MATRIX.csv`, `RELEASE1_SCOPE_MATRIX_R1.csv`, both current definition baselines, the tiered XML and `candidate_register.csv` as distinct sources. Conflicting scope dispositions, provisional working conversions and owner-selected presentation exceptions (including `Rpm_x25`) must remain visible rather than being silently overwritten.

The detailed source-level integration requirements and recommended sequence are in [SH705X_WORKBENCH_INTEGRATION_PLAN.md](SH705X_WORKBENCH_INTEGRATION_PLAN.md). This clarification does not change the live queue, WO70006 status, calibration definitions or protected evidence.


## Working evidence standard

Use a practical two-layer standard:

1. **Definition-ready structural fact:** address, storage type/width, extent, geometry, axis/query representation, and reader mechanics sufficiently establish a non-misleading raw/provisional RomRaider object. Physical naming or engineering units may remain unresolved.
2. **Semantic promotion:** a physical name, unit, conversion, strategy role or actuator consequence requires a target-side query and consumer path that supports that claim. Donor A2Ls, cross-ROM similarity, value shape and screenshots may guide discovery but do not substitute for target-side proof.

Do not let semantic uncertainty prevent a safe generic/raw definition when structural facts are adequate. Conversely, do not use a plausible name to conceal unresolved dimensions, axis or scaling. Preserve established user-directed presentation decisions as such, separately from firmware facts.

## What this plan does not do

- It does not change the live WO queue, priorities, ownership, or lifecycle.
- It does not close, reopen or unblock WO70006.
- It does not authorize changes to protected ROM/LST/A2L evidence, workbook, scanner source, or Release 1 files outside a separately scoped and authorized WO/integration batch.
- It does not make any calibration change suitable for use on a vehicle. All work remains static research/definition engineering.

## Source anchors

- `CONTROL/active_work_orders.md`, current lane table and operational frontier.
- `CONTROL/WORKER_PROTOCOL.md` and `CONTROL/INTEGRATION_PROCEDURE.md`.
- `CONTROL/WO70007.md`–`CONTROL/WO70011.md`.
- `FINDINGS/records/FND-000014.md`, `FND-000018.md`, `FND-000019.md`, `FND-000021.md`, `FND-000022.md`.
- `FINDINGS/reconciliations/REC-000016.md`, `REC-000022.md`–`REC-000025.md`.
- `tools/nissan_sh705x_workbench.md` and `tools/a2l_structural_matcher.md`.
