# Operating Protocol v3 — Autonomous Project Management

**Source:** user-directed standing-instruction update in the 2026-11-15 Control Notebook snapshot. This supersedes the older Dispatcher/Worker role split and separate dispatcher-delta workflow.

## Architecture
1. **GitHub `CONTROL/active_work_orders.md`:** sole operational authority for current work-order lifecycle, allocation, standing instructions, continuation and handoff.
2. **Master Workbook:** authoritative engineering archive for accepted technical findings, evidence, decisions, dependencies, registers and checkpoints.
3. **Chat:** temporary working space; reconcile with the GitHub register at batch start.
4. **Former OneDrive Control Notebook:** superseded historical archive; leave unchanged and do not use for current operational decisions.

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
- Update the existing GitHub `CONTROL/active_work_orders.md` in place at user-directed checkpoints; fetch its current blob SHA, commit the complete updated file, then read back and verify.
- Keep its Master Workbook pointer accurate, including version, exact filename/location and whether the GitHub XLSX binary is actually present.
- Do not claim a workbook or other artifact was integrated unless the exact destination was updated and read-back verified.
- Never create a parallel operational control notebook.

## Superseded workflow
- The older Dispatcher/Worker separation and mandatory role-transition labels are superseded.
- `EL19A_CONTROL.txt` and dispatcher-delta/RECON/CP12 text files are historical backups, not mandatory batch-start control sources. Preserve them unchanged; do not append ordinary progress there.
