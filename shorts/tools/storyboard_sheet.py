"""Storyboard sheets from a rendered animatic, for reviews (Codex can read images, not video).

    python3 shorts/tools/storyboard_sheet.py VIDEO.mp4 OUT_PREFIX [--plan shorts/pilot_ear_pop/plan.json]

For every shot: 3 frames (start, middle, end), labelled with the shot id, its time range and length,
the camera move and transition, and the caption spoken over it. Writes OUT_PREFIX_1.jpg,
OUT_PREFIX_2.jpg (6 shots per sheet) plus OUT_PREFIX_timing.md (the timing table, for the reviewer).
Only extracts frames from the video (ffmpeg); nothing is rendered.
"""
import json
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]


def font(size):
    for f in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/System/Library/Fonts/Helvetica.ttc"):
        if Path(f).exists():
            return ImageFont.truetype(f, size)
    return ImageFont.load_default()


def frame(video, n, fps, tmp):
    out = Path(tmp) / f"f{n}.png"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{(n - 1) / fps:.3f}", "-i", str(video),
                    "-frames:v", "1", "-vf", "scale=240:-1", str(out)], check=True)
    return Image.open(out).convert("RGB")


def caption_for(plan, sh):
    best = [c["text"] for c in plan["captions"] if c["start"] <= sh["end"] and c["end"] >= sh["start"]]
    return " / ".join(best) if best else ""


def main():
    a = sys.argv[1:]
    video, prefix = Path(a[0]), a[1]
    plan = json.loads(Path(a[a.index("--plan") + 1] if "--plan" in a else ROOT / "shorts/pilot_ear_pop/plan.json").read_text())
    fps = plan["fps"]
    shots = plan["shots"]
    f_small, f_big = font(13), font(17)
    rows, per = [], 6
    timing = ["| shot | time | length | move | out | beats (word @ s) | caption |", "|---|---|---|---|---|---|---|"]
    with tempfile.TemporaryDirectory() as tmp:
        for sh in shots:
            f0, f1 = sh["start"], sh["end"]
            imgs = [frame(video, f, fps, tmp) for f in (f0 + 1, (f0 + f1) // 2, max(f0 + 1, f1 - 1))]
            w, h = imgs[0].size
            row = Image.new("RGB", (w * 3 + 330, h), (24, 24, 28))
            for i, im in enumerate(imgs):
                row.paste(im, (i * w, 0))
            d = ImageDraw.Draw(row)
            x = w * 3 + 12
            secs = f"{(f0 - 1) / fps:.1f}-{f1 / fps:.1f}s ({(f1 - f0 + 1) / fps:.1f}s)"
            d.text((x, 10), f"{sh['id']}  {secs}", fill=(255, 220, 90), font=f_big)
            d.text((x, 38), f"{sh.get('size', '')} {sh.get('angle', '')}  move: {sh.get('move', '')}", fill=(220, 220, 220), font=f_small)
            d.text((x, 58), f"out: {sh.get('out', 'cut')}", fill=(220, 220, 220), font=f_small)
            beats = ", ".join(f"{b['word']}@{(b['frame'] - 1) / fps:.1f}s" for b in sh.get("beats", []) if b.get("word"))
            y = 82
            for line in textwrap.wrap("beats: " + beats, 40)[:4]:
                d.text((x, y), line, fill=(170, 200, 255), font=f_small)
                y += 17
            y += 6
            for line in textwrap.wrap('"' + caption_for(plan, sh) + '"', 40)[:7]:
                d.text((x, y), line, fill=(255, 255, 255), font=f_small)
                y += 17
            rows.append(row)
            timing.append(f"| {sh['id']} | {(f0 - 1) / fps:.1f}-{f1 / fps:.1f}s | {(f1 - f0 + 1) / fps:.1f}s | "
                          f"{sh.get('move', '')} | {sh.get('out', 'cut')} | {beats} | {caption_for(plan, sh)} |")
    outs = []
    for k in range(0, len(rows), per):
        chunk = rows[k:k + per]
        sheet = Image.new("RGB", (chunk[0].width, sum(r.height for r in chunk) + 4 * len(chunk)), (0, 0, 0))
        y = 0
        for r in chunk:
            sheet.paste(r, (0, y))
            y += r.height + 4
        out = f"{prefix}_{k // per + 1}.jpg"
        sheet.save(out, quality=82)
        outs.append(out)
    Path(f"{prefix}_timing.md").write_text("\n".join(timing) + "\n")
    print("\n".join(outs + [f"{prefix}_timing.md"]))


main()
