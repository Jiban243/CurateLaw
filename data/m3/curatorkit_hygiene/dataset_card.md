# Dataset Card: curatelaw_400_hygiene

## Summary

- **Run timestamp**: 2026-11-09T17:07:49.691557Z
- **Wall clock time**: 0.1s
- **Pipeline config hash**: `6c7214362c6e46a4`

## Source Documents

  - Unknown

## Pipeline Stages

| Step | Input | Passed | Recovered | Rejected | Forward |
|------|-------|--------|-----------|----------|---------|
| JSONLReader | 400 | 400 | — | 0 | 400 |
| SchemaGate | 400 | 400 | 0 | 0 | 400 |
| ExactDeduplicator | 400 | 400 | — | — | 400 |
| TextCleaner | 400 | 400 | — | — | 400 |
| AlpacaExporter | — | 400 | — | — | 400 |

## Gate Pass Rates and Rejection Breakdown

- **JSONLReader**: 400/0 passed (N/A), 0 rejected
- **SchemaGate**: 400/400 passed (100.0%), 0 rejected


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
