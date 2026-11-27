# Table-layout similarity across the 431 detailed DAT ROMs

**EL19A reference (pairwise metrics below are DAT-vs-DAT; direct target matches are in the companion report):** EL19A VERSA f501.bin, 1 MiB, SHA-256 `bfe037e8e6c389e2a90214047058eb6dc3bcaaaac5b5931bf98a3f5d9f64fd6a`.  
**Population:** the 431 unique direct-DAT payloads whose workbench scan produced detailed helper/table records. Other loaded files produced no table-detail records; loader-rejected files have no decoded layout to compare.  
**Pair count:** 92,665 ROM pairs (same 1-MiB size: 6,903; same 512-KiB size: 48,828; cross-size: 36,934).

## What “layout similarity” means here

- **Address Jaccard:** overlap of table start addresses, ignoring geometry.
- **Strict layout Jaccard:** overlap of address + end/extent + table kind + element type + dimensions + axis storage types.
- **Geometry multiset Jaccard:** similarity of table kind/type/dimensions/axis-type counts while ignoring addresses; repeated counts are retained.
- **Axis-pointer agreement:** separately counts exact equality of axis table addresses where table geometry already matches at a shared address.

These are workbench structural summaries, not semantic equivalence. Call PCs and payload values are not part of strict layout identity.

## Pairwise summary

| Comparison group | Pairs | Median address Jaccard | Median strict layout Jaccard | Median geometry multiset Jaccard | Pairs strict ≥90% | Pairs strict ≥95% | Same-primary-FID pairs |
|---|---:|---:|---:|---:|---:|---:|
| All pairs | 92,665 | 0.37% | 0.00% | 86.90% | 6.81% | 6.81% | 4,939 |
| Same-size 512 KiB pairs | 48,828 | 0.57% | 0.00% | 89.01% | 10.29% | 10.29% | 3,723 |
| Same-size 1 MiB pairs | 6,903 | 0.74% | 0.17% | 98.79% | 18.67% | 18.67% | 1,216 |
| Cross-size pairs | 36,934 | 0.15% | 0.00% | 64.98% | 0.00% | 0.00% | 0 |

### Same-FID comparison

There are 4,939 pairs sharing a non-empty primary FID. Their median strict-layout Jaccard is 100.00% and median geometry-multiset Jaccard is 100.00%. The remaining 87,726 pairs have median strict-layout Jaccard 0.00%.

## Highest strict layout matches

| Rank | ROM A (FID) | ROM B (FID) | Shared/union tables | Strict layout Jaccard | Address Jaccard | Geometry multiset Jaccard | Same FID? |
|---:|---|---|---:|---:|---:|---:|:---:|
| 1 | 237101A14A.dat (1CMCHXPD7) | 237101HA2B.dat (1CMCHXPD7) | 268/268 | 100.00% | 100.00% | 100.00% | yes |
| 2 | 237101A14A.dat (1CMCHXPD7) | 237101HA3B.dat (1CMCHXPD7) | 268/268 | 100.00% | 100.00% | 100.00% | yes |
| 3 | 237101A14A.dat (1CMCHXPD7) | 237101HS0E.dat (1CMCHXPD7) | 268/268 | 100.00% | 100.00% | 100.00% | yes |
| 4 | 237101A14A.dat (1CMCHXPD7) | 237102ZS20.dat (1CMCHXPD7) | 268/268 | 100.00% | 100.00% | 100.00% | yes |
| 5 | 237101A14A.dat (1CMCHXPD7) | 237102ZS6A.dat (1CMCHXPD7) | 268/268 | 100.00% | 100.00% | 100.00% | yes |
| 6 | 237101A14A.dat (1CMCHXPD7) | 237103AA7B.dat (1CMCHXPD7) | 268/268 | 100.00% | 100.00% | 100.00% | yes |
| 7 | 237101A14A.dat (1CMCHXPD7) | 237103AA8B.dat (1CMCHXPD7) | 268/268 | 100.00% | 100.00% | 100.00% | yes |
| 8 | 237101A14A.dat (1CMCHXPD7) | 237103AT0A.dat (1CMCHXPD7) | 268/268 | 100.00% | 100.00% | 100.00% | yes |
| 9 | 237101A14A.dat (1CMCHXPD7) | 237103AU0A.dat (1CMCHXPD7) | 268/268 | 100.00% | 100.00% | 100.00% | yes |
| 10 | 237101A14A.dat (1CMCHXPD7) | 237103AU0C.dat (1CMCHXPD7) | 268/268 | 100.00% | 100.00% | 100.00% | yes |
| 11 | 237101A14A.dat (1CMCHXPD7) | 237103AU1A.dat (1CMCHXPD7) | 268/268 | 100.00% | 100.00% | 100.00% | yes |
| 12 | 237101A14A.dat (1CMCHXPD7) | 237103AU1C.dat (1CMCHXPD7) | 268/268 | 100.00% | 100.00% | 100.00% | yes |
| 13 | 237101A14A.dat (1CMCHXPD7) | 237103AU2A.dat (1CMCHXPD7) | 268/268 | 100.00% | 100.00% | 100.00% | yes |
| 14 | 237101A14A.dat (1CMCHXPD7) | 237103AU3A.dat (1CMCHXPD7) | 268/268 | 100.00% | 100.00% | 100.00% | yes |
| 15 | 237101A14A.dat (1CMCHXPD7) | 237103AU3C.dat (1CMCHXPD7) | 268/268 | 100.00% | 100.00% | 100.00% | yes |
| 16 | 237101A14A.dat (1CMCHXPD7) | 237103AU4B.dat (1CMCHXPD7) | 268/268 | 100.00% | 100.00% | 100.00% | yes |
| 17 | 237101A14A.dat (1CMCHXPD7) | 237103AU4C.dat (1CMCHXPD7) | 268/268 | 100.00% | 100.00% | 100.00% | yes |
| 18 | 237101A14A.dat (1CMCHXPD7) | 237103AU5B.dat (1CMCHXPD7) | 268/268 | 100.00% | 100.00% | 100.00% | yes |
| 19 | 237101A14A.dat (1CMCHXPD7) | 237103AU6B.dat (1CMCHXPD7) | 268/268 | 100.00% | 100.00% | 100.00% | yes |
| 20 | 237101A14A.dat (1CMCHXPD7) | 237103BJ0A.dat (1CMCHXPD7) | 268/268 | 100.00% | 100.00% | 100.00% | yes |
| 21 | 237101A14A.dat (1CMCHXPD7) | 237103BJ1A.dat (1CMCHXPD7) | 268/268 | 100.00% | 100.00% | 100.00% | yes |
| 22 | 237101A14A.dat (1CMCHXPD7) | 237103BN0A.dat (1CMCHXPD7) | 268/268 | 100.00% | 100.00% | 100.00% | yes |
| 23 | 237101A14A.dat (1CMCHXPD7) | 237103BN1A.dat (1CMCHXPD7) | 268/268 | 100.00% | 100.00% | 100.00% | yes |
| 24 | 237101A14A.dat (1CMCHXPD7) | 237103BN3A.dat (1CMCHXPD7) | 268/268 | 100.00% | 100.00% | 100.00% | yes |
| 25 | 237101A14A.dat (1CMCHXPD7) | 237103BN4A.dat (1CMCHXPD7) | 268/268 | 100.00% | 100.00% | 100.00% | yes |

## Family and size coverage

| Primary fingerprint FID | Detailed ROMs | Size counts |
|---|---:|---|
| 9CMCVAPD31 | 40 | 524,288 B: 40 |
| I9CMCHVPD6 | 38 | 524,288 B: 38 |
| 1CMCHXPD7 | 35 | 524,288 B: 35 |
| 1CMC7QPD4 | 32 | 524,288 B: 32 |
| 2JCS62D8 | 32 | 1,048,576 B: 32 |
| 4CMCB1PDM1 | 32 | 524,288 B: 32 |
| Z3CMCJSPD4 | 32 | 1,048,576 B: 32 |
| 2XH5EJ7G2 | 22 | 524,288 B: 22 |
| 2JCSSKDD | 19 | 1,048,576 B: 19 |
| 2XH5ET6G3 | 14 | 524,288 B: 14 |
| 2XH5EUXG4 | 12 | 524,288 B: 12 |
| H1CMC7Q4003 | 10 | 524,288 B: 10 |
| 1CMC6GPDA | 9 | 524,288 B: 9 |
| 1CMC7QPD44 | 9 | 524,288 B: 9 |
| 1CMCA1PDB | 9 | 524,288 B: 9 |
| 1CMC7Q4001 | 8 | 524,288 B: 8 |
| 1CMC7QPD401 | 8 | 524,288 B: 8 |
| 9CMCHLE2 | 8 | 524,288 B: 8 |
| 2JCSFEDA | 7 | 1,048,576 B: 7 |
| 2JCSKHDB | 5 | 1,048,576 B: 5 |

Across these 431 snapshots, the workbench reported 128,307 table detections over 6,599 distinct table start addresses. Counts repeat across ROM snapshots. The most recurring addresses are: 49714 (144), 47185 (142), 47613 (142), 49498 (140), 47597 (137), 71164 (136), 49762 (135), 47581 (134), 47629 (134), 47661 (134), 47677 (134), 47053 (129).

## Interpretation

A high strict-layout score identifies close structural siblings in the scanned corpus. Similarity is expected to be inflated among revisions that retain the same firmware layout and primary FID. A geometry-only score can remain high even where tables have moved, so it is weaker evidence of shared code or calibration lineage. Conversely, low address overlap across different image sizes or firmware families does not show that the ROMs share no concepts. Do not use these layout metrics to transfer table names, units, scaling, query axes, or semantics to EL19A.

Full pairwise results: `table_layout_pairwise_431_DAT_2026-11-27.tsv`.
