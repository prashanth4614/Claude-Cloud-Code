#!/usr/bin/env python3
"""Short #1 in 3D: real-time Three.js plates rendered in headless Chromium.

Same narration, timing, sound and captions as ear_pop.py; only the visuals
change. Python computes the per-frame story state (eardrum bulge, tube
opening, pressure...), threejs/render_plates.mjs renders the 3D plates, and
skia composites labels, HUD badges, "POP!" and captions on top.

  python3 shorts/ear_pop_web3d.py --voice en_US-joe-medium.onnx --out out/ear_pop_web3d.mp4
"""
import argparse
import json
import math
import subprocess
import sys
from pathlib import Path

import skia

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from engine import FPS, Line, Short, back_out, clamp, ease, elastic_out, lerp, paint, pill, text  # noqa: E402
from ear_pop import DEFAULT, icon_card  # noqa: E402

# Story states, identical to the 2D version's s0..s8.
S0 = dict(DEFAULT, labels=(("canal", 0.2), ("drum", 0.9), ("middle", 1.9)))
S1 = dict(S0, labels=(), arrows=1.0, alt=0, cmp="=")
S2 = dict(S1, alt=8000, p_out=0.45, cmp="<")
S3 = dict(S2, bulge=1.0)
S4 = dict(S3, waves=1.0)
S5 = dict(S4, waves=0.0, tube=1.0, flow=1.0, labels=(("tube", 0.9), ("throat", 1.4)))
S6 = dict(S5, labels=(), bulge=0.0, p_out=0.45, cmp="=", tube=0.2, flow=0.0)
S7 = dict(S6, alt=0, p_out=1.0, cmp=">", tube=0.0)
S8 = dict(S7, bulge=-1.0, red=1.0)

LABELS = {"canal": ("EAR CANAL", (0, -120)), "drum": ("EARDRUM", (-140, 150)),
          "middle": ("MIDDLE EAR", (-60, -40)), "tube": ("EUSTACHIAN TUBE", (40, 120)),
          "throat": ("THROAT", (180, 40))}


def local_word(words, w):
    w = w.strip(",.!?").lower()
    return next(s for x, s, e in words if x == w)


def ear_state(prev, target, t, dur, words, tween=0.7, alt_linear=False, pop_word=None):
    """Pure version of ear_pop.diag_scene's interpolation."""
    pw = local_word(words, pop_word) if pop_word else None
    st = {}
    for k, v in target.items():
        p = prev.get(k, v)
        if k == "labels":
            st[k] = v
        elif k == "alt" and v is not None and p is not None:
            st[k] = lerp(p, v, ease(t / (dur * 0.9)) if alt_linear else ease(t / tween))
        elif isinstance(v, (int, float)) and isinstance(p, (int, float)):
            x = ease(t / tween)
            if pw is not None and k in ("bulge", "p_out"):
                x = elastic_out((t - pw) / 0.9) if t >= pw else 0
            st[k] = lerp(p, v, x)
        elif pw is not None and t < pw:
            st[k] = p
        else:
            st[k] = v
    st["pop_k"] = (t - pw) if pw is not None and t >= pw else -1
    return st


class Plates:
    """Shared frame store: scene functions look up the plate for `now`."""
    dir = None
    anchors = []
    states = {}

    @classmethod
    def draw(cls, c, now):
        n = min(int(round(now * FPS)), len(cls.anchors) - 1)
        img = skia.Image.MakeFromEncoded(skia.Data.MakeFromFileName(str(cls.dir / f"{n:05d}.jpg")))
        c.drawImage(img, 0, 0)
        return n


def ear_overlay(c, t, dur, ctx, spec):
    n = Plates.draw(c, ctx["now"])
    st = Plates.states[n]
    anchors = Plates.anchors[n] or {}
    for key, appear in st["labels"]:
        if t < appear or key not in anchors:
            continue
        k = back_out((t - appear) / 0.35)
        label, (dx, dy) = LABELS[key]
        ax, ay = anchors[key]
        lx, ly = clamp(ax + dx, 190, 890), ay + dy
        c.drawLine(lx, ly, ax, ay, paint("#ffffff", 230 * clamp(k), stroke=5))
        c.drawCircle(ax, ay, 10, paint("#ffffff", 255 * clamp(k)))
        pill(c, label, lx, ly, size=40, scale=k)
    popping = 0 <= st["pop_k"] < 1.1
    if st["alt"] is not None and not popping:
        pill(c, f"CABIN ALTITUDE  {int(st['alt']):,} FT", 540, 130, size=46, fill="#111827", fg="#ffffff")
    if st["cmp"] and not popping:
        col = {"=": "#2ec4b6", "<": "#ffb703", ">": "#ff4d4d"}[st["cmp"]]
        pill(c, f"OUTSIDE  {st['cmp']}  INSIDE", 540, 240, size=52, fill=col, fg="#111111")
    if st["pop_k"] >= 0:
        c.save()
        c.rotate(-8, 540, 300)
        text(c, "POP!", 540, 380, 230, fill="#ffd60a", stroke_w=26, weight="Black",
             scale=back_out(st["pop_k"] / 0.3, 2.6))
        c.restore()
    if spec.get("intro") and t < 0.3:
        c.drawPaint(paint("#ffffff", 255 * (1 - t / 0.3)))


def plain(c, t, dur, ctx, spec):
    Plates.draw(c, ctx["now"])


def tips(c, t, dur, ctx, spec):
    Plates.draw(c, ctx["now"])
    for i, (word, label, kind) in enumerate((("swallowing", "SWALLOW", "drop"), ("yawning", "YAWN", "yawn"),
                                            ("chewing", "CHEW GUM", "gum"))):
        icon_card(c, 200 + i * 340, 300, label, kind, back_out((t - local_word(ctx["words"], word)) / 0.35))


def cta(c, t, dur, ctx, spec):
    Plates.draw(c, ctx["now"])
    k = back_out(t / 0.4) * (1 + 0.05 * math.sin(ctx["now"] * 7))
    pill(c, "FOLLOW", 540, 300, size=80, fill="#ff0033", fg="#ffffff", scale=k, pad=50)
    text(c, "for more body facts", 540, 430, 52, stroke_w=12, alpha=255 * clamp(t / 0.4))


# Each line: narration, 3D shot spec, overlay, sfx, pause. Mirrors ear_pop.build().
SCRIPT = [
    ("Ever wondered why your ears pop on a plane?", dict(shot="plane"), plain, [(0, "whoosh"), (0.1, "rumble")], 0.18),
    ("Here's what's actually happening inside your head.", dict(shot="cabin", zoom=True, look=[1, 0]), plain, [], 0.18),
    ("Behind your eardrum is a tiny pocket of air, called the middle ear.",
     dict(shot="ear", prev=S0, target=S0, intro=True), ear_overlay, [(0, "whoosh"), ("eardrum", "ding"), ("middle", "ding")], 0.18),
    ("On the ground, the air pressure inside matches the air outside.",
     dict(shot="ear", prev=S0, target=S1), ear_overlay, [("matches", "ding")], 0.18),
    ("But as the plane climbs, the air pressure in the cabin drops.",
     dict(shot="ear", prev=S1, target=S2, alt_linear=True), ear_overlay, [(0.2, "rumble")], 0.18),
    ("The air trapped inside pushes out, and your eardrum bulges like a balloon.",
     dict(shot="ear", prev=S2, target=S3, tween=1.6), ear_overlay, [("bulges", "thud")], 0.18),
    ("That's the muffled, blocked feeling.", dict(shot="ear", prev=S3, target=S4), ear_overlay, [], 0.18),
    ("Then a tiny tube to your throat, the Eustachian tube, cracks open.",
     dict(shot="ear", prev=S4, target=S5, tween=1.2), ear_overlay, [("eustachian", "ding")], 0.18),
    ("Air escapes, the pressure evens out, and... POP!",
     dict(shot="ear", prev=S5, target=S6, pop_word="pop!"), ear_overlay, [("pop!", "pop")], 0.45),
    ("Landing is actually worse.", dict(shot="ear", prev=S6, target=S7, alt_linear=True), ear_overlay, [(0, "whoosh")], 0.18),
    ("The tube doesn't open on its own as easily, so your eardrum gets pushed inward.",
     dict(shot="ear", prev=S7, target=S8, tween=1.4), ear_overlay, [("inward.", "thud")], 0.18),
    ("That's why swallowing, yawning, or chewing gum helps. They pull the tube open.",
     dict(shot="cabin", expr="yawn", smile_after="chewing"), tips,
     [(0, "whoosh"), ("swallowing,", "pop"), ("yawning,", "pop"), ("chewing", "pop")], 0.18),
    ("Follow for more weird things your body does.", dict(shot="cabin", expr="smile", look=[0, -1]), cta, [(0, "ding")], 0.6),
]


def make_line(text_, spec, overlay, sfx, pause):
    return Line(text_, lambda c, t, d, ctx, s=spec, o=overlay: o(c, t, d, ctx, s), sfx, pause)


def jobs_for(short):
    jobs, states = [], {}
    n_frames = int(short.total * FPS)
    for n in range(n_frames):
        now = n / FPS
        idx = max(i for i, (s, _, _) in enumerate(short.timeline) if s <= max(now, short.timeline[0][0]))
        start, span, _ = short.timeline[idx]
        if idx == len(short.timeline) - 1:
            span = short.total - start
        t = now - start
        spec = SCRIPT[idx][1]
        words = short.line_words[idx]
        job = {"shot": spec["shot"], "now": now, "t": t, "dur": span}
        if spec["shot"] == "cabin":
            job["zoom"] = spec.get("zoom", False)
            job["look"] = spec.get("look", [0, 0])
            expr = spec.get("expr", "neutral")
            if spec.get("smile_after") and t >= local_word(words, spec["smile_after"]) + 0.6:
                expr = "smile"
            job["expr"] = expr
        if spec["shot"] == "ear":
            st = ear_state(spec["prev"], spec["target"], t, span, words, spec.get("tween", 0.7),
                           spec.get("alt_linear", False), spec.get("pop_word"))
            states[n] = st
            job["st"] = {k: st[k] for k in ("p_out", "bulge", "tube", "arrows", "waves", "flow", "red", "pop_k")}
        jobs.append(job)
    return jobs, states


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", required=True)
    ap.add_argument("--out", default="out/ear_pop_web3d.mp4")
    ap.add_argument("--work", default="out/ear_pop_web3d_work")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--reuse-plates", action="store_true", help="skip 3D rendering if plates exist")
    a = ap.parse_args()
    work = Path(a.work)
    short = Short([make_line(*row) for row in SCRIPT], a.voice, work)
    short._layout()
    jobs, Plates.states = jobs_for(short)
    Plates.dir = work / "plates"
    (work / "jobs.json").write_text(json.dumps(jobs))
    if not (a.reuse_plates and (Plates.dir / "anchors.json").exists()):
        subprocess.run(["node", str(HERE / "threejs" / "render_plates.mjs"), str(work / "jobs.json"),
                        str(Plates.dir), "--workers", str(a.workers)], check=True)
    Plates.anchors = json.loads((Plates.dir / "anchors.json").read_text())
    short._layout = lambda: None  # keep the exact TTS timing the plates were rendered for
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    short.render(a.out)
    print("wrote", a.out)
