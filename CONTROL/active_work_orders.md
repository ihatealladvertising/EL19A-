# EL19A — Operational Control and Work-Order Register

**Operational authority:** This file is the sole live source for worker assignments, FIFO order, WO lifecycle and current operational priorities.
**Repository:** `ihatealladvertising/EL19A-` · **Branch:** `main` · **Updated:** 2026-11-25
**Working rule:** Read this file's QUICK START, then open only your first READY WO and its named dependencies. Do not use archive/history summaries to infer current assignments.

## QUICK START — READ THIS FIRST

| Worker | Current task | Next READY tasks |
|---|---|---|
| Worker 1 | **WO70003** — Release 1 scope freeze | None |
| Worker 2 | None — lane exhausted | None |
| Worker 3 | **WO65913** | WO65916 → WO65919 → WO65922 → WO66048 → WO66049 |

Execute one WO at a time in lane FIFO order. If a lane's current cell is empty, take its first READY follow-on; if none exists, stop. The assigned WO report is the task specification.

## OPERATIONAL FRONTIER

### Primary deliverable — Conservative RomRaider Release 1

The project objective is a usable, defensible RomRaider definition for the exact EL19A `f501.bin` / FID `8CMCKRN5` ROM—not complete semantic reconstruction of every ECU function.

Follow [`CALIBRATIONS/RELEASE1_PLAN.md`](../CALIBRATIONS/RELEASE1_PLAN.md). The release dispositions are:

- **INCLUDE — ESTABLISHED:** representation, axes and displayed engineering scaling are supported; names/units are supported where used.
- **INCLUDE — RAW/PROVISIONAL:** address, extent, storage and geometry are supported; unresolved function/units/conversion use a generic label and raw values. Do not imply tune-readiness or invent physical axes.
- **EXCLUDE:** required representation fields or a material representation claim remain uncertain, contradictory or misleading.

Full physical semantics, a first-consumer trace for every object, exhaustive discovery and vehicle testing are not Release 1 prerequisites. Trace only when it resolves a concrete address, extent, type, geometry, axis, scaling, name or inclusion blocker.

### Current lane priorities

- **Worker 1 — WO70003:** reconcile every top-level object in the selected full-definition XML baseline against V58 and current Findings; produce the Release 1 scope matrix. This WO does not authorize XML editing or broad ROM discovery.
- **Worker 2:** lane exhausted. Worker 1 or Worker 3 may add a fully specified, bounded, local-execution-suitable WO directly to its FIFO when useful; do not create filler tasks to maintain queue depth.
- **Worker 3:** preserve the existing FIFO. WO65913 → WO65916 → WO65919 → WO65922 → WO66048 → WO66049. WO66048/WO66049 are bounded warm-up/idle candidate discriminators, not assumed calibration identities. WO66049 reuses WO66048's shared `sub_488BA` context and must follow it.

### Queue exceptions

- **Blocked:** WO65206 remains blocked by the negative WO65204 alignment; it is not assigned to an active lane.
- **Withdrawn:** WO65240 and WO65243 are withdrawn from the active pool and are non-operative historical artifacts.
- There is **no minimum backlog target** and no requirement to keep three READY WOs per lane. Workers 1 and 3 replenish queues only when a concrete, bounded task is justified.

## ACTIVE DEPENDENCIES

Each worker reads the dependencies named in its current WO, not a repository-wide task list.

- **WO70003:** Release 1 plan, calibration guide, selected XML baseline, V58 workbook, current Findings index and only the records/reports relevant to the baseline objects.
- **WO65913:** dependencies and evidence anchors are listed in [`WO65913.md`](WO65913.md). Later Worker 3 WOs carry their own dependency lists; in particular, WO66049 explicitly depends on completion of WO66048.
- Before any shared-main publication, read [`INTEGRATION_STATUS.md`](INTEGRATION_STATUS.md). The gate controls publication only; it does not stop local technical work.

## OPERATING RULES

- [`WORKER_PROTOCOL.md`](WORKER_PROTOCOL.md) governs worker selection, one-active-WO-per-lane execution, findings disposition and closeout.
- Worker 1 and Worker 3 own investigation/direction and may assign complete bounded execution WOs to Worker 2. Worker 2 is execution-only: it follows its FIFO and does not create or prioritize tasks.
- Multiple technically complete WOs may remain publication-pending while the lane proceeds to its next READY task. Remote status becomes CLOSED only after the full report/findings package is published and read back.
- All shared updates go directly to `main`. No branches, PRs, merges or history rewrites. Only the named integrator publishes while the integration gate is LOCKED; workers continue local investigations and pending-package preparation.
- [`INTEGRATION_PROCEDURE.md`](INTEGRATION_PROCEDURE.md) defines the lock and batch-publication procedure. Do not create routine claim, heartbeat or progress commits.
- Preserve existing WO IDs, owner and FIFO placement. Never silently overwrite technical findings; corrections are additive through the Findings reconciliation process.

## CURRENT ARTIFACTS

| Artifact | Current use |
|---|---|
| `EVIDENCE/VERSA f501.bin` | Target ROM; 1 MiB; MD5 `46991697c502052752a2cabcb84c9e27`; FID `8CMCKRN5` |
| `WORKBOOK/EL19A_Master_Reverse_Engineering_Workbook_V58_WO65114_ThinReferenceCloseout_2026-11-21.xlsx` | Current engineering workbook baseline (V58, 149 sheets) |
| `CALIBRATIONS/EL19A_best_guess_provisional_full_definition.xml` | Selected starting XML; preserve unchanged and create a separate successor |
| `CALIBRATIONS/RELEASE1_PLAN.md` | Release 1 scope and acceptance plan |
| `FINDINGS/INDEX.md` | Current address-indexed interpretation and reconciliation entry point |
| `CALIBRATIONS/discovered_tables_catalog.csv` | Discovery staging only; not the Release 1 inclusion list |
| `CONTROL/active_work_orders_compaction_2026-11-25.md` | Archive index and exact pointer to the pre-compaction register |
| `CONTROL/active_work_orders_archive_2026-11-20.md` | Earlier historical archive; not operational authority |

The selected baseline's recorded blob SHA is `77b00f4ea3046050dbd791644752e5c01857b75f`. Its 549 XML `<table>` elements include 261 calibration objects (including overlays); reconcile its actual top-level object list under WO70003 rather than treating that count as the final scope.

## HISTORY AND AUTHORITY

The live register contains only current assignments, release-critical priorities, active dependencies, operating rules and artifact pointers. Detailed work performed and historical closeouts remain in individual `CONTROL/WO<ID>.md` reports; durable calibration conclusions remain in `FINDINGS/`.

The exact full register immediately before this compaction is preserved in [the pre-compaction Git snapshot](https://github.com/ihatealladvertising/EL19A-/blob/143cbe90dcb78ec24963771a9653c2ec4f476d03/CONTROL/active_work_orders.md), blob SHA `6ef7365c3f99e2a829b09c22075ffd72e8ec1f7f`. The [2026-11-25 compaction archive note](active_work_orders_compaction_2026-11-25.md) explains the preservation map. Earlier history is in [the 2026-11-20 archive](active_work_orders_archive_2026-11-20.md). These historical sources never determine current assignments.
