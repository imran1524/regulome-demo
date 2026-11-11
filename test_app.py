from streamlit.testing.v1 import AppTest
import pandas as pd
import data

def test_runs_clean():
    at = AppTest.from_file("app.py", default_timeout=30).run()
    assert not at.exception, at.exception
    assert len(at.tabs) == 5

def test_each_case_and_snapshot():
    for c in data.CASES:
        for s in data.SNAPSHOTS:
            rows = data.score_rows(c, s, data.CASES[c]["default_cell"],
                                   {"baseline": .3, "avi": .25, "pheno": .25, "cell": .2})
            assert [r["rank"] for r in rows] == list(range(1, len(rows) + 1))

def test_cell_context_changes_top_candidate():
    w = {"baseline": 0, "avi": 0, "pheno": 0, "cell": 1}
    top = {ct: data.score_rows("CASE-1", "snapshot-A", ct, w)[0]["variant"] for ct in data.CELL_TYPES}
    assert len(set(top.values())) > 1

def test_snapshot_change_moves_ranks():
    w = {"baseline": .3, "avi": .25, "pheno": .25, "cell": .2}
    a = {r["variant"]: r["rank"] for r in data.score_rows("CASE-1", "snapshot-A", "Cortical neuron", w)}
    b = {r["variant"]: r["rank"] for r in data.score_rows("CASE-1", "snapshot-B", "Cortical neuron", w)}
    assert a != b

def test_top_k_recall():
    df = pd.DataFrame({"setup": ["x"]*4, "case_id": list("abcd"), "rank": [1, 5, 12, 30], "is_causal": [True]*4})
    assert data.top_k_recall(df, k=10) == {"x": 0.5}


def test_export_tab_tamper_demo_shows_failure():
    at = AppTest.from_file("app.py", default_timeout=30).run()
    btn = [b for b in at.button if b.label == "Run tampering demo"][0]
    btn.click().run()
    assert not at.exception
    errs = " ".join(e.value for e in at.error)
    oks = " ".join(s.value for s in at.success)
    assert "Replay" in errs and "FAIL" in errs
    assert "Core hash" in oks  # the forged hash still passes; replay is what catches it
