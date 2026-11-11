import hashlib
import json
from datetime import datetime, timezone

import pandas as pd
import streamlit as st

import bundle
import data

st.set_page_config(page_title="Regulome AI demo", page_icon="🧬", layout="wide")

st.title("Regulome AI: evidence-layer prototype")
st.warning(
    "SYNTHETIC DATA. Genes, variants and scores are invented to show the workflow. "
    "Not real AlphaGenome output, not a benchmark result, research use only, no clinical use."
)

# ---------- Sidebar: inputs ----------
with st.sidebar:
    st.header("Case")
    case_id = st.selectbox("Case", list(data.CASES), format_func=lambda c: data.CASES[c]["title"])
    case = data.CASES[case_id]
    st.caption("Phenotype (HPO): " + "; ".join(case["hpo"]))
    st.caption("Inheritance: " + case["inheritance"])

    cell_type = st.selectbox(
        "Cell context",
        data.CELL_TYPES,
        index=data.CELL_TYPES.index(case["default_cell"]),
    )
    snapshot = st.selectbox(
        "Score snapshot",
        list(data.SNAPSHOTS),
        format_func=lambda s: data.SNAPSHOTS[s]["label"],
    )

    st.header("Evidence weights")
    weights = {
        "baseline": st.slider("Baseline ranking (Genomiser-style)", 0.0, 1.0, 0.30, 0.05),
        "avi": st.slider("AVI-style variant impact", 0.0, 1.0, 0.25, 0.05),
        "pheno": st.slider("Phenotype match", 0.0, 1.0, 0.25, 0.05),
        "cell": st.slider("Cell-context relevance", 0.0, 1.0, 0.20, 0.05),
    }

LABELS = {"baseline": "Baseline", "avi": "AVI", "pheno": "Phenotype", "cell": "Cell context"}

tab_rank, tab_card, tab_diff, tab_bench, tab_export = st.tabs(
    ["1. Ranked candidates", "2. Evidence card", "3. What changed", "4. Benchmark", "5. Export & verify"]
)

rows = data.score_rows(case_id, snapshot, cell_type, weights)

# ---------- Tab 1: ranking ----------
with tab_rank:
    st.subheader("Candidates ranked for the chosen cell context")
    st.caption(
        "Rank combines four evidence sources. The agreement flag shows when sources disagree, "
        "which is where expert review is most needed."
    )
    df = pd.DataFrame(
        [
            {
                "Rank": r["rank"],
                "Variant": r["variant"],
                "Gene": r["gene"],
                "Region": r["region"],
                "Score": r["score"],
                "Agreement": r["agreement"],
                **{LABELS[k]: v for k, v in r["components"].items()},
            }
            for r in rows
        ]
    )
    st.dataframe(df, hide_index=True, width="stretch")

# ---------- Tab 2: evidence card ----------
with tab_card:
    st.subheader("Evidence record for one candidate")
    pick = st.selectbox("Candidate", [r["variant"] for r in rows])
    r = next(x for x in rows if x["variant"] == pick)
    c1, c2 = st.columns([1, 1])
    with c1:
        st.metric("Rank", r["rank"])
        st.metric("Combined score", r["score"])
        st.write(f"**Agreement across sources:** {r['agreement']}")
        st.write("**Contribution to score**")
        st.bar_chart(pd.Series({LABELS[k]: v for k, v in r["contrib"].items()}))
    with c2:
        decision = st.selectbox(
            "Reviewer decision",
            ["Not reviewed", "Take to functional validation", "Needs more evidence", "Deprioritise"],
        )
        note = st.text_area("Reviewer note", "")
        case_input = {"case": case_id, "hpo": case["hpo"], "inheritance": case["inheritance"]}
        input_hash = hashlib.sha256(json.dumps(case_input, sort_keys=True).encode()).hexdigest()
        record = {
            "record_version": "0.1-demo",
            "synthetic_data": True,
            "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "case_id": case_id,
            "input_sha256": input_hash,
            "variant": r["variant"],
            "gene": r["gene"],
            "region": r["region"],
            "cell_context": cell_type,
            "score_snapshot": snapshot,
            "sources": data.SNAPSHOTS[snapshot],
            "weights": weights,
            "components": r["components"],
            "combined_score": r["score"],
            "rank": r["rank"],
            "agreement": r["agreement"],
            "reviewer_decision": decision,
            "reviewer_note": note,
            "intended_use": "research only; not validated for clinical use",
        }
        st.write("**Provenance (re-runnable)**")
        st.json(record, expanded=False)
        st.download_button(
            "Download evidence record (JSON)",
            data=json.dumps(record, indent=2),
            file_name=f"evidence_{case_id}_{r['variant'].replace(':', '_').replace(' ', '_').replace('>', 'to')}.json",
            mime="application/json",
        )

# ---------- Tab 3: what changed ----------
with tab_diff:
    st.subheader("What changed when the scores were updated?")
    st.caption(
        "Same case, same weights, same cell context. Only the score release differs. "
        "This is the re-run view: which conclusions moved and why."
    )
    a = {x["variant"]: x for x in data.score_rows(case_id, "snapshot-A", cell_type, weights)}
    b = {x["variant"]: x for x in data.score_rows(case_id, "snapshot-B", cell_type, weights)}
    out = []
    for vid in a:
        ra, rb = a[vid], b[vid]
        delta_rank = ra["rank"] - rb["rank"]  # positive = moved up
        shifts = {k: rb["contrib"][k] - ra["contrib"][k] for k in ra["contrib"]}
        driver = max(shifts, key=lambda k: abs(shifts[k]))
        why = "no change" if abs(shifts[driver]) < 1e-9 else f"{LABELS[driver]} ({shifts[driver]:+.3f})"
        out.append(
            {
                "Variant": vid,
                "Gene": ra["gene"],
                "Rank A": ra["rank"],
                "Rank B": rb["rank"],
                "Move": f"up {delta_rank}" if delta_rank > 0 else (f"down {-delta_rank}" if delta_rank < 0 else "same"),
                "Main driver": why,
                "Score change": round(rb["score"] - ra["score"], 3),
                "_abs": abs(delta_rank),
            }
        )
    ddf = pd.DataFrame(out).sort_values(["_abs", "Rank B"], ascending=[False, True]).drop(columns="_abs")
    moved = int((ddf["Move"] != "same").sum())
    st.write(f"**{moved} of {len(ddf)} candidates changed rank.**")
    st.dataframe(ddf, hide_index=True, width="stretch")

# ---------- Tab 4: benchmark ----------
with tab_bench:
    st.subheader("Benchmark: top-10 recall by setup")
    st.caption(
        "Upload your own results to compute recall. CSV columns: setup, case_id, rank, is_causal "
        "(true/false). Example setups: Genomiser, Genomiser + AVI, Genomiser + Regulome layer."
    )
    sample = pd.DataFrame(
        {
            "setup": ["Genomiser"] * 3 + ["Genomiser + AVI"] * 3,
            "case_id": ["c1", "c2", "c3"] * 2,
            "rank": [4, 15, 2, 3, 9, 2],
            "is_causal": [True] * 6,
        }
    )
    with st.expander("Format example (made-up numbers, not a result)"):
        st.dataframe(sample, hide_index=True)
    up = st.file_uploader("Results CSV", type="csv")
    k = st.number_input("k", min_value=1, max_value=100, value=10)
    if up is not None:
        try:
            res = pd.read_csv(up)
            res["is_causal"] = res["is_causal"].astype(str).str.lower().isin(["true", "1", "yes"])
            recall = data.top_k_recall(res, k=int(k))
            if recall:
                st.bar_chart(pd.Series(recall, name=f"top-{int(k)} recall"))
                st.dataframe(
                    pd.DataFrame({"Setup": list(recall), f"Top-{int(k)} recall": [f"{v:.0%}" for v in recall.values()]}),
                    hide_index=True,
                )
            else:
                st.info("No causal variants found in the file.")
        except Exception as e:  # keep the demo robust to bad uploads
            st.error(f"Could not read the file: {e}")
    st.caption(
        "Report this honestly: a modest, reproducible gain over Genomiser plus AVI is a valid result. "
        "Pre-register the margin before running."
    )

# ---------- Tab 5: export & verify ----------
with tab_export:
    st.subheader("Export a verifiable evidence bundle")
    st.caption(
        "The bundle holds the inputs, hashes of the data and scoring code, the ranked results and any "
        "reviewer decisions. Anyone with this code can re-run it and check the result matches exactly."
    )
    if "reviews" not in st.session_state:
        st.session_state["reviews"] = []

    with st.expander("Add a reviewer decision (optional)", expanded=False):
        rv_var = st.selectbox("Variant", [x["variant"] for x in rows], key="rv_var")
        rv_dec = st.selectbox(
            "Decision",
            ["Take to functional validation", "Needs more evidence", "Deprioritise"],
            key="rv_dec",
        )
        rv_note = st.text_input("Note", key="rv_note")
        if st.button("Add decision"):
            st.session_state["reviews"].append(
                {"variant": rv_var, "decision": rv_dec, "note": rv_note, "case_id": case_id}
            )
        if st.session_state["reviews"]:
            st.write(f"{len(st.session_state['reviews'])} decision(s) queued")
            st.dataframe(pd.DataFrame(st.session_state["reviews"]), hide_index=True)
            if st.button("Clear decisions"):
                st.session_state["reviews"] = []

    b = bundle.build_bundle(case_id, snapshot, cell_type, weights, reviews=st.session_state["reviews"])
    st.write("**Fingerprints**")
    st.code(
        f"core_sha256:        {b['core_sha256']}\n"
        f"source_data_sha256: {b['core']['provenance']['source_data_sha256']}\n"
        f"scoring_code_sha256:{b['core']['provenance']['scoring_code_sha256']}",
        language="text",
    )
    st.download_button(
        "Download evidence bundle (JSON)",
        data=json.dumps(b, indent=2),
        file_name=f"bundle_{case_id}_{snapshot}.json",
        mime="application/json",
    )

    ICON = {"pass": "PASS", "warn": "WARN", "fail": "FAIL"}

    def show(checks):
        for c in checks:
            line = f"**{ICON[c['status']]}** {c['name']}: {c['detail']}"
            (st.success if c["status"] == "pass" else st.warning if c["status"] == "warn" else st.error)(line)

    st.divider()
    st.subheader("Verify a bundle")
    up_b = st.file_uploader("Upload a bundle JSON", type="json", key="bundle_up")
    if up_b is not None:
        try:
            ok, checks = bundle.verify_bundle(json.load(up_b))
            st.write("**Verified**" if ok else "**NOT verified**")
            show(checks)
        except Exception as e:
            st.error(f"Could not read the bundle: {e}")

    with st.expander("Demo: what tampering looks like"):
        st.caption(
            "Takes the bundle above, secretly swaps the top two ranks, and re-computes the hash to hide it. "
            "The hash check passes, but replaying the inputs exposes the edit."
        )
        if st.button("Run tampering demo"):
            t = json.loads(json.dumps(b))
            t["core"]["results"][0], t["core"]["results"][1] = t["core"]["results"][1], t["core"]["results"][0]
            t["core_sha256"] = bundle.sha(t["core"])
            t["reviews_sha256"] = bundle.sha({"core_sha256": t["core_sha256"], "reviews": t["reviews"]})
            ok, checks = bundle.verify_bundle(t)
            st.write("**Verified**" if ok else "**NOT verified**")
            show(checks)

    st.caption(
        "Limits: a hash makes edits evident, not impossible, and it says nothing about whether the "
        "science is right. Signing is a later step. Synthetic data only."
    )
