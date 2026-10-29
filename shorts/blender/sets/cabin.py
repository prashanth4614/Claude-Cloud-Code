"""Realistic narrow-body airliner cabin (the pilot's cabin set), modelled in code with CC0 PBR materials.

Layout (cabin space; origin = the CABIN world offset, Max faces -Y, rows run along Y):
  right block (window side): seats at x = 0 (aisle, Max's seat), 0.55, 1.10; window wall at x ~1.6
  aisle around x = -0.35; left block at x = -0.80, -1.35, -1.90; wall at x ~ -2.2
  rows every 0.8 m; Max's row at y = 0.35 (seat-pan centre); cushion top at z = 0.53
The fuselage is a curved shell with real window openings; a sky cyclorama outside shows
through them and lights the cabin, with warm LED coves along the overhead bins.
"""
import math

import bmesh
import bpy
from mathutils import Vector

from .pbr import plain, textured

ROW_Y0, ROW_PITCH = 0.35, 0.8
RIGHT_X = (0.0, 0.55, 1.10)
LEFT_X = (-0.80, -1.35, -1.90)
SEAT_TOP = 0.53
BACK_TOP = 1.16
CABIN_Y = (-6.4, 6.4)
WINDOW_Z = 1.2
CENTRE_X = -0.3          # fuselage centre line (aisle side of Max)


# ----------------------------------------------------------------- helpers --
def _link(ob, coll):
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    coll.objects.link(ob)
    return ob


def _mesh_obj(name, bm, coll, mat=None, smooth=True):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    if mat:
        me.materials.append(mat)
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    return ob


def box(name, coll, centre, size, mat, bevel=0.0, segs=3, rot=(0, 0, 0), subsurf=0, parent=None):
    """Bevelled box (cushions, panels, bins). size = full extents."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    ob = _mesh_obj(name, bm, coll, mat)
    ob.location = Vector(centre)
    ob.rotation_euler = [math.radians(a) for a in rot]
    if bevel:
        b = ob.modifiers.new("bevel", "BEVEL")
        b.width, b.segments, b.limit_method = bevel, segs, "NONE"
    if subsurf:
        s = ob.modifiers.new("subsurf", "SUBSURF")
        s.levels = s.render_levels = subsurf
    if parent:
        ob.parent = parent
    return ob


def extrude_profile(name, coll, pts_xz, y0, y1, mat, closed=False, y_steps=1, flip=False):
    """Extrude a 2-D (x, z) polyline along Y (fuselage walls, bins, coves)."""
    bm = bmesh.new()
    rings = []
    for i in range(y_steps + 1):
        y = y0 + (y1 - y0) * i / y_steps
        rings.append([bm.verts.new((x, y, z)) for x, z in pts_xz])
    n = len(pts_xz)
    for a, b in zip(rings, rings[1:]):
        for j in range(n if closed else n - 1):
            k = (j + 1) % n
            f = (a[j], a[k], b[k], b[j])
            bm.faces.new(f[::-1] if flip else f)
    if closed:
        for ring, rev in ((rings[0], True), (rings[-1], False)):
            bm.faces.new(ring[::-1] if rev != flip else ring)
    if closed:
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _mesh_obj(name, bm, coll, mat)


def _arc(cx, cz, r, a0, a1, n):
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cz + r * math.sin(math.radians(a0 + (a1 - a0) * i / n)))
            for i in range(n + 1)]


# ---------------------------------------------------------------- materials --
def materials():
    return {
        "panel": textured("cab_panel", "Plastic010", tint=(0.86, 0.85, 0.82), scale=2.0, rough_mul=0.9, normal=0.25,
                          base=(0.86, 0.85, 0.82)),
        "panel_dark": plain("cab_panel_dark", (0.32, 0.33, 0.35), rough=0.5),
        "seat": textured("cab_seat_wool", "poly_wool_herringbone", tint=(0.16, 0.26, 0.62), scale=5.0, normal=0.8,
                         sheen=0.4, base=(0.13, 0.18, 0.34)),
        "cover": textured("cab_headrest", "leather_white", tint=(0.95, 0.95, 0.93), scale=6.0, normal=0.5,
                          base=(0.9, 0.9, 0.88)),
        "arm": textured("cab_armrest", "fabric_leather_02", tint=(0.25, 0.25, 0.27), scale=6.0, base=(0.1, 0.1, 0.11)),
        "metal": plain("cab_metal", (0.62, 0.63, 0.65), rough=0.3, metal=1.0),
        "carpet": textured("cab_carpet", "Carpet012", tint=(0.42, 0.46, 0.55), scale=2.5, normal=1.0,
                           base=(0.2, 0.22, 0.28)),
        "led": plain("cab_led", (1.0, 0.86, 0.68), emission=6.0),
        "reading": plain("cab_reading_light", (1.0, 0.95, 0.85), emission=1.5, rough=0.2),
        "shade": plain("cab_window_shade", (0.82, 0.8, 0.76), rough=0.6),
        "tray": plain("cab_tray", (0.55, 0.56, 0.58), rough=0.4),
        "cut": plain("cab_cutter", (1, 0, 1)),
    }


def sky_cyclorama(coll, o):
    """Huge emissive cylinder outside the fuselage: sky gradient above, a soft cloud deck below."""
    m = bpy.data.materials.new("cab_outside_sky")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = 2.2
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(geo.outputs["Position"], sep.inputs[0])
    hz = nt.nodes.new("ShaderNodeMapRange")              # z -> 0 (cloud deck) .. 1 (high sky)
    hz.inputs["From Min"].default_value = o.z - 2.0
    hz.inputs["From Max"].default_value = o.z + 9.0
    nt.links.new(sep.outputs["Z"], hz.inputs["Value"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    cr = ramp.color_ramp
    cr.elements[0].position, cr.elements[0].color = 0.0, (0.95, 0.9, 0.85, 1)    # sunlit cloud tops
    cr.elements[1].position, cr.elements[1].color = 1.0, (0.28, 0.48, 0.86, 1)   # deep sky
    e = cr.elements.new(0.22)
    e.color = (1.0, 0.82, 0.6, 1)                                                 # warm horizon glow
    e2 = cr.elements.new(0.4)
    e2.color = (0.62, 0.74, 0.95, 1)
    nt.links.new(hz.outputs["Result"], ramp.inputs["Fac"])
    noise = nt.nodes.new("ShaderNodeTexNoise")                                    # cloud lumps below the horizon
    noise.inputs["Scale"].default_value = 0.35
    noise.inputs["Detail"].default_value = 8
    nt.links.new(geo.outputs["Position"], noise.inputs["Vector"])
    mask = nt.nodes.new("ShaderNodeMapRange")
    mask.inputs["From Min"].default_value = 0.25
    mask.inputs["From Max"].default_value = 0.1
    nt.links.new(hz.outputs["Result"], mask.inputs["Value"])
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    nt.links.new(noise.outputs["Fac"], mul.inputs[0])
    nt.links.new(mask.outputs["Result"], mul.inputs[1])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    nt.links.new(mul.outputs[0], mix.inputs[0])
    nt.links.new(ramp.outputs["Color"], mix.inputs[6])
    mix.inputs[7].default_value = (1.0, 1.0, 1.0, 1)
    nt.links.new(mix.outputs[2], em.inputs["Color"])
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=14, depth=40, location=o + Vector((0, 0, 1.0)),
                                        rotation=(math.radians(90), 0, 0))
    cyc = _link(bpy.context.active_object, coll)
    cyc.name = "cabin_outside_sky"
    cyc.data.materials.append(m)
    cyc.visible_shadow = False
    return cyc


# -------------------------------------------------------------------- shell --
def fuselage_profile():
    """Right half (x, z) from the floor up to the crown, in cabin space; mirrored about CENTRE_X."""
    right = [(1.50, 0.0), (1.58, 0.30), (1.64, 0.70), (1.66, 1.00), (1.66, 1.30), (1.62, 1.55), (1.52, 1.78)]
    right += _arc(CENTRE_X, 0.35, 2.05, math.degrees(math.atan2(1.78 - 0.35, 1.52 - CENTRE_X)) - 4, 90, 10)[1:]
    left = [(2 * CENTRE_X - x, z) for x, z in reversed(right[:-1])]
    return right + left


def build_cabin(scene, o):
    """Build the cabin with its cabin-space origin at world `o`. Returns the SET_cabin collection."""
    coll = bpy.data.collections.new("SET_cabin")
    scene.collection.children.link(coll)
    mats = materials()
    y0, y1 = CABIN_Y

    # floor + carpet aisle
    box("cabin_floor", coll, o + Vector((CENTRE_X, 0, -0.03)), (3.9, y1 - y0, 0.06), mats["panel_dark"])
    box("cabin_carpet", coll, o + Vector((CENTRE_X, 0, 0.005)), (3.6, y1 - y0, 0.01), mats["carpet"])

    # fuselage shell with window openings
    prof = [(o.x + x, o.z + z) for x, z in fuselage_profile()]
    shell = extrude_profile("cabin_shell", coll, prof, o.y + y0, o.y + y1, mats["panel"], y_steps=64, flip=True)
    sol = shell.modifiers.new("thickness", "SOLIDIFY")
    sol.thickness, sol.offset = 0.06, 1.0
    cutters = bpy.data.collections.new("cabin_window_cutters")
    coll.children.link(cutters)
    win_rows = [ROW_Y0 + ROW_PITCH * k for k in range(-7, 8)]
    for i, ry in enumerate(win_rows):
        wy = ry + 0.12
        if not (y0 + 0.4 < wy < y1 - 0.4):
            continue
        for side, wx in (("R", 1.66), ("L", 2 * CENTRE_X - 1.66)):
            c = box(f"cut_{side}_{i}", cutters, o + Vector((wx, wy, WINDOW_Z)), (0.6, 0.25, 0.36), mats["cut"],
                    bevel=0.11, segs=8)
            c.display_type = "WIRE"
            c.hide_render = True
            # window bezel (rounded frame) and, on some windows, a half-drawn shade
            bez = box(f"window_bezel_{side}_{i}", coll, o + Vector((wx + (-0.045 if side == "R" else 0.045), wy, WINDOW_Z)),
                      (0.03, 0.33, 0.45), mats["panel"], bevel=0.13, segs=8)
            hole = bez.modifiers.new("hole", "BOOLEAN")
            hole.object, hole.operation, hole.solver = c, "DIFFERENCE", "EXACT"
            shade = (i * 7 + (side == "L") * 3) % 5
            if shade in (1, 3):
                drop = 0.12 if shade == 1 else 0.24
                box(f"window_shade_{side}_{i}", coll,
                                        o + Vector((wx, wy, WINDOW_Z + 0.18 - drop / 2)),
                                        (0.012, 0.25, drop), mats["shade"], bevel=0.004)
    boo = shell.modifiers.new("windows", "BOOLEAN")
    boo.operand_type, boo.collection, boo.operation, boo.solver = "COLLECTION", cutters, "DIFFERENCE", "EXACT"
    cutters.hide_render = True

    # overhead bins (both sides) with door seams, LED coves and passenger service units
    bin_r = [(1.52, 1.62), (0.10, 1.62), (0.02, 1.70), (0.05, 1.90), (0.25, 2.02), (1.30, 2.10), (1.52, 1.95)]
    for side, pts in (("R", bin_r), ("L", [(2 * CENTRE_X - x, z) for x, z in bin_r])):
        b = extrude_profile(f"overhead_bins_{side}", coll, [(o.x + x, o.z + z) for x, z in pts], o.y + y0 + 0.2,
                            o.y + y1 - 0.2, mats["panel"], closed=True, flip=(side == "L"))
        bv = b.modifiers.new("bevel", "BEVEL")
        bv.width, bv.segments, bv.limit_method = 0.02, 3, "ANGLE"
        lip_x = 0.03 if side == "R" else 2 * CENTRE_X - 0.03
        for k in range(-4, 5):  # door seams every 1.6 m
            box(f"bin_seam_{side}_{k}", coll, o + Vector((lip_x, ROW_Y0 + 0.5 + 1.6 * k, 1.84)), (0.03, 0.006, 0.26),
                mats["panel_dark"])
        cove_x = 0.2 if side == "R" else 2 * CENTRE_X - 0.2
        box(f"led_cove_{side}", coll, o + Vector((cove_x, 0, 2.06)), (0.04, y1 - y0 - 0.6, 0.015), mats["led"])
        psu_x = 0.75 if side == "R" else 2 * CENTRE_X - 0.75
        box(f"psu_{side}", coll, o + Vector((psu_x, 0, 1.605)), (1.3, y1 - y0 - 0.5, 0.02), mats["panel"])
        for ry in win_rows:
            if y0 + 0.4 < ry < y1 - 0.4:
                for dx in (-0.45, 0.0, 0.45):
                    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.025, depth=0.01,
                                                        location=o + Vector((psu_x + dx, ry - 0.1, 1.592)))
                    rl = _link(bpy.context.active_object, coll)
                    rl.name = f"reading_light_{side}"
                    rl.data.materials.append(mats["reading"])

    # bulkheads at both ends
    box("bulkhead_back", coll, o + Vector((CENTRE_X, y1, 1.1)), (4.2, 0.08, 2.4), mats["panel"], bevel=0.02)
    box("bulkhead_front", coll, o + Vector((CENTRE_X, y0, 1.1)), (4.2, 0.08, 2.4), mats["panel"], bevel=0.02)

    # seats: every row on both sides
    for k in range(-7, 8):
        ry = ROW_Y0 + ROW_PITCH * k
        if not (y0 + 0.6 < ry < y1 - 0.6):
            continue
        seat_block_world(coll, mats, [o + Vector((x, ry, 0)) for x in RIGHT_X], f"R{k}")
        seat_block_world(coll, mats, [o + Vector((x, ry, 0)) for x in LEFT_X], f"L{k}")

    # light: warm overhead fill + soft daylight from the window side + the sky outside
    sky_cyclorama(coll, o)
    for name, loc, energy, color, size, rot in (
            ("cabin_key", (0.3, -1.0, 2.0), 260, (1.0, 0.9, 0.78), 1.6, (0, 0, 0)),
            ("cabin_aisle_fill", (CENTRE_X, 2.0, 2.05), 220, (1.0, 0.92, 0.84), 3.0, (0, 0, 0)),
            ("window_light", (1.45, -0.1, WINDOW_Z + 0.1), 120, (1.0, 0.92, 0.82), 0.9, (0, -90, 0))):
        ld = bpy.data.lights.new(name, "AREA")
        ld.energy, ld.color, ld.size = energy, color, size
        lo = bpy.data.objects.new(name, ld)
        coll.objects.link(lo)
        lo.location = o + Vector(loc)
        lo.rotation_euler = [math.radians(a) for a in rot]
    # ceiling wash: the indirect cove light real cabins have, as two long strips along the crown
    for side, x in (("R", 0.55), ("L", 2 * CENTRE_X - 0.55)):
        ld = bpy.data.lights.new(f"ceiling_wash_{side}", "AREA")
        ld.shape, ld.size, ld.size_y = "RECTANGLE", 0.5, y1 - y0 - 1.0
        ld.energy, ld.color = 900, (1.0, 0.93, 0.85)
        lo = bpy.data.objects.new(f"ceiling_wash_{side}", ld)
        coll.objects.link(lo)
        lo.location = o + Vector((x, 0, 2.15))
    return coll


def seat_block_world(coll, mats, positions, tag):
    """Three seats at world-space seat-pan centres (x varies, same y), with shared armrests and beam."""
    xs = [p.x for p in positions]
    y, oz = positions[0].y, positions[0].z
    for i, p in enumerate(positions):
        _seat_world(coll, mats, p, f"{tag}_{i}")
    edges = sorted(xs)
    pitch = abs(edges[1] - edges[0])
    arms = [edges[0] - pitch / 2] + [(a + b) / 2 for a, b in zip(edges, edges[1:])] + [edges[-1] + pitch / 2]
    for j, ax in enumerate(arms):
        box(f"armrest_{tag}_{j}", coll, (ax, y - 0.02, oz + SEAT_TOP + 0.17), (0.05, 0.4, 0.045), mats["arm"], bevel=0.015)
        box(f"armpost_{tag}_{j}", coll, (ax, y + 0.13, oz + SEAT_TOP + 0.07), (0.035, 0.05, 0.18), mats["panel_dark"],
            bevel=0.01)
    box(f"seat_beam_{tag}", coll, (sum(xs) / 3, y - 0.05, oz + 0.3), (abs(edges[-1] - edges[0]) + 0.46, 0.06, 0.05),
        mats["metal"], bevel=0.01)


def _seat_world(coll, mats, p, tag):
    w = 0.44
    box(f"seat_cushion_{tag}", coll, (p.x, p.y, p.z + SEAT_TOP - 0.06), (w, 0.48, 0.12), mats["seat"], bevel=0.035, segs=4)
    pivot = bpy.data.objects.new(f"seat_back_{tag}", None)
    coll.objects.link(pivot)
    pivot.location = (p.x, p.y + 0.27, p.z + SEAT_TOP - 0.02)
    pivot.rotation_euler = (math.radians(-12), 0, 0)
    h = BACK_TOP - SEAT_TOP + 0.02
    box(f"seat_backrest_{tag}", coll, (0, 0, h / 2), (w, 0.11, h), mats["seat"], bevel=0.04, segs=4, parent=pivot)
    box(f"seat_headrest_{tag}", coll, (0, -0.07, h - 0.13), (w - 0.06, 0.05, 0.2), mats["seat"], bevel=0.02, parent=pivot)
    box(f"seat_cover_{tag}", coll, (0, -0.098, h - 0.12), (w - 0.1, 0.012, 0.19), mats["cover"], bevel=0.005, segs=2,
        parent=pivot)
    box(f"seat_shell_{tag}", coll, (0, 0.065, h / 2 - 0.02), (w + 0.01, 0.03, h - 0.02), mats["panel"], bevel=0.012,
        parent=pivot)
    box(f"seat_tray_{tag}", coll, (0, 0.083, h * 0.55), (w - 0.08, 0.01, 0.3), mats["tray"], bevel=0.008, segs=2,
        parent=pivot)
    for dx in (-0.16, 0.16):
        box(f"seat_leg_{tag}", coll, (p.x + dx, p.y - 0.05, p.z + 0.22), (0.035, 0.035, 0.44), mats["metal"], bevel=0.008,
            rot=(8, 0, 0))
