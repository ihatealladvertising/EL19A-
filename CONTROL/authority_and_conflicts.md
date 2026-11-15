# Authority and Snapshot Reconciliation

## Source hierarchy
- Stable Control Notebook: operational authority.
- Current Master Workbook named in that Notebook: technical archive.
- Original ROM/LST/XML/reports/scripts: source evidence with their own provenance.
- Chat: temporary continuation context; not automatically a durable project record.
- Local drafts and copied/pasted Notebook snapshots are not equivalent to an exact current OneDrive read-back.

## Retrieved snapshots in this migration
| Snapshot | State recorded | Status |
|---|---|---|
| V53 workbook checkpoint, 2026-11-15 | WO64817 PARTIAL/PAUSED CP16; WO64819 ACTIVE PAIR-01; WO64820/64821 QUEUED | V53 binary fetched from its exact OneDrive URL; workbook checkpoint inspected |
| Later Library Notebook paste, 2026-11-15 17:55 | WO64822 ACTIVE; WO64819 PAUSED after CP18; WO64820/64821 deferred; V53 remains master | Library copy / pasted Notebook content; not an exact live Notebook read-back |
| Current chat continuation context | WO64824 — E974 output-chain investigation | Current working context; not found in the retrieved V53 checkpoint or later Library snapshot |
| Stable OneDrive Notebook item | `F6DEFBD470240AE6!sac2dd9024e574ee3a7462a1730baeddd` | Direct fetch returned 403 `serviceReadOnly` during this migration |

## Required reconciliation
Until the stable Notebook is fetched successfully, do not claim a single read-back-verified active WO. Preserve each snapshot and its timestamp/provenance. Current chat work may continue only within the user-authorized scope, but any change to active WO, checkpoint, dependencies or integration status must be reconciled to the Notebook before durable promotion.

## Historical WO64819 CP18 boundary
The user cancelled the WO64819 CP18 investigation. The bounded evidence did not demonstrate an actual code access to `FFFF37AE` (+0x90 from `FFFF371E`). Later Library snapshot records WO64819 paused at CP18 after bounded paths were exhausted. Do not resume that CP18 scope without a new explicit request and concrete lead.
