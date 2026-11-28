"""Run one reproducible ROM-folder scan batch, then build the master family index."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import platform
import sys
from pathlib import Path
TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))
import nissan_sh705x_workbench as wb
import nissan_rom_family_index as family
SUPPORTED = {'.bin', '.zip', '.s19', '.hex', '.dat'}

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def scan_directory(scan_dir: Path, out_dir: Path) -> Path:
    scan_out = out_dir / 'scans'
    scan_out.mkdir(parents=True, exist_ok=True)
    rows = []
    container_seen = {}
    decoded_seen = {}
    for path in sorted((p for p in scan_dir.rglob('*') if p.is_file())):
        rel = path.as_posix()
        if path.suffix.lower() not in SUPPORTED:
            rows.append({'path': rel, 'filename': path.name, 'bytes': path.stat().st_size, 'container_sha256': sha256_file(path), 'decoded_rom_sha256': '', 'decoded_size': '', 'cpu': '', 'fid': '', 'loader': '', 'helper_count': '', 'call_sites': '', 'resolved_calls': '', 'unique_tables': '', 'status': 'SKIPPED_UNSUPPORTED', 'catalogue_path': '', 'error': 'unsupported file extension; retained in source inventory but not passed to ROM loader'})
            continue
        try:
            container_sha = sha256_file(path)
            size = path.stat().st_size
            if container_sha in container_seen:
                prior = container_seen[container_sha]
                rows.append({'path': rel, 'filename': path.name, 'bytes': size, 'container_sha256': container_sha, 'decoded_rom_sha256': prior.get('decoded_rom_sha256', ''), 'decoded_size': prior.get('decoded_size', ''), 'cpu': prior.get('cpu', ''), 'fid': prior.get('fid', ''), 'loader': prior.get('loader', ''), 'helper_count': prior.get('helper_count', ''), 'call_sites': prior.get('call_sites', ''), 'resolved_calls': prior.get('resolved_calls', ''), 'unique_tables': prior.get('unique_tables', ''), 'status': 'EXACT_CONTAINER_DUPLICATE', 'catalogue_path': prior.get('catalogue_path', ''), 'error': ''})
                continue
            rom = wb.load_any_rom(path)
            fp = wb.rom_fingerprint(rom)
            sha = fp['sha256']
            meta = fp.get('nissan_meta') or {}
            base = {'path': rel, 'filename': path.name, 'bytes': size, 'container_sha256': container_sha, 'decoded_rom_sha256': sha, 'decoded_size': len(rom), 'cpu': ';'.join(fp.get('cpu_tags', [])), 'fid': meta.get('fid', ''), 'loader': meta.get('loader', ''), 'error': ''}
            if sha in decoded_seen:
                prior = decoded_seen[sha]
                base.update({'helper_count': prior.get('helper_count', ''), 'call_sites': prior.get('call_sites', ''), 'resolved_calls': prior.get('resolved_calls', ''), 'unique_tables': prior.get('unique_tables', ''), 'status': 'DECODED_IMAGE_DUPLICATE', 'catalogue_path': prior.get('catalogue_path', '')})
                rows.append(base)
                container_seen[container_sha] = base
                continue
            helpers = wb.discover_helpers(rom)
            calls = wb.extract_calls(rom, helpers)
            resolved = sum((1 for c in calls if c.get('table') is not None))
            tables = wb.summarize_tables(rom, calls)
            scan_doc = wb.build_scan_export(str(path), rom, helpers, calls)
            catalogue = wb.to_per_address_catalogue(scan_doc)
            catalogue['implicit_grids'] = {f'0x{k:05X}': v for k, v in wb.extract_implicit_grids(rom, helpers).items()}
            stem = sha[:16]
            cat_path = scan_out / f'{stem}.catalogue.json'
            manifest_path = scan_out / f'{stem}.manifest.json'
            cat_path.write_text(json.dumps(catalogue, indent=2, sort_keys=True) + '\n', encoding='utf-8')
            summary = (catalogue.get('manifest', {}) or {}).get('summary', {})
            manifest = {'schema': 'sh705x-run-manifest-v1', 'output_schema_version': catalogue.get('output_schema_version', ''), 'exit_status': 0, 'input': {'path': rel, 'container_sha256': container_sha, 'container_size_bytes': size, 'decoded_rom_sha256': sha, 'decoded_rom_size_bytes': len(rom)}, 'outputs': [{'path': cat_path.name, 'exists': True, 'size_bytes': cat_path.stat().st_size, 'sha256': sha256_file(cat_path)}], 'summary': summary, 'tool': {'name': 'nissan_sh705x_workbench.py', 'source_path': 'tools/nissan_sh705x_workbench.py'}}
            manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n', encoding='utf-8')
            base.update({'helper_count': len(helpers), 'call_sites': len(calls), 'resolved_calls': resolved, 'unique_tables': len(tables), 'status': 'SCAN_OK', 'catalogue_path': str(cat_path.relative_to(out_dir)), 'error': ''})
            rows.append(base)
            container_seen[container_sha] = base
            decoded_seen[sha] = base
        except Exception as exc:
            rows.append({'path': rel, 'filename': path.name, 'bytes': path.stat().st_size, 'container_sha256': '', 'decoded_rom_sha256': '', 'decoded_size': '', 'cpu': '', 'fid': '', 'loader': '', 'helper_count': '', 'call_sites': '', 'resolved_calls': '', 'unique_tables': '', 'status': 'LOAD_REJECTED', 'catalogue_path': '', 'error': f'{type(exc).__name__}: {exc}'})
    fields = ['path', 'filename', 'bytes', 'container_sha256', 'decoded_rom_sha256', 'decoded_size', 'cpu', 'fid', 'loader', 'helper_count', 'call_sites', 'resolved_calls', 'unique_tables', 'status', 'catalogue_path', 'error']
    inventory = out_dir / 'scan_inventory.tsv'
    with inventory.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, delimiter='\t', lineterminator='\n', extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)
    return inventory

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description='Scan the Nissan reference ROM folder and rebuild its family index')
    ap.add_argument('--scan-dir', default='EVIDENCE/rr roms')
    ap.add_argument('--out-dir', default='EVIDENCE/NISSAN_ROM_FAMILY_INDEX')
    ap.add_argument('--rom-id-crosswalk', default='EVIDENCE/NISSAN_ROM_ID_CROSSWALK_2026-11-27.tsv')
    ap.add_argument('--vehicle-catalog', default='EVIDENCE/NISSAN_ROM_VEHICLE_CATALOG_2026-11-27.tsv')
    ap.add_argument('--ecu-fid-catalog', default='EVIDENCE/NISSAN_ECU_FID_CATALOG_2026-11-27.tsv')
    ap.add_argument('--dat-scan-index', default='EVIDENCE/NISSAN_DAT_DETAILED_SCAN_INDEX_2026-11-27.tsv')
    ap.add_argument('--base-table-objects', default='EVIDENCE/NISSAN_BASE_TABLE_SET_2026-11-27/NISSAN_BASE_TABLE_OBJECTS_2026-11-27.tsv.gz')
    ap.add_argument('--reference-index', default=None)
    args = ap.parse_args(argv)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    inventory = scan_directory(Path(args.scan_dir), out / 'workbench')
    reference_index = args.reference_index
    if not reference_index:
        with inventory.open('r', encoding='utf-8', newline='') as stream:
            unique_roms = [Path(r['path']) for r in csv.DictReader(stream, delimiter='\t') if r['status'] == 'SCAN_OK']
        xml_inputs = sorted((str(p) for p in Path(args.scan_dir).rglob('*.xml')))
        reference_index = str(out / 'workbench' / 'rr_roms_reference_index.json')
        wb.cmd_ref_index(argparse.Namespace(action='build', out=reference_index, a2l=[], tsv=[], xml=xml_inputs, rom=[str(p) for p in unique_roms]))
    ns = argparse.Namespace(rom_id_crosswalk=args.rom_id_crosswalk, vehicle_catalog=args.vehicle_catalog, ecu_fid_catalog=args.ecu_fid_catalog, scan_inventory=str(inventory), catalogue_dir=str(out / 'workbench' / 'scans'), dat_scan_index=args.dat_scan_index, base_table_objects=args.base_table_objects, reference_index=reference_index, out_dir=str(out))
    summary = family.build_index(ns)
    scan_counts = {}
    with inventory.open('r', encoding='utf-8', newline='') as stream:
        for row in csv.DictReader(stream, delimiter='\t'):
            scan_counts[row['status']] = scan_counts.get(row['status'], 0) + 1
    tool_paths = {'workbench': Path(wb.__file__), 'family_index': Path(family.__file__), 'scanner': Path(wb.__file__).with_name('sh7058_cross_rom_scanner.py'), 'loader': Path(wb.__file__).with_name('sh705x_rom_loader.py'), 'romraider_ref_index': Path(wb.__file__).with_name('romraider_ref_index.py'), 'runner': Path(__file__)}
    tool_hashes = {name: {'path': str(path), 'sha256': sha256_file(path), 'bytes': path.stat().st_size} for name, path in tool_paths.items() if path.exists()}
    input_paths = [Path(args.rom_id_crosswalk), Path(args.vehicle_catalog), Path(args.ecu_fid_catalog), Path(args.dat_scan_index), Path(args.base_table_objects)]
    if reference_index:
        input_paths.append(Path(reference_index))
    input_hashes = {str(path): {'sha256': sha256_file(path), 'bytes': path.stat().st_size} for path in input_paths if path.exists()}
    report = {'schema': 'nissan-rom-family-index-run-v1', 'python_version': platform.python_version(), 'arguments': list(sys.argv), 'scan_directory': str(Path(args.scan_dir)), 'scan_counts': scan_counts, 'tool_sources': tool_hashes, 'input_hashes': input_hashes, 'index_summary': summary}
    (out / 'run_summary.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0
if __name__ == '__main__':
    raise SystemExit(main())