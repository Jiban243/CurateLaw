
import csv
from collections import Counter
from pathlib import Path


ROOT = Path("data/m3/v2_diagnostics")

SOURCE = ROOT / "M3_SINGLE_FLAG_FULL_AGREEMENTS.csv"
WORKING = ROOT / "M3_SINGLE_FLAG_HUMAN_REVIEW.csv"


REVIEWS = {
    "GEN0005": {
        "flag": "probation_notice_exception_requires_review",
        "decision": "hold_justified",
        "notes": (
            "The instruction specifies four months of probation "
            "and 30 days of mutual notice for a Platform Engineer "
            "in Punjab. The generated agreement instead permits "
            "either party to terminate during probation using "
            "seven days of written notice or payment in lieu, "
            "while the general termination clause provides "
            "30 days. This is an explicit but unrequested "
            "exception to the specified notice period. "
            "The exception is not automatically unlawful, "
            "but it changes a material contractual condition "
            "and requires clarification or revision. "
            "V2 correctly held this example. "
            "Not approved for training."
        ),
    },
    "GEN0114": {
        "flag": "employer_only_notice_pay_option_review",
        "decision": "hold_justified",
        "notes": (
            "The instruction specifies six months of probation "
            "and 30 days of mutual notice for a Cloud Security "
            "Engineer in Kerala. The response includes the "
            "mutual 30-day notice obligation, but expressly "
            "allows the employer to terminate immediately "
            "by paying salary in lieu of notice. A comparable "
            "employee option is not expressly provided. "
            "The probation clause additionally gives the "
            "employer termination discretion without assigning "
            "reasons, subject to its wording and applicable law. "
            "These features require contractual and legal review. "
            "The V2 hold is justified; no training approval."
        ),
    },
    "GEN0031": {
        "flag": "unrequested_probation_extension",
        "decision": "hold_justified",
        "notes": (
            "The instruction specifies five months of probation "
            "and 45 days of mutual notice for a Network Engineer "
            "in Tamil Nadu. The response preserves these initial "
            "terms but adds an employer-controlled extension "
            "of probation by up to one additional month. "
            "This could increase the effective probation period "
            "to six months without explicit authorization in "
            "the instruction. The extension is not automatically "
            "unlawful, but it is an unrequested material term. "
            "V2 correctly held the example for review. "
            "Not approved for training."
        ),
    },
}


def read_csv(path):
    with path.open(
        "r",
        encoding="utf-8",
        newline=""
    ) as file:
        reader = csv.DictReader(file)
        fields = reader.fieldnames
        rows = list(reader)

    if not fields:
        raise ValueError(
            f"CSV has no header: {path}"
        )

    return fields, rows


def main():
    if not SOURCE.is_file():
        raise SystemExit(
            f"Missing source file: {SOURCE}"
        )

    source_fields, source_rows = read_csv(SOURCE)

    if len(source_rows) != 46:
        raise SystemExit(
            "Expected 46 single-flag agreements, found "
            f"{len(source_rows)}."
        )

    if WORKING.exists():
        fields, rows = read_csv(WORKING)

        if len(rows) != 46:
            raise SystemExit(
                "Existing review file has unexpected row count."
            )
    else:
        fields = source_fields
        rows = [dict(row) for row in source_rows]

    required = {
        "scenario_id",
        "flag",
        "human_review_decision",
        "human_review_notes",
        "approved_for_training",
    }

    if not required.issubset(set(fields)):
        raise SystemExit(
            "Required review columns are missing."
        )

    index = {}

    for row in rows:
        sid = row["scenario_id"]

        if sid in index:
            raise SystemExit(
                f"Duplicate scenario ID: {sid}"
            )

        index[sid] = row

    source_ids = {
        row["scenario_id"]
        for row in source_rows
    }

    if set(index) != source_ids:
        raise SystemExit(
            "Working review IDs differ from original IDs."
        )

    for sid, review in REVIEWS.items():
        if sid not in index:
            raise SystemExit(
                f"Missing reviewed example: {sid}"
            )

        row = index[sid]

        if row["flag"] != review["flag"]:
            raise SystemExit(
                f"Unexpected V2 flag for {sid}"
            )

        existing = row["human_review_decision"].strip()

        if existing and existing != review["decision"]:
            raise SystemExit(
                f"Conflicting previous decision for {sid}"
            )

        approval = row["approved_for_training"].strip().lower()

        if approval not in {"", "false", "0", "no"}:
            raise SystemExit(
                f"Unexpected training approval for {sid}"
            )

    for sid, review in REVIEWS.items():
        row = index[sid]

        row["human_review_decision"] = review["decision"]
        row["human_review_notes"] = review["notes"]

    missing_notes = [
        row["scenario_id"]
        for row in rows
        if row["human_review_decision"].strip()
        and not row["human_review_notes"].strip()
    ]

    if missing_notes:
        raise SystemExit(
            f"Reviewed rows missing notes: {missing_notes}"
        )

    with WORKING.open(
        "w",
        encoding="utf-8",
        newline=""
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fields
        )

        writer.writeheader()
        writer.writerows(rows)

    reviewed = [
        row for row in rows
        if row["human_review_decision"].strip()
    ]

    remaining = [
        row for row in rows
        if not row["human_review_decision"].strip()
    ]

    print("=" * 65)
    print("M3.5.2 SINGLE-FLAG HUMAN REVIEW")
    print("=" * 65)

    print("\nRecorded decisions:")

    for sid in REVIEWS:
        row = index[sid]

        print(
            sid,
            row["human_review_decision"],
            f"notes={len(row['human_review_notes'])} chars"
        )

    print(
        f"\nReviewed: {len(reviewed)}/{len(rows)}"
    )

    print(
        "Remaining:",
        len(remaining)
    )

    print("\nRemaining by V2 flag:")

    counts = Counter(
        row["flag"]
        for row in remaining
    )

    for flag, count in sorted(counts.items()):
        print(
            f"  {flag}: {count}"
        )

    print(
        "\nReviewed rows missing human_notes:",
        len(missing_notes)
    )

    print("Training approvals: unchanged")
    print("Original V2 results: unchanged")
    print("Working file:", WORKING)


if __name__ == "__main__":
    main()
