"""Synthetic tests for the Nissan ROM identity/family index; no real ROMs."""
import contextlib
import csv
import gzip
import io
import json
import tempfile
import unittest
from pathlib import Path
from argparse import Namespace
import nissan_rom_family_index as idx

def write_tsv(path, fields, rows):
    with path.open('w', encoding='utf-8', newline='') as f:
        w = csv.writer(f, delimiter='\t', lineterminator='\n')
        w.writerow(fields)
        w.writerows(rows)

class NissanRomFamilyIndexTests(unittest.TestCase):

    def test_master_ids_are_expanded_rows_and_master_marker_is_preserved(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cross = root / 'cross.tsv'
            fields = ['ROM_ID_Normalized', 'ROM_ID_AsListed', 'IsMasterROM', 'MasterROM_ID', 'Model', 'Make', 'VehicleYear', 'EngineCode', 'Transmission', 'SourceLine']
            write_tsv(cross, fields, [['CD100', 'CD100', 'NO', 'CD102', '350Z', 'Nissan', '2003', 'VQ35DE', 'AT', '2'], ['CD102', 'CD102', 'YES', 'CD102', '350Z', 'Nissan', '2003', 'VQ35DE', 'AT', '2']])
            inv = root / 'scan.tsv'
            scan_fields = ['path', 'filename', 'bytes', 'container_sha256', 'decoded_rom_sha256', 'decoded_size', 'cpu', 'fid', 'loader', 'helper_count', 'call_sites', 'resolved_calls', 'unique_tables', 'status', 'catalogue_path', 'error']
            write_tsv(inv, scan_fields, [['EVIDENCE/rr roms/CD100.bin', 'CD100.bin', '100', 'c1', 'a' * 64, '100', 'SH7058', 'FID00001', 'LOADER80', '1', '4', '4', '2', 'SCAN_OK', '', '']])
            fid = root / 'fid.tsv'
            write_tsv(fid, ['SourceLine', 'Model', 'YearText', 'EngineText', 'ECUID', 'FID', 'SourcePath', 'SourceURL'], [['1', '350Z', '03', 'VQ35DE', 'CD100', 'FID00001', 'src', 'url']])
            base = root / 'objects.tsv.gz'
            rows = []
            for address, payload in [('0x1000', 'a' * 64), ('0x1100', 'b' * 64)]:
                rows.append(['DAT:' + 'a' * 16, 'FULL_SCAN_DIRECT_DAT', 'CD100.bin', 'FID00001', 'SH7058', '100', 'a' * 64, address, '0x1010', '0x1010', '16', '3D_AXIS', 'uint8', '1', 'unsigned_as_detected', 'byte', '4', '4', 'uint8', 'uint8', '', '', '', '', '1', payload, ''])
            write_tsv_tmp = root / 'obj.tmp.tsv'
            write_tsv(write_tsv_tmp, ['image_id', 'evidence_tier', 'source_file', 'primary_fid', 'cpu', 'rom_size_bytes', 'rom_sha256', 'address', 'end_inclusive', 'end_exclusive', 'extent_bytes', 'table_kind', 'element_type', 'element_width_bytes', 'signedness_from_type', 'byte_order', 'dim1', 'dim2', 'axis1_storage_type', 'axis2_storage_type', 'axis1_addresses', 'axis2_addresses', 'call_pcs', 'helper_addresses', 'nontrivial', 'payload_sha256', 'resolution_or_caveat'], rows)
            with gzip.open(base, 'wt', encoding='utf-8', newline='') as out:
                out.write(write_tsv_tmp.read_text(encoding='utf-8'))
            args = Namespace(rom_id_crosswalk=str(cross), vehicle_catalog=None, ecu_fid_catalog=str(fid), scan_inventory=str(inv), catalogue_dir=None, dat_scan_index=None, base_table_objects=str(base), reference_index=None, out_dir=str(root / 'out'))
            summary = idx.build_index(args)
            self.assertEqual(summary['master_rom_code_rows'], 2)
            self.assertEqual(summary['master_rom_ids'], 2)
            self.assertEqual(summary['master_flagged_rows'], 1)
            images = idx.read_tsv(Path(args.out_dir) / 'nissan_rom_image_index.tsv')
            self.assertEqual(len(images), 1)
            code_rows = idx.read_tsv(Path(args.out_dir) / 'nissan_rom_identifier_links.tsv')
            master = [r for r in code_rows if r['identifier_namespace'] == 'UPREV_ROM_CODE']
            self.assertEqual(len(master), 2)
            self.assertEqual({r['identifier'] for r in master}, {'CD100'})
            self.assertEqual({r['link_status'] for r in master}, {'EXACT_CATALOGUE_CODE_MATCH', 'EXACT_CATALOGUE_CODE_VIA_ECUID'})
            self.assertTrue(all(r['master_rom_id'] == 'CD102' for r in master))
            self.assertTrue(all(r['is_master_rom'] == 'NO' for r in master))
            fid_links = [r for r in code_rows if r['identifier_namespace'] == 'NISSAN_FID']
            self.assertEqual(len(fid_links), 1)
            self.assertEqual(fid_links[0]['link_status'], 'EXACT_IN_ECU_FID_INVENTORY')

    def test_exact_decoded_hash_deduplicates_sources_not_rom_code_links(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cross = root / 'cross.tsv'
            fields = ['ROM_ID_Normalized', 'ROM_ID_AsListed', 'IsMasterROM', 'MasterROM_ID', 'Model', 'Make', 'VehicleYear', 'EngineCode', 'Transmission', 'SourceLine']
            write_tsv(cross, fields, [['CD100', 'CD100', 'NO', 'CD102', '350Z', 'Nissan', '2003', 'VQ35DE', 'AT', '2'], ['CD102', 'CD102', 'YES', 'CD102', '350Z', 'Nissan', '2003', 'VQ35DE', 'AT', '2']])
            inv = root / 'scan.tsv'
            scan_fields = ['path', 'filename', 'bytes', 'container_sha256', 'decoded_rom_sha256', 'decoded_size', 'cpu', 'fid', 'loader', 'helper_count', 'call_sites', 'resolved_calls', 'unique_tables', 'status', 'catalogue_path', 'error']
            write_tsv(inv, scan_fields, [['folder/CD100.bin', 'CD100.bin', '100', 'c1', 'a' * 64, '100', 'SH7058', 'FID00001', 'LOADER80', '1', '4', '4', '2', 'SCAN_OK', '', ''], ['folder/CD102.bin', 'CD102.bin', '100', 'c2', 'a' * 64, '100', 'SH7058', 'FID00001', 'LOADER80', '1', '4', '4', '2', 'DECODED_IMAGE_DUPLICATE', '', '']])
            args = Namespace(rom_id_crosswalk=str(cross), vehicle_catalog=None, ecu_fid_catalog=None, scan_inventory=str(inv), catalogue_dir=None, dat_scan_index=None, base_table_objects=None, reference_index=None, out_dir=str(root / 'out'))
            summary = idx.build_index(args)
            self.assertEqual(summary['unique_decoded_images'], 1)
            image_rows = idx.read_tsv(Path(args.out_dir) / 'nissan_rom_image_index.tsv')
            self.assertEqual(image_rows[0]['source_count'], '2')
            ids = idx.read_tsv(Path(args.out_dir) / 'nissan_rom_identifier_links.tsv')
            linked = {r['identifier'] for r in ids if r['identifier_namespace'] == 'UPREV_ROM_CODE'}
            self.assertEqual(linked, {'CD100', 'CD102'})

    def test_multiset_jaccard_and_relationship_evidence_are_separate(self):
        a = idx.collections.Counter({('3D_AXIS', 'uint8', 1, 16, 16, 'uint8', 'uint8'): 10})
        b = idx.collections.Counter({('3D_AXIS', 'uint8', 1, 16, 16, 'uint8', 'uint8'): 5, ('2D_IMPL', 'uint8', 1, 16, 1, 'implicit_u8', ''): 5})
        self.assertAlmostEqual(idx.multiset_jaccard(a, b), 1.0 / 3.0)

    def test_catalogue_master_group_is_not_promoted_to_structural_component(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cross = root / 'cross.tsv'
            fields = ['ROM_ID_Normalized', 'ROM_ID_AsListed', 'IsMasterROM', 'MasterROM_ID', 'Model', 'Make', 'VehicleYear', 'EngineCode', 'Transmission', 'SourceLine']
            write_tsv(cross, fields, [['CD100', 'CD100', 'NO', 'CD102', '350Z', 'Nissan', '2003', 'VQ35DE', 'AT', '2'], ['CD102', 'CD102', 'YES', 'CD102', '350Z', 'Nissan', '2003', 'VQ35DE', 'AT', '2']])
            inv = root / 'scan.tsv'
            scan_fields = ['path', 'filename', 'bytes', 'container_sha256', 'decoded_rom_sha256', 'decoded_size', 'cpu', 'fid', 'loader', 'helper_count', 'call_sites', 'resolved_calls', 'unique_tables', 'status', 'catalogue_path', 'error']
            write_tsv(inv, scan_fields, [['folder/CD100.bin', 'CD100.bin', '100', 'c1', 'a' * 64, '100', 'SH7058', 'FID00001', 'LOADER80', '1', '4', '4', '2', 'SCAN_OK', '', ''], ['folder/CD102.bin', 'CD102.bin', '100', 'c2', 'b' * 64, '100', 'SH7058', 'FID00002', 'LOADER80', '1', '4', '4', '2', 'SCAN_OK', '', '']])
            args = Namespace(rom_id_crosswalk=str(cross), vehicle_catalog=None, ecu_fid_catalog=None, scan_inventory=str(inv), catalogue_dir=None, dat_scan_index=None, base_table_objects=None, reference_index=None, out_dir=str(root / 'out'))
            summary = idx.build_index(args)
            rel = idx.read_tsv(Path(args.out_dir) / 'nissan_rom_family_relationships.tsv')
            group_edges = [r for r in rel if 'CATALOGUE_MASTER_ROM_GROUP' in r['relationship_types']]
            self.assertEqual(len(group_edges), 1)
            self.assertIn('CATALOGUE_MASTER_ROM_GROUP_ONLY_NOT_STRUCTURAL_FAMILY_PROOF', group_edges[0]['evidence_boundary'])
            self.assertEqual(summary['candidate_components'], 0)

    def test_fid_prefix_is_only_a_candidate(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cross = root / 'cross.tsv'
            write_tsv(cross, ['ROM_ID_Normalized', 'ROM_ID_AsListed', 'IsMasterROM', 'MasterROM_ID', 'Model', 'Make', 'VehicleYear', 'EngineCode', 'Transmission', 'SourceLine'], [])
            inv = root / 'scan.tsv'
            write_tsv(inv, ['path', 'filename', 'bytes', 'container_sha256', 'decoded_rom_sha256', 'decoded_size', 'cpu', 'fid', 'loader', 'helper_count', 'call_sites', 'resolved_calls', 'unique_tables', 'status', 'catalogue_path', 'error'], [['folder/sample.bin', 'sample.bin', '100', 'c1', 'a' * 64, '100', 'SH7058', 'FID00001', 'LOADER80', '1', '4', '4', '2', 'SCAN_OK', '', '']])
            fid = root / 'fid.tsv'
            write_tsv(fid, ['SourceLine', 'Model', 'YearText', 'EngineText', 'ECUID', 'FID', 'SourcePath', 'SourceURL'], [['1', 'Sample', '03', 'VQ35DE', 'ECU0001', 'FID000012', 'src', 'url']])
            args = Namespace(rom_id_crosswalk=str(cross), vehicle_catalog=None, ecu_fid_catalog=str(fid), scan_inventory=str(inv), catalogue_dir=None, dat_scan_index=None, base_table_objects=None, reference_index=None, out_dir=str(root / 'out'))
            idx.build_index(args)
            links = idx.read_tsv(Path(args.out_dir) / 'nissan_rom_identifier_links.tsv')
            prefix = [r for r in links if r['link_status'] == 'PREFIX_CANDIDATE']
            exact = [r for r in links if r['link_status'] == 'EXACT_IN_ECU_FID_INVENTORY']
            self.assertEqual(len(prefix), 1)
            self.assertEqual(exact, [])

    def test_json_query_returns_structured_image_and_family_links(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cross = root / 'cross.tsv'
            write_tsv(cross, ['ROM_ID_Normalized', 'ROM_ID_AsListed', 'IsMasterROM', 'MasterROM_ID', 'Model', 'Make', 'VehicleYear', 'EngineCode', 'Transmission', 'SourceLine'], [['CD100', 'CD100', 'YES', 'CD100', '350Z', 'Nissan', '2003', 'VQ35DE', 'AT', '2']])
            inv = root / 'scan.tsv'
            write_tsv(inv, ['path', 'filename', 'bytes', 'container_sha256', 'decoded_rom_sha256', 'decoded_size', 'cpu', 'fid', 'loader', 'helper_count', 'call_sites', 'resolved_calls', 'unique_tables', 'status', 'catalogue_path', 'error'], [['folder/CD100.bin', 'CD100.bin', '100', 'c1', 'a' * 64, '100', 'SH7058', 'FID00001', 'LOADER80', '1', '4', '4', '2', 'SCAN_OK', '', '']])
            out = root / 'out'
            args = Namespace(rom_id_crosswalk=str(cross), vehicle_catalog=None, ecu_fid_catalog=None, scan_inventory=str(inv), catalogue_dir=None, dat_scan_index=None, base_table_objects=None, reference_index=None, out_dir=str(out))
            idx.build_index(args)
            index_json = out / 'nissan_rom_family_index.json'
            stream = io.StringIO()
            with contextlib.redirect_stdout(stream):
                idx.cmd_query(Namespace(index=str(index_json), rom_code='CD100', fid=None, sha256=None))
            result = json.loads(stream.getvalue())
            self.assertEqual(len(result['rom_code_matches']), 1)
            self.assertEqual(len(result['images']), 1)
            self.assertEqual(result['images'][0]['decoded_rom_sha256'], 'a' * 64)
    def test_strict_layout_overlap_forms_candidate_component(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cross = root / 'cross.tsv'
            write_tsv(cross, ['ROM_ID_Normalized', 'ROM_ID_AsListed', 'IsMasterROM', 'MasterROM_ID', 'Model', 'Make', 'VehicleYear', 'EngineCode', 'Transmission', 'SourceLine'], [])
            base = root / 'objects.tsv.gz'
            fields = ['image_id', 'evidence_tier', 'source_file', 'primary_fid', 'cpu', 'rom_size_bytes', 'rom_sha256', 'address', 'end_inclusive', 'end_exclusive', 'extent_bytes', 'table_kind', 'element_type', 'element_width_bytes', 'signedness_from_type', 'byte_order', 'dim1', 'dim2', 'axis1_storage_type', 'axis2_storage_type', 'axis1_addresses', 'axis2_addresses', 'call_pcs', 'helper_addresses', 'nontrivial', 'payload_sha256', 'resolution_or_caveat']
            rows = []
            for imgno, sha in ((1, 'a' * 64), (2, 'b' * 64)):
                for k in range(12):
                    start = 0x1000 + k * 0x100
                    rows.append([f'DAT:{imgno}', 'FULL_SCAN_DIRECT_DAT', f'rom{imgno}.dat', f'FID0000{imgno}', 'SH7058', '524288', sha, f'0x{start:05X}', f'0x{start+15:05X}', f'0x{start+16:05X}', '16', '2D_AXIS', 'uint8', '1', 'unsigned_as_detected', 'byte', '16', '1', 'uint8', '', '', '', '', '', '1', f'{k+1:064x}', 'synthetic'])
            tmp = root / 'objects.tsv'
            write_tsv(tmp, fields, rows)
            with gzip.open(base, 'wt', encoding='utf-8', newline='') as out:
                out.write(tmp.read_text(encoding='utf-8'))
            args = Namespace(rom_id_crosswalk=str(cross), vehicle_catalog=None, ecu_fid_catalog=None, scan_inventory=None, catalogue_dir=None, dat_scan_index=None, base_table_objects=str(base), reference_index=None, out_dir=str(root / 'out'))
            summary = idx.build_index(args)
            relationships = idx.read_tsv(Path(args.out_dir) / 'nissan_rom_family_relationships.tsv')
            self.assertEqual(len(relationships), 1)
            self.assertIn('HIGH_STRICT_LAYOUT_OVERLAP', relationships[0]['relationship_types'])
            components = idx.read_tsv(Path(args.out_dir) / 'nissan_rom_candidate_components.tsv')
            self.assertEqual(len(components), 1)
            self.assertEqual(components[0]['image_count'], '2')
            self.assertEqual(summary['candidate_components'], 1)

    def test_fid_inventory_ecuid_bridges_scan_without_filename_rom_code(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cross = root / 'cross.tsv'
            fields = ['ROM_ID_Normalized', 'ROM_ID_AsListed', 'IsMasterROM', 'MasterROM_ID', 'Model', 'Make', 'VehicleYear', 'EngineCode', 'Transmission', 'SourceLine']
            write_tsv(cross, fields, [['CD100', 'CD100', 'YES', 'CD100', '350Z', 'Nissan', '2003', 'VQ35DE', 'AT', '2']])
            inv = root / 'scan.tsv'
            scan_fields = ['path', 'filename', 'bytes', 'container_sha256', 'decoded_rom_sha256', 'decoded_size', 'cpu', 'fid', 'loader', 'helper_count', 'call_sites', 'resolved_calls', 'unique_tables', 'status', 'catalogue_path', 'error']
            write_tsv(inv, scan_fields, [['folder/unknown-stock.bin', 'unknown-stock.bin', '100', 'c1', 'a' * 64, '100', 'SH7058', 'FID00001', 'LOADER80', '1', '4', '4', '2', 'SCAN_OK', '', '']])
            fid = root / 'fid.tsv'
            write_tsv(fid, ['SourceLine', 'Model', 'YearText', 'EngineText', 'ECUID', 'FID', 'SourcePath', 'SourceURL'], [['1', '350Z', '03', 'VQ35DE', 'CD100', 'FID00001', 'src', 'url']])
            args = Namespace(rom_id_crosswalk=str(cross), vehicle_catalog=None, ecu_fid_catalog=str(fid), scan_inventory=str(inv), catalogue_dir=None, dat_scan_index=None, base_table_objects=None, reference_index=None, out_dir=str(root / 'out'))
            idx.build_index(args)
            links = idx.read_tsv(Path(args.out_dir) / 'nissan_rom_identifier_links.tsv')
            code = [r for r in links if r['identifier_namespace'] == 'UPREV_ROM_CODE']
            self.assertEqual(len(code), 1)
            self.assertEqual(code[0]['identifier'], 'CD100')
            self.assertEqual(code[0]['link_status'], 'EXACT_CATALOGUE_CODE_VIA_ECUID')
            self.assertEqual(code[0]['link_basis'], 'exact_ecuid_to_catalogue_code_via_fid_inventory')
            images = idx.read_tsv(Path(args.out_dir) / 'nissan_rom_image_index.tsv')
            self.assertEqual(images[0]['observed_rom_codes'], 'CD100')


    def test_full_historical_mass_scan_and_original_file_inventory_join(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cross = root / 'cross.tsv'
            write_tsv(cross,
                      ['ROM_ID_Normalized', 'ROM_ID_AsListed', 'IsMasterROM', 'MasterROM_ID', 'Model', 'Make', 'VehicleYear', 'EngineCode', 'Transmission', 'SourceLine'],
                      [['CD100', 'CD100', 'YES', 'CD100', '350Z', 'Nissan', '2003', 'VQ35DE', 'AT', '2']])
            dat = root / 'detailed.tsv'
            write_tsv(dat,
                      ['PayloadSHA256', 'SourceFile', 'ROMSizeBytes', 'CPU', 'PrimaryNissanMetadataFID', 'HelperCount', 'CallSiteAssociations', 'UniqueCallPCs', 'TableCount', 'NontrivialTableCount'],
                      [['a' * 64, 'a.dat', '256', 'SH7058', 'FID00001', '2', '4', '4', '3', '2']])
            mass = root / 'mass_scan.tsv'
            mass_fields = ['input_key', 'codec', 'input_sha256', 'source', 'source_count', 'status', 'decoded_rom_sha256', 'rom_size_bytes', 'cpu_tags', 'fid_tags', 'loader', 'helpers', 'helper_kinds', 'call_sites', 'resolved_calls', 'unique_tables', 'error']
            write_tsv(mass, mass_fields, [
                ['dat:' + 'b' * 64, 'dat', 'b' * 64, 'a.dat', '1', 'SCANNED', 'a' * 64, '256', '["SH7058"]', '[]', 'LDR', '2', '{}', '4', '4', '3', ''],
                ['dat:' + 'b' * 64, 'dat', 'b' * 64, 'b.dat', '1', 'SCANNED', 'a' * 64, '256', '["SH7058"]', '[]', 'LDR', '3', '{}', '5', '5', '4', ''],
                ['dat:' + 'c' * 64, 'dat', 'c' * 64, 'c.dat', '1', 'LOAD_REJECTED', '', '0', '[]', '[]', '', '0', '{}', '0', '0', '0', 'unrecognized container'],
                ['raw:' + 'd' * 64, 'raw', 'd' * 64, 'archive_member.bin', '1', 'SCANNED', 'e' * 64, '512', '["SH7058"]', '[]', '', '0', '{}', '0', '0', '0', '']
            ])
            inventory = root / 'file_inventory.tsv'
            write_tsv(inventory,
                      ['relative', 'extension', 'size_bytes', 'sha256', 'classification'],
                      [
                          ['a.dat', '.dat', '256', 'b' * 64, 'DIRECT_WORKBENCH_INPUT'],
                          ['b.dat', '.dat', '256', 'b' * 64, 'DIRECT_WORKBENCH_INPUT'],
                          ['c.dat', '.dat', '0', 'c' * 64, 'DIRECT_WORKBENCH_INPUT'],
                          ['archive.zip', '.zip', '1024', 'f' * 64, 'ZIP_PACKAGE'],
                          ['notes.txt', '.txt', '12', '', 'ANCILLARY_OR_UNSUPPORTED']
                      ])
            args = Namespace(
                rom_id_crosswalk=str(cross), vehicle_catalog=None, ecu_fid_catalog=None,
                scan_inventory=None, catalogue_dir=None, dat_scan_index=str(dat),
                base_table_objects=None, reference_index=None,
                mass_scan_results=str(mass), mass_file_inventory=str(inventory),
                out_dir=str(root / 'out'))
            summary = idx.build_index(args)
            self.assertEqual(summary['historical_mass_scan_result_rows'], 4)
            self.assertEqual(summary['historical_mass_scan_scanned_rows'], 3)
            self.assertEqual(summary['historical_mass_scan_load_rejected_rows'], 1)
            self.assertEqual(summary['historical_mass_scan_unique_input_hashes'], 3)
            self.assertEqual(summary['historical_mass_scan_unique_decoded_images'], 2)
            self.assertEqual(summary['historical_mass_scan_exact_file_sha_match_result_rows'], 3)
            self.assertEqual(summary['historical_mass_scan_unmatched_file_sha_result_rows'], 1)
            self.assertEqual(summary['original_file_inventory_rows'], 5)
            self.assertEqual(summary['mass_scan_exact_sha256_link_groups'], 2)
            self.assertEqual(summary['mass_scan_exact_sha256_pair_relations'], 5)
            self.assertEqual(summary['mass_scan_inventory_only_sha256_rows'], 1)
            mass_out = idx.read_tsv(Path(args.out_dir) / 'nissan_historical_mass_scan_results.tsv')
            self.assertEqual(len(mass_out), 4)
            self.assertEqual(sum(1 for row in mass_out if row['detailed_positive_431_match'] == 'YES'), 2)
            self.assertTrue(all(row['image_id'] for row in mass_out if row['status'] == 'SCANNED'))
            self.assertEqual(next(row for row in mass_out if row['status'] == 'LOAD_REJECTED')['image_id'], '')
            inventory_out = idx.read_tsv(Path(args.out_dir) / 'nissan_original_file_inventory.tsv')
            self.assertEqual(len(inventory_out), 5)
            links = idx.read_tsv(Path(args.out_dir) / 'nissan_mass_scan_input_hash_links.tsv')
            b_link = next(row for row in links if row['input_sha256'] == 'b' * 64)
            self.assertEqual(b_link['join_status'], 'EXACT_SHA256_MATCH')
            self.assertEqual(b_link['scan_result_row_count'], '2')
            self.assertEqual(b_link['file_inventory_row_count'], '2')
            self.assertEqual(b_link['sha256_pair_count'], '4')
            d_link = next(row for row in links if row['input_sha256'] == 'd' * 64)
            self.assertEqual(d_link['join_status'], 'MASS_SCAN_ONLY')
            f_link = next(row for row in links if row['input_sha256'] == 'f' * 64)
            self.assertEqual(f_link['join_status'], 'INVENTORY_ONLY')
            scan_sources = idx.read_tsv(Path(args.out_dir) / 'nissan_rom_scan_sources.tsv')
            self.assertEqual(sum(1 for row in scan_sources if row['dataset'] == 'historical_mass_scan'), 4)
            images = idx.read_tsv(Path(args.out_dir) / 'nissan_rom_image_index.tsv')
            a_image = next(row for row in images if row['decoded_rom_sha256'] == 'a' * 64)
            self.assertEqual(a_image['cpu_tags'], 'SH7058')
            self.assertIn('a.dat', a_image['source_paths'])
            self.assertIn('b.dat', a_image['source_paths'])


if __name__ == '__main__':
    unittest.main()
