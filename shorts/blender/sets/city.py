"""Dusk city for the landing shot (S10), replacing the grey-box blocks under SET_city.

Real scale. The jet passes ~30 m up on final approach, so the city is low-rise under the flight
path and rises to a downtown skyline further out (+Y). Facades get a procedural window grid
(randomly lit, warm or cool), streets get sodium lights, avenues get car head/tail lights, and the
backdrop dome shows the CC0 Poly Haven dusk sky.
"""
import math
import random

import bmesh
import bpy
from mathutils import Vector

from rigs import fcurves

from .pbr import LIB, plain

BLOCK, STREET = 48.0, 10.0
X_RANGE, Y_RANGE = (-190.0, 190.0), (-150.0, 240.0)


def _math(nt, op, a, b=None, value=None):
    n = nt.nodes.new("ShaderNodeMath")
    n.operation = op
    for i, v in enumerate((a, b)):
        if v is None:
            continue
        if isinstance(v, (int, float)):
            n.inputs[i].default_value = v
        else:
            nt.links.new(v, n.inputs[i])
    return n.outputs[0]


def facade_material():
    m = bpy.data.materials.new("city_facade")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    pos = nt.nodes.new("ShaderNodeSeparateXYZ")
    nor = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(geo.outputs["Position"], pos.inputs[0])
    nt.links.new(geo.outputs["Normal"], nor.inputs[0])
    ax = _math(nt, "ABSOLUTE", nor.outputs["X"])
    ay = _math(nt, "ABSOLUTE", nor.outputs["Y"])
    az = _math(nt, "ABSOLUTE", nor.outputs["Z"])
    u = _math(nt, "ADD", _math(nt, "MULTIPLY", pos.outputs["X"], ay), _math(nt, "MULTIPLY", pos.outputs["Y"], ax))
    v = pos.outputs["Z"]
    uu, vv = _math(nt, "DIVIDE", u, 2.6), _math(nt, "DIVIDE", v, 3.3)
    fu, fv = _math(nt, "FRACT", uu), _math(nt, "FRACT", vv)
    inside = _math(nt, "MULTIPLY",
                   _math(nt, "MULTIPLY", _math(nt, "GREATER_THAN", fu, 0.2), _math(nt, "LESS_THAN", fu, 0.8)),
                   _math(nt, "MULTIPLY", _math(nt, "GREATER_THAN", fv, 0.28), _math(nt, "LESS_THAN", fv, 0.86)))
    window = _math(nt, "MULTIPLY", inside, _math(nt, "LESS_THAN", az, 0.5))       # facades only, not roofs
    window = _math(nt, "MULTIPLY", window, _math(nt, "GREATER_THAN", v, 1.2))      # no windows at street level
    cell = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(_math(nt, "FLOOR", uu), cell.inputs[0])
    nt.links.new(_math(nt, "FLOOR", vv), cell.inputs[1])
    nt.links.new(_math(nt, "FLOOR", _math(nt, "DIVIDE", _math(nt, "ADD", pos.outputs["X"], pos.outputs["Y"]), 23.0)),
                 cell.inputs[2])
    wn = nt.nodes.new("ShaderNodeTexWhiteNoise")
    wn.noise_dimensions = "3D"
    nt.links.new(cell.outputs[0], wn.inputs["Vector"])
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(wn.outputs["Color"], sep.inputs[0])
    lit = _math(nt, "MULTIPLY", window, _math(nt, "GREATER_THAN", sep.outputs[0], 0.42))
    warm = nt.nodes.new("ShaderNodeMix")
    warm.data_type = "RGBA"
    nt.links.new(_math(nt, "GREATER_THAN", sep.outputs[1], 0.7), warm.inputs[0])
    warm.inputs[6].default_value = (1.0, 0.72, 0.42, 1)      # tungsten
    warm.inputs[7].default_value = (0.85, 0.92, 1.0, 1)      # office LED
    nt.links.new(warm.outputs[2], b.inputs["Emission Color"])
    strength = _math(nt, "MULTIPLY", lit, _math(nt, "ADD", 0.8, _math(nt, "MULTIPLY", sep.outputs[2], 1.6)))
    nt.links.new(strength, b.inputs["Emission Strength"])
    base = nt.nodes.new("ShaderNodeMix")                     # dark glass in the windows, concrete around
    base.data_type = "RGBA"
    nt.links.new(window, base.inputs[0])
    base.inputs[6].default_value = (0.07, 0.065, 0.065, 1)
    base.inputs[7].default_value = (0.02, 0.025, 0.035, 1)
    nt.links.new(base.outputs[2], b.inputs["Base Color"])
    rough = nt.nodes.new("ShaderNodeMapRange")
    nt.links.new(window, rough.inputs["Value"])
    rough.inputs["To Min"].default_value, rough.inputs["To Max"].default_value = 0.75, 0.08
    nt.links.new(rough.outputs["Result"], b.inputs["Roughness"])
    m.diffuse_color = (0.1, 0.1, 0.1, 1)
    return m


def ground_material():
    m = bpy.data.materials.new("city_ground")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    pos = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(geo.outputs["Position"], pos.inputs[0])
    road = []
    for axis in ("X", "Y"):
        f = _math(nt, "FRACT", _math(nt, "DIVIDE", pos.outputs[axis], BLOCK + STREET))
        road.append(_math(nt, "LESS_THAN", f, STREET / (BLOCK + STREET)))
    is_road = _math(nt, "MAXIMUM", road[0], road[1])
    col = nt.nodes.new("ShaderNodeMix")
    col.data_type = "RGBA"
    nt.links.new(is_road, col.inputs[0])
    col.inputs[6].default_value = (0.035, 0.045, 0.03, 1)    # yards and parks
    col.inputs[7].default_value = (0.03, 0.03, 0.032, 1)     # asphalt
    nt.links.new(col.outputs[2], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.85
    m.diffuse_color = (0.03, 0.03, 0.03, 1)
    return m


def dusk_sky(dome):
    """Map the dusk HDRI onto the backdrop dome (seen from inside), or keep a gradient if not fetched."""
    hdri = LIB / "hdri" / "qwantani_dusk_2_puresky_2k.exr"
    m = bpy.data.materials.new("city_dusk_sky")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = 0.22      # dusk: the sky is a backdrop, not daylight
    if hdri.exists():
        geo = nt.nodes.new("ShaderNodeNewGeometry")
        neg = nt.nodes.new("ShaderNodeVectorMath")
        neg.operation = "SCALE"
        neg.inputs["Scale"].default_value = -1.0
        nt.links.new(geo.outputs["Incoming"], neg.inputs[0])
        env = nt.nodes.new("ShaderNodeTexEnvironment")
        env.image = bpy.data.images.load(str(hdri), check_existing=True)
        nt.links.new(neg.outputs["Vector"], env.inputs["Vector"])
        nt.links.new(env.outputs["Color"], em.inputs["Color"])
    else:
        em.inputs["Color"].default_value = (0.1, 0.09, 0.22, 1)
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    dome.data.materials.clear()
    dome.data.materials.append(m)


def build_city(scene, o):
    coll = bpy.data.collections["SET_city"]
    keep = {"dusk_dome"}
    for ob in list(coll.objects):
        if ob.name not in keep:
            bpy.data.objects.remove(ob, do_unlink=True)
    dusk_sky(bpy.data.objects["dusk_dome"])
    rnd = random.Random(11)

    # ground
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=250.0)
    me = bpy.data.meshes.new("city_ground")
    bm.to_mesh(me)
    bm.free()
    g = bpy.data.objects.new("city_ground", me)
    coll.objects.link(g)
    g.location = o
    me.materials.append(ground_material())

    # buildings: one mesh, a few per block, low-rise under the flight path, taller toward +Y
    bm = bmesh.new()
    pitch = BLOCK + STREET
    for bx in range(int(X_RANGE[0] // pitch), int(X_RANGE[1] // pitch) + 1):
        for by in range(int(Y_RANGE[0] // pitch), int(Y_RANGE[1] // pitch) + 1):
            x0, y0 = bx * pitch + STREET, by * pitch + STREET
            if not (X_RANGE[0] < x0 < X_RANGE[1] and Y_RANGE[0] < y0 < Y_RANGE[1]):
                continue
            far = max(0.0, (y0 - 40.0) / 200.0)
            downtown = math.exp(-((x0 + 30) ** 2 + (y0 - 190) ** 2) / (2 * 70.0 ** 2))
            if rnd.random() < 0.08:
                continue                                            # a park
            n = rnd.choice((2, 3, 4))
            for i in range(n):
                for j in range(n):
                    w, d = BLOCK / n * rnd.uniform(0.6, 0.9), BLOCK / n * rnd.uniform(0.6, 0.9)
                    cx = x0 + BLOCK / n * (i + 0.5) + rnd.uniform(-2, 2)
                    cy = y0 + BLOCK / n * (j + 0.5) + rnd.uniform(-2, 2)
                    h = rnd.uniform(4, 10) * (1 + 1.5 * far) + rnd.uniform(0, 90) * downtown ** 1.5
                    if abs(cy) < 60:
                        h *= 0.55                                   # under the approach path: low-rise
                    h = max(3.9, round(h / 3.3) * 3.3 + 0.6)
                    verts = bmesh.ops.create_cube(bm, size=1.0)["verts"]
                    bmesh.ops.scale(bm, vec=(w, d, h), verts=verts)
                    bmesh.ops.translate(bm, vec=(cx, cy, h / 2), verts=verts)
    me = bpy.data.meshes.new("city_buildings")
    bm.to_mesh(me)
    bm.free()
    bld = bpy.data.objects.new("city_buildings", me)
    coll.objects.link(bld)
    bld.location = o
    me.materials.append(facade_material())

    # street lights along every street, car lights on the avenues
    lamp = plain("city_streetlight", (1.0, 0.62, 0.25), emission=40.0)
    head, tail = plain("city_headlight", (1.0, 0.95, 0.85), emission=30.0), plain("city_taillight", (1.0, 0.05, 0.02),
                                                                                    emission=30.0)
    bm_l, bm_c = bmesh.new(), bmesh.new()

    def lamp_at(p):
        v = bmesh.ops.create_icosphere(bm_l, subdivisions=1, radius=0.35)["verts"]
        bmesh.ops.translate(bm_l, vec=p, verts=v)
    kx = range(int(X_RANGE[0] // pitch), int(X_RANGE[1] // pitch) + 2)
    ky = range(int(Y_RANGE[0] // pitch), int(Y_RANGE[1] // pitch) + 2)
    for k in kx:                                                          # streets running along Y
        line = k * pitch + STREET / 2
        for t in range(int(Y_RANGE[0]), int(Y_RANGE[1]), 22):
            for side in (-1, 1):
                lamp_at((line + side * 4.0, t, 6.0))
        if k % 2 == 0:                                                    # avenues carry traffic
            for _ in range(14):
                yv = rnd.uniform(*Y_RANGE)
                for dx, mat_i in ((-1.6, 0), (1.6, 1)):
                    v = bmesh.ops.create_cube(bm_c, size=1.0)["verts"]
                    bmesh.ops.scale(bm_c, vec=(0.25, 1.2, 0.15), verts=v)
                    bmesh.ops.translate(bm_c, vec=(line + dx, yv, 0.7), verts=v)
                    for f in {f for vv in v for f in vv.link_faces}:
                        f.material_index = mat_i
    for k in ky:                                                          # cross streets along X
        line = k * pitch + STREET / 2
        for t in range(int(X_RANGE[0]), int(X_RANGE[1]), 22):
            for side in (-1, 1):
                lamp_at((t, line + side * 4.0, 6.0))
    for name, bmx, mats in (("city_streetlights", bm_l, [lamp]), ("city_traffic", bm_c, [head, tail])):
        me = bpy.data.meshes.new(name)
        bmx.to_mesh(me)
        bmx.free()
        ob = bpy.data.objects.new(name, me)
        coll.objects.link(ob)
        ob.location = o
        for m in mats:
            me.materials.append(m)
    # soft dusk light from the sky side, so the rooftops and the jet pick up the afterglow
    ld = bpy.data.lights.new("city_dusk_sun", "SUN")
    ld.energy, ld.color, ld.angle = 0.25, (1.0, 0.5, 0.35), math.radians(8)
    sun = bpy.data.objects.new("city_dusk_sun", ld)
    coll.objects.link(sun)
    sun.rotation_euler = (math.radians(84), 0, math.radians(200))
    return coll


def light_switch(f_start, f_end):
    """Sun lamps light every set at once: the golden 'Sun' is off while the dusk city is on screen
    (frames f_start..f_end), and the dusk sun is only on then."""
    gold, dusk = bpy.data.objects.get("Sun"), bpy.data.objects.get("city_dusk_sun")
    on = {gold: gold.data.energy if gold else 0, dusk: dusk.data.energy if dusk else 0}
    for lamp, inside in ((gold, 0.0), (dusk, 1.0)):
        if not lamp:
            continue
        for f, active in ((1, 1 - inside), (f_start - 1, 1 - inside), (f_start, inside), (f_end, inside),
                          (f_end + 1, 1 - inside)):
            lamp.data.energy = on[lamp] * active
            lamp.data.keyframe_insert("energy", frame=f)
        for fc in fcurves(lamp.data):
            for kp in fc.keyframe_points:
                kp.interpolation = "CONSTANT"
