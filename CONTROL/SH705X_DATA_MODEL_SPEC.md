# SH705X Data Model Specification — Canonical Conceptual Model and JSON Interchange Envelope

## Version

`spec:sh705x-datamodel-v1.0.0` — 2026-11-26

---

## Design Rationale

This model is designed as a **conceptual interchange envelope** for the SH7055/SH7058 Nissan/Hitachi lookup-helper and calibration-table scanner suite. It is not a database schema, not a Python class hierarchy, and not a validator. Its purpose is to let independently executable commands exchange reliable data about ROM tables, addresses, and calibration objects without duplicating decoding logic or collapsing evidence provenance.

Key principles:

- **File offset is never silently treated as ROM effective address or RAM address.** Both are retained as separate fields with explicit provenance.
- **Duplicate declarations sharing an address are retained as separate records**, each with their own identity.
- **Raw metadata and unsupported syntax are preserved** so that parser improvements do not discard evidence.
- **The JSON envelope is the canonical store**; TSV/CSV are derived review exports.
- **Versioned** — new fields may be added in minor versions; unknown fields are silently ignored by downstream consumers.
- **Address relocation–stable** — IDs survive cross-ROM comparison without dependence on absolute addresses.

---

## 1. ROM Artifact / Image

Canonical description of a binary ROM container, whether original or reconstructed.

| Field | Type | Description | Example |
|---|---|---|---|
| `artifact_id` | string | Globally unique identifier, format `rom:<basename>#<sha256>` | `rom:VERSA_f501.bin#bfe037e8e6c3a7d5e8f1a2c4b6d7e9f0a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3` |
| `container` | string | `.bin`, `.zip`, `.s19`, `.hex` | `bin` |
| `source_path` | string | Filesystem path or URL origin | `EVIDENCE/VERSA f501.bin` |
| `decoded_size_bytes` | integer | Size of reconstructed flat ROM image after decompression/map | `1048576` |
| `decoded_sha256` | string | SHA-256 of the decoded flat image | `bfe037e8e6c3a7d5e8f1a2c4b6d7e9f0a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5` |
| `loader` | string | Tool/Command that produced the decoded image | `sh7058_cross_rom_scanner.py v1.0.0` |
| `loader_args` | object | Arguments passed to the loader (for reproducibility) | `{"el19a": true, "xml": "CALIBRATIONS/EL19A_best_guess_provisional_full_definition.xml"}` |
| `byte_order` | enum `little`, `big` | Endianness of the decoded image | `big` |
| `import_notes` | string | Free-text notes on extraction, map quality, or ambiguity | `Extracted from Renesas SH7055 binary; mov.l @(d,PC) helper recovery` |

---

## 2. Processor / Profile

Description of the target processor family and configuration; ECU-specific data is kept outside generic processor behavior.

| Field | Type | Description | Example |
|---|---|---|---|
| `processor_family` | string | SH7055, SH7058, etc. | `SH7058` |
| `model` | string or null | Specific part number within family, or null | `SH705828N` |
| `endianness` | enum `little`, `big` | Processor byte order | `big` |
| `capabilities` | string[] | Feature flags (e.g. `mov.l @(d,PC)`, `bsr`) | `["mov.l @(d,PC)", "bsr"]` |
| `profile` | string or null | ECU-profile name if applicable | `MR18DE_CVT` |
| `address_domain` | enum `rom`, `ram`, `both` | Where the processor operates | `rom` |

---

## 3. Address Space / Memory Region

Disambiguation of file offset, ROM effective address, and RAM address. No silent conflation.

| Field | Type | Description | Example |
|---|---|---|---|
| `ea` | integer or null | ROM effective address (0 if file-offset–only) | `369ea` |
| `file_offset` | integer or null | Offset within the decoded flat image (0 if EA–only) | `369ea` |
| `ram_address` | integer or null | RAM address if known, otherwise null | null |
| `address_domain` | enum `rom`, `ram`, `both`, `unknown` | Primary domain of this address | `rom` |
| `translation_provenance` | string or null | How the EA was derived (e.g. `helper-relative`, `xml-storage-address`, `unknown`) | `helper-relative` |
| `resolution_status` | enum `resolved`, `unresolved`, `unknown`, `conflicting` | Whether the address has a single consistent meaning | `resolved` |

**Rule:** At least one of `ea` or `file_offset` must be present. If `ea` is present, `file_offset` may be null and vice versa; but a complete record has both.

---

## 4. Symbols

Declaration of names, namespaces, kinds, and source references. Duplicate declarations at one address are retained as separate records.

| Field | Type | Description | Example |
|---|---|---|---|
| `symbol_id` | string | Globally unique, format `sym:<basename>#<sha256-of-declaring-rom>` | `sym:lookup_helper#bfe037e8` |
| `name` | string | Symbol name | `LookupFreqTable` |
| `namespace` | string or null | Optional namespace grouping | null |
| `kind` | enum `function`, `label`, `table`, `variable`, `constant`, `enum`, `struct`, `typedef`, `unknown` | Declaration kind | `table` |
| `address` | string | Address as stored; never silently reinterpreted | `0x369ea` or `0x05c2e` |
| `address_ea` | integer or null | Effective address if different from stored string | `0x369ea` |
| `address_ram` | integer or null | RAM address if known | null |
| `declaring_artifact` | string | ROM artifact this symbol comes from | `rom:VERSA_f501.bin#bfe037e8` |
| `source_line` | string or null | Original source location, if available | `a2l:project.nxp, line 442` |
| `aliases` | string[] | Names also used for this declaration | `["FreqTable"]` |
| `duplicate_at` | string[] | Other addresses where this name appears | `["0x09b2e"]` |

**Rule:** Do not collapse two declarations sharing an address into one record. Each `symbol_id` is globally unique; `duplicate_at` tracks homonymy.

---

## 5. Calibration Objects

Storage-specific metadata for a lookup-helper–backed table object. This is the core "reader-backed object" from the scanner output.

| Field | Type | Description | Example |
|---|---|---|---|
| `obj_id` | string | Globally unique, format `obj:<artifact_id>#<sha256-of-extent>` | `obj:rom:VERSA_f501.bin#bfe037e8#588cff998ac404f6` |
| `artifact_id` | string | Referencing ROM artifact | `rom:VERSA_f501.bin#bfe037e8` |
| `table_address` | string | Storage address within the ROM | `0x369ea` |
| `ea` | integer or null | Effective address (may equal table_address) | `0x369ea` |
| `file_offset` | integer or null | File offset within decoded image | `0x369ea` |
| `storage_type` | enum `uint8`, `int8`, `uint16`, `int16`, `uint32`, `int32`, `float`, `unknown` | Storage width and signedness | `uint16` |
| `element_type` | enum `uint8`, `int8`, `uint16`, `int16`, `unknown` | Element type per scanner classification | `uint16` |
| `dim1` | integer | First dimension / number of axis-1 points | `16` |
| `dim2` | integer | Second dimension / number of axis-2 points | `16` |
| `axis1_type` | enum `uint8`, `uint16`, `implicit_u8`, `implicit_u16`, `unknown` | Axis 1 data type | `implicit_u16` |
| `axis2_type` | enum `uint8`, `uint16`, `implicit_u8`, `implicit_u16`, `unknown` | Axis 2 data type | `` |
| `byte_extent` | integer | `dim1 * dim2 * element_width_bytes` | `512` |
| `payload_sha256` | string | SHA-256 of the raw byte extent | `588cff998ac404f6c52735522519ee49af83e3b33083b6fc5e415abaed131428` |
| `distinct_byte_values` | integer or null | Count of unique byte values in the extent; `null` if unknown | `45` |
| `axis1_values` | string or null | Explicit stored values for axis 1, if any | null (implicit grid) |
| `axis2_values` | string or null | Explicit stored values for axis 2, if any | null (implicit grid) |
| `axis1_count` | integer or null | `dim1` if axis1 is explicit, otherwise null | `16` |
| `axis2_count` | integer or null | `dim2` if axis2 is explicit, otherwise null | `16` |
| `conversion_provenance` | string or null | How the conversion/calibration was derived; free text | `SH7058 helper @ 0x15000` |
| `reader_backed` | boolean | True if this object was emitted by the SH7058 scanner | `true` |
| `prior_report` | string or null | Link to prior FND/REC record, if any | `FND-2026-11-26-001` |

**Rule:** `byte_extent` = `dim1 * dim2 * element_width_bytes(element_type)`. `element_width_bytes(uint8)` = 1, `element_width_bytes(int8)` = 1, `element_width_bytes(uint16)` = 2, `element_width_bytes(int16)` = 2.

---

## 6. Axes and Conversions

Query domain, storage representation, and raw-vs-physical conversion. Source formula text is preserved; evaluation is not required.

| Field | Type | Description | Example |
|---|---|---|---|
| `conv_id` | string | Globally unique, format `conv:<obj_id>#<sha256>` | `conv:obj:rom:VERSA_f501.bin#bfe037e8#588cff99#conv1` |
| `obj_id` | string | Referencing calibration object | `obj:rom:VERSA_f501.bin#bfe037e8#588cff99` |
| `axis` | enum `axis1`, `axis2` | Which axis this describes | `axis1` |
| `convert_to` | string | Target physical unit (free text, not evaluated) | `RPM`, `MAP_kPa`, `FuelTrim_%` |
| `convert_from` | string | Storage domain (free text) | `count`, `raw_adc`, `voltage` |
| `formula_text` | string | Original formula or description; preserved as-is, not evaluated | `MAP = (raw * 100) / 65536` |
| `formula_direction` | enum `storage_to_physical`, `physical_to_storage`, `bidirectional`, `unknown` | Direction of the conversion | `storage_to_physical` |
| `query_domain` | string or null | The domain over which the lookup/interpolation is valid | null (implicit grid) |
| `axis_points` | string or null | Comma-separated list of explicit breakpoints, if any | null |
| `interp_method` | enum `linear`, `lookup`, `curve`, `clamp`, `unknown` | Interpolation/search/clamp behavior | `lookup` |
| `conversion_notes` | string or null | Free-text notes on source, derivation, or ambiguity | `Derived from SH7058 helper clamp at 0x15000` |

**Rule:** `formula_text` is stored as-is. No parser is required to evaluate it. `convert_from` and `convert_to` are free-text labels; no unit-registry enforcement is imposed.

---

## 7. Readers / Lookups / Consumers

Function and call-site identity, helper arguments, lookup behavior, and consumer relationships.

| Field | Type | Description | Example |
|---|---|---|---|
| `call_id` | string | Globally unique, format `call:<artifact_id>#<call_pc>` | `call:rom:VERSA_f501.bin#0x369ea` |
| `call_pc` | integer | Program counter of the call or table reference | `0x369ea` |
| `call_form` | enum `indirect_jsr`, `indirect_jmp`, `bsr`, `direct`, `unknown` | Type of call/transfer | `indirect_jsr` |
| `helper` | string | Referencing the helper that was followed to this call | `helper:rom:VERSA_f501.bin#0x15000` |
| `arguments` | object | Derived register values at the call site; at minimum `r4`, `r5`, `r6` | `{"r4": 0x369ea, "r5": 0x58556, "r6": 0x470b}` |
| `lookup_behavior` | string | Free-text description of how the lookup was performed | `implicit-grid 16x16 uint16 lookup` |
| `consumer` | string or null | Name or ID of the function/caller that consumes this lookup | `fuel_map_evaluation` |
| `consumer_role` | enum `primary`, `secondary`, `observer`, null | Role of the consumer | `primary` |

**Rule:** `arguments` must contain at least `r4` (the suspected table pointer) and may include `r5`, `r6` (axis values for 3D tables).

---

## 8. Evidence / Provenance

Immutable source hashes, path, source range, extraction method, observation, confidence/status, evidence class, and links to Findings/Reconciliation records.

| Field | Type | Description | Example |
|---|---|---|---|
| `ev_id` | string | Globally unique, format `ev:<sha256-of-source>` | `ev:bfe037e8e6c3a7d5e8f1a2c4b6d7e9f0a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5` |
| `source_path` | string | Filesystem path or URL of the source artifact | `EVIDENCE/VERSA f501.bin` |
| `source_hash` | string | SHA-256 of the exact source file (or member) | `bfe037e8e6c3a7d5e8f1a2c4b6d7e9f0a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5` |
| `evidence_class` | enum `target`, `donor`, `exact_payload`, `screenshot`, `inferred`, `xml_catalogue`, `reconciliation` | Classification of the evidence | `target` or `donor` |
| `extraction_method` | string | How the evidence was extracted | `SH7058 scanner helper enumeration` |
| `observation` | string | Measured or observed value | `16x16 uint8 table at 0x369ea` |
| `confidence` | enum `high`, `medium`, `low`, `unknown` | Confidence in the observation | `high` |
| `status` | enum `verified`, `unverified`, `pending`, `disputed` | Current status of the evidence | `verified` |
| `links` | object | Links to related records | `{"fnd_rec": "FND-2026-11-26-001", "wo": "WO70019"}` |
| `acquired` | string | ISO 8601 timestamp | `2026-11-26T14:30:00Z` |

**Rule:** Every evidence record has an immutable `source_hash`. The `evidence_class` distinguishes target-owned data from donor hypothesis data.

---

## 9. Analysis Run / Result

Tool identity, arguments, timestamp policy, input hashes, output schema version, and deterministic result identity.

| Field | Type | Description | Example |
|---|---|---|---|
| `run_id` | string | Globally unique, format `run:<tool>#<version>#<input_sha256>` | `run:sh7058_cross_rom_scanner.py#v1.0.0#bfe037e8` |
| `tool_name` | string | Name of the tool/Command | `sh7058_cross_rom_scanner.py` |
| `tool_version` | string | Tool version | `1.0.0` |
| `timestamp` | string | ISO 8601 UTC when the run started | `2026-11-26T14:00:00Z` |
| `input_artifacts` | string[] | List of `artifact_id`s this run consumed | `["rom:VERSA_f501.bin#bfe037e8"]` |
| `output_schema_version` | string | Version of the JSON interchange envelope produced | `sh705x-datamodel-v1.0.0` |
| `deterministic_id` | string | Hash of the structured output for equality-checking | `a1b2c3d4e5f60718293a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e` |
| `arguments` | object | Exact CLI arguments passed | `{"el19a": "EVIDENCE/VERSA f501.bin", "xml": "CALIBRATIONS/EL19A_best_guess_provisional_full_definition.xml"}` |
| `output_path` | string or null | Where the JSON or TSV output was written | `CONTROL/WO70019_batch.json` |

**Rule:** `deterministic_id` is computed as `sha256(run_id + json_dump(output, sort_keys=True))`. Two runs with identical input and arguments must produce the same `deterministic_id`.

---

## Versioning and Compatibility Rules

- Minor version bumps (e.g. `v1.0.0` → `v1.1.0`) may add new optional fields; existing consumers silently ignore unknown fields.
- Major version bumps (e.g. `v1.0.0` → `v2.0.0`) may rename or redefine fields; consumers must check `output_schema_version` and adapt accordingly.
- The `output_schema_version` field is mandatory in every envelope produced by a compliant tool.
- TSV/CSV exports derived from this envelope must include a header row indicating `spec:sh705x-datamodel-v1.0.0`.

---

## Worked Conceptual Examples

### Example A — Reader-Backed EL19A Calibration with Target Evidence

```json
{
  "artifact_id": "rom:VERSA_f501.bin#bfe037e8e6c3a7d5e8f1a2c4b6d7e9f0a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3",
  "processor": {
    "family": "SH7058",
    "model": "SH705828N",
    "endianness": "big",
    "capabilities": ["mov.l @(d,PC)", "bsr"],
    "profile": "MR18DE_CVT"
  },
  "calibration_objects": [
    {
      "obj_id": "obj:rom:VERSA_f501.bin#bfe037e8#588cff998ac404f6c52735522519ee49af83e3b33083b6fc5e415abaed131428",
      "table_address": "0x369ea",
      "ea": 0x369ea,
      "file_offset": 0x369ea,
      "storage_type": "uint16",
      "element_type": "uint16",
      "dim1": 16,
      "dim2": 16,
      "axis1_type": "implicit_u16",
      "axis2_type": "implicit_u16",
      "byte_extent": 512,
      "payload_sha256": "588cff998ac404f6c52735522519ee49af83e3b33083b6fc5e415abaed131428",
      "distinct_byte_values": 45,
      "conversion_provenance": "SH7058 helper @ 0x15000",
      "reader_backed": true,
      "prior_report": "FND-2026-11-26-001"
    }
  ],
  "axes_conversions": [
    {
      "conv_id": "conv:obj:rom:VERSA_f501.bin#bfe037e8#588cff99#conv1",
      "obj_id": "obj:rom:VERSA_f501.bin#bfe037e8#588cff998ac404f6c52735522519ee49af83e3b33083b6fc5e415abaed131428",
      "axis": "axis1",
      "convert_from": "raw_count",
      "convert_to": "RPM",
      "formula_text": "RPM = (raw * 60) / 65536",
      "formula_direction": "storage_to_physical",
      "query_domain": null,
      "axis_points": null,
      "interp_method": "lookup"
    }
  ],
  "readers_lookups_consumers": [
    {
      "call_id": "call:rom:VERSA_f501.bin#0x369ea",
      "call_pc": 56954,
      "call_form": "indirect_jsr",
      "helper": "helper:rom:VERSA_f501.bin#0x15000",
      "arguments": {"r4": 56954, "r5": 58556, "r6": 0},
      "consumer": "fuel_map_evaluation",
      "consumer_role": "primary"
    }
  ],
  "evidence": [
    {
      "ev_id": "ev:bfe037e8e6c3a7d5e8f1a2c4b6d7e9f0a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5",
      "source_path": "EVIDENCE/VERSA f501.bin",
      "source_hash": "bfe037e8e6c3a7d5e8f1a2c4b6d7e9f0a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5",
      "evidence_class": "target",
      "extraction_method": "SH7058 scanner helper enumeration",
      "observation": "16x16 uint16 table at 0x369ea",
      "confidence": "high",
      "status": "verified",
      "links": {"fnd_rec": "FND-2026-11-26-001", "wo": "WO70019"},
      "acquired": "2026-11-26T14:30:00Z"
    }
  ],
  "analysis_run": {
    "run_id": "run:sh7058_cross_rom_scanner.py#v1.0.0#bfe037e8",
    "tool_name": "sh7058_cross_rom_scanner.py",
    "tool_version": "1.0.0",
    "timestamp": "2026-11-26T14:00:00Z",
    "input_artifacts": ["rom:VERSA_f501.bin#bfe037e8"],
    "output_schema_version": "sh705x-datamodel-v1.0.0",
    "deterministic_id": "a1b2c3d4e5f60718293a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e",
    "arguments": {"el19a": "EVIDENCE/VERSA f501.bin", "xml": "CALIBRATIONS/EL19A_best_guess_provisional_full_definition.xml"},
    "output_path": "CONTROL/WO70019_batch.json"
  }
}
```

### Example B — Donor A2L Characteristic with Axis/Conversion Links (No Target-Side Semantic Promotion)

```json
{
  "artifact_id": "rom:CF48D.bin#cf48dsha256example00000000000000000000000001",
  "processor": {
    "family": "SH7055",
    "model": null,
    "endianness": "big",
    "capabilities": ["mov.w @(d,PC)", "extu.b"],
    "profile": null
  },
  "calibration_objects": [
    {
      "obj_id": "obj:rom:CF48D.bin#cf48dsha256example00000000000000000000000001#2f8e7a5c9d1e3b4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0",
      "table_address": "0x652b",
      "ea": 0x652b,
      "file_offset": 0x652b,
      "storage_type": "uint8",
      "element_type": "uint8",
      "dim1": 32,
      "dim2": 1,
      "axis1_type": "uint8",
      "axis2_type": "unknown",
      "byte_extent": 32,
      "payload_sha256": "2f8e7a5c9d1e3b4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0",
      "distinct_byte_values": null,
      "conversion_provenance": "CF48D A2L import, storage type from A2L `storagetype`",
      "reader_backed": false,
      "prior_report": null
    }
  ],
  "axes_conversions": [
    {
      "conv_id": "conv:obj:rom:CF48D.bin#cf48dsha256example00000000000000000000000001#2f8e7a5c9d1e3b4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0",
      "obj_id": "obj:rom:CF48D.bin#cf48dsha256example00000000000000000000000001#2f8e7a5c9d1e3b4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0",
      "axis": "axis1",
      "convert_from": "raw_adc",
      "convert_to": "MAP_kPa",
      "formula_text": "MAP_kPa = (raw * 200) / 255 - 100",
      "formula_direction": "storage_to_physical",
      "query_domain": null,
      "axis_points": null,
      "interp_method": "lookup"
    }
  ],
  "readers_lookups_consumers": [
    {
      "call_id": "call:rom:CF48D.bin#0x652b",
      "call_pc": 23531,
      "call_form": "bsr",
      "helper": "helper:rom:CF48D.bin#0x05000",
      "arguments": {"r4": 26379, "r5": 0, "r6": 0},
      "consumer": null,
      "consumer_role": null
    }
  ],
  "evidence": [
    {
      "ev_id": "ev:cf48dsha256example00000000000000000000000001",
      "source_path": "EVIDENCE/CF48D.bin",
      "source_hash": "cf48dsha256example00000000000000000000000001",
      "evidence_class": "donor",
      "extraction_method": "A2L import via a2l_structural_matcher.py",
      "observation": "32-byte uint8 array at 0x652b",
      "confidence": "medium",
      "status": "verified",
      "links": {"wo": "WO70021"},
      "acquired": "2026-11-26T15:00:00Z"
    }
  ],
  "analysis_run": {
    "run_id": "run:a2l_structural_matcher.py#v1.0.0#cf48dsha256example00000000000000000000000001",
    "tool_name": "a2l_structural_matcher.py",
    "tool_version": "1.0.0",
    "timestamp": "2026-11-26T15:00:00Z",
    "input_artifacts": ["rom:CF48D.bin#cf48dsha256example00000000000000000000000001"],
    "output_schema_version": "sh705x-datamodel-v1.0.0",
    "deterministic_id": "0a1b2c3d4e5f60718293a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e",
    "arguments": {"xml": "EVIDENCE/CF48D.xml"},
    "output_path": "CONTROL/WO70021_donor_examples.json"
  }
}
```

---

## Migration from Existing Scanner / Workbench Outputs

The scanner `sh7058_cross_rom_scanner.py` and the workbench `nissan_sh705x_workbench.py` produce output formats that are **derived reviews** of this envelope. Existing files are not altered:

- `CONTROL/WO70019_batch.json` — machine-readable batch scan export; fields map as follows:
  - `input → artifact_id`, `decoded_rom_sha256 → decoded_sha256`, `helpers → reader-backed symbol records`, `calls → call records`, `tables → calibration object records`
- `CONTROL/tsv_output/*.tables.tsv`, `*.calls.tsv`, `*.helpers.tsv` — TSV derivable from the envelope; not the canonical store.
- `CALIBRATIONS/EL19A_*.xml` — Release 1 XML; fields map selectively; unknown elements are preserved as `evidence_class: xml_catalogue`.

No existing outputs are modified or required to conform to this model; the model is backward-compatible (unknown fields are silently ignored).

---

## Acceptance Criteria

- [x] All nine model areas are specified with field tables, identities, references and unresolved-state behavior.
- [x] The versioned JSON envelope is sufficient for multiple standalone tools to exchange ROM, symbols, calibrations and evidence.
- [x] Worked examples (A and B) demonstrate separation of target proof and donor hypotheses, with no semantic promotion from donor to target.
- [x] Migration from existing scanner/workbench outputs is addressed without altering those outputs.
- [x] Findings disposition: **NOT REQUIRED** — specification work alone does not materially change a calibration interpretation.

---

## Authorized paths and exclusions

Authorized new outputs only:

- `CONTROL/SH705X_DATA_MODEL_SPEC.md` — this file
- `CONTROL/WO70021.md` — concise work-order report

Do not edit Python source, tests, workflows, ROM/LST/A2L/XML files, workbook, catalogue, scope matrix, Findings records/index or other WOs. Do not create a JSON Schema implementation, database or code scaffolding. Follow `CONTROL/WORKER_PROTOCOL.md`, including publication-gate and Worker 3 FIFO rules.