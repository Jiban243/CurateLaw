import csv
import json
import re
import hashlib
from pathlib import Path
from collections import Counter

base = Path("data/m1/corpus")
clause_dir = base / "extracted_clauses"
report_dir = base / "reports"
report_dir.mkdir(exist_ok=True)

schema = json.loads(
    (base / "employment_contract_schema.json").read_text(
        encoding="utf-8"
    )
)

section_ids = {
    section["section_id"]
    for section in schema["sections"]
}

category_map = {
    "employment_role": "role_duties",
    "compensation": "compensation",
    "probation": "probation",
    "working_conditions": "working_hours",
    "leave": "leave_benefits",
    "benefits": "leave_benefits",
    "confidentiality": "confidentiality",
    "intellectual_property": "ip",
    "termination": "termination",
    "notice_period": "termination",
    "dispute_resolution": "dispute_resolution",
    "restrictive_covenants": "optional"
}

with (base / "source_metadata.csv").open(
    encoding="utf-8", newline=""
) as f:
    metadata = {
        row["source_id"]: row
        for row in csv.DictReader(f)
    }

with (
    clause_dir / "TPL007_high_risk_triage.csv"
).open(encoding="utf-8", newline="") as f:
    triage = {
        row["block_id"]: row
        for row in csv.DictReader(f)
    }

sources = {
    "TPL007": "TPL007_clause_candidates.csv",
    "TPL009": "TPL009_clause_candidates.csv"
}

original_files = {
    "TPL007": "TPL007.docx",
    "TPL009": "TPL009.pdf"
}

inventory = []

for source_id, filename in sources.items():
    original = (
        base / "raw_sources/downloaded"
        / original_files[source_id]
    )

    digest = hashlib.sha256(
        original.read_bytes()
    ).hexdigest()

    with (clause_dir / filename).open(
        encoding="utf-8", newline=""
    ) as f:
        rows = list(csv.DictReader(f))

    for index, row in enumerate(rows, 1):
        text = row["text"].strip()

        hints = [
            item.strip()
            for item in row["category_hints"].split(";")
            if item.strip()
            and item.strip() != "unclassified"
        ]

        sections = sorted({
            category_map[category]
            for category in hints
            if category in category_map
        })

        if not set(sections).issubset(section_ids):
            raise ValueError("Invalid schema section")

        block_id = row.get(
            "block_id", f"{source_id}_B{index:03d}"
        )

        locator = row.get("source_locator", "")

        if not locator:
            locator = (
                f"PDF page {row.get('pdf_page', '')}, "
                f"block {row.get('block_number', '')}"
            )

        review = triage.get(block_id, {})

        risk_flags = [
            item.strip()
            for item in row.get("risk_flags", "").split(";")
            if item.strip()
        ]

        if review:
            risk_flags.append(
                review["risk_category"]
            )

        normalized = re.sub(
            r"^\s*\d+(?:\.\d+)*\s+",
            "",
            text
        )

        normalized = re.sub(
            r"\s+", " ", normalized
        ).strip().casefold()

        inventory.append({
            "block_id": block_id,
            "source_id": source_id,
            "source_url": metadata[source_id]["source_url"],
            "source_locator": locator,
            "source_sha256": digest,
            "original_text": text,
            "category_hints": ";".join(hints),
            "schema_sections": ";".join(sections),
            "risk_flags": ";".join(sorted(set(risk_flags))),
            "review_decision": review.get(
                "curation_decision",
                "pending_manual_review"
            ),
            "duplicate_of": "",
            "normalized_hash": hashlib.sha256(
                normalized.encode("utf-8")
            ).hexdigest(),
            "normalized_length": len(normalized),
            "legal_review_status": "pending",
            "permission_status": "uncleared",
            "approved_for_training": "false"
        })

seen = {}

for row in inventory:
    if row["normalized_length"] < 100:
        continue

    fingerprint = row["normalized_hash"]

    if fingerprint in seen:
        row["duplicate_of"] = seen[fingerprint]
    else:
        seen[fingerprint] = row["block_id"]

inventory_path = (
    clause_dir / "M1_UNIFIED_CLAUSE_INVENTORY.csv"
)

with inventory_path.open(
    "w", encoding="utf-8", newline=""
) as f:
    writer = csv.DictWriter(
        f, fieldnames=list(inventory[0])
    )
    writer.writeheader()
    writer.writerows(inventory)

coverage = Counter()

for row in inventory:
    for section in row["schema_sections"].split(";"):
        if section:
            coverage[section] += 1

report = {
    "total_blocks": len(inventory),
    "sources": sorted(sources),
    "unmapped_blocks": sum(
        not row["schema_sections"]
        for row in inventory
    ),
    "exact_duplicate_candidates": sum(
        bool(row["duplicate_of"])
        for row in inventory
    ),
    "schema_coverage": {
        section["section_id"]: {
            "heading": section["heading"],
            "candidate_blocks": coverage[
                section["section_id"]
            ]
        }
        for section in schema["sections"]
    },
    "training_approved": False,
    "review_status": "preliminary_candidates_only"
}

report_path = report_dir / "M1_SCHEMA_COVERAGE.json"

report_path.write_text(
    json.dumps(report, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

print("Unified inventory created")
print("Total blocks:", len(inventory))
print("Unmapped blocks:", report["unmapped_blocks"])
print("Duplicate candidates:", report["exact_duplicate_candidates"])
print("Schema sections:", len(schema["sections"]))
print("Training approved:", False)
print("Inventory:", inventory_path)
print("Coverage report:", report_path)

print("\nSchema coverage:")

for section_id, details in report["schema_coverage"].items():
    print(section_id, details["candidate_blocks"])
