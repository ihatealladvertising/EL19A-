**Integrator:** ChatGPT — scalar work-order allocation release (2026-11-28)
**Purpose:** WO70045 and WO70046 were published and read back; the auto-generated live index/dashboard now lists both as READY in coordinator FIFO order. No calibration, Findings, XML, ROM, A2L, workbook or tool-source artifact was changed.
**Lock released:** 2026-11-28 — both WO reports and generated register read back from remote main.
**State:** UNLOCKED

**Integrator:** ChatGPT — register two bounded scalar evidence work orders (2026-11-28)
**Purpose:** Publish WO70045 Release 1 scalar-alignment/scope reconciliation and WO70046 donor address-order correlation reproduction. No technical findings or protected calibration artifacts are changed in this allocation batch.
**Lock acquired:** 2026-11-28 — latest main gate read back as UNLOCKED; serialize work-order registration.
**State:** LOCKED

**Integrator:** ChatGPT — final WO70044 integration release (2026-11-28)
**Purpose:** Final report narrative, target outputs, test result and generated register all verified on main. WO70044 CLOSED; auto-register run 46112937250 passed and the updated WO record is read back in Recent Closed; no active claims/scope locks remain. Final production run 46112588137 and closeout regression run 46112824006 passed. No pending file publication remains in this work batch.
**Lock released:** 2026-11-28T05:37:58.360Z — latest main 01de687c8f345262f880aa96714aa1158d22a9a0; closeout state verified.
**State:** UNLOCKED

**Integrator:** ChatGPT — WO70044 closeout narrative correction (2026-11-28)
**Purpose:** Correct one stale sentence in the CLOSED WO70044 report to reflect the successful auto-register run 46112823979 and verified live-index/dashboard readback. No technical evidence or calibration interpretation changes.
**Lock acquired:** 2026-11-28T05:37:08.414Z — latest main f27063c6aa8fcb540d7a83017fa331e45ba93cb1; prior gate state UNLOCKED; no active claims or scope locks.
**State:** LOCKED

**Integrator:** ChatGPT — WO70044 closeout release (2026-11-28)
**Purpose:** Closeout complete. WO70044 is CLOSED; final production run 46112588137 passed and all six output files match the retained artifact's computed Git blob IDs and manifest SHA-256 values; closeout regression run 46112824006 passed 155 tests (2 optional skips); generated live index and dashboard readback list WO70044 under Recent Closed with no active CLAIMED work orders or scope locks. No further shared changes in this work batch remain pending.
**Lock released:** 2026-11-28T05:36:35.074Z — latest main 7772064646a036b7d82ad4c4a95797c548d72180; closeout and generated register verified.
**State:** UNLOCKED

**Integrator:** ChatGPT — WO70044 closeout integration (2026-11-28)
**Purpose:** Publish verified production per-call evidence closeout for EL19A F501 target 0x10F8A. Final production run 46112588137 passed and all six output artifacts were byte-for-byte matched against remote main Git blob IDs. Scanner regression run 46112237955 passed 155 tests with 2 optional skips. Worker 2 WO70041 advisory closed independently while this transaction was prepared; its files are outside this batch and preserved. No other active CLAIMED WOs or scope locks were present immediately before this closeout lock.
**Lock acquired:** 2026-11-28T05:34:26.676Z — latest main 7defc15c2340f13e2a36eaa950ed00fcaf1bef94; prior gate state **State:** UNLOCKED.
**State:** LOCKED

**Integrator:** ChatGPT — WO70044 production output publication release (2026-11-28)
**Purpose:** Release the publication gate for the production Actions rerun of the validated 10F8A per-call workflow. The locked preflight run 46112147883 completed both 0F10E and 10F8A exports and retained artifacts but correctly refused publication under LOCKED. Follow-up regression run 46112237955 passed 155 tests (2 optional skips), including both new 10F8A provenance-resolution tests. WO70044 is the only active CLAIMED task; no other active claims or scope locks were present at release.
**Lock released:** 2026-11-28T05:29:22.566Z — release solely to permit the production workflow to publish its hash-pinned outputs; WO70044 remains CLAIMED until report/output/register readback and closeout. The workflow serializes on `wo-register-main` and refuses publication if main advances.
**State:** UNLOCKED

**Integrator:** ChatGPT — WO70044 production-backed per-call trace for EL19A 0x10F8A (2026-11-28)
**Purpose:** Serialize the target-specific production static-flow exporter/workflow extension and its evidence/report publication. Scope is the 0x10F8A graph call at 0x648D8 / sub_22FAC only; preserve the golden graph and existing 0x0F10E production outputs. No calibration XML, ROM, A2L, workbook, catalogue, or physical-semantic promotion is authorized.
**Lock acquired:** 2026-11-28T05:19:12.386Z — latest main verified; prior gate state UNLOCKED; no active scope locks or CLAIMED work orders.
**State:** LOCKED

**Integrator:** ChatGPT — WO70039 final closeout and work-order registry migration-baseline correction (2026-11-28)
**Purpose:** Publish the verified WO70039 closeout and restore the v4 registry automation without altering the generated register directly. Grandfather the existing unstructured historical backlog through WO70038; all newly changed/added WO files remain strictly validated. The closeout package includes the report, metadata, bounded validator/pin/protocol regression and generated-register readback. No calibration, ROM, worker FIFO, Findings or workbook changes.
**Lock acquired:** 2026-11-28 — latest main `7fd97ed64a149fe3e92e104b20148a503c5f2677` and gate UNLOCKED were verified immediately before acquisition.
**State:** UNLOCKED

**Lock released (2026-11-28):** WO70039 is CLOSED — BOUNDED COMPLETE after post-closeout generated-register readback. Canonical closeout PR #49 merged at `e3552e76a8590d242c0e3d6a9d7ab7a24d227fa0`; final closed-state register trigger PR #51 merged at `bd8fe217fc08094d0acc4b0ca952e665cbab7412`. Main auto-register runs `46106329945`, `46106420391` and `46106515349` succeeded. Closed-state register materialization commit: `4a3418dc3dc1100bad5c172b84a1a0c76790e81b`. Readback: `CONTROL/WO_LIVE_INDEX.md` blob `d40a9d5080003eb1b7f7df08cfa4ca0e5b4bc2f9`; `CONTROL/active_work_orders.md` blob `94d475d7e09bdaa294c466b5aeb80800fcedc99e`. Both show 798 parsed records; WO70039 is absent from Active Claims / scope locks and present in Recent Closed Structured Work Orders. Registry legacy cutoff is 70038. No worker FIFO, calibration, ROM, A2L, workbook or Findings/REC artifact was changed in this closeout.

**Integrator:** ChatGPT — WO70039 full mass-scan index coverage correction (2026-11-28)
**Purpose:** Extend the index to ingest the complete 14,666-row historical scan-results ledger (including 12,176 SCANNED source rows and 2,490 LOAD_REJECTED rows) and the 16,584-row original file inventory, rather than relying only on the 431 detailed-positive subset. Preserve source references and deduplicate decoded images by SHA-256. Synchronize runner, schema, tests, docs and workflow, then release to rerun the full build.
**Lock acquired:** 2026-11-28 — gate verified UNLOCKED at base commit `4d1c4f43d14055e25db051f3225270823d4b7267`; serialization for WO70039 coverage correction.
**State:** LOCKED
**Lock released (2026-11-28):** WO70039 full historical scan/inventory implementation merged at fad9822fc258d9a7957ca7ad678749d827df3319. The latest-state gate guard and full-ledger regression test are in place; scanner/workbench suite passed 43/43 on PR #47. Released specifically for the fresh full-corpus build and manifest readback. The repository-wide WO registry PR validator still reports pre-existing strict-v4 metadata omissions in legacy work orders; WO70039 itself has the required v4 metadata. Worker FIFOs, calibration XML, Findings, ROM images and workbooks remain outside this integration scope.
**Publication-control incident (2026-11-28):** Actions run 46096837710 published index commit 7de6bbfc2bd3ec1558eabbb3ccdf5ce509d95277 while this latest state was LOCKED. The workflow guard used grep across the entire append-only file and matched the older historical UNLOCKED state below this entry. The generated data is retained; this was a gate-check defect, not an index-build failure. WO70039 is correcting the guard to inspect only the first/current State line and is extending the build to the full 14,666-row scan ledger and 16,584-row file inventory. The gate remains LOCKED until the correction is merged and verified, then a fresh build is explicitly released.

039 Nissan master-ROM and structural-family index implementation (2026-11-28)
**Purpose:** The implementation is published and verified; release gate to trigger the fresh 177-entry ROM-folder scan, rebuild the ROM/RomRaider reference index, join the 3,691-code catalogue + 43-row ECU/FID inventory + 431-DAT detailed index + 434-layout base set, publish machine-readable family-index outputs, and read back results. Worker lanes, calibration XML, Findings, ROM binaries and existing workbooks remain unchanged.
**Lock acquired:** 2026-11-28 — gate verified UNLOCKED at base commit `20b0f3642577d62912506d5d1cd8a72b0b5ff8f1`; publication serialized for WO70039.
**Implementation published:** builder commit `1d3907cee56101cb53f77f4d13a86139a5cb46fa`; runner commit `aeb6b8ffa700e35c75c60307d1596216eb9c553b`; eight-test suite commit `b33b8b031a23520d7f960e4fef8fe705e880b109`; workbench command commit `ca5a8f1a00d28ac52ef799548211cbfeba5b6daf`; CI/test/docs commits `58822c43cb1621920da2b2ee5bcff3698e4a3fbc`, `52e8835ac119a4090cb8786d46ee6544ed60bea6`, `4be82d542b1a11de3975da6c399b453e5e5cf8ed`; report/register commits `978ea4d9fd8289eade786245d81678f413ae64e0` and `08ad54885f03bbc6f5b96767d95b5c1b523b12fc`.
**State:** UNLOCKED
**Lock released:** 2026-11-28 — WO70039 implementation synchronized on main; released to allow the dedicated Nissan ROM family-index workflow to run and publish generated data only after it verifies main has not advanced. If another commit arrives during the scan, the workflow retains its artefact but refuses to publish stale index outputs. Full-corpus results remain pending until the generated manifest and index files are read back.



**State:** UNLOCKED

**Integrator:** ChatGPT — user-confirmed V6 A2L/HEX pair and full declaration payload readback (2026-11-27)
**Purpose:** Published and verified the user-confirmed V6 A2L/HEX pairing, complete V6/Juke raw calibration payload extracts, shared-symbol byte comparison, and superseding project-control addenda. No target calibration or tool source was modified.
**Lock acquired:** 2026-11-27 — fresh main gate UNLOCKED; user-confirmed V6 pairing; work limited to donor readback and project reconciliation.
**Lock released:** 2026-11-27 — User-confirmed V6 A2L/HEX pair validated across all 4,614 A2L calibration declarations. Published and read back: V6 full raw payload TSV (4,614 rows; Git blob `b074f7c2b9023938f025d56cec29b4147c6febf8`; commit `018d2ae78b4dc5a9f1e438f1b6b5bc7629d5f246`); Juke full raw payload TSV (7,676 rows; Git blob `ccc441501b37ad112f188d8d0d0c6f75a6fe6c06`; commit `b57c7dc9a7da75cafa339e26200d4eee3c5d2ab8`); V6/Juke shared-symbol comparison (2,628 rows; Git blob `a0ddab3edc7d8adef5b23007e7bcf3fe2f47a443`; commit `0ca96d667a8acaf57b8aa424f33251cfac28f39b`). Corrected WO65212, WO70017, WO70006 and WO65324; register now reflects the superseded pairing caveat. Three-image exact mADVPIAT/EL19A 0x0DE6E axis match recorded. No EL19A calibration XML, target ROM, A2L, workbook, scope matrix, catalogue, Findings or worker FIFO changed. Worker 1 remains WO70031 READY; Worker 2/3 unchanged.

**Lock released:** 2026-11-27 — `EVIDENCE/JUKE_9APCTDEM06_A2L_SCALARS_AND_AXES_2026-11-27.tsv` (6,748 rows; blob `10a484c5dc946e22b81605bb29b94203cfdf7f8a`; commit `1defbfe75bb4273c5192acc83f4f0d53ff4898d2`) and `CONTROL/WO65324.md` (final blob `c3a88d478a791343916f42d3bc9e575a3287a9f5`; final correction commit `d3b52e2a8e1754d0af59c98bdb44f5bcb21c693c`) published and read back. Findings disposition NOT REQUIRED; no protected calibration or worker-lane files edited.

**Lock released:** 2026-11-27 — permanent structural-only RAW/PROVISIONAL threshold update published, read back and adopted by the active definition-completion WO. Created and registered Worker 1 WO70031 against the preserved EL19A 291-address / 377-call exports and 151-ROM donor bundle; no global scan was rerun and no protected calibration/evidence/tool files were changed.

**Published and verified:**
- `CONTROL/WORKER_PROTOCOL.md` — commit `e63f01ea9512957d0114ce3fe49ab94e125bcbec`; blob `14d80a66f0f3eca4c42308023c265ee83c842a6e`.
- `CONTROL/PROJECT_DIRECTION_2026-11-26.md` — commit `32a557c4c458dd1b784c7028a67c9c79bda7806d`; blob `ea5a45285a6041c1707adafb6d747c3f6a4130ce`.
- `CONTROL/WO65324.md` — commit `33b5ef99ca88a5d0606bd7ede09d72ee4989896f`; blob `ccced4061f639b09244fb9021446b417c0d054e4`.
- `CONTROL/WO70031.md` — commit `4895af1c7c02c40b5d555d49537d3b004ff6853a`; blob `dd96540863c16b56951d1d5a1ee08e592a2f8a42`.
- `CONTROL/active_work_orders.md` — commit `d971bd7d50ee26ca756f52b950820a3d0f28ace1`; blob `621c95ff3dca14e35500c78a45cdcabbf9557914`.

**Queue readback:** Worker 1 — WO70031 READY; Worker 2 — WO70018 → WO70022 → WO70028 unchanged; Worker 3 — WO70026 → WO70029 → WO70030 unchanged. Shared-main publication gate returned to UNLOCKED.


**Integrator:** ChatGPT — first-class V6 donor rescan, index merge and EL19A comparison (2026-11-27)
**Purpose:** Reuse and SHA-verify the prior 150-ROM reference-index artifact; rescan only `EVIDENCE/side project/64810223F121200000.hex` and EL19A with the current workbench; export full call/helper/table JSON and TSV plus lossless per-address catalogues and manifests; reconcile the V6 306-table historical baseline; add V6 ROM payload and candidate A2L symbol associations to the reference index with explicit `PROVISIONAL_UNVERIFIED` pairing status; rerun exact-payload and same-geometry-difference comparisons. Temporary Actions workflow only. No tool source/tests, ROM, S19, HEX, A2L, XML definition, workbook, calibration catalogue, scope matrix, Findings or worker queue edits.
**Lock acquired:** 2026-11-27 — latest `main` gate verified UNLOCKED; V6 first-class donor execution and artifact publication.

**Integrator:** ChatGPT — rerun RR ROM workbench batch after user added extracted BIN images (2026-11-27)
**Purpose:** Re-run the existing read-only workbench across the refreshed `EVIDENCE/rr roms` folder, now 177 entries, including the 16 new BIN images corresponding to the previously unsupported RAR/7z archive submissions; rebuild the corpus reference index and record comparison to prior batch. Use a temporary Actions runner and remove it after results are read back. No source/tool/calibration files may be changed except the temporary workflow and additive batch report.
**Lock acquired:** 2026-11-27 — prior state UNLOCKED; live folder inventory refreshed.

**Integrator:** ChatGPT — user-requested read-only workbench batch over EVIDENCE/rr roms (2026-11-27)
**Purpose:** Add a temporary GitHub Actions workflow to run the existing read-only Nissan SH705x workbench against supported ROM files in EVIDENCE/rr roms, inventory all folder entries, index the contained RomRaider XML definitions, capture hashes/logs/artifacts, then remove the temporary workflow and verify cleanup. No ROM, XML definition, A2L, calibration, workbook, catalogue, tool source, or existing test/workflow content is to be modified.
**Lock acquired:** 2026-11-27 — prior state UNLOCKED; folder inventory and workbench CLI read-only preflight complete.

**Integrator:** ChatGPT — user-requested three-donor V6/Juke/Tiida alignment validation WO70030 (2026-11-27)
**Purpose:** Publish one bounded Worker 3 work order and append it to that lane's existing FIFO. No technical evidence, Findings, ROM/LST/A2L, calibration XML, workbook, catalogue, scripts or tool source are changed in this allocation batch.
**Lock acquired:** 2026-11-27 — prior state UNLOCKED; live register and next unused WO ID freshly verified.

**Previous state:** UNLOCKED

**Lock released:** 2026-11-27 — WO70030 report and Worker 3 FIFO registration published and read back from remote main. Worker 3 queue is WO70026 → WO70029 → WO70030. No Findings IDs, ROM/A2L/LST, calibration XML, workbook, catalogue, scripts, tool source or tests changed.
**WO70030 report:** `CONTROL/WO70030.md` — blob `cd53ec8b934b49a22285c264f24b2de47dac30d9`; report commit `7224536791c89bbabefede9f20388a1c89daa58a`.
**Live register:** `CONTROL/active_work_orders.md` — blob `d5586e21c4279bd2e816331b0436090d2a45eaa2`; register commit `321099205384a4961b3b376e74492011ee871518`.

**Released lock:** ChatGPT — 2026-11-27 workbench census preservation and four-WO allocation. Evidence intake and WO70026–WO70029 published and remotely read back; active register updated and read back. No Findings IDs allocated because the intake is explicitly reported/unverified; calibration interpretation is deferred to WO70026. No ROM, XML, workbook, tool-source or existing Findings edits.

**Integrator:** ChatGPT — register WO70024 allocation and closeout-recovery QA (2026-11-26)
**Purpose:** Add one read-only Worker 1 audit task for the locally committed WO70018 deliverables. WO70018 remains open until its report and TSV are safely published and read back. No local Git history reconciliation, WO70018 lifecycle change, calibration or tool-source changes are authorized in this batch.
**Lock acquired:** 2026-11-26 — prior state UNLOCKED; serialize new WO/report and register allocation.

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


**Integrator:** ChatGPT — align worker protocol with user-approved tool-first programme (2026-11-26)
**Purpose:** Replace the obsolete release-first objective with the SH705x toolkit as primary deliverable and EL19A RomRaider as a downstream generated byproduct. Preserve all live work-order assignments and remaining protocol sections.
**Lock acquired:** 2026-11-26 — prior state UNLOCKED; protocol and live register freshly read.

**Lock released:** 2026-11-26 — worker protocol read back; previous release-first objective replaced; queue unchanged; no code, tests or calibration/evidence artifacts changed.


**Integrator:** ChatGPT — assign high-priority scanner integration audit to idle Worker 1 (2026-11-26)
**Purpose:** Register WO70023 for a source-grounded, non-code specification of how existing per-call scanner evidence becomes per-address calibration catalogue records. Preserve Worker 2/3 FIFO and keep WO70021 canonical data-model authority.
**Lock acquired:** 2026-11-26 — fresh gate/register read; Worker 1 current assignment idle; WO70020 closed; WO70023 report path absent.

**Lock released:** 2026-11-26 — WO70023 report and Worker 1 queue/readback verified; Worker 2 and Worker 3 FIFO entries unchanged; no source code, tests or calibration/evidence artifacts modified.


**Lock released:** 2026-11-26 — WO70024 specification and Worker 1 READY assignment read back from remote main. WO70018 remains open in Worker 2 FIFO pending safe publication of its local report and TSV; no Worker 2 lifecycle change was made.

**Lock released:** 2026-11-26 — artifact-first reporting gate published and read back from remote `main`. `CONTROL/WORKER_PROTOCOL.md` blob `024414f88fad9a12b50842ffa75a121c8cef2ea8`; commit `9fc0e1d56e02e0de869f89c4940b2e6a1d3acdf7`. Shared-main publication gate returned to UNLOCKED. No work-order register or lane assignments changed.


**2026-11-27 batch readback:** Evidence intake EVIDENCE/WORKBENCH_CENSUS_2026-11-27.md (blob 9c20a7492626d2b24ed975891b1f74409d8d3c74); WO70026 (67c00714b0555a7840ade60b2ddbdfafbd2123bc); WO70027 (2f3260e37f984c823ea4a02cd7b7237b0b865f50); WO70028 (6ffe723f07beaf219f2fcef47d3f42aefa096a33); WO70029 (a0b7631e0f2e560b889fb48ddfa6488e0983759e); active register (35b93a9a78d09b931b5e2d5edfaabff419708aa7). All six paths read back from remote main. Queue depths: Worker 1 = 1; Worker 2 = 3; Worker 3 = 2. Findings index remains FND-000026 / REC-000027; no semantic promotion pending independent reproduction.


**Integrator:** ChatGPT — RR ROMs read-only workbench batch (2026-11-27)
**Purpose:** Scan the 161 entries in `EVIDENCE/rr roms`, inventory unsupported/duplicate inputs, and build a combined ROM/RomRaider XML reference index using the existing workbench. The temporary workflow was used only for execution and was removed after the run.
**Lock acquired:** 2026-11-27 — prior state UNLOCKED; no ROM, XML definition, A2L, calibration, workbook, catalogue, Findings or tool-source writes authorized.
**Run:** GitHub Actions `46022573374` — SUCCESS; commit `0590f0cf9cb4222474456db111c9fe2665f59a32`; Python 3.11.18. 134 unique ROM containers scanned successfully; 2 exact duplicate containers skipped; 25 unsupported-extension entries recorded; zero scan failures. 130 distinct decoded ROM SHA-256 groups; 126 CPU/FID-identified ROMs; 32,757 call sites / 29,540 resolved; 23,480 aggregate table instances. Reference index: 134 ROM records + 7 XML sources, 505 XML address keys, 3,425 exact payload hash/length keys, 123 code-region hash keys; exit code 0.
**Artifact:** `rr-roms-workbench-batch`, ID `15208363827`, size 24,496,815 bytes, SHA-256 `74eb21c751fdd55463ce4bde70d02e745c07f686c343f1cc2a391280a12e7544`; artifact retention through 2026-12-11.
**Durable report:** `EVIDENCE/RR_ROMS_WORKBENCH_BATCH_2026-11-27.md` — blob `a990e913e869c7cc12d4d1e3b1814412e02d6cf6`; commit `46b714665b28a2683433fc33b2f191c5ff97b564`.
**Temporary workflow cleanup:** `.github/workflows/rr-roms-workbench.yml` removed; absence verified by remote readback (404); deletion commit `b1d8266c3ea91b6f767d1370f96487c6a9ab6246`.
**Lock released:** 2026-11-27 — execution successful, artifact downloaded and hashed, durable report read back, temporary workflow removed. No ROM, S19, BIN, ZIP, XML definition, A2L, calibration, workbook, catalogue, scope matrix, Findings, tool source, test or existing workflow was modified.


**Integrator:** ChatGPT — refreshed RR ROM workbench batch after extracted BIN additions (2026-11-27)
**Run:** GitHub Actions `46023911353` — SUCCESS; commit `61a21947f81732bbaa71b361018a36281aa98c7c`; Python 3.11.18. 150 unique ROM containers scanned successfully from 177 folder entries; 2 exact container duplicates skipped; 25 remaining non-ROM/unsupported entries recorded; zero scan failures. The 16 newly added BINs were all successfully scanned and were unique decoded images against the prior corpus and each other. Totals: 146 decoded ROM hash groups; 142 CPU/FID-identified; 36,944 lookup calls / 33,220 resolved; 26,444 aggregate table instances. Reference index exit 0: 150 ROMs + 7 XML inputs, 505 XML address keys, 3,790 exact payload hash/length keys, 138 code-region hash keys.
**Artifact:** `rr-roms-workbench-refresh`, ID `15210278286`, 27,635,918 bytes, SHA-256 `951da219fb1a9e9aa6f26c4add239421a62ce5ed81af579bfcc3d1a58e015eed`; downloaded and hash-verified; retention through 2026-12-11.
**Durable report:** `EVIDENCE/RR_ROMS_WORKBENCH_REFRESH_2026-11-27.md` — blob `9dccb05bcf2785c5537c0c3da65c0a05468b76d6`; commit `ed4aef50ccf8f380b2e78e99af66fd3399155219`.
**Temporary workflow cleanup:** `.github/workflows/rr-roms-workbench-refresh.yml` deleted; cleanup commit `e254fea42494e37c5e7ded233c27603855224358`. Absence verified after deletion.
**Lock released:** 2026-11-27 — refreshed batch complete, artifact downloaded and hash verified, report read back, temporary workflow removed. ROMs and existing tool/definition/workbook/catalogue/Findings files were not modified.


**Lock released:** 2026-11-27 — V6 is now a first-class donor in the SH705x cross-ROM evidence set. The prior historical 306-candidate result was reproduced with its historical scanner revision; the current strict scanner emitted 302 candidates, all contained in the historical set, with four historical-only candidates retained and labelled. The expanded 151-ROM reference index and full current/historical per-call and per-address exports, reconciliation, EL19A exact-payload/same-geometry comparison and provisional cross-reference are committed under `EVIDENCE/V6_FIRST_CLASS_DONOR_2026-11-27/`. A2L pairing remains `PROVISIONAL_UNVERIFIED` pending independent pairing evidence under WO65212. `tools/nissan_sh705x_workbench.md` and the WO70019 V6 classification correction addendum were published and read back. All temporary V6 Actions workflows were removed and the remote tree was verified clear. No ROM, HEX, S19, A2L, XML calibration definition, workbook, calibration catalogue, scope matrix, Findings or worker queue was modified.
**V6 evidence bundle:** 20 files; merged raw index SHA-256 `3285f01771d4626cf4fcce287919efc4278ba20faa175a812f3fdde53a096a82`.
**Documentation commits:** workbench `74ee6b76b6a06f9af16b970a5ea522e9609264b0`; WO70019 `c4bd1b85293a15afeba3a64b8bfeb4e149f8695d`.


**Integrator:** ChatGPT — WO65324 V6/Juke exact non-constant payload reconciliation and coordinator-register synchronization (2026-11-27)
**Lock acquired:** 2026-11-27 — prior state UNLOCKED. This lock serializes the remaining coordinator-owned WO65324 report/register publication. Two preceding commits for the WO65324 evidence TSV/report were already published while the gate remained UNLOCKED; those commits changed only the new WO65324 evidence and report, not a worker lane, FIFO, Findings, XML, ROM/LST/A2L or tool source. No rollback or history rewrite will be attempted. Remaining register synchronization and gate release will be completed under this lock.

**Lock released:** 2026-11-27 — WO65324 exact V6/Juke/EL19A payload cross-reference published/read back (`EVIDENCE/WO65324_V6_JUKE_EL19A_EXACT_NAMED_NONCONSTANT_MATCHES_2026-11-27.tsv`, 15 rows; blob `6322806fb203fb2491d3115fbf1f653aeb79b4bd`); coordinator report updated/read back (`CONTROL/WO65324.md`, blob `008b08c25663e5961133cc89cf65d82c5c01aab1`; commit `3d6f14562dd822eccaa36dfa3b1a2b1a2be5aaf0`); only the WO65324 coordinator row updated/read back in `CONTROL/active_work_orders.md` (blob `6fd96fec5f6156bec9e074f890eba0e61d65802b`; commit `cd72a8ef0e31f9eb561f94a3c4e02ee4353a122e`). Exact result: 15 strict non-constant target placements across 13 shared donor symbols. No new Findings, XML, tool, ROM/LST/A2L, workbook, catalogue or scope-matrix changes. Worker 1–3 FIFOs and all other WO lifecycle states unchanged. Fresh EL19A scan/preview remains blocked on the pinned executable workspace and required inputs. The earlier evidence/report commits made before this lock were confined to WO65324 and are retained without rewriting history.
