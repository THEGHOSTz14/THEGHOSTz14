"""Shared GitHub HTTP helper: uses the credential Git already stores, when present.

Unauthenticated api.github.com is 60 requests/hour per IP, which made the render
and live-profile gates fail with 403 "rate limit exceeded" on a perfectly good
README. The token is read from Git Credential Manager into memory only - never
printed, never written to disk - and requests fall back to anonymous if it is absent.
"""
import json
import os
import subprocess
import urllib.error
import urllib.request

TOKEN = None
_cache = []


def token():
    global TOKEN
    if TOKEN is not None:
        return TOKEN
    TOKEN = ""
    if os.environ.get("GITHUB_TOKEN"):
        TOKEN = os.environ["GITHUB_TOKEN"].strip()
        return TOKEN
    try:
        out = subprocess.run(
            ["git", "credential", "fill"],
            input="protocol=https\nhost=github.com\n\n",
            capture_output=True, text=True, timeout=25,
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0", "GCM_INTERACTIVE": "never"},
        ).stdout
        for line in out.splitlines():
            if line.startswith("password="):
                TOKEN = line[len("password="):].strip()
                break
    except Exception:
        TOKEN = ""
    return TOKEN


def headers(extra=None):
    h = {"Accept": "application/vnd.github+json", "User-Agent": "profile-tools",
         "X-GitHub-Api-Version": "2022-11-28"}
    tok = token()
    if tok:
        h["Authorization"] = f"Bearer {tok}"
    h.update(extra or {})
    return h


def get_json(url):
    return json.loads(raw(url).decode())


def raw(url, timeout=60):
    req = urllib.request.Request(url, headers=headers())
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        if e.code == 403 and "rate limit" in (e.read().decode(errors="replace") or "").lower():
            raise RuntimeError(f"GitHub rate limit hit even with auth for {url}") from e
        raise


def post_json(url, payload, timeout=90):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers(
        {"Content-Type": "application/json"}), method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode()


def note():
    return "authenticated" if token() else "anonymous (60 req/h - expect flaky gates)"
