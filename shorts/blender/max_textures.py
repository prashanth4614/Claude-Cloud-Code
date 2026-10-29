"""Recolour MPFB's CC0 male_casualsuit06 texture to Max's outfit (run with system python + Pillow).

White logo tee -> plain teal tee (logo removed, fabric shading kept); light-wash jeans -> dark jeans.
Writes assets/characters/max/textures/max_outfit_diffuse.png, which build_max.py loads.

    python3 shorts/blender/max_textures.py [path/to/male_casualsuit06_diffuse.png]
"""
import os
import sys

from PIL import Image, ImageFilter, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_SRC = os.path.expanduser(
    "~/.config/blender/4.5/extensions/.user/user_default/mpfb/data/clothes/male_casualsuit06/male_casualsuit06_diffuse.png")
OUT = os.path.join(ROOT, "assets/characters/max/textures/max_outfit_diffuse.png")

TEAL = (20, 98, 104)       # reference sheet tee
SHIRT_BOTTOM = 0.43         # UV layout: tee in the top 43%, jeans below
JEANS_DARKEN = 0.52


def main(src):
    im = Image.open(src).convert("RGB")
    w, h = im.size
    cut = int(h * SHIRT_BOTTOM)
    shirt, jeans = im.crop((0, 0, w, cut)), im.crop((0, cut, w, h))

    # Tee: keep the fabric's light and folds, drop the printed logo (anything saturated or dark).
    lum = ImageOps.grayscale(shirt)
    hsv = shirt.convert("HSV")
    sat, val = hsv.getchannel("S"), hsv.getchannel("V")
    logo = Image.eval(sat, lambda s: 255 if s > 22 else 0)
    logo = Image.composite(logo, Image.eval(val, lambda v: 255 if v < 205 else 0), logo)
    logo = logo.filter(ImageFilter.MaxFilter(15)).filter(ImageFilter.GaussianBlur(6))
    mean = sum(lum.resize((64, 64)).tobytes()) / 4096.0
    # Fill the logo with the fabric's average tone before blurring, so no dark ghost bleeds in.
    hard = logo.point(lambda v: 255 if v > 8 else 0)
    smooth = Image.composite(Image.new("L", lum.size, int(mean)), lum, hard).filter(ImageFilter.GaussianBlur(24))
    lum = Image.composite(smooth, lum, logo)
    tee = Image.merge("RGB", [lum.point(lambda v, c=c: max(0, min(255, int(c * v / mean)))) for c in TEAL])

    # Jeans: darker, a touch less saturated.
    r, g, b = jeans.split()
    grey = ImageOps.grayscale(jeans)
    jeans = Image.merge("RGB", [Image.blend(ch, grey, 0.25).point(lambda v: int(v * JEANS_DARKEN)) for ch in (r, g, b)])

    out = Image.new("RGB", (w, h))
    out.paste(tee, (0, 0))
    out.paste(jeans, (0, cut))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    out.save(OUT, optimize=True)
    print("wrote", OUT)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SRC)
