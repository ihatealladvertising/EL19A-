# EL19A table-layout comparison against the 431 detailed DAT ROMs

**Target:** VERSA f501.bin, FID 8CMCKRN5, SHA-256 `bfe037e8e6c389e2a90214047058eb6dc3bcaaaac5b5931bf98a3f5d9f64fd6a`; 291 table records from the fresh WO65324 scan.  
**Comparison set:** 431 unique direct-DAT payloads with detailed helper/table findings, all decoded SHA-256 checked in the separate byte-similarity pass.  
**Method:** compare target table start addresses and strict structural signatures (end/extent, table kind, element type, dimensions, axis storage types). Also compare geometry histograms without addresses. Calls and payload values are excluded.

| DAT size group | ROMs | Median strict layout Jaccard | 90th percentile strict Jaccard | Median start-address Jaccard | Median geometry multiset Jaccard | Best shared start count | ROMs ≥50% strict layout | ROMs ≥90% strict layout |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 512-KiB DATs | 313 | 0.00% | 0.00% | 0.18% | 82.08% | 4 | 0 | 0 |
| 1-MiB DATs | 118 | 0.00% | 0.00% | 1.45% | 71.15% | 14 | 0 | 0 |

## Highest target-layout matches

| Rank | DAT source | Reported FID | Size | Shared starts / target tables | Same geometry at shared starts | Strict layout Jaccard | Geometry multiset Jaccard, address ignored |
|---:|---|---|---:|---:|---:|---:|---:|
| 1 | 237105LJ0A.dat | 6JCS7JD1 | 1,048,576 | 14/291 | 0/14 | 0.00% | 69.12% |
| 2 | 237105LK0A.dat | 6JCSF9D2 | 1,048,576 | 14/291 | 0/14 | 0.00% | 69.12% |
| 3 | 237105UN2A.dat | 6JCS7JD1 | 1,048,576 | 14/291 | 0/14 | 0.00% | 69.12% |
| 4 | 237105UN3A.dat | 6JCS7JD1 | 1,048,576 | 14/291 | 0/14 | 0.00% | 69.12% |
| 5 | 237101FB3B.dat | 2JCS62D8 | 1,048,576 | 13/291 | 0/13 | 0.00% | 71.15% |
| 6 | 237101J60C.dat | 2JCS62D8 | 1,048,576 | 13/291 | 0/13 | 0.00% | 71.15% |
| 7 | 237101J61C.dat | 2JCS62D8 | 1,048,576 | 13/291 | 0/13 | 0.00% | 71.15% |
| 8 | 237101J62D.dat | 2JCS62D8 | 1,048,576 | 13/291 | 0/13 | 0.00% | 71.15% |
| 9 | 237101J63C.dat | 2JCS62D8 | 1,048,576 | 13/291 | 0/13 | 0.00% | 71.15% |
| 10 | 237101J64C.dat | 2JCS62D8 | 1,048,576 | 13/291 | 0/13 | 0.00% | 71.15% |
| 11 | 237101J65D.dat | 2JCS62D8 | 1,048,576 | 13/291 | 0/13 | 0.00% | 71.15% |
| 12 | 237103UG2A.dat | 2JCS62D8 | 1,048,576 | 13/291 | 0/13 | 0.00% | 71.15% |
| 13 | 237103ZB4A.dat | 2JCS62D8 | 1,048,576 | 13/291 | 0/13 | 0.00% | 71.15% |
| 14 | 237103ZB5A.dat | 2JCS62D8 | 1,048,576 | 13/291 | 0/13 | 0.00% | 71.15% |
| 15 | 237108Y50B.dat | 2JCS62D8 | 1,048,576 | 13/291 | 0/13 | 0.00% | 71.15% |
| 16 | 237108Y51B.dat | 2JCS62D8 | 1,048,576 | 13/291 | 0/13 | 0.00% | 71.15% |
| 17 | 237108Y52B.dat | 2JCS62D8 | 1,048,576 | 13/291 | 0/13 | 0.00% | 71.15% |
| 18 | 23710BH44C.dat | 2JCS62D8 | 1,048,576 | 13/291 | 0/13 | 0.00% | 71.15% |
| 19 | 23710BH45C.dat | 2JCS62D8 | 1,048,576 | 13/291 | 0/13 | 0.00% | 71.15% |
| 20 | 23710BH46C.dat | 2JCS62D8 | 1,048,576 | 13/291 | 0/13 | 0.00% | 71.15% |
| 21 | 23710BH47C.dat | 2JCS62D8 | 1,048,576 | 13/291 | 0/13 | 0.00% | 71.15% |
| 22 | 23710BH48C.dat | 2JCS62D8 | 1,048,576 | 13/291 | 0/13 | 0.00% | 71.15% |
| 23 | 23710BH49C.dat | 2JCS62D8 | 1,048,576 | 13/291 | 0/13 | 0.00% | 71.15% |
| 24 | 23710BH50C.dat | 2JCS62D8 | 1,048,576 | 13/291 | 0/13 | 0.00% | 71.15% |
| 25 | 23710BH51C.dat | 2JCS62D8 | 1,048,576 | 13/291 | 0/13 | 0.00% | 71.15% |

## Interpretation

These are structural layout comparisons only. A small address Jaccard means the workbench table starts mostly differ; a high geometry-only score means similar object shapes can occur in another address layout. Neither establishes common calibration meaning, donor identity, units, scaling, axis semantics, or suitability for transferring definitions. The ranking is within the 431 detailed DAT images; the 2,482 rejected inputs and other loaded files with no table-detail records were not included as table-layout candidates.

Full 431-row comparison: `EL19A_table_layout_vs_431_DAT_2026-11-27.tsv`.
