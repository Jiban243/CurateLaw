import json
import hashlib
import re
from pathlib import Path
from collections import Counter

base = Path("data/m2")
output = base / "evaluation/heldout_eval_040.jsonl"
manifest_path = base / "evaluation/heldout_eval_manifest.json"

cases = []

def add(task_type, instruction, input_text="", expected=None):
    cases.append({
        "scenario_id": f"EVAL{len(cases) + 1:03d}",
        "task_type": task_type,
        "instruction": instruction,
        "input": input_text,
        "expected_facts": expected or {},
        "origin": "independently_authored_fictional_brief",
        "split": "heldout_evaluation",
        "training_excluded": True,
        "human_verified": False
    })

full = [
    ("Frontend Engineer", "Gujarat", 1100000, "hybrid", 4, 45),
    ("Site Reliability Engineer", "Karnataka", 2100000, "remote", 5, 60),
    ("Product Designer", "Maharashtra", 1400000, "on-site", 3, 30),
    ("Mobile Developer", "West Bengal", 1500000, "hybrid", 6, 45),
    ("Security Analyst", "Telangana", 1900000, "on-site", 4, 60),
    ("Technical Writer", "Tamil Nadu", 900000, "remote", 2, 30),
    ("Cloud Engineer", "Rajasthan", 1600000, "hybrid", 3, 45),
    ("Database Administrator", "Kerala", 1350000, "remote", 5, 60)
]

for role, state, salary, mode, probation, notice in full:
    add(
        "full_agreement",
        (
            f"Prepare an illustrative Indian employment agreement for a "
            f"{role} employed in {state}. The annual fixed salary is "
            f"INR {salary}; the arrangement is {mode}; the scheduled week "
            f"is 40 hours; probation is {probation} months; and mutual "
            f"contractual notice is {notice} days, subject to applicable "
            f"law. Use party placeholders. Cover appointment, duties, "
            f"location, salary, leave, applicable statutory benefits, "
            f"confidentiality, work-related IP, workplace conduct, "
            f"termination, disputes and signatures. Do not invent "
            f"statutory entitlements or impose a post-employment non-compete."
        ),
        expected={
            "role": role,
            "state": state,
            "salary_inr": salary,
            "work_mode": mode,
            "hours_per_week": 40,
            "probation_months": probation,
            "notice_days": notice
        }
    )

clauses = [
    ("Draft a probation clause for a Pune UX researcher: three months initially, extendable once by at most one month after written notice.", {"initial_months": 3, "extension_months": 1}),
    ("Draft a confidentiality clause for a fictional Bengaluru software startup. Exclude public information and lawfully required disclosures.", {"exceptions": ["public information", "lawful disclosure"]}),
    ("Draft a work-related intellectual-property clause for a Hyderabad developer. Avoid claiming ownership of unrelated personal projects.", {"scope": "work-related creations"}),
    ("Draft a working-hours clause for a Chennai technical support employee: 40 scheduled hours weekly, subject to applicable working-time law.", {"weekly_hours": 40}),
    ("Draft a mutual termination-notice clause for a Jaipur analyst: 45 days, subject to applicable law, with no automatic penalty.", {"notice_days": 45}),
    ("Draft a workplace grievance-reporting clause for a Kochi engineer. Include a reporting channel and prohibit retaliation.", {"required": ["reporting channel", "non-retaliation"]}),
    ("Draft an annual leave clause for a fictional technology employee with 22 contractual leave days, subject to any higher applicable entitlement.", {"contractual_leave_days": 22}),
    ("Draft a remote-work clause for a Kolkata developer working remotely four days weekly and in the office one day.", {"remote_days": 4, "office_days": 1})
]

for instruction, facts in clauses:
    add("clause_drafting", instruction, expected=facts)

custom = [
    ("Change only the annual salary to INR 1120000.", "The Employee will receive a fixed annual salary of INR 950000, payable monthly.", {"new_salary_inr": 1120000}),
    ("Change the working arrangement to hybrid: three office days and two remote days.", "The Employee shall work on-site five days per week.", {"office_days": 3, "remote_days": 2}),
    ("Change the mutual notice period to 30 days.", "Either Party may terminate employment by giving 45 days of written notice, subject to applicable law.", {"notice_days": 30}),
    ("Change the position to Machine Learning Engineer.", "The Employee is appointed as Data Analyst and shall carry out assigned analytical duties.", {"role": "Machine Learning Engineer"}),
    ("Change probation to three months and preserve the written-extension requirement.", "The initial probation period is six months and may be extended only after written notice.", {"probation_months": 3}),
    ("Change the normal work location to Ahmedabad.", "The Employee's normal place of work shall be Jaipur, subject to agreed remote-work arrangements.", {"location": "Ahmedabad"}),
    ("Change the scheduled working week to 40 hours, subject to applicable law.", "The normal scheduled working week shall comprise 48 hours.", {"hours_per_week": 40}),
    ("Change the contractual annual leave allocation to 22 days, subject to applicable law.", "The Employee shall receive 18 days of annual contractual leave.", {"leave_days": 22})
]

for instruction, input_text, facts in custom:
    add(
        "contract_customization",
        "Revise the supplied fictional clause. " + instruction
        + " Return only the revised clause without unrelated additions.",
        input_text,
        facts
    )

repairs = [
    ("The annual fixed salary is INR 1200000 (thirteen lakh rupees).", "Correct the amount to INR 1300000 consistently.", {"salary_inr": 1300000}),
    ("Probation is three (6) months from joining.", "Correct the inconsistency to three months.", {"probation_months": 3}),
    ("The agreed notice is 30 days. The notice provision later specifies 45 days.", "Make both references 30 days.", {"notice_days": 30}),
    ("The Employee is appointed as a Data Engineer. The duties section calls the role UX Designer.", "Make the role consistently Data Engineer.", {"role": "Data Engineer"}),
    ("The Employee is fully remote. The Employee must attend the office every weekday.", "Use the agreed hybrid schedule of three office days and two remote days.", {"office_days": 3, "remote_days": 2}),
    ("The weekly schedule is 40 hours. Another section says that normal weekly hours are 48.", "Correct the schedule consistently to 40 hours, subject to law.", {"hours_per_week": 40}),
    ("The Employee receives 20 annual contractual leave days. A later clause specifies 15 days.", "Use 20 days consistently, subject to any applicable higher entitlement.", {"leave_days": 20}),
    ("The normal office location is Chennai. The relocation section mistakenly identifies Pune as the current office.", "The agreed current office is Chennai. Correct the inconsistency.", {"location": "Chennai"})
]

for input_text, instruction, facts in repairs:
    add(
        "contradiction_correction",
        "Identify and correct the internal inconsistency in this fictional draft. "
        + instruction + " Return the corrected wording.",
        input_text,
        facts
    )

missing = [
    ("An Ahmedabad backend engineer is offered INR 1550000 fixed annually. Supply only the missing compensation clause.", {"salary_inr": 1550000}),
    ("A Bengaluru QA lead has a four-month probation term, extendable by one month with advance written notice. Supply only the probation clause.", {"probation_months": 4, "extension_months": 1}),
    ("A Delhi systems analyst has a mutual contractual notice period of 60 days, subject to applicable law. Supply only the notice clause.", {"notice_days": 60}),
    ("A Pune data engineer is responsible for data pipelines, monitoring and documentation. Supply only the duties clause.", {"duties": ["pipelines", "monitoring", "documentation"]}),
    ("A Hyderabad developer works remotely three days and from the office two days weekly. Supply only the workplace clause.", {"remote_days": 3, "office_days": 2}),
    ("A Chennai product analyst handles confidential commercial information. Add only a confidentiality clause with lawful-disclosure exceptions.", {"exception": "lawful disclosure"}),
    ("A Mumbai engineer develops work-related software. Add only an IP clause with clear scope and no claim over unrelated pre-existing personal projects.", {"scope": "work-related IP"}),
    ("An illustrative Indian employment agreement lacks execution fields. Supply only an execution/signature section for employer and employee.", {"parties": ["employer", "employee"]})
]

for instruction, facts in missing:
    add("missing_clause_completion", instruction, expected=facts)

if len(cases) != 40:
    raise ValueError(f"Expected 40 cases, got {len(cases)}")

if len({case["scenario_id"] for case in cases}) != 40:
    raise ValueError("Duplicate evaluation IDs")

def normalize(text):
    return re.sub(r"\s+", " ", text).strip().casefold()

training_path = base / "scenarios/train_seed_005.jsonl"

training_instructions = set()

if training_path.exists():
    for line in training_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            training_instructions.add(
                normalize(json.loads(line)["instruction"])
            )

if any(
    normalize(case["instruction"]) in training_instructions
    for case in cases
):
    raise ValueError("Exact training instruction overlap detected")

if output.exists():
    raise SystemExit(
        f"{output} already exists. Review it rather than overwriting."
    )

output.parent.mkdir(parents=True, exist_ok=True)

with output.open("w", encoding="utf-8") as f:
    for case in cases:
        f.write(json.dumps(case, ensure_ascii=False) + "\n")

digest = hashlib.sha256(output.read_bytes()).hexdigest()

manifest = {
    "dataset": "heldout_eval_040",
    "status": "provisional_pending_human_review",
    "count": len(cases),
    "task_distribution": dict(
        Counter(case["task_type"] for case in cases)
    ),
    "sha256": digest,
    "train_overlap_check": "exact_instruction_only",
    "training_excluded": True,
    "legal_verification_completed": False,
    "gold_reference_answers_available": False
}

manifest_path.write_text(
    json.dumps(manifest, indent=2),
    encoding="utf-8"
)

print("Held-out evaluation cases:", len(cases))
print("Task distribution:")

for task, count in manifest["task_distribution"].items():
    print(task, count)

print("Exact training-prompt overlaps: 0")
print("SHA256:", digest)
print("Evaluation file:", output)
print("Manifest:", manifest_path)
print("Human verification: pending")
