# EL19A Project State

**Snapshot:** 2026-11-15 (V54 E974 integration)  
**Repository:** private `ihatealladvertising/EL19A-`  
**Operational control:** GitHub `CONTROL/active_work_orders.md` is the sole current authority (cutover commit `83a9d6c36e65103f0749a26b31a13e8c4389dfc5`). Former OneDrive Control Notebook is a historical archive and remains unchanged.
**Migration:** V54 XLSX is committed in GitHub and verified against the previously verified V54 bytes by exact Git blob SHA. V53 is retained in GitHub with an `OLD_` prefix as the predecessor.

## Target identity
- 2008 Nissan Versa / Sentra C11X, manual transmission
- ROM: `VERSA f501.bin`, 1 MiB
- MD5: `46991697c502052752a2cabcb84c9e27`
- SHA256: `bfe037e8e6c389e2a90214047058eb6dc3bcaaaac5b5931bf98a3f5d9f64fd6a`
- CPU: Renesas SH7058 / SH705822N, SH-2 big-endian
- FID: `8CMCKRN5`
- IDA ROM base: `0x00000000`

## Engineering archive
**Current GitHub Master Workbook:** V54 — [`EL19A_Master_Reverse_Engineering_Workbook_V54_E974_WO64827_64829_2026-11-15.xlsx`](WORKBOOK/EL19A_Master_Reverse_Engineering_Workbook_V54_E974_WO64827_64829_2026-11-15.xlsx).
- Previous OneDrive source item: `F6DEFBD470240AE6!s67636be33e09417eabca44b75955d417` (raw V54 source previously read-back verified).
- GitHub blob SHA: `20a304effc7656596e1bd19c65b623140ec511d2` (matches the previously verified V54 bytes exactly).
- Size: 1350922 bytes; 144 sheets
- MD5: `49491a933e31f11bce0b859d8b4c376e`
- SHA-256: `b566fe7f19066caa16928788da83442d1d217e296454dbc6d59808f97897c244`
- Exact raw read-back was materialized and compared byte-for-byte with the final local export: MATCH.
- Additive successor from V53; V53 predecessor remains unchanged.
- V54 adds five sheets: WO64827 E974 Gate Trace; WO64828 E974 Input Audit; WO64829 E974 Feedback Trace; E974 Integrated Checkpoint; V54 Checkpoint. It also updates Session Control, WO Continuity Ledger, Batch Checkpoint Manifest and Project Index.
- V54 integrates WO64827–WO64829 technical closeouts; WO64825 remains PARTIAL. No XML edits, calibration promotions, or donor scale transfers.
- GitHub contains the V54 XLSX binary at the current-master path above. V53 is retained as `WORKBOOK/OLD_EL19A_Master_Reverse_Engineering_Workbook_V53_WO64817CP16_PAIR01_2026-11-15.xlsx`. The V54 Git blob SHA was calculated from the previously verified raw V54 file and exactly matches GitHub's repository blob SHA.

## Operational state — GitHub control authority
1. V53 checkpoint and its exact Control Notebook reciprocal save remain a historical snapshot: WO64817 PARTIAL/PAUSED at CP16; WO64819 ACTIVE (PAIR-01); WO64820/WO64821 QUEUED; WO64816/WO64818 PARTIAL/PAUSED; WO64795 proposed/not issued.
2. Later Library Notebook paste (2026-11-15 17:55) recorded WO64822 ACTIVE and WO64819 paused at CP18; this was a separate snapshot and must not be silently merged.
3. GitHub chat-level control records now record WO64827, WO64828 and WO64829 as TECHNICAL SCOPE COMPLETE. V54 incorporates all three. WO64825 remains PARTIAL.
4. On 2026-11-15 the user designated GitHub `CONTROL/active_work_orders.md` as the sole operational authority. The existing file was updated in place and read-back verified. The former OneDrive Control Notebook is historical only; do not wait for it or update it.
5. WO64829's remaining callback conversion/gating work is a concrete next lead only, **not issued as a new WO**.

The GitHub register now records no active WO, WO64827–WO64829 technical scopes complete, and WO64825 PARTIAL. Older V53 and Library snapshots remain preserved as historical records, not current lifecycle state.

## Technical authority and evidence
- V54 workbook is the current authoritative engineering archive; V53 is retained as an unchanged historical predecessor.
- Candidate inventory: V7 / 122 unique `storageaddress` placements; screenshot-scope broader inventory is 175 (122 + 53). The full 175 membership is not freshly audited.
- See V54 sheets: `Session Control`, `WO Continuity Ledger`, `Batch Checkpoint Manifest`, `V54 Checkpoint`, `Theory Handoff 2026-11-15`, `Project2 1D Crosswalk`, `EL19A 1D Lookup Candidates`, `P2 Candidate Register`, `P2 Handoff Log`, `Candidate Evidence Ledger`.
- All semantic candidate names remain provisional unless target reader, lookup mechanics and downstream use establish them. Do not transfer donor scaling/units.

## Operating constraints
- Minimum chat, tool calls and analysis overhead.
- Prefer local PowerShell/Python for bulk extraction; assistant interprets/adjudicates.
- Preserve original ROMs, LSTs, XMLs, scripts, workbooks and predecessor versions unchanged.
- No XML or workbook edits unless specifically requested.
- Do not upload, overwrite, move, delete, or regenerate project files without explicit authorization.
- Lifecycle states remain distinct; never claim ledger/workbook/read-back integration without actual evidence. GitHub `CONTROL/active_work_orders.md` is the sole operational lifecycle register.
- Do not resume cancelled WO64819 CP18 unless explicitly requested; the latest chat-level WO64824 context is separate.

## Migration boundary
GitHub contains the V54 Master Workbook binary and text control records / CSV supplement. V53 is retained in the repository as the renamed historical predecessor. The V54 binary identity is verified by exact Git blob SHA match to the previously verified raw V54 file. The former OneDrive Control Notebook is superseded and intentionally unchanged; GitHub `CONTROL/active_work_orders.md` is the sole operational control.
