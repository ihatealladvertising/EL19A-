# EL19A — Auto-Generated Work-Order Ownership Dashboard

> **Do not hand-edit this view.** Generated deterministically from `CONTROL/WO*.md` and `CONTROL/registry_pins.json` by `tools/wo_registry.py`.

- **Repository:** `ihatealladvertising/EL19A-` · **Authority branch:** `main`
- **Current Workbook:** `WORKBOOK/EL19A_Master_Reverse_Engineering_Workbook_V58_WO65114_ThinReferenceCloseout_2026-11-21.xlsx` (149 sheets)
- **XML Baseline:** `public/assets/aistudio/EL19A_merged_definition_v3_08a300db.xml` + `EL19A_ignition_decoded_fragment_33ea8e67.xml`
- **Catalog Staging:** `CALIBRATIONS/discovered_tables_catalog.csv`
- **Parsed Records:** `800` total (`5` structured v4, `795` legacy)

## Lane Allocation (Zero-Collision Prefixes)

| Lane | ID Range | Highest Used | Next Free | Session Assignment |
|---|---|---|---|---|
| `git-1` | `WO65200`–`WO69999` | `WO66051` | `WO66052` | Primary Git IDE / coordinator worker lane |
| `aistudio` | `WO70000`–`WO79999` | `WO70041` | `WO70042` | Stateless AI Studio container lane (no local .git; disjoint files only) |
| `git-2` | `WO80000`–`WO89999` | — | `WO80000` | Secondary Git IDE / parallel external worker lane |
| `reserve` | `WO90000`–`WO99999` | — | `WO90000` | Reserved synthesis / coordinator batch lane |

## Active Claims & Lease Health

_No active CLAIMED work orders._

## Target Scope Lock Table

_No active hex/key scope locks held._

## Structured Queue & Dependency Unblocking

| WO | Declared Status | Effective State | Priority | Depends On | Title |
|---|---|---|---|---|---|
| [WO70041](WO70041.md) | `RESERVED` | READY | P3 | — | Advisory audit of SH-2 reader-analysis reuse and test coverage |

## Recent Closed Structured Work Orders

| WO | Lane | Priority | Owner | Closed/Claimed Timestamp | Title |
|---|---|---|---|---|---|
| [WO70040](WO70040.md) | `aistudio` | P1 | `aistudio-readertrace-worker1` | `2026-11-28T04:47:27Z` | Reconstruct and evidence-audit the 0x0F10E reader-trace graph |
| [WO70039](WO70039.md) | `aistudio` | P1 | `aistudio-el19a-coordinator` | `2026-11-28T02:32:38Z` | Nissan master-ROM and structural-family index |
| [WO70002](WO70002.md) | `aistudio` | P1 | `aistudio-el13a-diff` | `2026-11-24T03:34:07Z` | EL19A vs EL13A Same-FID Calibration Diff and Unmapped Target Discovery |
| [WO70001](WO70001.md) | `aistudio` | P1 | `aistudio-governance-v4` | `2026-11-22T03:43:00Z` | Decentralized Work-Order Ownership, Partitioned Lanes, and CI Register Rebuilder |
