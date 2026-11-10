#!/usr/bin/env python3
import csv,json,pathlib,collections
root=pathlib.Path(__file__).resolve().parents[1]
s=list(csv.DictReader((root/'source_metadata.csv').open(encoding='utf-8')))
c=list(csv.DictReader((root/'extracted_clauses'/'clauses.csv').open(encoding='utf-8')))
assert len({r['source_id'] for r in s})==len(s)
assert len({r['clause_id'] for r in c})==len(c)
assert all(x['source_id'] in {r['source_id'] for r in s} for x in c)
assert all(x['source_url'].startswith('https://') for x in s)
assert all(x['source_locator'] for x in c)
assert all(x['verbatim_quote']=='' for x in c)
print('PASS',len(s),'sources;',len(c),'normalized clause observations; categories:',len({x['category'] for x in c}))
print('RAW ORIGINALS BUNDLED:',sum(r['raw_original_included']=='yes' for r in s),'(see README before marking M1 complete)')
print('Inspection statuses:',dict(collections.Counter(x['inspection_status'] for x in s)))
