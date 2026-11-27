# Standalone Work Order — ReproProgramming batch workbench run

**WO:** REPROPROGRAMMING-BATCH-2026-11-27  
**Status:** CLOSED — execution and output verification complete  
**Scope:** Run the SH705x workbench against every workbench-supported candidate found under `E:\Nissan Consult\ReproProgramming`; inventory all other files and archives; save reproducible results in this directory.  
**Run date:** 2026-11-27 (local desktop date)  
**Input root:** `E:\Nissan Consult\ReproProgramming`  
**Output root:** `E:\Nissan Consult\ReproProgramming\_SH705xWorkbench_Run_2026-11-27`

## Execution

- Python 3.12.10; `py7zr` 1.1.4 used to read 7z containers.
- Workbench checkout commit: `13acc0b58826c2b693ef495a0b3c61259daec760`.
- Executed `run_workbench_batch.py`; elapsed time reported by the runner: 2,501.4 seconds.
- Exact-payload inputs were scanned once and results mapped back to source files/archive members.
- The batch used the workbench's ROM/container loaders, ROM fingerprinting, helper discovery, call extraction, and table summaries.
- No source inputs were modified.

## Coverage and outcome

- 16,584 source files inventoried: 11,744 direct `.dat`/`.bin` candidates, 1,318 ZIP/PDX packages, 80 7z packages, and 3,442 ancillary or unsupported files.
- 13,698 unique workbench candidate payloads across 14,666 source references were attempted.
- Unique-payload results: **11,216 SCANNED**, **2,482 LOAD_REJECTED**.
- 431 unique scanned inputs produced detailed workbench findings (helper/call/table evidence). Across these, the maxima observed were 37 helpers and 421 unique tables in one input. See `scan_details.jsonl.gz` for the detailed records.
- 1,399 archives/members were inventoried for extraction; 1,395 read successfully and 4 archive reads failed. See `archive_inventory.tsv` for exact sources and errors.
- Rejection examples include unrecognized Consult `.dat` containers, unexpected Consult frame commands, and partial calibration `.dat` payloads that are not full ECU images. Exact per-reference errors are in `scan_results.tsv`.
- The 3,442 ancillary/unsupported files were inventoried but not passed as raw ROMs. This includes formats the workbench does not identify as supported ROM/container inputs; therefore this is exhaustive over discovered supported candidates, not a claim that arbitrary XML/CSV/package metadata was parsed as ROM.

## Artifacts

- `run_workbench_batch.py` — reproducible batch runner.
- `run_manifest.json` — run configuration, aggregate status, output sizes and SHA-256 hashes.
- `file_inventory.tsv` — source file inventory and classification.
- `archive_inventory.tsv` — archive/member enumeration and read outcomes.
- `candidate_tasks.json` — deduplicated candidate payload task/source mapping.
- `scan_results.tsv` — per-source-reference status, fingerprint, helper/call/table summary, and loader errors.
- `scan_details.jsonl.gz` — gzip-compressed detailed findings for the 431 detailed scans.

## Verification and closure

Verified `scan_results.tsv` contains 14,666 data rows plus its header; `file_inventory.tsv` contains 16,584 data rows plus its header; and `archive_inventory.tsv` contains 1,399 data rows plus its header. Decompressed and counted 431 valid JSONL detail records. The unique-payload aggregate matches the run manifest (13,698 = 11,216 + 2,482). Output byte sizes and SHA-256 values are recorded in `run_manifest.json`.

**Disposition:** Work order closed. Results are saved in the output root above. No vehicle validation or operational safety conclusion is implied by this static workbench processing.
