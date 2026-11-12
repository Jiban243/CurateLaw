
# CurateLaw-India

### Quality-Aware Synthetic Data Curation for Indian Employment-Contract Drafting

**Lexsi Labs Hiring Challenge | Track 1 — Data-Scarce Domains**

[GitHub Repository](https://github.com/Jiban243/CurateLaw) | [Development Log](DEVLOG.md)

## 1. Project Overview

CurateLaw-India is a data-centric language-model fine-tuning research project focused on Indian employment-contract drafting.

The project addresses the Track 1 problem statement:

> Where little real data exists, generate, verify and filter synthetic training data, and demonstrate that curation measurably outperforms training on raw generated data.

High-quality instruction-response datasets for specialized Indian employment-contract drafting are difficult to obtain. Synthetic data provides an alternative, but raw generated examples may contain:

- Incomplete contractual clauses
- Contradictory salary, probation, or notice terms
- Incorrect employee roles or working arrangements
- Unsupported contractual conditions
- Outdated or potentially inapplicable legal references
- Duplicate or low-diversity responses
- Incorrect internal clause references

CurateLaw-India investigates whether automated quality-aware curation can improve downstream fine-tuning outcomes.

### Research Question

**Does fine-tuning on a curated synthetic dataset produce better drafting quality and instruction consistency than fine-tuning the same model on an equally sized raw synthetic dataset?**

The project is an experimental research prototype, not a production legal-advice or contract-generation service.

## 2. Technology Stack

| Component | Technology |
|---|---|
| Programming language | Python 3.11 |
| Teacher model | Qwen/Qwen3-235B-A22B-Instruct-2507 |
| Teacher inference | Hugging Face Inference Providers |
| Data hygiene | CuratorKIT |
| Domain-specific validation | Custom Python quality checks |
| Fine-tuning | AlignTune (next stage) |
| Student model | Cohere Labs open-weight model (selection pending) |
| Evaluation | AuditKIT (planned) |
| Version control | Git and GitHub |

Related repositories:

- [CuratorKIT](https://github.com/Lexsi-Labs/CuratorKIT)
- [AlignTune](https://github.com/Lexsi-Labs/aligntune)
- [AuditKIT](https://github.com/Lexsi-Labs/AuditKIT)

## 3. Research Pipeline

```text
M1 — Domain Understanding and Reference Corpus
                     |
                     v
       Employment Contract Schema
                     |
                     v
M2 — Synthetic Scenario and Response Generation
                     |
                     v
       400 Frozen Synthetic Examples
                     |
          +----------+-----------+
          |                      |
          v                      v
    RAW DATASET           CURATION PIPELINE
          |                      |
          |               CuratorKIT Hygiene
          |                      |
          |               Domain Scoring V1
          |                      |
          |               Human Calibration
          |                      |
          |               Domain Scoring V2
          |                      |
          v                      v
    150 Raw Examples      150 Curated Examples
          |                      |
          v                      v
       AlignTune              AlignTune
          |                      |
          v                      v
       Model A                Model B
          |                      |
          +----------+-----------+
                     |
                     v
            AuditKIT Evaluation
                     |
                     v
          Compare Base / Raw / Curated
```

The purpose of the experiment is to isolate the effect of data curation while keeping the model architecture, training-example count, task distribution, and training configuration controlled.

## 4. Project Progress

**Status as of 12 November 2026**

| Milestone | Description | Status |
|---|---|---|
| M1 | Legal reference corpus and contract schema | Completed at prototype level |
| M2 | Synthetic scenario generation | Completed |
| M2 | Generate 400 instruction-response examples | Completed |
| M2 | Freeze 40 held-out evaluation scenarios | Completed |
| M3.1 | CuratorKIT hygiene validation | Completed |
| M3.2 | Initial domain scoring | Completed |
| M3.3 | Provisional cohort construction | Completed |
| M3.4 | Human calibration (27 examples) | Completed |
| M3.5 | Improved V2 domain scoring | Completed |
| M3.5 | Diagnostic analysis and supplemental pilot | Completed |
| M3.6 | Experimental raw and curated dataset preparation | Completed |
| M4 | AlignTune fine-tuning | Pending |
| M5 | AuditKIT evaluation and comparison | Pending |

The two experimental fine-tuning datasets have been prepared and committed to GitHub.

**No fine-tuning or model-comparison results have been reported yet.**

## 5. M1 — Domain Corpus Preparation

The domain preparation stage established a reference framework for Indian employment-contract drafting.

Artifacts include:

- A registry of 29 source metadata entries
- Six locally acquired reference sources
- 55 earlier normalized clause observations
- A 16-section employment-contract schema
- Clause extraction and classification reports
- Legal-reference and document-structure observations

Reference material was used to inform task design, contract structure, and validation criteria.

Third-party source documents and extracted copyrighted material are not automatically cleared for redistribution or model training.

### Employment Agreement Structure

The schema covers:

1. Parties and agreement date
2. Appointment
3. Duties and responsibilities
4. Workplace and work arrangement
5. Fixed annual salary
6. Probation
7. Working hours
8. Leave
9. Applicable statutory benefits
10. Confidentiality
11. Work-related intellectual property
12. Workplace policies
13. Termination
14. Dispute resolution
15. Governing law
16. Employer and employee signatures

## 6. M2 — Synthetic Data Generation

Synthetic instruction-response examples were generated using:

**Teacher:** `Qwen/Qwen3-235B-A22B-Instruct-2507`

**Provider:** Hugging Face Inference Providers

### Frozen Training Pool

A total of 400 examples were generated across five drafting tasks.

| Task | Examples |
|---|---:|
| Full agreement drafting | 120 |
| Clause drafting | 100 |
| Contract customization | 80 |
| Contradiction correction | 60 |
| Missing-clause completion | 40 |
| **Total** | **400** |

The frozen dataset is located at:

`data/m2/frozen/pool_raw_0400.jsonl`

### Held-Out Evaluation Dataset

A separate evaluation dataset contains 40 fictional scenarios, with eight scenarios per task.

File:

`data/m2/frozen/heldout_eval_040.jsonl`

The evaluation scenarios were excluded from the synthetic training pool.

Exact prompt-overlap checks were performed. Broader semantic leakage and near-duplicate relationships still require careful interpretation.

### Frozen Raw Dataset SHA-256

```text
ec94fba3a90b3cd9853b42ac9365154aa54f5973e183f2e06ca2895b127b466b
```

The freeze manifest records dataset checksums and provides a reproducibility reference.

## 7. M3 — Synthetic Data Curation

The curation stage combines CuratorKIT hygiene checks with task-specific deterministic validation.

### 7.1 CuratorKIT Hygiene

The initial CuratorKIT checks covered:

- Schema validation
- Text cleaning
- Exact-record deduplication
- Basic response validity

Results:

| Metric | Count |
|---|---:|
| Examples processed | 400 |
| Passed hygiene checks | 400 |
| Rejected | 0 |

Passing basic hygiene checks does not imply factual or legal correctness.

### 7.2 Domain Scoring V1

An initial rule-based scoring system classified all 400 examples.

| Screening tier | Count |
|---|---:|
| Strong screening candidate | 309 |
| Hold for manual review | 84 |
| Provisional exclusion | 7 |

V1 identified structural and instruction-following problems, but its initial rules also produced false positives and missed important drafting defects.

### 7.3 Human Calibration

A deliberately selected calibration sample of 27 examples was reviewed.

All 27 examples received documented human decisions and detailed review notes.

| Human decision | Count |
|---|---:|
| Accept screening | 5 |
| False positive | 10 |
| False negative | 5 |
| Needs legal expert | 7 |
| **Total** | **27** |

The calibration revealed several weaknesses:

- Superseded incorrect values being treated as active contradictions
- Missing joining-date placeholders
- Numeric and written salary inconsistencies
- Incorrect internal clause cross-references
- Unrequested probation extensions
- Unrequested termination-notice exceptions
- Employer-only notice-payment provisions
- Potentially outdated legal references

These findings informed the development of V2.

The calibration sample was intentionally selected for diagnostic purposes. Its error counts are not unbiased dataset-wide error estimates.

### 7.4 Domain Scoring V2

V2 introduced improved checks for factual consistency, drafting structure, instruction adherence, and legal-reference risks.

Results:

| Screening tier | V1 | V2 |
|---|---:|---:|
| Strong screening candidate | 309 | 256 |
| Hold for manual review | 84 | 125 |
| Provisional exclusion | 7 | 19 |

**124 examples changed screening tiers between V1 and V2.**

V2 detected the previously documented calibration risk cases, although those same cases influenced its design. Independent validation is necessary before making generalization claims.

Scoring and comparison artifacts are available in:

`data/m3/domain_curation_v2/`

## 8. Supplemental Generation Experiment

An additional generation experiment investigated whether more constrained teacher instructions could reduce recurring full-agreement drafting errors.

Preparation produced 100 supplemental fictional scenarios.

A five-example pilot was generated using the original teacher model and temperature, with a revised system prompt.

| Metric | Result |
|---|---:|
| Scenarios prepared | 100 |
| Pilot agreements generated | 5 |
| Generation finish reason | All completed normally |
| Preliminary strong screening | 3 |
| Flagged for review | 2 |

The pilot exposed issues involving placeholders and additional termination-related contractual conditions.

The supplemental dataset is retained as an experimental artifact.

**Supplemental examples were not included in the final 150-example training cohorts.**

This keeps the initial raw-versus-curated comparison within the same original generation pool.

## 9. Experimental Fine-Tuning Datasets

The first experimental training cohorts have been prepared from the original frozen 400-example pool.

Both cohorts contain 150 examples and use the same task distribution.

### Final Task Distribution

| Task | Raw | Curated |
|---|---:|---:|
| Full agreement drafting | 12 | 12 |
| Clause drafting | 45 | 45 |
| Contract customization | 45 | 45 |
| Contradiction correction | 32 | 32 |
| Missing-clause completion | 16 | 16 |
| **Total** | **150** | **150** |

The full-agreement quota was reduced from the initial provisional design because automated V2 screening left insufficient strong candidates for the original target.

The revised distribution is an experimental design limitation and must be disclosed when interpreting results.

### Raw Cohort

The raw baseline contains 150 examples sampled from the original generated pool without applying the V2 strong-candidate requirement.

### Curated Cohort

The curated dataset contains 150 examples selected using:

- V2 strong-candidate screening
- Task-aware quality ranking
- Response-level diversity controls
- Human-calibration risk exclusions
- Matched task distribution

### Cohort Overlap

The raw and curated cohorts share **71 scenario IDs**.

This is documented in the cohort manifest. The cohorts are not disjoint, and that overlap should be considered when interpreting the downstream experiment.

### Prepared Training Files

**Raw training dataset**

`data/m3/finetune_ready/raw_150_messages.jsonl`

**Curated training dataset**

`data/m3/finetune_ready/curated_150_messages.jsonl`

**Selection and provenance manifest**

`data/m3/finetune_ready/cohort_manifest.json`

Both training datasets use a chat-style JSONL representation:

```json
{
  "messages": [
    {
      "role": "user",
      "content": "Drafting instruction and optional input"
    },
    {
      "role": "assistant",
      "content": "Generated response"
    }
  ]
}
```

These files are prepared for experimental fine-tuning. AlignTune compatibility and tokenization requirements must be verified before training.

No formal legal approval is implied by dataset selection.

## 10. Repository Structure

```text
CurateLaw-India/
|
|-- README.md
|-- DEVLOG.md
|
|-- scripts/
|   |-- m2_generate_batch.py
|   |-- m2_audit_batch.py
|   |-- m3_score_curatelaw.py
|   |-- m3_score_v2.py
|   |-- m3_calibration_report.py
|   |-- m3_diagnose_v2.py
|   |-- m3_review_single_flags.py
|   |-- m3_record_single_flag_reviews.py
|   |-- m3_supplemental_generation.py
|   |-- m3_validate_supplemental_pilot.py
|   |-- m3_pilot_targeted_audit.py
|   |-- m3_prepare_finetuning.py
|
|-- data/
|   |-- m1/
|   |   |-- corpus/
|   |
|   |-- m2/
|   |   |-- scenarios/
|   |   |-- frozen/
|   |       |-- pool_raw_0400.jsonl
|   |       |-- heldout_eval_040.jsonl
|   |       |-- freeze_manifest.json
|   |
|   |-- m3/
|       |-- curatorkit_hygiene/
|       |-- domain_curation/
|       |-- domain_curation_v2/
|       |-- calibration_analysis/
|       |-- provisional_cohorts/
|       |-- v2_diagnostics/
|       |-- supplemental/
|       |-- finetune_ready/
|           |-- raw_150_messages.jsonl
|           |-- curated_150_messages.jsonl
|           |-- cohort_manifest.json
```

Some reference-corpus artifacts are kept locally and excluded from the public repository because their redistribution or training permissions have not been established.

## 11. Local Setup

The development environment uses Python 3.11.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install curatorkit huggingface_hub pandas pymupdf python-docx
```

Individual scripts may require additional dependencies. A fully locked environment has not yet been finalized.

Hugging Face credentials should be supplied through environment variables or secure prompts.

Never commit API keys, `.env` files, virtual environments, or restricted third-party legal source files.

## 12. Reproducibility

All scripts should be executed from the repository root.

### Regenerate V2 Screening Reports

```bash
python scripts/m3_score_v2.py
```

### Reproduce Calibration Analysis

```bash
python scripts/m3_calibration_report.py
```

### Reproduce V2 Diagnostics

```bash
python scripts/m3_diagnose_v2.py
```

### Reproduce Experimental Training Cohorts

```bash
python scripts/m3_prepare_finetuning.py
```

The cohort-selection script uses a fixed random seed and preserves the frozen dataset inputs.

Existing generated output files are not silently overwritten when their contents differ.

The original frozen dataset and held-out evaluation data should remain unchanged.

## 13. Next Stage — AlignTune Fine-Tuning

The next stage is to fine-tune a Cohere Labs open-weight model using AlignTune.

The experiment will compare:

| Model | Description |
|---|---|
| Base | Original pretrained or instruction-tuned checkpoint |
| Model A | Base model fine-tuned on raw synthetic data |
| Model B | Same base model fine-tuned on curated synthetic data |

### Experimental Controls

Both fine-tuning runs should use:

- The same base checkpoint
- Equal numbers of training examples
- Matched task distributions
- Identical training configurations
- Comparable token and compute budgets
- The same evaluation dataset
- Identical inference and decoding settings

Token-length distributions and effective training-token exposure should be recorded because equal example counts do not guarantee equal training budgets.

AlignTune integration has not yet been validated.

## 14. Evaluation Plan — AuditKIT

After training, AuditKIT will be used to compare the base model and the two fine-tuned variants on the frozen 40-scenario evaluation set.

Planned evaluation dimensions include:

1. Required-clause coverage
2. Instruction and factual consistency
3. Contractual term preservation
4. Contradiction detection and correction
5. Unrequested contractual additions
6. Structural and formatting compliance
7. Unsupported or questionable legal references

Results will be reported by task and overall.

The project's central hypothesis is that quality-aware curation improves downstream drafting performance compared with training on raw synthetic data under matched experimental conditions.

**This hypothesis has not yet been evaluated or confirmed.**

## 15. Limitations and Responsible Use

CurateLaw-India has several important limitations:

- Automated quality screening does not establish legal correctness.
- Human calibration was diagnostic and not statistically representative.
- Some statutory references require expert verification.
- Full agreements are underrepresented in the first training cohorts.
- The two training datasets overlap by 71 scenario IDs.
- The held-out evaluation set contains fictional scenarios.
- Exact prompt-isolation checks do not establish complete semantic independence.
- Source-document redistribution and training permissions remain subject to verification.
- Fine-tuning and downstream evaluation results are pending.

Generated agreements should not be relied on as legally valid employment contracts without qualified legal review.

## 16. Team and Contributions

CurateLaw-India is developed by a two-person team for the Lexsi Labs hiring challenge.

**Jiban — M1–M3: Data Preparation and Curation**

- Domain research and reference-corpus preparation
- Employment-contract schema
- Synthetic scenario and response generation
- CuratorKIT hygiene integration
- Domain-quality scoring
- Human calibration and diagnostic analysis
- Improved V2 curation
- Experimental training-dataset preparation
- Reproducibility and Git handoff

**Ayush — M4 onward: Model Fine-Tuning and Evaluation**

- Cohere Labs model selection and compatibility checks
- AlignTune fine-tuning setup
- Raw-versus-curated training experiments
- AuditKIT-based evaluation
- Model comparison and experimental reporting

Contributions and experiment outcomes should be updated as work progresses.

See [DEVLOG.md](DEVLOG.md) and Git commit history for additional engineering context.

## 17. Current Handoff

**Latest completed M3 commit:** `d4f8938`

**Working branch:** `jiban/m1-m3-progress`

**Handoff status:** Experimental training datasets prepared and pushed to GitHub.

Next action: validate AlignTune, train both variants, and evaluate them against the held-out benchmark.

---

**CurateLaw-India — A data-centric synthetic-data research prototype for Indian employment-contract drafting.**
