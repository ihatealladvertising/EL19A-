# Repository Integration Status

**State:** UNLOCKED

**Integrator:** ChatGPT — user-requested SH705x ROM tool plan and WO70020–WO70022 registration
**Purpose:** Publish the modular ROM-tool charter and three bounded architecture work orders. No implementation, ROM, LST, calibration XML, workbook, Findings or existing worker artifacts are authorized in this batch.
**Lock acquired:** 2026-11-26 — verified prior state UNLOCKED; serialize plan update for workbench integration priorities and source-level findings.

**Integrator:** ChatGPT — user-requested workbench Consult decoder/diff checkpoint (2026-11-26)
**Purpose:** Add auditable machine-readable per-call/per-table exports and regression coverage to the lookup scanner. No ROM, LST, XML, catalogue, scope matrix, workbook, Findings or worker-lane changes were made.
**Lock acquired:** 2026-11-26 — scanner tooling improvement; verified no concurrent integrator publication was in progress.
**Lock released:** 2026-11-26 — source, documentation, tests and workflow read back; GitHub Actions scanner test run 45900186172 passed (8 tests). No ROM binaries were available in this execution session, so no ROM census was run.
**Scanner source:** tools/sh7058_cross_rom_scanner.py — blob bf2b68b7b0cf88fd526ede20d1af180cf0b7a703; latest source commit 8b8f97868ea102f73011541002c3a8b4966aa177.
**Scanner documentation:** tools/sh7058_cross_rom_scanner.md — blob db619172ea73b4fbefeaf8dc02e8f3a9c13e7d3b.
**Regression tests:** tools/test_sh7058_cross_rom_scanner.py — blob bbef0833f70d8c608eaa8b85d186903f8e4a5571.
**CI workflow:** .github/workflows/sh7058-scanner-tests.yml — blob 731822940cdc3445e15050090899a4a2ecb72c06.

**Lock acquired:** 2026-11-26 — user-authorized transfer of unstarted WO70012 and WO70014 to Worker 2.
**Lock released:** 2026-11-26 — WO70014 and WO70012 reports and live register read back; Worker 1–3 READY queues empty; WO70006 remains BLOCKED at its complete raw-output input gate.
**Live register:** `CONTROL/active_work_orders.md` — blob `3e22ca9bbafb7b36a25883f6c21ffcb264402d58`; publication commit `e5cc635845181b760dca3bb3a7214643e0c1fd2a`.
**WO70012 report:** `CONTROL/WO70012.md` — blob `86a6cbde5f3566af9620809bb972dbc470cd3f24`; publication commit `e5cc635845181b760dca3bb3a7214643e0c1fd2a`.
**WO70014 report:** `CONTROL/WO70014.md` — blob `322ab166075363f91e2cce80e7fedb6718e3aa96`; publication commit `9b3d067170f1a73c2bf1fe3af6bb2741eda4877c`.
**WO70013 report:** `CONTROL/WO70013.md` — blob `aaf49a7082a4279ffe46bee37e112a022036071e`; report commit `1485da52689db055d1cfad14185c552bf7ce09db`.
**Finding:** `FINDINGS/records/FND-000026.md` — blob `6447a9360f62ac182b871636e6c043b252b009d3`; record commit `dbd00cac125c9296476689dc1b4f99a1a3038176`.
**Findings index:** `FINDINGS/INDEX.md` — blob `eb1f34429ba5397ff1c2a41470381778b0384510`; index commit `14229c4215cd64471710fd56b3e9437723f972f3`.
**Live register:** `CONTROL/active_work_orders.md` — blob `a2df26eacc5fd0412102f1929aa458905262ec4c`; register commit `de1c7103fedc6ff6b02617eb63485805195569cf`.
**Lock released:** 2026-11-26 — WO70013 report, FND-000026, index and Worker 2 lifecycle pointer read back; Worker 2 FIFO is exhausted; Worker 1 and Worker 3 heads unchanged.
**WO70010 report:** `CONTROL/WO70010.md` — blob `2284f00284e7bbe84e173c87338c072a387f3f19`; report commit `e9fa35ecc2e8c2b3d8d7499a1c83bdb5694ab921`.
**Live register:** `CONTROL/active_work_orders.md` — blob `7178415e3c31842b20cb773c44972e8fc5d3e978`; register commit `24dcafe1bf67d578f1cf4ee1cf38c3aefe709d73`.
**Lock released:** 2026-11-26 — WO70010 report and lifecycle pointer read back; Worker 2 FIFO advanced to WO70013; Worker 1 and Worker 3 heads left unchanged.
**WO70007 report:** `CONTROL/WO70007.md` — blob `801a42debc7fed7ebfc9b2af22d4968526ac71d7`; report commit `5c73a34dd7f51594bfef852302715e67b92eda4c`.
**Release 1 XML:** blob `4bab8bced09047c461520c6044415ca5357b0110`; **scope matrix:** blob `52fe30fdd760d3a13885007fe9391dead425ec21`; **catalogue:** blob `e8ee9f257e4cd114624cfc26dd08caecccdd59f7`; **manifest:** blob `657288a7e411dfd12ad2ecc0bea972c3165d7941`.
**Live register:** `CONTROL/active_work_orders.md` — blob `f504706813ff51abb74273d51e37dcfeb7ae1127`; register commit `f95944f9ed28383b1f33d3f5d10d684e8a629abb`.
**Lock released:** 2026-11-26 — WO70007 artifacts and lifecycle change read back; Worker 2 FIFO advanced to WO70010; Worker 1 and Worker 3 heads unchanged.
**WO70016 report:** `CONTROL/WO70016.md` — blob `f7c85eb0225ffb90eb5bb292ecd052b9c74c31f4`; report commit `d5c59bbf2779585e75fc877349df97d68d50e87a`.
**Live register:** `CONTROL/active_work_orders.md` — blob `a69d4caedc5c1e37ae31c71b5d064d608221106f`; register commit `7a74f2f3f2eeb79244c69597848d858bf8a92e05`.
**Lock commit:** `7e18f866d99f493c611590cd5ac614cb7c31455f`.

**Lock released:** 2026-11-26 — WO70016 report and lifecycle pointer read back; all three worker FIFO heads verified unchanged.
**WO70015:** `CONTROL/WO70015.md` — blob `dd4eed332f9b0e978de3c3dbcfdeab53cc81167d`, closeout commit `761c51bcfaa256018340a3f82b8c205ce6bf9441`.
**Live register:** `CONTROL/active_work_orders.md` — blob `48797f136b42dbfa4ca523102bb597e20a7621b3`, register commit `d58339ddc801973c92bb5c8c9e8e811731d16e6d`.

No worker WO, worker FIFO, Findings record/index, calibration XML, scope matrix, catalogue, workbook, ROM/LST/A2L, scanner/workbench source or protected evidence was changed in this batch.


**Integrator:** ChatGPT — follow-on work allocation for fingerprint join (2026-11-26)

**Purpose:** Publish WO70012–WO70014 for the three worker lanes and update the live FIFO register only.

**Integrator:** ChatGPT — EL19A target-side cross-ROM fingerprint join publication (2026-11-26)

**Purpose:** Publish `EVIDENCE/EL19A_22_FINGERPRINT_JOIN_2026-11-26.md`; no lifecycle, calibration definition, or Findings changes.

**Integrator:** ChatGPT — cross-ROM research record publication (2026-11-26)

**Purpose:** Publish the current project-direction record and outside-analyst prompt. No work-order lifecycle or calibration artifacts are being changed in this batch.

**Lock acquired:** 2026-11-26 — cross-ROM discovery research note
**Lock released:** 2026-11-26 — research note read back; current live queue read back and left unchanged

**Research note:** `EVIDENCE/CROSS_ROM_DISCOVERY_BATCH_2026-11-26.md` — blob `c7fb0346fed3bbd5ea21195d118d28fdb697b4a8`; commit `7e4ae9317a2c90dfa0f646e4c80ba45e939e2d67`.

No work-order lifecycle, lane ownership/FIFO, Findings, XML, scope matrix, catalogue, workbook, ROM/LST/A2L, or tool source was modified in this publication batch.
**Lock released:** 2026-11-26 — both documents and live-register pointer read back; existing lane assignments and FIFO verified unchanged

**Documentation batch commits:** gate lock `7a34fdf845803d7cb67044cabe30af27132c82ae`; project direction `4a81c8b2521e767526bce37b7eaa25d0902c8ea7`; outside analyst prompt `07a60cd179e4bc4d1d81b5bdb68f02e4428d0d7e`; register pointer `f722e2229019b0fc3630c1c54ce46cb8bbca95f3`.

No work-order lifecycle, assignment, priority, calibration XML, scope matrix, catalogue, workbook, ROM/LST/A2L, Findings or tool/source file was changed in this documentation batch.

**Lock acquired:** 2026-11-26 — WO70007–WO70011 allocation batch
**Lock released:** 2026-11-26 — five work-order reports and live register read back; lane assignments and FIFO order verified
**Lock released:** 2026-11-26 — WO70006 addendum read back and blocked lifecycle status verified  
**Lock released:** 2026-11-26 — all report, Findings, index and live-register readbacks verified

**WO allocation batch:** `WO70007`–`WO70011` created and read back on 2026-11-26.
- Report commits: `cbd724226c8ff1c40737a343384830f0563b188d` (70007); `2a61c5b756476f9c40049984dde7b963074d84d2` (70008); `c5ced00611cbf71364d0333a3c7e2e37cb757ecf` (70009); `d2375abd86b41e34f78456704b2d3d09ba332d76` (70010); `35b020bec13776b613eed2e63ccf42e10773bd72` (70011).
- Register commit: `ba29e52a24e4a9b846d934d76b5d1b22d4061d35`.
- Readback blobs: `WO70007 cd8e5a7feb6e6dd6b6df9b3a84ff59dec6a7a189`; `WO70008 7ef17695db82f21f84bef4c5adf2a5948e720e6c`; `WO70009 b2353b4596a20cf6b50e3f994b2b5ae891837f36`; `WO70010 046aa70855113b0e5cc8a5783293192b8a0dd86a`; `WO70011 742ab4e77f6966534133593162fa241f7c651364`; register `b49a259cbdafdd3538c0a289d6520b12da6ea3aa`.
- FIFO: Worker 1 `70008`; Worker 2 `70007 → 70010`; Worker 3 `70009 → 70011`.
- No Findings, XML, catalogue, workbook, ROM, LST, A2L, or script files changed in this allocation batch.

**Supplemental addendum commit:** `a000824d9f123eaf510a0e71be07fbb81cfda704` — WO70006 blob `8dcdc12eb5d4bcb48607e3dc4c1d89bd2d364a27`.

**Publication commits:**
- Findings batch: `28f812a95046cb27979be92704d89de91c665a52`
- WO index cross-reference finalization: `01dd5c5410b452cac898d9f50dbc0ad5716203c5`

**Final readback blobs:**
- `FINDINGS/records/FND-000021.md`: `4118d2dccacad31b9597ce6a7725dad52834cfbc`
- `FINDINGS/reconciliations/REC-000024.md`: `f1abfc23018dd1115bfe39bb57acaf2003e82488`
- `FINDINGS/records/FND-000022.md`: `0cb8fcfc8b0b10453ff5c00a6115c91e571d83d3`
- `FINDINGS/reconciliations/REC-000025.md`: `70082683df57ca64e3b080303abc1146f35aaabf`
- `FINDINGS/INDEX.md`: `a796e9e717d7144bc5d1d116ecb24ed4f830e575`
- `CONTROL/WO70006.md`: `011d6efeab6ec6e6c0983670921e7566e6efca55`
- `CONTROL/active_work_orders.md`: `c210e6497e390e000b4d1d4a9259162ea552496a`

**WO70006 status:** BLOCKED at the required complete raw-output gate. Its partial findings are published; the 293-table census, 115 reported XML omissions, 76 XML objects outside the reported scanner set, the `0x0A412` full-extent test, and all cross-ROM payload-count claims remain unverified pending per-call/per-table outputs. Worker 3 FIFO remains `WO70005` at the head; WO70006 is removed from READY and marked BLOCKED.

**Protected files unchanged:** XML, scope matrices, calibration catalogue, workbook, ROMs, LSTs, A2L files, scanner source and raw evidence outputs.

**Prior integration history:** 2026-11-26 linked-axis / provisional-visibility release (`REC-000021`); 2026-11-26 process-review interval update and protocol publication; 2026-11-25 Worker 3 WO publication. Historical artifact SHAs and detail remain in Git history.

This file is the publication gate. Workers must fetch/read its current state immediately before any shared-main publication. A missing or unreadable status file is fail-closed for publication. The gate does not stop technical investigation or local publication-pending preparation.


**Lock released:** 2026-11-26 — EL19A target-side 22-fingerprint join report published and read back; live work-order register read back unchanged.

**Research publication:** EVIDENCE/EL19A_22_FINGERPRINT_JOIN_2026-11-26.md — commit d3e16e515f404066a4c6dc869559936f00d34173; blob a95c3003f06d64d6e230dbc3a52b6d0329ef8b2e.

No work-order lifecycle, lane ownership/FIFO, Findings, XML, scope matrix, calibration catalogue, workbook, ROM/LST/A2L or tool source was changed in this publication batch.


**Lock released:** 2026-11-26 — WO70012–WO70014 and live FIFO register read back successfully.

**Follow-on work-order allocation:**
- WO70012 — Worker 1; report blob 607495ba95773f09d569be2abede9dded9c355c7.
- WO70013 — Worker 2; report blob bcba3dff669d71f092c648436ae0fb069246e9f7.
- WO70014 — Worker 3; report blob 8fb91bdc409d2161ef07d21b69985da0ac0e85a3.
- Live register commit: 99f4203acf21f0e84809ae7850dea6a19585c974; blob 5ca957a868851ad53119c1975e16bafc193b86d4.

**Verified FIFO:** Worker 1: WO70008 → WO70012. Worker 2: WO70007 → WO70010 → WO70013. Worker 3: WO70014. No existing assignment was changed or reordered. No Findings, XML, scope matrix, catalogue, workbook, ROM/LST/A2L or tool source was modified.


**Lock acquired:** 2026-11-26 — user-authorized transfer of WO70012 and WO70014 into Worker 2; technical execution and consolidated closeout.


**Lock released:** 2026-11-26 — user-authorized WO70014 → WO70012 Worker 2 sequence complete; both reports and active register verified on `main`; integration gate released UNLOCKED. WO70006 is the only remaining explicitly blocked scanner task; no READY lane work remains.


**Lock acquired:** 2026-11-26 — user-requested Nissan CONSULT .dat decoder / raw-diff checkpoint.
**Checkpoint report:** EVIDENCE/WORKBENCH_CONSULT_DAT_CHECKPOINT_2026-11-26.md — blob ad9b901c0279b27921ac5a01c8435b4cb5f5fd62; commit b85ff2d1846448139990bcefcec42efbf9fc5763.
**Lock released:** 2026-11-26 — checkpoint report read back; no work-order lifecycle, worker FIFO, Findings, calibration XML, scope matrix, catalogue, workbook, ROM/LST/A2L, or tool source/test files changed in this checkpoint batch.


**Lock acquired:** 2026-11-26 — user-requested one-shot execution of the existing Nissan CONSULT workbench against the ten newly added donor `.dat` files. Temporary GitHub Actions workflow only; no tool, calibration, ROM, Findings, workbook, scope-matrix or catalogue edits authorized. Do not publish other shared-main work until the run is complete and the temporary workflow has been removed.


**Lock released:** 2026-11-26 — one-shot CONSULT donor scan, decoder comparison and bounded MR16DDT format diagnostics completed. Temporary workflow `.github/workflows/el19a-dat-donor-batch.yml` removed and absence verified. Evidence report: `EVIDENCE/TEN_CONSULT_DAT_DONOR_SCREEN_2026-11-26.md` (blob `46ecf37a12fd2528c1f3499662368d284a0f663f`). Scan/diff run `45906082083` succeeded; final diagnostic run `45906621594` succeeded. No workbench/scanner source, regression tests, XML, catalogue, scope matrix, workbook, Findings, ROM/LST/A2L or worker queues were changed. Donor binaries already present in EVIDENCE were read-only inputs.


**Lock acquired:** 2026-11-26 — user-requested read-only workbench screening of eight newly added `.dat` files in EVIDENCE (EM61B/EM63B/EM65A/EM66A, 310364EM1C/310364EP1B, e1bc11b/e1bc12b). A temporary one-shot GitHub Actions workflow may be added and removed solely to execute existing loader/scanner commands and collect results. No tool source, tests, calibration XML, catalogue, scope matrix, workbook, Findings, ROM/LST/A2L or worker-lane files may be modified.


**Lock released:** 2026-11-26 — eight new EVIDENCE .dat files screened using the existing read-only workbench. Report `EVIDENCE/NEW_DAT_ADDITIONS_SCREEN_2026-11-26.md` (published and read back). Successful run `45907252456`; scan output artifact `el19a-new-dat-screen` SHA-256 `2309a63740ac69fe6c4dcfb79eb4b2a985737979382bb50b64176cffbfb18201`. Four EM revisions decode as SH705519N and have 274/274 helper-backed payloads identical to adjacent existing revisions; 310364 and E1BC pairs remain unsupported by current decoder. Temporary workflow `.github/workflows/el19a-new-dat-screen.yml` removed and absence verified. No tool source/tests, XML, catalogue, scope matrix, workbook, Findings, worker queue, ROM/LST/A2L files changed.


**Integrator:** ChatGPT — user-requested follow-on CONSULT donor comparison (2026-11-26)
**Purpose:** Read-only screening of newly added E1BR/D9 donors and bounded structural comparison against E1BR20E and the unclassified 310364 pair. Temporary one-shot GitHub Actions workflow only; no source, calibration, Findings, workbook, catalogue, scope matrix, ROM/LST/A2L or worker-queue changes.
**Lock acquired:** 2026-11-26 — follow-on donor screening; shared-main publication paused until temporary workflow removal and report readback.

**Lock released:** 2026-11-26 — follow-on CONSULT donor screen completed; temporary workflow `.github/workflows/el19a-followon-donor-screen.yml` removed and absence verified (GitHub contents API returned 404). Successful diagnostic run `45913585933`; artifact `15160523766` (SHA-256 `97e76d6bb6a68d530065d57051ab7f1dee7e0cc74672a9ecfd6bb95fa5d82c3a`). Report `EVIDENCE/FOLLOWON_DAT_DONOR_SCREEN_2026-11-26.md` published and read back (blob `c81d17ae65532bfafd48ed062a308bc7d46c9c11`). D9 0x8019/0x3482 frame variant reconstructed four 512 KiB images with passing frame checksums and contiguous 0x8000–0x70000 coverage, but no SH705x helper/CPU fingerprint; E1BR/E1BT/E1JD and 310364 remain unresolved by current loader. No Findings, XML, catalogue, scope matrix, workbook, ROM/LST/A2L, tool source/tests or worker queue changes.


**Integrator:** ChatGPT — user-requested definition-completion work-order allocation (2026-11-26)
**Purpose:** Publish WO70017–WO70020 and update only their own specifications plus the live FIFO/coordinator register. No technical evidence, Findings, XML, catalogue, scope matrix, workbook, ROM/LST/A2L, scripts or worker outputs are changed in this allocation.
**Lock acquired:** 2026-11-26 — verified prior state UNLOCKED; shared-main publication paused for this allocation batch.

**Lock released:** 2026-11-26 — WO70017–WO70019 and the live register were read back from main; three lane FIFO heads verified; no protected calibration artifacts changed.


**Lock released:** 2026-11-26 — SH705x ROM tool planning batch published and read back. Added `CONTROL/SH705X_ROM_TOOL_PLAN.md`, `CONTROL/WO70020.md`, `CONTROL/WO70021.md`, `CONTROL/WO70022.md`, and registered their FIFO positions in `CONTROL/active_work_orders.md`. Worker 1: WO70020; Worker 2: WO70018 → WO70022; Worker 3: WO70019 → WO70021. No source tools, tests, workflows, calibration XML, workbook, ROM/LST/A2L, catalogues or Findings were changed.


**Integrator:** ChatGPT — user-requested SH705x workbench integration-plan update (2026-11-26)
**Purpose:** Record existing scanner export capabilities, bounded static-index reuse, calibration-definition reconciliation, diagnostic/variant evidence adapters and regression-first integration order. No implementation/source-code, ROM, LST, A2L, XML, workbook, Findings or worker-queue changes are authorized.
**Lock acquired:** 2026-11-26 — verified prior state UNLOCKED; serialize plan/document publication.


**Lock released:** 2026-11-26 — Workbench integration-plan update published and read back. Updated `CONTROL/SH705X_ROM_TOOL_PLAN.md` to v0.2; added `CONTROL/SH705X_WORKBENCH_INTEGRATION_PLAN.md`; clarified `CONTROL/PROJECT_DIRECTION_2026-11-26.md` with the existing scanner-export capability and WO70006 boundary. Verified the new plan records scanner export reuse, static-index adapter constraints, definition-source conflicts, diagnostic/variant provider boundaries and regression-first sequence. Live work-order register and all worker FIFO assignments were unchanged. No source code, tests, workflow, ROM/LST/A2L, XML, workbook, Findings or catalogue artifacts were modified.


**Integrator:** ChatGPT — user-directed SH705x tool-first programme approval (2026-11-26)
**Purpose:** Update the SH705x charter, workbench integration plan and project direction to make the read-only modular ROM toolkit the primary deliverable and EL19A RomRaider definition completion its first generated validation output. Preserve all current worker assignments and queue order.
**Lock acquired:** 2026-11-26 — verified prior state UNLOCKED; user explicitly authorized moving from planning to implementation planning and bounded read-only tool creation after architecture reconciliation.

**Lock released:** 2026-11-26 — three tool-first programme documents read back and verified; live queue remained unchanged; no source code, tests, ROM/LST/A2L, XML, workbook, Findings or calibration inventory was changed in this batch.
