# Operating Protocol v1.1

## State and lifecycle
- Maintain Chat STATE_BLOCK and Controller Notebook as dual hot-state anchors.
- Lifecycle: `RETURNED → LEDGERED → WORKBOOK_SYNCED → READBACK_VERIFIED`.
- Never imply a later stage until the artifact is actually updated and independently read back.
- Keep active/paused work orders, pending integrations, latest checkpoint and save pointers explicit.

## Evidence provenance
Every technical claim promoted to verified must identify source file/version, PC/address/line, instruction bytes, registers/effective address and transfer effect where applicable. Unsupported findings remain in `open_leads`.

## Calibration confirmation
Candidate recognition by screenshot, value fingerprint, dimensions or donor resemblance is valid for hypothesis generation. Confirmation requires target-side reader identification, lookup mechanics (indexing/interpolation/clamping/width/signedness/scaling), and downstream calculation/decision/actuator trace.

## Working style
- Minimum chat and tool overhead.
- Batch significant discoveries/corrections/dependencies approximately every 5–8 hours of project work.
- Use local PowerShell/Python for bulk searches and extraction.
- Preserve existing scripts and tools; do not regenerate or overwrite without approval.
- No Library mutations or project file changes without explicit authorization.

## Repository handling
- Keep this repository private.
- Do not commit secrets, credentials or personal data.
- Assess large files for Git LFS.
- Preserve source artifacts unchanged; annotate copies separately.
