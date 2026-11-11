"""Verify an evidence bundle from the command line.

    python verify_bundle.py path/to/bundle.json

Exit code 0 = all checks passed (warnings allowed), 1 = a check failed.
"""
import json
import sys

import bundle


def main(argv):
    if len(argv) != 2:
        print("usage: python verify_bundle.py bundle.json")
        return 2
    try:
        with open(argv[1], "r", encoding="utf-8") as f:
            b = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"Could not read bundle: {e}")
        return 1
    ok, checks = bundle.verify_bundle(b)
    icon = {"pass": "PASS", "warn": "WARN", "fail": "FAIL"}
    for c in checks:
        print(f"[{icon[c['status']]}] {c['name']}: {c['detail']}")
    print("RESULT:", "verified" if ok else "NOT verified")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
