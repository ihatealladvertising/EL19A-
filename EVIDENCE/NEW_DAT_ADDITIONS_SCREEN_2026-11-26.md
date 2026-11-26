# New `dat` Additions Screening — 2026-11-26

## Scope

Eight new `.dat` files were found in `EVIDENCE/` compared with the previously screened set. The existing read-only `tools/nissan_sh705x_workbench.py scan` and `diff` commands were run without changing the workbench/scanner source.

Execution:
- Successful screening run: [GitHub Actions 45907252456](https://github.com/ihatealladvertising/EL19A-/actions/runs/45907252456)
- Artifact: `el19a-new-dat-screen`, SHA-256 `2309a63740ac69fe6c4dcfb79eb4b2a985737979382bb50b64176cffbfb18201`
- Input scan/diff + raw-header checks completed. The run included per-file JSON/TSV scans for decodable files, pairwise revision diffs, and bounded raw header inspection for unsupported files.

## Results

### EM family additions — confirmed SH7055-compatible

All four new EM files decode to 524,288-byte images with:
- CPU tag: `SH705519N`
- 34 lookup helpers
- 338 detected call sites, 334 resolved
- 274 unique helper-backed table bases
- 14 tables dual-used as axes; 12 reciprocal-pair endpoints

| File | Embedded identifying strings | Tables vs adjacent existing revision | Raw differing bytes |
|---|---|---:|---:|
| `23710EM61B.dat` | `1EM61B00`, `1CMC7QPD` | 274 identical vs EM60B | 28 in 15 clusters |
| `23710EM63B.dat` | `1EM63B00`, `1CMC7QPD` | 274 identical vs EM62B | 45 in 19 clusters |
| `23710EM65A.dat` | `1EM65A00`, `1CMC7QPD` | 274 identical vs EM64A | 28 in 15 clusters |
| `23710EM66A.dat` | `1EM66A00`, `1CMC7QPD` | 274 identical vs EM67A | 45 in 19 clusters |

Each comparison reports zero helper-backed table payload differences. The reported raw byte differences are outside the scanner's differing-table spans. They include version-like/header bytes, pointer-referenced values and bytes near axis locations; their purposes are not identified. Do not label them as checksum or calibration changes without further evidence.

**Interpretation:** These four files complete the two EM revision sequences already present in EVIDENCE. They add no newly detected helper-backed table payloads relative to their adjacent known revisions, but they add useful versioned ROM identity and non-table byte-difference evidence. Their shared SH705519N architecture is confirmed; their vehicle/engine application remains unproven here.

### 31036 family — different, unsupported container

| File | Size | Initial header text | Workbench result |
|---|---:|---|---|
| `310364EM1C.dat` | 1,397,629 B | `4EM1C1A` | Rejected: no valid CONSULT 0x8015 transfer-frame sequence |
| `310364EP1B.dat` | 1,397,629 B | `4EP1B1A` | Rejected: no valid CONSULT 0x8015 transfer-frame sequence |

The two files have different initial identifier strings and differ in their opening header bytes. The existing parser does not decode either one. A same-family relationship is plausible from their shared `310364` basename stem and file size, but is not established by successful payload decoding or a cross-ROM diff. No vehicle, engine, ECU, or processor is assigned.

### E1BC family — different, unsupported container

| File | Size | Header identifiers observed | Workbench result |
|---|---:|---|---|
| `e1bc11b.dat` | 485,548 B | `1BC11A`, `1BC105` | Rejected: no valid CONSULT 0x8015 transfer-frame sequence |
| `e1bc12b.dat` | 645,526 B | `1BC12A`, `1BC110` | Rejected: no valid CONSULT 0x8015 transfer-frame sequence |

These files begin with an `0x861000`-style header followed by ASCII identifiers. The files differ in size and additional header identifiers. The strings `1BC11A` and `1BC12A` are recorded literally; they are not interpreted as C11/C12 chassis designations. They remain an unclassified file-format lead.

## Recommended priority

1. **No further table scan is needed for EM61B/63B/65A/66A against the adjacent revisions**: all 274 helper-backed payloads are identical in each comparison. Keep these files as revision/version evidence.
2. **Investigate the 310364 container next** if additional donor discovery is desired. It is the larger of the two unsupported format families and has a distinct, repeatable opening structure across two files.
3. **Keep E1BC as a separate format investigation.** Its two files have different lengths and header IDs; do not treat their IDs as chassis codes based on string resemblance.
4. Do not promote any of these eight as an MR18DE/EL19A donor. No direct C11/MR18DE identity was established.

## Input SHA-256

```text
949abdfe2c4a2cacd13e7ebae67f97c6f5cd75bc0f9056558cfabbe50c870089  EVIDENCE/23710EM61B.dat
358a650d6f11a86b369045a74e009289656386f4e26b3f840096de983dac4252  EVIDENCE/23710EM63B.dat
c7c9a9c7d0e730f3abeb646d4cd280b621cd9bb0e3978afa0d02a6e59483bd55  EVIDENCE/23710EM65A.dat
de96f3cbd85ecced2bddde0bc6b8d53222f503f5777999323e55d9da5dec123b  EVIDENCE/23710EM66A.dat
772d97b5211c3f11d332b4256e5c34eb8a35c58b6832b0531fd4fe04c3c383bd  EVIDENCE/310364EM1C.dat
177be5e04a9a1a40f20ffd64a4b287ea5476719a7e1b312358153c903f5d6944  EVIDENCE/310364EP1B.dat
f6437760258978d4ba690d3f613b91aef96b597b17063c6ed3c4673958c19d0c  EVIDENCE/e1bc11b.dat
6a228c258df5442578a38235098fc2a8d1984afef2f062b284e071fb1174fb51  EVIDENCE/e1bc12b.dat
```

## Change boundary

No scripts, scanner/workbench source, tests, calibration XML, scope matrix, catalogue, workbook, Findings, worker queue, ROM, LST or A2L files were changed by this screening. The eight inputs were read-only. No calibration semantic interpretation is promoted by this report.
