
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


BASE = Path("data")
REVIEW_DIR = BASE / "m3/provisional_cohorts"
OUTPUT_DIR = BASE / "m3/calibration_analysis"

ORIGINAL_REVIEW = REVIEW_DIR / "M3_CALIBRATION_REVIEW.csv"
HUMAN_REVIEW = REVIEW_DIR / "M3_CALIBRATION_HUMAN_REVIEW.csv"
CURATED_COHORT = REVIEW_DIR / "M3_CURATED_150_CANDIDATES.csv"

DOMAIN_SCORES = (
    BASE / "m3/domain_curation/M3_DOMAIN_SCORES.csv"
)

FROZEN_RAW = BASE / "m2/frozen/pool_raw_0400.jsonl"
FROZEN_EVAL = BASE / "m2/frozen/heldout_eval_040.jsonl"
FREEZE_MANIFEST = BASE / "m2/frozen/freeze_manifest.json"

EXPECTED_RAW_SHA256 = (
    "ec94fba3a90b3cd9853b42ac9365154aa54f5973e183f2e06ca2895b127b466b"
)

DECISIONS = [
    "accept_screening",
    "false_positive",
    "false_negative",
    "needs_legal_expert",
]

TIERS = [
    "strong_screening_candidate",
    "hold_manual_review",
    "exclude_provisional",
]


def read_csv(path):
    with path.open(
        "r",
        encoding="utf-8",
        newline=""
    ) as file:
        return list(csv.DictReader(file))


def sha256(path):
    digest = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def create_index(rows, expected_count, label):
    result = {}

    for row in rows:
        sid = row.get("scenario_id", "").strip()

        if not sid:
            raise ValueError(
                f"{label} contains a missing scenario ID."
            )

        if sid in result:
            raise ValueError(
                f"{label} contains duplicate ID: {sid}"
            )

        result[sid] = row

    if len(result) != expected_count:
        raise ValueError(
            f"{label}: expected {expected_count} records, "
            f"found {len(result)}."
        )

    return result


def validate_inputs():
    required_files = [
        ORIGINAL_REVIEW,
        HUMAN_REVIEW,
        CURATED_COHORT,
        DOMAIN_SCORES,
        FROZEN_RAW,
        FROZEN_EVAL,
        FREEZE_MANIFEST,
    ]

    for path in required_files:
        if not path.is_file():
            raise FileNotFoundError(
                f"Required file missing: {path}"
            )

    raw_hash = sha256(FROZEN_RAW)
    eval_hash = sha256(FROZEN_EVAL)

    if raw_hash != EXPECTED_RAW_SHA256:
        raise ValueError(
            "Frozen raw dataset hash mismatch. "
            "The original 400-example dataset may have changed."
        )

    with FREEZE_MANIFEST.open(
        "r",
        encoding="utf-8"
    ) as file:
        manifest = json.load(file)

    for key, actual_hash in [
        ("raw_sha256", raw_hash),
        ("eval_sha256", eval_hash),
    ]:
        expected_hash = manifest.get(key)

        if expected_hash and expected_hash != actual_hash:
            raise ValueError(
                f"Freeze manifest verification failed: {key}"
            )

    return raw_hash, eval_hash


def validate_human_reviews(original, reviewed, scores):
    if set(original) != set(reviewed):
        raise ValueError(
            "Original and reviewed calibration IDs differ."
        )

    protected_fields = [
        "scenario_id",
        "review_purpose",
        "task_type",
        "screening_tier",
        "quality_score_heuristic",
        "hard_failure_reasons",
        "review_reasons",
        "instruction",
        "input",
        "output",
        "approved_for_training",
    ]

    for sid, row in reviewed.items():
        previous = original[sid]

        for field in protected_fields:
            if row.get(field, "") != previous.get(field, ""):
                raise ValueError(
                    f"Protected field changed for {sid}: {field}"
                )

        decision = row.get("human_decision", "").strip()
        notes = row.get("human_notes", "").strip()

        if decision not in DECISIONS:
            raise ValueError(
                f"Missing or invalid decision for {sid}: {decision}"
            )

        if not notes:
            raise ValueError(
                f"Missing human_notes for {sid}"
            )

        approved = (
            row.get("approved_for_training", "")
            .strip()
            .lower()
        )

        if approved not in {"", "false", "0", "no"}:
            raise ValueError(
                f"Unexpected training approval for {sid}"
            )

        if sid not in scores:
            raise ValueError(
                f"Missing original score for {sid}"
            )

        if (
            row["screening_tier"]
            != scores[sid]["screening_tier"]
        ):
            raise ValueError(
                f"Screening tier mismatch for {sid}"
            )


def analyze_cohort(curated_rows, reviewed, scores):
    flags = []

    for row in curated_rows:
        sid = row["scenario_id"]

        if sid not in scores:
            raise ValueError(
                f"Unknown curated candidate: {sid}"
            )

        if sid in reviewed:
            decision = reviewed[sid]["human_decision"]
        else:
            decision = "not_sampled"

        if decision == "false_negative":
            status = "BLOCK_REVIEWED_QUALITY_DEFECT"

        elif decision == "needs_legal_expert":
            status = "BLOCK_PENDING_LEGAL_REVIEW"

        else:
            status = "PROVISIONAL_NOT_APPROVED"

        flags.append({
            "scenario_id": sid,
            "task_type": row["task_type"],
            "human_decision": decision,
            "status": status,
            "approved_for_training": "false",
        })

    return flags


def save_csv(path, rows):
    if not rows:
        raise ValueError("Cannot save an empty CSV.")

    with path.open(
        "w",
        encoding="utf-8",
        newline=""
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(rows[0].keys())
        )

        writer.writeheader()
        writer.writerows(rows)


def build_report(summary, blocked):
    counts = summary["decision_counts"]
    matrix = summary["tier_by_decision"]

    lines = [
        "# M3.4 Human Calibration Report",
        "",
        "## Calibration Status",
        "",
        "**Human calibration completed: 27/27 examples.**",
        "",
        "- All 27 decisions are recorded.",
        "- Every reviewed example has human_notes.",
        "- Training-approved examples: 0.",
        "- Frozen datasets remain unchanged.",
        "",
        "## Human Review Results",
        "",
        "| Human decision | Count |",
        "|---|---:|",
    ]

    for decision in DECISIONS:
        lines.append(
            f"| `{decision}` | {counts.get(decision, 0)} |"
        )

    lines.extend([
        "",
        "## Automated Tier vs Human Decision",
        "",
        "| Automated tier | Accept | False positive | "
        "False negative | Needs legal expert |",
        "|---|---:|---:|---:|---:|",
    ])

    for tier in TIERS:
        values = [
            str(matrix[tier][decision])
            for decision in DECISIONS
        ]

        lines.append(
            f"| `{tier}` | "
            + " | ".join(values)
            + " |"
        )

    lines.extend([
        "",
        "## Provisional Curated Cohort",
        "",
        (
            "- Original curated candidates: "
            f"{summary['curated_candidates']}"
        ),
        (
            "- Human-reviewed candidates in the cohort: "
            f"{summary['reviewed_candidates_in_curated_cohort']}"
        ),
        (
            "- Candidates requiring blocking review: "
            f"{len(blocked)}"
        ),
        "",
        "| Scenario ID | Task | Human decision |",
        "|---|---|---|",
    ])

    for row in blocked:
        lines.append(
            f"| {row['scenario_id']} | "
            f"{row['task_type']} | "
            f"`{row['human_decision']}` |"
        )

    lines.extend([
        "",
        "## Engineering Findings",
        "",
        "1. Literal contradiction checks incorrectly flag "
        "superseded roles, salary amounts and working hours.",
        "2. Identical outputs for different short editing tasks "
        "are not necessarily defective training examples.",
        "3. Numeric and written salary representations "
        "require consistency validation.",
        "4. Explicit placeholders and internal clause "
        "cross-references require dedicated checks.",
        "5. Unsupported probation extensions, termination "
        "conditions and customization changes should be flagged.",
        "6. Legal-reference currentness must be reviewed "
        "separately from structural and instruction quality.",
        "",
        "## Methodological Limitations",
        "",
        "The 27 calibration examples were deliberately selected "
        "to investigate screening behavior.",
        "",
        "They do not constitute a random sample of the "
        "400-example dataset.",
        "",
        "Therefore, the observed decision percentages "
        "must not be interpreted as dataset-wide "
        "false-positive or false-negative rates.",
        "",
        "Human calibration does not establish legal "
        "correctness or automatically approve training data.",
        "",
        "## Next Steps",
        "",
        "1. Implement a versioned M3 scoring system.",
        "2. Fix confirmed false-positive and false-negative rules.",
        "3. Re-score all 400 frozen synthetic examples.",
        "4. Compare original and revised screening decisions.",
        "5. Review affected curated candidates.",
        "6. Rebuild task-matched provisional training cohorts.",
        "7. Finalize eligibility before AlignTune fine-tuning.",
        "",
        "## Dataset Provenance",
        "",
        (
            f"- Frozen raw SHA256: "
            f"`{summary['frozen_raw_sha256']}`"
        ),
        (
            f"- Frozen evaluation SHA256: "
            f"`{summary['frozen_eval_sha256']}`"
        ),
        (
            f"- Original scores SHA256: "
            f"`{summary['original_scores_sha256']}`"
        ),
        (
            f"- Human review SHA256: "
            f"`{summary['human_review_sha256']}`"
        ),
        "",
    ])

    return "\n".join(lines)


def main():
    raw_hash, eval_hash = validate_inputs()

    original_rows = read_csv(ORIGINAL_REVIEW)
    reviewed_rows = read_csv(HUMAN_REVIEW)
    score_rows = read_csv(DOMAIN_SCORES)
    curated_rows = read_csv(CURATED_COHORT)

    original = create_index(
        original_rows, 27, "Original calibration"
    )

    reviewed = create_index(
        reviewed_rows, 27, "Human calibration"
    )

    scores = create_index(
        score_rows, 400, "Original scoring"
    )

    create_index(
        curated_rows, 150, "Provisional curated cohort"
    )

    validate_human_reviews(
        original, reviewed, scores
    )

    counts = Counter(
        row["human_decision"]
        for row in reviewed_rows
    )

    matrix = {
        tier: {
            decision: sum(
                row["screening_tier"] == tier
                and row["human_decision"] == decision
                for row in reviewed_rows
            )
            for decision in DECISIONS
        }
        for tier in TIERS
    }

    flags = analyze_cohort(
        curated_rows, reviewed, scores
    )

    blocked = [
        row for row in flags
        if row["status"].startswith("BLOCK")
    ]

    reviewed_in_cohort = sum(
        row["human_decision"] != "not_sampled"
        for row in flags
    )

    summary = {
        "status": (
            "CALIBRATION_COMPLETE_TRAINING_NOT_APPROVED"
        ),
        "reviewed": 27,
        "decision_counts": dict(counts),
        "tier_by_decision": matrix,
        "frozen_raw_sha256": raw_hash,
        "frozen_eval_sha256": eval_hash,
        "original_scores_sha256": sha256(
            DOMAIN_SCORES
        ),
        "human_review_sha256": sha256(
            HUMAN_REVIEW
        ),
        "curated_candidates": 150,
        "reviewed_candidates_in_curated_cohort": (
            reviewed_in_cohort
        ),
        "flagged_curated_candidates": len(blocked),
        "flagged_ids": [
            row["scenario_id"]
            for row in blocked
        ],
        "training_approved": False,
    }

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    summary_path = (
        OUTPUT_DIR / "M3_CALIBRATION_SUMMARY.json"
    )

    report_path = (
        OUTPUT_DIR / "M3_CALIBRATION_REPORT.md"
    )

    flags_path = (
        OUTPUT_DIR
        / "M3_CURATED_CANDIDATE_REVIEW_FLAGS.csv"
    )

    save_csv(flags_path, flags)

    summary_path.write_text(
        json.dumps(
            summary,
            indent=2,
            ensure_ascii=False
        ) + "\n",
        encoding="utf-8"
    )

    report_path.write_text(
        build_report(summary, blocked),
        encoding="utf-8"
    )

    print("=" * 65)
    print("M3.4 HUMAN CALIBRATION AUDIT")
    print("=" * 65)

    print("Reviewed:", len(reviewed_rows), "/ 27")

    print(
        "Reviewed rows missing human_notes:",
        sum(
            not row["human_notes"].strip()
            for row in reviewed_rows
        )
    )

    print("\nDecision counts:")
    for decision in DECISIONS:
        print(
            f"  {decision}: "
            f"{counts.get(decision, 0)}"
        )

    print("\nTier-by-decision:")
    for tier, values in matrix.items():
        print(f"  {tier}: {values}")

    print(
        "\nReviewed examples in curated cohort:",
        reviewed_in_cohort
    )

    print(
        "Flagged curated candidates:",
        len(blocked)
    )

    print(
        "Flagged IDs:",
        summary["flagged_ids"]
    )

    print("\nGenerated files:")
    print("  Report:", report_path)
    print("  Summary:", summary_path)
    print("  Candidate flags:", flags_path)

    print("\nFrozen datasets: unchanged")
    print("Training approvals: 0")
    print("M3.5 CALIBRATION ANALYSIS COMPLETE")


if __name__ == "__main__":
    main()
