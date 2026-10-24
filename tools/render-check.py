#!/usr/bin/env python3
"""Render README.md through GitHub's own markdown API and fail on layout leaks.

Catches the failures a link check cannot see: markdown that GitHub shows as raw
text, accidental code blocks from 4-space indents, and unbalanced HTML tables.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gh

ROOT = Path(__file__).resolve().parent.parent

html = gh.post_json("https://api.github.com/markdown",
                    {"text": (ROOT / "README.md").read_text(encoding="utf-8"), "mode": "markdown"})
print(f"api auth: {gh.note()}")

counts = {tag: html.count(f"<{tag}") for tag in ("h1", "h2", "h3", "table", "td", "tr", "img", "picture", "pre", "ul", "blockquote")}
print("rendered:", counts)

errors = []
if counts["pre"]:
    errors.append("a code block appeared - an indented line is being parsed as markdown")
if counts["h1"] != 1:
    errors.append(f"expected exactly 1 h1, got {counts['h1']}")
if counts["img"] < 90:
    errors.append(f"only {counts['img']} images rendered")
for tag in ("table", "td", "tr"):
    if html.count(f"<{tag}") != html.count(f"</{tag}>"):
        errors.append(f"unbalanced <{tag}>: {html.count(f'<{tag}')} open vs {html.count(f'</{tag}>')} close")
visible_text = re.sub(r"<[^>]+>", " ", html)
for leak in re.findall(r"^\s{0,3}(?:#{1,6}\s|\*\*|<img|<td|<p\s|<picture)[^\n]{0,50}", visible_text, re.M):
    errors.append(f"markdown/html shown as literal text: {leak.strip()[:50]}")
if "&lt;" in html:
    errors.append("an HTML tag was escaped, so readers see it as text")

if errors:
    print("FAILED:", file=sys.stderr)
    for e in errors:
        print("  " + e, file=sys.stderr)
    sys.exit(1)
print("README renders clean")
