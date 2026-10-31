"""Max's look upgrade (v4): skin, eyes, teeth and hair at Zack-level polish, plus the house light rig.

    upgrade(rig)      tune the MPFB materials and the hair groom on a built Max (build_max.py calls it)
    studio(scene)     the "ink & amber" character light rig: warm key, cool fill, cyan rim, ink-teal world

Also runs on an existing file, without rebuilding:

    blender -b assets/characters/max/max_v3.blend -P shorts/blender/max_look.py -- --out assets/characters/max/max_v5.blend [--regroom] [--curves] [--sheet DIR]

Realism comes from light and materials, not polygons (shorts-craft §11): pores and patchy gloss on the skin,
a wet cornea coat on the eyes, fine clumped hair with stray tips, and a soft key with a cyan rim.
"""
import os
import sys

import bpy
from mathutils import Vector

# MPFB "ENHANCED_SSS" skin group inputs (the group exposes them; defaults in brackets)
SKIN = {
    "Pore strength": 0.55,        # [0.2] visible pores in close-ups (0.38 still read waxy on the Mac sheet)
    "Pore scale": 2600.0,         # [2500]
    "SSS strength": 0.32,         # [0.2] softer, light-through skin (less waxy)
    "SSS radius scale": 0.12,     # [0.1]
    "colorMixIn": (0.95, 0.25, 0.22, 1.0),
    "colorMixInStrength": 0.08,   # [0.05] a little blood flush
    "Clearcoat": 0.06,            # [0.1] a faint natural sheen (more made rim lights glare on the temples)
    "Clearcoat Roughness": 0.35,
}
SKIN_ROUGH = (0.38, 0.52)         # T-zone (oily) / elsewhere: by anatomy, from paint_zones() (Codex 010)
SKIN_LIP_ROUGH = 0.32
SKIN_FLUSH = 0.6                  # multiply strength toward a warm red on ears, nose tip and cheeks
SUBDIV_RENDER = 2                 # the face's render subdivision (silhouette, fine expression creases)

# hair groom (max_hair.py's particle systems): fine, smooth, barely clumped strands
HAIR = {"rendered_child_count": 150, "radius_scale": 0.00034, "tip_radius": 0.6, "clump_factor": 0.15,
        "clump_shape": 0.0, "roughness_1": 0.0004, "roughness_endpoint": 0.0005, "roughness_2": 0.0006,
        "roughness_2_threshold": 0.95}   # neat and groomed (the owner: "normal and stylish", no spikes)
HAIR_SHADER = {"Roughness": 0.32, "Radial Roughness": 0.35, "Coat": 0.12, "Random Color": 0.12,
               "Random Roughness": 0.25}


def _group_input(mat, name, value):
    for n in mat.node_tree.nodes:
        if n.type == "GROUP" and name in n.inputs:
            n.inputs[name].default_value = value
            return True
    return False


def paint_zones(rig, body):
    """Per-vertex skin zones from Max's facial landmarks (Codex 010: anatomy, not random noise):
    zone_oil (forehead centre and nose: the T-zone), zone_lip (lips), zone_red (ears, nose tip, cheeks)."""
    import numpy as np
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import max_hair
    co, _, _ = max_hair.shaped_mesh(body)
    eye, mouth, head = max_hair.landmarks(rig)
    ex, ey, ez = eye
    mx, my, mz = mouth
    centre = np.abs(co[:, 0] - ex) < 0.012
    band = centre & (co[:, 2] > mz + 0.005) & (co[:, 2] < ez + 0.005)
    nose = co[band][np.argmin(co[band][:, 1])] if band.any() else np.array([ex, ey - 0.03, (ez + mz) / 2])
    front = co[:, 1] < ey + 0.02                   # the face side of the head (front is -y)

    def fall(d, r0, r1):
        return np.clip((r1 - d) / (r1 - r0), 0, 1)
    dx, dz = np.abs(co[:, 0] - ex), co[:, 2] - ez
    forehead = fall(dx, 0.02, 0.045) * fall(np.abs(dz - 0.045), 0.02, 0.04) * front
    nose_d = np.linalg.norm(co - nose, axis=1)
    oil = np.maximum(forehead, fall(nose_d, 0.012, 0.03) * front)
    lip = fall(np.abs(co[:, 2] - mz), 0.006, 0.013) * fall(np.abs(co[:, 0] - mx), 0.02, 0.03) * (co[:, 1] < my - 0.005)
    cheeks = sum(fall(np.linalg.norm(co - np.array([ex + sx * 0.042, ey - 0.012, ez - 0.03]), axis=1), 0.01, 0.03)
                 for sx in (-1, 1))
    ears = fall(np.abs(co[:, 2] - (ez - 0.005)), 0.02, 0.035) * (dx > 0.066) * (co[:, 1] > ey + 0.02)
    red = np.clip(np.maximum.reduce([cheeks * 0.8, ears, fall(nose_d, 0.006, 0.016) * front]), 0, 1)
    me = body.data
    for name, vals in (("zone_oil", oil), ("zone_lip", lip), ("zone_red", red)):
        at = me.attributes.get(name) or me.attributes.new(name, "FLOAT", "POINT")
        at.data.foreach_set("value", vals.astype(np.float32))
    return {"oil": int((oil > 0.5).sum()), "lip": int((lip > 0.5).sum()), "red": int((red > 0.5).sum())}


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
    # roughness by anatomy: T-zone (oil) 0.38, cheeks and the rest 0.52, lips 0.32, plus +-0.025 noise
    oil = nt.nodes.new("ShaderNodeAttribute")
    oil.attribute_name, oil.attribute_type = "zone_oil", "GEOMETRY"
    lip = nt.nodes.new("ShaderNodeAttribute")
    lip.attribute_name, lip.attribute_type = "zone_lip", "GEOMETRY"
    red = nt.nodes.new("ShaderNodeAttribute")
    red.attribute_name, red.attribute_type = "zone_red", "GEOMETRY"
    base = nt.nodes.new("ShaderNodeMapRange")
    base.name = "max_look_rough"
    base.inputs["To Min"].default_value, base.inputs["To Max"].default_value = SKIN_ROUGH[1], SKIN_ROUGH[0]
    nt.links.new(oil.outputs["Fac"], base.inputs["Value"])
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 30.0
    jitter = nt.nodes.new("ShaderNodeMath")
    jitter.operation = "MULTIPLY_ADD"
    jitter.inputs[1].default_value, jitter.inputs[2].default_value = 0.05, -0.025
    nt.links.new(noise.outputs["Fac"], jitter.inputs[0])
    add = nt.nodes.new("ShaderNodeMath")
    add.operation = "ADD"
    nt.links.new(base.outputs["Result"], add.inputs[0])
    nt.links.new(jitter.outputs[0], add.inputs[1])
    lipmix = nt.nodes.new("ShaderNodeMix")
    lipmix.data_type = "FLOAT"
    nt.links.new(lip.outputs["Fac"], lipmix.inputs["Factor"])
    nt.links.new(add.outputs[0], lipmix.inputs["A"])
    lipmix.inputs["B"].default_value = SKIN_LIP_ROUGH
    nt.links.new(lipmix.outputs["Result"], bsdf.inputs["Roughness"])
    # natural redness on the ears, nose tip and cheeks (3-8 %)
    link = bsdf.inputs["Base Color"].links[0]
    flush = nt.nodes.new("ShaderNodeMix")
    flush.data_type, flush.blend_type = "RGBA", "MULTIPLY"
    amt = nt.nodes.new("ShaderNodeMath")
    amt.operation = "MULTIPLY"
    amt.inputs[1].default_value = SKIN_FLUSH
    nt.links.new(red.outputs["Fac"], amt.inputs[0])
    nt.links.new(amt.outputs[0], flush.inputs["Factor"])
    nt.links.new(link.from_socket, flush.inputs["A"])
    flush.inputs["B"].default_value = (1.0, 0.62, 0.55, 1.0)
    nt.links.new(flush.outputs["Result"], bsdf.inputs["Base Color"])


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
        for k, v in (("Roughness", 0.25), ("Subsurface Weight", 0.15), ("Coat Weight", 0.15), ("Coat Roughness", 0.1)):
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
    print("[max_look] skin zones", paint_zones(rig, body))
    for m in body.modifiers:
        if m.type == "SUBSURF":
            m.render_levels = SUBDIV_RENDER
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
    rig["max_look"] = "v5"


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
        ("Key", (-0.86, -1.23, 2.28), 100, (1.0, 0.86, 0.72), 1.0),  # Codex 010: 1 m wide, 1.5 m away, 35° side, 25° up
        ("Fill", (2.0, -1.8, 1.5), 35, (0.70, 0.82, 1.0), 3.0),     # low cool fill
        ("Rim", (0.9, 2.6, 2.9), 70, (0.37, 0.83, 0.90), 0.8),     # cyan rim (#5FD3E6)
        ("Kicker", (-1.4, 1.8, 1.7), 25, (0.37, 0.83, 0.90), 0.6),
        ("EyeLight", (0.25, -2.4, 1.68), 18, (1.0, 0.95, 0.9), 0.35),  # small, near the lens: a clear catchlight
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
    if "--regroom" in argv:        # re-run max_hair.groom on this Max (replaces the old hair, stubble and scalp)
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import max_hair
        body = next(o for o in rig.children_recursive if o.name.endswith(".body"))
        for mod in [m for m in body.modifiers if m.type == "PARTICLE_SYSTEM"]:
            body.modifiers.remove(mod)
        for ob in [o for o in bpy.data.objects if o.name.startswith("Max.scalp")]:
            bpy.data.objects.remove(ob, do_unlink=True)
        bpy.context.view_layer.objects.active = body
        max_hair.groom(rig, body)
    upgrade(rig)
    if "--curves" in argv:         # v5: the particle hair becomes real hair curves (max_hair_curves.py)
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import max_hair_curves
        max_hair_curves.to_curves(rig, next(o for o in rig.children_recursive if o.name.endswith(".body")))
    if "--sheet" in argv:          # turnaround + expression sheet in the house light rig
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import build_max
        build_max.sheet(rig, os.path.abspath(argv[argv.index("--sheet") + 1]))
    if "--out" in argv:
        out = os.path.abspath(argv[argv.index("--out") + 1])
        bpy.ops.file.pack_all()
        bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
        print("saved", out, os.path.getsize(out) // 1024, "KB")
