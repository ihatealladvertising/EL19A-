#!/usr/bin/env python3
"""Reproducible stdlib-only audit of A2L VALUE symbol order by ROM address."""
import argparse, bisect, collections, csv, hashlib, json, random, re, statistics
from pathlib import Path

CHAR = re.compile(r"/begin\s+CHARACTERISTIC\s+(\S+)([\s\S]*?)/end\s+CHARACTERISTIC", re.I)
DECL = re.compile(r"(?m)^\s*(VALUE|CURVE|MAP|CUBOID|CUBE_4|CUBE_5)\s+(0x[0-9A-Fa-f]+)\s+(\S+)")
NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
START, END, BLOCK = 0x8000, 0x97FF, 0x400

def sha256(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for b in iter(lambda:f.read(1048576),b""): h.update(b)
    return h.hexdigest()

def parse_a2l(path):
    raw=Path(path).read_bytes().decode("latin-1")
    starts=[0]+[i+1 for i,c in enumerate(raw) if c=="\n"]
    rows=[]; kinds=collections.Counter()
    for m in CHAR.finditer(raw):
        d=DECL.search(m.group(2))
        if not d: continue
        kind,addr,layout=d.groups(); kind=kind.upper(); kinds[kind]+=1
        rows.append({"name":m.group(1),"addr":int(addr,16),"kind":kind,"layout":layout,
                     "line":bisect.bisect_right(starts,m.start())})
    return rows,dict(kinds)

def unique_address_rows(rows):
    groups=collections.defaultdict(list)
    for r in rows: groups[r["addr"]].append(r)
    primary=sorted((min(g,key=lambda r:(r["line"],r["name"])) for g in groups.values()),
                   key=lambda r:(r["addr"],r["name"],r["line"]))
    return primary,groups

def stats(names):
    if not names: return {"n":0,"pairs":0,"ordered":0,"fraction":None,"runs":0,"max_run":0,"run_lengths":[]}
    ordered=0; cur=1; lengths=[]
    for a,b in zip(names,names[1:]):
        if a<=b: ordered+=1; cur+=1
        else: lengths.append(cur); cur=1
    lengths.append(cur)
    return {"n":len(names),"pairs":max(0,len(names)-1),"ordered":ordered,
            "fraction":ordered/(len(names)-1) if len(names)>1 else None,
            "runs":len(lengths),"max_run":max(lengths),"run_lengths":lengths}

def compact(names):
    ordered=0; cur=1; maximum=1
    for a,b in zip(names,names[1:]):
        if a<=b: ordered+=1; cur+=1
        else: maximum=max(maximum,cur); cur=1
    return ordered/(len(names)-1),max(maximum,cur)

def qtile(v,p):
    v=sorted(v); return v[min(len(v)-1,max(0,int(p*len(v)+0.999999999)-1))]

def nulls(rows,seed,reps):
    names=[r["name"] for r in rows]; blocks=collections.defaultdict(list)
    for i,r in enumerate(rows): blocks[r["addr"]//BLOCK].append(i)
    rng=random.Random(seed); gf=[];gm=[];bf=[];bm=[]; tmp=names[:]; btmp=names[:]
    for _ in range(reps):
        rng.shuffle(tmp); f,m=compact(tmp); gf.append(f);gm.append(m)
        btmp[:]=names
        for indexes in blocks.values():
            vals=[btmp[i] for i in indexes];rng.shuffle(vals)
            for i,v in zip(indexes,vals):btmp[i]=v
        f,m=compact(btmp);bf.append(f);bm.append(m)
    observed=stats(names)
    def summary(fr,mx):
        return {"adj_fraction_mean":statistics.mean(fr),"adj_fraction_p95":qtile(fr,.95),
                "longest_run_median":statistics.median(mx),"longest_run_p95":qtile(mx,.95),
                "longest_run_p99":qtile(mx,.99),
                "p_adj_fraction_ge_observed":(sum(x>=observed["fraction"] for x in fr)+1)/(reps+1),
                "p_longest_run_ge_observed":(sum(x>=observed["max_run"] for x in mx)+1)/(reps+1)}
    return {"repetitions":reps,"seed":seed,"block_size_bytes":BLOCK,"block_count":len(blocks),
            "global_permutation":summary(gf,gm),"within_1KiB_block_shuffle":summary(bf,bm)}

def prefix(names):
    if not names:return ""
    a,b=min(names),max(names);i=0
    while i<min(len(a),len(b)) and a[i]==b[i]:i+=1
    return a[:i]

def ranks(vals):
    order=sorted(range(len(vals)),key=lambda i:vals[i]); out=[0.0]*len(vals);i=0
    while i<len(order):
        j=i+1
        while j<len(order) and vals[order[j]]==vals[order[i]]:j+=1
        for k in range(i,j):out[order[k]]=(i+1+j)/2.0
        i=j
    return out

def spearman(rows):
    if len(rows)<2:return None
    x=list(range(1,len(rows)+1));y=ranks([r["name"] for r in rows])
    mx,my=statistics.mean(x),statistics.mean(y)
    cov=sum((a-mx)*(b-my) for a,b in zip(x,y))
    vx=sum((a-mx)**2 for a in x);vy=sum((b-my)**2 for b in y)
    return cov/(vx*vy)**.5 if vx and vy else None

def analyze(label,path,seed,reps):
    records,kinds=parse_a2l(path); values=[r for r in records if r["kind"]=="VALUE"]
    region=sorted((r for r in values if START<=r["addr"]<=END),key=lambda r:(r["addr"],r["name"],r["line"]))
    primary,groups=unique_address_rows(region); names=[r["name"] for r in primary]
    st=stats(names); run_segments=[]; start=0;cur=1
    for i in range(1,len(names)):
        if names[i-1]<=names[i]:cur+=1
        else:run_segments.append((start,i,cur));start=i;cur=1
    if names:run_segments.append((start,len(names),cur))
    longest=max(run_segments,key=lambda x:(x[2],-x[0]))
    seg=primary[longest[0]:longest[1]]
    allst=stats([r["name"] for r in region])
    allruns=[];start=0;cur=1;allnames=[r["name"] for r in region]
    for i in range(1,len(allnames)):
        if allnames[i-1]<=allnames[i]:cur+=1
        else:allruns.append((start,i,cur));start=i;cur=1
    if allnames:allruns.append((start,len(allnames),cur))
    all_long=max(allruns,key=lambda x:(x[2],-x[0]))
    aseg=region[all_long[0]:all_long[1]]
    full,fullgroups=unique_address_rows(values);fullst=stats([r["name"] for r in full])
    sub={}
    for lo in range(START,END+1,BLOCK):
        part=[r for r in primary if lo<=r["addr"]<lo+BLOCK]
        z=stats([r["name"] for r in part]);z.pop("run_lengths",None)
        sub["0x%05X-0x%05X"%(lo,lo+BLOCK-1)]=z
    pref=prefix(names)
    case=stats([x.casefold() for x in names])
    natural=stats([tuple((1,int(t)) if t.isdigit() else (0,t.casefold()) for t in re.split(r"(\d+)",x)) for x in names])
    stripped=stats([x[len(pref):] for x in names])
    def variant(pick):
        rr=sorted((pick(g) for g in groups.values()),key=lambda r:(r["addr"],r["name"],r["line"]))
        return stats([r["name"] for r in rr])["fraction"]
    dups=[g for g in groups.values() if len(g)>1]
    full_dups=[g for g in fullgroups.values() if len(g)>1]
    details={"length":longest[2],"start_address":"0x%05X"%seg[0]["addr"],"end_address":"0x%05X"%seg[-1]["addr"],
             "first_symbol":seg[0]["name"],"last_symbol":seg[-1]["name"],
             "first_source_line":seg[0]["line"],"last_source_line":seg[-1]["line"]}
    all_details={"length":all_long[2],"start_address":"0x%05X"%aseg[0]["addr"],"end_address":"0x%05X"%aseg[-1]["addr"],
                 "first_symbol":aseg[0]["name"],"last_symbol":aseg[-1]["name"]}
    summary={"source":{"path":str(path),"size_bytes":Path(path).stat().st_size,"sha256":sha256(path)},
      "declarations":{"characteristic_count":len(records),"kind_counts":kinds,"value_count":len(values)},
      "primary_region":{"range":"0x8000-0x97FF inclusive",
        "population_definition":"earliest source declaration per unique VALUE address; duplicate-address aliases reported separately",
        "raw_value_rows":len(region),"unique_addresses":len(groups),"duplicate_address_groups":len(dups),
        "rows_in_duplicate_groups":sum(map(len,dups)),"extra_alias_rows":sum(len(g)-1 for g in dups),
        "primary_count":len(primary),"adjacency_and_runs":{k:v for k,v in st.items() if k!="run_lengths"},
        "longest_run":details,"spearman_rho":spearman(primary),"subregions_1KiB":sub,
        "sensitivity":{"casefold_fraction":case["fraction"],"natural_sort_fraction":natural["fraction"],
          "common_prefix":pref,"prefix_stripped_fraction":stripped["fraction"],
          "nonascii_count":sum(not r["name"].isascii() for r in primary),
          "malformed_count":sum(not NAME.fullmatch(r["name"]) for r in primary),
          "last_declaration_representative_fraction":variant(lambda g:max(g,key=lambda r:(r["line"],r["name"]))),
          "lexicographic_first_representative_fraction":variant(lambda g:min(g,key=lambda r:(r["name"],r["line"]))),
          "lexicographic_last_representative_fraction":variant(lambda g:max(g,key=lambda r:(r["name"],-r["line"]))),
          "all_declarations_including_aliases":{k:v for k,v in allst.items() if k!="run_lengths"},
          "all_declarations_longest_run":all_details},
        "null_model":nulls(primary,seed,reps)},
      "full_address_range":{"unique_value_addresses":len(full),"duplicate_address_groups":len(full_dups),
        "rows_in_duplicate_groups":sum(map(len,full_dups)),
        "adjacency_and_runs":{k:v for k,v in fullst.items() if k!="run_lengths"}}}
    run_for={}
    for rid,(a,b,n) in enumerate(run_segments,1):
        for i in range(a,b):run_for[i]=(rid,n)
    rows=[]
    for i,r in enumerate(primary):
        rid,rlen=run_for[i];g=groups[r["addr"]]
        rows.append({"donor":label,"record_role":"PRIMARY_UNIQUE_ADDRESS","address":"0x%05X"%r["addr"],
          "symbol":r["name"],"record_type":r["kind"],"record_layout":r["layout"],"source_line":r["line"],
          "duplicate_group_size":len(g),"primary_representative":r["name"],"sorted_index":i+1,
          "previous_symbol":names[i-1] if i else "","next_symbol":names[i+1] if i+1<len(names) else "",
          "adjacent_nondecreasing_from_previous":str(names[i-1]<=r["name"]).lower() if i else "",
          "ascending_run_id":rid,"ascending_run_length":rlen})
    for addr,g in groups.items():
        if len(g)<2:continue
        rep=min(g,key=lambda r:(r["line"],r["name"]))
        for r in g:
            if r is rep:continue
            rows.append({"donor":label,"record_role":"DUPLICATE_ADDRESS_ALIAS","address":"0x%05X"%addr,
              "symbol":r["name"],"record_type":r["kind"],"record_layout":r["layout"],"source_line":r["line"],
              "duplicate_group_size":len(g),"primary_representative":rep["name"],"sorted_index":"",
              "previous_symbol":"","next_symbol":"","adjacent_nondecreasing_from_previous":"",
              "ascending_run_id":"","ascending_run_length":""})
    rows.sort(key=lambda r:(int(r["address"],16),0 if r["record_role"]=="PRIMARY_UNIQUE_ADDRESS" else 1,r["source_line"],r["symbol"]))
    return summary,rows

def write_outputs(v6,juke,out_tsv,out_json,expected_v6=None,expected_juke=None,seed=20261128,repetitions=10000):
    for path,expected,label in ((v6,expected_v6,"V6"),(juke,expected_juke,"Juke")):
        actual=sha256(path)
        if expected and actual.lower()!=expected.lower():
            raise ValueError("%s source SHA-256 mismatch: expected %s, got %s"%(label,expected,actual))
    a,ar=analyze("V6",v6,seed,repetitions);b,br=analyze("Juke",juke,seed+100000,repetitions)
    fields=["donor","record_role","address","symbol","record_type","record_layout","source_line",
      "duplicate_group_size","primary_representative","sorted_index","previous_symbol","next_symbol",
      "adjacent_nondecreasing_from_previous","ascending_run_id","ascending_run_length"]
    with open(out_tsv,"w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,delimiter="\t",lineterminator="\n");w.writeheader();w.writerows(ar+br)
    result={"method_version":"1.0","region":{"start":"0x8000","end_inclusive":"0x97FF","subregion_size_bytes":BLOCK},
      "primary_population":"CHARACTERISTIC records with record type VALUE; earliest declaration per unique ROM address; aliases retained separately",
      "sort":"numeric ROM address ascending; deterministic name and source-line tie-breaks",
      "adjacency":"case-sensitive ordinal; left <= right","run":"maximal contiguous nondecreasing symbol sequence",
      "null":"10,000 seeded global permutations and within-1KiB-block shuffles per donor; add-one empirical p-values",
      "donors":{"V6":a,"Juke":b},
      "output_tsv":{"path":str(out_tsv),"sha256":sha256(out_tsv),"row_count":len(ar)+len(br)}}
    with open(out_json,"w",encoding="utf-8",newline="\n") as f:json.dump(result,f,indent=2,sort_keys=True,ensure_ascii=False);f.write("\n")
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--v6-a2l",required=True);p.add_argument("--juke-a2l",required=True)
    p.add_argument("--out-tsv",required=True);p.add_argument("--out-json",required=True)
    p.add_argument("--expected-v6-sha256");p.add_argument("--expected-juke-sha256")
    p.add_argument("--seed",type=int,default=20261128);p.add_argument("--repetitions",type=int,default=10000)
    a=p.parse_args()
    print(json.dumps(write_outputs(a.v6_a2l,a.juke_a2l,a.out_tsv,a.out_json,a.expected_v6_sha256,
      a.expected_juke_sha256,a.seed,a.repetitions),indent=2,sort_keys=True,ensure_ascii=False))

if __name__=="__main__": main()
