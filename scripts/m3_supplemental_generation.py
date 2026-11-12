
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re

from collections import Counter
from datetime import datetime, timezone
from getpass import getpass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

FROZEN = ROOT / "data/m2/frozen"

SUPPLEMENTAL = ROOT / "data/m3/supplemental"

SCENARIOS = (
    SUPPLEMENTAL / "scenarios_0100.jsonl"
)

MANIFEST = (
    SUPPLEMENTAL / "preparation_manifest.json"
)

OUTPUT = (
    SUPPLEMENTAL / "generated_raw.jsonl"
)

PROMPT_VERSION = "m3_guarded_full_v1"

SEED = 20261112
COUNT = 100


SYSTEM_PROMPT = """
You draft fictional, illustrative Indian technology-sector
employment agreements for supervised-learning research.

Return ONLY the complete agreement in Markdown, using clearly
numbered section headings.

Follow these supplied details exactly:
- Employee role and Indian state
- Fixed annual salary in INR
- Work arrangement
- Scheduled weekly working hours
- Probation period in months
- Mutual termination-notice period in days

The specified terms must remain consistent throughout the
agreement, including during probation.

Do not introduce:
- A shorter probationary notice period
- An extension to the specified probation period
- Employer-only salary-in-lieu-of-notice rights
- Unrequested termination exceptions
- Additional compensation amounts
- Post-employment non-compete restrictions

Include the following sections:
1. Parties and agreement date
2. Appointment
3. Duties and responsibilities
4. Workplace and work arrangement
5. Fixed annual salary
6. Probation
7. Working hours
8. Leave
9. Applicable statutory benefits
10. Confidentiality
11. Work-related intellectual property
12. Workplace policies
13. Termination
14. Dispute resolution
15. Governing law
16. Employer and employee signatures

Use explicit placeholders including:
[Date], [Joining Date], [Employer Name], [Employee Name],
[Employer Address], [Employee Address].

Do not invent specific statutory rates or benefits.

Keep statutory obligations subject to applicable central
and state law. Prefer generic references to applicable law
instead of citing named statutes whose current applicability
has not been verified.

Avoid numbered cross-references to other sections.
Avoid writing salary amounts in words.
Do not copy third-party contract templates.

Produce a substantially complete illustrative agreement,
approximately 600 words or longer.

Before submitting, silently check the requested values,
section structure, placeholders, and internal consistency.

Do not output your checklist or commentary.
""".strip()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(
            lambda: file.read(1024 * 1024),
            b""
        ):
            digest.update(chunk)

    return digest.hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    with path.open(
        "r",
        encoding="utf-8"
    ) as file:
        return [
            json.loads(line)
            for line in file
            if line.strip()
        ]


def write_jsonl(
    path: Path,
    records: list[dict]
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with path.open(
        "w",
        encoding="utf-8"
    ) as file:
        for record in records:
            file.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                    sort_keys=True
                ) + "\n"
            )


def normalized_prompt(record: dict) -> str:
    instruction = str(
        record.get("instruction", "")
    )

    return " ".join(
        instruction.casefold().split()
    )


def get_work_mode(
    instruction: str
) -> str | None:
    match = re.search(
        r"\b(remote|hybrid|on-site|onsite)"
        r"\s+work arrangement\b",
        instruction,
        re.I
    )

    if not match:
        return None

    value = match.group(1).lower()

    if value == "onsite":
        return "on-site"

    return value


def scenario_signature(
    record: dict
) -> tuple | None:
    if record.get("task_type") != "full_agreement":
        return None

    facts = record.get(
        "expected_facts"
    ) or {}

    fields = (
        "role",
        "state",
        "salary_inr",
        "scheduled_weekly_hours",
        "probation_months",
        "notice_days"
    )

    values = [
        facts.get(field)
        for field in fields
    ]

    work_mode = get_work_mode(
        record.get("instruction", "")
    )

    if (
        any(value is None for value in values)
        or work_mode is None
    ):
        return None

    return tuple(
        str(value).casefold()
        for value in values
    ) + (work_mode,)


def verify_frozen_datasets():
    raw_path = (
        FROZEN / "pool_raw_0400.jsonl"
    )

    eval_path = (
        FROZEN / "heldout_eval_040.jsonl"
    )

    manifest_path = (
        FROZEN / "freeze_manifest.json"
    )

    with manifest_path.open(
        encoding="utf-8"
    ) as file:
        manifest = json.load(file)

    for path, key in [
        (raw_path, "raw_sha256"),
        (eval_path, "eval_sha256")
    ]:
        expected = manifest.get(key)
        actual = sha256(path)

        if expected != actual:
            raise SystemExit(
                f"Frozen checksum mismatch: {path}"
            )

    raw = read_jsonl(raw_path)
    evaluation = read_jsonl(eval_path)

    if len(raw) != 400:
        raise SystemExit(
            "Expected 400 frozen raw examples."
        )

    if len(evaluation) != 40:
        raise SystemExit(
            "Expected 40 held-out evaluation cases."
        )

    return raw, evaluation


def original_teacher(
    raw: list[dict]
) -> tuple[str, float]:
    full = [
        record
        for record in raw
        if record["task_type"] == "full_agreement"
    ]

    models = Counter(
        str(
            record.get("generation_model", "")
        ).strip()
        for record in full
    )

    temperatures = Counter(
        str(
            record.get("generation_temperature", "")
        ).strip()
        for record in full
    )

    model = models.most_common(1)[0][0]

    temperature = float(
        temperatures.most_common(1)[0][0]
    )

    if (
        not model
        or len(models) != 1
        or len(temperatures) != 1
    ):
        raise SystemExit(
            "Original full-agreement generation "
            "parameters are inconsistent."
        )

    return model, temperature


def prepare_scenarios(
    raw: list[dict],
    evaluation: list[dict]
) -> None:
    source = [
        record
        for record in raw
        if record["task_type"] == "full_agreement"
    ]

    if len(source) != 120:
        raise SystemExit(
            "Expected 120 original full agreements."
        )

    roles = sorted({
        record["expected_facts"]["role"]
        for record in source
    })

    states = sorted({
        record["expected_facts"]["state"]
        for record in source
    })

    salaries = sorted({
        int(record["expected_facts"]["salary_inr"])
        for record in source
    })

    hours = sorted({
        int(
            record["expected_facts"][
                "scheduled_weekly_hours"
            ]
        )
        for record in source
    })

    probation = sorted({
        int(record["expected_facts"]["probation_months"])
        for record in source
    })

    notice = sorted({
        int(record["expected_facts"]["notice_days"])
        for record in source
    })

    work_modes = sorted({
        get_work_mode(record["instruction"])
        for record in source
    })

    if None in work_modes:
        raise SystemExit(
            "Could not identify every original work mode."
        )

    existing_prompts = {
        normalized_prompt(record)
        for record in raw + evaluation
    }

    existing_signatures = {
        signature
        for record in raw + evaluation
        if (
            signature := scenario_signature(record)
        ) is not None
    }

    seen = set(existing_signatures)

    rng = random.Random(SEED)

    scenarios = []
    attempts = 0

    while (
        len(scenarios) < COUNT
        and attempts < 30000
    ):
        attempts += 1

        role = rng.choice(roles)
        state = rng.choice(states)
        salary = rng.choice(salaries)
        weekly_hours = rng.choice(hours)
        probation_months = rng.choice(probation)
        notice_days = rng.choice(notice)
        work_mode = rng.choice(work_modes)

        signature = (
            str(role).casefold(),
            str(state).casefold(),
            str(salary),
            str(weekly_hours),
            str(probation_months),
            str(notice_days),
            work_mode
        )

        if signature in seen:
            continue

        instruction = (
            f"For a fictional {role} employed in "
            f"{state}, India, draft an illustrative "
            f"employment agreement with INR {salary} "
            f"fixed annual salary, a {work_mode} "
            f"work arrangement, {weekly_hours} scheduled "
            f"hours per week, {probation_months} months "
            f"of probation, and {notice_days} days of "
            "mutual notice. Include parties, appointment, "
            "duties, workplace, salary, probation, "
            "working time, leave, applicable statutory "
            "benefits, confidentiality, work-related IP, "
            "workplace policy, termination, disputes "
            "and signatures. Use party and date "
            "placeholders. Do not invent legal rates, "
            "extra payment amounts, or post-employment "
            "non-competes; make contractual terms "
            "subject to applicable law."
        )

        normalized = " ".join(
            instruction.casefold().split()
        )

        if normalized in existing_prompts:
            continue

        sid = (
            f"SUP{len(scenarios) + 1:04d}"
        )

        scenarios.append({
            "scenario_id": sid,
            "task_type": "full_agreement",
            "instruction": instruction,
            "input": "",
            "expected_facts": {
                "role": role,
                "state": state,
                "salary_inr": salary,
                "scheduled_weekly_hours": weekly_hours,
                "probation_months": probation_months,
                "notice_days": notice_days,
                "work_arrangement": work_mode
            },
            "reference_text_copied": False,
            "scenario_origin": (
                "m3_supplemental_guarded_v1"
            ),
            "split": "train_pool_only"
        })

        existing_prompts.add(normalized)
        seen.add(signature)

    if len(scenarios) != COUNT:
        raise SystemExit(
            "Unable to generate 100 unique scenarios."
        )

    if SCENARIOS.exists() or MANIFEST.exists():
        if not (
            SCENARIOS.exists()
            and MANIFEST.exists()
        ):
            raise SystemExit(
                "Incomplete previous preparation. "
                "Refusing to overwrite files."
            )

        stored = read_jsonl(SCENARIOS)

        if stored != scenarios:
            raise SystemExit(
                "Existing supplemental scenarios "
                "differ from the deterministic result."
            )

        print(
            "Existing scenarios verified:",
            len(stored)
        )

    else:
        write_jsonl(
            SCENARIOS,
            scenarios
        )

    model, temperature = original_teacher(raw)

    metadata = {
        "count": COUNT,
        "seed": SEED,
        "prompt_version": PROMPT_VERSION,
        "scenario_sha256": sha256(SCENARIOS),
        "frozen_raw_sha256": sha256(
            FROZEN / "pool_raw_0400.jsonl"
        ),
        "frozen_eval_sha256": sha256(
            FROZEN / "heldout_eval_040.jsonl"
        ),
        "teacher_model": model,
        "teacher_temperature": temperature,
        "note": (
            "Supplemental scenarios use revised teacher "
            "instructions. Experimental cohorts must "
            "control for generation recipe and come "
            "from one documented common pool."
        )
    }

    if MANIFEST.exists():
        previous = json.loads(
            MANIFEST.read_text(
                encoding="utf-8"
            )
        )

        if previous != metadata:
            raise SystemExit(
                "Preparation manifest mismatch. "
                "Refusing to overwrite."
            )

    else:
        MANIFEST.write_text(
            json.dumps(
                metadata,
                indent=2
            ) + "\n",
            encoding="utf-8"
        )

    print("=" * 65)
    print("M3.5.3 SUPPLEMENTAL SCENARIOS PREPARED")
    print("=" * 65)

    print("Prepared scenarios:", len(scenarios))
    print("Teacher model:", model)
    print("Original temperature:", temperature)
    print("Scenario file:", SCENARIOS)
    print("Manifest:", MANIFEST)
    print("API calls: 0")
    print("Inference credits consumed: 0")


def generate(
    raw: list[dict],
    limit: int,
    max_tokens: int
) -> None:
    if not (
        SCENARIOS.exists()
        and MANIFEST.exists()
    ):
        raise SystemExit(
            "Prepare scenarios before generating."
        )

    metadata = json.loads(
        MANIFEST.read_text(
            encoding="utf-8"
        )
    )

    if (
        metadata["scenario_sha256"]
        != sha256(SCENARIOS)
    ):
        raise SystemExit(
            "Supplemental scenario checksum mismatch."
        )

    if (
        metadata["frozen_raw_sha256"]
        != sha256(
            FROZEN / "pool_raw_0400.jsonl"
        )
    ):
        raise SystemExit(
            "Original raw dataset has changed."
        )

    if (
        metadata["frozen_eval_sha256"]
        != sha256(
            FROZEN / "heldout_eval_040.jsonl"
        )
    ):
        raise SystemExit(
            "Original evaluation dataset has changed."
        )

    model, temperature = original_teacher(raw)

    if (
        model != metadata["teacher_model"]
        or temperature != metadata["teacher_temperature"]
    ):
        raise SystemExit(
            "Teacher model metadata mismatch."
        )

    scenarios = read_jsonl(SCENARIOS)

    valid_ids = {
        row["scenario_id"]
        for row in scenarios
    }

    previous = (
        read_jsonl(OUTPUT)
        if OUTPUT.exists()
        else []
    )

    previous_ids = [
        row["scenario_id"]
        for row in previous
    ]

    if (
        len(previous_ids) != len(set(previous_ids))
        or not set(previous_ids).issubset(valid_ids)
    ):
        raise SystemExit(
            "Existing generated output contains "
            "duplicate or unexpected IDs."
        )

    completed = set(previous_ids)

    pending = [
        row
        for row in scenarios
        if row["scenario_id"] not in completed
    ][:limit]

    print("Previously completed:", len(completed))
    print("Remaining:", len(scenarios) - len(completed))

    if not pending:
        print("No pending scenarios.")
        return

    print(
        "Maximum new paid requests:",
        len(pending)
    )

    print("Teacher:", model)

    token = (
        os.getenv("HF_TOKEN")
        or os.getenv("HUGGINGFACEHUB_API_TOKEN")
    )

    if not token:
        token = getpass(
            "Hugging Face token (hidden): "
        ).strip()

    if not token:
        raise SystemExit(
            "No Hugging Face token supplied."
        )

    from huggingface_hub import InferenceClient

    client = InferenceClient(
        token=token,
        timeout=180
    )

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    new_count = 0

    for scenario in pending:
        sid = scenario["scenario_id"]

        try:
            response = client.chat_completion(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT
                    },
                    {
                        "role": "user",
                        "content": scenario["instruction"]
                    }
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )

            content = (
                response.choices[0]
                .message.content
            )

            if (
                not isinstance(content, str)
                or not content.strip()
            ):
                print(
                    sid,
                    "empty response; not saved"
                )
                continue

            usage = getattr(
                response,
                "usage",
                None
            )

            finish_reason = (
                response.choices[0].finish_reason
            )

            record = {
                **scenario,
                "output": content.strip(),
                "origin": (
                    "m3_supplemental_guarded_v1"
                ),
                "generation_prompt_version": (
                    PROMPT_VERSION
                ),
                "generation_model": model,
                "generation_temperature": temperature,
                "max_output_tokens": max_tokens,
                "finish_reason": finish_reason,
                "prompt_tokens": getattr(
                    usage,
                    "prompt_tokens",
                    None
                ),
                "completion_tokens": getattr(
                    usage,
                    "completion_tokens",
                    None
                ),
                "created_at_utc": datetime.now(
                    timezone.utc
                ).isoformat(),
                "legal_review_status": "not_reviewed",
                "approved_for_training": False
            }

            with OUTPUT.open(
                "a",
                encoding="utf-8"
            ) as file:
                file.write(
                    json.dumps(
                        record,
                        ensure_ascii=False
                    ) + "\n"
                )

                file.flush()
                os.fsync(file.fileno())

            completed.add(sid)
            new_count += 1

            print(
                sid,
                "saved",
                len(content.split()),
                "words",
                "finish_reason=",
                finish_reason
            )

        except Exception as exc:
            print(
                sid,
                "request failed:",
                type(exc).__name__
            )

            print(
                "Failed example not saved. "
                "Rerun to resume."
            )

            break

    print("\nNew examples saved:", new_count)
    print("Total saved:", len(completed))
    print("Output:", OUTPUT)

    print(
        "Original datasets unchanged. "
        "Training approvals: 0"
    )


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--generate",
        action="store_true",
        help=(
            "Generate responses using Hugging Face. "
            "Without this option, only prepare scenarios."
        )
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=5
    )

    parser.add_argument(
        "--max-tokens",
        type=int,
        default=3200
    )

    args = parser.parse_args()

    if not 1 <= args.limit <= 100:
        parser.error(
            "--limit must be between 1 and 100."
        )

    if not 1000 <= args.max_tokens <= 5000:
        parser.error(
            "--max-tokens must be between 1000 and 5000."
        )

    raw, evaluation = verify_frozen_datasets()

    if args.generate:
        generate(
            raw,
            args.limit,
            args.max_tokens
        )

    else:
        prepare_scenarios(
            raw,
            evaluation
        )


if __name__ == "__main__":
    main()
