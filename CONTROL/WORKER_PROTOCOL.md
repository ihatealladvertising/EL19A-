# EL19A Worker Protocol

**Operating mode:** Three workers share one evidence-led task system. Workers 1 and 3 provide investigation and direction; Worker 2 is the local execution worker. The live register is the only task queue. Keep worker instructions and handoffs simple.

**Authority:** CONTROL/active_work_orders.md is the sole live queue and lifecycle authority. This file defines execution rules. These rules supersede older coordinator-only, parity-pick, self-selection prohibition, separate-branch and PR instructions retained in historical notes. Ordinary technical work remains independent across lanes; the temporary integration lock below is the only cross-lane publication pause.

## Start prompts

Run exactly one session per slot:

- Worker 1: "Use the QUICK START block in CONTROL/active_work_orders.md. Run your FIFO, one WO at a time. When you create a bounded routine trace suitable for local execution, assign it directly to Worker 2. Follow the WO's evidence and closeout rules."
- Worker 2: "Open CONTROL/active_work_orders.md, read QUICK START, and execute the first READY WO assigned to Worker 2. Read that WO and only its cited dependencies. Do not scan register history, create tasks or change priorities. After closeout, take the next READY WO. Stop when none remain."
- Worker 3: "Use the QUICK START block in CONTROL/active_work_orders.md. Run your FIFO, one WO at a time. When you create a bounded routine trace suitable for local execution, assign it directly to Worker 2. Follow the WO's evidence and closeout rules."

Never run two sessions under the same slot. All three slots may start immediately. No slot waits for another slot for assignment or technical execution. Workers must observe the temporary integration lock before publishing repository changes.

## Artifact-first reporting and completion gate — all workers

**The repository work-order artifacts are the deliverable. Chat is only a handoff channel.** This rule applies to Workers 1, 2 and 3 and overrides any prompt or habit that treats a detailed chat response as work-order closeout.

1. **Write the result to the authorized artifact path.** The primary report is `CONTROL/WO<ID>.md`, unless the WO explicitly specifies another report path. Put the substantive result there: objective and scope, methods/commands, inputs, observations, evidence anchors, results, limitations, unresolved items, exact changed/output paths, and the mandatory Findings disposition. Create every required machine-readable output (for example TSV/CSV/JSONL) at the exact path authorized by the WO. A summary in chat is never a substitute.
2. **Verify the artifact by reading it back.** After writing, reopen/read the complete report and every required output from the repository working copy or repository API. Confirm the files exist at the expected paths, are non-empty where appropriate, contain the expected sections/rows, and match the result you intend to report. For machine-readable files, perform a bounded structural check (headers, row counts, required fields, and representative records). Record the verification performed in the report. Do not claim an artifact is recorded merely because content was drafted in memory or printed in chat.
3. **Respect the integration gate.** If the gate is UNLOCKED and the WO/protocol authorizes publication, publish the complete authorized artifact set using the repository procedure, then fetch/read back each published artifact from remote `main` and record its commit/blob identity. If the gate is LOCKED, do not publish; write and verify the local report and outputs, mark the package `PUBLICATION-PENDING`, and record it in the lane's pending-publication ledger as required by `CONTROL/INTEGRATION_PROCEDURE.md`. A locally recorded pending package is not a remotely closed WO.
4. **Completion is evidence-based.** A WO may be described as locally complete only after its report and required outputs have been written and read back successfully. It may be described as remotely closed only after all required artifacts and lifecycle changes have been published and read back from remote `main`. If writing, reading back, or validating any required artifact fails, mark the task BLOCKED / NOT COMPLETE, state the exact failure, and stop at the WO boundary. Never paste the missing report into chat and call that a workaround.
5. **Chat is a compact handoff only.** After the artifact gate is satisfied, send only: WO ID; status (`PUBLICATION-PENDING`, `PUBLISHED`, or `BLOCKED / NOT COMPLETE`); report path; required output paths; commit/blob identity when published; and any material blocker or next dependency. Do not reproduce the full findings, tables, logs, or report body in chat unless the user explicitly asks for them.
6. **No silent artifact omission.** If the WO's required output path is missing or ambiguous, stop and resolve the ambiguity through the authorized project process before execution. Do not silently replace a required file with chat text, a screenshot, an untracked temporary file, or a differently named artifact.
7. **Worker 2 applies this gate without exception.** Worker 2 is local-execution-only: it must record and verify its report and authorized outputs before sending the compact handoff. It must not publish, commit, push, alter the live register, or perform repository administration unless a separate explicit authorization says otherwise. Posting a detailed result in chat does not complete Worker 2's assignment.

The report artifact, verified output files and publication state are the durable record. Chat messages are not part of the evidence archive and must not be used as the sole location for results.

## Worker lanes and collision prevention

All work is committed directly to shared main when the integration status is UNLOCKED. No feature branches, PRs, merges, cherry-picks, resets, force-pushes or history rewrites.

**Live assignments are defined only by `CONTROL/active_work_orders.md`.** Do not use historical queue tables or older assignment notes embedded elsewhere in the register to infer current ownership. A closed WO is not an active assignment even if an old paragraph still names its former owner. Explicit owner and FIFO placement in the live register determine every WO. WO numbers do not encode worker ownership.

Each slot owns its lane. It selects only its own READY/ASSIGNED work in the live register and performs at most one active investigation at a time. It may accumulate multiple technically completed, publication-pending WOs in FIFO order while continuing later READY work, including while the integration gate is LOCKED. It updates only its own lane's lifecycle records when the batch is published. Do not borrow another slot's WO, change another slot's owner/status, or wait for another slot.

**New WO IDs are global and sequential.** Use the next unused number after the highest existing WO ID; ownership is stated explicitly in the WO and live register, not encoded in the number. Before creating a report, refresh the register and confirm the report path is absent. Create the report, then add its queue row. If another worker creates the same path first, refresh and take the next unused number. If the register update conflicts, refresh and retry once. Never renumber existing WOs.

Workers 1 and 3 may create WOs for their own lanes or create fully specified, local-execution-suitable WOs assigned directly to Worker 2. A Worker 2 task must be added to Worker 2's READY FIFO with owner/status explicit; after registration, Worker 2 owns execution and the creator must not change its lifecycle. Worker 2 executes its FIFO and does not create or prioritize new tasks.

**Explicit user-directed transfer exception:** A direct user instruction may transfer an existing, unstarted READY WO to another slot when a lane is offline or exhausted. This is an exception to the default no-reassignment rule. Preserve WO IDs, technical scope, dependencies, evidence anchors, no-repeat boundaries and FIFO order. In one atomic `main` commit, update the WO report's assigned status, owner and sequencing language together with the live register's current/backlog entries. Retain original ownership/allocation as historical metadata; the updated live register determines the current owner. Do not transfer in-progress work unless the user explicitly names it and the handoff boundary is recorded. This makes concurrent WO creation use distinct IDs and report paths.

One session per lane plus explicit lane ownership prevents duplicate task execution. The register's SHA protects concurrent writes to the shared queue. The integration lock is a short, explicit exception: it serializes publication only, not technical work or task assignment.

## Worker 2 — local execution role

Worker 2 uses the local model and executes only its own FIFO in `CONTROL/active_work_orders.md`. It does not set project strategy, invent tasks, allocate work, or maintain a separate inbox/profile.

Workers 1 and 3 supply Worker 2 directly: when they identify a useful bounded trace that does not require premium-level semantic synthesis, they create a complete WO with **Owner: Worker 2** and add it to Worker 2's READY FIFO. Suitable tasks include bounded caller/callee traces, RAM reader/writer provenance, lookup-query mechanics, branch/delay-slot verification, and first-consumer traces. The task must include exact addresses/functions, available dependencies, evidence to reuse, no-repeat boundaries and a clear stop condition. Do not send vague proposals; create the actual WO.

Worker 2 takes the earliest READY task, follows its stated scope and the normal evidence/Findings closeout rules, then continues to the next READY task. If evidence is ambiguous, record the uncertainty and stop at the WO boundary; do not guess or expand scope. If its queue is empty, it stops. Workers 1 and 3 replenish it during their normal queue-generation work when defensible local tasks exist. No separate proposal, review-response or approval workflow is used.

## Autonomous execution loop

Repeat this loop for the lifetime of the worker session:

1. At startup, read only the QUICK START block in `CONTROL/active_work_orders.md` and open the first READY WO assigned to you. Read that WO and only its named dependencies. Do not parse historical register summaries or inventory the repository. Worker 2 must not read beyond the quick-start block to locate its task.
2. If CONTROL/WO<ID>.md already exists, read it. If an assigned legacy WO has no report file yet, the queue row and its cited dependencies in active_work_orders.md are the authoritative specification: create CONTROL/WO<ID>.md with the objective, exact scope, owner, branch main, authorized paths, dependencies and stop boundary from that register entry. This is execution setup, not a separate claim commit; do not invent or widen scope.
3. Perform the technical investigation to the specified stop boundary. Spend the effort on tracing, verification and interpretation, not administration.
4. Before closeout, perform a bounded reconciliation against the exact prior findings cited by the WO and any directly affected claims discovered during the investigation. Distinguish confirmed corrections from hypotheses.
5. Complete the mandatory **findings-disposition analysis** below for this WO. Decide PROMOTED, NOT REQUIRED or DEFERRED and prepare all required FND/REC content. A material result must never exist only in WO prose. When publication is available, create/read back the actual records and index entries. While publication is paused, prepare ID-neutral finding/reconciliation drafts keyed to this WO; do not reserve or invent global FND/REC IDs.
6. Write the full result to your own `CONTROL/WO<ID>.md` report and prepare a complete local closeout package. Include verified facts, evidence anchors, calculations/branches, confidence, limits, no-repeat notes, the findings disposition block, required FND/REC drafts, supported inventory-pointer edits, and a list of exact changed paths. Mark the package `PUBLICATION-PENDING` until remote publication and readback succeed. Record it in your lane's local pending-publication ledger as specified in `CONTROL/INTEGRATION_PROCEDURE.md`.
7. Do not mark a WO remotely CLOSED, update the remote lane summary, or claim that Findings records are published until its complete package has been published and read back from remote `main`. A locally complete package is not a remotely closed WO. When UNLOCKED, publish accumulated packages in FIFO order; close each WO in the register only after its report, actual FND/REC records, index and supported inventory pointers have passed remote readback. Do not seek coordinator approval for a bounded promotion within this standing authorization.
8. After the local package is complete and recorded, immediately take the earliest READY WO in your lane's FIFO backlog, even if earlier packages are still publication-pending. Maintain at most one active investigation per lane, but allow any number of completed pending packages. Workers 1 and 3 replenish queues under the technical-priority rules below. Worker 2 does not create or prioritize WOs; when its FIFO has no READY item, stop cleanly until a new task is assigned.

An existing ASSIGNED — WORKER N — READY entry reserves that task to its slot. Multiple READY entries may exist in a lane's FIFO backlog; they are not permission to execute concurrently. No separate claim commit is required. A worker may start only the earliest READY item after completing and locally recording the preceding WO's package; remote publication is not required to advance. Do not create routine claim, heartbeat, progress, handoff or status-polling commits. The active WO remains assigned to its slot until its remote closeout is published; its local pending package must remain separately identifiable and must not be overwritten.

## Tool-first ROM engineering objective

The primary project deliverable is a deterministic, modular, read-only ROM engineering toolkit, initially targeting SH7055 and SH7058 SuperH firmware. The existing Nissan EL19A project is the first end-to-end validation corpus. Completion of the EL19A RomRaider definition is a generated byproduct of the toolkit's discovery, structural verification, symbol cross-reference and export pipeline; it is not a separate priority that competes with reusable tool development.

Keep the shared core processor- and ECU-neutral. Put CPU behavior in processor backends, memory maps and fingerprints in explicit profiles, and container/A2L/XML handling in format adapters. Preserve independently executable commands over shared libraries. Reuse existing proven modules incrementally; do not duplicate helper discovery or create a monolithic rewrite.

### Current architecture gate — preserve existing FIFO

The registered architecture work remains the immediate work:
- **WO70020 — Worker 1:** inventory existing tools and define migration boundaries.
- **WO70021 — Worker 3:** specify the shared ROM/address/calibration/reader/evidence data model and JSON interchange; it remains behind Worker 3's current FIFO-head dependency.
- **WO70022 — Worker 2:** audit Python/runtime/dependencies/test/CI readiness; it remains behind Worker 2's current FIFO-head dependency.

Do not interrupt, reassign, reorder or bypass these tasks. After their reports are complete, reconcile the results into one implementation-ready architecture before allocating implementation work. Workers continue to follow the live register and integration protocol; this objective does not change queue authority.

### Tool implementation priorities

After the architecture reports are reconciled, create bounded implementation WOs in this order, adjusting only where the inventory or data-model results demonstrate a better reuse boundary:

1. **Regression foundation:** synthetic tests for ROM loaders, address mappings, helper/call exports, duplicate and conflicting geometries, missing/unresolved fields, parser edge cases, deterministic output and complete manifests. Keep ordinary tests independent of protected project ROM/A2L files.
2. **First working vertical slice:** wire the existing SH7058 scanner's per-call exporter into the shared model/workbench; group observations into one per-address calibration-candidate record without discarding individual calls, disagreements or unresolved context. Complete the run manifest and attributable output package.
3. **ROM/address core and profiles:** preserve original container and decoded image identity; distinguish file offsets, ROM effective addresses and RAM addresses; validate processor/memory profiles and region bounds. BIN is the first supported input path.
4. **Relational metadata and symbol cross-reference:** index A2L object relationships and current XML/catalogue/scope sources. Attach exact-address, axis-link, helper/function-context, payload/shape and subsystem-neighbor matches as typed hypotheses with immutable source hashes.
5. **Optional evidence providers:** integrate EL19A static access/GBR/diagnostic/variant datasets only through hash-validated, explicitly typed adapters. Missing or stale optional inputs must be visible as unavailable.
6. **Definition output:** derive conservative RomRaider XML from verified structural records and current Findings/Reconciliation state. Produce a build manifest and validation report; never silently replace the selected baseline.

The first usable milestone is a supported SH7058 BIN producing a deterministic per-address JSONL catalogue, derived CSV/TSV review exports, per-call evidence and a full run manifest. Report scan coverage and unresolved boundaries; do not claim exhaustive table discovery or complete semantic proof.

### Target facts and symbol hypotheses must remain separate

- **Target structural facts** may be established from the target ROM bytes plus reproducible scanner/catalogue evidence: effective address and address-space mapping, element type/width/signedness, exact bounded extent, dimensions/geometry, byte order and payload identity. Full reader mechanics, query reconstruction, interpolation/clamp behavior and downstream consumer tracing are **not prerequisites** for a structurally supported raw/provisional entry.
- **Reader/runtime enrichment** (exact caller, query source and transforms, search/interpolation/clamp mechanics, result staging and downstream consumer) is recorded when already available or when needed to resolve a structural conflict or establish a semantic claim. Do not trace every candidate merely to qualify it for raw/provisional inclusion.
- **Donor hypotheses** include A2L names/units/conversions, sibling-ROM payload or shape matches, variant differences and external symbol associations. Retain source IDs/hashes and match basis. Exact-payload and same-geometry donor matches are corroborating confidence signals, not mandatory inclusion gates; they cannot populate target-side names, units, physical axes or scaling as proven facts.
- Preserve duplicate declarations, competing geometries, unresolved references and unsupported metadata. Use null/unresolved states rather than guessed values.
- A helper call, candidate base or donor match does not alone prove a complete table structure. Verify the target-byte extent and geometry, preserve conflicts, and retain the limitations of nearest-prologue caller candidates or bounded register-window heuristics.

### EL19A RomRaider byproduct — downstream acceptance

For the first EL19A profile, the tool should generate a conservative definition from target-side structures and the current Findings/Reconciliation state. Preserve owner-directed presentation decisions separately from firmware facts.

Each generated object must receive one release disposition:

- **INCLUDE — ESTABLISHED:** address/extent, storage type, geometry, usable axes and displayed scaling are supported; any physical name and units included in the definition are supported.
- **INCLUDE — RAW/PROVISIONAL:** target address, element type/width, byte order, exact extent and dimensions/geometry are structurally supported, but function, physical axes/query domain, units, conversion or consumer remain unresolved. Use a generic non-misleading name, raw scaling and explicit sample-index axes where a physical axis is not established.
- **EXCLUDE / HOLD:** address mapping, storage type/width, exact extent or dimensions/geometry cannot be established from target evidence, or material structural conflicts/overlaps prevent a non-misleading object. Missing reader mechanics, physical query semantics or downstream consumer evidence alone is not an exclusion reason.

The generated EL19A definition must identify the exact ROM, load successfully in RomRaider, represent correct address/extent/type/byte order/dimensions and any structurally established orientation, use a supported physical axis/conversion only when established (otherwise an explicit index axis and raw scaling), label provisional objects, and include a build manifest tied to the source XML baseline, ROM hash, Findings index revision, included/excluded objects and unresolved issues. Validation is static/offline; no live-vehicle testing is part of acceptance.

### Efficient work-order rules

- Keep WOs bounded and reusable; batch related structures when one method answers them, and avoid one WO per address by default.
- Do not create filler or maintain a fixed queue depth. Create work only where there is a distinct payoff and a real dependency or available worker.
- Route complete, routine extraction/caller/reader tasks to Worker 2 where suitable; Worker 2 remains execution-only and follows its FIFO.
- Preserve FIFO and one active investigation per lane. Multiple completed publication-pending packages remain permitted under the integration procedure.

The 1D scalar/limiter sweep over `0x7800–0x9B00` remains complete under WO65090. Do not repeat it. Reuse existing reader indexes, helper crosswalks, maps, curves, Findings records and prior bounded negatives.

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

Run the review defined in `CONTROL/PROJECT_KNOWLEDGE_PROCESS_REVIEW.md` every 25 additional WO closeouts across all lanes or every 30 calendar days, whichever comes first. A user-requested process review or a material protocol change may trigger one sooner. The first worker/session to observe the due trigger performs it; check the review log first to avoid duplicate work. This is a short repository-only maintenance review, not a new technical WO and not authority to alter another lane's lifecycle.

Use the five required lenses: knowledge coverage, contradictions, investigation efficiency, method improvement and fresh-session context integrity. Record a compact dated entry in the review log, including concrete actions or explicit no-change dispositions. Promote material calibration interpretations through the Findings system; preserve prior claims with additive reconciliation. Promote reusable methods to durable repository documentation. Do not treat chat history or saved memory as a substitute for missing repository evidence.

The acceptance test is whether a competent investigator without conversation access can resume from repository files without repeating major investigations or inheriting incorrect assumptions. Mark PASS only after checking the live register, protocol, findings/reconciliation index, recovery guide, current calibration baseline/build state and relevant linked reports. Otherwise mark PARTIAL or FAIL and name the blockers.

## ChatGPT context recovery

A fresh ChatGPT session must follow `CONTROL/CHATGPT_CONTEXT_RECOVERY.md`. Start with the live operational register, then this protocol and the findings index; read current WO reports and source evidence as required. Do not treat saved memory, chat summaries or stale `PROJECT_STATE.md` snapshots as authoritative. Never claim repository state without current readback.

## Semantic evidence workstream

Semantic investigations run alongside the three existing structural worker lanes; there is no fourth lane. The purpose is to move from verified locations and reader mechanics toward defensible input, function and output identities. The semantic hypothesis and identity-layer requirements below apply to WOs explicitly labelled `SEMANTIC`; they do not apply to every XML inclusion decision. Release 1 may include structurally verified objects under generic raw/provisional labels without resolving their full physical identity.

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

- Record exact instruction PCs/listing anchors, effective addresses, widths, signedness, query and axis construction, search/interpolation/clamp behavior and branch conditions when available or relevant. Trace arithmetic and the first meaningful consumer when establishing a functional identity, resolving a material structural conflict, or validating a claimed runtime role—not as a universal prerequisite for a structurally correct raw/provisional XML entry. This relaxed structural-inclusion threshold is permanent from 2026-11-27.
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
- A worker may edit its own WO reports and lifecycle, plus its own new WO specifications and the `FINDINGS/` paths permitted by the mandatory findings-disposition gate. Workers 1 and 3 may also create new WO specifications assigned to Worker 2 and append those READY rows to Worker 2's FIFO; after registration, only Worker 2 changes that WO's lifecycle/report. No worker may change another lane's existing assignment, active WO, status or report.
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
| Worker 1 | WOs explicitly assigned to Worker 1; may create bounded execution WOs for Worker 2 |
| Worker 2 | WOs explicitly assigned to Worker 2; local FIFO execution only |
| Worker 3 | WOs explicitly assigned to Worker 3; may create bounded execution WOs for Worker 2 |

WO numbers are sequential; ownership is explicit. Workers 1 and 3 supply Worker 2 directly through the live FIFO. No separate inbox or approval step. Each lane executes only its own assigned tasks and follows the shared publication lock.
