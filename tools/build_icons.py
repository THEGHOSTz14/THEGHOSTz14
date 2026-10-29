#!/usr/bin/env python3
"""Generate the animated SVG artwork used by the profile README.

assets/tech/<name>.svg   one rounded "cube" tile per technology, logo + label,
                         with a staggered 3D flip/shine loop
assets/repos/<repo>.svg  a clickable preview card with live stars/forks

Both are plain SVG with inline CSS, which is the only animation GitHub's image
proxy (camo) will run: it serves `style-src 'unsafe-inline'` and nothing else.
"""
import html
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TECH_DIR = ROOT / "assets" / "tech"
REPO_DIR = ROOT / "assets" / "repos"
CACHE = Path(__file__).resolve().parent / ".icons"
TILE_VERSION = "t4"
CARD_VERSION = "c3"

FONT = "Segoe UI,Helvetica,Arial,sans-serif"

LANG_COLORS = {
    "Python": "#3572A5", "GDScript": "#355570", "C#": "#178600", "C++": "#F34B7D",
    "C": "#777777", "JavaScript": "#F1E05A", "TypeScript": "#3178C6", "HTML": "#E34C26",
    "CSS": "#563D7C", "Shell": "#89E051", "Batchfile": "#C1F12E", "Java": "#B07219",
    "Rust": "#DEA584", "Go": "#00ADD8", "CMake": "#DA3434",
}


def slugify(text):
    s = text.lower().replace("+", "plus").replace("#", "sharp").replace("&", "and")
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "item"


def monogram(label):
    words = [w for w in re.split(r"[\s/&-]+", label) if w]
    first = words[0] if words else label
    if len(first) >= 3:
        return first[:3].upper() if not first[0].isdigit() else first[:4].upper()
    return "".join(w[0] for w in words)[:3].upper()


def readable(hex_color, floor=0.22):
    """Blend a brand colour toward white until it reads on a near-black tile."""
    c = hex_color.lstrip("#")
    if len(c) == 3:
        c = "".join(ch * 2 for ch in c)
    r, g, b = (int(c[i:i + 2], 16) for i in (0, 2, 4))

    def lum(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4

    def rel(rgb):
        return 0.2126 * lum(rgb[0]) + 0.7152 * lum(rgb[1]) + 0.0722 * lum(rgb[2])

    while rel((r, g, b)) < floor:
        r = min(255, int(r + (255 - r) * 0.25))
        g = min(255, int(g + (255 - g) * 0.25))
        b = min(255, int(b + (255 - b) * 0.25))
    return f"#{r:02X}{g:02X}{b:02X}"


def fetch_icon(slug):
    CACHE.mkdir(exist_ok=True)
    cached = CACHE / f"{slug}.svg"
    if cached.exists():
        return cached.read_text(encoding="utf-8")
    req = urllib.request.Request(
        f"https://cdn.simpleicons.org/{slug}",
        headers={"User-Agent": "profile-art", "Accept": "image/svg+xml"},
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=25) as r:
                body = r.read().decode("utf-8")
            cached.write_text(body, encoding="utf-8")
            return body
        except urllib.error.HTTPError:
            raise
        except Exception:
            if attempt == 2:
                raise
    raise RuntimeError(slug)


def icon_paths(svg):
    # simple-icons serves one 24x24 path; keep every path in case a mark has two
    return "".join(re.findall(r"<path[^>]*/>", svg))


TILE = """<svg xmlns="http://www.w3.org/2000/svg" width="96" height="118" viewBox="0 0 96 118" role="img" aria-label="{label}">
<!-- {version} -->
<style>
  .bob {{ animation: bob 5.6s ease-in-out infinite; animation-delay: {delay:.2f}s; }}
  .flip {{ transform-box: fill-box; transform-origin: 50% 50%; animation: flip 7.2s cubic-bezier(.45,.05,.3,1) infinite; animation-delay: {delay:.2f}s; }}
  .gleam {{ animation: gleam 7.2s ease-in-out infinite; animation-delay: {delay:.2f}s; }}
  @keyframes bob {{ 0%, 100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-2.5px); }} }}
  @keyframes flip {{ 0%, 60% {{ transform: scaleX(1); }} 72% {{ transform: scaleX(.06); }} 84%, 100% {{ transform: scaleX(1); }} }}
  @keyframes gleam {{ 0%, 55% {{ transform: translateX(-70px); }} 80%, 100% {{ transform: translateX(130px); }} }}
</style>
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#25261d"/><stop offset="1" stop-color="#0d0e09"/>
  </linearGradient>
  <linearGradient id="sheen" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#ffffff" stop-opacity=".16"/><stop offset="1" stop-color="#ffffff" stop-opacity="0"/>
  </linearGradient>
  <clipPath id="clip"><rect x="0" y="0" width="96" height="96" rx="22"/></clipPath>
</defs>
<g class="bob"><g class="flip">
  <rect x="0.5" y="0.5" width="95" height="95" rx="21.5" fill="url(#bg)" stroke="#34352a"/>
  <g clip-path="url(#clip)">
    <rect x="1" y="1" width="94" height="46" rx="20" fill="url(#sheen)"/>
    <rect x="1" y="52" width="94" height="43" rx="18" fill="#000000" opacity=".22"/>
    <g transform="rotate(16 48 48)"><rect class="gleam" x="-46" y="-40" width="18" height="180" fill="#ffffff" opacity=".09"/></g>
    {art}
  </g>
  <rect x="0.5" y="0.5" width="95" height="95" rx="21.5" fill="none" stroke="#eaf3ff" stroke-opacity=".07"/>
</g></g>
<text x="48" y="112" text-anchor="middle" font-family="{font}" font-size="11.5" fill="#9aa4b4"{fit}>{label}</text>
</svg>
"""

CARD = """<svg xmlns="http://www.w3.org/2000/svg" width="480" height="132" viewBox="0 0 480 132" role="img" aria-label="{repo}">
<!-- {version} -->
<style>
  .sweep {{ animation: sweep 6.8s ease-in-out infinite; animation-delay: {delay:.2f}s; }}
  .arrow {{ transform-box: fill-box; transform-origin: center; animation: arrow 3.2s ease-in-out infinite; }}
  @keyframes sweep {{ 0% {{ transform: translateX(-170px); }} 55%, 100% {{ transform: translateX(540px); }} }}
  @keyframes arrow {{ 0%, 100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-2.5px); }} }}
</style>
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#14150f"/><stop offset="1" stop-color="#0a0b07"/>
  </linearGradient>
  <linearGradient id="edge" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#4FC1E9"/><stop offset="1" stop-color="#7C9AC4"/>
  </linearGradient>
  <clipPath id="clip"><rect x="1" y="1" width="478" height="130" rx="16"/></clipPath>
</defs>
<rect x="0.5" y="0.5" width="479" height="131" rx="16" fill="url(#bg)" stroke="#2a2b21"/>
<g clip-path="url(#clip)">
  <rect class="sweep" x="0" y="-20" width="110" height="180" fill="#4FC1E9" opacity=".05" transform="skewX(-14)"/>
</g>
<rect x="0.5" y="0.5" width="479" height="2.5" rx="1" fill="url(#edge)" opacity=".85"/>
<text x="24" y="40" font-family="{font}" font-size="19" font-weight="700" fill="{name_color}">{repo}</text>
<g class="arrow">
  <path d="M448 30 L458 20 M450 20 H458 V28" fill="none" stroke="#4FC1E9" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
</g>
{desc}
<circle cx="29" cy="113" r="5" fill="{lang_color}"/>
<text x="41" y="117" font-family="{font}" font-size="12" fill="#a6afbd">{lang}</text>
<g font-family="{font}" font-size="12">
  <g transform="translate(330 104) scale(.78)"><path fill="#e3b341" d="M8 .25a.75.75 0 0 1 .673.418l1.882 3.815 4.21.612a.75.75 0 0 1 .416 1.279l-3.046 2.97.719 4.192a.75.75 0 0 1-1.088.791L8 12.347l-3.766 1.98a.75.75 0 0 1-1.088-.79l.72-4.194L.818 6.374a.75.75 0 0 1 .416-1.28l4.21-.611L7.327.668A.75.75 0 0 1 8 .25Zm0 2.445L6.615 5.5a.75.75 0 0 1-.564.41l-3.097.45 2.24 2.184a.75.75 0 0 1 .216.664l-.528 3.084 2.769-1.456a.75.75 0 0 1 .698 0l2.77 1.456-.53-3.084a.75.75 0 0 1 .216-.664l2.24-2.183-3.096-.45a.75.75 0 0 1-.564-.41L8 2.694Z"/></g>
  <text x="344" y="116" fill="#a6afbd">{stars}</text>
  <g transform="translate(388 104) scale(.78)"><path fill="#a6afbd" d="M5 5.372v.878c0 .414.336.75.75.75h4.5a.75.75 0 0 0 .75-.75v-.878a2.25 2.25 0 1 1 1.5 0v.878a2.25 2.25 0 0 1-2.25 2.25h-1.5v2.128a2.251 2.251 0 1 1-1.5 0V8.5h-1.5A2.25 2.25 0 0 1 3.5 6.25v-.878a2.25 2.25 0 1 1 1.5 0ZM5 3.25a.75.75 0 1 0-1.5 0 .75.75 0 0 0 1.5 0Zm6.75.75a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5Zm-3 8.75a.75.75 0 1 0-1.5 0 .75.75 0 0 0 1.5 0Z"/></g>
  <text x="402" y="116" fill="#a6afbd">{forks}</text>
</g>
</svg>
"""


def wrap(text, limit=56, max_lines=2):
    words, lines, line = text.split(), [], ""
    for w in words:
        if len(line) + len(w) + (1 if line else 0) <= limit:
            line = f"{line} {w}".strip()
        else:
            lines.append(line)
            line = w
            if len(lines) == max_lines:
                break
    if line and len(lines) < max_lines:
        lines.append(line)
    if len(" ".join(words)) > len(" ".join(lines)):
        trimmed = lines[-1].rsplit(" ", 1)[0] if " " in lines[-1] else lines[-1]
        lines[-1] = trimmed.rstrip(".,;:") + "…"
    return lines


def tile_svg(label, slug, color, index):
    label_esc = html.escape(label)
    fit = ""
    if len(label) * 6.0 > 84:
        fit = ' textLength="84" lengthAdjust="spacingAndGlyphs"'
    if slug:
        art = (f'<g transform="translate(22 22) scale(2.1667)" fill="{color}">'
               f"{icon_paths(fetch_icon(slug))}</g>")
    else:
        art = (f'<text x="48" y="48" text-anchor="middle" dominant-baseline="central" '
               f'font-family="{FONT}" font-size="30" font-weight="700" '
               f'fill="{color}" letter-spacing="1">{html.escape(monogram(label))}</text>')
    return TILE.format(label=label_esc, art=art, font=FONT, fit=fit,
                       delay=-(index * 0.43) % 7.2, version=TILE_VERSION)


def card_svg(repo, desc, stars, forks, language, index):
    lines = wrap(desc)
    y = 66
    parts = []
    for line in lines:
        parts.append(f'<text x="24" y="{y}" font-family="{FONT}" font-size="13" '
                     f'fill="#8b949e">{html.escape(line)}</text>')
        y += 19
    return CARD.format(repo=html.escape(repo), desc="\n".join(parts), font=FONT,
                       name_color="#e6edf3", lang=html.escape(language or "—"),
                       lang_color=LANG_COLORS.get(language, "#6e7681"),
                       stars=stars, forks=forks,
                       delay=-(index * 0.8) % 6.8, version=CARD_VERSION)


def build_tiles(tech):
    TECH_DIR.mkdir(parents=True, exist_ok=True)
    names, used = {}, set()
    written = 0
    for index, (label, slug, color) in enumerate(
            (row for items in tech.values() for row in items)):
        base = slugify(label)
        name = base
        while name in used:
            name = base + "-2" if name == base else name + "-2"
        used.add(name)
        names[label] = name
        svg = tile_svg(label, slug, readable(color), index)
        path = TECH_DIR / f"{name}.svg"
        if not path.exists() or path.read_text(encoding="utf-8") != svg:
            path.write_text(svg, encoding="utf-8", newline="\n")
            written += 1
    print(f"tech tiles: {len(names)} total, {written} rewritten")
    return names


def build_repo_cards(projects, rows):
    REPO_DIR.mkdir(parents=True, exist_ok=True)
    by_name = {r["name"]: r for r in rows if not r.get("private")}
    written = 0
    for index, (repo, pitch, _logo) in enumerate(projects):
        row = by_name.get(repo)
        if not row:
            continue
        svg = card_svg(repo, pitch, row.get("stargazers_count", 0),
                       row.get("forks_count", 0), row.get("language"), index)
        path = REPO_DIR / f"{repo}.svg"
        if not path.exists() or path.read_text(encoding="utf-8") != svg:
            path.write_text(svg, encoding="utf-8", newline="\n")
            written += 1
    print(f"repo cards: {len(by_name)} public repos, {written} rewritten")


def main():
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import build_readme
    build_tiles(build_readme.TECH)
    build_repo_cards(build_readme.PROJECTS, build_readme.repo_rows())


if __name__ == "__main__":
    main()


USERNAME_FOR_API = "THEGHOSTz14"


LANG_FALLBACK = ["#4FC1E9", "#7C9AC4", "#A371F7", "#F0883E", "#3FB950", "#DB61A2", "#E3B341", "#39C5CF"]

LANGS = """<svg xmlns="http://www.w3.org/2000/svg" width="340" height="150" viewBox="0 0 340 150" role="img" aria-label="Most used languages">
<!-- {version} -->
<style>
  .glow {{ animation: glow 4.6s ease-in-out infinite; }}
  @keyframes glow {{ 0%, 100% {{ opacity: .45; }} 50% {{ opacity: 1; }} }}
</style>
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#14150f"/><stop offset="1" stop-color="#0a0b07"/>
  </linearGradient>
  <clipPath id="bar"><rect x="20" y="42" width="300" height="10" rx="5"/></clipPath>
</defs>
<rect x="0.5" y="0.5" width="339" height="149" rx="14" fill="url(#bg)" stroke="#2a2b21"/>
<text x="20" y="26" font-family="{font}" font-size="13" font-weight="700" fill="#e6edf3">Most used languages</text>
<rect x="20" y="42" width="300" height="10" rx="5" fill="#20211a"/>
<g clip-path="url(#bar)">
{segments}
  <rect class="glow" x="0" y="42" width="340" height="10" fill="#ffffff" opacity=".12"/>
</g>
{legend}
</svg>
"""


def build_languages(repo_names):
    """Sum the per-repo language bytes and draw one rounded stacked bar."""
    import gh

    totals = {}
    for repo in repo_names:
        try:
            langs = gh.get_json(f"https://api.github.com/repos/{USERNAME_FOR_API}/{repo}/languages")
        except Exception as exc:
            print(f"languages for {repo}: {exc}", file=sys.stderr)
            continue
        for lang, size in langs.items():
            totals[lang] = totals.get(lang, 0) + size
    if not totals:
        return None
    ranked = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)
    top = ranked[:5]
    rest = sum(v for _, v in ranked[5:])
    if rest:
        top.append(("other", rest))
    total = sum(v for _, v in top)

    segs, legend, x = [], [], 20
    for i, (lang, size) in enumerate(top):
        width = 300 * size / total
        color = LANG_COLORS.get(lang) or LANG_FALLBACK[i % len(LANG_FALLBACK)]
        segs.append(f'<rect x="{x:.1f}" y="42" width="{width:.1f}" height="10" fill="{color}"/>')
        col, row = divmod(i, 3)
        lx, ly = 20 + col * 160, 78 + row * 24
        name = lang if len(lang) <= 14 else lang[:13] + "…"
        legend.append(
            f'<circle cx="{lx + 4}" cy="{ly - 4}" r="4" fill="{color}"/>'
            f'<text x="{lx + 14}" y="{ly}" font-family="{FONT}" font-size="11.5" fill="#a6afbd">'
            f'{html.escape(name)} <tspan fill="#6e7681">{size * 100 / total:.0f}%</tspan></text>'
        )
        x += width

    svg = LANGS.format(segments="\n".join(segs), legend="\n".join(legend),
                       font=FONT, version=CARD_VERSION)
    path = ROOT / "assets" / "languages.svg"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or path.read_text(encoding="utf-8") != svg:
        path.write_text(svg, encoding="utf-8", newline="\n")
        print("languages card: rewritten")
    return path
