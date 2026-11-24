# Calibration Findings System

**Purpose:** durable, address-indexed technical knowledge for the EL19A calibration project. This layer is authoritative for findings and reconciliations; individual work orders remain the record of work performed, not the sole home of conclusions.

## Authority model

1. `EVIDENCE/` and indexed source artifacts preserve source material.
2. `FINDINGS/INDEX.md` is the entry point and address/finding lookup.
3. Individual finding records preserve observations and supported conclusions.
4. Reconciliation records preserve superseded interpretations and why they changed.
5. The existing calibration inventory remains the current proposed calibration view and must point back to finding IDs.
6. `CONTROL/active_work_orders.md` remains the sole operational lifecycle authority. It carries status and concise links only.

Do not silently overwrite a finding. Corrections are additive: create a reconciliation record and update the current index/inventory pointers while retaining the old record.

## Stable IDs

- Findings: `FND-000001`, monotonically allocated.
- Reconciliations: `REC-000001`, monotonically allocated.
- Evidence records: `EVD-000001`, monotonically allocated.
- Calibration objects retain their existing ROM address/object identity; do not invent a parallel CAL ID if a stable existing ID exists.

## Finding record minimum fields

- Stable finding ID; title; status (CURRENT, SUPERSEDED, DISPUTED, OPEN).
- Exact address(es), storage width/type, geometry where applicable.
- Exact observation, including ROM address/PC, bytes, calculations and reader mechanics as applicable.
- Conclusion and semantic layer (input identity, function identity, output identity, physical identity).
- Confidence and evidence grade, kept distinct.
- Source class and exact source references: ROM/LST, screenshot, A2L, donor, diagnostic, literature.
- Source WO IDs and precise report anchors.
- Related finding/reconciliation IDs; affected calibration inventory rows and XML objects.
- Explicit unknowns, contradictions, stop boundary and no-repeat notes.

## Reconciliation record minimum fields

- Stable reconciliation ID and affected address/object.
- Old interpretation and its source finding/report.
- Corrected/current interpretation and supporting finding(s).
- Reason for change, exact discriminating evidence and confidence.
- Status and affected inventory/XML references.
- Preserve the old interpretation as history; never erase it.

## Evidence index minimum fields

- Stable evidence ID; source class; artifact path/URL; immutable hash/version when available.
- Relevant address/table/screenshot region/page/ROM offset.
- What the artifact establishes and what it does not establish.
- Source WO(s) and linked finding IDs.

## Inventory integration

For every calibration candidate, retain the current proposed name, address, storage, geometry, axes/domains, scaling/units, confidence tier, evidence grade and source finding IDs. Keep observed facts separate from hypotheses. A missing finding link means the claim is not yet promoted by this system.

## Required build gate

Before creating or revising any RomRaider/XML definition:
1. Read the current calibration inventory and this index.
2. Resolve all current findings and reconciliation records affecting each included object.
3. Check that name, address, type, dimensions, axes, scaling, units and runtime/query domain agree with supported findings.
4. Preserve known exceptions and unresolved conflicts explicitly.
5. Link each XML object to its supporting finding IDs in a companion build manifest or comments where supported.
6. Record exclusions, unresolved conflicts and the index revision used for the build.

A build is not reconciled merely because the latest WO summaries were read.

## Initial migration policy

Migrate high-value calibration interpretation findings first, including user-finalized screenshot evidence and corrections that change axes, units, dimensions, scaling, labels or XML disposition. Do not mass-copy every RAM-cell consumer WO into this index; only findings that affect calibration interpretation or a reusable evidence method belong here. The initial index may contain no migrated records until the migration WO closes; never imply migration is complete prematurely.
