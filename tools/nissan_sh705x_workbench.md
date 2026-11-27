# `tools/nissan_sh705x_workbench.py`

Unified, read-only CLI combining the cross-generation Nissan SH7055/SH7058 ROM scanner, structural `LOADER`/`FID`/`RAMF`/`IVT` metadata & checksum verifier (`ck_std`, `ck_alt2`, `LOADER80` `sum16`), EL19A metadata/XML/catalog/scope-matrix audit, variant-isolation & raw scalar diffing, and structural function/payload/A2L lead matching into one tool.

It imports helper discovery and call extraction directly from `tools/sh7058_cross_rom_scanner.py` (leaving `sh7058_cross_rom_scanner.py` unmodified).

---

## Subcommands

### 1. `scan` — Single-ROM Fingerprint, Checksums & Lookup Inventory
Loads raw `.bin`, `.zip` (`.bin`/`.s19`/`.hex`/`.dat` inside), Motorola `.s19`, Intel `.hex`, or Nissan Consult `.dat`:
- **Standard ECU `.dat` (`0x80 0x15 0xFC ... 0x34 0x82`)**: validates KWP frame checksums and inverts the 2-round 16-bit Feistel cipher into a `0xFF`-bootblock-padded SH7055 image.
- **`%6` Consult `.dat` (`0x25 0x36 <idx3> <len=0x20>`, e.g. `E1BR20E.dat`)**: validates block checksums, separates `0x80xxxx` SBL blocks, and decrypts `0x820000+` 32-byte blocks into a full 512 KiB SH7055 ROM.
- **Explicit non-SH705x / non-flat diagnostics**: validates and identifies Hitachi/Nissan TCM `0x80 0x19` `.dat` (`310364EM1C.dat`, `310364EP1B.dat`), unencrypted KWP2000 partial calibration `0xB8 0x15 0xF1` `.dat` (`8201032726.dat`), UpRev `UpRev Osiris ROM File` (`.OsirisROM`, listing header/sections), WinOLS `WinOLS File` (`.ols`/`.ols.zip`), and non-ROM image/PDF binaries (e.g. PNG `url.bin`).

Prints MCU/reset fingerprints, parsed `LOADERxx` + Application `FID`/`DATABASE` + `RAMF` pointers + `IVT` handler count, verified checksums (`ck_std` full-ROM 32-bit `sumt`/`xort`, `ck_alt2` split 32-bit at `FID-8`/`FID-4`, and `LOADER80` 16-bit `cal16@0x08200` + `main16@split`), discovered SH-2 lookup helpers across layout generations (`< 0x10000` pre-cal, `~0x15xxx` SH7055 mid-ROM, `>= 0x20000` SH7058 post-cal), resolved tables, dual-used axes, and reciprocal inverse pairs.

```bash
python3 tools/nissan_sh705x_workbench.py scan "EVIDENCE/VERSA f501.bin" --tsv /tmp/el19a_scan.tsv --json /tmp/el19a_scan.json
python3 tools/nissan_sh705x_workbench.py scan "EVIDENCE/Nissan_Qashqai_2006_2.0i_140_hp_Hitachi_BEDxxx_MECxxx_OBD_NR.zip"
python3 tools/nissan_sh705x_workbench.py scan "EVIDENCE/unknown_EM62B_SH7055.bin.zip"
python3 tools/nissan_sh705x_workbench.py scan "EVIDENCE/237108W94B.dat"
python3 tools/nissan_sh705x_workbench.py scan "EVIDENCE/E1BR20E.dat"
python3 tools/nissan_sh705x_workbench.py scan "EVIDENCE/sentra revhang/sentra_8U92A.bin"
```

Verified `scan` results across `EVIDENCE/`:
- `EVIDENCE/VERSA f501.bin` (`LOADER80`, `8CMCKRN5`, `SH705822N`): `cal16` & `main16` OK; `34` helpers, `379` calls (`364` resolved → `293` tables; `14` dual-used axes, `14` reciprocal endpoints).
- `EVIDENCE/23710-EL13A-08-C11-MR18DE-CVT.bin` (`LOADER80`, `8CMCKRN5`, `SH705822N`): `cal16` & `main16` OK; `34` helpers, `379` calls (`364` resolved → `293` tables).
- `EVIDENCE/23710-8W83B-08-C11-MR18DE-AT.bin` (`LOADER80`, `8CMCDVN3`, `SH705822N`): `cal16` & `main16` OK; `34` helpers, `379` calls (`363` resolved → `293` tables).
- `EVIDENCE/Nissan Tiida_C12W_3DD9A_705828N.bin` (`LOADER80`, `0KHDCFDZ7`, `SH705828N`): `cal16` & `main16` OK; `37` helpers, `764` calls (`734` resolved → `585` tables).
- `EVIDENCE/Nissan Juke 1.6-dig-T S19 (9APCTDEM06)/9APCTDEM06.s19` (`LOADER80`, `0KHDCFDZ7`, `SH705828N`): `main16@0x20000` OK, `cal16@0x08200` BAD (`0xC277` vs `0x5319`, sparse `0x1A000..0x1FFFF` unpopulated in engineering S19); `37` helpers, `764` calls (`734` resolved → `585` tables).
- `EVIDENCE/Nissan_Qashqai_2006_2.0i_140_hp_Hitachi_BEDxxx_MECxxx_OBD_NR.zip` (`LOADER80`, `1TRKH1HN6`, `SH705828N`, `2 MiB`): `cal16` & `main16` OK; `37` helpers, `604` calls (`595` resolved → `483` tables).
- `EVIDENCE/side project/64810223F121200000.hex` (`7V4YHZEB2`, `SH705822N`): `main16@0x20000` OK; `36` helpers, `413` calls (`391` resolved → `306` tables).
- `EVIDENCE/CF48D.bin` (`LOADER60`, `6ZV5UN11`, `SH705823N`): `ck_std` OK (`sumt@0x08C38`, `xort@0x08C30`); `34` helpers, `376` calls (`357` resolved → `279` tables).
- `EVIDENCE/23710-EE310-07-C11-MR18DE-MT.bin` (`LOADER40`, `4CMC2LPDA`, `SH705520N`): `ck_std` OK (`sumt@0x072A0`, `xort@0x07298`); `37` helpers, `327` calls (`310` resolved → `249` tables).
- `EVIDENCE/E1BR20E.dat` (`LOADER40`, `9CMCVAPD31`, `SH705520N`): `%6` decrypted cleanly (`ck_std` OK: `sumt@0x06CEC`, `xort@0x06CE4`); `36` helpers, `351` calls (`331` resolved → `267` tables).
- `EVIDENCE/unknown_EM62B_SH7055.bin.zip` (`LOADER80`, `1CMC7QPD401`, `SH705519N`): `ck_alt2`, `cal16`, `main16` OK; `34` helpers, `339` calls (`335` resolved → `275` tables); `EVIDENCE/r4r42r24r2.bin` flags `ck_alt2=BAD` and `main16=BAD`.
- `EVIDENCE/237108W94B.dat` / `237108W95B.dat` / `23710EL58B.dat` / `23710EL59B.dat` (`4CMC7NPDF2`, `SH705519N`): `ck_alt2`, `cal16`, `main16` OK; `36` helpers, `319` calls (`313` resolved → `254` tables).
- `EVIDENCE/sentra revhang/sentra_8U92A.bin` & `NoRevHang_Sentra_8U92A.bin` (`LOADER10`, `5X61BECCNA`, `SH705513N`): `ck_std` OK (`sumt@0x06508`, `xort@0x06500`); `32` helpers, `270` calls (`256` resolved → `212` tables).

---

### 2. `audit` — Unified EL19A Cross-Check & Enriched TSV Export
Cross-references EL19A caller-backed tables against:
- `CALIBRATIONS/EL19A_release1_conservative.xml` (`254` definitions)
- `CALIBRATIONS/discovered_tables_catalog.csv` (`179` rows)
- `CALIBRATIONS/RELEASE1_SCOPE_MATRIX_R1.csv` (`254` rows)
- Sibling MR18DE ROMs (`EL13A` CVT, `8W83B` AT, `EE310` pre-cal MT) for payload conservation vs. variant changes
- Structural function/payload/A2L matches against `64810223F121200000.hex` + `64811000p2_m.a2l` (`SH705822N`) and `9APCTDEM06.s19` + `RFCC_2XHK19BDF1.a2l` (`SH705828N`), including `COMPU_METHOD` engineering units/scaling and referenced `MEASUREMENT` RAM cells.

```bash
python3 tools/nissan_sh705x_workbench.py audit --tsv /tmp/el19a_audit.tsv
```

Verified `audit` summary on `VERSA f501.bin`:
- `293` caller-backed tables (`178` in Release 1 XML, `115` missing from XML/catalog/scope matrix; `76` XML-only entries).
- Flags the `1` helper-vs-XML geometry mismatch (`0x0FEE0`: XML `1x32` vs `sub_22E98` `2D_IMPL uint16 64x1` spanning `0x0FEE0-0x0FF5F`).
- Lists all `14` linked axis / reciprocal pairs (including `0x0DE6E` ↔ `0x0E2ED` and `0x0CD56` ↔ `0x0FEC0`).
- Exports a `294`-line enriched TSV (`293` table rows + header) with variant flags and dual-A2L lead columns.

---

### 3. `inspect` — Targeted Table / Function / Literal Drill-Down
Inspects any hex address in the target ROM:
- **Table address** (e.g. `0x0FEE0`, `0x0D856`): helper geometry, byte span, axis addresses, XML status, decoded ROM values, caller function(s), and top V6/Juke A2L matches with units/scales and RAM names.
- **Caller function address** (e.g. `0x6B168`): every table call inside the `4F22` prologue window plus top ranked V6 and Juke structural function matches.
- **RAM / scalar literal** (e.g. `0xFFFF85DA`): 32-bit literal pool occurrences, same-address A2L `MEASUREMENT` hint (if any), and nearest enclosing matched lookup function(s).

```bash
python3 tools/nissan_sh705x_workbench.py inspect 0x0FEE0
python3 tools/nissan_sh705x_workbench.py inspect 0x6B168
python3 tools/nissan_sh705x_workbench.py inspect 0x0D856
python3 tools/nissan_sh705x_workbench.py inspect 0xFFFF85DA
```

---

### 4. `diff` — Cross-ROM Table & Raw Scalar Diff
Compares helper-resolved lookup tables between any two ROMs (`.bin`/`.zip`/`.s19`/`.hex`/`.dat`), separating same-address matches, same-address differing calibrations, exact-payload relocations, and non-trivial unmatched/variant-specific tables. When both ROMs have equal size, appends a raw byte/scalar cluster diff outside already-reported table diffs (with ASCII/u8/u16/u32 formatting, checksum field tags `ck_std`/`ck_alt2`/`LOADER80 sum16`, axis proximity, and 32-bit literal pool cross-references; use `--raw-limit N` or `0` for unlimited).

```bash
python3 tools/nissan_sh705x_workbench.py diff "EVIDENCE/VERSA f501.bin" "EVIDENCE/23710-EL13A-08-C11-MR18DE-CVT.bin"
python3 tools/nissan_sh705x_workbench.py diff "EVIDENCE/VERSA f501.bin" "EVIDENCE/23710-8W83B-08-C11-MR18DE-AT.bin"
python3 tools/nissan_sh705x_workbench.py diff "EVIDENCE/sentra revhang/sentra_8U92A.bin" "EVIDENCE/sentra revhang/NoRevHang_Sentra_8U92A.bin"
python3 tools/nissan_sh705x_workbench.py diff "EVIDENCE/unknown_EM62B_SH7055.bin" "EVIDENCE/r4r42r24r2.bin"
python3 tools/nissan_sh705x_workbench.py diff "EVIDENCE/237108W94B.dat" "EVIDENCE/237108W95B.dat"
```

Verified `diff` metrics:
- `EL19A` vs `EL13A` (CVT): `256` identical, `37` same-address differing payloads.
- `EL19A` vs `8W83B` (AT): `1` same-addr identical, `4` same-addr differing, `258` relocated exact-payload matches (`153` non-trivial), `30` unmatched (`27` non-trivial variant-specific/changed candidates).
- `sentra_8U92A.bin` vs `NoRevHang_Sentra_8U92A.bin`: `212` identical tables, `6` non-table differing bytes in `4` clusters (`0x05AF8` u8 `44->104`, `0x05B59` u8 `10->170`, plus `ck_std xort@0x06500` and `ck_std sumt@0x06508`).
- `unknown_EM62B_SH7055.bin` vs `r4r42r24r2.bin`: `275` identical tables, `8` differing bytes (`0x10404..0x1040B` tagged as `ck_alt2 sumt/xort [OK -> BAD]`, `pool32` refs `0x14320`, `0x1431C`).
- `237108W94B.dat` vs `237108W95B.dat`: `253` identical tables, `1` same-address differing table (`0x0AFCE`), `21` non-table differing bytes in `11` clusters (`0x08200..0x08201` tagged as `LOADER80 cal16 [OK]`).

---

## Evidence Boundary

- Helper geometry, ROM byte extents, checksums, and call sites in `VERSA f501.bin` are **target-ROM structural facts**.
- Any symbol names, engineering units, scaling formulas, and `MEASUREMENT` RAM names pulled from sibling ROMs (`EL13A`, `8W83B`, `EE310`) or the V6 (`64811000p2_m.a2l`) and Juke (`RFCC_2XHK19BDF1.a2l`) A2L pairs are **structural leads / hypotheses only** — never proof on EL19A until independently verified in EL19A target code (reader + consumer trace).
