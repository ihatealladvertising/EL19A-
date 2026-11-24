# Calibration Findings / Reconciliation Index

**Status:** SCAFFOLD ESTABLISHED — CONTENT MIGRATION PENDING  
**Authority:** This index is the entry point for calibration interpretation. See [README](README.md) for schemas and the mandatory XML build gate.

## Address lookup

No finding records have yet been migrated into this index. This is an explicit empty initial state, not evidence that the repository contains no findings.

## Current priority migrations

- User-finalized Rev Hang screenshot interpretation for E678/E688, preserving the screenshot-finalized RPM presentation while retaining timer-derived ROM query mechanics as a separate runtime fact.
- F3D6/F3DE query, axes and clamp findings.
- 9B2E/9C2E/9DAE raw UBYTE and runtime-alias disposition.
- High-value map/curve geometry and axis findings that affect the provisional full XML.
- Corrections to provisional labels, axes, scaling or object classification from completed WOs.

## Record locations

- Findings: `FINDINGS/records/FND-xxxxxx.md`
- Reconciliations: `FINDINGS/reconciliations/REC-xxxxxx.md`
- Evidence references: `FINDINGS/evidence/EVD-xxxxxx.md`

## Promotion rule

Every material change to calibration interpretation must create or update a finding record and, when it changes a prior interpretation, a reconciliation record. WO reports must link to these IDs. The calibration inventory must link back to the findings supporting its current values.
