#!/usr/bin/env python3
"""Fetch the live profile page and check every image GitHub actually served.

This is the end-to-end gate: it audits what a visitor sees (camo-proxied), not
what README.md claims. Run it after a push.
"""
import concurrent.futures
import html
import os
import re
import subprocess
import sys
import time

URL = "https://github.com/THEGHOSTz14"


def status(src):
    # os.devnull matters: curl on this box reports size_download=0 when told to
    # write to a literal "/dev/null", which looks exactly like an empty response.
    out = subprocess.run(
        ["curl", "-s", "-L", "-o", os.devnull, "-w", "%{http_code} %{size_download}", "-m", "40", src],
        capture_output=True, text=True,
    ).stdout.split()
    return src, (out + ["0", "0"])[:2]


page = subprocess.run(
    ["curl", "-s", "-L", "-m", "40", "-H", "User-Agent: Mozilla/5.0", URL],
    capture_output=True, text=True,
).stdout

if "Tech stack" not in page:
    print("FAILED: the profile page has no README section - is the repo named after the user?",
          file=sys.stderr)
    sys.exit(1)

sources = sorted({html.unescape(u) for u in re.findall(r'<img[^>]+src="(https://(?:camo\.githubusercontent\.com|raw\.githubusercontent\.com|avatars\.githubusercontent\.com)/[^"]+)"', page)})
print(f"profile page fetched, {len(sources)} hosted images to check")

def check(urls):
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        return [s for s, (c, n) in ex.map(status, urls) if c != "200" or int(n) < 200]

bad = check(sources)
if bad:  # camo throttles bursts; one serial retry separates throttling from breakage
    time.sleep(3)
    bad = check([u.split("  ")[-1] for u in bad])

for b in bad:
    print(f"  not loaded: {b[:110]}", file=sys.stderr)
if bad:
    print(f"FAILED: {len(bad)} of {len(sources)} images did not load", file=sys.stderr)
    sys.exit(1)
print(f"all {len(sources)} hosted images loaded on the live profile")
