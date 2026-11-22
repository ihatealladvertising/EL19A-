# EL19A Worker Protocol

**Operating mode:** Autonomous worker slots. Workers select, claim, investigate and close their own work orders. No coordinator/ChatGPT assignment or lifecycle intervention is required after launch.

**Authority:** `CONTROL/active_work_orders.md` is the live work-order pool and lifecycle record. This protocol supersedes older text in this repository that says workers must wait for coordinator assignment, may not select work, may not edit the register, or must use feature branches/PRs.

## Start prompts

Launch exactly one session for each slot, using the corresponding one-line instruction:

- **Worker 1:** "You are Worker 1. Follow CONTROL/WORKER_PROTOCOL.md and run your autonomous work loop until no eligible work remains."
- **Worker 2:** "You are Worker 2. Follow CONTROL/WORKER_PROTOCOL.md and run your autonomous work loop until no eligible work remains."
- **Worker 3:** "You are Worker 3. Follow CONTROL/WORKER_PROTOCOL.md and run your autonomous work loop until no eligible work remains."

Do not run two sessions under the same worker slot. The slot number is the worker's persistent identity and allocation lane.

## Autonomous allocation rules

All workers use shared `main`. No branches, PRs, coordinator handoffs, or manual task assignment.

1. **Worker 3 has first-pick priority.** Whenever Worker 3 has no active WO of its own, it claims the highest-numbered eligible `RESERVED — UNCLAIMED` WO. It records its claim before starting technical work.
2. **Worker 1 selects next.** Worker 1 may claim only when the register shows Worker 3 has an `ACTIVE — CLAIMED` WO (or Worker 3 has explicitly recorded that no eligible work remains). Worker 1 selects the lowest-numbered eligible odd WO. If none exists, it selects the lowest-numbered eligible WO of either parity.
3. **Worker 2 selects after accounting for Worker 1.** Worker 2 may claim only when Worker 3 has an `ACTIVE — CLAIMED` WO (or Worker 3 has explicitly recorded that no eligible work remains). From the eligible pool, first calculate Worker 1's next candidate by rule 2 and exclude it; then select the lowest-numbered eligible even WO. If none exists, select the lowest-numbered WO remaining after that exclusion.
4. **One active WO per slot.** A worker finishes or records a bounded blocked disposition for its current WO before claiming another. Never claim a WO already listed as active for any slot.
5. **Eligibility.** A WO is eligible only when its status is reserved/unclaimed, all stated dependencies are satisfied, required inputs are present, and its authorized output paths do not overlap any active assignment. Exclude blocked, active, closed, and already claimed tasks.
6. **Atomic claim.** Fetch the latest register and blob SHA. In one minimal register update, change the selected WO to `ACTIVE — CLAIMED` and record the owner slot, branch `main`, and exact allowed output path(s); also add it to the current Active WOs summary. Read back the committed register. Start only after the claim is visible.
7. **Claim collision.** If the register update is rejected, refresh the register once and recompute the slot's candidate from the latest pool. If the candidate is now active/closed, choose again by the same rule. Do not repeatedly retry stale content or overwrite another worker's claim.
8. **Priority sequencing.** Worker 1 and Worker 2 may work concurrently once Worker 3 has recorded an active claim. When Worker 3 closes a WO and has no active WO, Worker 1 and Worker 2 wait for Worker 3's next claim before taking another; Worker 3 therefore gets first pick at every new allocation cycle.

## Technical work — keep it the main activity

- After claiming, read the WO specification and only the cited evidence required for the task. Do not reread this protocol or survey the whole repository.
- Reuse named completed reports, indexes, reader mechanics and ROM/LST anchors. Do not repeat completed scans, helper censuses or unrelated inventories.
- Work to the WO's stated question and stop boundary. Record exact instruction PCs, effective addresses, widths, signedness, query/axis construction, branch conditions, arithmetic and first meaningful consumers as applicable.
- Separate verified facts, hypotheses and unresolved boundaries. Never promote a physical meaning, unit, or calibration label from resemblance alone.
- Do not create interim commits, routine progress reports, new tooling, broad scans, or unrelated cleanup. Spend the time on the technical investigation.

## Allowed repository activity

- Workers commit directly to `main`; never create branches, open PRs, cherry-pick, merge, reset, force-push or rewrite history.
- Each worker may edit only its own active WO report and the evidence/output paths expressly listed in that WO and its claim. A worker may update only its own claim and closeout status in `CONTROL/active_work_orders.md`; never edit another worker's assignments or statuses.
- If the WO report file does not yet exist, create `CONTROL/WO<ID>.md` from the scope in the register and record the investigation there. Do not invent a new scope.
- Make one final report/evidence update when the technical work is complete. Then make one minimal register update to remove the WO from Active WOs and mark its queue entry closed or blocked. Verify both updates.
- Use the latest blob SHA for every update. If a write fails, refresh the one affected file and retry once while preserving other workers' changes. If it still fails, stop repository work and report the exact error; do not spend time debugging Git or widen the scope.

## Closeout rules

- Mark `CLOSED — BOUNDED COMPLETE` when the issued scope has been answered to its stated boundary, including a well-supported bounded negative or unresolved external endpoint.
- Record the precise stop reason as `BLOCKED` only when a required input/dependency is genuinely unavailable; do not leave a completed bounded investigation active merely because a physical semantic remains unknown.
- The report must contain the result, evidence anchors, confidence/limits, no-repeat notes, changed paths and commit SHA. A concise handoff is sufficient; no coordinator approval is required for the worker to move to its next task.
- After closeout, immediately refresh the register and repeat the allocation rule for the same slot. Continue until no eligible WO remains.

## Stop conditions

Stop only for a genuine technical or authorization blocker, missing required input, overlapping output ownership, or a repository write that fails after one safe retry. State the exact blocker and what remains preserved. Do not turn routine Git updates into an investigation.

## Protected artifacts

Unless a specific WO explicitly authorizes them, do not modify ROMs, LSTs, XML definitions, A2L files, workbooks, calibration catalogues, evidence indexes, scripts, tools or Library content.

## Worker priority in one glance

| Slot | Next WO |
|---|---|
| Worker 3 | Highest-numbered eligible WO; first pick |
| Worker 1 | Lowest eligible odd WO; otherwise lowest eligible overall |
| Worker 2 | Lowest eligible even WO after excluding Worker 1's next candidate; otherwise lowest remaining |

The register is the only shared coordination point. Worker slot identity and deterministic selection replace manual coordinator assignment.
