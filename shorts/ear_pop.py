#!/usr/bin/env python3
"""Short #1: "Why do your ears pop on a plane?"

A body-science explainer in the fast-paced narrated style: hook in the first
second, a cross-section diagram that changes with every sentence, a payoff
("POP!"), a twist (landing is worse), practical tips and a follow CTA.
The character ("Max") and all artwork are original and drawn in code.

  python3 shorts/ear_pop.py --voice path/to/en_US-joe-medium.onnx --out out/ear_pop.mp4
  python3 shorts/ear_pop.py --voice ... --out out/ear_pop.mp4 --preview 1 5 12   # stills only
"""
import argparse
import math
import sys
from pathlib import Path

import skia

sys.path.insert(0, str(Path(__file__).parent))
from engine import (H, W, Line, Short, back_out, clamp, color, ease, ease_out,  # noqa: E402
                    elastic_out, lerp, linear, paint, pill, radial, rng, text)

SKIN, SKIN_D = "#ffd2ad", "#e59c72"
TISSUE_L, CAVITY = "#e8957f", "#22121f"


def grown(rr, d):
    out = skia.RRect(rr)
    out.outset(d, d)
    return out


def word_at(ctx, w):
    """Local start time of a spoken word in the current line."""
    w = w.strip(",.!?").lower()
    return next(s for x, s, e in ctx["words"] if x == w)


def shake(c, now, start, amp=14, length=0.35):
    k = clamp(1 - (now - start) / length) if now >= start else 0
    if k:
        c.translate(math.sin(now * 90) * amp * k, math.cos(now * 77) * amp * k)


# ------------------------------------------------------------ plane (hook) --
def cloud(c, x, y, s, alpha):
    for dx, dy, r in ((0, 0, 70), (70, -25, 85), (150, 0, 70), (75, 25, 75)):
        c.drawCircle(x + dx * s, y + dy * s, r * s, paint("#ffffff", alpha, blur=6 * s))


def scene_plane(c, t, dur, ctx):
    now = ctx["now"]
    c.drawPaint(paint(shader=linear(0, 0, 0, H, ["#0b3d91", "#3a86d1", "#a9d6ff"])))
    c.drawCircle(860, 380, 240, paint(shader=radial(860, 380, 240, [("#fff3b0", 200), ("#fff3b0", 0)])))
    for layer, (speed, scale, alpha) in enumerate(((60, 0.8, 120), (160, 1.3, 210))):
        r = rng(10 + layer)
        for i in range(7):
            x0, y0 = r.uniform(0, 1400), r.uniform(200, 1800)
            x = (x0 - now * speed * 1.6) % 1500 - 250
            y = (y0 + now * speed) % 1900 - 100
            cloud(c, x, y, scale, alpha)
    c.save()
    k = ease_out(t / 0.8)
    c.translate(lerp(-200, 540, k), 900 + math.sin(now * 2.2) * 10)
    c.rotate(-16)
    c.scale(1.15, 1.15)
    # contrail
    for dy in (-18, 18):
        c.drawLine(-340, dy, -900, dy + 40, paint("#ffffff", 120, stroke=14, blur=6))
    c.drawPath(_path([(-40, 10), (-170, 190), (-80, 190), (110, 10)]), paint("#8d99ae"))  # near wing
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(-130, 90, -30, 140), 25, 25), paint("#6c757d"))
    c.drawPath(_path([(-300, -40), (-290, -210), (-225, -210), (-180, -40)]), paint("#e63946"))  # tail
    body = skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(-340, -62, 330, 62), 62, 62)
    c.drawRRect(body.makeOffset(0, 14), paint("#000000", 60, blur=12))
    c.drawRRect(body, paint(shader=linear(0, -62, 0, 62, ["#ffffff", "#dfe7ef", "#aab7c4"])))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(-340, 8, 330, 22), 7, 7), paint("#e63946"))
    for i in range(11):
        c.drawCircle(-230 + i * 42, -14, 11, paint("#1d3557"))
    c.drawPath(_path([(255, -40), (305, -28), (300, -8), (250, -12)]), paint("#1d3557"))  # cockpit
    c.restore()


def _path(pts, close=True):
    p = skia.Path()
    p.moveTo(*pts[0])
    for pt in pts[1:]:
        p.lineTo(*pt)
    if close:
        p.close()
    return p


# ------------------------------------------------------------ cabin + Max --
def cabin_bg(c, now):
    c.drawPaint(paint(shader=linear(0, 0, 0, H, ["#22304f", "#141d33", "#0b1020"])))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(-40, 60, 1120, 250), 40, 40),
                paint(shader=linear(0, 60, 0, 250, ["#eef1f5", "#b9c2cf"])))
    win = skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(830, 420, 1030, 720), 90, 90)
    c.drawRRect(grown(win, 18), paint("#c9d1dc"))
    c.save()
    c.clipRRect(win, True)
    c.drawPaint(paint(shader=linear(0, 420, 0, 720, ["#2f6fd1", "#a9d6ff"])))
    r = rng(3)
    for i in range(5):
        x0, y0 = r.uniform(780, 1050), r.uniform(0, 600)
        cloud(c, x0 - 60, 380 + (y0 + now * 240) % 600, 0.55, 230)
    c.restore()


def max_char(c, now, expr="neutral", look=(0, 0)):
    """Original character 'Max', front view in a plane seat."""
    seat = skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(300, 430, 780, 1500), 130, 130)
    c.drawRRect(seat, paint(shader=linear(300, 0, 780, 0, ["#263d7a", "#33509c", "#1f3165"])))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(380, 450, 700, 590), 50, 50), paint("#e9edf3"))
    # torso + neck
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(250, 1080, 830, 1700), 180, 180),
                paint(shader=linear(0, 1080, 0, 1500, ["#2ec4b6", "#1f8a80"])))
    c.drawRect(skia.Rect.MakeLTRB(480, 960, 600, 1110), paint(SKIN_D))
    c.drawPath(_path([(460, 1085), (540, 1170), (620, 1085)]), paint(SKIN_D))
    # ears (viewer's right ear is the one we zoom into)
    for x in (338, 742):
        c.drawOval(skia.Rect.MakeXYWH(x - 42, 760, 84, 130), paint(SKIN_D))
        c.drawOval(skia.Rect.MakeXYWH(x - 22, 785, 44, 80), paint("#cf8460"))
    # head
    c.drawCircle(540, 800, 205, paint(shader=radial(500, 730, 260, [SKIN, SKIN_D])))
    hair = skia.Path()
    hair.moveTo(335, 780)
    hair.cubicTo(320, 560, 760, 540, 745, 780)
    hair.cubicTo(700, 650, 600, 640, 540, 680)
    hair.cubicTo(470, 640, 380, 660, 335, 780)
    c.drawPath(hair, paint(shader=linear(0, 580, 0, 780, ["#5a3620", "#3b2213"])))
    # eyes
    blink = 0.12 if (now % 3.3) < 0.12 else 1.0
    closed = expr in ("yawn", "wince")
    for ex in (462, 618):
        if closed:
            c.drawArc(skia.Rect.MakeXYWH(ex - 30, 770, 60, 40), 200, 140, False, paint("#2b1a12", stroke=9))
            continue
        c.drawOval(skia.Rect.MakeXYWH(ex - 34, 795 - 40 * blink, 68, 80 * blink), paint("#ffffff"))
        if blink > 0.5:
            c.drawCircle(ex + look[0] * 10, 800 + look[1] * 10, 21, paint("#2b1a12"))
            c.drawCircle(ex + look[0] * 10 + 7, 792 + look[1] * 10, 7, paint("#ffffff"))
    # brows
    tilt = 16 if expr == "wince" else (-8 if expr == "smile" else 0)
    c.drawLine(425, 735 + tilt, 500, 728 - tilt * 0.3, paint("#3b2213", stroke=13))
    c.drawLine(580, 728 - tilt * 0.3, 655, 735 + tilt, paint("#3b2213", stroke=13))
    c.drawArc(skia.Rect.MakeXYWH(515, 830, 50, 40), 20, 140, False, paint("#c97f5a", stroke=7))
    # mouth
    if expr == "yawn":
        open_ = 0.6 + 0.4 * math.sin(now * 3) ** 2
        r = skia.Rect.MakeXYWH(490, 900, 100, 110 * open_)
        c.drawOval(r, paint("#5c1a1a"))
        c.drawOval(skia.Rect.MakeXYWH(510, 900 + 70 * open_, 60, 35 * open_), paint("#e07a7a"))
    elif expr == "wince":
        p = skia.Path()
        p.moveTo(480, 935)
        for i in range(1, 7):
            p.lineTo(480 + i * 20, 935 + (8 if i % 2 else -8))
        c.drawPath(p, paint("#5c1a1a", stroke=8, cap=skia.Paint.kRound_Cap))
    elif expr == "smile":
        c.drawPath(_smile(1.0), paint("#5c1a1a"))
    else:
        c.drawArc(skia.Rect.MakeXYWH(490, 880, 100, 60), 20, 140, False, paint("#5c1a1a", stroke=9))


def _smile(k):
    p = skia.Path()
    p.moveTo(470, 905)
    p.quadTo(540, 905 + 110 * k, 610, 905)
    p.quadTo(540, 925, 470, 905)
    return p


def scene_cabin_zoom(c, t, dur, ctx):
    now = ctx["now"]
    z = 1 + 2.6 * ease(clamp((t - dur * 0.35) / (dur * 0.65)))
    c.translate(742, 825)
    c.scale(z, z)
    c.translate(-742, -825)
    cabin_bg(c, now)
    max_char(c, now, look=(1, 0))
    pulse = 0.5 + 0.5 * math.sin(now * 8)
    c.drawCircle(742, 825, 95 + 12 * pulse, paint("#ffd60a", 220, stroke=10))
    c.drawCircle(742, 825, 95 + 12 * pulse, paint("#ffd60a", 120, stroke=24, blur=14))


# ---------------------------------------------------------- ear diagram ----
TUBE = ((700, 865), (725, 1010), (520, 1040), (455, 1200))  # cubic bezier


def bez(u):
    (x0, y0), (x1, y1), (x2, y2), (x3, y3) = TUBE
    a, b, cc, d = (1 - u) ** 3, 3 * u * (1 - u) ** 2, 3 * u * u * (1 - u), u ** 3
    return a * x0 + b * x1 + cc * x2 + d * x3, a * y0 + b * y1 + cc * y2 + d * y3


DEFAULT = dict(p_out=1.0, bulge=0.0, tube=0.0, arrows=0.0, alt=None, cmp=None, waves=0.0,
               flow=0.0, red=0.0, labels=())


def diagram(c, st, ctx, pop_at=None):
    now = ctx["now"]
    c.drawPaint(paint(shader=radial(560, 820, 1150, ["#d47a66", "#8c3b3b", "#2a1016"])))
    for i in range(9):  # soft tissue texture
        r = rng(40 + i)
        c.drawCircle(r.uniform(0, W), r.uniform(300, 1500), r.uniform(80, 200),
                     paint("#ffffff", 10, blur=40))
    c.save()
    c.translate(540, 850)  # frame the cross-section larger in the 9:16 frame
    c.scale(1.1, 1.1)
    c.translate(-540, -800)
    bulge_px = -st["bulge"] * 120
    mid = (482 + bulge_px * 0.5, 700)
    canal = skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(-60, 620, 478, 780), 70, 70)
    chamber = skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(488, 540, 805, 875), 130, 130)
    tube_w = lerp(12, 56, st["tube"])
    tube = skia.Path()
    tube.moveTo(*TUBE[0])
    tube.cubicTo(*TUBE[1], *TUBE[2], *TUBE[3])
    lining = lerp(0, 1, st["red"])
    lining_col = "#ff4d4d" if lining > 0.5 else TISSUE_L
    # linings first, cavities on top -> seamless joins
    c.drawRRect(grown(canal, 12), paint(TISSUE_L))
    c.drawRRect(grown(chamber, 12), paint(TISSUE_L))
    c.drawPath(tube, paint(lining_col, stroke=tube_w + 22))
    c.drawOval(skia.Rect.MakeLTRB(300, 1170, 600, 1300), paint(TISSUE_L))
    cav = paint(shader=linear(0, 540, 0, 1300, ["#2b1830", CAVITY]))
    c.drawRRect(canal, cav)
    c.drawRRect(chamber, cav)
    c.drawPath(tube, paint("#2b1830", stroke=tube_w))
    c.drawOval(skia.Rect.MakeLTRB(312, 1182, 588, 1288), cav)
    # air particles: outside (canal) thins with altitude, inside stays
    r = rng(1)
    for i in range(int(34 * st["p_out"])):
        x0, y0, v, ph = r.uniform(0, 460), r.uniform(640, 760), r.uniform(20, 60), r.uniform(0, 6)
        x = (x0 + now * v) % 450
        c.drawCircle(x, y0 + math.sin(now * 3 + ph) * 8, 9, paint("#8ecae6", 230))
    r = rng(2)
    for i in range(24):
        a, b, f1, f2 = r.uniform(0, 6), r.uniform(0, 6), r.uniform(0.6, 1.4), r.uniform(0.6, 1.4)
        x = 650 + 120 * math.sin(now * f1 + a)
        y = 708 + 125 * math.sin(now * f2 + b)
        c.drawCircle(x, y, 9, paint("#bde0fe", 240))
        c.drawCircle(x, y, 14, paint("#bde0fe", 60, blur=6))
    if st["flow"] > 0.01:
        for i in range(10):
            u = (now * 0.7 + i / 10) % 1
            x, y = bez(u)
            c.drawCircle(x, y, 9, paint("#bde0fe", 240 * st["flow"]))
    # ossicles (tiny bones), first one rides on the eardrum
    bones = [mid, (590, 640), (655, 632), (720, 690)]
    for (x0, y0), (x1, y1) in zip(bones, bones[1:]):
        c.drawLine(x0, y0, x1, y1, paint("#f1e3c8", stroke=17))
    for x, y in bones[1:]:
        c.drawCircle(x, y, 13, paint("#fff4dd"))
    # eardrum
    drum = skia.Path()
    drum.moveTo(482, 598)
    drum.quadTo(482 + bulge_px, 700, 482, 802)
    strain = abs(st["bulge"])
    drum_col = "#ffb3a7" if strain > 0.5 else "#f6e7d7"
    c.drawPath(drum, paint(drum_col, 150 * strain, stroke=40, blur=14))
    c.drawPath(drum, paint(drum_col, stroke=16))
    # pressure arrows
    if st["arrows"] > 0.01:
        a = 255 * st["arrows"]
        lo = lerp(40, 170, clamp(st["p_out"] / 1.5))
        for y in (655, 700, 745):
            end = 470 + bulge_px * (1 - abs(y - 700) / 110) * 0.9
            _arrow(c, end - lo - 10, y, end - 10, y, "#4cc9f0", a)
            _arrow(c, 500 + 120, y, 500 + bulge_px * 0.6 + 14, y, "#ffb703", a)
    # muffled sound waves
    if st["waves"] > 0.01:
        for i in range(4):
            ph = (now * 0.9 + i * 0.25) % 1
            x = lerp(40, 380, ph)
            c.drawArc(skia.Rect.MakeXYWH(x - 60, 700 - 60, 120, 120), -50, 100, False,
                      paint("#ffffff", 220 * st["waves"] * (1 - ph) ** 2, stroke=8))
    if st["red"] > 0.01:
        x, y = bez(0.45)
        c.drawCircle(x + 90, y, 38, paint("#ff4d4d", 255 * st["red"]))
        for s in (-1, 1):
            c.drawLine(x + 72, y - 18 * s, x + 108, y + 18 * s, paint("#ffffff", 255 * st["red"], stroke=9))
    # labels with leader lines
    spots = {"canal": ("EAR CANAL", (200, 540), (200, 640)),
             "drum": ("EARDRUM", (330, 895), (478, 770)),
             "middle": ("MIDDLE EAR", (790, 470), (700, 570)),
             "tube": ("EUSTACHIAN TUBE", (760, 1120), (610, 1030)),
             "throat": ("THROAT", (210, 1260), (330, 1235))}
    for key, appear in st["labels"]:
        if ctx["now"] < appear:
            continue
        k = back_out((ctx["now"] - appear) / 0.35)
        label, (lx, ly), (ax, ay) = spots[key]
        c.drawLine(lx, ly, ax, ay, paint("#ffffff", 230 * clamp(k), stroke=5))
        c.drawCircle(ax, ay, 9, paint("#ffffff", 255 * clamp(k)))
        pill(c, label, lx, ly, size=38, scale=k)
    c.restore()
    # HUD: altitude + pressure comparison (hidden while "POP!" fills the top)
    if pop_at is not None and 0 <= ctx["now"] - pop_at < 1.1:
        st = dict(st, alt=None, cmp=None)
    if st["alt"] is not None:
        pill(c, f"CABIN ALTITUDE  {int(st['alt']):,} FT", 540, 230, size=46, fill="#111827", fg="#ffffff")
    if st["cmp"]:
        col = {"=": "#2ec4b6", "<": "#ffb703", ">": "#ff4d4d"}[st["cmp"]]
        pill(c, f"OUTSIDE  {st['cmp']}  INSIDE", 540, 350, size=52, fill=col, fg="#111111")
    if pop_at is not None and ctx["now"] >= pop_at:
        k = (ctx["now"] - pop_at)
        for i in range(14):
            ang = i / 14 * 2 * math.pi
            r0, r1 = 60 + 380 * ease_out(k / 0.4), 120 + 420 * ease_out(k / 0.4)
            c.drawLine(476 + math.cos(ang) * r0, 740 + math.sin(ang) * r0,
                       476 + math.cos(ang) * r1, 740 + math.sin(ang) * r1,
                       paint("#ffd60a", 255 * clamp(1 - k / 0.5), stroke=12))
        c.save()
        c.rotate(-8, 540, 380)
        text(c, "POP!", 540, 420, 230, fill="#ffd60a", stroke_w=26, weight="Black", scale=back_out(k / 0.3, 2.6))
        c.restore()


def _arrow(c, x0, y0, x1, y1, col, a):
    c.drawLine(x0, y0, x1, y1, paint(col, a, stroke=11))
    d = 1 if x1 > x0 else -1
    c.drawPath(_path([(x1 + 12 * d, y1), (x1 - 14 * d, y1 - 16), (x1 - 14 * d, y1 + 16)]), paint(col, a))


def diag_scene(prev, target, tween=0.7, alt_linear=False, pop_word=None):
    """Interpolate the diagram from the previous sentence's state to this one's."""
    def scene(c, t, dur, ctx):
        line_start = ctx["now"] - t
        st = {}
        for k, v in target.items():
            p = prev.get(k, v)
            if k == "labels":
                st[k] = [(key, line_start + at) for key, at in v]
            elif k == "alt" and v is not None and p is not None:
                st[k] = lerp(p, v, ease(t / (dur * 0.9)) if alt_linear else ease(t / tween))
            elif isinstance(v, (int, float)) and isinstance(p, (int, float)):
                x = elastic_out(t / 0.9) if (pop_word and k == "bulge") else ease(t / tween)
                if pop_word and k in ("bulge", "p_out"):
                    pw = word_at(ctx, pop_word)
                    x = elastic_out((t - pw) / 0.9) if t >= pw else 0
                st[k] = lerp(p, v, x)
            elif pop_word and t < word_at(ctx, pop_word):
                st[k] = p  # e.g. the "=" badge only flips at the pop itself
            else:
                st[k] = v
        pop_at = line_start + word_at(ctx, pop_word) if pop_word else None
        if pop_at:
            shake(c, ctx["now"], pop_at)
        intro = ctx.get("intro")  # flash in from the cabin zoom
        diagram(c, st, ctx, pop_at)
        if intro and t < 0.3:
            c.drawPaint(paint("#ffffff", 255 * (1 - t / 0.3)))
    return scene


# --------------------------------------------------------------- endings ---
def icon_card(c, x, y, label, kind, k):
    if k <= 0:
        return
    c.save()
    c.translate(x, y)
    c.scale(k, k)
    card = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-140, -120, 280, 250), 40, 40)
    c.drawRRect(card.makeOffset(0, 10), paint("#000000", 90, blur=14))
    c.drawRRect(card, paint("#ffffff"))
    if kind == "drop":
        p = skia.Path()
        p.moveTo(0, -95)
        p.cubicTo(45, -30, 55, 0, 0, 30)
        p.cubicTo(-55, 0, -45, -30, 0, -95)
        c.drawPath(p, paint("#4cc9f0"))
    elif kind == "yawn":
        c.drawCircle(0, -30, 62, paint(SKIN))
        c.drawOval(skia.Rect.MakeXYWH(-20, -20, 40, 52), paint("#5c1a1a"))
        for s in (-1, 1):
            c.drawLine(s * 32, -50, s * 14, -48, paint("#2b1a12", stroke=6))
    else:
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-70, -75, 140, 80), 20, 20), paint("#ff70a6"))
        for i in range(3):
            c.drawLine(-40 + i * 40, -65, -40 + i * 40, -5, paint("#ffffff", 120, stroke=6))
    text(c, label, 0, 95, 40, fill="#111111")
    c.restore()


def scene_tips(c, t, dur, ctx):
    now = ctx["now"]
    cabin_bg(c, now)
    max_char(c, now, expr="yawn" if t < word_at(ctx, "chewing") + 0.6 else "smile")
    for i, (word, label, kind) in enumerate((("swallowing", "SWALLOW", "drop"),
                                            ("yawning", "YAWN", "yawn"),
                                            ("chewing", "CHEW GUM", "gum"))):
        icon_card(c, 200 + i * 340, 420, label, kind, back_out((t - word_at(ctx, word)) / 0.35))


def scene_cta(c, t, dur, ctx):
    now = ctx["now"]
    cabin_bg(c, now)
    max_char(c, now, expr="smile", look=(0, -1))
    k = back_out(t / 0.4) * (1 + 0.05 * math.sin(now * 7))
    pill(c, "FOLLOW", 540, 390, size=80, fill="#ff0033", fg="#ffffff", scale=k, pad=50)
    text(c, "for more body facts", 540, 520, 50, stroke_w=10, alpha=255 * clamp(t / 0.4))


# ----------------------------------------------------------------- script --
# How the voice performs each line (ElevenLabs v3 audio tags + pacing
# punctuation). Captions show Line.text; words must match after tags and
# punctuation are removed. Shared with ear_pop_3d.py (same TTS cache).
DELIVERY = [
    "[curious] Ever wondered why your ears... pop on a plane?",
    "[conspiratorial] Here's what's ACTUALLY happening inside your head.",
    "Behind your eardrum is a tiny pocket of air... called the middle ear.",
    "[calm] On the ground, the air pressure inside matches the air outside.",
    "But as the plane climbs... the air pressure in the cabin DROPS.",
    "[tense] The air trapped inside pushes out, and your eardrum bulges... like a balloon.",
    "[sighs] That's the muffled... blocked feeling.",
    "Then a tiny tube to your throat, the Eustachian tube, [excited] cracks open.",
    "Air escapes, the pressure evens out, and... [excited] POP!",
    "[dramatic] Landing is actually WORSE.",
    "The tube doesn't open on its own as easily, so your eardrum gets pushed... inward.",
    "[upbeat] That's why swallowing, yawning, or chewing gum helps. They pull the tube open!",
    "[warm] Follow for more weird things your body does.",
]


def build():
    s0 = dict(DEFAULT, labels=(("canal", 0.2), ("drum", 0.9), ("middle", 1.9)))
    s1 = dict(s0, labels=(), arrows=1.0, alt=0, cmp="=")
    s2 = dict(s1, alt=8000, p_out=0.45, cmp="<")
    s3 = dict(s2, bulge=1.0)
    s4 = dict(s3, waves=1.0)
    s5 = dict(s4, waves=0.0, tube=1.0, flow=1.0, labels=(("tube", 0.9), ("throat", 1.4)))
    s6 = dict(s5, labels=(), bulge=0.0, p_out=0.45, cmp="=", tube=0.2, flow=0.0)
    s7 = dict(s6, alt=0, p_out=1.0, cmp=">", tube=0.0)
    s8 = dict(s7, bulge=-1.0, red=1.0)
    intro = diag_scene(s0, s0)

    def intro_scene(c, t, dur, ctx):
        ctx["intro"] = True
        intro(c, t, dur, ctx)
        ctx["intro"] = False

    lines = [
        Line("Ever wondered why your ears pop on a plane?", scene_plane, [(0, "whoosh"), (0.1, "rumble")],
             pause=0.3),
        Line("Here's what's actually happening inside your head.", scene_cabin_zoom, [(0.05, "chime")]),
        Line("Behind your eardrum is a tiny pocket of air, called the middle ear.", intro_scene,
             [(0, "whoosh"), ("eardrum", "ding"), ("middle", "ding")]),
        Line("On the ground, the air pressure inside matches the air outside.", diag_scene(s0, s1),
             [("matches", "ding")], pause=0.25),
        Line("But as the plane climbs, the air pressure in the cabin drops.", diag_scene(s1, s2, alt_linear=True),
             [(0.2, "rumble")]),
        Line("The air trapped inside pushes out, and your eardrum bulges like a balloon.",
             diag_scene(s2, s3, tween=1.6), [("bulges", "thud"), ("bulges", "muffle_on")]),
        Line("That's the muffled, blocked feeling.", diag_scene(s3, s4), pause=0.4),
        Line("Then a tiny tube to your throat, the Eustachian tube, cracks open.", diag_scene(s4, s5, tween=1.2),
             [("eustachian", "ding")]),
        Line("Air escapes, the pressure evens out, and... POP!", diag_scene(s5, s6, pop_word="pop!"),
             [("pop!", "pop"), ("pop!", "muffle_off")], pause=0.6),
        Line("Landing is actually worse.", diag_scene(s6, s7, alt_linear=True), [(0, "whoosh")], pause=0.3),
        Line("The tube doesn't open on its own as easily, so your eardrum gets pushed inward.",
             diag_scene(s7, s8, tween=1.4), [("inward.", "thud"), ("inward.", "muffle_on")]),
        Line("That's why swallowing, yawning, or chewing gum helps. They pull the tube open.", scene_tips,
             [(0, "whoosh"), ("swallowing,", "gulp"), ("swallowing,", "muffle_off"), ("yawning,", "pop"),
              ("chewing", "pop")]),
        Line("Follow for more weird things your body does.", scene_cta, [(0, "ding")], pause=0.6),
    ]
    for ln, say in zip(lines, DELIVERY):
        ln.say = say
    return lines


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", required=True, help="Piper .onnx voice (use a commercially licensed one)")
    ap.add_argument("--out", default="out/ear_pop.mp4")
    ap.add_argument("--work", default="out/ear_pop_work")
    ap.add_argument("--preview", type=float, nargs="*", help="render PNG stills at these seconds")
    a = ap.parse_args()
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Short(build(), a.voice, a.work).render(a.out, preview=a.preview)
