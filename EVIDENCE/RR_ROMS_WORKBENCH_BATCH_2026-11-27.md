# RR ROMs folder — SH705x workbench batch (2026-11-27)

**Result:** COMPLETE — all supported unique ROM containers scanned; RomRaider reference index built successfully.  
**Input folder:** `EVIDENCE/rr roms/`  
**Workbench:** `tools/nissan_sh705x_workbench.py` — standard `scan` plus `ref-index build`; read-only inputs.  
**Execution:** GitHub Actions run [46022573374](https://github.com/ihatealladvertising/EL19A-/actions/runs/46022573374), repository commit `0590f0cf9cb4222474456db111c9fe2665f59a32`, Python 3.11.18.  
**Outputs:** GitHub Actions artifact `rr-roms-workbench-batch`, artifact ID `15208363827`, 24,496,815 bytes, SHA-256 `74eb21c751fdd55463ce4bde70d02e745c07f686c343f1cc2a391280a12e7544` (artifact retention through 2026-12-11). The bundle contains 809 files: inventory/summary, per-ROM scan JSON, table TSV, lossless catalogue JSON, run manifests, stdout/stderr logs, and the combined reference index.

## Folder disposition

| Disposition | Count | Detail |
|---|---:|---|
| Unique ROM containers scanned | 134 | All 134 returned exit code 0 |
| Exact container duplicates | 2 | Not rescanned; both paths retained in the inventory |
| Unsupported-extension entries | 25 | 11 RAR, 5 7z, 7 XML, 1 PDF, 1 extensionless one-byte file |
| Total folder entries | 161 | No input file modified |

The two exact container duplicates were:
- `1CC02A-20180728-160303.bin.zip` → identical to `1CC02A-20180728-160303.bin(1).zip`
- `2002infinitiG20SPORTstockrom.bin` → identical to `2002infinitiG20SPORTstockrom(1).bin`

The seven top-level XML definition files were not passed to `scan`; all seven were included in the reference-index build. The 11 RAR and 5 7z containers were not scanned because the current loader supports BIN/ZIP/S19/HEX/DAT, not RAR/7z.

## Scan results

| Metric | Result |
|---|---:|
| Scan-success ROM containers | 134 / 134 |
| Distinct decoded ROM SHA-256 groups | 130 |
| Decoded-image duplicate groups | 4 |
| CPU/FID-family identified | 126 |
| CPU/FID not identified | 8 |
| Helper detections summed across scans | 3,234 |
| Lookup call sites | 32,757 |
| Resolved lookup calls | 29,540 |
| Unique table instances summed across ROMs | 23,480 |

CPU tags among the 126 identified images:

| CPU | ROMs |
|---|---:|
| SH705513N | 34 |
| SH705507N | 30 |
| SH705821N | 17 |
| SH705823N | 11 |
| SH705828N | 9 |
| SH705822N | 8 |
| SH705101N | 6 |
| SH705927N | 5 |
| SH705520N | 4 |
| SH705524N | 1 |
| SH705415N | 1 |

The nine SH705828N inputs are:
- `14ME6B_2XHK19BDF1-20180703-184814.bin.zip` — FID `2XHK1Q4DP`, 511 tables
- `14ME6B_2XHK19BDF1-20180802-181458.bin.zip` — FID `2XHK1Q4DP`, 511 tables
- `19GC4B_stock.zip` — FID `4ZHPGN2`, 432 tables
- `1A16A_Stock.zip` — FID `2XHK1QKDQ`, 511 tables
- `2020651123.bin.zip` — FID `11ZVK2GN51`, 423 tables
- `Nissan_Juke_1.6L_MT_94hp_2014Y_11KE6C_2XHK19BDF1_PCMFlash.zip` — FID `2XHK19BDF1`, 503 tables
- `unknown_1KA6A_SH7058.bin.zip` — FID `1XHK14CDG`, 465 tables
- `unknown_1KE9C_SH7058.bin.zip` — FID `2XHK19BDF1`, 503 tables
- `unknown_1KN0B_SH7058.bin.zip` — FID `0KHD95DZ3`, 580 tables

Four different container files decoded to duplicate images:
- `1cd700.bin.zip` and `350z_cd700_2003.bin.zip`
- `23710-AM905.bin.zip` and `AM905_7055_20190313.bin.zip`
- `9J00B.bin(1).zip` and `9j00b.bin.zip`
- `cd006.bin.zip` and `cd006_dump.bin.zip`

## RomRaider reference-index result

The workbench `ref-index build` completed with exit code 0 using all 134 successfully scanned ROM containers and all seven XML inputs.

| Index metric | Result |
|---|---:|
| ROM signature records | 134 |
| XML source documents | 7 (all parse status `ok`) |
| XML table declarations | 1,050 (duplicate XML sources retained) |
| Distinct XML storage-address keys | 505 |
| Distinct exact-payload hash/length keys | 3,425 |
| Distinct code-region hash keys | 123 |

The seven XML inputs were:
- `6J107_RomRaider.xml` — 252 tables
- `6J109_RomRaider-1.xml` — 252 tables
- `6J109_RomRaider.xml` — 252 tables; byte-identical to the preceding file
- `6Y324.xml` — 1 table
- `9J00B.xml` — 23 tables
- `CF49A-1.xml` — 135 tables
- `CF49A.xml` — 135 tables; byte-identical to the preceding file

No A2L file was supplied from this folder, so this batch indexed the RomRaider XML corpus and ROM signatures/payloads, not A2L symbol metadata.

## Checksum diagnostics requiring separate interpretation

The tool reported:
- `ck_std`: 90 OK; no BAD result.
- `ck_alt2`: one BAD result — `testrr.bin.zip`.
- `cal16`: 22 OK, 3 BAD — `E1JA01C.zip`, `E1JB00E.zip`, `Q1_JA93A.zip`.
- `main16`: 21 OK, 4 BAD — those same three files plus `z34_2017_stock_ROM.bin.zip`.

The three E1J/Q1 files are among the eight inputs with no detected CPU/FID and zero helpers/tables. These are diagnostic mismatches, not proof of corrupted files; applicability of each checksum convention/layout must be established before treating a BAD flag as a defect.

The eight successfully loaded images with no CPU/FID tag and zero helper/table detections were:
`14CE1A_F4KH1DQGNV1-20201114-110908.bin.zip`, `14EF2A_F4KH1DQGNV1-stok_2.0CVT4WD.bin.zip`, `14HF2A_F5FZ5TZHNR1.zip`, `2006 Altima 25 Auto.zip`, `E1JA01C.zip`, `E1JB00E.zip`, `Q1_JA93A.zip`, and `XTrail_T30.bin.zip`. Their format/processor identity remains unclassified.

## Reproducibility and evidence boundary

- Workbench repository commit: `0590f0cf9cb4222474456db111c9fe2665f59a32`.
- `tools/nissan_sh705x_workbench.py` SHA-256: `30e39d0774d144dd3d8fe7d9b5b95ed118fb9e785a05d51b138b1a13b0f4076a`.
- `tools/sh705x_rom_loader.py` SHA-256: `34d343f0aef64590a6b36930d008c659e1a1b901b7be254fd3b4fcde29147098`.
- `tools/sh7058_cross_rom_scanner.py` SHA-256: `ec0ba0d40a7c4a444b94a123be8426584724453a394ed8e8097f3d123982532d`.
- `tools/sh705x_discovery_v2.py` SHA-256: `ca72e863b7960c7608b25f1b57225b3c46c2f57efedbf1025ef0584ba600533a`.
- `tools/romraider_ref_index.py` SHA-256: `206f99ff2ea8f3c9e961353a0cd94059d22be9b62d9ea4a0ac97547de2f12f1e`.
- The scan was the standard workbench `scan` path with TSV, JSON, lossless per-address catalogue and run manifest exports. No enhanced-window or scalar-discovery flags were enabled.
- All ROM inputs were read-only. No A2L, XML definitions, calibration XML, workbook, catalogue, scope matrix, Findings, tool source or existing workflows were changed by the analysis.
- Donor/ROM fingerprint, exact payload and XML address matches remain structural leads; they do not establish target-side calibration semantics or authorize definition promotion.
