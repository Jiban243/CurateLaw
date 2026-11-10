#!/usr/bin/env python3
"""Optional SOURCE ACQUISITION script for CurateLaw M1.
Download only if you have appropriate rights and access. Python standard library.
This does NOT mark usage rights as cleared. It never overwrites existing downloads.
"""
import argparse,csv,hashlib,json,time,urllib.request,urllib.parse,pathlib
p=argparse.ArgumentParser()
p.add_argument('--allow-uncleared',action='store_true',help='Explicit acknowledgement that this only acquires private research copies; NOT permission for redistribution or model training')
p.add_argument('--include-research',action='store_true')
p.add_argument('--max-mb',type=int,default=30)
a=p.parse_args()
if not a.allow_uncleared:
 p.error('Usage rights unverified; pass --allow-uncleared only if you have personally checked lawful access/use.')
base=pathlib.Path(__file__).resolve().parents[1]
out=base/'raw_sources'/'downloaded';out.mkdir(parents=True,exist_ok=True)
rows=list(csv.DictReader((base/'source_metadata.csv').open(encoding='utf-8')))
log=[]
for r in rows:
 if r['priority']=='methodology' and not a.include_research: continue
 url=r['source_url']; sid=r['source_id']
 ext=pathlib.PurePosixPath(urllib.parse.urlsplit(url).path).suffix.lower()
 if ext not in ['.pdf','.docx','.html','.htm','.txt']: ext='.html'
 dest=out/(sid+ext)
 if dest.exists():
  log.append(dict(source_id=sid,status='already_present',file=str(dest.relative_to(base)),sha256=hashlib.sha256(dest.read_bytes()).hexdigest()));continue
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'CurateLaw-India-Research/0.1 (+public sources; contact publishers for permissions)'})
  with urllib.request.urlopen(req,timeout=25) as resp:
   ct=resp.headers.get('Content-Type','')
   data=resp.read(a.max_mb*1024*1024+1)
  if len(data)>a.max_mb*1024*1024: raise ValueError('exceeds size limit')
  if b'<html' in data[:1000].lower() and ext in ('.pdf','.docx'):raise ValueError('HTML/login returned instead of expected document')
  dest.write_bytes(data)
  log.append(dict(source_id=sid,status='downloaded',file=str(dest.relative_to(base)),size_bytes=len(data),content_type=ct,sha256=hashlib.sha256(data).hexdigest()))
 except Exception as e:log.append(dict(source_id=sid,status='failed',error=str(e)[:300],url=url))
 time.sleep(0.2)
(base/'raw_sources'/'download_log.json').write_text(json.dumps(log,indent=2),encoding='utf-8')
print('Downloaded',sum(x['status']=='downloaded' for x in log),'of',len(log),'attempts; inspect download_log.json')
