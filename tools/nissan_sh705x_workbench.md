# `tools/nissan_sh705x_workbench.py`

Unified, read-only CLI combining the cross-generation Nissan SH7055/SH7058 ROM scanner, EL19A metadata/XML/catalog/scope-matrix audit, variant-isolation diffing, and structural function/payload/A2L lead matching into one tool.

It imports helper discovery and call extraction directly from `tools/sh7058_cross_rom_scanner.py` (leaving `sh7058_cross_rom_scanner.py` unmodified).

---

## Subcommands

### 1. `scan` — Single-ROM Fingerprint & Lookup Inventory
Loads raw `.bin`, `.zip` (`.bin`/`.s19`/`.hex`/`.dat` inside), Motorola `.s19`, Intel `.hex`, or Nissan Consult `.dat` (validating KWP `0x8015 0x3482` frame checksums and inverting the 2-round 16-bit Feistel cipher into a 512 KiB `0xFF`-bootblock-padded SH7055 image), prints MCU/FID/reset fingerprints, discovers SH-2 lookup helpers across layout generations (pre-cal `mov.w < 0x10000`, SH7055 mid-ROM `~0x15xxx`, SH7058 post-cal `>= 0x20000`), resolves table calls, and detects dual-used axes and reciprocal inverse table pairs.

```bash
python3 tools/nissan_sh705x_workbench.py scan "EVIDENCE/VERSA f501.bin" --tsv /tmp/el19a_scan.tsv --json /tmp/el19a_scan.json
python3 tools/nissan_sh705x_workbench.py scan "EVIDENCE/Nissan_Qashqai_2006_2.0i_140_hp_Hitachi_BEDxxx_MECxxx_OBD_NR.zip"
python3 tools/nissan_sh705x_workbench.py scan "EVIDENCE/unknown_EM62B_SH7055.bin.zip"
python3 tools/nissan_sh705x_workbench.py scan "EVIDENCE/237108W94B.dat"
python3 tools/nissan_sh705x_workbench.py scan "EVIDENCE/sentra revhang/sentra_8U92A.bin"
```

Verified `scan` results:
- `EVIDENCE/VERSA f501.bin` (`SH705822N`, `8CMCKRN5`): `34` helpers, `379` call sites (`364` resolved → `293` unique tables; `14` dual-used as axes, `14` reciprocal-pair endpoints).
- `Nissan_Qashqai_2006_2.0i_140_hp_Hitachi_BEDxxx_MECxxx_OBD_NR.zip` (`SH705828N`, `1TRKH1HN`): `37` helpers, `604` call sites (`595` resolved → `483` unique tables).
- `unknown_EM62B_SH7055.bin.zip` (`SH705519N`, `1CMC7QPD`): `34` helpers, `339` call sites (`335` resolved → `275` unique tables).
- `237108W94B.dat` / `237108W95B.dat` / `23710EL58B.dat` / `23710EL59B.dat` (`SH705519N`, `4CMC7NPD`): `36` helpers, `319` call sites (`313` resolved → `254` unique tables).
- `sentra_8U92A.bin` (`SH705513N`, pre-cal): `32` helpers, `270` call sites (`256` resolved → `212` unique tables).

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
Compares helper-resolved lookup tables between any two ROMs (`.bin`/`.zip`/`.s19`/`.hex`/`.dat`), separating same-address matches, same-address differing calibrations, exact-payload relocations, and non-trivial unmatched/variant-specific tables. When both ROMs have equal size, appends a raw byte/scalar cluster diff outside already-reported table diffs (with ASCII/u8/u16/u32 formatting, axis proximity, and 32-bit literal pool cross-references; use `--raw-limit N` or `0` for unlimited).

```bash
python3 tools/nissan_sh705x_workbench.py diff "EVIDENCE/VERSA f501.bin" "EVIDENCE/23710-EL13A-08-C11-MR18DE-CVT.bin"
python3 tools/nissan_sh705x_workbench.py diff "EVIDENCE/VERSA f501.bin" "EVIDENCE/23710-8W83B-08-C11-MR18DE-AT.bin"
python3 tools/nissan_sh705x_workbench.py diff "EVIDENCE/sentra revhang/sentra_8U92A.bin" "EVIDENCE/sentra revhang/NoRevHang_Sentra_8U92A.bin"
python3 tools/nissan_sh705x_workbench.py diff "EVIDENCE/237108W94B.dat" "EVIDENCE/237108W95B.dat"
```

Verified `diff` metrics:
- `EL19A` vs `EL13A` (CVT): `256` identical, `37` same-address differing payloads.
- `EL19A` vs `8W83B` (AT): `1` same-addr identical, `4` same-addr differing, `258` relocated exact-payload matches (`153` non-trivial), `30` unmatched (`27` non-trivial variant-specific/changed candidates).
- `sentra_8U92A.bin` vs `NoRevHang_Sentra_8U92A.bin`: `212` identical tables, `6` non-table differing bytes in `4` clusters (`0x05AF8` u8 `44->104`, `0x05B59` u8 `10->170`, `0x06500..0x06501`, `0x06508..0x06509`).
- `unknown_EM62B_SH7055.bin` vs `r4r42r24r2.bin`: `275` identical tables, `8` differing bytes (`0x10404..0x1040B`, `pool32` refs `0x14320`, `0x1431C`).
- `237108W94B.dat` vs `237108W95B.dat`: `253` identical tables, `1` same-address differing table (`0x0AFCE`), `21` non-table differing bytes in `11` clusters.

---

## Evidence Boundary

- Helper geometry, ROM byte extents, and call sites in `VERSA f501.bin` are **target-ROM structural facts**.
- Any symbol names, engineering units, scaling formulas, and `MEASUREMENT` RAM names pulled from sibling ROMs (`EL13A`, `8W83B`, `EE310`) or the V6 (`64811000p2_m.a2l`) and Juke (`RFCC_2XHK19BDF1.a2l`) A2L pairs are **structural leads / hypotheses only** — never proof on EL19A until independently verified in EL19A target code (reader + consumer trace).
