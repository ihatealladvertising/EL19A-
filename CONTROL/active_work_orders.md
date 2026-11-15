# Work Order Status — Reconciled Migration Snapshot

**Snapshot date:** 2026-11-15

## Current chat continuation
- **WO64824 — E974 output-chain investigation** is the task identified by the latest chat continuation context. Preserve this as the current working task, but do not claim it is the read-back-verified active WO in the stable Control Notebook: its direct OneDrive fetch returned 403 during this migration, and WO64824 was not found in the retrieved V53 checkpoint or later Library Notebook snapshot.

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
