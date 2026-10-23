#!/usr/bin/env python3
"""
sync_from_forge.py - refreshes this repository's copies of the facts that live in the forge-of-dhar repository.

    python3 tools/sync_from_forge.py ../forge-of-dhar        # copy, then re-render the site
    python3 tools/sync_from_forge.py ../forge-of-dhar --check  # exit 1 if the copies differ from the checkout

What is copied (forge-of-dhar -> here):
    status/status.json          -> data/status.json          what works today, milestones, direction
    benchmarks/results/*.json   -> data/benchmarks/          the speed measurements
    PROGRESS.md                 -> docs/reports/PROGRESS.md  the live progress log
and data/SOURCE.json records the forge-of-dhar commit they came from. The forge repository is the single source of
truth: status is a statement about its code, and its tests (tests/test_status.py) check the status against a real run.
"""
import argparse
import filecmp
import json
import os
import shutil
import subprocess
import sys
from datetime import date

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAIRS = [("status/status.json", "data/status.json"), ("PROGRESS.md", "docs/reports/PROGRESS.md")]


def git(forge, *args):
    return subprocess.run(["git", *args], cwd=forge, capture_output=True, text=True, check=True).stdout.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("forge")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    forge = os.path.abspath(a.forge)
    files = list(PAIRS)
    for f in sorted(os.listdir(os.path.join(forge, "benchmarks", "results"))):
        if f.endswith(".json"):
            files.append(("benchmarks/results/" + f, "data/benchmarks/" + f))
    stale = [dst for src, dst in files
             if not os.path.exists(os.path.join(REPO, dst)) or not filecmp.cmp(os.path.join(forge, src), os.path.join(REPO, dst), shallow=False)]
    if a.check:
        print("copies match the forge-of-dhar checkout" if not stale else "OUT OF DATE vs the checkout: " + ", ".join(stale))
        return 1 if stale else 0
    for src, dst in files:
        os.makedirs(os.path.dirname(os.path.join(REPO, dst)), exist_ok=True)
        shutil.copyfile(os.path.join(forge, src), os.path.join(REPO, dst))
    meta = {
        "forge_repo": "https://github.com/garba-the-analyst/forge-of-dhar",
        "forge_head": git(forge, "rev-parse", "--short", "HEAD"),
        # the last commit that changed the compiler, its tests or its build rules (what the status is checked against)
        "forge_code_commit": git(forge, "log", "-1", "--format=%h", "--", "src", "tests", "Makefile"),
        "synced": date.today().isoformat(),
    }
    with open(os.path.join(REPO, "data", "SOURCE.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
        f.write("\n")
    print("copied %d files from %s (%s)" % (len(files), forge, meta["forge_head"]))
    return subprocess.run([sys.executable, os.path.join(REPO, "tools", "render_site.py")]).returncode


if __name__ == "__main__":
    sys.exit(main())
