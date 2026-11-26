# Outside Analyst Prompt — EL19A Definition Completion Review (2026-11-26)

You are an independent technical reviewer advising on a static reverse-engineering project. Your task is to assess the fastest evidence-safe path to a useful, conservative RomRaider definition for a 2008 Nissan Versa/Sentra C11X manual-transmission EL19A / MR18DE ECU.

## Repository and target

- Repository: https://github.com/ihatealladvertising/EL19A-
- Authority branch: `main`. Refresh the current branch before analysis; the supplied snapshot was commit `0f5e21718d17655a01c57d2bb24e499ea1232d60` (2026-11-26).
- Target ROM: `EVIDENCE/VERSA f501.bin`, 1 MiB, expected MD5 `46991697c502052752a2cabcb84c9e27`, FID `8CMCKRN5`.
- CPU: SH7058 / SH705822N, SH-2 big-endian.
- Goal: a complete and useful static RomRaider definition, not a claim of validated vehicle behavior. No live-vehicle testing is part of this task.

## Your role

Provide an independent, skeptical but practical review. Do not assume prior ChatGPT conclusions are correct merely because they are written in Findings. Verify key points against the actual current repository artifacts and identify conflicts. Do not edit, commit, create or close GitHub work orders, change the worker queue, or modify XML/CSV/workbook/source files. Return recommendations and proposed bounded work only; the project owner/integrator will decide what to implement.

## First: re-establish the live state

Read, at minimum:
- `CONTROL/active_work_orders.md` (the sole lifecycle/assignment authority);
- `CONTROL/WORKER_PROTOCOL.md` and `CONTROL/INTEGRATION_STATUS.md`;
- `CONTROL/WO70007.md` through `CONTROL/WO70011.md`;
- `CONTROL/WO70006.md`;
- `FINDINGS/INDEX.md`, plus the specific records/reconciliations named below;
- `CALIBRATIONS/EL19A_release1_conservative.xml`, the current Release 1 scope matrix/matrices, `CALIBRATIONS/discovered_tables_catalog.csv`, the current manifest/build notes, and the actual latest full-definition baseline if that is still the selected build input;
- `tools/nissan_sh705x_workbench.md`, `tools/a2l_structural_matcher.md`, and the corresponding Python source.

At the supplied snapshot the live queue contained five READY WOs: Worker 1 `WO70008`; Worker 2 `WO70007 → WO70010`; Worker 3 `WO70009 → WO70011`. This is a snapshot, not a claim about the state when you read it. Refresh the register and never reassign or duplicate work already claimed or active.

## The most important review questions

### A. What is genuinely needed to finish the definition?

Separate the work into:
1. **Release blockers**: known geometry, extent, storage, axis or scaling errors that make the current XML misleading or structurally wrong.
2. **Definition-ready but semantically provisional objects**: safe to include as generic/raw entries based on target reader evidence.
3. **Semantic research**: physical labels, units, fuel/air/torque meaning, true ignition degrees, knock strategy and actuator consequences that can remain open without blocking a conservative definition.
4. **Optional research**: interesting but low-payoff work that should not delay completion.

Be explicit about which questions must be answered before a useful Release 1.1 can ship and which should be deferred to Release 2 or later.

### B. Audit the pending Release 1.1 corrections against source artifacts

Independently inspect `FND-000018` / `REC-000022`, `FND-000019` / `REC-000023`, `FND-000021` / `REC-000024`, and `FND-000022` / `REC-000025`. Compare them to actual XML, scope-matrix, catalogue and manifest rows. Report exact paths, addresses, rows/objects and current-vs-required state.

Focus on:
- `0x0FEE0`: target evidence requires 64 big-endian UWORD entries and a 128-byte extent through `0x0FF5F`; the exact physical/query grid remains unresolved. WO70007 already owns the immediate Release 1 repair. Determine precisely what must be verified at integration, including whether all 64 payload words were actually extracted.
- `0x0ED64` / `0x0EDA0`: two 16×1 UBYTE threshold curves share the coolant-temperature image `U8[FFFF84B8]`; no RPM operand is present. Determine whether the XML/scope metadata still conveys an unsupported RPM axis or donor identity.
- `0x0EE68` / `0x0F01C`: two 16×1 UBYTE curves also use `U8[FFFF84B8]`. F01C's row 029 query/axis metadata needs review. **Important:** REC-000023 explicitly says the owner-directed provisional `Rpm_x25` display is a separate presentation decision, not a firmware fact. Do not recommend silently deleting that owner choice; state exactly what should be corrected as firmware metadata and what needs explicit owner approval.
- `0x0F02C`: separate four-entry UBYTE bin-floor table (38, 48, 54, 62), index 0–3. It is not part of the F01C curve and currently lacks a standalone XML/catalogue/scope object. Recommend a safe raw/provisional representation, or explain why it should wait.
- `0x0DE6E` ↔ `0x0E2ED`: reciprocal pair of two distinct 16-point UBYTE vectors, each used as the other's axis/data. Preserve linked/edit-coupled status if added; caller `0x05AB5A` remains unverified, while `0x05B23A` and `0x05B26A` are the current recorded callers. Evaluate whether this belongs in Release 1.1 or a later release.
- Reconcile whether WO70007 already resolves any `0x0FEE0` work so the next correction batch does not duplicate it.

### C. Unblock or retire the WO70006 census effort

WO70006 is marked BLOCKED because complete raw output is absent. The workbench documentation currently describes:
- `scan --tsv` / `scan --json`: table summaries with aggregated call PCs and axis lists;
- `audit --tsv`: table-level audit rows, not call-level argument provenance;
- `a2l_structural_matcher.py`: console output, no structured export interface.

Verify this against current source rather than relying on this summary. Then answer:
1. What minimum machine-readable call-level schema would actually satisfy the missing evidence gate?
2. Can it be generated by a small, low-risk addition to the existing tools, or is a bounded manual export more efficient?
3. Which reported totals (293 unique bases, 115 XML omissions, 76 XML-only objects, cross-ROM relocation/difference counts) are independently reproducible from repository inputs, and which are still only summary claims?
4. Should WO70006 remain blocked, be replaced with a narrower deliverable, or be explicitly abandoned? Give the evidence-based reason.

The schema should preserve exact call PC/helper, caller/function, data base, element type/width, dimensions, byte extent, axis pointer/role(s), query register/source/width/signedness, pre-call arithmetic, helper clamp/interpolation, result register and immediate consumer when actually traced, plus ROM/tool/A2L input hashes, command line and output hashes. Leave fields unresolved rather than inventing register provenance.

### D. Rank the next candidate investigations

Review the existing WO coverage first; do not duplicate it. In particular:
- `0x0FEE0` dual-donor `mQTBL` candidate (WO70008);
- `0x0D856` and `0x0C2D6` 8×8 UWORD candidates (WO70009);
- `0x0F3EE` 16×1 UBYTE curve / `mTTWISC` lead (WO70010);
- six-call `0x77616` constellation, including the six-address/five-address discrepancy and `0x0ECEE` (WO70011).

Then independently assess the next reported dual-donor lead: `0x0AFF2` (4×4 UBYTE) and `0x0E5E8` (8×1 UBYTE), with candidate symbols `mTDATDDS` / `mTDATDPRE`. Identify exactly what target reader, axis/query and consumer tracing would discriminate it. Do not treat donor symbol consensus as target semantics.

### E. Are we spending effort in the right part of the ECU?

Review FND-000014 / REC-000016 for the `0x0F712` / `0x10F8A` 32×1 UWORD transfer pair and related RAM cells. `FFFF1066` is a computed internal result; physical MAF/airflow identity and capture provenance remain unresolved.

Recommend one bounded forward path from this input-side pair toward load/fuel calculation and one bounded backward path from a concrete injector, ignition-coil or other physical output write toward the calibration inputs. State what evidence can establish an endpoint and where to stop. Prioritize a real physical output path over more broad status-bit tracing unless there is a concrete new sink.

The current findings already show that some exhaustively traced status networks terminate in internal state only (for example FND-000023). Do not reopen them without a direct new contradiction or identified output sink.

### F. Variant comparisons

The workbench documentation reports 37 same-address payload differences between EL19A and EL13A, plus relocated/non-trivial differences versus 8W83B. Audit how reproducible those counts are. Assess the outside-reported candidates `0x0E658`, `0x0ED8C`, `0x0EE48`, `0x10CC2`, `0x12A4E` and `0x12D18` alongside `0x0AFF2` / `0x0E5E8`. Treat differences only as a candidate generator, never proof of a variant-specific function.

## Evidence and efficiency rules

- Give exact repository paths, WO/FND/REC IDs, address ranges, table geometries and source line/PC anchors. Cite file links and line numbers where possible; include commit/blob hashes for files or binaries whose version matters.
- Separate **verified target fact**, **reported lead**, **hypothesis**, **owner-selected presentation**, and **unknown**.
- Use a practical definition-ready threshold: if target storage, geometry, extent, reader mechanics and a non-misleading axis/query representation are established, a generic raw/provisional table can be useful even while physical semantics remain unknown. Do not demand exhaustive consumer tracing merely to list a structurally verified object.
- Do not transfer A2L names, units or conversion formulas to EL19A without target-side support.
- Do not assume a donor A2L is paired with a donor binary unless the repository proves that pairing. The V6 A2L/HEX pairing caveat in WO65212 remains relevant.
- Avoid repeating closed work. Reuse Findings as no-repeat boundaries and correct errors additively.
- Be cost-conscious: prefer a small number of discriminating tasks, combine sibling objects that share one reader or method, and avoid speculative scans, broad RAM sweeps and process overhead.

## Required response format

Return:
1. **Executive verdict** — is the current plan pointed toward a useful definition, and what is the single biggest avoidable delay?
2. **Release 1.1 acceptance checklist** — exact minimum edits/verification, grouped by file/object; mark each mandatory, optional or owner-decision.
3. **Top five next actions**, ranked by payoff and confidence, with dependencies and a short reason. Do not create them in GitHub.
4. **WO70006 disposition** — what output is missing, smallest path to satisfy it, and whether the census remains worth doing.
5. **Fuel/physical-output path** — the best bounded forward and backward traces.
6. **Risks and factual corrections** — any claims in this prompt or current repository that you disconfirm.
7. **Draft work-order specifications** for only the highest-value work not already queued. Each draft must have exact scope, source anchors, acceptance test, stop boundary and authorized outputs.

Do not return a generic list of reverse-engineering techniques. The project needs a prioritized decision that gets the definition closer to complete.
