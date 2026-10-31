"""Max's look upgrade (v4): skin, eyes, teeth and hair at Zack-level polish, plus the house light rig.

    upgrade(rig)      tune the MPFB materials and the hair groom on a built Max (build_max.py calls it)
    studio(scene)     the "ink & amber" character light rig: warm key, cool fill, cyan rim, ink-teal world

Also runs on an existing file, without rebuilding:

    blender -b assets/characters/max/max_v3.blend -P shorts/blender/max_look.py -- --out assets/characters/max/max_v4.blend [--sheet DIR]

Realism comes from light and materials, not polygons (shorts-craft §11): pores and patchy gloss on the skin,
a wet cornea coat on the eyes, fine clumped hair with stray tips, and a soft key with a cyan rim.
"""
import os
import sys

import bpy
from mathutils import Vector

# MPFB "ENHANCED_SSS" skin group inputs (the group exposes them; defaults in brackets)
SKIN = {
    "Pore strength": 0.38,        # [0.2] visible pores in close-ups
    "Pore scale": 2600.0,         # [2500]
    "SSS strength": 0.32,         # [0.2] softer, light-through skin (less waxy)
    "SSS radius scale": 0.12,     # [0.1]
    "colorMixIn": (0.95, 0.25, 0.22, 1.0),
    "colorMixInStrength": 0.08,   # [0.05] a little blood flush
    "Clearcoat": 0.06,            # [0.1] a faint natural sheen (more made rim lights glare on the temples)
    "Clearcoat Roughness": 0.35,
}
SKIN_ROUGH = (0.36, 0.52)         # roughness varies across the face (oilier and drier patches)

# hair groom (max_hair.py's particle systems): finer strands, more of them, natural stray ends
HAIR = {"rendered_child_count": 220, "radius_scale": 0.00034, "tip_radius": 0.3, "clump_factor": 0.45,
        "clump_shape": 0.25, "roughness_1": 0.0008, "roughness_endpoint": 0.0025, "roughness_2": 0.004,
        "roughness_2_threshold": 0.75}
HAIR_SHADER = {"Roughness": 0.32, "Radial Roughness": 0.35, "Coat": 0.12, "Random Color": 0.12,
               "Random Roughness": 0.25}


def _group_input(mat, name, value):
    for n in mat.node_tree.nodes:
        if n.type == "GROUP" and name in n.inputs:
            n.inputs[name].default_value = value
            return True
    return False


def upgrade_skin(mat):
    for k, v in SKIN.items():
        _group_input(mat, k, v)
    g = next((n for n in mat.node_tree.nodes if n.type == "GROUP"), None)
    if not g:
        return
    nt = g.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    if "max_look_rough" in nt.nodes:
        return
    # roughness from a soft noise across the face instead of one value (oilier T-zone patches)
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.name = "max_look_rough"
    noise.inputs["Scale"].default_value = 18.0
    noise.inputs["Detail"].default_value = 3.0
    rng = nt.nodes.new("ShaderNodeMapRange")
    rng.inputs["To Min"].default_value, rng.inputs["To Max"].default_value = SKIN_ROUGH
    rng.inputs["From Min"].default_value, rng.inputs["From Max"].default_value = 0.35, 0.65
    nt.links.new(noise.outputs["Fac"], rng.inputs["Value"])
    nt.links.new(rng.outputs["Result"], bsdf.inputs["Roughness"])


def upgrade_eyes(mat):
    """A wet cornea: a clear glossy coat over the iris and sclera, a touch of softness in the sclera."""
    b = next((n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if not b:
        return
    for k, v in (("Roughness", 0.35), ("Coat Weight", 1.0), ("Coat Roughness", 0.02), ("Coat IOR", 1.376),
                 ("Subsurface Weight", 0.08), ("Specular IOR Level", 0.5)):
        if k in b.inputs:
            b.inputs[k].default_value = v


def upgrade_teeth(mat):
    b = next((n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if b:
        for k, v in (("Roughness", 0.3), ("Subsurface Weight", 0.15), ("Coat Weight", 0.3), ("Coat Roughness", 0.1)):
            if k in b.inputs:
                b.inputs[k].default_value = v


def upgrade_hair(body):
    for ps in body.particle_systems:
        if "hair" not in ps.name.lower() or "stubble" in ps.name.lower():
            continue
        s = ps.settings
        for k, v in HAIR.items():
            if hasattr(s, k):
                setattr(s, k, v)
        mat = bpy.data.materials.get("Max_hair")
        if mat:
            h = next((n for n in mat.node_tree.nodes if n.type == "BSDF_HAIR_PRINCIPLED"), None)
            for k, v in HAIR_SHADER.items():
                if h and k in h.inputs:
                    h.inputs[k].default_value = v


def upgrade(rig):
    body = next(o for o in rig.children_recursive if o.name.endswith(".body"))
    for ob in rig.children_recursive:
        if ob.type != "MESH":
            continue
        for mat in ob.data.materials:
            if not mat or not mat.use_nodes:
                continue
            if ob is body and mat.name == ob.name:
                upgrade_skin(mat)
            elif "high-poly" in ob.name:
                upgrade_eyes(mat)
            elif "teeth" in ob.name:
                upgrade_teeth(mat)
    upgrade_hair(body)
    rig["max_look"] = "v4"


def studio(scene):
    """The house character rig (ink & amber): warm amber key, low cool fill, strong cyan rim, ink-teal world."""
    w = bpy.data.worlds.new("InkTeal")
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.010, 0.032, 0.048, 1)
    bg.inputs[1].default_value = 1.0
    scene.world = w
    for ob in [o for o in scene.objects if o.type == "LIGHT"]:
        bpy.data.objects.remove(ob, do_unlink=True)
    for name, loc, energy, color, size in (
        ("Key", (-1.5, -2.0, 2.3), 260, (1.0, 0.80, 0.62), 1.8),    # warm amber key, soft
        ("Fill", (2.0, -1.8, 1.5), 35, (0.70, 0.82, 1.0), 3.0),     # low cool fill
        ("Rim", (0.9, 2.6, 2.9), 140, (0.37, 0.83, 0.90), 0.8),     # cyan rim (#5FD3E6)
        ("Kicker", (-1.4, 1.8, 1.7), 55, (0.37, 0.83, 0.90), 0.6),
    ):
        ld = bpy.data.lights.new(name, "AREA")
        ld.energy, ld.color, ld.size = energy, color, size
        lo = bpy.data.objects.new(name, ld)
        scene.collection.objects.link(lo)
        lo.location = loc
        lo.rotation_euler = (Vector((0, 0, 1.5)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    rig = bpy.data.objects.get("Max")
    if rig is None:
        raise SystemExit("open a Max .blend first")
    upgrade(rig)
    if "--sheet" in argv:          # turnaround + expression sheet in the house light rig
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import build_max
        build_max.sheet(rig, os.path.abspath(argv[argv.index("--sheet") + 1]))
    if "--out" in argv:
        out = os.path.abspath(argv[argv.index("--out") + 1])
        bpy.ops.file.pack_all()
        bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
        print("saved", out, os.path.getsize(out) // 1024, "KB")
