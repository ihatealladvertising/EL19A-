# Workbench census — reported results intake (2026-11-27)

**Status:** PRESERVED REPORTED RESULTS — NOT YET INDEPENDENTLY REPRODUCED FROM PINNED INPUTS  
**Origin:** User-provided summary of a full tools/nissan_sh705x_workbench.py run across EVIDENCE/, received 2026-11-27.  
**Purpose:** Preserve all reported results as durable research leads and regression targets. This intake is not a substitute for raw JSON/TSV/manifest, source-container hashes, decoded-ROM hashes, command line, stdout/stderr or tool commit. Follow-on WOs must pin these artifacts and independently reproduce the claims before promotion.

## 1. Consult %6 family — J10 MR20DE / SH705520N

Four Consult %6 files previously rejected as unsupported 86 10 00 reportedly decode as 512 KiB SH705520N ROMs, identify as LOADER40, and pass ck_std.

- E1BR20E (2WD MT) vs E1BR50E (4WD MT), same FID 9CMCVAPD31: 265 tables; 263 identical; only differing tables at 0x0A58E and 0x0A67E, both 2D_IMPL 8×1 uint16.
- Outside table payloads, 46 bytes differ in 19 clusters, including checksum words, a pool32-referenced array and mirrored scalar pairs.
- E1BR20E vs E1BT40A (2WD CVT), same FID: 230 identical tables; 35 differing tables spanning 3,232 bytes.
- E1JD81D, FID 4CMCB1PDM1: 253 tables; exact payload overlap reported as 145 with E1BR20E, 61 with EE310 (MR18DE MT), and 50 with EL19A.

**Boundary:** decoder success and payload overlap do not establish cross-model semantic equivalence. The 2WD/4WD pair is a controlled variant fixture; non-table differences need classification.

## 2. Tiida C12W 3DD9A and S19 twin

- C12W 3DD9A is reported byte-identical to 9APCTDEM06.s19 (SH705828N, FID 0KHDCFDZ7).
- Zero differing bytes across complete bootblock, unpopulated gap and executable code region.
- main16 checksum passes.
- 581/581 caller-backed tables and 351 axes align 1:1 with RFCC_2XHK19BDF1.a2l.
- 463 identical payloads and 118 calibrated differences spanning 7,170 bytes.
- A2L donor metadata is structural only, not target-side proof of semantic names, units or conversions.
- 3DD9A reportedly contains valid production cal16 at 0x08200.

**Boundary:** the BIN/S19 pair is a strong independent-container fixture. A2L alignment is a structural test corpus, not authorization to transfer semantics.

## 3. EL19A cross-generation donor conservation / missing XML coverage

Across 15 valid SH705x donor families:
- 146/183 (80%) of EL19A non-trivial caller-backed tables reportedly conserved byte-for-byte in at least one non-C11 donor.
- All 15/15 non-trivial EL19A tables absent from CALIBRATIONS/EL19A_release1_conservative.xml reportedly have exact-payload donor matches; 12/15 are outside EL13A/8W83B.

### Reciprocal pair
- 0x0DE6E ↔ 0x0E2ED: reciprocal 2D_AXIS 16×1 U8 objects.
- Exact payload conservation reported across seven ROM families: EL13A, 8W83B, EE310, EL58B/8W94B, E1BR20E, Qashqai 2 MiB and Juke06.
- V6/Juke A2L structure and payload leads converge on donor candidates mPIADVAT/mADVPIAT.

### Variant-sensitive trio
- 0x10CC2, 0x12A4E, 0x12D18: 2D_AXIS 16×1 U16.
- Reportedly differ in EL13A/8W83B but match EL58B at 0x0CE98 and Juke06 at 0x16454.
- 0x0CE98 is among 25 differing tables between 8W94B and EL58B.

### Qashqai / CF48D
- Qashqai 2 MiB 1TRKH1HN6: 482 tables; 68 non-trivial payloads reportedly match EL19A, and 41 match in 3DD9A/Juke06.
- CF48D.bin + XML: FID 6ZV5UN11, checksum OK, 278 tables.
- CF48D reportedly shares 30 non-trivial payloads with EL19A, including missing-XML table 0x0F536 at 0x0C374.
- EL19A tables 0x1100A, 0x1104A, 0x12C7E, 0x12CBE match CF48D XML Throttle Flow Potential pairs.

**Boundary:** exact payload conservation supports structural correspondence only. Do not transfer donor names, units, scaling, conversions, axes or physical meanings without EL19A reader/caller/consumer evidence. Preserve variant-sensitive differences.

## 4. Revision-pair and checksum/container triage

### Sentra 8U92A
- 8U92A vs NoRevHang_Sentra_8U92A.bin.
- verify_checksums() reportedly confirms 0x06500 xort and 0x06508 sumt are ck_std.
- Two non-table scalar changes: 0x05AF8 44→104; 0x05B59 10→170.
- All 211 tables unchanged.

### Consult DATs
- 12 DATs (EM60B..67A and 8W94B/8W95B/EL58B/EL59B) reportedly decode and pass ck_alt2, cal16 and main16.
- r4r42r24r2.bin fails ck_alt2 and main16; only reported delta is eight bytes at 0x10404..0x1040B.

### Container triage
- D9_* and 310364* identified as Hitachi TCM %8019 DAT.
- e1bc11b/e1bc12b and 237103ZM1E..4A excluded as different cipher/architecture.
- 8201032726.dat identified as partial KWP.
- EM43A*.OsirisROM, Renault OLS zip and url.bin PNG excluded.

**Boundary:** checksum status is per algorithm and image/container. A pass under one checksum is not a blanket integrity verdict. Isolate the eight-byte discrepancy; do not repair it.

## 5. Cross-cutting evidence requirements

Every follow-on output must retain, where available: original filename/path and source-container SHA-256; decoded ROM SHA-256, size, processor, FID, loader and decoder/version provenance; checksum algorithm, stored/computed values and result; table address, storage, dimensions, axis addresses, payload SHA-256 and donor/target identity; exact differing ranges; reader evidence separately from donor metadata; source command, tool commit, manifest, stdout/stderr and exit code.

Unknown hashes or absent raw exports must be marked NOT SUPPLIED / NOT VERIFIED, never inferred. Inputs remain read-only. No ROM patching, checksum repair, calibration XML edits, workbook edits or tool-source changes are authorized by this intake.

## 6. Follow-on work orders

- WO70026 — EL19A donor-conservation reconciliation and Findings promotion (Worker 3).
- WO70027 — C12W BIN/S19 twin and A2L structural fixture (Worker 1).
- WO70028 — Consult %6 decoder/variant regression fixtures (Worker 2).
- WO70029 — checksum, revision-pair and container-triage reconciliation (Worker 3).

All follow-on WOs must read this intake and pin exact source/output artifacts before treating reported figures as reproduced.
