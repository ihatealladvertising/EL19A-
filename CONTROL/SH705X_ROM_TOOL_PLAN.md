# SH705x ROM Tool — Architecture Charter and Development Plan

**Status:** PLANNING BASELINE v0.1 — architecture tasks registered; implementation not yet authorized  
**Date:** 2026-11-26  
**Repository:** `ihatealladvertising/EL19A-` · branch `main`

## 1. Purpose

Develop an extensible ROM engineering toolkit for SH705x firmware, initially using SH7055 and SH7058 families and the existing Nissan EL19A project as the first validation corpus. The design should permit additional processors, ROM families and ECU profiles without embedding ECU-specific assumptions into the core.

The intended user experience is a set of small, independently executable Python command-line scripts backed by one shared library. A unified launcher may be added later, but no command should require that launcher to run.

## 2. User-directed architecture

The confirmed starting direction is:

- Modular, individual Python scripts rather than one monolithic application.
- A shared core for common ROM/address/data handling.
- Reusable support for SH705x ROMs and potential expansion beyond SH705x.
- Existing EL19A tools should be reused and migrated incrementally where practical.

The following are planning defaults to validate during architecture work, not immutable decisions:

- Python 3, standard-library-first; optional third-party adapters only where justified.
- Command-line interface first; graphical interface deferred.
- Versioned JSON for machine-to-machine interchange; CSV/TSV for review and spreadsheet work.
- BIN support first; DAT and PDX only through independently validated format adapters.
- RomRaider XML as the first definition import/export target.
- Read-only ROM analysis as the initial operating mode.

## 3. Proposed component boundaries

| Component | Responsibility |
|---|---|
| `tools/` | Independently executable commands: identify, inspect, compare, scan, trace, parse and export |
| `lib/romtool/` | Shared ROM image, address, byte-reading, hashing, geometry, evidence and serialization logic |
| `formats/` | Container and metadata adapters: BIN, DAT, PDX, A2L and RomRaider XML |
| `processors/` | CPU-family behavior: SH7055, SH7058 and future processor backends |
| `profiles/` | ECU/ROM-family-specific fingerprints, memory layouts and calibration profile data |
| `tests/` | Synthetic fixtures, regression tests, format fixtures and integration tests |
| `CONTROL/` | Architecture decisions, specifications, work orders and project governance |

Exact package names and module boundaries remain subject to WO70020–WO70022.

## 4. Canonical conceptual objects

The shared model must account for at least:

- **ROM artifact/image:** original file identity, byte size, hashes, container identity, reconstructed image identity and source provenance.
- **Processor profile:** CPU family/model, endianness, address width, vector conventions and supported analysis capabilities.
- **Address space / memory region:** distinct file offsets, ROM effective addresses, RAM addresses, mapped ranges and translation rules.
- **Symbol:** name, namespace, type, address references, duplicate declarations and source provenance.
- **Calibration object:** storage address, element type, dimensions, extent, axes, record/layout information and conversion references.
- **Reader / lookup:** function and call-site identity, arguments, query derivation, interpolation/search/clamp mechanics and observed consumers.
- **Evidence / provenance:** source hash, source location, extraction method, observation, confidence, status and links to findings/reconciliation records.

A2L donor metadata, XML declarations, exact payload matches and EL19A target-side reader evidence must remain separate evidence classes. Unknown values and unresolved relationships must be represented explicitly rather than guessed.

## 5. Proposed command families

Initial commands are candidates, not a commitment to create one file per row if the architecture work identifies a better boundary:

1. `rom_identify.py` — identify format, CPU, ROM family, size and known signatures.
2. `rom_info.py` — report hashes, image layout, memory regions and identification confidence.
3. `rom_compare.py` — compare images, identical/changed regions and revisions.
4. `rom_extract.py` — extract and verify recognized container payloads.
5. `rom_scan_tables.py` / `rom_inspect_table.py` — discover and inspect calibration candidates.
6. `rom_find_references.py` / `rom_trace_readers.py` — inspect references, readers, lookups and consumers.
7. `rom_parse_a2l.py` / `rom_parse_xml.py` — import donor metadata and existing definitions.
8. `rom_compare_calibrations.py` — compare objects and evidence across ROMs.
9. `rom_generate_xml.py` / `rom_validate_xml.py` — generate and validate definition output.

## 6. Evidence, safety and compatibility rules

- Source ROMs are read-only by default; analysis outputs are written separately.
- Every machine-generated result records source file hashes, tool/version identity and relevant command parameters.
- Deterministic inputs/options should produce deterministic outputs.
- No ECU-specific calibration semantics in generic processor or format code.
- A donor name, unit, axis or conversion is not target-ROM proof.
- Target storage geometry, reader mechanics, query behavior and consumer paths remain distinct from hypotheses.
- Unknown blocks, unsupported format fields, duplicate declarations and unresolved references are retained and reported, not silently discarded.
- Existing proven tools are migrated incrementally; do not begin with a wholesale rewrite.
- ROM editing, patching, checksum modification and flashing are outside the initial read-only scope. They require separate explicit authorization and their own safety design.
- Definition-file generation is an offline output function and does not authorize ROM modification or flashing.

## 7. Phased roadmap and gates

### Gate 1 — Architecture definition
- WO70020: inventory current tools and migration boundaries.
- WO70021: define canonical shared data model and interchange contracts.
- WO70022: audit runtime compatibility, dependencies, tests and CI.
- Integrator consolidates their results into an implementation-ready architecture. No source-code migration is part of these WOs.

### Gate 2 — Foundation implementation
- ROM loading, hashes, file identity and address/memory mapping.
- Standalone `rom_identify.py`, `rom_info.py` and `rom_compare.py`.
- Synthetic fixtures and regression tests before broader ROM analysis integration.

### Gate 3 — Analysis and metadata
- SH705x backend integration, cross-ROM comparison and reference/caller analysis.
- Calibration geometry, reader mechanics and consumer tracing.
- Relational A2L and XML metadata adapters, with provenance.

### Gate 4 — Definition output
- Calibration comparison, conservative definition generation and validation.
- RomRaider first; additional output adapters only when supported by concrete demand.

### Gate 5 — Expansion
- Further SH705x variants, additional processor families and format adapters.
- Optional project database and graphical interface after the CLI/core stabilizes.
- ROM editing/patching/flashing remains a separate authorization and design gate.

## 8. Architecture work-order register

| WO | Owner | Scope | Dependency / FIFO position |
|---|---|---|---|
| WO70020 | Worker 1 | Existing toolchain inventory and migration map | Worker 1 head |
| WO70021 | Worker 3 | Shared data model and interface specification | After Worker 3's WO70019 |
| WO70022 | Worker 2 | Python/runtime/dependency/test/CI readiness audit | After Worker 2's WO70018 |

These are parallel discovery/specification tasks. They do not require one another to start. The next implementation WOs should be generated only after their results are reconciled.

## 9. Explicit non-authorizations for this planning phase

This charter and WO70020–WO70022 authorize architecture and inventory work only. They do not authorize edits to existing Python tools, calibration XML, the workbook, catalogue, scope matrix, ROM/LST/A2L evidence, findings, or release artifacts. No dependency installation, environment modification, ROM modification, patching or flashing is authorized.
