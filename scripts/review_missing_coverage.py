import csv
import re
from pathlib import Path
from collections import Counter

base = Path("data/m1/corpus")
source = base / "extracted_clauses/M1_UNIFIED_CLAUSE_INVENTORY.csv"
output = base / "reports/M1_COVERAGE_REVIEW_QUEUE.csv"

rules = {
    "parties": [
        r"by and between",
        r"registered office",
        r"hereinafter referred to as",
        r"residing at",
        r"companies act"
    ],
    "appointment": [
        r"date of appointment",
        r"appointed as",
        r"commencement",
        r"date of joining",
        r"employment period"
    ],
    "workplace": [
        r"place of work",
        r"work location",
        r"posted at",
        r"transfer",
        r"relocation",
        r"work from home"
    ],
    "working_hours": [
        r"working hours",
        r"hours of work",
        r"overtime",
        r"working week",
        r"shift timings"
    ],
    "social_security": [
        r"provident fund",
        r"gratuity",
        r"\besic\b",
        r"social security",
        r"pension"
    ],
    "workplace_policy": [
        r"code of conduct",
        r"misconduct",
        r"disciplinary",
        r"company policies",
        r"sexual harassment"
    ],
    "signatures": [
        r"in witness whereof",
        r"signed by",
        r"signature",
        r"authorised signatory",
        r"authorized signatory"
    ]
}

with source.open(newline="", encoding="utf-8") as f:
    inventory = list(csv.DictReader(f))

queue = []

for row in inventory:
    text = row["original_text"]
    existing = set(
        value for value in row["schema_sections"].split(";")
        if value
    )

    suggestions = []

    for section, patterns in rules.items():
        if section in existing:
            continue

        if any(
            re.search(pattern, text, re.IGNORECASE)
            for pattern in patterns
        ):
            suggestions.append(section)

    if not suggestions:
        continue

    queue.append({
        "block_id": row["block_id"],
        "source_id": row["source_id"],
        "source_locator": row["source_locator"],
        "existing_sections": row["schema_sections"],
        "suggested_sections": ";".join(suggestions),
        "original_text": text,
        "risk_flags": row["risk_flags"],
        "duplicate_of": row["duplicate_of"],
        "review_status": "pending_manual_review",
        "verified_sections": "",
        "review_notes": "",
        "approved_for_training": "false"
    })

fields = [
    "block_id",
    "source_id",
    "source_locator",
    "existing_sections",
    "suggested_sections",
    "original_text",
    "risk_flags",
    "duplicate_of",
    "review_status",
    "verified_sections",
    "review_notes",
    "approved_for_training"
]

with output.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(queue)

counts = Counter()

for row in queue:
    for section in row["suggested_sections"].split(";"):
        counts[section] += 1

print("Total inventory blocks:", len(inventory))
print("Blocks needing additional classification:", len(queue))
print()

for section in rules:
    print(section, ":", counts[section])

print()
print("Existing duplicate candidates:")

for row in inventory:
    if row["duplicate_of"]:
        print(row["block_id"], "duplicates", row["duplicate_of"])

print()
print("Saved:", output)
