# EL19A Worker Protocol

**Purpose:** Keep workers focused on the assigned technical investigation. Repository administration belongs to the coordinator.

**Authority:** `CONTROL/active_work_orders.md` is the lifecycle source of truth. The coordinator validates and records every assignment before sending it to a worker. This protocol governs execution after that assignment is received.

## Worker instructions — technical-first

1. **Accept only an explicit assignment.** The coordinator's assignment message must identify the WO, owner/session, allowed output path(s), and scope. Do not choose or claim work. If no assignment is given, ask the coordinator for one and wait.
2. **Do not do coordinator work.** After receiving a complete assignment, do not reread the work-order register or this protocol, inspect branches/PRs, reconcile statuses, allocate IDs, edit the register, or plan other workers' tasks. The coordinator has already checked ownership, dependencies and file conflicts.
3. **Read only what the task needs.** Read the assigned WO report and its cited inputs/evidence. Reuse completed work and indexes named by the WO. Do not repeat broad scans, helper censuses or unrelated repository inventories.
4. **Spend the effort on the technical question.** Follow the assigned trace to its stated stop boundary. Record exact instruction addresses, effective addresses, widths, signedness, gates, data/query flow and first meaningful consumers where applicable. Separate verified facts from hypotheses and unresolved boundaries. Do not promote physical meanings or units without evidence.
5. **Stay within the allowlist.** Edit only the report/evidence paths named in the coordinator's assignment. Do not edit the register, another WO, another worker's files, or protected artifacts.
6. **Use shared `main`; no branch or PR work.** Do not create or use feature branches, open PRs, or manage merges. Perform the technical work first. At completion, fetch the latest assigned output file from `main`, make the smallest necessary final update, and commit the report/evidence once. Avoid progress commits and repeated report rewrites.
7. **Do not troubleshoot repository administration.** If the final update is rejected, a file conflicts, or the authorized path is unavailable, stop after the first failure. Do not force-push, reset, rewrite history, retry stale content, edit a different path, or spend time resolving Git state. Send the coordinator the technical handoff plus the exact file/error; the coordinator will resolve the repository issue.
8. **One completion handoff.** When finished, provide the coordinator the result, evidence anchors, unresolved boundary, changed paths and commit SHA. Do not mark the WO closed or update its lifecycle state. Send an interim message only for a genuine blocker or when the coordinator asks for a checkpoint.

## Coordinator responsibilities

The coordinator alone:
- Reads and maintains the live register; allocates WO IDs; validates dependencies and scope; assigns owners; records `ACTIVE — CLAIMED`, branch `main`, and the exact output allowlist.
- Ensures concurrent assignments have disjoint write paths. Only one worker may own a given output file at a time.
- Reviews technical findings, checks evidence and scope, resolves rejected/conflicting repository writes, reconciles contradictions, and accepts or returns closeouts.
- Updates lifecycle status and records closure in the register.
- Generates and prioritizes follow-on WOs, avoiding duplicate investigations.

## Stop conditions

Stop technical or write activity and contact the coordinator if the assignment is incomplete, required evidence is unavailable, the requested work exceeds its authorized scope, or the assigned output cannot be committed in one safe final update. Do not independently widen scope or repair the process.

## Protected artifacts

Unless a specific WO and assignment explicitly authorize them, workers must not modify ROMs, LSTs, XML definitions, A2L files, workbooks, calibration catalogues, indexes, scripts, tools, or Library content.

## Operating model

The coordinator is the single lifecycle and repository-administration owner. Workers are technical investigators: one assigned question, only its allowed evidence, one final report update, one completion handoff. Shared `main` is the only working branch; the coordinator prevents overlapping file writes through serialized assignments.
