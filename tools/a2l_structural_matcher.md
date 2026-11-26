# Structural Function & A2L RAM/Table Matcher (`tools/a2l_structural_matcher.py`)

Pure Python 3 (standard library only) structural matcher linking **EL19A** (`EVIDENCE/VERSA f501.bin`) caller subroutines to the two compiled **ROM + A2L** pairs in `EVIDENCE/`:

- **V6 (`SH705822N`):** `EVIDENCE/side project/64810223F121200000.hex` + `EVIDENCE/side project/64811000p2_m.a2l`
  - `36` auto-discovered lookup helpers, `306` unique tables (**298 / 306** exact A2L `CHARACTERISTIC`/`AXIS_PTS` hits), **`12,917`** addressed `MEASUREMENT` RAM symbols.
- **Juke MR16DDT (`SH705828N`):** `EVIDENCE/Nissan Juke 1.6-dig-T S19 (9APCTDEM06)/9APCTDEM06.s19` + `RFCC_2XHK19BDF1.a2l`
  - `37` auto-discovered lookup helpers, `585` unique tables (**575 / 585** exact A2L `CHARACTERISTIC`/`AXIS_PTS` hits), **`9,100`** addressed `MEASUREMENT` RAM symbols.

> **Evidence Policy:** Every match produced by this script is a **high-precision structural hypothesis / lead only** (not target-side semantic proof on EL19A). A2L names, units, and scalings must not be promoted into EL19A definitions without target-side reader/query/consumer verification.

## Usage

Run from repository root:

```bash
python3 tools/a2l_structural_matcher.py
```

## How It Works

1. Parses both `.hex`/`.s19` flat images and Shift-JIS A2L files (`CHARACTERISTIC`, `AXIS_PTS`, `MEASUREMENT`).
2. Runs `discover_helpers` + `extract_calls` (from `tools/sh7058_cross_rom_scanner.py`) on `EL19A`, `V6_HEX`, and `Juke_S19`.
3. Segments caller functions at `sts.l pr,@-r15` (`0x4F22`) prologues (`217` caller functions in EL19A, `223` in V6, `403` in Juke) and extracts per-function structural fingerprints:
   - ordered lookup-helper signature sequence `(kind, dim1, dim2, elem_type)`
   - non-trivial table/axis payloads (`>2` distinct bytes)
   - ROM scalar pool constants (`< 0x20000`), immediate constants, function length, and referenced `0xFFFFxxxx` RAM cells (mapped to A2L `MEASUREMENT` names in V6/Juke).
4. Scores EL19A functions against V6 and Juke functions matching the same helper-signature bag, highlighting:
   - **Dual V6 + Juke Consensus Functions** (`45` functions where *both* `SH705822N` V6 and `SH705828N` Juke independently land on the same A2L symbol root), and
   - **Single-Source / Rare Structural Leads** (`25` additional functions containing tables absent from Release 1 XML).

## Key Verified Structural Leads (Live Run Summary)

- **Overall coverage:** `103 / 217` EL19A caller functions receive high-specificity structural matches (`45` with dual V6+Juke consensus, `58` non-trivial caller-backed table payload matches).
- **Selected uncatalogued / high-value leads to target for EL19A verification:**
  - **`0x0FEE0` (`fn 0x369D0`, `64×1 uint16`):** Unique `2D_IMPL 64×1 uint16` match in V6 (`0x3F48C` → **`mQTBL`**, RAM `vAFLE`/`vAVTPD`) and in Juke (`0x13984` → **`mQTBL`**, RAM `vUSB`/`vQA4`; plus `mTTFKK`). *Note: previously missed by `WO65133` because `0x0FEE0` was truncated to `32×1`.*
  - **`0x0D856` (`fn 0x6B168`, `8×8 uint16`):** 1:1 dual consensus across V6 (`0x7EDB4`) + Juke (`0x886E8`) on `[mTTQH0ST, mMTTE, mTEHOSMAP]` → points `0x0D856` to **`mTEHOSMAP`** (with `0x1100A=mTTQH0ST`, `0x0CD56=mMTTE`).
  - **`0x0C2D6` (`fn 0x6FBFE`, `8×8 uint16`):** 1:1 dual consensus across V6 (`0x824A2`) + Juke (`0x8E710`) on `[mTMAXPTQ, mMTTE, mMPAMBFAC]` → points `0x0C2D6` to **`mMPAMBFAC`** (with `0x10954=mTMAXPTQ`, `0x0CD56=mMTTE`).
  - **`0x0F3EE` (`fn 0x40F1A`, `16×1 uint8`):** Dual consensus across V6 (`0x48D16`) + Juke (`0x4BB8E`) on `[mTISCPAMB, mTISCTA, mTTWISC]` → points `0x0F3EE` to **`mTTWISC`** (target idle speed vs coolant temp lead).
  - **`0x0DE6E` ↔ `0x0E2ED` (`fn 0x5B1F6`, `16×1 uint8` inverse pair):** Juke `fn 0x765B2` matches `[mPIADVAT, mADVPIAT]` with exact payload match on `0x0DE6E` (`mADVPIAT`), corroborated by V6 `mPIADVAT`.
  - **`0x0E5C0` / `0x0A3C2` / `0x0A092` (`fn 0x6F190`):** 1:1 V6 match (`0x81C6A`) on `[mTDAPOREF, mMKDSPWR, mMDSFACSL]` (dashpot / `wvAPOFSR` group).
  - **`0x0BB56` (`fn 0x703AA`) & `0x11744` (`fn 0x704D2`):** Both `16×16 uint16` maps paired with `8×1 uint16` curves matching Juke `0x8EF24` (`[mMDRTQS_S, mTEBRTH_S]`) and `0x8EE1A` (`[mMDRTQSP, mTENBRTH]`).
  - **`0x0B212` / `0x0B012` / `0x0B112` / `0x0ECEE` / `0x1037C` / `0x0E64C` (`fn 0x77616`):** 6-call 1:1 V6 match (`0x8D4DA`, `18` shared scalar constants) on `[mTMSATH, mTMSATA, mTMSATB, mTMFPC1, mTCREM, mTDLMFD]`.
  - **`0x0AFF2` (`fn 0x5B33A`, `4×4 uint8`) & `0x0E5E8` (`8×1 uint8`):** Dual consensus (`V6 0x6CA2A`, `Juke 0x76746`) on `[mTDATDDS, mTDATDPRE]`.
