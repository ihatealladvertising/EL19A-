# Authority and Snapshot Reconciliation

## Current authority (effective 2026-11-15)
- **Operational control:** GitHub `CONTROL/active_work_orders.md` in `ihatealladvertising/EL19A-`, branch `main`. This existing file was promoted by explicit user instruction and is the sole authority for current work-order lifecycle, assignments, priorities, continuation and handoff.
- **Master Workbook:** latest verified engineering archive pointer recorded in the GitHub control register / `PROJECT_STATE.md`. Technical findings belong in the workbook and individual WO evidence records.
- **Source artifacts:** original ROM/LST/XML/reports/scripts retain their own provenance.
- **Chat:** temporary context only.
- **Former OneDrive Control Notebook:** historical read-only archive; do not update it or use it to decide current assignments. Preserve it unchanged.

## Cutover and preserved history
- On 2026-11-15 the user explicitly authorized replacing the OneDrive Control Notebook with the existing GitHub work-order register.
- The register was updated in place and committed. Commit: `83a9d6c36e65103f0749a26b31a13e8c4389dfc5`.
- Older V53 and Library Notebook snapshots recorded conflicting lifecycle states (including WO64819 and WO64822). These remain historical snapshots only; they were not silently merged into current status.
- Current GitHub register records WO64827–WO64829 technical scopes complete, WO64825 PARTIAL, and no active WO. No new work order was created by the cutover.
- The former OneDrive Notebook previously returned 403 `serviceReadOnly`; this access limitation is now historical and does not block GitHub operational control.

## Master Workbook boundary
- V54 is the current GitHub Master Workbook at `WORKBOOK/EL19A_Master_Reverse_Engineering_Workbook_V54_E974_WO64827_64829_2026-11-15.xlsx`.
- File size is 1,350,922 bytes. Git blob SHA `20a304effc7656596e1bd19c65b623140ec511d2` matches the Git blob SHA calculated from the previously verified raw V54 bytes, confirming byte-identical content.
- V53 is retained in GitHub as `WORKBOOK/OLD_EL19A_Master_Reverse_Engineering_Workbook_V53_WO64817CP16_PAIR01_2026-11-15.xlsx`.
- CSV and Markdown checkpoints supplement V54; they do not replace it.
