# EL19A — Auto-Generated Work-Order Ownership Dashboard

> **Do not hand-edit this view.** Generated deterministically from `CONTROL/WO*.md` and `CONTROL/registry_pins.json` by `tools/wo_registry.py`.

- **Repository:** `ihatealladvertising/EL19A-` · **Authority branch:** `main`
- **Current Workbook:** `WORKBOOK/EL19A_Master_Reverse_Engineering_Workbook_V58_WO65114_ThinReferenceCloseout_2026-11-21.xlsx` (149 sheets)
- **XML Baseline:** `public/assets/aistudio/EL19A_merged_definition_v3_08a300db.xml` + `EL19A_ignition_decoded_fragment_33ea8e67.xml`
- **Catalog Staging:** `CALIBRATIONS/discovered_tables_catalog.csv`
- **Parsed Records:** `798` total (`3` structured v4, `795` legacy)

## Lane Allocation (Zero-Collision Prefixes)

| Lane | ID Range | Highest Used | Next Free | Session Assignment |
|---|---|---|---|---|
| `git-1` | `WO65200`–`WO69999` | `WO66051` | `WO66052` | Primary Git IDE / coordinator worker lane |
| `aistudio` | `WO70000`–`WO79999` | `WO70039` | `WO70040` | Stateless AI Studio container lane (no local .git; disjoint files only) |
| `git-2` | `WO80000`–`WO89999` | — | `WO80000` | Secondary Git IDE / parallel external worker lane |
| `reserve` | `WO90000`–`WO99999` | — | `WO90000` | Reserved synthesis / coordinator batch lane |

## Active Claims & Lease Health

| WO | Lane | Priority | Owner | Claimed At | Lease Health | Target Scope |
|---|---|---|---|---|---|---|
| [WO70039](WO70039.md) | `aistudio` | P1 | `aistudio-el19a-coordinator` | `2026-11-28T02:32:38Z` | OK (1.6h / 24h) | `tooling:wo70039-full-mass-scan-index`, `tooling:wo_registry_migration_baseline`, `control:wo70039`, `control:integration-status`, `control:registry_pins`, `control:protocol-v4` |

## Target Scope Lock Table

| Canonical Scope Lock | Held By | Owner | Lane |
|---|---|---|---|
| `control:integration-status` | [WO70039](WO70039.md) | `aistudio-el19a-coordinator` | `aistudio` |
| `control:protocol-v4` | [WO70039](WO70039.md) | `aistudio-el19a-coordinator` | `aistudio` |
| `control:registry_pins` | [WO70039](WO70039.md) | `aistudio-el19a-coordinator` | `aistudio` |
| `control:wo70039` | [WO70039](WO70039.md) | `aistudio-el19a-coordinator` | `aistudio` |
| `tooling:wo70039-full-mass-scan-index` | [WO70039](WO70039.md) | `aistudio-el19a-coordinator` | `aistudio` |
| `tooling:wo_registry_migration_baseline` | [WO70039](WO70039.md) | `aistudio-el19a-coordinator` | `aistudio` |

## Structured Queue & Dependency Unblocking

_No queued v4 RESERVED/BLOCKED work orders._

## Recent Closed Structured Work Orders

| WO | Lane | Priority | Owner | Closed/Claimed Timestamp | Title |
|---|---|---|---|---|---|
| [WO70002](WO70002.md) | `aistudio` | P1 | `aistudio-el13a-diff` | `2026-11-24T03:34:07Z` | EL19A vs EL13A Same-FID Calibration Diff and Unmapped Target Discovery |
| [WO70001](WO70001.md) | `aistudio` | P1 | `aistudio-governance-v4` | `2026-11-22T03:43:00Z` | Decentralized Work-Order Ownership, Partitioned Lanes, and CI Register Rebuilder |
