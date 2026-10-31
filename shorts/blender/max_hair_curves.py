"""Max's hair as real hair curves (v5): the combed particle guides become a Curves object groomed with
Blender's bundled hair node assets, so the hair reads as thousands of fine strands, not locks.

    to_curves(rig, body)      convert the "Max hair" particle guides to curves and build the groom

Groom (one Geometry Nodes modifier on the Curves object):
    Deform Curves on Surface (follows the body with the rig and the face shapes; must come first)
    → Duplicate Hair Curves (STRANDS close copies of each converted strand: the guides plus their
      interpolated particle children, so the style stays as designed and the scalp is evenly covered)
    → Clump (subtle, toward each guide) → Frizz (tiny) → Shrinkwrap (no strand under the skin)
    → Set Hair Curve Profile (tapered strands)
Shader: Principled Hair BSDF, Huang model, dark brown.

Also runs on a built Max file:

    blender -b assets/characters/max/max_v4.blend -P shorts/blender/max_hair_curves.py -- --out OUT.blend
"""
import os
import sys

import bpy

CHILDREN = 25                 # particle children converted per guide: they fill the scalp evenly (3000 -> ~78k)
STRANDS = 1                   # extra duplicates per strand, close around it (-> ~156k strands in renders)
SPREAD = 0.0012               # m around each strand
CLUMP = {"Factor": 0.25, "Shape": 0.35, "Tip Spread": 0.0012}
FRIZZ = {"Factor": 1.0, "Distance": 0.0003, "Shape": 0.7}
PROFILE = {"Radius": 0.000035, "Shape": -0.35, "Factor Min": 0.15, "Factor Max": 1.0}  # radius 0.035 -> 0.005 mm (Codex 010)
SHADER = {"Melanin": 0.88, "Melanin Redness": 0.12, "Roughness": 0.3, "Coat": 0.08, "Random Color": 0.08,
          "Random Roughness": 0.2, "Aspect Ratio": 0.85}
GROUPS = ("Duplicate Hair Curves", "Clump Hair Curves", "Frizz Hair Curves", "Shrinkwrap Hair Curves",
          "Set Hair Curve Profile")
LIFT = 0.0018                 # m: duplicates are pushed out to at least this far above the scalp


def _assets():
    p = os.path.join(bpy.utils.system_resource("DATAFILES"), "assets", "nodes", "procedural_hair_node_assets.blend")
    missing = [g for g in GROUPS if g not in bpy.data.node_groups]
    if missing:
        with bpy.data.libraries.load(p) as (src, dst):
            dst.node_groups = missing
    return {g: bpy.data.node_groups[g] for g in GROUPS}


def _material():
    m = bpy.data.materials.get("Max_hair_curves") or bpy.data.materials.new("Max_hair_curves")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    h = nt.nodes.new("ShaderNodeBsdfHairPrincipled")
    h.model = "HUANG"
    if hasattr(h, "parametrization"):
        h.parametrization = "MELANIN"
    for k, v in SHADER.items():
        if k in h.inputs:
            h.inputs[k].default_value = v
    nt.links.new(h.outputs[0], out.inputs["Surface"])
    m.diffuse_color = (0.04, 0.025, 0.015, 1)
    return m


def _groom_tree(groups, surface):
    nt = bpy.data.node_groups.new("Max hair groom", "GeometryNodeTree")
    nt.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    nt.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    gi, go = nt.nodes.new("NodeGroupInput"), nt.nodes.new("NodeGroupOutput")
    deform = nt.nodes.new("GeometryNodeDeformCurvesOnSurface")
    chain = [deform]
    for name, vals in (("Duplicate Hair Curves", {"Amount": STRANDS, "Viewport Amount": 0.0, "Radius": SPREAD,
                                                  "Distribution Shape": -0.3, "Tip Roundness": 0.4,
                                                  "Even Thickness": True}),
                       ("Clump Hair Curves", CLUMP), ("Frizz Hair Curves", FRIZZ),
                       # duplicates spread around each guide in every direction, so on the flat-lying short sides
                       # half of them went under the skin (bald band above the ears): push them back out
                       ("Shrinkwrap Hair Curves", {"Factor": 1.0, "Offset Distance": LIFT, "Above Surface": 0.0,
                                                   "Smoothing Steps": 2, "Lock Roots": True}),
                       ("Set Hair Curve Profile", PROFILE)):
        n = nt.nodes.new("GeometryNodeGroup")
        n.node_tree = groups[name]
        for k, v in vals.items():
            if k in n.inputs:
                n.inputs[k].default_value = v
        if name == "Shrinkwrap Hair Curves":
            next(i for i in n.inputs if i.name == "Surface" and i.type == "OBJECT").default_value = surface
        chain.append(n)
    mat = nt.nodes.new("GeometryNodeSetMaterial")
    mat.inputs["Material"].default_value = _material()
    chain.append(mat)
    nt.links.new(gi.outputs[0], chain[0].inputs[0])
    for a, b in zip(chain, chain[1:]):
        nt.links.new(a.outputs[0], b.inputs[0])
    nt.links.new(chain[-1].outputs[0], go.inputs[0])
    for i, n in enumerate([gi] + chain + [go]):
        n.location = (i * 220, 0)
    return nt


def hair_surface(rig, body):
    """An invisible scalp mesh for the hair to attach to: the body's whole hair_scalp region (with the face
    shape applied), skinned to the head bone. The body itself can't be used: its mask and subdivision
    modifiers change its topology, which breaks Deform Curves on Surface."""
    import math
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import max_hair
    from mathutils import Vector
    co, nor, polys = max_hair.shaped_mesh(body)
    vg = body.vertex_groups["hair_scalp"].index
    w = {v.index: g.weight for v in body.data.vertices for g in v.groups if g.group == vg and g.weight > 0}
    # every face touching the hair region, plus one ring around it: roots outside the surface get snapped to
    # its edge (that pulled the temple hair up and left a bald band above the ears)
    ring = {v for f in polys if any(v in w for v in f) for v in f}
    faces = [f for f in polys if any(v in ring for v in f)]
    used = sorted({v for f in faces for v in f})
    remap = {v: i for i, v in enumerate(used)}
    me = bpy.data.meshes.new("Max.hair_surface")
    me.from_pydata([Vector(co[v]) for v in used], [], [[remap[v] for v in f] for f in faces])
    me.update()
    ctr = sum((v.co for v in me.vertices), Vector()) / len(me.vertices)
    uv = me.uv_layers.new(name="UVMap")
    for loop in me.loops:                                     # a simple spherical projection (a cap: no overlaps)
        d = me.vertices[loop.vertex_index].co - ctr
        uv.data[loop.index].uv = (math.atan2(d.x, -d.y) / (2 * math.pi) + 0.5, 0.5 + d.z * 4)
    ob = bpy.data.objects.new("Max.hair_surface", me)
    moved = max_hair.follow_face(body, ob, used)   # the roots move with the brows and forehead
    print(f"[hair surface] {len(moved)} face shapes follow the body: {moved}")
    for c in body.users_collection:
        c.objects.link(ob)
    ob.parent = rig
    ob.vertex_groups.new(name="head").add(list(range(len(me.vertices))), 1.0, "REPLACE")
    ob.modifiers.new("Armature", "ARMATURE").object = rig
    ob.hide_render = True
    ob.display_type = "WIRE"
    ob.hide_viewport = False
    ob.add_rest_position_attribute = True
    return ob


def to_curves(rig, body):
    ps = body.particle_systems.get("Max hair")
    if ps is None:
        raise SystemExit("no 'Max hair' particle system to convert")
    # convert the combed guides AND their interpolated children: the children are spread over the whole
    # scalp (duplicating only around the guides left the thinly guided sides bald)
    ps.settings.child_type = "INTERPOLATED"
    ps.settings.child_percent = CHILDREN
    mod = next(m for m in body.modifiers if m.type == "PARTICLE_SYSTEM" and m.particle_system == ps)
    mod.show_viewport = True
    bpy.ops.object.select_all(action="DESELECT")
    body.select_set(True)
    bpy.context.view_layer.objects.active = body
    before = set(bpy.data.objects)
    body.particle_systems.active_index = list(body.particle_systems).index(ps)
    bpy.ops.curves.convert_from_particle_system()
    cv = next(o for o in bpy.data.objects if o not in before and o.type == "CURVES")
    cv.name = "Max.hair"
    for c in list(cv.users_collection):
        c.objects.unlink(cv)
    for c in body.users_collection:
        c.objects.link(cv)
    body.modifiers.remove(mod)                   # the particle hair is replaced by the curves
    cap = bpy.data.objects.get("Max.scalp")
    if cap:                                      # ~150k strands cover the scalp on their own; the cap's jagged
        cap.hide_render = cap.hide_viewport = True   # edge showed through the soft hairline
    surf = hair_surface(rig, body)
    cv.data.surface = surf
    cv.data.surface_uv_map = "UVMap"
    mw = cv.matrix_world.copy()
    cv.parent = surf
    cv.matrix_world = mw
    bpy.ops.object.select_all(action="DESELECT")
    cv.select_set(True)
    bpy.context.view_layer.objects.active = cv
    bpy.ops.curves.snap_curves_to_surface(attach_mode="NEAREST")   # roots on the scalp, UV attachment
    gm = cv.modifiers.new("Groom", "NODES")
    gm.node_group = _groom_tree(_assets(), surf)
    cv.data.materials.append(bpy.data.materials["Max_hair_curves"])
    bpy.context.view_layer.update()
    n = len(cv.data.curves)
    print(f"[hair curves] {n} strands converted -> ~{n * (STRANDS + 1)} in renders")
    return cv


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    rig = bpy.data.objects["Max"]
    body = next(o for o in rig.children_recursive if o.name.endswith(".body"))
    to_curves(rig, body)
    if "--out" in argv:
        out = os.path.abspath(argv[argv.index("--out") + 1])
        bpy.ops.file.pack_all()
        bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
        print("saved", out, os.path.getsize(out) // 1024, "KB")
