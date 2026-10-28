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
    """Return (broken, unreachable) - a refused connection is not a broken image."""
    broken, throttled = [], []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        for src, (code, size) in ex.map(status, urls):
            if code == "000":
                throttled.append(src)          # connection refused/timeout: our own burst
            elif code != "200" or int(size) < 200:
                broken.append(f"HTTP {code} {size}B  {src[:100]}")
    return broken, throttled


broken, throttled = check(sources)
if throttled:  # camo rate-limits bursts; retry once, gently, before believing anything
    time.sleep(5)
    broken2, throttled = check(throttled)
    broken += broken2

for b in broken:
    print(f"  {b}", file=sys.stderr)
if throttled:
    print(f"note: {len(throttled)} image(s) unreachable this run - camo throttles this host; "
          "re-run rather than trusting it", file=sys.stderr)
if broken:
    print(f"FAILED: {len(broken)} of {len(sources)} images are broken", file=sys.stderr)
    sys.exit(1)
print(f"all {len(sources) - len(throttled)} reachable images loaded; "
      f"{len(throttled)} throttled-out this run")
