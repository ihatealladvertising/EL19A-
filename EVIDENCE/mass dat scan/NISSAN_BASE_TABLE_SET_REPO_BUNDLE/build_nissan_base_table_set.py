#!/usr/bin/env python3
"""Build a provenance-preserving Nissan SH705x base table set from pinned exports."""
from __future__ import annotations
import argparse, csv, gzip, hashlib, json, math, statistics
from collections import Counter, defaultdict
from pathlib import Path

_ap=argparse.ArgumentParser(description=__doc__)
_ap.add_argument('--out-dir',type=Path,default=Path(r'E:\Nissan Consult\ReproProgramming\_SH705xWorkbench_Run_2026-11-27'))
_ap.add_argument('--repo-dir',type=Path,default=Path(r'C:\Users\Vivian\Documents\Codex\2026-11-27\co\work\EL19A-align'))
_args=_ap.parse_args()
OUT=_args.out_dir.resolve()
REPO=_args.repo_dir.resolve()
EVID=REPO/'EVIDENCE'
V6=EVID/'V6_FIRST_CLASS_DONOR_2026-11-27'
ROWS=[]; AXES=[]; IMAGES={}
FIELDS=['image_id','evidence_tier','source_file','primary_fid','cpu','rom_size_bytes','rom_sha256','address','end_inclusive','end_exclusive','extent_bytes','table_kind','element_type','element_width_bytes','signedness_from_type','byte_order','dim1','dim2','axis1_storage_type','axis2_storage_type','axis1_addresses','axis2_addresses','call_pcs','helper_addresses','nontrivial','payload_sha256','resolution_or_caveat']
AFIELDS=['image_id','evidence_tier','rom_sha256','table_address','axis_role','axis_address','axis_storage_type','axis_payload_sha256','link_status']
def hexn(v):
    if v is None or v=='': return ''
    if isinstance(v,int): return f'0x{v:05X}'
    return str(v)
def listhex(vals):
    if not vals:return ''
    return ';'.join(hexn(v) for v in vals)
def add_image(iid,tier,src,fid,cpu,size,sha): IMAGES[iid]={'tier':tier,'source':src,'fid':fid,'cpu':cpu,'size':size,'sha':sha}
def add_row(meta,addr,end,extent,kind,etype,w,d1,d2,a1t='',a2t='',a1=(),a2=(),pcs=(),helpers=(),nontriv='',payload='',caveat=''):
    ROWS.append([meta['id'],meta['tier'],meta['source'],meta['fid'],meta['cpu'],meta['size'],meta['sha'],hexn(addr),hexn(end),hexn(end+1 if isinstance(end,int) else ''),extent,kind,etype,w,('unsigned_as_detected' if etype in ('uint8','uint16','uint32') else 'unknown'),('big_endian' if w and w>1 else ('byte' if w==1 else 'unknown')),d1,d2,a1t,a2t,listhex(a1),listhex(a2),listhex(pcs),listhex(helpers),nontriv,payload,caveat])
    for role,adds,typ in [('axis1',a1,a1t),('axis2',a2,a2t)]:
        for aa in adds:
            AXES.append([meta['id'],meta['tier'],meta['sha'],hexn(addr),role,hexn(aa),typ,'','explicit_scanner_or_caller_link'])
def read_tsv(path):
    with open(path,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f,delimiter='\t'))
def write_tsv(path,fields,rows):
    with open(path,'w',encoding='utf-8',newline='') as f:
        w=csv.writer(f,delimiter='\t',lineterminator='\n');w.writerow(fields);w.writerows(rows)
# 431 direct-DAT scans; per-ROM detailed helper/table exports.
scan=OUT/'scan_details.jsonl.gz'; n_dat=0
with gzip.open(scan,'rt',encoding='utf-8') as f:
    for line in f:
        doc=json.loads(line); fp=doc['fingerprint']; nm=fp.get('nissan_meta') or {}
        iid='DAT:'+fp['sha256'][:16]; add_image(iid,'FULL_SCAN_DIRECT_DAT', ';'.join(doc.get('sources',[])),nm.get('fid',''),';'.join(fp.get('cpu_tags',[])),fp['size'],fp['sha256']); meta={'id':iid,'tier':'FULL_SCAN_DIRECT_DAT','source':';'.join(doc.get('sources',[])),'fid':nm.get('fid',''),'cpu':';'.join(fp.get('cpu_tags',[])),'size':fp['size'],'sha':fp['sha256']}
        for k,t in doc['tables'].items():
            add_row(meta,t['table'],t['end'],t['bytes'],t['kind'],t['elem_type'],int(t['bytes'])//max(1,int(t['dim1'])*int(t['dim2'])),t['dim1'],t['dim2'],t.get('axis1_type',''),t.get('axis2_type',''),t.get('axis1s',[]),t.get('axis2s',[]),t.get('call_pcs',[]),t.get('helpers',[]),t.get('nontrivial',''),'','table shape/call evidence; per-table payload hash not exported')
        n_dat+=1
# EL19A target scan.
p=EVID/'WO65324_2026-11-27_scan_json.json.gz'; d=json.load(gzip.open(p,'rt',encoding='utf-8'));fp=d['fingerprint'];nm=fp.get('nissan_meta') or {}; iid='EL19A:'+fp['sha256'][:16]; add_image(iid,'FULL_SCAN_TARGET',d['file'],nm.get('fid',''),';'.join(fp.get('cpu_tags',[])),fp['size'],fp['sha256']); meta={'id':iid,'tier':'FULL_SCAN_TARGET','source':d['file'],'fid':nm.get('fid',''),'cpu':';'.join(fp.get('cpu_tags',[])),'size':fp['size'],'sha':fp['sha256']}
target_rows={int(r['address'],16):r for r in read_tsv(EVID/'WO70031_EL19A_STRUCTURAL_READINESS.tsv') if r.get('record_class')=='TARGET_CANDIDATE'}
for k,t in d['tables'].items():
    add_row(meta,t['table'],t['end'],t['bytes'],t['kind'],t['elem_type'],int(t['bytes'])//max(1,int(t['dim1'])*int(t['dim2'])),t['dim1'],t['dim2'],t.get('axis1_type',''),t.get('axis2_type',''),t.get('axis1s',[]),t.get('axis2s',[]),t.get('call_pcs',[]),t.get('helpers',[]),t.get('nontrivial',''),'','EL19A target structural scan; hashes/validation are in WO70031 matrix')
    tr=target_rows.get(int(k,16))
    if tr:
        ROWS[-1][25]=tr.get('payload_sha256','')
        ROWS[-1][26]='WO70031: '+tr.get('structural_status','')+'; '+tr.get('structural_disposition','')+'; '+tr.get('unresolved_fields','')
# V6 current strict candidate table variants with payload hashes.
with gzip.open(V6/'v6_current_strict_302_per_address.tsv.gz','rt',encoding='utf-8',newline='') as f:
    for r in csv.DictReader(f,delimiter='\t'):
        geos=json.loads(r['geometry_variants']);a1s=json.loads(r['axis1_variants']);a2s=json.loads(r['axis2_variants']); fp_sha='9d5efbd9010db790b858274b0d4f2a0d08bf47f30ee19cb93eed28d529e82039';iid='V6:'+fp_sha[:16];add_image(iid,'FULL_SCAN_FIRST_CLASS_DONOR','64810223F121200000.hex','7V4YHZEB2','SH705822N',1048576,fp_sha);meta={'id':iid,'tier':'FULL_SCAN_FIRST_CLASS_DONOR','source':'64810223F121200000.hex','fid':'7V4YHZEB2','cpu':'SH705822N','size':1048576,'sha':fp_sha}
        a1=[x.get('address') for x in a1s if x.get('address') is not None];a2=[x.get('address') for x in a2s if x.get('address') is not None]
        for ix,g in enumerate(geos):
            st=int(r['base_hex'],16);en=int(g['end_exclusive'])-1;w=int(g.get('element_width_bytes',1));kind=g.get('helper_kind','');ety=g.get('element_type','')
            add_row(meta,st,en,g['byte_length'],kind,ety,w,g['dim1'],g['dim2'],(a1s[0].get('type','') if a1s else ''),(a2s[0].get('type','') if a2s else ''),a1,a2,[int(x) for x in json.loads(r['call_pcs'])],[int(x) for x in json.loads(r['helper_addresses'])],'',g.get('payload_sha256',''),('current strict scan; geometry variant '+str(ix+1)+'/'+str(len(geos))+'; provisional A2L pairing not used'))
        for role,arr in [('axis1',a1s),('axis2',a2s)]:
            for a in arr:
                AXES.append([iid,'FULL_SCAN_FIRST_CLASS_DONOR',fp_sha,hexn(int(r['base_hex'],16)),role,hexn(a.get('address')),a.get('type',''),a.get('sha256',''),'explicit V6 scanner axis variant'])
# C12W 3DD9A caller table map; A2L metadata intentionally ignored.
p=EVID/'WO70027_TABLE_MAP.tsv'; crows=read_tsv(p); cpayload={r['table_addr']:r for r in read_tsv(EVID/'WO70027_PAYLOAD_COMPARE.tsv')}; sha='28119daaca1a0641e739ed85d74eacc134988dace10bf00a09875196c9186d42';iid='C12W:'+sha[:16];add_image(iid,'FULL_SCAN_WORKORDER_TABLE_MAP','Nissan Tiida_C12W_3DD9A_705828N.bin','0KHDCFDZ7','SH705828N',1048576,sha);meta={'id':iid,'tier':'FULL_SCAN_WORKORDER_TABLE_MAP','source':'Nissan Tiida_C12W_3DD9A_705828N.bin','fid':'0KHDCFDZ7','cpu':'SH705828N','size':1048576,'sha':sha}
for r in crows:
    st=int(r['table_addr'],16);en=int(r['table_end'],16);axes=[int(x,16) for x in r.get('caller_axis_addrs','').split(';') if x]
    kind=r['caller_kind'];d1=int(r['caller_dim1']);d2=int(r['caller_dim2']);w=int(r['bytes'])//max(1,d1*d2)
    pr=cpayload.get(r['table_addr'],{})
    add_row(meta,st,en,int(r['bytes']),kind,r['caller_elem_type'],w,d1,d2,'','',axes[:1],axes[1:2],[int(x,16) for x in r.get('call_pcs','').split(';') if x],[], '', pr.get('bin_payload_sha256',''), 'WO70027 target caller geometry/payload; donor A2L names/scales omitted; 3 geometry exceptions retained in source report')
    for ix,aa in enumerate(axes):AXES.append([iid,'FULL_SCAN_WORKORDER_TABLE_MAP',sha,hexn(st),f'axis{ix+1}',hexn(aa),'','', 'caller-axis address; storage type not exported'])
# Juke S19 twin: deliberately not copied into independent layout counts.
add_image('JUKE_S19_TWIN:4bcde3a7cab64691','INHERITED_CODE_TWIN_LAYOUT','9APCTDEM06.s19','0KHDCFDZ7','SH705828N',1048576,'4bcde3a7cab646917509beea312aa15eedfb23a59e1e5c43526eae9b0fa3fba0')
# C12W/Juke per-address payload overlay, stripped of donor A2L names.
payload_rows=[]
for r in read_tsv(EVID/'WO70027_PAYLOAD_COMPARE.tsv'):
    payload_rows.append([r['table_addr'],r['bytes'],r['elem_type'],r['geometry'],r['bin_payload_sha256'],r['s19_payload_sha256'],r['classification'],r['differing_bytes'],r['differing_ranges'],r['inside_caller_table_extent'],'C12W BIN SHA 28119daaca1a0641e739ed85d74eacc134988dace10bf00a09875196c9186d42','Juke S19 decoded SHA 4bcde3a7cab646917509beea312aa15eedfb23a59e1e5c43526eae9b0fa3fba0'])
write_tsv(OUT/'NISSAN_C12W_JUKE_TWIN_PAYLOADS_2026-11-27.tsv',['table_address','extent_bytes','element_type','caller_geometry','c12w_payload_sha256','juke_s19_payload_sha256','comparison_class','differing_bytes','differing_ranges','inside_caller_extent','c12w_rom_sha256','juke_s19_rom_sha256'],payload_rows)

# Additional 24-family donor aggregate from WO70026; deliberately not expanded into object rows.
w26=json.load(open(EVID/'WO70026_summary.json',encoding='utf-8'))
donor_cov=[]
for family,info in w26.get('donor_meta',{}).items():
    donor_cov.append([family,info.get('path',''),info.get('sha256',''),info.get('size',''),info.get('tables',''),info.get('nontrivial',''),'WO70026 per-donor aggregate only; per-table layout not in normalized object export; overlaps with the 431-DAT set may exist'])
write_tsv(OUT/'NISSAN_BASE_ADDITIONAL_DONOR_COVERAGE_2026-11-27.tsv',['donor_family_label','source_path','decoded_rom_sha256','rom_size_bytes','table_count_reported','nontrivial_table_count_reported','coverage_caveat'],donor_cov)

# Derived profiles from independent-layout observations only.
write_tsv(OUT/'NISSAN_BASE_TABLE_OBJECTS_2026-11-27.tsv',FIELDS,ROWS)
write_tsv(OUT/'NISSAN_BASE_AXIS_LINKS_2026-11-27.tsv',AFIELDS,AXES)

def shape(row):return (row[11],row[12],row[16],row[17],row[18],row[19])
def strict(row):return (row[7],row[8],row[10],*shape(row))
byshape=defaultdict(Counter); tablekind=Counter(); perimage=defaultdict(Counter); imagekind=defaultdict(Counter)
for row in ROWS:
    s=shape(row);byshape[s][row[0]]+=1;perimage[row[0]][s]+=1;tablekind[row[11]]+=1;imagekind[row[0]][row[11]]+=1
shape_rows=[]
for s,counts in sorted(byshape.items(),key=lambda kv:(-sum(kv[1].values()),kv[0])):
    k,e,d1,d2,a1,a2=s;shape_rows.append([k,e,d1,d2,a1,a2,sum(counts.values()),len(counts),len(IMAGES)-1,f'{len(counts)/(len(IMAGES)-1):.6f}',max(counts.values())])
write_tsv(OUT/'NISSAN_BASE_SHAPE_PROFILE_2026-11-27.tsv',['table_kind','element_type','dim1','dim2','axis1_storage_type','axis2_storage_type','object_observations','images_with_shape','independent_layout_images','image_prevalence_fraction','max_count_in_one_image'],shape_rows)
# Pairwise family-level consistency in 431 DAT scans only.
romrows=read_tsv(OUT/'dat_detailed_431_results.tsv'); name_to_id={r[2].split(';')[0]: 'DAT:'+r[3][:16] for r in ROWS[:0]} # build via input metadata below
# Build per-FID layout sets from normalized detail rows.
family_images=defaultdict(dict)
for iid,im in IMAGES.items():
    if iid.startswith('DAT:') and im['fid']:
        family_images[im['fid']][iid]=set()
for row in ROWS:
    if row[0] in {iid for m in family_images.values() for iid in m}:
        family_images[next(fid for fid,m in family_images.items() if row[0] in m)][row[0]].add(strict(row))
family_rows=[]
for fid,ims in sorted(family_images.items(),key=lambda kv:(-len(kv[1]),kv[0])):
    vals=list(ims.values());scores=[]
    for i in range(len(vals)):
        for j in range(i+1,len(vals)):
            a,b=vals[i],vals[j];u=len(a|b);scores.append(len(a&b)/u if u else 1.0)
    counts=[sum(1 for r in ROWS if r[0]==iid) for iid in ims]
    family_rows.append([fid,len(ims),min(counts),statistics.median(counts),max(counts),len(scores),f'{statistics.median(scores):.6f}' if scores else '',f'{min(scores):.6f}' if scores else '',sum(x==1 for x in scores),len(scores),len(set(tuple(sorted(v)) for v in vals))])
write_tsv(OUT/'NISSAN_BASE_FID_FAMILY_PROFILE_2026-11-27.tsv',['primary_fid','rom_snapshots','min_tables','median_tables','max_tables','pair_count','median_strict_layout_jaccard','min_strict_layout_jaccard','exact_layout_pairs','pair_count_recomputed','distinct_full_layout_signatures'],family_rows)
# Key structural subset summaries.
large=Counter(); axes_distinct=Counter(); d2=Counter(); d3=Counter(); scalar_note=[]
for row in ROWS:
    k,e,d1,d2v,a1,a2=shape(row)
    if k.startswith('3D') and d1>=8 and d2v>=8:large[(k,e,d1,d2v)]+=1
    if k.startswith('2D') and d1>=16: d2[(k,e,d1)]+=1
    if k.startswith('3D'):d3[(k,e,d1,d2v)]+=1
# Source hashes and output manifest.
inputs=[OUT/'scan_details.jsonl.gz',OUT/'dat_detailed_431_results.tsv',EVID/'WO65324_2026-11-27_scan_json.json.gz',V6/'v6_current_strict_302_per_address.tsv.gz',EVID/'WO70027_TABLE_MAP.tsv',EVID/'WO70027_SUMMARY.json',EVID/'WO70027_PAYLOAD_COMPARE.tsv',EVID/'WO70031_EL19A_STRUCTURAL_READINESS.tsv',EVID/'WO70026_summary.json',EVID/'WO70026_donor_conservation.tsv',OUT/'table_layout_similarity_431_DAT_2026-11-27.md',OUT/'EL19A_table_layout_vs_431_DAT_2026-11-27.md']
def hashfile(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
manifest={'generated_utc_date':'2026-11-27','scope':'independent detailed structural table layouts: 431 direct DAT + EL19A + V6 + C12W; Juke S19 recorded as an inherited code-twin, excluded from independent shape frequencies','counts':{'direct_dat_roms':n_dat,'independent_layout_images':len(IMAGES)-1,'normalized_table_object_rows':len(ROWS),'axis_link_rows':len(AXES),'unique_shapes':len(shape_rows),'primary_fid_families_with_detailed_dat':len(family_rows)},'sources':{},'outputs':{}}
for p in inputs:
    if p.exists():manifest['sources'][str(p)]={'bytes':p.stat().st_size,'sha256':hashfile(p)}
for fn in ['NISSAN_BASE_TABLE_OBJECTS_2026-11-27.tsv','NISSAN_BASE_AXIS_LINKS_2026-11-27.tsv','NISSAN_BASE_SHAPE_PROFILE_2026-11-27.tsv','NISSAN_BASE_FID_FAMILY_PROFILE_2026-11-27.tsv','NISSAN_BASE_ADDITIONAL_DONOR_COVERAGE_2026-11-27.tsv','NISSAN_C12W_JUKE_TWIN_PAYLOADS_2026-11-27.tsv']:
    p=OUT/fn;manifest['outputs'][fn]={'bytes':p.stat().st_size,'sha256':hashfile(p),'data_rows':sum(1 for _ in open(p,encoding='utf-8'))-1}
# Save concise digest for report authoring.
summary={'n_dat':n_dat,'images':len(IMAGES)-1,'rows':len(ROWS),'axes':len(AXES),'shapes':len(shape_rows),'families':len(family_rows),'wo70026_donor_aggregate_rows':len(donor_cov),'kind':dict(tablekind),'large3d':[[*k,v] for k,v in large.most_common(20)],'long2d':[[*k,v] for k,v in d2.most_common(20)],'top_shapes':shape_rows[:30],'top_families':family_rows[:20],'hashes':{k:v['sha256'] for k,v in manifest['outputs'].items()}}
(OUT/'NISSAN_BASE_TABLE_SET_summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
for fn in ['NISSAN_BASE_TABLE_SET_summary.json','build_nissan_base_table_set.py']:
    q=OUT/fn; manifest['outputs'][fn]={'bytes':q.stat().st_size,'sha256':hashfile(q)}
report_path=OUT/'NISSAN_BASE_TABLE_SET_2026-11-27.md'
if report_path.exists(): manifest['deliverable_report']={'path':report_path.name,'bytes':report_path.stat().st_size,'sha256':hashfile(report_path)}
(OUT/'NISSAN_BASE_TABLE_SET_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
print(json.dumps(summary,indent=2))


