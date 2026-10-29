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
from mathutils import Euler, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
from max_expressions import EXPRESSIONS, FACE_UNITS, HEAD_POSE, SHEET_ORDER  # noqa: E402

OUTFIT_TEX = os.path.join(ROOT, "assets/characters/max/textures/max_outfit_diffuse.png")
HAIR_COLOR = (0.035, 0.022, 0.014)      # dark brown (linear)
SKIN_WARM = (0.93, 0.78, 0.66)          # light-medium warm tone over the pale CC0 skin
EYE_TEX = "brown_eye.png"

# Phenotype: a man in his late twenties, slim-athletic, light-medium skin (reference sheet).
PHENOTYPE = {
    "gender": 1.0, "age": 0.52, "muscle": 0.58, "weight": 0.45, "proportions": 0.7,
    "height": 0.55, "cupsize": 0.5, "firmness": 0.5,
    "race": {"caucasian": 0.7, "asian": 0.15, "african": 0.15},
}
# Stylized-realistic push (Zack D-like): bigger, rounder eyes, softer jaw, slightly bigger head.
STYLE_TARGETS = {
    "l-eye-scale-incr": 0.85, "r-eye-scale-incr": 0.85,
    "l-eye-height2-incr": 0.4, "r-eye-height2-incr": 0.4,
    "head-scale-vert-incr": 0.15, "head-scale-horiz-incr": 0.1,
    "chin-width-decr": 0.15, "chin-prominent-decr": 0.1,
    "nose-scale-horiz-decr": 0.1,
    "mouth-scale-horiz-incr": 0.08,
}

HUMAN = {
    "name": "Max",
    "phenotype": PHENOTYPE,
    "rig": "default",
    "eyes": "high-poly.mhclo",
    "eyebrows": "eyebrow010.mhclo",
    "eyelashes": "eyelashes01.mhclo",
    "teeth": "teeth_base.mhclo",
    "tongue": "tongue01.mhclo",
    "hair": "cortu_short_messy_hair.mhclo",
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
                _tint(mat, (0.06, 0.04, 0.03))
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
    return bare if bare in FACE_UNITS else None


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


def thumbs_up(rig, on=True, frame=None):
    """Right hand: forearm raised in front of the chest, fist closed, thumb up."""
    poses = {
        "upperarm01.R": (0, 0, 0), "lowerarm01.R": (0, 0, 0), "wrist.R": (0, 0, 0),
    }
    if on:
        poses = {
            "upperarm01.R": (-20, 0, 55),
            "lowerarm01.R": (-95, 0, 0),
            "wrist.R": (0, -80, 0),
        }
        for f in range(2, 6):
            for j in (1, 2, 3):
                poses[f"finger{f}-{j}.R"] = (75, 0, 0)
        poses["finger1-2.R"] = (0, 0, -20)
    else:
        for f in range(1, 6):
            for j in (1, 2, 3):
                poses[f"finger{f}-{j}.R"] = (0, 0, 0)
    for bone, deg in poses.items():
        pb = rig.pose.bones.get(bone)
        if not pb:
            continue
        pb.rotation_mode = "XYZ"
        pb.rotation_euler = Euler([math.radians(a) for a in deg], "XYZ")
        if frame is not None:
            pb.keyframe_insert("rotation_euler", frame=frame)


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
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.film_transparent = False
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"
    world = bpy.data.worlds.new("Studio")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.42, 0.45, 0.5, 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.6
    sc.world = world
    # Three-point studio light, warm key / cool fill, like the cabin's window light.
    for name, loc, energy, color, size in (
        ("Key", (-1.6, -2.2, 2.4), 220, (1.0, 0.9, 0.8), 1.6),
        ("Fill", (2.2, -1.6, 1.6), 70, (0.85, 0.9, 1.0), 2.5),
        ("Rim", (0.6, 2.4, 2.4), 260, (1.0, 1.0, 1.0), 1.0),
    ):
        ld = bpy.data.lights.new(name, "AREA")
        ld.energy, ld.color, ld.size = energy, color, size
        lo = bpy.data.objects.new(name, ld)
        sc.collection.objects.link(lo)
        lo.location = loc
        lo.rotation_euler = (Vector((0, 0, 1.2)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
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
        lens, dist = (85, 1.25) if name != "thumbs_up" else (50, 1.6)
        tgt = hp + Vector((0, 0, -0.02 if name != "thumbs_up" else -0.22))
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
