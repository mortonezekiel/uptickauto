"""Original artwork for Uptick posts.

Every post gets three files, all drawn from scratch (no outside images, so no
licensing questions):

  card.png       1200x630 share card: brand, category, headline, trend line
  art-1600.webp  1600x900 abstract "uptick" chart used as the article hero
  art-800.webp   800x450 thumbnail of the same art

The trend line is decorative and seeded from the post's slug, so a post always
gets the same picture. It does not represent real data.
"""
from __future__ import annotations

import hashlib
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "theme" / "fonts"
ART_VERSION = 2
FILES = ("card.png", "art-1600.webp", "art-800.webp")

INK = (17, 24, 39)
MARK = (255, 226, 74)
WHITE = (255, 255, 255)
SOFT = (154, 165, 184)


def hex_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def mix(a, b, t: float):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _font(name: str, size: int, weight: int | None = None):
    font = ImageFont.truetype(str(FONTS / name), size)
    if weight is not None:
        try:
            font.set_variation_by_axes([weight])
        except Exception:
            pass
    return font


def display(size: int, weight: int = 800):
    return _font("SchibstedGrotesk-VF.ttf", size, weight)


def mono(size: int):
    return _font("DMMono-Medium.ttf", size)


def _rng(key: str) -> random.Random:
    return random.Random(int(hashlib.sha256(key.encode()).hexdigest()[:16], 16))


def _series(rng: random.Random, n: int = 60) -> list[float]:
    """A wandering line that drifts upward and surges at the end."""
    y, pts = 0.0, []
    drift = rng.uniform(0.002, 0.010)
    surge_at = rng.uniform(0.72, 0.84)
    for i in range(n):
        t = i / (n - 1)
        y += drift + rng.gauss(0, 0.032)
        if t > surge_at:
            y += rng.uniform(0.03, 0.08)
        pts.append(y)
    lo, hi = min(pts), max(pts)
    span = (hi - lo) or 1.0
    return [(p - lo) / span for p in pts]


def _smooth(vals: list[float], k: int = 2) -> list[float]:
    out = []
    for i in range(len(vals)):
        window = vals[max(0, i - k): i + k + 1]
        out.append(sum(window) / len(window))
    # keep the final surge crisp
    out[-1] = vals[-1]
    return out


def _points(vals, box):
    x0, y0, x1, y1 = box
    n = len(vals) - 1
    return [(x0 + (x1 - x0) * i / n, y1 - (y1 - y0) * v) for i, v in enumerate(vals)]


def _gradient(size, top, bottom):
    w, h = size
    img = Image.new("RGB", (1, h))
    for y in range(h):
        img.putpixel((0, y), mix(top, bottom, y / max(1, h - 1)))
    return img.resize((w, h))


def hero(slug: str, color: str, size=(1600, 900)) -> Image.Image:
    s = 2
    w, h = size[0] * s, size[1] * s
    base = hex_rgb(color)
    top, bottom = mix(base, (0, 0, 0), 0.18), mix(base, (0, 0, 0), 0.58)
    img = _gradient((w, h), top, bottom).convert("RGBA")
    draw = ImageDraw.Draw(img)

    step = 56 * s
    for gx in range(step // 2, w, step):
        for gy in range(step // 2, h, step):
            r = 2.2 * s
            draw.ellipse([gx - r, gy - r, gx + r, gy + r], fill=mix(bottom, WHITE, 0.16) + (255,))

    rng = _rng(slug)
    box = (0, h * 0.18, w * 0.9, h * 0.86)
    for k in range(3):
        faint = _points(_smooth(_series(rng), 3), (0, h * (0.22 + 0.07 * k), w * 0.9, h * 0.9))
        draw.line(faint, fill=mix(bottom, WHITE, 0.2) + (255,), width=3 * s, joint="curve")

    main = _points(_smooth(_series(rng), 2), box)
    area = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(area).polygon(main + [(main[-1][0], h), (0, h)], fill=mix(base, WHITE, 0.4) + (64,))
    img = Image.alpha_composite(img, area)
    draw = ImageDraw.Draw(img)
    draw.line(main, fill=mix(base, WHITE, 0.78) + (255,), width=10 * s, joint="curve")

    ex, ey = main[-1]
    halo = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    hd = ImageDraw.Draw(halo)
    for radius, alpha in ((46, 40), (32, 70)):
        r = radius * s
        hd.ellipse([ex - r, ey - r, ex + r, ey + r], fill=MARK + (alpha,))
    img = Image.alpha_composite(img, halo)
    draw = ImageDraw.Draw(img)
    r = 17 * s
    draw.ellipse([ex - r, ey - r, ex + r, ey + r], fill=MARK + (255,))
    return img.resize(size, Image.LANCZOS).convert("RGB")


def _wrap(text: str, font, max_width: float) -> list[str]:
    words, lines, line = text.split(), [], ""
    for word in words:
        trial = f"{line} {word}".strip()
        if font.getlength(trial) <= max_width or not line:
            line = trial
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def _badge(draw, x, y, size, s):
    draw.rounded_rectangle([x, y, x + size, y + size], radius=size * 0.25, fill=(32, 41, 60))
    u = size / 32
    pts = [(x + 7 * u, y + 21.5 * u), (x + 12.5 * u, y + 16 * u), (x + 16.5 * u, y + 19.5 * u), (x + 24.5 * u, y + 10 * u)]
    draw.line(pts, fill=MARK, width=round(3.2 * u), joint="curve")
    r = 2.6 * u
    draw.ellipse([x + 24.5 * u - r, y + 10 * u - r, x + 24.5 * u + r, y + 10 * u + r], fill=MARK)


def card(slug: str, title: str, category: str, color: str, site_name: str, size=(1200, 630)) -> Image.Image:
    s = 2
    w, h = size[0] * s, size[1] * s
    pad = 64 * s
    img = Image.new("RGBA", (w, h), INK + (255,))
    draw = ImageDraw.Draw(img)

    _badge(draw, pad, pad, 52 * s, s)
    draw.text((pad + 70 * s, pad + 26 * s), site_name, font=display(40 * s, 800), fill=WHITE, anchor="lm")

    cat_font = mono(24 * s)
    label = category.upper()
    lw = cat_font.getlength(label)
    cx = w - pad - lw
    sq = 14 * s
    draw.rectangle([cx - sq - 14 * s, pad + 26 * s - sq / 2, cx - 14 * s, pad + 26 * s + sq / 2], fill=hex_rgb(color))
    draw.text((cx, pad + 26 * s), label, font=cat_font, fill=SOFT, anchor="lm")

    size_px = 70
    while True:
        font = display(size_px * s, 800)
        lines = _wrap(title, font, w - 2 * pad)
        if len(lines) <= 3 or size_px <= 48:
            break
        size_px -= 4
    lines = lines[:3]
    line_h = size_px * s * 1.1
    ty = pad + 104 * s
    for i, line in enumerate(lines):
        draw.text((pad, ty + i * line_h), line, font=font, fill=WHITE)
    title_bottom = ty + len(lines) * line_h

    rng = _rng(slug)
    chart_top = max(title_bottom + 40 * s, h * 0.62)
    base = hex_rgb(color)
    pts = _points(_smooth(_series(rng), 2), (pad, chart_top, w - pad - 10 * s, h - 46 * s))
    area = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(area).polygon(pts + [(pts[-1][0], h), (pts[0][0], h)], fill=base + (90,))
    img = Image.alpha_composite(img, area)
    draw = ImageDraw.Draw(img)
    draw.line(pts, fill=mix(base, WHITE, 0.55) + (255,), width=7 * s, joint="curve")
    ex, ey = pts[-1]
    r = 14 * s
    draw.ellipse([ex - r, ey - r, ex + r, ey + r], fill=MARK + (255,))
    return img.resize(size, Image.LANCZOS).convert("RGB")


def make_post_media(slug: str, title: str, category: str, color: str, site_name: str, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    card(slug, title, category, color, site_name).save(out_dir / "card.png", optimize=True)
    art = hero(slug, color)
    art.save(out_dir / "art-1600.webp", quality=82, method=6)
    art.resize((800, 450), Image.LANCZOS).save(out_dir / "art-800.webp", quality=80, method=6)


def make_brand_assets(site_name: str, out_dir: Path) -> None:
    """Logo and icons in PNG for schema.org, Apple touch icon and favicon fallback."""
    out_dir.mkdir(parents=True, exist_ok=True)
    for px, name in ((512, "logo-512.png"), (180, "apple-touch-icon.png"), (32, "favicon-32.png")):
        s = 4
        big = Image.new("RGBA", (px * s, px * s), (0, 0, 0, 0))
        _badge(ImageDraw.Draw(big), 0, 0, px * s, s)
        big.resize((px, px), Image.LANCZOS).save(out_dir / name, optimize=True)
    # default share image for pages without their own
    s = 2
    w, h = 1200 * s, 630 * s
    img = Image.new("RGB", (w, h), INK)
    draw = ImageDraw.Draw(img)
    _badge(draw, w / 2 - 70 * s, 150 * s, 140 * s, s)
    draw.text((w / 2, 380 * s), site_name, font=display(110 * s, 800), fill=WHITE, anchor="mm")
    draw.text((w / 2, 470 * s), "WHY THE WORLD IS TALKING ABOUT IT", font=mono(26 * s), fill=SOFT, anchor="mm")
    img.resize((1200, 630), Image.LANCZOS).save(out_dir / "share-default.png", optimize=True)
