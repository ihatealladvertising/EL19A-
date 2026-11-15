# Evidence and Decisions

## Confirmed project constraints
- ROM identity: `f501.bin`, 1 MiB, MD5 `46991697c502052752a2cabcb84c9e27`.
- CPU: SH7058 / SH705822N, big-endian SH-2.
- FID: `8CMCKRN5`.
- Calibration semantics require target reader and consumer tracing; donor resemblance alone is not confirmation.

## WO64819 CP18 adjudication
- Work order cancelled by user.
- Pointer `off_2490C` at ROM `0x2490C` contains `FF FF 37 1E`, pointer to RAM base `FFFF371E`.
- Shown code around `0x24796–0x24830` accesses offsets `+0x32`, `+0x8A`; write at `0x24830` to `+0x8A`.
- Code at `0x249C0–0x249C8` writes offset `+0x8C`.
- No actual code access to `+0x90` was demonstrated in the evidence shown. `FFFF37AE` remains unresolved.
- Do not resume CP18 unless user explicitly requests it.

## Other output trace notes
- `sub_4E24C` / AB22 output writes `FFFF1054+0x2AE`. If decision bit `FFFF1D99+0x7F` is clear, writes calculated AB22 result; otherwise writes `0x80` fallback.
- The producers of `FFFF2150+0x9FA`, `FFFF2150+0x9F8`, and downstream consumers were open trace targets in the earlier checkpoint.
- Treat these as historical leads pending reconciliation with the latest Controller Notebook.

## Status discipline
No lead in this file should be promoted to verified solely because it appears here. Reconcile with primary LST/workbook/Controller Notebook evidence before use.
