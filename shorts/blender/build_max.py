"""Build Max, the recurring host, from free CC0 MakeHuman assets via the MPFB2 add-on.

    blender -b --factory-startup -P shorts/blender/build_max.py -- [--out PATH] [--sheet DIR]

Needs MPFB2 (extensions.blender.org, free) plus its CC0 asset packs: makehuman_system_assets,
skins01, hair01, eyebrows01, eyelashes01 and faceunits01 (the 52 ARKit face shapes that the
expressions are keyed on). See assets/characters/max/README.md.

Result: one rigged character (collection MAX, armature "Max") with face-unit shape keys on the body,
brows and lashes, saved as a .blend that the shot scenes link. --sheet also renders a turnaround and
an expression sheet (Cycles, CPU-friendly) for approval against max_reference.png.
"""
import importlib
import math
import os
import sys

import bpy
from mathutils import Euler, Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
from max_expressions import EXPRESSIONS, EXTRA_UNITS, FACE_UNITS, HEAD_POSE, SHEET_ORDER  # noqa: E402

OUTFIT_TEX = os.path.join(ROOT, "assets/characters/max/textures/max_outfit_diffuse.png")
HAIR_COLOR = (0.035, 0.022, 0.014)      # dark brown (linear)
SKIN_WARM = (0.86, 0.68, 0.55)          # warm tanned tone over the pale CC0 skin
EYE_TEX = "brown_eye.png"

# Phenotype: a man in his late twenties, slim-athletic, light-medium skin (reference sheet).
PHENOTYPE = {
    "gender": 1.0, "age": 0.58, "muscle": 0.6, "weight": 0.52, "proportions": 0.7,
    "height": 0.55, "cupsize": 0.5, "firmness": 0.5,
    "race": {"caucasian": 0.6, "asian": 0.2, "african": 0.2},
}
# Stylized-realistic push (Zack D-like): bigger, rounder eyes, a defined jaw, slightly bigger head.
STYLE_TARGETS = {
    "l-eye-scale-incr": 0.85, "r-eye-scale-incr": 0.85,
    "l-eye-height2-incr": 0.4, "r-eye-height2-incr": 0.4,
    "head-scale-vert-incr": 0.15, "head-scale-horiz-incr": 0.1,
    "chin-width-incr": 0.15, "chin-prominent-incr": 0.1,
    "nose-scale-horiz-decr": 0.1,
    "mouth-scale-horiz-incr": 0.08,
}

HUMAN = {
    "name": "Max",
    "phenotype": PHENOTYPE,
    "rig": "default",
    "eyes": "high-poly.mhclo",
    "eyebrows": "eyebrow009.mhclo",
    "eyelashes": "eyelashes01.mhclo",
    "teeth": "teeth_base.mhclo",
    "tongue": "tongue01.mhclo",
    "hair": "",                         # groomed particle hair instead (max_hair.py),
    "proxy": "",
    "targets": [{"target": k, "value": v} for k, v in STYLE_TARGETS.items()],
    "clothes": ["male_casualsuit06.mhclo", "shoes05.mhclo"],
    "skin_mhmat": "young_caucasian_male.mhmat",
    "skin_material_type": "ENHANCED_SSS",
    "eyes_material_type": "MAKESKIN",
    "skin_material_settings": {},
    "eyes_material_settings": {},
    "expressions": [],
}


def mpfb():
    for name in ("bl_ext.user_default.mpfb", "bl_ext.blender_org.mpfb", "mpfb"):
        try:
            importlib.import_module(name)
            return name
        except ImportError:
            continue
    raise SystemExit("MPFB2 is not installed (Edit > Preferences > Get Extensions > MPFB)")


def build():
    pkg = mpfb()
    HumanService = importlib.import_module(pkg + ".services.humanservice").HumanService
    FaceService = importlib.import_module(pkg + ".services.faceservice").FaceService

    settings = HumanService.get_default_deserialization_settings()
    settings["subdiv_levels"] = 1
    body = HumanService.deserialize_from_dict(dict(HUMAN), settings)

    if not FaceService.is_faceunits01_installed(force_recheck=True):
        raise SystemExit("faceunits01 asset pack missing: Max's expressions need it")
    FaceService.load_targets(body, load_microsoft_visemes=False, load_arkit_faceunits=True)
    FaceService.interpolate_targets(body)  # brows, lashes and stubble follow the face shapes

    rig = body.parent
    coll = bpy.data.collections.new("MAX")
    bpy.context.scene.collection.children.link(coll)
    for ob in [rig] + list(rig.children_recursive):
        for c in list(ob.users_collection):
            c.objects.unlink(ob)
        coll.objects.link(ob)
    rig.name = "Max"
    body.name = "Max.body"
    restyle(rig)
    link_face_drivers(rig, body)
    import max_hair
    max_hair.groom(rig, body)
    import max_look
    max_look.upgrade(rig)          # v4/v5: skin zones, eyes, teeth, render subdivision
    import max_hair_curves
    max_hair_curves.to_curves(rig, body)   # v5: real hair curves (~150k strands) from the combed guides
    return rig, body


def link_face_drivers(rig, body):
    """Brows, lashes, hair, teeth and tongue follow the body's face sliders, so one key moves the whole face."""
    src = body.data.shape_keys
    for ob in rig.children_recursive:
        if ob is body or ob.type != "MESH" or not ob.data.shape_keys:
            continue
        for kb in ob.data.shape_keys.key_blocks:
            unit = _unit(kb.name)
            if not unit or unit not in src.key_blocks:
                continue
            drv = kb.driver_add("value").driver
            drv.type = "AVERAGE"
            var = drv.variables.new()
            var.targets[0].id_type = "KEY"
            var.targets[0].id = src
            var.targets[0].data_path = f'key_blocks["{unit}"].value'


def _images(mat):
    return [n for n in mat.node_tree.nodes if n.type == "TEX_IMAGE"] if mat and mat.use_nodes else []


def _tint(mat, color, all_images=False):
    """Multiply a material's diffuse texture by a colour (keeps its detail, changes its tone)."""
    nt = mat.node_tree
    for n in _images(mat):
        nm = (n.image.name if n.image else "").lower()
        if not n.image or "normal" in nm or "objnorm" in nm or "_ao" in nm:
            continue
        if not all_images and "diff" not in nm and not nm.startswith("eyebrow"):
            continue
        for link in list(n.outputs["Color"].links):
            mix = nt.nodes.new("ShaderNodeMix")
            mix.data_type, mix.blend_type = "RGBA", "MULTIPLY"
            mix.inputs[0].default_value = 1.0
            mix.inputs[7].default_value = (*color, 1)
            nt.links.new(mix.outputs[2], link.to_socket)
            nt.links.new(n.outputs["Color"], mix.inputs[6])
    if mat.node_tree and not _images(mat):
        for g in [n for n in nt.nodes if n.type == "GROUP"]:
            for nn in g.node_tree.nodes if g.node_tree else []:
                if nn.type == "TEX_IMAGE" and nn.image and "diffuse" in nn.image.name.lower():
                    for link in list(nn.outputs["Color"].links):
                        mix = g.node_tree.nodes.new("ShaderNodeMix")
                        mix.data_type, mix.blend_type = "RGBA", "MULTIPLY"
                        mix.inputs[0].default_value = 1.0
                        mix.inputs[7].default_value = (*color, 1)
                        g.node_tree.links.new(mix.outputs[2], link.to_socket)
                        g.node_tree.links.new(nn.outputs["Color"], mix.inputs[6])


def restyle(rig):
    """Recolour the CC0 assets to the reference: teal tee, dark jeans, dark-brown hair, brown eyes."""
    outfit = bpy.data.images.load(OUTFIT_TEX, check_existing=True)
    eye_img = None
    for ob in rig.children_recursive:
        if ob.type != "MESH":
            continue
        name = ob.name.lower()
        for mat in ob.data.materials:
            if not mat:
                continue
            if "casualsuit06" in name:
                for n in _images(mat):
                    if "diffuse" in (n.image.name if n.image else "").lower():
                        n.image = outfit
            elif "messy" in name or "short02" in name or "hair" in name:
                _tint(mat, [c * 6 for c in HAIR_COLOR])
            elif "eyebrow" in name:
                _tint(mat, (0.03, 0.02, 0.015))
            elif name.endswith(".body"):
                _tint(mat, SKIN_WARM, all_images=True)
            elif "high-poly" in name or name.endswith("eyes"):
                for n in _images(mat):
                    if n.image and "eye" in n.image.name.lower() and "normal" not in n.image.name.lower():
                        if eye_img is None:
                            path = os.path.join(os.path.dirname(n.image.filepath_from_user()), EYE_TEX)
                            if os.path.exists(path):
                                eye_img = bpy.data.images.load(path, check_existing=True)
                        if eye_img:
                            n.image = eye_img


# ------------------------------------------------------------------ faces --
def _unit(name):
    """ARKit face-unit name of a shape key (MPFB names them bare, or "!ex-" on older versions)."""
    bare = name.split("ex-", 1)[1] if name.startswith(("!ex-", "ex-")) else name
    return bare if bare in FACE_UNITS or bare in EXTRA_UNITS else None


def face_meshes(rig):
    return [ob for ob in rig.children_recursive if ob.type == "MESH" and ob.data.shape_keys
            and any(_unit(k.name) for k in ob.data.shape_keys.key_blocks)]


def set_expression(rig, name, frame=None, weight=1.0):
    """Set (and optionally keyframe) one named expression on the body's face sliders, zeroing the rest."""
    units = EXPRESSIONS[name]
    body = next(ob for ob in rig.children if ob.name.endswith(".body"))
    for kb in body.data.shape_keys.key_blocks:
        unit = _unit(kb.name)
        if unit:
            kb.value = units.get(unit, 0.0) * weight
            if frame is not None:
                kb.keyframe_insert("value", frame=frame)
    pose_head(rig, HEAD_POSE.get(name, (0, 0, 0)), frame, weight)


def chew_keys(start, chews=3, period=12):
    """24 fps: three chews over 36 frames; opening peaks +3,+15,+27."""
    if chews < 1 or period < 8:
        raise ValueError("Chewing needs >=1 chew and >=8 frames/chew")
    yield start - 3, "neutral"
    for i in range(chews):
        t = start + i * period
        suffix = "_r" if i % 2 else ""
        yield t, "chew_b" + suffix
        yield t + round(period * 0.25), "chew" + suffix
        yield t + round(period * 0.58), "chew_b" + suffix
    yield start + chews * period, "neutral"


def ease_chew(rig, first, last):
    from rigs import fcurves
    body = next(o for o in rig.children if o.name.endswith(".body"))
    face_paths = {k.path_from_id("value")
                  for k in body.data.shape_keys.key_blocks if _unit(k.name)}
    head_paths = {
        rig.pose.bones[n].path_from_id("rotation_euler")
        for n in ("neck01", "neck02", "head") if n in rig.pose.bones
    }
    for owner, paths in ((body.data.shape_keys, face_paths),
                         (rig, head_paths)):
        for curve in fcurves(owner):
            if curve.data_path not in paths:
                continue
            for point in curve.keyframe_points:
                if first <= point.co.x <= last:
                    point.interpolation = "BEZIER"
                    point.handle_left_type = "AUTO_CLAMPED"
                    point.handle_right_type = "AUTO_CLAMPED"


def chew_cycle(rig, start, chews=3, period=12):
    """v6c (Codex 012): key `chews` chews (alternating sides) with eased curves."""
    for frame, name in chew_keys(start, chews, period):
        set_expression(rig, name, frame=frame)
    ease_chew(rig, start - 3, start + chews * period)


def swallow_motion(rig, start):
    """Key one swallow: lips seal and the larynx rises (frames start+4..+8), then everything settles back."""
    set_expression(rig, "neutral", start)
    set_expression(rig, "swallow", start + 5)
    set_expression(rig, "swallow", start + 8)
    set_expression(rig, "neutral", start + 15)


def pose_head(rig, deg, frame=None, weight=1.0):
    """Spread a head rotation over neck and head bones so it reads as natural, not a hinge."""
    share = {"neck01": 0.25, "neck02": 0.25, "head": 0.5}
    for bone, part in share.items():
        pb = rig.pose.bones.get(bone)
        if not pb:
            continue
        pb.rotation_mode = "XYZ"
        pb.rotation_euler = Euler([math.radians(a * part * weight) for a in deg], "XYZ")
        if frame is not None:
            pb.keyframe_insert("rotation_euler", frame=frame)


SHOULDER_RISE = 0.33       # collarbone lift per degree of arm elevation past SHOULDER_RISE_FROM (the ~1:2
SHOULDER_RISE_FROM = 35    # scapulohumeral rhythm), capped at SHOULDER_RISE_MAX degrees
SHOULDER_RISE_MAX = 32


def lift_shoulder(rig, side, direction):
    """v6e: raise the collarbone with the arm, as a real shoulder does. Rotating only the upper arm
    collapsed the top of the shoulder into a flat, "trimmed" line when the arm went up. (v6g: this alone
    fixes it; volume-preserving skinning was tried and removed: it ballooned the shoulders overhead.)"""
    clav = rig.pose.bones.get(f"clavicle.{side}")
    if not clav:
        return
    clav.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()
    d = (rig.matrix_world.to_3x3().inverted() @ Vector(direction)).normalized()
    elevation = math.degrees(d.angle(Vector((0, 0, -1))))
    rise = min(SHOULDER_RISE_MAX, SHOULDER_RISE * max(0.0, elevation - SHOULDER_RISE_FROM))
    if rise <= 0:
        return
    rest = clav.matrix.to_3x3().col[1].normalized()
    axis = rest.cross(Vector((0, 0, 1)))
    if axis.length < 1e-6:
        return
    lifted = Matrix.Rotation(math.radians(rise), 3, axis.normalized()) @ rest
    aim_bone(rig, clav.name, rig.matrix_world.to_3x3() @ lifted)


def aim_bone(rig, name, direction, up=None, up_child=None):
    """Point a pose bone along a world direction (rig-axis independent). Optionally roll it so the
    vector from its head to bone `up_child`'s head points as close to `up` as possible.
    Aiming an upper arm also lifts its collarbone (lift_shoulder)."""
    pb = rig.pose.bones.get(name)
    if not pb:
        return
    if name.startswith("upperarm01."):
        lift_shoulder(rig, name.split(".")[-1], direction)
    bpy.context.view_layer.update()
    inv = rig.matrix_world.to_3x3().inverted()
    d = (inv @ Vector(direction)).normalized()
    m = pb.matrix.copy()
    q = m.to_3x3().col[1].normalized().rotation_difference(d)
    rot = q.to_matrix() @ m.to_3x3()
    if up is not None and up_child and rig.pose.bones.get(up_child):
        c = rig.pose.bones[up_child]
        side = (q.to_matrix() @ (c.head - pb.head))
        y = d
        a = (side - y * side.dot(y))
        u = inv @ Vector(up)
        u = (u - y * u.dot(y))
        if a.length > 1e-6 and u.length > 1e-6:
            rot = a.normalized().rotation_difference(u.normalized()).to_matrix() @ rot
    new = rot.to_4x4()
    new.translation = m.translation
    pb.matrix = new
    bpy.context.view_layer.update()


def _key_bones(rig, names, frame):
    if frame is None:
        return
    for n in names:
        pb = rig.pose.bones.get(n)
        if pb:
            pb.keyframe_insert("rotation_quaternion" if pb.rotation_mode == "QUATERNION" else "rotation_euler", frame=frame)


THUMB_BONES = ["upperarm01.R", "upperarm02.R", "lowerarm01.R", "lowerarm02.R", "wrist.R",
               "upperarm01.L", "upperarm02.L", "lowerarm01.L", "lowerarm02.L"] + \
    [f"finger{f}-{j}.R" for f in range(1, 6) for j in (1, 2, 3)] + [f"metacarpal{i}.R" for i in range(1, 5)]


def thumbs_up(rig, on=True, frame=None, raised=False):
    """Right hand: fist closed, thumb straight up (world-aimed). raised=True lifts the fist to chin
    height (for a close-up to camera); otherwise the elbow stays at his side, forearm forward."""
    for n in THUMB_BONES:
        pb = rig.pose.bones.get(n)
        if pb:
            pb.rotation_mode = "QUATERNION"
            pb.rotation_quaternion = (1, 0, 0, 0)
    if on:
        # He faces -Y; his right side is -X.
        for n, d in (("upperarm01.L", (0.12, 0.02, -1)), ("upperarm02.L", (0.12, 0.02, -1)),
                     ("lowerarm01.L", (0.05, -0.15, -1)), ("lowerarm02.L", (0.05, -0.15, -1))):
            aim_bone(rig, n, d)  # other arm relaxed at his side
        upper, fore, hand = ((-0.08, -0.9, -0.42), (0.32, -0.3, 0.9), (0.3, -0.9, 0.35)) if raised else \
            ((-0.12, -0.3, -1), (0.3, -1, 0.35), (0.3, -1, 0.2))
        aim_bone(rig, "upperarm01.R", upper)
        aim_bone(rig, "upperarm02.R", upper)
        aim_bone(rig, "lowerarm01.R", fore)
        aim_bone(rig, "lowerarm02.R", fore)
        aim_bone(rig, "wrist.R", hand, up=(0, 0, 1), up_child="finger1-1.R")
        bpy.context.view_layer.update()
        wrist = rig.pose.bones["wrist.R"]
        fwd = (rig.matrix_world.to_3x3() @ wrist.matrix.to_3x3().col[1]).normalized()
        palm_in = Vector((1, 0, 0))  # toward his chest
        for f in range(2, 6):
            # Fist: with the thumb up the fingers stack vertically and curl sideways into the palm.
            dirs = [fwd.lerp(palm_in, 0.6), palm_in.lerp(-fwd, 0.5), -fwd]
            for j, dvec in zip((1, 2, 3), dirs):
                aim_bone(rig, f"finger{f}-{j}.R", dvec)
        for j in (1, 2, 3):
            aim_bone(rig, f"finger1-{j}.R", (0.15, -0.1, 1))
    _key_bones(rig, THUMB_BONES, frame)


# ------------------------------------------------------------------ sheet --
def head_point(rig):
    pb = rig.pose.bones.get("head")
    return rig.matrix_world @ ((pb.head + pb.tail) / 2) if pb else Vector((0, 0, 1.6))


def setup_render(res=(720, 720), samples=48):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.cycles_curves.shape = "THICK"
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.film_transparent = False
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"
    import max_look
    max_look.studio(sc)            # the house character rig (ink & amber)
    cd = bpy.data.cameras.new("SheetCam")
    cam = bpy.data.objects.new("SheetCam", cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    return cam


def aim(cam, pos, target, lens):
    cam.location = Vector(pos)
    cam.rotation_euler = (Vector(target) - Vector(pos)).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = lens


def render(path):
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("rendered", path)


def sheet(rig, outdir):
    os.makedirs(outdir, exist_ok=True)
    cam = setup_render()
    sc = bpy.context.scene
    hp = head_point(rig)
    # Turnaround: front, three-quarter, side (full body, 9:16).
    sc.render.resolution_x, sc.render.resolution_y = 540, 960
    mid = Vector((hp.x, hp.y, hp.z * 0.52))
    for name, ang in (("front", 0), ("three_quarter", 35), ("side", 90)):
        d = 4.2
        a = math.radians(ang)
        aim(cam, (mid.x + d * math.sin(a), mid.y - d * math.cos(a), mid.z + 0.1), mid, 50)
        render(os.path.join(outdir, f"turn_{name}.png"))
    # Expressions: head and shoulders.
    sc.render.resolution_x, sc.render.resolution_y = 600, 600
    for name in SHEET_ORDER:
        set_expression(rig, name)
        thumbs_up(rig, name == "thumbs_up")
        bpy.context.view_layer.update()
        hp = head_point(rig)
        lens, dist = (85, 1.25) if name != "thumbs_up" else (60, 1.3)    # thumbs-up: chest up, not full body
        tgt = hp + Vector((0, 0, -0.02 if name != "thumbs_up" else -0.26))
        aim(cam, (tgt.x + 0.25, tgt.y - dist, tgt.z + 0.05), tgt, lens)
        render(os.path.join(outdir, f"expr_{name}.png"))
    set_expression(rig, "neutral")
    thumbs_up(rig, False)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    out = os.path.join(ROOT, "out/characters/max/max_v1.blend")
    sheet_dir = None
    if "--out" in argv:
        out = os.path.abspath(argv[argv.index("--out") + 1])
    if "--sheet" in argv:
        sheet_dir = os.path.abspath(argv[argv.index("--sheet") + 1])

    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    rig, body = build()
    print("MAX", rig.name, [o.name for o in rig.children_recursive])
    print("FACE MESHES", [o.name for o in face_meshes(rig)])
    if sheet_dir:
        sheet(rig, sheet_dir)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
    print("saved", out, os.path.getsize(out) // 1024, "KB")


if __name__ == "__main__":
    main()
