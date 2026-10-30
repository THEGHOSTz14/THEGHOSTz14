#!/usr/bin/env python3
"""Generate the animated SVG artwork used by the profile README.

assets/tech/<name>.svg   one rounded "cube" tile per technology, logo + label,
                         the logo alone turning in 3D on a static tile
assets/repos/<repo>.svg  a clickable preview card with live stars/forks
assets/stats.svg         the totals card, built here because the public
                         github-readme-stats deployment is down
assets/languages.svg     the stacked language bar

Both are plain SVG with inline CSS, which is the only animation GitHub's image
proxy (camo) will run: it serves `style-src 'unsafe-inline'` and nothing else.
"""
import html
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TECH_DIR = ROOT / "assets" / "tech"
REPO_DIR = ROOT / "assets" / "repos"
CACHE = Path(__file__).resolve().parent / ".icons"
TILE_VERSION = "t9"
CARD_VERSION = "c5"

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
  .float {{ animation: float 6.4s ease-in-out infinite; animation-delay: {delay:.2f}s; }}
  .spin {{ transform-box: fill-box; transform-origin: 50% 50%; animation: spin 12s linear infinite; animation-delay: {delay:.2f}s; }}
  .gleam {{ animation: gleam 12s ease-in-out infinite; animation-delay: {delay:.2f}s; }}
  @keyframes float {{ 0%, 100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-1.5px); }} }}
  @keyframes spin {{
    0%, 50% {{ transform: perspective(190px) rotateY(0deg); opacity: 1; }}
    56% {{ transform: perspective(190px) rotateY(45deg); opacity: .85; }}
    59% {{ transform: perspective(190px) rotateY(90deg); opacity: 0; }}
    60.5% {{ transform: perspective(190px) rotateY(270deg); opacity: 0; }}
    66% {{ transform: perspective(190px) rotateY(315deg); opacity: .75; }}
    70%, 100% {{ transform: perspective(190px) rotateY(360deg); opacity: 1; }}
  }}
  @keyframes gleam {{ 0%, 34% {{ transform: translateX(-70px); }} 58%, 100% {{ transform: translateX(130px); }} }}
</style>
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#201617"/><stop offset="1" stop-color="#0a0707"/>
  </linearGradient>
  <linearGradient id="sheen" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#ffffff" stop-opacity=".16"/><stop offset="1" stop-color="#ffffff" stop-opacity="0"/>
  </linearGradient>
  <clipPath id="clip"><rect x="0" y="0" width="96" height="96" rx="22"/></clipPath>
</defs>
<rect x="0.5" y="0.5" width="95" height="95" rx="21.5" fill="url(#bg)" stroke="#3a2a28"/>
<g clip-path="url(#clip)">
  <rect x="1" y="1" width="94" height="46" rx="20" fill="url(#sheen)"/>
  <rect x="1" y="52" width="94" height="43" rx="18" fill="#000000" opacity=".22"/>
  <g transform="rotate(16 48 48)"><rect class="gleam" x="-46" y="-40" width="18" height="180" fill="#ffffff" opacity=".09"/></g>
  <g class="float"><g class="spin">{art}</g></g>
</g>
<rect x="0.5" y="0.5" width="95" height="95" rx="21.5" fill="none" stroke="#f2e8dd" stroke-opacity=".07"/>
<text x="48" y="112" text-anchor="middle" font-family="{font}" font-size="11.5" fill="#96897f"{fit}>{label}</text>
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
    <stop offset="0" stop-color="#1a1111"/><stop offset="1" stop-color="#0a0707"/>
  </linearGradient>
  <linearGradient id="edge" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#b31217"/><stop offset="1" stop-color="#e0533d"/>
  </linearGradient>
  <clipPath id="clip"><rect x="1" y="1" width="478" height="130" rx="16"/></clipPath>
</defs>
<rect x="0.5" y="0.5" width="479" height="131" rx="16" fill="url(#bg)" stroke="#3a2a28"/>
<g clip-path="url(#clip)">
  <rect class="sweep" x="0" y="-20" width="110" height="180" fill="#b31217" opacity=".05" transform="skewX(-14)"/>
</g>
<rect x="0.5" y="0.5" width="479" height="2.5" rx="1" fill="url(#edge)" opacity=".85"/>
<text x="24" y="40" font-family="{font}" font-size="19" font-weight="700" fill="{name_color}">{repo}</text>
<g class="arrow">
  <path d="M448 30 L458 20 M450 20 H458 V28" fill="none" stroke="#b31217" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
</g>
{desc}
<circle cx="29" cy="113" r="5" fill="{lang_color}"/>
<text x="41" y="117" font-family="{font}" font-size="12" fill="#96897f">{lang}</text>
<g font-family="{font}" font-size="12">
  <g transform="translate(330 104) scale(.78)"><path fill="#c9a227" d="M8 .25a.75.75 0 0 1 .673.418l1.882 3.815 4.21.612a.75.75 0 0 1 .416 1.279l-3.046 2.97.719 4.192a.75.75 0 0 1-1.088.791L8 12.347l-3.766 1.98a.75.75 0 0 1-1.088-.79l.72-4.194L.818 6.374a.75.75 0 0 1 .416-1.28l4.21-.611L7.327.668A.75.75 0 0 1 8 .25Zm0 2.445L6.615 5.5a.75.75 0 0 1-.564.41l-3.097.45 2.24 2.184a.75.75 0 0 1 .216.664l-.528 3.084 2.769-1.456a.75.75 0 0 1 .698 0l2.77 1.456-.53-3.084a.75.75 0 0 1 .216-.664l2.24-2.183-3.096-.45a.75.75 0 0 1-.564-.41L8 2.694Z"/></g>
  <text x="344" y="116" fill="#96897f">{stars}</text>
  <g transform="translate(388 104) scale(.78)"><path fill="#96897f" d="M5 5.372v.878c0 .414.336.75.75.75h4.5a.75.75 0 0 0 .75-.75v-.878a2.25 2.25 0 1 1 1.5 0v.878a2.25 2.25 0 0 1-2.25 2.25h-1.5v2.128a2.251 2.251 0 1 1-1.5 0V8.5h-1.5A2.25 2.25 0 0 1 3.5 6.25v-.878a2.25 2.25 0 1 1 1.5 0ZM5 3.25a.75.75 0 1 0-1.5 0 .75.75 0 0 0 1.5 0Zm6.75.75a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5Zm-3 8.75a.75.75 0 1 0-1.5 0 .75.75 0 0 0 1.5 0Z"/></g>
  <text x="402" y="116" fill="#96897f">{forks}</text>
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
        art = (f'<g transform="translate(26 26) scale(1.8333)" fill="{color}">'
               f"{icon_paths(fetch_icon(slug))}</g>")
    else:
        art = (f'<text x="48" y="48" text-anchor="middle" dominant-baseline="central" '
               f'font-family="{FONT}" font-size="26" font-weight="700" '
               f'fill="{color}" letter-spacing="1">{html.escape(monogram(label))}</text>')
    return TILE.format(label=label_esc, art=art, font=FONT, fit=fit,
                       delay=-(index * 1.9 % 12.0), version=TILE_VERSION)


def card_svg(repo, desc, stars, forks, language, index):
    lines = wrap(desc)
    y = 66
    parts = []
    for line in lines:
        parts.append(f'<text x="24" y="{y}" font-family="{FONT}" font-size="13" '
                     f'fill="#96897f">{html.escape(line)}</text>')
        y += 19
    return CARD.format(repo=html.escape(repo), desc="\n".join(parts), font=FONT,
                       name_color="#e8e1d5", lang=html.escape(language or "—"),
                       lang_color=LANG_COLORS.get(language, "#7d6f65"),
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


STATS = """<svg xmlns="http://www.w3.org/2000/svg" width="360" height="150" viewBox="0 0 360 150" role="img" aria-label="GitHub stats">
<!-- {version} -->
<style>
  .sweep {{ animation: sweep 5.4s linear infinite; }}
  @keyframes sweep {{ 0% {{ transform: translateX(-70px); }} 100% {{ transform: translateX(380px); }} }}
</style>
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#1a1111"/><stop offset="1" stop-color="#0a0707"/>
  </linearGradient>
  <linearGradient id="edge" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#b31217" stop-opacity=".1"/><stop offset=".5" stop-color="#b31217" stop-opacity=".85"/><stop offset="1" stop-color="#b31217" stop-opacity=".1"/>
  </linearGradient>
  <clipPath id="card"><rect x="0.5" y="0.5" width="359" height="149" rx="14"/></clipPath>
</defs>
<rect x="0.5" y="0.5" width="359" height="149" rx="14" fill="url(#bg)" stroke="#3a2a28"/>
<rect x="0.5" y="0.5" width="359" height="2.5" rx="1" fill="url(#edge)"/>
<g clip-path="url(#card)">
  <rect class="sweep" x="0" y="0" width="38" height="150" fill="#ffffff" opacity=".045"/>
</g>
{metrics}
</svg>
"""

STATS_VERSION = "s2"
STATS_CELLS = [
    ("contributions", "Contributions"),
    ("commits", "Commits"),
    ("repos", "Public repos"),
    ("stars", "Stars"),
]


def contribution_counts():
    """Sum the contribution calendar over whole years, which is what the dashboard totals."""
    import gh

    user = gh.get_json(f"https://api.github.com/users/{USERNAME_FOR_API}")
    start = int(user["created_at"][:4])
    end = date.today().year
    totals = {"contributions": 0, "commits": 0}
    query = """query($login:String!,$from:DateTime!,$to:DateTime!){user(login:$login){
      contributionsCollection(from:$from,to:$to){
        contributionCalendar{totalContributions}
        totalCommitContributions}}}"""
    for year in range(start, end + 1):
        body = {"query": query, "variables": {
            "login": USERNAME_FOR_API,
            "from": f"{year}-01-01T00:00:00Z",
            "to": f"{year}-12-31T23:59:59Z"}}
        payload = json.loads(gh.post_json("https://api.github.com/graphql", body))
        if "errors" in payload:
            raise RuntimeError(payload["errors"][0].get("message", "graphql error"))
        cc = payload["data"]["user"]["contributionsCollection"]
        totals["contributions"] += cc["contributionCalendar"]["totalContributions"]
        totals["commits"] += cc["totalCommitContributions"]
    return totals


def build_stats_card():
    """Draw the stats card locally: the public github-readme-stats deploy has been down."""
    import gh

    path = ROOT / "assets" / "stats.svg"
    try:
        totals = contribution_counts()
        repos = gh.get_json(
            f"https://api.github.com/users/{USERNAME_FOR_API}/repos?per_page=100&affiliation=owner"
        )
    except Exception as exc:
        # the refresh job still wants to publish tiles and cards when GitHub's API
        # sulks, so keep yesterday's numbers rather than failing the whole build
        print(f"stats card: kept the old one ({exc})", file=sys.stderr)
        return path if path.exists() else None
    numbers = {
        "contributions": totals["contributions"], "commits": totals["commits"],
        "repos": len(repos), "stars": sum(r["stargazers_count"] for r in repos),
    }
    cells = []
    for index, (key, label) in enumerate(STATS_CELLS):
        col, row = index % 2, index // 2
        x, y = 32 + col * 168, 58 + row * 54
        cells.append(
            f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="24" font-weight="700" '
            f'fill="#e8e1d5">{numbers[key]:,}</text>\n'
            f'<text x="{x}" y="{y + 18}" font-family="{FONT}" font-size="10.5" '
            f'fill="#96897f" letter-spacing=".4">{label}</text>'
        )
    svg = STATS.format(metrics="\n".join(cells), version=STATS_VERSION)
    path = ROOT / "assets" / "stats.svg"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or path.read_text(encoding="utf-8") != svg:
        path.write_text(svg, encoding="utf-8", newline="\n")
        print("stats card: rewritten")
    return path


def main():
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import build_readme
    build_tiles(build_readme.TECH)
    build_repo_cards(build_readme.PROJECTS, build_readme.repo_rows())
    build_stats_card()



USERNAME_FOR_API = "THEGHOSTz14"


LANG_FALLBACK = ["#b31217", "#e0533d", "#A371F7", "#F0883E", "#3FB950", "#DB61A2", "#E3B341", "#39C5CF"]

LANGS = """<svg xmlns="http://www.w3.org/2000/svg" width="340" height="150" viewBox="0 0 340 150" role="img" aria-label="Most used languages">
<!-- {version} -->
<style>
  .glow {{ animation: sweep 4.6s linear infinite; }}
  @keyframes sweep {{ 0% {{ transform: translateX(-80px); }} 100% {{ transform: translateX(360px); }} }}
</style>
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#1a1111"/><stop offset="1" stop-color="#0a0707"/>
  </linearGradient>
  <clipPath id="bar"><rect x="20" y="42" width="300" height="10" rx="5"/></clipPath>
</defs>
<rect x="0.5" y="0.5" width="339" height="149" rx="14" fill="url(#bg)" stroke="#3a2a28"/>
<text x="20" y="26" font-family="{font}" font-size="13" font-weight="700" fill="#e8e1d5">Most used languages</text>
<rect x="20" y="42" width="300" height="10" rx="5" fill="#241a19"/>
<g clip-path="url(#bar)">
{segments}
  <rect class="glow" x="20" y="42" width="44" height="10" fill="#ffffff" opacity=".22"/>
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
        segs.append(f'<rect x="{x:.1f}" y="42" width="{width:.1f}" height="10" fill="{color}" stroke="#0a0707" stroke-width="1"/>')
        col, row = divmod(i, 3)
        lx, ly = 20 + col * 160, 78 + row * 24
        name = lang if len(lang) <= 14 else lang[:13] + "…"
        legend.append(
            f'<circle cx="{lx + 4}" cy="{ly - 4}" r="4" fill="{color}"/>'
            f'<text x="{lx + 14}" y="{ly}" font-family="{FONT}" font-size="11.5" fill="#96897f">'
            f'{html.escape(name)} <tspan fill="#7d6f65">{size * 100 / total:.0f}%</tspan></text>'
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


if __name__ == "__main__":
    main()
