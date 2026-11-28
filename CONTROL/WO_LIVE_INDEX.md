# EL19A — Auto-Generated Work-Order Ownership Dashboard

> **Do not hand-edit this view.** Generated deterministically from `CONTROL/WO*.md` and `CONTROL/registry_pins.json` by `tools/wo_registry.py`.

- **Repository:** `ihatealladvertising/EL19A-` · **Authority branch:** `main`
- **Current Workbook:** `WORKBOOK/EL19A_Master_Reverse_Engineering_Workbook_V58_WO65114_ThinReferenceCloseout_2026-11-21.xlsx` (149 sheets)
- **XML Baseline:** `public/assets/aistudio/EL19A_merged_definition_v3_08a300db.xml` + `EL19A_ignition_decoded_fragment_33ea8e67.xml`
- **Catalog Staging:** `CALIBRATIONS/discovered_tables_catalog.csv`
- **Parsed Records:** `802` total (`7` structured v4, `795` legacy)

## Lane Allocation (Zero-Collision Prefixes)

| Lane | ID Range | Highest Used | Next Free | Session Assignment |
|---|---|---|---|---|
| `git-1` | `WO65200`–`WO69999` | `WO66051` | `WO66052` | Primary Git IDE / coordinator worker lane |
| `aistudio` | `WO70000`–`WO79999` | `WO70043` | `WO70044` | Stateless AI Studio container lane (no local .git; disjoint files only) |
| `git-2` | `WO80000`–`WO89999` | — | `WO80000` | Secondary Git IDE / parallel external worker lane |
| `reserve` | `WO90000`–`WO99999` | — | `WO90000` | Reserved synthesis / coordinator batch lane |

## Active Claims & Lease Health

| WO | Lane | Priority | Owner | Claimed At | Lease Health | Target Scope |
|---|---|---|---|---|---|---|
| [WO70043](WO70043.md) | `aistudio` | P1 | `aistudio-readertrace-integrator` | `2026-11-28T05:02:00Z` | OK (0.0h / 24h) | `rom:f501:0x0f10e`, `rom:f501:call_0x85b2e`, `tooling:reader_trace_production_static_flow_export`, `tools:export_reader_trace_static_flow`, `workflow:reader_trace_static_flow_production`, `evidence:reader_trace_0f10e_static_flow` |

## Target Scope Lock Table

| Canonical Scope Lock | Held By | Owner | Lane |
|---|---|---|---|
| `evidence:reader_trace_0f10e_static_flow` | [WO70043](WO70043.md) | `aistudio-readertrace-integrator` | `aistudio` |
| `rom:f501:0x0f10e` | [WO70043](WO70043.md) | `aistudio-readertrace-integrator` | `aistudio` |
| `rom:f501:call_0x85b2e` | [WO70043](WO70043.md) | `aistudio-readertrace-integrator` | `aistudio` |
| `tooling:reader_trace_production_static_flow_export` | [WO70043](WO70043.md) | `aistudio-readertrace-integrator` | `aistudio` |
| `tools:export_reader_trace_static_flow` | [WO70043](WO70043.md) | `aistudio-readertrace-integrator` | `aistudio` |
| `workflow:reader_trace_static_flow_production` | [WO70043](WO70043.md) | `aistudio-readertrace-integrator` | `aistudio` |

## Structured Queue & Dependency Unblocking

| WO | Declared Status | Effective State | Priority | Depends On | Title |
|---|---|---|---|---|---|
| [WO70041](WO70041.md) | `RESERVED` | READY | P3 | — | Advisory audit of SH-2 reader-analysis reuse and test coverage |

## Recent Closed Structured Work Orders

| WO | Lane | Priority | Owner | Closed/Claimed Timestamp | Title |
|---|---|---|---|---|---|
| [WO70042](WO70042.md) | `aistudio` | P1 | `aistudio-readertrace-integrator` | `2026-11-28T04:52:40Z` | Per-call static-flow adapter for Reader Trace v0.1 |
| [WO70040](WO70040.md) | `aistudio` | P1 | `aistudio-readertrace-worker1` | `2026-11-28T04:47:27Z` | Reconstruct and evidence-audit the 0x0F10E reader-trace graph |
| [WO70039](WO70039.md) | `aistudio` | P1 | `aistudio-el19a-coordinator` | `2026-11-28T02:32:38Z` | Nissan master-ROM and structural-family index |
| [WO70002](WO70002.md) | `aistudio` | P1 | `aistudio-el13a-diff` | `2026-11-24T03:34:07Z` | EL19A vs EL13A Same-FID Calibration Diff and Unmapped Target Discovery |
| [WO70001](WO70001.md) | `aistudio` | P1 | `aistudio-governance-v4` | `2026-11-22T03:43:00Z` | Decentralized Work-Order Ownership, Partitioned Lanes, and CI Register Rebuilder |
