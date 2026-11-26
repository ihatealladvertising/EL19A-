# Calibration Register Guide

## Current engineering baseline

The current engineering workbook is **V58**:
`WORKBOOK/EL19A_Master_Reverse_Engineering_Workbook_V58_WO65114_ThinReferenceCloseout_2026-11-21.xlsx` (149 sheets).

Older V53–V57 workbooks are historical snapshots. Their sheet lists, inventory counts and handoff summaries must not be presented as current V58 accounting unless independently rechecked against V58.

The initial `candidate_register.csv` and `EVIDENCE/open_leads.csv` are compact historical seed subsets, not complete inventories. `discovered_tables_catalog.csv` is discovery staging, not the release inclusion list. Use V58 together with `FINDINGS/INDEX.md` and its linked records for current interpretation.

## Release 1

The user-authorized full-definition starting point remains:
`CALIBRATIONS/EL19A_best_guess_provisional_full_definition.xml`.

It is the **selected best-guess baseline**. Preserve it unchanged and refine the separate successor XML. The current successor is an iterative working definition with candidate names/categories/conversions where useful, while keeping structural evidence and semantic confidence distinct. Dispositions are INCLUDE — ESTABLISHED, INCLUDE — PROVISIONAL, or EXCLUDE.

The tiered WO65325 XML and merged V3 XML are useful historical comparison artifacts; they are not silently substituted for the selected full-definition baseline. Reconcile their proven corrections and later Findings before constructing a successor.

## Working rules

- A structurally sound object should use the best available functional name/category and a plausible best-guess conversion where useful; mark it provisional and refine it as evidence improves.
- Keep addresses, extents, dimensions and reader/axis mechanics evidence-led; do not invent table geometry.
- A sample-index or fixed raw query axis must be labelled honestly; never imply physical units that are not supported.
- Semantic tracing refines candidate names/functions and conversions. It is not a universal prerequisite for including a useful best-guess object.
- The release manifest must identify the ROM hash, XML baseline, Findings index revision, object dispositions, exclusions and unresolved items.
