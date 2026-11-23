# EL19A — Operational Control and Work-Order Register

**Operational authority:** This file is the sole current source of truth for work-order lifecycle, assignments, priorities, continuation, and handoff. Technical evidence belongs in individual `WO<ID>.md` records.
**Repository:** `ihatealladvertising/EL19A-` · **Authority branch:** `main` · **Updated:** 2026-11-23
**Update rule:** Re-read the latest authoritative register before each change. Make one minimal register update per commit and verify it by readback. Do not maintain a parallel operational notebook.
**History:** The full pre-compaction register from this branch is preserved in [the 2026-11-20 archive snapshot](active_work_orders_archive_2026-11-20.md). It is historical only. Later base-branch updates are summarized below; their technical details are in the individual WO records.

## Autonomous worker-lane protocol (effective 2026-11-22)

The controlling execution rules are in [CONTROL/WORKER_PROTOCOL.md](WORKER_PROTOCOL.md). The three lanes operate independently; no ChatGPT/coordinator assignment, first-pick gate, runtime approval or cross-worker wait is required.

| Slot | Current assigned work | Ownership |
|---|---|---|
| Worker 1 | WO65281 | WO65278 CLOSED — BOUNDED COMPLETE (sole direct writer of FFFF158C = mov.w r5,@(r0,r14) at 0x66E6A, value sub_22F80(0x10286,0x1072C,U16[FFFF16C2]); query = FFFF99E7.bit0-gated copy of FFFF84FE; corrected WO65254 FFFF11C2->FFFF16C2, WO65097 FFFF8500->FFFF84FE, WO64868 0x8B52 gate misattribution); backlog WO65284->WO65290->WO65299->WO65302->WO65308->WO65263 → WO65323 |
| Worker 2 | WO65282 | WO65226 CLOSED — BOUNDED COMPLETE; WO65229 CLOSED — BOUNDED COMPLETE; WO65232 CLOSED — BOUNDED COMPLETE; WO65235 CLOSED — BOUNDED COMPLETE; WO65225 CLOSED — BOUNDED COMPLETE; WO65231 CLOSED — BOUNDED COMPLETE; WO65234 CLOSED — BOUNDED COMPLETE; WO65237 CLOSED — BOUNDED COMPLETE; WO65238 CLOSED — BOUNDED COMPLETE; WO65241 CLOSED — BOUNDED COMPLETE; WO65246 CLOSED — BOUNDED COMPLETE; WO65249 CLOSED — BOUNDED COMPLETE; WO65252 CLOSED — BOUNDED COMPLETE; WO65258 CLOSED — BOUNDED COMPLETE; WO65261 CLOSED — BOUNDED COMPLETE; WO65279 CLOSED — BOUNDED COMPLETE; queued WO65285, WO65288, WO65291, WO65294, WO65297, WO65300, WO65303, WO65306, WO65309 — READY |
| Worker 3 | WO65310 | WO65293 CLOSED — BOUNDED COMPLETE (3D ignition/fuel triage: hypothesis weakened, 8 ranked leads, no sink reached); WO65310 promoted to current P1; FIFO backlog WO65313→WO65316→WO65319 (user-queued MR16DDT crosswalk)→WO65322 → WO65325 |

**Ordered READY backlog (FIFO; one WO at a time per lane):**

| Lane | Queue order after current WO | Depth |
|---|---|---:|
| Worker 1 | WO65284 → WO65290 → WO65299 → WO65302 → WO65308 → WO65263 → WO65323 | 7 |
| Worker 2 | WO65285 → WO65288 → WO65291 → WO65294 → WO65297 → WO65300 → WO65303 → WO65306 → WO65309 | 9 |
| Worker 3 | WO65313 → WO65316 → WO65319 → WO65322 → WO65325 | 5 |

- **Availability:** Workers 1–3 may start their own READY work immediately and continue independently. No cross-lane wait or coordinator approval is required.
- **Lane ownership:** each worker works only WOs explicitly assigned to its slot. Existing WOs keep the explicit lane recorded here or in their queue row.
- **Future IDs:** new WOs after 65217 use ID modulo 3: remainder 1 → Worker 1; remainder 2 → Worker 2; remainder 0 → Worker 3. A worker creates and owns only its own lane's new WOs.
- **Queue replenishment:** maintain at least three READY follow-on WOs per lane beyond the current task where defensible technical questions exist. Workers execute FIFO, one WO at a time, and replenish after closeout without waiting for a user prompt. The buffer is not a filler quota; every WO must be bounded, distinct and evidence-led.
- **Lifecycle:** an ASSIGNED — WORKER N — READY row reserves the task to that slot. No separate claim commit is needed. A worker updates only its own WO report, its own queue/lifecycle entries, and its own new-WO specifications.
- **Reconciliation:** each worker reconciles directly related earlier findings before closeout. Corrections are additive, source-linked records; no worker silently edits another worker's report or changes another lane's status.
- **Shared main:** no feature branches or PRs. Re-read the latest register SHA before each write; on a conflict refresh once, preserve other lanes' changes and retry once.
- **Protected material:** no protected artifact edits without WO-specific authorization. Ignored and user-owned local files remain untouched regardless of .gitignore rules; using youtube videos.txt remains user-owned, uncommitted and untouched.

**Current queue state (2026-11-23):** Worker 1 current → WO65281; READY backlog → WO65284 → WO65290 → WO65299 → WO65302 → WO65308 → WO65263 → WO65323. Worker 2 current → WO65282; READY backlog → WO65285 → WO65288 → WO65291 → WO65294 → WO65297 → WO65300 → WO65303 → WO65306 → WO65309. Worker 3 current → WO65310; READY backlog → WO65313 → WO65316 → WO65319 → WO65322 → WO65325. WO65293 is CLOSED — BOUNDED COMPLETE. WO65319 is the user-queued MR16DDT/Juke architecture crosswalk. WO65322 is this lane's bounded follow-on from WO65293 lead 3; it was drafted as WO65319, but that ID was taken concurrently by the user's WO65319, so it was renumbered before any commit. Worker 1 and Worker 3 are authorized to start their current READY tasks; Worker 2 may start WO65282. Worker 1's high-payoff queue was reordered to WO65287 → WO65296 → WO65305; WO65263 is deferred to the end of its remaining backlog. Worker 1's prior WOs WO65242, WO65245, WO65248, WO65251, WO65254, WO65257, WO65260, WO65287, WO65296, WO65305, WO65266, WO65275 and WO65278 are CLOSED — BOUNDED COMPLETE. Worker 2's prior WOs WO65225, WO65226, WO65229, WO65231, WO65232, WO65234, WO65235, WO65237, WO65238, WO65241, WO65246, WO65249, WO65252, WO65258, WO65261 and WO65279 are CLOSED — BOUNDED COMPLETE. WO65206 remains blocked by the negative WO65204 alignment and is not assigned to either lane. The semantic workstream remains within the three execution lanes; no task is live unless listed in the current lane table.

**User-authorized lane transfer — 2026-11-23:** WO65293 was an unstarted READY Worker 1 task. At the user's direction, it is transferred to Worker 3 to run the bounded 3D ignition/fuel semantic triage in parallel with Worker 1's end-to-end ignition/map/fuel investigations. WO ID, technical scope, dependencies and stop conditions are unchanged; the WO report records Worker 3 as current owner and retains its original modulo-3 allocation as historical metadata. Worker 1's high-payoff queue was reordered to WO65287 → WO65296 → WO65305; WO65263 is deferred to the end of its remaining backlog.

**User-authorized lane transfer — 2026-11-22:** WO65226, WO65229, WO65232, WO65235, WO65238 and WO65241 were unstarted READY tasks in Worker 3's FIFO queue. At the user's direction, all six were transferred to Worker 2 without changing IDs, technical scope, dependencies or order. WO65226 and WO65229 are CLOSED — BOUNDED COMPLETE; WO65232 and WO65235 are CLOSED — BOUNDED COMPLETE; WO65241 and WO65246 are CLOSED — BOUNDED COMPLETE; the remaining two form its FIFO backlog. Worker 3 is offline and now has no assigned task or backlog. Original modulo-3 allocations remain historical metadata. WO65240 and WO65243 were found as extra READY artifacts in the fetched main snapshot; per the user's lane-state correction they are withdrawn from the active pool and retained only as non-operative records.

## Current project assets and operational frontier

- **Current workbook:** `WORKBOOK/EL19A_Master_Reverse_Engineering_Workbook_V58_WO65114_ThinReferenceCloseout_2026-11-21.xlsx` (149 sheets).
- **Current XML baseline:** `public/assets/aistudio/EL19A_merged_definition_v3_08a300db.xml` (`EL19A_Merged_Spec_v3`: 76 tables, 7 verified and 69 `[S]`) plus `EL19A_ignition_decoded_fragment_33ea8e67.xml` (6 ignition/knock tables).
- **Discovery staging:** `CALIBRATIONS/discovered_tables_catalog.csv` (179 helper/reader-verified varying tables absent from XML v3).
- **Live execution authority:** use only the lane table and FIFO queues in the autonomous worker-lane protocol above. The older paused/reserved queue snapshot previously placed here is superseded and must not be used for assignment or status. Current assignments are Worker 1 → WO65281 and Worker 3 → WO65310 (backlog includes the user-queued WO65319); Worker 2 current → WO65282. Worker 1, Worker 2, and Worker 3 may start immediately, one WO at a time per lane.
- **Blocked:** WO65206 remains blocked by the negative WO65204 alignment and is not assigned to either active lane. **Withdrawn from active pool:** WO65240 and WO65243 (retained as non-operative artifacts only).
- **Closed/reconciled history:** prior closeouts and technical reconciliations remain recorded below and in their individual WO reports; they do not override the live lane table.

## Queued work orders — allocated 2026-11-21

Allocated from the ranked candidate list supplied by the user. Allocation only: no investigation has been performed and no technical finding is claimed. WO65102 closed after allocation, so every queued WO is unblocked except WO65113, which waits on external material. This is a legacy allocation record. Current ownership is explicitly assigned in the autonomous worker-lane protocol and current operational frontier above.