---
tags:
- curatorkit
configs:
- config_name: sft_alpaca
  default: true
  description: curatorkit sft_alpaca export, sha256 c35ae3742e6fa9a2a0599bc645160ff61650a72416704a9f5800a73682a32938
  data_files:
  - split: train
    path: sft_alpaca.jsonl
---

# Dataset Card: curatelaw_diverse_pilot

## Summary

- **Run timestamp**: 2026-11-09T11:04:58.730840Z
- **Wall clock time**: 0.0s
- **Pipeline config hash**: `32a7923b51e73656`

## Source Documents

  - Unknown

## Pipeline Stages

| Step | Input | Passed | Recovered | Rejected | Forward |
|------|-------|--------|-----------|----------|---------|
| JSONLReader | 10 | 10 | — | 0 | 10 |
| SchemaGate | 10 | 10 | 0 | 0 | 10 |
| ExactDeduplicator | 10 | 10 | — | — | 10 |
| TextCleaner | 10 | 10 | — | — | 10 |
| AlpacaExporter | — | 10 | — | — | 10 |

## Gate Pass Rates and Rejection Breakdown

- **JSONLReader**: 10/0 passed (N/A), 0 rejected
- **SchemaGate**: 10/10 passed (100.0%), 0 rejected


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
| `sft_alpaca` | train (10) | `instruction`: string<br>`input`: string (empty when there is no input)<br>`output`: string |
