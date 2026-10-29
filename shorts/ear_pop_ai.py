#!/usr/bin/env python3
"""Short #1, AI-visuals version: assemble shots generated in ChatGPT / Gemini / Veo.

Drop one file per narration line into a shots folder, named by line number:
  01.png  02.mp4  03.jpg ...   (images or video clips, any aspect ratio)
Images get a slow Ken Burns move; clips are cropped to 9:16, slowed down a
little if they are shorter than the line, then held on their last frame.
Missing shots render as a labelled placeholder, so you can preview at any time.
Narration, captions, music, SFX, HUD badges and "POP!" are the same as in the
2D and 3D versions, so the three are directly comparable. See shorts/ai/README.md.

  python3 shorts/ear_pop_ai.py --voice en_US-joe-medium.onnx --shots shorts/ai/ear_pop/shots
"""
import argparse
import math
import subprocess
import sys
from pathlib import Path

import skia

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from engine import FPS, H, W, Line, Short, back_out, clamp, paint, pill, text  # noqa: E402
from ear_pop import icon_card  # noqa: E402
from ear_pop_web3d import SCRIPT, ear_state, local_word  # noqa: E402

IMAGE_EXT = (".png", ".jpg", ".jpeg", ".webp")
VIDEO_EXT = (".mp4", ".mov", ".webm")
SAMPLING = skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear)


def find_shot(folder, n):
    for ext in VIDEO_EXT + IMAGE_EXT:
        p = folder / f"{n:02d}{ext}"
        if p.exists():
            return p
    return None


def clip_frames(src, out_dir, dur):
    """Decode a clip to 1080x1920 frames covering `dur` seconds."""
    out_dir.mkdir(parents=True, exist_ok=True)
    probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(src)],
                           capture_output=True, text=True, check=True)
    clip = float(probe.stdout.strip())
    slow = clamp(dur / clip, 1.0, 1.6)  # stretch short clips a little; hold the last frame for the rest
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-an", "-vf",
                    f"setpts={slow:.4f}*PTS,fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase,"
                    f"crop={W}:{H},tpad=stop_mode=clone:stop_duration={dur + 1:.2f}",
                    "-frames:v", str(int(dur * FPS) + 2), "-q:v", "3", str(out_dir / "%05d.jpg")], check=True)
    return sorted(out_dir.glob("*.jpg"))


class Shot:
    def __init__(self, n, path, dur, work):
        self.n, self.path = n, path
        self.frames, self.image = [], None
        if path is None:
            return
        if path.suffix.lower() in VIDEO_EXT:
            self.frames = clip_frames(path, work / f"clip{n:02d}", dur)
        else:
            self.image = skia.Image.MakeFromEncoded(skia.Data.MakeFromFileName(str(path)))

    def draw(self, c, t, dur):
        if self.frames:
            f = self.frames[min(int(t * FPS), len(self.frames) - 1)]
            c.drawImage(skia.Image.MakeFromEncoded(skia.Data.MakeFromFileName(str(f))), 0, 0)
        elif self.image:
            # Ken Burns: cover-fit, slow zoom, direction alternates per shot
            iw, ih = self.image.width(), self.image.height()
            k = clamp(t / max(dur, 0.1))
            zoom = 1.04 + 0.1 * (k if self.n % 2 else 1 - k)
            s = max(W / iw, H / ih) * zoom
            dw, dh = iw * s, ih * s
            pan = (k - 0.5) * (dw - W) * 0.5 * (1 if self.n % 3 else -1)
            c.drawImageRect(self.image, skia.Rect.MakeXYWH((W - dw) / 2 + pan, (H - dh) / 2, dw, dh), SAMPLING)
        else:
            c.drawPaint(paint(shader=skia.GradientShader.MakeLinear(
                [skia.Point(0, 0), skia.Point(0, H)], [skia.Color(40, 30, 60), skia.Color(10, 10, 20)])))
            text(c, f"SHOT {self.n:02d}", 540, 760, 120, weight="Black")
            text(c, "missing: drop the image/clip in shots/", 540, 860, 40, fill="#bbbbbb", weight="Bold")


def hud(c, st):
    popping = 0 <= st["pop_k"] < 1.1
    if st["alt"] is not None and not popping:
        pill(c, f"CABIN ALTITUDE  {int(st['alt']):,} FT", 540, 130, size=46, fill="#111827", fg="#ffffff")
    if st["cmp"] and not popping:
        col = {"=": "#2ec4b6", "<": "#ffb703", ">": "#ff4d4d"}[st["cmp"]]
        pill(c, f"OUTSIDE  {st['cmp']}  INSIDE", 540, 240, size=52, fill=col, fg="#111111")
    if st["pop_k"] >= 0:
        c.drawPaint(paint("#fff6c0", 200 * clamp(1 - st["pop_k"] / 0.25)))  # flash
        c.save()
        c.rotate(-8, 540, 300)
        text(c, "POP!", 540, 380, 230, fill="#ffd60a", stroke_w=26, weight="Black", scale=back_out(st["pop_k"] / 0.3, 2.6))
        c.restore()


def make_scene(shot, spec, overlay_name):
    def scene(c, t, dur, ctx):
        if spec.get("pop_word") and t >= local_word(ctx["words"], spec["pop_word"]):
            k = t - local_word(ctx["words"], spec["pop_word"])
            if k < 0.35:  # camera shake on the pop
                c.translate(math.sin(t * 90) * 16 * (1 - k / 0.35), math.cos(t * 77) * 16 * (1 - k / 0.35))
        shot.draw(c, t, dur)
        if spec["shot"] == "ear":
            hud(c, ear_state(spec["prev"], spec["target"], t, dur, ctx["words"], spec.get("tween", 0.7),
                             spec.get("alt_linear", False), spec.get("pop_word")))
        if overlay_name == "tips":
            for i, (word, label, kind) in enumerate((("swallowing", "SWALLOW", "drop"), ("yawning", "YAWN", "yawn"),
                                                    ("chewing", "CHEW GUM", "gum"))):
                icon_card(c, 200 + i * 340, 175, label, kind, back_out((t - local_word(ctx["words"], word)) / 0.35))
        if overlay_name == "cta":
            k = back_out(t / 0.4) * (1 + 0.05 * math.sin(ctx["now"] * 7))
            pill(c, "FOLLOW", 540, 120, size=80, fill="#ff0033", fg="#ffffff", scale=k, pad=50)
            text(c, "for more body facts", 540, 250, 52, stroke_w=12, alpha=255 * clamp(t / 0.4))
        if t < 0.12 and ctx["index"] > 0:  # quick dip between shots hides hard cuts
            c.drawPaint(paint("#000000", 255 * (1 - t / 0.12) * 0.6))
    return scene


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", required=True)
    ap.add_argument("--shots", default=str(HERE / "ai" / "ear_pop" / "shots"))
    ap.add_argument("--out", default="out/ear_pop_ai.mp4")
    ap.add_argument("--work", default="out/ear_pop_ai_work")
    a = ap.parse_args()
    shots_dir, work = Path(a.shots), Path(a.work)
    holders = []
    lines = []
    for i, (text_, spec, overlay, sfx, pause) in enumerate(SCRIPT):
        holder = {}
        holders.append(holder)
        lines.append(Line(text_, lambda c, t, d, ctx, h=holder: h["scene"](c, t, d, ctx), sfx, pause))
    short = Short(lines, a.voice, work)
    short._layout()
    found = 0
    for i, ((s, span, _), row, holder) in enumerate(zip(short.timeline, SCRIPT, holders)):
        dur = (short.total - s) if i == len(SCRIPT) - 1 else span
        path = find_shot(shots_dir, i + 1)
        found += path is not None
        print(f"line {i + 1:02d} ({dur:.1f}s): {path.name if path else 'MISSING'}")
        holder["scene"] = make_scene(Shot(i + 1, path, dur, work), row[1], row[2].__name__)
    short._layout = lambda: None
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    short.render(a.out)
    print(f"wrote {a.out} ({found}/{len(SCRIPT)} shots present)")
