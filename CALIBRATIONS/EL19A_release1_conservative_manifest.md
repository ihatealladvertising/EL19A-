# EL19A Iterative Best-Guess Release 1 — Build Manifest

**Build state:** ITERATIVE BEST-GUESS BUILD — RomRaider import and 18-table visual spot-check PASS; further refinement active  
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
| Successor XML | `CALIBRATIONS/EL19A_release1_conservative.xml` | Not recomputed after label/comment update | `9f16c8ba461a2f0ce162a14688efdf96a6de1345` |
| Revised scope matrix | `CALIBRATIONS/RELEASE1_SCOPE_MATRIX_R1.csv` | Not recomputed after linked-warning update | `2a7f6bb77277f27620ebc648e26c286885efdf21` |

The selected baseline and original consultant CSV are retained unchanged.

## Final scope

| Disposition | Objects |
|---|---:|
| INCLUDE — ESTABLISHED | 2 |
| INCLUDE — PROVISIONAL | 252 |
| EXCLUDE | 7 |
| **Total baseline objects** | **261** |
| **Included in successor** | **254** |

The two established entries are the user-finalized 0x0E678 and 0x0E688 presentation exceptions. The other 252 included objects now use the selected baseline's best-guess names and functional categories; six candidate data conversions are restored where the matrix contains a plausible display hypothesis. These are working assumptions for refinement, not claims that all physical identities/units are proven. The seven exclusions comprise the superseded 0x0E904 duplicate view and six decoded overlays on the 9B2E-family maps.

## Material corrections implemented

1. **9B2E family:** successor axes X=`0x0E4AC`, Y=`0x0E4BC` per `FND-000003` / `REC-000003`; both axes raw, unsupported physical conversions removed.
2. **0x0E21A selector:** the three values `[6,8,12]` are thresholds producing index 0..3, not an interpolation axis. The three associated arrays are included against a static bin-index axis (`FND-000016` / `REC-000020`).
3. **Provisional axes:** ROM-axis references and implicit fixed grids are restored from helper/caller evidence (`FND-000017` / `REC-000019`). `0x0F712` reuses `FND-000014`.
4. **Working presentation:** best-guess functional labels and the original category structure are restored across the included objects. Six candidate data conversion families are enabled as provisional working guesses; the remaining objects retain raw display scaling unless the matrix records a conversion candidate. Keep refining these guesses as target-side evidence improves.

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

## Validation state and remaining refinement

- **RomRaider import:** user-reported PASS with the exact target f501.bin; the definition tree and tables load in RomRaider v1.1.0 (NOV26 2025).
- **18-table sample:** visually reviewed from EVIDENCE/RR TABLES SS. Captures 001–015 cover the first 15 objects; Capture023 is the corrected 0x11FC4 recheck; Capture024 is the fresh recheck of 0x0EFFC, 0x1109A and 0x12D98, replacing stale Captures 016–018.
- **Additional visual checks:** Captures 019–021 verify the three four-bin arrays using the static index 0..3; Capture022 verifies 0x0E678 and 0x0E688 in Electronic Throttle Control → Dashpot.
- **Corrected axis details:** 0x11FC4 uses X=0x128AE UBYTE and Y=0x129EE UWORD; 0x0EFFC uses static UBYTE 0,32,…,224; 0x1109A and 0x12D98 use static UWORD 0,4096,…,61440.
- **Structural audit:** 254 included objects; 145 ROM-backed axes and 125 static axes checked; no detected pointer, width, geometry, extent or static-axis-length mismatches.
- **Best-guess presentation:** 254 names/categories restored from the selected best-guess baseline and reconciled scope matrix. Six candidate data conversions are restored: Percent_ThrottleReduction, Temp_Coolant_Min, TVO_Degrees_Ref, Data_Pct_x0p78125, Rpm_x25 and Percent_UWORD_100_256. These are deliberate provisional display hypotheses and should be refined, not treated as verified physical conversions.
- **Remaining:** no exhaustive visual review of all 254 objects; no independent byte-by-byte ROM extraction in this integration session; no vehicle testing. Continue refining names, categories and conversions as the remaining reader/caller work yields better evidence. None of those tasks blocks use of this working definition.

## Exclusions and unresolved boundaries

- Excluded: superseded `0x0E904` static-axis duplicate and six decoded ignition/knock overlays.
- Physical operating domains, hardware source/sink identity and many physical units remain unresolved. Provisional names and conversions are intentional working hypotheses, not final semantic claims.
- No live-vehicle testing was performed or authorized.


## Owner directive — iterative best-guess definition

On 2026-11-26 the project owner explicitly directed that this definition be built with best guesses and refined from there. The successor now restores working names, categories and candidate data conversions from the selected full-definition baseline while preserving the verified target-side storage geometry and corrected axes. The provisional objects are intended to be useful in RomRaider now; unresolved semantics are refinement work, not a hold on the definition.


## Linked-storage editing warning — 0x0CD56 / 0x0FEC0

The two reader-backed objects at 0x0CD56 and 0x0FEC0 share their axis/data storage reciprocally: the 0xFEC0 curve's values are the Y breakpoints for the 0xCD56 surface, and row 0 of the 0xCD56 surface supplies the query axis for the 0xFEC0 curve. Both remain in the XML because both are used by target lookup paths. Their RomRaider names are marked `[P] [LINKED]`, and XML comments describe the dependency. Treat the two objects as a coupled pair when editing either one; no read-only behavior is asserted. See REC-000021.

All 252 provisional objects now carry a visible `[P]` marker; the two user-established E678/E688 entries retain their finalized labels.
