# Repository Integration Status

**State:** UNLOCKED

**Integrator:** none

**Purpose:** No active integration window. Workers may publish a complete accumulated lane batch to `main` under `CONTROL/WORKER_PROTOCOL.md` and `CONTROL/INTEGRATION_PROCEDURE.md`. The lock serializes publication only; workers continue technical work and may accumulate multiple local publication-pending WOs per lane.

**Last integration:** 2026-11-25 — Worker 2 local-agent adaptation; published protocol/profile/inbox, Worker 2 queue and pilot annotations, and integration-procedure update; all readbacks passed.

**Last release:** 2026-11-25 19:52:02 -03:00 — Worker 2 local-agent adaptation read back from remote `main`; publication may resume.


**Previous lock:** 2026-11-25 19:47 -03:00 — ChatGPT, Worker 2 local-agent adaptation. Released after protocol, profile, inbox, queue, WO and procedure readback.

**Lock acquired:** 2026-11-25 19:47 -03:00. Worker 2 local-agent adaptation. All other technical work may continue; no worker may publish until release.

This file is the publication gate. Workers must fetch/read its current state immediately before any shared-main publication. A missing or unreadable status file is fail-closed for publication: do not publish until the state is confirmed. It does not stop technical work or local pending-package preparation.
