# Calibration Register Guide

## Current engineering baseline

The current engineering workbook is **V58**:
`WORKBOOK/EL19A_Master_Reverse_Engineering_Workbook_V58_WO65114_ThinReferenceCloseout_2026-11-21.xlsx` (149 sheets).

Older V53–V57 workbooks are historical snapshots. Their sheet lists, inventory counts and handoff summaries must not be presented as current V58 accounting unless independently rechecked against V58.

The initial `candidate_register.csv` and `EVIDENCE/open_leads.csv` are compact historical seed subsets, not complete inventories. `discovered_tables_catalog.csv` is discovery staging, not the release inclusion list. Use V58 together with `FINDINGS/INDEX.md` and its linked records for current interpretation.

## Release 1

The user-authorized full-definition starting point remains:
`CALIBRATIONS/EL19A_best_guess_provisional_full_definition.xml`.

It is a **provisional build baseline, not a validated release**. Preserve it unchanged and create a separate successor XML. Release decisions follow `CALIBRATIONS/RELEASE1_PLAN.md` and the Release 1 dispositions: INCLUDE — ESTABLISHED, INCLUDE — RAW/PROVISIONAL, or EXCLUDE.

The tiered WO65325 XML and merged V3 XML are useful historical comparison artifacts; they are not silently substituted for the selected full-definition baseline. Reconcile their proven corrections and later Findings before constructing a successor.

## Working rules

- A structurally sound object may be included with a generic name and raw scaling when physical identity or units remain unknown.
- Never invent an address, extent, dimension, axis, unit or conversion.
- A sample-index axis is an index only, never a claim about the ECU's physical query domain.
- Semantic tracing is required when needed to establish a claimed name/function, distinguish a material conflict, or justify a physical axis or conversion. It is not a universal inclusion requirement.
- The release manifest must identify the ROM hash, XML baseline, Findings index revision, object dispositions, exclusions and unresolved items.
