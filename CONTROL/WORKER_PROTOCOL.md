# EL19A Worker Protocol

**Operating mode:** Repository-driven autonomous execution. The three worker sessions remain the project execution system. Worker 1 and Worker 3 retain their investigation/reasoning roles; Worker 2 is the dedicated full-time local execution agent. This role split does not create a fourth lane or change the shared queue authority. No coordinator or user action is required between ordinary bounded work orders.

**Authority:** CONTROL/active_work_orders.md is the sole live queue and lifecycle authority. This file defines execution rules. These rules supersede older coordinator-only, parity-pick, self-selection prohibition, separate-branch and PR instructions retained in historical notes. Ordinary technical work remains independent across lanes; the temporary integration lock below is the only cross-lane publication pause.

## Start prompts

Run exactly one session per slot:

- Worker 1: "You are Worker 1. Follow CONTROL/WORKER_PROTOCOL.md and run your autonomous lane until no defensible work remains."
- Worker 2: "You are Worker 2, the full-time local execution agent for EL19A. Use your configured local model/runtime. Follow CONTROL/WORKER_PROTOCOL.md and CONTROL/LOCAL_WORKER2_EXECUTION.md. Run your autonomous FIFO execution loop until no eligible local-execution work remains; process the Worker 2 proposal inbox at queue/replenishment boundaries and escalate rather than guess."
- Worker 3: "You are Worker 3. Follow CONTROL/WORKER_PROTOCOL.md and run your autonomous lane until no defensible work remains."

Never run two sessions under the same slot. All three slots may start immediately. No slot waits for another slot for assignment or technical execution. Workers must observe the temporary integration lock before publishing repository changes.

## Worker lanes and collision prevention

All work is committed directly to shared main when the integration status is UNLOCKED. No feature branches, PRs, merges, cherry-picks, resets, force-pushes or history rewrites.

**Live assignments are defined only by `CONTROL/active_work_orders.md`.** Do not use historical queue tables or older assignment notes embedded elsewhere in the register to infer current ownership. A closed WO is not an active assignment even if an old paragraph still names its former owner. Explicit current lane assignments in the live register override the modulo rule for already-existing WOs.

Each slot owns its lane. It selects only its own READY/ASSIGNED work in the live register and performs at most one active investigation at a time. It may accumulate multiple technically completed, publication-pending WOs in FIFO order while continuing later READY work, including while the integration gate is LOCKED. It updates only its own lane's lifecycle records when the batch is published. Do not borrow another slot's WO, change another slot's owner/status, or wait for another slot.

**New WO ID allocation is collision-free by lane:** for WOs created under this protocol, assign by ID remainder:
- ID mod 3 = 1: Worker 1
- ID mod 3 = 2: Worker 2
- ID mod 3 = 0: Worker 3

Start at the next unused WO ID after 65217. Advance by 3 until the ID is absent from both the register and CONTROL/WO<ID>.md. Legacy assignments listed in the register remain assigned as written; do not renumber or reassign them. A worker creates new WOs only in its own modulo lane.

**Explicit user-directed transfer exception:** A direct user instruction may transfer an existing, unstarted READY WO to another slot when a lane is offline or exhausted. This is an exception to the default no-reassignment rule. Preserve WO IDs, technical scope, dependencies, evidence anchors, no-repeat boundaries and FIFO order. In one atomic `main` commit, update the WO report's assigned status, owner and sequencing language together with the live register's current/backlog entries. Retain the original modulo allocation as historical metadata; the updated live register determines the new lane. Do not transfer in-progress work unless the user explicitly names it and the handoff boundary is recorded. This makes concurrent WO creation use distinct IDs and report paths.

One session per lane plus explicit lane ownership prevents duplicate task execution. The register's SHA protects concurrent writes to the shared queue. The integration lock is a short, explicit exception: it serializes publication only, not technical work or task assignment.

## Worker 2 — full-time local execution role

Worker 2 remains the existing modulo-3 lane (WO ID remainder 2). Do not create a fourth worker lane, renumber WOs, change the modulo-3 allocator, or transfer another lane's existing WO. Worker 2 uses the configured local model/runtime as a continuous execution worker; Worker 1 and Worker 3 remain the project's external investigation/reasoning contributors.

**Existing queue first:** Worker 2 executes its currently assigned WO and READY FIFO backlog in their existing order. The role change does not skip, rewrite, reassign or widen an already-issued WO. Each task still has one active investigation at a time and follows the normal findings, publication-pending, integration-lock and readback rules.

**Proposal intake:** `CONTROL/LOCAL_WORKER2_INBOX.md` is a non-authoritative proposal/review inbox, not a WO queue or lifecycle register. Worker 1, Worker 3 and the coordinator may append bounded task proposals or review responses there. Proposals must not reserve WO IDs, change ownership/status, or be treated as assigned work. Worker 2 checks the inbox at startup and when replenishing its READY backlog. Worker 2 alone validates a proposal, allocates its own next unused modulo-3-remainder-2 WO ID, creates the full `CONTROL/WO<ID>.md` and registers it in `CONTROL/active_work_orders.md`. A proposal becomes executable only after that registration and normal dependency checks succeed. Rejected, duplicate or blocked proposals receive a short reason in the inbox; do not create placeholder WOs.

**Local-execution suitability:** A Worker 2 WO must be independently executable with the available local evidence and tools. It must specify a falsifiable technical question, exact ROM/RAM addresses or routine windows, known inputs/dependencies, reuse/no-repeat boundaries, expected evidence and a bounded stop condition. Preferred work includes exact caller/callee and producer/consumer traces, RAM read/write provenance, lookup reader/query mechanics, branch/delay-slot verification, axis/storage checks, first-consumer traces, bounded cross-reference validation and narrowly scoped findings reconciliation. Use deterministic scripts/searches for mechanical extraction when available; the model interprets the selected evidence. Keep context to the relevant source windows and indexed records rather than loading huge listings wholesale.

Semantic tasks are allowed only when the WO supplies a falsifiable hypothesis, target-side evidence, a cheap discriminator and a precise identity layer/stop boundary. Worker 2 may establish software behavior and qualified input/output paths; it must not promote a physical sensor, calibration function, units or actuator meaning from names, shapes, donor labels or plausible values alone. Broad project strategy, open-ended discovery, multi-family semantic synthesis, unavailable external-source work and tasks requiring unbounded context are not local-execution eligible; return them to the proposal inbox for redesign or leave them with the reasoning lanes.

**Escalation instead of guessing:** When a meaningful ambiguity exceeds the WO's local-execution boundary, record an `EXTERNAL REVIEW REQUEST` in the WO report with (1) exact question, (2) competing interpretations, (3) verified evidence/PCs/addresses, (4) what is still unknown, and (5) the smallest discriminating test. Worker 1/3 or the coordinator may append a response keyed to that WO in the proposal inbox; no one edits Worker 2's report or lifecycle. Worker 2 evaluates any response against ROM evidence and records its disposition additively. Do not wait idle for review: close a bounded task when its issued question has been answered to its stop boundary, or mark it BLOCKED only for a genuinely unavailable required dependency, then continue with the next independent FIFO task. Physical meaning remaining unresolved is not itself a blocker.

**Backlog replenishment:** Worker 2 retains the standard target of three READY follow-on WOs beyond its current task. Prefer accepted inbox proposals first, ranked by information gain and local suitability; then create a defensible bounded task from the existing protocol priorities if no suitable proposal exists. Never lower evidence standards or invent work merely to keep the local model busy.


## Autonomous execution loop

Repeat this loop for the lifetime of the worker session:

1. At startup only, read this protocol and the current operational frontier in active_work_orders.md. Find the current WO and the ordered FIFO backlog for your lane. The next task is the earliest READY item. Do not re-read the protocol or inventory the repository on every iteration.
2. If CONTROL/WO<ID>.md already exists, read it. If an assigned legacy WO has no report file yet, the queue row and its cited dependencies in active_work_orders.md are the authoritative specification: create CONTROL/WO<ID>.md with the objective, exact scope, owner, branch main, authorized paths, dependencies and stop boundary from that register entry. This is execution setup, not a separate claim commit; do not invent or widen scope.
3. Perform the technical investigation to the specified stop boundary. Spend the effort on tracing, verification and interpretation, not administration.
4. Before closeout, perform a bounded reconciliation against the exact prior findings cited by the WO and any directly affected claims discovered during the investigation. Distinguish confirmed corrections from hypotheses.
5. Complete the mandatory **findings-disposition analysis** below for this WO. Decide PROMOTED, NOT REQUIRED or DEFERRED and prepare all required FND/REC content. A material result must never exist only in WO prose. When publication is available, create/read back the actual records and index entries. While publication is paused, prepare ID-neutral finding/reconciliation drafts keyed to this WO; do not reserve or invent global FND/REC IDs.
6. Write the full result to your own `CONTROL/WO<ID>.md` report and prepare a complete local closeout package. Include verified facts, evidence anchors, calculations/branches, confidence, limits, no-repeat notes, the findings disposition block, required FND/REC drafts, supported inventory-pointer edits, and a list of exact changed paths. Mark the package `PUBLICATION-PENDING` until remote publication and readback succeed. Record it in your lane's local pending-publication ledger as specified in `CONTROL/INTEGRATION_PROCEDURE.md`.
7. Do not mark a WO remotely CLOSED, update the remote lane summary, or claim that Findings records are published until its complete package has been published and read back from remote `main`. A locally complete package is not a remotely closed WO. When UNLOCKED, publish accumulated packages in FIFO order; close each WO in the register only after its report, actual FND/REC records, index and supported inventory pointers have passed remote readback. Do not seek coordinator approval for a bounded promotion within this standing authorization.
8. After the local package is complete and recorded, immediately take the earliest READY WO in your lane's FIFO backlog, even if earlier packages are still publication-pending. Maintain at most one active investigation per lane, but allow any number of completed pending packages. If the backlog is below target depth, replenish it under the technical-priority and WO-creation rules below. Continue without waiting for another slot or user prompt.

An existing ASSIGNED — WORKER N — READY entry reserves that task to its slot. Multiple READY entries may exist in a lane's FIFO backlog; they are not permission to execute concurrently. No separate claim commit is required. A worker may start only the earliest READY item after completing and locally recording the preceding WO's package; remote publication is not required to advance. Do not create routine claim, heartbeat, progress, handoff or status-polling commits. The active WO remains assigned to its slot until its remote closeout is published; its local pending package must remain separately identifiable and must not be overwritten.

## Technical direction and WO replenishment

Workers 1 and 3 maintain investigation priorities and technical direction inside their own lanes. Worker 2's role is execution-first: its next work comes from its current FIFO and accepted local-execution proposals; it may create its own bounded lane-2 task only when no suitable proposal is available. Do not wait for ChatGPT or a coordinator to invent ordinary work, and do not confuse Worker 2's execution queue with a strategic research lane.

When your lane's READY backlog is below target depth, choose the highest-payoff unresolved question using this order:

1. Follow explicit current user priorities recorded in the operational frontier or a WO.
2. Resolve an open P1 investigation, a concrete dependency, or a documented contradiction that blocks reliable downstream interpretation.
3. Trace high-value 3D maps and 32-point curves through reader mechanics, query/axis construction, arithmetic, output storage and first meaningful consumers. Reuse completed helper and axis work; do not repeat it.
4. Advance the reserved DTC/sensor-monitor and ROM configuration/option-byte tracks, including their unresolved inputs, guards and consumers.
5. Investigate other specific calibration candidates only when existing evidence supplies a defensible address/geometry/reader lead and the new scope adds information.
6. Consider metadata automation or donor-ROM comparison only when it directly improves EL19A evidence confidence. Donor labels and semantics are never transferred without independent target-side proof.

Explicit no-repeat boundaries in Guardrails and future priorities and in completed WO reports override this ranking. In particular, the 1D scalar/limiter sweep over 0x7800–0x9B00 is already complete under WO65090; do not recreate that interval census. Reuse the completed reader indexes, helper crosswalks, maps, curves, and prior bounded negatives.

When your lane has fewer than three READY follow-on WOs queued beyond its current in-progress task, create enough new bounded WOs to restore the target depth, provided defensible unresolved questions exist. The new WO must state:
- a precise technical question and why it has value;
- exact target addresses/functions/records and required inputs;
- named completed evidence to reuse and explicit no-repeat exclusions;
- the expected evidence and stop boundary;
- dependencies and their actual current status;
- only its own report path as an authorized output unless another output is specifically necessary and safe.
- for Worker 2 WOs, a `LOCAL EXECUTION FIT` of YES or CONDITIONAL, with the evidence-based reason and exact escalation point.

Create CONTROL/WO<ID>.md and add its queue row to active_work_orders.md with your slot ownership, priority, dependencies, branch main and exact allowed paths. Use the modulo ID rule above. Never create placeholder/filler tasks to keep the queue count high. If no defensible task exists, record the specific exhausted boundary in your lane's latest closeout and stop.

Maintain a target backlog of **three READY follow-on WOs per lane**, in addition to the current in-progress WO. This is an operating buffer, not a limit: an explicit user request may authorize a larger queue. Queue tasks in a clear FIFO order; all queued WOs remain assigned to their modulo lane, but the worker starts only the earliest READY item and never runs two WOs concurrently in the same lane. Create replacements as work is completed so the buffer is replenished without a user prompt. Do not create filler: every queued WO must have a distinct, defensible technical question, exact scope, reuse/no-repeat boundary and stop condition. Do not queue work already covered, completed or blocked by an unavailable dependency.

## Mandatory findings-disposition closeout gate

Every WO closeout must include this block in its report:

```text
FINDINGS DISPOSITION: PROMOTED | NOT REQUIRED | DEFERRED
FND: <IDs or none>
REC: <IDs or none>
INDEX: <updated/read-back commit or SHA, or not applicable>
INVENTORY: <finding-pointer update, unsupported format, or not applicable>
RATIONALE / FOLLOW-ON: <brief reason; required for NOT REQUIRED or DEFERRED>
```

Use exactly one disposition:

- **PROMOTED:** The result materially changes a calibration object's proposed identity, address, storage, geometry, axes/query domain, scaling, units, confidence, evidence status or XML inclusion/exclusion; corrects a prior material interpretation; or establishes a reusable evidence method that prevents a material false attribution. Create/update the stable FND record, create an additive REC when a prior interpretation is corrected, update the address lookup in `FINDINGS/INDEX.md`, and add inventory finding pointers only where the existing format supports a safe additive change. Record IDs and readback SHA.
- **NOT REQUIRED:** The result is only routine technical tracing or a bounded negative that does not change any calibration candidate's interpretation/evidence status, a reusable method, an XML disposition or a prior claim. State specifically what was checked and why it has no durable calibration-knowledge impact. "No new table found" alone is not enough when it materially changes a candidate's status.
- **DEFERRED:** A material correction is clear but cannot be fully reconciled within the current WO's scope or evidence. Before closing, create a bounded follow-on reconciliation WO in the responsible lane, cite both source reports/findings, define exact allowed paths and stop boundary, and record its ID here. Do not defer merely because physical meaning remains unknown; an appropriately qualified OPEN/DISPUTED finding can preserve that uncertainty now.

**Standing authorization and permitted paths:** This protocol itself grants each worker standing, narrowly scoped authorization to create new files under `FINDINGS/records/` and `FINDINGS/reconciliations/`, update `FINDINGS/INDEX.md`, and add finding-ID pointers to an existing calibration inventory only where its current schema safely supports additive pointers, when needed to satisfy this gate for that worker's own WO. This applies even when a legacy WO's "Authorized output" list predates the Findings system or omits these paths. It does not authorize changes to ROM/LST, XML definitions, workbooks, A2L files, calibration values/geometries, catalogue data, scripts, protected evidence or another worker's report/lifecycle. No unsupported schema changes or broad migrations.

**Record discipline:** Read the current index and relevant FND/REC records before allocating IDs. Allocate the next unused monotonically increasing ID, verify the target record path does not already exist, and never overwrite a record. If another worker wins the same ID, refresh and allocate the next unused ID. At publication time, update the index using its current blob SHA; on a concurrent-write rejection, refresh, preserve the other change and retry once. If safe publication still fails, retain the complete package as PUBLICATION-PENDING, leave the remote WO non-closed, record the exact publication blocker in the local ledger, and continue independent FIFO technical work. Read back every created record and the index entry from remote `main` before remote closure.

**Historical closeouts:** This gate applies immediately to every open/in-progress WO and all new WOs. It does not authorize workers to reopen or edit another lane's closed WO. A closed WO whose material result was not promoted must be handled by a new, bounded findings-migration/reconciliation WO in an owning lane. Do not mass-migrate routine RAM traces.

## Local pending-publication packages

The local batch ledger is `CONTROL/PENDING_PUBLICATION_WORKER<N>.md` in that worker's own checkout/worktree. It is a local working artifact, not a remote lifecycle authority and not a reason to create a commit while locked. Keep one entry per completed WO, in FIFO order, with: WO ID; package state (`PREPARED` or `PUBLISHED`); report path; exact local FND/REC draft paths; inventory/index changes required; disposition; dependencies; and any unresolved publication-time allocation. Never overwrite one WO's report or drafts with the next WO. Preserve all pending files across worker-loop iterations and do not discard them on a rejected push.

For a pending `PROMOTED` disposition, use ID-neutral draft filenames such as `FINDINGS/pending/WO<ID>-FND-draft.md` and `...-REC-draft.md` (or an equivalent clearly segregated local-only draft location). Do not allocate global FND/REC IDs, edit the shared index, or claim an FND/REC ID while publication is locked. At publication, the integrator allocates the next unused IDs against the latest remote index, materializes the canonical records, updates index/inventory pointers and replaces pending placeholders in the WO report. `NOT REQUIRED` packages need no FND/REC draft. `DEFERRED` packages must include the bounded follow-on WO draft/specification in the local package; its ID and register entry are finalized during publication.

A pending package is technically complete when its evidence, reconciliation, disposition and all draft content are complete. It remains publication-pending—not remotely closed—until the integration procedure's readback gate passes. Workers may continue to the next READY WO after recording the package. The local ledger is not committed or pushed separately; it is included in the eventual batch only if useful as an audit record. The integrator must never rely on a worker's chat summary in place of the actual local package contents.

## Reconciliation rules

Reconciliation is a normal part of every lane, not a coordinator-only duty.

- Compare new findings with the specifically relevant earlier WO reports and register claims. Reuse exact evidence and report anchors; do not conduct broad archive audits by default.
- If the current WO resolves a contradiction within its scope, state the old claim, corrected claim, evidence and confidence in the new report; append a concise reconciliation entry to the register.
- Never silently edit, overwrite or relabel another worker's report. Preserve it as historical evidence. A correction or synthesis is additive and points to both the old and new records.
- If a contradiction extends beyond the current scope, create a bounded reconciliation WO in your own lane, with both source reports as dependencies. Do not leave a known material conflict unrecorded.
- Do not mark another worker's WO closed or blocked. Each slot owns its own task lifecycle. Cross-lane observations may be recorded as findings or dependencies, but not as reassignment instructions.
- Keep status (active/closed/blocked), technical result (positive/negative/partial), and unresolved semantic boundary separate.

## Durable calibration knowledge preservation (effective 2026-11-23)

The authoritative calibration knowledge layer is `FINDINGS/INDEX.md`, governed by `FINDINGS/README.md`. The operational register remains the sole lifecycle authority; it is not the technical findings database.

- Any result that materially changes a calibration object's proposed identity, geometry, axes/query domain, storage, scaling, units, confidence, XML disposition or evidence status MUST be promoted into a stable finding record. A sentence in a WO report or chat is not sufficient.
- Every finding must link to exact source evidence, source WO/report anchors, affected addresses and inventory/XML objects; distinguish observation, inference, confidence and unresolved boundary.
- When a finding changes an earlier interpretation, create an additive reconciliation record preserving old interpretation → corrected interpretation, reason and both source links. Never erase or silently rewrite historical claims.
- Update the address lookup in `FINDINGS/INDEX.md`; update calibration-inventory finding pointers only where the format supports safe additive changes. Keep the operational register to status and concise links.
- Do not flood the index with routine RAM-cell endpoint traces that do not affect calibration interpretation or reusable evidence methods.
- **Definition-build gate:** before generating or revising any XML definition, reconcile every included/affected object against the current findings and reconciliation index, then record the index revision and unresolved conflicts in a build manifest/report. Reading only recent WO summaries does not satisfy this gate.
- Existing evidence classes remain separate. The E678/E688 Rev Hang screenshot-finalized presentation is a narrow user-authorized exception; preserve their RPM presentation while recording timer-derived ROM query mechanics separately. Apply ROM reader/query/consumer evidence normally to all other tables and reconcile source conflicts.

## Recurring Project Knowledge and Process Review

Run the review defined in `CONTROL/PROJECT_KNOWLEDGE_PROCESS_REVIEW.md` every 10 additional WO closeouts across all lanes or every 7 calendar days, whichever comes first. The first worker/session to observe the due trigger performs it; check the review log first to avoid duplicate work. This is a short repository-only maintenance review, not a new technical WO and not authority to alter another lane's lifecycle.

Use the five required lenses: knowledge coverage, contradictions, investigation efficiency, method improvement and fresh-session context integrity. Record a compact dated entry in the review log, including concrete actions or explicit no-change dispositions. Promote material calibration interpretations through the Findings system; preserve prior claims with additive reconciliation. Promote reusable methods to durable repository documentation. Do not treat chat history or saved memory as a substitute for missing repository evidence.

The acceptance test is whether a competent investigator without conversation access can resume from repository files without repeating major investigations or inheriting incorrect assumptions. Mark PASS only after checking the live register, protocol, findings/reconciliation index, recovery guide, current calibration baseline/build state and relevant linked reports. Otherwise mark PARTIAL or FAIL and name the blockers.

## ChatGPT context recovery

A fresh ChatGPT session must follow `CONTROL/CHATGPT_CONTEXT_RECOVERY.md`. Start with the live operational register, then this protocol and the findings index; read current WO reports and source evidence as required. Do not treat saved memory, chat summaries or stale `PROJECT_STATE.md` snapshots as authoritative. Never claim repository state without current readback.

## Semantic evidence workstream

Semantic investigations run alongside the three existing structural worker lanes; there is no fourth lane. The purpose is to move from verified locations and reader mechanics toward defensible input, function and output identities.

For every new WO labeled `SEMANTIC`, and every existing semantic WO before execution/continuation, include a falsifiable hypothesis record with:
- **Hypothesis:** proposed input, function, output or physical role/name.
- **Evidence:** exact EL19A addresses, instruction PCs, report/index anchors and any diagnostic/donor/literature references, clearly separated by source class.
- **Prediction:** the specific observation required if the hypothesis is correct.
- **Cheap discriminator:** the smallest bounded test that could falsify or distinguish it.
- **Result:** supported, weakened, rejected or unresolved; do not claim an unrun test.
- **Information gain:** which competing interpretations the test separates and why this test is the least-cost useful discriminator.

Each semantic WO and closeout must state which identity layer it advances: **input identity**, **function identity**, and/or **output identity**. A diagnostic-symbol join can name an input but cannot by itself name the table's function. Literature and donor labels generate or challenge hypotheses but are not target-side proof. Execution validation establishes software behavior only. Physical calibration identity requires target-side consumer/endpoint evidence and compatible units/branches.

Preserve the existing evidence grades (Reader-Verified, Query-Traced, Semantic-Strong). Do not redefine or promote them based on auxiliary flags. Where useful, record descriptive flags such as `QUERY_SYMBOL_JOINED`, `LITERATURE_CORRELATED`, `DONOR_CORROBORATED`, `EXECUTION_VALIDATED`, `SINK_ANCHORED`, and `PHYSICAL_IDENTITY_UNRESOLVED`; these flags are annotations, not evidence grades.

Semantic workstream phases:
1. identify the actual query input and join it to Consult Mode $22, OBD Mode $01 or named DTC source cells;
2. establish vocabulary from the repository's relevant tuning literature with page-level citations;
3. validate a bounded pure-software reader path by controlled execution and an independent reference model;
4. identify outputs by tracing backward from selected MMIO/actuator sinks through command variables and calculations to lookup results;
5. corroborate only the strongest candidates against independent donor definitions and diagnostic/literature references.

Two bounded companion tracks are authorized when queued as explicit WOs: (a) static Mode $06 service-support/dispatch and, only if present, monitor ID/result/limit/scaling provenance; vehicle access remains deferred; (b) sink-first actuator tracing from selected existing MMIO census endpoints. Neither permits a broad firmware/peripheral emulator, live-vehicle testing, or an indiscriminate MMIO sweep.

Rank semantic tests by expected information gain across competing hypotheses, not by the number of addresses inspected. Reuse completed WO65106 MMIO and WO65173 diagnostic joins; do not repeat their inventories. Donor comparisons must be selective and must test a concrete discriminator; address matching or donor-name agreement alone is insufficient.

## Evidence and technical standards

- Record exact instruction PCs/listing anchors, effective addresses, widths, signedness, query and axis construction, search/interpolation/clamp behavior, branch conditions, arithmetic and first meaningful consumers as applicable.
- Separate verified facts, hypotheses and unknowns. A name resemblance, shape match, donor label or plausible units is not semantic proof.
- A bounded negative is a valid result when the search method and coverage are stated.
- Reuse named reports, indexes, reader mechanics and ROM/LST anchors. Do not repeat completed scans, helper censuses, inventories or broad searches.
- Do not widen scope merely because a downstream physical meaning remains unresolved. Record the exact stop boundary and create a separate follow-on only when it has a concrete discriminator.

## Git and shared-register discipline

### Temporary integration lock

`CONTROL/INTEGRATION_STATUS.md` is the publication gate. Its state is either `UNLOCKED` or `LOCKED`.

- Before any final commit or push, every worker must fetch/read the current `CONTROL/INTEGRATION_STATUS.md`. Do not rely on a cached copy from startup.
- If the state is `LOCKED`, or the file is missing/unreadable, workers must not publish to shared `main`, push, or modify the shared remote register. They MUST continue independent technical work and may prepare/update their own local WO reports, ID-neutral FND/REC drafts, inventory-pointer edits and lane pending-publication ledger. Do not stage or create commits while locked. A missing/unreadable gate is treated as LOCKED for publication, not as a technical-work stop.
- Only the named integrator may write to the repository while the state is `LOCKED`. Workers must not bypass, remove, or change the lock.
- To acquire the lock, the integrator fetches current `main` and commits `LOCKED`, with owner, start time and purpose, to `CONTROL/INTEGRATION_STATUS.md`. If a concurrent push rejects that update, fetch again and retry against the new main; the lock is not active until the `LOCKED` commit is on remote `main`.
- Once the lock commit is on remote `main`, workers pause publication. The integrator fetches the latest main, reconciles incoming work, verifies the result, and pushes the integrated state.
- To release the lock, the integrator changes the status to `UNLOCKED`, records the integration commit and release time, and pushes that change. Workers resume only after the `UNLOCKED` state is visible on remote `main`.
- If any integration push is rejected, keep the lock `LOCKED`; fetch, reconcile, and retry. Never force-push. Keep the lock brief and release it as soon as synchronization is verified.
- A worker that discovers a lock during closeout must finish the local package and ledger entry, then continue to the next FIFO WO. Do not defer technical closeout or stop the lane merely because publication is locked. After release, refresh main and integrate all of that lane's pending packages as a batch, preserving other lanes' changes.

- Use main only. Do not create branches or PRs.
- No separate claim commit. Do not make interim commits or routine status updates.
- Publish a lane's accumulated pending packages as a batch, not as a separate integration transaction per WO. The batch may contain multiple reports, FND/REC records, index/inventory updates and one consolidated lane-register update. Publish records/reports before marking their WOs CLOSED in the register. A safe multi-file commit is preferred; if separate commits are required, keep the integration lock held until the entire batch is verified. Do not force-push or discard local pending packages.
- A worker may edit only its own WO report, its own lane's queue/status entries, and its own lane's new WO specifications, plus the `FINDINGS/` paths permitted by the mandatory findings-disposition gate. It may append a reconciliation note when supported by its own report. **Limited cross-lane exception:** Worker 1, Worker 3 and the coordinator may append task proposals or evidence-backed review responses to `CONTROL/LOCAL_WORKER2_INBOX.md`; Worker 2 may update proposal dispositions and consume review responses there. This inbox is non-authoritative and cannot create/assign/close a WO or authorize edits to another worker's report. All inbox writes obey the integration lock and readback discipline. No worker may change another lane's assignment, active WO, status or report.
- Before each register write, fetch the latest active_work_orders.md and its current blob SHA. Apply only your own small change. If rejected by a concurrent update, refresh once, preserve the other worker's changes, recompute the edit and retry once. Never overwrite a stale full-file copy. If the safe retry fails, stop repository writes and report the exact error.
- Verify every report, FND/REC record, index/inventory update and consolidated register change in the batch by remote readback. Only then remove its items from the local pending ledger or mark them published. Do not poll during technical work.
- Use explicit file paths for staging/commits. Never use broad add-all or cleanup operations.

## Closeout and stop conditions

- CLOSED — BOUNDED COMPLETE means the issued question was answered to its stated boundary, including a supported negative or unresolved external endpoint.
- BLOCKED is reserved for a genuinely unavailable required input/dependency. Explain the exact missing item and continue with another independent WO in your lane when possible.
- Do not leave a bounded, completed investigation active merely because physical semantics or a later external endpoint remain unknown.
- Stop only when your lane has no ready task and no defensible new question, a genuine technical/authorization blocker prevents safe work, or a repository write fails after one safe retry. Do not wait for another worker.

## Protected and user-owned material

Unless a specific WO explicitly authorizes the exact change, do not modify ROMs, LSTs, XML definitions, A2L files, workbooks, calibration catalogues, evidence indexes, scripts, tools or Library content.

All ignored, untracked and user-owned local files are protected. A .gitignore rule is not permission to inspect, read, open, move, rename, delete, back up, stage, commit, force-add or otherwise alter a protected file. Do not use git clean, reset --hard, broad checkout/restore, git add ., or git add -A.

In particular, using youtube videos.txt is a user-owned local file and must remain untouched and uncommitted. Do not open it, alter it, move it, delete it, back it up, stage it, commit it or force-add it. The .gitignore entry only keeps it out of ordinary Git status; it does not change ownership or grant permission.

## One-glance lane rules

| Slot | Owns |
|---|---|
| Worker 1 | Explicitly assigned Worker 1 tasks; new IDs where ID mod 3 = 1 |
| Worker 2 | Explicitly assigned Worker 2 tasks; new IDs where ID mod 3 = 2 |
| Worker 3 | Explicitly assigned Worker 3 tasks; new IDs where ID mod 3 = 0 |

No first-pick gate or coordinator dependency. Lanes do not wait on one another for assignment or technical execution; they pause repository publication only while `CONTROL/INTEGRATION_STATUS.md` is `LOCKED`. Each lane investigates, reconciles, closes and replenishes itself.
