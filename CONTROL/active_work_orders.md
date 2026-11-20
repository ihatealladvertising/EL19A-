# EL19A — Operational Control and Work-Order Register

**Operational authority:** This file is the sole current source of truth for work-order lifecycle, assignments, priorities, continuation, and handoff. Technical evidence belongs in individual `WO<ID>.md` records.
**Repository:** `ihatealladvertising/EL19A-` · **Authority branch:** `main` · **Updated:** 2026-11-20
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
- **Concurrent WOs:** WO65062, WO65063, and WO65064 are active under the user's concurrent-execution authorization of 2026-11-20. Their scopes remain separate.

## Active work

| WO | Status / priority | Latest checkpoint and continuation |
|---|---|---|
| [WO65062](WO65062.md) | **ACTIVE — P1** | Checkpoint 19a: conditional HCAN1 receive/buffer path and range-validated copy capability are documented. No runtime packet, destination, or target write is established. Continue only within the WO's methods and stop conditions; no exhaustive-access claim or semantic promotion. |
| [WO65063](WO65063.md) | **ACTIVE — P1** | Checkpoint 3 closes the WO65020 dependency: `FFFF85FC–FFFF85FF` is reused as mutable state, not established as a stable vector. Continue only the assigned `FFFF8684`/`FFFF889C` slot trace; current handler values remain unresolved. Next useful evidence is a proven runtime packet/destination or independent `FFFF85FC` handler/VBR-return path. |
| [WO65064](WO65064.md) | **ACTIVE — P1** | Checkpoint 2 traced operand provenance for six flagged gates in `0x9700–0x9800`; only `0x97B2` is a true threshold, on adjacent counters. Continue with the neighboring `0x9600–0x9700` and `0x9800–0x9B00` windows and the WO's listed open producers. Do not repeat the completed absolute-pointer census or six-gate trace. |

## Recent completed work

- [WO65071](WO65071.md) — **BOUNDED COMPLETE:** C0D6's gated UWORD at `FFFF2936` is directly consumed and contributes to a derived U32 staged at `FFFF2930`. Corrected WO65067's attribution: `FFFF1D62` is a blend selector/weight; the weighted result is stored at `FFFF156A`.
- [WO65070](WO65070.md) — **BOUNDED COMPLETE:** B956's UWORD staged at `FFFF27DE` is directly read and copied to `FFFF9C48`; no semantic name or downstream consumer was assigned.
- [WO65072](WO65072.md) — **BOUNDED COMPLETE:** `FFFF2BC0` and `FFFF2BC2`, read against threshold 100, are written from `FFFF937C/+2` by saturating-increment or alternate `IVECT1` paths in `sub_8CF66`. The upstream state sources and units remain unresolved.
- [WO65061](WO65061.md) — **CLOSED — BOUNDED COMPLETE:** resolved the stale-GBR false alias and verified the bounded `FFFF85DF` reader set; the historical false-positive origin remains unrecovered.
- [WO65020](WO65020.md) — **BOUNDED COMPLETE — CLOSED:** supplemental alias audit for the `FFFF85FC` TRAPA slot; see WO65063 checkpoint 3 for the bounded dependency result.
- WO65045 is **CLOSED — BOUNDED COMPLETE** by WO65056/65059; WO65054 is **CLOSED**, superseded by WO65056. Detailed recent results remain in their individual WO records.

## Guardrails and future priorities

- Do not repeat the completed `FFFF84BA` direct/wider/GBR/sibling-chain/ROM-pointer checks; the closed helper-family censuses; the `FFFF860D.bit3` writer search; or the `FFFF1018` reader/DMA/DTC checks. See the relevant WO records and archive for exact method boundaries.
- **Unassigned candidates after the active WOs close:** a 1D scalar/limiter sweep (`0x7800–0x9B00`, plus DTC/CID extraction) or a bounded semantic caller trace for high-priority WO65060 map families. These are recommendations only, not active assignments.
- Historical WO summaries and checkpoint details are preserved in the dated archive snapshot and individual WO records; neither expands an active WO's scope.
