"""Build the pilot's grey-box previz .blend (run inside Blender):

  blender -b --factory-startup -P shorts/pilot_ear_pop/build_previz.py -- [--stills DIR]

Reads plan.json (prep_plan.py) and writes out/pilot_ear_pop/pilot_ear_pop_previz.blend with:
  FILM  every set, the 14 shot cameras (bound to timeline markers, so playing it in camera
        view cuts between shots), all animation keyed to spoken words, plus the voice and SFX.
  EDIT  the cut: one strip per shot (FILM through that shot's camera), the dissolve,
        captions, voice and SFX. Play it to watch the whole film end to end.
--stills renders one low-res Cycles frame from the middle of every shot for review.
"""
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "blender"))
from greybox import CABIN, EAR, SKY, build_cabin, build_city, build_ear, build_sky, tube_point  # noqa: E402
from rigs import bake_move, bezier, camera, collection, ease, handheld, impulse_shake, key, lerp  # noqa: E402

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
    key(hand_l, "location", 300, lap_l)
    head_rot(300)
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
    fs, fy, fc, fo = (beat("S12", w) for w in ("swallowing", "yawning", "chewing", "open"))
    head_rot(fs - 2)
    head_rot(fs + 6, pitch=8)
    head_rot(fs + 14)
    mouth_shape(fy - 2)
    head_rot(fy - 2)
    head_rot(fy + 10, pitch=-16)
    mouth_shape(fy + 10, w=1.3, h=4.0)
    mouth_shape(fy + 24, w=1.3, h=4.0)
    head_rot(fy + 26)
    mouth_shape(fy + 30)
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
    flow_end = rng("S09")[1]
    for i, mol in enumerate(e["flow"]):
        key(mol, "scale", fk + 2 + i, (0.0,) * 3, interp="CONSTANT")
        key(mol, "scale", fk + 3 + i, (0.11,) * 3, interp="CONSTANT")
        key(mol, "scale", flow_end, (0.0,) * 3, interp="CONSTANT")
        for f in range(fk + 3 + i, flow_end, 3):
            key(mol, "location", f, tube_point(((f - fk) / 45.0 + i / 14) % 1.0), interp="LINEAR")
    # air escapes: inside air thins between "escapes" and "evens"
    fe, fv = beat("S09", "escapes"), beat("S09", "evens")
    for i, mol in enumerate(e["inside"]):
        if i % 5 < 2:
            key(mol, "scale", fe + i % 30, (0.11,) * 3)
            key(mol, "scale", fv + i % 10, (0.0,) * 3)
    # POP: eardrum snaps flat with an overshoot, flash and light ring
    fpop = beat("S09", "pop")
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
    ear = CABIN + Vector((0.13, 0.33, 1.66))
    window = CABIN + Vector((1.79, -0.25, 1.75))
    cams = {}

    def shot(sid, move, lens0, step=3):
        cam = camera(f"CAM_{sid}", coll, lens=lens0)
        f0, f1 = rng(sid)
        bake_move(cam, f0, f1, move, step=step)
        cams[sid] = cam
        return cam

    def s01(t):  # drone reveal: from under the wing, pulling back and rising as the jet climbs
        j = jet_at("S01", t)
        k = ease(t)
        return {"pos": j + lerp(Vector((-1.5, -5.5, -2.4)), Vector((-8, -30, 4)), k), "target": j, "lens": 24}
    shot("S01", s01, 24, step=2)

    def s02(t):  # dolly in to Max's ear, rack focus window -> ear
        k = ease(t)
        pos = lerp(CABIN + Vector((0.3, -2.7, 1.55)), CABIN + Vector((0.85, -0.45, 1.7)), k)
        tgt = lerp(CABIN + Vector((0.05, 0.35, 1.45)), ear, k)
        focus = lerp((window - pos).length, (ear - pos).length, ease(min(1, t / 0.4)))
        return {"pos": pos, "target": tgt, "lens": lerp(50, 85, k), "focus": focus}
    shot("S02", s02, 50)

    def s03(t):  # fly-through: down the canal, then arc out to the side cutaway
        if t < 0.55:
            k = ease(t / 0.55)
            x = lerp(-15.0, -3.4, k)
            return {"pos": EAR + Vector((x, 0.3, 0.2)), "target": EAR + Vector((x + 6, 0.3, 0.0)), "lens": 18}
        k = ease((t - 0.55) / 0.45)
        pos = bezier(EAR + Vector((-3.4, 0.3, 0.2)), EAR + Vector((-4.0, -4, 0.6)), EAR + Vector((-1, -12, 0.8)),
                     EAR + Vector((0.6, -16, 0.2)), k)
        return {"pos": pos, "target": lerp(EAR + Vector((2.6, 0.3, 0.0)), EAR + Vector((0.6, 0, -0.6)), k),
                "lens": lerp(18, 40, k)}
    shot("S03", s03, 18, step=2)

    shot("S04", lambda t: {"pos": EAR + Vector((-1.4 + 0.08 * t, -21, -0.4 + 0.05 * math.sin(t * 3))),
                           "target": EAR + Vector((-1.4, 0, -0.5)), "lens": 50}, 50)

    def s05a(t):  # drone flyover high above the cloud deck
        j = jet_at("S05a", t)
        return {"pos": j + lerp(Vector((-30, -75, 38)), Vector((-18, -82, 44)), ease(t)), "target": j, "lens": 35}
    shot("S05a", s05a, 35, step=2)

    shot("S05b", lambda t: {"pos": lerp(EAR + Vector((-1.4, -18, -0.4)), EAR + Vector((-1.4, -23, -0.6)), ease(t)),
                            "target": EAR + Vector((-1.4, 0, -0.5)), "lens": 50}, 50)

    shot("S06", lambda t: {"pos": lerp(EAR + Vector((-2.6, -15, -3.2)), EAR + Vector((-1.6, -10.5, -1.8)), ease(t)),
                           "target": EAR + Vector((-0.9, 0, 0.0)), "lens": 100, "roll": 5 * ease(t)}, 100)

    cam7 = shot("S07", lambda t: {"pos": lerp(CABIN + Vector((0.12, -1.0, 1.66)), CABIN + Vector((0.12, -0.92, 1.66)), t),
                                  "target": head(), "lens": 85}, 85)
    handheld(cam7, *rng("S07"), strength=0.2)

    shot("S08", lambda t: {"pos": lerp(EAR + Vector((2.0, -24, 0.5)), EAR + Vector((-0.5, -24, -8.5)), ease(t)),
                           "target": lerp(EAR + Vector((2.0, 0, -0.5)), EAR + Vector((-1.2, 0, -9.5)), ease(t)),
                           "lens": 40}, 40)

    f0, f1 = rng("S09")
    whip_t = 1 - 7 / (f1 - f0)

    def s09(t):  # push in, then whip-pan right into S10
        pos = lerp(EAR + Vector((-1.4, -22, -1.0)), EAR + Vector((-1.2, -16, -0.6)), ease(t))
        tgt = EAR + Vector((-1.2, 0, -0.6))
        if t > whip_t:
            tgt = tgt + Vector((70 * ((t - whip_t) / (1 - whip_t)) ** 2, 0, 0))
        return {"pos": pos, "target": tgt, "lens": 65}
    cam9 = shot("S09", s09, 65, step=1)
    impulse_shake(cam9, beat("S09", "pop"), frames=10, amp=0.25)

    f0, f1 = rng("S10")
    whip_in = 6 / (f1 - f0)

    def s10(t):  # drone tracking behind the descending jet (whip lands from the left)
        j = jet_at("S10", t)
        tgt = j + (Vector((-60 * (1 - t / whip_in) ** 2, 0, 0)) if t < whip_in else Vector())
        return {"pos": j + lerp(Vector((16, -24, 12)), Vector((13, -21, 9)), ease(t)), "target": tgt, "lens": 35}
    shot("S10", s10, 35, step=1)

    def s11(t):  # slow high-angle orbit, creeping opposite tilt
        a = math.radians(lerp(-90, -110, ease(t)))
        c = EAR + Vector((-1.0, 0, -1.8))
        return {"pos": c + Vector((24 * math.cos(a), 24 * math.sin(a), 6)), "target": c, "lens": 70, "roll": -5 * ease(t)}
    shot("S11", s11, 85)

    def s12(t):  # gentle arc around Max
        a = math.radians(lerp(-90, -75, ease(t)))
        c = CABIN + Vector((0, 0.35, 1.45))
        return {"pos": c + Vector((2.4 * math.cos(a), 2.4 * math.sin(a), 0.1)), "target": c + Vector((0, 0, 0.05)), "lens": 50}
    shot("S12", s12, 50)

    shot("S13", lambda t: {"pos": lerp(CABIN + Vector((0.05, -1.55, 1.62)), CABIN + Vector((0.05, -1.15, 1.63)), ease(t)),
                           "target": head() + Vector((0, 0, -0.04)), "lens": 85}, 85)

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


def viewports():
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
    for sh in PLAN["shots"]:
        film.camera = cams[sh["id"]]
        film.frame_set((sh["start"] + sh["end"]) // 2)
        film.render.filepath = str(out_dir / f"{sh['id']}.png")
        bpy.ops.render.render(write_still=True, scene=film.name)
    film.render.resolution_percentage = 100
    film.render.use_sequencer = True
    film.camera = cams["S01"]
    film.frame_set(1)


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    film = setup_film()
    sky = build_sky(film)
    m = build_cabin(film)
    e = build_ear(film)
    build_city(film)
    animate_jet(sky["jet"])
    animate_max(m)
    animate_ear(e)
    cams = build_cameras(film, m)
    film_sound(film)
    build_edit(film, cams)
    viewports()
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
