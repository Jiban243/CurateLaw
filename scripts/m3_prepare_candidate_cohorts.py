from __future__ import annotations

import csv
import hashlib
import json
import random
import re
from collections import Counter, defaultdict
from pathlib import Path

BASE = Path('data')
RAW = BASE / 'm2/frozen/pool_raw_0400.jsonl'
FREEZE = BASE / 'm2/frozen/freeze_manifest.json'
EVAL = BASE / 'm2/frozen/heldout_eval_040.jsonl'
SCORES = BASE / 'm3/domain_curation/M3_DOMAIN_SCORES.csv'
OUT = BASE / 'm3/provisional_cohorts'
SEED = 20261109
QUOTAS = {
    'full_agreement': 45,
    'clause_drafting': 38,
    'contract_customization': 30,
    'contradiction_correction': 22,
    'missing_clause_completion': 15,
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding='utf-8') as stream:
        return [json.loads(s) for s in stream if s.strip()]


def normalized(value: str) -> str:
    return re.sub(r'\s+', ' ', str(value)).strip().casefold()


def stable_key(sid: str) -> str:
    return hashlib.sha256(f'{SEED}:{sid}'.encode('utf-8')).hexdigest()


def write_once(path: Path, payload: str) -> None:
    contents = payload.encode('utf-8')
    if path.exists():
        if path.read_bytes() != contents:
            raise SystemExit(f'Existing file differs; not overwriting: {path}')
        return
    path.write_bytes(contents)


def csv_payload(records: list[dict], columns: list[str]) -> str:
    import io
    s = io.StringIO(newline='')
    writer = csv.DictWriter(s, fieldnames=columns, extrasaction='ignore')
    writer.writeheader()
    writer.writerows(records)
    return s.getvalue()


def main():
    for path in (RAW, FREEZE, EVAL, SCORES):
        if not path.exists():
            raise SystemExit(f'Missing required input: {path}')

    frozen = json.loads(FREEZE.read_text(encoding='utf-8'))
    if frozen.get('raw_sha256') != digest(RAW):
        raise SystemExit('Frozen raw hash mismatch')
    if frozen.get('eval_sha256') != digest(EVAL):
        raise SystemExit('Frozen evaluation hash mismatch')

    data = read_jsonl(RAW)
    ids = [r['scenario_id'] for r in data]
    if len(data) != 400 or len(set(ids)) != 400:
        raise SystemExit('Expected 400 unique raw records')
    by_id = {r['scenario_id']: r for r in data}

    with SCORES.open(encoding='utf-8', newline='') as stream:
        scored = list(csv.DictReader(stream))
    score_by_id = {r['scenario_id']: r for r in scored}
    if len(scored) != 400 or len(score_by_id) != 400 or set(by_id) != set(score_by_id):
        raise SystemExit('Scores do not cover all 400 frozen IDs')
    for sid, record in by_id.items():
        if record['task_type'] != score_by_id[sid]['task_type']:
            raise SystemExit(f'Score/task mismatch: {sid}')

    groups = defaultdict(list)
    for record in data:
        groups[record['task_type']].append(record['scenario_id'])

    rng = random.Random(SEED)
    raw_ids, curated_ids = [], []
    used_curated_outputs = set()

    for task, quota in QUOTAS.items():
        task_ids = sorted(groups[task])
        if len(task_ids) < quota:
            raise SystemExit(f'Not enough raw examples for {task}')
        raw_ids.extend(rng.sample(task_ids, quota))

        strong = [
            sid for sid in task_ids
            if score_by_id[sid]['screening_tier'] == 'strong_screening_candidate'
        ]
        strong.sort(key=lambda sid: (-float(score_by_id[sid]['quality_score_heuristic']), stable_key(sid)))
        chosen = []
        for sid in strong:
            fingerprint = hashlib.sha256(normalized(by_id[sid]['output']).encode('utf-8')).hexdigest()
            if fingerprint in used_curated_outputs:
                continue
            chosen.append(sid)
            used_curated_outputs.add(fingerprint)
            if len(chosen) == quota:
                break
        if len(chosen) != quota:
            raise SystemExit(f'Insufficient unique-output provisional strong candidates: {task} ({len(chosen)}/{quota})')
        curated_ids.extend(chosen)

    assert len(raw_ids) == 150 and len(curated_ids) == 150
    raw_set, curated_set = set(raw_ids), set(curated_ids)
    assert len(raw_set) == len(curated_set) == 150

    def cohort_rows(sids, name):
        return [
            {
                'cohort': name,
                'scenario_id': sid,
                'task_type': by_id[sid]['task_type'],
                'screening_tier': score_by_id[sid]['screening_tier'],
                'quality_score_heuristic': score_by_id[sid]['quality_score_heuristic'],
                'output_duplicate_candidate': score_by_id[sid]['output_duplicate_candidate'],
                'training_approved': 'false',
            }
            for sid in sids
        ]

    raw_rows = cohort_rows(raw_ids, 'raw_random_stratified')
    curated_rows = cohort_rows(curated_ids, 'curated_provisional')

    samples = []
    for task in QUOTAS:
        sids = sorted(groups[task])
        strong = [sid for sid in sids if score_by_id[sid]['screening_tier'] == 'strong_screening_candidate']
        strong.sort(key=stable_key)
        holds = [sid for sid in sids if score_by_id[sid]['screening_tier'] == 'hold_manual_review']
        holds.sort(key=lambda sid: (float(score_by_id[sid]['quality_score_heuristic']), stable_key(sid)))
        samples.extend((sid, 'calibration_strong_sample') for sid in strong[:2])
        samples.extend((sid, 'calibration_manual_hold') for sid in holds[:2])

    exclusions = sorted(
        sid for sid, score in score_by_id.items()
        if score['screening_tier'] == 'exclude_provisional'
    )
    samples.extend((sid, 'verify_provisional_exclusion') for sid in exclusions)
    if len({sid for sid, _ in samples}) != len(samples):
        raise SystemExit('Calibration review contains duplicate IDs')

    review_rows = []
    for sid, purpose in samples:
        score = score_by_id[sid]
        record = by_id[sid]
        review_rows.append({
            'scenario_id': sid,
            'review_purpose': purpose,
            'task_type': record['task_type'],
            'screening_tier': score['screening_tier'],
            'quality_score_heuristic': score['quality_score_heuristic'],
            'hard_failure_reasons': score['hard_failure_reasons'],
            'review_reasons': score['review_reasons'],
            'instruction': record['instruction'],
            'input': record.get('input', ''),
            'output': record['output'],
            'human_decision': '',
            'human_notes': '',
            'legal_review_status': 'pending',
            'approved_for_training': 'false',
        })

    OUT.mkdir(parents=True, exist_ok=True)
    cohort_cols = list(raw_rows[0])
    review_cols = list(review_rows[0])
    raw_manifest = OUT / 'M3_RAW_150_CANDIDATES.csv'
    curated_manifest = OUT / 'M3_CURATED_150_CANDIDATES.csv'
    human_queue = OUT / 'M3_CALIBRATION_REVIEW.csv'
    write_once(raw_manifest, csv_payload(raw_rows, cohort_cols))
    write_once(curated_manifest, csv_payload(curated_rows, cohort_cols))
    write_once(human_queue, csv_payload(review_rows, review_cols))

    def stats(rows):
        return {
            'by_task': dict(Counter(r['task_type'] for r in rows)),
            'by_screening_tier': dict(Counter(r['screening_tier'] for r in rows)),
            'mean_heuristic_score': round(sum(float(r['quality_score_heuristic']) for r in rows) / len(rows), 2),
        }

    summary = {
        'status': 'PROVISIONAL_NOT_TRAINING_APPROVED',
        'random_seed': SEED,
        'frozen_raw_sha256': digest(RAW),
        'frozen_eval_sha256': digest(EVAL),
        'domain_scores_sha256': digest(SCORES),
        'quota_by_task': QUOTAS,
        'raw_candidate_count': len(raw_rows),
        'curated_candidate_count': len(curated_rows),
        'raw_candidate_stats': stats(raw_rows),
        'curated_candidate_stats': stats(curated_rows),
        'overlapping_scenario_ids': len(raw_set & curated_set),
        'overlap_is_allowed': True,
        'curated_exact_duplicate_outputs': 0,
        'calibration_review_count': len(review_rows),
        'calibration_review_purposes': dict(Counter(r['review_purpose'] for r in review_rows)),
        'human_verification_completed': False,
        'legal_verification_completed': False,
        'training_approved': False,
        'note': 'Selection is based on deterministic heuristics and exact-output uniqueness; quality advantage is not established until independent evaluation. These are ID manifests, not trainer-ready files.',
    }
    summary_path = OUT / 'M3_CANDIDATE_COHORT_SUMMARY.json'
    write_once(summary_path, json.dumps(summary, indent=2, ensure_ascii=False) + '\n')

    print('Frozen raw records:', len(data))
    print('Raw provisional cohort:', len(raw_rows))
    print('Curated provisional cohort:', len(curated_rows))
    print('Shared scenario IDs:', len(raw_set & curated_set))
    print('Curated exact duplicate responses: 0')
    print('Raw screening tiers:', summary['raw_candidate_stats']['by_screening_tier'])
    print('Curated screening tiers:', summary['curated_candidate_stats']['by_screening_tier'])
    print('Calibration review rows:', len(review_rows))
    print('Raw ID manifest:', raw_manifest)
    print('Curated ID manifest:', curated_manifest)
    print('Human calibration queue:', human_queue)
    print('Summary:', summary_path)
    print('Training approved: False')


if __name__ == '__main__':
    main()
