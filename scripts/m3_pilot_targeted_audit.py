
import json
import re
from pathlib import Path

from m3_score_v2 import numbered_sections


ROOT = Path(__file__).resolve().parents[1]

GENERATED = (
    ROOT / "data/m3/supplemental/generated_raw.jsonl"
)

REQUIRED_PLACEHOLDERS = [
    "[Date]",
    "[Joining Date]",
    "[Employer Name]",
    "[Employee Name]",
    "[Employer Address]",
    "[Employee Address]",
]

PILOT_IDS = [
    f"SUP{i:04d}"
    for i in range(1, 6)
]


def read_jsonl(path):
    with path.open(
        encoding="utf-8"
    ) as file:
        return [
            json.loads(line)
            for line in file
            if line.strip()
        ]


def extract_excerpt(text, pattern, width=240):
    matches = []

    for match in re.finditer(
        pattern,
        text,
        re.I
    ):
        start = max(
            0,
            match.start() - 90
        )

        end = min(
            len(text),
            match.end() + width
        )

        excerpt = " ".join(
            text[start:end].split()
        )

        if excerpt not in matches:
            matches.append(excerpt)

    return matches[:3]


def show_section(sections, number, limit=700):
    entry = sections.get(number)

    if not entry:
        print(
            f"Section {number}: NOT DETECTED"
        )
        return

    title, body = entry

    print(
        f"\nSECTION {number}: {title}"
    )

    print(
        body.strip()[:limit]
        or "(empty section)"
    )


def audit(record):
    sid = record["scenario_id"]
    output = record["output"]
    facts = record["expected_facts"]

    sections = numbered_sections(output)

    print("\n" + "=" * 70)
    print("TARGETED AUDIT:", sid)
    print("=" * 70)

    print(
        "\nExpected facts:",
        json.dumps(
            facts,
            ensure_ascii=False
        )
    )

    print(
        "\nGenerated words:",
        len(output.split())
    )

    print(
        "Numbered sections:",
        len(sections)
    )

    missing = [
        placeholder
        for placeholder in REQUIRED_PLACEHOLDERS
        if placeholder.casefold()
        not in output.casefold()
    ]

    print(
        "Missing exact placeholders:",
        missing or "None"
    )

    print("\nSECTION HEADINGS:")

    for number, (title, _) in sorted(
        sections.items()
    ):
        print(
            f"  {number}. {title}"
        )

    print("\nCROSS-REFERENCES:")

    references = re.findall(
        r"\b(?:Section|Clause)\s+(\d{1,2})\b",
        output,
        re.I
    )

    if not references:
        print("  None")
    else:
        for target in sorted(
            set(map(int, references))
        ):
            if target in sections:
                heading = sections[target][0]
                status = f"exists: {heading}"
            else:
                status = "MISSING TARGET"

            print(
                f"  Reference to {target}: {status}"
            )

    print("\nADDITIONAL TERMINATION CONDITIONS:")

    patterns = {
        "garden_leave": (
            r"garden leave|"
            r"remain away from work|"
            r"not to report to work|"
            r"away from work duties"
        ),
        "salary_in_lieu": (
            r"salary in lieu|"
            r"payment in lieu|"
            r"pay in lieu"
        ),
        "termination_without_reason": (
            r"without assigning"
            r"(?: any)? reason"
        ),
        "probation_extension": (
            r"extend.{0,70}probation|"
            r"probation.{0,90}extend"
        ),
    }

    for label, pattern in patterns.items():
        excerpts = extract_excerpt(
            output,
            pattern
        )

        if not excerpts:
            print(
                f"  {label}: not detected"
            )
            continue

        print(
            f"\n  {label}:"
        )

        for excerpt in excerpts:
            print(
                "   ",
                excerpt
            )

    print("\nKEY SECTIONS:")

    for section_number, limit in [
        (1, 450),
        (5, 450),
        (6, 650),
        (8, 450),
        (9, 550),
        (13, 850),
        (16, 450),
    ]:
        show_section(
            sections,
            section_number,
            limit
        )


def main():
    if not GENERATED.is_file():
        raise SystemExit(
            f"Missing generated data: {GENERATED}"
        )

    rows = read_jsonl(GENERATED)

    index = {}

    for row in rows:
        sid = row["scenario_id"]

        if sid in index:
            raise SystemExit(
                f"Duplicate generated ID: {sid}"
            )

        index[sid] = row

    missing = [
        sid
        for sid in PILOT_IDS
        if sid not in index
    ]

    if missing:
        raise SystemExit(
            f"Missing pilot examples: {missing}"
        )

    print("=" * 70)
    print("M3.5.3 SUPPLEMENTAL PILOT TARGETED AUDIT")
    print("=" * 70)

    for sid in PILOT_IDS:
        audit(index[sid])

    print("\n" + "=" * 70)
    print("AUDIT COMPLETED")
    print("=" * 70)

    print("Examples inspected:", len(PILOT_IDS))
    print("Existing files modified: 0")
    print("API calls: 0")
    print("Training approvals: unchanged")


if __name__ == "__main__":
    main()
