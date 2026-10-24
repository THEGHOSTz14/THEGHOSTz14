#!/usr/bin/env python3
"""Fetch every remote image in README.md and fail on broken or error badges."""
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# branch-only artefacts: created by the Actions run, so 404 until the repo exists
ALLOW_MISSING = {"/github-snake/"}
BAD_WORDS = ("repo does not exist", "repo not found", "user does not exist", "user not found",
           "invalid", "cannot be parsed", "no public", "not found")


def fetch(url):
    body = subprocess.run(
        ["curl", "-s", "-L", "-m", "40", "-w", "\n%{http_code}", url],
        capture_output=True, text=True, errors="replace",
    ).stdout
    head, _, code = body.rpartition("\n")
    return code.strip(), head


def main():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    urls = sorted(set(re.findall(r'(?:src|srcset)="(https?://[^"]+)"', text)))
    problems = []
    with ThreadPoolExecutor(max_workers=12) as ex:
        results = dict(zip(urls, ex.map(lambda u: fetch(u), urls)))
    for url, (code, body) in results.items():
        name = url.split("?")[0].rsplit("/", 1)[-1]
        if any(m in url for m in ALLOW_MISSING):
            print(f"pending  {code or '---'}  {url[:96]}")
            continue
        low = body.lower()
        if code != "200":
            problems.append(f"HTTP {code or '---'}  {url}")
        elif any(w in low for w in BAD_WORDS):
            problems.append(f"error badge ({next(w for w in BAD_WORDS if w in low)})  {url}")
        elif "<svg" not in low and "<html" not in low:
            problems.append(f"empty body [{len(body)}B]  {url}")
        else:
            print(f"ok       200  {name:28} {len(body)}B")
    print(flush=True)
    print()
    if problems:
        print("FAILED:", file=sys.stderr, flush=True)
        for p in problems:
            print("  " + p, file=sys.stderr, flush=True)
        sys.exit(1)
    print(f"all {len(urls)} remote images resolve")


if __name__ == "__main__":
    main()
