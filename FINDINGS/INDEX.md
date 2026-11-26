# Calibration Findings / Reconciliation Index

**Status:** SEEDED — TWO A2L SYNTHESIS BATCHES MIGRATED; ONGOING  
**Authority:** This index is the entry point for calibration interpretation. See [README](README.md) for the full schemas and the mandatory XML build gate.  
**Index revision:** `FND-000020` (WO66051: the `0x08AF6E` block is routine-private read-modify-write scratch — `sub_8AD7C` copies 14 status bytes into its own −0x84 stack frame and writes them back to the same cells, so the status network has no publication path there, 2026-11-26); previous `FND-000019` / `REC-000023` (WO66049: `0x0F01C` is a 16×1 coolant-temperature-keyed curve whose "32-byte object" premise is void — `0x0F02C` is a separate 4-entry bin-indexed floor table and the pair publishes two clamped bytes at `FFFF1441`/`FFFF1384`, 2026-11-26); previous `FND-000018` / `REC-000022` (WO66048: the `0x0ED64`/`0x0EDA0` pair are coolant-temperature-keyed single-query thresholds that publish only a verdict, 2026-11-26); previous `FND-000016` / `FND-000017` and `REC-000019` / `REC-000020` / `REC-000021` (Release 1 selector, axis geometry and linked-storage presentation corrections, 2026-11-26); previous `FND-000015` / `REC-000017`, `REC-000018`, `FND-000014` / `REC-000016` and earlier records retained as current where applicable.

## Record schema

Finding records use the stable IDs `FND-000001` onward and carry: status; semantic layer; exact addresses, storage width and geometry; exact observations with ROM/LST PCs and mechanics; conclusion; confidence and evidence grade kept distinct; source class and exact WO/report anchors; related finding/reconciliation IDs; affected inventory/XML objects; and explicit unknowns, contradictions, stop boundary and no-repeat notes.

Reconciliation records use `REC-000001` onward and carry: affected address/object; old interpretation and source; corrected/current interpretation and supporting finding(s); reason and discriminating evidence; confidence; status; and affected inventory/XML references. Superseded interpretations are retained as history, never erased. Full normative text is in [README](README.md) §§Finding record minimum fields and Reconciliation record minimum fields.

## Address lookup

| Address / object | Current finding(s) | Reconciliation(s) | One-line disposition |
|---|---|---|---|
| `0xE678–0xE687`, `0xE688–0xE697` | `FND-000001` | `REC-000001` | User-finalized RPM display presentation retained for these two tables only; timer-derived implicit-grid query remains a separate runtime fact. |
| `0xF3D6`/`0xF3C6`, `0xF3DE`/`0xF3CE` | `FND-000002` | `REC-000002` | Two distinct generic 8-point UBYTE limit schedules with target-proven ×13/clamp mechanics; donor TVO units and main/sub labels not promoted. |
| `0x9B2E`, `0x9C2E`, `0x9DAE`; axes `0xE4AC`/`0xE4BC` | `FND-000003`, `FND-000017` | `REC-000003`, `REC-000019` | Three distinct placements; successor X=`0xE4AC`, Y=`0xE4BC` (baseline child order corrected); axes raw, ignition/knock labels provisional. |
| `0x848A`, `0x848B`; donor `0x90EA` | `FND-000004` | `REC-000004` | `848A/B` paired user-verified donor mapping; separate donor `mDDPAPO` and screenshot scalar roles; numeric coincidence does not merge them. |
| `0x0E904`; axis `0x0FA62` | `FND-000005` | `REC-000005` | XML v3 static `0–240` axis is wrong; future build uses explicit UWORD axis at `0x0FA62`; no XML edit in this revision. |
| `0x0F406` | `FND-000006` | `REC-000006` | Strong `mTTWN` donor candidate by geometry/output/context; `20 mV/count` is conditional on unknown board AVref; physical identity MED-LOW and unpromoted. |
| `0x0B756`, `0x0B7D6`; axes `0x0FCFC`/`0x0FD3C` | `FND-000007` | `REC-000007` | Distinct parallel 8×8 UWORD correction surfaces with raw shared queries; `B7D6` constant-neutral; donor RPM/ms/N×TP semantics unpromoted. |
| `0x0E904`, `0x0E914`, `0x0E934` | `FND-000008` | `REC-000008` | No V6 counterpart established among bounded candidates; withdrawn raw-vs-converted range contradictions retained only as history. |
| `0x0A272`; axes `0x0E006`/`0x0E002` | `FND-000009` | `REC-000009` | Target caller gives Y=`E006`/X=`E002` and matches XML; workbook “Not established” superseded; A0E2 remains a separate object. |
| `FFFF2B6C`–`FFFF2BA4` band of `unk_FFFF2150`; clamp edges `FFFF2B6E`/`FFFF2B72` used by `FFFF1640` | `FND-000010` | `REC-000010`–`REC-000012` | Firmware-initialised RAM, not calibration: fourteen initializer fields receive `0x7FFF`, A52 receives `0x8000`, and the bound publisher uses signed-minimum selection; remains opaque, with no definition or name. |
| Nissan ignition trimming / knock-window / VTC compensation architecture (cross-ROM context; no EL19A address promotion) | `FND-000011` | — | Donor A2Ls establish a trimming-map `X-64deg` display conversion, not a final-timing arithmetic step; 0x80 flag semantics and all donor-to-EL19A transfers remain unproven on EL19A. |
| `0x0F712` / `0x10F8A`; query operands `FFFF1064` / `FFFF1066` / `FFFF10A0`; related `FFFF33EA` / `FFFF14E0` | `FND-000014` | `REC-000016` | Reader-verified bidirectional 32×1 UWORD transfer pair; `FFFF1066` is a computed internal result, `FFFF1064` has a partial prior lookup-result path, `FFFF10A0` remains unresolved; capture source and physical MAF/airflow/RPM identity not established. |
| `FND-000015` | WO65916, WO65904 (descriptor bounds, zero-fill), WO65877 (gate and counter), WO65892 (`sub_228F0` byte1), WO65901 | none — `FFFF A074` is firmware RAM with no ROM image; no CSV/XML object is supported by the current schema |
| `FFFF3579` bit4 (GBR `FFFF34B3+0xC6` and `FFFF34C1+0xB8`), set via `or #h'10` in the `bra` delay slot at `0x07EBBE`, cleared at `0x07EBD0`, stored at `0x07EBD2` | `FND-000013` | — | Bit publication can be merged across a branch delay slot, so a store preceded by `and #h'~mask` may still be the SET path; decompile every incoming edge including delay slots before characterising a status-bit write. No calibration object affected. |
| `FFFF34E7` (= GBR `FFFF34C1+0x26` = `FFFF34B3+0x34`); `FFFF10FE`; `FFFF36BE`; `FFFFB552`; `FFFF355D`; `FFFF8E9E` | `FND-000016` | WO70003 corrected scope-freeze audit; target ROM `0x4057A–0x405D8` | `0x0E21A`, `0x0ED9C`, `0x0F2AE`, `0x107CC` | Bin-selector mechanics; static index representation in Release 1. |
| `FND-000017` | WO70003 corrected scope-freeze audit; target ROM/LST helper callsites listed in record | recovered provisional axes and fixed-grid tables; reused FND-000002/003/005/014 where established | Geometry/axis structure only; physical domains unresolved. |
| `FND-000012` | `REC-000013` | A GBR displacement is not an address until the routine's own base is resolved: `FFFF34E7` is one shared five-bit status byte, the eight `@(h'AA,gbr)` sites are three other cells, `FFFF109E` does not exist, and `FFFF355D`'s readers remain only `0x07EB14`/`0x0935C2`; no calibration object affected. |
| `0x0E21A`–`0x0E21C`; indexed arrays `0x0ED9C`, `0x0F2AE`, `0x107CC` | `FND-000016` | `REC-000020` | Three UBYTE thresholds `[6,8,12]` produce bin 0..3; not an interpolation axis; three arrays displayed raw against an explicit static bin index. |
| `0x0CD56` / `0x0FEC0` linked lookup pair | `FND-000017` | `REC-000019`, `REC-000021` | Reciprocal reader-backed objects: `0x0FEC0` is the surface's Y axis; row 0 of `0x0CD56` is the curve's query axis. Preserve both and edit as a linked pair. |
| `0x0AF72`, `0x0C3D6`, `0x0D8D6`, `0x0F6B2`, `0x0F6D2`, `0x0F7F2`, `0x10226`, `0x10CE2`, `0x10A54`, `0x10A64`, `0x10BC8`, `0x10EAA`, `0x10ECA`, `0x10EEA`, `0x10F6A`, `0x10F7A`, `0x0FEC0`, `0x1031C`, `0x0EFFC`, `0x1109A`, `0x12D98` and associated axes | `FND-000017` (reuse `FND-000002`, `FND-000005`, `FND-000014` where applicable) | `REC-000019` | Provisional ROM-axis pointers and implicit fixed grids recovered/corrected; physical domains remain unresolved. |
| `FFFF284E` (= `FFFF2150+0x6FE`); `FFFF357A` bit2 (`FFFF34C1+0xB9`); gate `FFFF34F0` bit4 (`FFFF34C1+0x2F`) | — (method already covered by `FND-000012`/`FND-000013`) | `REC-000018` | Configuration-mask memo: five resolved access sites, `0xFF` init (`0x0775BC`, `0x0776D0`), `0x80` = no-bits (`0x078C52`), accepted mask (`0x078C46`), and the single read (`0x078C34`) is an overlap test inside the writing routine, so the mask never leaves `sub_77608`; its only outward product is `FFFF357A` bit2. WO65910's `FFFF34E2` gate attribution is corrected to `FFFF34F0`. |
| `FFFF A074`-`FFFFA322` (3-byte entries, 198 live / 229 capacity); `FFFF34F5` bit5; `FFFFB526` | `FND-000015` | `REC-000017` | Diagnostic monitor status array: 198 live entries from the compile-time immediate `0xC6` (`0x08B33C`, `0x07437A`, `0x075DD4`, `0x075E9C`, `0x0800A2`), per-entry flags written by `sub_8081C`/`sub_8085E`/`sub_80884`, and the `FFFF34F5.bit5` latch arms when **no** evaluated entry has byte2 bit3 set. |
| `0x08AF6E` stack block in `sub_8AD7C`; cells `FFFF3539`, `FFFF353D`, `FFFF3548`, `FFFF354D`, `FFFF3554`, `FFFF3558`, `FFFF355B`, `FFFF356A`, `FFFF356C`, `FFFF357A`, `FFFF3580`, `FFFF3590`, `FFFF3595`, `FFFF35A4` | `FND-000020` (base rule `FND-000012`) | none — WO65922's `FFFF357A` snapshot claim upheld (slot `0x60`) | The `0x08AF6E` block is `sub_8AD7C`'s own −0x84 stack frame (`add` at `0x08AD94`, release at `0x08B3E0`); it is addressed only through `@(imm,r15)` with no `mov r15,rN` anywhere, the routine's only two calls (`0x08AEB8`, `0x08B2F8`) take scalar arguments, and all 14 copied status bytes are written back to the cells they came from (`0x08B16E`–`0x08B2F6`) — an in-place bit merge, not a diagnostic frame, queue payload or MMIO write. |
| `0x0F01C`, `0x0F02C`, `0x0EE68`; query cell `FFFF84B8`; bin input `FFFF84E4`; thresholds `0x0E21A`; outputs `FFFF1441`, `FFFF1384` | `FND-000019` (grid `FND-000017`; selector `FND-000016`; helper/query `FND-000018`) | `REC-000023` | `0x0F01C`–`0x0F02B` is a 16×1 UBYTE coolant-temperature curve (108→60, strictly non-increasing) read once at `0x048E60` in `sub_48D2E`; `0x0F02C`–`0x0F02F` (`26 30 36 3E` = 38/48/54/62) is a **separate 4-entry bin-indexed floor table** loaded by `off_48FFC` at `0x048EFE`, so the "32-byte object" reading spanned three objects and the `0x00`–`0x81` rising range belongs to the unrelated `0x0F031` ramp; both curve results are offset by `UBYTE[0x8565]=0x18`, floored at `table[bin]` and `UBYTE[0x8B9D]=0x04`, and published as `UBYTE[FFFF1054+0x3ED]` = `FFFF1441` and `UBYTE[FFFF1054+0x330]` = `FFFF1384`, with no idle/dashpot/actuator sink and no RPM operand. |
| `0x0ED64`, `0x0EDA0`; query cell `FFFF84B8`; compared cell `FFFF85A9`; output `FFFF34D2` bit6 (`FFFF34C1+0x11`) | `FND-000018` (grid from `FND-000017`; GBR/`mov.w` discipline `FND-000012`) | `REC-000022` | Two 16×1 UBYTE coolant-temperature-keyed thresholds queried at **one** shared index `U8[FFFF84B4+0x04]` (rescaled AN27 NTC temp) in `sub_488BA` at `0x04893A`/`0x048948`; results are used only as single-sided `cmp/gt` limits against `FFFF85A9` and never published, so the entire outward product is `FFFF34D2` bit6 plus a 0/1 return feeding the `FFFF11F3` enum machine and gating a `sub_48C1E` word into `UWORD[FFFFB644]`/`U16[FFFF11F0]`; no idle/dashpot/actuator sink, and the `Rpm_x25` donor label is contradicted. |

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
- [x] `FFFF A074` entry count, capacity, populate path and `FFFF34F5.bit5` gate polarity settled (`FND-000015` / `REC-000017`); the 198-versus-229 contradiction was a live-count/descriptor-capacity conflation, and WO65877's all-bit3-set gate is inverted.
- [x] `FFFF284E` mask memo settled as internal state with no outward consumer, and the `FFFF34E2`-versus-`FFFF34F0` gate attribution corrected (`REC-000018`); the `FFFF34xx` status block still terminates in status bytes, not an actuator.
- [x] WO70003 Release 1 scope-freeze corrections: 0x0E21A selector and provisional ROM/fixed-grid axis recoveries recorded in FND-000016/017 and REC-000019/020; 9B2E orientation implements FND-000003/REC-000003.
- [x] Reciprocal shared-storage warning for 0x0CD56/0x0FEC0: both reader-backed objects retained and marked [P] [LINKED], with edit-coupling documented in REC-000021.
- [x] WO66048 settled the axis of the `0x0ED64`/`0x0EDA0` pair as a single shared coolant-temperature query with a verdict-only output (`FND-000018` / `REC-000022`); the pair are single-sided thresholds, not warm-up/idle tables, and the `Rpm_x25` donor label is contradicted rather than merely unsupported.
- [x] WO66051 closed the status-network endpoint question at block scope: the `0x08AF6E` block is private scratch in `sub_8AD7C`'s own frame and the 14 status bytes are read-modify-written in place, so gathering status bytes into one block is not evidence of an external publication path (`FND-000020`).
- [x] WO66049 settled the `0x0F01C` region: `0x0F01C`–`0x0F02B` is a 16×1 curve on the same `U8[FFFF84B4+0x04]` coolant query as its `0xEE68` companion, while `0x0F02C`–`0x0F02F` is a separate 4-entry bin floor table (38/48/54/62) indexed by the `0x0E21A` 6/8/12 selector against `FFFF84E4`; the results are floored and published to `FFFF1441`/`FFFF1384` with no actuator sink, so the prior 32-byte/2×16/rising geometry reading is corrected (`FND-000019` / `REC-000023`).
- [ ] Broader geometry corrections only when they change an axis, unit, dimension, scaling, label or XML disposition. Routine RAM-cell endpoint traces remain outside this index — with the recorded exception of `FND-000010`, retained because it forecloses a calibration definition rather than merely tracing a cell.
- [ ] Further A2L synthesis migrations only from a closed report with new material calibration-interpretation evidence; do not re-screen the 179-row catalogue or repeat completed donor comparisons.

## Record locations

- Findings: `FINDINGS/records/FND-000001.md` … `FINDINGS/records/FND-000020.md`
- Reconciliations: `FINDINGS/reconciliations/REC-000001.md` … `FINDINGS/reconciliations/REC-000013.md`, plus `REC-000016.md`, `REC-000017.md`, `REC-000018.md`, `REC-000019.md`, `REC-000020.md`, `REC-000021.md`, `REC-000022.md` and `REC-000023.md` (`REC-000014/015` remain referenced by the WO66032 register summary but were not present in the canonical Findings tree at WO66047 preflight and were not reused).
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
- `0x0CD56`/`0x0FEC0` ordinary independent-table presentation versus target-side reciprocal use of each array as the other's axis; both objects are retained, visibly marked `[P] [LINKED]`, and must be edited together (`REC-000021`).
- WO65098's grouped no-writer disposition for `FFFF1064/FFFF1066/FFFF10A0` versus WO65089's `FFFF1066` store and the consumer-index `FFFF1064` prior-result path; split additively in `REC-000016`, with `FFFF10A0` still unresolved and no physical MAF/RPM identity promoted.
- WO65877's "all 198 entries have bit3 set" gate and WO65904's "229 entries / no populate path located / byte1 bit3" reading of `FFFF A074` versus the instruction-level 198-count, the byte2 bit3 all-clear polarity, and the located `sub_8081C`/`sub_8085E`/`sub_80884` per-entry flag setters; corrected additively in `REC-000017` with both source reports unedited (`FND-000015`).
- WO65865's `0x0A19B8`→`FFFF34E4` under base `FFFF34B0`, WO65838/WO65859's non-existent `FFFF109E`, and WO65886's "eight further `FFFF355D` readers" versus own-base resolution to `FFFF34E7`, `FFFF8E9E`, `FFFF10FE`, `FFFF36BE` and `FFFFB552`; superseded addresses retained only as history (`REC-000013`, method rule in `FND-000012`).

## Promotion rule

Every material change to calibration interpretation must create or update a finding record and, when it changes a prior interpretation, a reconciliation record. WO reports must link to these IDs. The calibration inventory must link back to the findings supporting its current values. Structural evidence grade is never semantic confidence, and donor names/units/conversions are never promoted without target-side evidence. A missing inventory link means the claim is not yet promoted by this system.
