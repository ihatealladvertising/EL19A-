from __future__ import annotations
import csv, gzip, json, hashlib, collections, statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / 'scan_results.tsv'
DETAILS = ROOT / 'scan_details.jsonl.gz'
OUT_TSV = ROOT / 'dat_detailed_431_results.tsv'
OUT_MD = ROOT / 'dat_detailed_431_summary.md'

def is_direct_dat(source: str) -> bool:
    return '!' not in source and Path(source).suffix.lower() == '.dat'

with RESULTS.open('r', encoding='utf-8-sig', newline='') as f:
    result_rows = list(csv.DictReader(f, delimiter='\t'))
refs_by_key = collections.defaultdict(list)
for row in result_rows:
    if is_direct_dat(row['source']):
        refs_by_key[row['input_key']].append(row)

details = []
with gzip.open(DETAILS, 'rt', encoding='utf-8') as f:
    for line in f:
        obj = json.loads(line)
        if obj['input_key'] in refs_by_key:
            details.append(obj)
details.sort(key=lambda x: (x.get('sources') or [''])[0].casefold())
if len(details) != 431:
    raise SystemExit(f'Expected the 431 direct-DAT detailed records; found {len(details)}')

rows = []
all_table_kinds = collections.Counter()
all_helper_kinds = collections.Counter()
all_table_types = collections.Counter()
all_table_geometries = collections.Counter()
all_helper_geometries = collections.Counter()
all_fids = collections.Counter()
primary_fids = collections.Counter()
cpu_tags = collections.Counter()
checksum = collections.defaultdict(collections.Counter)
table_address_hits = collections.Counter()
helper_address_hits = collections.Counter()
all_table_counts = []
all_helper_counts = []
all_call_counts = []
all_nontrivial = 0
all_tables = 0
all_call_associations = 0
all_unique_callpcs = 0
sum_table_bytes = 0

for d in details:
    fp = d.get('fingerprint') or {}
    hs = d.get('helpers') or {}
    ts = d.get('tables') or {}
    meta = fp.get('nissan_meta') or {}
    helper_kinds = collections.Counter((v or {}).get('kind', 'UNKNOWN') for v in hs.values())
    table_kinds = collections.Counter((v or {}).get('kind', 'UNKNOWN') for v in ts.values())
    table_types = collections.Counter((v or {}).get('elem_type', 'UNKNOWN') for v in ts.values())
    geometries = collections.Counter(f"{(v or {}).get('kind','?')}:{(v or {}).get('elem_type','?')}:{(v or {}).get('dim1','?')}x{(v or {}).get('dim2','?')}" for v in ts.values())
    hgeometries = collections.Counter(f"{(v or {}).get('kind','?')}:{(v or {}).get('elem_type','?')}:{(v or {}).get('dim1','?')}x{(v or {}).get('dim2','?')}" for v in hs.values())
    callpcs = {pc for t in ts.values() for pc in (t or {}).get('call_pcs', [])}
    call_assocs = sum(len((t or {}).get('call_pcs', [])) for t in ts.values())
    nontrivial = sum(bool((t or {}).get('nontrivial')) for t in ts.values())
    source_refs = sorted({rr['source'] for rr in refs_by_key[d['input_key']]})
    fids = fp.get('fid_tags') or []
    primary = meta.get('fid') or ''
    for fid in fids: all_fids[fid] += 1
    if primary: primary_fids[primary] += 1
    for cpu in fp.get('cpu_tags') or []: cpu_tags[cpu] += 1
    for table_addr in ts: table_address_hits[table_addr] += 1
    for helper_addr in hs: helper_address_hits[helper_addr] += 1
    for fam in ('ck_std', 'ck_alt2', 'cal16', 'main16'):
        chk = (fp.get('checksums') or {}).get(fam)
        status = (chk or {}).get('status') if isinstance(chk, dict) else None
        checksum[fam][status or 'NOT_REPORTED'] += 1
    all_helper_kinds.update(helper_kinds)
    all_table_kinds.update(table_kinds)
    all_table_types.update(table_types)
    all_table_geometries.update(geometries)
    all_helper_geometries.update(hgeometries)
    all_helper_counts.append(len(hs)); all_table_counts.append(len(ts)); all_call_counts.append(len(callpcs))
    all_nontrivial += nontrivial; all_tables += len(ts); all_call_associations += call_assocs; all_unique_callpcs += len(callpcs)
    sum_table_bytes += sum((v or {}).get('bytes', 0) for v in ts.values())
    rows.append({
        'source_files': ' ; '.join(source_refs),
        'source_file_count': len(source_refs),
        'input_key': d['input_key'],
        'payload_sha256': fp.get('sha256') or d.get('input_sha256',''),
        'rom_size_bytes': fp.get('size',''),
        'active_end': fp.get('active_end',''),
        'rom_md5': fp.get('md5',''),
        'cpu_tags': ' ; '.join(fp.get('cpu_tags') or []),
        'primary_nissan_meta_fid': primary,
        'detected_fid_tags': ' ; '.join(fids),
        'loader': meta.get('loader') or '',
        'helper_count': len(hs),
        'helper_kinds': ' ; '.join(f'{k}={v}' for k,v in sorted(helper_kinds.items())),
        'table_count': len(ts),
        'table_kinds': ' ; '.join(f'{k}={v}' for k,v in sorted(table_kinds.items())),
        'table_element_types': ' ; '.join(f'{k}={v}' for k,v in sorted(table_types.items())),
        'nontrivial_tables': nontrivial,
        'call_site_associations': call_assocs,
        'unique_call_pcs_within_input': len(callpcs),
        'table_bytes_summed_within_input': sum((v or {}).get('bytes',0) for v in ts.values()),
        'ck_std': ((fp.get('checksums') or {}).get('ck_std') or {}).get('status','') if isinstance((fp.get('checksums') or {}).get('ck_std'),dict) else '',
        'ck_alt2': ((fp.get('checksums') or {}).get('ck_alt2') or {}).get('status','') if isinstance((fp.get('checksums') or {}).get('ck_alt2'),dict) else '',
        'cal16': ((fp.get('checksums') or {}).get('cal16') or {}).get('status','') if isinstance((fp.get('checksums') or {}).get('cal16'),dict) else '',
        'main16': ((fp.get('checksums') or {}).get('main16') or {}).get('status','') if isinstance((fp.get('checksums') or {}).get('main16'),dict) else '',
        'helper_addresses': ' ; '.join(sorted(hs)),
        'table_addresses': ' ; '.join(sorted(ts)),
    })

fields = list(rows[0].keys())
with OUT_TSV.open('w', encoding='utf-8', newline='') as f:
    w = csv.DictWriter(f, fieldnames=fields, delimiter='\t', lineterminator='\n')
    w.writeheader(); w.writerows(rows)

# Unique direct-DAT payload scan statuses, not source-reference row totals.
dat_unique = {k: refs[0] for k, refs in refs_by_key.items()}
status_counts = collections.Counter(r['status'] for r in dat_unique.values())
rejects = collections.Counter(r['error'] for r in dat_unique.values() if r['status'] == 'LOAD_REJECTED')
size_counts = collections.Counter(str((d.get('fingerprint') or {}).get('size','')) for d in details)
# Per-ROM checksum status and structural distributions.
checks = {fam: checksum[fam] for fam in ('ck_std','ck_alt2','cal16','main16')}
# Highlight detected token groups while distinguishing them from stronger nissan_meta FID field.
top_fid_tokens = all_fids.most_common(12)
top_primary_fids = primary_fids.most_common(15)
top_table_inputs = sorted(rows, key=lambda x: (-int(x['table_count']),-int(x['helper_count']),x['source_files']))[:15]
top_call_inputs = sorted(rows, key=lambda x: (-int(x['unique_call_pcs_within_input']),-int(x['call_site_associations']),x['source_files']))[:10]
unique_table_addr_count = len(table_address_hits)
unique_helper_addr_count = len(helper_address_hits)
repeated_table_addrs = table_address_hits.most_common(15)

with OUT_MD.open('w', encoding='utf-8', newline='\n') as f:
    f.write('# Detailed SH705x Workbench Summary — 431 Direct `.dat` Results\n\n')
    f.write('**Work order:** REPROPROGRAMMING-BATCH-2026-11-27 (closed)  \n')
    f.write('**Input folder:** `E:\\Nissan Consult\\ReproProgramming`  \n')
    f.write('**Workbench revision:** `13acc0b58826c2b693ef495a0b3c61259daec760`  \n')
    f.write('**Runtime:** Python 3.12.10; py7zr 1.1.4  \n')
    f.write('**Source result:** `scan_results.tsv` joined to the 431 records in `scan_details.jsonl.gz` using the deduplicated `input_key`.\n\n')
    f.write('## Executive result\n\n')
    f.write(f"The folder contained **11,740 direct `.dat` source references**, representing **{len(dat_unique):,} unique `.dat` payloads** after byte-identical deduplication. Of these, **{status_counts['SCANNED']:,}** loaded as ROM candidates and were scanned; **{status_counts['LOAD_REJECTED']:,}** were rejected by the loader. **431 unique scanned `.dat` payloads** produced non-empty helper, call-site, and table detail records. The other **{status_counts['SCANNED']-431:,} successfully loaded `.dat` payloads** had no detailed helper/table record in this run.\n\n")
    f.write('The 431 are **ROM snapshots with static discovery output**, not 431 newly identified EL19A calibrations. Table counts recur across related ROM revisions; they are per-input detections and must not be summed as unique project-wide calibration objects. FID strings are recorded as detected metadata/tokens, not as independently authenticated vehicle identities.\n\n')
    f.write('## Coverage and scan outcomes\n\n')
    f.write('| Measure | Result |\n|---|---:|\n')
    f.write(f'| Direct `.dat` source references | 11,740 |\n| Unique direct `.dat` payloads | {len(dat_unique):,} |\n| Unique payloads scanned | {status_counts["SCANNED"]:,} |\n| Unique payloads rejected | {status_counts["LOAD_REJECTED"]:,} |\n| Detailed positive payloads | {len(details):,} |\n| Source paths represented among detailed payloads | {sum(int(x["source_file_count"]) for x in rows):,} |\n| ROM images represented among detailed payloads (512 KiB) | {size_counts["524288"]:,} |\n| ROM images represented among detailed payloads (1 MiB) | {size_counts["1048576"]:,} |\n')
    f.write('\n### Frequent loader rejection messages\n\n')
    f.write('These are loader outcomes, not proof that every rejected file is corrupt. The loader may not recognize a Consult container or may correctly classify a partial calibration payload as not being a full ECU image.\n\n| Rejection message | Unique payloads |\n|---|---:|\n')
    for msg,n in rejects.most_common(12):
        f.write(f'| {msg.replace("|", "\\|")} | {n:,} |\n')
    f.write('\n## What the 431 detailed inputs contain\n\n')
    f.write(f'- **Helper detections:** {sum(all_helper_counts):,} total across per-ROM snapshots; median {statistics.median(all_helper_counts):.0f} per input; range {min(all_helper_counts)}–{max(all_helper_counts)}.\n')
    f.write(f'- **Table detections:** {all_tables:,} total across snapshots, of which **{all_nontrivial:,}** were marked non-trivial by the workbench. Median {statistics.median(all_table_counts):.0f} tables per input; range {min(all_table_counts)}–{max(all_table_counts)}.\n')
    f.write(f'- **Call-site/table associations:** {all_call_associations:,} summed associations. There were {all_unique_callpcs:,} unique call PCs when counted separately within each input (the same code PC can recur in related snapshots).\n')
    f.write(f'- **Address recurrence:** {unique_helper_addr_count:,} distinct helper addresses and {unique_table_addr_count:,} distinct table addresses across the 431 snapshots. The most repeated table placements are listed below.\n')
    f.write(f'- **Summed table extents:** {sum_table_bytes:,} bytes over per-ROM detections; this intentionally counts repeated addresses in different ROM snapshots.\n\n')
    f.write('### Helper discovery kinds\n\n| Kind | Per-ROM detections across 431 inputs |\n|---|---:|\n')
    for k,n in all_helper_kinds.most_common(): f.write(f'| {k} | {n:,} |\n')
    f.write('\n### Table discovery kinds\n\n| Kind | Per-ROM detections across 431 inputs |\n|---|---:|\n')
    for k,n in all_table_kinds.most_common(): f.write(f'| {k} | {n:,} |\n')
    f.write('\n### Table element types and common geometries\n\n| Element type | Detections |\n|---|---:|\n')
    for k,n in all_table_types.most_common(): f.write(f'| {k} | {n:,} |\n')
    f.write('\n| Kind / element type / geometry | Detections |\n|---|---:|\n')
    for k,n in all_table_geometries.most_common(25): f.write(f'| {k} | {n:,} |\n')
    f.write('\n## FID and CPU metadata\n\n')
    f.write('### Primary FID field from the workbench fingerprint metadata\n\n| FID | Inputs |\n|---|---:|\n')
    for k,n in top_primary_fids: f.write(f'| {k} | {n:,} |\n')
    if not top_primary_fids: f.write('| No primary FID populated | 431 |\n')
    f.write('\n### Most common detected FID tokens\n\nThe token matcher can find incidental strings; treat these as search leads unless supported by the fingerprint metadata and source provenance.\n\n| Token | Inputs carrying token |\n|---|---:|\n')
    for k,n in top_fid_tokens: f.write(f'| {k} | {n:,} |\n')
    f.write('\n### CPU tags\n\n| CPU tag | Inputs |\n|---|---:|\n')
    for k,n in cpu_tags.most_common(15): f.write(f'| {k} | {n:,} |\n')
    f.write('\n## Checksum metadata status\n\n')
    f.write('Counts below are across the 431 detailed inputs. `NOT_REPORTED` means no status was included in the fingerprint output; it does not mean failure.\n\n| Checksum family | Status | Inputs |\n|---|---|---:|\n')
    for fam in ('ck_std','ck_alt2','cal16','main16'):
        for status,n in checks[fam].most_common(): f.write(f'| {fam} | {status} | {n:,} |\n')
    f.write('\n## Highest-detail input snapshots\n\nTable counts are per snapshot; matching addresses in different revisions are repeated.\n\n| Source file(s) | Primary FID | ROM bytes | Helpers | Calls | Tables | Non-trivial tables | SHA-256 |\n|---|---|---:|---:|---:|---:|---:|---|\n')
    for x in top_table_inputs:
        f.write(f"| {x['source_files'].replace('|','\\|')} | {x['primary_nissan_meta_fid'] or '—'} | {x['rom_size_bytes']} | {x['helper_count']} | {x['unique_call_pcs_within_input']} | {x['table_count']} | {x['nontrivial_tables']} | `{x['payload_sha256']}` |\n")
    f.write('\n## Most frequently recurring table addresses\n\n| Address | Number of detailed snapshots containing address |\n|---|---:|\n')
    for addr,n in repeated_table_addrs: f.write(f'| `{addr}` | {n:,} |\n')
    f.write('\n## Interpretation and limits\n\n')
    f.write('- The workbench used fingerprinting, helper discovery, call extraction, and table summarization. The report does **not** establish table names, units, conversions, query-axis meaning, ECU application, or vehicle behavior.\n')
    f.write('- Repeated detections across related images are useful for revision-family comparison but are not independent semantic confirmation. A positive table detection says the workbench found a structural candidate in that image.\n')
    f.write('- Several detected geometries use implicit or helper-derived axes. Their output is a structural lead; axis orientation and physical meaning require target-side confirmation for the ROM being defined.\n')
    f.write('- The 431 detailed payloads were selected by non-empty workbench helper/table results. This is a detailed subset of the `.dat` batch, not a separate validation set.\n')
    f.write('- No source ROM or `.dat` file was modified; this summary and its TSV are additive run outputs.\n\n')
    f.write('## Companion data and provenance\n\n')
    f.write('- `dat_detailed_431_results.tsv` contains one row per unique detailed `.dat` payload, with source path(s), full payload SHA-256, CPU/FID metadata, checksum outcomes, helper/table kinds, counts, addresses, and call-PC summaries.\n')
    f.write('- `scan_details.jsonl.gz` retains all 431 detailed JSON records.\n')
    f.write('- `scan_results.tsv` retains loader status and per-source-reference outcomes for the full batch.\n')
    f.write('- Batch manifest: `run_manifest.json`.\n')

# Record hashes and row-level structural verification.
with OUT_TSV.open('rb') as f: tsv_sha=hashlib.sha256(f.read()).hexdigest()
with OUT_MD.open('rb') as f: md_sha=hashlib.sha256(f.read()).hexdigest()
with OUT_TSV.open('r',encoding='utf-8',newline='') as f: tsv_rows=list(csv.DictReader(f,delimiter='\t'))
if len(tsv_rows)!=431: raise SystemExit(f'Output TSV row verification failed: {len(tsv_rows)}')
print(json.dumps({'summary':str(OUT_MD),'summary_bytes':OUT_MD.stat().st_size,'summary_sha256':md_sha,'detail_tsv':str(OUT_TSV),'detail_tsv_data_rows':len(tsv_rows),'detail_tsv_bytes':OUT_TSV.stat().st_size,'detail_tsv_sha256':tsv_sha,'source_detail_records':len(details),'direct_dat_unique':len(dat_unique),'unique_status':status_counts,'helper_detections':sum(all_helper_counts),'table_detections':all_tables,'nontrivial_tables':all_nontrivial,'call_site_associations':all_call_associations,'unique_call_pcs_within_inputs':all_unique_callpcs,'helper_kinds':all_helper_kinds,'table_kinds':all_table_kinds,'primary_fids':top_primary_fids,'top_fid_tokens':top_fid_tokens,'table_geometries':all_table_geometries.most_common(15),'check_statuses':{k:dict(v) for k,v in checks.items()}},indent=2))
