import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from getpass import getpass
from pathlib import Path
from huggingface_hub import InferenceClient

parser = argparse.ArgumentParser(description='Generate a small, resumable batch of synthetic contract training pairs.')
parser.add_argument('--limit', type=int, required=True, help='Maximum new teacher-model calls for this run (1-100).')
parser.add_argument('--model', default='Qwen/Qwen3-235B-A22B-Instruct-2507')
args = parser.parse_args()

if not 1 <= args.limit <= 100:
    raise SystemExit('Use a batch limit between 1 and 100.')

base = Path('data/m2')
scenarios_path = base / 'scenarios/train_pool_400.jsonl'
scenario_manifest_path = base / 'scenarios/train_pool_manifest.json'
evaluation_path = base / 'evaluation/heldout_eval_040.jsonl'
raw_path = base / 'generated_raw/pool_raw.jsonl'

manifest = json.loads(scenario_manifest_path.read_text(encoding='utf-8'))
actual_pool_hash = hashlib.sha256(scenarios_path.read_bytes()).hexdigest()
actual_eval_hash = hashlib.sha256(evaluation_path.read_bytes()).hexdigest()
if actual_pool_hash != manifest['sha256']:
    raise SystemExit('Training pool changed since creation; stopping.')
if actual_eval_hash != manifest['heldout_sha256']:
    raise SystemExit('Held-out evaluation set changed; stopping.')

scenarios = [json.loads(line) for line in scenarios_path.read_text(encoding='utf-8').splitlines() if line.strip()]
previous = [json.loads(line) for line in raw_path.read_text(encoding='utf-8').splitlines() if line.strip()] if raw_path.exists() else []
completed_ids = [row['scenario_id'] for row in previous]
if len(completed_ids) != len(set(completed_ids)):
    raise SystemExit('Duplicate scenario IDs in raw output. Please inspect before continuing.')

remaining = [row for row in scenarios if row['scenario_id'] not in set(completed_ids)]
selected = remaining[:args.limit]
if not selected:
    print('No ungenerated scenarios remain.')
    raise SystemExit(0)

print('Existing generated responses:', len(previous))
print('New teacher calls requested:', len(selected))
print('Teacher model:', args.model)
print('Selected tasks:', {x['task_type']:sum(r['task_type']==x['task_type'] for r in selected) for x in selected})
print('Remember to check your Hugging Face account billing and credit balance.')

token = os.environ.get('HF_TOKEN') or getpass('Hugging Face token (hidden): ')
client = InferenceClient(api_key=token, provider='auto')
raw_path.parent.mkdir(parents=True, exist_ok=True)

system_prompt = (
    'You produce original fictional Indian employment-contract drafting data for research. '
    'The user instruction and supplied input are the only factual specifications. '
    'Draft only what the task requests; do not introduce unrelated clauses. '
    'Preserve all salaries, dates, roles, working arrangements, notice periods and other facts. '
    'Avoid post-employment non-competes, fictional statutory rates and categorical legal-validity claims. '
    'Do not copy any pre-existing contract template. Return only the requested contract drafting text.'
)

for row in selected:
    sid = row['scenario_id']
    user_prompt = row['instruction']
    if row.get('input'):
        user_prompt += '\n\nSupplied fictional draft or context:\n' + row['input']
    max_tokens = 2400 if row['task_type'] == 'full_agreement' else 900
    print('Generating:', sid, row['task_type'], flush=True)
    try:
        response = client.chat.completions.create(
            model=args.model,
            messages=[{'role':'system','content':system_prompt},{'role':'user','content':user_prompt}],
            temperature=0.5,
            max_tokens=max_tokens
        )
        answer = response.choices[0].message.content
        if not isinstance(answer, str) or not answer.strip():
            print('Empty answer; stopping. No record saved for:', sid)
            break
        usage = getattr(response, 'usage', None)
        record = {
            'scenario_id':sid,
            'task_type':row['task_type'],
            'instruction':row['instruction'],
            'input':row['input'],
            'output':answer.strip(),
            'expected_facts':row['expected_facts'],
            'generation_model':args.model,
            'generation_temperature':0.5,
            'max_output_tokens':max_tokens,
            'finish_reason':getattr(response.choices[0], 'finish_reason', None),
            'prompt_tokens':getattr(usage,'prompt_tokens',None),
            'completion_tokens':getattr(usage,'completion_tokens',None),
            'created_at_utc':datetime.now(timezone.utc).isoformat(),
            'origin':'synthetic_teacher_generated',
            'legal_review_status':'unverified',
            'approved_for_training':False
        }
        with raw_path.open('a', encoding='utf-8') as file:
            file.write(json.dumps(record, ensure_ascii=False)+'\n')
        print('Saved:', sid, 'characters:', len(answer), 'completion tokens:',record['completion_tokens'],'finish:',record['finish_reason'])
    except Exception as exc:
        print('API error:',type(exc).__name__,str(exc)[:300])
        print('Saved earlier successful responses. Rerun to resume.')
        break

if raw_path.exists():
    total = sum(bool(line.strip()) for line in raw_path.read_text(encoding='utf-8').splitlines())
    print('Total raw pool responses:',total)
    print('Saved:',raw_path)
    print('No curation or training approval has been applied.')
