# Operating Protocol v3 — Autonomous Project Management

**Source:** user-directed standing-instruction update in the 2026-11-15 Control Notebook snapshot. This supersedes the older Dispatcher/Worker role split and separate dispatcher-delta workflow.

## Architecture
1. **Control Notebook:** sole operational authority for active/paused work orders, allocation, standing instructions, continuation state and exact master pointers.
2. **Master Workbook:** authoritative engineering archive for accepted technical findings, evidence, decisions, dependencies, registers and checkpoints.
3. **Chat:** temporary working space; reconcile with the durable sources at batch start.

## Autonomous management
The assistant manages work orders end-to-end: preflight, prioritization, bounded investigation, evidence review, ledger update, technical integration and handoff. No separate Dispatcher/Worker role labels or transitions are required.

## Standing instructions
- Keep each WO objective, inputs, dependencies, scope and stop condition explicit.
- Do not allocate a new WO while an active or unreconciled branch needs attention.
- Assess provenance, evidence quality, contradictions and confidence before accepting findings.
- Every checkpoint/closeout records status, findings/evidence, decisions/corrections, unresolved items/dependencies, resources, next action, completed work not to repeat, and Notebook/Workbook integration state.
- Preserve source artifacts and historical versions unchanged. No delete/move/overwrite without explicit authorization.
- No new scripts/tools/files, broad scans, unrelated traces or web searches unless the active task specifically requires them.
- Keep responses delta-only and economical.

## Save protocol
- Save the same main Control Notebook at the user-directed mid-work and end-of-work checkpoints; replace the exact existing OneDrive item and verify read-back.
- For every deployed Master Workbook successor, update that same Notebook in the same save batch with actual filename, browser URL, WebDAV path, Drive Item ID, version and date.
- The successor must contain the `Workbook Save Protocol` sheet.
- Read back both exact files and verify reciprocal pointers before closing the batch.
- Never label a local draft remotely saved or read-back verified.

## Superseded workflow
- The older Dispatcher/Worker separation and mandatory role-transition labels are superseded.
- `EL19A_CONTROL.txt` and dispatcher-delta/RECON/CP12 text files are historical backups, not mandatory batch-start control sources. Preserve them unchanged; do not append ordinary progress there.
