
from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path("data")

RAW = ROOT / "m2/frozen/pool_raw_0400.jsonl"
EVAL = ROOT / "m2/frozen/heldout_eval_040.jsonl"
FREEZE = ROOT / "m2/frozen/freeze_manifest.json"

V1 = ROOT / "m3/domain_curation/M3_DOMAIN_SCORES.csv"

CALIBRATION = (
    ROOT
    / "m3/provisional_cohorts/M3_CALIBRATION_HUMAN_REVIEW.csv"
)

COHORT = (
    ROOT
    / "m3/provisional_cohorts/M3_CURATED_150_CANDIDATES.csv"
)

OUT = ROOT / "m3/domain_curation_v2"

EXPECTED = {
    "full_agreement": 120,
    "clause_drafting": 100,
    "contract_customization": 80,
    "contradiction_correction": 60,
    "missing_clause_completion": 40,
}

QUOTAS = {
    "full_agreement": 45,
    "clause_drafting": 38,
    "contract_customization": 30,
    "contradiction_correction": 22,
    "missing_clause_completion": 15,
}

NUMBER_WORDS = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
}

SCALES = {
    "thousand": 1000,
    "lakh": 100000,
    "lac": 100000,
    "million": 1000000,
    "crore": 10000000,
    "billion": 1000000000,
}

SKIP_WORDS = {
    "indian",
    "rupees",
    "rupee",
    "only",
    "and",
    "inr",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path) -> list[dict]:
    with path.open(
        "r",
        encoding="utf-8",
        newline=""
    ) as file:
        return list(csv.DictReader(file))


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as file:
        return [
            json.loads(line)
            for line in file
            if line.strip()
        ]


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise ValueError(
            f"Cannot write empty CSV: {path}"
        )

    with path.open(
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


def normalize(value: str) -> str:
    return re.sub(
        r"\s+",
        " ",
        str(value)
    ).strip().casefold()


def extract_numbers(text: str) -> list[int]:
    matches = re.findall(
        r"(?<!\w)\d[\d,]*(?!\w)",
        text
    )

    return [
        int(value.replace(",", ""))
        for value in matches
    ]


def words_to_amount(text: str) -> int | None:
    tokens = re.findall(
        r"[a-z]+",
        text.lower().replace("-", " ")
    )

    total = 0
    current = 0
    found = False

    for token in tokens:
        if token in SKIP_WORDS:
            continue

        if token in NUMBER_WORDS:
            current += NUMBER_WORDS[token]
            found = True

        elif token == "hundred":
            current = max(1, current) * 100
            found = True

        elif token in SCALES:
            total += max(1, current) * SCALES[token]
            current = 0
            found = True

        else:
            return None

    return total + current if found else None


def salary_word_pairs(text: str) -> list[tuple[int, int]]:
    pattern = (
        r"(?:INR|₹)\s*([\d,]+)\s*"
        r"\(([^)\n]{6,105})\)"
    )

    pairs = []

    for match in re.finditer(pattern, text, re.I):
        numeric = int(
            match.group(1).replace(",", "")
        )

        written = words_to_amount(
            match.group(2)
        )

        if written is not None:
            pairs.append(
                (numeric, written)
            )

    return pairs


def numbered_sections(text: str) -> dict:
    pattern = re.compile(
        r"(?m)^\s*"
        r"(?:#{1,6}\s*)?"
        r"(?:\*\*|__)?"
        r"\s*(\d{1,2})\s*[.)]"
        r"\s*(?:\*\*|__)?"
        r"\s*([^\n*]{2,95})"
    )

    matches = list(
        pattern.finditer(text)
    )

    sections = {}

    for index, match in enumerate(matches):
        end = (
            matches[index + 1].start()
            if index + 1 < len(matches)
            else len(text)
        )

        number = int(
            match.group(1)
        )

        title = (
            match.group(2)
            .strip()
            .strip("*_: ")
        )

        body = text[
            match.end():end
        ]

        sections[number] = (
            title,
            body
        )

    return sections


def corrective_context(
    text: str,
    wrong_value: str
) -> bool:
    occurrences = list(
        re.finditer(
            re.escape(wrong_value),
            text,
            re.I
        )
    )

    if not occurrences:
        return False

    correction_words = (
        r"\b("
        r"reference|referred|incorrect|mistak|"
        r"error|instead|replace|replaced|"
        r"replacing|correct|corrected|"
        r"correction|deemed"
        r")\b"
    )

    for match in occurrences:
        start = max(
            0,
            match.start() - 80
        )

        end = min(
            len(text),
            match.end() + 100
        )

        context = text[start:end]

        if not re.search(
            correction_words,
            context,
            re.I
        ):
            return False

    return True


def expected_facts(record: dict) -> dict:
    facts = dict(
        record.get("expected_facts") or {}
    )

    instruction = record.get(
        "instruction",
        ""
    )

    patterns = {
        "salary_inr": (
            r"INR\s*([\d,]+)\s+"
            r"(?:fixed annual salary|annual fixed salary)"
        ),
        "scheduled_weekly_hours": (
            r"(\d+)\s+scheduled hours per week"
        ),
        "probation_months": (
            r"(\d+)\s+months? of probation"
        ),
        "notice_days": (
            r"(\d+)\s+days? of mutual notice"
        ),
    }

    for field, pattern in patterns.items():
        if facts.get(field) is not None:
            continue

        match = re.search(
            pattern,
            instruction,
            re.I
        )

        if match:
            facts[field] = int(
                match.group(1).replace(",", "")
            )

    if not facts.get("role"):
        match = re.search(
            r"For a fictional (.+?) employed in",
            instruction,
            re.I
        )

        if match:
            facts["role"] = match.group(1).strip()

    return facts


def quantity_present(
    text: str,
    number: int,
    unit: str
) -> bool:
    pattern = (
        r"(?<!\d)"
        + re.escape(str(number))
        + r"(?!\d)"
    )

    for match in re.finditer(pattern, text):
        start = max(
            0,
            match.start() - 20
        )

        end = min(
            len(text),
            match.end() + 38
        )

        context = text[start:end]

        if re.search(
            unit,
            context,
            re.I
        ):
            return True

    return False


def check_full_agreement(
    record: dict,
    hard: set,
    review: set
) -> None:
    answer = record.get("output", "")
    instruction = record.get("instruction", "")

    facts = expected_facts(record)

    sections = numbered_sections(answer)

    if len(answer.split()) < 350:
        hard.add(
            "incomplete_full_agreement"
        )

    if len(sections) < 8:
        review.add(
            "insufficient_detectable_numbered_sections"
        )

    if not re.search(
        r"signature|signatory|in witness whereof",
        answer,
        re.I
    ):
        review.add(
            "execution_block_check"
        )

    role = facts.get("role")

    if role and normalize(role) not in normalize(answer):
        review.add(
            "required_role_missing"
        )

    salary = facts.get("salary_inr")

    if salary is not None:
        visible = re.sub(
            r"[\s,₹]",
            "",
            answer
        ).casefold()

        salary_pattern = (
            r"(?<!\d)"
            + str(int(salary))
            + r"(?!\d)"
        )

        if not re.search(
            salary_pattern,
            visible
        ):
            review.add(
                "required_salary_missing"
            )

    quantity_fields = [
        ("probation_months", r"month"),
        ("scheduled_weekly_hours", r"hour"),
        ("notice_days", r"day"),
    ]

    for field, unit in quantity_fields:
        value = facts.get(field)

        if value is None:
            continue

        if not quantity_present(
            answer,
            int(value),
            unit
        ):
            review.add(
                f"required_{field}_missing"
            )

    for numeric, written in salary_word_pairs(answer):
        if numeric != written:
            hard.add(
                "numeric_written_salary_disagree"
            )

    for section_number, (
        heading,
        body
    ) in sections.items():

        references = re.finditer(
            r"\b(?:clause|section)\s+(\d{1,2})\b",
            body,
            re.I
        )

        for reference in references:
            target = int(
                reference.group(1)
            )

            if target not in sections:
                hard.add(
                    "cross_reference_target_missing"
                )
                continue

            context = body[
                max(0, reference.start() - 95):
                reference.end() + 30
            ]

            target_heading = sections[target][0]

            mentions_notice = re.search(
                r"terminat|notice",
                context + " " + heading,
                re.I
            )

            target_is_notice = re.search(
                r"terminat|notice",
                target_heading,
                re.I
            )

            if mentions_notice and not target_is_notice:
                hard.add(
                    "notice_cross_reference_points_to_other_section"
                )

    if re.search(
        r"\band the\s+"
        r"(?!Employee\b)"
        r"[A-Z][a-z]+\s+"
        r"agrees to accept appointment",
        answer
    ):
        review.add(
            "nonparty_accepts_appointment_possible_text_corruption"
        )

    extension_detected = bool(
        re.search(
            r"\bextend\b.{0,65}\bprobation",
            answer,
            re.I
        )
        or re.search(
            r"probation.{0,80}\bextend",
            answer,
            re.I
        )
    )

    if extension_detected:
        if not re.search(
            r"extend|extension",
            instruction,
            re.I
        ):
            review.add(
                "unrequested_probation_extension"
            )

    probation_body = " ".join(
        body
        for heading, body in sections.values()
        if "probation" in heading.lower()
    )

    notice = facts.get("notice_days")

    if (
        notice is not None
        and probation_body
        and re.search(
            r"\bnotice\b",
            probation_body,
            re.I
        )
    ):
        matches = re.findall(
            r"\((\d+)\)\s*days?\b"
            r"|(?<!\d)(\d+)\s*days?\b",
            probation_body,
            re.I
        )

        durations = [
            int(value)
            for pair in matches
            for value in pair
            if value
        ]

        if any(
            value != int(notice)
            for value in durations
        ):
            review.add(
                "probation_notice_exception_requires_review"
            )

    termination_body = " ".join(
        body
        for heading, body in sections.values()
        if "terminat" in heading.lower()
    )

    if re.search(
        r"\bemployer\b.{0,85}"
        r"\b(?:pay|payment|salary)\b"
        r".{0,35}\bin lieu",
        termination_body,
        re.I
    ):
        review.add(
            "employer_only_notice_pay_option_review"
        )


def check_contradiction_correction(
    record: dict,
    hard: set,
    review: set
) -> None:
    answer = record.get("output", "")
    instruction = record.get("instruction", "")
    supplied = record.get("input", "")

    target_role = re.search(
        r"make the role consistently\s+(.+?)\.",
        instruction,
        re.I
    )

    incorrect_role = re.search(
        r"mistakenly describes the role as\s+(.+?)\.",
        supplied,
        re.I
    )

    if target_role and incorrect_role:
        target = target_role.group(1).strip()
        wrong = incorrect_role.group(1).strip()

        if normalize(target) not in normalize(answer):
            hard.add(
                "correct_role_missing"
            )

        if re.search(
            re.escape(wrong),
            answer,
            re.I
        ):
            if corrective_context(
                answer,
                wrong
            ):
                review.add(
                    "amendment_style_role_replacement"
                )
            else:
                hard.add(
                    "incorrect_role_still_operative"
                )

    else:
        target_match = re.search(
            r"use\s+"
            r"(?:INR\s*)?"
            r"([\d,]+)\s*"
            r"(?:scheduled\s+)?"
            r"(months?|hours?)?"
            r"\s+consistently",
            instruction,
            re.I
        )

        source_values = set(
            extract_numbers(supplied)
        )

        if target_match:
            target = int(
                target_match.group(1).replace(",", "")
            )

            output_values = set(
                extract_numbers(answer)
            )

            if target not in output_values:
                hard.add(
                    "required_corrected_value_missing"
                )

            wrong_values = [
                value
                for value in source_values
                if value != target
            ]

            for wrong in wrong_values:
                if wrong not in output_values:
                    continue

                wrong_pattern = (
                    r"(?<!\d)"
                    + str(wrong)
                    + r"(?!\d)"
                )

                occurrences = list(
                    re.finditer(
                        wrong_pattern,
                        answer
                    )
                )

                all_corrective = all(
                    corrective_context(
                        answer,
                        match.group()
                    )
                    for match in occurrences
                )

                if all_corrective:
                    review.add(
                        "amendment_style_numeric_replacement"
                    )
                else:
                    hard.add(
                        "incorrect_numeric_value_still_operative"
                    )

    if re.search(
        r"\bmonthly installments\b",
        answer,
        re.I
    ) and not re.search(
        r"month|installment",
        supplied,
        re.I
    ):
        review.add(
            "unrequested_payment_schedule_added"
        )

    if len(answer.split()) > 85:
        review.add(
            "overlong_correction"
        )


def check_customization(
    record: dict,
    hard: set,
    review: set
) -> None:
    answer = record.get("output", "")
    instruction = record.get("instruction", "")
    supplied = record.get("input", "")

    if re.search(
        r"work arrangement to hybrid",
        instruction,
        re.I
    ):
        if not re.search(
            r"\bhybrid\b",
            answer,
            re.I
        ):
            hard.add(
                "requested_hybrid_change_missing"
            )

        extra_conditions = (
            r"approved remote location"
            r"|hybrid work policy"
        )

        if re.search(
            extra_conditions,
            answer,
            re.I
        ) and not re.search(
            extra_conditions,
            instruction + " " + supplied,
            re.I
        ):
            review.add(
                "unrequested_hybrid_conditions_added"
            )

    else:
        target_salary = re.search(
            r"(?:salary to|salary of)"
            r"\s+INR\s*([\d,]+)",
            instruction,
            re.I
        )

        target_notice = re.search(
            r"notice period to\s+"
            r"(\d+)\s+days?",
            instruction,
            re.I
        )

        target_match = (
            target_salary
            or target_notice
        )

        if target_match:
            target = int(
                target_match.group(1).replace(",", "")
            )

            if target not in extract_numbers(answer):
                hard.add(
                    "requested_customization_value_missing"
                )

    if len(answer.split()) > 120:
        review.add(
            "possibly_overlong_customization"
        )


def check_missing_clause(
    record: dict,
    hard: set,
    review: set
) -> None:
    answer = record.get("output", "")
    instruction = record.get("instruction", "")
    supplied = record.get("input", "")

    if re.search(
        r"joining[- ]date placeholders?",
        instruction,
        re.I
    ):
        placeholder_pattern = (
            r"\[[^\]]*"
            r"\b(?:joining|start|effective)\s*date\b"
            r"[^\]]*\]"
            r"|_{3,}"
        )

        if not re.search(
            placeholder_pattern,
            answer,
            re.I
        ):
            review.add(
                "required_joining_date_placeholder_missing"
            )

    if re.search(
        r"probation provision",
        instruction,
        re.I
    ):
        extension_detected = bool(
            re.search(
                r"\bextend\b.{0,70}\bprobation",
                answer,
                re.I
            )
            or re.search(
                r"probation.{0,95}\bextend",
                answer,
                re.I
            )
        )

        if extension_detected and not re.search(
            r"extend|extension",
            supplied + " " + instruction,
            re.I
        ):
            review.add(
                "unrequested_probation_extension"
            )

        if re.search(
            r"without assigning (?:any )?reason",
            answer,
            re.I
        ):
            review.add(
                "unrequested_probation_termination_discretion"
            )

    if re.search(
        r"mutual notice provision",
        instruction,
        re.I
    ):
        match = re.search(
            r"using\s+(\d+)\s+days",
            instruction,
            re.I
        )

        if match and not quantity_present(
            answer,
            int(match.group(1)),
            r"day"
        ):
            hard.add(
                "requested_notice_duration_missing"
            )

    if len(answer.split()) < 15:
        review.add(
            "very_short_missing_clause"
        )


def check_clause_drafting(
    record: dict,
    review: set
) -> None:
    answer = record.get("output", "")
    instruction = record.get("instruction", "")

    annual_leave = re.search(
        r"annual leave clause with\s+"
        r"(\d+)\s+days",
        instruction,
        re.I
    )

    if annual_leave:
        if re.search(
            r"\bcalendar days\b",
            answer,
            re.I
        ) and not re.search(
            r"\bcalendar days\b",
            instruction,
            re.I
        ):
            review.add(
                "leave_calendar_day_basis_requires_review"
            )

    if len(answer.split()) < 15:
        review.add(
            "very_short_clause"
        )


def score_record(
    record: dict,
    repeated_output: bool
) -> dict:
    sid = record["scenario_id"]
    task = record["task_type"]

    answer = str(
        record.get("output") or ""
    )

    hard = set()
    review = set()
    legal = set()

    if not answer.strip():
        hard.add(
            "empty_response"
        )

    if record.get("finish_reason") == "length":
        hard.add(
            "truncated_generation"
        )

    if re.search(
        r"\b(?:as an ai|i cannot draft)\b",
        answer,
        re.I
    ):
        hard.add(
            "refusal_or_meta_response"
        )

    if re.search(
        r"\bindustrial disputes act\s*,?\s*1947\b",
        answer,
        re.I
    ):
        legal.add(
            "historical_industrial_disputes_act_reference"
        )

    if re.search(
        r"\bcompanies act\s*,?\s*2006\b",
        answer,
        re.I
    ):
        legal.add(
            "possible_nonindian_statute_reference"
        )

    if re.search(
        r"\bnon[ -]?compete\b"
        r"|\brestraint of trade\b",
        answer,
        re.I
    ):
        legal.add(
            "post_employment_restriction_review"
        )

    if task == "full_agreement":
        check_full_agreement(
            record,
            hard,
            review
        )

    elif task == "contradiction_correction":
        check_contradiction_correction(
            record,
            hard,
            review
        )

    elif task == "contract_customization":
        check_customization(
            record,
            hard,
            review
        )

    elif task == "missing_clause_completion":
        check_missing_clause(
            record,
            hard,
            review
        )

    elif task == "clause_drafting":
        check_clause_drafting(
            record,
            review
        )

    else:
        hard.add(
            "unknown_task_type"
        )

    if hard:
        tier = "exclude_provisional"
    elif review or legal:
        tier = "hold_manual_review"
    else:
        tier = "strong_screening_candidate"

    score = max(
        0,
        100
        - 25 * len(hard)
        - 9 * len(review)
        - 18 * len(legal)
    )

    return {
        "scenario_id": sid,
        "task_type": task,
        "quality_score_heuristic_v2": score,
        "screening_tier_v2": tier,
        "hard_failure_reasons_v2": ";".join(
            sorted(hard)
        ),
        "review_reasons_v2": ";".join(
            sorted(review)
        ),
        "legal_review_reasons_v2": ";".join(
            sorted(legal)
        ),
        "duplicate_output_diversity_flag": str(
            repeated_output
        ).lower(),
        "approved_for_training": "false",
    }


def main():
    required = [
        RAW,
        EVAL,
        FREEZE,
        V1,
        CALIBRATION,
        COHORT,
    ]

    for path in required:
        if not path.is_file():
            raise SystemExit(
                f"Missing required file: {path}"
            )

    freeze = json.loads(
        FREEZE.read_text(encoding="utf-8")
    )

    if freeze.get("raw_sha256") != digest(RAW):
        raise SystemExit(
            "Frozen raw dataset checksum mismatch."
        )

    if freeze.get("eval_sha256") != digest(EVAL):
        raise SystemExit(
            "Frozen evaluation checksum mismatch."
        )

    raw_records = read_jsonl(RAW)

    expected_ids = {
        f"GEN{i:04d}"
        for i in range(1, 401)
    }

    raw_by_id = {
        row["scenario_id"]: row
        for row in raw_records
    }

    if (
        len(raw_records) != 400
        or set(raw_by_id) != expected_ids
    ):
        raise SystemExit(
            "Expected 400 unique frozen GEN IDs."
        )

    task_counts = Counter(
        row["task_type"]
        for row in raw_records
    )

    if task_counts != Counter(EXPECTED):
        raise SystemExit(
            f"Unexpected task distribution: {task_counts}"
        )

    original_rows = read_csv(V1)

    old_by_id = {
        row["scenario_id"]: row
        for row in original_rows
    }

    if (
        len(original_rows) != 400
        or set(old_by_id) != expected_ids
    ):
        raise SystemExit(
            "Original M3 scoring is incomplete."
        )

    review_rows = read_csv(CALIBRATION)

    reviewed = {
        row["scenario_id"]: row
        for row in review_rows
    }

    if (
        len(review_rows) != 27
        or len(reviewed) != 27
    ):
        raise SystemExit(
            "Expected 27 unique human calibration rows."
        )

    for row in review_rows:
        if (
            not row["human_decision"].strip()
            or not row["human_notes"].strip()
        ):
            raise SystemExit(
                "Incomplete human calibration."
            )

    cohort_rows = read_csv(COHORT)

    cohort_ids = {
        row["scenario_id"]
        for row in cohort_rows
    }

    if (
        len(cohort_rows) != 150
        or len(cohort_ids) != 150
    ):
        raise SystemExit(
            "Expected 150 original curated candidates."
        )

    output_groups = defaultdict(list)

    for record in raw_records:
        key = normalize(
            record.get("output", "")
        )

        output_groups[key].append(
            record["scenario_id"]
        )

    repeated_ids = {
        sid
        for group in output_groups.values()
        if len(group) > 1
        for sid in group
    }

    scores = [
        score_record(
            record,
            record["scenario_id"] in repeated_ids
        )
        for record in raw_records
    ]

    scores_by_id = {
        row["scenario_id"]: row
        for row in scores
    }

    changes = []

    for sid in sorted(expected_ids):
        old = old_by_id[sid]
        new = scores_by_id[sid]

        changed = (
            old["screening_tier"]
            != new["screening_tier_v2"]
        )

        changes.append({
            "scenario_id": sid,
            "task_type": new["task_type"],
            "tier_v1": old["screening_tier"],
            "tier_v2": new["screening_tier_v2"],
            "changed": str(changed).lower(),
            "hard_v1": old["hard_failure_reasons"],
            "hard_v2": new["hard_failure_reasons_v2"],
            "review_v2": new["review_reasons_v2"],
            "legal_v2": new["legal_review_reasons_v2"],
        })

    calibration_comparison = []

    for sid in sorted(reviewed):
        human = reviewed[sid]
        old = old_by_id[sid]
        new = scores_by_id[sid]

        decision = human["human_decision"]

        unresolved = decision in {
            "false_negative",
            "needs_legal_expert",
        }

        auto_miss = (
            unresolved
            and new["screening_tier_v2"]
            == "strong_screening_candidate"
        )

        calibration_comparison.append({
            "scenario_id": sid,
            "task_type": new["task_type"],
            "human_decision": decision,
            "tier_v1": old["screening_tier"],
            "tier_v2_automatic": new["screening_tier_v2"],
            "reviewer_block": str(
                unresolved
            ).lower(),
            "remaining_auto_miss": str(
                auto_miss
            ).lower(),
            "human_notes": human["human_notes"],
        })

    cohort_flags = []

    for record in cohort_rows:
        sid = record["scenario_id"]

        human = reviewed.get(sid)

        decision = (
            human["human_decision"]
            if human
            else "not_sampled"
        )

        score = scores_by_id[sid]

        if decision in {
            "false_negative",
            "needs_legal_expert",
        }:
            status = "BLOCK_HUMAN_REVIEW"

        elif (
            score["screening_tier_v2"]
            != "strong_screening_candidate"
        ):
            status = "BLOCK_V2_AUTOMATED_SCREEN"

        else:
            status = "PROVISIONAL_ONLY_NOT_APPROVED"

        cohort_flags.append({
            "scenario_id": sid,
            "task_type": record["task_type"],
            "tier_v1": old_by_id[sid]["screening_tier"],
            "tier_v2": score["screening_tier_v2"],
            "human_decision": decision,
            "status": status,
            "approved_for_training": "false",
        })

    task_capacity = {}

    for task, quota in QUOTAS.items():
        automatic_tiers = Counter(
            row["screening_tier_v2"]
            for row in scores
            if row["task_type"] == task
        )

        strong_candidates = sum(
            row["task_type"] == task
            and row["screening_tier_v2"]
            == "strong_screening_candidate"
            and reviewed.get(
                row["scenario_id"],
                {}
            ).get("human_decision") not in {
                "false_negative",
                "needs_legal_expert",
            }
            for row in scores
        )

        task_capacity[task] = {
            "v2_automatic_tiers": dict(
                automatic_tiers
            ),
            "provisional_strong_after_review_blocks": (
                strong_candidates
            ),
            "target_quota": quota,
            "meets_target_before_legal_approval": (
                strong_candidates >= quota
            ),
        }

    v1_tiers = Counter(
        row["screening_tier"]
        for row in original_rows
    )

    v2_tiers = Counter(
        row["screening_tier_v2"]
        for row in scores
    )

    changed_count = sum(
        row["changed"] == "true"
        for row in changes
    )

    remaining_misses = [
        row["scenario_id"]
        for row in calibration_comparison
        if row["remaining_auto_miss"] == "true"
    ]

    blocked_count = sum(
        row["status"].startswith("BLOCK")
        for row in cohort_flags
    )

    summary = {
        "status": (
            "V2_HEURISTIC_SCREENING_NOT_LEGALLY_VERIFIED"
        ),
        "frozen_raw_sha256": digest(RAW),
        "frozen_eval_sha256": digest(EVAL),
        "v1_scores_sha256": digest(V1),
        "human_calibration_sha256": digest(CALIBRATION),
        "tier_v1": dict(v1_tiers),
        "tier_v2": dict(v2_tiers),
        "changed_tiers": changed_count,
        "calibration_automatic_misses_remaining": (
            remaining_misses
        ),
        "original_curated_cohort": 150,
        "original_cohort_v2_or_human_blocked": (
            blocked_count
        ),
        "task_capacity": task_capacity,
        "all_approvals_false": True,
        "methodological_caveat": (
            "Human calibration informed V2 rule design. "
            "Performance on these reviewed examples "
            "does not demonstrate generalization. "
            "Validate using independently reviewed, "
            "previously unseen examples."
        ),
    }

    OUT.mkdir(
        parents=True,
        exist_ok=True
    )

    write_csv(
        OUT / "M3_DOMAIN_SCORES_V2.csv",
        scores
    )

    write_csv(
        OUT / "M3_V1_V2_CHANGES.csv",
        changes
    )

    write_csv(
        OUT / "M3_CALIBRATION_V2_COMPARISON.csv",
        calibration_comparison
    )

    write_csv(
        OUT / "M3_ORIGINAL_COHORT_V2_FLAGS.csv",
        cohort_flags
    )

    (
        OUT / "M3_DOMAIN_SUMMARY_V2.json"
    ).write_text(
        json.dumps(
            summary,
            indent=2,
            ensure_ascii=False
        ) + "\n",
        encoding="utf-8"
    )

    print("=" * 65)
    print("M3.5 VERSIONED DOMAIN SCORER V2")
    print("=" * 65)

    print(
        "Frozen raw:",
        len(raw_records)
    )

    print(
        "Frozen evaluation verified:",
        digest(EVAL) == freeze["eval_sha256"]
    )

    print(
        "\nV1 screening tiers:",
        dict(v1_tiers)
    )

    print(
        "V2 screening tiers:",
        dict(v2_tiers)
    )

    print(
        "Changed tiers:",
        changed_count
    )

    print(
        "\nRemaining automatic misses "
        "on reviewed risk cases:",
        remaining_misses
    )

    print(
        "\nOriginal curated cohort blocked "
        "by human review or V2:",
        blocked_count
    )

    print("\nTask capacity:")

    for task, info in task_capacity.items():
        print(
            f"  {task}: "
            f"provisional strong="
            f"{info['provisional_strong_after_review_blocks']} "
            f"/ quota={info['target_quota']}"
        )

    print("\nOutput directory:", OUT)
    print("Training approvals: 0")
    print("Original datasets: unchanged")


if __name__ == "__main__":
    main()
