# Work Order Status — Reconciled Migration Snapshot

**Snapshot date:** 2026-11-15

## Current chat continuation
- **WO64825 — E974 Output-Chain Investigation** (Agent: Grok) is the active task. Status advanced from BLOCKED to **PARTIAL** after annotated LST became available.

## WO64825 register entry (2026-11-15, updated)
- **WO ID / Title:** WO64825 — E974 Output-Chain Investigation
- **Agent:** Grok
- **Status:** PARTIAL
- **Completion date (this checkpoint):** 2026-11-15
- **Findings (instruction-level from annotated LST):**
  - **Callsite 1 (`0x3BB1A` / `sub_3BA88`):** GBR=`FFFF1E54`; query = `(FFFF85C4+0x12)>>1` clamped; result → `GBR+0xB8` (`FFFF1F0C`); read-back `0x3BBE4`; non-zero gates `sub_223FE` path. Confirmed.
  - **Callsite 2 (`0x3C042` / `sub_3BFC8`):** identical GBR and query construction; result → `GBR+0xB9` (`FFFF1F0D`); read-back `0x3C104`; likewise gates `sub_223FE`. Confirmed. Paired with callsite 1.
  - **Callsite 3 (`0x4130E` / `sub_412B8`):** distinct GBR=`FFFF1D80`; query from `FFFF859C+0x12`; result → `FFFF1F0E`; local read-back and bit tests only; no shared `sub_223FE` path observed. Confirmed distinct.
- **Evidence addresses:** `0xE974`, `0x3BB1A`, `0x3BB32`, `0x3BBE4`, `0x3BC0E`, `0x3C042`, `0x3C052`, `0x3C104`, `0x3C118`, `0x4130E`, `0x41318`, `0x41330` (annotated LST).
- **Confidence:** confirmed for the three chains up to `sub_223FE` gating / local status; unresolved beyond that point.
- **Decisions / corrections:** First two callsites are paired; third is independent. No semantic or XML promotion. No Workbook/Notebook edit performed by this agent.
- **Unresolved endpoints:** full dataflow and purpose of `sub_223FE`; later consumers of `FFFF1F0C`/`FFFF1F0D` under other GBR bases; query-word producers; any actuator/peripheral endpoint.
- **Dependencies / recommended next:** (1) bounded trace of `sub_223FE` from the two known call sites; (2) bounded XREF of the two result bytes outside the current GBR context.
- **Artifact locations:** this CONTROL file; chat report of 2026-11-15; source LST `EL19A_Complete_Disassembly_ANNOTATED_V3_NEXT6_WO64683_64684_CHECKPOINT_2026-11-11.lst`.
- **Integration note:** Investigation PARTIAL. Master Workbook / Control Notebook integration still pending explicit request.

## Durable / historical snapshots
- **V53 checkpoint:** WO64817 PARTIAL/PAUSED at CP16; WO64819 ACTIVE (PAIR-01); WO64820/WO64821 QUEUED; WO64816/WO64818 PARTIAL/PAUSED; WO64795 proposed/not issued.
- **Later Library Notebook snapshot (2026-11-15 17:55):** WO64822 ACTIVE for broad calibration harvesting; WO64819 PAUSED after CP18; WO64820/WO64821 queued/deferred; WO64817/WO64816/WO64818 paused. V53 remains the master pointer.
- The later Library snapshot's WO64822 CP02 notes:
  - E974: three `sub_22E10` callsites at PCs `0x3BB1A`, `0x3C042`, `0x4130E`; query `min(FFFF85D6 >> 1, 255)`; outputs GBR+0xB8/+0xB9 and `FFFF1F0E`.
  - EE08/EE28: cascade/selector path in `sub_3BEA6` / `sub_3F3C6`, selector bit `0x40`, output `FFFF1054+0x3CC`.
  - F33E–F36E: shared `FFFF84B8` query; source unresolved. Do not repeat source-path scans already completed under WO64819.
- **WO64819 CP18:** user cancelled the bounded CP18 investigation. `FFFF37AE` (+0x90 from `FFFF371E`) remained unresolved; later Library snapshot records the WO paused at CP18. Do not reopen without explicit request and a concrete new lead.

## Control-source limitation
Stable Control Notebook item: `F6DEFBD470240AE6!sac2dd9024e574ee3a7462a1730baeddd`. Exact OneDrive fetch returned 403 `serviceReadOnly` during migration. Treat V53, Library Notebook copies and chat context as separately sourced snapshots; do not silently merge them.

## Next reconciliation requirement
When the exact stable Notebook becomes readable, compare its `CONTROL`, standing instructions, work-order ledger, latest continuation and V53 pointer against this file. Update this file only from verified current state. No WO allocation or lifecycle mutation is implied by this migration.
