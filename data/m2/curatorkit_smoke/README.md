---
tags:
- curatorkit
configs:
- config_name: sft_alpaca
  default: true
  description: curatorkit sft_alpaca export, sha256 7bb7e5103d7c5e024d044d6720d5b1f62ce89f6bc8de77071a5b5640edc28652
  data_files:
  - split: train
    path: sft_alpaca.jsonl
---

# Dataset Card: curatelaw_m2_smoke

## Summary

- **Run timestamp**: 2026-11-09T09:28:03.109457Z
- **Wall clock time**: 0.0s
- **Pipeline config hash**: `6843d9f72cbc03ea`

## Source Documents

  - Unknown

## Pipeline Stages

| Step | Input | Passed | Recovered | Rejected | Forward |
|------|-------|--------|-----------|----------|---------|
| JSONLReader | 5 | 5 | — | 0 | 5 |
| SchemaGate | 5 | 5 | 0 | 0 | 5 |
| ExactDeduplicator | 5 | 5 | — | — | 5 |
| TextCleaner | 5 | 5 | — | — | 5 |
| AlpacaExporter | — | 5 | — | — | 5 |

## Gate Pass Rates and Rejection Breakdown

- **JSONLReader**: 5/0 passed (N/A), 0 rejected
- **SchemaGate**: 5/5 passed (100.0%), 0 rejected


**Rejection reasons:**
  - None

## Deduplication

  - exact_duplicates_removed: 0

## Known Limitations

- No MinHash deduplication applied.
- Table extraction requires `extract_tables: true` on the PDF reader and MinerU with GPU support. Disabled by default.
- Token counting uses a whitespace tokenizer by default. For exact LLM context window
  enforcement, enable `use_tiktoken: true` in the SchemaGate config.
- Both within-run (MinHash/Diversity) and cross-run (EmbeddingDeduplicator) deduplication
  are available. Cross-run dedup persists an embedding index across runs; use
  `embedding_reset_index: true` to start fresh.

## Reproduction

```bash
pip install curatorkit
curatorkit run pipeline.yaml --output-dir ./out/
```

## Tool Versions

- **curatorkit**: 0.1.23
- **python**: 3.11.17

## Configs

Load one with `datasets.load_dataset("<this folder or Hub repo>", "<config>")`.

| Config | Splits (rows) | Columns |
|--------|---------------|---------|
| `sft_alpaca` | train (5) | `instruction`: string<br>`input`: string (empty when there is no input)<br>`output`: string |
