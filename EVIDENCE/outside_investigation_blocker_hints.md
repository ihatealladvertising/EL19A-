# Outside Investigation Run: Overlooked Repo Hints & Creative Blocker Bypasses

**Scope & Provenance Rule:** Read-only audit of the existing repository (`/EVIDENCE/`, `/CONTROL/`, `/INDEX/`, `/FINDINGS/`) executed strictly to uncover overlooked, high-leverage hints that unlock current project blockers. No protected files (`VERSA f501.bin`, LSTs, XMLs, A2Ls, `CONTROL/`, `INDEX/`, `FINDINGS/`, `CALIBRATIONS/`, or existing scripts/evidence) were modified, and `EVIDENCE/using youtube videos.txt` was never accessed. Every entry separates **Verified Repo Fact** (exact file path, PC, byte offset, hash/match count, or documented hardware register) from **Creative Hypothesis / Bypass** and gives the **Smallest Falsifiable Test**. Donor labels (A2Ls, `.ols`, RomRaider XMLs, screenshots) are treated strictly as structural priors requiring target-ROM (`EL19A`) verification.

---

## Executive Summary: Highest-Leverage Unlocks

1. **`WO65118` XREF Global Double-Scaling Bug (`4,822 / 22,308` rows corrupted):** `EVIDENCE/WO65118_ram_byte_bit_xref_generator.py` parses byte-scaled displacements from IDA text and multiplies by `SCALE` again (`w` → `4x`, `l` → `16x`). This explains ~20+ repetitive false-EA micro-WOs (`WO65329`–`WO65698`+) from one root bug.
2. **`off_808B4` (`WO65623`–`WO65719`) Out-of-Bounds Walk Past a 198-Slot Table:** `sub_806BC` (`0x806C6`) caps index `r5 < 0xC6` (`198`). Slots `0xC6+` (`0x13A98+`) walk right off the table end across EL19A's ASCII FID (`8CMCKRN5`), CPU string (`SH705822N`), init vectors, and a 16-byte ADC descriptor array pointing at SH7058 `ADDR0..ADDR31` (`0xFFFFF800–0xFFFFF84B`, e.g., `0xFFFFF838/39` = `ADDR28`).
3. **`FFFF1800–FFFF1848` Overlay Paradox (`WO65493` / `WO65505`) Solved by `SH7058.PDF` + Struct-Base Writes:** `0xFFFF1800` is the Renesas SH7058 User Program Mode RAM buffer (`FTDAR = H'03`, entry points `FTDAR+16 = 0xFFFF1810` Erase/Program and `FTDAR+32 = 0xFFFF1820` Init) *only* during Flash mode (`0x4B40`, `FCCS = 0xFFFFE800`). Outside Flash mode it is normal shared RAM written via unmodeled base+disp pointers off `FFFF180C`/`FFFF181C`/`FFFF182C` (`0x292CE`, `0x292DC`, `0x20BBA`, `0x369F2`, `0x37184`, `0x36A24`, `0x2928E`, `0x29182`).
4. **Ignition Timing Sink-First Bypass (`WO65730` & `WO65287`):** OBD Mode 01 PID `0x0E` (`0x322B4`, `0xB90F2`) computes `128 + 2*(U8[0x841D] - FFFF85CB)` where `U8[0x841D] = 0x70` (`112`). Its producer at `0x470CE–0x47188` reads `FFFF1992` (`@(2, FFFF1990)`), `FFFF1E64.bit0`, and `FFFF3632.bit3` to write `FFFF85CB`. Combined with `EVIDENCE/64811000p2_m.a2l` (`vLADVTRM`/`vADVTRMAP`/`vFADV`) and `EVIDENCE/rr forum ignition tables.txt`, this links directly to `0x473AA–0x47408` stripping bit 7 (`& 0x7F`, `0x80` knock-window flag) from `0x9B2E` and `0x9C2E`.
5. **`EM43A.OsirisROM` Q4 `p256` IoC (`WO65569`–`WO65725`) Exposed as Encrypted `0xFF` Padding:** `VERSA f501.bin` Q4 (`0xC8000–0xFFFFF`) is `100.00%` `0xFF` padding (5 non-`FF` tail bytes). Comparing aligned `EM43A.OsirisROM` vs `EM43A Back To Stock.OsirisROM` (both have `ROMData ` header at `0x60..0x73` and tagged chunks like `Keys    `, `Verify  `, `CELData2` after `0x100074`), `T ^ S` shows `w0 == w1 == w3` on `2,560 / 10,240` (`25.00%`) Q4 16-byte blocks—exclusively at `file_off % 32 == 0` (`1,280` at `%64 == 0`, `1,280` at `%64 == 32`, `0` at `16`/`48`)—proving structured 32/64-byte keystream leakage over uniform padding.
6. **Untapped Sister Binaries & Crosswalk Assets:** `23710-8W83B-08-C11-MR18DE-AT.bin` (`8CMCDVN3`) shares **5,463** exact 64-byte chunks with `EL19A` (`VERSA f501.bin`, `8CMCKRN5`), and `23710-EL13A-08-C11-MR18DE-CVT.bin` shares **4,607** exact 64-byte chunks; plus `EVIDENCE/64811000p2_m.a2l` (5.5 MB), `RFCC_2XHK19BDF1.a2l` (3.76 MB), `Renault 3.5 V6 SH7058 4.09.ols.zip` (3,736 unique `m*` symbols + embedded 1 MiB SH7058 ROM), `NissanDefinitions-master/Nissan Definitions/A2L.xml` (2,668 lines), `US6276333.pdf` (Nissan ETC `QH0`/`TVO`/first-order lag patent), and `EVIDENCE/url.bin` (misnamed 814×611 RGBA PNG).

---

## 1. Root-Cause Bug in `WO65118` XREF (Explains ~20+ False-EA Micro-WOs)

- **Blocker:** Ongoing wave of single-EA repair WOs (`WO65329`–`WO65698`+) triggered by impossible/unproduced `WO65118` RAM addresses (`WO65493 §5` patched 3 examples: `0x292DC`, `0x7B2D8`, `0x37154` without diagnosing the generator).
- **Verified Repo Fact:**
  - In `EVIDENCE/WO65118_ram_byte_bit_xref_generator.py`, line 343 parses `disp` from **IDA disassembly text** (`mov.w @(h'10,gbr)` / `mov.l @(h'40,gbr)`), where IDA *already* displays the **byte-scaled** displacement (`disp_raw * width_bytes`).
  - Line 359 then executes `offset = disp * scale` (`SCALE = {"b": 1, "w": 2, "l": 4}`), double-scaling every non-byte `gbr_disp` and `base_disp` row (`effective_offset = raw_disp * scale^2`, so `w` = `4x` and `l` = `16x`).
  - Direct audit of `EVIDENCE/WO65118_ram_byte_bit_xref.tsv` (`22,308` data rows):
    - `gbr_disp` (`w`): `2,526` rows
    - `gbr_disp` (`l`): `1,206` rows
    - `base_disp` (`w`): `914` rows
    - `base_disp` (`l`): `176` rows
    - **Total corrupted rows:** **`4,822 / 22,308` (`21.62%`)** (`3,440` word rows + `1,382` longword rows).
  - *Note:* `tools/rom_access_indexer.py` avoids this by decoding raw 16-bit SH-2 opcodes directly.
- **Creative Bypass:** Stop filing per-EA corrective WOs against `WO65118_ram_byte_bit_xref.tsv`. Either switch RAM xref queries to opcode-level decoding or mechanically un-scale any `gbr_disp`/`base_disp` row via:
  $$\text{true\_ea} = \text{base} + \frac{\text{listed\_ea} - \text{base}}{\text{width\_bytes}} \quad (\text{width\_bytes} \in \{2, 4\})$$
- **Smallest Falsifiable Test:** Take the 3 previously flagged `WO65493 §5` EAs (`0x292DC`, `0x7B2D8`, `0x37154`) and 10 random `(gbr_disp|base_disp, w|l)` rows from `WO65118_ram_byte_bit_xref.tsv`, compute `(listed_ea - base) // width_bytes`, and verify 100% match against raw SH-2 opcode decoding in `VERSA f501.bin`.

---

## 2. `off_808B4` (`WO65623`–`WO65719`) Is an Out-of-Bounds Walk Past a 198-Slot Table

- **Blocker:** Repetitive index-band micro-WOs (`WO65623`, `WO65683`–`WO65719`) cataloging "table indices `0x100..0x1AF`" off `off_808B4` (`0x13780`) and puzzling over a 4-dword `0x180..0x1AF` cadence (`WO65719`).
- **Verified Repo Fact:**
  - In `EL19A` disassembly (`0x806C6`–`0x806EE`), `sub_806BC` executes `mov #-0x3A, r5 ; extu.b r5, r5` (`r5 = 0xC6 = 198`), bounding `off_808B4` (`dword_13780`) to **exactly 198 longword slots (`0x00..0xC5`, `0x13780..0x13A97`)**.
  - Slot `197` (`0x13A94`) is `0x000116BC`. Immediately at `0x13A98` ("index `0xC6`") sits ASCII `"8CMCKRN5"` (the EL19A FID), followed at `0x13AA8` by `"DATABASE...N.SH705822N"`, `0x13AD8` init vectors, and from `0x13B44+` through `0x13D80..0x13E40` ("indices `0x100..0x1AF`") a **16-byte struct array** (`FF FF F8 xx | FF FF F8 39 | FF FF F8 38 | 07/08/09/0A/0B 00 00 00 | FF FF F8 xx`).
  - `EVIDENCE/SH7058.PDF` (pp. 623–624, 1070–1071) documents `0xFFFFF800–0xFFFFF84B` as the SH7058 **A/D Converter Data Registers (`ADDR0..ADDR31`)** (`0xFFFFF838/39` = `ADDR28`).
- **Creative Bypass:** Close `WO65719`-class index-band walks immediately as OOB artifacts. Instead, disassemble the real consumer of the `0x13B44+` ADC-descriptor struct array to auto-label every ADC sensor channel (`0xFFFFF800–0xFFFFF84B`) and its destination RAM cell in one pass.
- **Smallest Falsifiable Test:** Search `EL19A` LST for literal pool references to `0x13B44` (or `0x13B40..0x13D80`) and verify the reader indexes 16-byte descriptors (`shll2`/`shll2`) rather than `sub_806BC` (`r5 < 0xC6`).

---

## 3. `FFFF1800–FFFF1848` Overlay Paradox (`WO65493` / `WO65505`) Solved by `SH7058.PDF` + Struct Bases

- **Blocker:** `WO65493` and `WO65505` could not reconcile `jsr @rN` targeting `0xFFFF1820` (`0x4BB0`) / `0xFFFF1810` (`0x4C6E`) or why `FFFF1820`, `FFFF1830`, `FFFF1838`, `FFFF1840`, `FFFF1844`, `FFFF1848` looked "read without writes" at runtime.
- **Verified Repo Fact:**
  - `EVIDENCE/SH7058.PDF` §23.5.2 (pp. 875–877, Figs. 23.12–23.13) documents on-chip Flash User Program Mode:
    - `0xFFFFE800` = **`FCCS`** (Flash Code Control Status).
    - **`FTDAR = H'03`** sets the Flash micro-ROM download destination to **`0xFFFF1800`**.
    - Renesas's sequence sets `VBR = 0` (`0x4B78`), triggers `FCCS.SCO=1`, checks `DPFR` at `FTDAR+0 = 0xFFFF1800` (`0x4B60`/`0x4B96`), calls **Initialization at `FTDAR + 32 = 0xFFFF1820`** with `r4 = FPEFEQ = 0x0FA0` (`40.00 MHz`) and `r5 = FUBRA = 0` (`0x4BAE–0x4BB0`), and calls **Erase/Program at `FTDAR + 16 = 0xFFFF1810`** (`0x4C6E`).
  - `movca.l` count in the entire `EL19A` LST is **`0`** (no cache-RAM trick).
  - Outside the Flash programming routine (`0x4B40`), `FFFF180C`, `FFFF181C`, and `FFFF182C` appear `158` times in runtime routines (`sub_20B80`, `sub_28C36`, `sub_35EA0`, `sub_369D0`, `sub_36A26`, etc.), and write those exact "unproduced" fields via struct-base offsets:
    - `FFFF180C + 0x02` → **`FFFF180E`** (`0x292CE`)
    - `FFFF181C + 0x02` → **`FFFF181E`** (`0x292DC`)
    - `FFFF181C + 0x08` / `FFFF182C + 0x08` → **`FFFF1824`** / **`FFFF1834`** (`0x20BBA`)
    - `FFFF182C + 0x02` → **`FFFF182E`** (`0x369F2`)
    - `FFFF182C + 0x04` → **`FFFF1830`** (`0x37184`)
    - `FFFF182C + 0x14` → **`FFFF1840`** (`0x36A24`)
    - `FFFF182C + 0x18` → **`FFFF1844`** (`0x2928E`)
    - `FFFF182C + 0x1C` → **`FFFF1848`** (`0x29182`)
- **Creative Bypass:** Model `0xFFFF1800+` cleanly as a dual-mode region: (a) Flash micro-ROM workspace solely during Flash boot/reprogramming (`0x4B40`), and (b) runtime RAM struct fields indexed from `FFFF180C`/`181C`/`182C`/`1860` (and `GBR = FFFF17D0` in `sub_35EA0`), terminating false "mystery RAM" chasing in `WO65493`/`WO65505`.
- **Smallest Falsifiable Test:** Verify callers of `0x4B40` in LST are gated by boot/reprogramming session state (`FCCS` / K-line/CAN seed-key) and never invoked during normal closed-loop engine runtime, and trace `sub_369D0`/`sub_36A26` for the remaining `FFFF1820`/`1838` offsets (e.g., via `FFFF1800`/`1818`/`1820` pointers or GBR `FFFF17D0`).

---

## 4. `WO65730` & `WO65287` Ignition `-64` / `128`-Flag Sink-First Bypass

- **Blocker:** Tracing forward from `0x9B2E` / `0x9C2E` / `0x9DAE` ignition maps stalled (`WO65730`, `WO65287`) because intermediate trims (`mMBTM`, `vADVHOS`, knock retard, dwell/clamp) branch heavily.
- **Verified Repo Fact:**
  - **OBD Mode 01 PID `0x0E` (Timing Advance)** at `0x322B0–0x322E8` and `0xB90E0–0xB9140` executes:
    `sub_33E18(clamp((U8[0x841D] - U8[FFFF85CB]) * 2, -128, 127) + 0x80)`
    where `0x0000841D = 0x70` (`112`).
  - **Direct Producer of `FFFF85CB`** at `0x470CE–0x47188` (`GBR = FFFF85C4`, `0x470D0–0x470D2`):
    - Reads `U8[0x841D]` (`0x70`) minus `U8[FFFF1992]` (`@(2, FFFF1990)` at `0x47136`), optionally subtracts `U8[0x8435]` if `FFFF1E64.bit0` is set (`0x47140–0x4714E`), clamps `[0, U8[0x86F1]]`, stores to **`@(7, gbr)` (`FFFF85CB`)** (`0x4716C`), and if `FFFF3632.bit3` (`@(0xA, FFFF3628)`) is set, subtracts `0x14` (`20`) and overwrites **`FFFF85CB`** (`0x4717C`), then calls `sub_27720`.
  - **`0x47284`** (`bsr calculate_state_dependent_correction_1992`) sits immediately above `0x47288` (`bsr sub_470CC`) in the same parent block!
  - **Upstream `0x9B2E` / `0x9C2E` Knock-Flag Strip** at `0x473AA–0x47408`:
    - Calls `sub_22CB8(0x9B2E)`, masks bit 7 (`and #h'80, r0` → `@(0x14, r15)` at `0x473C6–0x473CC`), masks lower 7 bits (`and #h'7F, r13` at `0x473CE–0x473D0`), and repeats the exact same split for `0x9C2E` (`@(0x18, r15)` and `r14` at `0x473EA–0x473F4`).
  - **External Domain Confirmation in Untapped Repo Files:**
    - `EVIDENCE/64811000p2_m.a2l` defines `vLADVTRM` (`"Trimming-map compensation value"`, `UBYTE`, `-64..191`), `vADVTRMAP` (`"Trimming-map reference value"`, `UBYTE`, `-64..191`), `mMBTM` (`"Ignition timing main constant"`), `vADVHOS` (`"The amount of ADV compensation"`, `SWORD`), and `vFADV` (`"A final ignition timing"`, `UBYTE 0..255` feeding `Gst_on_can_1_0_1` OBD PID `0x0E`).
    - `EVIDENCE/rr forum ignition tables.txt` documents this exact Nissan pipeline: strip bit 7 (`128` knock-window flag) from `vLADVTRM` → `vADVTRMAP` (`raw - 64` deg), sum with MBT + `vADVHOS` + trims → `vFADV` (OBD `0x0E`).
    - `EVIDENCE/Untitled.png` vs `EVIDENCE/Alex CD700.png` visually confirms raw bytes `123..131` inside the knock window (`128 ± 5`) vs `-5..+3°` once `128` (`0x80`) is masked.
- **Creative Bypass:** Walk **backward** from `0x4716C` (`FFFF85CB`) → `FFFF1992` → `0x47284` (`calculate_state_dependent_correction_1992`) and `0x471D4`/`0x47280`, meeting `0x473C4–0x47408` (`r13`/`r14` + `@(0x14,r15)`/`@(0x18,r15)`) in the middle (~150 bytes of code instead of blind forward fan-out). Also check `0x42ABE` (`FFFF1E60`) next to `0x42BA2`/`0x42BBE` (`9C2E`/`9DAE`).
- **Smallest Falsifiable Test:** Disassemble `0x47408–0x47598` and `0x4718C–0x47276` to confirm the RAM slots holding `r13`/`r14` (`vADVTRMAP` candidate) and `@(0x14,r15)`/`@(0x18,r15)` feed `calculate_state_dependent_correction_1992` (`FFFF1992`) and/or `0x470DE–0x47136`.

---

## 5. `EM43A.OsirisROM` Q4 `p256` IoC Loop (`WO65569`–`WO65725`) Exposed as Padding Keystream Leakage

- **Blocker:** Multi-WO effort (`WO65569`–`WO65725`) trying to interpret 64/256/512-byte periodicity inside `EM43A.OsirisROM` Q4 (`0xD8000–0xFFFFF`) as ROM code/table structure.
- **Verified Repo Fact:**
  - In `EVIDENCE/VERSA f501.bin` (same 1 MiB SH7058 family), **`0xC8000–0xFFFFF` is `100.00%` `0xFF` padding** except `5` non-`FF` bytes near EOF checksum/tail.
  - Both `EVIDENCE/EM43A.OsirisROM` (`1,049,801` B) and `EVIDENCE/EM43A Back To Stock.OsirisROM` (`1,048,838` B) share the same header (`UpRev Osiris ROM File Ver 1.0000`, `'fBH`'`, `ROMData ` chunk starting at `0x60..0x73`, `1 MiB` payload), with `Keys    `, `Verify  `, `CELData2`, `AITuneDesc`, `TuneVer ` metadata chunks appended *after* `0x100074`.
  - Single-file autocorrelation on `EM43A.OsirisROM` Q4 (`0xD8000–0xFFFFF`):
    - At `p = 512`, `tuned[i] == tuned[i+512]` occurs at `6.28%` (`1/16`), specifically **128 of 512 offsets (`offset % 4 == 0`) match at `25.1%` (`1/4`)**, while `p = 16, 32, 64, 128` have `0.00%` self-matches.
    - Comparing aligned `T ^ S` across Q4 (`10,240` 16-byte blocks): **exactly `2,560 / 10,240` (`25.00%`) satisfy `w0 == w1 == w3`**, and **100% of those occur at `file_off % 32 == 0`** (`1,280` at `%64 == 0`, `1,280` at `%64 == 32`, `0` at `16` or `48`).
- **Creative Bypass:** Stop running table/code IoC hunts (`WO65725`) inside encrypted `0xFF` padding (`0xD8000–0xFFFFF`). Because plaintext is known (`0xFF`), `EM43A Q4 ^ 0xFF` *is directly the raw UpRev keystream*—turning Q4 from a dead-end mystery into a known-plaintext oracle if UpRev cipher recovery is ever wanted, and allowing immediate deprecation of Q4 IoC micro-WOs.
- **Smallest Falsifiable Test:** Compare `T[off] ^ S[off]` at `0xD8000..0xFFFFF` against `0x00000..0x02000` (known non-`FF` header/vectors); if `w0 == w1 == w3` disappears in non-`FF` regions and reappears in any other large `0xFF` pad gap (e.g. `0xBxxxx–0xC8000` if present), the `0xFF`-keystream diagnosis is 100% confirmed.

---

## 6. High-Leverage Shortcuts for `WO65724` (PID-to-Table Joins), `WO65502` (`0x5B5CE`), & `WO65284`

### A. `WO65724` (`INDEX/catalog_179_consumer_summary.tsv` 1-Hop RAM Join)
- **Verified Repo Fact:** Only **`23 / 179`** (`12.8%`) catalog tables currently have populated `query_pid_semantics` (`156 / 179` have `-`). The single most common unmapped query RAM cell is **`FFFF85A9`** (`11` tables), followed by `FFFF84EA` (`4`), `FFFF859C` (`3`), `FFFF84E4` (`3`), `FFFF8494` (`2`), `FFFF84D4` (`2`), `FFFF8521` (`2`), `FFFF851E` (`2`), `FFFF2294` (`2`), `FFFF854A` (`2`).
- **Creative Bypass:** Instead of auditing 156 tables individually, trace the **single producer** of `FFFF85A9` (`@(h'D, FFFF859C)`—likely a filtered/conditioned sensor byte derived 1 hop from an existing `obd_mode01`/`consult_mode22` sensor or `ADDRx`), unlocking all **11** tables in one shot; repeat for `FFFF84EA` and `FFFF84E4`.
- **Smallest Falsifiable Test:** Trace the writer of `FFFF85A9` (via `GBR = FFFF859C` or `@(h'D, rN)` stores in `EL19A` LST, ~10 candidate sites) back to its ADC/Mode01/Mode22 source.

### B. `WO65502` (`sub_22E7C @ 0x5B5CE` Reading `0x108B4`)
- **Verified Repo Fact:** Disassembly at `0x5B5BC–0x5B61C` proves `sub_22E7C` (`0x5B5CE`) reads `0x108B4` indexed by `(U8[FFFF859C + 0x0D] << 8)` = **`FFFF85A9`** (`r5`), stores `U16` result at `FFFF1054 + 0x2CA0 = FFFF3CF4`, and immediately uses `r2` as a `[0..0x10000]` blending/lag weight between `FFFF1D4E` (`r8+0x3C`) and `FFFF1D54` (`r8+0x42`) + `FFFF6F14` (`r12+0x5EC0`)! Thus solving `FFFF85A9` simultaneously solves `WO65502` AND 11 `catalog_179` tables.

### C. `WO65284` Stale Deferral
- **Verified Repo Fact:** `CONTROL/WO65284.md` remains marked `DEFERRED — pending unstarted WO65285`, even though `CONTROL/WO65285.md` is already **`CLOSED — BOUNDED COMPLETE (NO-GO)`** for universal 1D A2L declaration ordering. `WO65284` already meets its explicit closeout trigger and can be closed cleanly without further work.

### D. Direct Quick Answers Verified in LST (`WO65728` & `WO65722`)
- **`WO65728` (`0x3634–0x363A`):** Immediately after `0x3632 and #h'7F, r0`, `0x3634` executes `mov.b r0, @((dword_8220 - h'821C), gbr)` (**net CLEAR `0x7F` at first store `0x3634`**), followed at `0x3636–0x364C` by sequential bit-clear masks (`0xBF`, `0xDF`, `0xE7`, `0xFB`) on `FFFF8220` before `0x3650 or #2`.
- **`WO65722` (`0x91444–0x9144C`):** Contains `0x91444 mov r12, r0`, `0x91446 and #h'FD, r0`, `0x91448 mov.l off_916A8, r2 ; FFFF360C`, `0x9144C mov.b r0, @(1, r2)` — **GBR (`FFFF9714`) is preserved**, with zero GBR writes or GBR-relative accesses.

---

## 7. Untapped Donor Twins, Official A2Ls, WinOLS Dictionaries, & Patents in `/EVIDENCE/`

| Asset in `/EVIDENCE/` | Verified Contents & Relevance | Creative Bypass for Blockers | Smallest Discriminator Test |
|---|---|---|---|
| `23710-8W83B-08-C11-MR18DE-AT.bin` (`8CMCDVN3`) & `23710-EL13A-08-C11-MR18DE-CVT.bin` | Same `SH705822N` CPU, SP `0xFFFF7FFC`, and reset vector `0x0000264C` (`8W83B`); **`5,463`** (`8W83B`) and **`4,607`** (`EL13A`) exact 64-byte code/data matches against `VERSA f501.bin` (`EL19A` MT). | Diff `EL19A` (MT) vs `8W83B` (AT) & `EL13A` (CVT) across aligned function blocks to isolate **MT-only code & Rev Hang / dashpot / clutch-switch / gear-ratio logic** in minutes. | Align `sub_5B5AC` (`WO65502`) & `0x369D0` (`WO65493` lag filter) between `EL19A` and `8W83B`; any divergent calibration/branch flags MT/AT behavior immediately. |
| `64811000p2_m.a2l` (5.51 MB) & `RFCC_2XHK19BDF1.a2l` (3.76 MB) *(also in `side project/`)* | Official RB4-ASAP2 Nissan SH7058 A2L definitions with exact RAM/ROM symbol names, scaling `COMPU_METHOD`s, `FUNCTION_LIST` groups (`KF7-320A`, `R301.23`, `Gst_on_can_1_0_1`), and English+Japanese descriptions (`vLADVTRM`, `vADVTRMAP`, `vFADV`, `mMBTM`, `vQH0`, `vTVO`, `vATVO`, `vADVHOS`). | Use as a **structural Rosetta Stone** for Nissan SH7058 scaling formulas, bit flags, and variable dependency graphs (`vADVTRMAP` → `vFADV`, `vQH0` → `vTVO`), while verifying every EL19A address independently. | Crosswalk `COMPU_METHOD` formulas for `vLADVTRM`/`vQH0`/`vTVO` against EL19A's `0x470CE` & `sub_36A26` arithmetic. |
| `Renault 3.5 V6 SH7058 4.09.ols.zip` (`15.12 MB` `.ols`) | Contains an embedded 1 MiB SH7058 ROM (`SP = 0xFFFF7FFC`, reset `0x000219A8`) plus **3,736 unique Nissan `m*` symbols** (`mMBTM`, `mCRSET`, `mMKLMRTH`, `mCALID`, etc.) paired with English descriptions. | Instant Nissan 4–8 char `m*` symbol dictionary for any table/axis encountered in A2Ls or `NissanDefinitions-master.zip`. | Extract the `(mSYMBOL, offset, dimensions, English description)` index from the `.ols` before guessing any new map name. |
| `NissanDefinitions-master.zip` → `Nissan Definitions/A2L.xml` (2,668 lines) & `ScalingData.xml` (810 lines) | Master RomRaider Nissan definition template mapping **human table name → `<!--mSYMBOL-->`, storage type, scaling formula, axes, and functional description**, plus 200+ sibling ROM XMLs (`Tiida`, `Sentra`, `CF48D`, `CD700`). | Bridges RomRaider community table names (e.g., `Ignition Timing`, `QH0 Low Flow Quantity Table`, `Target Throttle Valve Opening Table`) directly to official `m*` symbols in `64811000p2_m.a2l` and `.ols`. | Look up any newly discovered EL19A `sub_22CB8`/`sub_22DF8`/`sub_22E7C` table shape (`16x16`, `16x1`, `32x1`, `8x8`) and scaling unit to shortlist candidate `m*` algorithms. |
| `US6276333.pdf` ("Throttle Control for Engine", Nissan, 21 pp.) | Patent detailing Nissan's exact ETC math: `APS`/`Ne` → `tTE` → `tQH0TE` / `tQH0AP = f(Aaps/(Ne*VOL))` vs `tQH0LMT` → **`tQH0PTD` via first-order lag `K*tQH0AP + (1-K)*tQH0PTD[-1]`** → inverse `ADNVPTD` → `tATVO` → `tTVO` + **`Rev Hang.PNG`** / **`ZtyZpvE.jpg`**. | Matches `sub_36A26`'s `(cmd*k + state*(256-k)) >> 8` lag filter (`WO65493`, writing `FFFF1840`!) and explains how `QH0`, `TVO`, and dashpot/first-order throttle lag map to Rev Hang (`EL19A_ETC_Dashpot_Limiters_fragment-2.xml`). | Inspect `0x0CD56`/`0x0D456`/`0x0C756` consumers in `EL19A` LST to test whether they implement `ADNVPTD` (`QH0` → opening area) and `tQH0PTD` lag `K`. |
| `Nissan 370z - Tuning.pdf` (345 KB text), `UpRev-Nissan-Tuning-Guide-Rev2.pdf` (108 KB text), `common nissan tables and conventions`, `url.bin`, `gem117` | Full ProECU 370Z & UpRev tuning guides explaining torque management, throttle maps, and dashpot; `url.bin` (`685,214` B) is actually an **`814×611` RGBA PNG**; `gem117` (`667` KB) holds earlier deep disassembly checks (`0xAE8C8`, `0xB000`, `0x902E`, `0x91EE`). | Consult `gem117` before re-auditing `0x902E`/`0x91EE`/`0xAE8C8`; parse `Nissan 370z - Tuning.pdf` + `UpRev Rev2` for torque-management & Rev Hang calibration heuristics; rename/treat `url.bin` as PNG if inspected visually. | Grep `gem117` for any target EA (`0x9B2E`, `0xFFFF18xx`, `0x0CD56`) before launching a fresh disassembly WO. |
