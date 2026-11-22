# EL19A Worker Protocol

**Authority:** This file supplements, and never overrides, `CONTROL/active_work_orders.md`. The live register on `main` is the sole authority for WO lifecycle, assignment, priority and ownership.

## Worker startup instruction

Every worker receives the same standing prompt:

> Read `CONTROL/WORKER_PROTOCOL.md` and `CONTROL/active_work_orders.md` on `main` before doing anything. Work only on a WO that the live register explicitly assigns to you by owner/session, status `ACTIVE — CLAIMED`, and branch `main`. If no assignment names you, do not choose, claim, reserve, or start a WO; send the coordinator a short availability request and wait. Once assigned, read the complete WO and its cited evidence, work only within its authorized file scope, commit permitted outputs directly to `main`, and send the coordinator a completion handoff. Then reread this protocol and the live register before requesting another assignment.

## Assignment and concurrency rules

1. **Coordinator is the lifecycle single-writer:** Only the coordinator allocates WO IDs, approves/reserves work, assigns owners, records claims, changes lifecycle status in the register, reviews/accepts closeouts, and records closure. Workers never edit `CONTROL/active_work_orders.md`.
2. **No self-selection:** A reserved/unclaimed WO is not an assignment. Workers never choose the “next” WO, use even/odd/highest-ID partitions, infer ownership from a report or prior branch, or claim work themselves. They request an assignment and wait.
3. **Assignment transaction:** Before work starts, coordinator rereads the live register, verifies scope, dependencies and output-path availability, then records the WO ID, exact owner/session, branch `main`, status `ACTIVE — CLAIMED`, authorized file paths, and checkpoint in one minimal register commit. Coordinator reads the committed register back before instructing the worker to proceed.
4. **One WO, one owner:** An assignment is valid only when the current `main` register explicitly names the worker/session and records `ACTIVE — CLAIMED` with branch `main`. If owner, status, scope, or branch disagree, stop and ask the coordinator.
5. **Main-only worker commits:** All workers use the shared `main` branch. Do not create, use, or push feature/work branches; do not open PRs. An assigned worker may commit directly to `main`, but only the exact assigned WO report and evidence/output paths explicitly authorized by that WO and recorded in the assignment.
6. **File-level isolation:** Never edit the register, another WO report, another worker's files, or any path outside the assignment allowlist. The coordinator must prevent overlapping output paths before assigning concurrent work. Only one worker may own/write a given file at a time. Different workers may proceed concurrently only when their authorized write paths are disjoint.
7. **Safe shared-main updates:** Read the latest `main` and fetch the current blob SHA for every file immediately before updating it. Submit only the intended file change; never overwrite a whole stale snapshot. After a rejected update, non-fast-forward, or SHA conflict, fetch latest `main` and the affected file again, compare the intervening change, preserve it, and reapply only your own intended edit. Retry once; if it still conflicts or ownership is unclear, stop and send the exact error and commit/file details to the coordinator. Never force-push, reset, rewrite history, discard another worker's commit, or run repeated stale-SHA retries.
8. **Coordinator register serialization:** Worker commits may move `main` while the coordinator is working. The coordinator must fetch the latest register and blob SHA immediately before every register update, make a minimal change, and verify it by readback. Workers must never attempt to resolve or repair a register conflict.
9. **Parallelism:** Disjoint assigned WOs may be investigated concurrently. If scopes or output paths overlap, the coordinator must partition or serialize them before assignment. Concurrent commits to different files are allowed; on a shared-head conflict, follow rule 7.
10. **Checkpoints and completion:** Workers send concise status proposals. They may update their assigned report with evidence and a completion handoff, but must not mark their WO CLOSED or change lifecycle state. Coordinator reviews the report and authorized outputs, reconciles contradictions, then closes or returns the WO in the register.
11. **Recovery/reassignment:** Only the coordinator may release or reassign a claim, after checking the worker's status and current main contents. Workers must not take over another WO or another worker's output path.
12. **Stop conditions:** If the assignment is missing/mismatched, a required input is absent, a path is not authorized, a concurrent edit conflicts, or protected-artifact permission is unclear, stop before further modification and notify the coordinator.

## Coordinator batch cycle

At each coordination pass, the coordinator:
- Reads the latest `main` register and checks active claims, worker handoffs, and outstanding review obligations.
- Reconciles completed reports and evidence against the issued scope; records incomplete handoffs or corrections explicitly.
- Qualifies proposed work against existing reports, evidence and dependencies; rejects duplicates, combines related questions, splits oversized work and defers blocked work.
- Selects eligible WOs, checks scope and output-path disjointness, and records each owner/session and `main` assignment before execution.
- Reviews direct-main worker commits, validates the changed paths and evidence, resolves conflicts without discarding other work, and accepts or returns each completion.
- Updates the register in a minimal, serialized transaction and verifies the result by readback.
- Generates follow-ups and maintains the three highest-value unresolved technical questions.
- Reports technical outcomes, material priority changes, review obligations and genuine blockers only.

## Artifact authorization boundary

WO approval authorizes only the scope and output paths expressly listed in that WO and its assignment. It does not authorize changes to ROMs, LSTs, XML definitions, A2L files, workbooks, calibration catalogues, indexes, scripts, tools, or Library content unless the specific artifact and operation are explicitly authorized. Existing project restrictions remain in force.

## Operating model

This repository uses coordinator-managed assignment with workers committing authorized, disjoint files directly to `main`. It does not use worker-created feature branches or PRs. GitHub's shared branch is not an ownership lock: exclusive file/task ownership comes from the coordinator's serialized assignment transaction and path allowlist. Workers must never self-dispatch or edit lifecycle state. If an assignment race or same-file collision cannot be resolved by one safe refresh/reapply, stop and escalate.
