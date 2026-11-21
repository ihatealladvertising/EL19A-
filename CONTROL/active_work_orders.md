# EL19A — Operational Control and Work-Order Register

**Operational authority:** This file is the sole current source of truth for work-order lifecycle, assignments, priorities, continuation, and handoff. Technical evidence belongs in individual `WO<ID>.md` records.
**Repository:** `ihatealladvertising/EL19A-` · **Authority branch:** `main` · **Updated:** 2026-11-21
**Update rule:** Re-read the latest authoritative register before each change. Make one minimal register update per commit and verify it by readback. Do not maintain a parallel operational notebook.
**History:** The full pre-compaction register from this branch is preserved in [the 2026-11-20 archive snapshot](active_work_orders_archive_2026-11-20.md). It is historical only. Later base-branch updates are summarized below; their technical details are in the individual WO records.

## Concurrency protocol

- Before starting concurrent work, the coordinator checks the latest register and available branches, allocates a unique WO ID, records its assignment, and commits that reservation.
- Investigations may proceed in parallel. Each worker edits only its assigned `CONTROL/WO<ID>.md`; workers do not edit the shared register. Send the coordinator a concise checkpoint/status proposal for registration.
- The coordinator alone updates `active_work_orders.md`, against the latest authoritative version, one status/checkpoint transaction per commit. Do not combine concurrent proposals into a stale full-file replacement.
- After each commit, read back the register and verify the new status/checkpoint and all concurrent assignments remain present. Never resolve a conflict by discarding another worker's entry.
- Keep lifecycle, owner, priority, latest checkpoint, and next action here. Put detailed findings and superseded checkpoints in the WO record or dated archive.

## Current operational frontier

- **Current workbook:** `WORKBOOK/EL19A_Master_Reverse_Engineering_Workbook_V57_WO65003_WO65045_ProcessReconciliation_2026-11-18.xlsx` (149 sheets).
- **Current XML baseline:** `public/assets/aistudio/EL19A_merged_definition_v3_08a300db.xml` (`EL19A_Merged_Spec_v3`: 76 tables, 7 verified and 69 `[S]`) plus `EL19A_ignition_decoded_fragment_33ea8e67.xml` (6 ignition/knock tables).
- **Discovery staging:** `CALIBRATIONS/discovered_tables_catalog.csv` (179 helper/reader-verified varying tables absent from XML v3).
- **Concurrent WOs:** none active. WO65085–WO65089 are closed bounded-complete (2026-11-21); the user authorized concurrent execution on 2026-11-20.

## Active work

| WO | Status / priority | Latest checkpoint and continuation |
|---|---|---|
| WO65090 | **CLOSED — BOUNDED COMPLETE** | ROM `0x829A–0x829F` signed scalar/clamp cluster traced; carried forward direct boundaries `0x913A/0x913C`, `0x91C2/0x91C4/0x91C6`, `0x97B2`. Extracted and raw-ROM-verified 197 DTC-like records (`0x12E44–0x1377F`, stride `0x0C`, U16BE code at `+6`) and 144 unique CID-like records (`0x14664–0x148A3`, stride 4, U16BE + `00 FF`). No physical semantics or workbook/XML integration. Evidence: [WO65090](WO65090.md), PR [#8](https://github.com/ihatealladvertising/EL19A-/pull/8). |







## Recent completed work

- [WO65089](WO65089.md) — **BOUNDED COMPLETE — CLOSED:** traced three 3D groups and three 32-point UWORD curve groups through caller inputs, branch selection, helper return, RAM staging and first direct consumers. `0x0A342/0x0A382` are a bit7-selected UBYTE response pair; `0x0D8D6` is a centered UWORD correction surface; `0x0B422/0x0B4A2/0x0B522/0x0B5A2` are four same-index SWORD correction channels; `0x0F712/0x10F8A` form a bidirectional transfer pair; `0x10EEA/0x1100A` and `0x10F2A/0x1104A` form a range-selected two-piece UWORD transfer used multiplicatively. Software-role confidence high; physical domain/units unresolved. No workbook/XML/catalogue edit.
- [WO65088](WO65088.md) — **BOUNDED COMPLETE — CLOSED:** traced the two UWORD ceiling inputs from WO65087. `FFFF3366` has two direct stores in `sub_685A6` (`0x68614`, `0x686CA`); the first stores `min(UWORD[FFFF9932], UWORD[FFFF9936])` when `FFFF1E64.bit6` and `FFFF1E6C.bit7` are clear, and the alternate writer caps a candidate by `FFFF336C`. Exact-offset reader: `0x686F6`. Twenty literal-root loads of `FFFF9858` were verified; bounded paths are reads/adjacent-field accesses, with no direct UWORD writer found. No copy/common-source path established; computed aliases/runtime/DMA routes remain unresolved. No units; no workbook/XML/catalogue edit.
- [WO65087](WO65087.md) — **BOUNDED COMPLETE — CLOSED:** followed WO65086's 1000/800 pair to its use. Both sites apply the same operation — `min(value, 1000 | 800)` — as a **ceiling** selected by `0x8405` bit 0 (`06521A` `cmp/gt r2,r13` in `sub_65174`; `0687A0` `cmp/gt r2,r5` in `sub_685A6`), then convert the capped value by an identical `×727` (`0x2D7`) `÷800` (`0x2D7+0x49`) sequence through `sub_21BE4`, confirmed as a division (`div0u`/8×`div1`/`rotcl`). Capped value stored at `FFFF9916+0x18`/`+0xB4`, quotient at `FFFF2F00+0x468`. The bounded quantity is a runtime word (`FFFF2F00+0x466` / `FFFF9858`) minus 14 (`word[0x942E]`=8 plus 6), clamped at 0; max converted output is 908 (bit set) or 727 (clear). No units; no workbook/XML/catalogue edit. Follow-up completed by [WO65088](WO65088.md): two direct writer paths for `FFFF3366`; no direct UWORD writer established for `FFFF9858` within bounded literal-root methods.
- [WO65085](WO65085.md) — **BOUNDED COMPLETE — CLOSED:** completed the bit-7 gate-B trace and corrected WO65084's PC `0x6F6B8` attribution (`sub_6F69E`, not `sub_6F5E8`). Both selected ROM UWORDs (`0x965C`, `0x1171E`) are `0x8000`; bit-clear routes read UBYTE `FFFF2462` and query `FFFF84EA` through different helpers. Outputs stage at `FFFF1000` and `FFFF1026`, reaching distinct direct consumers (`sub_22D30` vs `sub_230B0`); no common consumer established within scope. `0x1171E` is one field in mixed constant data, not a proven table. No units; no workbook/XML/catalogue integration.
- [WO65086](WO65086.md) — **BOUNDED COMPLETE — CLOSED:** classified all twelve `0x8405` bit-0 sites: two select the same default pair — 1000 (`0x3E8`) with the bit set, 800 (`0x320`) clear — at `06519C` (`sub_65174`, override `FFFF35C8+0x53` bit 2) and `0686E2` (`sub_685A6`, override `FFFF3616+5` bit 2); four run an update block only when the bit is clear (`03652A`, `06CF80`, `06CFC6` — which publishes bit 2 of the `FFFF34C8` status byte — `06D420`); five run a staged computation only when it is set (`06E1DE`, `06E300`, `06FB0A`, `06FC08`, `06FD9E`); one consumes the bit as data (`06EDCE`). No single mechanical meaning; the 1000/800 pair is the only cross-site identity. Shipped `0x8405 = 0x0C` means the five set-only bodies and both 1000 choices are inactive in this calibration. No units; no workbook/XML/catalogue edit. Next: writer of `FFFF34C8` bit 2 and of the two override cells.
- [WO65084](WO65084.md) — **BOUNDED COMPLETE — CLOSED:** completed the `0x8405` option-byte gate inventory: 21 load sites, bit 0 ×12, bit 1 ×4, bit 7 ×2, bits 2/5/6 ×1, **bits 3 and 4 never tested**; shipped value `0x0C` (`0x8404–0x8407` = `07 0C 1E 03`, bit 3 set but unread). Worked gates: bit 0 selects 1000 (`0x3E8`) vs 800 (`0x320`) in `sub_685A6` with a `FFFF3616+5` bit-2 override; bit 7 selects ROM scalars `0x965C` / `0x1171E` (trust bank) over `FFFF2150+0x312`-staged values, refining WO65080's "no bank selector" negative; bit 2 publishes GBR bit `0x20` in `sub_2BEAC`. No units; no workbook/XML/catalogue edit. Gate-B follow-up completed by [WO65085](WO65085.md), which also corrected the `0x6F6B8` function attribution; its distinct downstream consumers are documented there.
- [WO65083](WO65083.md) — **BOUNDED COMPLETE — CLOSED:** completed the bounded literal-pool first-access census over ROM `0x7800–0x94FF` (3,663 first accesses from 3,962 literal-pool roots), classified repeated constants and traced direct UWORD comparison boundaries 78/956 and 60/964/1000. `0x9220`=10 is a count/record guard candidate; `0x90CC`=0x7FFF is generic saturation; `0x934C`=100 is an arithmetic bias. No units or calibration semantics assigned; no workbook/XML/catalogue integration.

- [WO65062](WO65062.md) — **BOUNDED COMPLETE — CLOSED:** completed the targeted byte/bit access slice for FFFF85C4–FFFF85FF and FFFF860B–FFFF860F, corrected indexed/GBR/call-boundary cases, and classified all five FFFF85E4 writers. Static loc_1D64 copy capability and HCAN1 buffer producer are documented; actual runtime packet/destination and post-relocation VBR slots remain unproven. No exhaustive whole-ROM or semantic claim; no workbook/XML/catalogue integration.

- [WO65064](WO65064.md) — **BOUNDED COMPLETE — CLOSED:** completed the 0x9700–0x9800 absolute-pointer UWORD census, the 0x9500–0x9600 25-candidate operand provenance, the 0x9600–0x9700 54-candidate operand provenance, and the 0x9800–0x9B00 multi-width census. Corrected candidate classification: 42 direct compare sites, 7 helper-input/coefficient uses, 5 constant/tautological comparisons; no units or semantic map identity assigned. The 7500/6700/7200 record chain remains as two clamp stages plus a distinct zero-gate default. No workbook/XML/catalogue integration.

- [WO65065](WO65065.md) — **BOUNDED COMPLETE — CLOSED:** traced the immediate counter-writer caller chain; identified `FFFF93F2` descriptor and `FFFF937C/FFFF937E` source initialization in `sub_90384`; a separate read of `FFFF937E` occurs at `0x9D930`. Runtime source updates and scheduler cadence remain unresolved; no workbook/XML/catalogue integration.
- [WO65066](WO65066.md)–[WO65069](WO65069.md) — **BOUNDED COMPLETE — RECOVERED TO MAIN (2026-11-21):** restores four closed technical records from detached concurrent-work branches; original findings, evidence limits, and non-integration dispositions are preserved in their individual records. No ROM/LST/XML/script/workbook artifact was changed.

- [WO65082](WO65082.md) — **BOUNDED COMPLETE — CLOSED:** corrected the premise that `0x12844` is a single calibration table. LST labels it `byte_12844`; sampled code treats it as a heterogeneous ROM data/configuration block with fixed-offset byte-field reads, a GBR base (`0x31DBA`), and a byte-indexed lookup (`0x33244`). The inherited 35-helper-argument claim was not independently reproduced; exact per-call helper use and embedded arrays at/after `0x1289C` remain unresolved. No workbook/XML/catalogue edit.

- [WO65081](WO65081.md) — **BOUNDED COMPLETE — CLOSED:** corrected WO65080's effective-address attribution. All six exact code-use sites for offsets `0x732`/`0x6D0` resolve through base `FFFF1054`, yielding `FFFF1786`/`FFFF1724`; none of the cited accesses target `FFFF2150+0x732/+0x6D0`. WO65080's proposed consumer trace is superseded. No workbook/XML/catalogue edit.

- [WO65080](WO65080.md) — **BOUNDED COMPLETE — CLOSED:** the `0x11700–0x13000` bank is consumed as a table set with its own axes, not a passive duplicate: 183 helper-argument loads (131 trust-range over 38 distinct addresses, 52 to the 18 normal mirrors), only 15/18 trust twins and 17/18 normal twins reached (`0x10CE2` never loaded). Where both banks appear in one routine (`sub_69496`, `sub_68C28`) the results land in different `FFFF2150` cells — parallel evaluation, not a selector or an in-place monitor comparison. ROM `0x8405` bit 2 gates compute-vs-reuse at `sub_703A8` (`0x104EC` path vs cached `FFFF1D12+0x60`) and `loc_704D0` (trust `0x11744`/`0x12B0E` vs cached `FFFF1054+0x73C`), not normal-vs-trust. No units, no workbook/XML/catalogue edit. Next: classify the `0x12844` mixed ROM data/configuration block and separately verify any embedded calibration arrays or actual helper arguments. The proposed consumer trace of `FFFF2150+0x732/+0x6D0` is superseded by [WO65081](WO65081.md); the `0x12844` geometry premise is corrected by [WO65082](WO65082.md).
- [WO65079](WO65079.md) — **BOUNDED COMPLETE — RECOVERED TO MAIN:** restored the stranded evidence record. No direct read of byte output `FFFF1130` was established by exact-address, GBR+`0xDC`, or fixed `Rn+0xDC` methods. Four `GBR+0xDC` reads resolve to `FFFFB584`, `FFFF2E08`, and `FFFF359D`; none target `FFFF1130`. Computed/inherited aliases remain untested.
- [WO65078](WO65078.md) — **BOUNDED COMPLETE — CLOSED:** traced B956 (`0x0B956`) in `sub_969C2`: UWORD query `FFFF8494` is zero-extended into R7; map/axis pointers are `0x0B956/0x10994/0x0FDAC`; helper return is stored unchanged at `FFFF27DE`. WO65070's direct copy to `FFFF9C48` is reused. Second stack query, physical meaning/units and cadence remain unresolved.


- [WO65077](WO65077.md) — **BOUNDED COMPLETE:** no direct read of the validated DTC block `0x12E44–0x1377F` was established by exact-address/proven-literal methods. The sole in-range literal at `0x70650` loads numeric `0x1312D` into register arithmetic, then stores a capped UWORD to `FFFF1400` and a derived byte to `FFFF1130`; it does not dereference the DTC block. Computed/indirect paths remain untested.
- [WO65076](WO65076.md) — **BOUNDED COMPLETE — CLOSED:** traced five direct readers of weighted C756/C956 result `FFFF156A`: secondary blend endpoint with `FFFF156C` into `FFFF1578`; difference input to `sub_22494`; selector-dependent staging into `FFFF157A`; and signed-saturating arithmetic feeding `FFFF156E`/`FFFF1576`. Physical meaning/units remain unresolved; no workbook/XML/catalog integration.


- [WO65075](WO65075.md) — **BOUNDED COMPLETE:** no post-stage direct UWORD read of `FFFF9C48` was established by exact-address/proven `FFFF9C10+0x38` methods; the verified read at `0x96D96` precedes the new store at `0x972E0` and is prior state. Three inherited-GBR byte sites remain unresolved possible aliases; no broader xref or semantic identity assigned.
- [WO65071](WO65071.md) — **BOUNDED COMPLETE:** C0D6's gated UWORD at `FFFF2936` is directly consumed and contributes to a derived U32 staged at `FFFF2930`. Corrected WO65067's attribution: `FFFF1D62` is a blend selector/weight; the weighted result is stored at `FFFF156A`.
- [WO65070](WO65070.md) — **BOUNDED COMPLETE:** B956's UWORD staged at `FFFF27DE` is directly read and copied to `FFFF9C48`; no semantic name or downstream consumer was assigned.
- [WO65072](WO65072.md) — **BOUNDED COMPLETE:** `FFFF2BC0` and `FFFF2BC2`, read against threshold 100, are written from `FFFF937C/+2` by saturating-increment or alternate `IVECT1` paths in `sub_8CF66`. The upstream state sources and units remain unresolved.
- [WO65073](WO65073.md) — **BOUNDED COMPLETE — DOCUMENTATION ONLY:** preserves the user-provided stranded WO65064 update with explicit source attribution and verification limits; no ROM re-analysis or semantic promotion.
- [WO65074](WO65074.md) — **BOUNDED COMPLETE:** traced the 7,500 and conditional 6,700 UWORD ceilings in `sub_5919A` across two parallel channels; selected pair is written to MMIO `FFFF33E6/FFFF33E8`. Physical units and peripheral function unresolved.
- [WO65063](WO65063.md) — **BOUNDED COMPLETE:** `FFFF8684` is mutable byte state despite reset vector-like fill; `FFFF889C` has reset fill and no later overwrite established by bounded pointer-root review. Runtime packet destination, live slot values and VBR/exception ordering remain unresolved at explicit stop boundary.
- [WO65061](WO65061.md) — **CLOSED — BOUNDED COMPLETE:** resolved the stale-GBR false alias and verified the bounded `FFFF85DF` reader set; the historical false-positive origin remains unrecovered.
- [WO65020](WO65020.md) — **BOUNDED COMPLETE — CLOSED:** supplemental alias audit for the `FFFF85FC` TRAPA slot; see WO65063 checkpoint 3 for the bounded dependency result.
- WO65045 is **CLOSED — BOUNDED COMPLETE** by WO65056/65059; WO65054 is **CLOSED**, superseded by WO65056. Detailed recent results remain in their individual WO records.

## Guardrails and future priorities

- Do not repeat the completed `FFFF84BA` direct/wider/GBR/sibling-chain/ROM-pointer checks; the closed helper-family censuses; the `FFFF860D.bit3` writer search; or the `FFFF1018` reader/DMA/DTC checks. See the relevant WO records and archive for exact method boundaries.
- **Unassigned candidates after the active WOs close:** a 1D scalar/limiter sweep (`0x7800–0x9B00`, plus DTC/CID extraction) or a bounded semantic caller trace for high-priority WO65060 map families. These are recommendations only, not active assignments.
- Historical WO summaries and checkpoint details are preserved in the dated archive snapshot and individual WO records; neither expands an active WO's scope.






