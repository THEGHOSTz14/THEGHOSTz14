#!/usr/bin/env python3
"""Draw assets/profile-card.png - the closing card at the bottom of the README.

Numbers are pulled live from api.github.com so re-running before a push refreshes
them. Rendered as PNG, not SVG: GitHub does not reliably show SVGs hosted in a repo.
"""
import json
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "profile-card.png"
USERNAME = "THEGHOSTz14"
SCALE = 2
W, H = 620 * SCALE, 168 * SCALE

BG = (13, 17, 23)
BG2 = (19, 28, 40)
BORDER = (48, 54, 61)
TEAL = (79, 193, 233)
VIOLET = (146, 124, 233)
TEXT = (230, 237, 243)
MUTED = (139, 148, 158)


def api(path):
    req = urllib.request.Request(
        f"https://api.github.com{path}",
        headers={"User-Agent": "profile-card", "Accept": "application/vnd.github+json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def font(name, size):
    return ImageFont.truetype(name, size * SCALE)


def main():
    me = api(f"/users/{USERNAME}")
    repos = api(f"/users/{USERNAME}/repos?per_page=100")
    stars = sum(r["stargazers_count"] for r in repos)

    img = Image.new("RGBA", (W, H), BG + (255,))
    d = ImageDraw.Draw(img)
    for y in range(H):  # diagonal-ish vertical gradient
        t = y / H
        d.line([(0, y), (W, y)], fill=tuple(int(BG[i] + (BG2[i] - BG[i]) * t) for i in range(3)))
    d.rounded_rectangle([0, 0, W - 1, H - 1], radius=26 * SCALE, outline=BORDER, width=2 * SCALE)
    for i, c in enumerate((TEAL, VIOLET)):  # accent bar on the left edge
        d.rectangle([4 * SCALE, 34 * SCALE + i * 44 * SCALE, 9 * SCALE, 70 * SCALE + i * 44 * SCALE], fill=c)

    av = Image.open(ROOT / "assets" / "avatar-ghost.png").convert("RGB")
    side = min(av.size)
    av = av.crop(((av.width - side) // 2, (av.height - side) // 2,
                  (av.width + side) // 2, (av.height + side) // 2)).resize((112 * SCALE, 112 * SCALE), Image.LANCZOS)
    mask = Image.new("L", av.size, 0)
    ImageDraw.Draw(mask).ellipse([0, 0, av.size[0] - 1, av.size[1] - 1], fill=255)
    img.paste(av, (26 * SCALE, 28 * SCALE), mask)
    d.ellipse([24 * SCALE, 26 * SCALE, 140 * SCALE, 142 * SCALE], outline=TEAL, width=2 * SCALE)

    x = 164 * SCALE
    f_name = font("C:/Windows/Fonts/consolab.ttf", 25)
    f_sub = font("C:/Windows/Fonts/segoeui.ttf", 14)
    f_stat = font("C:/Windows/Fonts/consola.ttf", 15)
    f_url = font("C:/Windows/Fonts/consola.ttf", 13)

    name = USERNAME
    d.text((x, 26 * SCALE), name, font=f_name, fill=TEXT)
    w_name = d.textlength(name, font=f_name)
    bx, by = x + w_name + 22 * SCALE, 40 * SCALE
    d.polygon([(bx, by - 13 * SCALE), (bx - 7 * SCALE, by + 2 * SCALE), (bx - 1 * SCALE, by + 2 * SCALE),
               (bx - 3 * SCALE, by + 13 * SCALE), (bx + 8 * SCALE, by - 2 * SCALE), (bx + 1 * SCALE, by - 2 * SCALE)],
              fill=VIOLET)
    d.text((bx + 16 * SCALE, 28 * SCALE), "[x14]", font=font("C:/Windows/Fonts/consola.ttf", 18), fill=VIOLET)

    d.text((x, 66 * SCALE), "Rohan · Industrial Electrical & PLC Engineer · Godot 4", font=f_sub, fill=MUTED)

    stats = [("repos", me["public_repos"]), ("stars", stars),
             ("followers", me["followers"]), ("following", me["following"])]
    cx = x
    for label, value in stats:
        d.text((cx, 96 * SCALE), str(value), font=f_stat, fill=TEAL)
        vw = d.textlength(str(value), font=f_stat)
        d.text((cx + vw + 5 * SCALE, 98 * SCALE), label, font=f_sub, fill=MUTED)
        cx += vw + 5 * SCALE + d.textlength(label, font=f_sub) + 18 * SCALE

    d.text((x, 126 * SCALE), f"github.com/{USERNAME}", font=f_url, fill=(102, 153, 204))

    alpha = Image.new("L", (W, H), 0)
    ImageDraw.Draw(alpha).rounded_rectangle([0, 0, W - 1, H - 1], radius=26 * SCALE, fill=255)
    img.putalpha(alpha)
    img.save(OUT, optimize=True)
    print(f"{OUT} {img.size} (displayed at 620x168) · repos={me['public_repos']} stars={stars} "
          f"followers={me['followers']} following={me['following']}")


if __name__ == "__main__":
    main()
