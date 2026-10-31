#!/usr/bin/env python3
"""The channel's house colour grade: our own look, so a Short reads as ours in the feed (not Zack D Films'
bright sky-blue high-key). Used by the shorts-craft skill for every new video.

  python3 shorts/look/house_grade.py preview IN.jpg [IN2.jpg ...] OUT.jpg   # side-by-side looks
  python3 shorts/look/house_grade.py lut LOOK OUT.cube                      # a .cube LUT (Blender, Resolve, ffmpeg)
  python3 shorts/look/house_grade.py frames LOOK IN_DIR OUT_DIR             # grade rendered frames (+ grain, vignette)

Looks: ink_amber is THE house look (the owner's choice, 2026-10-31); clay_sky is kept only for reference.
- ink_amber: "dark-mode science". Deep ink-teal shadows, warm amber highlights and skin, lifted matte
  blacks, slightly richer mids. The warm subject glows out of a cool dark world.
- clay_sky: "warm paper". Soft cream highlights, clay-warm mids, dusty sky-blue shadows, low contrast,
  gentle film fade. Calm and friendly; closer to Zack's brightness but warmer and matte.
The grade is display-referred (applied to the 8-bit render), so it is the same in every app via the LUT.
"""
import sys
from pathlib import Path

import numpy as np

LOOKS = {
    # lift: matte black level; shadow / highlight: split-tone tints (RGB offsets, weighted by darkness /
    # brightness); curve: midtone contrast; sat: saturation; warm_sat: saturation on warm hues (skin,
    # anatomy); cool_dim: darkening of cool, unsaturated areas (backgrounds) so the warm subject pops
    "ink_amber": {"lift": 0.03, "shadow": (-0.07, 0.03, 0.10), "highlight": (0.09, 0.035, -0.06),
                  "curve": 0.45, "sat": 0.78, "warm_sat": 1.22, "gamma": 1.18, "cool_dim": 0.22},
    "clay_sky": {"lift": 0.09, "shadow": (-0.03, 0.04, 0.10), "highlight": (0.07, 0.045, 0.0),
                 "curve": 0.08, "sat": 0.8, "warm_sat": 1.15, "gamma": 0.9, "cool_dim": 0.0},
}


def grade(rgb, look):
    """rgb: float array 0..1 (..., 3) -> graded."""
    p = LOOKS[look]
    x = np.clip(rgb, 0, 1) ** p["gamma"]
    lum = (x * [0.2126, 0.7152, 0.0722]).sum(-1, keepdims=True)
    x = x + np.array(p["shadow"]) * (1 - lum) ** 2 + np.array(p["highlight"]) * lum ** 2   # split tone
    x = x + p["curve"] * (x - 0.5) * (1 - np.abs(2 * x - 1))                              # soft S-curve on mids
    lum = (x * [0.2126, 0.7152, 0.0722]).sum(-1, keepdims=True)
    warm = np.clip((x[..., :1] - x[..., 2:3]) * 4, 0, 1)                                  # red > blue: skin, tissue
    s = p["sat"] + (p["warm_sat"] - p["sat"]) * warm
    x = lum + (x - lum) * s
    x = x * (1 - p["cool_dim"] * (1 - warm) * (1 - lum))                                 # sink the cool background
    x = p["lift"] + x * (1 - p["lift"])                                                    # matte blacks
    return np.clip(x, 0, 1)


def finish(img, look, seed=0):
    """Grade + the house finishing: soft vignette and fine grain (the grain also hides banding)."""
    h, w, _ = img.shape
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
    vig = 1 - 0.18 * np.clip(r - 0.55, 0, 1) ** 1.5
    out = grade(img, look) * vig[..., None]
    out = out + np.random.default_rng(seed).normal(0, 0.012, out.shape[:2])[..., None]
    return np.clip(out, 0, 1)


def write_cube(look, path, n=33):
    g = np.linspace(0, 1, n)
    b, gg, r = np.meshgrid(g, g, g, indexing="ij")           # .cube order: red fastest
    rgb = grade(np.stack([r, gg, b], -1).reshape(-1, 3), look)
    with open(path, "w") as f:
        f.write(f'TITLE "{look}"\nLUT_3D_SIZE {n}\n')
        for v in rgb:
            f.write(f"{v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")


def load(p):
    from PIL import Image
    return np.asarray(Image.open(p).convert("RGB")).astype(np.float64) / 255


def save(a, p):
    from PIL import Image
    Image.fromarray((a * 255 + 0.5).astype(np.uint8)).save(p, quality=92)


def preview(ins, out):
    """Rows: the given frames; columns: the render as is, then each look."""
    from PIL import Image, ImageDraw, ImageFont
    tw, th = 270, 480
    cols = ["as rendered"] + list(LOOKS)
    sheet = Image.new("RGB", (tw * len(cols), th * len(ins) + 44), (0, 0, 0))
    d = ImageDraw.Draw(sheet)
    try:
        f = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf", 26)
    except OSError:
        f = ImageFont.load_default()
    for c, name in enumerate(cols):
        d.text((c * tw + tw / 2, 22), name, font=f, fill=(255, 255, 255), anchor="mm")
    for r, p in enumerate(ins):
        a = load(p)
        for c, name in enumerate(cols):
            g = a if c == 0 else finish(a, name)
            im = Image.fromarray((g * 255 + 0.5).astype(np.uint8)).resize((tw, th))
            sheet.paste(im, (c * tw, 44 + r * th))
    sheet.save(out, quality=88)


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "preview":
        preview(a[1:-1], a[-1])
    elif a[0] == "lut":
        write_cube(a[1], a[2])
    elif a[0] == "frames":
        src, dst = Path(a[2]), Path(a[3])
        dst.mkdir(parents=True, exist_ok=True)
        for i, p in enumerate(sorted(src.glob("*.jpg"))):
            save(finish(load(p), a[1], seed=i), dst / p.name)
