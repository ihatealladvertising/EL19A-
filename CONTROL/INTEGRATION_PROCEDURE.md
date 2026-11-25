# EL19A Integration and Batch Publication Procedure

**Purpose:** Serialize writes to shared `main` without serializing technical investigations. A lane may accumulate any number of completed, publication-pending work orders while the integration gate is LOCKED. Publication is a batch operation, not a transaction repeated for each WO.

**Authority:** `CONTROL/INTEGRATION_STATUS.md` is the publication gate. `CONTROL/active_work_orders.md` remains the sole remote lifecycle authority. `CONTROL/WORKER_PROTOCOL.md` governs worker execution and local pending packages. This procedure governs the integrator's publication batch.

## 1. Two independent state dimensions

Do not conflate technical execution with publication:

- **ACTIVE:** one investigation currently being executed in a lane.
- **PUBLICATION-PENDING:** investigation, report and findings-disposition analysis are complete; its local package is preserved, but not yet published/read back.
- **CLOSED:** package has been published to remote `main`, all required readbacks passed, and the remote register records closure.

A lane may have one ACTIVE WO and multiple PUBLICATION-PENDING WOs. The worker advances to its next FIFO READY WO as soon as the prior WO's local package is complete and recorded. Publication lock never blocks technical work, queue selection, or local package preparation. It blocks worker writes to shared `main` only.

A WO must not be shown as remotely CLOSED while its report, required FND/REC records, index updates or supported inventory pointers remain unpublished. A local pending package is not a remote closeout.

## 2. Worker package contract

Each worker maintains its own local-only ledger at `CONTROL/PENDING_PUBLICATION_WORKER<N>.md` in its own checkout/worktree. Keep one FIFO entry per completed WO. Each entry identifies:

- WO ID and package state (`PREPARED` / `PUBLISHED`);
- complete WO report path;
- all ID-neutral FND/REC draft paths, if any;
- inventory/index changes required;
- disposition (`PROMOTED`, `NOT REQUIRED`, or `DEFERRED`);
- deferred follow-on WO draft, if applicable;
- evidence/dependency anchors and any publication-time allocation still required.

Never reuse or overwrite a pending report/draft for a later WO. Do not delete pending material after a rejected write or failed integration. The ledger is local staging metadata, not a new remote lifecycle authority.

While LOCKED, workers must not allocate global FND/REC IDs or edit the shared index. For `PROMOTED`, preserve complete ID-neutral FND/REC drafts, keyed to the WO (for example `FINDINGS/pending/WO<ID>-FND-draft.md`). At publication, the integrator assigns actual monotonically increasing IDs against the latest remote index, materializes canonical records, updates the index and supported inventory pointers, and replaces placeholders in the WO report. `NOT REQUIRED` needs no finding draft. `DEFERRED` must carry a bounded follow-on WO draft with source links and exact scope; finalize its ID and queue placement during publication.

If a worker has no separate worktree or cannot safely preserve local packages independently, it must not overwrite or discard earlier packages. It records the limitation and preserves all completed package contents in its lane's local pending ledger before proceeding.

## 3. Lock acquisition and worker behavior

1. Integrator fetches latest remote `main` and reads `CONTROL/INTEGRATION_STATUS.md`.
2. Integrator updates the gate to `LOCKED`, naming the integrator, start time and batch purpose. The lock is active only after that update is visible on remote `main`.
3. Workers immediately stop publishing to shared `main`. They do not stage or create commits while locked. They continue technical investigations and maintain local pending packages/ledgers.
4. Workers do not edit the remote active register while locked. They may continue selecting their own earliest READY work from the last verified remote FIFO, then record locally completed packages. They must not borrow another lane's tasks.
5. If the gate is missing or unreadable, workers treat publication as LOCKED and continue technical work/local preparation. Only the named integrator may write to shared `main` while locked.

The lock is a publication mutex, not a global work stop.

## 4. Batch collection and reconciliation

The integrator collects all available lane packages for the integration window. Do not force workers to publish one WO at a time or wait for a per-WO unlock/relock cycle.

For each lane, preserve FIFO order. Across lanes, publication order may be chosen for dependency safety, but never change lane ownership or technical result. Before writing:

- fetch latest `main`, the live register, Findings index, all relevant FND/REC records, and every source report needed by the packages;
- compare package paths and content against remote state; preserve all unrelated and concurrent changes;
- identify duplicate/provisional FND/REC allocations across lanes and assign unique IDs serially from the latest index;
- reconcile shared index edits additively; never overwrite a different lane's entries;
- resolve deferred WO IDs by the modulo lane rule and verify both report path and register absence;
- verify each package's mandatory findings-disposition block and ensure its disposition matches its drafts and intended register status;
- retain all historical reports; corrections are additive REC records, not silent edits to another worker's closeout.

If a package is incomplete or a required draft is missing, hold only that package out of the publishable batch and report the exact blocker. Other complete packages may proceed. Do not close a held WO remotely.

## 5. Batch publication sequence

Keep the gate LOCKED throughout the batch. Use explicit paths only; no broad add-all, cleanup, reset or force-push.

Recommended order:

1. Publish canonical FND/REC records for every publishable package, using collision-free IDs.
2. Publish the consolidated Findings index and supported inventory-pointer updates.
3. Publish all completed WO reports with final FND/REC IDs, index references, exact changed paths and publication commit references.
4. Publish any deferred follow-on WO specifications.
5. Make one consolidated update to `CONTROL/active_work_orders.md` for all completed WOs in the batch and all associated follow-on queue entries. Preserve other lanes' current assignments, FIFO ordering and concurrent changes. Mark a WO CLOSED only when its complete package is already published.
6. Read back every changed report, FND/REC record, index/inventory file, deferred WO and the final register from remote `main`. Verify IDs, cross-links, disposition blocks, queue order and status.

Prefer a single multi-file commit for a batch when the Git operation safely supports it. If the available API requires multiple commits, that is still one integration transaction: keep the gate LOCKED across all commits and do not release it between WOs or between package components. A partially published batch remains under lock until it is completed or safely rolled forward. Never claim a WO closed before the final readback succeeds.

If a write is rejected, fetch latest `main`, reconcile the changed file against the remote version, preserve all other workers' changes, and retry once with the refreshed content/SHA. Never force-push. If safe retry fails, keep LOCKED, preserve pending packages and report the exact blocker. Do not discard or mark unpublished packages complete.

## 6. Release and worker resumption

After every publishable package in the batch passes readback:

1. Update `CONTROL/INTEGRATION_STATUS.md` to `UNLOCKED`, recording the integration commit(s), batch contents/WO IDs and release time.
2. Read back the gate from remote `main`. Workers resume shared-main publication only after `UNLOCKED` is visible.
3. Workers refresh remote `main`, confirm which of their pending WOs are now remotely CLOSED, remove/mark those entries as published in their local ledgers, and continue their FIFO loops.
4. Any package not included remains locally pending and is carried into the next integration window. It must not be lost, silently dropped or represented as remotely closed.

## 7. Acceptance criteria

A correct batch procedure satisfies all of the following:

- A lane can complete WO A, preserve it as PUBLICATION-PENDING, and begin/complete WO B while the gate remains LOCKED.
- Any number of completed pending WOs can accumulate per lane; there is no one-pending-WO-per-lane limit.
- At most one investigation is active per lane; WOs within a lane still execute in FIFO order.
- No worker publishes to shared `main` while LOCKED.
- Concurrent lanes cannot allocate duplicate global FND/REC IDs or overwrite each other's index changes.
- The remote register marks each WO CLOSED only after its report and required findings package have been published and read back.
- One lock window can publish multiple WOs from multiple lanes, with one consolidated register update and no unlock/relock between individual WOs.
- Failed publication preserves the pending package and does not erase or misstate its technical completion.

## 8. Prohibited interpretations

- Do not interpret the lock as requiring workers to stop investigating.
- Do not interpret “one WO at a time” as “one unpublished closeout at a time.”
- Do not require a separate publication transaction, lock acquisition or unlock for each WO.
- Do not allocate FND/REC IDs independently in multiple unpublished lane worktrees.
- Do not mark a WO remotely CLOSED merely because its local report is complete.
- Do not discard local pending packages after a push rejection, session restart or partial batch.
