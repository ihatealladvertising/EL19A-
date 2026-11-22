# EL19A Project State

**Historical snapshot:** 2026-11-16 (V55; superseded by V58 on 2026-11-21). See the current-state synchronization block below.  
**Repository:** private `ihatealladvertising/EL19A-`  
**Operational control:** GitHub `CONTROL/active_work_orders.md` is the sole current authority (cutover commit `83a9d6c36e65103f0749a26b31a13e8c4389dfc5`). Former OneDrive Control Notebook is a historical archive and remains unchanged.
**Migration:** V55 XLSX is present on GitHub `main` at `WORKBOOK/EL19A_Master_Reverse_Engineering_Workbook_V55_WO64830_BFamilyClosure_2026-11-15.xlsx`; Git blob SHA `83a065db94c0945d352aac86f2d55353c547cebd`, upload commit `b9793eee8d09f25c8315175a1ce4af1bc01900f6` (2026-11-16T02:19:47Z). V54 is its predecessor; V53 remains retained with an `OLD_` prefix.

## Current synchronization — 2026-11-22

This section supersedes the older V55 operational-status statements below. The historical V55 checkpoint is retained; it is not the current workbook or lifecycle state.

- **Sole operational authority:** `CONTROL/active_work_orders.md` on `main`.
- **Current Master Workbook:** `WORKBOOK/EL19A_Master_Reverse_Engineering_Workbook_V58_WO65114_ThinReferenceCloseout_2026-11-21.xlsx`; 1,355,957 bytes; 149 sheets; Git blob SHA `58f0599c45fc7ee032d55110d186d7a846a02234`.
- **Current lifecycle at synchronization:** WO65151 is ACTIVE — CLAIMED; 27 work orders are reserved/unclaimed; no open pull requests at the time of this readback. Consult the live register for subsequent allocations and changes.
- **Latest technical integration:** WO65180, WO65181 and WO65182 are CLOSED — BOUNDED COMPLETE, merged through PRs #40, #41 and #42 respectively.
  - WO65180: both `0x0B756/0x0B7D6` query producers and first accumulator consumers are resolved; physical units remain unresolved.
  - WO65181: F3D6/F3DE shared query lineage resolves to `min(UWORD[FFFF8596] >> 7, 255)`; first downstream 32-point UWORD calculation paths are identified; timer timebase/physical units and actuator endpoint remain unresolved.
  - WO65182: ADC2 channel arguments `0x1B/0x1F` resolve to MCU inputs AN27/AN31; actual board AVref and physical coolant/IAT channel assignments remain unresolved. The nominal-5-V scale comparison is corrected: 19.53125 mV per staged `>>2` count and 156.25 mV per 8-count step; exact 160 mV requires AVref 5.12 V, not established on the ECU.
- **New reservations:** WO65183–WO65185 cover the QDSPT threshold/mode gate, the 0x0A342/0x0A382 query-selector/output path, and the separate 52.34% screenshot scalar feasibility frontier. WO65186–WO65188 cover the F3D6 dynamic clamp bounds, the shared F3D6/F3DE table-path gate FFFF99E7.bit3, and the selected difference-event 0x4E handler continuation. All six remain RESERVED — NOT STARTED; unclaimed. The other current reservations are listed in CONTROL/active_work_orders.md. No technical results are claimed for these specifications.

- **Artifact boundary:** these integrations changed only the assigned CONTROL reports and coordinator evidence notes. No new workbook, XML/A2L, ROM/LST, calibration catalogue, indexes, scripts or tools were edited.
- The old OneDrive Control Notebook remains historical only. Do not use this document's legacy snapshots to infer live WO lifecycle; reread the live register.

## Target identity
- 2008 Nissan Versa / Sentra C11X, manual transmission
- ROM: `VERSA f501.bin`, 1 MiB
- MD5: `46991697c502052752a2cabcb84c9e27`
- SHA256: `bfe037e8e6c389e2a90214047058eb6dc3bcaaaac5b5931bf98a3f5d9f64fd6a`
- CPU: Renesas SH7058 / SH705822N, SH-2 big-endian
- FID: `8CMCKRN5`
- IDA ROM base: `0x00000000`

## Engineering archive
**Historical workbook snapshot:** V55 — [`EL19A_Master_Reverse_Engineering_Workbook_V55_WO64830_BFamilyClosure_2026-11-15.xlsx`](WORKBOOK/EL19A_Master_Reverse_Engineering_Workbook_V55_WO64830_BFamilyClosure_2026-11-15.xlsx). Git blob SHA `83a065db94c0945d352aac86f2d55353c547cebd`; upload commit `b9793eee8d09f25c8315175a1ce4af1bc01900f6`. V54 is predecessor.

**V55 identity:** 1,357,719 bytes; local MD5 `960e88a4cb4bd3372e038db507b1ab61`; local SHA-256 `8fba20dfde97ce0f1daa71905e9ca8333c847b79a3d1f67706f25310f7d69887`. GitHub binary presence/commit is confirmed; raw XLSX byte read-back/hash recomputation was not available in the connector.
- Previous OneDrive source item: `F6DEFBD470240AE6!s67636be33e09417eabca44b75955d417` (raw V54 source previously read-back verified).
- GitHub blob SHA: `20a304effc7656596e1bd19c65b623140ec511d2` (matches the previously verified V54 bytes exactly).
- Size: 1350922 bytes; 144 sheets
- MD5: `49491a933e31f11bce0b859d8b4c376e`
- SHA-256: `b566fe7f19066caa16928788da83442d1d217e296454dbc6d59808f97897c244`
- Exact raw read-back was materialized and compared byte-for-byte with the final local export: MATCH.
- Additive successor from V53; V53 predecessor remains unchanged.
- V54 adds five sheets: WO64827 E974 Gate Trace; WO64828 E974 Input Audit; WO64829 E974 Feedback Trace; E974 Integrated Checkpoint; V54 Checkpoint. It also updates Session Control, WO Continuity Ledger, Batch Checkpoint Manifest and Project Index.
- V54 integrates WO64827–WO64829 technical closeouts; WO64825 remains PARTIAL. No XML edits, calibration promotions, or donor scale transfers.
- V54 XLSX remains in GitHub as the predecessor. V55 is the current master; V53 is retained as `WORKBOOK/OLD_EL19A_Master_Reverse_Engineering_Workbook_V53_WO64817CP16_PAIR01_2026-11-15.xlsx`.
- V55 additive checkpoint adds WO64830 closure and Timer-11 pin-mux supplement; it is committed and is the current GitHub master. Summary: `WORKBOOK/V55_WO64830_INTEGRATION_SUMMARY_2026-11-15.md`.

## Operational state — GitHub control authority
1. V53 checkpoint and its exact Control Notebook reciprocal save remain a historical snapshot: WO64817 PARTIAL/PAUSED at CP16; WO64819 ACTIVE (PAIR-01); WO64820/WO64821 QUEUED; WO64816/WO64818 PARTIAL/PAUSED; WO64795 proposed/not issued.
2. Later Library Notebook paste (2026-11-15 17:55) recorded WO64822 ACTIVE and WO64819 paused at CP18; this was a separate snapshot and must not be silently merged.
3. GitHub control records now record WO64827, WO64828, WO64829 and WO64830 as TECHNICAL SCOPE COMPLETE. V54 incorporates WO64827–WO64829; local V55 adds WO64830. WO64825 remains PARTIAL.
4. On 2026-11-15 the user designated GitHub `CONTROL/active_work_orders.md` as the sole operational authority. The existing file was updated in place and read-back verified. The former OneDrive Control Notebook is historical only; do not wait for it or update it.
5. WO64829's remaining callback conversion/gating work is a concrete next lead only, **not issued as a new WO**.

The GitHub register now records WO64832–WO64838 as technical scopes complete; no active work order remains. WO64835/64836 confirmed F062/E0CE's exact mTRPAMB/mLPAMB fingerprint but rejected live pressure semantics because HCAN1 MB12 is initialized inactive (MBC=111) and the query resolves to zero. WO64837 confirmed the exact F39E/E124 mTTVBHOS/mLVBHOS fingerprint, with target squared-difference query and internal correction output; physical meaning/units remain provisional. WO64838 confirmed exact F426/mTTXNEL raw payload, but FFFF84B8 source/temperature axis remains unproven and both known consumers are internal status/qualification paths. WO64839 confirmed E424 exact 16/16 mTA5N raw fingerprint; target uses the value in a four-UBYTE normalized product feeding FFFF12B0/FFFF1D1A, but no RPM mapping is proven. WO64840 confirmed F2B2 exact 16/16 mTTNKAS raw fingerprint; its query byte FFFF85A8 is the same current timer-derived index as FFFF85A9 (`min(UWORD[FFFF8596]>>7,255)`); target /64 product contributes to accumulated internal UWORD FFFF12F0. RPM/post-start semantics remain unproven. WO64825 remains PARTIAL; deferred legacy entries WO64275/64276/64435 are not silently resumed. Older V53 and Library snapshots remain preserved as historical records, not current lifecycle state.

## Technical authority and evidence
- V55 workbook is the current authoritative engineering archive; V54 and V53 are retained as historical predecessors. No active work order. The user-authorized three-WO batch WO64847–WO64849 is complete. A0E2 contributes to FFFF1D3B and downstream internal correction paths; physical ignition endpoint and screenshot 52.34% scalar remain unproven. WO64842 is closed with HOS semantics/units unresolved.
- Candidate inventory: V7 / 122 unique `storageaddress` placements; screenshot-scope broader inventory is 175 (122 + 53). The full 175 membership is not freshly audited.
- See V55 sheets (plus unchanged V54 predecessor sheets): `Session Control`, `WO Continuity Ledger`, `Batch Checkpoint Manifest`, `V54 Checkpoint`, `Theory Handoff 2026-11-15`, `Project2 1D Crosswalk`, `EL19A 1D Lookup Candidates`, `P2 Candidate Register`, `P2 Handoff Log`, `Candidate Evidence Ledger`.
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
GitHub contains the V55 Master Workbook binary and text control records / CSV supplement. V54 and V53 are retained as historical predecessors. V55 presence and Git blob/commit identity are verified; its local content hashes are recorded in the integration summary. The former OneDrive Control Notebook is superseded and intentionally unchanged; GitHub `CONTROL/active_work_orders.md` is the sole operational control.
