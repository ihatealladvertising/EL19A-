# Nissan SH705x Base Table Set — v0.1 (2026-11-27)

**Status:** structural baseline assembled from existing scan artifacts; not a semantic or vehicle-validated definition.

## Answer

There is a strong **structural vocabulary** shared across much of this Nissan SH705x corpus: common 8/16/32-point 1D vectors and repeated 8×8/16×16 lookup shapes occur in nearly every detailed image. Layouts are highly stable within the same primary FID/code family. They are **not one global address template** across Nissan ROMs. The evidence supports a family-aware base set with per-ROM overlays.

We cannot yet say we know the complete calibration-table, scalar and axis inventory that every Nissan ROM is “supposed to have.” The current evidence is sufficient to say what shapes and types the scanner commonly finds, and to seed family-specific structural inventories. It does not identify all those objects as ignition, fueling, knock, or other physical functions.

## What this version contains

- `NISSAN_BASE_TABLE_OBJECTS_2026-11-27.tsv`: **129,481** per-image structural table observations across **434 independently scanned layouts** (431 direct DAT images, plus EL19A, V6, and C12W 3DD9A). Each row keeps source image identity/hash, address/extent, kind, element type/width, dimensions, axis storage types and references where available, call/helper references, nontrivial flag, payload hash where the source exported one, and evidence caveat.
- `NISSAN_BASE_AXIS_LINKS_2026-11-27.tsv`: **75,110** explicit axis-link observations. These preserve address and storage type where exported; they do not claim the physical axis meaning.
- `NISSAN_BASE_SHAPE_PROFILE_2026-11-27.tsv`: **48** structural signatures and image prevalence.
- `NISSAN_BASE_FID_FAMILY_PROFILE_2026-11-27.tsv`: profile for **39** primary FID groups represented in the direct-DAT details.
- `NISSAN_BASE_ADDITIONAL_DONOR_COVERAGE_2026-11-27.tsv`: 24 extra donor aggregates reported by WO70026, kept separate because per-table exports are not included in this normalized set and some inputs may overlap the DAT set.
- `NISSAN_C12W_JUKE_TWIN_PAYLOADS_2026-11-27.tsv`: 581 per-address C12W BIN/Juke S19 payload comparisons, without donor A2L labels.
- `NISSAN_BASE_TABLE_SET_manifest.json`: source/output byte counts and SHA-256 values.
- `build_nissan_base_table_set.py`: rebuild script with `--out-dir` and `--repo-dir` options. The repo bundle includes the pinned 431-image per-address source export and run summaries needed with the repository WO evidence.

Juke 9APCTDEM06 S19 is recorded as a **code-twin inherited layout**, not counted as another independent scan: WO70027 found its executable code region byte-identical to the C12W 3DD9A BIN, while 7,170 calibration-region bytes differ. The 581 per-address payload comparisons (463 identical, 118 different) remain in the source evidence.

## Recurring shapes

The 431-DAT detailed census alone contains 128,307 table detections (73,401 marked nontrivial), 15,131 helper detections, and 157,369 call/table associations. These are per-ROM observations with revisions repeated, not globally unique table objects. In the combined 434-image normalized set, the most frequent shapes include:

| Shape signature | Observations | Images with shape |
|---|---:|---:|
| `2D_IMPL` `uint8` 8×1 (axes implicit_u8/unspecified) | 30,754 | 432/434 |
| `2D_IMPL` `uint8` 16×1 (axes implicit_u8/unspecified) | 23,129 | 432/434 |
| `2D_AXIS` `uint8` 8×1 (axes uint8/unspecified) | 12,892 | 433/434 |
| `2D_AXIS` `uint16` 16×1 (axes uint16/unspecified) | 7,822 | 433/434 |
| `2D_AXIS` `uint16` 8×1 (axes uint16/unspecified) | 6,780 | 433/434 |
| `2D_IMPL` `uint16` 16×1 (axes implicit_u16/unspecified) | 6,620 | 432/434 |
| `2D_IMPL` `uint16` 8×1 (axes implicit_u16/unspecified) | 6,435 | 432/434 |
| `3D_AXIS` `uint8` 8×8 (axes uint8/uint8) | 5,105 | 433/434 |
| `2D_AXIS` `uint16` 32×1 (axes uint16/unspecified) | 4,498 | 433/434 |
| `3D_AXIS` `uint8` 4×4 (axes uint8/uint8) | 4,316 | 433/434 |
| `3D_AXIS` `uint16` 16×16 (axes uint16/uint16) | 3,885 | 433/434 |
| `3D_AXIS` `uint8` 16×16 (axes uint8/uint8) | 3,136 | 433/434 |

Among table detections with both dimensions at least 8, there are **18,157** 3D observations in this set. Common scanner geometries include 8×8 UBYTE and 16×16 UWORD/UBYTE maps, plus 4×4 UBYTE maps. Common 2D vectors are UBYTE 8/16/32-point and UWORD 8/16/32-point structures. Geometry recurrence is a useful search prior; it is not a function label.

## How consistent are layouts?

- Across the 431 DAT images, **4,939 same-primary-FID image pairs** have an exact match in the compared strict layout signature (address, extent, kind, element type, dimensions, and axis storage types). That is strong evidence that revisions within these observed FID groups usually keep the same structure.
- Across all 92,665 DAT-to-DAT pairs, median strict-layout Jaccard is **0%**, while median address-ignored geometry-multiset Jaccard is **86.90%**. Similar-sized code families reuse common shapes but place them at different addresses.
- Against EL19A, each of the 431 DATs has **zero same-geometry matches at shared table-start addresses** under the direct address/layout comparison. The closest 1 MiB DATs share 14 of EL19A’s 291 start addresses, with 0 matching geometries at those starts. This makes them poor direct address templates for EL19A.
- C12W/Juke gives a useful controlled variant: same SH705828N code layout, 581 caller-backed table addresses, while 118 table payloads differ. This supports separating the structural family base from calibration-value overlays.

## Can we say what to find in ignition, fueling, knock and similar maps?

**Not comprehensively.** The scan establishes table-shaped lookup structures, types, extents, dimensions, and many caller/axis links. A large 8×8 or 16×16 map is not inherently ignition timing, fuel, knock, torque, or load. The meanings require target-side reader/query/consumer evidence or independently validated target metadata. Donor A2L names remain leads until reconciled to the target.

For EL19A, the current target scan contains 291 table candidates, and the WO70031 matrix classifies 287 as RAW/PROVISIONAL, two established-presentation exceptions, and two structural-overlap holds. Existing Findings retain the 9B2E ignition/knock presentation as provisional; that is not a complete spark/knock family inventory across the Nissan corpus. The base table set intentionally carries no semantic system labels.

**Scalars are a separate coverage gap.** The 431-DAT detailed table census is not a systematic scalar census. EL19A-specific work found 2,739 scalar candidates; a bounded review also recorded 72 off-window generic RAW/PROVISIONAL candidates, while 13 four-byte Tier-C A2L rows remain unresolved. These counts are EL19A-specific and do not establish scalar completeness across the 431 DAT images.

Axis addresses and storage types are captured where source exports provide them. The 75,110 links are not 75,110 distinct physical axes: addresses recur across images and axes may be shared. Physical units, query direction, implicit-grid mechanics and interpolation remain separate semantic evidence.

## Coverage boundary: interpreting “550+ scanned items”

The full detailed-layout denominator I can reproduce for this set is **434 independent ROM layouts**, not 550 complete independent per-ROM table catalogs. The batch inventory counted 11,668 unique direct `.dat` payloads, of which 9,186 loaded as ROM candidates; only 431 emitted non-empty detailed helper/table records. Another 2,482 were loader-rejected, and 8,755 loaded without detailed table records in that run. “No detail emitted” is not proof that the ROM contains no calibration tables.

The 151-ROM reference index is a metadata/cross-reference index whose earlier ROM rows were reused; it is not 151 independently reproduced full table catalogs. WO70026 adds 24-family aggregate counts and a 183-target-table donor-conservation ledger, but not a full per-address layout export for each of those 24 families. Intake/census claims and table detections must not be counted as independent complete ROM scans. This is why the project can have 550+ scanned files/items overall without having 550+ complete, comparable table layouts.

## Recommended base-set model

1. **Shared shape dictionary:** generic structural signatures and prevalence from this set; no semantic names.
2. **Family base layout:** canonical address/extent/geometry signature for a verified code/FID family, with exact variants preserved rather than merged.
3. **Per-ROM calibration overlay:** payload hashes, differing extents and exact revision/transmission/region metadata only when verified.
4. **Axis and scalar sidecar:** axis references and scalar candidates stored separately from map geometry; keep raw type/value confidence separate from meaning/units.
5. **Semantic crosswalk:** ignition, fuel, knock, torque, airflow and temperature labels added only with target-side evidence; unresolved entries stay `GENERIC CANDIDATE`, `NOT LOCATED`, `NOT APPLICABLE`, or `UNRESOLVED` as evidence warrants.

The user-suggested effects of boost, transmission, region and cylinder count are sensible dimensions to test, but the current corpus does not support assigning those causes to specific shape/count differences. Verified ROM metadata and stratified family comparisons are required.

## Published bundle

The repository bundle at `EVIDENCE/NISSAN_BASE_TABLE_SET_2026-11-27/` stores deterministic gzip representations of the six normalized TSV outputs, plus the 431-image source scan export, source manifests, current EL19A comparison, summary, and builder script. Decompress each `.tsv.gz` to recover the byte-identical TSV named in the output-hash list. `NISSAN_BASE_TABLE_SET_package_manifest.json` records package SHA-256 values and sizes.

## Evidence and reproducibility

Repository source snapshot: `ihatealladvertising/EL19A-` main at locked base commit `e071fbcf1fa34739c6f994d9f1c6a36d2d908916`.

- Direct DAT batch: `dat_detailed_431_summary.md`, `dat_detailed_431_manifest.json`, and `scan_details.jsonl.gz`. The 431 batch used workbench revision `13acc0b58826c2b693ef495a0b3c61259daec760`; this was an existing historical run.
- Target EL19A: `EVIDENCE/WO65324_2026-11-27_scan_json.json.gz` and `EVIDENCE/WO70031_EL19A_STRUCTURAL_READINESS.tsv`.
- V6: `EVIDENCE/V6_FIRST_CLASS_DONOR_2026-11-27/README.md` and `v6_current_strict_302_per_address.tsv.gz`; 302 current strict candidates.
- C12W/Juke: `EVIDENCE/WO70027_TABLE_MAP.tsv`, `WO70027_PAYLOAD_COMPARE.tsv`, and `WO70027_SUMMARY.json`.
- Additional partial donor coverage: `EVIDENCE/WO70026_summary.json` and `WO70026_donor_conservation.tsv`.
- Existing comparison reports: `table_layout_similarity_431_DAT_2026-11-27.md` and `EL19A_table_layout_vs_431_DAT_2026-11-27.md`.

No new workbench scan was executed for this synthesis. The generator only normalized and aggregated the pinned existing outputs. The repository package adds evidence/report artifacts only; no ROMs, A2Ls, XML definitions, Findings, or workbench source were modified. This report is a research aid, not a vehicle validation or operational-safety claim.

## Output hashes

- `NISSAN_BASE_TABLE_OBJECTS_2026-11-27.tsv` — 129,481 rows; 42,850,266 bytes; SHA-256 `7645959c3a86a0fc34a4bb57f7b4fae3e9dbff9cd70f7fdde0ef7e1c49434716`.
- `NISSAN_BASE_AXIS_LINKS_2026-11-27.tsv` — 75,110 rows; 12,676,635 bytes; SHA-256 `791fa4393da6b99d8cf286868e8c5383a97c4d45e470dc885d53ffbba5b1f1e8`.
- `NISSAN_BASE_SHAPE_PROFILE_2026-11-27.tsv` — 48 rows; 2,577 bytes; SHA-256 `13ac9294ecd7c89863ad0f778e80cd15ac3dcb31a6abfca4e8d504d4082db5ed`.
- `NISSAN_BASE_FID_FAMILY_PROFILE_2026-11-27.tsv` — 39 rows; 2,277 bytes; SHA-256 `01629bff5822551259bfb85455f1ee78137b909e168426d5875f5a3b84f589f6`.
- `NISSAN_BASE_ADDITIONAL_DONOR_COVERAGE_2026-11-27.tsv` — 24 rows; 5,967 bytes; SHA-256 `b7de76481a41f232600cddf2ae88d45cc8db5bf2e215173c811f4df016b848e6`.
- `NISSAN_C12W_JUKE_TWIN_PAYLOADS_2026-11-27.tsv` — 581 rows; 216,688 bytes; SHA-256 `cad40723c1e5a7f469e7d80d83b0020f0608b4a9882ce0717aa2bdc710af61d2`.
- `NISSAN_BASE_TABLE_SET_summary.json` — 9,856 bytes; SHA-256 `9b7e925a077f9d14718c5dde40f44dcf6bde2925bb639007930657f15c18f0e8`.
- `build_nissan_base_table_set.py` — 15,727 bytes; SHA-256 `68b80f0b58dab97bb237aad8cc00a7d85a1d56fb506d2da30c137249415fbc00`.
- `NISSAN_BASE_TABLE_SET_manifest.json` records pinned source and uncompressed output hashes; the package manifest records compressed repository artifacts.
