# Calibration Findings / Reconciliation Index

**Status:** SEEDED — INITIAL HIGH-VALUE BATCH MIGRATED; ONGOING  
**Authority:** This index is the entry point for calibration interpretation. See [README](README.md) for the full schemas and the mandatory XML build gate.  
**Index revision:** WO65548 initial seed, 2026-11-24.

## Record schema

Finding records use the stable IDs `FND-000001` onward and carry: status; semantic layer; exact addresses, storage width and geometry; exact observations with ROM/LST PCs and mechanics; conclusion; confidence and evidence grade kept distinct; source class and exact WO/report anchors; related finding/reconciliation IDs; affected inventory/XML objects; and explicit unknowns, contradictions, stop boundary and no-repeat notes.

Reconciliation records use `REC-000001` onward and carry: affected address/object; old interpretation and source; corrected/current interpretation and supporting finding(s); reason and discriminating evidence; confidence; status; and affected inventory/XML references. Superseded interpretations are retained as history, never erased. Full normative text is in [README](README.md) §§Finding record minimum fields and Reconciliation record minimum fields.

## Address lookup

| Address / object | Current finding(s) | Reconciliation(s) | One-line disposition |
|---|---|---|---|
| `0xE678–0xE687`, `0xE688–0xE697` | `FND-000001` | `REC-000001` | User-finalized RPM display presentation retained for these two tables only; timer-derived implicit-grid query remains a separate runtime fact. |
| `0xF3D6`/`0xF3C6`, `0xF3DE`/`0xF3CE` | `FND-000002` | `REC-000002` | Two distinct generic 8-point UBYTE limit schedules with target-proven ×13/clamp mechanics; donor TVO units and main/sub labels not promoted. |
| `0x9B2E`, `0x9C2E`, `0x9DAE`; axes `0xE4AC`/`0xE4BC` | `FND-000003` | `REC-000003` | Three distinct placements on fixed ROM axes; `9C2E`/`9DAE` payload aliases cancel in the paired differential; ignition/knock labels provisional. |
| `0x848A`, `0x848B`; donor `0x90EA` | `FND-000004` | `REC-000004` | `848A/B` paired user-verified donor mapping; separate donor `mDDPAPO` and screenshot scalar roles; numeric coincidence does not merge them. |
| `0x0E904`; axis `0x0FA62` | `FND-000005` | `REC-000005` | XML v3 static `0–240` axis is wrong; future build uses explicit UWORD axis at `0x0FA62`; no XML edit in this revision. |

## Current priority migrations

- [x] User-finalized Rev Hang screenshot interpretation for E678/E688, preserving the screenshot-finalized RPM presentation while retaining timer-derived ROM query mechanics as a separate runtime fact.
- [x] F3D6/F3DE query, axes and clamp findings.
- [x] 9B2E/9C2E/9DAE raw UBYTE and runtime alias disposition.
- [x] High-value axis correction at `0x0E904`/`0x0FA62`.
- [x] Correction to provisional scalar labels at `0x848A/0x848B`.
- [ ] Next high-value A2L synthesis batch: `0x0F406` NTC candidate and `0x0B756/0x0B7D6` scale-compatible analogues.
- [ ] E904/E914/E934 “no V6 counterpart established” dispositions and A272 axis correction.
- [ ] Broader geometry corrections only when they change an axis, unit, dimension, scaling, label or XML disposition. Routine RAM-cell endpoint traces remain outside this index.

## Record locations

- Findings: `FINDINGS/records/FND-000001.md` … `FINDINGS/records/FND-000005.md`
- Reconciliations: `FINDINGS/reconciliations/REC-000001.md` … `FINDINGS/reconciliations/REC-000005.md`
- Evidence references: `FINDINGS/evidence/EVD-xxxxxx.md` (schema reserved; no EVD records created in this revision)

## Migration coverage and cross-links

| Finding | Anchored source reports | Affected inventory/XML objects |
|---|---|---|
| `FND-000001` | WO65548, WO65012 §Results, WO65113 §§2–3, WO65095 closeout and erratum, WO65136, WO65141 | `candidate_register.csv` E678/E688; provisional XML lines 36/58 |
| `FND-000002` | WO64832 §§Stage 3–4, WO65013, WO65141 §1/§4, WO64912 | `candidate_register.csv` F3D6/F3DE; provisional XML lines 89/103 |
| `FND-000003` | WO64970, WO64968, WO64848 closeout, WO65109, WO64913 | `candidate_register.csv` 9C2E/9DAE; provisional XML lines 134/139/144 and 889–909 |
| `FND-000004` | WO64831 §§3–4/§9, WO65014 user correction, WO65112 errata, WO65141 | provisional XML lines 80/83 |
| `FND-000005` | WO65124 §6, WO65058, WO65162 I-04, catalogue row `0x0E904` | `discovered_tables_catalog.csv` `0x0E904`; provisional XML lines 319/918 |

**Inventory pointer status:** current calibration CSVs have no stable finding-ID column. No CSV, XML, workbook, catalogue, ROM, LST, A2L or script was edited in this revision; this index provides the address-to-inventory/XML crosswalk. Additive CSV pointers may be introduced only under a later explicitly authorized format change.

## Conflicts resolved without erasing history

- E678/E688 display-axis presentation versus unproven runtime RPM conversion: separated into user-finalized presentation and runtime mechanics (`REC-000001`).
- F3D6/F3DE donor TVO conversions versus target ×13/clamp path: donor semantics retained as comparison only (`REC-000002`).
- 9B2E dynamic-axis label and XML ignition/knock overlays versus fixed GBR-rooted axes, identical `9C2E`/`9DAE` payloads and bit-7 disposition (`REC-000003`).
- 0x848A/B, mDDPAPO and the single 52.34% screenshot scalar: kept as three distinct roles (`REC-000004`).
- E904 static inline axis versus verified explicit `0x0FA62` axis and interpolation (`REC-000005`).

## Promotion rule

Every material change to calibration interpretation must create or update a finding record and, when it changes a prior interpretation, a reconciliation record. WO reports must link to these IDs. The calibration inventory must link back to the findings supporting its current values. Structural evidence grade is never semantic confidence, and donor names/units/conversions are never promoted without target-side evidence. A missing inventory link means the claim is not yet promoted by this system.
