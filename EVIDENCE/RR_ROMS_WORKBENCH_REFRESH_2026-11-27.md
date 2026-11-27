# RR ROMs folder — refreshed SH705x workbench batch (2026-11-27)

**Result:** COMPLETE — 150 unique supported ROM containers scanned successfully; combined ROM/RomRaider reference index rebuilt successfully.  
**Input folder:** `EVIDENCE/rr roms/`  
**Previous batch:** [RR_ROMS_WORKBENCH_BATCH_2026-11-27.md](RR_ROMS_WORKBENCH_BATCH_2026-11-27.md)  
**Workbench:** `tools/nissan_sh705x_workbench.py`, unchanged from the previous batch.  
**Execution:** [GitHub Actions run 46023911353](https://github.com/ihatealladvertising/EL19A-/actions/runs/46023911353), repository commit `61a21947f81732bbaa71b361018a36281aa98c7c`, Python 3.11.18.  
**Artifact:** `rr-roms-workbench-refresh`, ID `15210278286`, 27,635,918 bytes, SHA-256 `951da219fb1a9e9aa6f26c4add239421a62ce5ed81af579bfcc3d1a58e015eed`; retained through 2026-12-11. Contains 905 files: per-ROM scans, TSVs, lossless catalogues, run manifests, logs, inventory, summary and combined reference index.

## Folder and batch reconciliation

The folder now contains 177 entries, up from 161 in the previous batch. The user added 16 extracted BIN images corresponding to the previously supplied RAR/7z submissions. All 16 new BINs were loaded and scanned successfully.

| Disposition | Count | Detail |
|---|---:|---|
| Unique ROM containers scanned | 150 | All 150 returned exit code 0 |
| Exact container duplicates | 2 | Not rescanned; paths retained |
| Skipped non-ROM/unsupported entries | 25 | 11 original RAR + 5 original 7z + 7 XML + 1 PDF + 1 extensionless one-byte file |
| Total folder entries | 177 | No input file modified |

The 16 extracted BIN names processed were:
- `03 Frontier D22 KA24DE USDM Calif 1Q4MDR.bin`
- `23710-WL60B.bin`
- `28.03.21 CD008 Stock.bin`
- `7y006.bin`
- `9GC4B.bin`
- `AT30A_F50.bin`
- `CF020 Stock.bin`
- `CM30Bstock_rom.bin`
- `FIRST ALTIMA DUMP 1ZD89B-20240813-143342.bin`
- `JK78C.bin`
- `M5113Nismo.bin`
- `Micra K12 CR12 MEC32 AY301 2005.bin`
- `Nissan_Primera_2005_QR20DE_103kW_CVT_1BA060_705513N.bin`
- `SH705507N_23710-AS700_1AS700.BIN.bin`
- `my_rom 7055_35.bin`
- `my_rom_2Y110_read_w_2sidkey.bin`

The original 16 RAR/7z archives remain in the folder and are still skipped by their archive extensions. This refresh did not add RAR/7z loader support; it scanned the extracted BINs. The two exact container duplicates remain:
- `1CC02A-20180728-160303.bin.zip` → identical to `1CC02A-20180728-160303.bin(1).zip`
- `2002infinitiG20SPORTstockrom.bin` → identical to `2002infinitiG20SPORTstockrom(1).bin`

## Aggregate workbench result

| Metric | First batch (161 entries) | Refreshed batch (177 entries) | Increase |
|---|---:|---:|---:|
| Successful unique ROM scans | 134 | 150 | +16 |
| Distinct decoded ROM SHA-256 groups | 130 | 146 | +16 |
| Identified CPU/FID ROMs | 126 | 142 | +16 |
| Helper detections summed across scans | 3,234 | 3,644 | +410 |
| Lookup call sites | 32,757 | 36,944 | +4,187 |
| Resolved lookup calls | 29,540 | 33,220 | +3,680 |
| Aggregate unique table instances | 23,480 | 26,444 | +2,964 |

All 16 new BINs have a detected Nissan FID and CPU tag. Their decoded ROM SHA-256 values are distinct from the prior 134-image corpus and from each other: the decoded-image group count therefore increases from 130 to 146 without increasing the four previously existing decoded-duplicate groups.

CPU-family counts in the refreshed 150-image corpus:

| CPU | ROMs |
|---|---:|
| SH705513N | 39 |
| SH705507N | 34 |
| SH705821N | 18 |
| SH705823N | 13 |
| SH705828N | 10 |
| SH705822N | 9 |
| SH705101N | 7 |
| SH705927N | 5 |
| SH705520N | 4 |
| SH705415N | 2 |
| SH705524N | 1 |
| Unidentified | 8 |

The eight unidentified images are unchanged from the first batch:
`14CE1A_F4KH1DQGNV1-20201114-110908.bin.zip`, `14EF2A_F4KH1DQGNV1-stok_2.0CVT4WD.bin.zip`, `14HF2A_F5FZ5TZHNR1.zip`, `2006 Altima 25 Auto.zip`, `E1JA01C.zip`, `E1JB00E.zip`, `Q1_JA93A.zip`, and `XTrail_T30.bin.zip`.

## Results for the 16 added BIN images

Each value below is the workbench result for that file, not a semantic calibration count.

| BIN | FID | CPU | Resolved calls | Unique tables |
|---|---|---|---:|---:|
| `03 Frontier D22 KA24DE USDM Calif 1Q4MDR.bin` | `1Q4MDRNX` | SH705507N | 0 | 0 |
| `23710-WL60B.bin` | `2WLVED18` | SH705513N | 253 | 212 |
| `28.03.21 CD008 Stock.bin` | `3GIPAN07` | SH705513N | 269 | 221 |
| `7y006.bin` | `4XXES9NP` | SH705513N | 283 | 232 |
| `9GC4B.bin` | `4ZHPGN2` | SH705828N | 529 | 432 |
| `AT30A_F50.bin` | `M3ZHEUSD8` | SH705507N | 0 | 0 |
| `CF020 Stock.bin` | `5ZVSVNJ` | SH705821N | 344 | 269 |
| `CM30Bstock_rom.bin` | `6ZV2RN10` | SH705823N | 356 | 278 |
| `FIRST ALTIMA DUMP 1ZD89B-20240813-143342.bin` | `6X6E58SYMN36` | SH705823N | 325 | 266 |
| `JK78C.bin` | `7MFV68NV` | SH705822N | 618 | 464 |
| `M5113Nismo.bin` | `N1MATBH5D5` | SH705507N | 0 | 0 |
| `Micra K12 CR12 MEC32 AY301 2005.bin` | `2MME4LGE7` | SH705415N | 226 | 192 |
| `Nissan_Primera_2005_QR20DE_103kW_CVT_1BA060_705513N.bin` | `3TRRNE5` | SH705513N | 251 | 211 |
| `SH705507N_23710-AS700_1AS700.BIN.bin` | `1NET665D5` | SH705507N | 0 | 0 |
| `my_rom 7055_35.bin` | `2WLVDD06` | SH705513N | 226 | 187 |
| `my_rom_2Y110_read_w_2sidkey.bin` | `8ZV4Q1DN` | SH705101N | 0 | 0 |

Five new BINs returned no resolved lookup calls: Frontier (193 calls but none resolved), AT30A_F50 (zero helpers), M5113Nismo (zero helpers), SH705507N_23710-AS700 (zero helpers), and my_rom_2Y110 (121 calls but none resolved). These remain successfully loaded/fingerprinted, but their calibration table inventory is empty in this scan and should not be represented as a positive table discovery.

The 11 other new BINs account for all 4,187 call sites, 3,680 resolved calls and 2,964 unique table instances added by this refresh.

## Reference-index result

The `ref-index build` completed with exit code 0 using all 150 successfully scanned ROM containers and all seven top-level XML inputs.

| Index metric | Result |
|---|---:|
| ROM signature records | 150 |
| XML source documents | 7 |
| Distinct XML storage-address keys | 505 |
| Distinct exact-payload hash/length keys | 3,790 |
| Distinct code-region hash keys | 138 |
| Reference index JSON SHA-256 | `2daba4660c89a1b2a09f51f322645d04463c20c7c2c7fee95acd0817e81f57cf` |

The XML source set and 505 XML address keys are unchanged from the first batch. No A2L was added to this folder, so the reference index remains a ROM-signature/exact-payload/RomRaider-XML index rather than a relational A2L index.

## Checksum diagnostics

Across the refreshed 177-entry inventory (checksums are only reported where the workbench recognized a relevant layout):
- `ck_std`: 101 OK; no BAD result.
- `ck_alt2`: one BAD result — `testrr.bin.zip`.
- `cal16`: 24 OK, 3 BAD — `E1JA01C.zip`, `E1JB00E.zip`, `Q1_JA93A.zip`.
- `main16`: 23 OK, 4 BAD — those same three files plus `z34_2017_stock_ROM.bin.zip`.

None of the 16 new BINs produced a BAD checksum result. These diagnostics are not, by themselves, proof of corruption; applicability of the checksum convention and layout must be established first.

## Reproducibility and evidence boundary

- Workbench repository commit: `61a21947f81732bbaa71b361018a36281aa98c7c`.
- Python: `3.11.18`.
- Tool hashes unchanged from the first batch:
  - `tools/nissan_sh705x_workbench.py`: `30e39d0774d144dd3d8fe7d9b5b95ed118fb9e785a05d51b138b1a13b0f4076a`
  - `tools/sh705x_rom_loader.py`: `34d343f0aef64590a6b36930d008c659e1a1b901b7be254fd3b4fcde29147098`
  - `tools/sh7058_cross_rom_scanner.py`: `ec0ba0d40a7c4a444b94a123be8426584724453a394ed8e8097f3d123982532d`
  - `tools/sh705x_discovery_v2.py`: `ca72e863b7960c7608b25f1b57225b3c46c2f57efedbf1025ef0584ba600533a`
  - `tools/romraider_ref_index.py`: `206f99ff2ea8f3c9e961353a0cd94059d22be9b62d9ea4a0ac97547de2f12f1e`
- Each ROM was run through standard `scan` with TSV, JSON, lossless per-address catalogue and run-manifest outputs. No enhanced-window or scalar-discovery flags were enabled.
- Run elapsed time reported by the runner: 177.868 seconds.
- Artifact ZIP SHA-256 independently verified after retrieval: `951da219fb1a9e9aa6f26c4add239421a62ce5ed81af579bfcc3d1a58e015eed`.
- All ROM inputs were read-only. No ROM, S19, BIN, ZIP, XML definition, A2L, calibration, workbook, catalogue, scope matrix, Findings, tool source or existing workflow was modified.
- Cross-ROM table inventories, donor fingerprints, exact payload hashes and XML address matches remain structural evidence/leads; none alone establishes calibration semantics or authorizes a RomRaider definition change.
