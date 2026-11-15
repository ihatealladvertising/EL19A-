# Migration Queue

**Target:** private GitHub repository `ihatealladvertising/EL19A-`  
**Rule:** copy artifacts unchanged; never delete or alter their OneDrive/Library/local originals as part of migration.

| Priority | Artifact | Current source / identity | Status | Action |
|---|---|---|---|---|
| 1 | V53 master workbook | OneDrive item `F6DEFBD470240AE6!sdc8e67e089974ba8a8f69d02828315be`; 1,333,108 bytes; MD5 `144522e97117f3d6b2fa9f7b71c98502`; SHA256 `3130c65164bbe7276e66eaf1df843a007cf2faf21086bde33478ed5f63169cc4` | Fetched and fingerprinted; not committed | Add unchanged binary from local Git clone; download from GitHub and compare both hashes |
| 2 | Stable Control Notebook | OneDrive item `F6DEFBD470240AE6!sac2dd9024e574ee3a7462a1730baeddd` | Exact fetch returned 403 `serviceReadOnly`; later Library/pasted snapshots exist | Obtain a successful exact read-back before treating any snapshot as current; then commit an archival snapshot plus metadata |
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

## Binary import limitation
The connected GitHub actions available in this session create/update UTF-8 text files and Git objects, but do not provide a local-file binary upload action. The V53 workbook is available in the current analysis workspace, but must be added through a local Git clone (or another user-controlled Git upload route). Once pushed, GitHub read-back can be checked against the hashes above.

## Do not
- Do not move/delete/overwrite OneDrive or Library originals.
- Do not import all historical duplicate LST/workbook copies indiscriminately.
- Do not commit secrets, tokens, credentials or personal data.
- Do not label any source as migrated until the GitHub copy is read back and verified.
