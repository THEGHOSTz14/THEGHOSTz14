#!/usr/bin/env python3
"""Regenerate README.md from the spec below.

Edit TECH / PROJECTS / LINKS here, then run:  python tools/build-readme.py

Every logo slug is HEAD-checked against cdn.simpleicons.org before anything is
written, so a typo fails the build instead of showing a broken tile on the profile.
"""
import re
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gh

ROOT = Path(__file__).resolve().parent.parent
PILL = "181712"
USERNAME = "THEGHOSTz14"

# (label, simple-icons slug or "" for a text-only tile, logo colour)
TECH = {
    "Languages & scripting": [
        ("Python", "python", "3776AB"),
        ("C", "c", "A8B9CC"),
        ("C++", "cplusplus", "00599C"),
        ("C#", "dotnet", "512BD4"),
        ("GDScript", "godotengine", "478CBF"),
        ("JavaScript", "javascript", "F7DF1E"),
        ("TypeScript", "typescript", "3178C6"),
        ("SQL", "", "4479A1"),
        ("Bash", "gnubash", "4EAA25"),
        ("MATLAB", "", "E1673C"),
    ],
    "Web": [
        ("HTML5", "html5", "E34F26"),
        ("CSS3", "css", "1572B6"),
        ("React", "react", "61DAFB"),
        ("Vite", "vite", "7D68FF"),
        ("Node.js", "nodedotjs", "5FA04E"),
        ("Express", "express", "FFFFFF"),
        ("Tailwind CSS", "tailwindcss", "06B6D4"),
        ("Nginx", "nginx", "009639"),
        ("Flask", "flask", "FFFFFF"),
        ("FastAPI", "fastapi", "009688"),
        ("GitHub Pages", "githubpages", "FFFFFF"),
    ],
    "AI / CV / data": [
        ("TensorFlow", "tensorflow", "FF6F00"),
        ("PyTorch", "pytorch", "EE4C2C"),
        ("Keras", "keras", "D00000"),
        ("OpenCV", "opencv", "5C3EE8"),
        ("scikit-learn", "scikitlearn", "F7931E"),
        ("NumPy", "numpy", "0095D5"),
        ("Pandas", "pandas", "150458"),
        ("Ultralytics YOLO", "ultralytics", "FFFF00"),
        ("Hugging Face", "huggingface", "FFD21E"),
        ("Ollama", "ollama", "FFFFFF"),
        ("CUDA", "nvidia", "76B900"),
        ("Jupyter", "jupyter", "F37626"),
    ],
    "Game dev & 3D": [
        ("Godot 4", "godotengine", "478CBF"),
        ("Unity", "unity", "FFFFFF"),
        ("Unreal Engine", "unrealengine", "FFFFFF"),
        ("Blender", "blender", "F5792A"),
        ("CLion", "clion", "21D789"),
        ("Rider", "rider", "FCA326"),
        ("TinkerCAD", "tinkercad", "2CBDF1"),
        ("SketchUp", "sketchup", "005F9E"),
    ],
    "PLC & automation platforms": [
        ("Siemens S7", "siemens", "009999"),
        ("TIA Portal", "", "009999"),
        ("Allen-Bradley", "rockwellautomation", "CD6321"),
        ("Studio 5000", "", "CD6321"),
        ("Schneider Electric", "schneiderelectric", "3DCD58"),
        ("ABB", "abb", "FF000F"),
        ("Delta", "delta", "FF6000"),
        ("Panasonic FPWIN", "panasonic", "FFFFFF"),
        ("Mitsubishi GX Works", "mitsubishi", "E60012"),
        ("Keyence KV Studio", "", "C8102E"),
        ("Omron CX-Programmer", "", "005E9E"),
        ("Ignition SCADA", "inductiveautomation", "00A0DF"),
        ("MQTT", "mqtt", "660066"),
        ("Modbus", "", "0072C6"),
        ("OPC UA", "", "F08119"),
    ],
    "Electrical design & simulation": [
        ("Ladder Logic", "", "00C2A8"),
        ("VFD & Servo", "", "FFB300"),
        ("24V DC / Sensor", "", "00C2A8"),
        ("Relay & Contactor", "", "FFB300"),
        ("Panel Wiring", "", "8AB4F8"),
        ("AutoCAD Electrical", "autodesk", "0696D7"),
        ("EPLAN", "", "FFCC00"),
        ("LabVIEW", "labview", "FFC220"),
        ("Proteus", "proteus", "1F4E79"),
        ("LTspice", "ltspice", "D6D6D6"),
        ("Multisim", "multisim", "00B4D8"),
    ],
    "Tooling, OS & cloud": [
        ("Git", "git", "F05032"),
        ("GitHub", "github", "FFFFFF"),
        ("GitLab", "gitlab", "FC6D26"),
        ("Docker", "docker", "2496ED"),
        ("Kubernetes", "kubernetes", "326CE5"),
        ("Linux", "linux", "FCC624"),
        ("Ubuntu", "ubuntu", "E95420"),
        ("Debian", "debian", "A81D33"),
        ("Kali Linux", "kalilinux", "557C94"),
        ("VS Code", "", "007ACC"),
        ("Vim", "vim", "019733"),
        ("Ansible", "ansible", "EE0000"),
        ("Terraform", "terraform", "7B42BC"),
        ("Jenkins", "jenkins", "D24939"),
        ("AWS", "", "FF9900"),
        ("Google Cloud", "googlecloud", "34A853"),
        ("Azure", "", "0089D6"),
        ("Cloudflare", "cloudflare", "F38020"),
        ("Grafana", "grafana", "F47A20"),
        ("Prometheus", "prometheus", "E6522C"),
        ("Windows Terminal", "", "4CC2FF"),
        ("Android", "android", "3DDC84"),
    ],
    "Hardware & IoT": [
        ("Arduino", "arduino", "008184"),
        ("Raspberry Pi", "raspberrypi", "C51A4A"),
        ("ESP32", "espressif", "E7352C"),
        ("STM32", "stmicroelectronics", "03239B"),
        ("Home Assistant", "homeassistant", "41BDF5"),
    ],
}

# (repo, one-line pitch, logo slug for the language tile)
# Repos that are not public are rendered as a plain bullet - no dead link, no
# "repo not found" pill. build-readme.py checks this against the API on every run.
PROJECTS = [
    ("GHOST_WEB_GAME-", "Godot 4.7 arcade game, exported to WASM for the y8 browser portal", "godotengine"),
    ("YOLO-BASIC-MODEL", "PyQt6 webcam app - YOLOv8 detection with DeepSORT tracking, MediaPipe finger counting and drawn count-zones", "ultralytics"),
    ("C-", "C# fundamentals exercises - syntax, input, math, booleans, branching - on .NET 10", "dotnet"),
]

# Only links the account actually owns. Add real handles, then re-run the script.
LINKS = [
    ("GitHub", f"https://github.com/{USERNAME}", "github", "FFFFFF"),
    ("Email", f"mailto:204194426+{USERNAME}@users.noreply.github.com", "gmail", "EA4335"),
]

# Uncomment once you have the real handle/ID - anything that does not resolve is
# dropped with a warning instead of being published as a dead tile.
EXTRA_LINKS = []
#     ("TryHackMe", f"https://tryhackme.com/p/HANDLE", "tryhackme", "DD00AA"),
#     ("HackTheBox", "https://app.hackthebox.com/users/ID", "hackthebox", "8CE100"),

# Your TryHackMe username, to show the profile card from the reference design.
THM_USER = ""

STATS = "https://github-readme-stats.vercel.app/api"
THEME = "theme=tokyonight&bg_color=0d1117&border_color=181712&title_color=7C9AC4&icon_color=4FC1E9&text_color=C9D1D9&hide_border=true"


def esc(s):
    out = s.replace("_", "__").replace("-", "--").replace("+", "%2B")
    out = out.replace("/", "%2F").replace("#", "%23").replace("&", "%26").replace(" ", "%20")
    return out


def readable(hex_color, floor=0.10):
    """Blend a brand colour toward white until it is visible on a #181712 pill.

    Pandas ships #150458, which is darker than the pill itself and rendered as an
    invisible logo.
    """
    c = hex_color.lstrip("#")
    r, g, b = (int(c[i:i + 2], 16) for i in (0, 2, 4))
    def lum(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    def rel(rgb):
        rl, gl, bl = (lum(x) for x in rgb)
        return 0.2126 * rl + 0.7152 * gl + 0.0722 * bl
    while rel((r, g, b)) < floor:
        r = min(255, int(r + (255 - r) * 0.2))
        g = min(255, int(g + (255 - g) * 0.2))
        b = min(255, int(b + (255 - b) * 0.2))
    return f"{r:02X}{g:02X}{b:02X}"


def pill(label, logo="", logo_color=None):
    url = (
        f"https://img.shields.io/badge/-{esc(label)}-{PILL}"
        f"?style=flat&labelColor={PILL}&color={PILL}"
    )
    if logo:
        url += f"&logo={logo}&logoColor={readable(logo_color) if logo_color else 'white'}"
    return url


def img(url, alt, width=None):
    w = f' width="{width}"' if width else ""
    return f'<img src="{url}" alt="{alt}"{w}>'


def centered(html_lines):
    # flush-left on purpose: a 4-space indent after a blank line is a code block in markdown
    return ["<p align=\"center\">", "", *[l.lstrip() for l in html_lines], "", "</p>", ""]




def reachable(url):
    req = urllib.request.Request(url, headers={"User-Agent": "readme-builder"}, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.status == 200
    except Exception:
        return False


def public_repos():
    """Repo names that are actually visible on the account right now."""
    rows = gh.get_json(f"https://api.github.com/users/{USERNAME}/repos?per_page=100")
    return {row["name"] for row in rows if not row.get("private")}


def build():
    visible = public_repos()
    hidden = [name for name, _, _ in PROJECTS if name not in visible]
    if hidden:
        print("not public, rendered without links: " + ", ".join(hidden), file=sys.stderr)
    slugs = sorted(
        {s for row in TECH.values() for _, s, _ in row if s}
        | {s for _, _, s in PROJECTS if s}
        | {s for _, _, s, _ in LINKS + EXTRA_LINKS if s}
    )
    bad = []
    for slug in slugs:
        req = urllib.request.Request(
            f"https://cdn.simpleicons.org/{slug}",
            headers={"User-Agent": "readme-builder", "Accept": "image/svg+xml"},
        )
        try:
            with urllib.request.urlopen(req, timeout=25) as r:
                if r.status != 200:
                    bad.append(slug)
        except Exception:
            bad.append(slug)
    if bad:
        print(f"unknown simple-icons slug(s): {', '.join(bad)}", file=sys.stderr)
        sys.exit(1)

    p = []
    a = p.append

    a("<div align=\"center\">")
    a("")
    a("  " + img("assets/banner.png", "Ghost circuit banner", "72%"))
    a("")
    a("  # 👻 Rohan · `THEGHOSTz14`")
    a("")
    a("  ### Industrial Electrical & PLC Engineer · Godot game dev · automating the boring parts")
    a("")
    a("  Manesar, India · *Om Industries Pvt Ltd* · I write code that either runs a plant or runs in a browser")
    a("")
    a("  " + img(
        "https://readme-typing-svg.demolab.com/?font=Fira%20Code&center=true&width=680&height=52"
        "&color=4FC1E9&vCenter=true&size=23&pause=1000&lines="
        + ";".join(["Rohan%20from%20Manesar",
                    "Industrial%20%26%20PLC%20engineer",
                    "Godot%204%20%2B%20GDScript",
                    "Automating%20the%20boring%20parts"]),
        "typewriter intro"))
    a("")
    a("  " + img(
        f"https://komarev.com/ghpvc/?username={USERNAME}&style=flat&labelColor={PILL}&color={PILL}&label=visitors",
        "profile views") + " " + img(
        f"https://img.shields.io/github/followers/{USERNAME}?style=flat&labelColor={PILL}&color={PILL}"
        f"&logo=github&logoColor=white&label=followers",
        "followers") + " " + img(
        f"https://img.shields.io/github/stars/{USERNAME}?style=flat&labelColor={PILL}&color={PILL}"
        f"&label=stars%20received",
        "stars received"))
    a("")
    a("  ---")
    a("")
    a("</div>")
    a("")

    a("### 🧾 About me")
    a("")
    a("- 🔭 **Building** → *GHOST WEB GAME* — a Godot 4.7 arcade game exported to WASM for the y8 browser portal")
    a("- 🏭 **Day job** → panel design, PLC programming, VFD & servo commissioning, plant troubleshooting")
    a("- 🌱 **Learning** → C#, computer vision with YOLO, and finishing projects instead of starting them")
    a("- 💬 **Ask me about** → ladder logic, 24 V sensor wiring, why a contactor chatters, Godot web exports")
    a("- ⚡ **Method** → I debug PLCs with a multimeter and games with `print()`. Both work.")
    a("")
    p.extend(centered([
        "  " + img(f"{STATS}?username={USERNAME}&show_icons=true&count_private=true"
                   f"&show=prs_merged,prs_merged_percentage,reviews&{THEME}&card_width=360", "GitHub stats"),
        "  " + img(
            "https://github-readme-streak-stats.herokuapp.com/?user=" + USERNAME
            + "&theme=tokyonight&background=0d1117&border=181712&ring=4FC1E9&fire=FF6F00"
            "&currStreakLabel=7C9AC4&sideLabels=C9D1D9&dates=8B949E&hide_border=true&card_width=360",
            "Contribution streak"),
    ]))
    a("## ⚡ Tech stack")
    a("")
    for title, items in TECH.items():
        a(f"**{title}**")
        a("")
        tiles = " ".join(img(pill(label, logo, color), label) for label, logo, color in items)
        p.extend(centered([f"    {tiles}"]))
    a("## 🚀 Things I have shipped")
    a("")
    shown = [row for row in PROJECTS if row[0] in visible]
    hidden = [row for row in PROJECTS if row[0] not in visible]
    for repo, pitch, _logo in shown:
        p.extend(centered([
            "  " + img(f"https://github-readme-stats.vercel.app/api/pin/?username={USERNAME}"
                       f"&repo={repo}&card_width=360&{THEME}", repo),
        ]))
    for repo, pitch, _logo in hidden:
        a(f"- **{repo}** — {pitch} _(private, ask me for a look)_")
        a("")

    a("## 📊 Activity")
    a("")
    p.extend(centered([
        "    " + img(f"{STATS}/top-langs/?username={USERNAME}&layout=compact&card_width=340&{THEME}", "Top languages"),
    ]))

    a("<!-- github-snake.svg is regenerated nightly by .github/workflows/snake.yml -->")
    snake = f"https://raw.githubusercontent.com/{USERNAME}/{USERNAME}/github-snake"
    p.extend(centered([
        "    <picture>",
        f'      <source media="(prefers-color-scheme: dark)" srcset="{snake}/github-snake-dark.svg" />',
        f'      <source media="(prefers-color-scheme: light)" srcset="{snake}/github-snake.svg" />',
        f'      <img alt="snake eating my contributions" src="{snake}/github-snake.svg" width="100%" />',
        "    </picture>",
    ]))

    if THM_USER:
        card = f"https://tryhackme-badges.s3.amazonaws.com/tryhackme.com/{THM_USER}.png"
        if reachable(card):
            a("## 🚩 TryHackMe")
            a("")
            p.extend(centered([img(card, "TryHackMe profile card", "620")]))
        else:
            print(f"tryhackme card does not resolve for {THM_USER!r} - section skipped", file=sys.stderr)

    a("## 📫 Reach me")
    a("")
    links = [row for row in LINKS + EXTRA_LINKS
             if row[1].startswith("mailto:") or reachable(row[1])]
    for row in LINKS + EXTRA_LINKS:
        if row not in links:
            print(f"link does not resolve, skipped: {row[1]}", file=sys.stderr)
    tiles = " ".join(
        f'<a href="{href}">' + img(pill(label, logo, color), label) + "</a>"
        for label, href, logo, color in links
    )
    p.extend(centered([f"    {tiles}"]))
    a("> Prefer the noreply address — it reaches me and keeps the inbox out of public git history.")
    a("")
    a("<div align=\"center\">")
    a("")
    a("  " + img("assets/profile-card.png", "Profile card", "100%"))
    a("")
    a("</div>")
    a("")
    a("<div align=\"center\">")
    a("")
    a("> `while (alive) { learn(); build(); ship(); }`")
    a("")
    a("  " + img("https://capsule-render.vercel.app/api?type=waving&color=0:1f6feb,100:0d1117"
                 "&height=130&section=footer&text=stay%20haunting&fontSize=26&fontColor=c9d1d9"
                 "&fontAlignY=82", "footer wave", "100%"))
    a("")
    a("</div>")
    a("")

    (ROOT / "README.md").write_text("\n".join(p), encoding="utf-8", newline="\n")
    urls = re.findall(r'src="(https?://[^"]+)"', "\n".join(p))
    print(f"README.md written: {len(p)} lines, {len(urls)} remote images")


if __name__ == "__main__":
    build()
