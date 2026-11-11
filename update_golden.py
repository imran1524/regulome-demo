"""Regenerate golden.json (pinned hashes used by test_replay.py).

Run this ONLY when you have deliberately changed the data or scoring in data.py,
and review the diff. A golden hash that changes unexpectedly means results are no
longer reproducible, which is exactly what the replay tests exist to catch.
"""
import json

import bundle
import data

WEIGHTS = {"baseline": 0.30, "avi": 0.25, "pheno": 0.25, "cell": 0.20}


def current():
    out = {}
    for c in data.CASES:
        for s in data.SNAPSHOTS:
            b = bundle.build_bundle(c, s, data.CASES[c]["default_cell"], WEIGHTS)
            out[f"{c}|{s}"] = {
                "source_data_sha256": b["core"]["provenance"]["source_data_sha256"],
                "results_sha256": bundle.sha(b["core"]["results"]),
            }
    return out


if __name__ == "__main__":
    with open("golden.json", "w") as f:
        json.dump(current(), f, indent=2, sort_keys=True)
        f.write("\n")
    print("golden.json updated")
