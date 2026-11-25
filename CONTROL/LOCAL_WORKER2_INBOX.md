# Worker 2 — Local Execution Proposal Inbox

**Purpose:** Let Workers 1 and 3 and the coordinator feed bounded tasks and review responses to the full-time local execution lane.

**This file is not an operational queue.** It creates no WO, reserves no ID, assigns no owner, changes no status and does not override `CONTROL/active_work_orders.md`. Only a complete WO registered in the live register is executable.

## Rules for contributors

- Workers 1 and 3 and the coordinator may append proposals here while the integration gate is UNLOCKED.
- Submit a proposal, not an already-assigned WO. Do not allocate a WO number or edit Worker 2's lane status/backlog.
- Prefer one falsifiable question per proposal, with exact EL19A evidence anchors and a cheap discriminator.
- Include dependencies and confirm that they are already available or identify the specific blocker.
- Explicitly state what prior WOs/indexes must be reused and what must not be repeated.
- Do not send broad scans, speculative table hunts, donor-label transfers or tasks requiring unapproved/protected-file modifications.
- Worker 2 alone reviews proposals and promotes accepted work into its own modulo-3 WO and live FIFO.
- When the integration gate is LOCKED, do not write this shared file; preserve the proposed entry locally and publish it after unlock.

## Task proposal template

```text
PROPOSAL ID: <proposer>-<local sequence or date; no WO number>
SUBMITTED BY:
DATE:
PRIORITY:
QUESTION:
WHY IT MATTERS:
TARGET ADDRESSES / FUNCTIONS / RECORDS:
AVAILABLE INPUTS / DEPENDENCIES:
EXISTING EVIDENCE TO REUSE:
NO-REPEAT BOUNDARY:
CHEAP DISCRIMINATOR:
EXPECTED EVIDENCE:
STOP CONDITION:
LOCAL EXECUTION FIT: YES | CONDITIONAL
PROPOSED REVIEW / ESCALATION POINT:
STATE: OPEN
```

## Local worker disposition

Worker 2 updates the proposal state only when it has evaluated the proposal:

- `PROMOTED → WO<ID>`: a complete Worker 2 WO was created and registered in the live FIFO.
- `RETURNED`: one or more required details are missing; state exactly what the proposer must supply.
- `REJECTED`: duplicate, blocked, non-defensible or unsuitable for local execution; state why.
- `DUPLICATE OF WO<ID>`: already covered by an existing investigation.

Do not leave a proposal marked PROMOTED unless both its report path and queue entry have been read back from remote `main`.

## External review responses

A reviewer may append an evidence-backed response to a Worker 2 report's `EXTERNAL REVIEW REQUEST`. Use:

```text
REVIEW RESPONSE FOR WO:
REVIEWER:
QUESTION ADDRESSED:
EVIDENCE / SOURCE ANCHORS:
ANALYSIS:
RECOMMENDATION:
LIMITS / REMAINING UNCERTAINTY:
```

Review responses are advisory evidence contributions. They do not change a WO's lifecycle, authorize edits to another lane's report, or supersede the original evidence. Worker 2 must validate and cite any accepted response.

## Inbox

No proposals or review responses have been submitted at creation. Append future entries below.
