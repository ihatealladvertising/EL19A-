# Ten CONSULT .dat Donor Screening — 2026-11-26

## Scope and method

Ran the existing read-only `tools/nissan_sh705x_workbench.py scan` and `diff` commands against the ten newly added files in `EVIDENCE/`. No workbench or scanner source was modified. The workbench's current CONSULT decoder validates each 0x8015/0x3482 transfer-frame checksum and applies its existing word-decryption routine. Scan fingerprints/helper counts below are observations from that decoder and scanner; a valid outer frame checksum alone does not prove that a decoded payload is a correct plaintext ROM.

Reference controls:
- `EVIDENCE/unknown_EM62B_SH7055.bin`
- `EVIDENCE/237108W94B.dat`
- `EVIDENCE/VERSA f501.bin` (EL19A, expected MD5 `46991697c502052752a2cabcb84c9e27`)

Execution:
- Scan and initial diff batch: GitHub Actions run [45906082083](https://github.com/ihatealladvertising/EL19A-/actions/runs/45906082083), artifact SHA-256 `cb6c7472779ccc78a708321e1d81cefbe79d5c265c0591bedbca891d26de6cc2`.
- Corrected address-coverage and cross-application MR16DDT comparisons: run [45906621594](https://github.com/ihatealladvertising/EL19A-/actions/runs/45906621594), artifact SHA-256 `cb9830489b99fa89d16f79b8e6ff84a5017efe8c4551b4b1b51777b378320cc3`.

## Scan summary

| Input | Decoded size | CPU / fingerprint | Helpers | Calls (resolved) | Tables | Assessment |
|---|---:|---|---:|---:|---:|---|
| `23710EM60B.dat` | 524,288 B | SH705519N / `1CMC7QPD` family | 34 | 338 (334) | 274 | Usable SH7055 donor; QPD401 branch reported in header inspection |
| `23710EM62B.dat` | 524,288 B | SH705519N / `1CMC7QPD` family | 34 | 338 (334) | 274 | Usable decoder control; payload from 0x08200 onward matches existing EM62B binary |
| `23710EM64A.dat` | 524,288 B | SH705519N / `1CMC7QPD` family | 34 | 338 (334) | 274 | Usable SH7055 donor; QPD402 branch reported in header inspection |
| `23710EM67A.dat` | 524,288 B | SH705519N / `1CMC7QPD` family | 34 | 338 (334) | 274 | Usable SH7055 donor; close revision of EM64A |
| `237103ZM1E.dat` | 2,097,152 B | No SH70 CPU string; FID-like `9FVUZIJ9` | 0 | 0 (0) | 0 | Frames parse, but usable plaintext/CPU family not established |
| `237103ZM2E.dat` | 2,097,152 B | No SH70 CPU string; FID-like `9FVUZIJ9` | 0 | 0 (0) | 0 | Same caveat as ZM1E |
| `237103ZM3A.dat` | 2,097,152 B | No SH70 CPU string; FID-like `9FVUZIJ9` | 0 | 0 (0) | 0 | Same caveat as ZM1E |
| `237103ZM4A.dat` | 2,097,152 B | No SH70 CPU string; FID-like `9FVUZIJ9` | 0 | 0 (0) | 0 | Same caveat as ZM1E |
| `E1BR20E.dat` | — | Not decoded | — | — | — | Unsupported by current decoder: no valid 0x8015/0x3482 frame sequence |
| `8201032726.dat` | — | Not decoded | — | — | — | Unsupported by current decoder: no valid 0x8015/0x3482 frame sequence |

The FID-like strings reported by the scanner are byte-pattern detections, not independently verified calibration IDs.

## EM-family comparisons — strongest result

### EM62B against the existing EM62B binary

`23710EM62B.dat` and `unknown_EM62B_SH7055.bin` have:
- 274 same-address tables with identical payloads;
- zero differing helper tables;
- zero raw differing bytes after the workbench excludes the leading 0x00000–0x081FF region that is 0xFF-padded in the decoded `.dat`.

This establishes that the decoded `.dat` content from 0x08200 to the end matches the existing EM62B binary. It validates the decoder for this QPD/SH705519N family, but EM62B is not a novel donor payload.

### Within-branch revisions

| Comparison | Same tables | Same-address changed tables | Raw differing bytes | Interpretation |
|---|---:|---:|---:|---|
| EM60B vs EM62B | 215 | 59 | 2,460 | Close QPD401-family revision pair |
| EM67A vs EM64A | 215 | 59 | 2,471 | Close QPD402-family revision pair |

All 274 discovered table bases remain present at the same addresses in each pair. The 59 payload changes are therefore useful candidate calibration/revision differences; the remaining raw differences include bytes outside those table spans (likely scalar, metadata or integrity fields, but not semantically classified here).

### Between EM identifier branches

EM64A vs EM62B:
- 215 exact same-address table payloads;
- 59 same-address tables with different payloads;
- no relocated exact-payload-only or unmatched helper tables;
- 425,829 raw differing bytes.

The branches share the same discovered helper/table architecture and address map, but the large raw difference means they should not be treated as simple calibration-only revisions without further code-region analysis.

### EM62B vs W94B control family

- 129 relocated exact table-payload matches (45 non-trivial);
- 143 tables unmatched in the EM62B-to-W94B direction (106 non-trivial);
- two same-address differing tables at `0x0BF4A` and `0x0C0DA`;
- raw binary difference: 468,676 bytes.

This is useful cross-family structural evidence, not evidence of direct calibration interchangeability.

## MR16DDT C12/C13 files — format boundary

All four `237103ZM*.dat` files have a valid, contiguous outer transfer sequence:
- 15,864 frames per file;
- 128-byte payload per frame;
- first address `0x10400`;
- final exclusive address `0x200000`;
- no frame checksum or command errors.

The resulting 2 MiB buffers show no SH70 processor tag and no recognised SH7055 helper signature in any tested 512 KiB window (0x00000, 0x80000, 0x100000, 0x180000). The current scanner consequently reports zero calls and tables. Because this is a substantially different image size and no CPU/helper identity was established, the output should be treated as a format/processor lead rather than a confirmed plaintext SH7055 ROM. The outer frame validation does not by itself validate the decrypted payload cipher for this family.

Raw comparisons do show that the decoded buffers are very close:
- ZM1E vs ZM2E: 41 differing bytes in 11 clusters.
- ZM3A vs ZM4A: 41 differing bytes in 11 clusters.
- ZM1E vs ZM3A (C13 vs C12 application labels): 92 differing bytes in 14 clusters.
- ZM2E vs ZM4A: 92 differing bytes in 14 clusters.

No helper/table matches were available to classify those differences. Preserve these four files, but do not spend EL19A table-analysis effort on them until their CPU and decryption/plaintext status are identified.

## Unsupported formats

`E1BR20E.dat` and `8201032726.dat` do not satisfy the workbench's current CONSULT 0x8015/0x3482 frame parser. Their raw headers differ from the decoded EM/MR16 framing path. No alternate unpacker, decryptor or installer was attempted. Both remain valid collection leads, but not scan-ready files.

## Recommendation

1. **Prioritize the EM series.** It is confirmed SH705519N with a stable 34-helper / 274-table layout and produces directly comparable payloads. The next best incremental files to add are `23710EM61B.dat`, `23710EM63B.dat`, `23710EM65A.dat`, and `23710EM66A.dat` to fill the two revision sequences.
2. Retain `23710EM62B.dat` as the validated decoder/control input, while noting it duplicates the existing EM62B binary from 0x08200 onward.
3. Keep the four MR16DDT files as a separate lower-priority lead; current CPU and payload plaintext status are unresolved.
4. Defer `E1BR20E.dat` and `8201032726.dat` until a decoder path for their respective containers is established.

None of these files is established as an MR18DE/EL19A-equivalent ECU image. No calibration XML, catalogue, scope matrix, workbook, Findings record, ROM or tool source was modified by this screening task.

## Input SHA-256

```text
9f5e0c7a28eaf52f1ad6e9e301db22023c044315fccf4db77eac37c60b92ab8f  EVIDENCE/23710EM62B.dat
42d2274e2ae1ed698e6581a3f2d015a58782cde4f468feb964afba4a30ddf29d  EVIDENCE/23710EM64A.dat
3e4c50acd9f9a3ab7aa99abdd5b5316726f458b88eab7f83d4d836dabf8002ee  EVIDENCE/23710EM60B.dat
a6cf8bf0021199feefde078e1db40c6070b7ee84b4593067900c09fec0e95aa5  EVIDENCE/23710EM67A.dat
9d1e431b6927b72985f973bb99787e3c07b0d83d7cd96ca78351d6eaf207af10  EVIDENCE/237103ZM3A.dat
7075b78c31469f6db2cdb642966d88cfcb9d2f6257d8b7e1b6c48fd58c30da0f  EVIDENCE/237103ZM1E.dat
e6924e4d070c8f5584442ff643ff3645d98bf5fd4420eb30d2a79875b78ec32a  EVIDENCE/237103ZM4A.dat
5740b87694f1075482869c38177a65b0c0a8b50ae85de103704967c919f58f8a  EVIDENCE/237103ZM2E.dat
53c9d50edbb9ef50d6d97c04f655a0e93d455f520bf9be053bc8988c8c297d8c  EVIDENCE/E1BR20E.dat
5d793f55ec52601103d1e4bdaaa73e5fffa3ebab71aa70af2a8ba32574a8f514  EVIDENCE/8201032726.dat
```
