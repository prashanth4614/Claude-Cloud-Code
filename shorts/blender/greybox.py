"""Grey-box (previz) sets: simple stand-in geometry at real scale, placed far apart so
every shot can share one film timeline. Each builder returns the objects the build
animates. In the realistic stage each set is swapped for its asset-library version
under the same object names, so cameras and animation carry over.
"""
import math
import random

import bpy
from mathutils import Matrix, Vector

from rigs import bezier, collection, empty, material, prim

SKY, CABIN, EAR, CITY = Vector((0, 0, 0)), Vector((300, 0, 0)), Vector((600, 0, 0)), Vector((900, 0, 0))


def _cut_near_half(ob, axis=1, keep_above=-0.08):
    """Delete faces on the camera side (-Y), turning a closed shape into a cutaway."""
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    doomed = [f for f in bm.faces if f.calc_center_median()[axis] < keep_above]
    bmesh.ops.delete(bm, geom=doomed, context="FACES")
    bm.to_mesh(ob.data)
    bm.free()


def _disc(name, coll, radius, rings, segments):
    """Flat disc with concentric rings (smooth when displaced by shape keys)."""
    verts, faces = [(0.0, 0.0, 0.0)], []
    for r in range(1, rings + 1):
        rad = radius * r / rings
        verts += [(rad * math.cos(2 * math.pi * k / segments), rad * math.sin(2 * math.pi * k / segments), 0.0)
                  for k in range(segments)]
    ring = lambda r, k: 1 + (r - 1) * segments + k % segments  # noqa: E731
    faces += [(0, ring(1, k), ring(1, k + 1)) for k in range(segments)]
    for r in range(1, rings):
        faces += [(ring(r, k), ring(r + 1, k), ring(r + 1, k + 1), ring(r, k + 1)) for k in range(segments)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    return ob


def _limb(name, coll, radius, mat, parent, origin, target_obj):
    """Cylinder from origin that stretches to target_obj (arms follow animated hands)."""
    ob = prim("cylinder", name, coll, mat=mat, vertices=16, radius=1, depth=1)
    ob.data.transform(Matrix.Rotation(-math.pi / 2, 4, "X"))
    ob.data.transform(Matrix.Translation((0, 0.5, 0)))
    ob.scale = (radius, 1, radius)
    ob.parent = parent
    ob.location = origin
    c = ob.constraints.new("STRETCH_TO")
    c.target = target_obj
    c.volume = "NO_VOLUME"
    c.rest_length = 1.0  # mesh is 1 unit long, so length == distance to the hand
    return ob


# -------------------------------------------------------------------- sky ---
def build_sky(scene):
    coll = collection("SET_sky", scene.collection)
    white = material("cloud", (0.95, 0.95, 0.97), rough=1.0)
    rnd = random.Random(7)
    for i in range(80):  # cloud deck below and around the climb
        x, y = rnd.uniform(-90, 110), rnd.uniform(-60, 140)
        z = rnd.uniform(-9, -3) if i < 60 else rnd.uniform(2, 14)
        s = rnd.uniform(3, 9)
        prim("ico_sphere", f"cloud_{i:02d}", coll, SKY + Vector((x, y, z)), (s, s * 0.8, s * 0.35), mat=white, subdivisions=2)
    prim("plane", "cloud_sea", coll, SKY + Vector((0, 0, -10)), (900, 900, 1),
         mat=material("cloud_sea", (0.86, 0.88, 0.93), rough=1.0))
    sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
    sun.data.energy, sun.data.color, sun.data.angle = 4.0, (1.0, 0.82, 0.6), math.radians(2)
    sun.rotation_euler = (math.radians(80), 0, math.radians(60))
    coll.objects.link(sun)
    jet = build_jet(scene)
    return {"jet": jet}


def build_jet(scene):
    coll = collection("ASSET_jet", scene.collection)
    body = material("jet_white", (0.9, 0.92, 0.95), rough=0.3)
    accent = material("jet_red", (0.8, 0.1, 0.12), rough=0.4)
    dark = material("jet_dark", (0.1, 0.12, 0.16), rough=0.2)
    root = empty("Jet", coll)
    prim("cylinder", "jet_fuselage", coll, (0, 0, 0), (0.95, 0.95, 6), (0, 90, 0), body, root, vertices=24)
    prim("uv_sphere", "jet_nose", coll, (6, 0, 0), (1.6, 0.95, 0.95), mat=body, parent=root)
    prim("cone", "jet_tailcone", coll, (-7.2, 0, 0.2), (0.95, 0.95, 1.4), (0, -90, 0), body, root, vertices=24)
    prim("cube", "jet_wings", coll, (0.3, 0, -0.35), (1.6, 7.5, 0.09), (0, 0, 0), body, root)
    prim("cube", "jet_tailfin", coll, (-7.6, 0, 1.9), (1.3, 0.08, 1.6), (0, -20, 0), accent, root)
    prim("cube", "jet_stabilizer", coll, (-7.6, 0, 0.5), (0.8, 2.8, 0.07), mat=body, parent=root)
    for s in (-1, 1):
        prim("cylinder", f"jet_engine_{s}", coll, (0.8, s * 3.3, -1.0), (0.45, 0.45, 1.1), (0, 90, 0), dark, root, vertices=20)
    prim("cube", "jet_windows", coll, (0.8, -0.94, 0.35), (4.6, 0.02, 0.12), mat=dark, parent=root)
    gear = empty("Jet_gear", coll, (0, 0, 0), root)
    for i, (x, y) in enumerate([(3.5, 0), (-0.5, 1.5), (-0.5, -1.5)]):
        prim("cylinder", f"jet_gear_{i}", coll, (x, y, -1.5), (0.18, 0.18, 0.7), mat=dark, parent=gear)
    gear.scale = (1, 1, 0.001)
    return root


# ------------------------------------------------------------------ cabin ---
def build_cabin(scene):
    coll = collection("SET_cabin", scene.collection)
    wall = material("cabin_wall", (0.82, 0.83, 0.85), rough=0.7)
    seatm = material("seat_navy", (0.12, 0.18, 0.38), rough=0.9)
    floor = material("cabin_floor", (0.25, 0.25, 0.28), rough=0.9)
    sky = material("window_sky", (0.55, 0.75, 1.0), emission=3.0)
    o = CABIN
    prim("cube", "cabin_floor", coll, o + Vector((0, 0, -0.02)), (3, 6, 0.02), mat=floor)
    prim("cube", "cabin_ceiling", coll, o + Vector((0, 0, 2.3)), (3, 6, 0.02), mat=wall)
    prim("cube", "cabin_wall_R", coll, o + Vector((1.85, 0, 1.15)), (0.05, 6, 1.15), mat=wall)
    prim("cube", "cabin_wall_back", coll, o + Vector((0, 4, 1.15)), (3, 0.05, 1.15), mat=wall)
    for i, y in enumerate((-0.25, 1.75)):
        prim("cube", f"window_frame_{i}", coll, o + Vector((1.81, y, 1.75)), (0.03, 0.26, 0.32), mat=wall)
        prim("cube", f"window_pane_{i}", coll, o + Vector((1.79, y, 1.75)), (0.02, 0.2, 0.26), mat=sky)
    for row, y in enumerate((0.35, -1.6)):  # Max's row and the row in front (seat backs)
        for x in ((-0.6, 0.6, 1.2) if row == 0 else (-0.6, 1.25)):  # leave a camera lane in front of Max
            prim("cube", f"seat_{row}_{x}", coll, o + Vector((x, y, 0.45)), (0.26, 0.26, 0.08), mat=seatm)
            prim("cube", f"seatback_{row}_{x}", coll, o + Vector((x, y + 0.27, 1.05)), (0.26, 0.07, 0.6), mat=seatm)
    prim("cube", "overhead_bins", coll, o + Vector((1.2, 0, 2.1)), (0.5, 6, 0.2), mat=wall)
    key = bpy.data.objects.new("cabin_key", bpy.data.lights.new("cabin_key", "AREA"))
    key.data.energy, key.data.size, key.data.color = 220, 2.0, (1.0, 0.88, 0.72)
    key.location = o + Vector((-0.6, -1.4, 2.25))
    coll.objects.link(key)
    win = bpy.data.objects.new("window_light", bpy.data.lights.new("window_light", "AREA"))
    win.data.energy, win.data.size, win.data.color = 160, 0.6, (0.75, 0.85, 1.0)
    win.location, win.rotation_euler = o + Vector((1.7, -0.1, 1.75)), (0, math.radians(-90), 0)
    coll.objects.link(win)
    return build_max(scene, o + Vector((0.0, 0.35, 0.0)))


def build_max(scene, at):
    """Max stand-in, in his reference colours (teal tee, dark jeans, white sneakers, dark-brown hair)."""
    coll = collection("CHAR_max", scene.collection)
    skin = material("max_skin", (0.86, 0.62, 0.48), rough=0.55)
    tee = material("max_tee", (0.18, 0.40, 0.44), rough=0.85)
    jeans = material("max_jeans", (0.12, 0.15, 0.24), rough=0.8)
    shoe = material("max_shoes", (0.92, 0.92, 0.92), rough=0.6)
    hair = material("max_hair", (0.12, 0.07, 0.04), rough=0.6)
    dark = material("max_eyes", (0.08, 0.05, 0.03), rough=0.2)
    lip = material("max_mouth", (0.45, 0.18, 0.16), rough=0.5)
    root = empty("Max", coll, at)
    prim("uv_sphere", "max_torso", coll, (0, 0, 1.12), (0.24, 0.15, 0.33), mat=tee, parent=root)
    prim("cylinder", "max_neck", coll, (0, 0, 1.47), (0.055, 0.055, 0.07), mat=skin, parent=root)
    for s in (-1, 1):
        prim("cylinder", f"max_thigh_{s}", coll, (s * 0.11, -0.22, 0.6), (0.085, 0.085, 0.24), (90, 0, 0), jeans, root)
        prim("cylinder", f"max_shin_{s}", coll, (s * 0.11, -0.46, 0.32), (0.07, 0.07, 0.24), mat=jeans, parent=root)
        prim("cube", f"max_shoe_{s}", coll, (s * 0.11, -0.52, 0.05), (0.06, 0.13, 0.05), mat=shoe, parent=root)
    head = empty("Max_head", coll, (0, 0, 1.52), root)  # pivot at the neck: nod, tilt, look
    prim("uv_sphere", "max_head_mesh", coll, (0, 0, 0.14), (0.105, 0.115, 0.135), mat=skin, parent=head)
    prim("uv_sphere", "max_hair", coll, (0, 0.025, 0.2), (0.115, 0.12, 0.1), mat=hair, parent=head)
    for s in (-1, 1):
        prim("uv_sphere", f"max_ear_{s}", coll, (s * 0.108, 0.005, 0.135), (0.018, 0.03, 0.04), mat=skin, parent=head)
        prim("uv_sphere", f"max_eye_{s}", coll, (s * 0.04, -0.105, 0.16), (0.016, 0.01, 0.016), mat=dark, parent=head)
    prim("uv_sphere", "max_mouth", coll, (0, -0.107, 0.075), (0.03, 0.01, 0.008), mat=lip, parent=head)
    hands = {}
    for s, side in ((1, "L"), (-1, "R")):  # Max faces -Y, so his left is +X
        h = prim("uv_sphere", f"Max_hand_{side}", coll, (s * 0.16, -0.32, 0.86), (0.045, 0.05, 0.035), mat=skin, parent=root)
        hands[side] = h
        _limb(f"max_arm_{side}", coll, 0.045, tee, root, (s * 0.25, 0, 1.33), h)
    return {"max": root, "head": head, "hands": hands, "ear_L": bpy.data.objects["max_ear_1"],
            "mouth": bpy.data.objects["max_mouth"], "eyes": [bpy.data.objects["max_eye_-1"], bpy.data.objects["max_eye_1"]]}


# -------------------------------------------------------------------- ear ---
TUBE_PTS = [Vector((2.6, 0.15, -2.2)), Vector((2.4, 0.15, -6.0)), Vector((-0.5, 0.15, -8.0)), Vector((-2.4, 0.15, -10.4))]


def build_ear(scene):
    coll = collection("SET_ear", scene.collection)
    o = EAR
    tissue = material("tissue", (0.78, 0.38, 0.36), rough=0.35)
    cavity = material("tissue_dark", (0.42, 0.13, 0.15), rough=0.5)
    bone = material("ossicle", (0.93, 0.88, 0.78), rough=0.4)
    dome = material("ear_dome", (0.06, 0.015, 0.025), emission=1.0)
    d = prim("uv_sphere", "ear_dome", coll, o, (90, 90, 90), mat=dome, segments=32, ring_count=16)
    d.visible_shadow = False
    canal = prim("cylinder", "ear_canal", coll, o + Vector((-8.6, 0, 0)), (1.5, 1.5, 7.8), (0, 90, 0), tissue, vertices=48,
                 end_fill_type="NOTHING")  # open tube: the eardrum is the end of the canal
    _cut_near_half(canal)
    chamber = prim("uv_sphere", "middle_ear", coll, o + Vector((2.2, 0, 0)), (2.6, 2.6, 2.6), mat=cavity, segments=48, ring_count=24)
    _cut_near_half(chamber)
    throat = prim("uv_sphere", "throat", coll, o + Vector((-3.4, 0, -12.6)), (2.6, 2.6, 2.2), mat=cavity, segments=40, ring_count=20)
    _cut_near_half(throat)
    # eardrum: a disc with shape keys Out (towards the canal) and In
    drum = _disc("Eardrum", coll, 1.55, rings=14, segments=48)
    drum.location, drum.rotation_euler = o + Vector((-0.8, 0, 0)), (0, math.radians(90), 0)
    drum.data.materials.append(material("eardrum", (0.97, 0.9, 0.84), rough=0.25, emission=0.0))
    drum.shape_key_add(name="Basis")
    for name, sign in (("Out", -1.1), ("In", 1.0)):
        sk = drum.shape_key_add(name=name)
        for v in sk.data:
            r2 = (v.co.x ** 2 + v.co.y ** 2) / 1.55 ** 2
            v.co.z = sign * (1 - r2)
    pts = [Vector((-0.75, 0, 0)), Vector((0.6, 0.2, 0.9)), Vector((1.4, 0.3, 0.8)), Vector((2.2, 0.3, 0.1))]
    for i in range(3):
        a, b = o + pts[i], o + pts[i + 1]
        bn = prim("cylinder", f"ossicle_{i}", coll, (a + b) / 2, (0.12, 0.12, (b - a).length / 2), mat=bone, vertices=16)
        bn.rotation_mode = "QUATERNION"
        bn.rotation_quaternion = (b - a).to_track_quat("Z", "Y")
    # Eustachian tube: a bevelled curve whose thickness opens and closes
    cu = bpy.data.curves.new("eustachian_tube", "CURVE")
    cu.dimensions, cu.bevel_depth, cu.bevel_resolution = "3D", 0.16, 6
    sp = cu.splines.new("BEZIER")
    sp.bezier_points.add(1)
    p0, p1 = sp.bezier_points
    p0.co, p0.handle_left, p0.handle_right = TUBE_PTS[0], TUBE_PTS[0] + Vector((0, 0, 1)), TUBE_PTS[1]
    p1.co, p1.handle_left, p1.handle_right = TUBE_PTS[3], TUBE_PTS[2], TUBE_PTS[3] + Vector((-1, 0, -1))
    tube = bpy.data.objects.new("Eustachian_tube", cu)
    tube.location = o
    coll.objects.link(tube)
    tube.data.materials.append(material("tube", (0.78, 0.38, 0.36), rough=0.35))
    # air molecules: cool blue outside (canal), warm amber inside (middle ear)
    blue = material("air_outside", (0.35, 0.75, 1.0), emission=2.0)
    amber = material("air_inside", (1.0, 0.62, 0.2), emission=2.0)
    rnd = random.Random(3)
    outside = [prim("uv_sphere", f"air_out_{i:02d}", coll, o + Vector((rnd.uniform(-15, -1.6), rnd.uniform(0.0, 1.2),
                    rnd.uniform(-1.1, 1.1))), (0.11,) * 3, mat=blue, segments=12, ring_count=6) for i in range(48)]
    inside = [prim("uv_sphere", f"air_in_{i:02d}", coll, o + Vector((2.2, 0, 0)) + Vector((rnd.uniform(-2.0, 2.0),
                   rnd.uniform(0.0, 1.9), rnd.uniform(-2.0, 2.0))).normalized() * rnd.uniform(0.4, 2.1),
                   (0.11,) * 3, mat=amber, segments=12, ring_count=6) for i in range(36)]
    flow = [prim("uv_sphere", f"air_flow_{i:02d}", coll, o + TUBE_PTS[0], (0.0,) * 3, mat=amber, segments=12, ring_count=6)
            for i in range(14)]
    flash = bpy.data.objects.new("pop_flash", bpy.data.lights.new("pop_flash", "POINT"))
    flash.data.energy, flash.data.color, flash.location = 0, (1.0, 0.95, 0.8), o + Vector((-1.4, -2.0, 0))
    coll.objects.link(flash)
    ring = prim("torus", "pop_ring", coll, o + Vector((-0.9, 0, 0)), (0, 0, 0), (0, 90, 0),
                material("pop_ring", (1.0, 0.95, 0.75), emission=6.0), major_radius=1.0, minor_radius=0.04)
    for name, loc, energy, col in (("ear_key", (-6, -14, 8), 3000, (1.0, 0.9, 0.85)),
                                   ("ear_rim", (6, 10, 4), 1500, (1.0, 0.6, 0.5)),
                                   ("ear_fill", (2, -10, -9), 900, (0.8, 0.5, 0.6)),
                                   ("canal_glow", (-4.5, 0.6, 0.4), 250, (1.0, 0.75, 0.65)),
                                   ("chamber_glow", (2.2, 1.2, 0.3), 200, (1.0, 0.7, 0.45))):
        lt = bpy.data.objects.new(name, bpy.data.lights.new(name, "POINT"))
        lt.data.energy, lt.data.color, lt.location = energy, col, o + Vector(loc)
        lt.data.shadow_soft_size = 3
        coll.objects.link(lt)
    return {"drum": drum, "tube": tube, "outside": outside, "inside": inside, "flow": flow, "flash": flash, "ring": ring}


def tube_point(t):
    return EAR + bezier(TUBE_PTS[0], TUBE_PTS[1], TUBE_PTS[2], TUBE_PTS[3], t)


# ------------------------------------------------------------------- city ---
def build_city(scene):
    coll = collection("SET_city", scene.collection)
    o = CITY
    dusk = material("dusk_dome", (0.10, 0.09, 0.22), emission=1.0)
    d = prim("uv_sphere", "dusk_dome", coll, o, (260, 260, 260), mat=dusk, segments=32, ring_count=16)
    d.visible_shadow = False
    prim("plane", "dusk_horizon", coll, o + Vector((0, 220, 20)), (300, 1, 30), (90, 0, 0),
         material("dusk_glow", (1.0, 0.45, 0.2), emission=2.5))
    prim("plane", "city_ground", coll, o, (260, 260, 1), mat=material("ground", (0.03, 0.03, 0.04), rough=1))
    bld = material("building", (0.05, 0.05, 0.07), rough=0.8)
    lights = material("city_lights", (1.0, 0.75, 0.35), emission=6.0)
    rnd = random.Random(5)
    for i in range(160):
        x, y = rnd.uniform(-60, 120), rnd.uniform(-40, 160)
        h = rnd.uniform(2, 14)
        prim("cube", f"bld_{i:03d}", coll, o + Vector((x, y, h / 2)), (rnd.uniform(1, 3), rnd.uniform(1, 3), h / 2), mat=bld)
        if i % 2 == 0:
            prim("cube", f"lit_{i:03d}", coll, o + Vector((x, y - 1.2, h * 0.6)), (0.6, 0.05, h * 0.25), mat=lights)
    return {}
