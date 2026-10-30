"""The real Max (assets/characters/max/max_v2.blend) in the pilot's cabin: seated, his ear measured
for the fly-in, and his performance hand-keyed to the voice beats.

    m = load(film)                     # append, seat, measure -> anchors for the cameras
    perform(m, beat, rng)              # expressions + arm moves + blinks, keyed on spoken words

Expressions come from shorts/blender/max_expressions.py, so tweaking a face there changes every shot.
"""
import math
import random
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "shorts" / "blender"))
from build_max import aim_bone, set_expression, thumbs_up, THUMB_BONES  # noqa: E402
from rigs import fcurves, material  # noqa: E402

MAX_BLEND = ROOT / "assets" / "characters" / "max" / "max_v3.blend"
SEAT_TOP = 0.53                      # greybox seat cushion top (z above the cabin floor)
STANDIN_HEAD = Vector((0.0, 0.35, 1.66))   # where the grey-box cameras expected his head (cabin space)

# he faces -Y; his left is +X
SEATED = [
    ("spine05", (0, 0.10, 1)), ("spine04", (0, 0.12, 1)), ("spine03", (0, 0.12, 1)),
    ("spine02", (0, 0.08, 1)), ("spine01", (0, 0.02, 1)),
    ("upperleg01.L", (0.1, -1, -0.06)), ("upperleg02.L", (0.1, -1, -0.06)),
    ("upperleg01.R", (-0.1, -1, -0.06)), ("upperleg02.R", (-0.1, -1, -0.06)),
    ("lowerleg01.L", (0.04, -0.3, -1)), ("lowerleg02.L", (0.04, -0.3, -1)),
    ("lowerleg01.R", (-0.04, -0.3, -1)), ("lowerleg02.R", (-0.04, -0.3, -1)),
    ("foot.L", (0.05, -1, -0.25)), ("foot.R", (-0.05, -1, -0.25)),
]
LAP = {  # arms resting, hands on his thighs
    "L": [("upperarm01.L", (0.18, -0.25, -1)), ("upperarm02.L", (0.18, -0.25, -1)),
          ("lowerarm01.L", (-0.05, -1, -0.35)), ("lowerarm02.L", (-0.05, -1, -0.35)), ("wrist.L", (-0.05, -1, -0.5))],
    "R": [("upperarm01.R", (-0.18, -0.25, -1)), ("upperarm02.R", (-0.18, -0.25, -1)),
          ("lowerarm01.R", (0.05, -1, -0.35)), ("lowerarm02.R", (0.05, -1, -0.35)), ("wrist.R", (0.05, -1, -0.5))],
}
ARM_L = ["upperarm01.L", "upperarm02.L", "lowerarm01.L", "lowerarm02.L", "wrist.L"]


def _key(rig, names, frame):
    for n in names:
        pb = rig.pose.bones.get(n)
        if pb:
            pb.rotation_mode = "QUATERNION"
            pb.keyframe_insert("rotation_quaternion", frame=frame)


def _apply(rig, pose):
    for name, d in pose:
        pb = rig.pose.bones.get(name)
        if pb:
            pb.rotation_mode = "QUATERNION"
        aim_bone(rig, name, d)


def load(film, cabin):
    """Append Max, seat him at his seat and return camera anchors in world space."""
    with bpy.data.libraries.load(str(MAX_BLEND), link=False) as (src, dst):
        dst.collections = ["MAX"]
    coll = dst.collections[0]
    coll.name = "CHAR_max"
    film.collection.children.link(coll)
    rig = bpy.data.objects["Max"]
    body = bpy.data.objects["Max.body"]
    film.frame_set(1)
    _apply(rig, SEATED)
    _apply(rig, LAP["L"] + LAP["R"])
    _key(rig, [n for n, _ in SEATED] + [n for n, _ in LAP["L"] + LAP["R"]], 1)
    bpy.context.view_layer.update()
    # sit: hip joints on the cushion, buttocks against the seat back
    hip = (rig.matrix_world @ rig.pose.bones["upperleg01.L"].head + rig.matrix_world @ rig.pose.bones["upperleg01.R"].head) / 2
    target = cabin + Vector((0.0, 0.47, SEAT_TOP + 0.085))
    rig.location += target - hip
    bpy.context.view_layer.update()

    eye = _eye_centre(rig)
    head_c = eye + Vector((0, 0.035, 0.0))
    hole = _ear_entrance(body, eye)
    plug = _ear_plug(rig, hole)
    anchor = bpy.data.objects.new("Max_head", None)   # cameras aim at Max_head + (0, 0, 0.14)
    coll.objects.link(anchor)
    anchor.parent, anchor.parent_type, anchor.parent_bone = rig, "BONE", "head"
    bpy.context.view_layer.update()
    anchor.matrix_world.translation = head_c - Vector((0, 0, 0.14))
    print(f"[max] seated; eyes {tuple(round(c, 3) for c in eye)}, ear {tuple(round(c, 3) for c in hole)}")
    return {"rig": rig, "body": body, "head": anchor, "hole": hole, "face": head_c - Vector((0, 0, 0.04)),
            "offset": head_c - (cabin + STANDIN_HEAD), "plug": plug, "real": True}


def _eye_centre(rig):
    dg = bpy.context.evaluated_depsgraph_get()
    eyes = bpy.data.objects["Max.high-poly"].evaluated_get(dg)
    return sum((eyes.matrix_world @ Vector(c) for c in eyes.bound_box), Vector()) / 8


def _ear_entrance(body, eye):
    """His left ear's concha (the hollow at the canal opening), from the posed, evaluated mesh."""
    dg = bpy.context.evaluated_depsgraph_get()
    be = body.evaluated_get(dg)
    me = be.to_mesh()
    mw = be.matrix_world
    pts = [mw @ v.co for v in me.vertices]
    be.to_mesh_clear()
    ear = [p for p in pts if p.x - eye.x > 0.062 and abs(p.z - (eye.z - 0.02)) < 0.035
           and 0.04 < p.y - eye.y < 0.13]
    if not ear:
        return eye + Vector((0.075, 0.085, -0.02))
    c = sum(ear, Vector()) / len(ear)
    # the concha sits slightly forward of and lower than the ear's centre, and recessed
    return Vector((c.x - 0.006, c.y - 0.006, c.z - 0.004))


def _ear_plug(rig, hole):
    """Small dark disc in the canal, so the push-through ends in black, as in the previz."""
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=hole)
    plug = bpy.context.active_object
    plug.name = "Max_ear_hole"
    for c in list(plug.users_collection):
        c.objects.unlink(plug)
    bpy.data.collections["CHAR_max"].objects.link(plug)
    plug.scale = (0.003, 0.006, 0.008)
    plug.data.materials.append(material("ear_hole", (0.02, 0.005, 0.005), rough=1.0))
    bpy.context.view_layer.update()
    mw = plug.matrix_world.copy()
    plug.parent, plug.parent_type, plug.parent_bone = rig, "BONE", "head"
    plug.matrix_world = mw
    return plug


# ------------------------------------------------------------ performance --
def perform(m, beat, rng, sc):
    rig = m["rig"]
    timeline = []                # (frame, expression, weight)

    def face(f, name, w=1.0):
        timeline.append((f, name, w))

    def arm_lap(side, f):
        sc.frame_set(f)
        _apply(rig, LAP[side])
        _key(rig, [n for n, _ in LAP[side]], f)

    def hand_to_ear(f, cover=False):
        """Left hand up to his ear (fingers on it, or cupping it when he winces)."""
        sc.frame_set(f)
        ear = m["hole"] + Vector((0.035, 0.0, 0.0) if not cover else (0.02, 0.0, 0.0))
        aim_bone(rig, "upperarm01.L", (0.55, -0.35, -0.6))
        aim_bone(rig, "upperarm02.L", (0.55, -0.35, -0.6))
        for b in ("lowerarm01.L", "lowerarm02.L"):
            pb = rig.pose.bones[b]
            d = ear - rig.matrix_world @ pb.head
            aim_bone(rig, b, d)
        aim_bone(rig, "wrist.L", (-0.25, 0.1, 1) if cover else (-0.4, 0.2, 1))
        _key(rig, ARM_L, f)

    # S00 cold open: already wincing, hand cupping his ear; during S01 (the plane) the hand goes back
    # to his lap, so it's clear of his ear before S02's camera flies into it
    s0_end = rng("S00")[1]
    face(1, "wince")
    face(s0_end, "wince", 0.9)
    hand_to_ear(1, cover=True)
    hand_to_ear(s0_end, cover=True)
    arm_lap("L", rng("S01")[0] + 20)
    fh = beat("S02", "touch")              # S02: a puzzled look as the camera swings round to his ear
    face(fh - 10, "neutral")
    face(fh + 4, "puzzled")
    # S07 "That's the muffled, blocked feeling": wince, hand cupping the ear
    fm = beat("S07", "muffled")
    s7_end = rng("S07")[1]
    face(fm - 6, "neutral")
    face(fm + 3, "wince")
    face(s7_end - 4, "wince", 0.85)
    face(s7_end + 8, "neutral")
    arm_lap("L", fm - 8)
    hand_to_ear(fm + 2, cover=True)
    hand_to_ear(s7_end, cover=True)
    arm_lap("L", s7_end + 10)
    # S09c, right after the POP: relief
    fr = beat("S09c", "relief")
    face(fr - 2, "neutral")
    face(fr + 8, "relief_smile")
    face(rng("S09c")[1] + 6, "relief_smile", 0.6)
    face(rng("S12a")[0] - 6, "neutral")
    # S12a "That's why swallowing, yawning, or chewing gum helps": one sustained close-up
    fs, fy, fc = (beat("S12a", w) for w in ("swallowing", "yawning", "chewing"))
    face(fs - 3, "neutral")
    face(fs + 4, "swallow")
    face(fs + 12, "neutral")
    face(fy - 2, "neutral")
    face(fy + 10, "yawn")
    face(fc - 2, "yawn", 0.8)
    face(fc + 4, "chew_b")
    for i in range(4):
        face(fc + 7 + i * 8, "chew")
        face(fc + 11 + i * 8, "chew_b")
    face(rng("S12a")[1], "neutral")
    # S13 (tail, no spoken outro): relieved grin and a thumbs-up to the lens, with the follow card
    ff = beat("S13", "thumbs")
    face(rng("S13")[0], "relief_smile")
    face(ff + 6, "thumbs_up")
    face(rng("S13")[1], "thumbs_up")
    sc.frame_set(ff - 5)
    thumbs_up(rig, False)
    _apply(rig, LAP["R"] + LAP["L"])
    _key(rig, THUMB_BONES, ff - 5)
    sc.frame_set(ff + 7)
    thumbs_up(rig, True, raised=True)
    # his left arm stays in his lap: re-aim it after thumbs_up's relaxed-arm pose
    _apply(rig, LAP["L"])
    _key(rig, THUMB_BONES, ff + 7)

    for f, name, w in sorted(timeline):
        sc.frame_set(f)
        set_expression(rig, name, frame=f, weight=w)
    _blinks(rig, timeline, sc.frame_end)


def _blinks(rig, timeline, end):
    """Natural blinks every 2.5-5 s (not while his eyes are already closed)."""
    body = next(o for o in rig.children if o.name.endswith(".body"))
    curves = [fc for fc in fcurves(body.data.shape_keys) if fc.data_path in ('key_blocks["eyeBlinkLeft"].value',
                                                           'key_blocks["eyeBlinkRight"].value')]
    closed = {"wince", "yawn"}
    busy = sorted(f for f, n, _ in timeline if n in closed)
    rnd = random.Random(3)
    f = 40
    while f < end - 10:
        if not any(abs(f - b) < 30 for b in busy):
            for fc in curves:
                before, after = fc.evaluate(f - 2), fc.evaluate(f + 4)
                fc.keyframe_points.insert(f - 2, before)
                fc.keyframe_points.insert(f + 1, 1.0)
                fc.keyframe_points.insert(f + 4, after)
        f += int(rnd.uniform(75, 150))
