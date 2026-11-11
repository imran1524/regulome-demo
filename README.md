# Regulome AI: evidence-layer prototype (synthetic data)

Shows three things for investors and design partners:
1. Ranked non-coding candidates, adjustable by cell context and evidence weights.
2. A per-variant evidence record with provenance and a reviewer decision (downloadable JSON).
3. A "what changed" view: same case re-run on a new score release, showing which rankings moved and why.
A fourth tab computes top-k recall from your own benchmark results CSV.
A fifth tab exports a machine-verifiable evidence bundle and verifies bundles.

ALL DATA IS SYNTHETIC. Research use only. No patient data. No clinical claims.

## Run locally
    pip install -r requirements.txt
    streamlit run app.py

## Deploy free
- Streamlit Community Cloud: push this folder to a public GitHub repo, then deploy app.py.
- Hugging Face Spaces: create a Streamlit Space and upload these files.
Check each service's current free-tier limits and terms.

## Moving to real data (licence guardrails)
- Baseline: open-source Exomiser/Genomiser output.
- Scores: only the AVI static download that DeepMind lists as permissive-use for commercial use.
  Do NOT use the Atlas API/portal, splicing scores, feature attributions or model weights
  as a company; those are non-commercial. Confirm in writing with Google.
- Replace the loaders in data.py; keep the evidence-record fields.

## Reproducibility checks (new)
- `bundle.py` builds evidence bundles: inputs, hashes of source data and scoring code, results, reviewer decisions.
- `verify_bundle.py bundle.json` verifies one from the command line (exit 0 = verified, 1 = failed).
- Verification does two things: integrity (hashes match) and replay (re-running the inputs gives identical results).
  Replay catches someone who edits results AND recomputes the hash.
- `test_replay.py` pins determinism: same hashes across repeats, processes and hash seeds; timestamp and key order do
  not change results; edits, moved reviews and changed data are detected.
- `golden.json` pins the expected hashes. If it fails, either results stopped being reproducible or you changed
  `data.py` on purpose: then run `python update_golden.py` and review the diff.

Limits: hashes make edits evident, not impossible, and say nothing about scientific validity. Signing is a later step.

## Test
    python -m pytest -q
