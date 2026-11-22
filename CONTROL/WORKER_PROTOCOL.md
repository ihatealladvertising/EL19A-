# EL19A Worker Protocol

**Operating mode:** Repository-driven autonomous execution. The three worker sessions are the operating system for investigation, technical prioritization, reconciliation and queue replenishment. No coordinator, ChatGPT session or user action is required between ordinary work orders.

**Authority:** CONTROL/active_work_orders.md is the sole live queue and lifecycle authority. This file defines execution rules. These rules supersede older coordinator-only, cross-worker waiting, parity-pick, self-selection prohibition, separate-branch and PR instructions retained in historical notes.

## Start prompts

Run exactly one session per slot:

- Worker 1: "You are Worker 1. Follow CONTROL/WORKER_PROTOCOL.md and run your autonomous lane until no defensible work remains."
- Worker 2: "You are Worker 2. Follow CONTROL/WORKER_PROTOCOL.md and run your autonomous lane until no defensible work remains."
- Worker 3: "You are Worker 3. Follow CONTROL/WORKER_PROTOCOL.md and run your autonomous lane until no defensible work remains."

Never run two sessions under the same slot. All three slots may start immediately. No slot waits for another slot to claim, finish, or authorize work.

## Worker lanes and collision prevention

All work is committed directly to shared main. No feature branches, PRs, merges, cherry-picks, resets, force-pushes or history rewrites.

**Live assignments are defined only by `CONTROL/active_work_orders.md`.** Do not use historical queue tables or older assignment notes embedded elsewhere in the register to infer current ownership. A closed WO is not an active assignment even if an old paragraph still names its former owner. Explicit current lane assignments in the live register override the modulo rule for already-existing WOs.

Each slot owns its lane. It selects only its own READY/ASSIGNED work in the live register, performs one WO at a time, and updates only its own lane's lifecycle records. Do not borrow another slot's WO, change another slot's owner/status, or wait for another slot.

**New WO ID allocation is collision-free by lane:** for WOs created under this protocol, assign by ID remainder:
- ID mod 3 = 1: Worker 1
- ID mod 3 = 2: Worker 2
- ID mod 3 = 0: Worker 3

Start at the next unused WO ID after 65217. Advance by 3 until the ID is absent from both the register and CONTROL/WO<ID>.md. Legacy assignments listed in the register remain assigned as written; do not renumber or reassign them. A worker creates new WOs only in its own modulo lane. This makes concurrent WO creation use distinct IDs and report paths.

One session per lane plus explicit lane ownership prevents duplicate task execution. The register's SHA protects concurrent writes to the shared queue; it is not a reason to introduce cross-worker waiting.

## Autonomous execution loop

Repeat this loop for the lifetime of the worker session:

1. At startup only, read this protocol and the current operational frontier in active_work_orders.md. Find the current WO and the ordered FIFO backlog for your lane. The next task is the earliest READY item. Do not re-read the protocol or inventory the repository on every iteration.
2. If CONTROL/WO<ID>.md already exists, read it. If an assigned legacy WO has no report file yet, the queue row and its cited dependencies in active_work_orders.md are the authoritative specification: create CONTROL/WO<ID>.md with the objective, exact scope, owner, branch main, authorized paths, dependencies and stop boundary from that register entry. This is execution setup, not a separate claim commit; do not invent or widen scope.
3. Perform the technical investigation to the specified stop boundary. Spend the effort on tracing, verification and interpretation, not administration.
4. Before closeout, perform a bounded reconciliation against the exact prior findings cited by the WO and any directly affected claims discovered during the investigation. Distinguish confirmed corrections from hypotheses.
5. Write the full result to your own CONTROL/WO<ID>.md report. Include verified facts, evidence anchors, calculations/branches, confidence, limits, no-repeat notes, changed paths and commit SHA.
6. Close the WO in active_work_orders.md, update your lane's current/closed summary, and record any reconciliation disposition. Do not seek coordinator review or approval for a bounded closeout.
7. Check your own lane. If a READY WO exists, take the earliest item in the lane's FIFO backlog immediately; execute only one WO at a time. If the backlog is below its target depth, replenish it under the technical-priority and WO-creation rules below. Continue without waiting for another slot or user prompt.

An existing ASSIGNED — WORKER N — READY entry reserves that task to its slot. Multiple READY entries may exist in a lane's FIFO backlog; they are not permission to execute concurrently. No separate claim commit is required. A worker may start only the earliest READY item after closing its current WO. Do not create routine claim, heartbeat, progress, handoff or status-polling commits. The current WO remains assigned to its slot until its closeout is recorded.

## Technical direction and WO replenishment

Workers are responsible for maintaining technical direction inside their own lanes. Do not wait for ChatGPT or a coordinator to invent the next WO.

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

Create CONTROL/WO<ID>.md and add its queue row to active_work_orders.md with your slot ownership, priority, dependencies, branch main and exact allowed paths. Use the modulo ID rule above. Never create placeholder/filler tasks to keep the queue count high. If no defensible task exists, record the specific exhausted boundary in your lane's latest closeout and stop.

Maintain a target backlog of **three READY follow-on WOs per lane**, in addition to the current in-progress WO. This is an operating buffer, not a limit: an explicit user request may authorize a larger queue. Queue tasks in a clear FIFO order; all queued WOs remain assigned to their modulo lane, but the worker starts only the earliest READY item and never runs two WOs concurrently in the same lane. Create replacements as work is completed so the buffer is replenished without a user prompt. Do not create filler: every queued WO must have a distinct, defensible technical question, exact scope, reuse/no-repeat boundary and stop condition. Do not queue work already covered, completed or blocked by an unavailable dependency.

## Reconciliation rules

Reconciliation is a normal part of every lane, not a coordinator-only duty.

- Compare new findings with the specifically relevant earlier WO reports and register claims. Reuse exact evidence and report anchors; do not conduct broad archive audits by default.
- If the current WO resolves a contradiction within its scope, state the old claim, corrected claim, evidence and confidence in the new report; append a concise reconciliation entry to the register.
- Never silently edit, overwrite or relabel another worker's report. Preserve it as historical evidence. A correction or synthesis is additive and points to both the old and new records.
- If a contradiction extends beyond the current scope, create a bounded reconciliation WO in your own lane, with both source reports as dependencies. Do not leave a known material conflict unrecorded.
- Do not mark another worker's WO closed or blocked. Each slot owns its own task lifecycle. Cross-lane observations may be recorded as findings or dependencies, but not as reassignment instructions.
- Keep status (active/closed/blocked), technical result (positive/negative/partial), and unresolved semantic boundary separate.

## Evidence and technical standards

- Record exact instruction PCs/listing anchors, effective addresses, widths, signedness, query and axis construction, search/interpolation/clamp behavior, branch conditions, arithmetic and first meaningful consumers as applicable.
- Separate verified facts, hypotheses and unknowns. A name resemblance, shape match, donor label or plausible units is not semantic proof.
- A bounded negative is a valid result when the search method and coverage are stated.
- Reuse named reports, indexes, reader mechanics and ROM/LST anchors. Do not repeat completed scans, helper censuses, inventories or broad searches.
- Do not widen scope merely because a downstream physical meaning remains unresolved. Record the exact stop boundary and create a separate follow-on only when it has a concrete discriminator.

## Git and shared-register discipline

- Use main only. Do not create branches or PRs.
- No separate claim commit. Do not make interim commits or routine status updates.
- Make one final technical report commit. Then make one minimal register closeout/replenishment commit. If the available Git operation supports a safe multi-file commit, they may be combined.
- A worker may edit only its own WO report, its own lane's queue/status entries, and its own lane's new WO specifications. It may append a reconciliation note when supported by its own report. It must not change another lane's assignment, active WO, status or report.
- Before each register write, fetch the latest active_work_orders.md and its current blob SHA. Apply only your own small change. If rejected by a concurrent update, refresh once, preserve the other worker's changes, recompute the edit and retry once. Never overwrite a stale full-file copy. If the safe retry fails, stop repository writes and report the exact error.
- Verify the committed report and register state by readback. Do not poll during technical work.
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

No first-pick gate. No cross-worker waiting. No coordinator dependency. Each lane investigates, reconciles, closes and replenishes itself.
