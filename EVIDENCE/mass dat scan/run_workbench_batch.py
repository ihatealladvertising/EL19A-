from __future__ import annotations
import csv, gzip, hashlib, json, os, sys, tempfile, time, zipfile, io
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path, PurePosixPath
import multiprocessing
ROOT=Path(r"E:\Nissan Consult\ReproProgramming")
OUT=ROOT/"_SH705xWorkbench_Run_2026-11-27"
WBROOT=Path(r"C:\Users\Vivian\Documents\Codex\2026-11-27\co\work\EL19A-align")
RUNTIME=Path(r"C:\Users\Vivian\Documents\Codex\2026-11-27\co\work\py7zr_runtime")
sys.path.insert(0,str(WBROOT/"tools")); sys.path.insert(0,str(RUNTIME))
import py7zr
import nissan_sh705x_workbench as wb
from sh705x_rom_loader import load_dat_bytes,load_hex_bytes,load_s19_bytes,_check_nonflat_container
from sh7058_cross_rom_scanner import discover_helpers,extract_calls

def sha(b): return hashlib.sha256(b).hexdigest()
def safe(n):
 p=PurePosixPath(n.replace("\\","/"))
 return not p.is_absolute() and ".." not in p.parts
def add(groups,codec,digest,src):
 key=codec+":"+digest
 groups.setdefault(key,{"key":key,"codec":codec,"sha256":digest,"sources":[]})["sources"].append(src)
def extract7(path,member):
 if not safe(member): raise ValueError("unsafe archive path")
 with tempfile.TemporaryDirectory(prefix="shx_",dir=str(OUT/"scratch")) as td:
  root=Path(td)
  with py7zr.SevenZipFile(path,"r") as z: z.extract(path=root,targets=[member])
  p=root.joinpath(*PurePosixPath(member.replace("\\","/")).parts)
  if not p.is_file():
   ms=[x for x in root.rglob("*") if x.is_file() and x.name==Path(member).name]
   if len(ms)!=1: raise FileNotFoundError(member)
   p=ms[0]
  return p.read_bytes()
def add_zip_bin(groups,path,rel,fmt,archives):
 try:
  with zipfile.ZipFile(path) as z:
   infos=[x for x in z.infolist() if not x.is_dir()]
   archives.append({"path":rel,"format":fmt,"status":"READ_OK","member_count":len(infos),"error":""})
   for x in infos:
    ext=Path(x.filename).suffix.lower()
    if ext not in {".bin",".dat",".hex",".s19"} or not safe(x.filename): continue
    raw=z.read(x.filename); codec="dat" if ext==".dat" else "hex" if ext==".hex" else "srec" if ext==".s19" else "raw"
    add(groups,codec,sha(raw),{"source":rel+"!"+x.filename,"container":rel,"member":x.filename,"kind":"zip_member","size_bytes":len(raw)})
 except Exception as e: archives.append({"path":rel,"format":fmt,"status":"ARCHIVE_READ_FAILED","member_count":0,"error":f"{type(e).__name__}: {e}"})
def build_tasks(inventory):
 groups={}; archives=[]
 prior=json.loads(Path(r"C:\Users\Vivian\Documents\Codex\2026-11-27\co\work\reproprogramming_rom_inventory.json").read_text(encoding="utf-8"))
 hashes={x["relative"]:x["sha256"] for x in prior["files"]}
 for row in inventory:
  rel=row["relative"]; p=ROOT/rel; ext=p.suffix.lower()
  if ext in {".dat",".bin",".hex",".s19"}:
   codec="dat" if ext==".dat" else "hex" if ext==".hex" else "srec" if ext==".s19" else "raw"
   digest=hashes.get(rel) or sha(p.read_bytes())
   row["sha256"]=digest
   add(groups,codec,digest,{"source":rel,"container":rel,"member":"","kind":"direct","size_bytes":row["size_bytes"]})
  elif ext in {".zip",".pdx"}: add_zip_bin(groups,p,rel,"ZIP" if ext==".zip" else "PDX/ZIP",archives)
  elif ext==".7z":
   try:
    with py7zr.SevenZipFile(p,"r") as z: infos=[x for x in z.list() if not x.is_directory]
    archives.append({"path":rel,"format":"7z","status":"READ_OK","member_count":len(infos),"error":""})
    for x in infos:
     n=x.filename
     if not safe(n): continue
     ex=Path(n).suffix.lower()
     if ex not in {".bin",".dat",".hex",".s19",".mot",".pdx",".zip"}: continue
     raw=extract7(p,n)
     if ex in {".pdx",".zip"}:
      try: add_zip_bin(groups,io.BytesIO(raw),rel+"!"+n,"nested PDX/ZIP",archives)
      except Exception as e: archives.append({"path":rel+"!"+n,"format":"nested ZIP","status":"ARCHIVE_READ_FAILED","member_count":0,"error":str(e)})
      continue
     codec="dat" if ex==".dat" else "hex" if ex==".hex" else "srec" if ex in {".s19",".mot"} else "raw"
     add(groups,codec,sha(raw),{"source":rel+"!"+n,"container":rel,"member":n,"kind":"7z_member","size_bytes":len(raw)})
   except Exception as e: archives.append({"path":rel,"format":"7z","status":"ARCHIVE_READ_FAILED","member_count":0,"error":f"{type(e).__name__}: {e}"})
 return list(groups.values()),archives
def load_source(task):
 s=task["sources"][0]; k=s["kind"]
 if k=="direct": return (ROOT/s["container"]).read_bytes()
 if k=="zip_member":
  with zipfile.ZipFile(ROOT/s["container"]) as z: return z.read(s["member"])
 if k=="7z_member": return extract7(ROOT/s["container"],s["member"])
 raise ValueError("unknown source kind: "+k)
def scan_task(task):
 try:
  raw=load_source(task)
  if sha(raw)!=task["sha256"]: raise ValueError("source payload changed after inventory")
  c=task["codec"]
  rom=load_dat_bytes(raw) if c=="dat" else load_hex_bytes(raw) if c=="hex" else load_s19_bytes(raw) if c=="srec" else raw
  if c=="raw": _check_nonflat_container(raw,task["sources"][0]["source"])
  fp=wb.rom_fingerprint(rom); hs=discover_helpers(rom); calls=extract_calls(rom,hs); tables=wb.summarize_tables(rom,calls)
  meta=fp["nissan_meta"]; hk=dict(Counter(h.kind for h in hs.values()))
  out={"input_key":task["key"],"codec":c,"input_sha256":task["sha256"],"sources":[x["source"] for x in task["sources"]],
       "source_count":len(task["sources"]),"status":"SCANNED","decoded_rom_sha256":fp["sha256"],"rom_size_bytes":fp["size"],
       "cpu_tags":fp["cpu_tags"],"fid_tags":fp["fid_tags"],"loader":meta.get("loader"),"helpers":len(hs),"helper_kinds":hk,
       "call_sites":len(calls),"resolved_calls":sum(ca["table"] is not None for ca in calls),"unique_tables":len(tables),"error":""}
  detail=None
  if hs or tables:
   detail={"input_key":task["key"],"input_sha256":task["sha256"],"sources":out["sources"],"fingerprint":fp,
           "helpers":{f"0x{k:05X}":vars(v) for k,v in sorted(hs.items())},
           "tables":{f"0x{a:05X}":{k:v for k,v in t.items() if k!="payload"} for a,t in sorted(tables.items())}}
  return out,detail
 except Exception as e:
  return {"input_key":task["key"],"codec":task["codec"],"input_sha256":task["sha256"],
          "sources":[x["source"] for x in task["sources"]],"source_count":len(task["sources"]),
          "status":"LOAD_REJECTED","decoded_rom_sha256":"","rom_size_bytes":0,"cpu_tags":[],"fid_tags":[],
          "loader":"","helpers":0,"helper_kinds":{},"call_sites":0,"resolved_calls":0,"unique_tables":0,
          "error":f"{type(e).__name__}: {e}"},None

def main():
 (OUT/"scratch").mkdir(parents=True,exist_ok=True)
 files=sorted(p for p in ROOT.rglob("*") if p.is_file() and OUT not in p.parents)
 inventory=[]
 for p in files:
  rel=str(p.relative_to(ROOT)); e=p.suffix.lower()
  cls="DIRECT_WORKBENCH_INPUT" if e in {".dat",".bin",".hex",".s19"} else "ZIP_PACKAGE" if e in {".pdx",".zip"} else "7Z_PACKAGE" if e==".7z" else "ANCILLARY_OR_UNSUPPORTED"
  inventory.append({"relative":rel,"extension":e,"size_bytes":p.stat().st_size,"sha256":"","classification":cls})
 # Hash all archive containers; direct DAT/BIN payload hashes are reused from the finished byte census.
 for r in inventory:
  p=ROOT/r["relative"]
  if r["classification"] in {"ZIP_PACKAGE","7Z_PACKAGE"}:
   h=hashlib.sha256()
   with p.open("rb") as f:
    for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
   r["sha256"]=h.hexdigest()
 tasks,archives=build_tasks(inventory)
 with (OUT/"file_inventory.tsv").open("w",encoding="utf-8",newline="") as f:
  w=csv.DictWriter(f,fieldnames=["relative","extension","size_bytes","sha256","classification"],delimiter="\t",lineterminator="\n"); w.writeheader(); w.writerows(inventory)
 with (OUT/"archive_inventory.tsv").open("w",encoding="utf-8",newline="") as f:
  w=csv.DictWriter(f,fieldnames=["path","format","status","member_count","error"],delimiter="\t",lineterminator="\n"); w.writeheader(); w.writerows(archives)
 (OUT/"candidate_tasks.json").write_text(json.dumps(tasks,indent=2)+"\n",encoding="utf-8")
 print(f"files={len(inventory)} unique_scan_inputs={len(tasks)} candidate_references={sum(len(t['sources']) for t in tasks)} archives={len(archives)}",flush=True)
 stats=Counter(); rowcount=detailcount=0; start=time.time()
 cols=["input_key","codec","input_sha256","source","source_count","status","decoded_rom_sha256","rom_size_bytes","cpu_tags","fid_tags","loader","helpers","helper_kinds","call_sites","resolved_calls","unique_tables","error"]
 with (OUT/"scan_results.tsv").open("w",encoding="utf-8",newline="") as tf, gzip.open(OUT/"scan_details.jsonl.gz","wt",encoding="utf-8") as df:
  w=csv.DictWriter(tf,fieldnames=cols,delimiter="\t",lineterminator="\n"); w.writeheader()
  ctx=multiprocessing.get_context("spawn")
  with ProcessPoolExecutor(max_workers=min(8,os.cpu_count() or 2),mp_context=ctx) as pool:
   futures={pool.submit(scan_task,t):t for t in tasks}; done=0
   for fu in as_completed(futures):
    result,detail=fu.result(); done+=1; stats[result["status"]]+=1
    if detail is not None: df.write(json.dumps(detail,separators=(",",":"),ensure_ascii=False)+"\n"); detailcount+=1
    task=futures[fu]
    for s in result["sources"]:
     w.writerow({"input_key":result["input_key"],"codec":result["codec"],"input_sha256":result["input_sha256"],
       "source":s,"source_count":result["source_count"],"status":result["status"],"decoded_rom_sha256":result["decoded_rom_sha256"],
       "rom_size_bytes":result["rom_size_bytes"],"cpu_tags":json.dumps(result["cpu_tags"],separators=(",",":")),
       "fid_tags":json.dumps(result["fid_tags"],separators=(",",":")),"loader":result["loader"],"helpers":result["helpers"],
       "helper_kinds":json.dumps(result["helper_kinds"],sort_keys=True,separators=(",",":")),"call_sites":result["call_sites"],
       "resolved_calls":result["resolved_calls"],"unique_tables":result["unique_tables"],"error":result["error"]}); rowcount+=1
    if done%100==0:
     tf.flush(); df.flush()
     progress={"completed":done,"total":len(tasks),"candidate_rows":rowcount,"statuses":dict(stats),"elapsed_seconds":round(time.time()-start,1)}
     (OUT/"progress.json").write_text(json.dumps(progress,indent=2)+"\n",encoding="utf-8"); print(json.dumps(progress),flush=True)
 summary={"root":str(ROOT),"output":str(OUT),"python":sys.version.split()[0],"py7zr":py7zr.__version__,
  "workbench_commit":"13acc0b58826c2b693ef495a0b3c61259daec760","source_files":len(inventory),
  "inventory_classes":dict(Counter(x["classification"] for x in inventory)),"unique_scan_inputs":len(tasks),
  "candidate_reference_rows":rowcount,"scan_statuses":dict(stats),"archives":len(archives),
  "archive_statuses":dict(Counter(x["status"] for x in archives)),"detailed_scans":detailcount,
  "elapsed_seconds":round(time.time()-start,1),"outputs":{}}
 for name in ["file_inventory.tsv","archive_inventory.tsv","candidate_tasks.json","scan_results.tsv","scan_details.jsonl.gz"]:
  p=OUT/name; summary["outputs"][name]={"bytes":p.stat().st_size,"sha256":sha(p.read_bytes())}
 (OUT/"run_manifest.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
 (OUT/"progress.json").write_text(json.dumps({"state":"COMPLETE",**summary},indent=2)+"\n",encoding="utf-8")
 print(json.dumps({"state":"COMPLETE",**summary},indent=2),flush=True)
if __name__=="__main__": main()
