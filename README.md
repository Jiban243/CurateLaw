# CurateLaw-India

**Quality-aware synthetic data for Indian employment-contract drafting**

[Repository](https://github.com/Jiban243/CurateLaw) · [Development history](DEVLOG.md)

> **Project status (10 November 2026):** M1 reference-corpus preparation and M2 synthetic generation have been completed at prototype level. M3 automated curation and provisional cohort selection are complete; **human calibration and legal review are next**. No model has been fine-tuned or evaluated yet, and no legal/training approvals are implied by the screening results.

## Overview

CurateLaw-India addresses a **data-scarce-domain challenge**: when high-quality domain-specific instruction data is scarce, can generating, verifying, and filtering synthetic examples produce better fine-tuning outcomes than using unfiltered generated examples?

Our domain is **Indian employment-contract drafting**. The project builds a traceable reference corpus, generates fictional drafting instructions and corresponding model-written responses, applies quality-aware curation, and will test the effect of curation on a small Cohere Labs open-weight language model.

**Primary research question:** With the **same base model, number of training examples, training configuration, and held-out evaluation set**, does a model trained on *curated synthetic data* outperform one trained on a *random sample of raw synthetic data*?

This is an experimental research prototype, **not a production legal-document service or a source of legal advice**.

## Experimental design

```text
M1  Real-world legal/template references and 16-section contract schema
       |
       | inform task design, risk checks and review criteria
       v
M2  Independently authored fictional scenarios
       |
       v
    Teacher LLM (Qwen3-235B-A22B-Instruct-2507 via Hugging Face)
       |
       v
    400 synthetic instruction-response pairs (frozen raw pool)
       |
       +------------------------------+
       |                              |
       v                              v
    Raw baseline                 CuratorKIT + domain checks
    Random selection             Quality / factual / diversity selection
       |                              |
       v                              v
    150 raw candidates           150 curated candidates
       |                              |
       v                              v
    Model A via AlignTune        Model B via AlignTune
       +---------------+--------------+
                       |
                       v
              AuditKIT evaluation
           + base model comparison
          (40 held-out scenarios)
```

**Key distinction:** M1's extracted real-world clauses are **reference/review material**, not the supervised synthetic examples and not automatically cleared for training. Both experimental fine-tuning cohorts must come from the **same M2 synthetic pool**. The raw baseline uses random selection; the curated baseline uses explicit quality-based selection with **matched task quotas**.

## Progress and verified dataset counts

| Stage | Result | Status |
| --- | --- | --- |
| **M1 — Source registry** | 29 metadata entries; 6 locally acquired originals (3 templates, 2 central-law PDFs, 1 Delhi government HTML source) | Prepared; provenance and usage-rights review outstanding |
| **M1 — Contract extraction** | 228 text-block candidates from TPL007 (90) and TPL009 (138) | Classified provisionally; not 228 complete contracts or verified clauses |
| **M1 — Other reference data** | 55 earlier normalized clause observations; 15 statutory-reference candidates; 16-section schema | Separate record types; **do not add these counts as training samples** |
| **M1 — Review** | 22 prioritized contract-block decisions | Preliminary; manual and legal review pending |
| **M2 — Training scenario pool** | 400 fictional scenarios across 5 drafting tasks | Generated |
| **M2 — Raw synthetic data** | **400 distinct scenario IDs and 400 saved instruction-response pairs** | Frozen and hash-verified |
| **M2 — Evaluation** | **40** held-out fictional scenarios, 8 per task | Prepared; human review and semantic leakage checks pending |
| **M3 — CuratorKIT hygiene** | 400 passed / 0 rejected | Schema, cleaning and exact *pair* deduplication only |
| **M3 — Domain screening** | **309** strong candidates, **84** manual-review holds, **7** provisional exclusions | Heuristic classifications, **not legal approvals** |
| **M3 — Candidate cohorts** | 150 raw and 150 curated; 56 shared scenario IDs | Provisional, task-matched, not training-ready |
| **M3 — Human calibration** | 27 review records prepared | **Next step** |
| **M4–M6 — Fine-tuning/evaluation** | No models trained; no comparison scores yet | Not started |

### Synthetic task distribution

| Task | Raw generated pool | Curated cohort target (150) |
| --- | ---: | ---: |
| Full agreement drafting | 120 | 45 |
| Individual clause drafting | 100 | 38 |
| Contract customization | 80 | 30 |
| Contradiction correction | 60 | 22 |
| Missing-clause completion | 40 | 15 |
| **Total** | **400** | **150** |

The raw candidate cohort is also stratified to the same 150-example task quotas. Its recorded screening tiers were **122 strong / 26 held / 2 provisionally excluded**; the curated candidate cohort contains **150 strong-screening candidates**. These differences describe **data selection**, not measured model performance.

## Data provenance and reproducibility

The **frozen raw pool** contains exactly 400 unique IDs (`GEN0001`–`GEN0400`). Its SHA-256 checksum is:

```text
ec94fba3a90b3cd9853b42ac9365154aa54f5973e183f2e06ca2895b127b466b
```

The frozen 40-case evaluation file was separately fingerprinted:

```text
944ba82ed4937a41f32c064aaaa89f1b34aeb2d44a89e0860aac51aa3d46bff9
```

We observed **21 extra occurrences of identical normalized responses**. CuratorKIT's exact instruction-following deduplicator passed all 400 because repeated response text does not necessarily imply an identical **instruction + input + output** record. Response-only repetition is therefore recorded for further task-aware diversity analysis.

The initial leakage check found **zero exact instruction matches** between the synthetic training pool and the evaluation prompts. **Semantic similarity, shared templates, and broader leakage have not yet been ruled out.**

## Repository layout

The paths below describe artifacts created by the pipeline. Some may be **local-only or deliberately excluded from Git** (especially third-party originals and extracted copyrighted text).

```text
.
├── README.md
├── DEVLOG.md
├── scripts/
│   ├── m2_prepare_training_pool.py
│   ├── m2_generate_batch.py
│   ├── m2_audit_batch.py
│   ├── m3_score_curatelaw.py
│   └── m3_prepare_candidate_cohorts.py
└── data/
    ├── m1/corpus/
    │   ├── source_metadata.csv
    │   ├── source_metadata.json
    │   ├── employment_contract_schema.json
    │   ├── raw_sources/downloaded/         (third-party originals; restricted)
    │   ├── extracted_clauses/              (review candidates; restricted)
    │   └── reports/
    ├── m2/
    │   ├── scenarios/                      (training prompts)
    │   ├── generated_raw/pool_raw.jsonl
    │   ├── frozen/
    │   │   ├── pool_raw_0400.jsonl
    │   │   ├── heldout_eval_040.jsonl
    │   │   └── freeze_manifest.json
    │   ├── evaluation/                     (held-out cases and manifest)
    │   └── quality_reports/
    └── m3/
        ├── curatorkit_hygiene/
        ├── domain_curation/                (scores, tiers, review queue)
        └── provisional_cohorts/            (150/150 IDs, calibration queue)
```

Additional source-extraction and inspection scripts live under `data/m1/corpus/tools/` and `scripts/`, depending on the stage.

## Local setup

Development so far has used **Python 3.11** on macOS, a project-local virtual environment, [CuratorKIT](https://github.com/Lexsi-Labs/CuratorKIT) and [Hugging Face Inference Providers](https://huggingface.co/docs/inference-providers/index).

```bash
cd CurateLaw-India
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install curatorkit huggingface_hub pandas pymupdf python-docx
```

If cloning the GitHub repository directly, use the directory name created by `git clone` instead. Install any additional dependencies required by individual scripts. Dependency versions and a locked environment file still need finalization.

For new teacher-generation runs, use a **Hugging Face token with Inference Providers permission**. The generator prompts for it without echoing it. Never commit access tokens, `.env` files, `.venv/`, or downloaded third-party legal documents. API inference and GPU fine-tuning may be billed separately.

### Reproduce completed local checks

Assuming the relevant local data files exist:

```bash
python scripts/m2_audit_batch.py
python scripts/m3_score_curatelaw.py
python scripts/m3_prepare_candidate_cohorts.py
```

To reproduce the initial CuratorKIT hygiene pass on the frozen pool:

```python
from curatorkit import Curator, CuratorConfig

result = Curator(CuratorConfig(
    dataset="data/m2/frozen/pool_raw_0400.jsonl",
    name="curatelaw_400_hygiene",
    dedup="exact",
    clean=True,
    schema_gate=True,
    min_tokens=5,
    max_tokens=6000,
    export_formats=["alpaca"],
    output_dir="data/m3/curatorkit_hygiene",
)).run()
result.print_summary()
```

**Do not rerun the paid generator to reproduce a frozen dataset.** Use the saved raw pool and its checksum. Running the same model again does not guarantee byte-identical responses.

## M3 curation approach

We separate **mechanical validity**, **task/domain quality**, and **human/legal approval**:

1. **CuratorKIT hygiene:** schema gate, exact pair deduplication, and text cleaning.
2. **Deterministic domain screening:** task-sensitive response length and structure; salary, role, notice, probation and work-arrangement preservation; flagged restrictive language; legal-currency and cross-jurisdiction checks.
3. **Candidate selection:** score/rank examples within each task, control duplicates and preserve quota-matched task diversity.
4. **Human calibration:** inspect strong, held and excluded examples for false positives/negatives; record reviewers' rationales and adjust rules reproducibly.
5. **Separate clearance:** verify legal applicability and any source-use permissions before approving material for actual model training.

Examples discovered during validation include an **incomplete full agreement**, **role inconsistency**, **validator false positives for Markdown headings/signature blocks**, and **an outdated statutory-reference candidate**. These findings motivate curation rules; they do not establish that the rules catch every relevant failure.

### Current cohort preparation

- **Raw candidates:** 150 records sampled randomly within task quotas from the frozen pool, irrespective of heuristic quality.
- **Curated candidates:** 150 higher-scoring records within identical task quotas; zero repeated normalized responses within this cohort.
- **Overlap:** 56 IDs shared across cohorts. This is allowed because the models are trained separately; all evaluation scenarios remain excluded.
- **Calibration:** 27 human-review records available in `data/m3/provisional_cohorts/M3_CALIBRATION_REVIEW.csv`, with a readable companion report.
- **Approval:** All candidate datasets remain **provisional**; no training approval has been granted.

## Evaluation plan (not yet executed)

The intended comparison uses the **same Cohere Labs open-weight base checkpoint**, equal 150-example training cohorts, equal training hyperparameters and decoding settings, and one independent 40-case benchmark. [AlignTune](https://github.com/Lexsi-Labs/aligntune) is planned for fine-tuning; [AuditKIT](https://github.com/Lexsi-Labs/AuditKIT) is planned for model evaluation.

Metrics under consideration include required-clause coverage, instruction/fact consistency, unsupported contractual terms, contradictions, format compliance, and task-specific success. Legal-quality judgments need a documented, human-reviewed rubric. **There are no measured model A versus model B results yet.**

## Limitations and responsible use

- **Source rights:** Original third-party PDF/DOCX/HTML documents and their extracted text are **not automatically licensed for redistribution or training**. M1 permission review remains open; keep restricted artifacts out of public commits.
- **Legal currency:** Applicability depends on jurisdiction, employee category, commencement dates, transitional provisions and current law. Automated keyword checks are not legal opinions.
- **Automated scoring:** The 309/84/7 screening split describes heuristic tiers only; even a strong candidate may contain unsupported assertions or drafting defects.
- **Evaluation validity:** Current held-out cases are fictional and not fully human verified. Exact-match isolation alone is insufficient to rule out semantic leakage.
- **Generalization:** A small task-matched comparison will not establish universal performance across all Indian employment contracts or states.
- **Budget:** Teacher inference was tested through Hugging Face; GPU training costs and the final student checkpoint still require validation.

## Immediate next steps

1. **M3.4 — Human calibration:** review the 27 cases, log accepted flags, false positives/negatives and legal-review holds; refine and rerun scoring when justified.
2. **M3 finalization:** audit near-duplicates and diversity, validate legal/permission gates, and freeze approved, quota-matched raw and curated training manifests.
3. **M4/M5 — AlignTune:** select a suitable Cohere Labs checkpoint, run a low-cost smoke test and fine-tune both cohorts with identical settings.
4. **M6 — AuditKIT:** validate the held-out benchmark and report base/raw/curated results, failure breakdowns, costs and limitations.

## Contributions and project history

CurateLaw-India is being developed by a **two-person team**. **Jiban ([Jiban243](https://github.com/Jiban243))** has led the M1–M3 data preparation and reported pipeline runs documented here. The shared [DEVLOG.md](DEVLOG.md) records contributor-specific decisions, commit references and engineering trade-offs as the project evolves. Additional contributions should be attributed in that log and in Git history.

---

*Research prototype for the Track 1 data-scarce-domains challenge. Do not use generated agreements without qualified legal review.*
