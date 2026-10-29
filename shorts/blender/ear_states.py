"""Per-line shot list and ear-diagram states for the 3D ear-pop short.

Pure Python (no numpy/bpy), imported by both the Blender plate renderer
(shorts/blender/ear_pop_3d.py) and the compositor (shorts/ear_pop_3d.py), so
the 3D physics (eardrum bulge, tube opening, air) and the 2D HUD (altitude,
OUTSIDE vs INSIDE, labels, POP!) always agree.

State keys mirror the 2D version (shorts/ear_pop.py):
  p_out  outside air density in the ear canal (1 = ground level)
  bulge  eardrum: +1 bulges out into the canal, -1 pushed inward
  tube   Eustachian tube opening (0 closed, 1 open)
  arrows pressure-arrow visibility     waves  muffled sound rings
  flow   air flowing down the tube     red    tube struggling (landing)
  alt    cabin altitude (HUD)          cmp    OUTSIDE ? INSIDE badge (HUD)
"""
import math

DEFAULT = dict(p_out=1.0, bulge=0.0, tube=0.0, arrows=0.0, alt=None, cmp=None, waves=0.0,
               flow=0.0, red=0.0, labels=())


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def elastic_out(x):
    x = clamp(x)
    if x in (0, 1):
        return x
    return 2 ** (-10 * x) * math.sin((x * 10 - 0.75) * (2 * math.pi) / 3) + 1


def lerp(a, b, x):
    return a + (b - a) * x


def word_at(words, w):
    """Local start time of a spoken word; words = [(word, start, end), ...]."""
    w = w.strip(",.!?").lower()
    return next(s for x, s, e in words if x == w)


def _states():
    s0 = dict(DEFAULT, labels=(("canal", 0.2), ("drum", 0.9), ("middle", 1.9)))
    s1 = dict(s0, labels=(), arrows=1.0, alt=0, cmp="=")
    s2 = dict(s1, alt=8000, p_out=0.45, cmp="<")
    s3 = dict(s2, bulge=1.0)
    s4 = dict(s3, waves=1.0)
    s5 = dict(s4, waves=0.0, tube=1.0, flow=1.0, labels=(("tube", 0.9), ("throat", 1.4)))
    s6 = dict(s5, labels=(), bulge=0.0, p_out=0.45, cmp="=", tube=0.2, flow=0.0)
    s7 = dict(s6, alt=0, p_out=1.0, cmp=">", tube=0.0)
    s8 = dict(s7, bulge=-1.0, red=1.0)
    return s0, s1, s2, s3, s4, s5, s6, s7, s8


S0, S1, S2, S3, S4, S5, S6, S7, S8 = _states()


def ear(prev, target, tween=0.7, alt_linear=False, pop_word=None, cam="front", intro=False):
    return dict(shot="ear", prev=prev, target=target, tween=tween, alt_linear=alt_linear,
                pop_word=pop_word, cam=cam, intro=intro)


# One entry per narration line, in order (shorts/ear_pop_3d.py holds the text).
SHOTS = [
    dict(shot="plane"),
    dict(shot="cabin", cam="zoom_ear", expr="neutral", look=(1, 0)),
    ear(S0, S0, cam="intro", intro=True),
    ear(S0, S1, cam="drift_l"),
    ear(S1, S2, alt_linear=True, cam="drift_r"),
    ear(S2, S3, tween=1.6, cam="push_drum"),
    ear(S3, S4, cam="canal"),
    ear(S4, S5, tween=1.2, cam="tube"),
    ear(S5, S6, pop_word="pop!", cam="pop"),
    ear(S6, S7, alt_linear=True, cam="drift_l"),
    ear(S7, S8, tween=1.4, cam="push_drum"),
    dict(shot="cabin", cam="tips", expr="tips"),
    dict(shot="cabin", cam="cta", expr="smile", look=(0, -1)),
]


def ear_state(shot, t, dur, words):
    """Interpolate the diagram from the previous line's state to this one's.
    Returns (state, pop_time) with label/pop times local to the line."""
    prev, target = shot["prev"], shot["target"]
    pop_word, tween = shot["pop_word"], shot["tween"]
    pw = word_at(words, pop_word) if pop_word else None
    st = {}
    for k, v in target.items():
        p = prev.get(k, v)
        if k == "labels":
            st[k] = list(v)
        elif k == "alt" and v is not None and p is not None:
            st[k] = lerp(p, v, ease(t / (dur * 0.9)) if shot["alt_linear"] else ease(t / tween))
        elif isinstance(v, (int, float)) and isinstance(p, (int, float)):
            x = ease(t / tween)
            if pop_word and k in ("bulge", "p_out"):
                x = elastic_out((t - pw) / 0.9) if t >= pw else 0
            st[k] = lerp(p, v, x)
        elif pop_word and t < pw:
            st[k] = p  # e.g. the "=" badge only flips at the pop itself
        else:
            st[k] = v
    return st, pw
