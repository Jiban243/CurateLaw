import json
import csv
import re
from pathlib import Path
from collections import Counter

base = Path("data/m2")
raw_file = base / "generated_raw/synthetic_smoke_005.jsonl"
report_dir = base / "quality_reports"
report_dir.mkdir(parents=True, exist_ok=True)

def load_jsonl(path):
    with path.open(encoding="utf-8") as f:
        return [
            json.loads(line)
            for line in f
            if line.strip()
        ]

def extract(pattern, text):
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1).strip() if match else None

def number_mentioned(text, number, unit):
    pattern = (
        rf"\b{re.escape(str(number))}\b"
        rf".{{0,25}}\b{re.escape(unit)}\b"
    )
    return bool(re.search(pattern, text, re.IGNORECASE))

sections = {
    "parties": ["employer", "employee", "company"],
    "appointment": ["appointment", "commencement", "joining date"],
    "role_duties": ["duties", "responsibilities"],
    "workplace": ["place of work", "work location", "remote", "hybrid", "on-site"],
    "compensation": ["salary", "remuneration", "compensation"],
    "probation": ["probation"],
    "working_hours": ["working hours", "hours per week", "work schedule"],
    "leave_benefits": ["leave", "holiday"],
    "social_security": ["statutory benefits", "provident fund", "social security"],
    "confidentiality": ["confidential"],
    "ip": ["intellectual property", "inventions", "copyright"],
    "workplace_policy": ["conduct", "workplace policy", "company policy"],
    "termination": ["termination", "notice period"],
    "dispute_resolution": ["dispute", "arbitration", "jurisdiction"],
    "signatures": ["signature", "signed by", "in witness"],
    "optional": ["optional"]
}

raw = load_jsonl(raw_file)
results = []

for record in raw:
    sid = record["scenario_id"]
    instruction = record["instruction"]
    output = record["output"]
    lower = output.lower()

    role = extract(r"Role:\s*([^.]+)\.", instruction)
    salary = extract(r"Annual compensation:\s*INR\s*(\d+)", instruction)
    probation = extract(r"Probation:\s*(\d+)\s*months", instruction)
    notice = extract(
        r"Mutual contractual notice:\s*(\d+)\s*days",
        instruction
    )

    normalized_output = re.sub(r"[\s,]", "", output)

    checks = {
        "role_found": bool(role and role.lower() in lower),
        "salary_found": bool(salary and salary in normalized_output),
        "probation_number_found": bool(
            probation and number_mentioned(output, probation, "months")
        ),
        "notice_number_found": bool(
            notice and number_mentioned(output, notice, "days")
        ),
        "numbered_format": bool(
            len(set(re.findall(r"(?m)^[ \t]*(?:\x23{1,6}[ \t]*)?(?:\*\*|__)?(\d{1,2})[.)][ \t]+[A-Za-z]", output))) >= 5
        ),
        "minimum_length": len(output.split()) >= 350
    }

    covered = [
        name
        for name, words in sections.items()
        if name != "optional"
        and any(word in lower for word in words)
    ]

    risks = []

    if "companies act 2006" in lower:
        risks.append("foreign_uk_law_reference")

    if re.search(r"non[- ]compete|restraint of trade", lower):
        risks.append("restrictive_covenant_check")

    if re.search(r"without (?:prior )?notice", lower):
        risks.append("termination_notice_check")

    if re.search(r"forfeit|automatic injunction", lower):
        risks.append("penalty_or_forfeiture_check")

    failed = [
        name for name, passed in checks.items()
        if not passed
    ]

    results.append({
        "scenario_id": sid,
        "word_count": len(output.split()),
        "section_keyword_count": len(covered),
        "section_keyword_matches": ";".join(covered),
        "failed_automated_checks": ";".join(failed),
        "risk_review_flags": ";".join(risks),
        "screening_status": (
            "needs_manual_review"
            if failed or risks or len(covered) < 12
            else "automated_checks_passed"
        ),
        "legal_review_status": "unverified",
        "approved_for_training": "false"
    })

output_csv = report_dir / "M2_SMOKE_QUALITY_AUDIT.csv"

with output_csv.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(results[0]))
    writer.writeheader()
    writer.writerows(results)

summary = {
    "total_generated": len(results),
    "status_counts": dict(
        Counter(r["screening_status"] for r in results)
    ),
    "average_keyword_section_count": round(
        sum(r["section_keyword_count"] for r in results)
        / len(results), 2
    ),
    "human_legally_verified": 0,
    "training_approved": 0,
    "caution": (
        "Heuristic checks are not sufficient for legal verification. "
        "Missing checks may also reflect different wording."
    )
}

output_json = report_dir / "M2_SMOKE_AUDIT_SUMMARY.json"
output_json.write_text(
    json.dumps(summary, indent=2),
    encoding="utf-8"
)

print("Total generated:", len(results))
print("Average keyword section coverage:",
      summary["average_keyword_section_count"])
print("Screening distribution:", summary["status_counts"])
print("Training approved:", 0)

for row in results:
    print("\nScenario:", row["scenario_id"])
    print("Words:", row["word_count"])
    print("Keyword section matches:", row["section_keyword_count"])
    print("Failed checks:", row["failed_automated_checks"] or "None")
    print("Risk flags:", row["risk_review_flags"] or "None")
    print("Screening:", row["screening_status"])

print("\nSaved:", output_csv)
print("Summary:", output_json)
