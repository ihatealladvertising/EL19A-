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

## Golden-case caveat: EL19A 0x0F10E

WO70013 describes the 16-point implicit grid as `0,16,...,224`, but 16 points at step 16 from zero give 240 at index 15. The reported `q >= 0xF0` terminal return is consistent with index 15 being 240. This graph records the discrepancy as unresolved. It also records `source_listing_sha256: null` and `independent_redecode_performed: false` because the closed report does not preserve the exact Stage-16 listing hash. Neither gap is silently filled.
