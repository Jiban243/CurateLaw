
import csv
import hashlib
import json
import random
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

RAW = DATA / "m2/frozen/pool_raw_0400.jsonl"
EVAL = DATA / "m2/frozen/heldout_eval_040.jsonl"
FREEZE = DATA / "m2/frozen/freeze_manifest.json"

SCORES = DATA / "m3/domain_curation_v2/M3_DOMAIN_SCORES_V2.csv"

REVIEWS = (
    DATA / "m3/provisional_cohorts/"
    "M3_CALIBRATION_HUMAN_REVIEW.csv"
)

OUT = DATA / "m3/finetune_ready"

SEED = 20261112
TARGET = 150

QUOTAS = {
    "full_agreement": 12,
    "clause_drafting": 45,
    "contract_customization": 45,
    "contradiction_correction": 32,
    "missing_clause_completion": 16,
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_jsonl(path):
    with path.open(encoding="utf-8") as file:
        return [
            json.loads(line)
            for line in file
            if line.strip()
        ]


def read_csv(path):
    with path.open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def normalize(text):
    return " ".join(str(text).casefold().split())


def save_unchanged(path, content):
    if path.exists():
        if path.read_text(encoding="utf-8") != content:
            raise RuntimeError(
                f"Existing output differs. Not overwriting: {path}"
            )
    else:
        path.write_text(content, encoding="utf-8")


def chat_example(record):
    user = record["instruction"].strip()
    supplied = str(record.get("input") or "").strip()

    if supplied:
        user += "\n\nInput:\n" + supplied

    return {
        "messages": [
            {"role": "user", "content": user},
            {
                "role": "assistant",
                "content": record["output"].strip()
            },
        ]
    }


def main():
    for path in [RAW, EVAL, FREEZE, SCORES, REVIEWS]:
        if not path.is_file():
            raise RuntimeError(f"Missing file: {path}")

    manifest = json.loads(
        FREEZE.read_text(encoding="utf-8")
    )

    if sha256(RAW) != manifest["raw_sha256"]:
        raise RuntimeError("Frozen raw checksum mismatch.")

    if sha256(EVAL) != manifest["eval_sha256"]:
        raise RuntimeError("Held-out evaluation checksum mismatch.")

    raw_rows = read_jsonl(RAW)
    eval_rows = read_jsonl(EVAL)
    score_rows = read_csv(SCORES)
    review_rows = read_csv(REVIEWS)

    records = {
        row["scenario_id"]: row
        for row in raw_rows
    }

    scores = {
        row["scenario_id"]: row
        for row in score_rows
    }

    reviews = {
        row["scenario_id"]: row
        for row in review_rows
    }

    if (
        len(records) != 400
        or len(raw_rows) != 400
        or len(scores) != 400
        or set(records) != set(scores)
        or len(reviews) != 27
        or len(review_rows) != 27
        or len(eval_rows) != 40
    ):
        raise RuntimeError("Unexpected dataset structure.")

    if sum(QUOTAS.values()) != TARGET:
        raise RuntimeError("Quota total mismatch.")

    for row in review_rows:
        if not (
            row["human_decision"].strip()
            and row["human_notes"].strip()
        ):
            raise RuntimeError("Incomplete human calibration.")

    heldout_prompts = {
        (
            normalize(row["instruction"]),
            normalize(row.get("input", ""))
        )
        for row in eval_rows
    }

    for record in raw_rows:
        if (
            normalize(record["instruction"]),
            normalize(record.get("input", ""))
        ) in heldout_prompts:
            raise RuntimeError(
                "Exact held-out prompt overlap detected."
            )

    blocked = {
        sid
        for sid, row in reviews.items()
        if row["human_decision"] in {
            "false_negative",
            "needs_legal_expert",
        }
    }

    rng = random.Random(SEED)
    selected = {}
    used_responses = set()

    pools = {}

    for task in QUOTAS:
        pool = [
            record
            for record in raw_rows
            if record["task_type"] == task
            and record["scenario_id"] not in blocked
            and scores[record["scenario_id"]][
                "screening_tier_v2"
            ] == "strong_screening_candidate"
        ]

        rng.shuffle(pool)

        pool.sort(
            key=lambda row: -int(
                scores[row["scenario_id"]][
                    "quality_score_heuristic_v2"
                ]
            )
        )

        pools[task] = pool

    curated = []

    for task, quota in QUOTAS.items():
        count = 0

        for record in pools[task]:
            if count >= quota:
                break

            sid = record["scenario_id"]
            response_key = normalize(record["output"])

            if (
                sid in selected
                or not response_key
                or response_key in used_responses
            ):
                continue

            selected[sid] = record
            used_responses.add(response_key)
            curated.append(record)
            count += 1

    if len(curated) < TARGET:
        remaining = []

        for task in QUOTAS:
            remaining.extend(
                record
                for record in pools[task]
                if record["scenario_id"] not in selected
            )

        rng.shuffle(remaining)

        remaining.sort(
            key=lambda row: -int(
                scores[row["scenario_id"]][
                    "quality_score_heuristic_v2"
                ]
            )
        )

        for record in remaining:
            if len(curated) >= TARGET:
                break

            sid = record["scenario_id"]
            response_key = normalize(record["output"])

            if (
                sid in selected
                or not response_key
                or response_key in used_responses
            ):
                continue

            selected[sid] = record
            used_responses.add(response_key)
            curated.append(record)

    if len(curated) < TARGET:
        raise RuntimeError(
            f"Only {len(curated)} unique strong examples "
            "available. No unsafe automatic backfill performed."
        )

    actual_quotas = Counter(
        record["task_type"]
        for record in curated
    )

    raw_cohort = []

    for task, count in actual_quotas.items():
        candidates = [
            record
            for record in raw_rows
            if record["task_type"] == task
        ]

        raw_cohort.extend(
            rng.sample(candidates, count)
        )

    rng.shuffle(curated)
    rng.shuffle(raw_cohort)

    if len(raw_cohort) != TARGET:
        raise RuntimeError("Raw cohort size mismatch.")

    if any(
        record["scenario_id"] in blocked
        for record in curated
    ):
        raise RuntimeError("Blocked candidate selected.")

    raw_chat = [
        chat_example(record)
        for record in raw_cohort
    ]

    curated_chat = [
        chat_example(record)
        for record in curated
    ]

    if any(
        not example["messages"][1]["content"]
        for example in raw_chat + curated_chat
    ):
        raise RuntimeError("Empty assistant response.")

    OUT.mkdir(parents=True, exist_ok=True)

    files = {
        "raw_150_messages.jsonl": raw_chat,
        "curated_150_messages.jsonl": curated_chat,
    }

    for filename, examples in files.items():
        content = "".join(
            json.dumps(
                item,
                ensure_ascii=False
            ) + "\n"
            for item in examples
        )

        save_unchanged(OUT / filename, content)

    raw_ids = [
        record["scenario_id"]
        for record in raw_cohort
    ]

    curated_ids = [
        record["scenario_id"]
        for record in curated
    ]

    provenance = {
        "status": "EXPERIMENTAL_ONLY_NOT_LEGALLY_APPROVED",
        "seed": SEED,
        "examples_per_cohort": TARGET,
        "generation_pool": "frozen_original_400",
        "generation_recipe_matched": True,
        "task_quotas": dict(actual_quotas),
        "raw_ids": raw_ids,
        "curated_ids": curated_ids,
        "overlapping_ids": sorted(
            set(raw_ids) & set(curated_ids)
        ),
        "raw_dataset_sha256": sha256(RAW),
        "evaluation_sha256": sha256(EVAL),
        "v2_scores_sha256": sha256(SCORES),
        "human_review_sha256": sha256(REVIEWS),
        "training_approval_granted": False,
        "limitations": [
            "Full agreements are underrepresented.",
            "Automated screening is not legal certification.",
            "Calibration examples informed V2 scorer design.",
            "Raw and curated cohorts may overlap.",
        ],
    }

    save_unchanged(
        OUT / "cohort_manifest.json",
        json.dumps(
            provenance,
            indent=2
        ) + "\n"
    )

    print("=" * 65)
    print("CURATELAW — FIRST FINE-TUNING DATASETS")
    print("=" * 65)

    print("Raw examples:", len(raw_cohort))
    print("Curated examples:", len(curated))
    print("Matched task quotas:", dict(actual_quotas))

    print(
        "Overlapping scenario IDs:",
        len(provenance["overlapping_ids"])
    )

    print("\nFiles:")
    for filename in files:
        print(" ", OUT / filename)

    print(" ", OUT / "cohort_manifest.json")

    print("\nFrozen original 400: unchanged")
    print("Held-out evaluation 40: unchanged")
    print("Training approval: not granted")
    print("Ready for AlignTune format/config validation.")


if __name__ == "__main__":
    main()
