
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path("data")

RAW = ROOT / "m2/frozen/pool_raw_0400.jsonl"
FREEZE = ROOT / "m2/frozen/freeze_manifest.json"

V1 = ROOT / "m3/domain_curation/M3_DOMAIN_SCORES.csv"
V2 = ROOT / "m3/domain_curation_v2/M3_DOMAIN_SCORES_V2.csv"

CALIBRATION = (
    ROOT
    / "m3/provisional_cohorts/M3_CALIBRATION_HUMAN_REVIEW.csv"
)

OUT = ROOT / "m3/v2_diagnostics"

REPORT = OUT / "M3_V2_FULL_AGREEMENT_DIAGNOSTIC.md"
DETAILS = OUT / "M3_V2_FULL_AGREEMENT_DIAGNOSTIC.csv"
SUMMARY = OUT / "M3_V2_DIAGNOSTIC_SUMMARY.json"

TARGET_FULL_AGREEMENTS = 45


def read_csv(path):
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def read_jsonl(path):
    with path.open("r", encoding="utf-8") as f:
        return [
            json.loads(line)
            for line in f
            if line.strip()
        ]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_index(rows, label):
    result = {}

    for row in rows:
        sid = row["scenario_id"]

        if sid in result:
            raise ValueError(
                f"Duplicate ID in {label}: {sid}"
            )

        result[sid] = row

    return result


def split_reasons(value):
    return [
        item.strip()
        for item in str(value or "").split(";")
        if item.strip()
    ]


def detect_numbered_headings(text):
    pattern = re.compile(
        r"(?m)^\s*"
        r"(?:#{1,6}\s*)?"
        r"(?:\*\*|__)?"
        r"(\d{1,2})\s*[.)]"
    )

    return [
        int(match.group(1))
        for match in pattern.finditer(text)
    ]


def get_context(text, reason):
    patterns = {
        "salary": r"INR|salary|compensation",
        "notice": r"notice|termination|in lieu",
        "probation": r"probation|extend",
        "cross_reference": r"clause\s+\d+|section\s+\d+",
        "industrial_disputes": r"industrial disputes",
        "role": r"appointed|appointment|role",
        "numbered_sections": r"^\s*(?:#{1,6}\s*)?\*?\*?\d+[.)]",
        "working": r"hours|working time",
        "signature": r"signature|signatory|witness",
    }

    selected_pattern = None

    for keyword, pattern in patterns.items():
        if keyword in reason.lower():
            selected_pattern = pattern
            break

    if selected_pattern is None:
        selected_pattern = (
            r"probation|notice|salary|appointment|"
            r"workplace|termination"
        )

    lines = text.splitlines()
    matches = []

    for number, line in enumerate(lines):
        if re.search(
            selected_pattern,
            line,
            re.I
        ):
            start = max(0, number - 1)
            end = min(len(lines), number + 3)

            excerpt = "\n".join(
                lines[start:end]
            ).strip()

            if excerpt:
                matches.append(excerpt)

        if len(matches) >= 2:
            break

    if not matches:
        return text[:500].strip()

    return "\n\n".join(matches)[:850]


def main():
    inputs = [
        RAW,
        FREEZE,
        V1,
        V2,
        CALIBRATION,
    ]

    for path in inputs:
        if not path.is_file():
            raise FileNotFoundError(
                f"Required file not found: {path}"
            )

    manifest = json.loads(
        FREEZE.read_text(encoding="utf-8")
    )

    if sha256(RAW) != manifest["raw_sha256"]:
        raise ValueError(
            "Frozen raw dataset hash mismatch."
        )

    raw = make_index(
        read_jsonl(RAW),
        "frozen raw dataset"
    )

    old = make_index(
        read_csv(V1),
        "V1 scores"
    )

    new = make_index(
        read_csv(V2),
        "V2 scores"
    )

    calibrated = make_index(
        read_csv(CALIBRATION),
        "human calibration"
    )

    if not (
        len(raw) == 400
        and len(old) == 400
        and len(new) == 400
        and len(calibrated) == 27
    ):
        raise ValueError(
            "Unexpected dataset or report sizes."
        )

    if set(raw) != set(old) or set(raw) != set(new):
        raise ValueError(
            "Raw, V1 and V2 scenario IDs differ."
        )

    full_ids = sorted(
        sid
        for sid, record in raw.items()
        if record["task_type"] == "full_agreement"
    )

    if len(full_ids) != 120:
        raise ValueError(
            f"Expected 120 full agreements, "
            f"found {len(full_ids)}."
        )

    tier_counts_v1 = Counter()
    tier_counts_v2 = Counter()
    transitions = Counter()

    reason_counts = {
        "hard": Counter(),
        "review": Counter(),
        "legal": Counter(),
    }

    single_blocker_counts = Counter()
    reason_examples = {}

    details = []

    for sid in full_ids:
        source = raw[sid]
        previous = old[sid]
        current = new[sid]

        tier_v1 = previous["screening_tier"]
        tier_v2 = current["screening_tier_v2"]

        hard = split_reasons(
            current["hard_failure_reasons_v2"]
        )

        review = split_reasons(
            current["review_reasons_v2"]
        )

        legal = split_reasons(
            current["legal_review_reasons_v2"]
        )

        tier_counts_v1[tier_v1] += 1
        tier_counts_v2[tier_v2] += 1
        transitions[(tier_v1, tier_v2)] += 1

        all_reasons = (
            [("hard", r) for r in hard]
            + [("review", r) for r in review]
            + [("legal", r) for r in legal]
        )

        for category, reason in all_reasons:
            reason_counts[category][reason] += 1

            key = f"{category}:{reason}"

            reason_examples.setdefault(key, [])

            if len(reason_examples[key]) < 3:
                reason_examples[key].append(sid)

        if len(all_reasons) == 1:
            category, reason = all_reasons[0]
            single_blocker_counts[
                f"{category}:{reason}"
            ] += 1

        response = str(
            source.get("output", "")
        )

        headings = detect_numbered_headings(
            response
        )

        decision = calibrated.get(
            sid,
            {}
        ).get(
            "human_decision",
            "not_calibrated"
        )

        details.append({
            "scenario_id": sid,
            "tier_v1": tier_v1,
            "tier_v2": tier_v2,
            "v2_score": current[
                "quality_score_heuristic_v2"
            ],
            "human_decision": decision,
            "word_count": len(
                response.split()
            ),
            "detectable_numbered_headings": len(
                headings
            ),
            "hard_reasons": ";".join(hard),
            "review_reasons": ";".join(review),
            "legal_reasons": ";".join(legal),
        })

    strong = tier_counts_v2[
        "strong_screening_candidate"
    ]

    shortfall = max(
        0,
        TARGET_FULL_AGREEMENTS - strong
    )

    total_changed = sum(
        count
        for (before, after), count
        in transitions.items()
        if before != after
    )

    ranked_reasons = sorted(
        (
            (
                category,
                reason,
                count
            )
            for category, counter
            in reason_counts.items()
            for reason, count
            in counter.items()
        ),
        key=lambda item: (
            -item[2],
            item[0],
            item[1]
        )
    )

    OUT.mkdir(
        parents=True,
        exist_ok=True
    )

    with DETAILS.open(
        "w",
        encoding="utf-8",
        newline=""
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=list(details[0])
        )

        writer.writeheader()
        writer.writerows(details)

    summary = {
        "full_agreements": len(full_ids),
        "v1_tiers": dict(tier_counts_v1),
        "v2_tiers": dict(tier_counts_v2),
        "changed_tiers": total_changed,
        "curated_full_agreement_target": (
            TARGET_FULL_AGREEMENTS
        ),
        "provisional_strong_shortfall": shortfall,
        "reason_counts": {
            category: dict(counter)
            for category, counter
            in reason_counts.items()
        },
        "single_blocker_counts": dict(
            single_blocker_counts
        ),
        "frozen_raw_sha256": sha256(RAW),
        "v1_sha256": sha256(V1),
        "v2_sha256": sha256(V2),
        "calibration_sha256": sha256(
            CALIBRATION
        ),
        "training_approved": False,
    }

    SUMMARY.write_text(
        json.dumps(
            summary,
            indent=2,
            ensure_ascii=False
        ) + "\n",
        encoding="utf-8"
    )

    lines = [
        "# M3.5.1 — V2 Full Agreement Diagnostic",
        "",
        "## Capacity",
        "",
        f"- Total full agreements: {len(full_ids)}",
        f"- V2 strong candidates: {strong}",
        f"- Target: {TARGET_FULL_AGREEMENTS}",
        f"- Shortfall: {shortfall}",
        f"- V1-to-V2 tier changes: {total_changed}",
        "",
        "## Screening tiers",
        "",
        "| Tier | V1 | V2 |",
        "|---|---:|---:|",
    ]

    for tier in [
        "strong_screening_candidate",
        "hold_manual_review",
        "exclude_provisional",
    ]:
        lines.append(
            f"| `{tier}` | "
            f"{tier_counts_v1[tier]} | "
            f"{tier_counts_v2[tier]} |"
        )

    lines.extend([
        "",
        "## V1 to V2 transitions",
        "",
        "| V1 tier | V2 tier | Count |",
        "|---|---|---:|",
    ])

    for (before, after), count in sorted(
        transitions.items(),
        key=lambda item: -item[1]
    ):
        lines.append(
            f"| `{before}` | `{after}` | {count} |"
        )

    lines.extend([
        "",
        "## Most frequent V2 flags",
        "",
        "| Category | Flag | Agreements |",
        "|---|---|---:|",
    ])

    for category, reason, count in ranked_reasons:
        lines.append(
            f"| {category} | `{reason}` | {count} |"
        )

    lines.extend([
        "",
        "## Single-blocker cases",
        "",
        "A single-blocker case has exactly one "
        "V2 hard, review or legal flag.",
        "",
        "| Flag | Agreements |",
        "|---|---:|",
    ])

    for reason, count in single_blocker_counts.most_common():
        lines.append(
            f"| `{reason}` | {count} |"
        )

    lines.extend([
        "",
        "## Representative flagged examples",
        "",
        "These examples are for diagnostic inspection. "
        "They have not been newly human-approved.",
        "",
    ])

    for category, reason, count in ranked_reasons[:10]:
        key = f"{category}:{reason}"

        lines.append(
            f"### {category}: {reason} ({count})"
        )
        lines.append("")

        candidates = reason_examples.get(
            key,
            []
        )

        candidates.sort(
            key=lambda sid: (
                sid in calibrated,
                sid
            )
        )

        for sid in candidates[:2]:
            record = raw[sid]

            lines.append(
                f"**{sid}** — "
                f"V2 `{new[sid]['screening_tier_v2']}`"
            )

            lines.append("")
            lines.append(
                "**Instruction:** "
                + record["instruction"]
            )
            lines.append("")
            lines.append("**Relevant response excerpt:**")
            lines.append("")
            lines.append("```text")
            lines.append(
                get_context(
                    record["output"],
                    reason
                )
            )
            lines.append("```")
            lines.append("")

    lines.extend([
        "## Interpretation",
        "",
        "Counts describe automatic flag occurrences. "
        "They do not establish that all flags are correct.",
        "",
        "The next step is to inspect representative "
        "cases, fix demonstrable parser or rule errors, "
        "and separately resolve genuinely questionable "
        "contractual or legal provisions.",
        "",
        "Original scores, datasets and human annotations "
        "were not modified.",
        "",
    ])

    REPORT.write_text(
        "\n".join(lines),
        encoding="utf-8"
    )

    print("=" * 65)
    print("M3.5.1 V2 FULL AGREEMENT DIAGNOSTIC")
    print("=" * 65)

    print("Full agreements:", len(full_ids))
    print("V1 tiers:", dict(tier_counts_v1))
    print("V2 tiers:", dict(tier_counts_v2))
    print("V1/V2 tier changes:", total_changed)

    print(
        "Provisional strong shortfall:",
        shortfall
    )

    print("\nMost frequent V2 flags:")

    for category, reason, count in ranked_reasons[:15]:
        print(
            f"  {category}: {reason} = {count}"
        )

    print("\nSingle-blocker cases:")

    for reason, count in single_blocker_counts.most_common(10):
        print(
            f"  {reason} = {count}"
        )

    print("\nRepresentative example IDs:")

    for category, reason, count in ranked_reasons[:8]:
        key = f"{category}:{reason}"

        print(
            f"  {reason}: "
            f"{reason_examples.get(key, [])}"
        )

    print("\nGenerated reports:")
    print(" ", REPORT)
    print(" ", DETAILS)
    print(" ", SUMMARY)

    print("\nOriginal datasets: unchanged")
    print("Training approvals: 0")


if __name__ == "__main__":
    main()
