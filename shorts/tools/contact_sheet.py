#!/usr/bin/env python3
"""Lay images out as a labelled contact sheet (review sheets for the gates in production-process).

  python3 shorts/tools/contact_sheet.py OUT.jpg IMG [IMG ...] [--cols 4] [--width 360] [--label-from-name]
  python3 shorts/tools/contact_sheet.py OUT.jpg --dir DIR [--glob '*.png'] ...

Each tile is scaled to --width; its label is the file name (minus prefix/extension), or the text after '='
when given as path=label. The label sits in a bar under the tile, so it never covers the picture.
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def font(size):
    for p in ("/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf",
              str(Path(__file__).resolve().parents[2] / "fonts" / "Inter-ExtraBold.otf"),
              str(Path.home() / "Library" / "Fonts" / "Inter-ExtraBold.otf")):
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def main():
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    out, rest = a[0], a[1:]
    opt = lambda k, d: rest[rest.index(k) + 1] if k in rest else d   # noqa: E731
    cols, width = int(opt("--cols", 4)), int(opt("--width", 360))
    if "--dir" in rest:
        items = [str(p) for p in sorted(Path(opt("--dir", ".")).glob(opt("--glob", "*.png")))]
    else:
        skip = {"--cols", "--width", "--glob", "--dir"}
        items, i = [], 0
        while i < len(rest):
            if rest[i] in skip:
                i += 2
                continue
            items.append(rest[i])
            i += 1
    tiles = []
    for it in items:
        path, _, label = it.partition("=")
        im = Image.open(path).convert("RGB")
        im = im.resize((width, round(im.height * width / im.width)))
        tiles.append((im, label or Path(path).stem.split("_", 1)[-1].replace("_", " ")))
    th = max(t.height for t, _ in tiles)
    bar = max(28, width // 10)
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * width, rows * (th + bar)), (8, 12, 18))
    d = ImageDraw.Draw(sheet)
    f = font(int(bar * 0.6))
    for k, (im, label) in enumerate(tiles):
        x, y = (k % cols) * width, (k // cols) * (th + bar)
        sheet.paste(im, (x, y))
        d.text((x + width / 2, y + th + bar / 2), label, font=f, fill=(235, 235, 235), anchor="mm")
    sheet.save(out, quality=90)
    print(f"-> {out} ({len(tiles)} tiles)")


if __name__ == "__main__":
    main()
