"""Build the pilot's grey-box previz .blend (run inside Blender):

  blender -b --factory-startup -P shorts/pilot_ear_pop/build_previz.py -- [--stills DIR] [--standin]

Reads plan.json (prep_plan.py) and writes out/pilot_ear_pop/pilot_ear_pop_previz.blend with:
  FILM  every set, the 14 shot cameras (bound to timeline markers, so playing it in camera
        view cuts between shots), all animation keyed to spoken words, plus the voice and SFX.
  EDIT  the cut: one strip per shot (FILM through that shot's camera), the dissolve,
        captions, voice and SFX. Play it to watch the whole film end to end.
--stills renders low-res Cycles frames (early/middle/late) of every shot for review.
Max is the real rigged character (assets/characters/max/max_v2.blend, see real_max.py) with his
expressions keyed to the voice; --standin uses the grey-box Max instead.
"""
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "blender"))
from greybox import CABIN, EAR, EAR_MAP, SKY, build_cabin, build_city, build_ear, build_sky, tube_point  # noqa: E402
from rigs import bake_move, bezier, camera, collection, ease, handheld, impulse_shake, key, lerp  # noqa: E402
sys.path.insert(0, str(HERE))
import real_max  # noqa: E402
from sets.cabin import build_cabin as real_cabin  # noqa: E402

PLAN = json.loads((HERE / "plan.json").read_text())
OUT = HERE.parent.parent / "out" / "pilot_ear_pop"
SHOT = {s["id"]: s for s in PLAN["shots"]}


def beat(shot_id, word):
    return next(b["frame"] for b in SHOT[shot_id]["beats"] if b.get("word") == word)


def rng(shot_id):
    return SHOT[shot_id]["start"], SHOT[shot_id]["end"]


# ---------------------------------------------------------------- scenes ---
def setup_film():
    sc = bpy.context.scene
    sc.name = "FILM"
    for ob in list(bpy.data.objects):  # drop the startup cube, camera and light
        bpy.data.objects.remove(ob)
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)
    sc.render.fps = PLAN["fps"]
    sc.render.resolution_x, sc.render.resolution_y = PLAN["resolution"]
    sc.frame_start, sc.frame_end = 1, PLAN["frame_end"]
    sc.sync_mode = "AUDIO_SYNC"  # playback follows the voice: drops frames on slow machines instead of drifting
    # View > Viewport Render Animation then writes a synced MP4 (picture + voice + SFX) next to the .blend
    r = sc.render
    r.image_settings.file_format = "FFMPEG"
    r.ffmpeg.format, r.ffmpeg.codec, r.ffmpeg.constant_rate_factor = "MPEG4", "H264", "MEDIUM"
    r.ffmpeg.audio_codec, r.ffmpeg.audio_bitrate, r.ffmpeg.audio_channels = "AAC", 192, "STEREO"
    r.filepath = "//pilot_ear_pop_previz_"
    for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
        try:
            sc.render.engine = eng
            break
        except TypeError:
            continue
    sc.view_settings.view_transform = "AgX"
    world = bpy.data.worlds.new("golden_hour")
    world.use_nodes = True
    nt = world.node_tree
    sky = nt.nodes.new("ShaderNodeTexSky")
    for attr, val in (("sky_type", "NISHITA"), ("sun_elevation", math.radians(7)), ("sun_rotation", math.radians(60))):
        try:
            setattr(sky, attr, val)
        except (TypeError, AttributeError):
            pass
    nt.links.new(sky.outputs["Color"], nt.nodes["Background"].inputs["Color"])
    nt.nodes["Background"].inputs["Strength"].default_value = 0.35
    sc.world = world
    return sc


# ------------------------------------------------------------- animation ---
def animate_jet(jet):
    gear = bpy.data.objects["Jet_gear"]
    for sid, p0, p1, rot, gear_down in (
            ("S01", SKY + Vector((-8, 0, -1)), SKY + Vector((10, 0, 6)), (0, -18, 0), False),
            ("S05a", SKY + Vector((-6, 0, 40)), SKY + Vector((6, 0, 42)), (0, -6, 0), False),
            ("S10", Vector((930, 0, 38)), Vector((912, 0, 27)), (0, -6, 180), True)):
        f0, f1 = rng(sid)
        jet.rotation_euler = [math.radians(a) for a in rot]
        jet.keyframe_insert("rotation_euler", frame=f0)
        key(jet, "location", f0, p0, interp="LINEAR")
        key(jet, "location", f1, p1, interp="LINEAR")
        key(gear, "scale", f0, (1, 1, 1 if gear_down else 0.001), interp="CONSTANT")


def jet_at(sid, t):
    jet = bpy.data.objects["Jet"]
    f0, f1 = rng(sid)
    fc = [c for c in jet.animation_data.action.fcurves if c.data_path == "location"]
    fr = f0 + (f1 - f0) * t
    return Vector([c.evaluate(fr) for c in sorted(fc, key=lambda c: c.array_index)])


def animate_max(m):
    head, hand_l, hand_r, mouth = m["head"], m["hands"]["L"], m["hands"]["R"], m["mouth"]
    lap_l, lap_r = Vector(hand_l.location), Vector(hand_r.location)
    ear = Vector((0.13, -0.02, 1.66))
    eye_open = [Vector(e.scale) for e in m["eyes"]]

    def head_rot(f, pitch=0, roll=0, yaw=0):
        key(head, "rotation_euler", f, [math.radians(pitch), math.radians(roll), math.radians(yaw)])

    def mouth_shape(f, w=1.0, h=1.0):
        key(mouth, "scale", f, (0.03 * w, 0.01, 0.008 * h))

    for f in (1,):
        key(hand_l, "location", f, lap_l)
        key(hand_r, "location", f, lap_r)
        head_rot(f)
        mouth_shape(f)
    # S02: touches his ear on "happening"
    fh = beat("S02", "happening")
    key(hand_l, "location", fh - 3, lap_l)
    key(hand_l, "location", fh + 10, ear)
    head_rot(fh - 3)
    head_rot(fh + 12, roll=-6, yaw=4)
    key(hand_l, "location", fh + 32, lap_l)  # hand clears the ear before the camera flies in
    head_rot(fh + 34)
    # S07: winces, hand over the ear, eyes squeezed, on "muffled"
    fm = beat("S07", "muffled")
    key(hand_l, "location", fm - 8, lap_l)
    key(hand_l, "location", fm + 4, ear + Vector((0.02, -0.01, 0.0)))
    head_rot(fm - 8)
    head_rot(fm + 6, pitch=-4, roll=-10)
    for e, s in zip(m["eyes"], eye_open):
        key(e, "scale", fm - 2, s)
        key(e, "scale", fm + 4, (s.x, s.y, s.z * 0.2))
        key(e, "scale", 1300, s)
    key(hand_l, "location", 1300, lap_l)
    head_rot(1300)
    # S12: swallow (nod), yawn (head back + mouth open), chew, relief smile
    fs = beat("S12a", "swallowing")
    fy, fc, fo = (beat("S12b", w) for w in ("yawning", "chewing", "open"))
    head_rot(fs - 2)
    head_rot(fs + 6, pitch=8)
    head_rot(fs + 14)
    mouth_shape(fy - 2)
    head_rot(fy - 2)
    head_rot(fy + 10, pitch=-16)
    mouth_shape(fy + 10, w=1.3, h=4.0)
    mouth_shape(fc - 8, w=1.3, h=4.0)  # hold the yawn while the camera pulls out to reveal it
    head_rot(fc - 6)
    mouth_shape(fc - 2)
    for i in range(4):
        mouth_shape(fc + i * 7, h=1.0)
        mouth_shape(fc + i * 7 + 3, w=0.9, h=1.8)
    mouth_shape(fo - 2)
    mouth_shape(fo + 6, w=1.6, h=0.6)
    # S13: thumbs up on "follow"
    ff = beat("S13", "follow")
    key(hand_r, "location", ff - 4, lap_r)
    key(hand_r, "location", ff + 8, Vector((-0.2, -0.3, 1.45)))
    head_rot(ff - 4)
    head_rot(ff + 8, roll=4)


def animate_ear(e):
    drum, tube = e["drum"], e["tube"]
    keys = drum.data.shape_keys.key_blocks
    tube_mat = tube.data.materials[0].node_tree.nodes["Principled BSDF"]
    drum_mat = drum.data.materials[0].node_tree.nodes["Principled BSDF"]
    for f in (1,):
        key(keys["Out"], "value", f, 0.0)
        key(keys["In"], "value", f, 0.0)
        key(tube.data, "bevel_depth", f, 0.16)
        key(tube_mat.inputs["Base Color"], "default_value", f, (0.78, 0.38, 0.36, 1))
        key(drum_mat.inputs["Emission Strength"], "default_value", f, 0.0)
        drum_mat.inputs["Emission Color"].default_value = (1.0, 0.25, 0.15, 1)
        tube_mat.inputs["Emission Color"].default_value = (1.0, 0.1, 0.1, 1)
        key(tube_mat.inputs["Emission Strength"], "default_value", f, 0.0)
    # gentle drifting molecules (noise on their location curves)
    for i, mol in enumerate(e["outside"] + e["inside"]):
        key(mol, "location", 1, Vector(mol.location))
        key(mol, "scale", 1, (0.11,) * 3)
        for fc in mol.animation_data.action.fcurves:
            if fc.data_path == "location":
                n = fc.modifiers.new("NOISE")
                n.scale, n.strength, n.phase = 40, 0.6 if fc.array_index != 0 or i >= 48 else 1.2, i * 3.1 + fc.array_index
    # cabin pressure drops: outside air thins (staggered) on "drops"
    fd = beat("S05b", "drops")
    for i, mol in enumerate(e["outside"]):
        if i % 20 < 11:
            key(mol, "scale", fd - 6 + i % 18, (0.11,) * 3)
            key(mol, "scale", fd + 2 + i % 18, (0.0,) * 3)
    # eardrum bulges outward on "bulges", strain glow
    fp, fb = beat("S06", "pushes"), beat("S06", "bulges")
    key(keys["Out"], "value", fp, 0.0)
    key(keys["Out"], "value", fb + 12, 1.0)
    key(drum_mat.inputs["Emission Strength"], "default_value", fp, 0.0)
    key(drum_mat.inputs["Emission Strength"], "default_value", fb + 12, 2.5)
    # the tube cracks open on "cracks"; air flows down it until the end of S09
    fk = beat("S08", "cracks")
    key(tube.data, "bevel_depth", fk - 2, 0.16)
    key(tube.data, "bevel_depth", fk + 10, 0.55)
    flow_end = rng("S09b")[1]
    for i, mol in enumerate(e["flow"]):
        key(mol, "scale", fk + 2 + i, (0.0,) * 3, interp="CONSTANT")
        key(mol, "scale", fk + 3 + i, (0.11,) * 3, interp="CONSTANT")
        key(mol, "scale", flow_end, (0.0,) * 3, interp="CONSTANT")
        for f in range(fk + 3 + i, flow_end, 3):
            ring = Vector((0, math.cos(i * 2.4), math.sin(i * 2.4))) * 0.3  # stream around the tube's axis (and the camera)
            key(mol, "location", f, tube_point(((f - fk) / 45.0 + i / 14) % 1.0, e["origin"]) + ring, interp="LINEAR")
    # air escapes: inside air thins between "escapes" and "evens"
    fe, fv = beat("S09a", "escapes"), beat("S09a", "evens")
    for i, mol in enumerate(e["inside"]):
        if i % 5 < 2:
            key(mol, "scale", fe + i % 30, (0.11,) * 3)
            key(mol, "scale", fv + i % 10, (0.0,) * 3)
    # POP: eardrum snaps flat with an overshoot, flash and light ring
    fpop = beat("S09b", "pop")
    key(keys["Out"], "value", fpop - 1, 1.0)
    key(keys["Out"], "value", fpop + 3, 0.0)
    key(keys["In"], "value", fpop + 3, 0.0)
    key(keys["In"], "value", fpop + 7, 0.22)
    key(keys["In"], "value", fpop + 14, 0.0)
    key(drum_mat.inputs["Emission Strength"], "default_value", fpop - 1, 2.5)
    key(drum_mat.inputs["Emission Strength"], "default_value", fpop + 4, 0.0)
    key(e["flash"].data, "energy", fpop - 1, 0.0)
    key(e["flash"].data, "energy", fpop + 1, 6000.0)
    key(e["flash"].data, "energy", fpop + 12, 0.0)
    key(e["ring"], "scale", fpop, (0.0,) * 3, interp="CONSTANT")
    key(e["ring"], "scale", fpop + 1, (0.3,) * 3)
    key(e["ring"], "scale", fpop + 14, (4.5,) * 3)
    key(e["ring"], "scale", fpop + 15, (0.0,) * 3, interp="CONSTANT")
    # landing: outside air returns, the tube closes and turns red, eardrum pushed in
    f11 = rng("S11")[0]
    for mol in e["outside"]:
        key(mol, "scale", f11 - 5, (0.11,) * 3)
    key(tube.data, "bevel_depth", f11 - 5, 0.16)
    fo, fi = beat("S11", "open"), beat("S11", "inward")
    key(tube_mat.inputs["Base Color"], "default_value", fo - 2, (0.78, 0.38, 0.36, 1))
    key(tube_mat.inputs["Base Color"], "default_value", fo + 8, (0.9, 0.08, 0.08, 1))
    key(tube_mat.inputs["Emission Strength"], "default_value", fo - 2, 0.0)
    key(tube_mat.inputs["Emission Strength"], "default_value", fo + 8, 2.0)
    key(keys["In"], "value", fi - 6, 0.0)
    key(keys["In"], "value", fi + 14, 1.0)
    key(drum_mat.inputs["Emission Strength"], "default_value", fi - 6, 0.0)
    key(drum_mat.inputs["Emission Strength"], "default_value", fi + 14, 2.0)


# --------------------------------------------------------------- cameras ---
def build_cameras(sc, m):
    coll = collection("CAMERAS", sc.collection)
    head = lambda: m["head"].matrix_world.translation + Vector((0, 0, 0.14))  # noqa: E731
    sc.frame_set(1)
    D = m.get("offset", Vector())                    # real Max's head vs the grey-box Max's (cabin shots follow it)
    cab = lambda x, y, z: CABIN + Vector((x, y, z)) + D  # noqa: E731
    hole = m.get("hole", CABIN + Vector((0.13, 0.355, 1.65)))   # Max's left ear opening (head neutral)
    face = m.get("face", CABIN + Vector((0.0, 0.35, 1.62)))
    window = CABIN + Vector((1.79, -0.25, 1.75 + D.z))
    I, M = EAR, EAR_MAP                              # inside-the-ear set, x-ray map set
    drum = I + Vector((-0.8, 0, 0))
    cams = {}

    def shot(sid, move, lens0, step=3, clip=0.02):
        cam = camera(f"CAM_{sid}", coll, lens=lens0)
        cam.data.clip_start = clip
        f0, f1 = rng(sid)
        bake_move(cam, f0, f1, move, step=step)
        cams[sid] = cam
        return cam

    def turn(pos, yaw_deg, pitch=0.0, dist=4.0):
        a = math.radians(yaw_deg)
        return pos + Vector((math.cos(a), math.sin(a), pitch)) * dist

    def s01(t):  # drone reveal: from under the wing, pulling back and rising as the jet climbs
        j = jet_at("S01", t)
        return {"pos": j + lerp(Vector((-1.5, -5.5, -2.4)), Vector((-8, -30, 4)), ease(t)), "target": j, "lens": 24}
    shot("S01", s01, 24, step=2)

    def s02(t):  # curved push round Max to his ear, then INTO the ear opening (ends in darkness)
        k = ease(t)
        pos = bezier(cab(0.3, -2.7, 1.55), cab(0.95, -1.7, 1.62),
                     cab(0.9, 0.1, 1.66), hole + Vector((0.002, 0, 0)), k)  # ends inside the opening: black
        if t < 0.6:
            tgt = lerp(cab(0.05, 0.35, 1.45), hole, ease(t / 0.6))
        else:
            tgt = hole + lerp(Vector(), Vector((-0.3, 0, 0)), ease((t - 0.6) / 0.4))
        focus = lerp((window - pos).length, (hole - pos).length, ease(min(1, t / 0.4)))
        return {"pos": pos, "target": tgt, "lens": lerp(50, 28, k), "focus": max(0.01, focus)}
    shot("S02", s02, 50, step=2, clip=0.002)

    def s03(t):  # out of the dark, gliding down the glowing canal, slowing at the eardrum
        x = lerp(-18.5, -2.4, ease(t))
        wob = Vector((0, 0.12 * math.sin(t * 7), 0.15 + 0.1 * math.sin(t * 5)))
        return {"pos": I + Vector((x, 0, 0)) + wob, "target": I + Vector((x + 6, 0, 0.05)), "lens": 20}
    shot("S03", s03, 20, step=2)

    def s04(t):  # slip through the eardrum into the middle ear, then turn round to face it
        if t < 0.5:
            x = lerp(-2.4, 1.2, ease(t / 0.5))
            return {"pos": I + Vector((x, 0, 0.1)), "target": I + Vector((x + 5, 0, 0.1)), "lens": 22}
        k = ease((t - 0.5) / 0.5)
        pos = lerp(I + Vector((1.2, 0, 0.1)), I + Vector((3.4, 0.9, 0.7)), k)
        return {"pos": pos, "target": turn(pos, lerp(0, -168, k), lerp(0, -0.16, k)), "lens": 22}
    shot("S04", s04, 22, step=2)

    shot("S04m", lambda t: {"pos": M + Vector((-1.4 + 0.08 * t, -21, -0.4 + 0.05 * math.sin(t * 3))),
                            "target": M + Vector((-1.4, 0, -0.5)), "lens": 50}, 50)

    def s05a(t):  # drone flyover high above the cloud deck
        j = jet_at("S05a", t)
        return {"pos": j + lerp(Vector((-30, -75, 38)), Vector((-18, -82, 44)), ease(t)), "target": j, "lens": 35}
    shot("S05a", s05a, 35, step=2)

    shot("S05b", lambda t: {"pos": lerp(I + Vector((2.8, -1.5, -1.0)), I + Vector((3.3, -1.7, -1.1)), ease(t)),
                            "target": drum + Vector((0, 0, -0.2)), "lens": 30}, 30)

    shot("S06", lambda t: {"pos": lerp(I + Vector((2.2, -1.5, -1.2)), I + Vector((1.3, -1.0, -0.8)), ease(t)),
                           "target": drum + Vector((0, 0, -0.1)), "lens": 24, "roll": 5 * ease(t)}, 24)

    cam7 = shot("S07", lambda t: {"pos": lerp(cab(0.12, -1.0, 1.66), cab(0.12, -0.92, 1.66), t),
                                  "target": head(), "lens": 85}, 85)
    handheld(cam7, *rng("S07"), strength=0.2)

    shot("S08", lambda t: {"pos": lerp(I + Vector((3.4, -1.2, 0.9)), I + Vector((2.75, 0.35, -1.0)), ease(t)),
                           "target": lerp(I + Vector((0.8, 0, -0.8)), I + Vector((2.55, 0.15, -3.2)), ease(t)),
                           "lens": 24}, 24)

    f0, f1 = rng("S09a")
    whip_up = 1 - 6 / (f1 - f0)

    def s09a(t):  # ride down the Eustachian tube with the escaping air, whip up at the end
        u = lerp(0.0, 0.7, ease(t))
        tgt = tube_point(min(1.0, u + 0.15), I)
        if t > whip_up:
            tgt = tgt + Vector((0, 0, 40 * ((t - whip_up) / (1 - whip_up)) ** 2))
        return {"pos": tube_point(u, I), "target": tgt, "lens": 18}
    shot("S09a", s09a, 18, step=1)

    f0, f1 = rng("S09b")
    whip_t = 1 - 6 / (f1 - f0)

    def s09b(t):  # face the eardrum from inside: POP! then whip-pan right into S10
        tgt = drum
        if t > whip_t:
            tgt = tgt + Vector((0, 70 * ((t - whip_t) / (1 - whip_t)) ** 2, 0))
        return {"pos": lerp(I + Vector((2.9, -1.6, -1.1)), I + Vector((2.1, -1.2, -0.8)), ease(t)), "target": tgt, "lens": 28}
    cam9 = shot("S09b", s09b, 28, step=1)
    impulse_shake(cam9, beat("S09b", "pop"), frames=10, amp=0.06)

    f0, f1 = rng("S10")
    whip_in = 6 / (f1 - f0)

    def s10(t):  # drone tracking behind the descending jet (whip lands from the left)
        j = jet_at("S10", t)
        tgt = j + (Vector((-60 * (1 - t / whip_in) ** 2, 0, 0)) if t < whip_in else Vector())
        return {"pos": j + lerp(Vector((16, -24, 12)), Vector((13, -21, 9)), ease(t)), "target": tgt, "lens": 35}
    shot("S10", s10, 35, step=1)

    def s11(t):  # arc inside the middle ear: eardrum caves toward us, tube pinched red below
        k = ease(t)
        pos = bezier(I + Vector((3.4, -1.2, -0.6)), I + Vector((3.9, -0.4, -0.8)), I + Vector((3.9, 0.5, -0.7)),
                     I + Vector((3.4, 1.1, -0.4)), k)
        return {"pos": pos, "target": I + Vector((0.6, 0, -0.9)), "lens": 22, "roll": -5 * k}
    shot("S11", s11, 22)

    shot("S12a", lambda t: {"pos": I + Vector((lerp(-2.6, -19.0, t * t), 0, 0.15)),   # accelerate back out
                            "target": I + Vector((lerp(-2.6, -19.0, t * t) - 6, 0, 0.1)), "lens": 20}, 20, step=2)

    def s12b(t):  # emerge from Max's ear, pull back and arc round to his face (yawn reveal)
        k = ease(min(1.0, t * 1.4)) if m.get("real") else ease(t)  # real Max: reach his face while he yawns
        pos = bezier(hole + Vector((0.002, 0, 0)), hole + Vector((0.6, 0, 0.05)), cab(1.1, -1.2, 1.62),
                     cab(0.35, -2.2, 1.55), k)
        tgt = lerp(hole - Vector((0.3, 0, 0)), face, ease(min(1.0, t * 1.6)))
        return {"pos": pos, "target": tgt, "lens": lerp(28, 40, k)}
    shot("S12b", s12b, 28, step=2, clip=0.002)

    shot("S13", lambda t: {"pos": lerp(cab(0.05, -1.55, 1.62), cab(0.05, -1.15, 1.63), ease(t)),
                           "target": head() + (Vector((-0.04, 0, -0.07)) if m.get("real") else Vector((0, 0, -0.04))),
                           "lens": 70 if m.get("real") else 85}, 85)  # real Max: keep his raised thumb in frame

    for sid, cam in cams.items():  # timeline markers bound to cameras -> camera cuts in FILM
        mk = sc.timeline_markers.new(sid, frame=SHOT[sid]["start"])
        mk.camera = cam
    sc.camera = cams["S01"]
    return cams


# ------------------------------------------------------------------- edit ---
def add_sound(seq, name, path, channel, frame):
    st = strips(seq).new_sound(name, str(path), channel, frame)
    st.sound.pack()
    return st


def strips(seq):
    return seq.strips if hasattr(seq, "strips") else seq.sequences


def effect(ss, name, kind, channel, start, end, a=None, b=None):
    """new_effect across Blender versions (inputs were seq1/seq2 before 4.4, input1/input2 after)."""
    kw = {}
    if a is not None:
        names = [p.identifier for p in ss.bl_rna.functions["new_effect"].parameters]
        k1, k2 = ("input1", "input2") if "input1" in names else ("seq1", "seq2")
        kw = {k1: a, k2: b}
    return ss.new_effect(name, kind, channel, frame_start=start, frame_end=end, **kw)


def build_edit(film, cams):
    ed = bpy.data.scenes.new("EDIT")
    ed.render.fps = film.render.fps
    ed.render.resolution_x, ed.render.resolution_y = film.render.resolution_x, film.render.resolution_y
    ed.frame_start, ed.frame_end = 1, film.frame_end
    ed.sync_mode = "AUDIO_SYNC"
    ed.render.sequencer_gl_preview = "MATERIAL"
    seq = ed.sequence_editor_create()
    ss = strips(seq)
    total = film.frame_end
    prev = None
    for i, sh in enumerate(PLAN["shots"]):
        ch = 2 + i % 2
        st = ss.new_scene(sh["id"], film, ch, 1)
        st.scene_camera = cams[sh["id"]]
        out = sh.get("out", "cut")
        extra = int(out.split(":")[1]) if out.startswith("dissolve") else 0
        st.frame_offset_start = sh["start"] - 1
        st.frame_offset_end = max(0, total - (sh["end"] + extra))
        if prev is not None and prev[1].startswith("dissolve"):
            n = int(prev[1].split(":")[1])
            effect(ss, f"dissolve_{prev[0].name}", "CROSS", 4, sh["start"], sh["start"] + n, prev[0], st)
        prev = (st, out)
    for i, c in enumerate(PLAN["captions"]):
        t = effect(ss, f"cap_{i + 1:02d}", "TEXT", 6, c["start"], c["end"] + 6)
        t.text, t.font_size, t.wrap_width = c["text"], 58, 0.86
        t.location, t.anchor_x, t.anchor_y = (0.5, 0.22), "CENTER", "CENTER"
        t.use_box, t.box_color = True, (0, 0, 0, 0.55)
    add_sound(seq, "voice", HERE / PLAN["voice"], 8, 1)
    for i, s in enumerate(PLAN["sfx"]):
        st = add_sound(seq, f"sfx_{s['cue']}", HERE / s["file"], 9 + i % 2, s["frame"])
        st.volume = 0.35
    for b in (b for sh in PLAN["shots"] for b in sh["beats"] if b.get("word")):
        ed.timeline_markers.new(b["word"], frame=b["frame"])
    return ed


def film_sound(film):
    seq = film.sequence_editor_create()
    add_sound(seq, "voice", HERE / PLAN["voice"], 1, 1)
    for i, s in enumerate(PLAN["sfx"]):
        add_sound(seq, f"sfx_{s['cue']}", HERE / s["file"], 2 + i % 2, s["frame"]).volume = 0.35


def viewports(film=None):
    if film is not None:  # open the file on FILM, so the first thing you see is the 3D film
        for wm in bpy.data.window_managers:
            for win in wm.windows:
                win.scene = film
    for scr in bpy.data.screens:
        for area in scr.areas:
            if area.type == "VIEW_3D":
                for sp in area.spaces:
                    if sp.type == "VIEW_3D":
                        sp.shading.type = "MATERIAL"
                        sp.shading.use_scene_world = True
                        sp.shading.use_scene_lights = True
                        sp.region_3d.view_perspective = "CAMERA"
                        sp.overlay.show_overlays = True


def stills(film, cams, out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    film.render.engine = "CYCLES"
    film.cycles.samples, film.cycles.use_denoising = 12, True
    film.render.resolution_percentage = 25
    film.render.use_sequencer = False
    for sh in PLAN["shots"]:  # early / middle / late frame of every shot, to check each move
        film.camera = cams[sh["id"]]
        for tag, k in (("a", 0.12), ("b", 0.5), ("c", 0.92)):
            film.frame_set(int(sh["start"] + (sh["end"] - sh["start"]) * k))
            film.render.filepath = str(out_dir / f"{sh['id']}_{tag}.png")
            bpy.ops.render.render(write_still=True, scene=film.name)
    film.render.resolution_percentage = 100
    film.render.use_sequencer = True
    film.camera = cams["S01"]
    film.frame_set(1)


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    film = setup_film()
    sky = build_sky(film)
    if "--standin" in args or not real_max.MAX_BLEND.exists():
        m = build_cabin(film)
    else:
        m = real_max.load(film, CABIN)
        if "--greybox-sets" in args:
            build_cabin(film, with_max=False, window_z=1.75 + m["offset"].z)
        else:
            real_cabin(film, CABIN)
    e = build_ear(film, EAR, inside=True)
    e_map = build_ear(film, EAR_MAP, inside=False)
    build_city(film)
    animate_jet(sky["jet"])
    if m.get("real"):
        real_max.perform(m, beat, rng, film)
    else:
        animate_max(m)
    animate_ear(e)
    animate_ear(e_map)
    cams = build_cameras(film, m)
    film_sound(film)
    build_edit(film, cams)
    viewports(film)
    if "--stills" in args:
        stills(film, cams, Path(args[args.index("--stills") + 1]))
        for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
            try:
                film.render.engine = eng
                break
            except TypeError:
                continue
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "pilot_ear_pop_previz.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(path), compress=True)
    print(f"[build] saved {path}")


main()
