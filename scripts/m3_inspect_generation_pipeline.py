
import ast
import json
from collections import Counter
from pathlib import Path


ROOT = Path(".")
RAW = ROOT / "data/m2/frozen/pool_raw_0400.jsonl"
SCENARIO_DIR = ROOT / "data/m2/scenarios"
SCRIPT_DIR = ROOT / "scripts"

GENERATOR = SCRIPT_DIR / "m2_generate_batch.py"


def read_jsonl(path):
    with path.open(encoding="utf-8") as file:
        return [
            json.loads(line)
            for line in file
            if line.strip()
        ]


def inspect_generator(path):
    print("\nEXISTING GENERATOR")

    if not path.is_file():
        print("Generator not found:", path)
        return

    source = path.read_text(encoding="utf-8")

    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        print("Cannot parse generator:", exc)
        return

    functions = []
    arguments = []
    imported_modules = []

    for node in ast.walk(tree):
        if isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef)
        ):
            functions.append(node.name)

        if isinstance(node, ast.Import):
            imported_modules.extend(
                alias.name
                for alias in node.names
            )

        if isinstance(node, ast.ImportFrom):
            if node.module:
                imported_modules.append(node.module)

        if not isinstance(node, ast.Call):
            continue

        if not isinstance(node.func, ast.Attribute):
            continue

        if node.func.attr != "add_argument":
            continue

        for arg in node.args:
            if isinstance(arg, ast.Constant):
                value = arg.value

                if (
                    isinstance(value, str)
                    and value.startswith("--")
                ):
                    arguments.append(value)

    relevant_imports = sorted({
        module
        for module in imported_modules
        if any(
            keyword in module.lower()
            for keyword in [
                "huggingface",
                "groq",
                "openai",
                "dotenv",
                "argparse",
            ]
        )
    })

    print("Path:", path)
    print("Functions:", sorted(set(functions)))
    print("CLI options:", sorted(set(arguments)))
    print("Relevant imports:", relevant_imports)

    print(
        "Uses Hugging Face InferenceClient:",
        "InferenceClient" in source
    )

    print(
        "Uses resumable generation:",
        any(
            word in source.lower()
            for word in [
                "resume",
                "existing_ids",
                "completed_ids",
                "already_done",
            ]
        )
    )


def inspect_scenarios(folder):
    print("\nEXISTING SCENARIO FILES")

    if not folder.is_dir():
        print("Scenario directory not found:", folder)
        return

    files = sorted(
        folder.rglob("*.jsonl")
    )

    if not files:
        print("No JSONL scenario files found.")
        return

    for path in files[:20]:
        try:
            records = read_jsonl(path)
        except (OSError, ValueError) as exc:
            print(path, "READ ERROR:", exc)
            continue

        print("\nFile:", path)
        print("Records:", len(records))

        if not records:
            continue

        first = records[0]

        if not isinstance(first, dict):
            print("First record is not an object.")
            continue

        print("Fields:", sorted(first.keys()))

        task_distribution = Counter(
            str(record.get("task_type", "unknown"))
            for record in records
            if isinstance(record, dict)
        )

        print(
            "Task distribution:",
            dict(task_distribution)
        )

        full = next(
            (
                record
                for record in records
                if isinstance(record, dict)
                and record.get("task_type")
                == "full_agreement"
            ),
            None
        )

        if full:
            print(
                "Sample full-agreement scenario ID:",
                full.get("scenario_id")
            )

            print(
                "Sample full-agreement fields:",
                sorted(full.keys())
            )


def inspect_raw(path):
    print("FROZEN GENERATION DATA")

    if not path.is_file():
        raise SystemExit(
            f"Frozen dataset missing: {path}"
        )

    rows = read_jsonl(path)

    if len(rows) != 400:
        raise SystemExit(
            f"Expected 400 examples, found {len(rows)}."
        )

    print("Total:", len(rows))

    print(
        "Task distribution:",
        dict(Counter(
            row.get("task_type")
            for row in rows
        ))
    )

    full = next(
        row for row in rows
        if row.get("task_type") == "full_agreement"
    )

    print(
        "Generated record fields:",
        sorted(full.keys())
    )

    print(
        "Sample ID:",
        full.get("scenario_id")
    )

    print(
        "Sample task:",
        full.get("task_type")
    )

    print(
        "Sample instruction:",
        full.get("instruction", "")
    )

    print(
        "Expected-facts structure:",
        full.get("expected_facts", "not present")
    )

    print(
        "Generation metadata fields:",
        sorted(
            key for key in full
            if any(
                word in key.lower()
                for word in [
                    "model",
                    "token",
                    "provider",
                    "finish",
                    "status",
                    "generation",
                ]
            )
        )
    )


def main():
    print("=" * 65)
    print("CURATELAW — SUPPLEMENTAL GENERATION READINESS")
    print("=" * 65)

    inspect_raw(RAW)
    inspect_generator(GENERATOR)
    inspect_scenarios(SCENARIO_DIR)

    print("\nNEXT DATASET REQUIREMENTS")
    print("Original frozen raw examples: 400")
    print("Existing full agreements: 120")
    print("V2 provisional strong full agreements: 14")
    print("Full-agreement training quota: 45")
    print("Minimum provisional shortfall: 31")

    print("\nNo files modified.")
    print("No model API calls.")
    print("No inference credits consumed.")


if __name__ == "__main__":
    main()
