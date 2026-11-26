# SH7058 / SH7055 Cross-ROM Lookup-Helper & Calibration Scanner (`tools/sh7058_cross_rom_scanner.py`)

Pure Python 3 (standard library only) read-only SH-2 big-endian scanner for Nissan/Hitachi SH7055 and SH7058 ECU binaries (`.bin` or `.zip`).

## What It Does

1. **Auto-discovers lookup helpers** (`2D_IMPL`, `2D_AXIS`, `3D_IMPL`, `3D_AXIS`) across both post-calibration (`0x15xxx..0x27xxx`, `mov.l` `0xD7xx`/`0xD6xx`) and early pre-calibration (`0x05xxx..0x07xxx`, `mov.w` `0x97xx`/`0x96xx`) Nissan/Hitachi SH-2 helper layouts (`0x04000..0x80000`), recovering element type (`uint8`/`int8`/`uint16`/`int16`), dimensions, and axis widths without requiring a disassembly `.lst` or symbol file.
2. **Infers ROM layout & tracks call-site arguments** across executable code using a bounded SH-2 forward register window (`r4` = table pointer, `r5` / `r6` = axis pointers, supporting both `mov.l` and `mov.w` helper/table loads up to a 20-instruction load-to-call window).
3. **Audits EL19A against Release 1 XML** (`CALIBRATIONS/EL19A_release1_conservative.xml`), identifying caller-backed tables absent from the XML and geometry/type disagreements (`CF48D.xml` is also checked when `CF48D.bin` is scanned).
4. **Cross-matches sibling ROMs** by same-address+kind and exact table payload bytes (reporting total matches and non-trivial matches with `>2` distinct byte values).

## Usage

Run from repository root:

```bash
python3 tools/sh7058_cross_rom_scanner.py
```

Custom ROM / XML / sibling paths (`.bin` or `.zip`):

```bash
python3 tools/sh7058_cross_rom_scanner.py \
  --el19a "EVIDENCE/VERSA f501.bin" \
  --xml "CALIBRATIONS/EL19A_release1_conservative.xml" \
  --siblings "EVIDENCE/23710-EE310-07-C11-MR18DE-MT.bin" "EVIDENCE/CF48D.bin"
```

## Verified Benchmark Across All 8 Raw Repository ROMs

### Baseline (`VERSA f501.bin` — EL19A, `8CMCKRN5`, `SH705822N`, SHA-256 `bfe037e8e6c3...`)

- **Auto-discovered helpers:** `34` (`2D_IMPL=9`, `2D_AXIS=9`, `3D_IMPL=2`, `3D_AXIS=14`)
- **Call sites:** `379` total, `364` with resolved ROM table pointers (`293` unique table addresses)
- **Release 1 XML overlap (`254` tables):** `178` matched in XML, `115` caller-backed tables not in Release 1 XML (`2D_IMPL=71`, `2D_AXIS=32`, `3D_AXIS=11`, `3D_IMPL=1`, including `0x0AFF2` `4×4` @ `0x5B3C0`)
- **Scanner vs XML geometry/type disagreements:** `1` genuine mismatch:
  - **`0x0FEE0`:** XML/scope matrix list `2D uint16 1×32` (`0x0FEE0–0x0FF1F`, `64 B`), whereas `sub_22E98` (`max_val=0x3F00`, clamp `add #0x7E, r4` = `+126 B` at `0x22EA6`, `mov.w @r4, r0` at `0x22EAA`) + `sub_234FC` (8 shifts, `idx = r5 >> 8`) index a **`64×1 uint16` curve** (`0x0FEE0–0x0FF5F`, `128 B`, grid `0, 256, …, 16128`), with `0x0FF60+` zero-padded.

### Sibling Comparison

| ROM | Variant / MCU | Helpers | Call Sites (Resolved / Unique) | Same-Addr+Kind vs EL19A | Exact Payload Matches (Non-Trivial) | Practical Porting Outlook |
|---|---|---:|---:|---:|---:|---|
| `23710-EL13A-08-C11-MR18DE-CVT.bin` | C11 MR18DE CVT (`SH705822N`, `8CMCKRN5`) | 34 | 379 (364 / 293) | 293 | 259 (162) | Code-identical to EL19A; differing payloads isolate MT vs CVT calibrations directly |
| `23710-8W83B-08-C11-MR18DE-AT.bin` | C11 MR18DE AT (`SH705822N`, `8CMCDVN3`) | 34 | 379 (363 / 293) | 14 | 253 (158) | Same 34-helper set and 293-table layout shifted in ROM; strong mechanical + payload portability |
| `23710-EE310-07-C11-MR18DE-MT.bin` | 2007 C11 MR18DE MT (`SH705520N`, `4CMC2LPDA`, 512 KiB) | 37 | 327 (310 / 249) | 0 | 191 (99) | Pre-cal helper band (`0x05A54..`); strong MT-to-MT payload similarity (`99` non-trivial matches) |
| `unknown_EM62B_SH7055.bin.zip` | `1EM62B00` / `1CMC7QPD4` (`SH705519N`, 512 KiB) | 34 | 339 (335 / 275) | 0 | 118 (38) | Mid-ROM helpers (`0x15364..`); clean structural extraction (`0x8E6E–0x1199C`) |
| `CF48D.bin` | `1CF48D1C` (`SH705823N`, 1 MiB) | 34 | 376 (357 / 279) | 0 | 104 (32) | Pre-cal helper band (`0x06E10..`); matches `57` tables in `CF48D.xml` (`0` explicit geometry diffs; `137` XML entries are 1D scalars/other readers) |
| `Nissan Tiida_C12W_3DD9A_705828N.bin` | Tiida C12W (`SH705828N`) | 37 | 764 (734 / 585) | 0 | 221 (33) | Clean structural extraction; 2x table count and relocated code limit direct payload porting |
| `Nissan_Qashqai_2006_2.0i_140_hp_Hitachi_BEDxxx_MECxxx_OBD_NR.zip` | 2.0L MR20DE (`SH705828N`, `1TRKH1HN`, 2 MiB `0xFF`-padded) | 37 | 604 (595 / 483) | 0 | 242 (72) | Clean structural extraction (`0x09B26–0x16F2C`); <0.1% code overlap blocks automatic label transfer |

## Key Insights & Current Limitations

- **Cross-generation ABI continuity:** From 512 KiB `SH7055` (`4CMC`/`1CMC`) through 1 MiB `SH705822N`/`SH705823N` to `SH705828N` (including `0xFF`-padded 2 MiB reads), Nissan/Hitachi kept the same four lookup-helper stub patterns and `r4`/`r5`/`r6` register contract, shifting only helper placement and `mov.w` vs `mov.l` pool addressing.
- **EL19A structural observations:**
  - `0x0DE6E` and `0x0E2ED` form a bidirectional inverse 2D axis/table pair (both called via `sub_22F28`, each passing the other as `r5`).
  - `0x0FEC0` is dual-used as a direct 2D curve via `sub_22F80` and as an explicit Y-axis for `0x0CD56` via `sub_22D68`.
- **Known limits:**
  - Only tracks local intra-window register loads (`56` bytes before call, `20` insns from helper-addr load to `jsr`/`jmp`); tables/axes constructed across earlier function calls or dynamic pointer arithmetic stay `None` (`unresolved`).
  - Pre-cal ROMs (`min(helpers) < 0x10000`) use `cal_hi = 0x14000`; if a different pre-cal firmware places tables above `0x14000`, `infer_layout()` bounds may need widening.
  - Exact-payload matching counts include flat/trivial fills; always rely on the non-trivial match count (`>2` distinct bytes) and verify via caller/RAM lineage before assigning semantics on diverged ROMs.
