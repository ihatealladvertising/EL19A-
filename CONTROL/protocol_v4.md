# Operating Protocol v4 — Decentralized Work-Order Ownership & Auto-Register

**Effective:** 2026-11-21  
**Supersedes:** Manual shared-register updates in `CONTROL/protocol_v3.md` (historical `protocol_v1.1.md` and `protocol_v3.md` preserved unchanged).

## 1. Core Principles

1. **Per-WO Record Is Source of Truth:** Every active or new work order (`WO65164+` or any v4 record containing a `<!-- WO_META_START -->` block) stores its authoritative ownership, status, lease timestamp, dependency links, and locked target scope inside `CONTROL/WO<ID>.md`.
2. **Never Hand-Edit Shared Registers:** Workers **must not** edit `CONTROL/active_work_orders.md` or `CONTROL/WO_LIVE_INDEX.md`. The GitHub Action (`wo-ownership.yml`) is the sole serialized writer of both on `main`.
3. **Partitioned ID Lanes (Zero Collision Across Tools):** Sessions allocate new IDs strictly inside their assigned lane without needing a central lock server:

| Lane Key | ID Range | Assigned Session Type |
|---|---|---|
| `git-1` | `WO65200`–`WO69999` | Primary Git IDE / coordinator sessions |
| `aistudio` | `WO70000`–`WO79999` | AI Studio / no-`.git` stateless containers |
| `git-2` | `WO80000`–`WO89999` | Secondary Git IDE / external parallel sessions |
| `reserve` | `WO90000`–`WO99999` | Coordinator synthesis / overflow batches |

4. **Concrete Owner Identity (No Ambiguous Strings):** Generic placeholders (`current session`, `this session`, `worker`, `TBD`, `unknown`) are rejected by CI. Use a specific persistent tag identifying the environment and task stream (e.g., `aistudio-rosetta`, `git-kilo-a2l`, `git-codex-cf48d`).

## 2. Structured v4 Metadata Block

Every new work order (`WO65164+` and all `WO70000+` / `WO80000+` / `WO90000+` files) must include a valid JSON block delimited by `<!-- WO_META_START -->` and `<!-- WO_META_END -->` near the top of `CONTROL/WO<ID>.md`:

```markdown
<!-- WO_META_START -->
{
  "wo_id": "WO70001",
  "title": "Short descriptive title",
  "lane": "aistudio",
  "status": "CLAIMED",
  "priority": "P1",
  "owner": "aistudio-el19a-tooling",
  "claimed_at": "2026-11-21T19:45:00Z",
  "lease_hours": 24,
  "target_scope": ["0x0000E904", "FFFF84FE"],
  "depends_on": [],
  "branch": "aistudio/wo70001-short-slug"
}
<!-- WO_META_END -->
```

- **Allowed `status` values:** `RESERVED`, `CLAIMED`, `BLOCKED`, `CLOSED`.
- **Target-Scope Locking:** List every ROM address (`0x0E904`), ROM range (`0x8000-0x80FF`), RAM cell (`FFFF84FE`), or non-hex subsystem key (`tooling:wo_registry`) actively modified or traced. CI normalizes hex tokens (`0xE904` == `0x0E904`) and blocks merging two concurrently `CLAIMED` WOs with overlapping scopes unless linked via `depends_on`.
- **24-Hour Soft Lease:** `CLAIMED` records older than `lease_hours` (default `24`) without an updated timestamp are flagged `STALE` in `CONTROL/WO_LIVE_INDEX.md` and `CONTROL/active_work_orders.md`.

## 3. Session Workflows

- **AI Studio (no-`.git`) sessions:**
  1. Run `python3 tools/wo_registry.py next-id --lane aistudio --remote` (falls back cleanly to local `CONTROL/` if offline) to inspect the next free `WO70xxx` ID and active scope locks.
  2. Create `CONTROL/WO70xxx.md` (via `tools/wo_registry.py init ...`) and write only strictly disjoint deliverable files. Never touch `CONTROL/active_work_orders.md` or another owner's `WO*.md`.
- **Git IDE sessions:**
  1. Pull `main` and check `CONTROL/WO_LIVE_INDEX.md` or run `python3 tools/wo_registry.py next-id --lane git-1` (or `git-2`).
  2. Run `python3 tools/wo_registry.py validate` before pushing a PR.
- **On PR & Merge to `main`:**
  1. PR checks verify schema, lane bounds, non-generic `owner`, scope exclusivity, and zero hand-edits to protected register files.
  2. Push to `main` triggers the serialized rebuild job, regenerating `CONTROL/WO_LIVE_INDEX.md` and updating the auto-generated dashboard block inside `CONTROL/active_work_orders.md`.
