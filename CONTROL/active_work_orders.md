# EL19A — Operational Control and Work-Order Register

**Operational authority:** this GitHub file is the single source of truth for current work-order lifecycle, assignments, priorities, continuation and handoff.
**Repository:** `ihatealladvertising/EL19A-` · **Branch:** `main` · **Effective:** 2026-11-15 (user-authorized cutover)
**Update rule:** edit this existing file in place; commit to GitHub; read back and verify. Do not maintain a parallel operational OneDrive control notebook.

## Operational frontier — updated 2026-11-20

- **Current workbook:** `WORKBOOK/EL19A_Master_Reverse_Engineering_Workbook_V57_WO65003_WO65045_ProcessReconciliation_2026-11-18.xlsx` (149 sheets).
- **Current XML baseline:** `public/assets/aistudio/EL19A_merged_definition_v3_08a300db.xml` (`EL19A_Merged_Spec_v3`: 76 tables — 7 verified, 69 `[S]`) + `EL19A_ignition_decoded_fragment_33ea8e67.xml` (6 ignition/knock tables).
- **Structured discovery staging:** `CALIBRATIONS/discovered_tables_catalog.csv` (**`179`** helper/reader-verified varying tables absent from XML v3: `13` `16×16`, `11` `8×8`, `14` `32×1`, `51` `16×1`, `83` `8×1`, `7` `4×1`).
- **Active WOs:** **WO65062 — ACTIVE** (bounded RAM byte/bit xref slice + local GBR/function-state map; see [WO65062](WO65062.md)).
- **WO65062 checkpoint 1 (2026-11-20):** partial positive access slices recorded for `FFFF85C4–FFFF85FF` and `FFFF860B–FFFF860F`. Traced `sub_20DCE` whole-byte transfers, `sub_24740` bit5 RMW writers for `860B/860D`, `sub_257AC` and other distinct `85E4` writers, plus local GBR contexts (`85C4`, `85EC`, `8594`, `2F00`). `860D/860B` bit3 remains a bounded no-independent-writer result per WO65059; whole-byte propagation is separate. Computed/indexed refs and broader direct-base coverage remain unresolved; no exhaustive claim. See [WO65062](WO65062.md).
- **WO65062 checkpoint 1a:** added seven direct UBYTE operations on base byte `FFFF85C4` (`0x2628A`, `0x262D6`, `0x267AE`, `0x268CA`, `0x26D00`, `0x26E3E`, `0x26E4A`). Several use the byte as a ROM-table index (`0x13C0F`, `0x13C00`, `0x13C05`); no semantic name assigned. See [WO65062](WO65062.md).
- **WO65062 checkpoint 1b:** refined the five currently identified U32 writers to `FFFF85E4`: `0x257C6` and `0x85A26` are explicit `0xFFFFFFFF` sentinel writes; `0x257E0` is the traced timer-difference/shift-right-5 producer; `0x271F2` stores computed R6 in a JSR delay slot; `0x29034` stores R10 with upstream origin still open. Read at `0x27B38` is compared with `0x249F`. Keep sources separate; meaning/units unresolved. See [WO65062](WO65062.md).
- **WO65062 correction 1c:** `0x36826/0x3682A` and `0x36856/0x3685A` resolve to `FFFF861F` (`base FFFF860C + 0x13`); `0x36980/0x36992` resolve to `FFFF861C` (`base + 0x10`). These are outside the target slice, not unresolved accesses to `FFFF860C`; the target-byte read/write remains `0x20FCE/0x20FE0`. See [WO65062](WO65062.md).
- **WO65062 checkpoint 1d:** added eight further direct UBYTE readers of base byte `FFFF85C4`: `0x42A4A`, `0x42E90`, `0x43152`, `0x43366`, `0x43530`, `0x43712`, `0x4373C`, `0x4387A`. Uses include zero/nonzero gates and selector-driven pointer/table arithmetic; downstream function semantics remain unassigned. See [WO65062](WO65062.md).
- **WO65062 checkpoint 1e:** traced `FFFF85C4` byte writers: `0x268CA` stores `ROM[0x13C23][GBR+0xF2]`; `0x26D00` stores `ROM[0x13C14][GBR+0xF2]` (with `0x13C19` as a separate branch/gate lookup). Readers `0x267AE` and `0x26E3E/0x26E4A` use the byte to gate/select lookups `0x13C37`, `0x13C00`, `0x13C05`, staging output at `FFFF1990+0x1FD`. Semantic name/units remain unassigned. See [WO65062](WO65062.md).
- **WO65062 checkpoint 2:** resolved further `FFFF85C4` base-pointer operations: third direct UBYTE writer at `0x27562` via `ROM[0x13C1E + UBYTE(GBR+0xAD)]`; additional readers at offsets `+7/+8/+0x0A/+0x0C/+0x0D/+0x10/+0x12/+0x14/+0x16`; two U32 reads of `FFFF85E4` (`0x27B38`, `0x27EDE`); two UBYTE writers at `FFFF85E8` (`0x35BD4`, `0x35BE8`); fixed reads of `85E8/85E9` at `0xB924E/0xB92B8`. `sub_35BCC` has unresolved computed read `FFFF85E8 + UBYTE(arg)` at `0x35C26`; caller bound is next focused lead. See [WO65062](WO65062.md).
- **WO65062 correction 2a:** `0x35C26` is resolved to fixed UBYTE read `FFFF85E8`: only direct incoming branch to `loc_35C18` is `0x35B54`, preceded by `mov #0,r4` at `0x35B52`; `extu.b` gives R5/R0=0. Supersedes the provisional dynamic `FFFF85E8 + UBYTE(arg)` uncertainty. See [WO65062](WO65062.md).
- **WO65062 checkpoint 2b:** traced `FFFF85E8` write/read mechanics: incoming R4 byte compared against ROM bounds `0x8F47/0x8F48` (or clamped to `0xFF`) and written at `0x35BD4/0x35BE8`; wrapper then sets R4=0 so `0x35C26` reads fixed `FFFF85E8`. UBYTE is compared unsigned with `0xC8` (200), gating status updates at `FFFF8626` and `FFFF1F09`. External R4 origin, units and semantic identity remain unresolved. See [WO65062](WO65062.md).
- **WO65062 checkpoint 3:** found three UBYTE writers to `FFFF85DF` in `prepare_85DF_and_19BF`: `0x59BF2` writes 0 when `FFFF3616 & 0x0C` is nonzero; `0x59C02` writes R13 when that mask is clear and `FFFF1E68.bit2` is clear; `0x59C04` writes R5 when bit2 is set. `callback_update_85E0` calls the producer then conditionally reads `FFFF85DF` at `0x59CA2` under the same bit2 condition and writes the value to `FFFF85E0`. R13/R5 originate in UWORD `FFFF1CAE/1CCC` and byte inputs `FFFF1CD6`/`FFFF1990+0x41`; units/meaning unassigned. Three readers previously listed remain known but are not an exhaustive access census. See [WO65062](WO65062.md).
- **WO65062 checkpoint 3a:** added direct `FFFF85C4` byte readers `0x431B2`, `0x4320C`, `0x4325E`, `0x433C4`, `0x434EC`, `0x43504`, `0x4367E`, `0x4377C`, `0x437C2`, `0x438D4`, `0x46FF8` (selector/index and curve-bank use); added `FFFF85CB` read `0x471C0`; `FFFF85CD` read `0x471DC` and `rts`-delay-slot write `0x47224`; `FFFF85D1` reads `0x37B32/0x43982`; `FFFF85D6` read `0x47028`. Also added `FFFF860D.bit3` consumer `0x470DE` (GBR=`FFFF85C4`, displacement `0x49`, tested at `0x470E0`); WO65059 bounded no-bit3-writer conclusion unchanged. See [WO65062](WO65062.md).
- **WO65062 checkpoint 3b:** added four direct UBYTE reads of `FFFF85C4`: `0x26902` (compared with 1, gates `FFFF2150+0x5E2` status path), `0x26D26` (zero/nonzero, nonzero value decremented and passed to `sub_220C0`, result staged at `FFFF8682`), `0x4D05E` (selector indexes ROM arrays `0x13C32/0x13C3B`, derived mask ORed into `FFFF1054+0x1F2`), `0x500FC` (zero/nonzero gate into `FFFF1E63` status path). No semantic label assigned. See [WO65062](WO65062.md).
- **WO65062 checkpoint 3c:** independently verified GBR-relative accesses: `0x344EE` writes `FFFF85C6` (GBR `FFFF8594`); `0x396A6` reads `FFFF85DA` (GBR `FFFF8534`); `0x39B40` reads `FFFF85CC` (GBR `FFFF8534`); `0x434CC` reads `FFFF85DA` (GBR `FFFF85C4`); `0x69806` reads `FFFF85D4` (GBR `FFFF8534`); `0x9E122/0x9E14C` read `FFFF85E2/E1` (GBR `FFFF85E1`) and gate bits6/5 at `FFFF1D99+0x23`. `0x34AB6/0x34B2E` operand comments imply nominal 85DA but local GBR is unproven; remain unresolved. See [WO65062](WO65062.md).
- **WO65061 checkpoint 2:** resolved the stale-GBR false alias at caller PC `0x55846`: caller GBR `FFFF8A34` gives actual effective address `FFFF8AE4`; retaining callee `sub_55F66` GBR `FFFF8A40` would falsely yield `FFFF8AF0`. PKIOR_W ISR `INT_ATU11_IMI1AC` pointer/save/restore/RTE boundary verified; exact historical false-hit PC remains unrecovered. See [WO65061](WO65061.md).
- **Latest completed WOs:**
  - **WO65061 CLOSED — BOUNDED COMPLETE (2026-11-20):** exact stale-GBR false alias resolved at `0x55846` (actual `FFFF8AE4`, not false `FFFF8AF0`); `FFFF85DF` has three verified readers (`0x46BDE`, `0x47014`, `0x59CA2`). PKIOR_W ISR boundary verified; historical original false-positive PC remains unrecovered. See [WO65061](WO65061.md).
  - `WO65056` (CLOSED, 2026-11-20): Resolved `WO65054` and `FFFF84BA`/`FFFF84B8`/`FFFF84BB` provenance end-to-end (`sub_253C0(0x1B/0x1F)` $\rightarrow$ `sub_22E28(0xF406)` NTC thermistor curve $\rightarrow$ `loc_353EC`/`loc_3567C` $\rightarrow$ `FFFF84BB..84C1` $\rightarrow$ `0x20ECC` 7-byte `sub_2245C` copy $\rightarrow$ `FFFF84B4..84BA`); confirmed `FFFF1DB4.bit5` gates `FFFF1054+0x39C` $\rightarrow$ `FFFF1018` in `sub_403D8` (`0x40532–0x4057C`); surfaced 4-bin selector `0xE21A` feeding `0xED9C`, `0xF2AE`, `0x107CC`. See [WO65056](WO65056.md).
  - `WO65057` (CLOSED, 2026-11-20): Completed global helper-family frontier sweep (`sub_22AB8`, `sub_22FD8`, `sub_22F28`, `sub_22EB4`, `sub_22DE0`, `sub_22E28`, `sub_22E44`, `sub_22E60`, `sub_23078`, `sub_22CB8`); verified 12+ uncatalogued varying tables (`A0F2`, `A8A2`, `E904/FA62`, `E914/FA82`, `E934/E082`, `E9AC/F51E`, `F406`, `DE5E`, `E4D4`, `F4BE`, `10D12`, `10D1A`, `10974`); classified `sub_22A8C`/`sub_23004`/`sub_2304C` as fixed-point math primitives (not table lookups). See [WO65057](WO65057.md).
  - `WO65058` (CLOSED, 2026-11-20): Traced caller query inputs, arithmetic transforms, destination RAM, and downstream consumers for 15 newly surfaced / unmerged tables from `WO65057` (`A0F2`, `A8A2`, `10974`, `E904/FA62`, `E914/FA82`, `E934/E082`, `E9AC/F51E`, `DE5E` [`SBYTE`], `E4D4`, `F4BE`, `10D12`/`10D1A`, `10E6A`, `10FEA`, `1501C`); flagged bogus static `0..240` Y-axis on `0x0E904` in XML v3 line 319 (true ROM axis is `0x0FA62`). See [WO65058](WO65058.md).
  - `WO65059` (CLOSED, 2026-11-20): Completed final closure traces for `WO65045`. Exhaustively proved no ROM instruction or block copy writes `FFFF860D.bit3` / `FFFF860B.bit3` (`WO65016` locked; no EL19A `mDSHCUT` threshold writer). Confirmed `FFFF1018` (`0x4057C`) has zero ROM readers/DMA transfers; proved `sub_403D8`'s active control path exits via `UWORD[FFFF1054+0x394]` $\rightarrow$ `UWORD[FFFF1054+0x3D6]` $\rightarrow$ `sub_4110C` $\rightarrow$ `sub_41016` $\rightarrow$ `UWORD[FFFF1014]` (`0x41102`). See [WO65059](WO65059.md).
  - `WO65060` (CLOSED, 2026-11-20): Swept all remaining lookup helpers (`sub_22DF8`, `sub_22F54`, `sub_22F80`, `sub_22FAC`, `sub_22E7C`, `sub_22E98`, `sub_22AFC`, `sub_22CF8`, `sub_22C00`, `sub_22C38`, `sub_22D30`, `sub_22E10`, `sub_22EFC`, `sub_230B0`, `sub_230E8`, `sub_23128`, `sub_23144`, `sub_23170`, `sub_2319C`) + inline `0xB422–0xB5A2`, expanding `discovered_tables_catalog.csv` by `+154` varying tables (`25 -> 179`); proved exact 18-for-18 Normal $\leftrightarrow$ Trustful (`0x11700–0x13000`) dual-bank mirror (`0xCD56==11FC4`, `C756==119C4`, `D456==121C4`, `F712==128FE`, etc.); surfaced `0x130DE+` OBD-II DTC table block; benchmarked full `EL19A` inventory against `CF48D_7797437d.xml`. See [WO65060](WO65060.md).
- **Closed / Parked status changes:** `WO65054` is **CLOSED** (superseded by `WO65056`); `WO65045` is now **CLOSED — BOUNDED COMPLETE** (`WO65056` + `WO65059`).
- **Do not repeat (exhausted negative proofs):** direct/wider/GBR/sibling-chain/ROM-pointer scans for `FFFF84BA`; `sub_22EFC` / `sub_22E10` / `sub_22AB8` / `sub_22DF8` / `sub_22F54` / `sub_22F80` / `sub_22FAC` / `sub_230B0–2319C` global helper censuses; `sub_22C00`/`C38`/`CB8` (`9B2E`/`9C2E`/`9DAE`); treating `sub_22A8C`/`23004`/`2304C` as lookup tables; whole-ROM searches for a `FFFF860D.bit3` writer (`WO65016`/`WO65059`); `FFFF1018` readers/DMAC/DTC consumers (`WO65059`).
- **Next recommended batch (after WO65062):** (1) **1D Scalar & Limiter Sweep (`0x7800–0x9B00`)** targeting the main `CF48D` gap (`K-Value`, `Injector Latency`, `MAF Factor`, `Rev/Speed Limiters`, `Target Idle RPM`, `STFT/LTFT/Dwell limits`) + `0x130DE+` DTC / `0x14000+` CID Supmask extraction; and/or (2) **Semantic Caller Trace** on high-priority `WO65060` `3D` maps (`0xB422..0xB5A2`, `0xB756/B7D6`, `0xB956`, `0xBB56`, `0xC0D6`, `0xC756/C956`, `0xD456/D656`, `0xD8D6`) and `MAF`/`QH0`/`TVO` `32×1` curves (`0xF712`/`10F8A`/`10EEA`/`10F2A`/`1104A`).

---

## Historical operational state & archived batches (2026-11-15 – 2026-11-17)

- **Completed:** WO65009 — `sub_6F4C0` updates `FFFF1D99+0x7A.bit3`: if `FFFF99F4+0x0D.bit7` is clear, set bit3; otherwise clear bit3 only when `FFFF860B.bit3` is clear. Called from `sub_6F89A` in callback `loc_6ECF0`. Input flag meanings/producers unresolved. See [WO65009](WO65009.md).
- **Completed:** WO65011 — callback pointer at table slot `0x21894` enters `loc_6ECF0`; callback calls `sub_6EAAC`, then `sub_6F89A` (including selector update), then tail-jumps to `loc_66DF6`. Dispatch predicate/cadence unresolved. See [WO65011](WO65011.md).
- **Completed batch:** WO65012–WO65014 — curve spot checks support E678/E688 and F3D6/F3DE. Scalar mapping superseded by the user's corrected evidence: EL19A `0x848A/0x848B` are leading `mDDSHPTD/N` UBYTE candidates; `mDSHCUT` target address remains unknown; `mDDPAPO` is a UWORD donor symbol with 52.34% raw fingerprint 0x0086 × 0.390625, target address unknown. WO65014's earlier dismissal of 0x848A/B as mDDPAPO candidates is retained as history but its overall scalar mapping is superseded. See [WO65012](WO65012.md), [WO65013](WO65013.md), [WO65014](WO65014.md).
- **Bounded complete:** WO65015 — 0x848A/B pair and selector branch verified; Drive/Neutral labels remain provisional and FFFF8603.bit6 source unresolved. See [WO65015](WO65015.md).
- **Bounded complete:** WO65016 — no EL19A mDSHCUT scalar identified; FFFF860D.bit3 producer and physical meaning unresolved. See [WO65016](WO65016.md).
- **Bounded complete:** WO65017 — donor mDDPAPO 0x0086/0.390625 fingerprint validated; no EL19A counterpart identified. See [WO65017](WO65017.md).
- **Bounded complete:** WO65036 — no direct producers found for FFFF849A or FFFF859C+0x16; paired lookup differential arithmetic and two FFFF1C79 consumers traced. Upstream alias/bulk/peripheral source remains unresolved. See [WO65036](WO65036.md).
- **Bounded complete:** WO65037 — ADF2/AF72 paired-output interpolation, status/sentinel logic, alternate FFFF1CA5 writer and downstream arithmetic traced; physical semantics unresolved. See [WO65037](WO65037.md).
- **Bounded complete:** WO65038 — all ten selected sub_22E10 UBYTE candidates audited for caller query, result staging and immediate local use; no semantic or unit assignments promoted. The remaining 30 moderate/high-variation candidates were not audited. See [WO65038](WO65038.md).


## Standing main priority — rapid table discovery and axis completion
- **Completed:** WO64975 — DAD8–DB57 contains four adjacent 16-point strictly increasing UWORD BE vectors with terminal FFFF; DB20 is the fifth word inside DB18, not a map base. Proposed DC10–DE0F 16×16 UWORD map is rejected as a varying-map candidate (480/512 bytes zero). Reader/axes unknown. See [WO64975](WO64975.md).
- **Completed:** WO64976 — D056–D155 contains eight adjacent 16-point nondecreasing UWORD BE vectors at 0x20 spacing; D116/D136 are duplicate payload placements. No reader or axes found; L1 morphology only. See [WO64976](WO64976.md).
- **Completed:** WO64977 — DE70–DE7F is a strictly increasing 16-point UBYTE vector (06,09,0C,0F,12,15,18,1B,1E,21,24,27,2A,2D,32,64); no reader/axis found; L1 only. See [WO64977](WO64977.md).
- **Completed:** WO64978 — new 9B19–9B28 4×4 UBYTE manual lookup; E062/E066 are explicit raw 4-point axes; index offset is 4×index(E062)+index(E066). Reader callsite 0x4DEE4–0x4DF24. Separate from 9B2E. See [WO64978](WO64978.md).
- **Completed:** WO64979 — new EBC0–EBC7 8-point UBYTE curve via sub_22EFC at 0xA960A; explicit raw UBYTE axis E11C–E123. See [WO64979](WO64979.md).
- **Completed:** WO64980 — new EA5C–EA63 8-point UBYTE zero curve via sub_22EFC at 0xAEE94; explicit raw UBYTE axis E12C–E133. Retain as constant/structural, not varying calibration. See [WO64980](WO64980.md).
- **Previously registered, not new:** EBD8–EBDF is an 8-point UBYTE curve using E092–E099 via sub_22EFC at 0x4DB0C; XML axis mapping already exists. Do not duplicate.
- **Completed:** WO64981 — new F21E–F225 8-point UBYTE curve via sub_22EFC at 0xA3AF8; explicit raw axis EBB8–EBBF. Values 40 40 40 4D 56 58 58 58. No semantic assignment. See [WO64981](WO64981.md).
- **Completed:** WO64982 — new F0C2–F0C9 8-point UBYTE zero curve via sub_22EFC at 0x40AE4; explicit raw axis E3B3–E3BA. Keep structural/constant only. See [WO64982](WO64982.md).
- **Completed:** WO64983 — new F326–F32D 8-point UBYTE zero curve via sub_22EFC at 0x40B88; explicit raw axis E2C1–E2C8. Keep structural/constant only. See [WO64983](WO64983.md).
- **Completed:** WO64984 — 10A84–10AA3 and 10AA4–10AC3 are separate 16-point UWORD BE curves selected by callers at 0x37296/0x372A2 and 0x767B4/0x767BC; both use sub_22E7C with query-derived internal indexing and no ROM axis pointer. No fake axis objects; preserve the pair. See [WO64984](WO64984.md).
- **Completed:** WO64985 — 108B4–108D3 is a 16-point UWORD BE curve (six 1900, ten 1E46) read by sub_22E7C at 0x5B5CE; helper derives position internally, so no explicit ROM axis is expected. See [WO64985](WO64985.md).
- **Completed:** WO64986 — 10AC4–10AE3 is a 16-point all-FD50 UWORD BE vector read by sub_22E7C at 0x68DEE; fixed-grid helper, no ROM axis; constant structural object only. See [WO64986](WO64986.md).
- **Completed:** WO64987 — existing UWORD 16-point pair 10206/10226 now caller-verified via sub_22F80; both use shared explicit axis 109B4 (16 UWORD BE, raw, strictly increasing). These are existing V56 Nov09 UWORD Expansion candidates, not new identities. See [WO64987](WO64987.md).
- **Completed:** WO64988 — 101E6–10205 remains a UWORD 16-point candidate with no direct xref, literal pointer or target reader/axis found. Separate preceding 101A6–101E5 32-point UWORD monotonic vector is L1 possible-axis lead only; do not assign it to 101E6. See [WO64988](WO64988.md).
- **Completed:** WO64989 — 102A6–102C5 remains an unassigned UWORD 16-point candidate with no direct xref, pointer or target reader/axis; adjacent 102C6 zeros / 102E6 FF and later 102FC/112CA pair do not provide an axis for it. See [WO64989](WO64989.md).
- **Completed:** WO64990 — two direct calls at 0x3A07E/0x3A090 confirm 102FC (16×1 UWORD BE) uses explicit axis 112CA (16×1 UWORD BE), both raw and strictly increasing. Existing V56 candidate; no new identity or semantic promotion. See [WO64990](WO64990.md).
- **Completed:** WO64991 — two direct sub_22F54 calls (0x5959E/0x595D6) confirm 10904 (8×1 UWORD BE) uses explicit axis F9F2 (8×1 UWORD BE). sub_2340C zero-extends and compares unsigned; no ×4/×16 axis transform. 10904 is constant (eight × 1A2C), structural-only. Correct prior F9F2 SWORD label to UWORD. See [WO64991](WO64991.md).
- **Completed:** WO64992 — D000–DFFF screen identified D260–D275 as an unreferenced 11-point strictly increasing UWORD BE vector (L1 only); excluded registered D-bank objects; surfaced DEC8–DECF and DED0–DED7 as two referenced, strictly increasing 8-point UBYTE vectors used by manual compare loops. See [WO64992](WO64992.md).
- **Completed:** WO64993 — DEC8 and DED0 are explicit 8-point UBYTE threshold vectors; each manual loop compares indices 1–7 and saturates at index 8. Their one-based indices select rows/columns in the constant 8×8 UBYTE matrix at 9ADE–9B1D (all cells 0x64). This is a manual binning/selector structure, not an interpolated calibration map. Corrects WO64992's tentative 9AE0 matrix start to 9ADE. See [WO64993](WO64993.md).
- **Completed:** WO64994 — two direct calls (0xA3E6C, 0xA4944) confirm 10BE8 (16×1 UWORD BE) uses explicit axis FB68–FB87 (16×1 UWORD BE). sub_22F80/sub_2340C interpret query and breakpoints as unsigned UWORD; axis values are raw, with no ×4/×16 conversion at the reader boundary. V6 mTROUTE fingerprint remains discovery-only; no semantic/unit transfer. See [WO64994](WO64994.md).
- **Completed:** WO64995 — bounded D4B6/D4D6 UWORD-vector reference check. The annotated LST contains no direct data-pointer evidence: exact `h'D4B6` / `h'D4D6` literal searches return zero; other matches are comment mentions or coincident instruction PCs. Retain both as separate L1 morphology-only leads; no axis assignment or semantics. See [WO64995](WO64995.md).
- **Completed:** WO64996 — target ROM identity reverified; 0x01006C contains a provisional 9-point ascending BE UWORD vector and 0x0107DA a provisional 13-point ascending BE UWORD vector. Annotated-listing literal/address searches found no reader or direct reference; both remain L1 morphology-only leads with inferred boundaries, no units/semantics. See [WO64996](WO64996.md).
- **Completed:** WO64997 — scanned the preserved 419,661-row `EL19A_Xref_Index.csv` (40,053,620 bytes; Library file ID `file_000000007200820eab5768cf16ee5637`) in chunks. Neither 0x01006C nor 0x0107DA appears as source or target EA or anywhere in the CSV. Combined with WO64996, both remain separate L1 morphology-only vectors; stop this address family. See [WO64997](WO64997.md).
- **Completed:** WO64998 — bounded E424 query audit. `sub_449C2` reads UBYTE `FFFF859C+0x0D` at 0x449FA, calls `sub_22E10` with E424 at 0x44A00, stages the result at FFFF105D and uses it in a local composite multiply path. No bounded direct writer/source for FFFF85A9 found; query range/conversion and physical meaning remain unresolved. Juke mTA5N/RPM/raw÷256 remains reference-only. See [WO64998](WO64998.md).
- **Completed:** WO64999 — bounded F2B2 reader/query and result-use audit. `sub_4DC32` reads UBYTE `FFFF85A8` (= `FFFF859C+0x0C`), calls `sub_22E10` with F2B2 at `0x4DD6C`, stages the result at `FFFF15C5`, then reloads and uses it in a local multiply. Producer, query conversion and external consumers remain unresolved; stopped before global RAM/XREF scan. See [WO64999](WO64999.md).
- **Completed:** WO65000 — bounded F062 query/result audit. `sub_AAAE0` reads UWORD `FFFFA338`, shifts right 8 for the F062/E0CE lookup, and stages the UBYTE result at `FFFF2998`. Direct consumers found at `0x75C52`, `0x9CF82`, `0x9EA5C`, `0x9ED00`, `0xA1200`, `0xA1918` and `0xA604E`, using numeric branching/multiply paths. A `sub_21FFC` copy at `0x20F70` conditionally maps `FFFFA34C+0x14` to `FFFFA324+0x14` if runtime length from `FFFF33CE` is ≥0x18; source producer for `FFFFA360` and actual copy length remain unresolved. Pressure semantics not proven. See [WO65000](WO65000.md).
- **Completed:** WO65001 — V56 candidates A652 and AC12 are distinct 4×4 UBYTE placements with byte-identical payloads; both use `sub_22B44` with shared raw UBYTE axes E2A1 (R5) and E0A2 (R6). Both callers query the first axis with UBYTE `FFFF859C+8`; second query is caller-stack supplied. Output staging is confirmed; physical X/Y labels, units and function remain unassigned. See [WO65001](WO65001.md).
- **Completed:** WO65002 — A3C2 is directly read as a 4×4 UBYTE map by `sub_22B44` at 0x6F37C; R5=DF35 and R6=DF29 are raw UBYTE axes. First query is `min(FFFF345E >> 2, 255)`; second query is stack-supplied. Result is staged locally. Axis values/payload hash, second-query source and semantics remain unresolved. See [WO65002](WO65002.md).
- **Completed:** WO65003 — documented and closed EXT-CLAUDE-01's outside audit: two confirmed `FFFF85DF` readers (`0x46BDE`, `0x47014`), downstream path to ATU-II channel 11 compare-register write `FFFFF5C2` (physical pin/actuator unproven), and a method-bounded negative for `FFFF85E0`. Corrects WO64847's incomplete reader search and WO64829's `sub_22E10` sentinel wording. No XML/workbook/source artifact changes. See [WO65003](WO65003.md).
- **Completed:** WO65004 — 10954 is a 16-point UWORD table read by sub_22F80 at 0x6FC18 with explicit raw unsigned UWORD axis F912 (16 points, strictly increasing). Query is UWORD FFFF1054+0x384; result is offset by -0x8000 and staged at FFFF2150+0x68A. Units/semantics remain unresolved. See [WO65004](WO65004.md).
- **Completed:** WO65005 — corrected the 32-point UWORD pair roles in sub_68A86: data 1100A uses axis 10EEA; data 1104A uses axis 10F2A. sub_22FAC/sub_2340C performs raw unsigned UWORD axis search and sub_231C8 interpolation. Query derives from U32 FFFF1054+0x52C; second branch uses query >>4; both results stage at FFFF1054+0x5C4. Leading high axis entries retained as observed; no semantics assigned. See [WO65005](WO65005.md).
- **Completed:** WO65006 — 10CC2 and 10CE2 are paired 16-point UWORD BE curves using shared axis 109B4 through sub_22F80; both use UWORD FFFF9860+0x18 and stage at FFFF2150+0x9FE/+0xA00. Semantics and query producer unresolved. See [WO65006](WO65006.md).
- **Completed:** WO65007 — confirmed a second consumer of FFFF9860+0x18 in sub_986F0; it subtracts FFFF9860+0xB4, calls sub_22494 and stages FFFF2150+0x2C2. Producer/units remain unresolved. See [WO65007](WO65007.md).
- **Completed:** WO65008 — FFFF1D99+0x7A bit 3 selects the 10206/10226 pair when SET and 10CC2/10CE2 when CLEAR; both pairs use axis 109B4 and query FFFF9860+0x18, then converge on FFFF2150+0x9FE/+0xA00 staging. Selector meaning unresolved. See [WO65008](WO65008.md).
- **Next:** WO65009 — bounded audit of the producer/writer for FFFF1D99+0x7A bit 3; stop at first unresolved state-transfer or interrupt boundary.
- **Completed (side research):** WO65010 — 0x8485 is UBYTE 0x0A copied into FFFF36C1 by sub_9FA50 and sub_A7D60; sub_9FA50 tests it as a zero/nonzero gate, not a coolant-temperature threshold. Keep separate from 0x848A/0x848B. See [WO65010](WO65010.md). Main next task WO65009 unchanged.
- **Completed:** WO64972 — new CD56–CF55 16×16 UWORD BE table candidate; sub_22D68 caller confirms R4=CD56, R5=E2C9 (16 UBYTE ×16), R6=FEC0 (16 UWORD raw), two UWORD query inputs. FEC0 also used as 1D values with CD56 as UWORD axis via sub_22F80. Structural confidence high; semantics unassigned. See [WO64972](WO64972.md).
- **Completed:** WO64973 — C6D6–C755 is an L1 morphology-only 8×8 UWORD BE candidate immediately preceding C756; no direct reader, pointer, or axes found. Do not promote. See [WO64973](WO64973.md).
- **Completed:** WO64974 — CC56–CD55 contains eight adjacent 16-point descending UWORD BE vectors at 0x20 spacing; no direct reader/axis reference found. Keep as L1 curve/vector group, separate from CD56. See [WO64974](WO64974.md).
- **Superseded:** D000–DFFF scan instruction completed in WO64992; next bounded check is DEC8/DED0 as specified above.
- **Completed:** WO64971 — B000–BFFF screen found one L1 morphology block, BD56–BE55: 16 adjacent 8-point UWORD BE nondecreasing vectors at 0x10 spacing. No registered identity, direct xref or literal pointer found; retain as provisional vector/possible-axis family only. See [WO64971](WO64971.md). Next: one C000–CFFF morphology screen.
- **Completed:** WO64969 — one 9B2E call at 0x473C0 confirms R4=9B2E, R5=GBR+0x10, R6=GBR and a separate stack query. Its dynamic-axis conclusion is superseded by WO64970: loc_472DC sets GBR=E4AC, so R5 resolves to fixed E4BC (Y, ×4) and R6 to E4AC (X, raw). See [WO64969](WO64969.md) and [WO64970](WO64970.md). No dynamic axes remain in this bounded caller context. Next: candidate morphology scan of one narrow ROM region.
- **Completed:** WO64970 — corrected 9B2E GBR root: E4AC loaded at 0x472F0 and restored at 0x4762E; 9B2E uses the same fixed E4AC/E4BC axes as 9C2E/9DAE. See [WO64970](WO64970.md).
- **Completed:** WO64966 — sole sub_22BC0 call at 0x37CEA confirms A272 (4×4 UBYTE), R5=E006/Y×4, R6=E002/X raw; XML axis mapping already agrees. See [WO64966](WO64966.md). Next: sub_22B7C only.
- **Completed:** WO64968 — static sub_22CB8 calls confirm 9C2E/9DAE (16×16 UBYTE) share R5=E4BC (Y, ×4) and R6=E4AC (X, raw); two distinct query inputs, duplicate payload but separate placements. See [WO64968](WO64968.md). Next: dynamic 9B2E only.
- **Completed:** WO64967 — both sub_22B7C calls resolve to AB72/AB62 4×4 UBYTE maps sharing raw axes F54E/F552; query 1 is R7 from FFFF859C+8 and query 2 is stack-supplied. See [WO64967](WO64967.md). Next: static sub_22CB8 pair only.
- **Completed:** WO64965 — single-address AFD2 check; direct R4 pointer at 0x6D7AC reaches sub_22B44 at 0x6D7DE with axes E3F3/E3EF. AFD2–AFE1 is zero-filled; branch alternatives AFE2/AFC2 share the same helper and axes. Existing XML mapping already correct. See [WO64965](WO64965.md).
- **Completed:** WO64964 — sub_22C38 micro-census; both caller families resolve to existing A342/A382 and AB22 placements. DFF2/DFFA and E24D/E022 are confirmed pointer pairs; Y×4, X raw. See [WO64964](WO64964.md). Next: sub_22B44 only.
- **Completed:** WO64963 — sub_22C00 micro-census; eight call sites resolve to eight already-registered bases (A092, AC62, ACE2, ACA2, AD22, ADF2, AF72, A452); no new varying map. See [WO64963](WO64963.md). Next: sub_22C38 only.
**Effective:** 2026-11-16, per user instruction. This workstream supersedes deeper semantic investigations until candidate coverage and axis gaps have diminishing returns.

- **Primary objective:** rapidly harvest plausible EL19A table/curve candidates and reconcile axes for existing candidate inventory and RR-040 XML.
- **Working method:** combine visual/data morphology, byte-pattern matching, preceding/succeeding breakpoint inspection, existing caller references and helper contracts. Treat morphology/proximity/donor fingerprints as discovery evidence, not confirmation.
- **Depth limit:** trace only enough to establish candidate address, extent, type, likely dimensions, axis pointer(s), helper/caller arguments, ordering and scaling. Do not continue into full semantic/actuator paths unless they materially discriminate table structure.
- **Cadence:** at most three WOs per batch. When a path stops yielding structural progress, close it with explicit unresolved items and move to the next coverage gap automatically.
- **Output:** keep new candidates separate from existing candidates needing axis correction; distinguish explicit axes, fixed-grid readers, dynamic/descriptor axes and structural-only objects.
- **Artifact guardrail:** update only these GitHub work-order documents and this operational register as authorized by the user. Do not modify XML, workbook, ROM, annotated listing, scripts, IDB or Library files. No outside workers.

- **Completed batch:** WO64911–WO64913 — B-family/UWORD pointers, UWORD curve/fixed-grid axes, and 4×4/8×8 axis-order reconciliation completed. Main structural corrections and remaining gaps are captured in the linked WOs. No candidate promoted semantically; no source artifact changed.

- **Completed batch:** WO64914–WO64916 — ROM-hash-verified fixed-grid curves at 154D0/154D8; newly catalogued duplicate 16×16 UWORD maps CD56/11FC4 with two matching caller-specific axis pairs; exact boundaries/values for four pre-existing UWORD vector morphology leads. No semantics promoted and no source artifact changed.

- **Completed batch:** WO64917–WO64919 — corrected C756/C956 reader linkage and reconciled their four identical payload placements/axis copies; mapped D456/D656 and duplicate 121C4/123C4 placements with exact axes; completed structural axis record for constant 11744. No semantic promotion; no source artifact changed.
- **Active work order:** None — continue with remaining candidate register axis gaps and rapid map-family harvesting.

- **Completed batch:** WO64920–WO64922 — reconciled 104EC/12B0E 8-point UWORD curves and axes; completed eight 16-point UWORD curve placement/axis relationships across Families A/B; harvested the adjacent 108B4–10B64 UWORD group, recording fixed 8/16-point grids separately from explicit FC10/FC30 axes. No semantic promotions; no source artifact changed.

- **Completed batch:** WO64923–WO64925 — revisited start-related UWORD candidates and exact adjacent vector morphology; added 10266 as a fixed-grid 16-point UWORD candidate and completed existing 10286→1072C axis association; reconciled reciprocal table/axis roles for 10F8A/F712 and 12D58/128FE plus 12B9E/12C7E and 12BDE/12CBE; classified F406 as a 32-point UBYTE fixed-grid curve (0,8,…,248), no ROM axis. No semantic promotions or source artifact changes.

- **Completed batch:** WO64926–WO64928 — completed the four physical placements of two reciprocal 32-point UWORD vector pairs; verified two 16-point UWORD curves (10EAA/10ECA) and their copies (12B3E/12B5E) with explicit shared axis copies 105DC/12B7E; completed B956/C0D6 16×16 UWORD map axis arrays and dual-query caller arguments. No semantic promotions; no source artifact changed.

- **Completed batch:** WO64938–WO64940 — reconciled reciprocal 16-point UBYTE vectors DE6E/E2ED and their reversed helper roles; verified EB78 as a varying 16-point UBYTE curve on explicit axis 1500C and EE9E/EEAE as all-zero structural objects; completed four sub_22CF8 8×8 UWORD reader structures and eight axis pointers, classifying B622/C2D6/C3D6/D856 as constant/sentinel-heavy rather than varying maps. No semantic promotions or source artifact changes.

- **Completed:** WO64956 — closed the residual sub_22EFC caller set. Eight unregistered 8-point UBYTE objects are all-zero, all-FF or constant; axes are explicit but several are degenerate. F4C2/F49E was already verified in WO64811; no new varying candidate admitted. This helper family is now exhausted for the current discovery pass.

- **Completed WOs:** WO64957 and WO64958 already existed in the repository and were preserved; WO64957 completed E520/E668 axis/reader work, WO64958 completed constant / degenerate sub_22EFC objects.
- **Completed batch:** WO64959–WO64961 — audited the remaining direct sub_22DF8 R4 pointers in NEXT6_16. Added three varying candidates E4CC/E590/E634, seven E7xx–EAxx varying/duplicate placements (E7D8/E7E0/E828/E898/E984/E9DC/E8B0), and EDE8; recorded constant/sentinel objects and duplicate physical placements separately. Excluded existing WO64914/WO64929/WO64932–64937 and RR-040 entries. No ROM axes fabricated; no semantics promoted.

- **Completed:** WO64962 — audited all 84 NEXT6_16 sub_22E10 calls and reconciled 71 unique table bases exactly to V56's 71-entry 1D UBYTE catalogue. E434 and EDC8/EDD8 include caller-register forms but were already registered. Confirmed generated query grid 0,16,…,240; no ROM axes. Recorded duplicate payload and constant/sentinel groups. No new candidate or source artifact change.
- **Active work order:** None — next batch should census explicit 4×4 / 8×8 / 16×16 map helper callers against existing register and XML, beginning with sub_22C00 / sub_22C38 and then sub_22BC0 / sub_22B44 family.
- **Active work order:** None — next priority is the sub_22E10 16-point UBYTE caller census against the 71-entry V56 catalogue, checking missing physical placements and repeated payloads, then any remaining explicit map gaps.
- **Active work order:** None — next batch should audit remaining sub_22DF8 fixed-grid UBYTE callers against the current candidate register, recording only unregistered varying objects and their duplicate placements; constants remain structural-only.
- **Active work order:** None — next step should move to the remaining UBYTE 16-point helper group and audit the unregistered 8×8 / 4×4 caller regions only for direct structural gaps.
- **Active work order:** None — next step should return to rapid small-map and curve candidate harvesting, then reconcile any new axis pointers; avoid further depth on the closed UWORD groups.

- **Completed batch:** WO64929–WO64931 — added fixed-grid 8-point UWORD candidates 10E6A/10FEA/1501C; added fixed-grid 16-point UWORD candidates 100BE/100DE/1109A/1033C; corrected duplicate physical placement 10D42 for 10266; classified DAD6 as a dynamic row bank with 16-UWORD row slices and an inner fixed-grid lookup. Constant/sentinel structures retained separately. No semantic promotions or source artifact changes.

- **Completed batch:** WO64932–WO64934 — reconciled EC08/EC10/EC18/EC20 and EC28/EC30 UBYTE curve copies with branch-selected F0CE/F0D6 axes; classified EC38 as a 16-point constant UBYTE object on E0A6; decoded E840/E848/E858/E850/E860/E878 fixed-grid curves/structural objects; resolved EBC8 as a fixed-grid curve and retained nearby EB80–EBF8 morphology leads. No semantic promotions; no source artifact changed.
- **Active work order:** None — continue to the next UBYTE data region and search for additional referenced/unregistered map and curve candidates; stop after structural value and axis evidence.
- **Active work order:** None — next pass should continue a rapid UBYTE morphology/adjacency scan, then check any resulting map candidates against existing reader/axis inventories.

- **Completed batch:** WO64941–WO64943 — added explicit-axis 8-point UWORD curves 10F6A/10F7A on shared axis 112EA; reconciled duplicate 14FDC/14FFC curves with duplicate axes 14FCC/14FEC; added 1007E/1008E/10984/1040C with explicit axes 112AA/112BA/FBC8/1046C. No semantic promotions; no source artifact changed.
- **Active work order:** None — next step should continue the sub_22F54 explicit-axis pointer inventory, distinguishing constant/sentinel objects and any repeated payloads, then switch to the next helper family.

- **Completed batch:** WO64944–WO64946 — reconciled duplicate 10A54/10A64 UWORD payloads and their distinct R5 pointer arguments (FB22 monotonic; 14EFC irregular); classified 1074C/1075C all-0x8000 objects with duplicate axis arrays 112FA/1130A; classified 10E8A/10C08/10D02 as all-zero UWORD structures with explicit axis pointer arrays FAA2/1131A/1132A. No semantic promotions; no source artifact changed.
- **Active work order:** None — continue the remaining sub_22F54 caller set, prioritizing varying payloads with explicit or derivable axes; stop and move on once objects are constant/structural.

- **Completed batch:** WO64947–WO64949 — added 10BC8/10BD8 and 10D6A/10BB8 8-point UWORD curve/axis pairs; added 1003E/FBA8 8-point UWORD curve/axis pair with a zero-extended byte query. 10BB8 retains a final FFFF sentinel. No semantic promotions or source artifact changes.
- **Active work order:** None — continue remaining direct UWORD helper candidates, then return to small-map and 1D candidate coverage as needed.

- **Completed batch:** WO64950–WO64952 — added varying 16-point UWORD curves 1031C/F962 and 1061C/F982; classified 10A34/10246 as byte-identical all-0x8000 objects using the existing 109B4 axis; classified 10D7A as all-0x1000 with explicit axis 1005E. No semantic promotions or source artifact changes.
- **Completed batch:** WO64953–WO64955 — added 105FC/FA42 as a varying 16-point UWORD curve; reconciled F692/F6B2/F7F2/F6D2 as constant/plateau UWORD structures and FEC0 as a dual-role vector used with a dynamic CD56-row or stack axis; added duplicate placements 10AF4/10B14 on FC10, completed 10954→F912 axis linkage, and confirmed 10CC2/10CE2 are duplicate placements of 10206/10226 on 109B4. No semantic promotions or source artifact changes.
- **Active work order:** None — continue the remaining sub_22F80 pointer set, then shift to any still-uncovered reader families.
- **Active work order:** None — next batch should take remaining 16-point UWORD pairs and unresolved axis/vector candidates, then shift back to small UBYTE map/curve morphology.
- **Active work order:** None — next batch should move to the remaining start-fuel UWORD candidates and any unmapped axis/descriptor candidates, stopping quickly where no target caller or axis pointer exists.
- **Active work order:** None — next pass should continue rapid candidate harvesting and axis gap completion using the available target ROM and current register.
- **Active work order:** None — next batch should prioritize additional candidate harvesting from available target data regions, then reconcile only newly exposed axis candidates.
## Current operational state

- **Completed batch:** WO64890–WO64892 are closed; see [WO64890](WO64890.md), [WO64891](WO64891.md), and [WO64892](WO64892.md). WO64890 compared the donor A2L's FFFF8A87 masks: fNEUT=bit 0x08, fNEUTD=bit 0x04, fPOSLP=bit 0x02; the target direct-reference inventory showed no bit-0x08 test and one bit-0x04 gated read. WO64891 bounded that bit-0x04 reader to a separate service chain and found sub_56AAA initializes FFFF8A86/87 to zero. WO64892 found no direct relationship from either flag to the sub_5611C/FFFF11F3 QDSPT selector chain. Drive/Neutral orientation remains provisional.
- **Completed:** WO64892 — compared FFFF8A87 bit-0x08/0x04 paths against the FFFF11F3 producer and sub_5611C reader; no direct selector link established. See [WO64892](WO64892.md).
- **Completed:** WO64891 — bounded the bit-0x04 read in sub_94B3E to a separate service chain; sub_56AAA initializes the FFFF8A86/87 word to zero. Upstream switch source remains unresolved. See [WO64891](WO64891.md).
- **Completed:** WO64890 — crosswalked donor fNEUT (bit 0x08) and fNEUTD (bit 0x04) at FFFF8A87; target direct references do not establish fNEUT/Neutral semantics. See [WO64890](WO64890.md).

- **Completed batch:** WO64887–WO64889 are closed; see [WO64887](WO64887.md), [WO64888](WO64888.md), and [WO64889](WO64889.md). WO64887 established `0x83EB/0x83EC) as the strongest cross-ROM `mDDSHPTD/N` address/function-family match; the same V6 A2L assigns `0x848A/0x848B` to unrelated symbols/functions. WO64888 traced the `sub_5611C` multiplier to the low byte of caller pointer `FFFF8AA4`, giving fixed `R12=0xA4). WO64889 traced `FFFF1054+0x19F` as a multi-state enum (0–4), with state >=2 routing directly to the `0x83EC` reader, but no D/N mapping established.
- **Completed:** WO64889 — `FFFF1054+0x19F` is a derived 0–4 state enum written by `sub_491BC`; `sub_5611C` uses >=2 as a direct route to `0x83EC), but enum codes are not proven Drive/Neutral. See [WO64889](WO64889.md).
- **Completed:** WO64888 — `sub_5611C` receives its multiplier through a stack argument formed as `GBR+0x70`; with GBR=`FFFF8A34`, `EXTU.B` yields fixed `R12=0xA4). Physical scaling meaning unresolved. See [WO64888](WO64888.md).
- **Completed:** WO64887 — V6 A2L maps `0x83EB/0x83EC` to `mDDSHPTD/N` in `R301.26.Dashpot_DandN_1_0_2`; it maps `0x848A/0x848B` to unrelated `mDMNRGG/mDMPNREF` in different functions. Keep `0x848A/0x848B` as separate EL19A QDSPT operands. See [WO64887](WO64887.md).

- **Completed batch:** WO64884–WO64886 are closed; see [WO64884](WO64884.md), [WO64885](WO64885.md), and [WO64886](WO64886.md). WO64884 expanded the `FFFF8603` direct code-store inventory to 13 observed instructions (11 base-pointer byte+1 RMW and two GBR-relative full-byte RMW); all preserve bit 6, so its origin remains unresolved. WO64885 established a second paired UBYTE rate candidate at `0x83EB/0x83EC` (target raw `0x14/0x00`) with branch-specific reads in `sub_5611C`, while preserving ambiguity from a separate composite use and the unresolved relationship to `0x848A/0x848B`. WO64886 traced the pair to internal UWORD counter/threshold and caller-buffer updates; no physical throttle/actuator endpoint was established.
- **Completed:** WO64886 — `sub_5611C` uses `0x83EB/0x83EC` as branch-selected UBYTE multipliers and updates internal `FFFF2150+0x8FC/+0x8FE`, `FFFF2150+0x292`, and `FFFF8A50` state. No physical endpoint. See [WO64886](WO64886.md).
- **Completed:** WO64885 — established the alternate `0x83EB/0x83EC` pair (raw `0x14/0x00`) with branch-specific runtime reads and donor A2L reference fingerprint; D/N labels, scale, and relationship to `0x848A/0x848B` remain provisional. See [WO64885](WO64885.md).
- **Completed:** WO64884 — superseded WO64883's five-site `FFFF8603` writer inventory with 13 observed direct store instructions, all preserving bit 6. Bit 6 origin remains unresolved. See [WO64884](WO64884.md).

- **Completed batch:** WO64881–WO64883 are closed; see [WO64881](WO64881.md), [WO64882](WO64882.md), and [WO64883](WO64883.md). Their original five-site `FFFF8603` writer inventory was superseded by WO64884's 13-site correction. The five original sites and their selector/gate observations remain valid; bit 6 is preserved by all 13 direct stores now identified. WO64879's three-site inventory remains superseded by WO64881.

- **Completed batch:** WO64878–WO64880 are closed; see [WO64878](WO64878.md), [WO64879](WO64879.md), [WO64880](WO64880.md). WO64878 corrects WO64876's copy direction: `sub_2245C` copies R2→R1, so `FFFF8602..8604 → FFFF85FF..FFFF8601` at `0x20FBA–0x20FBE`; thus `FFFF8603` is copied to `FFFF8600`. WO64879 found three explicit `FFFF8603` update sites (`0xB1044`, `0xB1B7A`, `0xB1B92`), updating bits 0x20, 0x08 and 0x01 while preserving bit 0x40. WO64880 traced the update routines to a 30-entry record dispatcher: selector 0x4AA0 → `sub_B0FD8`, 0x2EE0 → `sub_B1A24`; neither establishes D/N semantics. The source of `FFFF8603.bit6` remains unresolved.

- **Active work order:** None — batch WO64908–WO64910 completed; Prompt 7 coverage stage closed; await next user direction.
- **Completed batch:** WO64908–WO64910 are closed; see [WO64908](WO64908.md), [WO64909](WO64909.md), and [WO64910](WO64910.md). WO64908 reconciled AB62/AB72 as paired 4×4 UBYTE fuel-cut-timing candidates with F552/F54E axes, and F426 as a separate 16-point UBYTE fuel-cut-prohibition lead; no rev/speed limiter or fuel-restore counterpart confirmed. WO64909 retained E424/F2B2, ECCE–ED2D, and paired thermal/catalyst-temperature fingerprint candidates; E8C0/E94C remain all-0x80 structural objects; no coolant-MBT/EGR/idle-RPM/open-loop delay/K-value/JAR equivalent confirmed. WO64910 retained F10E as a provisional diagnostic/cylinder-discrimination threshold; no misfire map or VVT-abnormality map/delay confirmed. Manual-transmission configuration does not by itself exclude engine protection/diagnostic families. No calibration promoted; no source artifact changed.
- **Completed batch:** WO64905–WO64907 are closed; see [WO64905](WO64905.md), [WO64906](WO64906.md), and [WO64907](WO64907.md). WO64905 confirmed A552 as a 16×16 UBYTE lookup through sub_22C78 at two callers with E291 (×4) / E339 axes, but neither VVT nor fuel-compensation semantics were established. WO64906 found no confirmed MAF or ISC calibration; DB20/DC10 remain disputed, including the DB20 extent/storage/dimension mismatch and incompatible sub_22C00 contract. WO64907 retained the target QH0 16-point and 32-point UWORD vector candidates/readers, while torque units, semantic conversion and physical endpoint remain unresolved. No candidate promoted; no source artifacts changed.
- **Completed batch:** WO64902–WO64904 are closed; see [WO64902](WO64902.md), [WO64903](WO64903.md), and [WO64904](WO64904.md). WO64902 resolved C776–C936 as interior rows of the 16×16 UWORD candidate at C756; C756 and C956 are adjacent, byte-identical 512-byte placements, not injector-latency row families. WO64903 retained the paired UWORD start-fuel candidates 101E6/110EA and 102A6/12AAE plus the 102FC/112CA base-fuel candidate; no target AFR map/conversion or fuel-trim equivalent was found. WO64904 retained E700/E708 as provisional 8-point UBYTE dwell candidates; no main ignition or knock map equivalent was identified. No semantic or calibration promotion.
- **Completed:** WO64904 — E700/E708 remain provisional dwell-curve candidates; B756/B7D6/A452 and map families reconciled without main-spark/knock promotion; E400 remains rejected. See [WO64904](WO64904.md).
- **Completed:** WO64903 — paired start-fuel candidate placements 101E6/110EA and 102A6/12AAE are byte-identical UWORD curves; 102FC/112CA is a base-fuel-related UWORD candidate; no AFR/trim family found. See [WO64903](WO64903.md).
- **Completed:** WO64902 — C776–C936 descending rows are internal to C756's 16×16 UWORD extent; C756 and C956 are byte-identical separate placements. Injector identity not supported. See [WO64902](WO64902.md).
- No external workers dispatched. No workbook, XML, ROM, annotated LST, scripts, IDB or Library files changed.

- **Completed batch:** WO64899–WO64901 are closed; see [WO64899](WO64899.md), [WO64900](WO64900.md), and [WO64901](WO64901.md). WO64899 confirmed the 0x28-byte FFFF85C4→FFFF859C copy maps +0x08 from FFFF85CC; bounded direct-base review found reads but no direct store to FFFF85CC, so its producer remains unresolved. WO64900 traced FFFF234A as an index into ROM 0xDEDA feeding internal accumulators FFFF2D38/FFFF2D3C; same-byte FFFF3501 readers update other bits but do not explicitly test its generated 0x08/0x04 bits in the reviewed routines. WO64901 resolved ECCE/ECDE R9=0xFF and q=min(2×max(U8[FFFF859C+8]−8,0),255); sub_22E10 returns the final point for q>=0xF0 (input byte>=128). All scopes stop at internal state/source boundary; semantics and physical endpoints remain unproven. Raw-ROM checks for this batch covered 344 instructions / 688 bytes with zero mismatches. No workbook/XML/source changes.

- **Completed:** WO64901 — resolved ECCE/ECDE caller cap (R9=0xFF) and the final-point threshold (input >=128). See [WO64901](WO64901.md).
- **Completed:** WO64900 — traced FFFF234A to ROM-table-indexed internal accumulators; FFFF3501 downstream byte readers process other bits but do not test 0x08/0x04 in the bounded routines. See [WO64900](WO64900.md).
- **Completed:** WO64899 — mapped FFFF859C+8 to FFFF85CC; bounded direct-base review found no direct writer, so source provenance remains unresolved. See [WO64899](WO64899.md).

- **Completed batch:** WO64896–WO64898 are closed; see [WO64896](WO64896.md), [WO64897](WO64897.md), and [WO64898](WO64898.md). WO64896 verified six adjacent 16-point UBYTE curves at ECCE/ECDE/ECEE/ECFE/ED0E/ED1E; corrected aggregate extent to ECCE–ED2D (the historical ECCE–ED1D covers only five curves), with a two-byte overlap at dword_ED2C preserved as a label/alias boundary. WO64897 traced ECEE–ED1E as four fixed-grid lookups using q=min(2×max(U8[FFFF859C+8]−8,0),255), producing five-state internal selector FFFF2150+0x1FA. WO64898 traced ECCE/ECDE using the same query shape with caller-local R9 cap and threshold status bits 0x08/0x04 at FFFF3501. All three stop at internal state; idle/coolant meanings and physical endpoints remain unproven. Raw-ROM verification covered 422 instructions / 844 bytes with zero mismatches. No workbook/XML/source edits.

- **Completed:** WO64898 — ECCE/ECDE lookup pair and two-bit internal status update at FFFF3501 verified; R9 cap/query producers and semantic identity unresolved. See [WO64898](WO64898.md).
- **Completed:** WO64897 — ECEE/ECFE/ED0E/ED1E query and five-state FFFF234A result traced; physical meaning/consumer unresolved. See [WO64897](WO64897.md).
- **Completed:** WO64896 — six 16-byte curve extents verified; corrected aggregate range ECCE–ED2D; ED2C label overlap preserved. See [WO64896](WO64896.md).

- **Completed batch:** WO64893–WO64895 are closed; see [WO64893](WO64893.md), [WO64894](WO64894.md), and [WO64895](WO64895.md). WO64893 raw-ROM verification disproved the claimed MOV.W at 0x47686 (actual bytes 8B 4A = BF loc_4771E). WO64894 mapped the 0x28-byte FFFF85C4→FFFF859C copy and traced +0x0D to FFFF85CE-derived FFFF85D1; producers for +0x08, +0x16 and FFFF849A remain unresolved. WO64895 raw-ROM-verified distinct 0x80 behavior: RP-004 propagates bit 7 from the first sampled cell while interpolating low 7 bits; RP-006 returns 0x80 if any participating cell is >=0x80. All scopes are technical-scope complete at these boundaries; no workbook/XML/source edits.

- **Completed:** WO64895 — separate RP-004/RP-006 sampled-cell 0x80 contracts verified against original ROM; caller semantics remain unassigned. See [WO64895](WO64895.md).
- **Completed:** WO64894 — FFFF859C+0x0D source traced through the 0x28-byte block copy to FFFF85D1; +0x08, +0x16 and FFFF849A producers remain unresolved. See [WO64894](WO64894.md).
- **Completed:** WO64893 — raw ROM confirms 0x47686 is BF loc_4771E (bytes 8B 4A), not MOV.W to FFFF C006. See [WO64893](WO64893.md).
- **Completed:** WO64877 — no defensible D/N correlation found; retain generic E678-branch scalar 0x848A and E688-branch scalar 0x848B. Next lead is the broader FFFF85FF structure producer. See [WO64877](WO64877.md).
- **Completed:** WO64876 — bounded direct writer audit; its original copy-direction statement is superseded by correction WO64878 (actual copy is FFFF8602→FFFF85FF). See [WO64876](WO64876.md) and [WO64878](WO64878.md).
- **Completed:** WO64875 — no direct FFFF85F8.bit4 writer found; nearby timer/status routine modifies FFFF85F9, not the branch bit. See [WO64875](WO64875.md).
- **Completed:** WO64874 — traced selected 0x848A/0x848B scalar through FFFF2446 and the bounded UWORD FFFF1018 internal-state calculation. No physical throttle actuator/command endpoint established. See [WO64874](WO64874.md).
- **Completed:** WO64873 — confirmed E688/0x848B branch requires FFFF85F8.bit4 AND FFFF8600.bit6; flag semantics do not establish Drive/Neutral identity. See [WO64873](WO64873.md).
- **Completed:** WO64872 — confirmed 0x848A and 0x848B are paired UBYTE operands multiplying E678/E688 lookup results with UBYTE R11+0x622; selected scalar also writes FFFF2446. Names/units remain provisional. See [WO64872](WO64872.md).
- **Completed:** WO64871 — traced A0E2-derived composite through `FFFF1206 → FFFF120A → FFFF1D3B`, then to internal outputs `FFFF10CE` and `FFFF26A8`. No physical throttle actuator or confirmed MBT semantic endpoint; the 52.34% match remains numerical only. See [WO64871](WO64871.md).
- **Completed:** WO64870 — reconstructed the A0E2 local arithmetic: raw UBYTE result `FFFF1207) feeds a saturated composite UBYTE `FFFF1206`, then a multi-input UWORD `FFFF120A). No direct `raw×100/128` conversion found. See [WO64870](WO64870.md).
- **Completed:** WO64869 — confirmed A0E2's 4×4 UBYTE reader, axes E006/E002, independent queries FFFF85A4/FFFF849A and raw output FFFF1207. The 0x43 cell is not proven to be selected at runtime; query producers remain unresolved. See [WO64869](WO64869.md).
- **Completed:** WO64868 — tested D456/D656 as 16×16 UWORD map candidates using `sub_22D30`; results and a third 1D lookup blend into UWORD FFFF1538 and internal qualification state. mTAPTR semantics and physical throttle endpoint remain unproven. See [WO64868](WO64868.md).
- **Completed:** WO64867 — verified QH0 vector/axis reader paths at 1100A/10EEA, 1104A/10F2A, 12CBE/12BDE and 12C7E/12B9E; traced 12D58/128FE into FFFF1054/FFFF2150 schedule state. Physical throttle target remains unproven. See [WO64867](WO64867.md).
- **Completed:** WO64866 — verified AFF2 as a 4×4 UBYTE lookup via sub_22B44 with axes E5CC/E5C8, staged at FFFF1054+0x490 and used in internal state calculations. mTDATDDS/torque-reduction endpoint not confirmed. See [WO64866](WO64866.md).
- **Completed:** WO64865 — tested EL19A 0x90EA against the proposed mDDPAPO identity. It is a UWORD member of a 16-UWORD block; five indexed operands feed a composite FFFF2150+0xAD4 state calculation. No isolated mDDPAPO scalar, transferable donor scale or physical throttle endpoint established. See [WO64865](WO64865.md).
- **Completed:** WO64864 — confirmed FFFF860D/E are copied both to FFFF860B/C and, separately, FFFF8611/12. The additional mirror does not identify the upstream writer or a coolant comparator; mDSHCUT remains unresolved. See [WO64864](WO64864.md).
- **Completed:** WO64863 — confirmed 0x848A and 0x848B are UBYTE operands read in the E678/E688 QDSPT branches and stored to FFFF2446; downstream contributes to internal UWORD FFFF1018. Paired mDDSHPTD/N interpretation remains provisional; units and physical throttle endpoint unproven. See [WO64863](WO64863.md).
- **Completed:** WO64862 — separate sub_5C220 UWORD writer to FFFF12EA uses ROM 0x78C2 and dynamic FFFF8494 via division helper; value feeds FFFF154A→FFFF154C→FFFF154E and FFFF1254 internal RAM branches. No direct FFFF12EA read, physical actuator endpoint or 52.34% scalar match. See [WO64862](WO64862.md).
- **Completed:** WO64861 — bounded ATU-II/GPIO output audit found Timer-5 compare scheduling and Timer-7 setup, but no TIOR5 runtime output configuration, no Timer-7 output routing, Timer-11 pin mux remains disabled, and no direct PDR output write or FFFF2446/FFFF1018 hardware dataflow. ETC endpoint not established. See [WO64861](WO64861.md).
- **Completed:** WO64860 — corrected the output base: sub_403D8 writes UBYTE FFFF2446 (not FFFF12EA), reads it internally, compares/subtracts against UWORD FFFF1042 and stores bounded UWORD/sentinel to FFFF1018. No physical actuator endpoint; no 52.34% linkage. See [WO64860](WO64860.md).
- **Completed:** WO64859 — FFFF860B/E refresh copies FFFF860D/E into FFFF860B/C; FFFF860B.bit3 therefore inherits FFFF860D.bit3. Upstream writer/coolant comparator remains unresolved; no donor mDSHCUT address/scale transfer. See [WO64859](WO64859.md).
- **Completed batch:** callback/FFFF85DF consumer WOs WO64856–WO64858 are closed.
- **Completed:** WO64858 — 0x60-byte copy in sub_2088C mirrors FFFF8534+0x19 to FFFF84ED; no further consumer/alias established. No physical throttle endpoint or 52.34% conversion. See [WO64858](WO64858.md).
- **Completed:** WO64857 — FFFF8534+0x19 has writers at 0x38056/0x28C2E and is mirrored to FFFF84ED by a 0x60-byte copy; no direct/GBR consumer established. Callback cadence is every two sub_2088C interrupts; wall-clock period unknown. See [WO64857](WO64857.md).
- **Completed:** WO64856 — found direct FFFF85DF reader at 0x37F82; it contributes to computed UBYTE FFFF8534+0x19. Callback 0x59CAE is entry 3 in a nine-function dispatch table. See [WO64856](WO64856.md).
- **Completed batch:** WO64850, WO64854 and WO64855 are complete; their scalar/AB22 traces are not to be repeated.
- **Completed:** WO64855 — FFFF1C78+0x24 consumer chain continues through FFFF1054+0x2AD to FFFF1054+0x468; all demonstrated endpoints are internal RAM state, no throttle actuator path proven. See [WO64855](WO64855.md).
- **Completed:** WO64854 — corrected the suspected 9F8/9FA linkage (separate sub_6E558 state, not AB22); AB22 byte output feeds a bounded UWORD at FFFF1C78+0x24, but throttle role remains unproven. See [WO64854](WO64854.md).
- **Completed:** WO64850 — resumed scalar audit found 0x90EA is one of a 16-UWORD block feeding composite internal state FFFF2150+0xAD4; no 52.34% conversion or throttle endpoint. See [WO64850](WO64850.md).
- **Completed:** WO64853 — bounded DMAC/DTC audit found no programmed SAR/DAR transfer or descriptor for FFFF14E0/FFFF1018; indirect provenance remains unresolved. See [WO64853](WO64853.md).
- **Completed:** WO64852 — FFFF1018 UWORD producer confirmed at 0x4057C; no direct reader or explicit pointer alias found in the annotated listing. Bulk-copy/DMA/DTC consumer not established; physical throttle endpoint unproven. See [WO64852](WO64852.md).
- **Completed:** WO64851 — ATU02/ATU12 interrupt paths call sub_2088C → sub_257AC; timer-delta arithmetic and Timer-1A register involvement confirmed, but FFFF14E0 producer, physical event, clock/cadence and RPM conversion remain unresolved. See [WO64851](WO64851.md).
- **Historical pause superseded:** WO64850's independent 52.34% scalar audit was resumed and technically closed on 2026-11-16; see [WO64850](WO64850.md). The screenshot scalar remains unidentified.
- **Completed batch:** E678/E688 follow-up WOs WO64851–WO64853 are complete; do not repeat those traces.
- **Completed:** WO64849 — A0E2 runtime role and correction convergence. Periodic path calls A0E2 reader then sub_44054; FFFF120A × UBYTE FFFF1466 contributes to bounded FFFF1D3B. sub_44E78/sub_59F46 derive FFFF14BC/14BD, sub_45114 selects FFFF1D4C, and difference-driven E2ED/DE6E lookup paths write FFFF10CE and FFFF2150+0x558 / FFFF1D18+6. Physical spark/coil endpoint and MBT semantics remain unproven; 52.34% scalar remains unrelated/unidentified. See [WO64849](WO64849.md).
- **Completed:** WO64848 — 9C2E/9DAE paired-map audit. Corrected FFFF1D7F.bit7 to a path gate, not a demonstrated map selector. Both 16×16 lookups execute sequentially with identical inputs/axes; V55 records byte-identical payloads, so their masked outputs cancel and the FFFF1C79 path reduces to signed high-byte conversion of UWORD FFFF10F8. Query producers and downstream FFFF1C79 consumer remain unresolved. Historical WO64275/64276/64435 were reconciled as stale notes, not reactivated. See [WO64848](WO64848.md).
- **Completed:** WO64847 — E974 callback final byte generation. Reconstructed FFFF85DF = mode-selected baseline/adjusted max(A,B) with FFFF19D1 signed offset and 0x1B override; FFFF85E0 copies FFFF85DF in bit2 mode, otherwise uses min(UWORD[FFFF1CA8+0x24]>>8,127). Scheduler cadence and physical endpoint remain unresolved; no XML/workbook edits. See [WO64847](WO64847.md).
- **Completed:** WO64846 — screenshot Throttle Reduction Rate scalar. A0E2 is a 4×4 UBYTE map read via sub_22B44 at 0x43F02, axes E002/E006; its 0x43 cell is a numeric coincidence with 52.34% under unsupported ×0.78125. Result stored at FFFF1207; no throttle-reduction semantics or physical endpoint established. The screenshot scalar remains unidentified. See [WO64846](WO64846.md).
- **Completed:** WO64845 — FFFF860D upstream status-byte producer. The 0x20Fxx routine copies FFFF860D/E into FFFF860B/C; sub_2245C call at 0x20FE2 copies FFFF861A to FFFF8613, not into FFFF860D. 44 exact references were reviewed; no direct FFFF860D writer established. Source remains unresolved at RAM boundary; no coolant comparator/threshold found. See [WO64845](WO64845.md).
- **Completed:** WO64844 — mDSHCUT / FFFF860B.bit3. Exact-reference scan found many readers but no direct bit-3 writer. The only direct pointer-store path at 0x20FD4–0x20FE0 copies FFFF860D/E into FFFF860B/C; 44 exact references to FFFF860D were found, with no direct writer established in the bounded pass. Retain generic FFFF860B.bit3 only; coolant comparator, target scalar, X−50°C conversion and fDSHCUT semantics remain unproven. See [WO64844](WO64844.md).
- **Completed:** WO64843 — E934/mTHPAMB: strong partial 16-point structure and reciprocal raw/128 composite arithmetic, but query resolves to high byte of CAN-mailbox-related constant 0xDA80, not a demonstrated pressure-mV input. Retain generic E934 only; eliminate mTHPAMB pressure semantics. Outputs terminate in internal state; no physical endpoint. Donor raw payload equality untested.
- **Completed:** WO64842 — E904/E914 vs V6 mTHOSNTP/mTHOSRCV: strong partial geometry/storage fit (16-point UBYTE curves and 16-point UWORD axes); donor V6 raw payload unavailable. Target query = `(U8[FFFF85A9] × U16[FFFF8494]) >> 4`; FFFF85A9 is timer-rate-derived and FFFF8494 is seeded from an A552-derived UWORD result. Target `>>7` applies raw/128 equivalent inside composite product. Distinct indexed paths update bounded internal event/state; rpm·ms units and HOS semantic/physical endpoint unresolved. Retain generic E904/E914 only; no XML promotion.
- **Completed:** WO64841 — A342/A382 paired maps: exact 8×8 UBYTE geometry and exact donor raw X/Y axes; target map payloads differ. DFF2 uses timer-rate query FFFF85DA (RPM relation unproven); DFFA uses FFFF857A from bounded UWORD lookup/shift path. FFFF85FB.bit7 selects A382 vs A342 but writer/mode meaning remain unresolved. Target map result enters composite product and bounded internal UWORD state; no physical endpoint. Retain generic pair only; no donor percentage conversion or semantic XML promotion.
- **Completed:** WO64835 — F062/E0CE exact 16/16 structural match to Juke mTRPAMB/mLPAMB; query source is MB12 control/identifier, not payload; MB12 inactive in target initialization and query resolves to zero. Active pressure-table semantics rejected; keep generic exact fingerprint only. See corrections in WO64835/WO64836.
- **Completed:** WO64834 — E678/E688 retained as generic QDSPT/dashpot candidates; strong partial structural fit, partial family-behaviour fit; no donor axis/conversion or D/N semantic promotion.
- **Completed:** WO64833 — EFA4→mTFVAPO correspondence rejected by 0/16 byte equality across all three Juke donor ROMs; EFA4 remains generic.
- **Completed:** WO64832 — bounded structural/behaviour test complete; retain F3D6/F3DE as generic schedule candidates only. No donor conversion or TVO semantic promotion.
- **Completed:** WO64830 remains TECHNICAL SCOPE COMPLETE at the bounded internal-state endpoint; do not repeat its completed trace.
- **Completed technical work:** WO64827, WO64828 and WO64829 — technical scopes complete. Detailed evidence remains in `CONTROL/WO64828.md`, `CONTROL/WO64829.md`; WO64827 closeout is preserved below.
- **Partial / paused:** WO64825 remains PARTIAL. Preserve its unresolved scope; do not resume without explicit authorization and a concrete lead.
- **Timer-11 supplement to WO64794 (2026-11-15):** target code at `sub_2598E` writes `PLIOR=0x37EF`, `PLCRH=0`, `PLCRL=0`, `PLIR=0`, `PLDR=0x0400`. PL1/PL2 direction bits are outputs, but the Port-L function-select bits are cleared; no PLCRL reconfiguration was found in the bounded LST text search. Thus the configured Timer-11 compare events are **not shown routed to TIO11A/B pins**; the ignition-coil hypothesis is weakened. WO64794 overall remains PARTIAL; Timer-11 interrupt purpose and other output hardware remain open.
- **Deferred candidate (not issued):** 9C2E/9DAE differential provenance/consumer path. Before issue, reconcile legacy V54 `P2 Work Orders` entries WO64275/WO64276 and WO64435 against this register; do not silently reactivate or duplicate them.
- **Workbook:** current GitHub master is V55: `WORKBOOK/EL19A_Master_Reverse_Engineering_Workbook_V55_WO64830_BFamilyClosure_2026-11-15.xlsx` (Git blob SHA `83a065db94c0945d352aac86f2d55353c547cebd`; upload commit `b9793eee8d09f25c8315175a1ce4af1bc01900f6`, 2026-11-16T02:19:47Z). V54 is the predecessor. The V55 binary's presence/commit is verified; its local MD5/SHA-256 identity is recorded in the integration summary but was not recomputed from GitHub raw bytes in this check.
- **Former OneDrive Control Notebook:** superseded; leave unchanged as a historical archive.

## Operating rules

1. This file alone controls current work-order status, allocation, priority, dependencies, pause/resume conditions and next action.
2. A new WO, resume, cancellation or priority change requires user authorization or an explicit existing standing instruction.
3. Do not infer an active WO from old snapshots, completed investigations or unissued leads.
4. Record each material status change here, with date, rationale, evidence link and commit. Keep detailed technical evidence in its WO record and the Master Workbook.
5. At each handoff, state the exact next action, source reference, dependencies, unresolved boundaries and completed work not to repeat.
6. Preserve historical snapshots and original artifacts. Do not delete or overwrite the former OneDrive Notebook.

## Latest checkpoint — 2026-11-16
User-authorized batch WO64881–WO64883 is complete. The direct writer inventory for FFFF8603 is corrected from three to five sites: 0xB1044 (sub_B0FD8), 0xB1B7A/0xB1B92 (sub_B1A24), 0xB399C (sub_B3924) and 0xB3A66 (sub_B3A0E). Each modifies bits 5, 3 or 0 and preserves bit 6. The additional routines are reached through second-stage record selectors 0x4AA0 and 0x2E80, respectively, and have local state/validity gates; no D/N semantics are established. No identified direct writer sets or clears FFFF8603.bit6. Its origin remains unresolved; investigate indirect aliases, bulk transfer, peripheral/external updates or earlier initialization if resumed. No workbook/XML/ROM/LST edits. Do not repeat WO64878–WO64883. Corrected the copy direction at 0x20FBA–0x20FBE: sub_2245C copies R2→R1, so FFFF8602..8604 are copied to FFFF85FF..FFFF8601; FFFF8603 therefore supplies FFFF8600.bit6. Three explicit FFFF8603 update sites were found; they modify bits 0x20, 0x08 and 0x01 but preserve bit 0x40. The two routines map to selectors 0x4AA0 and 0x2EE0 in a 30-entry record dispatcher. Neither selector nor the traced status logic establishes Drive/Neutral semantics. The source of FFFF8603.bit6 remains unresolved. No workbook/XML/ROM/LST edits. Next lead: identify the non-local/initial source of FFFF8603.bit6, including any indirect or bulk-copy writer. Do not repeat WO64878–WO64880.

## Previous checkpoint — 2026-11-16
User-authorized expanded batch WO64869–WO64871 is complete; no active work remains. WO64869 confirmed A0E2 as a 4×4 UBYTE lookup via sub_22B44 with axes E006/E002, independent queries FFFF85A4/FFFF849A and raw output FFFF1207; the 0x43 cell is not proven to be selected at runtime and both query producers remain unresolved. WO64870 reconstructed the A0E2 local arithmetic: FFFF1207 contributes to saturated composite UBYTE FFFF1206, which feeds multi-input UWORD FFFF120A; no direct raw×100/128 conversion was found. WO64871 traced FFFF120A through sub_44054 to UBYTE FFFF1D3B and then through sub_5B1F4/sub_5AB20 to internal RAM outputs FFFF10CE and FFFF26A8. No physical throttle endpoint or confirmed MBT/ignition semantic was established. The 52.34% screenshot association remains provisional/numerical only; A0E2 is not a confirmed scalar definition. WO64866–WO64868 remain closed and were not repeated. V55 remains current; no XML, workbook, ROM or LST edits. Stop pending new user authorization.

## Prior checkpoint — 2026-11-16
WO64861 closed as a bounded negative ETC hardware-output discriminator: Timer-5 compare registers schedule interrupts, TIOR5 output mode was not configured in the inspected code, Timer-7 output routing was not established, Timer-11 pin mux remains disabled, and no direct PDR output write/dataflow from FFFF2446/FFFF1018 was found. WO64862 is active to resolve the separate sub_5C220 UWORD writer at FFFF12EA. V55 remains current; no XML/workbook edits.

## Prior checkpoint — 2026-11-16
WO64860 closed after correcting the objective's address error: R14 is FFFF2150, so the selected QDSPT byte is FFFF2446, not FFFF12EA; it is read within sub_403D8 and contributes to UWORD FFFF1018. No actuator endpoint or 52.34% linkage. WO64861 is active for independent ETC hardware-output discovery. V55 remains current; no XML/workbook edits.

## Prior checkpoint — 2026-11-16
WO64843 closed at a bounded internal-state endpoint. E934/E082 is a strong partial 16-point UBYTE structural match; the query is high byte 0xDA of a CAN-mailbox-related constant 0xDA80 copied into FFFFA338. Target interpolation at that query returns 0x82. The target uses the raw/128 coefficient reciprocally in signed division and as a query to a second lookup, but the mV-axis/pressure interpretation is contradicted. Retain generic E934 only. WO64844 is ACTIVE: trace FFFF860B.bit3 writer and coolant-temperature threshold source against V6 mDSHCUT/fDSHCUT; A2L conversion is X-50°C, -40°C predicts raw 0x0A. Do not repeat the sub_403D8 read test or completed QDSPT curves.

## Previous checkpoint — 2026-11-16
WO64832 closed at a bounded internal software-event endpoint. Structural fit to the JUKE `mTTVOULM/mTTVOULMS` architecture is STRONG PARTIAL; target TVO-angle semantics are WEAK. The target query comes from `UWORD[FFFF85CE] >> 4`; its upstream writer and the dynamic-bound producers remain unresolved. The target calculates two bounded UWORD schedules and compares them to trigger internal event/status handling; no physical throttle endpoint is proven. WO64833 completed: EFA4→mTFVAPO eliminated by 0/16 raw-byte equality across three Juke ROM variants; its timer-derived query and internal FFFF1014 dataflow contradict the donor fixed-RPM/angle configuration. WO64834 completed: E678/E688 retained as generic QDSPT/dashpot candidates (strong partial structure; partial family behaviour); Juke raw bytes differ, V6 raw HEX unavailable, RPM axis and ×2 L/min conversion unproven; FFFF1676 is a 0/255 runtime gate, not ×2 conversion; internal output FFFF1018 only. WO64835/WO64836 closed the F062/mTRPAMB test: exact structure remains, but HCAN1 MB12 is initialized with MBC=111 (inactive), message-control word zero, and no data-field consumer/reconfiguration found. F062 query is q=0 in the observed configuration, returning zero; live pressure semantics are rejected. No XML/Workbook edit. No XML or Master Workbook edits. V55 remains current.

## Previous checkpoint — 2026-11-16
WO64841 closed as a bounded internal software calculation. Structural fit: STRONG PARTIAL (two 8×8 UBYTE maps; both raw axes exactly match Juke mMITANDA/mMITANDD axis vectors; target 64-byte map payloads differ). Behaviour fit: PARTIAL/UNRESOLVED (DFF2 uses timer-rate-derived UWORD FFFF85DA, not a proven RPM quantity; DFFA uses FFFF857A from a UWORD lookup/shift path; FFFF85FB.bit7 chooses A382 vs A342 but its writer and mode meaning were not located; result enters a runtime composite calculation; no physical endpoint). Preserve generic A342/A382 names only. WO64842 is now ACTIVE for E904/E914 versus V6 mTHOSNTP/mTHOSRCV; reference theory is 16-point UBYTE, raw/128 data, 16-point UWORD rpm·ms axis at raw×0.1953125. The target reader is known; active work is query provenance, unit compatibility and composite downstream behaviour. V55 remains current. No XML/Workbook edits.

## Latest checkpoint — 2026-11-16
WO64842 closed as a bounded internal-state curve test. Reference geometry is 16×UBYTE data and 16×UWORD axes, but donor V6 raw payload is unavailable. Both target queries derive from U8 FFFF85A9 × U16 FFFF8494 /16; the UWORD factor is copied from +2, whose bounded writer is an A552-derived result. Target applies >>7 raw/128-equivalent scaling inside composite products, then routes to separate internal event/state paths. The target's rpm·ms axis equivalence and HOS meaning remain unresolved; retain generic E904/E914 only. WO64843 is now ACTIVE for E934/E082 vs V6 mTHPAMB/mLHPAMB. Reference: 16×UBYTE raw/128 coefficient on a 16-point UBYTE axis raw×20mV. Target data/axis and sub_22F28 reader are known; work is query FFFFA338 provenance, pressure-unit compatibility, composite scale and direct consumers. V55 remains current; no XML/Workbook edits.
## Previous checkpoint — 2026-11-15

WO64830 completed the bounded B-family downstream trace. All five B212-derived bytes (FFFF2834–FFFF2838) and the B012/B112-derived bytes (FFFF27CC–FFFF27CE) reach dynamic numeric threshold comparisons and internal state/counter updates. No physical sensor/actuator or MMIO endpoint was established. The next 9C2E/9DAE branch is not issued pending reconciliation of legacy V54 ACTIVE entries WO64275/64276/64435. Timer-11 PL1/PL2 pin-mux audit weakens its TIO11 ignition-output hypothesis; WO64794 remains PARTIAL. V55 local export exists; V54 remains current GitHub master until V55 is uploaded and verified.

## Cutover record — 2026-11-15

User authorized replacement of the OneDrive Control Notebook with this existing GitHub register. Older OneDrive/Library states are retained as historical, not merged into current lifecycle state. This GitHub file is the operational control point.

## Archived work-order evidence and historical snapshots


## WO64829 closeout / checkpoints 1–2 (2026-11-15)
- **Status:** TECHNICAL SCOPE COMPLETE — bounded internal-state reconstruction. Full evidence: `CONTROL/WO64829.md`.
- **Reader:** `sub_22E10` is a 16-point UBYTE lookup with adjacent-sample interpolation; `q>=0xF0` returns numeric sentinel 0xF0. Interpolation is linear from sample A toward B with fraction `(q&0x0F)/16), integer truncation, no rounding.
- **First lookup:** base `0xF38E`; `q1=min(4×max(UBYTE(FFFF1CA8+0x29)-UBYTE(FFFF1CA8+0x3A),0),255)`. Delta >=60 returns sentinel 0xF0. Bytes: `7D 7C 76 6E 66 60 5A 53 4D 46 40 3A 33 2D 26 20`.
- **Feedback multiply / second lookup:** prior `FFFF19BF` × first lookup result passes through `sub_223FC` = arithmetic `>>7`; raw result is capped at 0x80 for the second query. `q2=min(2×(128-v),255)`, where `v=min(floor(prior×first_result/128),128)`. For v<=8, second lookup returns sentinel. Base `0xF092`; bytes: `00 08 0C 0F 14 19 1E 23 28 2D 32 37 3C 41 46 4B`.
- **State selection:** `D=clip_signed(S2-UBYTE(FFFF1990+0x1F1),-128,127)`; `K=clip_signed(UBYTE(FFFF1CA8+0x26)-(UBYTE(+0x01)+UBYTE(+0x29))+0x40,-128,127)`. `C=0x0A` when `FFFF1E54+5.bit4` is SET; `C=0` when CLEAR (ROM bytes at `0x8296/0x8297 = 0A 00`).
- **Outputs:** `FFFF19D1_next=min(max(D,K),C)). Returned `r2) becomes `FFFF19BF_next): `C` when `D>=K), otherwise `min(K,C)`. `FFFF1D99+0x6D.bit1` reflects whether the *uncapped* scaled feedback product is >127. `FFFF1D80+1.bit0` copies that flag when D>=K, otherwise is forced set.
- **Next lead, not issued as a new WO:** immediate caller preserves `max(FFFF1CAE,FFFF1CCC)` and combines it with `FFFF19D1` before conditional stores to `FFFF85DF` at `0x59BF2`, `0x59C02`, and `0x59C04`. The final conversion/gating equation and physical meaning remain unverified.
- **Integration:** GitHub WO file and register updated; Master Workbook and Stable Control Notebook unchanged. Exact Notebook read-back still unavailable (403); no authoritative Notebook lifecycle closure or reciprocal save verification claimed. No source artifacts modified.

## WO64828 closeout / checkpoint 5 (2026-11-15)
- **Status:** TECHNICAL SCOPE COMPLETE — bounded unresolved outcome. Full evidence: `CONTROL/WO64828.md`.
- **Dynamic alias resolved:** only observed `sub_506A0` caller at `0x51C58` is preceded by `sub_5062C` (`0x51C52`). `sub_5062C` returns R4 as `FFFF357E & 0x80`, so R4 is only `0x00` or `0x80`. `sub_506A0` zero-extends R4 to R9 and stores to `FFFF1C78+0x0E+2×R9`; only destinations `FFFF1C86` / `FFFF1D86` are reachable through this call. Target indexes 0x14/0x23/0x28 (fields `FFFF1CAE/1CCC/1CD6`) are impossible here.
- **Remaining boundary:** no producer for the three input fields, and no later explicit consumer/physical ADC or actuator endpoint for `FFFF85E0`, was established in the available LST. Other unrepresented indirect, bulk-copy, DMA or peripheral updates are not globally excluded.
- **Integration:** GitHub closeout committed; Master Workbook unchanged; Stable Control Notebook unchanged and exact live read-back unavailable (403). No source edits.
- **Next:** WO64829 reconstructed the feedback lookup/state logic. The remaining callback conversion to `FFFF85DF` is a separate candidate scope; do not assume physical meaning.

## WO64827 closeout (2026-11-15)
- **WO ID / Title:** WO64827 — E974 Downstream Gating and Consumer XREF Investigation
- **Agent:** Grok
- **Technical status:** COMPLETE (bounded investigation / stop condition met)
- **Depends on:** WO64825 (PARTIAL; preserved)
- **Investigation date:** 2026-11-15

### Confirmed findings
- **Timer-derived operand producer:** `sub_257AC → FFFF85E4 → sub_34476 → FFFF8596 → sub_344A4 → FFFF85D6`.
  - `sub_257AC` supplies the timer-derived `FFFF85E4) value; downstream conversion uses `48,000,000 / FFFF85E4`.
  - Saturation/fallback behavior observed: saturates at `0xFFFF`; fallback `0x044E`.
  - `sub_34476` forms `FFFF8596`; `sub_344A4` stores the shifted/scaled result to `FFFF85D6`.
  - The query path uses `FFFF8596 >> 7`, capped at 255.
  - Physical units and semantic name remain unresolved; do not assign a semantic XML name.
- **E974 output `FFFF1F0C):** drives `FFFF8626.bit2`; this affects `FFFF1C93` and downstream `FFFF19BF` / `FFFF85E0), optional ADC channel 9 aggregation, and `FFFF8494) threshold state (including the `FFFF2F00` path).
  - Furthest confirmed endpoint is internal status/threshold and ADC aggregation. No terminal physical sensor or actuator was established.
- **E974 output `FFFF1F0D):** gates a hysteretic update of `FFFF1E54.byte0 bit 0x20`. No separate direct consumer beyond the traced status behavior was established.
- **`sub_223FE` correction:** pure signed arithmetic helper, effectively `R0 >>= 6`; no RAM access, no side effects, no branches, and it does not read `FFFF1F0C` or `FFFF1F0D`. The word at `FFFF8594+2` is the scaled operand; E974 outputs are boolean enable gates, not numeric inputs.
- **0x55xxx correction:** earlier same-GBR interpretation was overbroad. Sites `0x5599A`, `0x55A24`, and `0x55C82` resolve to `FFFF8AF0/FFFF8AF1), not the E974 bytes at `FFFF1F0C/FFFF1F0D`. Do not count them as additional direct E974 consumers.
- **Decision:** keep physical semantics and XML promotion unresolved. No calibration/XML promotion is justified by this trace.

### Stop condition / unresolved boundaries
- Producer and conversion chain for the timer-derived operand are traced to the furthest supported point; physical units/name remain unknown.
- E974 downstream effects are traced to internal status, threshold, and ADC aggregation; terminal physical sensor/actuator remains unproven.
- The separate `0x55xxx` sites are not direct E974 consumers.
- These unresolved semantic/physical endpoints are explicit boundaries, not unfinished searches within WO64827's bounded scope. Further work requires a new concrete lead or separately authorized scope.

### Integration and lifecycle
- GitHub migration register updated from the previous PARTIAL snapshot using the completed investigation report.
- Master Workbook: **not edited**.
- Stable Control Notebook: **not edited / not read-back verified**; exact item `F6DEFBD470240AE6!sac2dd9024e574ee3a7462a1730baeddd` previously returned 403 `serviceReadOnly`.
- Therefore this GitHub record reports technical completion only; it does not claim authoritative Notebook lifecycle closure or reciprocal save verification.
- **Completed work not to repeat:** timer producer chain; E974 `FFFF1F0C` / `FFFF1F0D` downstream status paths; `sub_223FE` operand-vs-enable distinction; correction of the three `0x55xxx` addresses.
- **Historical next action (superseded):** reconcile the closeout to the then-authoritative OneDrive Notebook. On 2026-11-15 the user designated this GitHub register as the sole operational authority; do not reopen the Notebook-sync task.

## WO64825 register entry (2026-11-15, preserved)
- **WO ID / Title:** WO64825 — E974 Output-Chain Investigation
- **Agent:** Grok
- **Status:** PARTIAL
- **Findings (instruction-level from annotated LST):**
  - Callsite 1 (`0x3BB1A` / `sub_3BA88`): GBR=`FFFF1E54`; query = `(FFFF85C4+0x12)>>1` clamped; result → `GBR+0xB8` (`FFFF1F0C`); read-back `0x3BBE4`; non-zero gates `sub_223FE` path. Confirmed.
  - Callsite 2 (`0x3C042` / `sub_3BFC8`): identical GBR and query construction; result → `GBR+0xB9` (`FFFF1F0D`); read-back `0x3C104`; likewise gates `sub_223FE`. Confirmed. Paired with callsite 1.
  - Callsite 3 (`0x4130E` / `sub_412B8`): distinct GBR=`FFFF1D80`; query from `FFFF859C+0x12`; output `FFFF1F0E`; local read-back and bit tests only; no shared `sub_223FE` path observed. Confirmed distinct.
- **Evidence addresses:** `0xE974`, `0x3BB1A`, `0x3BB32`, `0x3BBE4`, `0x3BC0E`, `0x3C042`, `0x3C052`, `0x3C104`, `0x3C118`, `0x4130E`, `0x41318`, `0x41330`.
- **Integration note:** Investigation PARTIAL; predecessor to WO64827.

## Durable / historical snapshots
- **V53 checkpoint:** WO64817 PARTIAL/PAUSED at CP16; WO64819 ACTIVE (PAIR-01); WO64820/WO64821 QUEUED; WO64816/WO64818 PARTIAL/PAUSED; WO64795 proposed/not issued.
- **Later Library Notebook snapshot (2026-11-15 17:55):** WO64822 ACTIVE for broad calibration harvesting; WO64819 PAUSED after CP18; WO64820/WO64821 queued/deferred; WO64817/WO64816/WO64818 paused. V53 remains the master pointer.
- The later Library snapshot's WO64822 CP02 notes:
  - E974: three `sub_22E10` callsites at PCs `0x3BB1A`, `0x3C042`, `0x4130E`; query `min(FFFF85D6 >> 1, 255)`; outputs GBR+0xB8/+0xB9 and `FFFF1F0E`.
  - EE08/EE28: cascade/selector path in `sub_3BEA6` / `sub_3F3C6`, selector bit `0x40`, output `FFFF1054+0x3CC`.
  - F33E–F36E: shared `FFFF84B8` query; source unresolved. Do not repeat source-path scans already completed under WO64819.
- **WO64819 CP18:** user cancelled the bounded CP18 investigation. `FFFF37AE` (+0x90 from `FFFF371E`) remained unresolved; later Library snapshot records the WO paused at CP18. Do not reopen without explicit request and a concrete new lead.

## Historical Control Notebook access limitation
The former OneDrive Control Notebook item `F6DEFBD470240AE6!sac2dd9024e574ee3a7462a1730baeddd` returned 403 `serviceReadOnly` during migration. It is now a legacy read-only archive, not an operational source. Earlier references in this retained history to waiting for Notebook access are superseded by the 2026-11-15 authority cutover.


- **WO64829 selector correction (2026-11-15):** final branch audit corrects C polarity: bit4 SET selects ROM byte 0x8296 (=0x0A); bit4 CLEAR selects 0x8297 (=0x00). See `CONTROL/WO64829.md` correction note and `WORKBOOK/WO64828_WO64829_E974_CHECKPOINT_2026-11-15.csv`. Earlier opposite-polarity summary is superseded.


## V54 workbook integration (2026-11-15)
- **Current Master Workbook (OneDrive):** [EL19A_Master_Reverse_Engineering_Workbook_V54_E974_WO64827_64829_2026-11-15.xlsx](https://onedrive.live.com/personal/f6defbd470240ae6/_layouts/15/doc.aspx?resid=67636be3-3e09-417e-abca-44b75955d417&cid=f6defbd470240ae6); item `F6DEFBD470240AE6!s67636be33e09417eabca44b75955d417`; 1,350,922 bytes; 144 sheets; MD5 `49491a933e31f11bce0b859d8b4c376e`; SHA256 `b566fe7f19066caa16928788da83442d1d217e296454dbc6d59808f97897c244`. Exact raw read-back was materialized and compared byte-for-byte with the final local export.
- **Integrated WOs:** WO64827, WO64828 and WO64829 are TECHNICAL SCOPE COMPLETE and now recorded in V54 sheets `WO64827 E974 Gate Trace`, `WO64828 E974 Input Audit`, `WO64829 E974 Feedback Trace`, plus `E974 Integrated Checkpoint`.
- **Key correction:** WO64829 selector polarity is `FFFF1E54+5.bit4 SET => C=0x0A; CLEAR => C=0x00`. Earlier opposite-polarity wording is superseded.
- **Remaining lead (not issued):** reconstruct final byte-generation/gating from `max(FFFF1CAE,FFFF1CCC)` plus `FFFF19D1` into `FFFF85DF`; physical meaning and `FFFF85E0` endpoint remain unresolved.
- **Authority boundary:** Stable Control Notebook item `F6DEFBD470240AE6!sac2dd9024e574ee3a7462a1730baeddd` remains unchanged; exact read-back returned 403 `serviceReadOnly`. No authoritative lifecycle sync or globally verified active WO is claimed. WO64825 remains PARTIAL.
- **GitHub binary boundary:** repository still contains the V53 XLSX binary. Text control records and CSV supplement are being synchronized to V54; V54 XLSX binary has not been uploaded to GitHub by the available GitHub file-write interface.


## WO64831 closeout — 2026-11-15
- **Status:** SCOPE COMPLETE — bounded 45-minute Dashpot/Rev-Hang evidence consolidation. Full record: `CONTROL/WO64831.md`.
- **Confirmed/strong candidates:** E678/E688 are paired 16-point UBYTE QDSPT airflow-table candidates (`mTDSHPTD/N`); 0x848A/0x848B are paired UBYTE QDSPT reduction-rate scalar candidates (`mDDSHPTD/N`), but neither D/N selector labels nor donor scaling are proven in EL19A.
- **Critical distinction:** screenshot's single 52.34% Throttle Reduction Rate remains unidentified; it is not established by the paired 0x848A/0x848B bytes. A0E2 is a 4×4 map, not a scalar.
- **mDSHCUT:** V6 donor symbol is coolant-temp prohibition scalar, raw −50°C conversion; −40°C predicts raw 0x0A. EL19A `sub_403D8` tests `FFFF860B.bit3`, matching V6 `fDSHCUT` mask 0x08, but target flag meaning and threshold reader/address remain unproven. EL19A ROM 0x84C4 is pointer data, not the donor scalar.
- **EFA4:** 16-point UBYTE lookup feeds FFFF13EA and downstream FFFF1014 path; `mTFVAPO` is only a low-confidence morphology hypothesis, not an assignment. F3D6/F3DE remain strong `mTTVOULM/S` curve candidates.
- **No XML/workbook/source artifact edits.** No candidate promoted. Full distinctions, evidence addresses, corrections and next bounded investigation are in WO64831.md.
- **Next:** independently trace (1) EL19A coolant-temperature comparison and writer of `FFFF860B.bit3`; (2) the screenshot's single Throttle Reduction Rate scalar and its downstream throttle-target effect. Do not repeat completed E678/E688/EFA4 initial reader traces.
- **Operational state:** no new active WO issued; WO64831 is a completed consolidation record only.


- **Completed batch:** WO64935–WO64937 — harvested 17 additional directly referenced 8-point UBYTE placements through fixed-grid sub_22DF8 across E6xx–F5xx; recorded exact bytes/hashes and caller sites; separated two constant structural objects and duplicate 0x80 payload placement. No ROM axes expected; no semantics promoted; no source artifact changed.
- **Active work order:** None — next step should return to small-map reader pointer coverage and 16-point UBYTE candidates outside the already inventoried sub_22E10 71-entry set, then test any remaining explicit-axis 8-point entries for duplicates.


## Active batch continuation — 2026-11-16
WO65015–WO65017 are PAUSED — PRIORITY DEFERRED (2026-11-17); unresolved leads preserved. See their individual WO pause notes. Latest bounded updates: WO65015 confirms the consumer truth table (E688 only when FFFF85F8.bit4 and FFFF8600.bit6 are both clear; otherwise E678), while physical Drive/Neutral interpretation remains donor-family supported but not directly decoded; both selector bits also gate other status/event paths. WO65016 separates FFFF860D.bit5 readers from the mDSHCUT bit3 lead; FFFF860D/0E are copied into FFFF860B/C and separately 8611/12, but original producer/coolant semantics remain unresolved. WO65017 raw scan triage leaves aligned 0xEC9C=0x0086 only as an unassigned byte-table morphology lead; no QDSPT/APO reader or target scalar established. See individual WOs for evidence PCs. No XML, workbook, ROM, LST, IDB, scripts or Library files changed.


WO65015 additional provenance checkpoint (2026-11-16): sub_2245C at 0x20FBA–0x20FC0 copies three bytes from FFFF8602–8604 to FFFF85FF–8601, so the sub_403D8 selector condition FFFF8600.bit6 is copied from FFFF8603.bit6. FFFF8603 is rewritten at 0x34ADC by a status-composition routine that preserves bit6 while modifying bit7; upstream origin and Drive/Neutral meaning remain open. WO65015–65017 are PAUSED — PRIORITY DEFERRED (2026-11-17); unresolved leads preserved. See their individual WO pause notes.



### Active batch continuation — 2026-11-17
WO65015–WO65017 remain ACTIVE. New bounded findings: WO65015 found a second FFFF8603 writer at 0x35100–0x3514A that modifies bit1 while preserving selector bit6; original bit6 source remains unresolved. WO65016 identified sub_B119A as a composition writer for FFFF860D bits 0x01/0x02/0x04/0x10, but it preserves bit3; coolant semantics and bit3 origin remain unresolved. WO65017 extended the target 0x90EA trace: it belongs to a multi-UWORD signed-arithmetic coefficient family consumed through sub_22A8C/sub_23004, not a direct-axis lookup; donor address transfer remains rejected and target mDDPAPO location unresolved. See individual WOs. No XML, workbook, ROM, LST, IDB, scripts or Library files changed.


### Active batch continuation — 2026-11-17 (additional bounded findings)
WO65015–WO65017 remain ACTIVE. WO65015 writer inventory reconciled to seven identified RMW sites on FFFF8603 (five direct-base sites plus GBR-relative stores at 0x34ADC and 0x3514A); all seven preserve bit6, so its source remains unresolved. WO65016 adds sub_B12A6 at 0xB12DE as a FFFF860D.bit6 writer driven inversely by FFFF2EFE.bit6; sub_B119A updates bits 0/1/2/4, while bit3 remains unassigned and its numeric coolant threshold is still unknown. WO65017 excludes QDSPT-path UWORD operands 0x92C4=0x0000 and 0x924E=0xFFFF from the 0x0086 mDDPAPO fingerprint; target counterpart remains unknown. Updated only the three WO documents and this register; no workbook/XML/ROM/LST/IDB/script/Library edits.


### Active batch continuation — 2026-11-17 (bit-3 consumer check)
WO65016: annotated LST contexts at 0x3526A–0x35282 and 0x3BFF4–0x3C00E confirm FFFF860D.bit3 is used as a state gate for a GBR-relative record update and an E974 16-point lookup path. Neither is a numeric coolant comparison. This adds consumer context but does not establish or exclude a coolant-related source; mDSHCUT target scalar remains unresolved. WO65015 and WO65017 have no new promotion in this pass. WO65015's earlier five/seven RMW writer audits are not repeated; source bit6 investigation remains at the separate indirect/initial-source stage authorized by continuation. Updated WO65016 and this register only; no workbook/XML/ROM/LST/IDB/scripts/Library changes.


- **Completed:** WO65018 — `sub_403D8` is reached through the separate 122-entry callback table at `0x2187C`: zero-based slot 35 / one-based slot 36 at `0x21908` points to `loc_3C478`, which calls `sub_403D8` via literal `0x3C504`. Dispatcher `sub_20DCE` is called by `INT_TRAPA62`; ROM vector entry `0x200FC` points to `0x25004`. This is distinct from the six `sub_209A6` callback groups; ATU-31 attribution and runtime cadence are not established. See [WO65018](WO65018.md). No workbook/XML/ROM/LST/IDB/script/Library changes.


- **Active:** WO65019 — inspect every TRAPA #0x3E site (including the newly surfaced 0xB8766 site), per-site VBR setup/handler routing, enclosing conditions and startup/event/periodic context. Do not infer cadence without direct scheduler/timer evidence. See [WO65019](WO65019.md). No workbook/XML/ROM/LST/IDB/script/Library changes.


- **Completed:** WO65019 — audited all four actual `trapa #0x3E` sites. Only `0x26BC` is proven to route via VBR=`0x20004`, slot `0x200FC`, to `INT_TRAPA62 → sub_20DCE`; `0x10F4` uses inherited VBR (VBR=0 slot points to `loc_26F8`), `0x157E` selects RAM slot `FFFF85FC` with target unresolved, and `0xB8766` selects ROM slot `0x6FF8` containing `FFFFFFFF`. Separate `alt_Poweron_Reset` trampoline at `0x21AA8` directly jumps to `INT_TRAPA62`. No cadence established. See [WO65019](WO65019.md). No workbook/XML/ROM/LST/IDB/script/Library changes.


- **Active:** WO65020 — bounded provenance of RAM TRAPA vector slot `FFFF85FC` used by site `0x157E`; identify complete longword initialization/producer and handler only if supported. See [WO65020](WO65020.md). No ROM/XML/workbook/LST/IDB/script/Library edits.


- **Bounded complete — CLOSED:** WO65020 — direct LST references show fragmented byte copies only (`85FB→85FC`, `85FE→85FD`, `8602→85FF`); no complete runtime vector or handler destination established. Indirect aliases and live values remain unresolved. See [WO65020](WO65020.md). No source artifacts modified.


## Active call-table inventory batch — 2026-11-17

- **CLOSED:** WO65021 — six `sub_209A6` callback tables reconciled; see batch closeout below and [WO65021](WO65021.md).
- **CLOSED:** WO65022 — nine-entry `sub_2088C` table reconciled; see batch closeout below and [WO65022](WO65022.md).
- **BOUNDED CLOSED:** WO65023 — additional indexed callback candidates found; complete inventory remains unresolved. See batch closeout below and [WO65023](WO65023.md).
- **Batch rule:** at most three WOs; minimum chat; only these WO files and this register may be updated. No XML/workbook/ROM/LST/IDB/script/Library edits. Table existence/count does not establish task purpose, cadence or interrupt attribution.


## Call-table inventory batch closeout — 2026-11-17

- **COMPLETE — CLOSED:** WO65021 — six `sub_209A6` tables reconciled: bases `216EC/2170C/21744/21760/21858/21870`, counts `8/14/7/62/6/3`, 100 unique BE pointers, all targets verified as code entries; exact loop PCs and bounds recorded. See [WO65021](WO65021.md).
- **COMPLETE — CLOSED:** WO65022 — `sub_2088C` nine-entry table at `0x21A64–0x21A87`; all nine unique BE pointers verified as code entries; exact loop mechanics recorded. See [WO65022](WO65022.md).
- **BOUNDED COMPLETE — CLOSED:** WO65023 — local indirect-transfer scan found 21 additional candidate sites beyond the known dispatcher loops, including a ROM function-pointer-array lead at `0x13AD8`; three computed jumps are switch dispatch, and callback/record candidate bounds remain unresolved. Therefore complete ROM-wide call-table coverage is **not established**. See [WO65023](WO65023.md).
- **Next recommended scope:** resolve the `0x13AD8` pointer array and then reconstruct bounds/source records for indexed callback families at `0x35xx/0x37xx/0x38xx/0x3Cxx` and `0xB4xx`. Do not claim completeness from the current bounded scan.
- **Artifact boundary:** only WO65021–WO65023 and this operational register updated. No XML, workbook, ROM, LST, IDB, scripts or Library files modified.


## Active call-table continuation batch — 2026-11-17

- **COMPLETE — CLOSED:** WO65024 — resolve ROM function-pointer-array lead at 0x13AD8, called through indexed indirect site 0x250C4. Establish index mechanics, pointer extent/count and valid targets. See [WO65024](WO65024.md).
- **BOUNDED COMPLETE — CLOSED:** WO65025 — reconstruct indexed callback candidates at 0x35C4, 0x35F8, 0x3718, 0x384C and 0x3CCA; identify shared bases/record layouts and bounds. See [WO65025](WO65025.md).
- **BOUNDED COMPLETE — CLOSED:** WO65026 — reconstruct indexed callback candidates at 0xB4B3C, 0xB4B70, 0xB4CB6, 0xB4DE2 and 0xB5280; determine whether these share one family. See [WO65026](WO65026.md).
- **Batch constraints:** maximum three WOs; bounded structural tracing only; preserve hypotheses separately from verified mechanics; do not infer cadence, task semantics or ROM-wide completeness. If a candidate stops yielding structural progress, close it with the exact method boundary and move on.
- **Artifact boundary:** only WO65024–WO65026 and this register may be updated. No XML, workbook, ROM, LST, IDB, scripts or Library edits.


## Call-table continuation batch closeout — 2026-11-17

- **BOUNDED COMPLETE — CLOSED:** WO65024 — `0x13AD8` contains three BE function pointers (`0x24BCC`, `0x24E50`, `0x24BD0)); indirect call at `0x250C4` indexes it using a longword read from MMIO `0xF78E`. Runtime index domain is unresolved; next longword is non-pointer. See [WO65024](WO65024.md).
- **BOUNDED COMPLETE — CLOSED:** WO65025 — five low-ROM indirect call sites share a 24-byte-stride ROM structure rooted at `0x4D84`; field offsets +8/+12/+16/+20 and several code targets decoded. Bounds and legal index domains remain unresolved. See [WO65025](WO65025.md).
- **BOUNDED COMPLETE — CLOSED:** WO65026 — five `0xB4xxx` sites divide into RAM callback records selected via `0x163A4` and ROM descriptor records rooted at `0x163B0`; 24-byte stride and field offsets verified, several targets decoded. Bounds and safe index domains remain unresolved. See [WO65026](WO65026.md).
- **Concurrency:** WO65015–WO65017 paused (not closed) to prioritize the user-directed call-table inventory; their unresolved technical leads are preserved. Three-slot active limit now available.
- **Artifact boundary:** only WO65015–WO65017, WO65024–WO65026 and this operational register updated. No XML, Master Workbook, ROM, LST, IDB, scripts or Library files modified.



## Active indirect-call completion batch — 2026-11-17

- **BOUNDED COMPLETE — CLOSED:** WO65027 — six stack-sourced call sites resolve to fixed helper targets; no callback tables. See [WO65027](WO65027.md).
- **BOUNDED COMPLETE — CLOSED:** WO65028 — all 21 previously identified candidates classified except 0x7207A; 213 residual indirect transfers remain unresolved under the bounded scan method. See [WO65028](WO65028.md).
- **BOUNDED COMPLETE — CLOSED:** WO65029 — no local upper bounds established for reviewed indices; observed valid positions are not complete legal domains. See [WO65029](WO65029.md).
- **Batch constraints:** maximum three WOs; bounded traces only; no global RAM provenance scan; do not claim ROM-wide completeness or infer task semantics/cadence from structure alone.
- **Artifact boundary:** only WO65027–WO65029 and this register may be updated. No XML, Master Workbook, ROM, LST, IDB, scripts or Library edits.


## Indirect-call completion batch closeout — 2026-11-17

- **BOUNDED COMPLETE — CLOSED:** WO65027 — six stack-sourced indirect calls resolve to fixed helper targets: `sub_21AC0` (four sites), `sub_22F80` (one), and `0xA6E1C` (one). No callback table established. See [WO65027](WO65027.md).
- **BOUNDED COMPLETE — CLOSED:** WO65028 — bounded 18-line pattern audit classified the 21 additional sites from WO65023; `0x7207A` remains a specific indexed-call candidate; 213 residual indirect transfers were not locally resolved and may use earlier/indirect pointer provenance. Three computed jumps remain excluded from function-call-table counts. See [WO65028](WO65028.md).
- **BOUNDED COMPLETE — CLOSED:** WO65029 — reviewed index producers/guards for `0x13AD8`, `0x4D84`, `0x163B0` and selected RAM records; no complete legal index domains proven. Observed static targets are recorded as positions, not maximum bounds. See [WO65029](WO65029.md).
- **Side-project stopping point:** the three established dispatcher families (231 entries), the additional 3-entry `0x13AD8` array, the 24-byte-stride callback/descriptor families, and six fixed stack-sourced helper calls are documented. ROM-wide completeness is **not** proven. The remaining indexed site `0x7207A` is now resolved as a stack-preserved fixed call to `sub_2272E`; 213 residual indirect transfers remain unresolved under the bounded scan. Do not claim all call tables have been found.
- **Active state:** no active WOs remain in this call-table track. WO65015–WO65017 remain paused and can be resumed only when prioritized again.
- **Artifact boundary:** only WO65027–WO65029 and this operational register updated in this closeout. No XML, Master Workbook, ROM, LST, IDB, scripts or Library files modified.


- **Final candidate correction — 2026-11-17:** WO65028 addendum resolves `0x7207A` as a stack-preserved fixed call to `sub_2272E` (literal `0x2272E` loaded at `0x72050`, stored at `0x72058`, reloaded at `0x72076`). All 21 additional WO65023 candidates are now structurally classified. The 213 residual indirect transfers remain outside the bounded local-pattern result.


## Residual indirect-transfer audit batch — 2026-11-17

- **COMPLETE — CLOSED:** WO65030 — corrected the alleged 41-pointer vector at `0x219C0`: it is the 41-entry suffix of the existing 122-entry `sub_20DCE` table at `0x2187C–0x21A60`. Address `0x21A0C` is overall slot 100; it points to `0x70788`, which calls `sub_AAAE0`. No separate table is established. See [WO65030](WO65030.md).
- **ACTIVE:** WO65031 — residual indirect-transfer audit, `0x00000–0x3FFFF`; 65 unannotated sites initially, including known sites to exclude. See [WO65031](WO65031.md).
- **ACTIVE:** WO65032 — residual indirect-transfer audit, `0x40000–0x7FFFF`; 96 unannotated sites initially, including known sites to exclude. See [WO65032](WO65032.md).
- **Batch constraints:** maximum three WOs; bounded call-register provenance only; no global RAM-writer scan; no semantic/cadence attribution from structure alone.
- **Artifact boundary:** only WO65030–WO65032 and this operational register updated. No XML, Master Workbook, ROM, LST, IDB, scripts or Library files modified.


## Residual indirect-transfer audit batch closeout — 2026-11-17

- **BOUNDED COMPLETE — CLOSED:** WO65031 — low-ROM segment `0x00000–0x3FFFF`: 65 unannotated indirect-transfer sites reviewed. Classified fixed ROM helpers, RAM-resident pointer slots, stack-sourced arguments, computed switch jumps, runtime record callback fields and the already-known sequential `sub_20DCE` table call. No additional static ROM pointer table established. See [WO65031](WO65031.md).
- **BOUNDED COMPLETE — CLOSED:** WO65032 — middle-ROM segment `0x40000–0x7FFFF`: 96 unannotated sites reviewed; 86 stack-sourced pointer arguments, three fixed calls to `sub_224A0`, and one unresolved register-provenance site. No additional static ROM pointer table established. See [WO65032](WO65032.md).
- **Batch result:** the alleged separate 41-entry `0x219C0` vector is rejected as a suffix of the existing 122-entry `sub_20DCE` table. The bounded low/middle segment reviews found no new static ROM function-pointer vector. High-ROM residual segment `0x80000–0xFFFFF` remains for a later batch; residual stack/RAM pointer provenance is not globally resolved.
- **Active state:** no active WOs remain in this batch.
- **Artifact boundary:** only WO65031, WO65032 and this operational register updated in closeout. No XML, Master Workbook, ROM, LST, IDB, scripts or Library files modified.


## Next indirect-transfer provenance batch — 2026-11-17

- **BOUNDED COMPLETE — CLOSED:** WO65033 — high-ROM residual indirect-transfer audit `0x80000–0xFFFFF`; 80 sites classified. See [WO65033](WO65033.md).
- **BOUNDED COMPLETE — CLOSED:** WO65034 — seven direct RAM-address transfer targets reconciled to ROM literals; no callback slots established. See [WO65034](WO65034.md).
- **BOUNDED COMPLETE — CLOSED:** WO65035 — 12 representative stack-sourced sites classified. See [WO65035](WO65035.md).
- **Batch limit:** three work orders; bounded traces only; no exhaustive global dataflow or broad RAM-writer scan.
- **Artifact boundary:** only WO65033–WO65035 and this operational register may be updated. No XML, Master Workbook, ROM, LST, IDB, scripts or Library modifications.


## Indirect-transfer provenance batch closeout — 2026-11-17

- **BOUNDED COMPLETE — CLOSED:** WO65033 — all 80 unannotated high-ROM indirect-transfer sites classified: 70 fixed ROM helper calls, five previously classified callback/descriptor calls, and five unresolved register/stack provenance sites. No additional static ROM pointer vector established. See [WO65033](WO65033.md).
- **BOUNDED COMPLETE — CLOSED:** WO65034 — corrected seven purported RAM callback slots to direct RAM-address JSR/JMP targets sourced from ROM literals. Two addresses also have GBR-relative data references; RAM code/data initialization remains unresolved. See [WO65034](WO65034.md).
- **BOUNDED COMPLETE — CLOSED:** WO65035 — 12 representative stack-sourced sites: seven fixed helper pointers, three shared caller-supplied pointer arguments at `SP+0x30`, and two unresolved stack producers. See [WO65035](WO65035.md).
- **Batch result:** No additional static ROM function-pointer vector established in the high-ROM residual population. The unresolved remainder is provenance of caller-supplied/stack pointers, two register tail jumps, and RAM-address transfer destinations—not evidence of another ROM table.
- **Active state:** no active WOs remain in this batch.
- **Artifact boundary:** only WO65033–WO65035 and this operational register updated. No XML, Master Workbook, ROM, LST, IDB, scripts or Library files modified.


## Active calibration dataflow batch — 2026-11-17

- **BOUNDED COMPLETE:** WO65036 — 9C2E/9DAE paired 16×16 lookups and differential arithmetic/output consumers structurally traced; input producers/physical meanings unresolved. See [WO65036](WO65036.md).
- **BOUNDED COMPLETE:** WO65037 — ADF2/AF72 paired lookup arithmetic, alternate startup writer and downstream consumers/override paths traced; semantics unresolved. See [WO65037](WO65037.md).
- **BOUNDED COMPLETE:** WO65038 — ten selected sub_22E10 candidates audited for query, result staging and immediate local use; remaining 30 moderate/high-variation candidates not audited. See [WO65038](WO65038.md).
- **Priority source:** Master Workbook V56, sheet "P2 Next Priorities" (ranked items 2, 4 and 5). The 9B2E/WO64435 dependency is not duplicated.
- **Batch constraints:** at most three WOs; minimum chat; bounded producer/consumer tracing; preserve provisional semantics; no broad global scans.
- **Artifact boundary:** only WO65036–WO65038 and this register may be updated. No XML, Master Workbook, ROM, annotated LST, IDB, scripts or Library modifications. The source workbook and LST were read-only inputs.


### Active batch progress — 2026-11-17
- WO65036: XREF checkpoint records 41 unique literal-pointer load sites for FFFF849A; FFFF85B2 is accessed as [FFFF859C+0x16], so its producer search must follow the base-plus-offset. No producer promoted yet.
- WO65037: first paired consumer found in sub_AE9EA: reads FFFF1707/FFFF1708, selects/interpolates them through sub_21AC0 and stores a UBYTE at FFFF1CA5. Other consumers and alternate writers remain to be reconciled.
- WO65038: target-ROM morphology ranking completed; ten candidates selected (E9FC, EB40, F072, F2F2, F256, EA3C, EA2C, E800, F01C, EDA0). Caller/query/result-consumer traces remain open.


## Priority progress — 2026-11-17
- **WO65036:** direct provenance pass: 41 FFFF849A pointer-load sites are read-side; FFFF859C+0x16 known readers are also read-side. No direct producer found. Differential arithmetic corrected: only GBR+6.bit5 CLEAR and GBR+3.bit7 SET enter the 9C2E/9DAE differential; W = signed UWORD[FFFF10F8] + ((A−B)<<8), word staged at FFFF100A, signed-byte conversion at FFFF1C79. Two downstream readers of FFFF1C79 found. Stop at unresolved alias/bulk/peripheral source boundary; no global writer scan.
- **WO65037:** map outputs FFFF1708/1707 feed endpoint/interpolation path to FFFF1CA5; signed interpolation, 0x80 sentinel gates, conditional signed correction, initialization writer (0x7E defaults), and three direct downstream consumer routines are documented. Physical meaning unresolved; sub_AE942 remains a possible alternate FFFF1CA5 writer/override.
- **WO65015–WO65017:** bounded closures completed and readback verified; their unresolved leads remain documented and can be reopened only with new evidence.

- **WO65037 follow-through:** sub_AE942 alternate FFFF1CA5 writer resolved. It executes after sub_AE8CE and can overwrite its result from either a status-gated direct UBYTE source (FFFF85AC or FFFFB2BC), a UWORD source FFFF847A>>2 clamped to UBYTE, or the shared interpolation/0x80 sentinel path. Downstream consumers therefore see the post-sub_AE942 value, not necessarily the map result.


## Bounded closeouts — 2026-11-17
- WO65036 closed at the direct-producer boundary after 41 FFFF849A pointer-load sites and known FFFF859C+0x16 readers were audited. Legacy WO64275/WO64276 documents were not found in the current main control tree; status not inferred.
- WO65037 closed after paired output arithmetic, startup initialization writer, alternate sub_AE942 writer, sentinel and direct downstream consumers were traced. Physical semantics remain unassigned.
- WO65038 remains the sole active item from this batch; do not reopen WO65036/WO65037 without a new specific producer/transfer or semantic evidence lead.


### WO65038 caller-audit progress — 2026-11-17
- First three of ten selected candidates traced: E9FC (query max(UBYTE[FFFF859C+0x0D]−0x10,0), result FFFF1054+0x26C; paired local multiply with F12E), EB40 (query min(2×UWORD[FFFF84D4+0x24],255), result FFFF1054+0x2B4; signed correction path to +0x2B5), F072 (multi-stage stack/RAM-derived query, result FFFF1131; paired F082 lookup follows). Evidence PCs and caveats are in [WO65038](WO65038.md).
- Remaining seven candidates: F2F2, F256, EA3C, EA2C, E800, F01C, EDA0. Continue in bounded groups of three; keep physical semantics provisional.

- **WO65038 second caller-audit group complete (6/10):** F2F2 query `min(2×max(UBYTE[FFFF859C+8]−8,0), highbyte(UWORD[FFFF8494]))`, result retained in R11; F256 query `min(4×UBYTE[FFFF84D4+0x5D],255)`, result at `FFFF2150+0x970) and enters `sub_223FC` path; EA3C uses raw UBYTE `[FFFF84B4+4]`, result shifted ×256 to `FFFF2150+0x606) and participates in the paired EA2C/F2B2 path. Evidence in [WO65038](WO65038.md). Remaining EA2C, E800, F01C, EDA0.

- **WO65038 third caller-audit group complete (9/10):** EA2C raw `[FFFF84B4+4]` → `FFFF1054+0x312`, paired with EA3C/E63C/F2B2; E800 query `min(4×UBYTE[FFFF1054+0x1C1],255)` → `FFFF1054+0x1C0); F01C raw `[FFFF84B4+4]` → stack local, paired with EE68 under the same query. Evidence in [WO65038](WO65038.md). Only EDA0 remains.


## WO65038 top-ten caller audit closeout — 2026-11-17
- **BOUNDED COMPLETE — CLOSED:** WO65038 — E9FC, EB40, F072, F2F2, F256, EA3C, EA2C, E800, F01C and EDA0 each have bounded caller/query/result-staging/immediate-use traces. No physical semantics or units assigned; 30 remaining moderate/high-variation candidates remain unaudited. See [WO65038](WO65038.md).
- **Active state:** no active work orders remain in this calibration dataflow batch. Next work should be selected from the remaining candidate/axis coverage gaps, not by repeating the completed top-ten set.
- **Artifact boundary:** only WO65038 and this register updated. ROM and V32 listing were read-only inputs; no workbook, XML, IDB, scripts or Library files modified.


## Next selective sub_22E10 caller batch — 2026-11-17
- **BOUNDED COMPLETE:** WO65039 — E510 at `0x4FA02` traced; correct entry is `loc_4F8AC` (not inventory label `sub_4F6DE`), query is high byte of UWORD `FFFF8518`, result staged `FFFF14CA`, immediate arithmetic traced. See [WO65039](WO65039.md).
- **BOUNDED COMPLETE:** WO65040 — EB30 at `0x48120` traced; query `clamp_u8(ceil((FFFF85B2−96)/2))`, result contributes `(curve−0x80)` to bounded UWORD `FFFF1382`. See [WO65040](WO65040.md).
- **BOUNDED COMPLETE:** WO65041 — EDF0 at `0x3C776` traced; raw UBYTE `FFFF84B8` query, result at `FFFF138C`, multiplied with `FFFF1387` and passed through `sub_223FC` to `FFFF1386`. See [WO65041](WO65041.md).
- **Selection basis:** next uncovered target-ROM 16-byte candidates with distinct caller families; raw payloads and morphology are recorded in each WO. Discovery evidence only.
- **Batch rule:** maximum three WOs; minimum chat; bounded caller traces only. At completion, recommend the next three uncovered candidates rather than opening more than three concurrently.
- **Artifact boundary:** only WO65039–WO65041 and this register may be updated. No XML, Master Workbook, ROM, annotated LST, IDB, scripts or Library modifications.


## Caller-audit batch WO65039–WO65041 closeout — 2026-11-17
- All three bounded audits complete; report findings and caller-label correction are in WO65039–WO65041. E510's V32 caller label was corrected from `sub_4F6DE` to `loc_4F8AC` using the code entry and XREF pointer at `0x21928`.
- ROM identity verified locally: 1 MiB; MD5 `46991697c502052752a2cabcb84c9e27`. All three 16-byte payloads match the target ROM.
- No physical semantics/units assigned. Upstream input producers and downstream system-level consumers remain outside bounded scope.
- No active work remains in the WO65039–WO65041 batch. Next priority: another three uncovered high-variation `sub_22E10` candidates from the existing inventory, avoiding previously audited candidates and previously completed work-order targets.
- Artifact boundary observed: only WO65039–WO65041 and this register updated; no workbook/XML/ROM/LST/IDB/scripts/Library changes.


## Selective F34E caller/result audit — 2026-11-17

- **BOUNDED COMPLETE — CLOSED:** WO65042 — F34E's two `sub_22E10` callers both use raw UBYTE query FFFF84B8. In `loc_4F8AC`, result remains in R11 and affects multiplication plus an upper-bound clamp. In `loc_4FBC2`, it scales UWORD FFFF134E by `F34E_result × 100 / 2^14`, capped to UWORD, staged at FFFF15A2 and copied to FFFF1D5C. Target payload verified: `6D 6D 6D 57 40 35 28 1D 16 12 0E 0E 0E 0E 0E 0E`. Semantics/units and FFFF84B8 producer remain unresolved. See [WO65042](WO65042.md).
- **Next:** WO65043 — F35E result/dataflow audit only; reuse the same bounded FFFF84B8 query evidence, do not repeat producer scans.
- **Batch method:** one candidate per saved/verified report; proceed to the next only after successful report and register readback. Maximum three WOs per batch.
- **Artifact boundary:** only WO65042 and this register updated. No XML, Master Workbook, ROM, LST, IDB, scripts or Library modifications.


## Selective F35E caller/result audit — 2026-11-17

- **BOUNDED COMPLETE — CLOSED:** WO65043 — F35E's two `sub_22E10` callers use raw UBYTE FFFF84B8. In `loc_4F8AC`, result R8 is passed to `sub_543CC`, whose UWORD return is stored at FFFF1D5A. In `loc_4FBC2`, result is multiplied by UWORD FFFF134E and 100, shifted right 14, capped to UWORD, staged at FFFF15A4 and copied to FFFF1D5E. Target payload verified: `85 85 85 6B 4E 41 30 23 1A 16 11 11 11 11 11 11`. Semantics/units and FFFF84B8 producer remain unresolved. See [WO65043](WO65043.md).
- **Next:** WO65044 — F33E result/dataflow audit only; reuse the same bounded FFFF84B8 query evidence, do not repeat producer scans.
- **Batch method:** one candidate per saved/verified report; proceed only after report and register readback. Maximum three WOs per batch.
- **Artifact boundary:** only WO65043 and this register updated. No XML, Master Workbook, ROM, LST, IDB, scripts or Library modifications.


## Selective F33E caller/result audit — 2026-11-17

- **BOUNDED COMPLETE — CLOSED:** WO65044 — F33E's two `sub_22E10` callers use raw UBYTE FFFF84B8. In `loc_4F8AC`, result R12 enters coupled fixed-point arithmetic with the neighboring curve results; no standalone result store is established. In `loc_4FBC2`, F33E is scaled with UWORD FFFF134E and 100, shifted right 14, capped to UWORD, stored at FFFF1D58 and copied to FFFF1D5A. Target payload verified: `3F 3F 35 29 00 00 00 00 00 00 00 00 00 00 00 00`. Semantics/units and FFFF84B8 producer remain unresolved. See [WO65044](WO65044.md).
- **Batch closeout:** WO65042–WO65044 each completed and individually readback-verified before proceeding. All three share raw query FFFF84B8; no query-producer scan was repeated. No semantic labels or units promoted.
- **Next recommended:** WO65045 — F36E result/dataflow audit, same caller family and shared query; then select the next uncovered high-variation sub_22E10 candidate from the remaining inventory (avoid E510, EB30, EDF0 and the ten WO65038 candidates).
- **Active state:** no active WOs in this batch.
- **Artifact boundary:** only WO65042–WO65044 and this register updated. No XML, Master Workbook, ROM, LST, IDB, scripts or Library modifications.

## Active coolant / dashpot provenance investigation — 2026-11-17

- **ACTIVE:** WO65045 — identify the source and sensor-block role of UBYTE `FFFF84BA`; reproduce the hysteresis comparison at `0x40422–0x4044C`; trace `FFFF1DB4.bit5` separately from the `sub_403D8`-tested `FFFF860B.bit3`; establish or reject a direct data/control link. Initial LST polarity correction: +3 applies when `FFFF1DB4.bit5` is CLEAR. Task 1 direct byte-store census: two syntactic `mov.b @(6,Rn)` candidates were both false positives after register redefinition; zero confirmed literal-base byte stores to `FFFF84BA`. Wider stores/offset aliases and semantic identity remain open. See [WO65045](WO65045.md).
- **Starting correction:** R2=`FFFF84B4`, displacement +6 gives effective address `FFFF84BA`. Do not use `FFFF84C0`; that was an arithmetic slip in the initial WO draft and was corrected before register activation.
- **Bounded method:** targeted writers/transfer provenance and selected readers only; stop at alias/bulk/peripheral boundaries. No global RAM-writer scan.
- **Artifact boundary:** only the authorized WO65045/WO65046 documents and this register may be updated. No workbook, XML, ROM, LST, IDB, scripts or Library modifications.


## FFFF84BA wider-store audit — 2026-11-17

- **BOUNDED COMPLETE — CLOSED:** WO65046 inspected eleven literal-base load windows for stores through `FFFF84B4`; all apparent stores were false positives after register redefinition. No confirmed wider-width or indexed store to `FFFF84BA` found in the bounded 30-instruction windows. Explicit read-side uses include `0x9538A`, `0x95DCE`, `0x9633C`, `0x5054A`, `0x770B8`, and `0x77152`. This is not a ROM-wide no-writer proof; alias/GBR/block/peripheral paths remain open. See [WO65046](WO65046.md).
- **Active:** WO65045 remains open for producer provenance and sensor-block identity. Next isolated task: narrow explicit pointer-offset/GBR alias check around concrete readers; stop at transfer boundaries.
- **Artifact boundary:** only WO65046, WO65045 and this register updated. ROM/LST/XREF inputs read-only; no workbook, XML, IDB, scripts or Library changes.


## FFFF84BA GBR-alias provenance task — 2026-11-17

- **BOUNDED COMPLETE — CLOSED:** WO65047 — GBR roots resolve `0x9538A` and `0x95DCE` to `FFFF84B4+6`, and `0x9633C` to `FFFF8494+0x26`; all are reads of `FFFF84BA`. Eight relevant GBR-root contexts were checked for stores/RMWs overlapping the byte; none found. No local producer/transfer path established. See [WO65047](WO65047.md).
- **Parent:** WO65045 remains ACTIVE for overall source/sensor identity and dashpot linkage; this WO is an isolated subtask.
- **Artifact boundary:** only WO65047 and this register may be updated for this task. Inputs read-only; no workbook, XML, ROM, LST, XREF, IDB, scripts or Library changes.


## WO65047 closeout — 2026-11-17

- **BOUNDED COMPLETE — CLOSED:** GBR-relative alias review completed and report read-back verified. No direct GBR store/RMW or local transfer populating `FFFF84BA` found in the selected contexts. This is a bounded negative only; computed aliases, external callers, bulk transfer and peripheral/interrupt acquisition remain unresolved.
- **Active:** WO65045 remains open for overall provenance, sensor identity and separate dashpot-linkage investigation. No coolant identity assigned.
- **Next:** select a concrete transfer/source lead before further scans; avoid repeating direct-store and GBR-store censuses.
- **Artifact boundary:** only WO65047 and the operational register updated. Source files remained read-only.


## FFFF84BA reader-role discrimination — 2026-11-17

- **BOUNDED COMPLETE — CLOSED:** WO65048 — six reader contexts establish `FFFF84BA` as a threshold operand, clamp ceiling, numeric-conversion input and copied record field within a multi-field RAM structure rooted at `FFFF84B4`. No coolant channel/conversion evidence; physical identity remains unresolved. See [WO65048](WO65048.md).
- **Parent:** WO65045 remains ACTIVE; WO65046/WO65047 are closed bounded provenance passes.
- **Artifact boundary:** only WO65048 and this register may be updated. All source files read-only; no workbook, XML, ROM, LST, XREF, IDB, scripts or Library changes.


## WO65048 closeout — 2026-11-17

- **BOUNDED COMPLETE — CLOSED:** six selected readers audited. `FFFF84BA` is used as a threshold operand, clamp ceiling, conversion input and copied record field. Adjacent +1/+3/+4 reads support a multi-field structure; no coolant-specific channel or conversion identity found.
- **Active:** WO65045 remains open for producer/sensor identity and separate dashpot linkage. No coolant label promoted.
- **Next:** pursue only a concrete new acquisition/alias/copy/caller-pointer lead; do not repeat direct byte, wider-store or GBR-store scans.
- **Artifact boundary:** only WO65048 and the operational register updated. Source files remained read-only.


## FC90/111EA temperature-axis alignment — 2026-11-17

- **BOUNDED COMPLETE — CLOSED:** WO65049 — FC90/111EA pointer alignment corrected. Query is `UBYTE[FFFF84BA]×0x100`; pointer `0x111EA` yields BE UWORD axis `3200,4600,5000,6E00,7300,7800,7D00,8200` (Q8.8 = 50–130). Historical `0032,...,0082` note was two-byte misaligned. Temperature-like input confirmed; coolant plausible but not identified. See [WO65049](WO65049.md).
- **Correction:** WO65049 reproduced the pointer-relative axis and helper; the old `0032,...,0082` note was misaligned. Use `3200,...,8200` as BE UWORD Q8.8 breakpoints.
- **Parent:** WO65045 remains ACTIVE. WO65046–WO65048 are closed bounded tasks.
- **Artifact boundary:** only WO65049 and this register may be updated. Source files read-only; no workbook, XML, ROM, LST, XREF, IDB, scripts or Library changes.


## WO65049 closeout — 2026-11-17

- **BOUNDED COMPLETE — CLOSED:** FC90/111EA reader contract reproduced. `FFFF84BA` is shifted left 8 and searched against pointer-relative BE UWORD axis `3200,4600,5000,6E00,7300,7800,7D00,8200`; this is Q8.8 50–130. Interpolated UWORD is stored at `FFFF27DC`.
- **Historical correction:** WO64815's `0032,...,0082` axis note was two bytes misaligned because the data row begins at `0x111E8` but the actual pointer is `0x111EA`. Corrected record is in WO65049; no workbook/XML edit made.
- **Identity:** temperature-like input confirmed; coolant plausible but not proven. Adjacent `FFFF84B8` donor temperature evidence belongs to +4 and must not be transferred to +6.
- **Active:** WO65045 remains open for source/sensor identity and separate dashpot-flag linkage.
- **Next:** identify a concrete acquisition/channel mapping that distinguishes `FFFF84B4+4` from `+6`; do not repeat direct/wider/GBR writer scans.
- **Artifact boundary:** only WO65049 and the operational register updated; source files remained read-only.


## sub_70880 sensor-chain predecessor audit — 2026-11-17

- **BOUNDED COMPLETE — CLOSED:** WO65050 — predecessor group A reviewed. No writes/transfers to `FFFF84B4`/`FFFF84BA`; `sub_95C1C` routines read +6 and compare it against constants at GBR+0x26, gating other control outputs. No coolant identity or producer found. See [WO65050](WO65050.md).
- **Parent:** WO65045 remains ACTIVE. WO65046–WO65049 are closed bounded tasks.
- **Artifact boundary:** only WO65050 and this register may be updated. Source files read-only; no workbook, XML, ROM, LST, XREF, IDB, scripts or Library changes.


## WO65050 closeout — 2026-11-17

- **BOUNDED COMPLETE — CLOSED:** `sub_957BA`, `sub_9595C`, `sub_95C1C` predecessor group reviewed. No producer/transfer into `FFFF84B4` found. `sub_95C1C` independently reads `FFFF84BA` at `0x95C8E/0x95D10`, compares it to constants at GBR+0x26 (roots `0x8D36/0x8D37`), and gates writes to other state/output fields.
- **Active:** WO65045 remains open; temperature-like identity for +6 is supported, coolant remains unconfirmed, producer unresolved.
- **Next:** inspect only next sibling pair `sub_961E0` and `sub_968B6` before `sub_969C2`; stop if no concrete acquisition/transfer lead.
- **Artifact boundary:** only WO65050 and the operational register updated; source files remained read-only.


## sub_961E0 targeted sensor source check — 2026-11-17

- **BOUNDED COMPLETE — CLOSED:** WO65051 — `sub_961E0` and direct callees contain no producer/transfer into `FFFF84BA`; `sub_95FB2` and `sub_960A8` add two read-side unsigned threshold comparisons against ROM bytes `0x8D5C/0x8D5D`, gating other state outputs. Temperature-like role reinforced; coolant unresolved. See [WO65051](WO65051.md).
- **Parent:** WO65045 remains ACTIVE; WO65050 predecessor group A is closed.
- **Artifact boundary:** only WO65051 and this register may be updated. Source files read-only; no workbook, XML, ROM, LST, XREF, IDB, scripts or Library changes.


## WO65051 closeout — 2026-11-17

- **BOUNDED COMPLETE — CLOSED:** `sub_961E0` and direct local callees reviewed. No writes/transfers to `FFFF84B4`/ `FFFF84BA`. Two routines read +6 and compare against ROM thresholds `0x8D5C/0x8D5D`, gating separate status/counter outputs.
- **Active:** WO65045 remains open; producer and physical sensor identity unresolved, dashpot link not established.
- **Next:** one isolated check of `sub_968B6` at `0x7087A`, final sibling before `sub_969C2`.
- **Artifact boundary:** only WO65051 and the operational register updated; source files remained read-only.


## sub_968B6 targeted sensor source check — 2026-11-17

- **BOUNDED COMPLETE — CLOSED:** WO65052 — `sub_968B6` and direct callees contain no producer/transfer into `FFFF84BA`; `sub_962B8` reads +6 and converts to `FFFF2150+0x920`; `sub_96412` reads adjacent +3. Separate `sub_9689E` consumer copies +6 to `FFFFA378+0xEE3/+0xE9A`. No coolant identity. See [WO65052](WO65052.md).
- **Parent:** WO65045 remains ACTIVE; WO65051 is closed.
- **Artifact boundary:** only WO65052 and this register may be updated. Source files read-only; no workbook, XML, ROM, LST, XREF, IDB, scripts or Library changes.


## WO65052 closeout — 2026-11-17

- **BOUNDED COMPLETE — CLOSED:** `sub_968B6` and direct callees reviewed. No producer/copy-in to `FFFF84BA`. The chain includes the known +6 conversion consumer and adjacent +3 reader. Separate `sub_9689E` called from `sub_7432C` copies +6 into `FFFFA378+0xEE3/+0xE9A`; this is consumer-side only.
- **Active:** WO65045 remains open. Producer and exact temperature identity unresolved; coolant plausible, not confirmed.
- **Next:** pivot away from the exhausted `sub_70880` sibling chain to a concrete acquisition/caller/interrupt mapping for the `FFFF84B4` structure. Do not repeat direct/wider/GBR or sibling-chain scans.
- **Artifact boundary:** only WO65052 and the operational register updated; source files remained read-only.


## FFFF84BA literal ROM-pointer check — 2026-11-17

- **BOUNDED COMPLETE — CLOSED:** WO65053 — supplied scan found no even-offset big-endian literal pointer to `FFFF84BA` in ROM. The scan used a 2-byte step; odd offsets were not tested. This does not exclude calculated/indirect references or establish absence of a producer. See [WO65053](WO65053.md).
- **Parent:** WO65045 remains ACTIVE for producer provenance, sensor identity, and dashpot linkage.
- **Artifact boundary:** only WO65053 and this register updated. Pointer-search result was supplied by user from Claude; not independently rerun. All source files remain read-only.


## WO65045 caller-path mapping — 2026-11-17

- **BOUNDED COMPLETE — checkpoint 2 (parent remains ACTIVE):** NEXT6_16 listing maps `0x707CC → sub_77608 → 0x784F6/sub_79A78 → 0x79C92/sub_7A204`. `sub_79A78` reads `FFFF84BA` against ROM threshold `0x8ED7` and selects `0x893F/0x8940`; `sub_7A204` has four further `FFFF84BA` reads compared with `0x32` in counter-update branches. Same `sub_79A78` span reads `FFFF860B.bit3` and adjacent `FFFF860F.bit3`, compares their boolean states, but does not write `FFFF860B`; `sub_7A204` has no `FFFF860B` reference. Task-level caller path confirmed; interrupt cadence/acquisition source unresolved. No direct linkage established. See [WO65045](WO65045.md), checkpoint 2.
- **Report verification:** WO65045 content SHA `7a2b24d47c0d7037d40153cec480c6b45e56c78b` (readback verified).
- **Next:** parent remains ACTIVE; pivot only to a new concrete acquisition/descriptor/interrupt lead. Do not repeat this caller path or prior writer/sibling-chain scans.
- **Artifact boundary:** only WO65045 and this operational register updated. NEXT6_16 listing read-only; no workbook, XML, ROM, LST, XREF, IDB, scripts or Library modifications.


## WO65054 — indirect sensor-acquisition path for FFFF84BA — 2026-11-17

- **ACTIVE — PARKED:** original `0x16DA4` → `FFFF84BB` / `0x20C7E` indirect-dispatch trace is paused while WO65055 resolves the newly identified table/descriptor consumers. WO65054 is not closed; resume only if WO65055 establishes a direct connection or reaches its bounded stop.
- Reuse completed direct/GBR writer, sibling-chain, caller-path, and literal-pointer checks. No global writer scan or repeated FC90/111EA work.
- Stop at the first unresolved dispatch/peripheral/DMA boundary if no concrete source is found.
- **Artifact boundary:** only WO65054 and this register may be updated; source artifacts, XML, workbook and Library remain read-only. See [WO65054](WO65054.md).


## WO65055 — acquisition-table and ADC descriptor mapping — 2026-11-17

- **BOUNDED COMPLETE — CLOSED:** sub_24EA8 (0x24EA8–0x24F40) copies 0x448 bytes / 274 BE32 entries from ROM 0x16CD0–0x17117 into RAM FFFFB61C–FFFFBA63. ROM 0x16DA4 value FFFF84BB lands at RAM FFFFB6F0 (offset +0xD4). No consumer of FFFFB6F0 was found in the bounded pass.
- The 0x13B50 records contain ADC-register-address patterns (ADCR0_B, ADCSR0_B, ADDR7H/8H/10H/11H), but the reviewed direct consumers of dword_13B44 read only its +0/+4/+8 prefix. No consumer of the descriptor-like records or link to FFFF84BA was established. Sensor identity and producer remain unresolved.
- WO65054 remains PARKED, not closed; parent WO65045 remains ACTIVE. No follow-on WO was started.
- See [WO65055](WO65055.md). Only WO65055 and this register were updated; source artifacts, XML, workbook and Library remained read-only.

