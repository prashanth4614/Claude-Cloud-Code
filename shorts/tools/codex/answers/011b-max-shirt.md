# Codex answer: 011b-max-shirt

_model: gpt-6.1-sol, reasoning effort: high, read-only, cap 1200s_

**Use rest-space attributes and two chained Bump nodes.** This preserves teal, the diffuse texture and existing normal map; folds follow the skinned mesh. No cloth simulation.

Insert immediately before [`def upgrade(rig)`](/Users/prashanthmogili/Claude-Cloud-Code-codex/shorts/blender/max_look.py:221). Add `upgrade_shirt(rig)` immediately after `upgrade_hair(body)` at line 242.

```python
def upgrade_shirt(rig):
    """Shirt-only shading; rest-space folds follow skinning, without simulation."""
    import math
    from mathutils import Vector

    ob = next(o for o in rig.children_recursive
              if o.type == "MESH" and "male_casualsuit06" in o.name)
    if ob.get("max_shirt_upgrade") == 1:
        return

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
            0.00055 * envelope(d, (0.085, 0.16, 0.055)),
            0.00085 * envelope(dp, (0.075, 0.16, 0.065)),
            0.00120 * envelope(db, (0.19, 0.20, 0.115)),
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
            ("Roughness", 0.65), ("Sheen Weight", 0.15),
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
```

The existing normal feeds folds, then knit, then Principled, using Blender’s [Bump Normal input](https://docs.blender.org/UATEST/manual/en/dev/render/shader_nodes/displacement/bump.html).

**Thickness:** skip. Solidify’s vertex group controls thickness, not which faces receive a shell; this combined proxy needs separation or explicit border geometry first. Bump cannot improve collar/hem silhouettes.

**One verification render:** after inserting, run locally. Not executed here: read-only session; no Blender on `PATH`.

```bash
/Applications/Blender.app/Contents/MacOS/Blender \
-b assets/characters/max/max_v5.blend --python-expr '
import bpy, sys
from mathutils import Vector
sys.path.insert(0, "shorts/blender")
import max_look, build_max
rig = bpy.data.objects["Max"]
max_look.upgrade_shirt(rig)
build_max.thumbs_up(rig, True, raised=True)
# Opposite arm raised toward ear: test both shoulder regions together.
for name in ("upperarm01.L", "upperarm02.L"):
    build_max.aim_bone(rig, name, (0.8, -0.15, 0.35))
for name in ("lowerarm01.L", "lowerarm02.L"):
    build_max.aim_bone(rig, name, (-0.35, -0.2, 1))
bpy.context.view_layer.update()
cam = build_max.setup_render((960, 1100), samples=64)
target = build_max.head_point(rig) + Vector((0, 0, -0.30))
build_max.aim(cam, target + Vector((0.28, -1.75, 0.08)), target, 55)
build_max.render("/tmp/max_shirt_check.png")
'
```

Inspect shoulders/armpits for stretched ridges, belly for gentle drape, jeans for unchanged shading.

**Risks/cost:** assumes one connected tee island; fails safely if joined to jeans. Detached collar islands remain unchanged. Rest-space folds deform with poses but don’t recompute tension; extreme poses may stretch them. Knit may alias in distant shots. No additional geometry; shader overhead unbenchmarked. Free assets/local render; allow roughly 15–30 minutes for integration and visual tuning.
_took 194 s_
STATUS: OK
