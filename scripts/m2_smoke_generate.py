import json
import os
from getpass import getpass
from pathlib import Path

from huggingface_hub import InferenceClient
from curatorkit import Curator, CuratorConfig

base = Path("data/m2")
seed_path = base / "scenarios/train_seed_005.jsonl"
raw_path = base / "generated_raw/synthetic_smoke_005.jsonl"
curated_dir = base / "curatorkit_smoke"

model = "Qwen/Qwen3-235B-A22B-Instruct-2507"

token = os.environ.get("HF_TOKEN") or getpass(
    "Hugging Face access token (hidden): "
)

client = InferenceClient(
    api_key=token,
    provider="auto"
)

seeds = [
    json.loads(line)
    for line in seed_path.read_text(encoding="utf-8").splitlines()
    if line.strip()
]

existing = set()

if raw_path.exists():
    for line in raw_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            existing.add(json.loads(line)["scenario_id"])

for seed in seeds:
    sid = seed["scenario_id"]

    if sid in existing:
        print("Already generated:", sid)
        continue

    print("Generating:", sid, flush=True)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You draft illustrative Indian employment agreements "
                        "for synthetic-data research. Do not copy source templates. "
                        "Follow the user's specified facts faithfully. "
                        "Do not invent legal entitlements, statutory rules or "
                        "unsupported contractual terms. Output only the draft."
                    )
                },
                {
                    "role": "user",
                    "content": seed["instruction"]
                }
            ],
            temperature=0.4,
            max_tokens=2800
        )

        answer = response.choices[0].message.content

        if not isinstance(answer, str) or len(answer.strip()) < 400:
            print("Invalid or incomplete response:", sid)
            continue

        record = {
            "scenario_id": sid,
            "instruction": seed["instruction"],
            "input": "",
            "output": answer.strip(),
            "generation_model": model,
            "data_origin": "synthetic",
            "legal_review_status": "unverified",
            "approved_for_training": False
        }

        with raw_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

        print("Saved:", sid, "characters:", len(answer))

    except Exception as error:
        print("Generation failed:", sid, type(error).__name__, str(error)[:350])
        break

raw_records = [
    json.loads(line)
    for line in raw_path.read_text(encoding="utf-8").splitlines()
    if line.strip()
] if raw_path.exists() else []

print("\nRaw synthetic pairs:", len(raw_records))

if not raw_records:
    raise SystemExit("No synthetic pairs generated; curation skipped.")

print("\nRunning CuratorKIT ingestion and hygiene test")

result = Curator(CuratorConfig(
    dataset=str(raw_path),
    name="curatelaw_m2_smoke",
    dedup="exact",
    clean=True,
    schema_gate=True,
    min_tokens=5,
    max_tokens=6000,
    export_formats=["alpaca"],
    output_dir=str(curated_dir)
)).run()

result.print_summary()

print("Raw synthetic pool:", raw_path)
print("CuratorKIT output:", curated_dir / "sft_alpaca.jsonl")
print("CuratorKIT manifest:", curated_dir / "manifest.json")
print("Training approval: pending further quality and legal review")
