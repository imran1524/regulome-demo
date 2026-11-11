"""Machine-verifiable evidence bundles.

A bundle records everything needed to replay a ranking and check that nothing
was altered:

  core            inputs, hashes of the source data and scoring code, and results
  core_sha256     hash of `core` (detects edits to anything inside it)
  reviews         reviewer decisions, chained to core_sha256
  reviews_sha256  hash of {core_sha256, reviews}
  meta            timestamp and tool name (deliberately NOT hashed, so that
                  rebuilding the same analysis gives the same hashes)

Verification does two independent things:
  1. integrity: recompute the hashes from what is stored in the file;
  2. replay: re-run the scoring from the stored inputs and compare with the
     stored results. This catches someone who edits results AND re-hashes.

Limits, stated plainly: hashes are tamper-EVIDENT, not tamper-PROOF. Anyone can
recompute a hash after editing a file; replay catches edited results, but not a
forged bundle for different inputs. Signing is a later step. A hash also says
nothing about whether the science is right.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import data

BUNDLE_VERSION = "1.0"
TOOL = "regulome-demo 0.2 (synthetic data)"
_HERE = Path(__file__).parent


def canonical(obj) -> bytes:
    """Deterministic JSON bytes: sorted keys, no whitespace, no NaN."""
    return json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode("utf-8")


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha(obj) -> str:
    return sha256_bytes(canonical(obj))


def source_data(case_id, snapshot):
    """Everything the scorer reads for one case and snapshot."""
    return {
        "case": data.CASES[case_id],
        "snapshot": data.SNAPSHOTS[snapshot],
        "variants": data.variants(case_id, snapshot),
    }


def source_data_sha256(case_id, snapshot) -> str:
    return sha(source_data(case_id, snapshot))


def scoring_code_sha256() -> str:
    """Hash of data.py with line endings normalised (so Windows/Mac/Linux agree)."""
    raw = (_HERE / "data.py").read_bytes().replace(b"\r\n", b"\n")
    return sha256_bytes(raw)


def _clean_weights(weights):
    return {k: float(weights[k]) for k in sorted(weights)}


def build_bundle(case_id, snapshot, cell_type, weights, reviews=None, now=None):
    weights = _clean_weights(weights)
    rows = data.score_rows(case_id, snapshot, cell_type, weights)
    core = {
        "bundle_version": BUNDLE_VERSION,
        "synthetic_data": True,
        "intended_use": "research only; not validated for clinical use",
        "inputs": {
            "case_id": case_id,
            "snapshot": snapshot,
            "cell_type": cell_type,
            "weights": weights,
        },
        "provenance": {
            "source_data_sha256": source_data_sha256(case_id, snapshot),
            "scoring_code_sha256": scoring_code_sha256(),
        },
        "results": rows,
    }
    core_hash = sha(core)
    reviews = list(reviews or [])
    return {
        "core": core,
        "core_sha256": core_hash,
        "reviews": reviews,
        "reviews_sha256": sha({"core_sha256": core_hash, "reviews": reviews}),
        "meta": {
            "created_utc": (now or datetime.now(timezone.utc)).isoformat(timespec="seconds"),
            "tool": TOOL,
        },
    }


def _check(name, status, detail=""):
    return {"name": name, "status": status, "detail": detail}


def verify_bundle(bundle):
    """Return (ok, checks). ok is False if any check has status 'fail'."""
    checks = []

    # 0. structure
    try:
        core = bundle["core"]
        inputs = core["inputs"]
        case_id, snapshot = inputs["case_id"], inputs["snapshot"]
        cell_type, weights = inputs["cell_type"], inputs["weights"]
        stored_results = core["results"]
        prov = core["provenance"]
        if case_id not in data.CASES or snapshot not in data.SNAPSHOTS or cell_type not in data.CELL_TYPES:
            raise KeyError("unknown case, snapshot or cell type")
    except (KeyError, TypeError) as e:
        return False, [_check("Structure", "fail", f"Missing or unknown field: {e}")]
    checks.append(_check("Structure", "pass", "Required fields present"))

    # 1. integrity of core
    recomputed = sha(core)
    if recomputed == bundle.get("core_sha256"):
        checks.append(_check("Core hash", "pass", "Stored core matches its hash"))
    else:
        checks.append(_check("Core hash", "fail", "Core was changed after the hash was made"))

    # 2. integrity of reviews, chained to core
    expect = sha({"core_sha256": bundle.get("core_sha256"), "reviews": bundle.get("reviews", [])})
    if expect == bundle.get("reviews_sha256"):
        checks.append(_check("Reviews hash", "pass", f"{len(bundle.get('reviews', []))} review(s) intact"))
    else:
        checks.append(_check("Reviews hash", "fail", "Reviews were changed or detached from this core"))

    # 3. source data unchanged since the bundle was made
    now_data = source_data_sha256(case_id, snapshot)
    if now_data == prov.get("source_data_sha256"):
        checks.append(_check("Source data", "pass", "Matches the data the bundle was built from"))
    else:
        checks.append(_check("Source data", "fail", "Current source data differs from the bundle's"))

    # 4. scoring code unchanged (warning only: results check below is decisive)
    if scoring_code_sha256() == prov.get("scoring_code_sha256"):
        checks.append(_check("Scoring code", "pass", "Same scoring code"))
    else:
        checks.append(_check("Scoring code", "warn", "Scoring code differs from the bundle's"))

    # 5. replay: rerun from stored inputs and compare to stored results
    try:
        replay = data.score_rows(case_id, snapshot, cell_type, {k: float(v) for k, v in weights.items()})
    except Exception as e:  # malformed weights etc.
        checks.append(_check("Replay", "fail", f"Could not re-run: {e}"))
        return False, checks
    if canonical(replay) == canonical(stored_results):
        checks.append(_check("Replay", "pass", "Re-running the inputs reproduces the stored results exactly"))
    else:
        diffs = [
            f"{a.get('variant', '?')}: stored rank {a.get('rank')} vs replay rank {b.get('rank')}"
            for a, b in zip(stored_results, replay)
            if canonical(a) != canonical(b)
        ][:3]
        checks.append(_check("Replay", "fail", "Results differ from a fresh run. " + "; ".join(diffs)))

    ok = all(c["status"] != "fail" for c in checks)
    return ok, checks
