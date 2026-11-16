# Migration Queue

**Target:** private GitHub repository `ihatealladvertising/EL19A-`  
**Rule:** copy artifacts unchanged; never delete or alter their OneDrive/Library/local originals as part of migration.

| Priority | Artifact | Current source / identity | Status | Action |
|---|---|---|---|---|
| 1 | V54 Master Workbook | GitHub `WORKBOOK/EL19A_Master_Reverse_Engineering_Workbook_V54_E974_WO64827_64829_2026-11-15.xlsx`; 1,350,922 bytes; Git blob SHA `20a304effc7656596e1bd19c65b623140ec511d2`; MD5 `49491a933e31f11bce0b859d8b4c376e`; SHA256 `b566fe7f19066caa16928788da83442d1d217e296454dbc6d59808f97897c244` | **COMPLETE — present in GitHub; Git blob identity verified against previously verified V54 bytes** | No action; use V54 as current master |
| 2 | Former OneDrive Control Notebook | OneDrive item `F6DEFBD470240AE6!sac2dd9024e574ee3a7462a1730baeddd` | **SUPERSEDED — retained unchanged as historical archive** | No operational updates; GitHub `CONTROL/active_work_orders.md` is the sole operational control |
| 3 | ROM `VERSA f501.bin` | 1 MiB; MD5 `46991697c502052752a2cabcb84c9e27`; SHA256 `bfe037e8e6c389e2a90214047058eb6dc3bcaaaac5b5931bf98a3f5d9f64fd6a` | Identity known; binary not imported in this migration | Add unchanged file from user's verified local source; hash after GitHub read-back |
| 4 | Annotated disassembly | `EL19A_Complete_Disassembly_ANNOTATED_V3_NEXT6_16_ALL_PENDING_ANNOTATIONS.lst`; Library copy 27,045,080 bytes | Library copy found; user previously downloaded backups and intended to delete Library copies | Do not use/delete/move Library copy. Import only from user's verified local backup; use Git LFS |
| 5 | Current RomRaider XML | Exact current accepted filename/version not established in this migration | Pending inventory | Import only the user-designated current XML and validation artifacts; keep candidate/prototype XML separate |
| 6 | Existing scripts, XREF utilities, reports | Exact authoritative paths/versions not yet reconciled | Pending inventory | Reuse originals; import only after local path/version/hash identification |

## Already in GitHub
- README and project identity.
- Project state and snapshot-conflict record.
- Operating protocol v3; v1.1 preserved as superseded history.
- Work-order snapshot reconciliation.
- V53 source manifest.
- Provisional register guide and seed CSVs.
- Git attributes and ignore rules.

## Binary migration status
V54 has been placed in GitHub by the user and is confirmed byte-identical to the previously verified V54 source by matching Git blob SHA. V53 is retained under an `OLD_` filename. The V54 migration is complete. Other binary artifacts (ROM/LST/XML/scripts) require their own source identification, upload and read-back verification.

## Do not
- Do not move/delete/overwrite OneDrive or Library originals.
- Do not import all historical duplicate LST/workbook copies indiscriminately.
- Do not commit secrets, tokens, credentials or personal data.
- Do not label any source as migrated until the GitHub copy is read back and verified.
