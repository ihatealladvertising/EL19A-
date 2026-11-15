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
- [Work-order snapshot reconciliation](CONTROL/active_work_orders.md)
- [Operating protocol v3](CONTROL/protocol_v3.md)
- [Authority and snapshot conflicts](CONTROL/authority_and_conflicts.md)
- [V53 workbook source manifest](WORKBOOK/V53_SOURCE_MANIFEST.md)
- [Calibration register guide](CALIBRATIONS/README.md)

## Authority and evidence policy
- Control Notebook: operational authority for work-order lifecycle and exact master pointers.
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
GitHub is connected and the initial text/control seed is committed and read-back verified. The V53 workbook was fetched from its exact OneDrive URL and fingerprinted, but the raw XLSX is not yet committed to GitHub. ROM, LST, XML, scripts and reports remain outside GitHub until added unchanged and verified.

## Safeguards
- Repository is private.
- Do not commit credentials, tokens or personal data.
- Preserve original ROM, listings, workbooks and scripts unchanged.
- Assess large listings for Git LFS.
- Do not alter or upload project files to OneDrive/Library without explicit authorization.
- No XML or workbook edits unless explicitly requested.
