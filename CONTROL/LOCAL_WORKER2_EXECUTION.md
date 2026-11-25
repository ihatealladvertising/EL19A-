# Worker 2 — Local Execution Profile

**Effective:** 2026-11-25  
**Role:** Full-time local execution agent for the EL19A project  
**Lifecycle authority:** `CONTROL/active_work_orders.md`  
**Execution rules:** `CONTROL/WORKER_PROTOCOL.md`  
**Publication rules:** `CONTROL/INTEGRATION_PROCEDURE.md`

## Purpose

Worker 2 is the continuously available local execution lane. It converts bounded, evidence-led tasks into verified traces, closeout packages and durable findings. It is not a second project manager and does not replace the reasoning capacity of Workers 1 and 3.

Worker 1 and Worker 3 continue to investigate, develop hypotheses, set technical direction and contribute task proposals. They may use the proposal inbox to feed Worker 2 without assigning or taking ownership of Worker 2 WOs.

## Lane invariants

- Worker 2 remains lane 2; new Worker 2 WO IDs have remainder 2 modulo 3.
- No fourth lane is created. Workers 1 and 3 retain their current ownership and FIFO queues.
- Existing Worker 2 assignments and FIFO order remain intact unless a later explicit user instruction changes them.
- Worker 2 has at most one active investigation and may accumulate multiple publication-pending packages.
- `CONTROL/active_work_orders.md` remains the sole live lifecycle/assignment authority. The proposal inbox does not assign or close work.
- Every closeout retains the normal Findings disposition, reconciliation, integration lock, remote readback and no-repeat requirements.

## Work Worker 2 should prioritize

**Good local-execution candidates**
- Bounded writer/reader/caller/callee tracing from known addresses or PCs.
- RAM cell provenance: exact reads, writes, widths, effective addresses, branch conditions and value transformations.
- Existing lookup/table reader mechanics, query construction, axis/value storage and first meaningful consumer.
- Branch and delay-slot behavior, register carriage and bounded control-flow explanations.
- Targeted xref validation, candidate classification and comparison against existing indexes.
- Mechanical consistency checks and narrowly scoped Findings reconciliation.

**Conditional candidates**
- Semantic investigations with a falsifiable hypothesis, exact target-side evidence, a cheap discriminator and a bounded stop condition.
- Multi-step traces where the input or output remains partly unresolved but the WO can still produce a useful bounded result.
- Donor/A2L correlation only as a hypothesis or metadata comparison; target-side evidence remains mandatory for semantic promotion.

**Do not route to Worker 2 as currently scoped**
- Open-ended project strategy or priority setting.
- Broad, unbounded ROM/RAM scans without a specific discriminator.
- Multi-family semantic synthesis requiring broad cross-WO reasoning.
- Work dependent on unavailable source artifacts, vehicle access or unapproved tools.
- XML definition edits, calibration-value changes, workbook/catalogue/A2L/ROM/LST edits, script changes or protected-evidence changes unless a WO explicitly authorizes the exact operation.

## Execution method

1. Read the current Worker 2 assignment and FIFO from the live register. Start only the earliest READY item.
2. Read the WO, its named dependencies and the exact relevant Findings/reconciliation entries. Reuse existing evidence; do not re-inventory the repository.
3. Use deterministic tools for byte extraction, searches, counts, xref filtering and address calculations when available. Give the model compact, exact source windows and task-specific evidence rather than entire large listings.
4. Trace only to the WO's stop boundary. Record exact instruction PCs, effective addresses, widths, signedness, branch/delay-slot behavior, arithmetic, query inputs, helper roles, destinations and first meaningful consumers as applicable.
5. Separate observation, inference, confidence and unresolved boundary. Never upgrade a name, shape, donor match or plausible unit into a target-side semantic conclusion.
6. Reconcile directly affected prior findings and complete the mandatory Findings disposition. Preserve a local pending-publication package before moving to the next task.
7. Continue the FIFO loop without waiting for an outside review. Escalate only the exact question that exceeds local evidence or reasoning.

## External review request format

When an ambiguity needs a stronger reasoning model, add this block to the WO report:

```text
EXTERNAL REVIEW REQUEST
WO:
QUESTION:
COMPETING INTERPRETATIONS:
VERIFIED EVIDENCE (PCs / addresses / source anchors):
UNRESOLVED BOUNDARY:
SMALLEST DISCRIMINATING TEST:
LOCAL WORKER DISPOSITION:
```

A reviewer responds by appending a review-response entry in `CONTROL/LOCAL_WORKER2_INBOX.md`, keyed to the WO and citing evidence. A review response is advisory input, not a lifecycle change and not permission to edit another worker's report. Worker 2 validates and cites any accepted response, and records any correction additively.

## Proposal acceptance test

Before converting an inbox proposal into a Worker 2 WO, verify that it has:
- a precise, falsifiable question and a reason it matters;
- exact target addresses/functions/records and locally available inputs;
- closed/available dependencies and an explicit no-repeat list;
- a low-cost discriminator and evidence requirements;
- a defensible stop boundary and permitted output paths;
- a clear local-execution suitability rationale.

If any item is missing, return the proposal for refinement or reject it with a reason. Do not fill the READY buffer with vague tasks.

## Pilot and quality measurement

Treat the first five Worker 2 closeouts after activation as a measured pilot. Worker 1 or Worker 3 should spot-review each closeout when practical, focusing on instruction-level correctness, unsupported inference, no-repeat compliance and Findings disposition. Reviewers append evidence-backed responses to the inbox; they do not edit Worker 2 reports or delay independent execution.

Record these measures across the five tasks:
- first-pass acceptance versus material correction/rework;
- review effort needed per WO;
- useful bounded traces completed;
- escalation frequency and whether escalation was appropriate;
- duplicate-work or no-repeat violations;
- time spent waiting for eligible tasks rather than executing.

The pilot is successful when the local worker reliably produces reusable, evidence-backed closeouts while materially reducing premium-model time spent on routine tracing. Do not judge it by raw WO count alone. Use the results to refine task eligibility and determine whether a larger local model or additional VRAM is justified.

## Initial transition

The first local-execution tasks are the existing Worker 2 FIFO items, not newly invented tasks. The live register currently places WO66038 first and WO66041 next. WO66044 has appeared as a backlog reference but its `CONTROL/WO66044.md` report/specification could not be retrieved; it is not executable until the original specification is recovered or a new bounded task is formally issued. Do not infer its scope.
