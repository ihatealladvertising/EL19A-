# EL19A ECU Reverse-Engineering Project

Private engineering repository for the Nissan EL19A / SH7058 ECU analysis and NissanDefinitions-compatible RomRaider XML development.

## Project identity

- Target: 2008 Nissan Versa / Sentra C11X, manual transmission
- ROM: `VERSA f501.bin` (1 MiB)
- MD5: `46991697c502052752a2cabcb84c9e27`
- CPU: Renesas SH7058 / SH705822N, SH-2 big-endian
- FID: `8CMCKRN5`
- ROM base in IDA: `0x00000000`

## Authority and evidence policy

- Preserve original ROMs, disassemblies, workbooks and scripts unchanged.
- The engineering workbook remains the detailed archive until its contents are migrated and read-back verified.
- Distinguish hypotheses, returned worker findings, ledgered findings, workbook-synced findings and read-back-verified findings.
- A calibration candidate is not confirmed by shape, values, address coincidence or donor resemblance alone. Establish the target reader, lookup mechanics and downstream consumer before assigning confirmed semantics.
- Keep generic names for unresolved tables and RAM members.
- Never silently promote a hypothesis to a verified fact.

## Repository layout

- `PROJECT_STATE.md` — compact current project state and migration caveats.
- `CONTROL/` — operating protocol, work-order status and checkpoints.
- `EVIDENCE/` — verified facts, open leads and decisions.
- `CALIBRATIONS/` — provisional candidate register and eventual definitions.
- `ANALYSIS/` — reusable scripts, tools and reports.
- `DISASSEMBLY/` — immutable source exports and separately versioned annotations.
- `WORKBOOK/` — preserved workbook releases and migration manifests.

## Handling rules

- This repository is private.
- Do not commit credentials, tokens, personal data, or unlicensed third-party material.
- Large binaries and large listing files should be assessed for Git LFS before import.
- Do not replace the existing V53 workbook or original ROM/LST files during migration.
- Each imported artifact must have its source, version, size/hash where available, and verification status recorded.
