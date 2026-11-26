# EL19A RomRaider Definition — Release 1 Plan

**Objective:** deliver a conservative, useful RomRaider definition for the exact EL19A `f501.bin` / FID `8CMCKRN5` ROM. Release 1 is a practical calibration-display deliverable, not a claim that every ECU calibration function has been semantically reverse-engineered.

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
| **INCLUDE — RAW/PROVISIONAL** | Address/extent, storage and geometry are supported. Use a generic non-misleading name and raw scaling where units/conversion/function remain unresolved. A sample-index axis may be used only when clearly labelled as an index and when the display is not misleading. |
| **EXCLUDE** | Address/extent, storage, geometry, required axis representation or a material representation conflict is unresolved. Record the reason. |

An unresolved physical function does not automatically exclude an object. Raw/provisional entries are not thereby tune-ready. Never infer physical units or query axes from donor labels, shape, curve resemblance or numerically plausible results.

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
- Do not present raw/provisional objects as semantically established or tune-ready.
- Do not invent axes, units, breakpoints, scaling or names.
- No live-vehicle testing.


## Owner integration checkpoint — 2026-11-26

The selected V58 baseline is reconciled against the 261-row consultant scope matrix. The owner-corrected matrix is `CALIBRATIONS/RELEASE1_SCOPE_MATRIX_R1.csv` (2 ESTABLISHED / 252 RAW-PROVISIONAL / 7 EXCLUDE). The separate successor `CALIBRATIONS/EL19A_release1_conservative.xml` is built and structurally checked; the baseline is unchanged. Findings `FND-000016/017` and `REC-000019/020` capture the new material interpretations. See `CALIBRATIONS/EL19A_release1_conservative_manifest.md` for hashes and the explicit validation boundary. RomRaider desktop import and visual checks remain pending; do not describe the candidate as a RomRaider-validated final release.
