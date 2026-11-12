# M3.4 Human Calibration Report

## Calibration Status

**Human calibration completed: 27/27 examples.**

- All 27 decisions are recorded.
- Every reviewed example has human_notes.
- Training-approved examples: 0.
- Frozen datasets remain unchanged.

## Human Review Results

| Human decision | Count |
|---|---:|
| `accept_screening` | 5 |
| `false_positive` | 10 |
| `false_negative` | 5 |
| `needs_legal_expert` | 7 |

## Automated Tier vs Human Decision

| Automated tier | Accept | False positive | False negative | Needs legal expert |
|---|---:|---:|---:|---:|
| `strong_screening_candidate` | 4 | 0 | 5 | 1 |
| `hold_manual_review` | 0 | 4 | 0 | 6 |
| `exclude_provisional` | 1 | 6 | 0 | 0 |

## Provisional Curated Cohort

- Original curated candidates: 150
- Human-reviewed candidates in the cohort: 10
- Candidates requiring blocking review: 6

| Scenario ID | Task | Human decision |
|---|---|---|
| GEN0289 | full_agreement | `false_negative` |
| GEN0349 | full_agreement | `false_negative` |
| GEN0151 | clause_drafting | `needs_legal_expert` |
| GEN0108 | contract_customization | `false_negative` |
| GEN0153 | missing_clause_completion | `false_negative` |
| GEN0075 | missing_clause_completion | `false_negative` |

## Engineering Findings

1. Literal contradiction checks incorrectly flag superseded roles, salary amounts and working hours.
2. Identical outputs for different short editing tasks are not necessarily defective training examples.
3. Numeric and written salary representations require consistency validation.
4. Explicit placeholders and internal clause cross-references require dedicated checks.
5. Unsupported probation extensions, termination conditions and customization changes should be flagged.
6. Legal-reference currentness must be reviewed separately from structural and instruction quality.

## Methodological Limitations

The 27 calibration examples were deliberately selected to investigate screening behavior.

They do not constitute a random sample of the 400-example dataset.

Therefore, the observed decision percentages must not be interpreted as dataset-wide false-positive or false-negative rates.

Human calibration does not establish legal correctness or automatically approve training data.

## Next Steps

1. Implement a versioned M3 scoring system.
2. Fix confirmed false-positive and false-negative rules.
3. Re-score all 400 frozen synthetic examples.
4. Compare original and revised screening decisions.
5. Review affected curated candidates.
6. Rebuild task-matched provisional training cohorts.
7. Finalize eligibility before AlignTune fine-tuning.

## Dataset Provenance

- Frozen raw SHA256: `ec94fba3a90b3cd9853b42ac9365154aa54f5973e183f2e06ca2895b127b466b`
- Frozen evaluation SHA256: `944ba82ed4937a41f32c064aaaa89f1b34aeb2d44a89e0860aac51aa3d46bff9`
- Original scores SHA256: `0e6cd151559554770293c3b1dfe814c460c3d9ab36a784c2a60c007d18c9ba6e`
- Human review SHA256: `58bf74302bc62d3e5759a02280708f3bc8efaf182c3bec34f1688586388ceaab`
