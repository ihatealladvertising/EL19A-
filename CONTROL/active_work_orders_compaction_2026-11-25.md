# Active Work-Orders Register Compaction — 2026-11-25

## Purpose

This note records the preservation path for the full historical material removed from the live register during its 2026-11-25 compaction. It is an archive index, not an operational queue and not a verbatim copy.

## Exact pre-compaction register

The complete pre-compaction version of `CONTROL/active_work_orders.md` is retained in Git history at:

- [Pre-compaction register snapshot — commit 143cbe90dcb78ec24963771a9653c2ec4f476d03](https://github.com/ihatealladvertising/EL19A-/blob/143cbe90dcb78ec24963771a9653c2ec4f476d03/CONTROL/active_work_orders.md)
- **Original Git blob SHA:** `6ef7365c3f99e2a829b09c22075ffd72e8ec1f7f`
- **Path:** `CONTROL/active_work_orders.md`

This is the exact file revision immediately before compaction. It preserves the former embedded closeout narratives, old queue snapshots, status summaries and operational-frontier notes. The commit is retained on `main`; no historical Git objects or work-order reports were rewritten.

## Existing archive

The earlier pre-compaction snapshot remains available at [`active_work_orders_archive_2026-11-20.md`](active_work_orders_archive_2026-11-20.md). It is historical only and does not determine current worker assignments.

## Where detailed project history belongs

- **Work performed and evidence:** each individual `CONTROL/WO<ID>.md` report. Closed work orders remain in the repository and are not deleted by this compaction.
- **Durable calibration conclusions and corrections:** `FINDINGS/INDEX.md`, `FINDINGS/records/` and `FINDINGS/reconciliations/`.
- **Current engineering baseline:** the V58 workbook and its linked source artifacts.
- **Evidence artifacts:** `EVIDENCE/` and the immutable source references recorded by the work orders/findings.
- **Current assignments, FIFO order and operational frontier:** only `CONTROL/active_work_orders.md`.

The compacted live register intentionally removes duplicated per-WO completion prose and obsolete assignment snapshots. It retains current Worker 1/2/3 assignments, the current Release 1 objective, live blockers/withdrawals that affect queue interpretation, operating rules and pointers to current artifacts.

## Assignment snapshot at compaction

| Worker | Current task | Next READY tasks |
|---|---|---|
| Worker 1 | WO70003 | None |
| Worker 2 | None — lane exhausted | None |
| Worker 3 | WO65913 | WO65916 → WO65919 → WO65922 → WO66048 → WO66049 |

This table documents the snapshot only. For all future execution, consult the current live register and its Quick Start block.
