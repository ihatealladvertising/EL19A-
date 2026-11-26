# Follow-on CONSULT Donor Screen — 2026-11-26

## Scope and execution

Read-only screen of the newly available EVIDENCE files, using the committed workbench plus a bounded experimental parser for the D9 transfer framing. No calibration meaning, unit, scaling, or donor applicability is promoted.

Successful diagnostic run: GitHub Actions run [45913585933](https://github.com/ihatealladvertising/EL19A-/actions/runs/45913585933), artifact ID `15160523766`, ZIP SHA-256 `97e76d6bb6a68d530065d57051ab7f1dee7e0cc74672a9ecfd6bb95fa5d82c3a`.

## Results

### D9 candidates — experimental 0x8019 / 0x3482 decode

All four files use a transfer-frame marker `80 19` rather than the existing loader's `80 15`. A bounded variant parser accepted service `34 82` data records and stopped at a terminal `34 81` frame. For each file:

- 3,328 data frames; first frame at `0x25`, last at `0x72898`.
- All data-frame additive checksums passed; terminal `34 81` checksum also passed.
- 425,984 transferred bytes, one contiguous covered range `0x08000–0x6FFFF`; no uncovered holes or repeated-byte overcount.
- Reconstructed image size 524,288 bytes (512 KiB), with erased `0xFF` prefix and tail.
- The output is **not identified as SH705x**: no SH70 CPU/FID tags, reset PC/SP are `FFFFFFFF/FFFFFFFF`, and the SH705x helper scanner found 0 helpers, 0 calls and 0 tables. Treat this as a structurally consistent experimental container reconstruction, not a verified executable ECU ROM.

| File | Raw SHA-256 | Reconstructed SHA-256 |
|---|---|---|
| `D9_BR60B.dat` | `322e257627bf58f8497829b0a7eb0d1e1246062a332640744ef21be4c1d0b00b` | `db1df9afd25945d2610901be55146ab3426f363d87f935a4c8a1b922d631d086` |
| `D9_BR61B.dat` | `f0fcdf7c6956bd53a88560f426c3e88b9ca6ed8e308b71a715aa4f37e2b3bb54` | `db1df9afd25945d2610901be55146ab3426f363d87f935a4c8a1b922d631d086` |
| `D9_JD08B.dat` | `db822e4a5d9b3d17946c778a9a1e90e3d2bd5fd9c801746eee1bd9e009d12016` | `ca0eb818058410f7e77827309f170d0016c856330061909d3e67696c0e064147` |
| `D9_JD09C.dat` | `280f185afffaa789663fb18e4ac4e9b9a01711cbcf3c7a81916163782e017e58` | `b8a45a135cf7ee59f96cd95cc18690a19cc9464ba95bb46a77e9e4200a91601a` |

Decoded-image comparisons:
- BR60B and BR61B are byte-identical (0 differing bytes).
- JD08B differs from the BR60B/BR61B image at 53 bytes.
- JD09C differs from the BR60B/BR61B image at 228,938 bytes and from JD08B at 228,942 bytes.

These are raw reconstructed-image comparisons only. With no SH705x helper/table structures, they do not establish calibration deltas or ECU function.

### E1BR / E1BT / E1JD candidates

The following present files were screened with the existing `0x8015 0x3482` loader and rejected as unsupported by that parser:

- `E1BR20E.dat` — 645,965 B; raw SHA-256 `53c9d50edbb9ef50d6d97c04f655a0e93d455f520bf9be053bc8988c8c297d8c`.
- `E1BR50E.dat` — 645,965 B; raw SHA-256 `7e990f4a80d2d4ad6df2c20d3b1b3ec4eb60171c604cc0c6f15f221b038871bd`.
- `E1BT40A.dat` — 645,965 B; raw SHA-256 `426e1e0c4779798d069b485ff71f78ed8e86604c1af9f83a632baab062dac015`.
- `E1JD81D.dat` — 645,965 B; raw SHA-256 `086e68c41e1476e39ccc05faa1b6d01653438bc8af45905d113fa7ddc8f13681`.

They begin with a distinct `86 10 00`-style header; none contains the expected `80 15 FC` transfer-frame marker. The existing loader cannot reconstruct them. Their file/CSV application labels remain external metadata, not decoded-image evidence.

### 310364 pair

Both files are 1,397,629 bytes and begin with an `A1 19 00 34` container header. At offset `0x24` the observed marker is `80 19 FC 88 34 81`, not the D9 `34 82` data-transfer service. The existing loader rejects both.

- `310364EM1C.dat` raw SHA-256: `772d97b5211c3f11d332b4256e5c34eb8a35c58b6832b0531fd4fe04c3c383bd`.
- `310364EP1B.dat` raw SHA-256: `177be5e04a9a1a40f20ffd64a4b287ea5476719a7e1b312358153c903f5d6944`.
- Equal raw lengths; 586 differing bytes across 118 contiguous-difference clusters. First differing offsets: `0x5`, `0x7`, `0x10`, `0x16`, `0x24`; first larger changed cluster is `0x69EF–0x69F6`.
- They are closely related containers, but their internal payload format and device/application role remain unresolved. Do not classify them as TCMs from the `310364` prefix.

## Inventory correction

The EVIDENCE directory currently contains the four D9 files and three optional E1BR/E1BT/E1JD files listed above. The three previously recommended priority variants `E1BR21E.dat`, `E1BR22E.dat`, and `E1BR23E.dat` are **not present** in the current EVIDENCE root. My earlier confirmation that all seven priority donors had been added was incorrect.

## Disposition

- D9: useful as a separate, structurally consistent 0x8019-format family for future format/architecture identification; not currently useful for EL19A SH705x table comparison.
- E1BR/E1BT/E1JD: retain as unresolved alternate-format candidates; no payload decoded.
- 310364 pair: retain unclassified; shared container characteristics and 586-byte delta only.
- No Findings record is required: this screen does not alter EL19A calibration interpretation.
- No XML, catalogue, scope matrix, workbook, ROM/LST/A2L, source tool, test, or worker queue was changed.
