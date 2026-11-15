# EL19A Project State

**Snapshot date:** 2026-11-15  
**Repository:** private `ihatealladvertising/EL19A-`  
**Migration status:** initial seed committed; source artifact import pending.

## Target identity

- 2008 Nissan Versa / Sentra C11X, manual transmission
- ROM: `VERSA f501.bin`, 1 MiB
- MD5: `46991697c502052752a2cabcb84c9e27`
- SHA256: `bfe037e8e6c389e2a90214047058eb6dc3bcaaaac5b5931bf98a3f5d9f64fd6a`
- CPU: Renesas SH7058 / SH705822N, SH-2 big-endian
- FID: `8CMCKRN5`
- IDA ROM base: `0x00000000`

## Active work

Latest chat context identifies **WO64824 — E974 output-chain investigation** as the active task. Its authoritative Controller Notebook was requested by a direct-fetch identifier, but that fetch failed in the current connector session. The V53 workbook and Controller Notebook have not yet been independently located/read back in OneDrive during this migration. Therefore WO64824 details and lifecycle state must be reconciled against the authoritative notebook before further technical work or status promotion.

## Last known workbook baseline

`EL19A_Master_Reverse_Engineering_Workbook_V53_WO64817CP16_PAIR01_2026-11-15.xlsx`

This is a named baseline from project context, not yet imported or read-back verified in this repository.

## Last known disassembly baseline

`EL19A_Complete_Disassembly_ANNOTATED_V3_NEXT6_16_ALL_PENDING_ANNOTATIONS.lst`

Large annotated listings (~27 MB) are not yet imported. Preserve local originals. Assess Git LFS and verify hashes before import.

## Operational constraints

- Minimum chat, tool calls and analysis overhead.
- Prefer local PowerShell/Python for bulk extraction; assistant interprets/adjudicates.
- No XML or workbook edits unless specifically requested.
- Do not upload, overwrite, move, delete or regenerate source files without explicit authorization.
- Preserve original ROM, listing exports, scripts and workbooks unchanged.
- Separate verified facts from hypotheses and worker returns.
- Lifecycle gates remain distinct: RETURNED → LEDGERED → WORKBOOK_SYNCED → READBACK_VERIFIED.
- Verify connector and file availability independently in each session.

## Migration caveat

This repository currently contains a compact context seed, not the full engineering archive. No ROM, workbook, LST, scripts, XML, or original evidence files have been imported yet.
