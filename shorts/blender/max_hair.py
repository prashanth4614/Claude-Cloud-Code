"""Max's hair and stubble: particle grooms combed from code (free, renders in Cycles and EEVEE).

groom(rig, body) adds to Max.body:
  - "Max hair": ~2.5k combed guide strands + interpolated children. A thick, messy, dark-brown mop:
    longer textured top swept forward over the forehead, short tapered sides and back.
  - "Max stubble": very short dark hairs on the jaw, chin, upper lip and cheeks. They ride on the
    face shapes, so the stubble moves with every expression.
  - "Max.scalp": a thin dark-brown cap under the hair, so no skin shows between strands.

Every strand is computed from the shaped head (eye and mouth positions), so the groom refits if the
face shape changes. Tweak the look with the constants below.
"""
import math
import random

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

SEED = 7
GUIDES = 1800                 # fewer, chunkier locks (stylized, reads in wide shots)
CHILDREN = 70                 # rendered children per guide
TOP_LEN, SIDE_LEN, BACK_LEN = 0.058, 0.026, 0.022
SWEEP = Vector((0.5, -0.2, 0.42))   # front/top flow: up off the forehead and over to his left (+X)
HAIR_MELANIN, HAIR_REDNESS = 0.9, 0.12     # dark brown, highlights without orange tips
STUBBLE_COUNT, STUBBLE_LEN = 14000, 0.0022


# --------------------------------------------------------------- geometry --
def shaped_mesh(body):
    """Body vertex positions with the phenotype shape keys applied (expressions at 0), plus normals."""
    me = body.data
    n = len(me.vertices)
    keys = me.shape_keys.key_blocks
    basis = np.empty(n * 3, dtype=np.float32)
    keys[0].data.foreach_get("co", basis)
    co = basis.copy()
    buf = np.empty(n * 3, dtype=np.float32)
    for kb in keys[1:]:
        if kb.value == 0.0 or kb.mute:
            continue
        kb.data.foreach_get("co", buf)
        co += (buf - basis) * kb.value
    tmp = me.copy()
    tmp.vertices.foreach_set("co", co)
    tmp.update()
    nor = np.empty(n * 3, dtype=np.float32)
    tmp.vertex_normals.foreach_get("vector", nor)
    polys = [tuple(p.vertices) for p in tmp.polygons]
    bpy.data.meshes.remove(tmp)
    return co.reshape(-1, 3), nor.reshape(-1, 3), polys


def landmarks(rig):
    """Eye centre, mouth centre and head centre (object space of the body; rig sits at the origin)."""
    dg = bpy.context.evaluated_depsgraph_get()

    def centre(suffix):
        ob = next(o for o in rig.children_recursive if o.name.endswith(suffix))
        oe = ob.evaluated_get(dg)
        return sum((oe.matrix_world @ Vector(c) for c in oe.bound_box), Vector()) / 8

    eye = centre("high-poly")
    teeth = centre("teeth_base")
    head = Vector((eye.x, eye.y + 0.085, eye.z + 0.02))
    return eye, teeth, head


def _ramp(x, pts):
    """Piecewise-linear lookup in a sorted [(x, y), ...] table."""
    if x <= pts[0][0]:
        return pts[0][1]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return pts[-1][1]


def _smooth(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def scalp_weight(p, eye, head):
    """1 inside the hairline, fading to 0 over ~1 cm. Hairline height above the eyes by angle round the head."""
    rel = p - head
    if rel.length > 0.17 or p.z < eye.z - 0.11:
        return 0.0
    phi = abs(math.degrees(math.atan2(rel.x, -rel.y)))   # 0 = front, 90 = side, 180 = back
    hairline = _ramp(phi, [(0, 0.064), (30, 0.06), (55, 0.046), (80, 0.03), (100, 0.022), (120, -0.01), (150, -0.06), (180, -0.08)])
    w = _smooth(0.0, 0.012, (p.z - eye.z) - hairline)
    # keep the ears and the skin right behind them clear
    if 75 < phi < 125 and abs(rel.x) > 0.072 and p.z - eye.z < 0.035:
        w = 0.0
    return w


def beard_weight(p, eye, mouth, head):
    rel = p - head
    if rel.y > 0.0 or abs(rel.x) > 0.078:
        return 0.0
    h = p.z - eye.z
    top = _ramp(abs(rel.x), [(0.0, mouth.z - eye.z + 0.022), (0.03, -0.052), (0.06, -0.048), (0.078, -0.02)])
    bottom = mouth.z - eye.z - 0.085
    w = _smooth(top, top - 0.008, h) * _smooth(bottom, bottom + 0.012, h)
    # lips stay clean
    lx, lz = (p.x - mouth.x) / 0.029, (p.z - mouth.z) / 0.012
    if lx * lx + lz * lz < 1.0 and p.y < mouth.y + 0.02:
        w = 0.0
    return w * (0.55 + 0.45 * _smooth(-0.07, -0.03, rel.y * -1))  # lighter toward the ears


# --------------------------------------------------------------- materials --
def hair_material(name, melanin, redness, rough=0.28):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    h = nt.nodes.new("ShaderNodeBsdfHairPrincipled")
    if hasattr(h, "parametrization"):
        h.parametrization = "MELANIN"
    for key, val in (("Melanin", melanin), ("Melanin Redness", redness), ("Roughness", rough),
                     ("Radial Roughness", 0.3), ("Coat", 0.1), ("Random Roughness", 0.2), ("Random Color", 0.1)):
        if key in h.inputs:
            h.inputs[key].default_value = val
    nt.links.new(h.outputs[0], out.inputs["Surface"])
    m.diffuse_color = (0.05, 0.03, 0.02, 1)
    return m


# ---------------------------------------------------------------- systems --
def _add_system(body, name, count, length, steps, vgroup, mat):
    for o in bpy.context.selected_objects:
        o.select_set(False)
    bpy.context.view_layer.objects.active = body
    body.select_set(True)
    mod = body.modifiers.new(name, "PARTICLE_SYSTEM")
    # must sit after the Armature but before the helper masks, or roots emit at the origin; later
    # systems go after earlier ones so a combed system never moves (moving it scrambles its strands)
    mods = list(body.modifiers)
    first = next(i for i, m in enumerate(mods) if m.type == "MASK")
    body.modifiers.move(mods.index(mod), first)
    print("MODSTACK", [m.name for m in body.modifiers])
    ps = body.particle_systems[name]
    s = ps.settings
    s.name = name
    s.type = "HAIR"
    s.count = count
    s.hair_length = length
    s.hair_step = steps
    s.emit_from = "FACE"
    s.distribution = "RAND"
    s.use_even_distribution = True
    ps.vertex_group_density = vgroup
    ps.seed = SEED
    if mat.name not in body.data.materials:
        body.data.materials.append(mat)
    s.material_slot = mat.name
    s.use_hair_bspline = True
    s.display_step, s.render_step = 3, 5
    return mod, ps, s


def _evaluated(body, name):
    """Roots plus the evaluated object/modifier/particles. Keys must be written through these:
    the original particles have no hair-space matrix, so writing through them doubles every root."""
    dg = bpy.context.evaluated_depsgraph_get()
    oe = body.evaluated_get(dg)
    pe = oe.particle_systems[name]
    roots = [pe.co_hair(oe, particle_no=i, step=0).copy() for i in range(len(pe.particles))]
    return roots, oe, oe.modifiers[name], pe


def _activate_edit(body):
    bpy.ops.particle.particle_edit_toggle()
    bpy.ops.particle.particle_edit_toggle()


def groom(rig, body):
    rnd = random.Random(SEED)
    co, nor, polys = shaped_mesh(body)
    eye, mouth, head = landmarks(rig)
    # Only real skin: MPFB's basemesh also holds hidden helper shells (hair helmet, tights, ...).
    gi = body.vertex_groups["body"].index
    skin = {v.index for v in body.data.vertices if any(g.group == gi and g.weight > 0.5 for g in v.groups)}
    polys = [f for f in polys if all(v in skin for v in f)]
    bvh = BVHTree.FromPolygons([Vector(v) for v in co], polys)

    scalp = body.vertex_groups.get("hair_scalp") or body.vertex_groups.new(name="hair_scalp")
    beard = body.vertex_groups.get("hair_beard") or body.vertex_groups.new(name="hair_beard")
    sw, bw = {}, {}
    for i in skin:
        v = Vector(co[i])
        w = scalp_weight(v, eye, head)
        if w > 0:
            sw[i] = w
        b = beard_weight(v, eye, mouth, head)
        if b > 0:
            bw[i] = b
    for i, w in sw.items():
        scalp.add([i], w, "REPLACE")
    for i, w in bw.items():
        beard.add([i], w, "REPLACE")

    build_scalp_cap(rig, body, co, polys, sw)

    hair_mat = hair_material("Max_hair", HAIR_MELANIN, HAIR_REDNESS)
    mod, ps, s = _add_system(body, "Max hair", GUIDES, TOP_LEN, 6, "hair_scalp", hair_mat)
    s.child_type = "INTERPOLATED"
    s.child_percent, s.rendered_child_count = 8, CHILDREN
    s.virtual_parents = 0.0
    s.clump_factor, s.clump_shape = 0.7, -0.1        # defined locks with soft, rounded ends (not spikes)
    s.roughness_1, s.roughness_1_size = 0.0012, 1.0
    s.roughness_endpoint, s.roughness_end_shape = 0.003, 1.0
    s.roughness_2, s.roughness_2_size, s.roughness_2_threshold = 0.0015, 1.0, 0.85   # few flyaways
    s.child_length_threshold = 0.25
    s.root_radius, s.tip_radius, s.radius_scale = 1.0, 0.45, 0.0005   # blunt lock ends: soft, not spiky
    s.use_close_tip = True
    s.kink, s.kink_amplitude, s.kink_frequency, s.kink_shape = "WAVE", 0.0012, 1.2, 0.0   # a soft wave, not curls
    _activate_edit(body)
    roots, oe, me, pe = _evaluated(body, "Max hair")
    sweep = SWEEP.normalized()
    for idx, (part, root) in enumerate(zip(ps.particles, roots)):
        root = Vector(root)
        loc, n, _, _ = bvh.find_nearest(root)
        n = n if n is not None else (root - head).normalized()
        rel = root - head
        h = root.z - eye.z
        phi = abs(math.degrees(math.atan2(rel.x, -rel.y)))
        top = _smooth(0.045, 0.085, h) * (1 - _smooth(120, 160, phi))
        back = _smooth(110, 160, phi) * (1 - top)
        length = (SIDE_LEN * (1 - top - back) + TOP_LEN * top + BACK_LEN * back) * rnd.uniform(0.8, 1.2)
        side_flow = Vector((0.0, 0.45, -1.0)).normalized()
        flow = (sweep * top + side_flow * (1 - top)).normalized()
        lift = 0.45 * top + 0.25 * (1 - top)
        d = (n * lift + flow * (1 - lift)).normalized()
        jitter = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-0.5, 0.5))) * 0.35
        d = (d + jitter).normalized()
        nk = len(part.hair_keys)
        seg = length / (nk - 1)
        p = root.copy()
        pts = [root]
        for k in range(1, nk):
            wave = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))) * 0.18 * top
            d = (d + flow * 0.45 + wave + Vector((0, 0, -1)) * (0.22 + 0.15 * (1 - top))).normalized()
            p = p + d * seg
            near, nn, _, _ = bvh.find_nearest(p)
            if near is not None:
                off = 0.0022 + 0.0012 * k * (0.5 + top)
                if (p - near).dot(nn) < off:
                    p = near + nn * off
            pts.append(p.copy())
        for key, q in zip(part.hair_keys, pts):
            key.co_object_set(oe, me, pe.particles[idx], q)

    stub_mat = hair_material("Max_stubble", 0.95, 0.3, rough=0.45)
    smod, sps, ss = _add_system(body, "Max stubble", STUBBLE_COUNT, STUBBLE_LEN, 2, "hair_beard", stub_mat)
    ss.child_type = "NONE"
    ss.root_radius, ss.tip_radius, ss.radius_scale = 1.0, 0.2, 0.00012
    _activate_edit(body)
    sroots, oe, me, pe = _evaluated(body, "Max stubble")
    for idx, (part, root) in enumerate(zip(sps.particles, sroots)):
        root = Vector(root)
        _, n, _, _ = bvh.find_nearest(root)
        n = n if n is not None else Vector((0, -1, 0))
        d = (n + Vector((0, 0, -0.9)) + Vector((rnd.uniform(-.3, .3), 0, rnd.uniform(-.2, .2)))).normalized()
        L = STUBBLE_LEN * rnd.uniform(0.6, 1.3)
        keys = part.hair_keys
        for k, key in enumerate(keys):
            key.co_object_set(oe, me, pe.particles[idx], root + d * (L * k / (len(keys) - 1)))

    bpy.context.view_layer.update()
    report(body)
    return ps, sps


def report(body):
    dg = bpy.context.evaluated_depsgraph_get()
    oe = body.evaluated_get(dg)
    for pe in oe.particle_systems:
        n = len(pe.particles)
        steps = pe.settings.hair_step
        lens = [(pe.co_hair(oe, particle_no=i, step=steps) - pe.co_hair(oe, particle_no=i, step=0)).length
                for i in range(0, n, max(1, n // 200))]
        roots = [pe.co_hair(oe, particle_no=i, step=0) for i in range(0, n, max(1, n // 200))]
        lo = [min(r[a] for r in roots) for a in range(3)]
        hi = [max(r[a] for r in roots) for a in range(3)]
        print(f"GROOM {pe.name}: {n} strands, tip distance {min(lens):.4f}..{max(lens):.4f} m, "
              f"roots in {[round(v, 3) for v in lo]}..{[round(v, 3) for v in hi]}")


def build_scalp_cap(rig, body, co, polys, weights):
    """Dark-brown cap 1.5 mm over the scalp, skinned to the head bone (no skin between strands)."""
    keep = {i for i, w in weights.items() if w > 0.7}     # inset from the hairline: its edge never shows
    faces = [f for f in polys if all(v in keep for v in f)]
    used = sorted({v for f in faces for v in f})
    remap = {v: i for i, v in enumerate(used)}
    me = bpy.data.meshes.new("Max.scalp")
    me.from_pydata([Vector(co[v]) for v in used], [], [[remap[v] for v in f] for f in faces])
    me.update()
    for v in me.vertices:
        v.co += v.normal * 0.0015
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new("Max.scalp", me)
    for c in body.users_collection:
        c.objects.link(ob)
    ob.parent = rig
    vg = ob.vertex_groups.new(name="head")
    vg.add(list(range(len(me.vertices))), 1.0, "REPLACE")
    arm = ob.modifiers.new("Armature", "ARMATURE")
    arm.object = rig
    mat = bpy.data.materials.new("Max_scalp")
    mat.use_nodes = True
    b = mat.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.035, 0.021, 0.013, 1)       # matches the hair at the root
    b.inputs["Roughness"].default_value = 0.7
    mat.diffuse_color = (0.022, 0.013, 0.008, 1)
    me.materials.append(mat)
    return ob
