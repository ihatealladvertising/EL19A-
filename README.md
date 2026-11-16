# EL19A ECU Reverse-Engineering Project

Private repository for the Nissan EL19A / SH7058 ECU reverse-engineering project and NissanDefinitions-compatible RomRaider XML development.

## Project identity
- Target: 2008 Nissan Versa / Sentra C11X, manual transmission
- ROM: `VERSA f501.bin`, 1 MiB
- MD5: `46991697c502052752a2cabcb84c9e27`
- CPU: Renesas SH7058 / SH705822N, SH-2 big-endian
- FID: `8CMCKRN5`
- ROM base: `0x00000000`

## Current project pointers
- [Project state](PROJECT_STATE.md)
- [Operational work-order control — single source of truth](CONTROL/active_work_orders.md)
- [Operating protocol v3](CONTROL/protocol_v3.md)
- [Authority and snapshot conflicts](CONTROL/authority_and_conflicts.md)
- [Current V54 Master Workbook](WORKBOOK/EL19A_Master_Reverse_Engineering_Workbook_V54_E974_WO64827_64829_2026-11-15.xlsx)
- [V54 integration and integrity record](WORKBOOK/V54_E974_INTEGRATION_SUMMARY_2026-11-15.md)
- [V53 historical source manifest](WORKBOOK/V53_SOURCE_MANIFEST.md)
- [Artifact migration queue](MIGRATION_QUEUE.md)
- [Calibration register guide](CALIBRATIONS/README.md)

## Authority and evidence policy
- `CONTROL/active_work_orders.md` on GitHub: sole operational authority for work-order lifecycle and handoff.
- Former OneDrive Control Notebook: superseded historical archive; leave unchanged.
- Master Workbook: authoritative technical archive for accepted evidence, findings and decisions.
- Original ROM/LST/XML/reports/scripts: source artifacts with their own provenance.
- Chat: temporary working context.
- Preserve conflicting snapshots; never silently merge or promote a hypothesis.
- Calibration semantics require target reader, lookup mechanics and downstream consumer evidence. Donor names/scaling are not target proof.

## Repository layout
- `CONTROL/` — operating protocol, work-order state and continuity notes.
- `EVIDENCE/` — evidence decisions and open leads.
- `CALIBRATIONS/` — provisional candidate register and definitions.
- `ANALYSIS/` — reusable scripts, tools and reports.
- `DISASSEMBLY/` — immutable source exports and separately versioned annotations.
- `WORKBOOK/` — workbook releases and migration manifests.

## Migration status
GitHub operational control is established in `CONTROL/active_work_orders.md` (commit `83a9d6c36e65103f0749a26b31a13e8c4389dfc5`). The former OneDrive Control Notebook is retained unchanged as a historical archive. The current V54 Master Workbook is committed in GitHub. Its Git blob SHA matches the previously verified V54 bytes exactly; V53 remains archived under an `OLD_` filename. ROM, LST, XML, scripts and reports remain outside GitHub until added unchanged and verified. ROM, LST, XML, scripts and reports remain outside GitHub until added unchanged and verified.

## Safeguards
- Repository is private.
- Do not commit credentials, tokens or personal data.
- Preserve original ROM, listings, workbooks and scripts unchanged.
- Assess large listings for Git LFS.
- Do not alter or upload project files to OneDrive/Library without explicit authorization.
- No XML or workbook edits unless explicitly requested.
