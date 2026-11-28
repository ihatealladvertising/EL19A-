# SH705x Reader Trace Graph — additive contract v0.1

**Schema ID:** `sh705x-reader-trace-graph-v0.1`  
**Base interchange:** `sh705x-datamodel-v1.0.0`  
**State:** Provisional graph extension. It does not imply that an SH-2 instruction tracer is implemented.

## Compatibility boundary

`CONTROL/SH705X_DATA_MODEL_SPEC.md` remains canonical for ROM artifacts, processor profiles, address spaces, symbols, calibration objects, axes/conversions, calls, evidence and analysis runs. The reader graph is a per-call extension which references those identities. It must not create a competing ROM/object model or duplicate the existing SH-2 decoder.

## Required graph members

| Member | Purpose |
|---|---|
| `schema_version`, `data_model_version` | Extension and base-model version identity |
| `trace_id` | Stable per-object/per-call trace identity |
| `artifact` | Artifact ID, decoded SHA-256, CPU family and source path |
| `target_object` | EA, extent, dimensions, storage type and payload SHA-256 |
| `call_ref` | Call ID, call PC, call form and helper EA |
| `nodes[]` | Typed ROM, code, RAM, register, helper, branch and consumer entities |
| `edges[]` | Directed relationships between nodes |
| `evidence[]` | Exact source identity, explicit hash algorithm, hash, anchor and extraction method |
| `lookup_contract` | Query input, axis model, interpolation and endpoint behavior |
| `unresolved_boundaries[]` | Stop point, reason and required evidence/discriminator |
| `coverage` | Start/stop boundaries, listing hash and independent re-decode status |
| `semantic_disposition` | Physical-identity and promotion boundary |

## Evidence-basis vocabulary

Evidence basis is separate from confidence:

- `direct_observation`: bytes/instructions independently inspected in the extraction producing the graph.
- `reported_observation`: transcribed from a cited prior report, not independently re-decoded here.
- `derived`: transparent calculation/consequence of cited observations.
- `heuristic`: candidate pattern, not confirmed.
- `unresolved`: intentionally unasserted relationship or stop boundary.

Asserted edges require one or more evidence references. A Git blob SHA-1 is not a file SHA-256. Citing a report hash does not establish the hash of a source listing omitted from that report.

## Validation

`tools/reader_trace_graph.py` checks required fields and versions, explicit hash algorithms, object extent arithmetic, payload-hex length/hash when bytes are supplied, unique IDs, edge endpoints, evidence references, boundary references, lookup node references, coverage metadata and arithmetic warnings for implicit-grid endpoint conflicts. It validates graph structure/provenance—not instruction truth or semantic correctness.

## Reader/consumer and semantic boundary

Query source/type/signedness/register, axis model, interval/interpolation, endpoint behavior, result registers/RAM destinations and consumers are separate graph elements. The first meaningful software consumer is not a demonstrated physical actuator or output endpoint. A graph may stop at that consumer while physical function and units remain unresolved. Donor labels, A2L declarations and screenshot names do not substitute for target-side evidence.

## Existing-indexer bridge

`tools/reader_trace_indexer_adapter.py` is a thin adapter over existing structured outputs. It consumes validated `valid_hits` rows from `rom_access_indexer.run_indexer` and one per-address `write_catalog_summary` row from `build_static_indices.py`. It does not decode SH-2 instructions or reimplement register, delay-slot, branch or call handling.

The adapter accepts the exact 11-field tuple rows returned by `rom_access_indexer.run_indexer` as well as explicitly named mappings; it does not require callers to reconstruct a second schema. It also requires positive, internally consistent PC-concordance counters.

When a per-address static summary includes multiple reader call sites, it does not fan out the aggregate query inputs or destination writes across every call. It records the reader sites separately and leaves the aggregate query/result attribution unresolved until per-call evidence exists.

The adapter preserves evidence grade by relationship:
- A byte-concordant ROM read in the indexer's validated hit output becomes a `direct_observation` edge to its code site.
- Query-register provenance and taint-classified destination flow from the static index become `derived` edges.
- A fallback `near` store remains `heuristic`, with an explicit unresolved boundary.
- A downstream RAM read is represented as a read-site observation only. It does not assert that the lookup result caused the read or that the consumer has a physical calibration meaning.

The input evidence references must already exist in the graph and identify the source output hashes and run/listing manifest. The adapter is idempotent by deterministic node/edge IDs. It should be used only after the existing index runs have passed their own ROM/listing concordance and provenance gates.

## Composed enrichment entry point

`tools/reader_trace_pipeline.py` exposes `enrich_reader_trace(...)` as the single composition point for the current v0.1 pipeline. It:

1. Merges validated byte-concordant ROM read rows and the existing per-address static query/destination summary via `reader_trace_indexer_adapter`.
2. Attaches an exact helper contract only when CPU family, decoded ROM SHA-256 and helper EA match a pinned profile.
3. Revalidates the enriched graph and returns warnings plus explicit flags for profile attachment, instruction decoding and semantic promotion.

The function does not decode SH-2 instructions, does not invent a profile for an unknown helper, does not fan out aggregate multi-reader query/result paths and always reports that it performed no instruction decode and no semantic promotion. Callers can pass the returned graph to `write_trace_graph` after inspecting its warnings and provenance.

## Per-call static-flow bridge

`tools/reader_trace_static_flow_adapter.py` is an additive adapter over the raw
`cat_calls` mapping returned by `build_static_indices.full_rom_analysis()`.
`build_static_flow_call_document()` normalizes and preserves each call row,
including every query-origin token and destination store, then
`write_static_flow_call_document()` emits deterministic JSON and returns the
exact file SHA-256 for the graph evidence record.

The document pins both the decoded ROM SHA-256 and the source listing-member
SHA-256/path. Before graph enrichment, the caller must add an evidence record
whose SHA-256 exactly matches the serialized JSON. The adapter then selects
only the row matching all three graph identities: target EA, call PC and helper
EA (the helper EA is accepted only from an exact `sub_<hex>` helper symbol).
It never attaches a second call's query inputs or result stores.

Query RAM-to-register origins and taint-proven R0 stores are represented as
`derived`. A static tracker's `near` destination remains `heuristic` and gets
an unresolved boundary; it is never connected to the lookup result. The source
listing hash is recorded in graph coverage while
`independent_redecode_performed` remains false: this adapter does not decode
instructions. It also does not infer query transforms, downstream value
causality, physical function or units.

When the composed pipeline receives a per-call document, it suppresses the
aggregate per-address query and destination fields before invoking the existing
summary adapter. This preserves the per-address adapter's conservative
multi-reader behavior while using exact per-call records for the selected
call. Existing calls without a per-call document remain backward-compatible.

## Exact-image helper contracts

`tools/reader_trace_helper_profiles.py` holds a deliberately small, report-sourced helper registry. A profile is keyed by the exact tuple:

`(processor_family, decoded_rom_sha256, helper_ea)`

No name-only, nearby-address, cross-ROM or cross-CPU fallback is allowed. Current EL19A/f501 profiles cover `sub_22E10` (16-point implicit UBYTE), `sub_22FAC` (32-point explicit-axis UWORD), `sub_22B44` (two-axis UBYTE map) and `sub_22DF8` (8-point implicit UBYTE). Each attached profile carries its evidence refs, source listing hash if recorded, report-sourced basis and limitations. Missing required evidence causes attachment to fail. A successful attachment does not upgrade `reported_observation` to `direct_observation`.

## Golden-case caveat: EL19A 0x0F10E

WO70013 describes the 16-point implicit grid as `0,16,...,224`, but 16 points at step 16 from zero give 240 at index 15. The reported `q >= 0xF0` terminal return is consistent with index 15 being 240. This graph records the discrepancy as unresolved. It also records `source_listing_sha256: null` and `independent_redecode_performed: false` because the closed report does not preserve the exact Stage-16 listing hash. Neither gap is silently filled.
