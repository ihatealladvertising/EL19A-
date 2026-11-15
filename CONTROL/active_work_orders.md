# Work Order Status — Reconciled Migration Snapshot

**Snapshot date:** 2026-11-15

## Current chat continuation
- **WO64825 — E974 Output-Chain Investigation** is the active task issued in this session (Agent: Grok). Status: **BLOCKED** pending access to the annotated LST. Investigation cannot proceed beyond the three already-documented callsites without the listing.
- Prior note retained for continuity: WO64824 was the earlier chat label for the same E974 topic; it is superseded by the formal WO64825 issuance below.

## WO64825 register entry (2026-11-15)
- **WO ID / Title:** WO64825 — E974 Output-Chain Investigation
- **Agent:** Grok
- **Status:** BLOCKED (missing annotated LST)
- **Findings (existing durable evidence only):**
  - Callsite 1 (`0x3BB1A` / `sub_3BA88`): query `min(FFFF85D6 >> 1, 255)` → `GBR+0xB8` (GBR=`FFFF1E54`) → read at `0x3BBE4` → gates `sub_223FE` (confirmed).
  - Callsite 2 (`0x3C042` / `sub_3BFC8`): same query → `GBR+0xB9` → read at `0x3C104` → gates `sub_223FE` (confirmed).
  - Callsite 3 (`0x4130E`): query `min(FFFF85AE >> 1, 255)` → `FFFF1F0E` (GBR=`FFFF1D80`) → read at `0x41330` (confirmed; distinct).
- **Evidence addresses:** `0xE974`, `0x3BB1A`, `0x3C042`, `0x4130E`, `0x3BBE4`, `0x3C104`, `0x41330` (V53 workbook + prior CONTROL notes).
- **Confidence:** confirmed for the above; all further consumer chains unresolved.
- **Decisions:** No semantic promotion. No XML / workbook / Notebook edit. Investigation incomplete.
- **Unresolved endpoints:** Full downstream consumer chains for all three results; relationship between the first pair and the third site; any actuator/output decisions.
- **Dependencies:** Annotated LST covering the three callsite regions and subsequent code.
- **Recommended next action:** Supply the annotated LST → resume WO64825 from the three immediate read-back sites.
- **Artifact locations:** This CONTROL file; chat report of 2026-11-15.
- **Integration note:** Investigation not completed; Master Workbook / Control Notebook integration remains pending.

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
