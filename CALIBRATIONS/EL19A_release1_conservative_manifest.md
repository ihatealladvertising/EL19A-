# EL19A Conservative Release 1 — Build Manifest

**Build state:** BUILT — STRUCTURALLY CHECKED; initial RomRaider tree load user-reported PASS; table-level review pending  
**Build date:** 2026-11-26  
**Target:** 2008 Nissan Versa/Sentra C11X MT, EL19A / MR18DE, FID `8CMCKRN5`, SH7058/SH705822N

## Immutable inputs

| Input | Path / identity | Hash |
|---|---|---|
| Target ROM | `EVIDENCE/VERSA f501.bin`, 1,048,576 bytes | MD5 `46991697c502052752a2cabcb84c9e27`; SHA-256 `bfe037e8e6c389e2a90214047058eb6dc3bcaaaac5b5931bf98a3f5d9f64fd6a` (reported in WO70003; not independently rehashed in this integration session) |
| Selected baseline XML | `CALIBRATIONS/EL19A_best_guess_provisional_full_definition.xml` | Git blob `77b00f4ea3046050dbd791644752e5c01857b75f`; source SHA-256 `54d396013125d639f226029b938556a151c99844e06fa0f8eadd938afbbd7f8d` |
| Original consultant scope matrix | `CALIBRATIONS/RELEASE1_SCOPE_MATRIX.csv` | Git blob `fece677945a6e95b92d8cc993f03998e7e63c702`; SHA-256 `5bde1d62cf8cbd377e1c3ffd4af83ab857557594d041b5a460c2cee079383141` |

## Successor artifacts

| Artifact | Path | Content SHA-256 | Git blob |
|---|---|---|---|
| Successor XML | `CALIBRATIONS/EL19A_release1_conservative.xml` | `f311bf98007865d6e5f8ff0fce8aa0bc6bde2d9e4250bbb19feb67281512b90d` | `33a798efcbf2b8a1d80dc88be25af02d12297ce7` |
| Revised scope matrix | `CALIBRATIONS/RELEASE1_SCOPE_MATRIX_R1.csv` | `0cb93ce51d74d2fba2f85ec4e15982ae8bf424a3483442d3e3aa5cd7431a4ed7` | `f9fa05cafc99a338a9c0fcad94796762af3fd8af` |

The selected baseline and original consultant CSV are retained unchanged.

## Final scope

| Disposition | Objects |
|---|---:|
| INCLUDE — ESTABLISHED | 2 |
| INCLUDE — RAW/PROVISIONAL | 252 |
| EXCLUDE | 7 |
| **Total baseline objects** | **261** |
| **Included in successor** | **254** |

The two established entries are the user-finalized `0x0E678` and `0x0E688` presentation exceptions. The seven exclusions comprise the superseded `0x0E904` duplicate view and six decoded overlays on the 9B2E-family raw maps. The remaining included objects use generic names/raw scaling and do not claim unresolved physical units.

## Material corrections implemented

1. **9B2E family:** successor axes X=`0x0E4AC`, Y=`0x0E4BC` per `FND-000003` / `REC-000003`; both axes raw, unsupported physical conversions removed.
2. **0x0E21A selector:** the three values `[6,8,12]` are thresholds producing index 0..3, not an interpolation axis. The three associated arrays are included against a static bin-index axis (`FND-000016` / `REC-000020`).
3. **Provisional axes:** ROM-axis references and implicit fixed grids are restored from helper/caller evidence (`FND-000017` / `REC-000019`). `0x0F712` reuses `FND-000014`.
4. **Display policy:** included provisional tables/axes use generic names/raw conversions. Donor-only RPM, percent, temperature, airflow and ignition conversions are not carried forward.

## Findings revision

New records: `FND-000016`, `FND-000017`, `REC-000019`, `REC-000020`.  
Reused: `FND-000002`, `FND-000003`, `FND-000005`, `FND-000014`, `REC-000002`, `REC-000003`, `REC-000005`, `REC-000016`.  
Canonical address lookup: `FINDINGS/INDEX.md`. The existing calibration CSV schema has no finding-ID column; no unsupported inventory schema change was made.

## Validation performed

- XML tree parse completed with balanced elements after serialization.
- 261 original top-level objects reconciled to the 261 matrix rows in exact address/order.
- Successor contains 254 top-level calibration objects.
- Storage type, endian, dimensions and byte extent checked against each revised matrix row.
- Every 2D curve has one displayed Y axis; every 3D surface has one X and one Y axis; scalar objects have no axes.
- Static axes have the declared number of data points.
- All 145 ROM-backed axis bindings were checked against the revised matrix descriptor; the final audit found zero width/scaling mismatches. Mixed-width pairs at data objects `0x0CD56` and `0x11FC4` were corrected to UBYTE X axes / UWORD Y axes.
- ROM axis pointers and calibration data extents are within the 1 MiB address range.
- 9B2E orientation verified in successor; `0x0E21A` is not attached as a ROM axis to the three selector tables.
- Final post-correction audit checked 145 ROM-backed axes and 125 static axes; no matrix/XML axis pointer, storage-width, static-length, data-extent or object-count mismatches remained.
- Remote readback of XML and revised matrix matched the exact generated content.

## Validation not yet performed — do not overstate release status

- **Initial RomRaider import/tree load:** user-reported PASS on 2026-11-26 after removing the duplicate XML declaration; the ROM loads and the definition tree displays many tables. This is an owner-reported result, not an independently observed test; RomRaider version was not supplied.
- **Table-level visual validation:** still pending. Individual maps/curves, rendered dimensions, axis values, and selected table bytes have not yet been exhaustively checked in RomRaider.
- **Post-import axis correction:** a matrix/XML audit found stale Y-axis ROM pointers on `0x0EFFC`, `0x1109A` and `0x12D98`, although the reader evidence specifies implicit fixed grids. The successor now uses static UBYTE `0,32,…,224` for `0x0EFFC` and static UWORD `0,4096,…,61440` for `0x1109A` and `0x12D98`. Reload the current canonical XML in RomRaider; the prior UI result predates these changes.
- **Independent byte-by-byte ROM extraction:** not performed here. Address/width/axis mechanics are based on the current scope matrix and referenced ROM/LST audit; the ROM SHA-256 above is consultant-reported.
- **Visual inspection of all 254 objects in RomRaider:** pending.

Before treating this as the fully validated release, load `EL19A_release1_conservative.xml` in RomRaider against the exact ROM above and inspect all table families. Prioritize static bin-index axes, the shared-row `0x0CD56` reference, UWORD BE axes and 9B2E X/Y orientation.

## Exclusions and unresolved boundaries

- Excluded: superseded `0x0E904` static-axis duplicate and six decoded ignition/knock overlays.
- Physical operating domains, hardware source/sink identity and physical units remain unresolved for raw/provisional entries; these are deliberately not claimed by Release 1.
- No live-vehicle testing was performed or authorized.
