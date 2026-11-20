# EL19A — Operational Control and Work-Order Register

**Operational authority:** This file is the sole current source of truth for work-order lifecycle, assignments, priorities, continuation, and handoff. Technical evidence belongs in individual `WO<ID>.md` records.
**Repository:** `ihatealladvertising/EL19A-` · **Authority branch:** `main` · **Updated:** 2026-11-20
**Update rule:** Re-read this file immediately before each update, make a minimal targeted change, commit, and verify the resulting revision. Do not maintain a parallel operational notebook.
**History:** The full prior register is preserved in [the 2026-11-20 archive snapshot](active_work_orders_archive_2026-11-20.md). That snapshot is historical only and does not determine current status.

## Concurrency protocol

- Work orders may be investigated concurrently; allocate each WO ID once before work begins.
- Each worker edits only its own `WO<ID>.md`. Do not concurrently edit this register.
- A coordinator allocates IDs and serializes register changes against the latest version, keeping only current status, assignment, priority, latest checkpoint, and next action here. Put detailed findings and superseded checkpoints in the WO record.
- Verify the register update after commit. Never replace the file from a stale copy or resolve a conflict by discarding another worker's entry.

## Current operational frontier

- **Current workbook:** `WORKBOOK/EL19A_Master_Reverse_Engineering_Workbook_V57_WO65003_WO65045_ProcessReconciliation_2026-11-18.xlsx` (149 sheets).
- **Current XML baseline:** `public/assets/aistudio/EL19A_merged_definition_v3_08a300db.xml` (`EL19A_Merged_Spec_v3`: 76 tables, 7 verified and 69 `[S]`) plus `EL19A_ignition_decoded_fragment_33ea8e67.xml` (6 ignition/knock tables).
- **Discovery staging:** `CALIBRATIONS/discovered_tables_catalog.csv` (179 helper/reader-verified varying tables absent from XML v3).

## Active work

| WO | Status / priority | Scope and continuation |
|---|---|---|
| [WO65062](WO65062.md) | **ACTIVE — P1** | Bounded RAM byte/bit xref slice for `FFFF85C4–FFFF85FF` and `FFFF860B–FFFF860F`, with local GBR/function-state provenance. Latest checkpoint: 19a; the conditional HCAN1 receive/buffer path and range-validated copy capability are documented, but no runtime packet, destination, or target write is established. Continue only within the WO's methods and stop conditions; no exhaustive-access claim or semantic promotion. |

## Recent completed work

- [WO65071](WO65071.md) — **BOUNDED COMPLETE:** C0D6's gated UWORD at `FFFF2936` is directly consumed and contributes to a derived U32 staged at `FFFF2930`. Corrected WO65067's attribution: `FFFF1D62` is a blend selector/weight; the weighted result is stored at `FFFF156A`.
- [WO65070](WO65070.md) — **BOUNDED COMPLETE:** B956's UWORD staged at `FFFF27DE` is directly read and copied to `FFFF9C48`; no semantic name or downstream consumer was assigned.
- [WO65061](WO65061.md) — **CLOSED — BOUNDED COMPLETE:** resolved the stale-GBR false alias and verified the bounded `FFFF85DF` reader set; the historical false-positive origin remains unrecovered.
- WO65045 is **CLOSED — BOUNDED COMPLETE** by WO65056/65059; WO65054 is **CLOSED**, superseded by WO65056. Detailed recent results remain in their individual WO records and the archive snapshot.

## Guardrails and future priorities

- Do not repeat the completed `FFFF84BA` direct/wider/GBR/sibling-chain/ROM-pointer checks; the closed helper-family censuses; the `FFFF860D.bit3` writer search; or the `FFFF1018` reader/DMA/DTC checks. See the archive snapshot and linked WOs for exact method boundaries.
- **Unassigned candidates after WO65062 closes:** a 1D scalar/limiter sweep (`0x7800–0x9B00`, plus DTC/CID extraction) or a bounded semantic caller trace for high-priority WO65060 map families. These are recommendations only, not active assignments.
- Historical WO summaries and checkpoint details are retained in the dated archive snapshot; each WO's technical report is the primary evidence for its findings.
