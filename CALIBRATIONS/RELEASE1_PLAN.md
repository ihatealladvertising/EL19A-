# EL19A RomRaider Definition — Release 1 Plan

**Objective:** deliver a useful, editable RomRaider definition for the exact EL19A `f501.bin` / FID `8CMCKRN5` ROM using the best available target-side evidence and clearly identified best guesses. Release 1 is an iterative working definition: build with plausible names, categories and conversions, then refine them as investigation and RomRaider review improve.

## Authoritative inputs

- **Target ROM:** `EVIDENCE/VERSA f501.bin`, 1 MiB, MD5 `46991697c502052752a2cabcb84c9e27`.
- **Engineering workbook:** `WORKBOOK/EL19A_Master_Reverse_Engineering_Workbook_V58_WO65114_ThinReferenceCloseout_2026-11-21.xlsx`.
- **Selected starting XML:** `CALIBRATIONS/EL19A_best_guess_provisional_full_definition.xml` (preserve unchanged; create a separate successor).
- **Current interpretation index:** `FINDINGS/INDEX.md` and the current records under `FINDINGS/records/` and `FINDINGS/reconciliations/`.

Do not use old V53 accounting as current V58 inventory. Do not silently substitute the tiered WO65325 or merged V3 files for the selected full-definition baseline.

## Release dispositions

| Disposition | Acceptance |
|---|---|
| **INCLUDE — ESTABLISHED** | Address/extent, storage, geometry, axes and displayed conversion are supported; any physical name/units used are supported. |
| **INCLUDE — PROVISIONAL** | Address/extent, storage, geometry and axis mechanics are sufficiently supported for display. Use the best available functional name/category and a plausible conversion where a defensible candidate exists. Treat these as working hypotheses, not verified facts; retain raw scaling where no useful conversion guess is available. |
| **EXCLUDE** | A material address, extent, storage, geometry or required axis representation conflict prevents a useful display. Record the reason. |

**Working rule:** unresolved semantics are a refinement target, not a reason to strip useful candidate names/conversions or hold the definition back. Preserve a clear provisional marker or status note and correct guesses as better evidence arrives. Do not invent ROM addresses, data extents, dimensions or reader/axis mechanics.

## Execution sequence

1. **Freeze the scope.** Reconcile the selected starting XML object list against V58 and the current Findings index. Produce an object-by-object matrix with source address, data type, extent, dimensions, axis source, scaling, supporting evidence and one of the three release dispositions.
2. **Resolve only release blockers.** Use existing ROM/LST reports and Findings first. Open a new bounded trace only when it can resolve an address, extent, geometry, axis, scaling, naming or inclusion blocker. Group related objects sharing the same reader/helper or evidence method into batch work orders.
3. **Construct a successor XML.** Preserve the selected baseline. Change only items justified by the scope matrix and supporting target-side evidence. Keep raw/provisional objects generic; remove or exclude misleading entries.
4. **Validate the successor.** Confirm RomRaider loads the file and that every included object reads the intended bytes, dimensions, orientation, axes and conversions against the exact target ROM.
5. **Publish the build manifest.** Record ROM hash, baseline XML path/hash, successor path/hash, Findings index revision, included/excluded object dispositions, unresolved semantic issues, and validation results.

## What is not a Release 1 prerequisite

- Full input/function/output/physical identity for every object.
- A first-consumer or actuator-sink trace for every table.
- Complete DTC, sensor-monitor, peripheral or option-byte reconstruction.
- Exhaustive discovery of every possible calibration object.
- Vehicle testing.

These may support later releases or be pursued where they resolve a concrete Release 1 blocker. They must not hold the first defensible definition hostage.

## Guardrails

- Do not edit the ROM, LST, A2Ls, workbook, evidence artifacts or discovery catalogue as part of Release 1 assembly.
- Do not overwrite the selected baseline XML; create a clearly named successor.
- Do not present provisional names or conversions as established facts. They are working hypotheses for iterative review, not a reason to omit an otherwise useful object.
- Do not invent axes, units, breakpoints, scaling or names.
- No live-vehicle testing.


## Owner integration checkpoint — 2026-11-26

The selected V58 baseline is reconciled against the 261-row consultant scope matrix. The owner-corrected matrix is `CALIBRATIONS/RELEASE1_SCOPE_MATRIX_R1.csv` (2 ESTABLISHED / 252 RAW-PROVISIONAL / 7 EXCLUDE). The separate successor `CALIBRATIONS/EL19A_release1_conservative.xml` is built and structurally checked; the baseline is unchanged. Findings `FND-000016/017` and `REC-000019/020` capture the new material interpretations. See `CALIBRATIONS/EL19A_release1_conservative_manifest.md` for hashes and the explicit validation boundary. Initial RomRaider ROM-load / definition-tree creation is USER-REPORTED PASS after duplicate-header removal; individual table rendering, axis/data spot-checks and full visual review remain pending. Do not describe all 254 objects as fully validated.


## RomRaider import checkpoint — 2026-11-26

The project owner reports that, after removing the duplicate XML declaration, the target ROM loads and the RomRaider definition tree displays many tables. The canonical GitHub successor was corrected to contain one XML declaration and read back successfully. Record this as a **user-reported initial import/tree-load PASS**; table-level rendering, axis/data spot-checks and full visual review of the 254 objects remain pending. See the updated build manifest and WO70003 owner integration checkpoint.


## Post-import matrix/XML audit correction — 2026-11-26

A post-import audit discovered that three entries describing implicit fixed grids also quoted their previous bad XML pointers. The generated XML had mistakenly retained those old pointers. The canonical successor has now been corrected: `0x0EFFC` uses a static UBYTE `0,32,…,224` Y grid; `0x1109A` and `0x12D98` use static UWORD `0,4096,…,61440` Y grids. All three stale ROM pointers (`0x08CD3`, `0x093F4`, `0x1170A`) have been removed. The final matrix/XML audit passed with 254 objects, 145 ROM-backed axes, 125 static axes and zero detected mismatches. Because this edit followed the owner's initial RomRaider tree-load report, reload the current canonical XML before continuing table-level verification.


## Owner-directed best-guess iteration — 2026-11-26

The project owner explicitly directed that the RomRaider definition be built with the best available guesses and refined from there. This supersedes the earlier conservative presentation rule that stripped provisional names and all unverified conversions to generic/raw displays.

The current successor restores the selected baseline's candidate functional names and useful category structure for all 254 included objects. It restores six candidate data conversions where the scope matrix records a best-guess scale: throttle-reduction percent, coolant minimum temperature, TVO degrees, percent-valued data, RPM ×25, and UWORD percent. These remain provisional; the XML's structural axes and dimensions retain the corrected target-side implementation.

RomRaider screenshot review:
- The 18-table spot-check sequence is covered by the repository captures.
- Captures 016–018 were superseded by fresh corrected views in Capture024.
- Capture023 confirms 0x11FC4 with X=0x128AE and Y=0x129EE.
- Capture024 confirms the corrected fixed grids for 0x0EFFC, 0x1109A and 0x12D98.
- Captures 019–021 cover the three 0x0E21A selector arrays; Capture022 covers 0x0E678 and 0x0E688.

Do not wait for full semantic closure of the remaining work orders before using or improving this definition. Continue the investigation in parallel and revise candidate labels, categories, scaling and axes as evidence warrants.


## Explicit provisional and shared-storage UI markers — 2026-11-26

All 252 provisional objects in the iterative best-guess successor use a visible `[P]` label prefix; the two established E678/E688 entries retain their user-finalized names. Functional categories and best-guess conversions remain enabled.

The 0x0CD56 / 0x0FEC0 reciprocal shared-storage lookup pair is marked `[P] [LINKED]` in RomRaider. The 0x0FEC0 curve values are the 0x0CD56 surface Y axis; row 0 of 0x0CD56 is the 0x0FEC0 curve query axis. Preserve both objects and consider both before changing either. See REC-000021.
