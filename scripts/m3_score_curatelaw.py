import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path('data/m2')
FROZEN = ROOT / 'frozen/pool_raw_0400.jsonl'
MANIFEST = ROOT / 'frozen/freeze_manifest.json'
AUDIT = ROOT / 'quality_reports/M2_BATCH_QUALITY_AUDIT.csv'
EVAL = ROOT / 'frozen/heldout_eval_040.jsonl'
OUT = Path('data/m3/domain_curation')
EXPECTED = {'full_agreement': 120, 'clause_drafting': 100,
            'contract_customization': 80, 'contradiction_correction': 60,
            'missing_clause_completion': 40}
QUOTAS = {'full_agreement': 45, 'clause_drafting': 38,
          'contract_customization': 30, 'contradiction_correction': 22,
          'missing_clause_completion': 15}


def read_jsonl(path):
    with path.open(encoding='utf-8') as handle:
        return [json.loads(line) for line in handle if line.strip()]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def norm(text):
    return re.sub(r'\s+', ' ', str(text)).strip().casefold()


def number_with_unit(text, value, unit):
    pat = r'(?<!\d)' + re.escape(str(value)) + r'(?!\d)(?:\W+\w+){0,5}\W+' + unit + r'\b'
    return bool(re.search(pat, text, re.I))


def has_amount(text, number):
    cleaned = re.sub(r'[\s,₹]', '', text).casefold()
    return str(number) in cleaned


def numbered_sections(text):
    pat = r'(?m)^\s*(?:\#{1,6}\s*)?(?:\*\*|__)?\s*\d{1,2}[.)](?:\s|$)'
    return len(re.findall(pat, text))


def has_execution(text):
    tail = text[-2000:]
    return all([
        re.search(r'in witness whereof|executed this agreement|signed by', tail, re.I),
        re.search(r'employer|company', tail, re.I),
        re.search(r'employee', tail, re.I),
        re.search(r'signature|signatory|_{5,}', tail, re.I),
    ])


def score_row(record, old_audit, duplicated_output):
    sid = record['scenario_id']
    task = record['task_type']
    answer = record.get('output', '')
    instruction = record.get('instruction', '')
    input_text = record.get('input', '')
    facts = record.get('expected_facts') or {}
    raw_issues = list(filter(None, old_audit.get('hard_check_failures', '').split(';')))
    raw_warnings = list(filter(None, old_audit.get('manual_review_flags', '').split(';')))
    hard = []
    review = []
    score = 100

    if not answer.strip():
        hard.append('empty_response')
    if record.get('finish_reason') == 'length':
        hard.append('truncated_generation')
    if re.search(r'\b(as an ai|i cannot draft)\b', answer, re.I):
        hard.append('refusal_or_meta_response')

    for issue in raw_issues:
        if issue == 'full_agreement_unusually_short' or issue == 'contradictory_role_retained':
            hard.append(issue)
        else:
            review.append('audit_hard_check:' + issue)
            score -= 12

    if task == 'full_agreement':
        if len(answer.split()) < 350:
            hard.append('incomplete_full_agreement')
        role = facts.get('role')
        if role and norm(role) not in norm(answer):
            review.append('scenario_role_not_present')
            score -= 14
        salary = facts.get('salary_inr')
        if salary is not None and not has_amount(answer, salary):
            review.append('scenario_salary_not_present')
            score -= 14
        for key, unit in [('notice_days', 'days?'),
                          ('probation_months', 'months?'),
                          ('scheduled_weekly_hours', 'hours?')]:
            value = facts.get(key)
            if value is not None and not number_with_unit(answer, value, unit):
                review.append('scenario_' + key + '_not_present')
                score -= 10
        if numbered_sections(answer) < 5:
            review.append('numbered_structure_review')
            score -= 5
        if not has_execution(answer):
            review.append('execution_section_review')
            score -= 6
    elif task in ('contract_customization', 'contradiction_correction'):
        if len(answer.split()) > 350:
            review.append('possible_overlong_revision')
            score -= 5
    elif task in ('clause_drafting', 'missing_clause_completion'):
        if len(answer.split()) < 20:
            review.append('unusually_short_clause')
            score -= 8
        if len(answer.split()) > 400:
            review.append('possible_unrequested_expansion')
            score -= 5
    else:
        hard.append('unknown_task_type')

    if re.search(r'\bindustrial disputes act\s*,?\s*1947\b', answer, re.I):
        review.append('legacy_industrial_disputes_act_reference')
        score -= 18
    if re.search(r'\bcompanies act\s*,?\s*2006\b', answer, re.I):
        review.append('possible_uk_legislation_reference')
        score -= 18
    if re.search(r'\bnon[ -]?compete\b|\brestraint of trade\b', answer, re.I):
        review.append('restrictive_covenant_context_review')
        score -= 10
    if re.search(r'without (?:prior )?notice|summary dismissal', answer, re.I):
        if re.search(r'(?:salary|pay(?:ment)?) in lieu', answer, re.I):
            review.append('notice_in_lieu_applicability_review')
            score -= 4
        else:
            review.append('immediate_termination_context_review')
            score -= 8
    if re.search(r'forfeit(?:ure)?|automatic injunction|liquidated damages', answer, re.I):
        review.append('penalty_or_forfeiture_context_review')
        score -= 12

    if duplicated_output:
        review.append('identical_response_other_scenario')
        score -= 3

    for warning in raw_warnings:
        if warning == 'numbered_headings_not_detected' and numbered_sections(answer) >= 5:
            continue
        if warning == 'section_keywords_missing:signature' and has_execution(answer):
            continue
        if warning == 'notice_exception_review':
            continue
        if warning.startswith('section_keywords_missing:'):
            missing = warning.split(':', 1)[1]
            if missing == 'signature' and has_execution(answer):
                continue
            review.append('keyword_coverage_review:' + missing)
            score -= 6
        elif warning == 'numbered_headings_not_detected':
            review.append('heading_format_review')
        elif warning not in ('notice_exception_review',):
            review.append('audit_review:' + warning)
            score -= 5

    score = max(0, min(100, score))
    hard = sorted(set(hard))
    review = sorted(set(review))
    if hard:
        tier = 'exclude_provisional'
    elif review or score < 85:
        tier = 'hold_manual_review'
    else:
        tier = 'strong_screening_candidate'

    return {
        'scenario_id': sid,
        'task_type': task,
        'quality_score_heuristic': score,
        'screening_tier': tier,
        'hard_failure_reasons': ';'.join(hard),
        'review_reasons': ';'.join(review),
        'previous_audit_status': old_audit.get('screening_status', ''),
        'word_count': len(answer.split()),
        'output_duplicate_candidate': str(duplicated_output).lower(),
        'human_review_status': 'pending',
        'legal_review_status': 'pending',
        'approved_for_training': 'false'
    }


def main():
    for p in (FROZEN, MANIFEST, AUDIT, EVAL):
        if not p.exists():
            raise SystemExit(f'Missing required file: {p}')
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
    if manifest['raw_sha256'] != sha256(FROZEN):
        raise SystemExit('Raw freeze checksum mismatch. Stopping.')
    if manifest['eval_sha256'] != sha256(EVAL):
        raise SystemExit('Evaluation freeze checksum mismatch. Stopping.')
    raw = read_jsonl(FROZEN)
    if len(raw) != 400 or {r['scenario_id'] for r in raw} != {f'GEN{i:04d}' for i in range(1, 401)}:
        raise SystemExit('Expected 400 frozen GEN IDs, exactly once each.')
    with AUDIT.open(encoding='utf-8', newline='') as f:
        audits = list(csv.DictReader(f))
    audit_by_id = {r['scenario_id']: r for r in audits}
    if len(audits) != 400 or len(audit_by_id) != 400 or set(audit_by_id) != {r['scenario_id'] for r in raw}:
        raise SystemExit('Quality audit missing or stale. Run: python scripts/m2_audit_batch.py')
    output_groups = defaultdict(list)
    for record in raw:
        output_groups[norm(record.get('output', ''))].append(record['scenario_id'])
    duplicate_ids = {sid for ids in output_groups.values() if len(ids) > 1 for sid in ids}

    scores = [score_row(r, audit_by_id[r['scenario_id']], r['scenario_id'] in duplicate_ids) for r in raw]
    scores_by_id = {r['scenario_id']: r for r in scores}
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / 'M3_DOMAIN_SCORES.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(scores[0]))
        writer.writeheader()
        writer.writerows(scores)
    review_ids = {r['scenario_id'] for r in scores if r['screening_tier'] != 'strong_screening_candidate'}
    with (OUT / 'M3_REVIEW_QUEUE.csv').open('w', newline='', encoding='utf-8') as f:
        columns = list(scores[0]) + ['instruction', 'input', 'output', 'human_decision', 'reviewer_notes']
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for record in raw:
            if record['scenario_id'] in review_ids:
                sid = record['scenario_id']
                writer.writerow({**scores_by_id[sid], 'instruction': record['instruction'],
                                'input': record.get('input', ''), 'output': record['output'],
                                'human_decision': '', 'reviewer_notes': ''})
    with (OUT / 'M3_PROVISIONAL_STRONG_CANDIDATES.jsonl').open('w', encoding='utf-8') as f:
        for record in raw:
            if scores_by_id[record['scenario_id']]['screening_tier'] == 'strong_screening_candidate':
                f.write(json.dumps(record, ensure_ascii=False) + '\n')

    by_task = defaultdict(Counter)
    for r in scores:
        by_task[r['task_type']][r['screening_tier']] += 1
    task_rows = {}
    for task, expected_n in EXPECTED.items():
        actual_n = sum(1 for r in raw if r['task_type'] == task)
        if actual_n != expected_n:
            raise SystemExit(f'Task distribution changed for {task}: {actual_n}')
        strong = by_task[task]['strong_screening_candidate']
        task_rows[task] = {
            'total': expected_n,
            'strong_screening_candidates': strong,
            'hold_manual_review': by_task[task]['hold_manual_review'],
            'exclude_provisional': by_task[task]['exclude_provisional'],
            'proposed_training_quota': QUOTAS[task],
            'meets_quota_before_human_review': strong >= QUOTAS[task]
        }
    summary = {
        'raw_sha256': sha256(FROZEN),
        'eval_sha256': sha256(EVAL),
        'total_records': len(raw),
        'screening_tiers': dict(Counter(r['screening_tier'] for r in scores)),
        'identical_response_extra_occurrences': sum(len(v)-1 for v in output_groups.values() if len(v)>1),
        'identical_response_rows_affected': len(duplicate_ids),
        'task_readiness': task_rows,
        'legal_verification_completed': False,
        'human_verification_completed': False,
        'training_approved': 0,
        'method': 'CuratorKIT schema/clean/exact dedup followed by task-aware deterministic scoring; not a legal or LLM-judge audit',
        'warning': 'Heuristic scores and tiers are provisional; do not use as claims of legal validity.'
    }
    (OUT / 'M3_DOMAIN_SUMMARY.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print('Frozen examples:', len(raw))
    print('Screening tiers:', summary['screening_tiers'])
    print('Identical response extra occurrences:', summary['identical_response_extra_occurrences'])
    print('Review queue:', len(review_ids))
    print('Task-specific preliminary capacity for proposed 150-example curated subset:')
    for name, item in task_rows.items():
        print(f"  {name}: strong={item['strong_screening_candidates']} / quota={item['proposed_training_quota']}, capacity_ok={item['meets_quota_before_human_review']}")
    print('Scores:', OUT / 'M3_DOMAIN_SCORES.csv')
    print('Review queue:', OUT / 'M3_REVIEW_QUEUE.csv')
    print('Summary:', OUT / 'M3_DOMAIN_SUMMARY.json')
    print('Training approvals: 0')


if __name__ == '__main__':
    main()
