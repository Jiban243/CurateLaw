
---

# Development Log — Jiban

## 13 November 2026 — M1–M3 Completion and Fine-Tuning Handoff

**Contributor:** Jiban  
**Project:** CurateLaw-India  
**Track:** Lexsi Labs Track 1 — Data-Scarce Domains  
**Branch:** `jiban/m1-m3-progress`  
**Status:** Data preparation and curation completed for the initial fine-tuning experiment.

### 1. Project Objective

CurateLaw-India investigates whether quality-aware synthetic-data curation improves downstream language-model fine-tuning compared with training on unfiltered synthetic data.

The selected domain is Indian employment-contract drafting.

The experimental objective is to compare two models initialized from the same Cohere Labs open-weight checkpoint:

- Model A: Fine-tuned on raw synthetic data.
- Model B: Fine-tuned on curated synthetic data.

Both training datasets have equal example counts and matched task distributions.

Downstream evaluation using AuditKIT remains pending.

### 2. M1 — Domain Research and Corpus Preparation

Completed the initial domain-research and reference-corpus preparation.

Key work:

- Established Indian employment-contract drafting as the target domain.
- Prepared a source registry containing 29 metadata entries.
- Acquired six local reference documents/sources.
- Prepared a structured 16-section employment-agreement schema.
- Collected 55 normalized clause observations.
- Performed provisional extraction and classification of contract text.
- Identified legal-reference, document-structure, and source-permission risks.

Engineering decision:

Reference contracts and legal documents were treated as sources for domain understanding and validation design rather than automatically approved supervised fine-tuning examples.

Third-party document redistribution and training permissions remain subject to review.

### 3. M2 — Synthetic Data Generation

Built the synthetic-data preparation and generation pipeline.

Teacher model:

`Qwen/Qwen3-235B-A22B-Instruct-2507`

Inference provider:

Hugging Face Inference Providers.

Generated and froze 400 synthetic instruction-response pairs.

Task distribution:

| Task | Count |
|---|---:|
| Full agreement drafting | 120 |
| Clause drafting | 100 |
| Contract customization | 80 |
| Contradiction correction | 60 |
| Missing-clause completion | 40 |
| Total | 400 |

Prepared 40 independent held-out evaluation scenarios, with eight scenarios per task.

Frozen training pool:

`data/m2/frozen/pool_raw_0400.jsonl`

Frozen evaluation scenarios:

`data/m2/frozen/heldout_eval_040.jsonl`

Raw dataset SHA-256:

`ec94fba3a90b3cd9853b42ac9365154aa54f5973e183f2e06ca2895b127b466b`

Verified frozen inputs through checksums and preserved generation metadata.

Exact prompt-overlap checks found no direct training/evaluation prompt duplication. Semantic leakage has not been fully ruled out.

### 4. M3.1 — CuratorKIT Hygiene

Integrated CuratorKIT for initial synthetic-data hygiene checks.

Results:

- Examples processed: 400
- Examples passing basic hygiene: 400
- Examples rejected: 0

Checks covered basic schema validity, text cleaning, and exact-record deduplication.

Important finding:

Passing mechanical hygiene checks does not guarantee instruction adherence, contractual consistency, or legal correctness.

### 5. M3.2 — Domain Quality Scoring V1

Implemented deterministic task-aware domain screening.

V1 results:

| Tier | Count |
|---|---:|
| Strong screening candidate | 309 |
| Hold for manual review | 84 |
| Provisional exclusion | 7 |

The scorer considered contract completeness, structural validity, requested factual terms, and potential legal-reference risks.

Initial errors included incorrect flags for superseded values and failures to identify genuine drafting inconsistencies.

### 6. M3.3–M3.4 — Human Calibration

Prepared and completed a 27-example human calibration sample spanning strong candidates, manual-review holds, and provisional exclusions.

Every reviewed example received a documented human decision and detailed `human_notes`.

Final results:

| Human decision | Count |
|---|---:|
| Accept screening | 5 |
| False positive | 10 |
| False negative | 5 |
| Needs legal expert | 7 |
| Total | 27 |

Important findings:

- Superseded incorrect roles and amounts were sometimes falsely flagged as active contradictions.
- Identical short responses across different prompts did not always indicate defective examples.
- Numeric and written salary inconsistencies were sometimes missed.
- Missing required placeholders could pass automated screening.
- Internal clause cross-reference errors could be missed.
- Unrequested probation extensions and termination conditions required additional checks.
- Potentially outdated statutory references required separate legal-review treatment.

The calibration sample was deliberately selected for diagnosis and is not representative of the entire 400-example population.

No training approvals were granted through the calibration process.

### 7. M3.5 — Domain Scoring V2

Developed `scripts/m3_score_v2.py` to improve automated quality screening.

V2 introduced checks for:

- Numeric versus written salary consistency
- Missing required contractual values
- Incorrect internal clause references
- Unrequested probation extensions
- Probation notice exceptions
- Employer-only payment-in-lieu provisions
- Missing instruction-specific placeholders
- Contradiction-correction context
- Historical or potentially inapplicable legal references

Results:

| Tier | V1 | V2 |
|---|---:|---:|
| Strong screening candidate | 309 | 256 |
| Hold for manual review | 84 | 125 |
| Provisional exclusion | 7 | 19 |

A total of 124 examples changed screening tiers.

V2 identified the previously documented calibration risk cases, although this is not independent evidence of generalization because calibration findings informed its rules.

The original scorer and datasets were preserved.

### 8. Full-Agreement Diagnostics

Investigated why only 14 of 120 generated full agreements were provisionally strong under V2.

Major flag frequencies:

| Flag | Agreements |
|---|---:|
| Probation notice exception | 64 |
| Employer-only notice payment | 49 |
| Unrequested probation extension | 23 |
| Historical statutory reference | 12 |
| Incorrect notice cross-reference | 11 |
| Numeric/written salary mismatch | 6 |

These counts overlap.

Analyzed 46 single-flag agreements and documented three representative reviews:

- GEN0005: Unrequested seven-day probation notice exception
- GEN0114: Employer-only notice-payment provision
- GEN0031: Unrequested probation extension

All three were retained as justified holds with detailed reviewer notes.

Engineering decision:

Did not relax quality standards merely to increase the number of strong candidates.

### 9. Supplemental Generation Experiment

Prepared 100 additional fictional full-agreement scenarios using a revised, versioned generation prompt.

Generated a five-example pilot using the same teacher checkpoint and temperature.

Pilot results:

- Successfully generated: 5
- Normal completion: 5
- Agreements with 16 detected numbered sections: 5
- Preliminary strong screening: 3
- Flagged for review: 2

The pilot exposed additional drafting concerns involving party-name placeholders and termination-related conditions.

The supplemental generation experiment was preserved separately.

**No supplemental examples were included in the first fine-tuning cohorts.**

This avoided mixing generation-prompt improvements with the primary curation comparison.

### 10. M3.6 — Experimental Fine-Tuning Dataset Preparation

Prepared the first matched raw and curated training cohorts using only the original frozen pool of 400 examples.

Final task distribution:

| Task | Raw | Curated |
|---|---:|---:|
| Full agreement | 12 | 12 |
| Clause drafting | 45 | 45 |
| Contract customization | 45 | 45 |
| Contradiction correction | 32 | 32 |
| Missing-clause completion | 16 | 16 |
| Total | 150 | 150 |

Raw dataset:

`data/m3/finetune_ready/raw_150_messages.jsonl`

Curated dataset:

`data/m3/finetune_ready/curated_150_messages.jsonl`

Manifest:

`data/m3/finetune_ready/cohort_manifest.json`

Selection properties:

- Equal example counts
- Matched task distributions
- Shared original generation pool
- Fixed selection seed
- V2 strong screening for curated examples
- Exclusion of documented human-confirmed risk cases from the curated cohort
- Response-level diversity controls
- Frozen evaluation dataset excluded from training

The two datasets share 71 scenario IDs.

The original full-agreement quota was reduced because too few examples passed the stricter automated screening.

This design change and the cohort overlap must be disclosed when interpreting downstream results.

The files are experimental training inputs, not legally certified examples.

### 11. Key Engineering Contributions

My responsibilities across M1–M3 included:

1. Domain research and employment-contract schema preparation.
2. Synthetic training-scenario design.
3. Teacher-model generation and frozen dataset management.
4. CuratorKIT hygiene integration.
5. Task-aware quality scoring.
6. Human calibration and error analysis.
7. Versioned scorer improvement.
8. Automated diagnostics and reporting.
9. Supplemental-generation experimentation.
10. Matched raw-versus-curated cohort preparation.
11. Data provenance, reproducibility, and repository handoff.

The central engineering outcome is a reproducible pipeline connecting synthetic generation, automated curation, targeted human calibration, and controlled training-dataset selection.

### 12. Reproducibility and Git History

Important commits:

- `d4f8938` — Complete M3 curation and prepare matched fine-tuning datasets.
- `90e51c3` — Update README with completed M1–M3 pipeline and fine-tuning handoff.

Repository:

https://github.com/Jiban243/CurateLaw

Branch:

`jiban/m1-m3-progress`

The repository was successfully pushed and verified with a clean working tree after the README update.

### 13. Handoff to Ayush

**Jiban's M1–M3 experimental data-preparation work is complete.**

Ayush takes over the fine-tuning and downstream evaluation stages.

Next responsibilities:

- Select and validate a compatible Cohere Labs open-weight checkpoint.
- Set up AlignTune.
- Validate the chat-format training datasets.
- Fine-tune the same checkpoint separately on raw and curated datasets.
- Keep hyperparameters and compute budgets controlled.
- Evaluate the base, raw-tuned, and curated-tuned models using AuditKIT.
- Report overall and task-level performance.
- Document failure cases, limitations, and reproducibility information.

### 14. Outstanding Limitations

The following remain open:

- Automated screening does not establish legal correctness.
- Human calibration was diagnostic, not statistically representative.
- The evaluation set requires further scrutiny for semantic leakage.
- Full-agreement examples are underrepresented in the first cohorts.
- Raw and curated cohorts overlap by 71 examples.
- Third-party legal-source permissions require separate verification.
- AlignTune compatibility has not yet been established.
- No model has been fine-tuned or evaluated at this handoff point.
- The claim that curation improves downstream performance remains a hypothesis until measured.

### Final Status

**M1–M3: Completed for the first experimental fine-tuning run.**

**M4 — Fine-tuning: Handed over to Ayush.**

**M5 — Evaluation and results: Pending.**

Contributor: Jiban

---
