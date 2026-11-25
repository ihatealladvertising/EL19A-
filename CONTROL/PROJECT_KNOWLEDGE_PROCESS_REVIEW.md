# Project Knowledge and Process Review

**Purpose:** keep the repository independently usable as the project's memory. Conversation history and saved memory are supplementary navigation aids, never required technical authority.

## Recurrence

Run a short review at the first of:
- every 10 additional WO closeouts across all lanes; or
- 7 calendar days after the previous review.

The first worker/session to notice the threshold performs the review from current `main`. Check this log before starting; if another session has already recorded the due interval, do not duplicate it. A review is a bounded repository-maintenance task, not a new technical WO and not permission to change another lane's lifecycle. Re-read the latest file SHA before appending and verify readback.

## Five-point review

1. **Knowledge coverage:** list material conclusions still found only in WO reports or chat; identify the smallest migration needed into `FINDINGS/INDEX.md`, a durable method note, or another authoritative repository file. Chat-only claims are migration candidates, not facts.
2. **Contradictions:** identify superseded/current conflicts in labels, axes, query domains, dimensions, scaling, units or semantics. Link both sources and record additive reconciliation; do not silently rewrite history.
3. **Investigation efficiency:** name productive WO families and their reusable outputs; flag repeated negative boundaries, duplicate scope or low-information work. Add precise no-repeat guidance or retire/re-scope only through the normal lane lifecycle.
4. **Method improvement:** capture reusable reader patterns, comparison/alignment techniques, evidence rules and validation methods in a durable index/protocol with provenance and limits.
5. **Context integrity:** test whether a fresh investigator can reconstruct current assignments, findings, baseline, dependencies and blockers from repository files alone. Record missing links, stale snapshots and the exact recovery-path correction.

## Required entry format

Append one compact entry per review:

- **Date / reviewer / trigger:** date, session or lane, and WO-count or 7-day trigger.
- **Coverage:** highest-value WO-only/chat-only knowledge and migration disposition.
- **Contradictions:** unresolved or reconciled conflicts; affected finding/reconciliation IDs.
- **Efficiency:** productive/repetitive families and concrete no-repeat or reprioritization action.
- **Methods:** reusable methods promoted or missing documentation.
- **Fresh-session test:** PASS / PARTIAL / FAIL, with missing repository artifact(s) and exact repair.
- **Actions:** files changed, or explicit “none”; commit and readback SHA.

## Acceptance test

**Could another competent investigator, with no access to conversation history, resume the project without repeating major investigations or inheriting incorrect assumptions?**

A PASS requires that the live register, operating protocol, findings/reconciliation index, context-recovery guide, current calibration baseline/build state and linked source reports provide a coherent route to the current project state. Otherwise mark PARTIAL or FAIL and name the blockers. Do not claim PASS merely because files exist; verify that the links and current claims agree.

---

## Review log

## Review entry — 2026-11-25

- **Date / reviewer / trigger:** 2026-11-25 / ChatGPT integrator / first review after the findings-preservation control was adopted; more than ten additional WO closeouts were visible across the lanes.
- **Coverage:** Recent WO-only material includes the MAF scaling FOUND result (0x0F712 axis / 0x10F8A curve), the 0x848A/0x848B object-type distinction, the 0x8550 mDSHCUT premise conflict, and the corrected GBR-derived addresses in WO65865/WO65883/WO65886. WO66032 is queued to perform the bounded backfill; no FND/REC promotion is claimed by this review.
- **Contradictions:** WO65865's no-reader/no-writer result for FFFF1DB4 conflicts with WO65817's proposed mDSHCUT bit gate; WO65847's RAM-vs-ROM result for 0x848A/0x848B limits the earlier paired D/N interpretation in FND-000004/REC-000004; WO65883 corrects the staging/source addresses previously called FFFF109E and FFFF1054+0x2EC. These require source-linked reconciliation, not edits to historical WO reports.
- **Efficiency:** The highest-value method correction is per-function GBR resolution across function boundaries; fixed line windows and reuse of a nearby routine's GBR base are unsafe. Routine flag-consumer follow-ons should not be multiplied once a bounded internal-state/no-output result is established.
- **Methods:** Added a mandatory WO findings-disposition gate, a standing narrow authorization for FND/REC/index and safe existing inventory-pointer updates, collision-safe ID/index publication instructions, and a DEFERRED rule requiring a queued reconciliation WO.
- **Fresh-session test:** PARTIAL. The live register, worker protocol, Findings README/index and relevant recent WO reports were checked. The context-recovery guide and current baseline/build-manifest state were not re-audited in this maintenance pass; WO66032 remains pending for the historical findings backfill.
- **Actions:** Updated `CONTROL/WORKER_PROTOCOL.md`, `FINDINGS/README.md`, created `CONTROL/WO66032.md`, and assigned WO66032 to Worker 2 in `CONTROL/active_work_orders.md`. Commits: `2e39c794`, `346538a1`, `e9725cc1`, `a8b68d6d`, `e84e1522`, `c2ad9f5e`. Readback verification pending final integration check.

