"""The one 3D world for "Why you fall stepping off a slow train": a Mumbai suburban station.

    blender -b assets/characters/max/max_v6.blend -P shorts/train_step_off/blender/build_set.py -- \
        --out out/train_step_off/set.blend

Everything is procedural (no downloads). Units are metres; the train runs along +X, track centre at
y = 0, rail top at z = 0. Real-world sizes (Indian broad gauge, Mumbai EMU), from research.md:
- gauge 1.676 m;
- coach length 20.7 m, width 3.66 m, roof 3.9 m above the rail;
- coach floor 1.2 m above the rail; platform top 0.9 m, so a 0.30 m step down;
- the platform edge 0.20 m from the coach side (the gap).
Coaches have wide open doorways (no doors) on both sides, a door pole, and barred windows.
Materials are blockout-ready (viewport colour = base colour) and get the ink & amber look later.
"""
import math
import os
import random
import sys

import bpy
from mathutils import Vector

GAUGE = 1.676
COACH_L, COACH_W, COACH_H = 20.7, 3.66, 3.9
FLOOR_Z = 1.2
PLATFORM_Z = 0.9
GAP = 0.20
PLATFORM_Y0 = -(COACH_W / 2 + GAP)          # the platform edge (platform on the -Y side)
PLATFORM_DEPTH = 9.0
PLATFORM_LEN = 140.0
DOOR_W, DOOR_H = 1.30, 2.05
DOOR_X = (-7.6, -2.3, 2.3, 7.6)             # doorway centres along a coach (2 pairs, Mumbai EMU layout)
WIN_W, WIN_H, WIN_Z = 0.95, 0.85, FLOOR_Z + 0.85
COACHES = 4                                  # one hero coach (index 1) + neighbours for the drone shot
SEED = 11

COL = {
    "white": (0.86, 0.86, 0.84, 1),
    "purple": (0.30, 0.14, 0.42, 1),
    "maroon": (0.36, 0.08, 0.10, 1),
    "grey": (0.32, 0.33, 0.34, 1),
    "dark": (0.05, 0.05, 0.06, 1),
    "steel": (0.55, 0.56, 0.58, 1),
    "concrete": (0.46, 0.44, 0.40, 1),
    "coping": (0.62, 0.60, 0.55, 1),
    "yellow": (0.85, 0.66, 0.08, 1),
    "ballast": (0.24, 0.22, 0.20, 1),
    "rust": (0.30, 0.17, 0.10, 1),
    "canopy": (0.40, 0.42, 0.44, 1),
    "building": (0.55, 0.52, 0.48, 1),
    "console": (0.10, 0.22, 0.42, 1),
    "dial": (0.92, 0.92, 0.90, 1),
}


def coll(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(c)
    return c


def mat(name, rgba=None, rough=0.6, metal=0.0, emit=0.0):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    rgba = rgba or COL[name]
    b.inputs["Base Color"].default_value = rgba
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = rgba
        b.inputs["Emission Strength"].default_value = emit
    m.diffuse_color = rgba
    return m


def box(name, size, loc, material, c, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)   # keep the location: rotations pivot here
    if bevel:
        m = ob.modifiers.new("Bevel", "BEVEL")
        m.width, m.segments = bevel, 2
    ob.data.materials.append(material)
    for cc in ob.users_collection:
        cc.objects.unlink(ob)
    c.objects.link(ob)
    return ob


def cyl(name, r, depth, loc, rot, material, c, verts=24):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, location=loc, rotation=rot, vertices=verts)
    ob = bpy.context.active_object
    ob.name = name
    ob.data.materials.append(material)
    for cc in ob.users_collection:
        cc.objects.unlink(ob)
    c.objects.link(ob)
    return ob


def cut(target, cutter):
    m = target.modifiers.new("cut_" + cutter.name, "BOOLEAN")
    m.object, m.operation, m.solver = cutter, "DIFFERENCE", "EXACT"
    cutter.display_type = "WIRE"
    cutter.hide_render = True
    cutter.hide_viewport = True


def livery_material():
    """White body with a purple band below the windows and a thin one above (Mumbai EMU style),
    driven by object-space height, so every coach gets it without UVs."""
    m = bpy.data.materials.get("emu_livery")
    if m:
        return m
    m = bpy.data.materials.new("emu_livery")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Roughness"].default_value = 0.42
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    r = ramp.color_ramp
    r.interpolation = "CONSTANT"
    z0, z1 = -0.3, COACH_H + 0.3                        # map object z (coach origin at rail level) to 0-1
    def at(z):
        return (z - z0) / (z1 - z0)
    stops = [(0.0, COL["grey"]), (at(FLOOR_Z - 0.05), COL["white"]), (at(WIN_Z - 0.32), COL["purple"]),
             (at(WIN_Z - 0.06), COL["white"]), (at(WIN_Z + WIN_H + 0.12), COL["purple"]),
             (at(WIN_Z + WIN_H + 0.22), COL["white"]), (at(COACH_H - 0.25), COL["grey"])]
    r.elements[0].position, r.elements[0].color = stops[0]
    r.elements[1].position, r.elements[1].color = stops[1]
    for pos, c in stops[2:]:
        e = r.elements.new(pos)
        e.color = c
    mapz = nt.nodes.new("ShaderNodeMapRange")
    mapz.inputs["From Min"].default_value, mapz.inputs["From Max"].default_value = z0, z1
    nt.links.new(sep.outputs["Z"], mapz.inputs["Value"])
    nt.links.new(mapz.outputs["Result"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    m.diffuse_color = COL["white"]
    return m


def build_coach(index, c):
    """One EMU coach centred at x = index * (COACH_L + 0.6). Returns its root empty."""
    x0 = (index - 1) * (COACH_L + 0.6)
    root = bpy.data.objects.new(f"coach_{index}", None)
    c.objects.link(root)
    root.location = (x0, 0, 0)
    parts = []
    body = box(f"coach_{index}_body", (COACH_L, COACH_W, COACH_H - FLOOR_Z + 0.35),
               (x0, 0, FLOOR_Z - 0.35 + (COACH_H - FLOOR_Z + 0.35) / 2), livery_material(), c, bevel=0.06)
    body.location.z -= 0.0
    # the livery reads object z from the rail: keep the body's origin at rail level
    bpy.context.view_layer.objects.active = body
    body.select_set(True)
    cursor = bpy.context.scene.cursor.location.copy()
    bpy.context.scene.cursor.location = (x0, 0, 0)
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
    bpy.context.scene.cursor.location = cursor
    body.select_set(False)
    parts.append(body)
    # livery stripes as thin strips (3 mm proud), so they read in every view mode, not only in Cycles
    # (split between the doorways: the stripe stops at each door frame)
    edges = [-COACH_L / 2 + 0.05] + [e for dx in DOOR_X for e in (dx - DOOR_W / 2, dx + DOOR_W / 2)] + [COACH_L / 2 - 0.05]
    for side in (-1, 1):
        for z, h in ((WIN_Z - 0.19, 0.26), (WIN_Z + WIN_H + 0.17, 0.10)):
            for a, b in zip(edges[0::2], edges[1::2]):
                parts.append(box(f"coach_{index}_stripe_{side}_{z:.2f}_{a:.1f}", (b - a, 0.006, h),
                                 (x0 + (a + b) / 2, side * (COACH_W / 2 + 0.003), z), mat("purple", rough=0.4), c))
    hollow = box(f"coach_{index}_hollow", (COACH_L - 0.12, COACH_W - 0.12, COACH_H - FLOOR_Z - 0.1),
                 (x0, 0, FLOOR_Z + (COACH_H - FLOOR_Z - 0.1) / 2), mat("dark"), c)
    cut(body, hollow)
    for side in (-1, 1):
        for dx in DOOR_X:
            d = box(f"coach_{index}_door_{side}_{dx}", (DOOR_W, 0.6, DOOR_H),
                    (x0 + dx, side * COACH_W / 2, FLOOR_Z + DOOR_H / 2), mat("dark"), c)
            cut(body, d)
            pole = cyl(f"coach_{index}_pole_{side}_{dx}", 0.02, DOOR_H, (x0 + dx, side * (COACH_W / 2 - 0.12),
                       FLOOR_Z + DOOR_H / 2), (0, 0, 0), mat("steel", rough=0.25, metal=1.0), c, verts=12)
            parts.append(pole)
        # windows between doorways, with horizontal bars
        xs = [-9.6, -6.0, -4.95, -0.7, 0.7, 4.95, 6.0, 9.6]
        for wx in xs:
            w = box(f"coach_{index}_win_{side}_{wx}", (WIN_W, 0.6, WIN_H),
                    (x0 + wx, side * COACH_W / 2, WIN_Z + WIN_H / 2), mat("dark"), c)
            cut(body, w)
            for k in range(4):
                bar = box(f"coach_{index}_bar_{side}_{wx}_{k}", (WIN_W, 0.02, 0.02),
                          (x0 + wx, side * (COACH_W / 2 - 0.03), WIN_Z + 0.15 + k * 0.19), mat("steel", rough=0.3, metal=1.0), c)
                parts.append(bar)
    floor = box(f"coach_{index}_floor", (COACH_L - 0.14, COACH_W - 0.14, 0.04), (x0, 0, FLOOR_Z - 0.02),
                mat("floor", (0.18, 0.17, 0.16, 1), rough=0.8), c)
    parts.append(floor)
    roof = box(f"coach_{index}_roof", (COACH_L - 0.2, COACH_W - 0.5, 0.18), (x0, 0, COACH_H + 0.05),
               mat("grey"), c, bevel=0.08)
    parts.append(roof)
    under = box(f"coach_{index}_under", (COACH_L - 2.0, COACH_W - 0.7, 0.55), (x0, 0, FLOOR_Z - 0.62),
                mat("dark"), c)
    parts.append(under)
    for bx in (-COACH_L / 2 + 2.6, COACH_L / 2 - 2.6):
        bog = box(f"coach_{index}_bogie_{bx}", (2.6, GAUGE + 0.3, 0.45), (x0 + bx, 0, 0.62), mat("dark"), c)
        parts.append(bog)
        for wx in (-0.9, 0.9):
            for side in (-1, 1):
                wh = cyl(f"coach_{index}_wheel_{bx}_{wx}_{side}", 0.46, 0.14,
                         (x0 + bx + wx, side * GAUGE / 2, 0.46), (math.pi / 2, 0, 0), mat("rust"), c)
                parts.append(wh)
    # seats just inside the hero doorways (visible through the door)
    for dx in DOOR_X:
        for off in (-1.2, 1.2):
            s = box(f"coach_{index}_seat_{dx}_{off}", (0.9, 1.1, 0.45),
                    (x0 + dx + off * 1.0, 0.6, FLOOR_Z + 0.22), mat("seat", (0.40, 0.34, 0.20, 1), rough=0.5), c)
            parts.append(s)
    for p in parts:
        p.parent = root
        p.matrix_parent_inverse = root.matrix_world.inverted()
    return root


def build_track(c):
    ballast = box("ballast", (PLATFORM_LEN + 200, 4.6, 0.25), (0, 0, -0.30), mat("ballast", rough=1.0), c)
    for side in (-1, 1):
        box(f"rail_{side}", (PLATFORM_LEN + 200, 0.07, 0.16), (0, side * GAUGE / 2, -0.08),
            mat("rail", (0.35, 0.33, 0.32, 1), rough=0.35, metal=0.9), c)
    sl = box("sleeper", (0.25, 2.75, 0.15), (0, 0, -0.17), mat("sleeper", (0.42, 0.40, 0.37, 1)), c)
    arr = sl.modifiers.new("Array", "ARRAY")
    arr.count, arr.relative_offset_displace = 520, (2.4, 0, 0)
    sl.location.x = -(PLATFORM_LEN + 200) / 2
    return ballast


def build_platform(c):
    y_mid = PLATFORM_Y0 - PLATFORM_DEPTH / 2
    slab = box("platform", (PLATFORM_LEN, PLATFORM_DEPTH, PLATFORM_Z + 0.3), (0, y_mid, (PLATFORM_Z - 0.3) / 2),
               mat("concrete", rough=0.85), c)
    coping = box("platform_coping", (PLATFORM_LEN, 0.45, 0.06), (0, PLATFORM_Y0 - 0.225, PLATFORM_Z + 0.005),
                 mat("coping", rough=0.7), c)
    # expansion joints every 2 m: real, and a fixed landmark that shows the foot staying put (Codex 019)
    for i in range(-int(PLATFORM_LEN / 4), int(PLATFORM_LEN / 4) + 1):
        box(f"platform_joint_{i}", (0.025, PLATFORM_DEPTH - 0.5, 0.004), (i * 2.0, y_mid + 0.25, PLATFORM_Z + 0.002),
            mat("joint", (0.20, 0.19, 0.17, 1), rough=0.9), c)
    line = box("platform_yellow_line", (PLATFORM_LEN, 0.12, 0.01), (0, PLATFORM_Y0 - 0.62, PLATFORM_Z + 0.006),
               mat("yellow", rough=0.5), c)
    wall = box("platform_wall", (PLATFORM_LEN, 0.15, PLATFORM_Z + 0.3), (0, PLATFORM_Y0 + 0.075, (PLATFORM_Z - 0.3) / 2),
               mat("grey"), c)
    # canopy: pillars every 7 m and a roof
    pillars = []
    for i in range(-9, 10):
        x = i * 7.0
        pillars.append(box(f"pillar_{i}", (0.25, 0.25, 4.2), (x, PLATFORM_Y0 - 5.2, PLATFORM_Z + 2.1),
                           mat("canopy", rough=0.4, metal=0.6), c))
    roof = box("canopy_roof", (PLATFORM_LEN, 6.5, 0.12), (0, PLATFORM_Y0 - 4.6, PLATFORM_Z + 4.25),
               mat("canopy_roof", (0.30, 0.31, 0.33, 1), rough=0.5, metal=0.4), c)
    roof.rotation_euler.x = math.radians(-4)
    # benches and a sign board near the hero door
    for i, x in enumerate((-12.0, -4.0, 6.0, 14.0)):
        box(f"bench_{i}", (1.8, 0.45, 0.45), (x, PLATFORM_Y0 - 6.2, PLATFORM_Z + 0.22), mat("bench", (0.15, 0.30, 0.55, 1), rough=0.4, metal=0.5), c)
    box("sign_board", (2.4, 0.08, 0.6), (-2.3, PLATFORM_Y0 - 5.2, PLATFORM_Z + 3.4), mat("sign", (0.95, 0.80, 0.15, 1), rough=0.4), c)
    return slab


def build_city(c):
    rnd = random.Random(SEED)
    for side, y0 in ((1, 9.0), (-1, PLATFORM_Y0 - PLATFORM_DEPTH - 6.0)):
        for i in range(70):
            w, d = rnd.uniform(8, 18), rnd.uniform(8, 16)
            h = rnd.choice([rnd.uniform(6, 20), rnd.uniform(20, 70), rnd.uniform(70, 140)])
            x = rnd.uniform(-160, 160)
            y = y0 + side * rnd.uniform(0, 120)
            shade = rnd.uniform(0.8, 1.15)
            col = tuple(min(1, v * shade) for v in COL["building"][:3]) + (1,)
            box(f"bldg_{side}_{i}", (w, d, h), (x, y, h / 2 - 0.4), mat(f"bldg_{i % 6}", col, rough=0.8), c)
    ground = box("ground", (900, 900, 0.1), (0, 0, -0.5), mat("ground", (0.28, 0.26, 0.22, 1), rough=1.0), c)
    return ground


def build_cab(c):
    """Only what the speedometer close-up sees, far from the station (x = 400)."""
    o = Vector((400, 0, 1.2))
    box("cab_console", (1.2, 0.5, 0.6), o + Vector((0, 0, -0.35)), mat("console", rough=0.5), c, bevel=0.03)
    face = cyl("speedo_face", 0.12, 0.02, o + Vector((0, -0.26, 0.0)), (math.pi / 2, 0, 0), mat("dial", rough=0.3), c, verts=48)
    rim = cyl("speedo_rim", 0.13, 0.03, o + Vector((0, -0.25, 0.0)), (math.pi / 2, 0, 0),
              mat("rim", (0.08, 0.08, 0.09, 1), rough=0.3, metal=0.8), c, verts=48)
    # ticks 0-120 km/h over 270 degrees, labels every 20
    for v in range(0, 121, 5):
        a = math.radians(225 - v * 270 / 120)
        major = v % 20 == 0
        label = major or v in (10, 30)     # the low-speed end must be readable (Codex 019)
        L = 0.03 if major else 0.015
        r = 0.105 - L / 2
        t = box(f"speedo_tick_{v}", (0.004 if not major else 0.006, 0.004, L),
                o + Vector((r * math.cos(a), -0.272, r * math.sin(a))), mat("dark"), c)
        t.rotation_euler.y = -(a - math.pi / 2)
        if label:
            bpy.ops.object.text_add(location=o + Vector((0.072 * math.cos(a), -0.272, 0.072 * math.sin(a))),
                                    rotation=(math.pi / 2, 0, 0))
            tx = bpy.context.active_object
            tx.name = f"speedo_num_{v}"
            tx.data.body = str(v)
            tx.data.size = 0.018
            tx.data.align_x, tx.data.align_y = "CENTER", "CENTER"
            tx.data.materials.append(mat("dark"))
            for cc in tx.users_collection:
                cc.objects.unlink(tx)
            c.objects.link(tx)
    bpy.ops.object.text_add(location=o + Vector((0, -0.272, -0.05)), rotation=(math.pi / 2, 0, 0))
    unit = bpy.context.active_object
    unit.name, unit.data.body, unit.data.size = "speedo_unit", "km/h", 0.016
    unit.data.align_x, unit.data.align_y = "CENTER", "CENTER"
    unit.data.materials.append(mat("dark"))
    for cc in unit.users_collection:
        cc.objects.unlink(unit)
    c.objects.link(unit)
    pivot = bpy.data.objects.new("speedo_needle_pivot", None)
    c.objects.link(pivot)
    pivot.location = o + Vector((0, -0.275, 0))
    needle = box("speedo_needle", (0.004, 0.003, 0.095), o + Vector((0, -0.276, 0.045)), mat("needle", (0.75, 0.08, 0.05, 1), rough=0.3), c)
    needle.parent = pivot
    needle.matrix_parent_inverse = pivot.matrix_world.inverted()
    pivot["kmh_per_rad"] = 120 / math.radians(270)
    return pivot


def set_speed(pivot, kmh, frame=None):
    """Point the needle at kmh (0 at 225 degrees, 120 at -45 degrees, clockwise)."""
    pivot.rotation_euler.y = -(math.radians(225 - kmh * 270 / 120) - math.pi / 2)
    if frame is not None:
        pivot.keyframe_insert("rotation_euler", index=1, frame=frame)


def build(rig=None):
    c = coll("station")
    for i in range(COACHES):
        build_coach(i, coll("train"))
    build_track(c)
    build_platform(c)
    build_city(coll("city"))
    pivot = build_cab(coll("cab"))
    set_speed(pivot, 10)
    if rig is not None:                        # Max in the hero doorway (coach 1, the door at x = 2.3)
        rig.location = (2.3, -(COACH_W / 2 - 0.35), FLOOR_Z)
        rig.rotation_euler.z = 0.0              # facing -Y: out of the door, onto the platform
    bpy.context.scene["train_step_off"] = {"floor_z": FLOOR_Z, "platform_z": PLATFORM_Z, "edge_y": PLATFORM_Y0,
                                           "hero_door_x": 2.3}
    return pivot


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    build(bpy.data.objects.get("Max"))
    if "--out" in argv:
        out = os.path.abspath(argv[argv.index("--out") + 1])
        os.makedirs(os.path.dirname(out), exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
        print("saved", out, os.path.getsize(out) // 1024, "KB")
