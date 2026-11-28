from __future__ import annotations
import argparse
import collections
import csv
import gzip
import hashlib
import itertools
import json
import math
import os
import re
import statistics
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple
SCHEMA = 'nissan-rom-family-index-v1'
PROFILE_SCHEMA = 'nissan-rom-structural-profile-v1'

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def read_tsv(path: Optional[Path]) -> List[Dict[str, str]]:
    if not path:
        return []
    with path.open('r', encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream, delimiter='\t'))

def write_tsv(path: Path, fields: Sequence[str], rows: Iterable[Sequence[Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.writer(stream, delimiter='\t', lineterminator='\n')
        writer.writerow(fields)
        for row in rows:
            writer.writerow(['' if value is None else value for value in row])

def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')

def norm_code(value: str) -> str:
    return re.sub('[^A-Z0-9]', '', (value or '').upper())

def parse_int(value: Any) -> Optional[int]:
    if value is None or value == '':
        return None
    try:
        return int(str(value), 0)
    except ValueError:
        try:
            return int(str(value))
        except ValueError:
            return None

def parse_string_list(value: Any) -> List[str]:
    """Parse JSON string/list fields, including a JSON string nested inside a CSV field."""
    if value is None or value == '':
        return []
    current = value
    for _ in range(2):
        if not isinstance(current, str):
            break
        try:
            parsed = json.loads(current)
        except (TypeError, ValueError):
            break
        if isinstance(parsed, list):
            return [str(item).strip() for item in parsed if str(item).strip()]
        if isinstance(parsed, str):
            current = parsed
            continue
        return []
    if isinstance(current, (tuple, set)):
        return [str(item).strip() for item in current if str(item).strip()]
    if isinstance(current, str):
        return [item.strip() for item in re.split('[;,]', current) if item.strip()]
    return []

def image_key(sha: str, fallback: str='') -> str:
    return 'ROMIMG:' + (sha[:16].lower() if sha else hashlib.sha256(fallback.encode()).hexdigest()[:16])

def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))

def iter_catalogues(catalogue_dir: Optional[Path]) -> Iterable[Tuple[Path, dict, dict]]:
    if not catalogue_dir or not catalogue_dir.exists():
        return
    for manifest_path in sorted(catalogue_dir.rglob('*.manifest.json')):
        try:
            manifest = load_json(manifest_path)
            inp = manifest.get('input', {})
            outputs = manifest.get('outputs', [])
            cat_path = None
            for output in outputs:
                op = str(output.get('path', ''))
                if op.endswith('.catalogue.json'):
                    candidate = catalogue_dir / Path(op).name
                    if candidate.exists():
                        cat_path = candidate
                        break
            if cat_path is None:
                candidate = manifest_path.with_name(manifest_path.name.replace('.manifest.json', '.catalogue.json'))
                if candidate.exists():
                    cat_path = candidate
            if cat_path:
                yield (manifest_path, manifest, load_json(cat_path))
        except (OSError, ValueError, json.JSONDecodeError):
            continue

def geometry_rows_from_catalogue(doc: dict) -> List[dict]:
    rows: List[dict] = []
    for candidate in doc.get('candidates', []):
        base = parse_int(candidate.get('base', candidate.get('ea')))
        variants = candidate.get('geometry_variants') or []
        if not variants and candidate.get('spans'):
            for span in candidate.get('spans', []):
                variants.append({'byte_length': span.get('byte_length'), 'dim1': candidate.get('dim1'), 'dim2': candidate.get('dim2'), 'element_type': span.get('element_type'), 'element_width_bytes': span.get('element_width_bytes'), 'helper_kind': candidate.get('kind'), 'end_exclusive': span.get('end_exclusive'), 'payload_sha256': span.get('sha256')})
        axis1s = candidate.get('axis1_variants') or []
        axis2s = candidate.get('axis2_variants') or []
        axis1 = axis1s[0].get('type', '') if axis1s else candidate.get('axis1_type', '')
        axis2 = axis2s[0].get('type', '') if axis2s else candidate.get('axis2_type', '')
        for variant in variants:
            width = parse_int(variant.get('element_width_bytes'))
            if width is None:
                et = str(variant.get('element_type', ''))
                width = {'uint8': 1, 'int8': 1, 'uint16': 2, 'int16': 2, 'uint32': 4, 'int32': 4}.get(et)
            length = parse_int(variant.get('byte_length'))
            end = parse_int(variant.get('end_exclusive'))
            rows.append({'address': base, 'end_exclusive': end if end is not None else base + length if base is not None and length is not None else None, 'byte_length': length, 'kind': variant.get('helper_kind', candidate.get('helper_kind', '')), 'element_type': variant.get('element_type', ''), 'element_width_bytes': width, 'byte_order': ('big_endian' if width and width > 1 else ('byte' if width == 1 else 'unknown')), 'dim1': parse_int(variant.get('dim1')), 'dim2': parse_int(variant.get('dim2')), 'axis1_storage_type': axis1, 'axis2_storage_type': axis2, 'payload_sha256': variant.get('payload_sha256', ''), 'geometry_conflict': bool(candidate.get('geometry_conflict')), 'axis_conflict': bool(candidate.get('axis1_conflict') or candidate.get('axis2_conflict')), 'source': 'scanner_catalogue'})
    return [r for r in rows if r['address'] is not None and r['byte_length'] is not None]

def geometry_rows_from_base(path: Optional[Path]) -> Iterable[Tuple[str, str, dict]]:
    if not path or not path.exists():
        return
    opener = gzip.open if path.suffix.lower() == ".gz" else open
    with opener(path, "rt", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        # Exact column names emitted by build_nissan_base_table_set.py.
        required = {"image_id", "rom_sha256", "address", "table_kind", "extent_bytes", "element_type", "element_width_bytes", "dim1", "dim2"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError("Base table object file missing columns: " + ", ".join(sorted(missing)))
        for raw in reader:
            addr = parse_int(raw.get("address"))
            extent = parse_int(raw.get("extent_bytes"))
            end = parse_int(raw.get("end_exclusive"))
            if end is None and addr is not None and extent is not None:
                end = addr + extent
            row = {"address": addr, "end_exclusive": end, "byte_length": extent, "kind": raw.get("table_kind", ""), "element_type": raw.get("element_type", ""), "element_width_bytes": parse_int(raw.get("element_width_bytes")), "byte_order": raw.get("byte_order", ""), "dim1": parse_int(raw.get("dim1")), "dim2": parse_int(raw.get("dim2")), "axis1_storage_type": raw.get("axis1_storage_type", ""), "axis2_storage_type": raw.get("axis2_storage_type", ""), "payload_sha256": raw.get("payload_sha256", ""), "geometry_conflict": False, "axis_conflict": False, "source": "base_table_set", "source_path": raw.get("source_file", ""), "primary_fid": raw.get("primary_fid", ""), "cpu": raw.get("cpu", ""), "rom_size": parse_int(raw.get("rom_size_bytes"))}
            yield (raw.get("rom_sha256", ""), raw.get("image_id", ""), row)

def multiset_jaccard(a: collections.Counter, b: collections.Counter) -> float:
    if not a and (not b):
        return 1.0
    inter = sum((a & b).values())
    union = sum((a | b).values())
    return inter / union if union else 1.0

def build_index(args: argparse.Namespace) -> dict:
    crosswalk_rows = read_tsv(Path(args.rom_id_crosswalk))
    vehicle_rows = read_tsv(Path(args.vehicle_catalog)) if getattr(args, 'vehicle_catalog', None) else []
    ecu_fid_rows = read_tsv(Path(args.ecu_fid_catalog)) if getattr(args, 'ecu_fid_catalog', None) else []
    scan_rows = read_tsv(Path(args.scan_inventory)) if getattr(args, 'scan_inventory', None) else []
    dat_rows = read_tsv(Path(args.dat_scan_index)) if getattr(args, 'dat_scan_index', None) else []
    mass_scan_rows = read_tsv(Path(args.mass_scan_results)) if getattr(args, 'mass_scan_results', None) else []
    original_inventory_rows = read_tsv(Path(args.mass_file_inventory)) if getattr(args, 'mass_file_inventory', None) else []
    inventory_by_sha: Dict[str, List[dict]] = collections.defaultdict(list)
    for inventory_row in original_inventory_rows:
        inventory_sha = (inventory_row.get('sha256') or '').strip().lower()
        if inventory_sha:
            inventory_by_sha[inventory_sha].append(inventory_row)
    code_by_norm: Dict[str, dict] = {}
    for row in crosswalk_rows:
        code = norm_code(row.get('ROM_ID_Normalized', row.get('ROM_ID_AsListed', '')))
        if not code:
            continue
        if code in code_by_norm:
            raise ValueError(f'Duplicate normalized ROM ID in crosswalk: {code}')
        code_by_norm[code] = row
    images: Dict[str, dict] = {}
    scan_sources: List[dict] = []
    source_count_by_sha = collections.Counter()

    def add_image(sha: str, fallback: str='') -> dict:
        key = image_key(sha, fallback)
        if key not in images:
            images[key] = {'image_id': key, 'decoded_rom_sha256': (sha or '').lower(), 'rom_size_bytes': '', 'cpu_tags': set(), 'fid_values': set(), 'loader_values': set(), 'source_paths': set(), 'scan_datasets': set(), 'helper_count': None, 'call_count': None, 'resolved_calls': None, 'table_count': None, 'nontrivial_table_count': None, 'checksum_summary': set(), 'table_rows': []}
        source_count_by_sha[images[key]['decoded_rom_sha256']] += 1
        return images[key]
    for row in scan_rows:
        status = (row.get('status') or row.get('Status') or '').upper()
        sha = row.get('decoded_rom_sha256', row.get('DecodedROMSHA256', ''))
        filename = row.get('filename', row.get('Filename', ''))
        source_path = row.get('path', row.get('SourcePath', filename))
        if status not in ('SCAN_OK', 'DECODED_IMAGE_DUPLICATE', 'EXACT_CONTAINER_DUPLICATE') or not sha:
            scan_sources.append({'dataset': 'workbench_scan', 'source_path': source_path, 'filename': filename, 'scan_status': status or 'UNKNOWN', 'decoded_rom_sha256': sha, 'container_sha256': row.get('container_sha256', row.get('ContainerSHA256', '')), 'image_id': '', 'error': row.get('error', row.get('Error', ''))})
            continue
        image = add_image(sha, source_path)
        key = image['image_id']
        image['rom_size_bytes'] = row.get('decoded_size', row.get('DecodedSize', image['rom_size_bytes'])) or image['rom_size_bytes']
        cpu = row.get('cpu', row.get('fid_cpu', row.get('CPU', '')))
        if cpu:
            image['cpu_tags'].update((x.strip() for x in re.split('[;,]', cpu) if x.strip()))
        fid = row.get('fid', row.get('PrimaryNissanMetadataFID', ''))
        if fid:
            image['fid_values'].add(fid.strip().upper())
        loader = row.get('loader', row.get('Loader', ''))
        if loader:
            image['loader_values'].add(loader.strip())
        image['source_paths'].add(source_path)
        image['scan_datasets'].add('rr_roms_workbench')
        image['helper_count'] = parse_int(row.get('helper_count', row.get('HelperCount')))
        image['call_count'] = parse_int(row.get('call_sites', row.get('CallSites')))
        image['resolved_calls'] = parse_int(row.get('resolved_calls', row.get('ResolvedCalls')))
        image['table_count'] = parse_int(row.get('unique_tables', row.get('UniqueTables', row.get('table_count', row.get('TableCount')))))
        scan_sources.append({'dataset': 'workbench_scan', 'source_path': source_path, 'filename': filename, 'scan_status': status, 'decoded_rom_sha256': sha, 'container_sha256': row.get('container_sha256', row.get('ContainerSHA256', '')), 'image_id': key, 'error': row.get('error', '')})
    for row in dat_rows:
        sha = row.get('PayloadSHA256', '')
        source_path = row.get('SourceFile', '')
        if not sha:
            continue
        image = add_image(sha, source_path)
        key = image['image_id']
        image['rom_size_bytes'] = row.get('ROMSizeBytes', image['rom_size_bytes']) or image['rom_size_bytes']
        cpu = row.get('CPU', '')
        if cpu:
            image['cpu_tags'].add(cpu)
        fid = row.get('PrimaryNissanMetadataFID', '')
        if fid:
            image['fid_values'].add(fid.strip().upper())
        image['source_paths'].add(source_path)
        image['scan_datasets'].add('direct_dat_431')
        image['helper_count'] = max(image['helper_count'] or 0, parse_int(row.get('HelperCount')) or 0)
        image['call_count'] = max(image['call_count'] or 0, parse_int(row.get('CallSiteAssociations')) or 0)
        image['resolved_calls'] = max(image['resolved_calls'] or 0, parse_int(row.get('UniqueCallPCs')) or 0)
        image['table_count'] = max(image['table_count'] or 0, parse_int(row.get('TableCount')) or 0)
        image['nontrivial_table_count'] = max(image['nontrivial_table_count'] or 0, parse_int(row.get('NontrivialTableCount')) or 0)
        image['checksum_summary'].update((f'{k}={v}' for k, v in row.items() if k.startswith('Checksum_') and v))
        scan_sources.append({'dataset': 'direct_dat_431', 'source_path': source_path, 'filename': source_path, 'scan_status': 'DETAILED_POSITIVE', 'decoded_rom_sha256': sha, 'container_sha256': row.get('PayloadKey', ''), 'image_id': key, 'error': ''})
    detailed_dat_sha = {(row.get('PayloadSHA256') or '').strip().lower() for row in dat_rows if row.get('PayloadSHA256')}
    mass_rows_by_input_sha: Dict[str, List[dict]] = collections.defaultdict(list)
    for row in mass_scan_rows:
        input_sha = (row.get('input_sha256') or '').strip().lower()
        if input_sha:
            mass_rows_by_input_sha[input_sha].append(row)
        status = (row.get('status') or '').upper()
        decoded_sha = (row.get('decoded_rom_sha256') or '').strip().lower()
        source_path = row.get('source', '')
        inventory_matches = inventory_by_sha.get(input_sha, [])
        image_id = ''
        if status == 'SCANNED' and decoded_sha:
            image = add_image(decoded_sha, source_path)
            image_id = image['image_id']
            image['rom_size_bytes'] = row.get('rom_size_bytes', image['rom_size_bytes']) or image['rom_size_bytes']
            image['cpu_tags'].update(parse_string_list(row.get('cpu_tags', '')))
            image['loader_values'].add(row.get('loader', '').strip()) if row.get('loader', '').strip() else None
            image['source_paths'].add(source_path) if source_path else None
            image['source_paths'].update((item.get('relative', '') for item in inventory_matches if item.get('relative')))
            image['scan_datasets'].add('historical_mass_scan')
            image['helper_count'] = max(image['helper_count'] or 0, parse_int(row.get('helpers')) or 0)
            image['call_count'] = max(image['call_count'] or 0, parse_int(row.get('call_sites')) or 0)
            image['resolved_calls'] = max(image['resolved_calls'] or 0, parse_int(row.get('resolved_calls')) or 0)
            image['table_count'] = max(image['table_count'] or 0, parse_int(row.get('unique_tables')) or 0)
        scan_sources.append({
            'dataset': 'historical_mass_scan',
            'source_path': source_path,
            'filename': Path(source_path).name if source_path else '',
            'scan_status': status or 'UNKNOWN',
            'decoded_rom_sha256': decoded_sha,
            'container_sha256': input_sha,
            'image_id': image_id,
            'error': row.get('error', ''),
            'input_key': row.get('input_key', ''),
            'codec': row.get('codec', ''),
            'source_count': row.get('source_count', ''),
            'file_inventory_match_count': len(inventory_matches),
            'file_inventory_paths': ';'.join(sorted({item.get('relative', '') for item in inventory_matches if item.get('relative')})),
            'file_inventory_classifications': ';'.join(sorted({item.get('classification', '') for item in inventory_matches if item.get('classification')})),
            'rom_size_bytes': row.get('rom_size_bytes', ''),
            'cpu_tags': row.get('cpu_tags', ''),
            'fid_tags': row.get('fid_tags', ''),
            'loader': row.get('loader', ''),
            'helpers': row.get('helpers', ''),
            'helper_kinds': row.get('helper_kinds', ''),
            'call_sites': row.get('call_sites', ''),
            'resolved_calls': row.get('resolved_calls', ''),
            'unique_tables': row.get('unique_tables', ''),
            'detailed_positive_431_match': 'YES' if decoded_sha and decoded_sha in detailed_dat_sha else 'NO'
        })
    mass_hash_link_rows = []
    for input_sha in sorted(set(mass_rows_by_input_sha) | set(inventory_by_sha)):
        scan_matches = mass_rows_by_input_sha.get(input_sha, [])
        inventory_matches = inventory_by_sha.get(input_sha, [])
        decoded_hashes = sorted({(row.get('decoded_rom_sha256') or '').lower() for row in scan_matches if row.get('decoded_rom_sha256')})
        mass_hash_link_rows.append({
            'input_sha256': input_sha,
            'join_status': 'EXACT_SHA256_MATCH' if scan_matches and inventory_matches else ('MASS_SCAN_ONLY' if scan_matches else 'INVENTORY_ONLY'),
            'scan_result_row_count': len(scan_matches),
            'scan_input_keys': ';'.join(sorted({row.get('input_key', '') for row in scan_matches if row.get('input_key')})),
            'scan_codecs': ';'.join(sorted({row.get('codec', '') for row in scan_matches if row.get('codec')})),
            'scan_statuses': ';'.join(sorted({row.get('status', '') for row in scan_matches if row.get('status')})),
            'scan_source_references': ';'.join(sorted({row.get('source', '') for row in scan_matches if row.get('source')})),
            'decoded_rom_sha256s': ';'.join(decoded_hashes),
            'image_ids': ';'.join(sorted({image_key(sha) for sha in decoded_hashes})),
            'file_inventory_row_count': len(inventory_matches),
            'file_inventory_paths': ';'.join(sorted({row.get('relative', '') for row in inventory_matches if row.get('relative')})),
            'file_inventory_classifications': ';'.join(sorted({row.get('classification', '') for row in inventory_matches if row.get('classification')})),
            'sha256_pair_count': len(scan_matches) * len(inventory_matches)
        })
    base_rows_by_image: Dict[str, List[dict]] = collections.defaultdict(list)
    base_count = 0
    if getattr(args, 'base_table_objects', None):
        base_path = Path(args.base_table_objects)
        for sha, source_iid, row in geometry_rows_from_base(base_path):
            image = add_image(sha, source_iid)
            image['source_paths'].add('base_table_set:' + source_iid)
            if row.get('source_path'):
                image['source_paths'].add(row['source_path'])
            image['scan_datasets'].add('base_table_set_434')
            if row.get('primary_fid'):
                image['fid_values'].add(row['primary_fid'].upper())
            if row.get('cpu'):
                image['cpu_tags'].add(row['cpu'])
            if row.get('rom_size'):
                image['rom_size_bytes'] = str(row['rom_size'])
            base_rows_by_image[image['image_id']].append(row)
            base_count += 1
    catalogue_files = 0
    for manifest_path, manifest, doc in iter_catalogues(Path(args.catalogue_dir) if getattr(args, 'catalogue_dir', None) else None):
        inp = manifest.get('input', {})
        sha = inp.get('decoded_rom_sha256', '')
        source_path = inp.get('path', manifest_path.name)
        if not sha:
            continue
        image = add_image(sha, source_path)
        key = image['image_id']
        image['source_paths'].add(source_path)
        image['scan_datasets'].add('workbench_structural_catalogue')
        meta = doc.get('manifest', {}).get('summary', {}) or {}
        if meta:
            image['helper_count'] = max(image['helper_count'] or 0, parse_int(meta.get('helper_count')) or 0)
            image['call_count'] = max(image['call_count'] or 0, parse_int(meta.get('call_count')) or 0)
            image['resolved_calls'] = max(image['resolved_calls'] or 0, parse_int(meta.get('resolved_call_count')) or 0)
            image['table_count'] = max(image['table_count'] or 0, parse_int(meta.get('unique_resolved_table_bases')) or 0)
        if key not in base_rows_by_image:
            image['table_rows'].extend(geometry_rows_from_catalogue(doc))
        catalogue_files += 1
    fid_by_norm: Dict[str, List[dict]] = collections.defaultdict(list)
    for row in ecu_fid_rows:
        for key_name in ('FID', 'ECUID'):
            value = norm_code(row.get(key_name, ''))
            if value:
                fid_by_norm[value].append({'namespace': key_name, 'record': row})
    code_patterns = [(code, re.compile('(?<![A-Z0-9])' + re.escape(code) + '(?![A-Z0-9])', re.I)) for code in sorted(code_by_norm, key=len, reverse=True)]
    identifiers: List[dict] = []
    for image in images.values():
        matched_codes: Dict[str, set] = collections.defaultdict(set)
        for source_path in image['source_paths']:
            basename = Path(source_path).name.upper()
            for code, pattern in code_patterns:
                if pattern.search(basename):
                    matched_codes[code].add(source_path)
        for code, paths in sorted(matched_codes.items()):
            row = code_by_norm[code]
            identifiers.append({'image_id': image['image_id'], 'identifier_namespace': 'UPREV_ROM_CODE', 'identifier': row.get('ROM_ID_AsListed', code), 'normalized_identifier': code, 'link_basis': 'exact_filename_token', 'link_status': 'EXACT_CATALOGUE_CODE_MATCH', 'match_confidence': 'HIGH_FOR_CODE_TOKEN', 'master_rom_id': row.get('MasterROM_ID', ''), 'is_master_rom': row.get('IsMasterROM', ''), 'model': row.get('Model', ''), 'make': row.get('Make', ''), 'vehicle_year': row.get('VehicleYear', ''), 'engine_code': row.get('EngineCode', ''), 'transmission': row.get('Transmission', ''), 'source_line': row.get('SourceLine', ''), 'source_paths': ';'.join(sorted(paths))})
        for fid in sorted(image['fid_values']):
            f_norm = norm_code(fid)
            exact = fid_by_norm.get(f_norm, [])
            if exact:
                for hit in exact:
                    r = hit['record']
                    identifiers.append({'image_id': image['image_id'], 'identifier_namespace': 'NISSAN_' + hit['namespace'], 'identifier': fid, 'normalized_identifier': f_norm, 'link_basis': 'exact_fid_or_ecuid', 'link_status': 'EXACT_IN_ECU_FID_INVENTORY', 'match_confidence': 'EXACT_IDENTIFIER', 'master_rom_id': '', 'is_master_rom': '', 'model': r.get('Model', ''), 'make': 'Nissan', 'vehicle_year': r.get('YearText', ''), 'engine_code': r.get('EngineText', ''), 'transmission': '', 'source_line': r.get('SourceLine', ''), 'source_paths': ';'.join(sorted(image['source_paths']))})
                    ecuid = norm_code(r.get('ECUID', '')) if hit['namespace'] == 'FID' else ''
                    if ecuid and ecuid in code_by_norm:
                        code_row = code_by_norm[ecuid]
                        identifiers.append({'image_id': image['image_id'], 'identifier_namespace': 'UPREV_ROM_CODE', 'identifier': code_row.get('ROM_ID_AsListed', ecuid), 'normalized_identifier': ecuid, 'link_basis': 'exact_ecuid_to_catalogue_code_via_fid_inventory', 'link_status': 'EXACT_CATALOGUE_CODE_VIA_ECUID', 'match_confidence': 'EXACT_ECUID_CROSSWALK', 'master_rom_id': code_row.get('MasterROM_ID', ''), 'is_master_rom': code_row.get('IsMasterROM', ''), 'model': code_row.get('Model', ''), 'make': code_row.get('Make', ''), 'vehicle_year': code_row.get('VehicleYear', ''), 'engine_code': code_row.get('EngineCode', ''), 'transmission': code_row.get('Transmission', ''), 'source_line': code_row.get('SourceLine', ''), 'source_paths': ';'.join(sorted(image['source_paths']))})
            else:
                prefix_hits = []
                for candidate, hits in fid_by_norm.items():
                    if min(len(candidate), len(f_norm)) >= 8 and (candidate.startswith(f_norm) or f_norm.startswith(candidate)):
                        prefix_hits.extend(((candidate, hit) for hit in hits))
                for candidate, hit in prefix_hits:
                    r = hit['record']
                    identifiers.append({'image_id': image['image_id'], 'identifier_namespace': 'NISSAN_' + hit['namespace'], 'identifier': fid, 'normalized_identifier': f_norm, 'link_basis': 'prefix_candidate_not_identity', 'link_status': 'PREFIX_CANDIDATE', 'match_confidence': 'LOW_UNCONFIRMED', 'master_rom_id': '', 'is_master_rom': '', 'model': r.get('Model', ''), 'make': 'Nissan', 'vehicle_year': r.get('YearText', ''), 'engine_code': r.get('EngineText', ''), 'transmission': '', 'source_line': r.get('SourceLine', ''), 'source_paths': ';'.join(sorted(image['source_paths']))})
    profiles: Dict[str, dict] = {}
    for iid, image in images.items():
        # Prefer the fresh current-workbench catalogue when present; fall back to
        # the pinned 434-layout base set for images without a fresh detailed catalogue.
        rows = list(image['table_rows']) or list(base_rows_by_image.get(iid, []))
        if rows:
            if image['table_count'] is None:
                image['table_count'] = len(rows)
            if image['nontrivial_table_count'] is None:
                image['nontrivial_table_count'] = sum((str(r.get('nontrivial', '')).lower() in ('1', 'true', 'yes') for r in rows))
            if image['helper_count'] is None:
                helpers = {x for r in rows for x in str(r.get('helper_addresses', '')).split(';') if x}
                image['helper_count'] = len(helpers)
            if image['call_count'] is None:
                pcs = {x for r in rows for x in str(r.get('call_pcs', '')).split(';') if x}
                image['call_count'] = len(pcs)
            if image['resolved_calls'] is None:
                image['resolved_calls'] = image['call_count']
        strict = collections.Counter()
        geometry = collections.Counter()
        payloads = collections.defaultdict(set)
        payload_hashes = set()
        for row in rows:
            address = parse_int(row.get('address'))
            length = parse_int(row.get('byte_length'))
            kind = str(row.get('kind', ''))
            etype = str(row.get('element_type', ''))
            width = parse_int(row.get('element_width_bytes'))
            dim1 = parse_int(row.get('dim1'))
            dim2 = parse_int(row.get('dim2'))
            ax1 = str(row.get('axis1_storage_type', ''))
            ax2 = str(row.get('axis2_storage_type', ''))
            byte_order = str(row.get('byte_order', 'unknown'))
            sig_geometry = (kind, etype, width, byte_order, dim1, dim2, ax1, ax2)
            sig_strict = (address, length, *sig_geometry)
            geometry[sig_geometry] += 1
            strict[sig_strict] += 1
            ph = str(row.get('payload_sha256', ''))
            if ph:
                payload_hashes.add(ph)
                payloads[ph].add(address)
        unique_shapes = len(geometry)
        profiles[iid] = {'image_id': iid, 'decoded_rom_sha256': image['decoded_rom_sha256'], 'cpu_tags': sorted(image['cpu_tags']), 'fid_values': sorted(image['fid_values']), 'rom_size_bytes': image['rom_size_bytes'], 'source_paths': sorted(image['source_paths']), 'scan_datasets': sorted(image['scan_datasets']), 'profile_basis': 'FULL_GEOMETRY' if rows else 'SUMMARY_ONLY', 'structural_observation_count': sum(strict.values()), 'unique_geometry_signatures': unique_shapes, 'strict_signature_count': len(strict), 'payload_hash_count': len(payload_hashes), 'strict_counter': strict, 'geometry_counter': geometry, 'payload_hashes': payload_hashes, 'payload_addresses': payloads, 'table_kinds': collections.Counter((str(r.get('kind', '')) for r in rows)), 'helper_count': image['helper_count'], 'call_count': image['call_count'], 'resolved_calls': image['resolved_calls'], 'table_count': image['table_count'], 'nontrivial_table_count': image['nontrivial_table_count']}
    code_hashes_by_sha: Dict[str, set] = collections.defaultdict(set)
    if getattr(args, 'reference_index', None):
        ref = load_json(Path(args.reference_index))
        for code_hash, entries in ref.get('lookups', {}).get('code_hash_index', {}).items():
            for entry in entries:
                sha = entry.get('decoded_rom_sha256', '').lower()
                if sha:
                    code_hashes_by_sha[sha].add(code_hash)
    full_ids = [iid for iid, p in profiles.items() if p['profile_basis'] == 'FULL_GEOMETRY']
    shape_document_frequency = collections.Counter()
    for iid in full_ids:
        shape_document_frequency.update(set(profiles[iid]['geometry_counter']))
    profile_count = max(1, len(full_ids))

    def rare_geometry_jaccard(ca: collections.Counter, cb: collections.Counter) -> Tuple[float, float]:
        weighted_intersection = 0.0
        weighted_union = 0.0
        for sig in set(ca) | set(cb):
            df = shape_document_frequency.get(sig, 0)
            weight = math.log((profile_count + 1) / (df + 1))
            weighted_intersection += min(ca.get(sig, 0), cb.get(sig, 0)) * weight
            weighted_union += max(ca.get(sig, 0), cb.get(sig, 0)) * weight
        return (weighted_intersection / weighted_union if weighted_union else 0.0, weighted_intersection)
    metadata_by_image: Dict[str, dict] = {}
    for iid in images:
        linked = [r for r in identifiers if r['image_id'] == iid and r['link_status'] in ('EXACT_CATALOGUE_CODE_MATCH', 'EXACT_CATALOGUE_CODE_VIA_ECUID')]
        linked += [r for r in identifiers if r['image_id'] == iid and r['identifier_namespace'].startswith('NISSAN_') and (r['link_status'] == 'EXACT_IN_ECU_FID_INVENTORY')]
        metadata_by_image[iid] = {'models': sorted({r['model'] for r in linked if r['model']}), 'years': sorted({r['vehicle_year'] for r in linked if r['vehicle_year']}), 'engines': sorted({r['engine_code'] for r in linked if r['engine_code']}), 'transmissions': sorted({r['transmission'] for r in linked if r['transmission']})}
    candidate_pairs: Dict[Tuple[str, str], dict] = {}
    for a_id, b_id in itertools.combinations(sorted(full_ids), 2):
        a, b = (profiles[a_id], profiles[b_id])
        strict_j = multiset_jaccard(a['strict_counter'], b['strict_counter'])
        geom_j = multiset_jaccard(a['geometry_counter'], b['geometry_counter'])
        rare_geom_j, rare_geom_common = rare_geometry_jaccard(a['geometry_counter'], b['geometry_counter'])
        shared_payloads = a['payload_hashes'] & b['payload_hashes']
        shared_payload_same_addr = sum((bool(a['payload_addresses'].get(h, set()) & b['payload_addresses'].get(h, set())) for h in shared_payloads))
        code_shared = code_hashes_by_sha.get(a['decoded_rom_sha256'], set()) & code_hashes_by_sha.get(b['decoded_rom_sha256'], set())
        strict_common = sum((a['strict_counter'] & b['strict_counter']).values())
        geometry_common = sum((a['geometry_counter'] & b['geometry_counter']).values())
        reasons = []
        if code_shared:
            reasons.append('IDENTICAL_CODE_REGION_HASH')
        if strict_j >= 0.8 and strict_common >= 12:
            reasons.append('HIGH_STRICT_LAYOUT_OVERLAP')
        if rare_geom_j >= 0.8 and rare_geom_common >= 8:
            reasons.append('SHAPE_PROFILE_SIMILARITY_LEAD')
        elif strict_j >= 0.3 and strict_common >= 20:
            reasons.append('MODERATE_STRICT_LAYOUT_OVERLAP')
        if shared_payload_same_addr >= 12:
            reasons.append('REPEATED_EXACT_PAYLOADS_AT_SAME_ADDRESS')
        if not reasons:
            continue
        score = min(1.0, 0.45 * strict_j + 0.35 * geom_j + (0.2 if code_shared else 0.0))
        candidate_pairs[a_id, b_id] = {'image_a': a_id, 'image_b': b_id, 'relationship_types': ';'.join(reasons), 'relationship_score': round(score, 6), 'strict_layout_jaccard': round(strict_j, 6), 'geometry_multiset_jaccard': round(geom_j, 6), 'rare_geometry_weighted_jaccard': round(rare_geom_j, 6), 'rare_geometry_weighted_common': round(rare_geom_common, 6), 'strict_common_observations': strict_common, 'geometry_common_observations': geometry_common, 'shared_payload_hashes': len(shared_payloads), 'shared_payloads_same_address': shared_payload_same_addr, 'shared_code_region_hashes': len(code_shared), 'common_code_hashes': ';'.join(sorted(code_shared)), 'rom_size_a': a['rom_size_bytes'], 'rom_size_b': b['rom_size_bytes'], 'cpu_a': ';'.join(a['cpu_tags']), 'cpu_b': ';'.join(b['cpu_tags']), 'fid_a': ';'.join(a['fid_values']), 'fid_b': ';'.join(b['fid_values']), 'models_a': ';'.join(metadata_by_image[a_id]['models']), 'models_b': ';'.join(metadata_by_image[b_id]['models']), 'years_a': ';'.join(metadata_by_image[a_id]['years']), 'years_b': ';'.join(metadata_by_image[b_id]['years']), 'engines_a': ';'.join(metadata_by_image[a_id]['engines']), 'engines_b': ';'.join(metadata_by_image[b_id]['engines']), 'transmissions_a': ';'.join(metadata_by_image[a_id]['transmissions']), 'transmissions_b': ';'.join(metadata_by_image[b_id]['transmissions']), 'evidence_boundary': 'STRUCTURAL_FAMILY_CANDIDATE_NOT_SEMANTIC_OR_ECU_IDENTITY'}
    by_fid: Dict[str, List[str]] = collections.defaultdict(list)
    for iid, profile in profiles.items():
        for fid in profile['fid_values']:
            by_fid[fid].append(iid)
    for fid, ids in by_fid.items():
        for a_id, b_id in itertools.combinations(sorted(set(ids)), 2):
            pair = (a_id, b_id)
            if pair in candidate_pairs:
                candidate_pairs[pair]['relationship_types'] += ';SAME_PRIMARY_FID_GROUP'
            else:
                a, b = (profiles[a_id], profiles[b_id])
                candidate_pairs[pair] = {'image_a': a_id, 'image_b': b_id, 'relationship_types': 'SAME_PRIMARY_FID_GROUP', 'relationship_score': 0.0, 'strict_layout_jaccard': '', 'geometry_multiset_jaccard': '', 'strict_common_observations': 0, 'geometry_common_observations': 0, 'rare_geometry_weighted_jaccard': '', 'rare_geometry_weighted_common': 0, 'shared_payload_hashes': 0, 'shared_payloads_same_address': 0, 'shared_code_region_hashes': 0, 'common_code_hashes': '', 'rom_size_a': a['rom_size_bytes'], 'rom_size_b': b['rom_size_bytes'], 'cpu_a': ';'.join(a['cpu_tags']), 'cpu_b': ';'.join(b['cpu_tags']), 'fid_a': fid, 'fid_b': fid, 'models_a': ';'.join(metadata_by_image[a_id]['models']), 'models_b': ';'.join(metadata_by_image[b_id]['models']), 'years_a': ';'.join(metadata_by_image[a_id]['years']), 'years_b': ';'.join(metadata_by_image[b_id]['years']), 'engines_a': ';'.join(metadata_by_image[a_id]['engines']), 'engines_b': ';'.join(metadata_by_image[b_id]['engines']), 'transmissions_a': ';'.join(metadata_by_image[a_id]['transmissions']), 'transmissions_b': ';'.join(metadata_by_image[b_id]['transmissions']), 'evidence_boundary': 'FID_GROUP_ONLY_STRUCTURAL_OR_PHYSICAL_IDENTITY_NOT_ESTABLISHED'}
    relationships = sorted(candidate_pairs.values(), key=lambda r: (-float(r['relationship_score']), -int(r['shared_payload_hashes']), r['image_a'], r['image_b']))
    parent = {iid: iid for iid in images}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        ra, rb = (find(a), find(b))
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)
    for rel in relationships:
        kinds = rel['relationship_types']
        strict_j = float(rel['strict_layout_jaccard'] or 0)
        if 'IDENTICAL_CODE_REGION_HASH' in kinds or (strict_j >= 0.8 and int(rel['strict_common_observations']) >= 12):
            union(rel['image_a'], rel['image_b'])
    groups: Dict[str, List[str]] = collections.defaultdict(list)
    for iid in images:
        groups[find(iid)].append(iid)
    components = []
    component_by_image = {}
    for root, members in sorted(groups.items()):
        if len(members) < 2:
            continue
        cid = 'CANDIDATE_FAMILY:' + hashlib.sha256('|'.join(sorted(members)).encode()).hexdigest()[:12]
        for iid in members:
            component_by_image[iid] = cid
        components.append({'candidate_component_id': cid, 'image_count': len(members), 'image_ids': ';'.join(sorted(members)), 'status': 'STRICT_LAYOUT_CANDIDATE_COMPONENT_NOT_VERIFIED_FAMILY'})
    by_master_rom: Dict[str, List[str]] = collections.defaultdict(list)
    for identifier in identifiers:
        master_id = norm_code(identifier.get('master_rom_id', ''))
        if identifier.get('identifier_namespace') == 'UPREV_ROM_CODE' and identifier.get('link_status') in ('EXACT_CATALOGUE_CODE_MATCH', 'EXACT_CATALOGUE_CODE_VIA_ECUID') and master_id:
            by_master_rom[master_id].append(identifier['image_id'])
    for master_id, ids in by_master_rom.items():
        for a_id, b_id in itertools.combinations(sorted(set(ids)), 2):
            pair = (a_id, b_id)
            if pair in candidate_pairs:
                if 'CATALOGUE_MASTER_ROM_GROUP' not in candidate_pairs[pair]['relationship_types']:
                    candidate_pairs[pair]['relationship_types'] += ';CATALOGUE_MASTER_ROM_GROUP'
            else:
                a, b = (profiles[a_id], profiles[b_id])
                candidate_pairs[pair] = {'image_a': a_id, 'image_b': b_id, 'relationship_types': 'CATALOGUE_MASTER_ROM_GROUP', 'relationship_score': 0.0, 'strict_layout_jaccard': '', 'geometry_multiset_jaccard': '', 'rare_geometry_weighted_jaccard': '', 'rare_geometry_weighted_common': 0, 'strict_common_observations': 0, 'geometry_common_observations': 0, 'shared_payload_hashes': 0, 'shared_payloads_same_address': 0, 'shared_code_region_hashes': 0, 'common_code_hashes': '', 'rom_size_a': a['rom_size_bytes'], 'rom_size_b': b['rom_size_bytes'], 'cpu_a': ';'.join(a['cpu_tags']), 'cpu_b': ';'.join(b['cpu_tags']), 'fid_a': ';'.join(a['fid_values']), 'fid_b': ';'.join(b['fid_values']), 'models_a': ';'.join(metadata_by_image[a_id]['models']), 'models_b': ';'.join(metadata_by_image[b_id]['models']), 'years_a': ';'.join(metadata_by_image[a_id]['years']), 'years_b': ';'.join(metadata_by_image[b_id]['years']), 'engines_a': ';'.join(metadata_by_image[a_id]['engines']), 'engines_b': ';'.join(metadata_by_image[b_id]['engines']), 'transmissions_a': ';'.join(metadata_by_image[a_id]['transmissions']), 'transmissions_b': ';'.join(metadata_by_image[b_id]['transmissions']), 'evidence_boundary': 'CATALOGUE_MASTER_ROM_GROUP_ONLY_NOT_STRUCTURAL_FAMILY_PROOF'}
    relationships = sorted(candidate_pairs.values(), key=lambda r: (-float(r['relationship_score']), -int(r['shared_payload_hashes']), r['image_a'], r['image_b']))
    group_members: Dict[Tuple[str, str], List[dict]] = collections.defaultdict(list)
    for row in crosswalk_rows:
        group_members[str(row.get('SourceLine', '')), norm_code(row.get('MasterROM_ID', ''))].append(row)
    master_group_rows = []
    for (source_line, master_id), members in sorted(group_members.items()):
        master_rows = [r for r in members if str(r.get('IsMasterROM', '')).upper() == 'YES']
        anchor = master_rows[0] if master_rows else members[0]
        master_group_rows.append({'master_group_id': f'UPREV_MASTER_GROUP:{source_line}:{master_id}', 'master_rom_id': anchor.get('MasterROM_ID', master_id), 'model': anchor.get('Model', ''), 'make': anchor.get('Make', ''), 'vehicle_year': anchor.get('VehicleYear', ''), 'engine_code': anchor.get('EngineCode', ''), 'transmission': anchor.get('Transmission', ''), 'rom_code_count': len(members), 'rom_codes': ';'.join(sorted({r.get('ROM_ID_AsListed', '') for r in members})), 'master_flagged_code_count': len(master_rows), 'source_line': source_line, 'source_url': anchor.get('SourceURL', '')})
    image_rows = []
    for iid, img in sorted(images.items()):
        profile = profiles[iid]
        exact_codes = [r for r in identifiers if r['image_id'] == iid and r['identifier_namespace'] == 'UPREV_ROM_CODE' and (r['link_status'] in ('EXACT_CATALOGUE_CODE_MATCH', 'EXACT_CATALOGUE_CODE_VIA_ECUID'))]
        exact_fids = [r for r in identifiers if r['image_id'] == iid and r['identifier_namespace'].startswith('NISSAN_') and (r['link_status'] == 'EXACT_IN_ECU_FID_INVENTORY')]
        years = sorted({r['vehicle_year'] for r in exact_codes if r['vehicle_year']})
        image_rows.append([iid, img['decoded_rom_sha256'], img['rom_size_bytes'], ';'.join(sorted(img['cpu_tags'])), ';'.join(sorted(img['fid_values'])), ';'.join(sorted(img['loader_values'])), ';'.join(sorted(img['scan_datasets'])), len(img['source_paths']), ';'.join(sorted(img['source_paths'])), len({r['normalized_identifier'] for r in exact_codes}), len(exact_fids), ';'.join(sorted({r['identifier'] for r in exact_codes})), ';'.join(sorted({r['master_rom_id'] for r in exact_codes if r['master_rom_id']})), ';'.join(sorted({r['is_master_rom'] for r in exact_codes if r['is_master_rom']})), ';'.join(years), profile['profile_basis'], profile['structural_observation_count'], profile['unique_geometry_signatures'], profile['helper_count'], profile['call_count'], profile['resolved_calls'], profile['table_count'], profile['nontrivial_table_count'], component_by_image.get(iid, '')])
    profile_rows = []
    for iid, p in sorted(profiles.items()):
        profile_rows.append([iid, p['decoded_rom_sha256'], p['profile_basis'], p['rom_size_bytes'], ';'.join(p['cpu_tags']), ';'.join(p['fid_values']), p['structural_observation_count'], p['unique_geometry_signatures'], p['strict_signature_count'], p['payload_hash_count'], json.dumps(dict(sorted(p['table_kinds'].items())), sort_keys=True), p['helper_count'], p['call_count'], p['resolved_calls'], p['table_count'], p['nontrivial_table_count'], component_by_image.get(iid, ''), ';'.join(p['scan_datasets']), ';'.join(p['source_paths'])])
    generation = collections.defaultdict(lambda: {'images': set(), 'full': set(), 'summary': set(), 'observations': 0, 'tables': []})
    for ident in identifiers:
        if ident['link_status'] not in ('EXACT_CATALOGUE_CODE_MATCH', 'EXACT_CATALOGUE_CODE_VIA_ECUID', 'EXACT_IN_ECU_FID_INVENTORY'):
            continue
        basis = 'UPREV_ROM_CODE' if ident['identifier_namespace'] == 'UPREV_ROM_CODE' else 'ECU_FID_INVENTORY'
        key = (basis, ident.get('make', ''), ident.get('model', ''), ident.get('vehicle_year', ''), ident.get('engine_code', ''), ident.get('transmission', ''))
        iid = ident['image_id']
        generation[key]['images'].add(iid)
        if profiles[iid]['profile_basis'] == 'FULL_GEOMETRY':
            generation[key]['full'].add(iid)
            generation[key]['observations'] += profiles[iid]['structural_observation_count']
        else:
            generation[key]['summary'].add(iid)
        if profiles[iid]['table_count'] is not None:
            generation[key]['tables'].append(profiles[iid]['table_count'])
    generation_rows = []
    for key, values in sorted(generation.items()):
        basis, make, model, year, engine, trans = key
        vals = values['tables']
        generation_rows.append([basis, make, model, year, engine, trans, len(values['images']), len(values['full']), len(values['summary']), values['observations'], min(vals) if vals else '', round(statistics.median(vals), 2) if vals else '', max(vals) if vals else ''])
    ident_fields = ['image_id', 'identifier_namespace', 'identifier', 'normalized_identifier', 'link_basis', 'link_status', 'match_confidence', 'master_rom_id', 'is_master_rom', 'model', 'make', 'vehicle_year', 'engine_code', 'transmission', 'source_line', 'source_paths']
    ident_rows = [[r.get(k, '') for k in ident_fields] for r in identifiers]
    scan_fields = ['dataset', 'source_path', 'filename', 'scan_status', 'decoded_rom_sha256', 'container_sha256', 'image_id', 'error', 'input_key', 'codec', 'source_count', 'file_inventory_match_count', 'file_inventory_paths', 'file_inventory_classifications', 'rom_size_bytes', 'cpu_tags', 'fid_tags', 'loader', 'helpers', 'helper_kinds', 'call_sites', 'resolved_calls', 'unique_tables', 'detailed_positive_431_match']
    scan_out_rows = [[r.get(k, '') for k in scan_fields] for r in scan_sources]
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    write_tsv(out / 'nissan_master_rom_code_index.tsv', list(crosswalk_rows[0].keys()) if crosswalk_rows else [], ([r.get(k, '') for k in crosswalk_rows[0].keys()] for r in crosswalk_rows) if crosswalk_rows else [])
    group_fields = ['master_group_id', 'master_rom_id', 'model', 'make', 'vehicle_year', 'engine_code', 'transmission', 'rom_code_count', 'rom_codes', 'master_flagged_code_count', 'source_line', 'source_url']
    write_tsv(out / 'nissan_master_rom_groups.tsv', group_fields, ([g.get(k, '') for k in group_fields] for g in master_group_rows))
    write_tsv(out / 'nissan_rom_image_index.tsv', ['image_id', 'decoded_rom_sha256', 'rom_size_bytes', 'cpu_tags', 'nissan_fid_values', 'loader_values', 'scan_datasets', 'source_count', 'source_paths', 'exact_catalogue_code_links', 'exact_fid_inventory_links', 'observed_rom_codes', 'master_rom_groups', 'master_status_values', 'catalogue_vehicle_years', 'profile_basis', 'structural_observation_count', 'unique_geometry_signatures', 'helper_count', 'call_count', 'resolved_calls', 'table_count', 'nontrivial_table_count', 'candidate_component_id'], image_rows)
    write_tsv(out / 'nissan_rom_scan_sources.tsv', scan_fields, scan_out_rows)
    mass_result_fields = list(mass_scan_rows[0].keys()) if mass_scan_rows else ['input_key', 'codec', 'input_sha256', 'source', 'source_count', 'status', 'decoded_rom_sha256', 'rom_size_bytes', 'cpu_tags', 'fid_tags', 'loader', 'helpers', 'helper_kinds', 'call_sites', 'resolved_calls', 'unique_tables', 'error']
    mass_result_fields += ['image_id', 'detailed_positive_431_match', 'file_inventory_match_count', 'file_inventory_paths', 'file_inventory_classifications']
    mass_result_out = []
    for row in mass_scan_rows:
        input_sha = (row.get('input_sha256') or '').strip().lower()
        decoded_sha = (row.get('decoded_rom_sha256') or '').strip().lower()
        matches = inventory_by_sha.get(input_sha, [])
        values = dict(row)
        values.update({
            'image_id': image_key(decoded_sha, row.get('source', '')) if row.get('status') == 'SCANNED' and decoded_sha else '',
            'detailed_positive_431_match': 'YES' if decoded_sha and decoded_sha in detailed_dat_sha else 'NO',
            'file_inventory_match_count': len(matches),
            'file_inventory_paths': ';'.join(sorted({item.get('relative', '') for item in matches if item.get('relative')})),
            'file_inventory_classifications': ';'.join(sorted({item.get('classification', '') for item in matches if item.get('classification')}))
        })
        mass_result_out.append([values.get(key, '') for key in mass_result_fields])
    write_tsv(out / 'nissan_historical_mass_scan_results.tsv', mass_result_fields, mass_result_out)
    inventory_fields = list(original_inventory_rows[0].keys()) if original_inventory_rows else ['relative', 'extension', 'size_bytes', 'sha256', 'classification']
    write_tsv(out / 'nissan_original_file_inventory.tsv', inventory_fields, ([row.get(key, '') for key in inventory_fields] for row in original_inventory_rows))
    mass_link_fields = ['input_sha256', 'join_status', 'scan_result_row_count', 'scan_input_keys', 'scan_codecs', 'scan_statuses', 'scan_source_references', 'decoded_rom_sha256s', 'image_ids', 'file_inventory_row_count', 'file_inventory_paths', 'file_inventory_classifications', 'sha256_pair_count']
    write_tsv(out / 'nissan_mass_scan_input_hash_links.tsv', mass_link_fields, ([row.get(key, '') for key in mass_link_fields] for row in mass_hash_link_rows))
    write_tsv(out / 'nissan_rom_identifier_links.tsv', ident_fields, ident_rows)
    write_tsv(out / 'nissan_rom_structural_profiles.tsv', ['image_id', 'decoded_rom_sha256', 'profile_basis', 'rom_size_bytes', 'cpu_tags', 'nissan_fid_values', 'structural_observation_count', 'unique_geometry_signatures', 'strict_signature_count', 'payload_hash_count', 'table_kind_counts_json', 'helper_count', 'call_count', 'resolved_calls', 'table_count', 'nontrivial_table_count', 'candidate_component_id', 'scan_datasets', 'source_paths'], profile_rows)
    write_tsv(out / 'nissan_rom_generation_summary.tsv', ['metadata_basis', 'make', 'model', 'vehicle_year', 'engine_code', 'transmission', 'unique_images', 'full_geometry_images', 'summary_only_images', 'structural_observations', 'min_scanned_table_count', 'median_scanned_table_count', 'max_scanned_table_count'], generation_rows)
    rel_fields = list(relationships[0].keys()) if relationships else ['image_a', 'image_b', 'relationship_types', 'relationship_score', 'strict_layout_jaccard', 'geometry_multiset_jaccard', 'rare_geometry_weighted_jaccard', 'rare_geometry_weighted_common', 'strict_common_observations', 'geometry_common_observations', 'shared_payload_hashes', 'shared_payloads_same_address', 'shared_code_region_hashes', 'common_code_hashes', 'rom_size_a', 'rom_size_b', 'cpu_a', 'cpu_b', 'fid_a', 'fid_b', 'models_a', 'models_b', 'years_a', 'years_b', 'engines_a', 'engines_b', 'transmissions_a', 'transmissions_b', 'evidence_boundary']
    write_tsv(out / 'nissan_rom_family_relationships.tsv', rel_fields, ([r.get(k, '') for k in rel_fields] for r in relationships))
    write_tsv(out / 'nissan_rom_candidate_components.tsv', ['candidate_component_id', 'image_count', 'image_ids', 'status'], ([r[k] for k in ('candidate_component_id', 'image_count', 'image_ids', 'status')] for r in components))
    source_paths = [getattr(args, 'rom_id_crosswalk', None), getattr(args, 'vehicle_catalog', None), getattr(args, 'ecu_fid_catalog', None), getattr(args, 'scan_inventory', None), getattr(args, 'dat_scan_index', None), getattr(args, 'base_table_objects', None), getattr(args, 'reference_index', None), getattr(args, 'mass_scan_results', None), getattr(args, 'mass_file_inventory', None)]
    inputs = {}
    for p in source_paths:
        if p:
            pp = Path(p)
            if pp.exists():
                inputs[str(pp)] = {'sha256': sha256_file(pp), 'bytes': pp.stat().st_size}
    mass_status_counts = collections.Counter((row.get('status') or 'UNKNOWN').upper() for row in mass_scan_rows)
    inventory_class_counts = collections.Counter((row.get('classification') or 'UNKNOWN') for row in original_inventory_rows)
    mass_scanned_rows = [row for row in mass_scan_rows if (row.get('status') or '').upper() == 'SCANNED']
    mass_decoded_hashes = {(row.get('decoded_rom_sha256') or '').strip().lower() for row in mass_scanned_rows if row.get('decoded_rom_sha256')}
    matched_mass_rows = [row for row in mass_scan_rows if (row.get('input_sha256') or '').strip().lower() in inventory_by_sha]
    mass_scan_hash_groups = len(mass_rows_by_input_sha)
    inventory_sha_rows = [row for row in original_inventory_rows if (row.get('sha256') or '').strip()]
    exact_hash_groups = sum((1 for sha in mass_rows_by_input_sha if sha in inventory_by_sha))
    exact_hash_pair_count = sum((len(mass_rows_by_input_sha[sha]) * len(inventory_by_sha[sha]) for sha in mass_rows_by_input_sha if sha in inventory_by_sha))
    summary = {'schema': SCHEMA, 'profile_schema': PROFILE_SCHEMA, 'master_rom_code_rows': len(crosswalk_rows), 'master_rom_groups': len(master_group_rows), 'master_rom_ids': len(code_by_norm), 'master_flagged_rows': sum((r.get('IsMasterROM', '') == 'YES' for r in crosswalk_rows)), 'vehicle_catalog_rows': len(vehicle_rows), 'ecu_fid_inventory_rows': len(ecu_fid_rows), 'scan_inventory_rows': len(scan_rows), 'direct_dat_detailed_rows': len(dat_rows), 'historical_mass_scan_result_rows': len(mass_scan_rows), 'historical_mass_scan_unique_input_hashes': mass_scan_hash_groups, 'historical_mass_scan_status_counts': dict(sorted(mass_status_counts.items())), 'historical_mass_scan_scanned_rows': mass_status_counts.get('SCANNED', 0), 'historical_mass_scan_load_rejected_rows': mass_status_counts.get('LOAD_REJECTED', 0), 'historical_mass_scan_unique_decoded_images': len(mass_decoded_hashes), 'historical_mass_scan_detailed_positive_match_rows': sum((1 for row in mass_scan_rows if (row.get('decoded_rom_sha256') or '').strip().lower() in detailed_dat_sha and (row.get('status') or '').upper() == 'SCANNED')), 'historical_mass_scan_exact_file_sha_match_result_rows': len(matched_mass_rows), 'historical_mass_scan_unmatched_input_sha256_groups': sum((1 for sha in mass_rows_by_input_sha if sha not in inventory_by_sha)), 'historical_mass_scan_unmatched_file_sha_result_rows': len(mass_scan_rows) - len(matched_mass_rows), 'original_file_inventory_rows': len(original_inventory_rows), 'original_file_inventory_class_counts': dict(sorted(inventory_class_counts.items())), 'original_file_inventory_rows_with_sha256': len(inventory_sha_rows), 'original_file_inventory_rows_without_sha256': len(original_inventory_rows) - len(inventory_sha_rows), 'mass_scan_exact_sha256_link_groups': exact_hash_groups, 'mass_scan_exact_sha256_pair_relations': exact_hash_pair_count, 'mass_scan_inventory_only_sha256_rows': sum((1 for row in inventory_sha_rows if (row.get('sha256') or '').lower() not in mass_rows_by_input_sha)), 'unique_decoded_images': len(images), 'source_scan_records': len(scan_sources), 'image_profile_full_geometry': sum((p['profile_basis'] == 'FULL_GEOMETRY' for p in profiles.values())), 'image_profile_summary_only': sum((p['profile_basis'] == 'SUMMARY_ONLY' for p in profiles.values())), 'base_table_object_rows': base_count, 'scanner_catalogue_files': catalogue_files, 'identifier_links': len(identifiers), 'exact_ecuid_to_catalogue_code_links': sum((r.get('link_status') == 'EXACT_CATALOGUE_CODE_VIA_ECUID' for r in identifiers)), 'family_relationship_edges': len(relationships), 'candidate_components': len(components), 'component_images': sum((len(r['image_ids'].split(';')) for r in components)), 'relationship_policy': 'exact code-region hashes and strict address+geometry overlap can form candidate components; address-ignored shape similarity, payload reuse, same-FID and master-ROM-group links remain separate leads and never imply semantic identity', 'inputs': inputs}
    image_fields = ['image_id', 'decoded_rom_sha256', 'rom_size_bytes', 'cpu_tags', 'nissan_fid_values', 'loader_values', 'scan_datasets', 'source_count', 'source_paths', 'exact_catalogue_code_links', 'exact_fid_inventory_links', 'observed_rom_codes', 'master_rom_groups', 'master_status_values', 'catalogue_vehicle_years', 'profile_basis', 'structural_observation_count', 'unique_geometry_signatures', 'helper_count', 'call_count', 'resolved_calls', 'table_count', 'nontrivial_table_count', 'candidate_component_id']
    profile_fields = ['image_id', 'decoded_rom_sha256', 'profile_basis', 'rom_size_bytes', 'cpu_tags', 'nissan_fid_values', 'structural_observation_count', 'unique_geometry_signatures', 'strict_signature_count', 'payload_hash_count', 'table_kind_counts_json', 'helper_count', 'call_count', 'resolved_calls', 'table_count', 'nontrivial_table_count', 'candidate_component_id', 'scan_datasets', 'source_paths']
    index_json = {'schema': SCHEMA, 'summary': summary, 'master_rom_codes': crosswalk_rows, 'master_rom_groups': master_group_rows, 'generation_summary': [dict(zip(['metadata_basis', 'make', 'model', 'vehicle_year', 'engine_code', 'transmission', 'unique_images', 'full_geometry_images', 'summary_only_images', 'structural_observations', 'min_scanned_table_count', 'median_scanned_table_count', 'max_scanned_table_count'], row)) for row in generation_rows], 'images': [dict(zip(image_fields, row)) for row in image_rows], 'identifiers': [dict(zip(ident_fields, row)) for row in ident_rows], 'scan_sources': [dict(zip(scan_fields, row)) for row in scan_out_rows], 'structural_profiles': [dict(zip(profile_fields, row)) for row in profile_rows], 'relationships': relationships, 'candidate_components': components}
    write_json(out / 'nissan_rom_family_index.json', index_json)
    write_json(out / 'nissan_rom_family_index_manifest.json', {'schema': SCHEMA + '-manifest', 'summary': summary, 'outputs': {p.name: {'bytes': p.stat().st_size, 'sha256': sha256_file(p)} for p in sorted(out.iterdir()) if p.is_file() and p.name != 'nissan_rom_family_index_manifest.json'}})
    return summary

def cmd_build(ns: argparse.Namespace) -> int:
    summary = build_index(ns)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0

def cmd_query(ns: argparse.Namespace) -> int:
    index_doc = load_json(Path(ns.index))
    code_query = norm_code(ns.rom_code or '')
    fid_query = norm_code(ns.fid or '')
    sha_query = (ns.sha256 or '').lower()
    code_hits = [r for r in index_doc.get('master_rom_codes', []) if code_query and norm_code(r.get('ROM_ID_Normalized', '')) == code_query]
    ident_hits = []
    for item in index_doc.get('identifiers', []):
        norm = norm_code(item.get('normalized_identifier', ''))
        if code_query and norm == code_query or (fid_query and norm == fid_query):
            ident_hits.append(item)
    image_ids = {r['image_id'] for r in ident_hits}
    if sha_query:
        for row in index_doc.get('images', []):
            if str(row.get('decoded_rom_sha256', '')).lower() == sha_query:
                image_ids.add(row.get('image_id'))
    image_hits = [r for r in index_doc.get('images', []) if r.get('image_id') in image_ids]
    relationship_hits = [r for r in index_doc.get('relationships', []) if r.get('image_a') in image_ids or r.get('image_b') in image_ids]
    result = {'rom_code_matches': code_hits, 'identifier_links': ident_hits, 'images': image_hits, 'family_relationships': relationship_hits}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0

def main(argv: Optional[Sequence[str]]=None) -> int:
    parser = argparse.ArgumentParser(description='Build/query the Nissan master-ROM and structural-family index')
    sub = parser.add_subparsers(dest='action', required=True)
    build = sub.add_parser('build')
    build.add_argument('--rom-id-crosswalk', required=True)
    build.add_argument('--vehicle-catalog')
    build.add_argument('--ecu-fid-catalog')
    build.add_argument('--scan-inventory')
    build.add_argument('--catalogue-dir')
    build.add_argument('--dat-scan-index')
    build.add_argument('--base-table-objects')
    build.add_argument('--mass-scan-results', default='EVIDENCE/mass dat scan/scan_results.tsv')
    build.add_argument('--mass-file-inventory', default='EVIDENCE/mass dat scan/file_inventory.tsv')
    build.add_argument('--reference-index')
    build.add_argument('--out-dir', required=True)
    build.set_defaults(func=cmd_build)
    query = sub.add_parser('query')
    query.add_argument('--index', required=True)
    query.add_argument('--rom-code')
    query.add_argument('--fid')
    query.add_argument('--sha256')
    query.set_defaults(func=cmd_query)
    args = parser.parse_args(argv)
    return args.func(args)
if __name__ == '__main__':
    raise SystemExit(main())