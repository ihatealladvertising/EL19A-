# Calibration Findings / Reconciliation Index

**Status:** SEEDED — TWO A2L SYNTHESIS BATCHES MIGRATED; ONGOING  
**Authority:** This index is the entry point for calibration interpretation. See [README](README.md) for the full schemas and the mandatory XML build gate.  
**Index revision:** `FND-000014` generic bidirectional 32-point UWORD transfer pair with physical domain unresolved, plus `REC-000016` split forward-query operand provenance (WO66047, 2026-11-25); `FND-000013` bit-publication split across a branch delay slot (WO65910, 2026-11-25); `FND-000012`/`REC-000013` GBR-relative address rule and four attribution corrections (WO65895, 2026-11-25); `FND-000011` donor-only ignition trimming/display and compensation context; `FND-000010`/`REC-000010` firmware-RAM band reconciliation (WO65811); `REC-000011` WO65808 initializer/publisher correction; and `REC-000012` WO65739 copy-helper extent erratum — the latter recorded 2026-11-24.

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
| `0x0F406` | `FND-000006` | `REC-000006` | Strong `mTTWN` donor candidate by geometry/output/context; `20 mV/count` is conditional on unknown board AVref; physical identity MED-LOW and unpromoted. |
| `0x0B756`, `0x0B7D6`; axes `0x0FCFC`/`0x0FD3C` | `FND-000007` | `REC-000007` | Distinct parallel 8×8 UWORD correction surfaces with raw shared queries; `B7D6` constant-neutral; donor RPM/ms/N×TP semantics unpromoted. |
| `0x0E904`, `0x0E914`, `0x0E934` | `FND-000008` | `REC-000008` | No V6 counterpart established among bounded candidates; withdrawn raw-vs-converted range contradictions retained only as history. |
| `0x0A272`; axes `0x0E006`/`0x0E002` | `FND-000009` | `REC-000009` | Target caller gives Y=`E006`/X=`E002` and matches XML; workbook “Not established” superseded; A0E2 remains a separate object. |
| `FFFF2B6C`–`FFFF2BA4` band of `unk_FFFF2150`; clamp edges `FFFF2B6E`/`FFFF2B72` used by `FFFF1640` | `FND-000010` | `REC-000010`–`REC-000012` | Firmware-initialised RAM, not calibration: fourteen initializer fields receive `0x7FFF`, A52 receives `0x8000`, and the bound publisher uses signed-minimum selection; remains opaque, with no definition or name. |
| Nissan ignition trimming / knock-window / VTC compensation architecture (cross-ROM context; no EL19A address promotion) | `FND-000011` | — | Donor A2Ls establish a trimming-map `X-64deg` display conversion, not a final-timing arithmetic step; 0x80 flag semantics and all donor-to-EL19A transfers remain unproven on EL19A. |
| `0x0F712` / `0x10F8A`; query operands `FFFF1064` / `FFFF1066` / `FFFF10A0`; related `FFFF33EA` / `FFFF14E0` | `FND-000014` | `REC-000016` | Reader-verified bidirectional 32×1 UWORD transfer pair; `FFFF1066` is a computed internal result, `FFFF1064` has a partial prior lookup-result path, `FFFF10A0` remains unresolved; capture source and physical MAF/airflow/RPM identity not established. |
| `FFFF3579` bit4 (GBR `FFFF34B3+0xC6` and `FFFF34C1+0xB8`), set via `or #h'10` in the `bra` delay slot at `0x07EBBE`, cleared at `0x07EBD0`, stored at `0x07EBD2` | `FND-000013` | — | Bit publication can be merged across a branch delay slot, so a store preceded by `and #h'~mask` may still be the SET path; decompile every incoming edge including delay slots before characterising a status-bit write. No calibration object affected. |
| `FFFF34E7` (= GBR `FFFF34C1+0x26` = `FFFF34B3+0x34`); `FFFF10FE`; `FFFF36BE`; `FFFFB552`; `FFFF355D`; `FFFF8E9E` | `FND-000012` | `REC-000013` | A GBR displacement is not an address until the routine's own base is resolved: `FFFF34E7` is one shared five-bit status byte, the eight `@(h'AA,gbr)` sites are three other cells, `FFFF109E` does not exist, and `FFFF355D`'s readers remain only `0x07EB14`/`0x0935C2`; no calibration object affected. |

## Current priority migrations

- [x] User-finalized Rev Hang screenshot interpretation for E678/E688, preserving the screenshot-finalized RPM presentation while retaining timer-derived ROM query mechanics as a separate runtime fact.
- [x] F3D6/F3DE query, axes and clamp findings.
- [x] 9B2E/9C2E/9DAE raw UBYTE and runtime alias disposition.
- [x] High-value axis correction at `0x0E904`/`0x0FA62`.
- [x] Correction to provisional scalar labels at `0x848A/0x848B`.
- [x] Next high-value A2L synthesis batch: `0x0F406` NTC candidate and `0x0B756/0x0B7D6` scale-compatible analogue dispositions.
- [x] E904/E914/E934 “no V6 counterpart established” dispositions and A272 axis correction.
- [x] Firmware-initialised RAM correction for the `FFFF2150` limit band and `FFFF1640` clamp edges (`FND-000010`/`REC-000010`); WO65808's A52/A58 initializer and signed-minimum corrections are in `REC-000011`, and WO65739's separate copier-extent erratum is in `REC-000012`.
- [x] Donor-only ignition trimming/display and compensation context captured as `FND-000011`; EL19A raw UBYTE and no-`-64` dispositions remain unchanged.
- [x] GBR-relative address rule captured as `FND-000012` with the four attribution corrections in `REC-000013`; `FFFF109E`, `FFFF34E4`-at-`0x0A19B8` and the eight-extra-`FFFF355D`-readers statements are superseded and must not be reused.
- [x] `0x0F712` / `0x10F8A` target-side transfer-pair identity qualified; the MAF/Flow catalogue label remains a hypothesis, and input-source/physical-domain boundaries are explicitly recorded (`FND-000014` / `REC-000016`).
- [ ] Broader geometry corrections only when they change an axis, unit, dimension, scaling, label or XML disposition. Routine RAM-cell endpoint traces remain outside this index — with the recorded exception of `FND-000010`, retained because it forecloses a calibration definition rather than merely tracing a cell.
- [ ] Further A2L synthesis migrations only from a closed report with new material calibration-interpretation evidence; do not re-screen the 179-row catalogue or repeat completed donor comparisons.

## Record locations

- Findings: `FINDINGS/records/FND-000001.md` … `FINDINGS/records/FND-000014.md`
- Reconciliations: `FINDINGS/reconciliations/REC-000001.md` … `FINDINGS/reconciliations/REC-000013.md`, plus `REC-000016.md` (`REC-000014/015` remain referenced by the WO66032 register summary but were not present in the canonical Findings tree at WO66047 preflight and were not reused).
- Evidence references: `FINDINGS/evidence/EVD-xxxxxx.md` (schema reserved; no EVD records created in this revision)

## Migration coverage and cross-links

| Finding | Anchored source reports | Affected inventory/XML objects |
|---|---|---|
| `FND-000001` | WO65548, WO65012 §Results, WO65113 §§2–3, WO65095 closeout and erratum, WO65136, WO65141 | `candidate_register.csv` E678/E688; provisional XML lines 36/58 |
| `FND-000002` | WO64832 §§Stage 3–4, WO65013, WO65141 §1/§4, WO64912 | `candidate_register.csv` F3D6/F3DE; provisional XML lines 89/103 |
| `FND-000003` | WO64970, WO64968, WO64848 closeout, WO65109, WO64913 | `candidate_register.csv` 9C2E/9DAE; provisional XML lines 134/139/144 and 889–909 |
| `FND-000004` | WO64831 §§3–4/§9, WO65014 user correction, WO65112 errata, WO65141 | provisional XML lines 80/83 |
| `FND-000005` | WO65124 §6, WO65058, WO65162 I-04, catalogue row `0x0E904` | `discovered_tables_catalog.csv` `0x0E904`; provisional XML lines 319/918 |
| `FND-000006` | WO65134 §§1–5 and scale erratum, WO65141 §1/§4/erratum, WO65182, WO65056/65057 reused | `discovered_tables_catalog.csv` `0x0F406`; no XML edit |
| `FND-000007` | WO65137 §§2–5 and callsite erratum, WO65180, WO65141 §§1/3/4/5/refresh, WO65060/64940 reused | `discovered_tables_catalog.csv` `0x0B756`; paired `0x0B7D6`; no XML edit |
| `FND-000008` | WO65127 §§1–6, WO65139 §§3–4 and coordinator erratum, WO65141 §§1/3/4, WO65124 §6 | `discovered_tables_catalog.csv` `0x0E904`; provisional XML lines 319/918 as history/build context; no XML edit |
| `FND-000009` | WO64913 §Closeout/register corrections, WO64966, WO65162 X026/X027, WO65548 remaining list | provisional XML X026/X027 (`0xA0E2`/`0xA272`); workbook crosswalk as superseded source; no edit |
| `FND-000010` | WO65499 §§3–4 (superseded census), WO65733 §§2–5 (three indexed-store initializer clusters), WO65808 (A52/A58 values and signed-minimum publisher), WO65739 (copy-helper extent), WO65496 §3 (copy call site) | none — the band is excluded from the calibration inventory and no XML object covers it; no edit |
| `FND-000011` | `EVIDENCE/rr forum ignition tables v2.txt`; `CONTROL/WO65730.md` §§1–4; user-supplied screenshot descriptions (2026-11-24) | none — cross-ROM context only; no EL19A inventory or XML object changed; screenshot filenames await exact repository-path/byte reconciliation |
| `FND-000012` | WO65865, WO65883, WO65886, WO65889, WO65892 (per-site base tables) | none — evidence method and RAM-cell address corrections only; no inventory row or XML object changes |

**Inventory pointer status:** current calibration CSVs have no stable finding-ID column. No CSV, XML, workbook, catalogue, ROM, LST, A2L, protected evidence or script was edited in this revision; this index provides the address-to-inventory/XML crosswalk. Additive CSV pointers may be introduced only under a later explicitly authorized format change.

## Conflicts resolved without erasing history

- E678/E688 display-axis presentation versus unproven runtime RPM conversion: separated into user-finalized presentation and runtime mechanics (`REC-000001`).
- F3D6/F3DE donor TVO conversions versus target ×13/clamp path: donor semantics retained as comparison only (`REC-000002`).
- 9B2E dynamic-axis label and XML ignition/knock overlays versus fixed GBR-rooted axes, identical `9C2E`/`9DAE` payloads and bit-7 disposition (`REC-000003`).
- 0x848A/B, mDDPAPO and the single 52.34% screenshot scalar: kept as three distinct roles (`REC-000004`).
- E904 static inline axis versus verified explicit `0x0FA62` axis and interpolation (`REC-000005`).
- `0x0F406` exact nominal-5-V `20/160 mV` claim versus external AVref and conditional compatibility (`REC-000006`).
- `0x0B756/0x0B7D6` compact callsite/“query unavailable” summary versus corrected calls, staged results and parallel first consumers, with physical units still open (`REC-000007`).
- E904/E914/E934 raw-versus-converted range contradictions versus NOT ESTABLISHED disposition (`REC-000008`).
- A272 workbook “Not established” axes versus caller/XML `E006`/`E002`, with A0E2 kept separate (`REC-000009`).
- WO65499's “zero fixed-displacement writers ⇒ no initializer” reading of the `FFFF2150` limit band versus three indexed-store initializer clusters, with the old census retained as history (`REC-000010`).
- WO65733's broad “all sixteen fields are `0x7FFF`” and signed-maximum publisher descriptions versus WO65808's fourteen `0x7FFF` fields, A52/A58 `0x8000` values, and signed-minimum publisher (`REC-000011`).
- WO65733's `copy_longwords_by_size` maximum `+0x3C` statement versus WO65739's length-`0x60` generic path reaching `+0x5C` at the different `FFFF84D4` destination; no effect on the `FFFF2150` no-copy conclusion (`REC-000012`).
- WO65098's grouped no-writer disposition for `FFFF1064/FFFF1066/FFFF10A0` versus WO65089's `FFFF1066` store and the consumer-index `FFFF1064` prior-result path; split additively in `REC-000016`, with `FFFF10A0` still unresolved and no physical MAF/RPM identity promoted.
- WO65865's `0x0A19B8`→`FFFF34E4` under base `FFFF34B0`, WO65838/WO65859's non-existent `FFFF109E`, and WO65886's "eight further `FFFF355D` readers" versus own-base resolution to `FFFF34E7`, `FFFF8E9E`, `FFFF10FE`, `FFFF36BE` and `FFFFB552`; superseded addresses retained only as history (`REC-000013`, method rule in `FND-000012`).

## Promotion rule

Every material change to calibration interpretation must create or update a finding record and, when it changes a prior interpretation, a reconciliation record. WO reports must link to these IDs. The calibration inventory must link back to the findings supporting its current values. Structural evidence grade is never semantic confidence, and donor names/units/conversions are never promoted without target-side evidence. A missing inventory link means the claim is not yet promoted by this system.
