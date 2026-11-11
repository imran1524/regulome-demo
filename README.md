# Regulome AI: evidence-layer prototype (synthetic data)

Shows three things for investors and design partners:
1. Ranked non-coding candidates, adjustable by cell context and evidence weights.
2. A per-variant evidence record with provenance and a reviewer decision (downloadable JSON).
3. A "what changed" view: same case re-run on a new score release, showing which rankings moved and why.
A fourth tab computes top-k recall from your own benchmark results CSV.

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
