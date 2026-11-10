# Three requested references: relevance to CurateLaw-India

## RES001 — VidhikDastaavej, LREC 2026
- Introduces a dataset of **11,825** anonymized private legal documents across **133 categories**. This is **not** itself evidence that this dataset has 138 employment-contract examples or an M1 employment-law source.
- Presents a **model-agnostic, two-stage** process: plan document sections, then generate grounded sections using retrieved context. Reports better structure and expert-rated outcomes than the fine-tuned baselines evaluated.
- Recommendation for this project: structure each synthetic label as independent contract sections with clause-specific evidence references and evaluate section coverage and factual consistency. Benchmark a structured retrieval baseline; do not assume fine-tuning wins.
- Repository has an Apache-2.0 LICENSE file, but separate permission for underlying law-firm-derived document corpus must be checked before using/redistributing data.

## RES002 — Medium blog, 10 March 2025
- Describes **Llama-3.2-1B-Instruct**, **LoRA with 4-bit quantization**, and locally generated synthetic contract examples using **DeepSeek-R1 14B**.
- Practical implementation precedent, **not legal authority** and **not independently verified evidence** of legally correct contracts. It does not demonstrate a matched raw-vs-curated data ablation in the article.
- Recommendation: use only for architecture inspiration and require explicit citation and human/legal review in Stage 2.

## RES003 — Lin & Cheng, 2024
- Describes tuning a pretrained LLM for legal-document drafting with unannotated documents and privacy-oriented local workflows.
- The focus includes Chinese legal text, **not Indian employment law**. Do not cite it as a source of Indian contract clauses.

## Gap / testable hypothesis
Our contribution is not 'AI writes contracts'; it is **raw synthetic vs equally sized verified synthetic training data** for a narrow Indian employment-drafting task, with immutable scenario holdout and source-grounding/compliance evaluations. The teacher-generated examples must not copy other parties' long template text or include fabricated legal requirements.
