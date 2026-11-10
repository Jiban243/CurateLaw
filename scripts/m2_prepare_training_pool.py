import json
import random
import hashlib
import re
from pathlib import Path
from collections import Counter

base = Path('data/m2')
eval_file = base / 'evaluation/heldout_eval_040.jsonl'
eval_manifest = base / 'evaluation/heldout_eval_manifest.json'
out = base / 'scenarios/train_pool_400.jsonl'
manifest_out = base / 'scenarios/train_pool_manifest.json'

expected_hash = json.loads(eval_manifest.read_text(encoding='utf-8'))['sha256']
actual_hash = hashlib.sha256(eval_file.read_bytes()).hexdigest()
if expected_hash != actual_hash:
    raise SystemExit('Evaluation dataset changed. Stopping to protect holdout.')
if out.exists() or manifest_out.exists():
    raise SystemExit('A training-pool file already exists. No overwrite performed.')

rng = random.Random(20261109)
roles = ['Platform Engineer','MLOps Specialist','Network Engineer','Data Scientist','Application Developer','UI Engineer','Release Engineer','IT Operations Analyst','Automation Engineer','Business Systems Analyst','Infrastructure Engineer','API Developer','Cloud Security Engineer','Data Quality Specialist','Product Engineer','Systems Developer']
states = ['Delhi','Karnataka','Maharashtra','Tamil Nadu','Telangana','Gujarat','Rajasthan','Kerala','West Bengal','Haryana','Odisha','Punjab']
modes = ['remote','hybrid','on-site']
counts = {'full_agreement':120,'clause_drafting':100,'contract_customization':80,'contradiction_correction':60,'missing_clause_completion':40}
rows = []

def add(kind, instruction, input_text, facts):
    rows.append({'task_type':kind,'instruction':instruction,'input':input_text,'expected_facts':facts,'scenario_origin':'programmatically_composed_original_brief','reference_text_copied':False,'split':'training_generation'})

for kind, count in counts.items():
    for j in range(count):
        role = rng.choice(roles)
        state = rng.choice(states)
        mode = rng.choice(modes)
        salary = rng.randrange(7,25)*100000 + rng.choice([0,25000,50000,75000])
        notice = rng.choice([30,45,60,75,90])
        probation = rng.choice([2,3,4,5,6])
        hours = rng.choice([35,38,40,42])
        facts = {'role':role,'state':state,'salary_inr':salary,'notice_days':notice,'probation_months':probation,'scheduled_weekly_hours':hours}
        prefix = f'For a fictional {role} employed in {state}, India, '
        guard = 'Do not invent legal rates, extra payment amounts, or post-employment non-competes; make contractual terms subject to applicable law.'
        if kind == 'full_agreement':
            inst = (prefix + f'draft an illustrative employment agreement with INR {salary} fixed annual salary, a {mode} work arrangement, {hours} scheduled hours per week, {probation} months of probation, and {notice} days of mutual notice. Include parties, appointment, duties, workplace, salary, probation, working time, leave, applicable statutory benefits, confidentiality, work-related IP, workplace policy, termination, disputes and signatures. Use party and date placeholders. ' + guard)
            inp = ''
        elif kind == 'clause_drafting':
            topic = j % 10
            prompts = [
                f'draft a probation clause with {probation} months initially and a possible one-month written extension',
                f'draft a mutual termination-notice clause with {notice} days written notice',
                'draft a confidentiality clause with public-domain and legally compelled-disclosure exceptions',
                'draft a work-related intellectual-property clause excluding unrelated pre-existing personal projects',
                f'draft a working-time clause with a {hours}-hour scheduled week, subject to applicable law',
                f'draft a contractual annual leave clause with {rng.choice([18,20,22,24])} days, subject to any greater legal entitlement',
                f'draft a workplace-location clause for a {mode} role, with reasonable prior notice for changes',
                'draft a workplace data-security clause describing reasonable access and incident reporting',
                'draft a grievance-reporting clause with non-retaliation protections',
                'draft an end-of-employment return-of-company-property clause that preserves statutory rights'
            ]
            inst = prefix + prompts[topic] + '. Return only the requested clause. ' + guard
            inp = ''
        elif kind == 'contract_customization':
            k = j % 4
            if k == 0:
                prior = salary-100000
                inp = f'The {role} will receive INR {prior} annually as fixed salary.'
                change = f'change only the annual fixed salary to INR {salary}'
            elif k == 1:
                prior = notice+15
                inp = f'Either party may terminate with {prior} days of prior written notice, subject to law.'
                change = f'change the mutual notice period to {notice} days'
            elif k == 2:
                inp = f'The {role} will work on-site at the employer office on all scheduled working days.'
                change = f'change the work arrangement to {mode}'
            else:
                inp = f'The {role} will ordinarily work 48 scheduled hours per week, subject to law.'
                change = f'change the scheduled week to {hours} hours, subject to law'
            inst = prefix + change + ' in the supplied fictional clause; preserve all unrelated conditions. Return only the revised clause. ' + guard
        elif kind == 'contradiction_correction':
            k = j % 5
            if k == 0:
                inp = f'The {role} receives annual pay of INR {salary}. The annual pay is also described as INR {salary+100000}.'
                change = f'Use INR {salary} consistently'
            elif k == 1:
                inp = f'The {role} has a probation period of {probation} months. The next paragraph says {probation+2} months.'
                change = f'Use {probation} months consistently'
            elif k == 2:
                inp = f'The notice period is {notice} days. A later provision says {notice+15} days.'
                change = f'Use {notice} days throughout'
            elif k == 3:
                inp = f'The employee is appointed as {role}. A later provision mistakenly describes the role as Sales Executive.'
                change = f'Make the role consistently {role}'
            else:
                inp = f'The scheduled work week is {hours} hours. The next clause calls the standard schedule 48 hours.'
                change = f'Use {hours} scheduled hours consistently'
            inst = prefix + 'correct the inconsistency in the supplied fictional text. ' + change + '. Return the corrected clause or clauses only. ' + guard
        else:
            topic = j % 5
            fragments = [
                f'Outline: {role}; {state}; salary INR {salary}; {mode} work. The appointment clause is missing.',
                f'Outline: {role}; {state}; salary INR {salary}; {mode} work. The working-hours clause is missing.',
                f'Outline: {role}; {state}; salary INR {salary}; {mode} work. The probation clause is missing.',
                f'Outline: {role}; {state}; salary INR {salary}; {mode} work. The termination-notice clause is missing.',
                f'Outline: {role}; {state}; salary INR {salary}; {mode} work. The confidentiality clause is missing.'
            ]
            inp = fragments[topic]
            objectives = [
                'Complete only the appointment provision, using joining-date placeholders',
                f'Complete only the working-hours provision using {hours} scheduled hours each week',
                f'Complete only the probation provision using {probation} months',
                f'Complete only the mutual notice provision using {notice} days, subject to applicable law',
                'Complete only the confidentiality provision with appropriate exceptions'
            ]
            inst = prefix + objectives[topic] + ' for the supplied outline. ' + guard
        add(kind, inst, inp, facts)

rng.shuffle(rows)
for i, row in enumerate(rows,1):
    row['scenario_id'] = f'GEN{i:04d}'


def normalized(record):
    return re.sub(r'\s+', ' ', record['instruction']+' '+record['input']).strip().casefold()

keys = [normalized(row) for row in rows]
if len(keys) != len(set(keys)):
    raise SystemExit('Duplicate generated training scenarios; stopping.')
heldout = [json.loads(line) for line in eval_file.read_text(encoding='utf-8').splitlines() if line.strip()]
heldout_keys = {normalized(row) for row in heldout}
if set(keys) & heldout_keys:
    raise SystemExit('Exact held-out overlap detected.')

out.parent.mkdir(parents=True,exist_ok=True)
with out.open('w',encoding='utf-8') as file:
    for row in rows:
        file.write(json.dumps(row,ensure_ascii=False)+'\n')
manifest = {'count':len(rows),'distribution':dict(Counter(x['task_type'] for x in rows)),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'heldout_sha256':actual_hash,'seed':20261109,'status':'scenario_prompts_only_not_training_data','exact_overlap_detected':False,'human_review':'pending'}
manifest_out.write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('Training scenarios:',len(rows))
print('Distribution:',manifest['distribution'])
print('Evaluation overlap:',0)
print('Training SHA256:',manifest['sha256'])
print('Saved:',out)
