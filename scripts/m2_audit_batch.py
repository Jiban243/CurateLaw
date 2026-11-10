import csv
import json
import re
from collections import Counter
from pathlib import Path

BASE = Path('data/m2')
SOURCE = BASE / 'generated_raw/pool_raw.jsonl'
OUT = BASE / 'quality_reports'
OUT.mkdir(parents=True, exist_ok=True)


def read_jsonl(path):
    return [json.loads(s) for s in path.read_text(encoding='utf-8').splitlines() if s.strip()]


def number_with_unit(text, value, unit):
    return bool(re.search(r'(?<!\d)' + re.escape(str(value)) + r'(?!\d)(?:\W+\w+){0,4}\W+' + unit + r'\b', text, re.I))


def amount_present(text, value):
    normalized = re.sub(r'[\s,₹]', '', text).lower()
    return str(value) in normalized


def target(pattern, instruction):
    match = re.search(pattern, instruction, re.I)
    return match.group(1) if match else None


def audit(row):
    task = row['task_type']
    instruction = row['instruction']
    source = row.get('input', '')
    answer = row.get('output', '')
    facts = row.get('expected_facts', {})
    issues = []
    warnings = []
    word_count = len(answer.split())

    if not answer.strip():
        issues.append('empty_response')
    if row.get('finish_reason') == 'length':
        issues.append('truncated_completion')
    if re.search(r'\b(?:as an ai|i cannot draft)\b', answer, re.I):
        issues.append('assistant_refusal_or_meta_text')
    if re.search(r'companies act\s*,?\s*2006', answer, re.I):
        warnings.append('possible_foreign_law_reference')
    if re.search(r'non[- ]compete|restraint of trade', answer, re.I):
        warnings.append('restrictive_covenant_review')
    if re.search(r'without (?:prior )?notice|summary dismissal', answer, re.I):
        warnings.append('notice_exception_review')
    if re.search(r'forfeit|automatic injunction|liquidated damages', answer, re.I):
        warnings.append('penalty_or_forfeiture_review')

    if task == 'full_agreement':
        if word_count < 350:
            issues.append('full_agreement_unusually_short')
        if facts.get('role') and facts['role'].casefold() not in answer.casefold():
            issues.append('role_not_detected')
        if facts.get('salary_inr') and not amount_present(answer, facts['salary_inr']):
            issues.append('salary_not_detected')
        for fact_key, unit in [('notice_days', 'days?'), ('probation_months', 'months?'), ('scheduled_weekly_hours', 'hours?')]:
            if facts.get(fact_key) is not None and not number_with_unit(answer, facts[fact_key], unit):
                issues.append(fact_key + '_not_detected')
        mode = target(r'\b(remote|hybrid|on-site) work arrangement', instruction)
        if mode and mode.casefold() not in answer.casefold():
            issues.append('work_mode_not_detected')
        if not re.search(r'(?m)^\s*(?:\#{1,6}\s*)?(?:\*\*)?\d{1,2}[.)]\s+[A-Za-z]', answer):
            warnings.append('numbered_headings_not_detected')
        required = ['appointment', 'salary', 'probation', 'confidential', 'termination', 'signature']
        absent = [part for part in required if part not in answer.casefold()]
        if absent:
            warnings.append('section_keywords_missing:' + ','.join(absent))

    elif task == 'contract_customization':
        if word_count > 350:
            warnings.append('possible_unrequested_expansion')
        new_salary = target(r'change only the annual fixed salary to INR\s*(\d+)', instruction)
        new_notice = target(r'change the mutual notice period to\s*(\d+) days?', instruction)
        new_hours = target(r'change the scheduled week to\s*(\d+) hours?', instruction)
        new_mode = target(r'change the work arrangement to\s*(remote|hybrid|on-site)', instruction)
        if new_salary:
            if not amount_present(answer, new_salary):
                issues.append('target_salary_missing')
            old = target(r'INR\s*(\d+)', source)
            if old and old != new_salary and amount_present(answer, old):
                issues.append('obsolete_salary_retained')
        elif new_notice:
            if not number_with_unit(answer, new_notice, 'days?'):
                issues.append('target_notice_missing')
            old = target(r'(\d+) days?', source)
            if old and old != new_notice and number_with_unit(answer, old, 'days?'):
                issues.append('obsolete_notice_retained')
        elif new_hours:
            if not number_with_unit(answer, new_hours, 'hours?'):
                issues.append('target_hours_missing')
            old = target(r'(\d+) scheduled hours?', source)
            if old and old != new_hours and number_with_unit(answer, old, 'hours?'):
                issues.append('obsolete_hours_retained')
        elif new_mode:
            if new_mode.casefold() not in answer.casefold():
                issues.append('target_work_mode_missing')
        else:
            warnings.append('customization_target_not_parsed')

    elif task == 'contradiction_correction':
        if word_count > 350:
            warnings.append('possible_unrequested_expansion')
        salary = target(r'use INR\s*(\d+) consistently', instruction)
        months = target(r'use (\d+) months? consistently', instruction)
        days = target(r'use (\d+) days? throughout', instruction)
        hours = target(r'use (\d+) scheduled hours? consistently', instruction)
        role = target(r'make the role consistently\s+([^.]+)', instruction)
        if salary:
            if not amount_present(answer, salary):
                issues.append('correct_salary_missing')
            originals = re.findall(r'INR\s*(\d+)', source, re.I)
            if any(v != salary and amount_present(answer, v) for v in originals):
                issues.append('contradictory_salary_retained')
        elif months:
            if not number_with_unit(answer, months, 'months?'):
                issues.append('correct_probation_missing')
            olds = re.findall(r'(\d+) months?', source, re.I)
            if any(v != months and number_with_unit(answer, v, 'months?') for v in olds):
                issues.append('contradictory_probation_retained')
        elif days:
            if not number_with_unit(answer, days, 'days?'):
                issues.append('correct_notice_missing')
            olds = re.findall(r'(\d+) days?', source, re.I)
            if any(v != days and number_with_unit(answer, v, 'days?') for v in olds):
                issues.append('contradictory_notice_retained')
        elif role:
            if role.casefold() not in answer.casefold():
                issues.append('correct_role_missing')
            if 'sales executive' in answer.casefold() and role.casefold() != 'sales executive':
                issues.append('contradictory_role_retained')
        elif hours:
            if not number_with_unit(answer, hours, 'hours?'):
                issues.append('correct_hours_missing')
            olds = re.findall(r'(\d+) hours?', source, re.I)
            if any(v != hours and number_with_unit(answer, v, 'hours?') for v in olds):
                issues.append('contradictory_hours_retained')
        else:
            warnings.append('correction_target_not_parsed')

    elif task in ('clause_drafting', 'missing_clause_completion'):
        if word_count < 20:
            warnings.append('clause_unusually_short')
        if word_count > 400:
            warnings.append('possible_unrequested_full_contract')
        if task == 'missing_clause_completion':
            for keyword, unit in [('scheduled hours', 'hours?'), ('probation', 'months?'), ('mutual notice', 'days?')]:
                if keyword in instruction.casefold():
                    n = target(r'using\s+(\d+)\s+(?:scheduled\s+)?(?:hours?|months?|days?)', instruction)
                    if n and not number_with_unit(answer, n, unit):
                        issues.append('requested_clause_value_missing')
                    break
    else:
        issues.append('unknown_task_type')

    return {
        'scenario_id': row['scenario_id'],
        'task_type': task,
        'word_count': word_count,
        'completion_tokens': row.get('completion_tokens', ''),
        'finish_reason': row.get('finish_reason', ''),
        'hard_check_failures': ';'.join(issues),
        'manual_review_flags': ';'.join(warnings),
        'screening_status': 'needs_manual_review' if issues or warnings else 'passed_heuristics',
        'approved_for_training': 'false'
    }


raw = read_jsonl(SOURCE)
if not raw:
    raise SystemExit('Raw pool is empty.')
ids = [row['scenario_id'] for row in raw]
if len(ids) != len(set(ids)):
    raise SystemExit('Duplicate scenario IDs detected in raw pool.')

reports = [audit(row) for row in raw]
report_path = OUT / 'M2_BATCH_QUALITY_AUDIT.csv'
with report_path.open('w', encoding='utf-8', newline='') as stream:
    writer = csv.DictWriter(stream, fieldnames=list(reports[0]))
    writer.writeheader()
    writer.writerows(reports)

summary = {
    'total_raw_generated': len(raw),
    'task_distribution': dict(Counter(r['task_type'] for r in raw)),
    'screening_distribution': dict(Counter(r['screening_status'] for r in reports)),
    'total_completion_tokens_if_reported': sum((r.get('completion_tokens') or 0) for r in raw),
    'training_approved': 0,
    'limitations': 'Heuristic screening only; not legal verification, factual certification, or permission clearance.'
}
summary_path = OUT / 'M2_BATCH_QUALITY_SUMMARY.json'
summary_path.write_text(json.dumps(summary, indent=2), encoding='utf-8')

print('Raw generated:', len(raw))
print('Task distribution:', summary['task_distribution'])
print('Screening distribution:', summary['screening_distribution'])
print('Completion tokens:', summary['total_completion_tokens_if_reported'])
for row in reports:
    print(row['scenario_id'], row['task_type'], 'words=' + str(row['word_count']),
          'status=' + row['screening_status'],
          'issues=' + (row['hard_check_failures'] or '-'),
          'review=' + (row['manual_review_flags'] or '-'))
print('Audit:', report_path)
print('Summary:', summary_path)
print('Training approved: 0')
