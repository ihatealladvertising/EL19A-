# Work Order Status — Reconciled Migration Snapshot

**Snapshot date:** 2026-11-15

## Current chat continuation
- **WO64827 — E974 Downstream Gating and Consumer XREF Investigation** (Agent: Grok) is the active task. Status: **PARTIAL**.
- Prior WO64825 remains PARTIAL and is the direct predecessor.

## WO64827 register entry (2026-11-15)
- **WO ID / Title:** WO64827 — E974 Downstream Gating and Consumer XREF Investigation
- **Agent:** Grok
- **Status:** PARTIAL
- **Investigation date:** 2026-11-15
- **Depends on:** WO64825 (PARTIAL)
- **sub_223FE findings:**
  - Pure arithmetic helper: R0 ← (signed) R0 >> 6. Five `shar` + delay-slot `shar` after `rts`.
  - No RAM access, no side effects, no branches.
  - Does **not** read `FFFF1F0C` or `FFFF1F0D`.
  - Confidence: confirmed.
- **Paired result paths:**
  - Both `FFFF1F0C` (`0x3BBE4`) and `FFFF1F0D` (`0x3C104`) act solely as boolean enable gates (`tst` / `bt`).
  - Value actually scaled by `sub_223FE` is the word at `FFFF8594+2` (extu.w).
  - Post-scale comparison against a threshold derived from ROM + other bytes; then local status-bit updates on the `FFFF1E54` object.
  - Paths converge on the same helper and operand; remain distinct only in the status bits they affect.
  - Confidence: confirmed.
- **Additional XREF consumers (bounded, same GBR object):**
  - Further enable-style reads of `+0xB8` / `+0xB9` under GBR=`FFFF1E54` in the `0x55xxx` region (`0x5599A`, `0x55A24`, `0x55C82` and nearby).
  - These feed multi-condition aggregators that write status fields on the same object and related bases (`FFFF2150` family).
  - Other `@(h'B8/B9,gbr)` sites exist under different GBR roots and were not expanded.
  - Confidence: confirmed for presence and enable role; moderate for exact aggregation semantics.
- **Furthest confirmed downstream endpoints:**
  - Enable decision admitting a scaled comparison of `(FFFF8594+2)>>6`.
  - Local status-bit updates on the `FFFF1E54` object.
  - No actuator / timer-output / peripheral write linked from these two bytes in the examined windows.
- **Decisions / corrections:** E974 paired outputs are enable gates only, not numeric inputs to `sub_223FE`. No semantic or XML promotion. No Workbook / Notebook edit.
- **Unresolved / blockers:** producer and meaning of `FFFF8594+2`; full consumer set of the post-gate status bits; whether the `0x55xxx` aggregators reach an actuator path.
- **Recommended next action:** (1) producer/scaling of `FFFF8594+2`; (2) follow status bits written on the `FFFF1E54` object after the gated paths.
- **Artifact locations:** this CONTROL file; chat report of 2026-11-15; annotated LST `EL19A_Complete_Disassembly_ANNOTATED_V3_NEXT6_WO64683_64684_CHECKPOINT_2026-11-11.lst`.
- **Integration note:** Investigation PARTIAL. Master Workbook / Control Notebook integration still pending explicit request. WO64825 history preserved below.

## WO64825 register entry (2026-11-15, preserved)
- **WO ID / Title:** WO64825 — E974 Output-Chain Investigation
- **Agent:** Grok
- **Status:** PARTIAL
- **Findings (instruction-level from annotated LST):**
  - Callsite 1 (`0x3BB1A` / `sub_3BA88`): GBR=`FFFF1E54`; query = `(FFFF85C4+0x12)>>1` clamped; result → `GBR+0xB8` (`FFFF1F0C`); read-back `0x3BBE4`; non-zero gates `sub_223FE` path. Confirmed.
  - Callsite 2 (`0x3C042` / `sub_3BFC8`): identical GBR and query construction; result → `GBR+0xB9` (`FFFF1F0D`); read-back `0x3C104`; likewise gates `sub_223FE`. Confirmed. Paired with callsite 1.
  - Callsite 3 (`0x4130E` / `sub_412B8`): distinct GBR=`FFFF1D80`; query from `FFFF859C+0x12`; result → `FFFF1F0E`; local read-back and bit tests only; no shared `sub_223FE` path observed. Confirmed distinct.
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

## Control-source limitation
Stable Control Notebook item: `F6DEFBD470240AE6!sac2dd9024e574ee3a7462a1730baeddd`. Exact OneDrive fetch returned 403 `serviceReadOnly` during migration. Treat V53, Library Notebook copies and chat context as separately sourced snapshots; do not silently merge them.

## Next reconciliation requirement
When the exact stable Notebook becomes readable, compare its `CONTROL`, standing instructions, work-order ledger, latest continuation and V53 pointer against this file. Update this file only from verified current state. No WO allocation or lifecycle mutation is implied by this migration.
