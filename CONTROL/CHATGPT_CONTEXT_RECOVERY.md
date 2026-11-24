# ChatGPT Context Recovery Control — EL19A

**Purpose:** let a fresh ChatGPT session recover the project's actual state quickly without relying on compressed chat memory or stale summaries.

## Mandatory recovery sequence

1. Read `CONTROL/active_work_orders.md` first. It alone determines current WO ownership, status, FIFO queues and blockers.
2. Read this file and `CONTROL/WORKER_PROTOCOL.md` for operating rules.
3. Read `FINDINGS/INDEX.md` and `FINDINGS/README.md` for the current technical-knowledge authority and migration state.
4. Read the current assigned WO report for each active lane only when that lane matters to the request. Read its cited dependencies only as needed.
5. Read the relevant calibration inventory and XML baseline/build manifest before definition work. Do not infer current state from `PROJECT_STATE.md` unless its synchronization block is current; it may be historical.
6. For technical questions, follow finding IDs to their source WOs/evidence. Chat summaries and memory are navigation aids, never technical authority.

Read `CONTROL/PROJECT_KNOWLEDGE_PROCESS_REVIEW.md` as part of recovery; its latest entry records known documentation gaps, contradictions, method changes and fresh-session test results. The review log is a diagnostic aid, not a substitute for the live register or findings index.

## Source-of-truth hierarchy

- Work-order lifecycle/assignment: `CONTROL/active_work_orders.md`.
- Execution rules: `CONTROL/WORKER_PROTOCOL.md`.
- Calibration interpretation: `FINDINGS/INDEX.md` and linked finding/reconciliation records.
- Raw evidence: exact linked ROM/LST, screenshot, A2L, donor, diagnostic or literature artifact.
- Current calibration proposal: the designated calibration inventory, reconciled against findings.
- XML output: the designated immutable baseline plus its successor/build manifest.
- Chat history, saved memory and this recovery control: orientation only, subordinate to repository readback.

## Non-negotiable interpretation rules

- Do not present a WO closure count as a count of major semantic discoveries.
- Separate observation, inference, confidence, evidence grade and unresolved physical meaning.
- Do not silently overwrite an older interpretation; use additive reconciliation records.
- **Rev Hang exception:** E678/E688 retain the user's screenshot-finalized RPM presentation and values. Keep the ROM timer-derived 0–240 query domain as a separate runtime fact and investigate the mapping; do not replace those two finalized screenshot tables with timer-indexed curves.
- For all other calibration objects, apply ROM reader/query/consumer evidence normally. Screenshot/A2L/donor evidence remains source-specific and conflicts must be reconciled rather than automatically privileging one source.
- Before every XML generation/revision, reconcile the affected objects against the findings index, not merely recent WO summaries.
- Never claim an index migration, file update, commit or readback unless verified from GitHub in the current session.

## Minimal response format when user asks for project state

Report only what the request needs. For a restore-context handoff use:
- current WO / next action;
- dependencies;
- latest workbook or calibration baseline;
- blockers;
- relevant finding/reconciliation IDs;
- next exact action.

Avoid dumping historical queues, old project-state snapshots or unrelated memory. If live state is uncertain, reread the register instead of guessing.

## Update discipline

When a session makes a material project decision or discovers a reusable technical result:
1. Commit the exact source/report.
2. Create/update finding and reconciliation records if calibration interpretation changes.
3. Update the calibration inventory pointers where affected.
4. Update the operational register only for lifecycle status and concise links.
5. Verify GitHub readback and record commit/blob SHAs in the response.

This file is a recovery guide, not a competing state register. Keep live status and technical claims in their authoritative files.
