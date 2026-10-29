#!/usr/bin/env python3
"""Short #1, 3D version: "Why do your ears pop on a plane?"

Same script, voice, captions, music and SFX as shorts/ear_pop.py, but every
background is a Blender render (shorts/blender/ear_pop_3d.py). Steps:

  1. TTS every line (engine.Short) to get exact line timings,
  2. render one Blender PNG plate per line, as long as that line is on screen,
  3. composite: plate + 2D HUD (labels, altitude, OUTSIDE vs INSIDE, POP!) +
     captions + audio -> MP4.

  python3 shorts/ear_pop_3d.py --voice voices/en_US-joe-medium.onnx --out out/ear_pop_3d.mp4
  python3 shorts/ear_pop_3d.py --voice ... --res 540x960 --lines 0 1 8 --out out/test.mp4  # quick test

Plates are cached per resolution in <work>/plates/<res>/lineNN and only
re-rendered when a line's length changes (or with --force).
"""
import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import skia

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "blender"))
from ear_pop import icon_card, shake  # noqa: E402
from ear_states import SHOTS, ear_state, word_at  # noqa: E402
from engine import (FPS, H, W, Line, Plate, Short, back_out, clamp, ease_out,  # noqa: E402
                    font, paint, pill, text)

BLENDER = os.environ.get("BLENDER") or shutil.which("blender") or "/Applications/Blender.app/Contents/MacOS/Blender"

# (text, sfx, pause) per line; SHOTS[i] in ear_states.py describes the visuals.
SCRIPT = [
    ("Ever wondered why your ears pop on a plane?", [(0, "whoosh"), (0.1, "rumble")], 0.18),
    ("Here's what's actually happening inside your head.", [], 0.18),
    ("Behind your eardrum is a tiny pocket of air, called the middle ear.",
     [(0, "whoosh"), ("eardrum", "ding"), ("middle", "ding")], 0.18),
    ("On the ground, the air pressure inside matches the air outside.", [("matches", "ding")], 0.18),
    ("But as the plane climbs, the air pressure in the cabin drops.", [(0.2, "rumble")], 0.18),
    ("The air trapped inside pushes out, and your eardrum bulges like a balloon.", [("bulges", "thud")], 0.18),
    ("That's the muffled, blocked feeling.", [], 0.18),
    ("Then a tiny tube to your throat, the Eustachian tube, cracks open.", [("eustachian", "ding")], 0.18),
    ("Air escapes, the pressure evens out, and... POP!", [("pop!", "pop")], 0.45),
    ("Landing is actually worse.", [(0, "whoosh")], 0.18),
    ("The tube doesn't open on its own as easily, so your eardrum gets pushed inward.", [("inward.", "thud")], 0.18),
    ("That's why swallowing, yawning, or chewing gum helps. They pull the tube open.",
     [(0, "whoosh"), ("swallowing,", "pop"), ("yawning,", "pop"), ("chewing", "pop")], 0.18),
    ("Follow for more weird things your body does.", [(0, "ding")], 0.6),
]

# label text and offset (px, 1080-wide frame) from its 3D anchor
LABELS = {"canal": ("EAR CANAL", (40, -120)), "drum": ("EARDRUM", (-150, 150)),
          "middle": ("MIDDLE EAR", (100, -130)), "tube": ("EUSTACHIAN TUBE", (200, -70)),
          "throat": ("THROAT", (-150, 40))}


class Anchors:
    """Per-frame screen positions of 3D points, written by the Blender script."""

    def __init__(self, plate_dir):
        self.path, self.data = Path(plate_dir) / "anchors.json", None

    def __call__(self, name, t):
        if self.data is None:
            self.data = json.loads(self.path.read_text())["anchors"]
        pts = self.data[name]
        x, y = pts[int(clamp(math.floor(t * FPS + 1e-6), 0, len(pts) - 1))]
        return x * W, y * H


# ------------------------------------------------------------------ scenes --
def plane_scene(plate, anchors, i):
    def scene(c, t, dur, ctx):
        plate.draw(c, t)
    return scene


def cabin_scene(plate, anchors, i):
    cam = SHOTS[i]["cam"]

    def scene(c, t, dur, ctx):
        plate.draw(c, t)
        now = ctx["now"]
        if cam == "zoom_ear":  # pulsing ring on the ear we're about to fly into
            x, y = anchors("ear", t)
            tx, ty = anchors("ear_top", t)
            r = 1.5 * math.hypot(tx - x, ty - y) + 12 * (0.5 + 0.5 * math.sin(now * 8))
            a = 255 * clamp(t / 0.3) * clamp((600 - r) / 250)
            if a > 1:
                c.drawCircle(x, y, r, paint("#ffd60a", a * 0.86, stroke=10))
                c.drawCircle(x, y, r, paint("#ffd60a", a * 0.47, stroke=24, blur=14))
        elif cam == "tips":
            for k, (word, label, kind) in enumerate((("swallowing", "SWALLOW", "drop"),
                                                    ("yawning", "YAWN", "yawn"),
                                                    ("chewing", "CHEW GUM", "gum"))):
                icon_card(c, 200 + k * 340, 360, label, kind, back_out((t - word_at(ctx["words"], word)) / 0.35))
        elif cam == "cta":
            k = back_out(t / 0.4) * (1 + 0.05 * math.sin(now * 7))
            pill(c, "FOLLOW", 540, 330, size=80, fill="#ff0033", fg="#ffffff", scale=k, pad=50)
            text(c, "for more body facts", 540, 460, 50, stroke_w=10, alpha=255 * clamp(t / 0.4))
    return scene


def ear_scene(plate, anchors, i):
    shot = SHOTS[i]

    def scene(c, t, dur, ctx):
        st, pw = ear_state(shot, t, dur, ctx["words"])
        now = ctx["now"]
        pop_at = now - t + pw if pw is not None else None
        if pop_at is not None:
            shake(c, now, pop_at)
        plate.draw(c, t)
        for key, at in st["labels"]:
            if t < at:
                continue
            k = back_out((t - at) / 0.35)
            label, (dx, dy) = LABELS[key]
            ax, ay = anchors(key, t)
            half = font(38).measureText(label) / 2 + 46  # keep the pill on screen
            lx, ly = clamp(ax + dx, half, W - half), ay + dy
            c.drawLine(lx, ly, ax, ay, paint("#ffffff", 230 * clamp(k), stroke=5))
            c.drawCircle(ax, ay, 9, paint("#ffffff", 255 * clamp(k)))
            pill(c, label, lx, ly, size=38, scale=k)
        if st["red"] > 0.01:  # the tube can't open: red "X" badge
            x, y = anchors("tube_x", t)
            c.drawCircle(x, y, 38, paint("#ff4d4d", 255 * st["red"]))
            for s in (-1, 1):
                c.drawLine(x - 18, y - 18 * s, x + 18, y + 18 * s, paint("#ffffff", 255 * st["red"], stroke=9))
        popping = pop_at is not None and 0 <= now - pop_at < 1.1
        if st["alt"] is not None and not popping:
            pill(c, f"CABIN ALTITUDE  {int(st['alt']):,} FT", 540, 230, size=46, fill="#111827", fg="#ffffff")
        if st["cmp"] and not popping:
            col = {"=": "#2ec4b6", "<": "#ffb703", ">": "#ff4d4d"}[st["cmp"]]
            pill(c, f"OUTSIDE  {st['cmp']}  INSIDE", 540, 350, size=52, fill=col, fg="#111111")
        if pop_at is not None and now >= pop_at:
            k = now - pop_at
            cx, cy = anchors("drum_c", t)
            for j in range(14):
                ang = j / 14 * 2 * math.pi
                r0, r1 = 60 + 380 * ease_out(k / 0.4), 120 + 420 * ease_out(k / 0.4)
                c.drawLine(cx + math.cos(ang) * r0, cy + math.sin(ang) * r0,
                           cx + math.cos(ang) * r1, cy + math.sin(ang) * r1,
                           paint("#ffd60a", 255 * clamp(1 - k / 0.5), stroke=12))
            c.save()
            c.rotate(-8, 540, 380)
            text(c, "POP!", 540, 420, 230, fill="#ffd60a", stroke_w=26, weight="Black", scale=back_out(k / 0.3, 2.6))
            c.restore()
        if shot.get("intro") and t < 0.3:  # white flash in from the ear close-up
            c.drawPaint(paint("#ffffff", 255 * (1 - t / 0.3)))
    return scene


SCENES = {"plane": plane_scene, "cabin": cabin_scene, "ear": ear_scene}


# ------------------------------------------------------------------ plates --
def render_plates(short, idx, plates, res, samples, force):
    total_frames, total_time = 0, 0.0
    for j, (start, span, words) in enumerate(short.spans()):
        i = idx[j]
        d = plates / f"line{i:02d}"
        n = max(1, math.ceil(span * FPS - 1e-6))
        meta = d / "anchors.json"
        stale = force or not meta.exists() or json.loads(meta.read_text())["frames"] != n \
            or len(list(d.glob("*.png"))) != n
        if not stale:
            print(f"line {i:2d}: cached ({n} frames)")
            continue
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True)
        wj = d / "words.json"
        wj.write_text(json.dumps({"start": start, "words": words}))
        print(f"line {i:2d}: rendering {n} frames ({span:.2f}s) ...", flush=True)
        t0 = time.time()
        r = subprocess.run([BLENDER, "-b", "--factory-startup", "-P", str(HERE / "blender" / "ear_pop_3d.py"), "--",
                            "--line", str(i), "--out", str(d), "--res", res, "--fps", str(FPS),
                            "--seconds", f"{span:.6f}", "--words", str(wj), "--samples", str(samples)],
                           capture_output=True, text=True)
        if r.returncode or len(list(d.glob("*.png"))) != n:
            print(r.stdout[-3000:], r.stderr[-3000:])
            raise RuntimeError(f"Blender failed on line {i}")
        el = time.time() - t0
        total_frames, total_time = total_frames + n, total_time + el
        print(f"         done in {el:.0f}s ({el / n:.2f}s/frame)", flush=True)
    if total_frames:
        print(f"plates: {total_frames} frames in {total_time / 60:.1f} min, "
              f"{total_time / total_frames:.2f}s/frame incl. Blender startup")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", required=True, help="Piper .onnx voice (en_US-joe-medium: CC0)")
    ap.add_argument("--out", default="out/ear_pop_3d.mp4")
    ap.add_argument("--work", default="out/ear_pop_3d_work")
    ap.add_argument("--res", default="1080x1920", help="Blender plate resolution")
    ap.add_argument("--samples", type=int, default=24, help="EEVEE samples per frame")
    ap.add_argument("--lines", type=int, nargs="*", help="only these lines (quick tests)")
    ap.add_argument("--preview", type=float, nargs="*", help="write PNG stills at these seconds instead")
    ap.add_argument("--force", action="store_true", help="re-render all plates")
    a = ap.parse_args()
    idx = a.lines if a.lines else list(range(len(SCRIPT)))
    plates = Path(a.work) / "plates" / a.res
    lines = []
    for i in idx:
        txt, fx, pause = SCRIPT[i]
        d = plates / f"line{i:02d}"
        lines.append(Line(txt, SCENES[SHOTS[i]["shot"]](Plate(d), Anchors(d), i), fx, pause))
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    short = Short(lines, a.voice, a.work)
    render_plates(short, idx, plates, a.res, a.samples, a.force)
    t0 = time.time()
    short.render(a.out, preview=a.preview)
    print(f"composite: {time.time() - t0:.0f}s -> {a.out} ({short.total:.1f}s)")


if __name__ == "__main__":
    main()
