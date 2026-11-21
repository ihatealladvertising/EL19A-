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
- **Concurrent WOs:** WO65062, WO65064, and WO65065 are active under the user's concurrent-execution authorization of 2026-11-20/21. Their scopes remain separate.

## Active work

| WO | Status / priority | Latest checkpoint and continuation |
|---|---|---|
| [WO65062](WO65062.md) | **ACTIVE — P1** | Checkpoint 19a: conditional HCAN1 receive/buffer path and range-validated copy capability are documented. No runtime packet, destination, or target write is established. Continue only within the WO's methods and stop conditions; no exhaustive-access claim or semantic promotion. |

| [WO65064](WO65064.md) | **ACTIVE — P1** | Checkpoint 4 adds the `0x9500–0x9600` census (86 word loads, 63/128 slots, 25 compare-on-loaded candidates after an operand check that rejected 15) and resolves the 7500/6700 pairing: in `sub_5919A`, 7500 (`0x987E`) caps the record values at `GBR+0x74/+0x76` and 6700 (`0x97AE`) is a second, flag-gated cap on their copies at `+0x6C/+0x6E`, while 7200 (`0x9588`) is the zero-gate default for `+0x94/+0x96`; `0x95A0`=7500 is confirmed reached and never compared. No units assigned. Next: operand provenance for the 25 `0x9500–0x9600` candidates, then the `0x9600–0x9700` set. |
| [WO65065](WO65065.md) | **ACTIVE — P1** | Checkpoint 1 identifies `sub_8CF66` as the writer of UWORDs `FFFF2BC0/FFFF2BC2`, incremented with `0xFFFF` saturation or zeroed by descriptor gates. Source-field/descriptor producers and cadence remain unresolved; continue only its assigned scope. |


## Recent completed work


- [WO65079](WO65079.md) — **BOUNDED COMPLETE:** no direct read of byte output `FFFF1130` was established by exact-address, GBR+`0xDC`, or fixed `Rn+0xDC` methods. Four `GBR+0xDC` reads resolve to `FFFFB584`, `FFFF2E08`, and `FFFF359D`; none target `FFFF1130`. Computed/inherited aliases remain untested.
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






