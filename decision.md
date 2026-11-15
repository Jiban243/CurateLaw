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
