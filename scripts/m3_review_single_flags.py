
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path("data")

RAW = ROOT / "m2/frozen/pool_raw_0400.jsonl"
FREEZE = ROOT / "m2/frozen/freeze_manifest.json"

V2 = (
    ROOT / "m3/domain_curation_v2/M3_DOMAIN_SCORES_V2.csv"
)

CALIBRATION = (
    ROOT / "m3/provisional_cohorts/"
    "M3_CALIBRATION_HUMAN_REVIEW.csv"
)

OUTPUT = (
    ROOT / "m3/v2_diagnostics/"
    "M3_SINGLE_FLAG_FULL_AGREEMENTS.csv"
)

TARGET_FLAGS = [
    "probation_notice_exception_requires_review",
    "employer_only_notice_pay_option_review",
    "unrequested_probation_extension",
]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path):
    with path.open(
        encoding="utf-8",
        newline=""
    ) as file:
        return list(csv.DictReader(file))


def read_jsonl(path):
    with path.open(encoding="utf-8") as file:
        return [
            json.loads(line)
            for line in file
            if line.strip()
        ]


def split_flags(value):
    return [
        item.strip()
        for item in str(value or "").split(";")
        if item.strip()
    ]


def extract_sections(text):
    heading_pattern = re.compile(
        r"(?m)^\s*"
        r"(?:#{1,6}\s*)?"
        r"(?:\*\*)?"
        r"(\d{1,2})[.)]\s*"
        r"([^\n]{2,110})"
    )

    matches = list(
        heading_pattern.finditer(text)
    )

    sections = []

    for i, match in enumerate(matches):
        end = (
            matches[i + 1].start()
            if i + 1 < len(matches)
            else len(text)
        )

        heading = match.group(2).strip("* _: ")

        sections.append({
            "number": int(match.group(1)),
            "heading": heading,
            "text": text[match.start():end].strip(),
        })

    return sections


def relevant_excerpt(text, flag):
    sections = extract_sections(text)

    if flag in {
        "probation_notice_exception_requires_review",
        "unrequested_probation_extension",
    }:
        keywords = ["probation", "termination"]

    else:
        keywords = ["termination", "probation"]

    selected = []

    for keyword in keywords:
        match = next(
            (
                section
                for section in sections
                if keyword in section["heading"].lower()
            ),
            None
        )

        if match and match not in selected:
            selected.append(match)

    if selected:
        return "\n\n".join(
            section["text"][:1800]
            for section in selected
        )

    fallback = re.search(
        r"probation|termination|notice",
        text,
        re.I
    )

    if fallback:
        start = max(0, fallback.start() - 200)
        end = min(len(text), fallback.start() + 1800)
        return text[start:end]

    return text[:1800]


def main():
    for path in [
        RAW,
        FREEZE,
        V2,
        CALIBRATION
    ]:
        if not path.exists():
            raise SystemExit(
                f"Missing required file: {path}"
            )

    manifest = json.loads(
        FREEZE.read_text(encoding="utf-8")
    )

    if sha256(RAW) != manifest["raw_sha256"]:
        raise SystemExit("Frozen dataset checksum mismatch.")

    raw_records = read_jsonl(RAW)
    v2_rows = read_csv(V2)
    calibration_rows = read_csv(CALIBRATION)

    raw = {
        row["scenario_id"]: row
        for row in raw_records
    }

    v2 = {
        row["scenario_id"]: row
        for row in v2_rows
    }

    calibrated_ids = {
        row["scenario_id"]
        for row in calibration_rows
    }

    if (
        len(raw_records) != 400
        or len(raw) != 400
        or len(v2_rows) != 400
        or len(v2) != 400
        or len(calibration_rows) != 27
        or len(calibrated_ids) != 27
        or set(raw) != set(v2)
    ):
        raise SystemExit("Unexpected dataset structure.")

    groups = {
        reason: []
        for reason in TARGET_FLAGS
    }

    for sid in sorted(raw):
        record = raw[sid]
        score = v2[sid]

        if record["task_type"] != "full_agreement":
            continue

        flags = (
            split_flags(score["hard_failure_reasons_v2"])
            + split_flags(score["review_reasons_v2"])
            + split_flags(score["legal_review_reasons_v2"])
        )

        if len(flags) != 1:
            continue

        reason = flags[0]

        if reason not in groups:
            continue

        groups[reason].append({
            "scenario_id": sid,
            "flag": reason,
            "v2_tier": score["screening_tier_v2"],
            "v2_score": score["quality_score_heuristic_v2"],
            "previously_calibrated": (
                "yes" if sid in calibrated_ids else "no"
            ),
            "instruction": record["instruction"],
            "input": record.get("input", ""),
            "generated_response": record["output"],
            "human_review_decision": "",
            "human_review_notes": "",
            "approved_for_training": "false",
        })

    all_rows = [
        row
        for reason in TARGET_FLAGS
        for row in groups[reason]
    ]

    if not all_rows:
        raise SystemExit("No matching single-flag examples.")

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with OUTPUT.open(
        "w",
        encoding="utf-8",
        newline=""
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(all_rows[0].keys())
        )

        writer.writeheader()
        writer.writerows(all_rows)

    print("=" * 68)
    print("M3.5.2 — SINGLE-FLAG FULL AGREEMENT INSPECTION")
    print("=" * 68)

    print("\nSingle-flag counts:")

    for flag in TARGET_FLAGS:
        records = groups[flag]

        fresh = sum(
            row["previously_calibrated"] == "no"
            for row in records
        )

        print(
            f"  {flag}: "
            f"{len(records)} total, "
            f"{fresh} not previously calibrated"
        )

    print("\nREPRESENTATIVE EXAMPLES")

    for index, flag in enumerate(TARGET_FLAGS, start=1):
        candidates = [
            row for row in groups[flag]
            if row["previously_calibrated"] == "no"
        ]

        if not candidates:
            print(
                f"\nNo uncalibrated example for {flag}"
            )
            continue

        example = candidates[0]

        print("\n" + "=" * 68)
        print(f"EXAMPLE {index}: {example['scenario_id']}")
        print("=" * 68)

        print("FLAG:", flag)
        print("V2 TIER:", example["v2_tier"])
        print("V2 SCORE:", example["v2_score"])

        print("\nINSTRUCTION:")
        print(example["instruction"])

        print("\nINPUT:")
        print(example["input"] or "(empty)")

        print("\nRELEVANT GENERATED CLAUSES:")
        print(
            relevant_excerpt(
                example["generated_response"],
                flag
            )
        )

    print("\n" + "=" * 68)
    print("Total single-flag examples:", len(all_rows))
    print("Review queue:", OUTPUT)
    print("Existing scores and annotations: unchanged")
    print("Training approvals: unchanged")


if __name__ == "__main__":
    main()
