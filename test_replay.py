"""Replay and tamper-detection tests.

These tests substantiate one claim only: given the same inputs, data and code,
the analysis reproduces exactly, and edits to a bundle are detected. They say
nothing about whether the scores are scientifically meaningful.
"""
import copy
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

import bundle
import data
import update_golden

HERE = Path(__file__).parent
W = {"baseline": 0.30, "avi": 0.25, "pheno": 0.25, "cell": 0.20}


def make(case="CASE-1", snap="snapshot-A", cell="Cortical neuron", weights=W, reviews=None, now=None):
    return bundle.build_bundle(case, snap, cell, weights, reviews=reviews, now=now)


def statuses(b):
    ok, checks = bundle.verify_bundle(b)
    return ok, {c["name"]: c["status"] for c in checks}


# ---------- determinism ----------

def test_same_inputs_same_hashes_repeatedly():
    hashes = {make()["core_sha256"] for _ in range(5)}
    assert len(hashes) == 1


def test_timestamp_does_not_change_core_hash():
    a = make(now=datetime(2026, 1, 1, tzinfo=timezone.utc))
    b = make(now=datetime(2030, 6, 6, tzinfo=timezone.utc))
    assert a["meta"]["created_utc"] != b["meta"]["created_utc"]
    assert a["core_sha256"] == b["core_sha256"]


def test_weight_key_order_is_irrelevant():
    a = make(weights={"baseline": .3, "avi": .25, "pheno": .25, "cell": .2})
    b = make(weights={"cell": .2, "pheno": .25, "avi": .25, "baseline": .3})
    assert a["core_sha256"] == b["core_sha256"]


def test_different_inputs_different_hashes():
    base = make()["core_sha256"]
    assert make(snap="snapshot-B")["core_sha256"] != base
    assert make(cell="Cardiomyocyte")["core_sha256"] != base
    assert make(weights={**W, "avi": 0.5})["core_sha256"] != base
    assert make(case="CASE-2", cell="Cardiomyocyte")["core_sha256"] != base


@pytest.mark.parametrize("seed", ["0", "1", "12345"])
def test_same_hash_across_processes_and_hash_seeds(seed):
    code = (
        "import bundle;"
        "b=bundle.build_bundle('CASE-1','snapshot-A','Cortical neuron',"
        "{'baseline':.3,'avi':.25,'pheno':.25,'cell':.2});"
        "print(b['core_sha256'])"
    )
    env = {**os.environ, "PYTHONHASHSEED": seed}
    out = subprocess.run([sys.executable, "-c", code], cwd=HERE, env=env,
                         capture_output=True, text=True, check=True).stdout.strip()
    assert out == make()["core_sha256"]


# ---------- golden (pinned) hashes ----------

def test_golden_hashes_unchanged():
    golden = json.loads((HERE / "golden.json").read_text())
    assert update_golden.current() == golden, (
        "Pinned hashes changed. If data.py was changed on purpose, run "
        "`python update_golden.py` and review the diff; otherwise results are no longer reproducible."
    )


# ---------- verification passes on honest bundles ----------

def test_fresh_bundle_verifies():
    ok, s = statuses(make())
    assert ok
    assert set(s.values()) == {"pass"}


def test_roundtrip_through_json_file_verifies(tmp_path):
    p = tmp_path / "b.json"
    p.write_text(json.dumps(make(reviews=[{"variant": "chr1:1000100 G>A", "decision": "Needs more evidence", "note": "x"}]), indent=2))
    loaded = json.loads(p.read_text())
    ok, _ = bundle.verify_bundle(loaded)
    assert ok


def test_all_cases_and_snapshots_verify():
    for c in data.CASES:
        for s in data.SNAPSHOTS:
            ok, _ = bundle.verify_bundle(make(c, s, data.CASES[c]["default_cell"]))
            assert ok, (c, s)


def test_meta_edit_is_not_flagged():
    b = make()
    b["meta"]["created_utc"] = "1999-01-01T00:00:00+00:00"
    ok, _ = bundle.verify_bundle(b)
    assert ok


# ---------- tamper detection ----------

def test_edited_result_without_rehash_is_caught():
    b = make()
    b["core"]["results"][0]["score"] = 0.999
    ok, s = statuses(b)
    assert not ok
    assert s["Core hash"] == "fail"
    assert s["Replay"] == "fail"


def test_edited_result_with_rehash_is_still_caught_by_replay():
    b = make()
    b["core"]["results"][0], b["core"]["results"][1] = b["core"]["results"][1], b["core"]["results"][0]
    b["core_sha256"] = bundle.sha(b["core"])
    b["reviews_sha256"] = bundle.sha({"core_sha256": b["core_sha256"], "reviews": b["reviews"]})
    ok, s = statuses(b)
    assert not ok
    assert s["Core hash"] == "pass"      # the forger fixed the hash...
    assert s["Replay"] == "fail"         # ...but replay disagrees


def test_edited_weights_with_rehash_is_caught():
    b = make()
    b["core"]["inputs"]["weights"]["avi"] = 0.9
    b["core_sha256"] = bundle.sha(b["core"])
    b["reviews_sha256"] = bundle.sha({"core_sha256": b["core_sha256"], "reviews": b["reviews"]})
    ok, s = statuses(b)
    assert not ok and s["Replay"] == "fail"


def test_edited_review_is_caught():
    b = make(reviews=[{"variant": "v", "decision": "Deprioritise", "note": ""}])
    b["reviews"][0]["decision"] = "Take to functional validation"
    ok, s = statuses(b)
    assert not ok and s["Reviews hash"] == "fail"


def test_review_cannot_be_moved_to_another_bundle():
    r = [{"variant": "v", "decision": "Take to functional validation", "note": "n"}]
    a = make(reviews=r)
    other = make(snap="snapshot-B")
    other["reviews"] = copy.deepcopy(a["reviews"])
    other["reviews_sha256"] = a["reviews_sha256"]
    ok, s = statuses(other)
    assert not ok and s["Reviews hash"] == "fail"


def test_changed_source_data_is_caught(monkeypatch):
    b = make()
    original = data._V[0]
    changed = list(original)
    changed[5] = original[5] + 5  # snapshot A AVI value for the first variant
    monkeypatch.setitem(data.__dict__, "_V", [tuple(changed)] + data._V[1:])
    ok, s = statuses(b)
    assert not ok
    assert s["Source data"] == "fail"
    assert s["Replay"] == "fail"


def test_code_change_with_same_results_is_only_a_warning(monkeypatch):
    b = make()
    monkeypatch.setattr(bundle, "scoring_code_sha256", lambda: "0" * 64)
    ok, s = statuses(b)
    assert ok
    assert s["Scoring code"] == "warn"
    assert s["Replay"] == "pass"


def test_malformed_bundles_fail_cleanly():
    for bad in [{}, {"core": {}}, {"core": {"inputs": {"case_id": "NOPE", "snapshot": "x", "cell_type": "y", "weights": {}}, "results": [], "provenance": {}}}]:
        ok, checks = bundle.verify_bundle(bad)
        assert not ok
        assert checks[0]["status"] == "fail"


def test_cli_exit_codes(tmp_path):
    good = tmp_path / "good.json"
    good.write_text(json.dumps(make()))
    bad_b = make()
    bad_b["core"]["results"][0]["score"] = 0.5
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps(bad_b))
    run = lambda p: subprocess.run([sys.executable, "verify_bundle.py", str(p)], cwd=HERE, capture_output=True, text=True)
    assert run(good).returncode == 0
    r = run(bad)
    assert r.returncode == 1 and "NOT verified" in r.stdout
    assert run(tmp_path / "missing.json").returncode == 1
