# CurateLaw-India — M1 Source Corpus (initial research deliverable)

**Research snapshot:** 2026-11-08  
**Project:** Lexsi AI Hackathon, Track 1 / Data-Scarce Domains  
**Scope:** India-based employment contracts for demonstration / research, **not legal advice**.

## Status — important disclosure
This is a **source-audited, extraction-ready starter corpus**, not a legally approved drafting dataset. **Original third-party source files are NOT bundled** (binary access unsuccessful, reuse rights not verified). The `raw_sources/` folder contains exact source links; the reproducible downloader can acquire local originals where lawful. Therefore **M1 is not yet fully complete under the original-source-file acceptance criterion**. Do not claim it is.

## Contents
- `source_metadata.csv` / `.json`: 26 traceable, typed source records; dates, jurisdiction, version, source inspection status, rights flag.
- `raw_sources/*.url`: original URLs, one per source; `tools/fetch_sources.py` downloader.
- `processed_sources/*.md`: original, independently written normalized summaries with section references, **not full scraped third-party text**.
- `processed_sources/stage2_reference_packets.jsonl`: compact structured reference items for teacher prompts with source/section/jurisdiction/risk IDs.
- `extracted_clauses/clauses.csv` / `.jsonl`: 55 source-linked, paraphrased observations; no unlicensed full clause reproductions.
- `extracted_clauses/coverage_report.json`, `dedup_report.json`, `RISK_REVIEW.md`.
- `employment_contract_schema.json`: 16-section schema; structured fields and safety checks.
- `research_notes/paper_review.md`: evaluation of all 3 requested research resources.
- `tools/audit_dataset.py`: integrity checks.
- `tools/extract_local_documents.py`: optional PDF/DOCX extraction after lawful acquisition, with page markers and content hashes.
- `M1_ACCEPTANCE_STATUS.md`: requirement-by-requirement status and blockers.

## How we collected and categorized
1. Prioritized India Code, Ministry of Labour & Employment, Gazette, PIB and Startup India's government-hosted contract examples.
2. Inspected readable primary-source text and page/section locators; recorded 2025 commencement and May 2026 Central Rules.
3. Classified private templates separately from statutory law. Added 2016 version labels and explicit rights/legal-currentness warnings.
4. Created **paraphrased normalized clause observations**, not language to transplant into an actual legal contract.
5. Retained one source per source URL; exact URL duplicate check performed. Cross-version source similarity requires original bytes and SHA256 after acquisition.

## Non-negotiable legal and data caveats
- Four central Labour Codes effective from **2025-11-21**. Relevant **May 2026 Central Rules** exist; they do not automatically supersede every State employment condition, and coverage depends on establishment/worker definitions.
- 2016 LetsVenture templates are illustrative only. The post-termination non-compete in TPL003 is flagged critical, **not approved for generation**.
- There is **no universal Indian statutory probation or notice-period number** in this corpus. Do not let the teacher invent one.
- State Shops/Establishments Acts and notifications may differ; example States are Delhi and Karnataka. Law requires current-date human verification.
- No employee personal data. Aadhaar, if referenced by a law, is a **schema consideration, not a field to populate with actual IDs**.
- Reproduction rights for publicly accessible templates and government PDFs are **NOT assumed**. The research repository's software licence cannot automatically authorize reuse of underlying legal documents.

## Stage 2 suggested prompt contract
Use only `stage2_reference_packets.jsonl` and `employment_contract_schema.json`; cite `source_id` + `source_locator` for each asserted legally constrained term. Request made-up employee identities and no real IDs. In every output require `review_status=requires_indian_legal_review` and report `compliance_flags`. For generation, start with a narrow scenario (e.g. salaried tech employee in one named State with explicitly specified pay/probation/notice choices). **Do not claim a choice is legally compliant without a checked, current, jurisdiction-matched authoritative source.**

## Remaining work before sign-off
1. Run the downloader, manually verify it acquired the intended binaries, and record content hashes.
2. For permitted local copies, run `python tools/extract_local_documents.py --permit-local-extraction` and inspect produced text.
3. Check each publisher's permission statement, mark each item either permitted for full-text research/training or metadata-only.
4. Re-check current State laws and notifications for your chosen deployment State and employment category.
5. Get an Indian labour-law practitioner to review the rule map, restrictive covenants and synthetic scenario constraints before practical use.
6. Re-run SHA256/content-based duplicate checks and inspect any near-duplicate documents after downloading originals.

Run checks: `python tools/audit_dataset.py`.
