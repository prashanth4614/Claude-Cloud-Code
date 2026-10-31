# Codex answer: 011a-max-eyes

_model: gpt-6.1-sol, reasoning effort: high, read-only, cap 1200s_

**Verdict: add it, but reject ambiguous lid selection.** A distance band alone can select socket or cheek vertices. This patch finds a connected lower-lid path near the actual eyeball surface.

Insert before [`upgrade()`](/Users/prashanthmogili/Claude-Cloud-Code-codex/shorts/blender/max_look.py:221). Call `add_eye_wetness(rig, body)` immediately after `rig["max_look"] = "v5"`.

```python
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
            if hit is not None and distance < 1.5 * mm and normal.y < -0.15:
                candidates[i] = (hit, normal, distance)

        corners = [i for i in candidates
                   if abs(co[i].z - centre.z) < 0.3 * radius.z]
        if not corners:
            raise ValueError(f"No lid corners: side {side}")
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
            raise ValueError(f"Disconnected lid band: side {side}")
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
            centre = hit + normal * (0.09 * mm)
            for k in range(ring):
                angle = 2 * math.pi * k / ring
                positions.append(centre
                                 + across * (0.10 * mm * taper * math.cos(angle))
                                 + normal * (0.035 * mm * taper * math.sin(angle)))
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
```

The ribbon is a closed, flattened water volume: **0.20 mm wide**, tapered at its ends. White transmission avoids an opaque eyeliner effect. Both meshes inherit body weights and driven facial deltas; corner geometry blends neighbouring vertices toward its anchor.

**Verification render:** eye-level, 85 mm, approximately 15° three-quarter; both eyes spanning roughly 600 pixels. Use existing `ear_pop`, house lighting, Cycles 128 samples, 1080×1920. Inspect native resolution and a 360-pixel-wide reduction: subtle interrupted highlights, pink corners, no continuous dark stroke.

**Risks:** untested in Blender here. Proximity/path selection remains heuristic; inspect its placement before production. Full closure can expose wet geometry through the upper lid; the eyeball guard prevents penetration, not eyelid collisions. Subdivision can soften the caruncle excessively. Rebuild after phenotype changes. One still cannot verify blink, squint and wide extremes—scrub those separately.

**Cost:** ₹0 assets; approximately 20–40 minutes integration/inspection. Geometry overhead negligible; transmission render overhead needs measurement. No files changed or render performed.
_took 177 s_
STATUS: OK
