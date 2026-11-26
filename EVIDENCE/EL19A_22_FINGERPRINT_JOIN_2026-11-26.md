# EL19A Target-Side Join of the 22-Object Cross-ROM Fingerprint Family

**Date:** 2026-11-26  
**Status:** Exact-byte join completed; target-side object classification partially complete.  
**Scope:** Read-only raw payload comparison and reconciliation against the current EL19A catalogue, Release 1 scope matrix and XML. No ROM, tool, calibration definition, workbook, Findings record or work-order lifecycle was modified.

## Executive result

The 22 nontrivial payload fingerprints listed in [CROSS_ROM_DISCOVERY_BATCH_2026-11-26.md](CROSS_ROM_DISCOVERY_BATCH_2026-11-26.md) were searched byte-for-byte across the complete EL19A target image.

- **19 of 22 fingerprints** occur in EL19A exactly.
- Those 19 fingerprints produce **27 raw byte occurrences** at distinct ROM offsets.
- **21 occurrences** begin at addresses already represented as target helper-backed table objects in CALIBRATIONS/discovered_tables_catalog.csv.
- **Three additional occurrences** are at existing provisional Release 1 table starts in the scope matrix/XML: 0x0F426, 0x0F10E and 0x0F062.
- One further occurrence, 0x129EE, is documented as the Y axis of the reader-backed 16×16 map at 0x11FC4. It is an axis reference, not a new standalone table.
- Two raw occurrences, 0x04E71 and 0x106EC, are not currently located in the catalogue, scope matrix or XML. They remain unclassified.
- Three fingerprints have no exact byte match anywhere in EL19A: EE310 donor offsets 0x0978E, 0x097BE and 0x09B32. This means only that the donor payloads are not byte-identical in EL19A; it does not establish that corresponding functions or tables are absent.

This is a strong cross-generation conservation result. It is not a semantic name-transfer result.

## Input identity and reproducibility

### EL19A target

- Repository path: EVIDENCE/VERSA f501.bin
- Repository blob: 3c0b1a261a13801ecd703ba05f8f4e88d8bb4267
- Size: 1,048,576 bytes (0x100000)
- MD5: 46991697c502052752a2cabcb84c9e27
- SHA-256: bfe037e8e6c389e2a90214047058eb6dc3bcaaaac5b5931bf98a3f5d9f64fd6a
- The Library analysis copy was checked against the expected MD5 and independently recomputed Git blob SHA-1; both match the repository target blob exactly.

### C11 MR18DE MT donor

- Repository path: EVIDENCE/23710-EE310-07-C11-MR18DE-MT.bin
- Repository blob: 07b4b22db12339fe392cf3fb3d5f0480ab9df303
- Size: 524,288 bytes (0x80000)
- This is the C11 MR18DE manual-transmission donor used for byte-payload extraction. The 22-family was originally identified as shared across four other Nissan ROM images in the cross-ROM discovery report.

### EL19A structures used for classification

- CALIBRATIONS/discovered_tables_catalog.csv — blob a46f47264f230823d06166e1725914cb8c2926b2
- CALIBRATIONS/RELEASE1_SCOPE_MATRIX_R1.csv — blob 2a7f6bb77277f27620ebc648e26c286885efdf21
- CALIBRATIONS/EL19A_release1_conservative.xml — blob 9f16c8ba461a2f0ce162a14688efdf96a6de1345

### Method

Each complete donor payload (8, 16, 32 or 64 bytes, according to its stated UBYTE/UWORD geometry) was searched as an exact byte string through the full 1 MiB EL19A image. Match offsets were then reconciled against the current catalogue, scope matrix and XML. The catalogue is a curated inventory, not the complete 293-table scanner census, so an address absent from that catalogue is not automatically unused or non-table data.

This execution performed the raw target byte join and the documented-inventory cross-check. It did not rerun the workbench complete scan/audit CLI or independently regenerate every helper call argument. The table-reader statements below are cited from existing target-side catalogue records; the XML/scope-only entries retain their current evidence tier.

## Complete 22-fingerprint join

| # | EE310 donor address | Geometry / storage | Exact EL19A byte occurrences | EL19A classification |
|---:|---:|---|---|---|
| 1 | 0x0A08C | 32×1 UBYTE | 0x0F406 | Catalogue table; also Release 1/scope entry |
| 2 | 0x099EE | 8×1 UBYTE | 0x0E9BC | Catalogue table; also Release 1/scope entry |
| 3 | 0x0A024 | 8×1 UBYTE | 0x0F39E | Catalogue table; also Release 1/scope entry |
| 4 | 0x09F6C | 8×1 UBYTE | 0x0F2A6 | Catalogue table; also Release 1/scope entry |
| 5 | 0x098CE | 8×1 UBYTE | 0x04E71, 0x0E7D0 | 0x0E7D0 is catalogue/Release 1; 0x04E71 unclassified |
| 6 | 0x09A0E | 8×1 UBYTE | 0x0E9EC | Catalogue table; also Release 1/scope entry |
| 7 | 0x0A0F8 | 8×1 UBYTE | 0x0F4C2 | Catalogue table; also Release 1/scope entry |
| 8 | 0x09A6A | 8×1 UBYTE | 0x0EA90 | Catalogue table; also Release 1/scope entry |
| 9 | 0x098DE | 8×1 UBYTE | 0x0E7E0 | Catalogue table; also Release 1/scope entry |
| 10 | 0x0A912 | 32×1 UWORD BE | 0x10F8A, 0x12D58 | Both catalogue table objects |
| 11 | 0x0A972 | 32×1 UWORD BE | 0x1100A, 0x12CBE | Both catalogue table objects |
| 12 | 0x0A9B2 | 32×1 UWORD BE | 0x1104A, 0x12C7E | Both catalogue table objects |
| 13 | 0x0A892 | 32×1 UWORD BE | 0x106EC, 0x10EEA, 0x12BDE | 0x10EEA and 0x12BDE catalogue objects; 0x106EC unclassified |
| 14 | 0x0A8D2 | 32×1 UWORD BE | 0x10F2A, 0x12B9E | Both catalogue table objects |
| 15 | 0x0A2DC | 16×1 UWORD BE | 0x0FEC0, 0x129EE | 0x0FEC0 catalogue object; 0x129EE is a documented axis of map 0x11FC4 |
| 16 | 0x0A7D2 | 4×1 UWORD BE | 0x10D12 | Catalogue table object |
| 17 | 0x0A0AC | 16×1 UBYTE | 0x0F426 | Existing Release 1/scope table; absent from current curated catalogue |
| 18 | 0x0978E | 8×1 UBYTE | — | No exact EL19A match |
| 19 | 0x097BE | 8×1 UBYTE | — | No exact EL19A match |
| 20 | 0x09B32 | 16×1 UBYTE | — | No exact EL19A match |
| 21 | 0x09E4C | 16×1 UBYTE | 0x0F10E | Existing Release 1/scope table; absent from current curated catalogue |
| 22 | 0x09DD4 | 16×1 UBYTE | 0x0F062 | Existing Release 1/scope table; absent from current curated catalogue |

## Strongest target-side discoveries

### 1. Five 32-point UWORD payloads have two EL19A copies apiece

The five EE310 vectors at 0x0A912, 0x0A972, 0x0A9B2, 0x0A892 and 0x0A8D2 are each found byte-for-byte at two EL19A addresses, yielding two five-object families:

| First EL19A family | Matching second copy | Existing target catalogue relationship |
|---|---|---|
| 0x10F8A | 0x12D58 | Explicit trustful twin; 0x10F8A is the 32-point UWORD curve on axis 0x0F712; 0x12D58 uses axis 0x128FE |
| 0x1100A | 0x12CBE | Explicit trustful twin; 0x1100A is paired with 0x1104A |
| 0x1104A | 0x12C7E | Explicit trustful twin; 0x1104A is paired with 0x10F2A |
| 0x10EEA | 0x12BDE | Explicit trustful twin; each is the axis for its paired 32-point curve |
| 0x10F2A | 0x12B9E | Explicit trustful twin; each is the axis for its paired 32-point curve |

The target catalogue records the corresponding helper readers:
- First-family objects are read through sub_22FAC at call sites including 0x648D8, 0x68A86+, 0x68ACA, 0x6904A and 0x68F54.
- Second-family copies are read through sub_2319C at 0x6810A, 0x68BD4, 0x68BF6, 0x69518 and 0x69568.

This is not merely address-nearby similarity: the full 64-byte payloads are exact, and the existing target inventory already documents the duplicate relationships and reader-backed objects. The join materially strengthens the cross-ROM conservation of this 32-point family. It does not establish a physical label or unit for every member.

### 2. The 16-point UWORD payload is reused as two target axes

The donor payload at 0x0A2DC appears at:
- 0x0FEC0, a reader-backed 16×1 UWORD BE curve whose values are the Y axis of the 0x0CD56 16×16 surface.
- 0x129EE, the 16-point UWORD BE Y axis of the reader-backed 0x11FC4 16×16 surface.

Thus the same exact vector is used in two distinct target map contexts. The first is already documented as linked storage in Release 1; the second is present as the axis of 0x11FC4.

### 3. Additional byte-identical UBYTE curves span target subsystems

The 32-point UBYTE match at 0x0F406 is a particularly strong anchor: target catalogue evidence identifies it as the ADC NTC voltage-to-temperature linearization curve, read by sub_22E28 at 0x28B38, 0x28B6E, 0x354AE and 0x3572C. Its fixed query grid is 0..248 in steps of 8; the recorded consumer path feeds the coolant/air-temperature image through sub_2245C.

Eight other 8-point UBYTE fingerprints land on existing target catalogue objects:
- 0x0E9BC — sub_22DF8 @ 0x28BBC
- 0x0F39E — sub_22EFC @ 0x36C84, axis 0x0E124
- 0x0F2A6 — sub_22EFC @ 0x36CE8, axis 0x0E108
- 0x0E7D0 — sub_22DF8 @ 0x37F64
- 0x0E9EC — sub_22DF8 @ 0x40FD0
- 0x0F4C2 — sub_22EFC @ 0x46538, axis 0x0F49E
- 0x0EA90 — sub_22DF8 @ 0x4DED2
- 0x0E7E0 — sub_22DF8 @ 0x50014

These are byte-level donor matches to target table starts, but no donor symbol names, units or conversions are assigned.

### 4. A four-point UWORD curve also matches exactly

The donor at 0x0A7D2 matches target 0x10D12 byte-for-byte. The target catalogue records a 4×1 UWORD BE lookup through sub_22E44 @ 0x6AA4A, with query min(0xC000, sub_22494()<<6) selected by the comparison against U16[0x985A]. Its result is stored at FFFF1054+0x430, followed by calls to sub_6A8C0 and sub_6A96C.

## Three exact matches at provisional XML/scope table starts

The donor 16-point UBYTE fingerprints at 0x0A0AC, 0x09E4C and 0x09DD4 occur at target 0x0F426, 0x0F10E and 0x0F062, respectively.

The current Release 1/scope matrix describes these as:
- 0x0F426: provisional Engine Speed Threshold Curve, with implicit raw query grid 0,16,…,240.
- 0x0F10E: provisional Cranking Fuel Value vs Coolant curve, with implicit raw query grid 0,16,…,240.
- 0x0F062: provisional Ambient Pressure Reference curve, with the axis at 0x0E0CE.

These exact donor matches strengthen the evidence that the target payloads are conserved from the older C11 MR18DE MT ROM. The current curated catalogue does not contain separate rows for these three addresses. They therefore remain at their current target evidence level; this report does not independently supply their helper call PCs or complete consumer traces, and it does not promote the provisional physical names.

## Unclassified raw matches — do not promote yet

Two exact matches require a separate target-side reference check:

- 0x04E71: an 8-byte match for donor 0x098CE. It has no current row in the discovered-table catalogue, scope matrix or Release 1 XML.
- 0x106EC: a 64-byte match for donor 0x0A892. It has no current row in the discovered-table catalogue, scope matrix or Release 1 XML, and it is not listed as an axis by the current catalogue.

These locations may be literals, embedded data, unindexed lookup data or incidental byte sequences. Until a reader/reference is demonstrated, they are raw occurrences only.

## Three donor fingerprints not present exactly in EL19A

| EE310 donor address | Geometry | Result |
|---|---|---|
| 0x0978E | 8×1 UBYTE | No exact match |
| 0x097BE | 8×1 UBYTE | No exact match |
| 0x09B32 | 16×1 UBYTE | No exact match |

No negative semantic inference is warranted. A candidate EL19A function may use a changed calibration payload, a different representation or another table location.

## Evidence disposition and next useful tests

**Disposition: structural cross-ROM corroboration; no new FND/REC allocated.** The report establishes exact payload identities and target inventory relationships, not new physical meanings. Existing target object names, units and scaling remain unchanged.

Recommended bounded follow-up:
1. Trace all target references/calls for the three scope/XML-only exact matches (0x0F426, 0x0F10E, 0x0F062) and record complete helper/query/consumer paths.
2. Check references to raw occurrences 0x04E71 and 0x106EC; either identify their true object extent/reader or close them as unclassified/non-table occurrences.
3. Compare the three no-hit donor fingerprints with only same-geometry EL19A reader-backed candidates, and report byte differences without asserting function absence.
4. Preserve the five-pair 32-point UWORD family as a reusable fingerprint set for future Nissan ROMs.

**No calibration XML, scope matrix, catalogue, ROM, LST, A2L, workbook, tool source, Findings index or live work-order register was edited by this investigation.**
