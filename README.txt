CurateLaw-India M2 generation batch

Copy both .py files from the scripts folder into your existing project's scripts folder. Run these commands from your project root:

python scripts/m2_prepare_training_pool.py
python scripts/m2_generate_batch.py --limit 10

The first command creates 400 original instruction-only training-generation scenarios, distributed across five task types. It verifies the held-out evaluation SHA-256, checks exact prompt overlap and refuses to overwrite a prior pool.

The second command makes at most 10 new teacher-model calls. It is resumable and saves each response immediately to data/m2/generated_raw/pool_raw.jsonl. This is a raw, unfiltered synthetic response pool. You can repeat later with --limit 10 or --limit 25 after checking your available credits.

Hugging Face Inference Providers may bill your account for generation. Do not paste an access token into chat; the script accepts HF_TOKEN or asks for a hidden token at runtime.

The held-out evaluation dataset remains completely separate from synthetic training. Neither these scripts nor the raw pool constitutes legal verification, permission clearance, or approval for deployment.
