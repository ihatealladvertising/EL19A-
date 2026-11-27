# V6 first-class donor — 2026-11-27

## Result

V6 is now a first-class SH705x cross-ROM donor. The earlier 306-table result was reproduced using the historical scanner revision against the exact same decoded ROM, reconciled against the current strict scanner, and retained in the expanded 151-ROM reference index.

| Measure | Historical scanner | Current strict scanner |
|---|---:|---:|
| Helpers | 36 | 36 |
| Calls | 413 | 408 |
| Resolved calls | 391 | 386 |
| Unique table bases | 306 | 302 |

All 302 current strict candidates occur in the historical set. Four historical candidates are not re-emitted by the stricter current scanner: **0x0CE32, 0x0DACE, 0x0E57A and 0x10528**. Five historical call sites are absent from the current set: **0x44946, 0x45F04, 0x4C93A, 0x4EBBA and 0x7D52C**. The four additional candidate addresses are retained as historical-only donor leads, not promoted to current strict resolutions.

## EL19A comparison (306-candidate union)

- Exact payload matches: **832 candidate pairs**, covering **110 EL19A addresses** and **102 V6 addresses**.
- Same-geometry, different-payload comparisons: **15290 pairs**, covering **290 EL19A addresses** and **305 V6 addresses**.
- Geometry is defined by element type, dimensions and byte length. Helper-kind differences remain metadata. Identical payload/geometry variants emitted by both scanner versions are counted once.
- Canonical matcher: **124 EL19A candidate addresses** with V6 donor cross-reference hits.

These are structural donor relationships only. They do not establish semantic identity, units, conversion, calibration correctness or an EL19A target-table definition.

## A2L boundary

The candidate A2L file is EVIDENCE/side project/64811000p2_m.a2l (SHA-256 6c1248fb0acf5e80a77ff470cf8e14cda97260b291a556f330967748a7b30a88). Its ROM pairing remains **PROVISIONAL_UNVERIFIED** under WO65212. Same-address symbol overlap is recorded only as a provisional association; it is not independent proof that this A2L belongs to this HEX. No A2L names or semantics are treated as confirmed V6/EL19A truth.

## Source identity and index

- V6 input: EVIDENCE/side project/64810223F121200000.hex
- V6 container SHA-256: 8cf39f78efc67f6ae162386454c121fcc6be4771fd624150ca7c2b4102679c0a
- Decoded 1 MiB ROM SHA-256: 9d5efbd9010db790b858274b0d4f2a0d08bf47f30ee19cb93eed28d529e82039
- FID / CPU: 7V4YHZEB2 / SH705822N
- Expanded reference index: 151 ROMs, 7 XML documents, 1 provisional A2L.
- Expanded raw JSON index SHA-256: 3285f01771d4626cf4fcce287919efc4278ba20faa175a812f3fdde53a096a82
- Historical scanner revision: 1f302841b3ec5add5b3beb0644211b1375084c3d
- Current scanner source SHA-256: ec0ba0d40a7c4a444b94a123be8426584724453a394ed8e8097f3d123982532d
- Prior 150-ROM index reused without rescanning those ROMs; its raw SHA-256 was 2daba4660c89a1b2a09f51f322645d04463c20c7c2c7fee95acd0817e81f57cf.

## Correction

WO70019's zero-helper/zero-match V6 row was an input-classification error: the Intel HEX ROM was treated as an A2L source. It is superseded for this V6 input by this verified ROM scan and reconciliation.

## Preserved exports

All catalogue, per-call, per-address, full-index and comparison exports are stored beside this report as deterministic gzip files. manifest.json records raw and compressed sizes and SHA-256 digests for every file. Decompress a .gz file with standard gzip-compatible software before opening it.

Source artifacts: successful current-workbench run 46028977924 and successful deduplicated reconciliation run 46030473101 (artifact 15214012314; SHA-256 5da5b77cdafe8cf450cf52cc1b9f4471ecdae81a56ee88fb35c0147d272ca591).
