#!/usr/bin/env python3
"""
Tool-X link checker.

Checks every entry in core/data.json to see whether its source is still
reachable, WITHOUT actually downloading/installing anything:

  - git entries    -> `git ls-remote <url>` (just asks "does this repo
                       exist", downloads nothing)
  - curl/wget      -> HTTP HEAD request to the url
  - package_manager -> can't be verified without root + `apt update`,
                       so these are reported separately as "not checked"

Usage:
    python3 check_tools.py                  # just print a report
    python3 check_tools.py --clean          # also write data.clean.json
                                             # with dead entries removed
    python3 check_tools.py --workers 20     # check 20 at a time (default 15)
"""

import argparse
import concurrent.futures
import json
import os
import subprocess
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

GUI_DIR = Path(__file__).resolve().parent
PROJECT_DIR = GUI_DIR.parent
CORE_DIR = PROJECT_DIR / "core"


def check_git(url, timeout):
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GIT_ASKPASS"] = "echo"
    try:
        result = subprocess.run(
            ["git", "ls-remote", url],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
            env=env,
            timeout=timeout,
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        return None  # unknown, treat separately
    except Exception:
        return False


def check_http(url, timeout):
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "tool-x-checker"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return 200 <= resp.status < 400
    except urllib.error.HTTPError as e:
        # Some servers don't support HEAD but do support GET; a 405 doesn't
        # mean the resource is gone.
        return e.code not in (404, 410)
    except Exception:
        return False


def check_one(name, info, timeout):
    pm = info["package_manager"]
    url = info.get("url")

    if pm == "package_manager":
        return name, "skipped", "needs apt/pkg -- not checked"

    if not url:
        return name, "skipped", "no url"

    if pm == "git":
        ok = check_git(url, timeout)
        if ok is None:
            return name, "unknown", "timed out"
        return (name, "ok", "") if ok else (name, "dead", "repo not reachable")

    if pm in ("curl", "wget"):
        ok = check_http(url, timeout)
        return (name, "ok", "") if ok else (name, "dead", "url not reachable")

    return name, "skipped", f"unknown package_manager '{pm}'"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=15)
    parser.add_argument("--timeout", type=int, default=10)
    parser.add_argument("--clean", action="store_true", help="write data.clean.json without dead entries")
    args = parser.parse_args()

    data = json.load(open(CORE_DIR / "data.json", encoding="utf-8"))
    total = len(data)
    print(f"Checking {total} entries with {args.workers} parallel workers...\n")

    results = {"ok": [], "dead": [], "unknown": [], "skipped": []}
    start = time.time()
    done = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(check_one, name, info, args.timeout): name
            for name, info in data.items()
        }
        for fut in concurrent.futures.as_completed(futures):
            name, status, reason = fut.result()
            results[status].append(name)
            done += 1
            if done % 20 == 0 or done == total:
                print(f"  checked {done}/{total}...")

    elapsed = time.time() - start
    print(f"\nDone in {elapsed:.0f}s\n")

    print("=" * 50)
    print(f"Working (git/curl verified): {len(results['ok'])}")
    print(f"Dead (repo/url gone):        {len(results['dead'])}")
    print(f"Timed out (unsure):          {len(results['unknown'])}")
    print(f"Skipped (apt-based, or n/a): {len(results['skipped'])}")
    print("=" * 50)

    if results["dead"]:
        print("\nDead entries:")
        for n in sorted(results["dead"]):
            print(f"  - {n}")

    if results["unknown"]:
        print("\nTimed out (re-run to confirm, could be slow network):")
        for n in sorted(results["unknown"]):
            print(f"  - {n}")

    report_path = GUI_DIR / "check_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nFull report saved to {report_path}")

    if args.clean:
        cleaned = {k: v for k, v in data.items() if k not in results["dead"]}
        clean_path = CORE_DIR / "data.clean.json"
        with open(clean_path, "w", encoding="utf-8") as f:
            json.dump(cleaned, f, indent=2)
        print(f"Cleaned database ({len(cleaned)} entries) saved to {clean_path}")
        print("Review it, then rename it to data.json to use it.")


if __name__ == "__main__":
    main()
