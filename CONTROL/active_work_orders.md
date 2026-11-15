## Current chat continuation
- **WO64828 — E974 Input Provenance and ADC/Threshold Endpoint Trace** (Agent: ChatGPT): **ACTIVE**. Issued 2026-11-15; targeted follow-through from WO64827.
- **WO64827 — E974 Downstream Gating and Consumer XREF Investigation** (Agent: Grok): **TECHNICAL SCOPE COMPLETE**. Authoritative Control Notebook lifecycle synchronization remains pending because exact Notebook read-back is unavailable (403).
- Prior WO64825 remains PARTIAL. WO64827's bounded scope is complete; WO64825's separate unresolved items are not silently closed.

## WO64828 issue / checkpoint 2 (2026-11-15)
- **Status:** ACTIVE. Full scope and evidence: `CONTROL/WO64828.md`.
- **Primary source updated:** newer read-only listing `EL19A_Complete_Disassembly_ANNOTATED_V3_NEXT6_WO64683_64684_CHECKPOINT_2026-11-11.lst` (27,050,057 bytes; modified 2026-11-12); older stage-16 listing superseded for this trace. Existing `EL19A_IDA_Export.zip` used only as supplementary xref index.
- **E974 dependency:** `0x3C37C) reads `FFFF8626), tests bit 0x04 and, with `FFFF1D7C.bit4`, forces `FFFF1C93=0x80) at `0x3C454); else computes an alternative `FFFF1C93) value. Together with WO64827's `FFFF1F0C → FFFF8626.bit2`, confirmed E974 control dependency into callback input.
- **Callback/helper:** `prepare_85DF_and_19BF` at `0x59B58` reads UWORD `FFFF1CAE)/`FFFF1CCC), selects max, caps its high byte at 0x7F; combines UBYTE `FFFF1C93)/`FFFF1CD6) as bounded `1C93+1CD6-0x80), calls `calculate_and_update_1C01), and stores returned byte to `FFFF19BF) at `0x59BB6). Helper reads prior `FFFF19BF) at `0x59A46`, performs ROM lookup/fixed-point operations, and updates `FFFF1990+0x41 = FFFF19D1) at `0x59B1A/0x59B32). Initialization writes `0x80) to `FFFF19BF) at `0x28C94`.
- **Conditional outputs:** helper state `FFFF19D1) plus selected UWORD forms candidate `FFFF85DF). If `FFFF3616 & 0x0C` nonzero, output forced to zero; otherwise `FFFF1E68.bit2` selects between `r5) and capped max-byte `r13`. Wrapper condition correction: if `FFFF1E68.bit2` is SET, it copies `FFFF85DF) to `FFFF85E0); if CLEAR, it calculates `FFFF85E0) from `FFFF1CCC). This creates a conditional E974→1C93→helper→85DF→85E0 internal path when applicable.
- **Writer audit:** latest LST has 40 literal code loads of `FFFF1CA8`; static register/GBR constant-offset/index writes found none to `FFFF1CAE) (+0x06), `FFFF1CCC) (+0x24), or `FFFF1CD6) (+0x2E). Only other static indexed word stores through that base are `0x299F8`→`FFFF1CDC) (+0x34) and `0x5F53C`→`FFFF1CCA) (+0x22). No static-offset write to `FFFF1C78+0x36/+0x54/+0x5E) found. This does not exclude indirect aliases, block copies, DMA/peripheral writers, or code not represented as direct constant-offset stores.
- **Current endpoint:** explicit latest-LST chain is `19BF) init/update/feedback; `19D1) helper-state update; `85DF) written at `0x59BF2/0x59C02/0x59C04` and read at `0x59CA2`; `85E0) written at `0x59CA6`. No further explicit `85E0) consumer identified. ADC channel 9 and `FFFF8494/FFFF2F00) endpoint claims are not yet linked by exact dataflow to this callback.
- **Not resolved:** actual writers for `FFFF1CAE), `FFFF1CCC), `FFFF1CD6`; additional indirect/bulk/peripheral writers; physical/ADC endpoint. No semantic/XML promotion.
- **Integration:** `CONTROL/WO64828.md` checkpoint 2 committed. Master Workbook and Stable Control Notebook unchanged; exact Notebook read-back remains unavailable (403).
- **Next:** only targeted indirect-pointer / bulk-copy / peripheral-update producer checks and any direct `FFFF85E0) downstream consumer lead; stop rather than repeat constant-offset audit or broad-scan.

## WO64827 closeout (2026-11-15)
- **WO ID / Title:** WO64827 — E974 Downstream Gating and Consumer XREF Investigation
- **Agent:** Grok
- **Technical status:** COMPLETE (bounded investigation / stop condition met)
- **Depends on:** WO64825 (PARTIAL; preserved)
- **Investigation date:** 2026-11-15

### Confirmed findings
- **Timer-derived operand producer:** `sub_257AC → FFFF85E4 → sub_34476 → FFFF8596 → sub_344A4 → FFFF85D6`.
  - `sub_257AC` supplies the timer-derived `FFFF85E4) value; downstream conversion uses `48,000,000 / FFFF85E4`.
  - Saturation/fallback behavior observed: saturates at `0xFFFF`; fallback `0x044E`.
  - `sub_34476` forms `FFFF8596`; `sub_344A4` stores the shifted/scaled result to `FFFF85D6`.
  - The query path uses `FFFF8596 >> 7`, capped at 255.
  - Physical units and semantic name remain unresolved; do not assign a semantic XML name.
- **E974 output `FFFF1F0C):** drives `FFFF8626.bit2`; this affects `FFFF1C93` and downstream `FFFF19BF` / `FFFF85E0), optional ADC channel 9 aggregation, and `FFFF8494) threshold state (including the `FFFF2F00` path).
  - Furthest confirmed endpoint is internal status/threshold and ADC aggregation. No terminal physical sensor or actuator was established.
- **E974 output `FFFF1F0D):** gates a hysteretic update of `FFFF1E54.byte0 bit 0x20`. No separate direct consumer beyond the traced status behavior was established.
- **`sub_223FE` correction:** pure signed arithmetic helper, effectively `R0 >>= 6`; no RAM access, no side effects, no branches, and it does not read `FFFF1F0C` or `FFFF1F0D`. The word at `FFFF8594+2` is the scaled operand; E974 outputs are boolean enable gates, not numeric inputs.
- **0x55xxx correction:** earlier same-GBR interpretation was overbroad. Sites `0x5599A`, `0x55A24`, and `0x55C82` resolve to `FFFF8AF0/FFFF8AF1), not the E974 bytes at `FFFF1F0C/FFFF1F0D`. Do not count them as additional direct E974 consumers.
- **Decision:** keep physical semantics and XML promotion unresolved. No calibration/XML promotion is justified by this trace.

### Stop condition / unresolved boundaries
- Producer and conversion chain for the timer-derived operand are traced to the furthest supported point; physical units/name remain unknown.
- E974 downstream effects are traced to internal status, threshold, and ADC aggregation; terminal physical sensor/actuator remains unproven.
- The separate `0x55xxx` sites are not direct E974 consumers.
- These unresolved semantic/physical endpoints are explicit boundaries, not unfinished searches within WO64827's bounded scope. Further work requires a new concrete lead or separately authorized scope.

### Integration and lifecycle
- GitHub migration register updated from the previous PARTIAL snapshot using the completed investigation report.
- Master Workbook: **not edited**.
- Stable Control Notebook: **not edited / not read-back verified**; exact item `F6DEFBD470240AE6!sac2dd9024e574ee3a7462a1730baeddd` previously returned 403 `serviceReadOnly`.
- Therefore this GitHub record reports technical completion only; it does not claim authoritative Notebook lifecycle closure or reciprocal save verification.
- **Completed work not to repeat:** timer producer chain; E974 `FFFF1F0C` / `FFFF1F0D` downstream status paths; `sub_223FE` operand-vs-enable distinction; correction of the three `0x55xxx` addresses.
- **Next action:** when exact Control Notebook access is restored, reconcile this closeout and update the Notebook's WO lifecycle state. Do not repeat bounded traces absent a new lead.

## WO64825 register entry (2026-11-15, preserved)
- **WO ID / Title:** WO64825 — E974 Output-Chain Investigation
- **Agent:** Grok
- **Status:** PARTIAL
- **Findings (instruction-level from annotated LST):**
  - Callsite 1 (`0x3BB1A` / `sub_3BA88`): GBR=`FFFF1E54`; query = `(FFFF85C4+0x12)>>1` clamped; result → `GBR+0xB8` (`FFFF1F0C`); read-back `0x3BBE4`; non-zero gates `sub_223FE` path. Confirmed.
  - Callsite 2 (`0x3C042` / `sub_3BFC8`): identical GBR and query construction; result → `GBR+0xB9` (`FFFF1F0D`); read-back `0x3C104`; likewise gates `sub_223FE`. Confirmed. Paired with callsite 1.
  - Callsite 3 (`0x4130E` / `sub_412B8`): distinct GBR=`FFFF1D80`; query from `FFFF859C+0x12`; output `FFFF1F0E`; local read-back and bit tests only; no shared `sub_223FE` path observed. Confirmed distinct.
- **Evidence addresses:** `0xE974`, `0x3BB1A`, `0x3BB32`, `0x3BBE4`, `0x3BC0E`, `0x3C042`, `0x3C052`, `0x3C104`, `0x3C118`, `0x4130E`, `0x41318`, `0x41330`.
- **Integration note:** Investigation PARTIAL; predecessor to WO64827.

## Durable / historical snapshots
- **V53 checkpoint:** WO64817 PARTIAL/PAUSED at CP16; WO64819 ACTIVE (PAIR-01); WO64820/WO64821 QUEUED; WO64816/WO64818 PARTIAL/PAUSED; WO64795 proposed/not issued.
- **Later Library Notebook snapshot (2026-11-15 17:55):** WO64822 ACTIVE for broad calibration harvesting; WO64819 PAUSED after CP18; WO64820/WO64821 queued/deferred; WO64817/WO64816/WO64818 paused. V53 remains the master pointer.
- The later Library snapshot's WO64822 CP02 notes:
  - E974: three `sub_22E10` callsites at PCs `0x3BB1A`, `0x3C042`, `0x4130E`; query `min(FFFF85D6 >> 1, 255)`; outputs GBR+0xB8/+0xB9 and `FFFF1F0E`.
  - EE08/EE28: cascade/selector path in `sub_3BEA6` / `sub_3F3C6`, selector bit `0x40`, output `FFFF1054+0x3CC`.
  - F33E–F36E: shared `FFFF84B8` query; source unresolved. Do not repeat source-path scans already completed under WO64819.
- **WO64819 CP18:** user cancelled the bounded CP18 investigation. `FFFF37AE` (+0x90 from `FFFF371E`) remained unresolved; later Library snapshot records the WO paused at CP18. Do not reopen without explicit request and a concrete new lead.

## Control-source limitation
Stable Control Notebook item: `F6DEFBD470240AE6!sac2dd9024e574ee3a7462a1730baeddd`. Exact OneDrive fetch returned 403 `serviceReadOnly` during migration. Treat V53, Library Notebook copies and chat context as separately sourced snapshots; do not silently merge them.

## Next reconciliation requirement
When the exact stable Notebook becomes readable, compare its `CONTROL`, standing instructions, work-order ledger, latest continuation and V53 pointer against this file. Update the Notebook from verified state and verify read-back. No further WO allocation is implied by this closeout.
