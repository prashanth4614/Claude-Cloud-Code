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
SCALP_TINT = 0.85                 # how far the skin under the hair is darkened toward a shadowed scalp
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
    from mathutils import Vector
    scalp = np.array([max_hair.scalp_weight(Vector(c), eye, head, fade=True) for c in co])   # hair + side fade
    me = body.data
    for name, vals in (("zone_oil", oil), ("zone_lip", lip), ("zone_red", red), ("zone_scalp", scalp)):
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
    # the scalp under the hair is darker (roots, hair shadow): no warm skin band at the hairline, and the
    # short sides read as a soft fade instead of a shaved line
    sc = nt.nodes.new("ShaderNodeAttribute")
    sc.attribute_name, sc.attribute_type = "zone_scalp", "GEOMETRY"
    tint = nt.nodes.new("ShaderNodeMix")
    tint.data_type = "RGBA"
    famt = nt.nodes.new("ShaderNodeMath")
    famt.operation = "MULTIPLY"
    famt.inputs[1].default_value = SCALP_TINT
    nt.links.new(sc.outputs["Fac"], famt.inputs[0])
    nt.links.new(famt.outputs[0], tint.inputs["Factor"])
    nt.links.new(flush.outputs["Result"], tint.inputs["A"])
    tint.inputs["B"].default_value = (0.09, 0.062, 0.05, 1.0)
    nt.links.new(tint.outputs["Result"], bsdf.inputs["Base Color"])


def upgrade_eyes(mat):
    """A wet cornea: a clear glossy coat over the iris and sclera, a touch of softness in the sclera."""
    b = next((n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if not b:
        return
    for k, v in (("Roughness", 0.35), ("Coat Weight", 1.0), ("Coat Roughness", 0.02), ("Coat IOR", 1.376),
                 ("Subsurface Weight", 0.08), ("Specular IOR Level", 0.5)):
        if k in b.inputs:
            b.inputs[k].default_value = v
    # v6b: the irises read orange-red; a deeper, cooler brown (white sclera is unaffected by saturation)
    if b.inputs["Base Color"].is_linked and "max_look_iris" not in mat.node_tree.nodes:
        link = b.inputs["Base Color"].links[0]
        hsv = mat.node_tree.nodes.new("ShaderNodeHueSaturation")
        hsv.name = "max_look_iris"
        hsv.inputs["Hue"].default_value = 0.52     # a touch toward yellow: brown, not red
        hsv.inputs["Saturation"].default_value = 0.88
        hsv.inputs["Value"].default_value = 0.78    # deeper
        mat.node_tree.links.new(link.from_socket, hsv.inputs["Color"])
        mat.node_tree.links.new(hsv.outputs["Color"], b.inputs["Base Color"])


def upgrade_lashes(mat):
    """v6b: the MPFB lashes read long, thick and spiky (a mascara look): thin them by lowering their opacity."""
    b = next((n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if not b or "max_look_lash" in mat.node_tree.nodes:
        return
    alpha = b.inputs["Alpha"]
    m = mat.node_tree.nodes.new("ShaderNodeMath")
    m.name, m.operation = "max_look_lash", "MULTIPLY"
    m.inputs[1].default_value = LASH_OPACITY
    if alpha.is_linked:
        mat.node_tree.links.new(alpha.links[0].from_socket, m.inputs[0])
    else:
        m.inputs[0].default_value = alpha.default_value
    mat.node_tree.links.new(m.outputs[0], alpha)


def upgrade_teeth(mat):
    b = next((n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if b and "max_look_enamel" not in mat.node_tree.nodes:      # tint the texture to a warm enamel
        link = b.inputs["Base Color"].links[0] if b.inputs["Base Color"].is_linked else None
        if link:
            mix = mat.node_tree.nodes.new("ShaderNodeMix")
            mix.name = "max_look_enamel"
            mix.data_type, mix.blend_type = "RGBA", "MULTIPLY"
            mix.inputs["Factor"].default_value = 1.0
            mix.inputs["B"].default_value = ENAMEL
            mat.node_tree.links.new(link.from_socket, mix.inputs["A"])
            mat.node_tree.links.new(mix.outputs["Result"], b.inputs["Base Color"])
    if b:
        for k, v in (("Roughness", 0.25), ("Subsurface Weight", 0.15), ("Coat Weight", 0.15), ("Coat Roughness", 0.1)):
            if k in b.inputs:
                b.inputs[k].default_value = v


UPPER_TEETH_SHIFT = (0.0, -0.0006, -0.0024)   # m: down 2.4 mm, forward 0.6 mm (front is -y)
ENAMEL = (1.15, 1.08, 0.95, 1.0)               # warm and brighter (v6b: the teeth read grey-blue in shadow)
LASH_OPACITY = 0.75                            # 0.5 made the eyes lose definition


def upgrade_teeth_geometry(teeth):
    """The upper row sat so high that an open mouth showed only the lower teeth (it read as "gappy").
    Move the upper row (the vertices that don't move with jawOpen) down and slightly forward, in the
    basis and in every shape key."""
    if teeth.get("max_look_teeth"):
        return 0
    keys = teeth.data.shape_keys.key_blocks if teeth.data.shape_keys else None
    if not keys or "jawOpen" not in keys:
        return 0
    basis, jaw = keys[0], keys["jawOpen"]
    upper = [i for i in range(len(basis.data)) if (Vector(jaw.data[i].co) - Vector(basis.data[i].co)).length < 1e-5]
    off = Vector(UPPER_TEETH_SHIFT)
    for kb in keys:
        for i in upper:
            kb.data[i].co = Vector(kb.data[i].co) + off
    for i in upper:
        teeth.data.vertices[i].co = Vector(teeth.data.vertices[i].co) + off
    teeth["max_look_teeth"] = True
    return len(upper)


def add_throat_rise(rig, body):
    """A "throatRise" shape key on the body: the larynx (front of the neck, found from the neck-bone weights
    and the front-most skin, per Codex 011: not the bone midpoint, which lands on the nape) rises ~4 mm
    and pushes ~1 mm forward, with a soft 2 cm falloff (the neck mesh is coarse). Used by the swallow expression."""
    import numpy as np
    keys = body.data.shape_keys.key_blocks
    if "throatRise" in keys:
        return 0
    names = {g.index: g.name for g in body.vertex_groups}
    neck = {i for i, n in names.items() if n in ("neck01", "neck02", "neck03")}
    basis = keys[0]
    co = np.array([tuple(basis.data[i].co) for i in range(len(basis.data))])
    w = np.array([sum(g.weight for g in v.groups if g.group in neck) for v in body.data.vertices])
    front = (w > 0.3) & (np.abs(co[:, 0]) < 0.03)
    if not front.any():
        return 0
    band = front & (co[:, 2] > np.percentile(co[front, 2], 35)) & (co[:, 2] < np.percentile(co[front, 2], 75))
    centre = co[band][np.argmin(co[band][:, 1])]          # the front-most point (front is -y): the larynx
    d = np.linalg.norm((co - centre) * [1.0, 1.0, 0.8], axis=1)
    fall = np.exp(-(d / 0.022) ** 2) * (w > 0.1)
    sk = body.shape_key_add(name="throatRise", from_mix=False)
    delta = np.outer(fall, [0.0, -0.0012, 0.004])
    sk.data.foreach_set("co", (co + delta).astype(np.float32).ravel())
    sk.value = 0.0
    return int((fall > 0.5).sum())


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


# Eye wetness: Codex 011a patch (applied and verified by Claude): a tear meniscus along each lower lid
# and a pink caruncle at each inner corner, following the body's armature and face shapes.
LID_DIST = 2.5                   # mm: lid vertices this close to the eyeball surface (Codex 011a)


def add_eye_wetness(rig, body):
    """Build on the unposed asset. Geometry uses neutral phenotype coordinates."""
    import heapq
    import math
    import os
    import sys

    import bpy
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from max_expressions import FACE_UNITS
    from max_hair import follow_face

    eyes = next(o for o in rig.children_recursive
                if o.type == "MESH" and "high-poly" in o.name)
    arms = [m for m in body.modifiers if m.type == "ARMATURE"]
    if len(arms) != 1 or arms[0].object != rig:
        raise ValueError("Expected one body Armature modifier targeting rig")

    scale = body.matrix_world.to_scale()
    if (min(scale) <= 0 or max(scale) / min(scale) > 1.0001
            or body.matrix_world.determinant() <= 0):
        raise ValueError("Wetness requires uniform, positive body scale")
    mm = 0.001 / (bpy.context.scene.unit_settings.scale_length * scale.x)

    def neutral(ob):
        keys = ob.data.shape_keys
        if not keys:
            return [v.co.copy() for v in ob.data.vertices]
        if not keys.use_relative:
            raise ValueError("Expected relative shape keys")
        blocks = keys.key_blocks
        co = [p.co.copy() for p in blocks[0].data]
        for kb in list(blocks)[1:]:
            if kb.name in FACE_UNITS or kb.mute or not kb.value:
                continue
            if kb.vertex_group:
                raise ValueError("Masked phenotype keys need explicit evaluation")
            for i, p in enumerate(kb.data):
                co[i] += (p.co - kb.relative_key.data[i].co) * kb.value
        return co

    co = neutral(body)
    transform = body.matrix_world.inverted() @ eyes.matrix_world
    eco = [transform @ p for p in neutral(eyes)]
    epolys = [tuple(p.vertices) for p in eyes.data.polygons]
    surface = BVHTree.FromPolygons(eco, epolys)

    tmp = bpy.data.meshes.new("_wetness_normals")
    tmp.from_pydata(co, [], [tuple(p.vertices) for p in body.data.polygons])
    tmp.update()
    normals = [v.normal.copy() for v in tmp.vertices]
    bpy.data.meshes.remove(tmp)

    adjacency = [[] for _ in co]
    for edge in body.data.edges:
        a, b = edge.vertices
        adjacency[a].append(b)
        adjacency[b].append(a)

    def material(name, color, roughness, transmission):
        mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        nodes.clear()
        out = nodes.new("ShaderNodeOutputMaterial")
        bsdf = nodes.new("ShaderNodeBsdfPrincipled")
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["IOR"].default_value = 1.336
        bsdf.inputs["Transmission Weight"].default_value = transmission
        mat.node_tree.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
        return mat

    water = material("Max_tear_water", (1, 1, 1, 1), 0.03, 1.0)
    tissue = material("Max_caruncle", (0.48, 0.16, 0.14, 1), 0.2, 0.0)

    def make(name, positions, faces, used, mat, root=None, blend=1.0):
        old = bpy.data.objects.get(name)
        if old:
            old_mesh = old.data
            bpy.data.objects.remove(old, do_unlink=True)
            if old_mesh.users == 0:
                bpy.data.meshes.remove(old_mesh)

        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(positions, [], faces)
        mesh.update()
        ob = bpy.data.objects.new(name, mesh)
        body.users_collection[0].objects.link(ob)
        ob.parent = body.parent
        ob.parent_type = body.parent_type
        ob.parent_bone = body.parent_bone
        ob.matrix_parent_inverse = body.matrix_parent_inverse.copy()
        ob.matrix_basis = body.matrix_basis.copy()
        mesh.materials.append(mat)
        for p in mesh.polygons:
            p.use_smooth = True

        # Exact source weights; corner patch uses an affine blend with its root.
        groups = {g.index: ob.vertex_groups.new(name=g.name)
                  for g in body.vertex_groups}
        for j, source in enumerate(used):
            weights = {}
            contributions = [(source, blend)]
            if root is not None:
                contributions.append((root, 1.0 - blend))
            for index, factor in contributions:
                for g in body.data.vertices[index].groups:
                    weights[g.group] = weights.get(g.group, 0.0) + factor * g.weight
            for index, weight in weights.items():
                if weight > 0:
                    groups[index].add([j], weight, "REPLACE")

        # Zero threshold retains every FACE_UNIT driver, including tiny motion.
        follow_face(body, ob, used, min_move=0.0)
        if root is not None:
            source_keys = body.data.shape_keys.key_blocks
            basis = source_keys[0]
            for kb in list(mesh.shape_keys.key_blocks)[1:]:
                source = source_keys[kb.name]
                dr = source.data[root].co - basis.data[root].co
                for j, index in enumerate(used):
                    delta = source.data[index].co - basis.data[index].co
                    kb.data[j].co = (mesh.vertices[j].co
                                     + blend * delta + (1.0 - blend) * dr)

        arm = ob.modifiers.new("Armature", "ARMATURE")
        arm.object = rig
        for prop in ("use_deform_preserve_volume", "use_vertex_groups",
                     "use_bone_envelopes", "vertex_group", "invert_vertex_group"):
            setattr(arm, prop, getattr(arms[0], prop))

        sub = ob.modifiers.new("Smooth wet surface", "SUBSURF")
        sub.levels = sub.render_levels = 2

        # Collision guard after deformation/subdivision; leaves outside points alone.
        guard = ob.modifiers.new("Keep outside eyeball", "SHRINKWRAP")
        guard.target = eyes
        guard.wrap_method = "NEAREST_SURFACEPOINT"
        guard.wrap_mode = "OUTSIDE_SURFACE"
        guard.offset = 0.03 * mm
        ob["max_eye_wetness"] = True
        return ob

    mid = (min(p.x for p in eco) + max(p.x for p in eco)) / 2
    plans = []
    for side in (-1, 1):
        globe = [p for p in eco if (p.x - mid) * side > 0]
        if not globe:
            raise ValueError("Cannot separate the two eyeballs")
        lo = Vector(tuple(min(p[k] for p in globe) for k in range(3)))
        hi = Vector(tuple(max(p[k] for p in globe) for k in range(3)))
        centre, radius = (lo + hi) / 2, (hi - lo) / 2

        candidates = {}
        for i, p in enumerate(co):
            if not (abs(p.x - centre.x) < radius.x + 1.5 * mm
                    and centre.z - radius.z < p.z < centre.z + 0.25 * radius.z
                    and p.y < centre.y - 0.15 * radius.y
                    and normals[i].y < 0.4):
                continue
            hit, normal, _, distance = surface.find_nearest(p)
            if hit is not None and distance < LID_DIST * mm and normal.y < -0.15:
                candidates[i] = (hit, normal, distance)

        # the lid band's largest connected stretch (an isolated corner vertex broke the path on one side
        # or the other: Claude, after testing); its two x-extremes, near the eye's mid-height, are the ends
        comps, seen = [], set()
        for s0 in candidates:
            if s0 in seen:
                continue
            comp, stack = [], [s0]
            seen.add(s0)
            while stack:
                i = stack.pop()
                comp.append(i)
                for j in adjacency[i]:
                    if j in candidates and j not in seen:
                        seen.add(j)
                        stack.append(j)
            comps.append(comp)
        band = max(comps, key=lambda c: max(co[i].x for i in c) - min(co[i].x for i in c))
        corners = [i for i in band if abs(co[i].z - centre.z) < 0.45 * radius.z] or band
        start = min(corners, key=lambda i: co[i].x)
        end = max(corners, key=lambda i: co[i].x)
        if co[end].x - co[start].x < 1.2 * radius.x:
            raise ValueError(f"Insufficient lid span: side {side}")

        # Connected path, strongly favouring vertices nearest the globe.
        distances, previous, queue = {start: 0.0}, {}, [(0.0, start)]
        while queue:
            distance, i = heapq.heappop(queue)
            if distance != distances[i]:
                continue
            if i == end:
                break
            for j in adjacency[i]:
                if j not in candidates:
                    continue
                gap = (candidates[i][2] + candidates[j][2]) / (0.6 * mm)
                cost = (co[j] - co[i]).length * (1.0 + gap * gap)
                trial = distance + cost
                if trial < distances.get(j, float("inf")):
                    distances[j], previous[j] = trial, i
                    heapq.heappush(queue, (trial, j))

        if end not in distances:
            far = max(distances, key=lambda i: (co[i] - co[start]).length)
            raise ValueError(f"Disconnected lid band: side {side}: {len(candidates)} candidates, "
                             f"{len(distances)} reachable from the inner/outer corner; start x {co[start].x:.4f} "
                             f"end x {co[end].x:.4f}, reached x {co[far].x:.4f}; eye centre x {centre.x:.4f} r {radius.x:.4f}")
        path = [end]
        while path[-1] != start:
            path.append(previous[path[-1]])
        path.reverse()
        if len(path) < 5 or min(co[i].z for i in path) > centre.z - mm:
            raise ValueError(f"Ambiguous lower lid: side {side}")
        plans.append((side, path, candidates))

    result = []
    for side, path, candidates in plans:
        positions, used, faces = [], [], []
        count, ring = len(path), 8
        for j, source in enumerate(path):
            hit, normal, _ = candidates[source]
            normal = normal.normalized()
            tangent = (co[path[min(j + 1, count - 1)]]
                       - co[path[max(j - 1, 0)]]).normalized()
            across = tangent.cross(normal).normalized()
            taper = 0.1 + 0.9 * math.sin(math.pi * j / (count - 1))
            centre = hit + normal * (0.12 * mm)
            for k in range(ring):
                angle = 2 * math.pi * k / ring
                positions.append(centre
                                 + across * (0.20 * mm * taper * math.cos(angle))
                                 + normal * (0.06 * mm * taper * math.sin(angle)))   # v6b: 2x (0.2 mm didn't show)
                used.append(source)
        for j in range(count - 1):
            for k in range(ring):
                a, b = j * ring + k, j * ring + (k + 1) % ring
                faces.append((a, b, b + ring, a + ring))
        faces.extend([tuple(reversed(range(ring))),
                      tuple((count - 1) * ring + k for k in range(ring))])
        result.append(make(f"Max.tear.{side}", positions, faces, used, water))

        root = min((path[0], path[-1]), key=lambda i: abs(co[i].x - mid))
        patch = [tuple(p.vertices) for p in body.data.polygons
                 if root in p.vertices]
        used = sorted({i for face in patch for i in face})
        if not patch:
            raise ValueError("Inner corner has no incident faces")
        extent = max((co[i] - co[root]).length for i in used)
        blend = min(1.0, 0.85 * mm / max(extent, 1e-12))
        positions = []
        for i in used:
            p = co[root] + blend * (co[i] - co[root])
            r = min(1.0, (p - co[root]).length / (0.85 * mm))
            p += normals[i] * ((0.05 + 0.12 * (1.0 - r * r)) * mm)
            positions.append(p)
        remap = {source: j for j, source in enumerate(used)}
        faces = [tuple(remap[i] for i in face) for face in patch]
        result.append(make(f"Max.caruncle.{side}", positions, faces, used,
                           tissue, root=root, blend=blend))
    return result


# Armpit correctives: Codex 012 patch (applied and verified by Claude). Shape keys sampled from the
# real skinning, driven by the upper-arm angle: crisp folds and less upward drag when an arm lifts.
PIT_ONSET, PIT_FULL = 40, 85   # upper-arm angle from straight down (deg): corrective starts / is full


def add_shirt_correctives(rig, ob, shirt, positions,
                         shoulders, metres, transform):
    import math
    from mathutils import Matrix, Vector
    from build_max import aim_bone

    if ob.get("max_shirt_correctives") == 1:
        return
    if not any(m.type == "ARMATURE" and m.object == rig
               and m.show_viewport for m in ob.modifiers):
        raise ValueError("Expected active Max armature modifier")

    if not ob.data.shape_keys:
        ob.shape_key_add(name="Basis", from_mix=False)
    keys = ob.data.shape_keys
    if not keys.use_relative:
        raise ValueError("Expected relative shirt shape keys")

    names = ["max_pit_L", "max_pit_R"]
    # Safe retry after an interrupted build.
    for name in names + ["__pit_probe"]:
        old = keys.key_blocks.get(name)
        if old:
            ob.shape_key_remove(old)

    basis = keys.reference_key
    probe = ob.shape_key_add(name="__pit_probe", from_mix=False)
    saved_pose = [(p, p.matrix_basis.copy()) for p in rig.pose.bones]
    saved_mods = [(m, m.show_viewport) for m in ob.modifiers]
    saved_position = rig.data.pose_position
    to_local = transform.to_3x3().inverted() * (1.0 / metres)   # mathutils Matrix has no "/"
    centre_x = sum(p.x for p in shoulders.values()) / 2
    made = []
    eps = 0.001                       # one millimetre in rig/metre coordinates

    def evaluated_positions():
        bpy.context.view_layer.update()
        ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh = ev.to_mesh()
        try:
            if len(mesh.vertices) != len(positions):
                raise ValueError("Probe requires unchanged vertex indices")
            return [transform @ v.co * metres for v in mesh.vertices]
        finally:
            ev.to_mesh_clear()

    try:
        rig.data.pose_position = "POSE"
        # Probe only skinning; subdivision must not mix neighbouring vertices.
        for m, _ in saved_mods:
            if m.type != "ARMATURE":
                m.show_viewport = False

        for side, name in zip(("L", "R"), names):
            for p, _ in saved_pose:
                p.matrix_basis.identity()
            bpy.context.view_layer.update()

            shoulder = shoulders[side]
            sign = 1 if shoulder.x > centre_x else -1
            a = math.radians(70)
            direction = rig.matrix_world.to_3x3() @ Vector(
                (sign * math.sin(a), -0.25, -math.cos(a)))
            for bone in ("upperarm01", "upperarm02"):
                aim_bone(rig, f"{bone}.{side}", direction)

            probe.value = 0
            base = evaluated_positions()
            columns = []
            for axis in range(3):
                step = Vector((0, 0, 0))
                step[axis] = eps
                local_step = to_local @ step
                for i in shirt:
                    probe.data[i].co = basis.data[i].co + local_step
                probe.value = 1
                moved = evaluated_positions()
                columns.append([(q - p) / eps
                                for p, q in zip(base, moved)])
            probe.value = 0

            pit = shoulder + Vector((-sign * 0.03, 0, -0.12))
            weights = {}
            for i in shirt:
                p = positions[i]
                if sign * (p.x - centre_x) <= 0:
                    continue
                d = p - pit
                w = 1.0
                for component, width in zip(d, (0.10, 0.18, 0.13)):
                    w *= max(0.0, 1.0 - (component / width) ** 2) ** 2
                # Protect shoulder cap and sleeve.
                w *= min(1.0, max(0.0,
                    (shoulder.z - 0.045 - p.z) / 0.04))
                if w > 1e-4:
                    weights[i] = w
            if not weights:
                raise ValueError(f"No armpit vertices: {side}")

            centre = sum((base[i] * w for i, w in weights.items()),
                         Vector()) / sum(weights.values())
            key = ob.shape_key_add(name=name, from_mix=False)
            key.relative_key = basis
            key.value = 0
            made.append((side, key))

            for i, w in weights.items():
                q = base[i]
                # Remove part of the skin-driven lift; cap at 22 mm.
                drop = max(-0.022, min(0.008,
                    -0.35 * (q.z - positions[i].z)))
                u = q.z + drop - centre.z - (
                    0.55 * sign * (q.x - centre.x))
                relief = 0.006 * sum(
                    math.exp(-((u - offset) / 0.012) ** 2)
                    for offset in (-0.04, 0.0, 0.04))
                outward = Vector((q.x - centre_x,
                                   q.y - shoulder.y, 0)).normalized()
                desired = w * (outward * relief + Vector((0, 0, drop)))
                jacobian = Matrix(
                    [column[i] for column in columns]).transposed()
                if abs(jacobian.determinant()) < 1e-8:
                    raise ValueError(f"Singular skinning at vertex {i}")
                key.data[i].co = basis.data[i].co + (
                    to_local @ (jacobian.inverted() @ desired))
    finally:
        probe.value = 0
        ob.shape_key_remove(probe)
        for p, matrix in saved_pose:
            p.matrix_basis = matrix
        for m, enabled in saved_mods:
            m.show_viewport = enabled
        rig.data.pose_position = saved_position
        bpy.context.view_layer.update()

    torso = max(
        (b for b in rig.data.bones if b.name.startswith("spine")),
        key=lambda b: (b.head_local.z + b.tail_local.z) / 2)
    up_sign = 1 if torso.tail_local.z > torso.head_local.z else -1

    for side, key in made:
        driver = key.driver_add("value").driver
        driver.type = "SCRIPTED"
        # Evaluated world quaternions: independent of pose rotation mode,
        # armature heading, and upper-arm axial twist.
        for prefix, bone in (("a", f"upperarm01.{side}"),
                             ("t", torso.name)):
            for component in "wxyz":
                v = driver.variables.new()
                v.name = prefix + component
                v.type = "TRANSFORMS"
                target = v.targets[0]
                target.id = rig
                target.bone_target = bone
                target.transform_space = "WORLD_SPACE"
                target.rotation_mode = "QUATERNION"
                target.transform_type = "ROT_" + component.upper()
        # Dot product of each bone's world +Y axis.
        dot = (
            "4*(ax*ay-aw*az)*(tx*ty-tw*tz)"
            "+(1-2*(ax*ax+az*az))*(1-2*(tx*tx+tz*tz))"
            "+4*(ay*az+aw*ax)*(ty*tz+tw*tx)"
        )
        onset = math.cos(math.radians(PIT_ONSET))   # 0 in the rest A-pose (about 35 deg)
        span = onset - math.cos(math.radians(PIT_FULL))
        driver.expression = (
            f"min(1,max(0,({up_sign}*({dot})+{onset:.6f})/"
            f"{span:.6f}))")

    ob.data.update()
    ob["max_shirt_correctives"] = 1


# Shirt fabric and folds: Codex 011b patch (applied and verified by Claude).
def upgrade_shirt(rig):
    """Shirt-only shading; rest-space folds follow skinning, without simulation."""
    import math
    from mathutils import Vector

    ob = next(o for o in rig.children_recursive
              if o.type == "MESH" and "male_casualsuit06" in o.name)
    shaded = ob.get("max_shirt_upgrade") == 1

    unit = bpy.context.scene.unit_settings.scale_length
    scales = [v.length for v in rig.matrix_world.to_3x3().col]
    if max(scales) - min(scales) > 1e-5:
        raise ValueError("upgrade_shirt requires uniform armature scale")
    metres = scales[0] * unit

    # Mesh and bone coordinates in the same REST-space frame, measured in metres.
    transform = rig.matrix_world.inverted() @ ob.matrix_world
    positions = [transform @ v.co * metres for v in ob.data.vertices]
    shoulders = {
        side: rig.data.bones[f"upperarm01.{side}"].head_local * metres
        for side in ("L", "R")
    }
    spine = [p * metres for b in rig.data.bones
             if b.name.startswith("spine")
             for p in (b.head_local, b.tail_local)]
    if not spine:
        raise ValueError("Missing spine landmarks")
    shoulder_z = sum(p.z for p in shoulders.values()) / 2
    centre_x = sum(p.x for p in shoulders.values()) / 2

    # Tee and jeans share an object/material. Isolate the tee by connectivity.
    parent = list(range(len(positions)))

    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for edge in ob.data.edges:
        a, b = edge.vertices
        parent[root(a)] = root(b)
    islands = {}
    for i in range(len(positions)):
        islands.setdefault(root(i), []).append(i)

    chest = Vector((centre_x,
                    sum(p.y for p in shoulders.values()) / 2 - 0.10,
                    shoulder_z - 0.13))
    seed = min(range(len(positions)),
               key=lambda i: (positions[i] - chest).length_squared)
    shirt = set(islands[root(seed)])
    low = min(positions[i].z for i in shirt)
    high = max(positions[i].z for i in shirt)
    if low < shoulder_z - 0.70 or high < shoulder_z - 0.08:
        raise ValueError("Cannot safely isolate tee island; split shirt faces first")

    faces = [p.index for p in ob.data.polygons
             if all(i in shirt for i in p.vertices)]
    material_ids = {ob.data.polygons[i].material_index for i in faces}
    for index in material_ids:
        mat = ob.data.materials[index]
        if not mat or not mat.use_nodes or not any(
                n.type == "BSDF_PRINCIPLED" for n in mat.node_tree.nodes):
            raise ValueError("Expected direct Principled shirt material")

    # Isolate mesh edits and copied shirt materials from every other user.
    if ob.data.users > 1:
        ob.data = ob.data.copy()
    mesh = ob.data
    add_shirt_correctives(
        rig, ob, shirt, positions, shoulders, metres, transform)
    if shaded:
        return

    belly_z = max(low + 0.09, min(p.z for p in spine) + 0.08)
    belly_y = sum(p.y for p in spine) / len(spine)
    phases, amplitudes = [], []

    def envelope(d, widths):
        return math.exp(-sum((d[k] / widths[k]) ** 2 for k in range(3)))

    for i, p in enumerate(positions):
        side = min(shoulders, key=lambda s: abs(p.x - shoulders[s].x))
        shoulder = shoulders[side]
        sign = 1 if shoulder.x > centre_x else -1
        d = p - shoulder
        pit = shoulder + Vector((-sign * 0.025, 0, -0.065))
        dp = p - pit
        db = p - Vector((centre_x, belly_y, belly_z))

        # Smooth phases are interpolated; sine is evaluated per shading sample.
        phases.extend((
            math.tau * ((d.z + 0.35 * sign * d.x) / 0.042
                        + 0.5 * (d.x / 0.12) ** 2),
            math.tau * ((dp.z - 0.65 * sign * dp.x) / 0.035
                        + 0.18 * (dp.x / 0.10) ** 2),
            math.tau * (db.z / 0.13 + 0.22 * (db.x / 0.18) ** 2),
        ))
        amplitudes.extend((
            0.0010 * envelope(d, (0.085, 0.16, 0.055)),     # v6b: ~1.8x (folds read "smooth CG")
            0.0016 * envelope(dp, (0.075, 0.16, 0.065)),
            0.0021 * envelope(db, (0.19, 0.20, 0.115)),
        ) if i in shirt else (0, 0, 0))

    for name, values in (
        ("max_shirt_rest", [c for p in positions for c in p]),
        ("max_shirt_phase", phases),
        ("max_shirt_amp", amplitudes),
    ):
        attr = mesh.attributes.get(name)
        if attr:
            mesh.attributes.remove(attr)
        attr = mesh.attributes.new(name, "FLOAT_VECTOR", "POINT")
        attr.data.foreach_set("vector", values)

    replacements = {}
    for index in material_ids:
        mat = mesh.materials[index].copy()
        mat.name += "_shirt_fabric"
        nt = mat.node_tree
        nodes, links = nt.nodes, nt.links
        bsdf = next(n for n in nodes if n.type == "BSDF_PRINCIPLED")
        previous_normal = (
            bsdf.inputs["Normal"].links[0].from_socket
            if bsdf.inputs["Normal"].is_linked else None
        )

        def math_node(operation, *values):
            node = nodes.new("ShaderNodeMath")
            node.operation = operation
            for j, value in enumerate(values):
                if isinstance(value, (int, float)):
                    node.inputs[j].default_value = value
                else:
                    links.new(value, node.inputs[j])
            return node.outputs[0]

        def channels(name):
            attr = nodes.new("ShaderNodeAttribute")
            attr.attribute_type = "GEOMETRY"
            attr.attribute_name = name
            split = nodes.new("ShaderNodeSeparateXYZ")
            links.new(attr.outputs["Vector"], split.inputs[0])
            return tuple(split.outputs)

        def constant(name, value):
            socket = bsdf.inputs.get(name)
            if socket is not None:
                for link in list(socket.links):
                    links.remove(link)
                socket.default_value = value

        for name, value in (
            ("Roughness", 0.65), ("Sheen Weight", 0.08),   # v6b: less sheen keeps the teal rich
            ("Sheen Roughness", 0.70), ("Coat Weight", 0.0),
            ("Metallic", 0.0),
        ):
            constant(name, value)

        phase = channels("max_shirt_phase")
        amp = channels("max_shirt_amp")
        terms = [math_node("MULTIPLY", math_node("SINE", ph), weight)
                 for ph, weight in zip(phase, amp)]
        height = math_node("ADD", math_node("ADD", terms[0], terms[1]),
                           terms[2])

        folds = nodes.new("ShaderNodeBump")
        folds.label = "Shoulder / armpit / belly: metres"
        folds.inputs["Strength"].default_value = 1.0
        folds.inputs["Distance"].default_value = 1.0 / unit
        links.new(height, folds.inputs["Height"])
        if previous_normal is not None:
            links.new(previous_normal, folds.inputs["Normal"])

        # Fine repeating chevrons: a knit approximation, 0.65 × 0.8 mm.
        x, y, z = channels("max_shirt_rest")
        across = math_node("MULTIPLY", math_node("ADD", x, y),
                           math.tau / 0.00065)
        row = math_node("MULTIPLY", z, math.tau / 0.0008)
        chevron = math_node("MULTIPLY",
                            math_node("ABSOLUTE", math_node("SINE", across)),
                            1.8)
        knit_height = math_node(
            "MULTIPLY_ADD",
            math_node("SINE", math_node("ADD", row, chevron)), 0.5, 0.5)

        knit = nodes.new("ShaderNodeBump")
        knit.label = "Knit: 0.03 mm"
        knit.inputs["Strength"].default_value = 1.0
        knit.inputs["Distance"].default_value = 0.00003 / unit
        links.new(knit_height, knit.inputs["Height"])
        links.new(folds.outputs["Normal"], knit.inputs["Normal"])
        links.new(knit.outputs["Normal"], bsdf.inputs["Normal"])

        # Base Color, UVs, images and the original normal-map chain stay intact.
        replacements[index] = len(mesh.materials)
        mesh.materials.append(mat)

    for i in faces:
        polygon = mesh.polygons[i]
        polygon.material_index = replacements[polygon.material_index]
    mesh.update()
    ob["max_shirt_upgrade"] = 1


def upgrade(rig):
    body = next(o for o in rig.children_recursive if o.name.endswith(".body"))
    print("[max_look] skin zones", paint_zones(rig, body))
    print("[max_look] throat-rise vertices:", add_throat_rise(rig, body))
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
            elif "eyelash" in ob.name:
                upgrade_lashes(mat)
    teeth = next((o for o in rig.children_recursive if "teeth" in o.name and o.type == "MESH"), None)
    if teeth:
        print("[max_look] upper teeth moved:", upgrade_teeth_geometry(teeth))
    upgrade_hair(body)
    try:
        upgrade_shirt(rig)
        print("[max_look] shirt fabric + folds applied")
    except (ValueError, KeyError) as e:     # Codex's guards: fail safe, never a broken shirt
        print("[max_look] shirt upgrade SKIPPED:", e)
    rig["max_look"] = "v6"
    try:
        wet = add_eye_wetness(rig, body)
        print("[max_look] eye wetness:", [o.name for o in wet])
    except ValueError as e:             # Codex's guard rails: never ship a mis-placed lid ribbon silently
        print("[max_look] eye wetness SKIPPED:", e)


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
        ("Rim", (0.9, 2.6, 2.9), 35, (0.37, 0.83, 0.90), 0.8),     # cyan rim (#5FD3E6)
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
