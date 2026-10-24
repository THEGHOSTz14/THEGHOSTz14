#!/usr/bin/env python3
"""Render README.md to a standalone HTML preview (GitHub's own markdown renderer).

Usage:  python tools/preview.py <output.html>

Useful while the profile repo does not exist yet, or before pushing a redesign:
the badge and widget URLs are the same ones GitHub will fetch, so the preview is
the real thing, not a mock-up. The banner is inlined as a downscaled data URI.
"""
import base64
import io
import json
import pathlib
import re
import sys
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
STYLE = """
.gh{background:#0d1117;color:#c9d1d9;font:14px/1.6 -apple-system,"Segoe UI",Helvetica,Arial,sans-serif;
    border:1px solid #30363d;border-radius:10px;padding:28px 36px;max-width:1010px;margin:0 auto}
.gh h1,.gh h2,.gh h3{color:#e6edf3;border-bottom:1px solid #21262d;padding-bottom:.3em}
.gh h1{font-size:1.9em;margin:.2em 0}.gh h2{font-size:1.4em}.gh h3{font-size:1.15em;border:none}
.gh a{color:#4493f8}.gh code{background:#1f2428;padding:.15em .35em;border-radius:4px;color:#e6edf3}
.gh img{max-width:100%}.gh table{border-collapse:collapse;width:100%}
.gh hr{border:0;border-top:1px solid #30363d;margin:22px 0}
.gh blockquote{color:#8b949e;border-left:.25em solid #30363d;margin:0;padding:0 1em}
.gh ul{padding-left:1.5em}
.wrap{background:#010409;padding:24px;margin:0}
"""


def data_uri(name, width=1000):
    from PIL import Image
    im = Image.open(ROOT / "assets" / name).convert("RGB")
    if im.width > width:
        im = im.resize((width, round(width * im.height / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=82, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def inline_assets(html):
    for name, width in (("banner.png", 1000), ("profile-card.png", 1240)):
        uri = data_uri(name, width)
        html = re.sub(rf'<img src="assets/{re.escape(name)}"([^>]*)>',
                      lambda m, u=uri: f'<img src="{u}"{m.group(1)}>', html)
    return html


def main():
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    out = pathlib.Path(sys.argv[1])
    md = (ROOT / "README.md").read_text(encoding="utf-8")
    req = urllib.request.Request(
        "https://api.github.com/markdown",
        data=json.dumps({"text": md, "mode": "markdown"}).encode(),
        headers={"Accept": "application/vnd.github+json",
                 "Content-Type": "application/json",
                 "User-Agent": "readme-preview"},
    )
    body = urllib.request.urlopen(req, timeout=90).read().decode()
    body = inline_assets(body)
    html = f"<style>{STYLE}</style><div class='wrap'><div class='gh'>{body}</div></div>"
    out.write_text(html, encoding="utf-8")
    print(f"{out} written ({len(html)//1024} KB)")


if __name__ == "__main__":
    main()
