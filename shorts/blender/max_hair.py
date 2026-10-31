"""Max's hair and stubble: particle grooms combed from code (free, renders in Cycles and EEVEE).

groom(rig, body) adds to Max.body:
  - "Max hair": ~3k combed guide strands + interpolated children. v4: a neat, modern side part. The
    longer top is combed back and over with a low quiff at the front; the sides and back are short and tidy.
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
GUIDES = 3000                 # v4: more, finer guides for a smooth, groomed look (not chunky locks)
CHILDREN = 60                 # rendered children per guide (max_look.py raises it for renders)
TOP_LEN, SIDE_LEN, BACK_LEN = 0.072, 0.018, 0.02   # longer top, short tapered sides and back
TOP_BLEND = (0.03, 0.09)      # height above the eyes where the long top blends into the short sides (v6e: was 0.045-0.085)
EAR_CLEAR = 0.012             # no hair over the ear below this height above the eyes (the ear top is at ~0.004)
FRINGE_Z = 0.054              # front strands stay above this height over the eyes (no locks on the forehead)
# v4 style: a neat side part. The part sits on his right (-X); the top is combed back and over to his left
# (+X) with a soft lift at the front (a low quiff), the short side below the part is combed down and back.
PART_X = -0.035               # part line, relative to the head centre (his right is -X)
SWEEP = Vector((0.55, 0.55, 0.12))   # top flow: back and over to his left, lying on the head
FRONT_LIFT = 0.4              # lift at the front hairline only (the quiff), fading to flat by mid-head
WAVE = 0.04                   # a whisper of wave (v3: 0.15-0.3 made spiky zigzags)
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


def scalp_weight(p, eye, head, fade=False):
    """1 inside the hairline, fading to 0 over ~1 cm. Hairline height above the eyes by angle round the head.
    fade=True: a wider, lower gradient on the sides and back (the skin tint of a fade haircut)."""
    rel = p - head
    if rel.length > 0.17 or p.z < eye.z - 0.11:
        return 0.0
    phi = abs(math.degrees(math.atan2(rel.x, -rel.y)))   # 0 = front, 90 = side, 180 = back
    # v5b: lower and fuller (the v5 review: the hairline read as receding, an "M" with bare temples)
    # v6e (Codex 013, "the top ends above a pale shaved band"): temples come down into a short sideburn in
    # front of the ear (the ear spans phi ~90-120 and tops out ~4 mm above eye level)
    hairline = _ramp(phi, [(0, 0.057), (30, 0.049), (55, 0.030), (68, 0.012), (78, -0.010), (88, -0.024),
                           (100, -0.02), (125, -0.03), (150, -0.06), (180, -0.08)])
    if fade:
        side = _smooth(50, 80, phi)                 # sides and back only: never darken the forehead
        w = _smooth(-0.022 * side, 0.012 + 0.02 * side, (p.z - eye.z) - hairline)
    else:
        w = _smooth(0.0, 0.012, (p.z - eye.z) - hairline)
    # keep the ears clear, with a small margin (v6e: was 35 mm above the eyes, a bald strip over each ear)
    if 86 < phi < 128 and abs(rel.x) > 0.072 and p.z - eye.z < EAR_CLEAR:
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
    s.clump_factor, s.clump_shape = 0.15, 0.0        # v4: barely clumped, so no pointed spikes
    s.roughness_1, s.roughness_1_size = 0.0004, 1.0
    s.roughness_endpoint, s.roughness_end_shape = 0.0005, 1.0
    s.roughness_2, s.roughness_2_size, s.roughness_2_threshold = 0.0006, 1.0, 0.95   # rare flyaways
    s.child_length_threshold = 0.25
    s.root_radius, s.tip_radius, s.radius_scale = 1.0, 0.6, 0.00034   # blunt ends: soft, not spiky
    s.use_close_tip = True
    s.kink = "NO"                                    # v4: smooth strands (no wave kink)
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
        top = _smooth(TOP_BLEND[0], TOP_BLEND[1], h) * (1 - _smooth(120, 160, phi))   # v6e: a wider blend
        back = _smooth(110, 160, phi) * (1 - top)
        length = (SIDE_LEN * (1 - top - back) + TOP_LEN * top + BACK_LEN * back) * rnd.uniform(0.85, 1.15)
        # v5 (Codex 010): a feathered hairline. Strands near the edge of the hair region are shorter, so the
        # hairline fades into the skin instead of ending in a hard "helmet" line
        edge = scalp_weight(root, eye, head)
        length *= 0.6 + 0.4 * _smooth(0.1, 0.5, edge)                          # v5b: a gentler feather
        if edge < 0.45:                            # v5c: break up the hairline (no ruled edge): uneven lengths
            length *= rnd.uniform(0.45, 1.0)
        layer = rnd.random()                       # 0 = lies on the scalp, 1 = outer layer (depth, not a shell)
        length *= 1 - 0.55 * _smooth(-0.01, 0.06, rel.y) * top     # v4: taper over the crown (no "shelf" at the back)
        side_flow = Vector((0.0, 0.5, -1.0)).normalized()          # sides: combed down and back, flat
        if top > 0.3 and rel.x < PART_X:                            # below the part: combed to his right, down
            top_flow = Vector((-0.5, 0.45, -0.25)).normalized()
        else:
            top_flow = sweep
        flow = (top_flow * top + side_flow * (1 - top)).normalized()
        front = _smooth(-0.02, -0.09, rel.y) * top                 # near the front hairline (rel.y < 0 = front)
        lift = FRONT_LIFT * front + 0.12 * top * (1 - front) + 0.05 * (1 - top)
        d = (n * lift + flow * (1 - lift)).normalized()
        jitter = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-0.5, 0.5))) * (0.05 if edge >= 0.45 else 0.22)
        phase, amp = rnd.uniform(0, 2 * math.pi), WAVE * rnd.uniform(0.5, 1.0)
        d = (d + jitter).normalized()
        nk = len(part.hair_keys)
        seg = length / (nk - 1)
        p = root.copy()
        pts = [root]
        for k in range(1, nk):
            side = d.cross(n)                         # one smooth S-wave per strand (no random zigzag)
            wave = (side.normalized() if side.length > 1e-6 else Vector()) * amp * math.sin(phase + 1.3 * k)
            d = (d + flow * 0.45 + wave + Vector((0, 0, -1)) * (0.22 + 0.15 * (1 - top))).normalized()
            p = p + d * seg
            rp = p - head                             # forehead guard: nothing droops below the front hairline
            if abs(math.degrees(math.atan2(rp.x, -rp.y))) < 55 and p.z - eye.z < FRINGE_Z:
                p.z = eye.z + FRINGE_Z
                d.z = abs(d.z) + 0.2
                d.normalize()
            near, nn, _, _ = bvh.find_nearest(p)
            if near is not None:
                # v5 (Codex 010): clearance by position ALONG the strand (t), not by key index: the old
                # 0.0022 + 0.0012*k forced the top tips >= 13 mm off the skull, a puffed helmet shell.
                # Each strand gets a layer: inner strands lie close, outer ones a few mm out (volume with depth).
                t = k / (nk - 1)
                bulge = 0.35 + 0.65 * math.sin(math.pi * min(1.0, t * 1.2))   # some lift kept to the tip
                # a real side-part cut sits ~1-2 cm thick on top: outer layers up to ~15 mm, inner ones low
                off = 0.0004 + (0.003 + 0.016 * layer) * bulge * (0.2 + 0.8 * top)   # v5b: a bit more lift
                off_max = off + 0.004 + 0.01 * front * t                                  # quiff room
                dist = (p - near).dot(nn)
                if dist < off:
                    p = near + nn * off
                elif dist > off_max:
                    p = near + nn * off_max
                    d = (p - pts[-1]).normalized()      # carry on along the head, not outward
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


def follow_face(body, ob, used, min_move=0.0001):
    """Give `ob` (a mesh built from the body vertices `used`, in order) the body's face shapes that move those
    vertices (brows, forehead), driven by the body's sliders, so it moves with the skin on expressions."""
    import sys as _sys
    import os as _os
    _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
    from max_expressions import FACE_UNITS
    keys = body.data.shape_keys.key_blocks
    basis = keys[0]
    moved = []
    for kb in keys:
        if kb.name not in FACE_UNITS:
            continue
        delta = [Vector(kb.data[v].co) - Vector(basis.data[v].co) for v in used]
        if max(d.length for d in delta) >= min_move:
            moved.append((kb.name, delta))
    if not moved:
        return []
    if not ob.data.shape_keys:
        ob.shape_key_add(name="Basis", from_mix=False)
    for name, delta in moved:
        sk = ob.shape_key_add(name=name, from_mix=False)
        for i, d in enumerate(delta):
            sk.data[i].co = Vector(ob.data.vertices[i].co) + d
        drv = sk.driver_add("value").driver
        drv.type = "AVERAGE"
        var = drv.variables.new()
        var.targets[0].id_type = "KEY"
        var.targets[0].id = body.data.shape_keys
        var.targets[0].data_path = f'key_blocks["{name}"].value'
    return [m[0] for m in moved]


def copy_skin_weights(rig, body, ob, used):
    """Give `ob` (built from body vertices `used`, in that order) the body's own bone weights, so it bends
    exactly like the skin under it. v6c: a rigid head=1.0 weight let the hair lift off the forehead when the
    neck bent (swallow pose): the forehead skin also follows neck01-03 and the oculi bones."""
    bones = {b.name for b in rig.data.bones}
    names = {g.index: g.name for g in body.vertex_groups if g.name in bones}
    groups = {}
    for i, v in enumerate(used):
        for g in body.data.vertices[v].groups:
            if g.group in names and g.weight > 0:
                n = names[g.group]
                if n not in groups:
                    groups[n] = ob.vertex_groups.new(name=n)
                groups[n].add([i], g.weight, "REPLACE")
    return sorted(groups)


def build_scalp_cap(rig, body, co, polys, weights):
    """Dark scalp-toned cap 0.2 mm over the scalp, skinned like the body under it (no bright skin between strands).
    v5 (Codex 010): it sat 1.5 mm out and read as a dark shell rim behind the ear; now it's closer, inset
    further from the hairline, and closer to a scalp colour."""
    keep = {i for i, w in weights.items() if w > 0.85}    # inset from the hairline: its edge never shows
    faces = [f for f in polys if all(v in keep for v in f)]
    used = sorted({v for f in faces for v in f})
    remap = {v: i for i, v in enumerate(used)}
    me = bpy.data.meshes.new("Max.scalp")
    me.from_pydata([Vector(co[v]) for v in used], [], [[remap[v] for v in f] for f in faces])
    me.update()
    for v in me.vertices:
        v.co += v.normal * 0.0002
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new("Max.scalp", me)
    for c in body.users_collection:
        c.objects.link(ob)
    ob.parent = rig
    copy_skin_weights(rig, body, ob, used)      # the body's own weights (a rigid head bone lifted off)
    arm = ob.modifiers.new("Armature", "ARMATURE")
    arm.object = rig
    follow_face(body, ob, used)                # the cap moves with the brows (else it showed at the hairline)
    mat = bpy.data.materials.new("Max_scalp")
    mat.use_nodes = True
    b = mat.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.075, 0.048, 0.034, 1)       # a shadowed scalp under dark hair
    b.inputs["Roughness"].default_value = 0.7
    mat.diffuse_color = (0.022, 0.013, 0.008, 1)
    me.materials.append(mat)
    return ob
