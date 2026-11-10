import csv
import re
from pathlib import Path
import pymupdf

base = Path("data/m1/corpus")
pdf_dir = base / "raw_sources/downloaded"
output = base / "processed_sources/legal_section_review_queue.csv"

targets = [
    ("LAW002", "5", "minimum_wages",
     "no employer shall pay to any employee wages less than"),
    ("LAW002", "14", "overtime",
     "the overtime rate which shall not be less than twice"),
    ("LAW002", "17", "wage_payment",
     "the employer shall pay or cause to be paid wages to the employees"),
    ("LAW002", "18", "deductions",
     "there shall be no deductions from the wages of the employee"),
    ("LAW009", "10", "contract_validity",
     "all agreements are contracts if they are made"),
    ("LAW009", "14", "free_consent",
     "consent is said to be free when it is not caused by"),
    ("LAW009", "23", "lawful_consideration",
     "the consideration or object of an agreement is lawful"),
    ("LAW009", "27", "restraint_of_trade",
     "every agreement by which any one is restrained"),
    ("LAW009", "73", "breach_compensation",
     "the party who suffers by such breach is entitled"),
    ("LAW009", "74", "penalty",
     "if a sum is named in the contract as the amount")
]

documents = {}

for source_id in ["LAW002", "LAW009"]:
    with pymupdf.open(pdf_dir / f"{source_id}.pdf") as doc:
        documents[source_id] = [
            re.sub(r"\s+", " ", page.get_text("text")).strip()
            for page in doc
        ]

rows = []

for source_id, section, category, anchor in targets:
    found = False

    for page_number, text in enumerate(documents[source_id], start=1):
        position = text.casefold().find(anchor.casefold())

        if position == -1:
            continue

        found = True

        rows.append({
            "source_id": source_id,
            "section_number": section,
            "category": category,
            "pdf_page": page_number,
            "text_excerpt": text[
                max(0, position - 180):position + 450
            ],
            "review_status": "pending",
            "notes": ""
        })

    if not found:
        print(f"NOT FOUND: {source_id} Section {section}")

fields = [
    "source_id", "section_number", "category",
    "pdf_page", "text_excerpt", "review_status", "notes"
]

with open(output, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)

for row in rows:
    print(
        row["source_id"],
        "Section", row["section_number"],
        "PDF page", row["pdf_page"],
        row["category"]
    )

print("Review candidates:", len(rows))
print("Saved:", output)
