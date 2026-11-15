# CurateLaw-India — M4 Fine-Tuning and M5 Evaluation

**Contributor:** Ayush  
**Branch:** `ayush/m4-m5`  
**Status:** First controlled Base/Raw/Curated comparison completed; legal and independent human review remain pending.

> This README is an **addendum** to the existing top-level `README.md` and `DEVLOG.md` covering Jiban's M1–M3 work. Neither original file needs to be modified.

## Objective

Evaluate whether systematic synthetic-data curation improves small-language-model drafting quality compared with training on equally sized raw synthetic examples for fictional Indian employment contracts.

The **observed result was mixed**: both fine-tuned models showed much better token-limit avoidance than the base model, but curated training did not demonstrate overall superiority over raw training on the measured quality metrics.

## Inputs from M1–M3

| Item | Specification |
|---|---|
| Raw training examples | 150 |
| Curated training examples | 150 |
| Five-task distribution (each arm) | Full agreement 12; clause drafting 45; customization 45; contradiction correction 32; missing clause 16 |
| Shared training scenario IDs | 71 |
| Held-out evaluation scenarios | 40 (8 per task) |
| Held-out benchmark SHA-256 | `944ba82ed4937a41f32c064aaaa89f1b34aeb2d44a89e0860aac51aa3d46bff9` |

The synthetic cohorts are experimental training inputs, not legally certified data. The benchmark's expected facts are not adjudicated gold reference answers.

## M4 — Fine-tuning

| Setting | Value |
|---|---|
| Student model | `CohereLabs/tiny-aya-global` |
| Model revision | `af89d219b53ed9b13b8a4645f9c8028973510324` |
| Method | QLoRA, 4-bit NF4, fp16 compute |
| Workflow | AlignTune 0.1.35 with TRL-backed trainer |
| LoRA | rank 8; alpha 16; dropout 0.05; q/k/v/o projections |
| Epochs | 2 |
| Learning rate | 1e-4 |
| Microbatch / accumulation | 1 / 4 |
| Max sequence length | 3072 |
| Seed | 42 |
| Observed optimizer steps | 76 each |
| Execution | Google Colab Tesla T4 |

**Loss masking adjustment:** The working trainer was explicitly given separate `prompt` and `completion` messages so that the loss mask applied only to assistant responses. Token-level checks and a T4 smoke test verified masking before the full training runs.

Two LoRA adapters were saved independently: raw (`model_a_raw`) and curated (`model_b_curated`). The final reported training losses (~0.974 and ~1.142 respectively) should not be used to rank downstream model quality.

### Training notebook

Place the **latest fully saved Colab notebook**, not an earlier partial snapshot, at:

`notebooks/CurateLaw_M4_M5.ipynb`

The notebook must contain or link to all executed training, inference, and scoring cells needed for reproduction. Remove access tokens and other credentials, clear sensitive cell outputs, and verify the notebook opens before committing.

## M5 — Frozen inference

Generate predictions for Base, Raw and Curated on the same 40 scenarios using deterministic decoding, with maximum **1536 new tokens** for full agreements and **384** for other tasks. The saved full inference run is labeled `full_v2`.

| Model | Responses | Token-limit hits | Generated tokens |
|---|---:|---:|---:|
| Base | 40 | 39 | 24,215 |
| Raw fine-tuned | 40 | 6 | 13,477 |
| Curated fine-tuned | 40 | 5 | 13,589 |

A token-limit hit alone does not prove a response is incorrect. Similarly, not hitting the limit does not prove correctness.

## Evaluation results

| Metric | Base | Raw | Curated |
|---|---:|---:|---:|
| Token-limit avoidance | 2.50% | 85.00% | 87.50% |
| Literal expected-fact presence (M5.8 v1) | 73.99% | 71.79% | 68.93% |
| Corrected expected-fact presence (M5.10 v2) | 83.99% | 80.54% | 80.18% |
| Responses with at least one screening flag (M5.11A) | 39/40 | 15/40 | 16/40 |
| AI-assisted provisional quality review (M5.11B) | 5.125/8 | 6.000/8 | 5.875/8 |

**Matched corrected fact-presence comparison:** Curated − Raw = −0.36 percentage points; exploratory paired bootstrap 95% interval [−6.79, +3.93] percentage points. Curated wins 4 scenarios, ties 35, and loses 1 on this specific proxy.

**AI-assisted review:** Curated wins 3 scenarios, ties 30, loses 7 against raw. These scores were generated through an AI-assisted rubric, **not independent human or legal review**. Do not describe the exercise as human-adjudicated or as evidence of legal correctness.

### Task-level corrected fact presence (M5.10)

| Task | Base | Raw | Curated |
|---|---:|---:|---:|
| Full agreement | 80.36% | 71.43% | 82.14% |
| Clause drafting | 81.25% | 68.75% | 56.25% |
| Customization | 87.50% | 87.50% | 87.50% |
| Contradiction correction | 100.00% | 100.00% | 100.00% |
| Missing-clause completion | 70.83% | 75.00% | 75.00% |

**Caution:** A 100% value on automated contradiction-correction fact presence indicates detectable requested values, not that corrections were actually coherent. The revised scorer also checks spelled-out time quantities; this was a post-hoc correction of an observed false negative.

## Known failure cases

- Numeric salaries paired with inconsistent written amounts (e.g., INR 900,000 described as “Nine Crores”).
- Requested 45-day notice replaced by `[Number of Days]` in one curated response (EVAL013).
- Correct probation duration expressed as `three months` incorrectly scored as absent by v1; corrected in v2 (EVAL026).
- Incorrect termination-notice terms, unresolved placeholders, repeated paragraphs and extra explanations on wording-only tasks.
- Potentially unsupported statutory citations and contractual entitlements requiring legal review.

These are examples of why fact-presence, completion, and legal correctness must be measured separately.

## Suggested repository layout for M4–M5

```text
CurateLaw/
├── README.md                         # existing M1–M3 file; unchanged
├── DEVLOG.md                         # existing M1–M3 file; unchanged
├── decision.md                       # new M4–M5 engineering decisions
├── README_M4_M5.md                   # this addendum
├── notebooks/
│   └── CurateLaw_M4_M5.ipynb         # latest sanitized notebook (add yourself)
└── results/
    └── m4_m5/
        ├── inference_summary.json    # if available and cleared for sharing
        ├── expected_facts_v2_summary.json
        ├── quality_risk_summary.json
        └── ai_assisted_review_report.md
```

**Note:** This layout is a target, not an assertion that those notebook/results files are present in the repository. Copy only verified artifacts. In particular, do not silently rename an older partial notebook as a complete M4–M5 reproduction.

### Google Drive artifact locations

Within `MyDrive/LexiLabs/`:

- `finetuning_artifacts/model_a_raw/checkpoints/`
- `finetuning_artifacts/model_b_curated/checkpoints/`
- `evaluation_artifacts/heldout_eval_040.jsonl`
- `evaluation_artifacts/full_inference_v2/`
- `evaluation_artifacts/auditkit_results/expected_facts_v1/`
- `evaluation_artifacts/auditkit_results/expected_facts_v2/`
- `evaluation_artifacts/auditkit_results/contract_quality_screen_v1/`
- `evaluation_artifacts/blinded_quality_review_v1/`

Keep access tokens, private source documents and large checkpoint binaries out of the public Git repository.

## Reproduction and verification

1. Start from the existing M1–M3 repository and the frozen 150-example cohorts. Do not regenerate or alter the benchmark during the comparison.
2. Install compatible Colab/Python packages and authenticate to Hugging Face **through secrets**, never committed code.
3. Use the pinned model revision and inspect the completion-only mask before training.
4. Train separate raw and curated LoRA adapters from the same base revision.
5. Evaluate Base/Raw/Curated using the same 40 inputs, deterministic decoding and saved `full_v2` predictions.
6. Run AuditKIT diagnostic and expected-fact scorers against **saved predictions**. Preserve M5.8 v1 and M5.10 v2 as separate reports.
7. Run the risk screen and optional AI-assisted review. Do not represent heuristic or AI-assisted ratings as expert legal validation.

The checkpoint files and complete environment are not embedded here. To reproduce the experimental numbers exactly, use the final executed notebook and the pinned dependency/configuration artifacts from Drive. Python/package versions changed across Colab runtimes; environment locking remains follow-up work.

## Final conclusion and limitations

Both fine-tuned models substantially reduced token-limit hits relative to the base model. Curated performed better on the full-agreement fact-presence subset, but **did not exceed raw on overall corrected expected-fact presence or the exploratory AI-assisted drafting-quality rubric**. The central hiring-challenge hypothesis was therefore **not established** in this single-run, 40-scenario experiment.

The study is limited by the small held-out set, one training seed, cohort overlap, incomplete legal verification, imperfect heuristics, and non-independent AI-assisted review. No generated employment contract should be used as legal advice or without qualified review.

For methodological decisions, read [`decision.md`](decision.md). For M1–M3 history, read the existing [`README.md`](README.md) and [`DEVLOG.md`](DEVLOG.md).
