# EL19A Project State

**Snapshot:** 2026-11-15  
**Repository:** private `ihatealladvertising/EL19A-`  
**Migration:** bootstrap committed; V53 source fetched and fingerprinted; raw binary import still pending.

## Target identity
- 2008 Nissan Versa / Sentra C11X, manual transmission
- ROM: `VERSA f501.bin`, 1 MiB
- MD5: `46991697c502052752a2cabcb84c9e27`
- SHA256: `bfe037e8e6c389e2a90214047058eb6dc3bcaaaac5b5931bf98a3f5d9f64fd6a`
- CPU: Renesas SH7058 / SH705822N, SH-2 big-endian
- FID: `8CMCKRN5`
- IDA ROM base: `0x00000000`

## Engineering archive
Current deployed master baseline: **V53** — `EL19A_Master_Reverse_Engineering_Workbook_V53_WO64817CP16_PAIR01_2026-11-15.xlsx`.
- OneDrive item: `F6DEFBD470240AE6!sdc8e67e089974ba8a8f69d02828315be`
- Browser URL: https://onedrive.live.com/personal/f6defbd470240ae6/_layouts/15/doc.aspx?resid=dc8e67e0-8997-4ba8-a8f6-9d02828315be&cid=f6defbd470240ae6
- Size: 1,333,108 bytes; 139 sheets
- MD5: `144522e97117f3d6b2fa9f7b71c98502`
- SHA256: `3130c65164bbe7276e66eaf1df843a007cf2faf21086bde33478ed5f63169cc4`
- Exact source URL fetched in this migration session; workbook is available locally at `/mnt/data/EL19A_Master_Reverse_Engineering_Workbook_V53_WO64817CP16_PAIR01_2026-11-15.xlsx`.
- The workbook's V53 checkpoint says it was deployed additively from V52 and exact-item read-back verified, with reciprocal stable Notebook pointers.
- The raw XLSX has not yet been committed to GitHub. See `WORKBOOK/V53_SOURCE_MANIFEST.md`.

## Operational state — conflicting snapshots, do not silently merge
1. **V53 checkpoint (durable workbook snapshot):** WO64817 PARTIAL/PAUSED at CP16; WO64819 ACTIVE (PAIR-01); WO64820 and WO64821 QUEUED; WO64816/WO64818 PARTIAL/PAUSED; WO64795 proposed/not issued.
2. **Later Library Notebook draft/snapshot (2026-11-15 17:55 paste):** records a subsequent user-authorized reprioritization to WO64822 ACTIVE, after WO64819 was paused at CP18; WO64820/WO64821 deferred; WO64817/WO64816/WO64818 paused. Its master pointer remains V53.
3. **Latest chat continuation context:** identifies WO64824 — E974 output-chain investigation. This WO is not present in the retrieved V53 checkpoint or the later Library snapshot searched in this migration. Treat it as current chat-level task context, not yet reconciled to the authoritative stable Notebook.
4. Stable Control Notebook item: `F6DEFBD470240AE6!sac2dd9024e574ee3a7462a1730baeddd`. A direct OneDrive fetch during this migration returned 403 `serviceReadOnly`; available Library snapshots are not equivalent to a successful current read-back of that exact item.

**Until the stable Notebook is retrieved and reconciled, do not claim one globally verified active WO.** For the current chat, preserve WO64824/E974 as the requested continuation, while retaining the durable V53 and Library-snapshot histories above.

## Technical authority and evidence
- V53 workbook is the authoritative engineering archive baseline available for migration.
- Candidate inventory: V7 / 122 unique `storageaddress` placements; screenshot-scope broader inventory is 175 (122 + 53). The full 175 membership is not freshly audited.
- See V53 sheets: `Session Control`, `WO Continuity Ledger`, `Batch Checkpoint Manifest`, `V53 Checkpoint`, `Theory Handoff 2026-11-15`, `Project2 1D Crosswalk`, `EL19A 1D Lookup Candidates`, `P2 Candidate Register`, `P2 Handoff Log`, `Candidate Evidence Ledger`.
- All semantic candidate names remain provisional unless target reader, lookup mechanics and downstream use establish them. Do not transfer donor scaling/units.

## Operating constraints
- Minimum chat, tool calls and analysis overhead.
- Prefer local PowerShell/Python for bulk extraction; assistant interprets/adjudicates.
- Preserve original ROMs, LSTs, XMLs, scripts, workbooks and predecessor versions unchanged.
- No XML or workbook edits unless specifically requested.
- Do not upload, overwrite, move, delete, or regenerate project files without explicit authorization.
- Lifecycle states remain distinct; never claim ledger/workbook/read-back integration without actual evidence.
- Do not resume cancelled WO64819 CP18 unless explicitly requested; the latest chat-level WO64824 context is separate.

## Migration boundary
GitHub currently contains text bootstrap/control files only. V53 XLSX, ROM, annotated LST, XMLs, scripts and reports have not been imported as binary/source artifacts. Large files should be added through a local Git clone; use Git LFS for large LSTs if needed. OneDrive remains the verified source location until each artifact is committed and read back from GitHub.
