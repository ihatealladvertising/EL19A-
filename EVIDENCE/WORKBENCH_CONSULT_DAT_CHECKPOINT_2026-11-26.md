# Workbench Consult .dat Decoder / Raw-Diff Checkpoint — 2026-11-26

## Status

**Checkpointed: implementation present on main; functional results reported and independently cross-checked at algorithm/structure level; regression hardening still required.**

This is a tooling checkpoint, not an EL19A calibration finding. No calibration name, unit, scaling, or vehicle behavior is promoted by this work.

## Scope and repository state

The user authorized adding:
1. Nissan CONSULT .dat container extraction/decryption to tools/nissan_sh705x_workbench.py.
2. A raw byte/scalar-cluster fallback to diff, to expose changes not represented by helper-called lookup tables.

Current repository files:
- tools/nissan_sh705x_workbench.py — blob c5f51baebcaff6811363da8742aeabae82e2fd9b.
- tools/nissan_sh705x_workbench.md — blob 6cec001b7641a3a4e1c43a114bf14cd835b21e23.
- Decoder functions present: decrypt_consult_dat_word(), load_dat_bytes(); load_any_rom() handles direct .dat inputs and .dat members inside .zip.
- diff includes same-size raw byte-cluster comparison and --raw-limit (default 40; 0 means unlimited).
- No dedicated workbench regression-test module is present in the checked-in test set. The current CI workflow .github/workflows/sh7058-scanner-tests.yml only compiles/runs sh7058_cross_rom_scanner.py and test_sh7058_cross_rom_scanner.py; it neither tests nor triggers on changes to nissan_sh705x_workbench.py.

## Reported implementation behavior

### CONSULT .dat extraction/decryption

The implementation:
- Locates a KWP transfer-frame sequence beginning 80 15 FC (with a fixed-offset fallback at 0x43).
- Parses 0x3482 transfer records, checks each frame's trailing additive checksum, obtains a 3-byte destination address and payload length, and decrypts each 32-bit big-endian payload word using the 2-round 16-bit Feistel inverse in decrypt_consult_dat_word().
- Reconstructs a 512 KiB image padded with 0xFF where no payload is supplied.
- Routes direct .dat inputs and .dat archive members through the decoder.

### Input identities recorded in the research batch

The cross-ROM research report records these four tracked inputs (each 540,947 bytes; decoded size 524,288 bytes):
- EVIDENCE/237108W94B.dat — blob 5edd6952721340dd97474b9dff11d30c62515f5d.
- EVIDENCE/237108W95B.dat — blob d079b118b6c95617cfcb16ee813886fa11c1664f.
- EVIDENCE/23710EL58B.dat — blob 79bc1362b0e3c0ebb8bc58311d626f1149ee0bce.
- EVIDENCE/23710EL59B.dat — blob bd4ba97ca54b207d932731938a7aae7492435e34.

The research batch reports 3,836 transfer frames per file, with all frame checksums passing. Each decoded image was 512 KiB and classified as SH705519N / FID family 4CMC7NPD, with 36 helpers, 319 call sites, 313 resolved call sites and 254 unique table objects.

**Execution distinction:** the repository research report says these decoder/frame and scanner-equivalent checks were reproduced independently in JavaScript; it explicitly does not claim that the Python CLI was executed in that analysis session. Separately, the user supplied a Gemini execution summary reporting direct Python workbench scans/diffs with the same general decoder output. Treat that as an external run report until its raw logs or a reproducible local run are retained. The workbench source and documentation are committed, but the decoder is not yet covered by repository CI.

## Raw diff results reported

The updated diff path compares same-size decoded images and reports differing raw-byte clusters outside same-address table payloads already classified as changed. It formats small clusters heuristically as ASCII/u8/u16/u32 and can note nearby axes or 32-bit literal-pool references.

Reported examples:
- Sentra sentra_8U92A.bin vs NoRevHang_Sentra_8U92A.bin: 212 detected tables identical; six raw differing bytes in four clusters: 0x05AF8, 0x05B59, 0x06500–0x06501, 0x06508–0x06509.
- EM62B vs r4r42r24r2.bin: 275 detected tables identical; eight raw differing bytes at 0x10404–0x1040B.
- W94B vs W95B: 253 identical same-address table payloads and one changed UBYTE 8×1 table at 0x0AFCE–0x0AFD5; the research report also records header/signature-like raw deltas.
- EL58B vs EL59B: all 254 detected table payloads identical, with 21 raw image bytes differing in 11 clusters.

These are byte-level observations. The new fallback does not establish whether an isolated byte cluster is a calibration scalar, executable patch, checksum, signature, or metadata.

## Important validation limits

1. **No checked-in codec/parser tests.** The existing CI does not exercise the Consult decoder, malformed-frame handling, archive-wrapped .dat loading, or the raw-diff fallback.
2. **No committed golden-vector test.** The Feistel inverse has no paired forward transform or small known plaintext/ciphertext test vector in the checked-in regression suite.
3. **Frame-walk termination is permissive.** Parsing stops when the next bytes are not 80 15; trailing bytes after the last accepted frame are not validated against a known terminator/trailer layout.
4. **Start fallback is format-specific.** If the marker is not found in the first 0x200 bytes, the parser tries fixed offset 0x43. That is acceptable only for the observed file family, not a generic CONSULT .dat guarantee.
5. **Destination bounds need hardening.** The current image-size calculation does not impose a strict maximum destination extent before allocation. A malformed or unexpected address could produce an output larger than the expected 512 KiB image.
6. **Overlap/coverage checks are absent.** The parser does not report duplicate, overlapping, missing, or out-of-order transfer ranges, nor total transferred bytes or address coverage.
7. **Raw diff is intentionally heuristic.** It requires equal decoded image sizes. It masks same-address differing table extents, but does not fully classify changed table extents with changed geometry, relocated/unmatched tables, or every axis span before clustering. Such clusters must not automatically be called non-table scalar changes.

## Safe conclusion

The implementation is a useful first decoder/diff extension and the supplied results justify continuing with these CONSULT files as SH705519N donor evidence. The four .dat files are now represented in the project's structural comparison work. This does not establish EL19A compatibility or physical meanings for any changed byte/table.

## Recommended next bounded step

Add a dedicated tools/test_nissan_sh705x_workbench.py suite and include it in CI. Cover:
- Feistel inverse against a known encrypt/decrypt vector;
- synthetic valid multi-frame reconstruction and exact 512 KiB output;
- bad frame checksum, wrong service identifier, invalid payload length, truncation, address overflow, and unexpected trailing bytes;
- direct .dat and ZIP-wrapped .dat loading;
- raw-diff clusters for scalar-sized differences, changed table payloads, axis-only differences, and unequal-size skip behavior.

Then rerun the actual Python CLI on all four tracked .dat inputs and capture concise stdout, decoded-image SHA-256 values, frame counts, and scan/diff summaries. Until that passes, retain decoder status as **functional candidate / not yet regression-qualified**.

## Non-changes

This checkpoint changes no ROM, LST, A2L, XML, calibration catalogue, scope matrix, workbook, Findings record/index, active work-order assignment, or worker FIFO.
