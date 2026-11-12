
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from m3_score_v2 import (
    score_record,
    quantity_present,
    salary_word_pairs,
    numbered_sections,
)


ROOT = Path(__file__).resolve().parents[1]

FROZEN = ROOT / "data/m2/frozen"
SUPPLEMENTAL = ROOT / "data/m3/supplemental"

RAW = FROZEN / "pool_raw_0400.jsonl"
EVAL = FROZEN / "heldout_eval_040.jsonl"
FREEZE_MANIFEST = FROZEN / "freeze_manifest.json"

SCENARIOS = SUPPLEMENTAL / "scenarios_0100.jsonl"
GENERATION = SUPPLEMENTAL / "generated_raw.jsonl"
PREPARATION = SUPPLEMENTAL / "preparation_manifest.json"

REPORT = SUPPLEMENTAL / "pilot_v2_validation.csv"
SUMMARY = SUPPLEMENTAL / "pilot_v2_summary.json"

PROMPT_VERSION = "m3_guarded_full_v1"
EXPECTED_PILOT_IDS = {
    f"SUP{i:04d}"
    for i in range(1, 6)
}

REQUIRED_PLACEHOLDERS = [
    "[Date]",
    "[Joining Date]",
    "[Employer Name]",
    "[Employee Name]",
    "[Employer Address]",
    "[Employee Address]",
]


def sha256(path):
    digest = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(
            lambda: file.read(1024 * 1024),
            b""
        ):
            digest.update(chunk)

    return digest.hexdigest()


def read_jsonl(path):
    with path.open(
        "r",
        encoding="utf-8"
    ) as file:
        return [
            json.loads(line)
            for line in file
            if line.strip()
        ]


def normalized(text):
    return " ".join(
        str(text).casefold().split()
    )


def unique_index(rows, label):
    result = {}

    for row in rows:
        sid = row.get("scenario_id")

        if not sid or sid in result:
            raise ValueError(
                f"Missing or duplicate ID in {label}: {sid}"
            )

        result[sid] = row

    return result


def verify_sources():
    for path in [
        RAW,
        EVAL,
        FREEZE_MANIFEST,
        SCENARIOS,
        GENERATION,
        PREPARATION,
    ]:
        if not path.is_file():
            raise FileNotFoundError(
                f"Missing required file: {path}"
            )

    freeze = json.loads(
        FREEZE_MANIFEST.read_text(
            encoding="utf-8"
        )
    )

    preparation = json.loads(
        PREPARATION.read_text(
            encoding="utf-8"
        )
    )

    checks = [
        (
            RAW,
            freeze["raw_sha256"]
        ),
        (
            EVAL,
            freeze["eval_sha256"]
        ),
        (
            SCENARIOS,
            preparation["scenario_sha256"]
        ),
    ]

    for path, expected_hash in checks:
        if sha256(path) != expected_hash:
            raise ValueError(
                f"Checksum mismatch: {path}"
            )

    if preparation["prompt_version"] != PROMPT_VERSION:
        raise ValueError(
            "Unexpected supplemental prompt version."
        )

    raw = read_jsonl(RAW)
    evaluation = read_jsonl(EVAL)
    scenarios = read_jsonl(SCENARIOS)
    generated = read_jsonl(GENERATION)

    if (
        len(raw) != 400
        or len(evaluation) != 40
        or len(scenarios) != 100
    ):
        raise ValueError(
            "Unexpected frozen or scenario record counts."
        )

    scenario_by_id = unique_index(
        scenarios,
        "supplemental scenarios"
    )

    generated_by_id = unique_index(
        generated,
        "generated responses"
    )

    if not EXPECTED_PILOT_IDS.issubset(
        set(generated_by_id)
    ):
        raise ValueError(
            "All five pilot responses must exist."
        )

    if not set(generated_by_id).issubset(
        set(scenario_by_id)
    ):
        raise ValueError(
            "Generated dataset contains unknown IDs."
        )

    previous_prompts = {
        normalized(row.get("instruction", ""))
        for row in raw + evaluation
    }

    for sid, record in generated_by_id.items():
        scenario = scenario_by_id[sid]

        for field in [
            "scenario_id",
            "task_type",
            "instruction",
            "input",
            "expected_facts",
        ]:
            if record.get(field) != scenario.get(field):
                raise ValueError(
                    f"Generated record differs from "
                    f"scenario {sid}: {field}"
                )

        if record.get("generation_model") != preparation[
            "teacher_model"
        ]:
            raise ValueError(
                f"Teacher model mismatch: {sid}"
            )

        if record.get(
            "generation_prompt_version"
        ) != PROMPT_VERSION:
            raise ValueError(
                f"Prompt version mismatch: {sid}"
            )

        if normalized(
            record.get("instruction", "")
        ) in previous_prompts:
            raise ValueError(
                f"Exact train/evaluation prompt overlap: {sid}"
            )

        if record.get("approved_for_training") is True:
            raise ValueError(
                f"Unexpected training approval: {sid}"
            )

    return generated_by_id


def check_pilot_contract(record):
    output = str(
        record.get("output") or ""
    )

    facts = record["expected_facts"]

    issues = []

    if record.get("finish_reason") != "stop":
        issues.append(
            "generation_did_not_finish_normally"
        )

    word_count = len(output.split())

    if word_count < 600:
        issues.append(
            "below_600_word_generation_target"
        )

    sections = numbered_sections(output)

    section_numbers = set(sections)

    expected_sections = set(
        range(1, 17)
    )

    if not expected_sections.issubset(section_numbers):
        missing = sorted(
            expected_sections - section_numbers
        )

        issues.append(
            "missing_numbered_sections_"
            + "_".join(map(str, missing))
        )

    for placeholder in REQUIRED_PLACEHOLDERS:
        if placeholder.casefold() not in output.casefold():
            issues.append(
                "missing_placeholder_"
                + re.sub(
                    r"[^a-z0-9]+",
                    "_",
                    placeholder.casefold()
                ).strip("_")
            )

    role = str(facts["role"])

    if normalized(role) not in normalized(output):
        issues.append(
            "requested_role_missing"
        )

    salary = int(
        facts["salary_inr"]
    )

    currency_amounts = [
        int(value.replace(",", ""))
        for value in re.findall(
            r"(?:INR|₹)\s*([\d,]+)",
            output,
            re.I
        )
    ]

    if salary not in currency_amounts:
        issues.append(
            "requested_salary_missing"
        )

    unexpected_amounts = {
        amount
        for amount in currency_amounts
        if amount != salary
    }

    if unexpected_amounts:
        issues.append(
            "additional_inr_amount_requires_review"
        )

    for numeric, written in salary_word_pairs(output):
        if numeric != written:
            issues.append(
                "numeric_written_salary_mismatch"
            )

    requirements = [
        (
            "scheduled_weekly_hours",
            r"hours?"
        ),
        (
            "probation_months",
            r"months?"
        ),
        (
            "notice_days",
            r"days?"
        ),
    ]

    for field, unit in requirements:
        value = int(
            facts[field]
        )

        if not quantity_present(
            output,
            value,
            unit
        ):
            issues.append(
                f"requested_{field}_not_detected"
            )

    arrangement = str(
        facts["work_arrangement"]
    ).lower()

    if arrangement == "on-site":
        work_pattern = r"\bon[\s-]?site\b"
    else:
        work_pattern = (
            r"\b"
            + re.escape(arrangement)
            + r"\b"
        )

    if not re.search(
        work_pattern,
        output,
        re.I
    ):
        issues.append(
            "work_arrangement_not_detected"
        )

    termination = " ".join(
        body
        for heading, body in sections.values()
        if "terminat" in heading.casefold()
        or "notice" in heading.casefold()
    )

    if not termination:
        issues.append(
            "termination_section_not_detected"
        )

    elif not re.search(
        r"\beither party\b"
        r"|\bboth parties\b"
        r"|\bemployer and (?:the )?employee\b",
        termination,
        re.I
    ):
        issues.append(
            "mutual_termination_language_requires_review"
        )

    return {
        "issues": sorted(set(issues)),
        "word_count": word_count,
        "numbered_sections": len(section_numbers),
        "sections": sections,
    }


def show_relevant_clauses(sections):
    for heading, body in sections.values():
        lower = heading.casefold()

        if any(
            keyword in lower
            for keyword in [
                "probation",
                "terminat",
                "notice",
            ]
        ):
            print(
                "\n",
                heading,
                sep=""
            )

            print(
                body.strip()[:1300]
                or "(no body detected)"
            )


def main():
    generated = verify_sources()

    rows = []

    print("=" * 68)
    print("M3.5.3 — SUPPLEMENTAL PILOT V2 VALIDATION")
    print("=" * 68)

    for sid in sorted(EXPECTED_PILOT_IDS):
        record = generated[sid]

        v2 = score_record(
            record,
            repeated_output=False
        )

        pilot = check_pilot_contract(
            record
        )

        v2_reasons = [
            value
            for field in [
                "hard_failure_reasons_v2",
                "review_reasons_v2",
                "legal_review_reasons_v2",
            ]
            for value in v2[field].split(";")
            if value
        ]

        issues = pilot["issues"]

        if (
            v2["screening_tier_v2"]
            == "strong_screening_candidate"
            and not issues
        ):
            status = (
                "PROVISIONAL_STRONG_AWAITING_REVIEW"
            )

        else:
            status = (
                "HOLD_FOR_MANUAL_REVIEW"
            )

        row = {
            "scenario_id": sid,
            "task_type": record["task_type"],
            "generation_prompt_version": PROMPT_VERSION,
            "word_count": pilot["word_count"],
            "numbered_sections": pilot["numbered_sections"],
            "finish_reason": record.get(
                "finish_reason", ""
            ),
            "v2_score": v2[
                "quality_score_heuristic_v2"
            ],
            "v2_tier": v2[
                "screening_tier_v2"
            ],
            "v2_reasons": ";".join(
                v2_reasons
            ),
            "additional_pilot_checks": ";".join(
                issues
            ),
            "pilot_status": status,
            "human_decision": "",
            "human_notes": "",
            "approved_for_training": "false",
        }

        rows.append(row)

        print("\n" + "=" * 68)
        print("SCENARIO:", sid)
        print("=" * 68)

        print(
            "Words:",
            pilot["word_count"]
        )

        print(
            "Numbered sections:",
            pilot["numbered_sections"]
        )

        print(
            "V2 tier:",
            row["v2_tier"]
        )

        print(
            "V2 score:",
            row["v2_score"]
        )

        print(
            "V2 reasons:",
            v2_reasons or "None"
        )

        print(
            "Additional check flags:",
            issues or "None"
        )

        print(
            "Pilot status:",
            status
        )

        print("\nPROBATION AND TERMINATION CLAUSES:")

        show_relevant_clauses(
            pilot["sections"]
        )

    REPORT.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with REPORT.open(
        "w",
        encoding="utf-8",
        newline=""
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(rows[0])
        )

        writer.writeheader()
        writer.writerows(rows)

    counts = Counter(
        row["pilot_status"]
        for row in rows
    )

    summary = {
        "pilot_count": len(rows),
        "generation_prompt_version": PROMPT_VERSION,
        "status_counts": dict(counts),
        "provisional_strong_ids": [
            row["scenario_id"]
            for row in rows
            if row["pilot_status"]
            == "PROVISIONAL_STRONG_AWAITING_REVIEW"
        ],
        "manual_review_ids": [
            row["scenario_id"]
            for row in rows
            if row["pilot_status"]
            == "HOLD_FOR_MANUAL_REVIEW"
        ],
        "training_approved": False,
        "source_sha256": sha256(
            GENERATION
        ),
        "note": (
            "Automated checks are preliminary. "
            "Neither V2 screening nor this pilot "
            "establishes legal correctness or "
            "training eligibility."
        ),
    }

    SUMMARY.write_text(
        json.dumps(
            summary,
            indent=2,
            ensure_ascii=False
        ) + "\n",
        encoding="utf-8"
    )

    print("\n" + "=" * 68)
    print("PILOT SUMMARY")
    print("=" * 68)

    print(
        "Generated pilot:",
        len(rows)
    )

    print(
        "Provisional strong:",
        len(summary["provisional_strong_ids"])
    )

    print(
        "Manual review required:",
        len(summary["manual_review_ids"])
    )

    print(
        "Provisional strong IDs:",
        summary["provisional_strong_ids"]
    )

    print(
        "Manual review IDs:",
        summary["manual_review_ids"]
    )

    print("\nReport:", REPORT)
    print("Summary:", SUMMARY)

    print("\nOriginal 400: unchanged")
    print("Held-out 40: unchanged")
    print("Training approvals: 0")
    print("API calls: 0")


if __name__ == "__main__":
    main()
