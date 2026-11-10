#!/usr/bin/env python3
"""Optional post-download extraction for sources where lawful local text processing is permitted.

python tools/extract_local_documents.py --permit-local-extraction

Reads raw_sources/downloaded/SOURCE_ID.pdf|.docx|.html, writes page-marked
processed_sources/full_text_local/SOURCE_ID.txt and SHA256-based reports.
NOT for redistribution; only run with appropriate rights.
"""
import argparse,csv,hashlib,json,pathlib,re,collections
p=argparse.ArgumentParser()
p.add_argument('--permit-local-extraction',action='store_true')
a=p.parse_args()
if not a.permit_local_extraction: p.error('Review each source licence; explicitly opt in with --permit-local-extraction.')
root=pathlib.Path(__file__).resolve().parents[1]
folder=root/'raw_sources'/'downloaded'
out=root/'processed_sources'/'full_text_local';out.mkdir(parents=True,exist_ok=True)
meta={r['source_id']:r for r in csv.DictReader((root/'source_metadata.csv').open(encoding='utf8'))}
report=[]
for f in sorted(folder.glob('*')):
 if not f.is_file():continue
 sid=f.stem
 if sid not in meta:continue
 try:
  b=f.read_bytes();orig_hash=hashlib.sha256(b).hexdigest()
  if f.suffix.lower()=='.pdf':
   import fitz
   doc=fitz.open(f)
   pages=[f'[[PDF PAGE {i+1}]]\n'+page.get_text('text') for i,page in enumerate(doc)]
   raw='\n\n'.join(pages)
  elif f.suffix.lower()=='.docx':
   from docx import Document
   d=Document(f)
   raw='\n'.join(x.text for x in d.paragraphs if x.text.strip())
   for table in d.tables:
    for row in table.rows:
     raw+='\n'+' | '.join(cell.text for cell in row.cells)
  elif f.suffix.lower() in ('.html','.htm'):
   from html.parser import HTMLParser
   class Grab(HTMLParser):
    def __init__(self):super().__init__();self.buf=[];self.skip=0
    def handle_starttag(self,tag,attrs):
     if tag in ('script','style'):self.skip+=1
     if tag in ('p','li','br','h1','h2','h3'):self.buf.append('\n')
    def handle_endtag(self,tag):
     if tag in ('script','style') and self.skip:self.skip-=1
    def handle_data(self,s):
     if not self.skip:self.buf.append(s)
   parser=Grab();parser.feed(b.decode('utf8','replace'));raw=' '.join(parser.buf)
  else: raw=b.decode('utf8','replace')
  raw=raw.replace('\r\n','\n').replace('\r','\n')
  raw=re.sub(r'[ \t]+',' ',raw)
  raw=re.sub(r'\n{4,}','\n\n\n',raw).strip()
  if len(raw)<150:raise ValueError('too little extracted text; likely scanned or login page')
  dest=out/(sid+'.txt');dest.write_text(raw+'\n',encoding='utf8')
  report.append({'source_id':sid,'status':'extracted','original_sha256':orig_hash,'text_sha256':hashlib.sha256(raw.encode()).hexdigest(),'characters':len(raw),'file':str(dest.relative_to(root))})
 except Exception as e:report.append({'source_id':sid,'status':'failed','error':str(e)[:250]})
(root/'processed_sources'/'local_extract_log.json').write_text(json.dumps(report,indent=2),encoding='utf8')
from collections import defaultdict
groups=defaultdict(list)
for r in report:
 if 'text_sha256' in r:groups[r['text_sha256']].append(r['source_id'])
(root/'extracted_clauses'/'postdownload_content_dedup.json').write_text(json.dumps({'exact_duplicate_extracted_text_groups':[v for v in groups.values() if len(v)>1],'note':'Near-duplicate detection needs manual content comparison; file hashes alone miss revisions.'},indent=2),encoding='utf8')
print('Extracted',sum(x['status']=='extracted' for x in report),'/',len(report))
