# Cross-ROM Discovery Batch — 2026-11-26

**Purpose:** Record high-value cross-ROM structural results produced with the newly extended Nissan SH705x workbench and independent scanner-equivalent reproduction.  
**Repository snapshot:** `ihatealladvertising/EL19A-`, `main` at `02f434dc78bfaf2d6651dacf3f787d0e6be3d9b9`; current tool work committed at `ac955233f018e508f86611d4a6dbfb3c9c265918`.  
**Disposition:** Research evidence only. No EL19A semantic names, engineering units or calibration-definition changes are promoted by this report.

## 1. Tool and method provenance

Current tool files at the analysis snapshot:

- `tools/nissan_sh705x_workbench.py`, blob `c5f51baebcaff6811363da8742aeabae82e2fd9b`.
- `tools/nissan_sh705x_workbench.md`, blob `6cec001b7641a3a4e1c43a114bf14cd835b21e23`.
- `tools/sh7058_cross_rom_scanner.py`, blob `1cab97def9263f87d399fd9b29d443dd188c20e8`.

The workbench's new Consult `.dat` loader/decryptor was checked by reproducing its frame walk, frame checksum validation and 16-bit word transform against the four Consult images below. The table inventory/diff calculations in this run used a JavaScript reproduction of the repository scanner's helper-pattern discovery and bounded call-register reconstruction logic. It is an independent execution of the same core patterns, not a claim that the Python CLI itself was executed in this environment. The computed helper/call/table counts matched the pushed workbench's reported counts for the same 512 KiB images and decoded `.dat` images.

**Important execution boundary:** GitHub's file-content connector supplied the 512 KiB and ~541 KiB inputs used here, but returned empty byte content for the 1 MiB ROM files. Consequently, this batch independently processes the 512 KiB images listed below and the four decoded Consult images. The published 1 MiB EL19A/EL13A/8W83B/CF48D/Tiida/Juke workbench summaries are not presented as freshly rerun here.

For 2D helper labels below, `2D_IMPL` and `2D_AXIS` are the scanner's helper-pattern categories. They are not physical function names; `2D_AXIS` indicates an explicit axis/query search form. Dimensions, type and exact payload are structural evidence only.

## 2. Input images and repository identities

| Input | Decoded/input size | Git blob |
|---|---:|---|
| `EVIDENCE/237108W94B.dat` | 540,947 B input; 524,288 B decoded | `5edd6952721340dd97474b9dff11d30c62515f5d` |
| `EVIDENCE/237108W95B.dat` | 540,947 B input; 524,288 B decoded | `d079b118b6c95617cfcb16ee813886fa11c1664f` |
| `EVIDENCE/23710EL58B.dat` | 540,947 B input; 524,288 B decoded | `79bc1362b0e3c0ebb8bc58311d626f1149ee0bce` |
| `EVIDENCE/23710EL59B.dat` | 540,947 B input; 524,288 B decoded | `bd4ba97ca54b207d932731938a7aae7492435e34` |
| `EVIDENCE/unknown_EM62B_SH7055.bin` | 524,288 B | `f6e595fd6b2ddf640c21a88d999ddf03c46b7937` |
| `EVIDENCE/r4r42r24r2.bin` | 524,288 B | `e5be9a0f5a286776f0803da27c2595ac7cad4ae8` |
| `EVIDENCE/23710-EE310-07-C11-MR18DE-MT.bin` | 524,288 B | `07b4b22db12339fe392cf3fb3d5f0480ab9df303` |
| `EVIDENCE/sentra revhang/sentra_8U92A.bin` | 524,288 B | `a6b191068c8de0e0faed9762bc905dd82b66d665` |
| `EVIDENCE/sentra revhang/NoRevHang_Sentra_8U92A.bin` | 524,288 B | `9635802247655a8c518aedb90aa6291c8587e8ad` |

Each of the four Consult images decoded as 3,836 KWP frames. Every frame checksum passed in the validation pass; all four decoded images were 512 KiB with the scanner reporting 36 helpers, 319 calls, 313 resolved calls and 254 unique reader-backed table objects.

Other scanner counts reproduced in this run:

| ROM | Helpers | Calls | Resolved | Unique table objects |
|---|---:|---:|---:|---:|
| W94B decoded | 36 | 319 | 313 | 254 |
| W95B decoded | 36 | 319 | 313 | 254 |
| EL58B decoded | 36 | 319 | 313 | 254 |
| EL59B decoded | 36 | 319 | 313 | 254 |
| EM62B | 34 | 339 | 335 | 275 |
| `r4r42r24r2.bin` | 34 | 339 | 335 | 275 |
| EE310 pre-cal MT | 37 | 327 | 310 | 249 |
| Sentra 8U92A | 32 | 270 | 256 | 212 |
| Sentra NoRevHang | 32 | 270 | 256 | 212 |

## 3. Major result: a 22-object Nissan calibration payload family shared by four ROMs

An exact-payload crosswalk was built across:

1. W94B decoded from `237108W94B.dat`;
2. `unknown_EM62B_SH7055.bin`;
3. the C11 MR18DE manual-transmission `23710-EE310-07-C11-MR18DE-MT.bin`;
4. Sentra `sentra_8U92A.bin`.

After collapsing duplicate occurrences within each ROM to unique payload signatures:

- 36 unique exact payload signatures occur in all four images;
- 22 of those have more than two distinct byte values (nontrivial);
- **all 22 retain the same helper category, storage type and geometry in all four images**.

This is a strong shared Nissan lookup-library subset spanning different firmware/application images and ROM layouts. It does not prove that any of the 22 objects has the same physical purpose in every vehicle; it proves exact payload reuse plus matching target reader-shape classification in the four scanned ROMs.

| # | W94B | EM62B | EE310 MT | Sentra 8U92A | Helper category | Type × geometry |
|---:|---:|---:|---:|---:|---|---|
| 1 | `0x0B7A4` | `0x0BC85` | `0x0A08C` | `0x088F6` | 2D_IMPL | UBYTE 32×1 |
| 2 | `0x0B186` | `0x0B5DF` | `0x099EE` | `0x08336` | 2D_IMPL | UBYTE 8×1 |
| 3 | `0x0B73C` | `0x0BC2D` | `0x0A024` | `0x0889E` | 2D_AXIS | UBYTE 8×1 |
| 4 | `0x0B684` | `0x0BB75` | `0x09F6C` | `0x087FA` | 2D_AXIS | UBYTE 8×1 |
| 5 | `0x0B066` | `0x0B497` | `0x098CE` | `0x08226` | 2D_IMPL | UBYTE 8×1 |
| 6 | `0x0B1A6` | `0x0B5FF` | `0x09A0E` | `0x08356` | 2D_IMPL | UBYTE 8×1 |
| 7 | `0x0B810` | `0x0BD19` | `0x0A0F8` | `0x08962` | 2D_AXIS | UBYTE 8×1 |
| 8 | `0x0B202` | `0x0B663` | `0x09A6A` | `0x083AA` | 2D_IMPL | UBYTE 8×1 |
| 9 | `0x0B076` | `0x0B4A7` | `0x098DE` | `0x08236` | 2D_IMPL | UBYTE 8×1 |
| 10 | `0x0BFEA` | `0x0C590` | `0x0A912` | `0x090CC` | 2D_AXIS | UWORD 32×1 |
| 11 | `0x0C04A` | `0x0C5F0` | `0x0A972` | `0x0913C` | 2D_AXIS | UWORD 32×1 |
| 12 | `0x0C08A` | `0x0C630` | `0x0A9B2` | `0x0917C` | 2D_AXIS | UWORD 32×1 |
| 13 | `0x0BF6A` | `0x0C510` | `0x0A892` | `0x0904C` | 2D_AXIS | UWORD 32×1 |
| 14 | `0x0BFAA` | `0x0C550` | `0x0A8D2` | `0x0908C` | 2D_AXIS | UWORD 32×1 |
| 15 | `0x0B9F4` | `0x0BF4A` | `0x0A2DC` | `0x08B16` | 2D_AXIS | UWORD 16×1 |
| 16 | `0x0BEAA` | `0x0C450` | `0x0A7D2` | `0x08FFC` | 2D_IMPL | UWORD 4×1 |
| 17 | `0x0B7C4` | `0x0BCA5` | `0x0A0AC` | `0x08916` | 2D_IMPL | UBYTE 16×1 |
| 18 | `0x0AF26` | `0x0B337` | `0x0978E` | `0x080F2` | 2D_IMPL | UBYTE 8×1 |
| 19 | `0x0AF56` | `0x0B367` | `0x097BE` | `0x08122` | 2D_IMPL | UBYTE 8×1 |
| 20 | `0x0B2BA` | `0x0B73B` | `0x09B32` | `0x0849A` | 2D_IMPL | UBYTE 16×1 |
| 21 | `0x0B5A4` | `0x0BA6D` | `0x09E4C` | `0x086FE` | 2D_IMPL | UBYTE 16×1 |
| 22 | `0x0B52C` | `0x0B9DD` | `0x09DD4` | `0x08686` | 2D_AXIS | UBYTE 16×1 |

### Pairwise context for the common library

Unique payload-signature intersection counts:

| Comparison | Common signatures | Nontrivial | Same helper/type/dimensions | Nontrivial with same shape |
|---|---:|---:|---:|---:|
| W94B – EM62B | 67 | 38 | 64 | 38 |
| W94B – EE310 MT | 146 | 102 | 146 | 102 |
| W94B – Sentra | 39 | 24 | 38 | 24 |
| EM62B – EE310 MT | 62 | 35 | 59 | 35 |
| EM62B – Sentra | 46 | 27 | 45 | 27 |
| EE310 MT – Sentra | 41 | 26 | 40 | 26 |

Object-occurrence comparisons differ from unique-signature counts because one payload can occur more than once within a ROM. For example, W94B and EE310 share 210 matching table-object occurrences by exact payload (120 nontrivial); 191 also match helper category/type/dimensions (120 nontrivial). EE310 and Sentra share 97 matching object occurrences (30 nontrivial; all 30 nontrivial matches retain the same helper category/type/dimensions).

**Why this matters to EL19A:** EE310 is a particularly relevant predecessor because it is an MR18DE C11 manual-transmission image. Its large exact-payload overlap with both the W94B line and Sentra shows that the scanner is finding repeated Nissan table payloads across different ROM layouts. This creates a high-value candidate index for comparing the same payload fingerprints and reader constellations against EL19A. It does not yet assign a physical name or unit to any EL19A address.

## 4. W94B / W95B is a controlled one-table variant change

Both decoded images have 254 detected table objects.

- 253 objects have identical same-address payloads.
- Exactly one object differs at the same address: `0x0AFCE–0x0AFD5`.
- Scanner classification: 2D_IMPL, UBYTE, 8×1.
- W94B payload: `1B 1B 1B 1B 1B 1B 1B 1B` (eight decimal 27 values).
- W95B payload: `00 00 00 00 00 00 00 00`.
- No other detected table payload changed between the two decoded images.

The caller trace in W94B establishes:

| PC / operand | Instruction-level result |
|---|---|
| `0x3DCA8` | `mov.w @(PC+0x8C*2),r1`; literal at `0x3DDC4` is `0x850A`, sign-extended to `R1=0xFFFF850A` |
| `0x3DCAE` | `mov.b @(0xC,r1),r0` reads `UBYTE[0xFFFF8516]` |
| `0x3DCB0` | `mov.l @(PC+0x75*4),r8`; literal at `0x3DE88` is `0x0000CCCD` |
| `0x3DCB2`–`0x3DCC4` | Zero-extend input; multiply by `0xCCCD`; take product shifted right 15 |
| `0x3DCC6`–`0x3DCCA` | Clamp query to maximum 255 |
| `0x3DCD2` | Call helper `0x15258`; delay slot moves the UBYTE query into R5 |

Thus the query is:

`q = min(255, (UBYTE[0xFFFF8516] × 0xCCCD) >> 15)`

The lookup returns a constant value for either image because all eight cells are identical: 27 in W94B and 0 in W95B. The query calculation is therefore structurally established, but its variation does not change the lookup output for these two payloads. The physical meaning of `FFFF8516`, the meaning of 27, and the result's downstream consumer remain unresolved. A repository search for `FFFF8516`, `0xAFCE`, `0x15258` and `0x3DCD2` found no corresponding textual LST/Findings references in the current repository; the available W94B image has no matching annotated listing in this evidence set.

### Non-table changes in the W94B/W95B pair

The raw images differ in 29 bytes across 11 clusters. Besides the eight table bytes, the other changes are in header/checksum/signature-like areas:

- `0x8200–0x8201`: stored 16-bit checksum changes `C1 6E → 58 80`;
- `0x8208`, `0x8213`, `0x82C3`, `0x868D`, `0x8D19`, `0xAB09`, `0xAB9A`: isolated one-byte changes;
- `0x8C98–0x8C9B` and `0x8CA0–0x8CA3`: two adjacent 32-bit values change.

The two 32-bit words were not explained by the tested simple sum32/XOR32 hypotheses. They remain opaque; do not label them as a particular checksum/signature algorithm.

## 5. EL58B / EL59B is table-identical under the scanner

The two decoded 512 KiB images each contain 254 detected lookup objects. The comparison found:

- **254 identical table payloads at the same addresses;**
- zero same-address table-payload differences;
- 21 raw image bytes differ in 11 clusters, all outside the detected table payloads.

The differing clusters include the 16-bit value at `0x8200`, several isolated one-byte fields, and two 32-bit values at `0x8C98–0x8CA3`. These are non-table/header/signature-like differences, but their exact roles remain unresolved.

This result is useful as a negative control: a ROM pair can differ at raw-byte level while all lookup payloads detected by the scanner remain unchanged.

## 6. Sentra Rev Hang / NoRevHang pair: six non-table bytes, no changed lookup tables

Inputs: `EVIDENCE/sentra revhang/sentra_8U92A.bin` and `EVIDENCE/sentra revhang/NoRevHang_Sentra_8U92A.bin`.

Both images have 32 helpers, 270 call sites, 256 resolved calls and 212 unique table objects. The pairwise comparison found:

- 212 same-address identical detected table payloads;
- zero same-address changed table payloads;
- zero relocated or unmatched detected table objects;
- exactly six raw differing bytes outside those table spans, grouped into four clusters:

| Address | Original | NoRevHang |
|---|---|---|
| `0x05AF8` | `2C` | `68` |
| `0x05B59` | `0A` | `AA` |
| `0x06500–0x06501` | `06 1B` | `42 BB` |
| `0x06508–0x06509` | `FB 6D` | `38 0D` |

The differences are real and outside all 212 detected table payloads, but their instruction/data role has not been decoded. Do not yet call them executable-code patches or identify a Rev Hang control strategy. The falsifiable next step is to disassemble these four bounded byte clusters and their immediate control-flow context. The present evidence supports a narrower conclusion: **the NoRevHang variant does not change any lookup payload detected by the scanner; its observed binary delta is a six-byte non-table patch.**

## 7. EM62B / r4r42r24r2 is table-identical except for an eight-byte opaque field

Both 512 KiB images scan as 34 helpers, 339 calls, 335 resolved calls and 275 unique table objects.

- Every one of the 275 detected table objects is identical at the same address.
- The raw images differ at exactly eight bytes, all contiguous at `0x10404–0x1040B`:

| Image | `0x10404–0x1040B` |
|---|---|
| `unknown_EM62B_SH7055.bin` | `D2 BC 1C 62 C0 A8 0E E2` |
| `r4r42r24r2.bin` | `6B 3F F4 EA A7 D4 29 9A` |

The two 32-bit words at `0x10404` and `0x10408` have not been matched to the tested sum32/XOR32 hypotheses. The eight-byte block is therefore described only as an opaque signature/checksum-like field. The table-identical result is strong; the interpretation of the eight-byte field is not.

## 8. Combined interpretation and EL19A relevance

These experiments establish three useful properties of the expanded toolchain:

1. The new `.dat` decoder makes a previously inaccessible Consult image family comparable at the same ROM-image level as the raw 512 KiB binaries.
2. Exact lookup payloads are reused extensively across Nissan ROMs even when addresses and application layouts differ. The four-way, 22-entry crosswalk is a concrete, reusable candidate list rather than a donor-name guess.
3. Some variant differences are wholly outside detected lookup payloads (Sentra NoRevHang; EM62B/r4r42r24r2; EL58B/EL59B), while other variants alter a small, countable set of lookup tables (W94B/W95B; W94B/EL58B).

The C11 MR18DE MT `EE310` image is the most directly relevant historical comparison for EL19A among this set. The 22 four-way payload anchors should be checked against the full EL19A scan/audit outputs, then compared by callsite/axis constellation, not merely by address. The currently documented EL19A workbench audit already reports large cross-variant candidate sets, but its 1 MiB ROM binary inputs could not be reloaded through the file connector in this run. That comparison should be performed in the project checkout using the pushed CLI and saved TSV/JSON output.

## 9. Recommended next bounded investigations

1. **EL19A fingerprint join for the 22 shared signatures.** In the local checkout, run the updated workbench scan/audit exports on EL19A and the 512 KiB cross-ROM set; match by full payload bytes plus helper category/type/dimensions; record every EL19A address, call PC, axes and geometry. Stop before promoting donor physical names.
2. **Sentra six-byte NoRevHang patch decode.** Disassemble only `0x05AF8`, `0x05B59`, `0x06500–0x06501`, and `0x06508–0x06509`, with nearby instruction/control-flow boundaries. Decide whether each difference is opcode, literal, branch target or metadata. Do not expand to a broad Rev Hang search until the patch role is known.
3. **W94B/W95B input-field producer trace.** Trace writes to `FFFF8516` and the downstream consumer of the constant-valued `0xAFCE` result. Keep any physical sensor/system interpretation provisional until the target ROM's own producer/consumer evidence supports it.
4. **Opaque metadata/checksum field discrimination.** If useful to format support, compare `0x8C98–0x8CA3` across W94/W95/EL58/EL59 and `0x10404–0x1040B` across EM62B/r4r42r24r2 with a full range/algorithm search. This is lower priority than the three reader/caller investigations above.

## 10. Evidence limits / non-promotions

- The 22 cross-ROM objects are exact payload and reader-shape correspondences, not semantic identifications.
- The W94B/W95B `FFFF8516` input has no established physical name or unit.
- The constant values 27 and 0 at `0xAFCE` have no established meaning.
- The six Sentra bytes have not yet been disassembled; they are not yet proven to be code.
- The 32-bit changed fields at W94/EL58 and EM62B pairs are not proven to be checksum fields or particular algorithms.
- New `EVIDENCE/8201032726.dat` and `EVIDENCE/E1BR20E.dat` files were observed to use a different/unresolved container format and were not decoded in this run. `EVIDENCE/310364EM1C.dat` and `EVIDENCE/310364EP1B.dat` were not inspected because their binary contents were not retrievable through the available file connector.
- No FND/REC, XML, scope matrix, catalogue, workbook, ROM, LST, A2L, tool source, or work-order lifecycle record was modified by the analysis. This report is a cross-ROM research artifact, not an EL19A calibration finding.
