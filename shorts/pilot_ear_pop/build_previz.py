"""Build the pilot's grey-box previz .blend (run inside Blender):

  blender -b --factory-startup -P shorts/pilot_ear_pop/build_previz.py -- [--stills DIR] [--standin]

Reads plan.json (prep_plan.py) and writes out/pilot_ear_pop/pilot_ear_pop_previz.blend with:
  FILM  every set, one camera per shot (bound to timeline markers, so playing it in camera
        view cuts between shots), all animation keyed to spoken words, plus the voice and SFX.
  EDIT  the cut: one strip per shot (FILM through that shot's camera), short bold captions with
        the keyword in yellow, the map's labels and pressure badges, the follow card, voice and SFX.
        Play it to watch the whole film end to end.
--stills renders low-res Cycles frames (early/middle/late) of every shot for review.
Max is the real rigged character (assets/characters/max/max_v3.blend, see real_max.py) with his
expressions keyed to the voice; --standin uses the grey-box Max instead.
"""
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Quaternion, Vector

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "blender"))
from greybox import CABIN, CITY, EAR, EAR_MAP, SKY, build_cabin, build_max as greybox_max, build_city, build_ear, build_sky, tube_point  # noqa: E402
from rigs import bake_move, bezier, camera, collection, ease, handheld, impulse_shake, key, lerp, material, output_format, fcurves, prim  # noqa: E402
sys.path.insert(0, str(HERE))
import real_max  # noqa: E402
from sets import city as city_real  # noqa: E402
from sets import assemble  # noqa: E402

PLAN = json.loads((HERE / "plan.json").read_text())
OUT = HERE.parent.parent / "out" / "pilot_ear_pop"
SHOT = {s["id"]: s for s in PLAN["shots"]}


def beat(shot_id, word):
    """Frame of a beat: a spoken word, or a timed beat's `key` (shots.yaml)."""
    return next(b["frame"] for b in SHOT[shot_id]["beats"] if word in (b.get("word"), b.get("key")))


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
    output_format(r.image_settings, "FFMPEG")
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
            ("S05a", SKY + Vector((-10, 0, 3)), SKY + Vector((10, 0, 10)), (0, -8, 0), False),   # visibly climbing, nose up 8 deg
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
    fc = [c for c in fcurves(jet) if c.data_path == "location"]
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
    # S00: the cold open, wincing with a hand on his ear; the hand is back in his lap by S02's fly-in
    key(hand_l, "location", 1, ear + Vector((0.02, -0.01, 0.0)))
    head_rot(1, pitch=-4, roll=-10)
    key(hand_l, "location", rng("S02")[0] - 2, lap_l)
    head_rot(rng("S02")[0] - 2)
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
    fs, fy, fc = (beat("S12a", w) for w in ("swallowing", "yawning", "chewing"))
    fo = beat("S12b", "open")
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
    ff = beat("S13", "thumbs")
    key(hand_r, "location", ff - 4, lap_r)
    key(hand_r, "location", ff + 8, Vector((-0.2, -0.3, 1.45)))
    head_rot(ff - 4)
    head_rot(ff + 8, roll=4)


CLOSED = 0.05   # Eustachian tube bevel when shut: a thin slit
BEAD = 0.08     # air bead radius: smaller than the set's 0.11, so the air reads without crowding the frame


def animate_ear(e):
    drum, tube = e["drum"], e["tube"]
    keys = drum.data.shape_keys.key_blocks
    tube_mat = tube.data.materials[0].node_tree.nodes["Principled BSDF"]
    drum_mat = drum.data.materials[0].node_tree.nodes["Principled BSDF"]
    for f in (1,):
        key(keys["Out"], "value", f, 0.0)
        key(keys["In"], "value", f, 0.0)
        key(tube.data, "bevel_depth", f, CLOSED)   # the tube is a closed slit until it cracks open
        key(tube_mat.inputs["Base Color"], "default_value", f, (0.78, 0.38, 0.36, 1))
        key(drum_mat.inputs["Emission Strength"], "default_value", f, 0.0)
        drum_mat.inputs["Emission Color"].default_value = (1.0, 0.25, 0.15, 1)
        tube_mat.inputs["Emission Color"].default_value = (1.0, 0.1, 0.1, 1)
        key(tube_mat.inputs["Emission Strength"], "default_value", f, 0.0)
    # gentle drifting molecules (noise on their location curves)
    o = e["origin"]
    valve = bpy.data.objects.get(f"tube_valve_{e['tag']}")   # inside only: the lips at the tube's mouth

    def tube_shut(f, shut):
        key(tube.data, "bevel_depth", f, CLOSED if shut else 0.55)
        if valve:
            key(valve, "scale", f, (0.26, 0.26, 0.05) if shut else (0.0, 0.0, 0.0))
    for i, mol in enumerate(e["outside"] + e["inside"]):
        if i < len(e["outside"]) and mol.location.x > o.x - 2.4:
            mol.location.x = o.x - 2.4      # canal air keeps clear of the eardrum: air never passes through it
        key(mol, "location", 1, Vector(mol.location))
        key(mol, "scale", 1, (BEAD,) * 3)
        for fc in fcurves(mol):
            if fc.data_path == "location":
                n = fc.modifiers.new("NOISE")
                n.scale, n.strength, n.phase = 40, 0.3 if fc.array_index == 0 else 0.6, i * 3.1 + fc.array_index
    # cabin pressure drops: outside air thins (staggered) on "drops"
    fd = beat("S05b", "drops")
    for i, mol in enumerate(e["outside"]):
        if i % 20 < 11:
            key(mol, "scale", fd - 6 + i % 18, (BEAD,) * 3)
            key(mol, "scale", fd + 2 + i % 18, (0.0,) * 3)
    # eardrum bulges outward on "bulges", strain glow
    fp, fb = beat("S06a", "pushes"), beat("S06b", "bulges")
    key(keys["Out"], "value", fp, 0.0)
    key(keys["Out"], "value", fb + 12, 1.0)
    key(drum_mat.inputs["Emission Strength"], "default_value", fp, 0.0)
    key(drum_mat.inputs["Emission Strength"], "default_value", fb + 12, 2.5)
    for mol in e["inside"]:          # the trapped air crowds toward the eardrum, then eases back once it pops
        base = Vector(mol.location)
        crowd = base + Vector((-0.45 * max(0.0, 1.0 - (base.x - o.x) / 4.5), 0, 0))
        key(mol, "location", fp - 2, base)
        key(mol, "location", fb + 10, crowd)
        key(mol, "location", beat("S09b", "pop") + 6, crowd)
        key(mol, "location", beat("S09b", "pop") + 30, base)
    # the tube's slit cracks open on "cracks"; air flows down it (middle ear -> throat) until the end of S09
    fk = beat("S08b", "cracks")
    tube_shut(1, True)
    tube_shut(fk - 2, True)
    tube_shut(fk + 10, False)
    flow_end = rng("S09b")[1]
    for i, mol in enumerate(e["flow"]):
        key(mol, "scale", fk + 2 + i, (0.0,) * 3, interp="CONSTANT")
        key(mol, "scale", fk + 3 + i, (BEAD,) * 3, interp="CONSTANT")
        key(mol, "scale", flow_end, (0.0,) * 3, interp="CONSTANT")
        for f in range(fk + 3 + i, flow_end, 3):
            ring = Vector((0, math.cos(i * 2.4), math.sin(i * 2.4))) * 0.3  # stream around the tube's axis (and the camera)
            key(mol, "location", f, tube_point(((f - fk) / 45.0 + i / 14) % 1.0, e["origin"]) + ring, interp="LINEAR")
    # air escapes: inside air thins between "escapes" and "evens"
    fe, fv = beat("S09a", "escapes"), beat("S09a", "evens")
    for i, mol in enumerate(e["inside"]):
        if i % 5 < 2:
            key(mol, "scale", fe + i % 30, (BEAD,) * 3)
            key(mol, "scale", fv + i % 10, (0.0,) * 3)
    # POP: eardrum snaps flat with an overshoot, a soft flash and light ring (a snap, not a burst)
    fpop = beat("S09b", "pop")
    key(keys["Out"], "value", fpop - 1, 1.0)
    key(keys["Out"], "value", fpop + 3, 0.0)
    key(keys["In"], "value", fpop + 3, 0.0)
    key(keys["In"], "value", fpop + 7, 0.22)
    key(keys["In"], "value", fpop + 14, 0.0)
    key(drum_mat.inputs["Emission Strength"], "default_value", fpop - 1, 2.5)
    key(drum_mat.inputs["Emission Strength"], "default_value", fpop + 4, 0.0)
    key(e["flash"].data, "energy", fpop - 1, 0.0)
    key(e["flash"].data, "energy", fpop + 1, 3000.0)
    key(e["flash"].data, "energy", fpop + 12, 0.0)
    key(e["ring"], "scale", fpop, (0.0,) * 3, interp="CONSTANT")
    key(e["ring"], "scale", fpop + 1, (0.3,) * 3)
    key(e["ring"], "scale", fpop + 14, (2.6,) * 3)
    key(e["ring"], "scale", fpop + 15, (0.0,) * 3, interp="CONSTANT")
    # descent: outside air returns, the tube stays shut and turns red, eardrum pushed in
    f11 = rng("S11a")[0]
    for mol in e["outside"]:
        key(mol, "scale", f11 - 5, (BEAD,) * 3)
    tube_shut(f11 - 25, False)
    tube_shut(f11 - 5, True)
    fo, fi = beat("S11a", "shut"), beat("S11b", "inward")
    key(tube_mat.inputs["Base Color"], "default_value", fo - 2, (0.78, 0.38, 0.36, 1))
    key(tube_mat.inputs["Base Color"], "default_value", fo + 8, (0.9, 0.08, 0.08, 1))
    key(tube_mat.inputs["Emission Strength"], "default_value", fo - 2, 0.0)
    key(tube_mat.inputs["Emission Strength"], "default_value", fo + 8, 2.0)
    key(keys["In"], "value", fi - 6, 0.0)
    key(keys["In"], "value", fi + 14, 1.0)
    key(drum_mat.inputs["Emission Strength"], "default_value", fi - 6, 0.0)
    key(drum_mat.inputs["Emission Strength"], "default_value", fi + 14, 2.0)
    # swallowing pulls the tube open: cabin air (blue) flows UP into the middle ear, the eardrum returns
    fu, fr = beat("S12b", "pull"), beat("S12b", "open")
    tube_shut(fu - 3, True)
    tube_shut(fu + 6, False)
    key(tube_mat.inputs["Base Color"], "default_value", fu - 3, (0.9, 0.08, 0.08, 1))
    key(tube_mat.inputs["Base Color"], "default_value", fu + 6, (0.78, 0.38, 0.36, 1))
    key(tube_mat.inputs["Emission Strength"], "default_value", fu - 3, 2.0)
    key(tube_mat.inputs["Emission Strength"], "default_value", fu + 6, 0.0)
    key(keys["In"], "value", fu, 1.0)
    key(keys["In"], "value", fr + 4, 0.0)
    key(drum_mat.inputs["Emission Strength"], "default_value", fu, 2.0)
    key(drum_mat.inputs["Emission Strength"], "default_value", fr + 4, 0.0)
    f12, end = rng("S12b")[0], rng("S13")[1]
    for i, mol in enumerate(blue_flow(e)):
        key(mol, "scale", f12, (0.0,) * 3, interp="CONSTANT")
        key(mol, "scale", fu + i, (BEAD,) * 3, interp="CONSTANT")
        for f in range(fu + i, end, 3):
            u = 1.0 - min(1.0, (f - fu) / 40.0 + i / 12)       # from the throat end up toward the middle ear
            ring = Vector((0, math.cos(i * 2.4), math.sin(i * 2.4))) * 0.2
            if e["tag"] == "map":           # the map's tube is opaque: draw the air on its near side
                ring += Vector((0, -0.65, 0))
            key(mol, "location", f, tube_point(u, o) + ring, interp="LINEAR")


def blue_flow(e, n=12):
    """Cabin air for the descent's fix: blue copies of the tube-flow beads (same set collection)."""
    blue = bpy.data.materials["air_outside"]
    out = []
    for i in range(n):
        src = e["flow"][i % len(e["flow"])]
        ob = src.copy()
        ob.data = src.data.copy()
        ob.data.materials.clear()
        ob.data.materials.append(blue)
        ob.animation_data_clear()
        ob.name = f"air_up_{i:02d}_{e['tag']}"
        src.users_collection[0].objects.link(ob)
        ob.scale = (0.0,) * 3
        out.append(ob)
    return out


def rest_line(e):
    """On the x-ray map: a faint line where the flat eardrum sits, so its bulge (out, then in) reads
    at a glance in the profile shots."""
    o = e["origin"]
    ob = prim("cylinder", "eardrum_rest_line_map", e["drum"].users_collection[0], o + Vector((-0.8, -1.7, 0)),
              (0.025, 0.025, 1.6), mat=material("rest_line", (1.0, 1.0, 1.0), emission=1.5), vertices=12)
    ob.visible_shadow = False
    return ob


def declutter(cams, ears, frac=0.2, fly_frac=0.25, step=2):
    """Keep the air beads from cluttering a shot: hide a bead for the frames where its on-screen size
    passes `frac` of the frame width (`fly_frac` in flythroughs, where passing beads give the sense of
    speed), or where it sits in front of the eardrum, over its silhouette. The beads flowing down the
    tube are the subject of their shots and are never hidden."""
    by_set = {"ear_inside": ears[0], "ear_map": ears[1]}
    DRUM_SHOTS = {"S04", "S05b", "S09b", "S11a"}        # the eardrum's shape is the point: keep it unobstructed

    def at(ob, path, n, f):
        cs = {c.array_index: c for c in fcurves(ob) if c.data_path == path}
        base = getattr(ob, path)
        return [cs[i].evaluate(f) if i in cs else base[i] for i in range(n)]

    report, spans = [], {}

    def on_screen(e, cam, f):
        """Beads in frame and not hidden at frame f."""
        pos = Vector(at(cam, "location", 3, f))
        rot = Quaternion(at(cam, "rotation_quaternion", 4, f)).normalized()
        fwd, right, up = rot @ Vector((0, 0, -1)), rot @ Vector((1, 0, 0)), rot @ Vector((0, 1, 0))
        tan_h = 12.0 / at(cam.data, "lens", 1, f)[0]
        n = 0
        for mol in e["outside"] + e["inside"]:
            v = Vector(at(mol, "location", 3, f)) - pos
            d = v.dot(fwd)
            if d <= 0.05 or at(mol, "scale", 3, f)[0] < 0.01 or any(a <= f <= b for a, b in spans.get(mol.name, [])):
                continue
            if abs(v.dot(right)) < d * tan_h * 9 / 16 and abs(v.dot(up)) < d * tan_h:
                n += 1
        return n
    for sid, cam in cams.items():
        e = by_set.get(SHOT[sid]["set"])
        if e is None:
            continue
        cap = fly_frac if SHOT[sid]["move"] == "flythrough" else frac
        f0, f1 = rng(sid)
        drum = e["drum"].location
        n_bad = set()
        for f in range(f0, f1 + 1, step):
            pos = Vector(at(cam, "location", 3, f))
            fwd = Quaternion(at(cam, "rotation_quaternion", 4, f)).normalized() @ Vector((0, 0, -1))
            tan_w = 12.0 / at(cam.data, "lens", 1, f)[0] * 9 / 16     # half-width over depth (24 mm vertical, 9:16)
            dd = (drum - pos).dot(fwd)
            drum_c, drum_r = ((drum - pos) / dd, 1.55 / dd / tan_w) if dd > 0 else (None, 0)
            for mol in e["outside"] + e["inside"]:
                v = Vector(at(mol, "location", 3, f)) - pos
                d = v.dot(fwd)
                if d <= 0.05 or at(mol, "scale", 3, f)[0] < 0.01:
                    continue
                if BEAD / (d * tan_w) > cap or (drum_c is not None and sid in DRUM_SHOTS and d < dd
                                                and ((v / d) - drum_c).length / tan_w < drum_r):
                    spans.setdefault(mol.name, []).append((f, min(f + step - 1, f1)))
                    n_bad.add(mol.name)
        if n_bad:
            report.append(f"{sid} {on_screen(e, cam, (f0 + f1) // 2)} in frame ({len(n_bad)} hidden at times)")
    for name, frames in spans.items():                   # merge touching spans, key hide on / off
        mol, merged = bpy.data.objects[name], []
        for a, b in sorted(frames):
            if merged and a <= merged[-1][1] + 1:
                merged[-1][1] = max(merged[-1][1], b)
            else:
                merged.append([a, b])
        for a, b in merged:
            for f, h in ((a - 1, False), (a, True), (b + 1, False)):
                for prop in ("hide_render", "hide_viewport"):
                    setattr(mol, prop, h)
                    mol.keyframe_insert(prop, frame=f)
    print(f"[build] declutter (mid-shot beads in frame, of {len(ears[0]['outside']) + len(ears[0]['inside'])}"
          f" per set): {', '.join(report)}")


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

    def face_cu(sid, lens=85, near=-0.92, far=-1.0, shake=0.0, aim=Vector((0, 0, 0))):
        """Max close-up from the aisle side (the hook, the wince, his relief, the tips)."""
        cam = shot(sid, lambda t: {"pos": lerp(cab(0.12, far, 1.66), cab(0.12, near, 1.66), ease(t)),
                                   "target": head() + aim, "lens": lens}, lens)
        if shake:
            handheld(cam, *rng(sid), strength=shake)
        return cam

    face_cu("S00", near=-0.95, far=-0.98, shake=0.3)    # cold open: he's already wincing

    def s01(t):  # drone reveal: from under the wing, pulling back and rising as the jet climbs
        j = jet_at("S01", t)
        return {"pos": j + lerp(Vector((-1.5, -5.5, -2.4)), Vector((-8, -30, 4)), ease(t)), "target": j, "lens": 24}
    shot("S01", s01, 24, step=2)

    def s02(t):  # fast curved push round Max to his ear, then INTO the ear opening (ends in darkness)
        k = ease(t)
        pos = bezier(cab(0.6, -1.7, 1.6), cab(1.0, -0.9, 1.63),
                     cab(0.8, 0.1, 1.66), hole + Vector((0.002, 0, 0)), k)  # ends inside the opening: black
        if t < 0.5:
            tgt = lerp(face, hole, ease(t / 0.5))
        else:
            tgt = hole + lerp(Vector(), Vector((-0.3, 0, 0)), ease((t - 0.5) / 0.5))
        return {"pos": pos, "target": tgt, "lens": lerp(45, 28, k), "focus": max(0.01, (hole - pos).length)}
    shot("S02", s02, 45, step=1, clip=0.002)

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

    # x-ray map: a slow push in (orientation, labelled in the edit)
    shot("S04m", lambda t: {"pos": M + Vector((0.2, lerp(-21, -19, ease(t)), -1.5)),
                            "target": M + Vector((0.2, 0, -1.5)), "lens": 35}, 35)   # canal end, drum, middle ear, tube

    # the climb: the camera holds its height while the jet rises nose-up past the cloud deck
    p5 = SKY + Vector((-22, -66, 4))
    shot("S05a", lambda t: {"pos": p5 + Vector((0, 0, 0.6 * t)), "target": jet_at("S05a", t) - Vector((0, 0, 3)),
                            "lens": 40}, 40, step=2)

    shot("S05b", lambda t: {"pos": lerp(I + Vector((2.8, -1.5, -1.0)), I + Vector((3.3, -1.7, -1.1)), ease(t)),
                            "target": drum + Vector((0, 0, -0.2)), "lens": 30}, 30)

    # from the back of the middle ear, over the crowding amber air toward the eardrum
    shot("S06a", lambda t: {"pos": lerp(I + Vector((4.0, -1.0, -0.6)), I + Vector((3.2, -0.8, -0.5)), ease(t)),
                            "target": drum + Vector((0, 0, -0.1)), "lens": 24, "roll": 3 * ease(t)}, 24)

    def profile(sid, d0=12.5, d1=10.8, lens=50):
        """Profile cutaway on the x-ray map: the eardrum edge-on against its resting line."""
        return shot(sid, lambda t: {"pos": M + Vector((-1.0, -lerp(d0, d1, ease(t)), 0.05)),
                                    "target": M + Vector((-1.0, 0, 0.0)), "lens": lens}, lens)
    profile("S06b")

    face_cu("S07", shake=0.2)

    shot("S08a", lambda t: {"pos": lerp(I + Vector((3.4, -1.2, 0.9)), I + Vector((2.8, 0.3, -0.7)), ease(t)),
                            "target": lerp(I + Vector((0.8, 0, -0.8)), I + Vector((2.55, 0.15, -3.0)), ease(t)),
                            "lens": 24}, 24)

    shot("S08b", lambda t: {"pos": lerp(I + Vector((2.75, 0.3, -1.0)), I + Vector((2.62, 0.2, -1.7)), ease(t)),
                            "target": I + Vector((2.55, 0.15, -3.2)), "lens": 28}, 28)

    f0, f1 = rng("S09a")
    whip_up = 1 - 6 / (f1 - f0)

    def s09a(t):  # ride down the Eustachian tube with the escaping air, whip up at the end
        u = lerp(0.0, 0.7, ease(t))
        tgt = tube_point(min(1.0, u + 0.15), I)
        if t > whip_up:
            tgt = tgt + Vector((0, 0, 40 * ((t - whip_up) / (1 - whip_up)) ** 2))
        return {"pos": tube_point(u, I), "target": tgt, "lens": 18}
    shot("S09a", s09a, 18, step=1)

    # face the eardrum from inside: POP!, held until the snap and the ring have finished
    cam9 = shot("S09b", lambda t: {"pos": lerp(I + Vector((2.9, -1.6, -1.1)), I + Vector((2.2, -1.25, -0.85)), ease(t)),
                                   "target": drum, "lens": 28}, 28, step=1)
    impulse_shake(cam9, beat("S09b", "pop"), frames=8, amp=0.03)

    face_cu("S09c", near=-0.9, far=-0.97)                # his relief

    def s10(t):  # drone tracking behind the descending jet
        j = jet_at("S10", t)
        return {"pos": j + lerp(Vector((16, -24, 12)), Vector((13, -21, 9)), ease(t)), "target": j, "lens": 35}
    shot("S10", s10, 35, step=1)

    def s11a(t):  # arc inside the middle ear: outside air back, tube pinched red below
        k = ease(t)
        pos = bezier(I + Vector((3.4, -1.2, -0.6)), I + Vector((3.8, -0.6, -0.8)), I + Vector((3.9, 0.1, -0.75)),
                     I + Vector((3.6, 0.6, -0.55)), k)
        # "rises": on the eardrum (outside air thickening beyond it); then tilt down to the shut, red valve
        tilt = ease(min(1.0, max(0.0, (t - 0.4) / 0.35)))
        tgt = lerp(I + Vector((0.6, 0, -0.9)), valve_at, tilt)
        return {"pos": pos, "target": tgt, "lens": 22, "roll": -5 * k * (1 - tilt)}
    valve_ob = bpy.data.objects.get("tube_valve_in")
    valve_at = valve_ob.matrix_world.translation.copy() if valve_ob else I + Vector((2.5, 0.15, -3.0))
    shot("S11a", s11a, 22)

    profile("S11b")

    face_cu("S12a", lens=70, near=-1.0, far=-1.15, aim=Vector((0, 0, -0.03)))   # swallow, yawn, chew

    # the fix, on the map: tube opens, blue air rises into the middle ear, the eardrum returns
    shot("S12b", lambda t: {"pos": M + Vector((1.0, -lerp(19.0, 17.0, ease(t)), -2.2)),
                            "target": M + Vector((1.0, 0, -2.2)), "lens": 40}, 40)

    shot("S13", lambda t: {"pos": lerp(cab(0.05, -1.55, 1.62), cab(0.05, -1.15, 1.63), ease(t)),
                           "target": head() + (Vector((-0.04, 0, -0.07)) if m.get("real") else Vector((0, 0, -0.04))),
                           "lens": 70 if m.get("real") else 85}, 85)  # real Max: keep his raised thumb in frame

    for sid, cam in cams.items():  # timeline markers bound to cameras -> camera cuts in FILM
        mk = sc.timeline_markers.new(sid, frame=SHOT[sid]["start"])
        mk.camera = cam
    sc.camera = cams["S01"]
    return cams


# ------------------------------------------------------------------- edit ---
def add_sound(seq, name, path, channel, frame, volume=1.0):
    """Sound strip, packed into the .blend. A missing file (the voice take is kept out of git, so a
    fresh clone has none) is skipped with a warning: review builds don't need audio."""
    if not Path(path).exists():
        print(f"[build] WARNING: {Path(path).name} not found, no '{name}' audio in this build")
        return None
    st = strips(seq).new_sound(name, str(path), channel, frame)
    st.sound.pack()
    st.volume = volume
    return st


def strips(seq):
    return seq.strips if hasattr(seq, "strips") else seq.sequences


def effect(ss, name, kind, channel, start, end, a=None, b=None):
    """new_effect across Blender versions: inputs were seq1/seq2 before 4.4 and input1/input2 after;
    5.x takes a length instead of frame_end."""
    names = [p.identifier for p in ss.bl_rna.functions["new_effect"].parameters]
    kw = {}
    if a is not None:
        k1, k2 = ("input1", "input2") if "input1" in names else ("seq1", "seq2")
        kw = {k1: a, k2: b}
    if "length" in names:
        kw["length"] = end - start
    else:
        kw["frame_end"] = end
    return ss.new_effect(name, kind, channel, frame_start=start, **kw)


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
    for i, c in enumerate(PLAN["captions"]):   # Shorts style: short bold chunks, keyword in yellow, above the UI
        t = effect(ss, f"cap_{i + 1:02d}", "TEXT", 6, c["start"], c["end"] + 1)
        style_text(t, c["text"], 92, (0.5, 0.37), (1.0, 0.86, 0.1, 1) if c["hot"] else (1, 1, 1, 1))
    for i, (text, f0, f1, y) in enumerate(overlays(film, cams)):
        t = effect(ss, f"card_{i + 1:02d}", "TEXT", 7 + i % 2, f0, f1)
        label = isinstance(y, tuple)                     # a map label at (x, y), or a centred card at height y
        style_text(t, text, 54 if label else 64, y if label else (0.5, y),
                   (0.75, 0.93, 1.0, 1) if label else (1, 1, 1, 1))
    add_sound(seq, "voice", HERE / PLAN["voice"], 8, 1)
    for i, s in enumerate(PLAN["sfx"]):
        add_sound(seq, f"sfx_{s['cue']}", HERE / s["file"], 9 + i % 2, s["frame"], volume=0.35)
    for b in (b for sh in PLAN["shots"] for b in sh["beats"] if b.get("word")):
        ed.timeline_markers.new(b["word"], frame=b["frame"])
    return ed


def style_text(t, text, size, loc, color):
    t.text, t.font_size, t.wrap_width = text, size, 0.9
    t.location, t.anchor_x, t.anchor_y = loc, "CENTER", "CENTER"
    t.color = color
    for attr, val in (("use_bold", True), ("use_outline", True), ("outline_color", (0, 0, 0, 1)),
                      ("outline_width", 0.12), ("use_shadow", True), ("use_box", False)):
        if hasattr(t, attr):
            setattr(t, attr, val)


def overlays(film, cams):
    """(text, first frame, last frame, y or (x, y)) for the badges, the map's labels and the follow card.
    The labels sit on the parts they name: projected through the S04m camera."""
    from bpy_extras.object_utils import world_to_camera_view
    M = EAR_MAP
    out = []
    f0, f1 = rng("S04m")
    film.frame_set((f0 + f1) // 2)
    for text, p in (("CANAL", M + Vector((-2.8, 0, 1.9))), ("EARDRUM", M + Vector((-0.8, 0, 2.3))),
                    ("MIDDLE EAR", M + Vector((2.2, 0, 3.1))), ("TUBE", tube_point(0.45, M) + Vector((1.1, 0, 0)))):
        v = world_to_camera_view(film, cams["S04m"], p)
        if 0.05 < v.x < 0.95 and 0.05 < v.y < 0.95:   # kept inside the safe area (edges, Shorts UI at the bottom)
            out.append((text, f0, f1, (round(min(max(v.x, 0.15), 0.85), 3), round(min(max(v.y, 0.2), 0.82), 3))))
        else:
            print(f"[build] WARNING: map label {text} is off-screen ({v.x:.2f}, {v.y:.2f}); not shown")
    badge = 0.92
    out += [("OUTSIDE = INSIDE", f0 + 4, f1, badge),
            ("INSIDE > OUTSIDE", beat("S06b", "bulges"), rng("S06b")[1], badge),
            ("OUTSIDE > INSIDE", beat("S11b", "inward"), rng("S11b")[1], badge),
            ("OUTSIDE = INSIDE", beat("S12b", "open"), rng("S12b")[1], badge),
            ("Follow for more weird body facts", rng("S13")[0] + 8, rng("S13")[1] + 1, 0.27)]
    film.frame_set(1)
    return out


def film_sound(film):
    seq = film.sequence_editor_create()
    add_sound(seq, "voice", HERE / PLAN["voice"], 1, 1)
    for i, s in enumerate(PLAN["sfx"]):
        add_sound(seq, f"sfx_{s['cue']}", HERE / s["file"], 2 + i % 2, s["frame"], volume=0.35)


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


def eye_lights(film, cams, shots):
    """Animator's eye light: a small soft light riding with the close-up camera, on only during that
    shot, so Max's eyes get a catchlight and read alive."""
    for sid in shots:
        cam = cams[sid]
        ld = bpy.data.lights.new(f"eye_light_{sid}", "AREA")
        ld.size, ld.color = 0.12, (1.0, 0.96, 0.9)
        lt = bpy.data.objects.new(f"eye_light_{sid}", ld)
        film.collection.objects.link(lt)
        lt.parent = cam
        lt.location = (0.0, 0.06, 0.0)            # just above the lens, pointing where the camera points
        lt.visible_camera = False
        f0, f1 = rng(sid)
        for f, e in ((1, 0.0), (f0 - 1, 0.0), (f0, 2.5), (f1, 2.5), (f1 + 1, 0.0)):
            key(ld, "energy", f, e, interp="CONSTANT")


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    film = setup_film()
    greybox_sets = "--greybox-sets" in args
    if greybox_sets:
        sky = build_sky(film)
    else:
        assemble.realistic_sets(film)
        sky = {"jet": bpy.data.objects["Jet"]}
    if "--standin" in args or not real_max.MAX_BLEND.exists():
        m = build_cabin(film) if greybox_sets else greybox_max(film, CABIN + Vector((0.0, 0.35, 0.0)))
    else:
        m = real_max.load(film, CABIN)
        if greybox_sets:
            build_cabin(film, with_max=False, window_z=1.75 + m["offset"].z)
    if greybox_sets:
        e, e_map = build_ear(film, EAR, inside=True), build_ear(film, EAR_MAP, inside=False)
        build_city(film)
    else:
        e, e_map = assemble.ear_dict("in", EAR), assemble.ear_dict("map", EAR_MAP)
        city_real.light_switch(*rng("S10"))
    animate_jet(sky["jet"])
    if m.get("real"):
        real_max.perform(m, beat, rng, film)
    else:
        animate_max(m)
    animate_ear(e)
    animate_ear(e_map)
    rest_line(e_map)
    cams = build_cameras(film, m)
    declutter(cams, (e, e_map))
    if m.get("real"):
        eye_lights(film, cams, ("S00", "S07", "S09c", "S12a", "S13"))
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
