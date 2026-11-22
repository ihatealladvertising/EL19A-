# WO65216 — Curve-Family Consumer Reconciliation

**Status:** BOUNDED COMPLETE — CLOSED  
**Completed:** 2026-11-22  
**Scope:** Documentation-only reconciliation of WO65197–WO65203  
**Pinned listing used by source reports:** `EL19A_Complete_Disassembly_ANNOTATED_V3_NEXT6_16_ALL_PENDING_ANNOTATIONS(1).lst`, SHA-256 `148385bbec91f6a491dcaa403962836f709c2f273df9a17ec51f1dea5f7f4549`

## Executive finding

The family-level statement in the Index Reconciliation sections of WO65197 and WO65198 that all adjacent curve-consumer WOs found no first consumer is **incorrect as a family-wide summary**. It accurately describes several individual curves, but not all.

Across WO65197–WO65203:
- **Two curves have documented downstream consumer paths:** `0x0EB30` (WO65202) and `0x0E700` (WO65203).
- **The remaining traced outputs have bounded no-consumer/dead-store findings:** `0x10954`, `0x1501C`, `0x0E924`, `0x0E954`, `0x0E9BC`, `0x0E9EC`, and `0x0E708`.
- The adjacent ROM placement of `0x0E700` and `0x0E708` does **not** make them a paired mechanism.
- No physical calibration identity or engineering units are established by this reconciliation. A consumer is evidence of runtime use, not proof of what the calibration means.

## Consolidated result matrix

| Source WO | ROM table(s) | Reader / shape | Query and staging summary | Downstream status |
|---|---|---|---|---|
| WO65197 | `0x10954` | `sub_22F80`, 16-point UWORD BE | Query `FFF13D8`; curve output staged at `FFF27DA`, transformed through square / `sub_22434` / subtract / clamp; final result `FFF3470` | **No consumer.** Full-listing check found no external reader of final `FFF3470`; earlier cells are intermediate staging only. |
| WO65198 | `0x1501C` | `sub_22E60`, UWORD curve | Output `FFF269E`; later chain adds read-only `FFF2442`, clamps and stores `FFF279A` | **No consumer.** `FFF269E` is only read within the chain; `FFF279A` has no external reader. The suspected `0x38A8A` access resolves to `FFF169E`, not `FFF279A`. |
| WO65199 | `0x0E924`, `0x0E954` | `sub_22E10`, two 16-point UBYTE curves | Same query `FFF8521`, shared output `FFF2717`; mutually exclusive selection | **No consumer.** Shared query/output and selector establish a structural pairing, but `FFF2717` has no external reader. |
| WO65200 | `0x0E9BC` | `sub_22DF8`, 8-point UBYTE; three reader paths | Query `FFF84BF`; outputs `FFF18CE` and shifted `FFF1854` | **No consumer.** Neither output has external readers. |
| WO65201 | `0x0E9EC` | `sub_22DF8`, 8-point UBYTE | Query from low byte of the `FFF84D4`-adjacent word; curve output `FFF2741`; axis-pointer byte staged at `FFF2740` | **No consumer.** Both staging cells have zero external references. |
| WO65202 | `0x0EB30` | `sub_22E10`, 16-point UBYTE | Query `clamp(FFF85B2 - 96, 0, 255)`; output updates UWORD accumulator `FFF1382` by curve result minus 128, clamped to 0..65535 | **Consumer found.** `FFF1382` is compared unsigned against ROM word `[0x9318]` at `0x48160`; the comparison affects the branch at `0x48162`. |
| WO65203 | `0x0E700`, `0x0E708` | Both `sub_22DF8`, 8-point UBYTE | `0x0E700`: computed query `FFF11B8`, output `FFF11B9`. `0x0E708`: query `FFF11BC` (never written), output `FFF11BD`. | **Different outcomes.** `0x0E700` result is loaded into `r6` and fed into `sub_21AC0`; `0x0E708` output is never read (dead store). |

## Important distinctions

### 1. Consumer does not mean semantic identity

For `0x0EB30`, the trace establishes a real path from a 16-point UBYTE lookup into an accumulator and then an unsigned threshold comparison against ROM constant `0x9318`. It does not establish the physical quantity represented by the curve, the units of the query, or the calibration label.

For `0x0E700`, the result reaches `sub_21AC0` after the caller's multiply/accumulate operations. This is stronger than a dead-store candidate, but the downstream routine's full semantic role is not established by WO65203.

### 2. Pairing claims must remain local to the evidence

- `0x0E924` / `0x0E954`: structurally paired in the reported reader: shared query and output, mutually exclusive selection. Their shared result remains unconsumed.
- `0x0E700` / `0x0E708`: **not** one paired mechanism. Separate query cells, separate output cells, different dataflow; one result is consumed and the other is discarded.
- ROM adjacency alone is not evidence of a shared calibration function.

### 3. Negative findings are bounded

“No consumer” here means the source report's full-listing reference check found no external reader of the specified staging/output cell, within the pinned listing and described dataflow. It does not prove the ROM table is unused in every possible indirect, dynamic, or unexamined context. In particular, WO65198 explicitly resolves a tempting apparent hit as a different RAM address.

## Required correction to historical summaries

The following statements remain valid only as per-table findings, not as family-wide conclusions:

- **WO65197 — Index Reconciliation:** the sentence saying WO65200/WO65201/WO65202/WO65203/WO65199/WO65198 “all found no first consumer” is superseded. WO65202 and WO65203 each report a positive consumer path for `0x0EB30` and `0x0E700`, respectively.
- **WO65198 — Index Reconciliation:** the sentence saying WO65200/WO65201/WO65202/WO65203/WO65199 “all found no first consumer” is superseded for the same reason.
- **WO65199 — Index Reconciliation:** its statement about WO65200/WO65201/WO65202/WO65203 is also too broad: WO65202 and WO65203 are positive-consumer exceptions. Its own no-consumer result for `0x0E924` / `0x0E954` remains valid.

This report is the additive correction; the historical source reports are not edited.

## Follow-up value and stop boundary

No repeated ROM/LST trace was needed to reconcile the seven reports. The highest-value semantic follow-ups, if later prioritized, are narrowly:
1. trace the `0x0E700` result through `sub_21AC0` to the first externally meaningful effect; and
2. trace the branch/effect following the `0x0EB30` accumulator comparison at `0x48160`.

These are distinct paths and should not be merged into a claim that the whole family has one common function. Do not repeat the helper census, query construction, or staging-cell scans already completed by WO65202/WO65203. Do not assign names or units without further consumer evidence.

**No protected artifacts were changed.** This reconciliation modifies only this evidence report and the operational register lifecycle entry.
