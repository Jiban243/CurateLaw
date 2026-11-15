
"""
CurateLaw M5 V3
Independent evaluation screening of saved model predictions.

This script:
1. Verifies the frozen evaluation benchmark.
2. Validates Base, Raw and Curated predictions.
3. Detects potential drafting-quality problems.
4. Identifies identical Raw/Curated responses.
5. Checks training/inference prompt-label mismatches.
6. Generates a blinded review sheet.
7. Saves a private model-identity key.
8. Produces a reproducible screening summary.

No GPU, API keys, model inference or additional training required.

Important:
Automatic screening flags are NOT verified factual errors.
This script does not claim to measure legal correctness.
"""

from __future__ import annotations

import csv
import hashlib
import json
import random
import re

from collections import Counter
from pathlib import Path


# ============================================================
# PROJECT PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

BENCHMARK = (
    ROOT
    / "data"
    / "m2"
    / "frozen"
    / "heldout_eval_040.jsonl"
)

PRED_DIR = (
    ROOT
    / "evaluation_artifacts"
    / "m5_v3"
    / "inputs"
)

OUT = ROOT / "results" / "m5_v3"

EXPECTED_BENCHMARK_SHA = (
    "944ba82ed4937a41f32c064aaaa89f1b34aeb2d44a89e0860aac51aa3d46bff9"
)

MODELS = ("base", "raw", "curated")


# ============================================================
# OLD VALUES IN CONTRACT-EDITING SCENARIOS
# ============================================================

# These patterns flag old values retained in generated text.
# They do NOT automatically establish incorrectness.
# For example, a response may quote an old value while
# explicitly correcting it.

STALE = {
    "EVAL017": (
        r"(?<!\d)950[,. ]?000(?!\d)",
        "old_salary_950000",
    ),
    "EVAL018": (
        r"\bon[- ]site\b.{0,40}\bfive\s+days\b",
        "old_five_office_days",
    ),
    "EVAL019": (
        r"\b(?:45|forty[- ]five)\s+days?\b",
        "old_notice_45_days",
    ),
    "EVAL020": (
        r"\bData Analyst\b",
        "old_role_data_analyst",
    ),
    "EVAL021": (
        r"\b(?:six|6)\s+months?\b",
        "old_probation_six_months",
    ),
    "EVAL022": (
        r"\bJaipur\b",
        "old_location_jaipur",
    ),
    "EVAL023": (
        r"\b48\s+hours?\b",
        "old_week_48_hours",
    ),
    "EVAL024": (
        r"\b18\s+days?\b",
        "old_leave_18_days",
    ),
    "EVAL025": (
        r"(?<!\d)1[,. ]?200[,. ]?000(?!\d)",
        "old_salary_1200000",
    ),
    "EVAL026": (
        r"\b(?:six|6)\s+months?\b",
        "old_probation_six_months",
    ),
    "EVAL027": (
        r"\b(?:45|forty[- ]five)\s+days?\b",
        "old_notice_45_days",
    ),
    "EVAL028": (
        r"\bUX Designer\b",
        "old_role_ux_designer",
    ),
    "EVAL029": (
        r"\bfully\s+remote\b|\bevery\s+weekday\b",
        "old_remote_arrangement",
    ),
    "EVAL030": (
        r"\b48\s+hours?\b",
        "old_week_48_hours",
    ),
    "EVAL031": (
        r"\b15\s+days?\b",
        "old_leave_15_days",
    ),
    "EVAL032": (
        r"\bPune\b",
        "old_location_pune",
    ),
}


# ============================================================
# FILE UTILITIES
# ============================================================

def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        raise FileNotFoundError(
            f"Missing input file: {path}"
        )

    with path.open(encoding="utf-8") as file:
        return [
            json.loads(line)
            for line in file
            if line.strip()
        ]


def sha256(path: Path) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def write_csv(
    path: Path,
    rows: list[dict],
    fields: list[str],
) -> None:

    with path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fields,
        )

        writer.writeheader()
        writer.writerows(rows)


# ============================================================
# AUTOMATED RESPONSE FLAGS
# ============================================================

def flags_for(
    scenario: dict,
    prediction: dict,
) -> list[str]:

    sid = scenario["scenario_id"]
    response = prediction["response"]

    found = []

    # 1. Generation reached its token budget.
    if prediction["hit_token_limit"]:
        found.append("token_limit_hit")

    # 2. Completely empty response.
    if not response.strip():
        found.append("empty_response")

    # 3. Unresolved value placeholders.
    placeholder_pattern = (
        r"\[(?:number|amount|salary|days|months|"
        r"notice|duration)\b[^\]]*\]"
    )

    if re.search(
        placeholder_pattern,
        response,
        re.IGNORECASE,
    ):
        found.append("unresolved_value_placeholder")

    # 4. Repeated long paragraphs.
    paragraphs = [
        re.sub(
            r"\s+",
            " ",
            paragraph,
        ).strip().casefold()
        for paragraph in re.split(
            r"\n\s*\n",
            response,
        )
    ]

    paragraphs = [
        paragraph
        for paragraph in paragraphs
        if len(paragraph) >= 80
    ]

    counts = Counter(paragraphs)

    if any(
        count >= 2
        for count in counts.values()
    ):
        found.append("repeated_long_paragraph")

    # 5. Old values retained after editing.
    if sid in STALE:
        pattern, tag = STALE[sid]

        if re.search(
            pattern,
            response,
            re.IGNORECASE,
        ):
            found.append(tag + "_present")

    # 6. Very long responses for non-agreement tasks.
    if (
        scenario["task_type"] != "full_agreement"
        and len(response.split()) > 250
    ):
        found.append("long_output_review")

    # 7. Written salary values requiring review.
    if sid in (
        "EVAL004",
        "EVAL006",
        "EVAL007",
    ):
        if re.search(
            r"\b(?:crores?|lakhs?)\b",
            response,
            re.IGNORECASE,
        ):
            found.append(
                "written_salary_amount_review"
            )

    return found


# ============================================================
# MAIN EVALUATION
# ============================================================

def main() -> None:

    print("=" * 70)
    print("CURATELAW — M5 V3 EVALUATION SCREENING")
    print("=" * 70)

    # --------------------------------------------------------
    # 1. Verify frozen benchmark.
    # --------------------------------------------------------

    benchmark_hash = sha256(BENCHMARK)

    if benchmark_hash != EXPECTED_BENCHMARK_SHA:
        raise ValueError(
            "Frozen benchmark checksum mismatch.\n"
            f"Actual: {benchmark_hash}\n"
            f"Expected: {EXPECTED_BENCHMARK_SHA}"
        )

    scenarios = read_jsonl(BENCHMARK)

    scenario_map = {
        row["scenario_id"]: row
        for row in scenarios
    }

    if (
        len(scenarios) != 40
        or len(scenario_map) != 40
    ):
        raise ValueError(
            "Expected exactly 40 unique evaluation scenarios."
        )

    print("\nBenchmark verified.")
    print("Scenarios:", len(scenarios))

    # --------------------------------------------------------
    # 2. Load predictions from all models.
    # --------------------------------------------------------

    predictions = {}

    input_hashes = {
        str(BENCHMARK): benchmark_hash
    }

    for model in MODELS:

        path = PRED_DIR / f"{model}_predictions.jsonl"

        if not path.is_file():
            raise FileNotFoundError(
                f"Missing {model} predictions:\n{path}"
            )

        input_hashes[str(path)] = sha256(path)

        rows = read_jsonl(path)

        indexed = {
            row["scenario_id"]: row
            for row in rows
        }

        if (
            len(rows) != 40
            or len(indexed) != 40
            or set(indexed) != set(scenario_map)
        ):
            raise ValueError(
                f"{model}: invalid or duplicate scenario IDs."
            )

        for sid, row in indexed.items():

            if row["model"] != model:
                raise ValueError(
                    f"{model}/{sid}: model label mismatch."
                )

            if row["benchmark_sha256"] != benchmark_hash:
                raise ValueError(
                    f"{model}/{sid}: benchmark mismatch."
                )

            if not isinstance(
                row.get("response"),
                str,
            ):
                raise ValueError(
                    f"{model}/{sid}: missing response text."
                )

        predictions[model] = indexed

        print(
            f"{model.upper()} predictions verified:",
            len(rows),
        )

    # --------------------------------------------------------
    # 3. Verify matched prompts and token budgets.
    # --------------------------------------------------------

    mismatched_input_labels = 0

    for sid, scenario in scenario_map.items():

        rows = [
            predictions[model][sid]
            for model in MODELS
        ]

        prompts = {
            row["prompt"]
            for row in rows
        }

        budgets = {
            row["max_new_tokens"]
            for row in rows
        }

        if len(prompts) != 1:
            raise ValueError(
                f"{sid}: prompts differ between models."
            )

        if len(budgets) != 1:
            raise ValueError(
                f"{sid}: generation budgets differ."
            )

        if (
            scenario.get("input")
            and "Provided text:" in rows[0]["prompt"]
        ):
            mismatched_input_labels += 1

    # --------------------------------------------------------
    # 4. Automated screening.
    # --------------------------------------------------------

    OUT.mkdir(
        parents=True,
        exist_ok=True,
    )

    counts = {}
    review_queue = []
    records = []

    for model in MODELS:

        flag_counts = Counter()

        for sid in sorted(scenario_map):

            scenario = scenario_map[sid]
            prediction = predictions[model][sid]

            flags = flags_for(
                scenario,
                prediction,
            )

            flag_counts.update(flags)

            records.append({
                "scenario_id": sid,
                "model": model,
                "task_type": scenario["task_type"],
                "flags": ";".join(flags),
                "flag_count": len(flags),
                "hit_token_limit": (
                    prediction["hit_token_limit"]
                ),
                "response_words": len(
                    prediction["response"].split()
                ),
            })

            if flags:
                review_queue.append({
                    "scenario_id": sid,
                    "model": model,
                    "task_type": scenario["task_type"],
                    "flags": ";".join(flags),
                    "instruction": (
                        scenario["instruction"]
                    ),
                    "input": scenario.get("input", ""),
                    "response": (
                        prediction["response"]
                    ),
                })

        counts[model] = dict(
            sorted(flag_counts.items())
        )

    # --------------------------------------------------------
    # 5. Create blinded review dataset.
    # --------------------------------------------------------

    rng = random.Random(20261116)

    blind_rows = []
    identity_key = {}

    for sid in sorted(scenario_map):

        candidates = list(MODELS)
        rng.shuffle(candidates)

        for label, model in zip(
            "ABC",
            candidates,
        ):

            blind_id = f"{sid}-{label}"

            identity_key[blind_id] = model

            scenario = scenario_map[sid]

            blind_rows.append({
                "blind_id": blind_id,
                "task_type": scenario["task_type"],
                "instruction": (
                    scenario["instruction"]
                ),
                "input": scenario.get("input", ""),
                "expected_facts": json.dumps(
                    scenario["expected_facts"],
                    ensure_ascii=False,
                ),
                "response": (
                    predictions[model][sid]["response"]
                ),
                "requested_facts_correct_0_2": "",
                "no_contradictions_0_2": "",
                "instruction_compliance_0_2": "",
                "completeness_0_2": "",
                "reviewer_notes": "",
            })

    rng.shuffle(blind_rows)

    # --------------------------------------------------------
    # 6. Save automatic flags.
    # --------------------------------------------------------

    write_csv(
        OUT / "automatic_flags.csv",
        records,
        [
            "scenario_id",
            "model",
            "task_type",
            "flags",
            "flag_count",
            "hit_token_limit",
            "response_words",
        ],
    )

    # --------------------------------------------------------
    # 7. Save flagged review queue.
    # --------------------------------------------------------

    write_csv(
        OUT / "flagged_review_queue.csv",
        review_queue,
        [
            "scenario_id",
            "model",
            "task_type",
            "flags",
            "instruction",
            "input",
            "response",
        ],
    )

    # --------------------------------------------------------
    # 8. Save blinded review form.
    # --------------------------------------------------------

    write_csv(
        OUT / "blinded_review_form.csv",
        blind_rows,
        [
            "blind_id",
            "task_type",
            "instruction",
            "input",
            "expected_facts",
            "response",
            "requested_facts_correct_0_2",
            "no_contradictions_0_2",
            "instruction_compliance_0_2",
            "completeness_0_2",
            "reviewer_notes",
        ],
    )

    # The identity key must remain private.
    (OUT / "PRIVATE_blinding_key.json").write_text(
        json.dumps(
            identity_key,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    # --------------------------------------------------------
    # 9. Compare exact Raw and Curated responses.
    # --------------------------------------------------------

    identical = [
        sid
        for sid in sorted(scenario_map)
        if (
            predictions["raw"][sid]["response"]
            ==
            predictions["curated"][sid]["response"]
        )
    ]

    # --------------------------------------------------------
    # 10. Generate reproducible summary.
    # --------------------------------------------------------

    summary = {
        "status": (
            "EXPLORATORY_AUTOMATED_SCREENING_"
            "NOT_VERIFIED_ACCURACY"
        ),
        "benchmark_sha256": benchmark_hash,
        "input_sha256": input_hashes,
        "examples_per_model": 40,
        "raw_curated_exact_response_ties": (
            len(identical)
        ),
        "identical_scenario_ids": identical,
        "train_inference_label_mismatch_scenarios": (
            mismatched_input_labels
        ),
        "flags_by_model": counts,
        "limitations": [
            (
                "Flags indicate candidates for review, "
                "not confirmed inaccuracies."
            ),
            (
                "This script intentionally does not "
                "compute a new model-quality score."
            ),
            (
                "Benchmark expected facts and legal content "
                "are not independently verified."
            ),
            (
                "Do not publish the private blinding key "
                "with the reviewer form."
            ),
        ],
    }

    (OUT / "screening_summary.json").write_text(
        json.dumps(
            summary,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    # --------------------------------------------------------
    # 11. Save the review rubric.
    # --------------------------------------------------------

    rubric = """# CurateLaw M5 V3 — Blinded Review Rubric

Review each response against its frozen scenario.

Each dimension is scored:

- 0 = Fails
- 1 = Partially meets requirements or ambiguous
- 2 = Meets requirements

## 1. Requested facts correct

All required facts and numerical values are accurately represented.

Contradictory written and numeric values do not receive full credit.

## 2. No contradictions

The response contains no material internal contradictions.

For editing tasks, old incorrect values must not remain as active terms.

## 3. Instruction compliance

The output performs the requested operation.

It avoids inventing unrelated terms or ignoring "return only"
instructions.

## 4. Completeness

The requested clause, correction or agreement is sufficiently
complete and is not cut off or left unresolved.

## Review procedure

Record a reason for every score of 0 or 1.

Do not open PRIVATE_blinding_key.json until the review scores
are finalized.

Independent reviewers are preferred.

This is an experimental drafting-quality assessment,
NOT independent legal verification.
"""

    (OUT / "review_rubric.md").write_text(
        rubric,
        encoding="utf-8",
    )

    # --------------------------------------------------------
    # 12. Print the results.
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("M5 V3 SCREENING COMPLETED")
    print("=" * 70)

    print(
        "Benchmark checksum verified:",
        benchmark_hash,
    )

    print(
        "Raw/Curated identical responses:",
        len(identical),
        "/ 40",
    )

    print(
        "Train/inference input-label mismatches:",
        mismatched_input_labels,
    )

    print("\nFlag counts (NOT accuracy scores):")

    for model in MODELS:
        print(
            f"  {model.upper()}:",
            counts[model],
        )

    print(
        "\nBlinded review rows:",
        len(blind_rows),
    )

    print("\nOutput directory:", OUT)

    print("\nGenerated files:")

    for filename in [
        "automatic_flags.csv",
        "flagged_review_queue.csv",
        "blinded_review_form.csv",
        "PRIVATE_blinding_key.json",
        "screening_summary.json",
        "review_rubric.md",
    ]:
        print(" ", OUT / filename)

    print("\nNo inference, retraining or model calls performed.")
    print("Original M1-M5 artifacts remain unchanged.")


if __name__ == "__main__":
    main()
