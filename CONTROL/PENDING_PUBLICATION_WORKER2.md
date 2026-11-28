# Worker 2 Pending Publication Package

**Updated:** 2026-11-28
**Gate observed at publication:** `UNLOCKED` (first `**State:**` line of `CONTROL/INTEGRATION_STATUS.md` at `origin/main` = `6e6957b`)
**Lane state:** Worker 2 FIFO depth 0 — no READY or ACTIVE work order remains.

## Published (no further action)

### WO70028 — Consult %6 decoder and controlled-variant regression fixtures
**Status:** CLOSED — BOUNDED COMPLETE (2026-11-27)
**Findings disposition:** NOT REQUIRED
**Published at:** commit `7636783` (fast-forward on `main` after `d64d2e6`); remote readback verified.
**Remote blobs:** report `51214758de1f5d02cac81d668a4696e7ac5f7a86`; `EVIDENCE/WO70028_fixtures.json` `514f0b2724eec4166bd30b67f6e10f0101db89f0`; `EVIDENCE/WO70028_e1br20e_vs_e1br50e_diff.json` `86570a8228e35d130e3fa3824e96d7868cbd8fe0`; `EVIDENCE/WO70028_e1br20e_vs_e1bt40a_diff.json` `87536600ca1c7a6d0fecb77238518898a846f7ed`; `EVIDENCE/WO70028_e1jd81d_overlaps.json` `aca16f01ed8782f3861f07abc3fd26dc57f80fc1`; `EVIDENCE/WO70028_synthetic_tests.json` `b74dcdf2c2aacb01ed17960b880c42320833f68a`.

### WO70022 — Python/runtime/dependency/test/CI readiness audit
**Status:** CLOSED — BOUNDED COMPLETE (2026-11-27)
**Published at:** commit `5a0d759`; **Findings disposition:** NOT REQUIRED

### WO70018 — RomRaider screenshot OCR validation
**Status:** CLOSED — BOUNDED COMPLETE (2026-11-27)
**Published at:** commit `132d964`; **Findings disposition:** NOT REQUIRED

## Published 2026-11-28 (previously PREPARED under the 2026-11-28 LOCKED gate)

### P-2.1 — WO70028 lane-row lifecycle correction in `CONTROL/active_work_orders.md`
**Package state:** PUBLISHED in the 2026-11-28 Worker 2 publication batch (parent commit `6e6957b`)
**Disposition:** NOT REQUIRED (lifecycle text only; no FND/REC)
**Problem:** the WO report and all five evidence artifacts are published at `7636783`, but the Worker 2 lane row still advertises the task as READY, so the register does not reflect that the WO is remotely closed. The ordered READY backlog table already states `Worker 2 | — | 0`, so the lane row is the only contradictory text.
**Exact edit** — in the `| Worker 2 | — | ...` row, replace:

```text
WO70028 READY — Consult %6 decoder and controlled-variant regression fixtures; FIFO after WO70022;
```

with:

```text
WO70028 CLOSED — BOUNDED COMPLETE (2026-11-27; NOT REQUIRED — four Consult %6 inputs re-decoded and validated (512 KiB, SH705520N, LOADER40, ck_std OK) with container/decoded SHA-256; E1BR20E/E1BR50E 263 identical tables and 2 differing at 0x0A58E/0x0A67E (2D_IMPL 8x1 U16) plus 46 non-table bytes in 19 clusters; E1BR20E/E1BT40A 230 identical / 35 differing / 3,232 diff bytes; E1JD81D 143/61/50 exact-payload overlaps with E1BR20E/EE310/EL19A; 8 synthetic %6 edge-case tests specified; no ROM/checksum repair, XML, workbook, catalogue, A2L, source or workflow edit; published commit `7636783`);
```

**Other required changes:** none. No FND/REC, no index row, no inventory pointer (routine fixture reproduction).
**Base to apply against at publication:** current `CONTROL/active_work_orders.md` on `origin/main` (`838d118`); re-read the lane row and its blob immediately before the write, since the register is under active coordinator modification.
**Local worktree note:** the checked-out register here is 55 commits behind `origin/main`, so the edit was deliberately not written into the stale worktree file; only these verbatim strings are prepared.

## Local changes recorded in this ledger
- `CONTROL/WO70028.md` — status line now carries the publishing commit and report blob; added the canonical `FINDINGS DISPOSITION:` block required by `CONTROL/WORKER_PROTOCOL.md` (the published version carried the disposition only as prose) and a `Publication identity` section recording the blobs and the outstanding lane-row residue.
- `CONTROL/PENDING_PUBLICATION_WORKER2.md` — this ledger.

## Notes
- No ROM/checksum repair, XML, workbook, catalogue, A2L, source-script, workflow, Findings or other lane's report/lifecycle edit was made.
- Synthetic %6 tests remain delivered as specification only; the repository test path was not authorized by WO70028.
