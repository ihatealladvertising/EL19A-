# Repository Integration Status

**State:** UNLOCKED

**Integrator:** none

**Purpose:** No active integration window. Workers may publish to `main` under `CONTROL/WORKER_PROTOCOL.md`.

**Last release:** Initial adoption of the integration-lock protocol.

This file is the publication gate. Workers must fetch/read its current state immediately before committing or pushing. A missing or unreadable status file is fail-closed: do not publish until the state is confirmed.
