
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

# M4–M5 Engineering Decisions — CurateLaw-India

**Contributor:** Ayush  
**Branch:** `ayush/m4-m5`  
**Date:** 14 November 2026  
**Scope:** M4 fine-tuning and M5 evaluation only. This document supplements, and does not replace, Jiban's M1–M3 `README.md` and `DEVLOG.md`.

## D01 — Preserve the M1–M3 handoff

Use the frozen raw/curated cohorts prepared by M3, with **150 examples per arm**, a matched five-task distribution (12 full agreement, 45 clause drafting, 45 customization, 32 contradiction correction, 16 missing-clause completion), and **71 shared scenario IDs**. No supplemental pilot examples were added to these cohorts. Preserve the original M1–M3 data, source files, and Git history.

**Consequence:** The experiment compares the first available cohorts, not independent or legally certified training sets. Equal example counts do not imply equal token exposure.

## D02 — Pin the student model and use comparable training settings

- Base: `CohereLabs/tiny-aya-global`.
- Frozen model revision: `af89d219b53ed9b13b8a4645f9c8028973510324`.
- Training approach: AlignTune `0.1.35` orchestration with TRL-backed QLoRA training on a Google Colab Tesla T4.
- Quantization: 4-bit NF4; fp16 compute.
- LoRA: rank 8, alpha 16, dropout 0.05; `q_proj`, `k_proj`, `v_proj`, `o_proj` target modules.
- Shared hyperparameters: learning rate `1e-4`, 2 epochs, microbatch 1, gradient accumulation 4, sequence length 3072, random seed 42.
- Observed run length: 76 optimizer steps for each training arm.

The baseline model was not fine-tuned. The raw and curated adapters were trained independently from the same base checkpoint. One run per arm was completed; training-seed variance was not assessed.

## D03 — Correct completion-only loss masking

An AlignTune dataset normalization step converted prompt/completion data to a combined `messages` representation, which did not produce the intended loss mask for user tokens in the tested trainer setup. Rather than training on user text, the effective TRL dataset was supplied explicitly as `prompt` (user message) and `completion` (assistant message) records.

**Verification:** Inspected token-level masks and confirmed that user text was excluded from the supervised loss while assistant completions were trained. A T4 smoke test was completed before the full runs.

**Reproducibility requirement:** Keep the notebook cells implementing and verifying this override. Do not claim that default AlignTune preprocessing alone provides this behavior.

## D04 — Preserve separate adapters, not merged full checkpoints

Model A raw and Model B curated were saved separately in Drive under:

- `LexiLabs/finetuning_artifacts/model_a_raw/checkpoints/`
- `LexiLabs/finetuning_artifacts/model_b_curated/checkpoints/`

Each adapter contained 3,833,856 trainable parameters across 288 tensors. Storage dtype differed in the saved adapters (reported raw FP32; curated BF16); this should be inspected when publishing weights or attempting strict byte-for-byte comparisons. Reported final training losses were approximately 0.974 raw and 1.142 curated; **training losses are not head-to-head downstream quality scores**.

**Git decision:** Do not commit large binary weights by default. Keep them in Drive or an appropriate model-artifact repository, and document access and hashes separately where possible.

## D05 — Freeze the evaluation scenarios before model comparison

The test set contains **40 held-out scenarios**, eight per drafting task, with 120 generated responses across Base, Raw and Curated. The frozen benchmark SHA-256 is:

`944ba82ed4937a41f32c064aaaa89f1b34aeb2d44a89e0860aac51aa3d46bff9`

All models were evaluated with the same held-out prompts. Deterministic decoding was used (`do_sample=False`, one beam), with generation budgets of 1536 new tokens for full agreements and 384 for other tasks.

The benchmark contains `expected_facts`, **not independently adjudicated gold reference contracts**. Its provenance records human verification and legal verification as incomplete. Exact instruction-overlap checks do not exclude all semantic leakage.

## D06 — Keep original evaluation results immutable and version scorer changes

All evaluation runs use saved `full_v2` predictions; scorer revisions must not regenerate or change outputs.

- **M5.7 — AuditKIT output diagnostics:** token-limit avoidance Base 2.5%, Raw 85.0%, Curated 87.5%. Nonempty output: 40/40 for each model.
- **M5.8 — literal expected-fact presence (v1):** Base 73.99%, Raw 71.79%, Curated 68.93%.
- **M5.10 — revised expected-fact presence (v2):** Base 83.99%, Raw 80.54%, Curated 80.18%. Revision recognized written-out time quantities (e.g., “three months”).
- **M5.11A — risk-screen flags:** responses with at least one flag: Base 39/40, Raw 15/40, Curated 16/40.
- **M5.11B — AI-assisted provisional drafting-quality rubric:** Base 5.125/8, Raw 6.000/8, Curated 5.875/8.

The corrected fact-presence comparison **Curated − Raw = −0.36 percentage points**, exploratory paired 95% bootstrap interval **[−6.79, +3.93] percentage points**. The AI-assisted quality scores are not independently human-reviewed or legal-expert-certified; the review was performed by an AI assistant and must be labeled accordingly. Risk flags are indicators for inspection, not verified errors.

## D07 — Report negative and mixed results transparently

The experiment supports a strong improvement in **token-limit avoidance** after task fine-tuning. It does **not** establish that curated training outperforms raw training overall. Curated was higher on full-agreement expected-fact presence (82.14% vs raw 71.43%), but lower on clause drafting (56.25% vs raw 68.75%). Overall corrected fact presence and AI-assisted rubric both slightly favored raw; differences were small and/or uncertain.

Do not select favorable slices or change scoring rules post hoc to manufacture a positive result. Interpret all post-hoc scorer updates as exploratory.

## D08 — Keep legal and ethical limits explicit

Observed examples included incorrect numeric-versus-written salaries, incorrect notice terms, unresolved placeholders, repeated text, and potentially unsupported legal references. A model that repeats a requested amount is not necessarily factually consistent or legally valid. No output should be presented as legal advice or a certified employment contract.

Human review of the 27 M3 calibration examples does **not** constitute independent human review of the 120 M5 generated outputs.

## D09 — Repository and artifact policy

Commit reviewable source, a genuinely executed notebook, configurations, provenance manifests, concise summaries, and optionally the 120 fictional prediction responses if cleared for public release. Preserve the original `README.md` and `DEVLOG.md` untouched on this branch. Keep model weights, credentials, Colab tokens, runtime caches, restricted legal source documents, and oversized transient artifacts out of Git.

**Files to add to this branch:** `decision.md`, `README_M4_M5.md`, the final updated notebook under `notebooks/`, and verified M5 report/summary artifacts under `results/m4_m5/`. These paths describe the desired repo structure, not a claim that every artifact is already in the local clone.

## D10 — Remaining verification

Before final submission, confirm that the pushed notebook is the **final** executed M4–M5 version; the available earlier notebook snapshot includes Model A work but not all subsequent M5 cells. Validate the two adapter checkpoint directories, compare manifest and prediction hashes, and make an inventory of publicly committed versus Drive-only artifacts. For stronger scientific evidence, repeat multiple training seeds and obtain independently blinded human/legal assessment of the held-out outputs.
