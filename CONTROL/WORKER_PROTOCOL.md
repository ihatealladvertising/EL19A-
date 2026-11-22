# EL19A Worker Protocol

**Authority:** This file supplements, and never overrides, `CONTROL/active_work_orders.md`. The live register is the sole authority for WO lifecycle, assignment, priority and ownership.

## Worker startup instruction

Every worker receives the same standing prompt:

> Read `CONTROL/WORKER_PROTOCOL.md` and `CONTROL/active_work_orders.md` on `main` before doing anything. Work only on a WO that the live register explicitly assigns to you by owner and branch. If no assignment names you, do not choose, claim, reserve, or start a WO; send the coordinator a short availability request and wait. Once assigned, read the complete WO and its cited evidence, work only within scope, commit only to the assigned branch, submit a completion report/PR, and notify the coordinator. Then reread this protocol and the live register before requesting another assignment.

## Assignment and concurrency rules

1. **Single writer:** The coordinator alone allocates WO IDs, approves/reserves WOs, assigns owners/branches, changes lifecycle status in the register, and integrates PRs to `main`.
2. **No self-selection:** Workers never choose the “next” WO, use even/odd/highest-ID partitions, or infer ownership from an unclaimed reservation. A reservation is not an assignment.
3. **One WO, one owner:** An assignment is valid only when the current `main` register records the WO, named owner/session, dedicated branch, status `ACTIVE — CLAIMED`, and assignment checkpoint. If any of these disagree, stop and ask the coordinator.
4. **Isolated work:** Workers edit only their assigned WO report and explicitly authorized evidence outputs on their dedicated branch. Never edit `CONTROL/active_work_orders.md`, another WO report, another worker's branch, or protected engineering artifacts unless the WO expressly authorizes that exact change.
5. **No direct-main pushes:** Workers never push to `main`, merge PRs, or update authoritative lifecycle state. Submit a PR or completion handoff to the coordinator.
6. **Serialized integration:** The coordinator reviews the diff against the current `main`, checks scope/evidence, handles rebase/conflicts, merges, updates the register in a minimal transaction, then reads back and verifies the result. Never merge a stale register snapshot or discard another worker's entry.
7. **No unsafe branch locks:** A branch-creation operation that can create *or update* a ref is not an atomic lock. Do not use branch names alone as proof of exclusive ownership. The authoritative assignment is the coordinator's serialized register transaction.
8. **Parallelism:** Disjoint assigned WOs may run concurrently. If scopes or output paths overlap, coordinator must serialize or explicitly partition them before assignment.
9. **Checkpoints:** Workers send concise status proposals; coordinator batches register updates. Detailed evidence stays in the assigned report/artifact, not chat or the shared register.
10. **Completion:** Worker reports verified findings, hypotheses, bounded negatives, corrections, exact evidence locations, checks performed, limitations and recommended follow-up. It does not mark its own WO closed.
11. **Stale/abandoned work:** Only the coordinator may release/reassign a claim, after checking branch activity and available worker status. Workers must not steal or reassign work.
12. **Stop conditions:** If the assigned branch is missing, owner differs, scope conflicts, required input is absent, or a protected-artifact permission is unclear, stop before modifying files and notify the coordinator.

## Coordinator batch cycle

At each coordination pass, the controller:
- Reads the latest `main` register and checks open PRs/assigned branches.
- Reconciles finished reports and outstanding review obligations.
- Qualifies proposed work against existing reports, evidence and dependencies; rejects duplicates, combines related questions, splits oversized work and defers blocked work.
- Selects the highest-value eligible WOs, checks scope disjointness, allocates IDs and records each owner/branch in the register before execution.
- Reviews worker reports and PRs, quantifies evidence strength, resolves contradictions and integrates accepted results.
- Updates the register once per lifecycle transaction and verifies each write by readback.
- Generates follow-ups and maintains the three highest-value unresolved technical questions.
- Reports technical outcomes, material priority changes and genuine blockers only.

## Artifact authorization boundary

WO approval authorizes only the scope and outputs expressly listed in that WO. It does not authorize changes to ROMs, LSTs, XML definitions, A2L files, workbooks, calibration catalogues, indexes, scripts, tools, or Library content unless the specific artifact and operation are explicitly authorized. Existing project restrictions remain in force.

## Current limitation / future hardening

This protocol implements **coordinator-managed serialized assignment**, not a self-service automated dispatcher. Workers cannot safely pull arbitrary tasks merely by reading repository files: the repository currently has no verified atomic claim queue or dispatcher endpoint. Until one is implemented and tested, workers must request assignments from the coordinator rather than self-assign. Do not represent Git branch creation as an atomic lock. Any future dispatcher must provide serialized claims, durable owner/lease state, stale-claim recovery, isolated branches, and coordinator-controlled integration without requiring user administration.
