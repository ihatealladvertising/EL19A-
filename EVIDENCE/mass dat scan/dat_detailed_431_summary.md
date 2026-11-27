# Detailed SH705x Workbench Summary — 431 Direct `.dat` Results

**Work order:** REPROPROGRAMMING-BATCH-2026-11-27 (closed)  
**Input folder:** `E:\Nissan Consult\ReproProgramming`  
**Workbench revision:** `13acc0b58826c2b693ef495a0b3c61259daec760`  
**Runtime:** Python 3.12.10; py7zr 1.1.4  
**Source result:** `scan_results.tsv` joined to the 431 records in `scan_details.jsonl.gz` using the deduplicated `input_key`.

## Executive result

The folder contained **11,740 direct `.dat` source references**, representing **11,668 unique `.dat` payloads** after byte-identical deduplication. Of these, **9,186** loaded as ROM candidates and were scanned; **2,482** were rejected by the loader. **431 unique scanned `.dat` payloads** produced non-empty helper, call-site, and table detail records. The other **8,755 successfully loaded `.dat` payloads** had no detailed helper/table record in this run.

The 431 are **ROM snapshots with static discovery output**, not 431 newly identified EL19A calibrations. Table counts recur across related ROM revisions; they are per-input detections and must not be summed as unique project-wide calibration objects. FID strings are recorded as detected metadata/tokens, not as independently authenticated vehicle identities.

## Coverage and scan outcomes

| Measure | Result |
|---|---:|
| Direct `.dat` source references | 11,740 |
| Unique direct `.dat` payloads | 11,668 |
| Unique payloads scanned | 9,186 |
| Unique payloads rejected | 2,482 |
| Detailed positive payloads | 431 |
| Source paths represented among detailed payloads | 431 |
| ROM images represented among detailed payloads (512 KiB) | 313 |
| ROM images represented among detailed payloads (1 MiB) | 118 |

### Frequent loader rejection messages

These are loader outcomes, not proof that every rejected file is corrupt. The loader may not recognize a Consult container or may correctly classify a partial calibration payload as not being a full ECU image.

| Rejection message | Unique payloads |
|---|---:|
| ValueError: Unrecognized Consult .dat container format | 1,484 |
| ValueError: Unexpected Consult .dat frame command 3481 at 0x25 | 35 |
| ValueError: Unexpected Consult .dat frame command 3481 at 0x34 | 3 |
| ValueError: Unencrypted KWP2000 partial calibration .dat (header='BF10EO4BE7679R0HY00E', 45516 verified frames covering 0x10000..0x8C3FA7) is not a full SH705x ECU image. | 1 |
| ValueError: Unencrypted KWP2000 partial calibration .dat (header='BF11BO4BE7679R0HY00E', 45515 verified frames covering 0x10000..0x8C3FA7) is not a full SH705x ECU image. | 1 |
| ValueError: Unencrypted KWP2000 partial calibration .dat (header='BR30BA4BEJD580 26014', 25844 verified frames covering 0x480000..0x87C9E7) is not a full SH705x ECU image. | 1 |
| ValueError: Unencrypted KWP2000 partial calibration .dat (header='BR32A4BEJD50026013', 21323 verified frames covering 0x480000..0x87C9E7) is not a full SH705x ECU image. | 1 |
| ValueError: Unencrypted KWP2000 partial calibration .dat (header='BR33A4BEJD500`26013', 21323 verified frames covering 0x480000..0x87C9E7) is not a full SH705x ECU image. | 1 |
| ValueError: Unencrypted KWP2000 partial calibration .dat (header='JD58DA4BEJD580 p26014', 5028 verified frames covering 0x840000..0x87C9E7) is not a full SH705x ECU image. | 1 |
| ValueError: Unencrypted KWP2000 partial calibration .dat (header='BF10DO4BE6350R&HY00Ef', 45320 verified frames covering 0x10000..0x8C3A8F) is not a full SH705x ECU image. | 1 |
| ValueError: Unencrypted KWP2000 partial calibration .dat (header='HY03BO4BE7679R sHY00E', 45410 verified frames covering 0x10000..0x8C3B73) is not a full SH705x ECU image. | 1 |
| ValueError: Unencrypted KWP2000 partial calibration .dat (header='HY02EO4BE6350RrHY00E', 45320 verified frames covering 0x10000..0x8C3A8F) is not a full SH705x ECU image. | 1 |

## What the 431 detailed inputs contain

- **Helper detections:** 15,131 total across per-ROM snapshots; median 34 per input; range 34–37.
- **Table detections:** 128,307 total across snapshots, of which **73,401** were marked non-trivial by the workbench. Median 274 tables per input; range 251–421.
- **Call-site/table associations:** 157,369 summed associations. There were 157,369 unique call PCs when counted separately within each input (the same code PC can recur in related snapshots).
- **Address recurrence:** 838 distinct helper addresses and 6,599 distinct table addresses across the 431 snapshots. The most repeated table placements are listed below.
- **Summed table extents:** 6,271,172 bytes over per-ROM detections; this intentionally counts repeated addresses in different ROM snapshots.

### Helper discovery kinds

| Kind | Per-ROM detections across 431 inputs |
|---|---:|
| 3D_AXIS | 6,677 |
| 2D_IMPL | 3,870 |
| 2D_AXIS | 3,529 |
| 3D_IMPL | 1,055 |

### Table discovery kinds

| Kind | Per-ROM detections across 431 inputs |
|---|---:|
| 2D_IMPL | 71,188 |
| 2D_AXIS | 34,801 |
| 3D_AXIS | 20,269 |
| 3D_IMPL | 2,049 |

### Table element types and common geometries

| Element type | Detections |
|---|---:|
| uint8 | 86,598 |
| uint16 | 41,709 |

| Kind / element type / geometry | Detections |
|---|---:|
| 2D_IMPL:uint8:8x1 | 30,688 |
| 2D_IMPL:uint8:16x1 | 23,082 |
| 2D_AXIS:uint8:8x1 | 12,832 |
| 2D_AXIS:uint16:16x1 | 7,777 |
| 2D_AXIS:uint16:8x1 | 6,723 |
| 2D_IMPL:uint16:16x1 | 6,604 |
| 2D_IMPL:uint16:8x1 | 6,422 |
| 3D_AXIS:uint8:8x8 | 5,090 |
| 3D_AXIS:uint16:16x16 | 4,935 |
| 2D_AXIS:uint16:32x1 | 4,478 |
| 3D_AXIS:uint8:4x4 | 4,297 |
| 3D_AXIS:uint8:16x16 | 3,173 |
| 2D_AXIS:uint8:16x1 | 2,991 |
| 3D_AXIS:uint16:8x8 | 2,736 |
| 2D_IMPL:uint8:4x1 | 2,031 |
| 3D_IMPL:uint8:8x8 | 1,425 |
| 2D_IMPL:uint16:4x1 | 1,144 |
| 2D_IMPL:uint8:32x1 | 795 |
| 3D_IMPL:uint16:16x16 | 468 |
| 2D_IMPL:uint16:64x1 | 381 |
| 3D_IMPL:uint8:16x16 | 156 |
| 2D_IMPL:uint16:32x1 | 41 |
| 3D_AXIS:uint8:2x2 | 38 |

## FID and CPU metadata

### Primary FID field from the workbench fingerprint metadata

| FID | Inputs |
|---|---:|
| 9CMCVAPD31 | 40 |
| I9CMCHVPD6 | 38 |
| 1CMCHXPD7 | 35 |
| 2JCS62D8 | 32 |
| 1CMC7QPD4 | 32 |
| Z3CMCJSPD4 | 32 |
| 4CMCB1PDM1 | 32 |
| 2XH5EJ7G2 | 22 |
| 2JCSSKDD | 19 |
| 2XH5ET6G3 | 14 |
| 2XH5EUXG4 | 12 |
| H1CMC7Q4003 | 10 |
| 1CMC7QPD44 | 9 |
| 1CMC6GPDA | 9 |
| 1CMCA1PDB | 9 |

### Most common detected FID tokens

The token matcher can find incidental strings; treat these as search leads unless supported by the fingerprint metadata and source provenance.

| Token | Inputs carrying token |
|---|---:|
| 000000L9 | 92 |
| 000000YC | 92 |
| 999FFFFC | 81 |
| 0PPPPPPP | 79 |
| 111113CJ | 69 |
| 666668JR | 69 |
| 900RRRRR | 59 |
| 1CMC7QPD | 54 |
| 66TTTTHE | 50 |
| 55GGGGGE | 50 |
| 3ZZZZZZZ | 50 |
| 9CMCVAPD | 40 |

### CPU tags

| CPU tag | Inputs |
|---|---:|
| SH705519N | 241 |
| SH705828N | 118 |
| SH705520N | 72 |

## Checksum metadata status

Counts below are across the 431 detailed inputs. `NOT_REPORTED` means no status was included in the fingerprint output; it does not mean failure.

| Checksum family | Status | Inputs |
|---|---|---:|
| ck_std | NOT_REPORTED | 359 |
| ck_std | OK | 72 |
| ck_alt2 | NOT_REPORTED | 241 |
| ck_alt2 | OK | 190 |
| cal16 | OK | 359 |
| cal16 | NOT_REPORTED | 72 |
| main16 | OK | 359 |
| main16 | NOT_REPORTED | 72 |

## Highest-detail input snapshots

Table counts are per snapshot; matching addresses in different revisions are repeated.

| Source file(s) | Primary FID | ROM bytes | Helpers | Calls | Tables | Non-trivial tables | SHA-256 |
|---|---|---:|---:|---:|---:|---:|---|
| 237105LJ0A.dat | 6JCS7JD1 | 1048576 | 37 | 516 | 421 | 221 | `07832a8231ded2852b0a0f08301d852c51497baa11d8044c8992e899e82e4b57` |
| 237105LK0A.dat | 6JCSF9D2 | 1048576 | 37 | 516 | 421 | 218 | `1307db075e73a6341366a381715f6d77c6575e4924737184b7c42b347521b8a8` |
| 237105UN2A.dat | 6JCS7JD1 | 1048576 | 37 | 516 | 421 | 217 | `a24d55039f8ad65e9c9965c07b0ca52adf994b54341bd5d04485dc94dfac4a15` |
| 237105UN3A.dat | 6JCS7JD1 | 1048576 | 37 | 516 | 421 | 217 | `4845cb740646a61b970b1556c316ab6e5a32596a1e5bba478c5614fd475828fd` |
| 237101FB1D.dat | 2JCSXKDF | 1048576 | 37 | 499 | 410 | 256 | `017ce6492800fa39c043fb98045e4e0fb24ba437845f0435b9bbc29c33d88dc0` |
| 237101FB2D.dat | 2JCSXKDF | 1048576 | 37 | 499 | 410 | 256 | `6bba39f09de218e8f419aa727c32f1d8d6d3bf3b8cf9223437b4dff8739d4f6d` |
| 237101HN2A.dat | 2JCSKHDB | 1048576 | 37 | 499 | 410 | 222 | `2e53bbb30809c0810c014ea4f3210f1a7d71aec7702de30e1f89a1ff89454059` |
| 237101PW2A.dat | 2JCSSKDD | 1048576 | 37 | 499 | 410 | 216 | `3d7b8ec08b3a23085dfe665f6a2249438185d1c6ceaf738d159cca9a68664ffd` |
| 237101PW2B.dat | 2JCSSKDD | 1048576 | 37 | 499 | 410 | 216 | `a58f6e0d0afd64fdfff5ed5e711fe26ebe82427380eff62fbfbd2445693d572c` |
| 237101PW3A.dat | 2JCSSKDD | 1048576 | 37 | 499 | 410 | 216 | `0ce00c29b6804c202bd1d467d5c6a98431586b34d86e9be621a7a6f5fdf38351` |
| 237101PW3B.dat | 2JCSSKDD | 1048576 | 37 | 499 | 410 | 216 | `d453aeb5d61b8ad09ab9eff0cd2de0c9b0c7c924d842b0d3cf776d093195edc6` |
| 237102FJ2A.dat | 2JCSSKDD | 1048576 | 37 | 499 | 410 | 214 | `ee8c449f9bb7002018a431262a057210e7c78d20d1591a67a75f7c2720376d72` |
| 237102FJ3A.dat | 2JCSSKDD | 1048576 | 37 | 499 | 410 | 217 | `1b6895abda91b8a85a19ef1fc290881d18bca639938718047fc44b5bfc314ac3` |
| 237102FL1B.dat | 2JCSSKDD | 1048576 | 37 | 499 | 410 | 215 | `b65c4e71b0c805bcc03e7f02bbab6b9cdec628c917ce6c320bc8a496fe02575a` |
| 237102GB1A.dat | 2JCSSKDD | 1048576 | 37 | 499 | 410 | 217 | `d46dccd4905ffa97bf4712a15f541c0d47ccfd798584212e40858be2534677d0` |

## Most frequently recurring table addresses

| Address | Number of detailed snapshots containing address |
|---|---:|
| `0x0C232` | 144 |
| `0x0B851` | 142 |
| `0x0B9FD` | 142 |
| `0x0C15A` | 140 |
| `0x0B9ED` | 137 |
| `0x115FC` | 136 |
| `0x0C262` | 135 |
| `0x0B9DD` | 134 |
| `0x0BA0D` | 134 |
| `0x0BA2D` | 134 |
| `0x0BA3D` | 134 |
| `0x0B7CD` | 129 |
| `0x0BA45` | 129 |
| `0x0B66B` | 124 |
| `0x0BD19` | 112 |

## Interpretation and limits

- The workbench used fingerprinting, helper discovery, call extraction, and table summarization. The report does **not** establish table names, units, conversions, query-axis meaning, ECU application, or vehicle behavior.
- Repeated detections across related images are useful for revision-family comparison but are not independent semantic confirmation. A positive table detection says the workbench found a structural candidate in that image.
- Several detected geometries use implicit or helper-derived axes. Their output is a structural lead; axis orientation and physical meaning require target-side confirmation for the ROM being defined.
- The 431 detailed payloads were selected by non-empty workbench helper/table results. This is a detailed subset of the `.dat` batch, not a separate validation set.
- No source ROM or `.dat` file was modified; this summary and its TSV are additive run outputs.

## Companion data and provenance

- `dat_detailed_431_results.tsv` contains one row per unique detailed `.dat` payload, with source path(s), full payload SHA-256, CPU/FID metadata, checksum outcomes, helper/table kinds, counts, addresses, and call-PC summaries.
- `scan_details.jsonl.gz` retains all 431 detailed JSON records.
- `scan_results.tsv` retains loader status and per-source-reference outcomes for the full batch.
- Batch manifest: `run_manifest.json`.
