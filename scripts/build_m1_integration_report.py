import csv
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter

base = Path("data/m1/corpus")
output_dir = base / "reports"
output_dir.mkdir(parents=True, exist_ok=True)

def read_csv(path):
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))

metadata = read_csv(base / "source_metadata.csv")

json_metadata = json.loads(
    (base / "source_metadata.json").read_text(encoding="utf-8")
)

legal_path = (
    base / "processed_sources/legal_reference_registry.jsonl"
)

legal = [
    json.loads(line)
    for line in legal_path.read_text(encoding="utf-8").splitlines()
    if line.strip()
]

tpl007 = read_csv(
    base / "extracted_clauses/TPL007_clause_candidates.csv"
)

tpl009 = read_csv(
    base / "extracted_clauses/TPL009_clause_candidates.csv"
)

triage007 = read_csv(
    base / "extracted_clauses/TPL007_high_risk_triage.csv"
)

triage009 = read_csv(
    base / "extracted_clauses/TPL009_context_review.csv"
)

csv_ids = {r["source_id"] for r in metadata}
json_ids = {r["source_id"] for r in json_metadata}

if len(csv_ids) != len(metadata):
    raise ValueError("Duplicate source IDs in CSV")

if len(json_ids) != len(json_metadata):
    raise ValueError("Duplicate source IDs in JSON")

if csv_ids != json_ids:
    raise ValueError("CSV and JSON source IDs do not match")

downloaded = base / "raw_sources/downloaded"
originals = []

for path in sorted(downloaded.iterdir()):
    if not path.is_file():
        continue

    sid = path.stem

    originals.append({
        "source_id": sid,
        "filename": path.name,
        "size_bytes": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "metadata_registered": sid in csv_ids
    })

coverage = Counter()

for row in tpl007 + tpl009:
    for category in row["category_hints"].split(";"):
        if category and category != "unclassified":
            coverage[category] += 1

unclassified = sum(
    row["category_hints"] == "unclassified"
    for row in tpl007 + tpl009
)

approved_legal = sum(
    record.get("training_eligible") is True
    for record in legal
)

report = {
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    "project": "CurateLaw-India",
    "milestone": "M1",
    "source_metadata_records": len(metadata),
    "metadata_id_consistency": True,
    "downloaded_originals": originals,
    "legal_reference_candidates": len(legal),
    "approved_legal_references": approved_legal,
    "tpl007_candidate_blocks": len(tpl007),
    "tpl009_candidate_blocks": len(tpl009),
    "unclassified_blocks": unclassified,
    "preliminary_review_records": len(triage007) + len(triage009),
    "category_hint_counts": dict(sorted(coverage.items())),
    "known_duplicate": {
        "source_id": "TPL009",
        "clause_a": "7.1",
        "clause_b": "10.1",
        "normalized_similarity": 1.0,
        "status": "duplicate_candidate"
    },
    "stage2_training_approved": False,
    "pending_gates": [
        "Source licence and training permission review",
        "Original text and section verification",
        "Legal applicability review",
        "Clause grouping and deduplication",
        "Approved reference subset creation"
    ]
}

json_path = output_dir / "m1_handoff_manifest.json"

json_path.write_text(
    json.dumps(report, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

lines = [
    "CurateLaw-India M1 Integration Report",
    "=" * 45,
    "",
    f"Source records: {len(metadata)}",
    f"Local originals: {len(originals)}",
    f"Legal candidates: {len(legal)}",
    f"TPL007 blocks: {len(tpl007)}",
    f"TPL009 blocks: {len(tpl009)}",
    f"Unclassified blocks: {unclassified}",
    f"Preliminary review records: {len(triage007) + len(triage009)}",
    f"Approved legal references: {approved_legal}",
    "",
    "Locally Acquired Sources",
    "-" * 30
]

for item in originals:
    lines.append(
        f"{item['filename']} | SHA256: {item['sha256']}"
    )

lines += [
    "",
    "Category Hints",
    "-" * 30
]

for category, count in sorted(coverage.items()):
    lines.append(f"{category}: {count}")

lines += [
    "",
    "Known Quality Issues",
    "-" * 30,
    "TPL009 clauses 7.1 and 10.1 are duplicate candidates.",
    "TPL007 contains outdated or questionable clause wording.",
    "TPL008 contains party identification and drafting errors.",
    "Some TPL009 provisions are director-specific.",
    "Legal applicability and source permissions remain unresolved.",
    "",
    "Stage 2 Status",
    "-" * 30,
    "Not approved for training or redistribution.",
    "Complete the outstanding review gates before release."
]

report_path = output_dir / "M1_INTEGRATION_REPORT.md"
report_path.write_text(
    "\n".join(lines) + "\n",
    encoding="utf-8"
)

print("M1 integration audit successful")
print("Sources:", len(metadata))
print("Local originals:", len(originals))
print("Legal references:", len(legal))
print("Contract candidate blocks:", len(tpl007) + len(tpl009))
print("Unclassified blocks:", unclassified)
print("Preliminary review records:", len(triage007) + len(triage009))
print("Stage 2 training approved:", False)
print("Report:", report_path)
print("Manifest:", json_path)
