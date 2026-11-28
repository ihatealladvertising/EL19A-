# Nissan ROM registry and mass-DAT scan reconciliation — 2026-11-27

## Purpose
Create a structured vehicle/ROM-ID lookup from the first table in `EVIDENCE/master rom table/uprev ecus.txt` and reconcile its distinct identifier namespace with the completed mass SH705x DAT scan. This is reference metadata only; it does not establish target ECU identity or promote calibration semantics.

## Vehicle / ROM catalogue

- Source file SHA identity in Git: `ef91ee0a01aa699aeef0957d4e7f08b70628832d` (Git blob SHA; not a SHA-256 digest).
- Structured table boundary: 2,161 data rows, ending at source line 2,162; marker line 2,163.
- 2,161 vehicle/master-ROM records; 3,691 expanded ROM-ID mappings; 3,691 unique codes; zero duplicate expanded ROM IDs.
- 58 model names; makes: Infiniti, Nissan; year range 2003–2022; 20 engine codes; transmissions: AT, CVT, MT.
- 16 MR18DE vehicle/master-ROM rows: Cube 4, Tiida 3, Versa 9.
- Every master-ROM ID appears in its own ROMs Updated list in the normalized source rows.

### Identifier warning: EL19A

The vehicle/master-ROM list has one expanded ROM ID `EL19A`, at source line 1881: 2008 Nissan Sentra, MR20DE, MT, master ROM EL19A. This is a record in the Uprev vehicle/ROM-code catalogue, **not** an ECU FID or a verified binary identity. The EL19A project target is independently pinned as `f501.bin` / FID `8CMCKRN5` / MR18DE. No exact `8W83B` ROM code appears in the supplied first table. Preserve this as a namespace/metadata discrepancy for review; do not rewrite the project target mapping from this catalogue.

## Mass DAT scan — what was actually processed

Source work order: [REPROPROGRAMMING batch workbench run](https://github.com/ihatealladvertising/EL19A-/blob/main/EVIDENCE/mass%20dat%20scan/WORK_ORDER_REPROPROGRAMMING_BATCH_2026-11-27.md)

- Input inventory: 16,584 source files: 11,744 direct .dat/.bin candidates, 1,318 ZIP/PDX packages, 80 7z packages, 3,442 ancillary/unsupported.
- 13,698 unique candidate payloads across 14,666 source references: 11,216 scanned and 2,482 loader-rejected.
- Direct .dat subset: 11,740 source references and 11,668 unique payloads; 9,186 loaded as ROM candidates, 2,482 rejected.
- 431 unique direct-.dat payloads yielded detailed helper/call/table records. 8,755 other successfully loaded direct-.dat payloads did not yield detailed helper/table records in this run.
- These 431 are **detailed-positive DAT snapshots**, not a 431-object calibration list and not a universal count of tables in a Nissan ECU.
- 1,399 archives/members inventoried: 1,395 read successfully; 4 archive reads failed.
- Run took 2,501.4 seconds using Python 3.12.10, py7zr 1.1.4, workbench commit `13acc0b58826c2b693ef495a0b3c61259daec760`.
- Detailed-result file SHA-256 from the batch manifest: `03b102954ab8b4210d1fe23e217289586c27c9b607d28dc062fd7b52a0da4a31`. Gzip scan-details SHA-256: `1211c98e5e9afefb470a78e268da0c644017016df79a5af3e0c672afa43ce977`.

### Detailed DAT-result totals (summed per snapshot; duplicates/revisions repeat)

| Metric | Result |
|---|---:|
| Detailed DAT inputs | 431 |
| ROM size 512 KiB | 313 |
| ROM size 1 MiB | 118 |
| CPU SH705519N | 241 |
| CPU SH705520N | 72 |
| CPU SH705828N | 118 |
| Helper detections | 15,131 |
| Table detections | 128,307 |
| Non-trivial table detections | 73,401 |
| Call-site/table associations | 157,369 |
| Primary FID families | 39 |

The scan summary reports 838 distinct helper addresses, 6,599 distinct table addresses, 48 recurring structural signatures, and 6,271,172 bytes of summed table extents. Those are across-snapshot observations; do not sum repeated table detections as project-wide unique objects.

### 431, 433 and 434 denominator reconciliation

- **431** = detailed direct-DAT records in `dat_detailed_431_results.tsv`.
- **433** = 431 DAT records plus the EL19A and V6 comparison images.
- **434** = 431 DAT records plus EL19A, V6 and the C12W 3DD9A comparison image in WO70034.
- Juke S19 is recorded as an inherited code twin and is excluded from the independent layout-image count.

The standalone mass-DAT batch itself did **not** produce 433 direct-DAT detailed records. Its verified detailed-record count is 431.

## Cross-reference of scan FIDs to the supplied ECU/FID inventory

The second, multiline inventory in the source text was kept separate from the 2,161-row vehicle table. It yields 43 ECU/FID metadata rows after excluding the header. Across 39 primary scan FIDs:
- 1 primary FID family has an exact FID inventory match.
- 2 additional FID families have prefix-only candidates.
- The remaining 36 have no match in this 43-row inventory.

Exact match: `1CMC7QPD401` (8 detailed DAT records) → ECUID `EM62B`, Tiida, HR16DE, source line 2411.
Prefix-only candidates: `1CMC7QPD4` (32 records) → `1CMC7QPD401`; `5CMCE3E61` (2 records) → `5CMCE3E6` (ECUIDs EC80A and EC82A; Note/Tiida?; HR16DE). These are not exact identity joins.
No match was found for the target FID `8CMCKRN5` or the ROM code `8W83B` in the supplied ECU/FID text inventory.

The primary scan FID field is preserved as scanned metadata, not authenticated vehicle identity. Incidental strings in `detected_fid_tags` are not substituted for the primary field.

## Outputs

- `NISSAN_ROM_VEHICLE_CATALOG_2026-11-27.tsv` — 2,161 source vehicle/master-ROM rows.
- `NISSAN_ROM_ID_CROSSWALK_2026-11-27.tsv` — 3,691 expanded ROM-ID rows.
- `NISSAN_ECU_FID_CATALOG_2026-11-27.tsv` — 43 parsed ECU/FID rows from the separate multiline inventory.
- `NISSAN_DAT_DETAILED_SCAN_INDEX_2026-11-27.tsv` — 431 detailed DAT snapshot rows.
- `NISSAN_DAT_FID_VEHICLE_RECONCILIATION_2026-11-27.tsv` — 39 primary FID family rows with exact/prefix/no-match disposition.

All TSV outputs open directly in Excel. The provided PNGs were enumerated but not visually transcribed in this pass. The existing `rom_table_builder.mjs` is a local workbook-builder reference; it hardcodes Windows paths and intentionally ignores the second ECU/FID inventory. No tool source, calibration XML, ROM, A2L, workbook baseline, Findings record or worker lane was modified.

## Findings disposition
**NOT REQUIRED** — no physical calibration interpretation was promoted. This is an identifier/registry normalization and scan-coverage reconciliation only.
