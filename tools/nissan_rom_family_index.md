# Nissan Master ROM & Structural-Family Index

## Purpose

This is the cross-scan identity and comparison layer for the Nissan ROM corpus. It turns scan outputs into a searchable register and reproducible pairwise relationships, so newly scanned ROMs can be compared with known images and likely structural generations.

The index is relational. It deliberately keeps these identities separate:

1. **UpRev catalogue ROM code** — a vehicle/application ROM code. Every code has its own row; the catalogue IsMasterROM flag and MasterROM_ID relationship are preserved.
2. **Nissan binary identifiers** — primary metadata FID and the separate ECU ID inventory. Exact matches and prefix-only candidates are represented differently.
3. **Decoded ROM image** — canonical identity is the decoded image SHA-256. Identical decoded images deduplicate to one image record while all source files and scan records remain linked.
4. **Structural-family candidate** — a derived relationship based on executable-code hashes and/or table-layout evidence. It is not a catalogue ID, FID, ECU declaration, or semantic calibration identity.

## Canonical sources

The default build consumes:

- EVIDENCE/NISSAN_ROM_ID_CROSSWALK_2026-11-27.tsv — 3,691 individual ROM-code rows; the master code is marked YES on its own row and each variant refers to MasterROM_ID.
- EVIDENCE/NISSAN_ROM_VEHICLE_CATALOG_2026-11-27.tsv — 2,161 source vehicle/master-ROM groups.
- EVIDENCE/NISSAN_ECU_FID_CATALOG_2026-11-27.tsv — separate 43-row ECU/FID inventory.
- EVIDENCE/NISSAN_DAT_DETAILED_SCAN_INDEX_2026-11-27.tsv — 431 direct-DAT detailed-positive scan records.
- EVIDENCE/mass dat scan/scan_results.tsv — 14,666 historical scan-result records, including successful loads and rejected containers.
- EVIDENCE/mass dat scan/file_inventory.tsv — 16,584 original file-inventory rows, including direct inputs, archive packages and ancillary files.
- EVIDENCE/NISSAN_BASE_TABLE_SET_2026-11-27/NISSAN_BASE_TABLE_OBJECTS_2026-11-27.tsv.gz — 129,481 per-image table observations across 434 independent layouts (431 DAT layouts plus EL19A, V6 and C12W).
- Fresh workbench scan outputs from EVIDENCE/rr roms/, including per-image lossless catalogues and a combined ROM/RomRaider code-region/payload reference index.

The source datasets overlap. ROM images are joined on decoded SHA-256 and are not summed as independent ROMs. The historical scan ledger is joined to the original file inventory on input SHA-256, with duplicate-key cardinality preserved in a grouped bridge. The 431 detailed-positive DAT rows match the historical ledger through decoded-image SHA-256; they are a detailed subset, not 431 additional images. A scan-result SHA without an exact file-inventory match remains an explicit unmatched source reference.

## Output files

Generated under EVIDENCE/NISSAN_ROM_FAMILY_INDEX/:

| File | Grain | Contents |
|---|---|---|
| nissan_master_rom_code_index.tsv | One row per ROM code | Full 3,691-code crosswalk, master flag, model, make, year, engine, transmission, source line |
| nissan_master_rom_groups.tsv | One row per catalogue group | Master code, member count, member codes |
| nissan_rom_image_index.tsv | One row per decoded image SHA | Source paths, ROM size, CPU, FIDs, linked catalogue codes/groups, scan coverage and candidate component |
| nissan_rom_scan_sources.tsv | One row per source scan record | Refreshed ROM-folder, detailed DAT and historical mass-scan records linked to canonical decoded-image IDs |
| nissan_historical_mass_scan_results.tsv | One row per historical scan-result record | All 14,666 original records, exact input hash, codec, status, decoded-image hash, loader metrics, errors and file-inventory joins |
| nissan_original_file_inventory.tsv | One row per original file | All 16,584 original file paths, extensions, sizes, hashes and classifications |
| nissan_mass_scan_input_hash_links.tsv | One row per SHA-256 key across scan results and inventory | Exact/mass-only/inventory-only dispositions, source cardinalities and paths without false one-to-one joins |
| nissan_rom_identifier_links.tsv | One row per identifier-to-image link | Identifier namespace, exact/prefix status, confidence, model/year/engine metadata and provenance |
| nissan_rom_structural_profiles.tsv | One row per image | Full-geometry or summary-only coverage, geometry/signature/payload counts, table-kind counts and scanner aggregates |
| nissan_rom_generation_summary.tsv | One row per metadata application group | Year/model/engine/transmission, separated by UpRev-code and exact ECU-FID metadata, image and structure coverage |
| nissan_rom_family_relationships.tsv | One row per related image pair | Relationship types, strict and shape similarity, payload/code hashes, vehicle metadata and evidence boundary |
| nissan_rom_candidate_components.tsv | One row per candidate cluster | Connected components formed only by the high-specificity rules below |
| nissan_rom_family_index.json | Versioned canonical JSON | Named-field records for codes, groups, images, links, scan sources, profiles, relationships and components |
| nissan_rom_family_index_manifest.json | One build manifest | Input/output sizes and hashes plus build summary |
| run_summary.json | One run | Scan status counts, tool source hashes, input hashes, Python version and index summary |
| workbench/ | Per-image scan artefacts | Fresh per-ROM catalogues/manifests, inventory and generated reference index |

TSV files are tab-delimited and open in Excel. JSON is the canonical structured output.

## Relationship interpretation

Relationships are emitted as separate, filterable evidence types:

- CATALOGUE_MASTER_ROM_GROUP — two scanned images have ROM codes in the same catalogue master group. This is catalogue metadata, not proof of shared firmware or structure.
- SAME_PRIMARY_FID_GROUP — same detected primary FID. This is an identifier cohort, not proof of identical code/layout.
- IDENTICAL_CODE_REGION_HASH — shared exact code-region hash from the workbench reference index.
- HIGH_STRICT_LAYOUT_OVERLAP — strict address + extent + kind + element-type + dimensions + axis-storage signature Jaccard at least 0.80 with at least 12 shared observations.
- MODERATE_STRICT_LAYOUT_OVERLAP — lower strict-layout overlap retained as a comparison lead.
- SHAPE_PROFILE_SIMILARITY_LEAD — rare/IDF-weighted address-ignored geometry similarity. This is a lead because common Nissan table shapes recur broadly across firmware.
- REPEATED_EXACT_PAYLOADS_AT_SAME_ADDRESS — repeated payload hashes at the same storage address. Useful supporting evidence, not a physical table-name transfer.

Candidate components are formed only by an exact shared code-region hash or the high strict-layout rule. Same-FID, master-ROM group, payload-only, and address-ignored shape links do not independently merge components.

A high structural match can indicate a likely code/layout lineage, but it does not transfer calibration names, units, axis meaning or vehicle function. Those require the target-side evidence standards used elsewhere in this project.

## Coverage and confidence

- FULL_GEOMETRY means per-image table-geometry observations are available from the 434-layout base set or a fresh workbench catalogue.
- SUMMARY_ONLY means scan metadata exists but no per-image geometry rows were exported. It is not proof that the ROM has no calibration objects.
- EXACT_CATALOGUE_CODE_MATCH is an exact whole-token match of a catalogue ROM code in a source filename. It does not infer a code from a partial substring.
- EXACT_IN_ECU_FID_INVENTORY is an exact FID/ECUID match to the separate ECU/FID inventory.
- EXACT_CATALOGUE_CODE_VIA_ECUID is an explicit two-step cross-reference: the scanned primary FID exactly matches an ECU/FID inventory record, and that record's ECUID exactly matches one catalogue ROM-code row. The FID and catalogue-code links remain separate records; this is not a direct equivalence between their identifier namespaces.
- PREFIX_CANDIDATE is a low-confidence lead only. Prefix matching never changes the binary FID or assigns an exact ECU identity.
- CANDIDATE_FAMILY labels are reproducible review clusters, not official firmware family designations.
- HISTORICAL_MASS_SCAN covers 14,666 result rows: 12,176 SCANNED and 2,490 LOAD_REJECTED. The row count is not the unique-input count; repeated rows and source references remain visible.
- The historical scan ledger contains 13,698 distinct input SHA-256 keys and 11,145 distinct decoded-image SHA-256 values among SCANNED rows. Image records deduplicate on decoded hash; source-result records do not.
- Input SHA-256 joins to the original inventory are grouped by hash. A hash may occur on multiple scan-result and inventory rows; the bridge records both counts and the possible pair count rather than asserting a single filename.
- Broader fid_tags fields in the historical ledger are retained as source evidence but are not promoted to primary Nissan FID values. Only the established primary-FID evidence path feeds exact ECU/FID inventory matching.

The scanner currently handles .bin, .zip, .s19, .hex and .dat containers. RAR/7z submissions must first be extracted to a supported ROM file.

## Commands

Build from existing scanner outputs:

    python tools/nissan_sh705x_workbench.py rom-index build --rom-id-crosswalk EVIDENCE/NISSAN_ROM_ID_CROSSWALK_2026-11-27.tsv --vehicle-catalog EVIDENCE/NISSAN_ROM_VEHICLE_CATALOG_2026-11-27.tsv --ecu-fid-catalog EVIDENCE/NISSAN_ECU_FID_CATALOG_2026-11-27.tsv --scan-inventory EVIDENCE/NISSAN_ROM_FAMILY_INDEX/workbench/scan_inventory.tsv --catalogue-dir EVIDENCE/NISSAN_ROM_FAMILY_INDEX/workbench/scans --dat-scan-index EVIDENCE/NISSAN_DAT_DETAILED_SCAN_INDEX_2026-11-27.tsv --base-table-objects EVIDENCE/NISSAN_BASE_TABLE_SET_2026-11-27/NISSAN_BASE_TABLE_OBJECTS_2026-11-27.tsv.gz --mass-scan-results "EVIDENCE/mass dat scan/scan_results.tsv" --mass-file-inventory "EVIDENCE/mass dat scan/file_inventory.tsv" --reference-index EVIDENCE/NISSAN_ROM_FAMILY_INDEX/workbench/rr_roms_reference_index.json --out-dir EVIDENCE/NISSAN_ROM_FAMILY_INDEX

Query by catalogue code, binary FID, or decoded-image SHA-256:

    python tools/nissan_sh705x_workbench.py rom-index query --index EVIDENCE/NISSAN_ROM_FAMILY_INDEX/nissan_rom_family_index.json --rom-code CD008
    python tools/nissan_sh705x_workbench.py rom-index query --index EVIDENCE/NISSAN_ROM_FAMILY_INDEX/nissan_rom_family_index.json --fid 2XHK19BDF1

Run a fresh folder scan, rebuild the reference index and regenerate the joined outputs:

    python tools/run_nissan_rom_family_index.py --scan-dir "EVIDENCE/rr roms" --out-dir EVIDENCE/NISSAN_ROM_FAMILY_INDEX

The GitHub Actions workflow nissan-rom-family-index.yml runs this deterministic entry point on relevant main-branch input/tool changes and commits generated outputs. Generated outputs are excluded from the workflow path filters to avoid a loop.

## Limits

- Catalogue ROM codes are not FIDs or decoded-image hashes.
- Filename code matching is conservative and can miss files with no ROM code in the filename; FID/ECUID metadata and structural links help reconcile these.
- FID reuse can cross vehicle boundaries; FID membership is not treated as family proof.
- A geometry profile can be incomplete if the scan did not emit detailed candidates. Original scan status and coverage denominator remain visible.
- The index is a corpus-navigation and analysis aid. It does not validate live-vehicle behavior or authorize donor calibration semantics or XML promotion.
