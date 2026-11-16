# EL19A — Operational Control and Work-Order Register

**Operational authority:** this GitHub file is the single source of truth for current work-order lifecycle, assignments, priorities, continuation and handoff.
**Repository:** `ihatealladvertising/EL19A-` · **Branch:** `main` · **Effective:** 2026-11-15 (user-authorized cutover)
**Update rule:** edit this existing file in place; commit to GitHub; read back and verify. Do not maintain a parallel operational OneDrive control notebook.

## Current operational state

- **Active work order:** WO64857 — FFFF8534+0x19 consumer and control-endpoint trace. See [WO64857](WO64857.md). Follow the new FFFF85DF consumer output; determine whether it reaches a throttle target/actuator.
- **Completed:** WO64856 — found direct FFFF85DF reader at 0x37F82; it contributes to computed UBYTE FFFF8534+0x19. Callback 0x59CAE is entry 3 in a nine-function dispatch table; exact cadence unresolved. See [WO64856](WO64856.md).
- **Completed batch:** WO64850, WO64854 and WO64855 are complete; their scalar/AB22 traces are not to be repeated.
- **Completed:** WO64855 — FFFF1C78+0x24 consumer chain continues through FFFF1054+0x2AD to FFFF1054+0x468; all demonstrated endpoints are internal RAM state, no throttle actuator path proven. See [WO64855](WO64855.md).
- **Completed:** WO64854 — corrected the suspected 9F8/9FA linkage (separate sub_6E558 state, not AB22); AB22 byte output feeds a bounded UWORD at FFFF1C78+0x24, but throttle role remains unproven. See [WO64854](WO64854.md).
- **Completed:** WO64850 — resumed scalar audit found 0x90EA is one of a 16-UWORD block feeding composite internal state FFFF2150+0xAD4; no 52.34% conversion or throttle endpoint. See [WO64850](WO64850.md).
- **Completed:** WO64853 — bounded DMAC/DTC audit found no programmed SAR/DAR transfer or descriptor for FFFF14E0/FFFF1018; indirect provenance remains unresolved. See [WO64853](WO64853.md).
- **Completed:** WO64852 — FFFF1018 UWORD producer confirmed at 0x4057C; no direct reader or explicit pointer alias found in the annotated listing. Bulk-copy/DMA/DTC consumer not established; physical throttle endpoint unproven. See [WO64852](WO64852.md).
- **Completed:** WO64851 — ATU02/ATU12 interrupt paths call sub_2088C → sub_257AC; timer-delta arithmetic and Timer-1A register involvement confirmed, but FFFF14E0 producer, physical event, clock/cadence and RPM conversion remain unresolved. See [WO64851](WO64851.md).
- **Paused:** WO64850 — independent 52.34% throttle-reduction scalar discovery. Paused by user-prioritized E678/E688 follow-up; retain its existing findings and resume only after this bounded batch or further user direction. See [WO64850](WO64850.md).
- **Completed batch:** E678/E688 follow-up WOs WO64851–WO64853 are complete; do not repeat those traces.
- **Completed:** WO64849 — A0E2 runtime role and correction convergence. Periodic path calls A0E2 reader then sub_44054; FFFF120A × UBYTE FFFF1466 contributes to bounded FFFF1D3B. sub_44E78/sub_59F46 derive FFFF14BC/14BD, sub_45114 selects FFFF1D4C, and difference-driven E2ED/DE6E lookup paths write FFFF10CE and FFFF2150+0x558 / FFFF1D18+6. Physical spark/coil endpoint and MBT semantics remain unproven; 52.34% scalar remains unrelated/unidentified. See [WO64849](WO64849.md).
- **Completed:** WO64848 — 9C2E/9DAE paired-map audit. Corrected FFFF1D7F.bit7 to a path gate, not a demonstrated map selector. Both 16×16 lookups execute sequentially with identical inputs/axes; V55 records byte-identical payloads, so their masked outputs cancel and the FFFF1C79 path reduces to signed high-byte conversion of UWORD FFFF10F8. Query producers and downstream FFFF1C79 consumer remain unresolved. Historical WO64275/64276/64435 were reconciled as stale notes, not reactivated. See [WO64848](WO64848.md).
- **Completed:** WO64847 — E974 callback final byte generation. Reconstructed FFFF85DF = mode-selected baseline/adjusted max(A,B) with FFFF19D1 signed offset and 0x1B override; FFFF85E0 copies FFFF85DF in bit2 mode, otherwise uses min(UWORD[FFFF1CA8+0x24]>>8,127). Scheduler cadence and physical endpoint remain unresolved; no XML/workbook edits. See [WO64847](WO64847.md).
- **Completed:** WO64846 — screenshot Throttle Reduction Rate scalar. A0E2 is a 4×4 UBYTE map read via sub_22B44 at 0x43F02, axes E002/E006; its 0x43 cell is a numeric coincidence with 52.34% under unsupported ×0.78125. Result stored at FFFF1207; no throttle-reduction semantics or physical endpoint established. The screenshot scalar remains unidentified. See [WO64846](WO64846.md).
- **Completed:** WO64845 — FFFF860D upstream status-byte producer. The 0x20Fxx routine copies FFFF860D/E into FFFF860B/C; sub_2245C call at 0x20FE2 copies FFFF861A to FFFF8613, not into FFFF860D. 44 exact references were reviewed; no direct FFFF860D writer established. Source remains unresolved at RAM boundary; no coolant comparator/threshold found. See [WO64845](WO64845.md).
- **Completed:** WO64844 — mDSHCUT / FFFF860B.bit3. Exact-reference scan found many readers but no direct bit-3 writer. The only direct pointer-store path at 0x20FD4–0x20FE0 copies FFFF860D/E into FFFF860B/C; 44 exact references to FFFF860D were found, with no direct writer established in the bounded pass. Retain generic FFFF860B.bit3 only; coolant comparator, target scalar, X−50°C conversion and fDSHCUT semantics remain unproven. See [WO64844](WO64844.md).
- **Completed:** WO64843 — E934/mTHPAMB: strong partial 16-point structure and reciprocal raw/128 composite arithmetic, but query resolves to high byte of CAN-mailbox-related constant 0xDA80, not a demonstrated pressure-mV input. Retain generic E934 only; eliminate mTHPAMB pressure semantics. Outputs terminate in internal state; no physical endpoint. Donor raw payload equality untested.
- **Completed:** WO64842 — E904/E914 vs V6 mTHOSNTP/mTHOSRCV: strong partial geometry/storage fit (16-point UBYTE curves and 16-point UWORD axes); donor V6 raw payload unavailable. Target query = `(U8[FFFF85A9] × U16[FFFF8494]) >> 4`; FFFF85A9 is timer-rate-derived and FFFF8494 is seeded from an A552-derived UWORD result. Target `>>7` applies raw/128 equivalent inside composite product. Distinct indexed paths update bounded internal event/state; rpm·ms units and HOS semantic/physical endpoint unresolved. Retain generic E904/E914 only; no XML promotion.
- **Completed:** WO64841 — A342/A382 paired maps: exact 8×8 UBYTE geometry and exact donor raw X/Y axes; target map payloads differ. DFF2 uses timer-rate query FFFF85DA (RPM relation unproven); DFFA uses FFFF857A from bounded UWORD lookup/shift path. FFFF85FB.bit7 selects A382 vs A342 but writer/mode meaning remain unresolved. Target map result enters composite product and bounded internal UWORD state; no physical endpoint. Retain generic pair only; no donor percentage conversion or semantic XML promotion.
- **Completed:** WO64835 — F062/E0CE exact 16/16 structural match to Juke mTRPAMB/mLPAMB; query source is MB12 control/identifier, not payload; MB12 inactive in target initialization and query resolves to zero. Active pressure-table semantics rejected; keep generic exact fingerprint only. See corrections in WO64835/WO64836.
- **Completed:** WO64834 — E678/E688 retained as generic QDSPT/dashpot candidates; strong partial structural fit, partial family-behaviour fit; no donor axis/conversion or D/N semantic promotion.
- **Completed:** WO64833 — EFA4→mTFVAPO correspondence rejected by 0/16 byte equality across all three Juke donor ROMs; EFA4 remains generic.
- **Completed:** WO64832 — bounded structural/behaviour test complete; retain F3D6/F3DE as generic schedule candidates only. No donor conversion or TVO semantic promotion.
- **Completed:** WO64830 remains TECHNICAL SCOPE COMPLETE at the bounded internal-state endpoint; do not repeat its completed trace.
- **Completed technical work:** WO64827, WO64828 and WO64829 — technical scopes complete. Detailed evidence remains in `CONTROL/WO64828.md`, `CONTROL/WO64829.md`; WO64827 closeout is preserved below.
- **Partial / paused:** WO64825 remains PARTIAL. Preserve its unresolved scope; do not resume without explicit authorization and a concrete lead.
- **Timer-11 supplement to WO64794 (2026-11-15):** target code at `sub_2598E` writes `PLIOR=0x37EF`, `PLCRH=0`, `PLCRL=0`, `PLIR=0`, `PLDR=0x0400`. PL1/PL2 direction bits are outputs, but the Port-L function-select bits are cleared; no PLCRL reconfiguration was found in the bounded LST text search. Thus the configured Timer-11 compare events are **not shown routed to TIO11A/B pins**; the ignition-coil hypothesis is weakened. WO64794 overall remains PARTIAL; Timer-11 interrupt purpose and other output hardware remain open.
- **Deferred candidate (not issued):** 9C2E/9DAE differential provenance/consumer path. Before issue, reconcile legacy V54 `P2 Work Orders` entries WO64275/WO64276 and WO64435 against this register; do not silently reactivate or duplicate them.
- **Workbook:** current GitHub master is V55: `WORKBOOK/EL19A_Master_Reverse_Engineering_Workbook_V55_WO64830_BFamilyClosure_2026-11-15.xlsx` (Git blob SHA `83a065db94c0945d352aac86f2d55353c547cebd`; upload commit `b9793eee8d09f25c8315175a1ce4af1bc01900f6`, 2026-11-16T02:19:47Z). V54 is the predecessor. The V55 binary's presence/commit is verified; its local MD5/SHA-256 identity is recorded in the integration summary but was not recomputed from GitHub raw bytes in this check.
- **Former OneDrive Control Notebook:** superseded; leave unchanged as a historical archive.

## Operating rules

1. This file alone controls current work-order status, allocation, priority, dependencies, pause/resume conditions and next action.
2. A new WO, resume, cancellation or priority change requires user authorization or an explicit existing standing instruction.
3. Do not infer an active WO from old snapshots, completed investigations or unissued leads.
4. Record each material status change here, with date, rationale, evidence link and commit. Keep detailed technical evidence in its WO record and the Master Workbook.
5. At each handoff, state the exact next action, source reference, dependencies, unresolved boundaries and completed work not to repeat.
6. Preserve historical snapshots and original artifacts. Do not delete or overwrite the former OneDrive Notebook.

## Latest checkpoint — 2026-11-16
WO64843 closed at a bounded internal-state endpoint. E934/E082 is a strong partial 16-point UBYTE structural match; the query is high byte 0xDA of a CAN-mailbox-related constant 0xDA80 copied into FFFFA338. Target interpolation at that query returns 0x82. The target uses the raw/128 coefficient reciprocally in signed division and as a query to a second lookup, but the mV-axis/pressure interpretation is contradicted. Retain generic E934 only. WO64844 is ACTIVE: trace FFFF860B.bit3 writer and coolant-temperature threshold source against V6 mDSHCUT/fDSHCUT; A2L conversion is X-50°C, -40°C predicts raw 0x0A. Do not repeat the sub_403D8 read test or completed QDSPT curves.

## Previous checkpoint — 2026-11-16
WO64832 closed at a bounded internal software-event endpoint. Structural fit to the JUKE `mTTVOULM/mTTVOULMS` architecture is STRONG PARTIAL; target TVO-angle semantics are WEAK. The target query comes from `UWORD[FFFF85CE] >> 4`; its upstream writer and the dynamic-bound producers remain unresolved. The target calculates two bounded UWORD schedules and compares them to trigger internal event/status handling; no physical throttle endpoint is proven. WO64833 completed: EFA4→mTFVAPO eliminated by 0/16 raw-byte equality across three Juke ROM variants; its timer-derived query and internal FFFF1014 dataflow contradict the donor fixed-RPM/angle configuration. WO64834 completed: E678/E688 retained as generic QDSPT/dashpot candidates (strong partial structure; partial family behaviour); Juke raw bytes differ, V6 raw HEX unavailable, RPM axis and ×2 L/min conversion unproven; FFFF1676 is a 0/255 runtime gate, not ×2 conversion; internal output FFFF1018 only. WO64835/WO64836 closed the F062/mTRPAMB test: exact structure remains, but HCAN1 MB12 is initialized with MBC=111 (inactive), message-control word zero, and no data-field consumer/reconfiguration found. F062 query is q=0 in the observed configuration, returning zero; live pressure semantics are rejected. No XML/Workbook edit. No XML or Master Workbook edits. V55 remains current.

## Previous checkpoint — 2026-11-16
WO64841 closed as a bounded internal software calculation. Structural fit: STRONG PARTIAL (two 8×8 UBYTE maps; both raw axes exactly match Juke mMITANDA/mMITANDD axis vectors; target 64-byte map payloads differ). Behaviour fit: PARTIAL/UNRESOLVED (DFF2 uses timer-rate-derived UWORD FFFF85DA, not a proven RPM quantity; DFFA uses FFFF857A from a UWORD lookup/shift path; FFFF85FB.bit7 chooses A382 vs A342 but its writer and mode meaning were not located; result enters a runtime composite calculation; no physical endpoint). Preserve generic A342/A382 names only. WO64842 is now ACTIVE for E904/E914 versus V6 mTHOSNTP/mTHOSRCV; reference theory is 16-point UBYTE, raw/128 data, 16-point UWORD rpm·ms axis at raw×0.1953125. The target reader is known; active work is query provenance, unit compatibility and composite downstream behaviour. V55 remains current. No XML/Workbook edits.

## Latest checkpoint — 2026-11-16
WO64842 closed as a bounded internal-state curve test. Reference geometry is 16×UBYTE data and 16×UWORD axes, but donor V6 raw payload is unavailable. Both target queries derive from U8 FFFF85A9 × U16 FFFF8494 /16; the UWORD factor is copied from +2, whose bounded writer is an A552-derived result. Target applies >>7 raw/128-equivalent scaling inside composite products, then routes to separate internal event/state paths. The target's rpm·ms axis equivalence and HOS meaning remain unresolved; retain generic E904/E914 only. WO64843 is now ACTIVE for E934/E082 vs V6 mTHPAMB/mLHPAMB. Reference: 16×UBYTE raw/128 coefficient on a 16-point UBYTE axis raw×20mV. Target data/axis and sub_22F28 reader are known; work is query FFFFA338 provenance, pressure-unit compatibility, composite scale and direct consumers. V55 remains current; no XML/Workbook edits.
## Previous checkpoint — 2026-11-15

WO64830 completed the bounded B-family downstream trace. All five B212-derived bytes (FFFF2834–FFFF2838) and the B012/B112-derived bytes (FFFF27CC–FFFF27CE) reach dynamic numeric threshold comparisons and internal state/counter updates. No physical sensor/actuator or MMIO endpoint was established. The next 9C2E/9DAE branch is not issued pending reconciliation of legacy V54 ACTIVE entries WO64275/64276/64435. Timer-11 PL1/PL2 pin-mux audit weakens its TIO11 ignition-output hypothesis; WO64794 remains PARTIAL. V55 local export exists; V54 remains current GitHub master until V55 is uploaded and verified.

## Cutover record — 2026-11-15

User authorized replacement of the OneDrive Control Notebook with this existing GitHub register. Older OneDrive/Library states are retained as historical, not merged into current lifecycle state. This GitHub file is the operational control point.

## Archived work-order evidence and historical snapshots


## WO64829 closeout / checkpoints 1–2 (2026-11-15)
- **Status:** TECHNICAL SCOPE COMPLETE — bounded internal-state reconstruction. Full evidence: `CONTROL/WO64829.md`.
- **Reader:** `sub_22E10` is a 16-point UBYTE lookup with adjacent-sample interpolation; `q>=0xF0` returns numeric sentinel 0xF0. Interpolation is linear from sample A toward B with fraction `(q&0x0F)/16), integer truncation, no rounding.
- **First lookup:** base `0xF38E`; `q1=min(4×max(UBYTE(FFFF1CA8+0x29)-UBYTE(FFFF1CA8+0x3A),0),255)`. Delta >=60 returns sentinel 0xF0. Bytes: `7D 7C 76 6E 66 60 5A 53 4D 46 40 3A 33 2D 26 20`.
- **Feedback multiply / second lookup:** prior `FFFF19BF` × first lookup result passes through `sub_223FC` = arithmetic `>>7`; raw result is capped at 0x80 for the second query. `q2=min(2×(128-v),255)`, where `v=min(floor(prior×first_result/128),128)`. For v<=8, second lookup returns sentinel. Base `0xF092`; bytes: `00 08 0C 0F 14 19 1E 23 28 2D 32 37 3C 41 46 4B`.
- **State selection:** `D=clip_signed(S2-UBYTE(FFFF1990+0x1F1),-128,127)`; `K=clip_signed(UBYTE(FFFF1CA8+0x26)-(UBYTE(+0x01)+UBYTE(+0x29))+0x40,-128,127)`. `C=0x0A` when `FFFF1E54+5.bit4` is SET; `C=0` when CLEAR (ROM bytes at `0x8296/0x8297 = 0A 00`).
- **Outputs:** `FFFF19D1_next=min(max(D,K),C)). Returned `r2) becomes `FFFF19BF_next): `C` when `D>=K), otherwise `min(K,C)`. `FFFF1D99+0x6D.bit1` reflects whether the *uncapped* scaled feedback product is >127. `FFFF1D80+1.bit0` copies that flag when D>=K, otherwise is forced set.
- **Next lead, not issued as a new WO:** immediate caller preserves `max(FFFF1CAE,FFFF1CCC)` and combines it with `FFFF19D1` before conditional stores to `FFFF85DF` at `0x59BF2`, `0x59C02`, and `0x59C04`. The final conversion/gating equation and physical meaning remain unverified.
- **Integration:** GitHub WO file and register updated; Master Workbook and Stable Control Notebook unchanged. Exact Notebook read-back still unavailable (403); no authoritative Notebook lifecycle closure or reciprocal save verification claimed. No source artifacts modified.

## WO64828 closeout / checkpoint 5 (2026-11-15)
- **Status:** TECHNICAL SCOPE COMPLETE — bounded unresolved outcome. Full evidence: `CONTROL/WO64828.md`.
- **Dynamic alias resolved:** only observed `sub_506A0` caller at `0x51C58` is preceded by `sub_5062C` (`0x51C52`). `sub_5062C` returns R4 as `FFFF357E & 0x80`, so R4 is only `0x00` or `0x80`. `sub_506A0` zero-extends R4 to R9 and stores to `FFFF1C78+0x0E+2×R9`; only destinations `FFFF1C86` / `FFFF1D86` are reachable through this call. Target indexes 0x14/0x23/0x28 (fields `FFFF1CAE/1CCC/1CD6`) are impossible here.
- **Remaining boundary:** no producer for the three input fields, and no later explicit consumer/physical ADC or actuator endpoint for `FFFF85E0`, was established in the available LST. Other unrepresented indirect, bulk-copy, DMA or peripheral updates are not globally excluded.
- **Integration:** GitHub closeout committed; Master Workbook unchanged; Stable Control Notebook unchanged and exact live read-back unavailable (403). No source edits.
- **Next:** WO64829 reconstructed the feedback lookup/state logic. The remaining callback conversion to `FFFF85DF` is a separate candidate scope; do not assume physical meaning.

## WO64827 closeout (2026-11-15)
- **WO ID / Title:** WO64827 — E974 Downstream Gating and Consumer XREF Investigation
- **Agent:** Grok
- **Technical status:** COMPLETE (bounded investigation / stop condition met)
- **Depends on:** WO64825 (PARTIAL; preserved)
- **Investigation date:** 2026-11-15

### Confirmed findings
- **Timer-derived operand producer:** `sub_257AC → FFFF85E4 → sub_34476 → FFFF8596 → sub_344A4 → FFFF85D6`.
  - `sub_257AC` supplies the timer-derived `FFFF85E4) value; downstream conversion uses `48,000,000 / FFFF85E4`.
  - Saturation/fallback behavior observed: saturates at `0xFFFF`; fallback `0x044E`.
  - `sub_34476` forms `FFFF8596`; `sub_344A4` stores the shifted/scaled result to `FFFF85D6`.
  - The query path uses `FFFF8596 >> 7`, capped at 255.
  - Physical units and semantic name remain unresolved; do not assign a semantic XML name.
- **E974 output `FFFF1F0C):** drives `FFFF8626.bit2`; this affects `FFFF1C93` and downstream `FFFF19BF` / `FFFF85E0), optional ADC channel 9 aggregation, and `FFFF8494) threshold state (including the `FFFF2F00` path).
  - Furthest confirmed endpoint is internal status/threshold and ADC aggregation. No terminal physical sensor or actuator was established.
- **E974 output `FFFF1F0D):** gates a hysteretic update of `FFFF1E54.byte0 bit 0x20`. No separate direct consumer beyond the traced status behavior was established.
- **`sub_223FE` correction:** pure signed arithmetic helper, effectively `R0 >>= 6`; no RAM access, no side effects, no branches, and it does not read `FFFF1F0C` or `FFFF1F0D`. The word at `FFFF8594+2` is the scaled operand; E974 outputs are boolean enable gates, not numeric inputs.
- **0x55xxx correction:** earlier same-GBR interpretation was overbroad. Sites `0x5599A`, `0x55A24`, and `0x55C82` resolve to `FFFF8AF0/FFFF8AF1), not the E974 bytes at `FFFF1F0C/FFFF1F0D`. Do not count them as additional direct E974 consumers.
- **Decision:** keep physical semantics and XML promotion unresolved. No calibration/XML promotion is justified by this trace.

### Stop condition / unresolved boundaries
- Producer and conversion chain for the timer-derived operand are traced to the furthest supported point; physical units/name remain unknown.
- E974 downstream effects are traced to internal status, threshold, and ADC aggregation; terminal physical sensor/actuator remains unproven.
- The separate `0x55xxx` sites are not direct E974 consumers.
- These unresolved semantic/physical endpoints are explicit boundaries, not unfinished searches within WO64827's bounded scope. Further work requires a new concrete lead or separately authorized scope.

### Integration and lifecycle
- GitHub migration register updated from the previous PARTIAL snapshot using the completed investigation report.
- Master Workbook: **not edited**.
- Stable Control Notebook: **not edited / not read-back verified**; exact item `F6DEFBD470240AE6!sac2dd9024e574ee3a7462a1730baeddd` previously returned 403 `serviceReadOnly`.
- Therefore this GitHub record reports technical completion only; it does not claim authoritative Notebook lifecycle closure or reciprocal save verification.
- **Completed work not to repeat:** timer producer chain; E974 `FFFF1F0C` / `FFFF1F0D` downstream status paths; `sub_223FE` operand-vs-enable distinction; correction of the three `0x55xxx` addresses.
- **Historical next action (superseded):** reconcile the closeout to the then-authoritative OneDrive Notebook. On 2026-11-15 the user designated this GitHub register as the sole operational authority; do not reopen the Notebook-sync task.

## WO64825 register entry (2026-11-15, preserved)
- **WO ID / Title:** WO64825 — E974 Output-Chain Investigation
- **Agent:** Grok
- **Status:** PARTIAL
- **Findings (instruction-level from annotated LST):**
  - Callsite 1 (`0x3BB1A` / `sub_3BA88`): GBR=`FFFF1E54`; query = `(FFFF85C4+0x12)>>1` clamped; result → `GBR+0xB8` (`FFFF1F0C`); read-back `0x3BBE4`; non-zero gates `sub_223FE` path. Confirmed.
  - Callsite 2 (`0x3C042` / `sub_3BFC8`): identical GBR and query construction; result → `GBR+0xB9` (`FFFF1F0D`); read-back `0x3C104`; likewise gates `sub_223FE`. Confirmed. Paired with callsite 1.
  - Callsite 3 (`0x4130E` / `sub_412B8`): distinct GBR=`FFFF1D80`; query from `FFFF859C+0x12`; output `FFFF1F0E`; local read-back and bit tests only; no shared `sub_223FE` path observed. Confirmed distinct.
- **Evidence addresses:** `0xE974`, `0x3BB1A`, `0x3BB32`, `0x3BBE4`, `0x3BC0E`, `0x3C042`, `0x3C052`, `0x3C104`, `0x3C118`, `0x4130E`, `0x41318`, `0x41330`.
- **Integration note:** Investigation PARTIAL; predecessor to WO64827.

## Durable / historical snapshots
- **V53 checkpoint:** WO64817 PARTIAL/PAUSED at CP16; WO64819 ACTIVE (PAIR-01); WO64820/WO64821 QUEUED; WO64816/WO64818 PARTIAL/PAUSED; WO64795 proposed/not issued.
- **Later Library Notebook snapshot (2026-11-15 17:55):** WO64822 ACTIVE for broad calibration harvesting; WO64819 PAUSED after CP18; WO64820/WO64821 queued/deferred; WO64817/WO64816/WO64818 paused. V53 remains the master pointer.
- The later Library snapshot's WO64822 CP02 notes:
  - E974: three `sub_22E10` callsites at PCs `0x3BB1A`, `0x3C042`, `0x4130E`; query `min(FFFF85D6 >> 1, 255)`; outputs GBR+0xB8/+0xB9 and `FFFF1F0E`.
  - EE08/EE28: cascade/selector path in `sub_3BEA6` / `sub_3F3C6`, selector bit `0x40`, output `FFFF1054+0x3CC`.
  - F33E–F36E: shared `FFFF84B8` query; source unresolved. Do not repeat source-path scans already completed under WO64819.
- **WO64819 CP18:** user cancelled the bounded CP18 investigation. `FFFF37AE` (+0x90 from `FFFF371E`) remained unresolved; later Library snapshot records the WO paused at CP18. Do not reopen without explicit request and a concrete new lead.

## Historical Control Notebook access limitation
The former OneDrive Control Notebook item `F6DEFBD470240AE6!sac2dd9024e574ee3a7462a1730baeddd` returned 403 `serviceReadOnly` during migration. It is now a legacy read-only archive, not an operational source. Earlier references in this retained history to waiting for Notebook access are superseded by the 2026-11-15 authority cutover.


- **WO64829 selector correction (2026-11-15):** final branch audit corrects C polarity: bit4 SET selects ROM byte 0x8296 (=0x0A); bit4 CLEAR selects 0x8297 (=0x00). See `CONTROL/WO64829.md` correction note and `WORKBOOK/WO64828_WO64829_E974_CHECKPOINT_2026-11-15.csv`. Earlier opposite-polarity summary is superseded.


## V54 workbook integration (2026-11-15)
- **Current Master Workbook (OneDrive):** [EL19A_Master_Reverse_Engineering_Workbook_V54_E974_WO64827_64829_2026-11-15.xlsx](https://onedrive.live.com/personal/f6defbd470240ae6/_layouts/15/doc.aspx?resid=67636be3-3e09-417e-abca-44b75955d417&cid=f6defbd470240ae6); item `F6DEFBD470240AE6!s67636be33e09417eabca44b75955d417`; 1,350,922 bytes; 144 sheets; MD5 `49491a933e31f11bce0b859d8b4c376e`; SHA256 `b566fe7f19066caa16928788da83442d1d217e296454dbc6d59808f97897c244`. Exact raw read-back was materialized and compared byte-for-byte with the final local export.
- **Integrated WOs:** WO64827, WO64828 and WO64829 are TECHNICAL SCOPE COMPLETE and now recorded in V54 sheets `WO64827 E974 Gate Trace`, `WO64828 E974 Input Audit`, `WO64829 E974 Feedback Trace`, plus `E974 Integrated Checkpoint`.
- **Key correction:** WO64829 selector polarity is `FFFF1E54+5.bit4 SET => C=0x0A; CLEAR => C=0x00`. Earlier opposite-polarity wording is superseded.
- **Remaining lead (not issued):** reconstruct final byte-generation/gating from `max(FFFF1CAE,FFFF1CCC)` plus `FFFF19D1` into `FFFF85DF`; physical meaning and `FFFF85E0` endpoint remain unresolved.
- **Authority boundary:** Stable Control Notebook item `F6DEFBD470240AE6!sac2dd9024e574ee3a7462a1730baeddd` remains unchanged; exact read-back returned 403 `serviceReadOnly`. No authoritative lifecycle sync or globally verified active WO is claimed. WO64825 remains PARTIAL.
- **GitHub binary boundary:** repository still contains the V53 XLSX binary. Text control records and CSV supplement are being synchronized to V54; V54 XLSX binary has not been uploaded to GitHub by the available GitHub file-write interface.


## WO64831 closeout — 2026-11-15
- **Status:** SCOPE COMPLETE — bounded 45-minute Dashpot/Rev-Hang evidence consolidation. Full record: `CONTROL/WO64831.md`.
- **Confirmed/strong candidates:** E678/E688 are paired 16-point UBYTE QDSPT airflow-table candidates (`mTDSHPTD/N`); 0x848A/0x848B are paired UBYTE QDSPT reduction-rate scalar candidates (`mDDSHPTD/N`), but neither D/N selector labels nor donor scaling are proven in EL19A.
- **Critical distinction:** screenshot's single 52.34% Throttle Reduction Rate remains unidentified; it is not established by the paired 0x848A/0x848B bytes. A0E2 is a 4×4 map, not a scalar.
- **mDSHCUT:** V6 donor symbol is coolant-temp prohibition scalar, raw −50°C conversion; −40°C predicts raw 0x0A. EL19A `sub_403D8` tests `FFFF860B.bit3`, matching V6 `fDSHCUT` mask 0x08, but target flag meaning and threshold reader/address remain unproven. EL19A ROM 0x84C4 is pointer data, not the donor scalar.
- **EFA4:** 16-point UBYTE lookup feeds FFFF13EA and downstream FFFF1014 path; `mTFVAPO` is only a low-confidence morphology hypothesis, not an assignment. F3D6/F3DE remain strong `mTTVOULM/S` curve candidates.
- **No XML/workbook/source artifact edits.** No candidate promoted. Full distinctions, evidence addresses, corrections and next bounded investigation are in WO64831.md.
- **Next:** independently trace (1) EL19A coolant-temperature comparison and writer of `FFFF860B.bit3`; (2) the screenshot's single Throttle Reduction Rate scalar and its downstream throttle-target effect. Do not repeat completed E678/E688/EFA4 initial reader traces.
- **Operational state:** no new active WO issued; WO64831 is a completed consolidation record only.
