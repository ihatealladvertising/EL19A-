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

## Promotion workflow and WO closeout integration

Promotion is part of ordinary WO closeout, not a separate optional coordinator task. The controlling checklist and standing worker authorization are in `CONTROL/WORKER_PROTOCOL.md`.

For each completed WO, the owner must record one disposition in the WO report:

- **PROMOTED:** Material calibration interpretation/evidence changes are captured in one or more stable FND records; prior material interpretations are preserved by additive REC records; the address lookup is updated; and supported inventory finding-ID pointers are updated.
- **NOT REQUIRED:** The work is a routine trace or bounded negative with no change to a calibration candidate's identity, evidence status, XML inclusion/exclusion, a prior claim, or a reusable evidence method. State the exact reason; do not use this category to avoid recording an important negative.
- **DEFERRED:** A material correction is known but cannot be completed within the WO boundary. Create and queue a bounded reconciliation WO before closing the current WO, and name that follow-on in the report.

A material negative is still a finding when it removes support for a proposed calibration name, invalidates a reader/axis/consumer claim, changes a candidate's confidence or evidence status, rules an object out of an XML definition, or establishes a reusable method that prevents false address attribution. Lack of a physical endpoint does not prevent recording a qualified structural or functional finding.

Routine RAM-cell endpoint traces are not automatically FND records. Do not flood this system with internal state observations unless they materially alter a calibration interpretation or establish a reusable evidence method.

### Standing authorization and safe publication

The worker protocol grants each worker narrowly scoped standing authorization to create FND/REC records, update this index, and add finding-ID pointers to an existing inventory only where its current schema supports safe additive changes. This covers legacy WOs whose original authorized-path list predates this system. It does not authorize edits to calibration values, XML, workbooks, ROM/LST, A2Ls, catalogue data, scripts, protected evidence, or another worker's report/lifecycle.

Before allocating an ID, read the current index and confirm the next monotonically increasing ID and target path are unused. Never replace an existing FND/REC file to make a correction; create a new REC and update current pointers. Update the index against its current blob SHA, retry once after refreshing if a concurrent write is rejected, and read back every new record and index change from remote `main`. If safe publication fails after the permitted retry, keep the WO open and report the blocker.

## Required build gate

Before creating or revising any RomRaider/XML definition:
1. Read the current calibration inventory and this index.
2. Resolve all current findings and reconciliation records affecting each included object.
3. Check that name, address, type, dimensions, axes, scaling, units and runtime/query domain agree with supported findings.
4. Preserve known exceptions and unresolved conflicts explicitly.
5. Link each XML object to its supporting finding IDs in a companion build manifest or comments where supported.
6. Record exclusions, unresolved conflicts and the index revision used for the build.

A build is not reconciled merely because the latest WO summaries were read.

## Migration policy

Promote material findings as each WO closes. Do not wait for a periodic review or a bulk migration WO to capture new results. Historical WO-only findings that predate this gate should be migrated through bounded reconciliation WOs, prioritizing corrections that affect calibration identity, axes, scaling, units, confidence, XML disposition or reusable evidence methods. Do not mass-copy every RAM-cell consumer WO into this index.
