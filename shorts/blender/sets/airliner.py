"""A modelled twin-engine airliner (original design and livery, no real airline) and a realistic sky.

build_airliner(coll) replaces the grey-box jet under the same rig: the "Jet" empty (animated
flight path) and the "Jet_gear" empty (its z-scale drops the landing gear). Dimensions match
the grey-box jet (about 16 m long, 15 m span) so every camera framing carries over.
The jet faces +X; its left wing is +Y.

realistic_sky(scene, sky_coll) swaps the grey-box clouds for a displaced, softly lit cloud deck
and puffy cumulus, and lights the world with a CC0 Poly Haven sunset HDRI.
"""
import math

import bmesh
import bpy
from mathutils import Vector

from .pbr import LIB, plain

R = 0.95                     # fuselage radius
NOSE_X, TAIL_X = 7.6, -8.6   # nose tip / tail tip


# --------------------------------------------------------------- geometry --
def _obj(name, bm, coll, mat, parent, smooth=True, subsurf=0):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    ob.parent = parent
    if mat:
        me.materials.append(mat)
    for p in me.polygons:
        p.use_smooth = smooth
    if subsurf:
        s = ob.modifiers.new("smooth", "SUBSURF")
        s.levels, s.render_levels = 1, subsurf
    return ob


def fuselage_section(x):
    """(radius, centre z) of the fuselage at station x: ogive nose, constant barrel, upswept tail."""
    if x > 4.6:                                   # nose
        t = (x - 4.6) / (NOSE_X - 4.6)
        r = R * (1 - t ** 2.2) ** 0.5
        return max(r, 0.0), -0.18 * t ** 1.5 * R
    if x < -4.2:                                  # tail cone, bottom sweeps up
        t = (-4.2 - x) / (-4.2 - TAIL_X)
        r = R * (1 - 0.86 * t ** 1.15)
        return r, (R - r) * 0.92
    return R, 0.0


def loft(rings_fn, stations, segs, cap_start=True, cap_end=True):
    """Loft closed rings (list of Vector) through stations; optional pointed caps."""
    bm = bmesh.new()
    rings = [[bm.verts.new(v) for v in rings_fn(s)] for s in stations]
    for a, b in zip(rings, rings[1:]):
        for j in range(segs):
            k = (j + 1) % segs
            bm.faces.new((a[j], a[k], b[k], b[j]))
    if cap_start:
        bm.faces.new(list(reversed(rings[0])))
    if cap_end:
        bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def fuselage(coll, mats, root):
    segs = 48
    xs = [TAIL_X + 0.02] + [TAIL_X + (NOSE_X - TAIL_X) * (i / 90) ** 1.0 for i in range(1, 90)] + [NOSE_X - 0.01]

    def ring(x):
        r, zc = fuselage_section(x)
        r = max(r, 0.02)
        return [Vector((x, r * math.cos(2 * math.pi * j / segs), zc + r * math.sin(2 * math.pi * j / segs) * 1.04))
                for j in range(segs)]
    return _obj("jet_fuselage", loft(ring, xs, segs), coll, mats["livery"], root, subsurf=2)


AIRFOIL = None


def airfoil(n=20):
    """Unit-chord cambered airfoil (NACA 2412-like), points from TE over the top to the LE and back."""
    global AIRFOIL
    if AIRFOIL:
        return AIRFOIL
    pts = []
    for i in range(n + 1):
        b = math.pi * i / n
        x = 0.5 * (1 + math.cos(b))                      # TE (1) -> LE (0)
        t = 0.12 * 5 * (0.2969 * math.sqrt(x) - 0.126 * x - 0.3516 * x ** 2 + 0.2843 * x ** 3 - 0.1036 * x ** 4)
        c = 0.02 / 0.16 * (0.8 * x - x * x) if x < 0.4 else 0.02 / 0.36 * (0.2 + 0.8 * x - x * x)
        pts.append((x, c + t))
    for i in range(1, n):
        b = math.pi * i / n
        x = 0.5 * (1 - math.cos(b))                      # LE -> TE underside
        t = 0.12 * 5 * (0.2969 * math.sqrt(x) - 0.126 * x - 0.3516 * x ** 2 + 0.2843 * x ** 3 - 0.1036 * x ** 4)
        c = 0.02 / 0.16 * (0.8 * x - x * x) if x < 0.4 else 0.02 / 0.36 * (0.2 + 0.8 * x - x * x)
        pts.append((x, c - t))
    AIRFOIL = pts
    return pts


def surface(name, coll, mat, root, sections, vertical=False, thick=1.0):
    """Lifting surface lofted through sections [(le_x, span_pos, height, chord, thickness_scale)].
    Horizontal: span along Y, thickness in Z. vertical=True: span along Z, thickness in Y (the fin)."""
    pts = airfoil()
    segs = len(pts)

    def ring(sec):
        le, span, h, chord, ts = sec
        out = []
        for u, v in pts:
            x = le - u * chord
            if vertical:
                out.append(Vector((x, v * chord * ts * thick * 0.5, span)))
            else:
                out.append(Vector((x, span, h + v * chord * ts * thick)))
        return out
    return _obj(name, loft(ring, sections, segs), coll, mat, root, subsurf=1)


def wings(coll, mats, root):
    sweep, dihedral = math.radians(27), math.radians(5)
    for side, s in (("L", 1), ("R", -1)):
        secs = []
        for i in range(9):
            t = i / 8
            y = 0.55 + (7.4 - 0.55) * t
            chord = 3.4 + (1.0 - 3.4) * t ** 0.9
            le = 1.9 - (y - 0.55) * math.tan(sweep)
            z = -0.45 + (y - 0.55) * math.tan(dihedral)
            secs.append((le, s * y, z, chord, 1.0 - 0.25 * t))
        if s < 0:
            secs = secs[::-1]
        surface(f"jet_wing_{side}", coll, mats["paint"], root, secs)
        # winglet: a small swept fin canted up at the tip
        tip_le = 1.9 - (7.4 - 0.55) * math.tan(sweep)
        tip_z = -0.45 + (7.4 - 0.55) * math.tan(dihedral)
        wl = surface(f"jet_winglet_{side}", coll, mats["accent"], root,
                     [(tip_le - 0.05, tip_z + 0.0, 0, 0.95, 0.8), (tip_le - 0.55, tip_z + 0.85, 0, 0.35, 0.8)],
                     vertical=True, thick=0.6)
        wl.location = (0, s * 7.38, 0)
        wl.rotation_euler = (math.radians(-12 * s), 0, 0)
        # nav light: red on the left tip, green on the right
        _light_dot(f"jet_nav_{side}", coll, root, (tip_le - 0.3, s * 7.45, tip_z + 0.02),
                   mats["nav_red"] if s > 0 else mats["nav_green"])
    for side, s in (("L", 1), ("R", -1)):
        secs = []
        for i in range(5):
            t = i / 4
            y = 0.25 + (3.0 - 0.25) * t
            secs.append((-6.3 - (y - 0.25) * math.tan(math.radians(32)), s * y, 0.42 + 0.12 * t, 1.8 - 1.1 * t, 0.9))
        if s < 0:
            secs = secs[::-1]
        surface(f"jet_stabilizer_{side}", coll, mats["paint"], root, secs)
    fin = []
    for i in range(6):
        t = i / 5
        z = 0.55 + 3.0 * t
        fin.append((-5.5 - 3.0 * t * math.tan(math.radians(38)), z, 0, 2.9 - 1.8 * t, 1.0))
    surface("jet_tailfin", coll, mats["accent"], root, fin, vertical=True, thick=0.9)
    _light_dot("jet_beacon_top", coll, root, (-1.0, 0, R + 0.06), mats["nav_red"])
    _light_dot("jet_beacon_bottom", coll, root, (0.5, 0, -R - 0.06), mats["nav_red"])
    _light_dot("jet_strobe_tail", coll, root, (TAIL_X + 0.05, 0, 0.8), mats["strobe"])


def _light_dot(name, coll, root, loc, mat):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=6, radius=0.07)
    ob = _obj(name, bm, coll, mat, root)
    ob.location = loc
    return ob


def engines(coll, mats, root):
    prof = [(2.25, 0.44), (2.28, 0.49), (2.2, 0.54), (1.8, 0.58), (1.0, 0.58), (0.2, 0.53), (-0.35, 0.42)]
    segs = 48
    for side, s in (("L", 1), ("R", -1)):
        c = Vector((0.0, s * 3.1, -1.0))

        def ring(p):
            x, r = p
            return [c + Vector((x, r * math.cos(2 * math.pi * j / segs), r * math.sin(2 * math.pi * j / segs)))
                    for j in range(segs)]
        nac = _obj(f"jet_engine_{side}", loft(ring, prof, segs, cap_start=True, cap_end=False), coll, mats["paint"],
                   root, subsurf=2)
        # intake: dark inner duct, the fan, a chrome lip and a spinner
        lip = bpy.data.meshes.new(f"jet_intake_lip_{side}")
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=False, segments=segs, radius1=0.44, radius2=0.41, depth=0.25)
        bm.to_mesh(lip)
        bm.free()
        lo = bpy.data.objects.new(f"jet_intake_lip_{side}", lip)
        coll.objects.link(lo)
        lo.parent, lo.location, lo.rotation_euler = root, c + Vector((2.18, 0, 0)), (0, math.radians(-90), 0)
        lip.materials.append(mats["chrome"])
        bm = bmesh.new()
        bmesh.ops.create_circle(bm, cap_ends=True, segments=segs, radius=0.42)
        fan = _obj(f"jet_fan_{side}", bm, coll, mats["fan"], root)
        fan.location, fan.rotation_euler = c + Vector((2.0, 0, 0)), (0, math.radians(90), 0)
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=32, radius1=0.13, radius2=0.0, depth=0.3)
        sp = _obj(f"jet_spinner_{side}", bm, coll, mats["chrome"], root)
        sp.location, sp.rotation_euler = c + Vector((2.12, 0, 0)), (0, math.radians(90), 0)
        bm = bmesh.new()                                        # exhaust cone
        bmesh.ops.create_cone(bm, cap_ends=True, segments=32, radius1=0.3, radius2=0.04, depth=0.7)
        ex = _obj(f"jet_exhaust_{side}", bm, coll, mats["metal_dark"], root)
        ex.location, ex.rotation_euler = c + Vector((-0.6, 0, 0)), (0, math.radians(-90), 0)
        bm = bmesh.new()                                        # pylon up into the wing
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(2.0, 0.16, 0.5), verts=bm.verts)
        py = _obj(f"jet_pylon_{side}", bm, coll, mats["paint"], root, smooth=False)
        py.location = c + Vector((0.6, 0, 0.62))
        bv = py.modifiers.new("bevel", "BEVEL")
        bv.width, bv.segments = 0.06, 3


def windows(coll, mats, root):
    """Cabin windows and cockpit panes as thin dark glass inlays on the fuselage."""
    bm = bmesh.new()
    zc, h, w, pitch = 0.27, 0.17, 0.12, 0.42
    for side in (1, -1):
        x = 4.3
        while x > -5.6:
            if not (2.4 < x < 2.9 or -4.6 < x < -4.1):            # gaps for the doors
                y = side * (math.sqrt(R * R - zc * zc) * 1.0 + 0.004)
                ring = []
                for k in range(16):
                    a = 2 * math.pi * k / 16
                    cx, cz = math.cos(a), math.sin(a)
                    sx = math.copysign(abs(cx) ** 0.6, cx) * w / 2  # rounded rectangle (superellipse)
                    sz = math.copysign(abs(cz) ** 0.6, cz) * h / 2
                    ring.append(bm.verts.new((x + sx, y, zc + sz * 1.04)))
                bm.faces.new(ring if side > 0 else ring[::-1])
            x -= pitch
    # cockpit: four panes wrapping the nose
    for k, (dx, ang) in enumerate(((6.15, 28), (6.35, 10), (6.35, -10), (6.15, -28))):
        r, zc2 = fuselage_section(dx)
        a = math.radians(ang)
        cz = zc2 + r * 0.5
        y = math.sin(a) * r * 0.86 + math.copysign(0.004, ang)
        x0 = dx + 0.05 * math.cos(a)
        quad = [bm.verts.new(v) for v in ((x0 - 0.2, y * 1.02, cz - 0.12), (x0 + 0.18, y * 0.9, cz - 0.12),
                                          (x0 + 0.1, y * 0.86, cz + 0.12), (x0 - 0.22, y * 0.98, cz + 0.12))]
        bm.faces.new(quad if ang > 0 else quad[::-1])
    return _obj("jet_windows", bm, coll, mats["glass"], root, smooth=False)


def gear(coll, mats, gear_root):
    for i, (x, y, z, n) in enumerate([(5.0, 0, -0.9, 2), (-0.3, 1.4, -0.85, 2), (-0.3, -1.4, -0.85, 2)]):
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=0.07, radius2=0.07, depth=1.1)
        leg = _obj(f"jet_gear_leg_{i}", bm, coll, mats["chrome"], gear_root)
        leg.location = (x, y, z - 0.55)
        for w in range(n):
            bm = bmesh.new()
            bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=0.3, radius2=0.3, depth=0.22)
            wh = _obj(f"jet_gear_wheel_{i}_{w}", bm, coll, mats["tyre"], gear_root, subsurf=1)
            wh.location = (x, y + (w - 0.5) * 0.3, z - 1.1)
            wh.rotation_euler = (math.radians(90), 0, 0)


def livery_material():
    """Original livery: white body, light-grey belly, a teal cheatline, a teal tail (matches Max's tee)."""
    m = bpy.data.materials.new("jet_livery")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Roughness"].default_value = 0.22
    if "Coat Weight" in b.inputs:
        b.inputs["Coat Weight"].default_value = 0.7
        b.inputs["Coat Roughness"].default_value = 0.05
    coord = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(coord.outputs["Object"], sep.inputs[0])

    def band(lo, hi, soft=0.01):
        a = nt.nodes.new("ShaderNodeMapRange")
        a.inputs["From Min"].default_value, a.inputs["From Max"].default_value = lo - soft, lo
        nt.links.new(sep.outputs["Z"], a.inputs["Value"])
        bnode = nt.nodes.new("ShaderNodeMapRange")
        bnode.inputs["From Min"].default_value, bnode.inputs["From Max"].default_value = hi + soft, hi
        nt.links.new(sep.outputs["Z"], bnode.inputs["Value"])
        mul = nt.nodes.new("ShaderNodeMath")
        mul.operation = "MULTIPLY"
        nt.links.new(a.outputs["Result"], mul.inputs[0])
        nt.links.new(bnode.outputs["Result"], mul.inputs[1])
        return mul.outputs[0]
    belly = band(-3.0, -0.5, 0.05)
    stripe = band(-0.2, -0.06, 0.008)
    c1 = nt.nodes.new("ShaderNodeMix")
    c1.data_type = "RGBA"
    nt.links.new(belly, c1.inputs[0])
    c1.inputs[6].default_value = (0.93, 0.94, 0.95, 1)
    c1.inputs[7].default_value = (0.7, 0.72, 0.76, 1)
    c2 = nt.nodes.new("ShaderNodeMix")
    c2.data_type = "RGBA"
    nt.links.new(stripe, c2.inputs[0])
    nt.links.new(c1.outputs[2], c2.inputs[6])
    c2.inputs[7].default_value = (0.02, 0.36, 0.42, 1)
    nt.links.new(c2.outputs[2], b.inputs["Base Color"])
    m.diffuse_color = (0.93, 0.94, 0.95, 1)
    return m


def materials():
    paint = plain("jet_paint", (0.93, 0.94, 0.95), rough=0.22, coat=0.7)
    return {
        "livery": livery_material(),
        "paint": paint,
        "accent": plain("jet_teal", (0.02, 0.36, 0.42), rough=0.25, coat=0.7),
        "chrome": plain("jet_chrome", (0.8, 0.8, 0.82), rough=0.12, metal=1.0),
        "metal_dark": plain("jet_metal_dark", (0.25, 0.25, 0.27), rough=0.35, metal=1.0),
        "fan": plain("jet_fan", (0.05, 0.05, 0.06), rough=0.3, metal=0.8),
        "glass": plain("jet_window_glass", (0.015, 0.02, 0.03), rough=0.05, coat=1.0),
        "tyre": plain("jet_tyre", (0.03, 0.03, 0.03), rough=0.7),
        "nav_red": plain("jet_nav_red", (1.0, 0.05, 0.03), emission=25.0),
        "nav_green": plain("jet_nav_green", (0.05, 1.0, 0.2), emission=25.0),
        "strobe": plain("jet_strobe", (1.0, 1.0, 1.0), emission=30.0),
    }


def build_airliner(scene):
    """Replace the grey-box jet's meshes with the airliner, keeping the Jet / Jet_gear rig."""
    root = bpy.data.objects["Jet"]
    gear_root = bpy.data.objects["Jet_gear"]
    coll = root.users_collection[0]
    for ob in list(coll.objects):
        if ob.type == "MESH":
            bpy.data.objects.remove(ob, do_unlink=True)
    mats = materials()
    fuselage(coll, mats, root)
    wings(coll, mats, root)
    engines(coll, mats, root)
    windows(coll, mats, root)
    gear(coll, mats, gear_root)
    return root


# -------------------------------------------------------------------- sky ---
def cloud_material():
    """Sunlit cloud: bright, soft, light scattering deep inside (subsurface), no specular glint."""
    m = bpy.data.materials.get("cloud_real")
    if m:
        return m
    m = bpy.data.materials.new("cloud_real")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.95, 0.95, 0.97, 1)
    b.inputs["Roughness"].default_value = 1.0
    for k, v in (("Subsurface Weight", 1.0), ("Subsurface Scale", 3.0), ("Specular IOR Level", 0.0),
                 ("Sheen Weight", 0.6)):
        if k in b.inputs:
            b.inputs[k].default_value = v
    if "Subsurface Radius" in b.inputs:
        b.inputs["Subsurface Radius"].default_value = (1.0, 0.95, 0.9)
    coord = nt.nodes.new("ShaderNodeTexCoord")
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = 0.08
    n.inputs["Detail"].default_value = 12
    n.inputs["Roughness"].default_value = 0.65
    nt.links.new(coord.outputs["Object"], n.inputs["Vector"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.5
    bump.inputs["Distance"].default_value = 1.5
    nt.links.new(n.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    m.diffuse_color = (0.95, 0.95, 0.97, 1)
    return m


def cloud_volume_material(noise_space):
    """Volumetric cumulus lobe (recipe from Codex review 002): the noise perturbs the BOUNDARY, so the
    container's ellipsoid never shows; density fades to 0 before the hull; noise is anchored to one
    shared unit-scale Empty, so billows are the same real size in every lobe.
        r = |2*Generated - 1|      N = noise(P, 0.7, detail 3)      F = noise(P, 4, detail 2)
        t = clamp((0.80 - r + 0.15*(2N - 1)) / 0.25)      density = k * smoothstep(t) * (0.7 + 0.3 F)"""
    m = bpy.data.materials.get("cloud_volume")
    if m:
        return m
    m = bpy.data.materials.new("cloud_volume")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    L = nt.links.new

    def math(op, a, b=None):
        n = nt.nodes.new("ShaderNodeMath")
        n.operation = op
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = v
            else:
                L(v, n.inputs[i])
        return n.outputs[0]
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    vol = nt.nodes.new("ShaderNodeVolumePrincipled")
    vol.inputs["Color"].default_value = (1.0, 1.0, 1.0, 1)
    vol.inputs["Anisotropy"].default_value = 0.5
    if "Density Attribute" in vol.inputs:
        vol.inputs["Density Attribute"].default_value = ""
    gen = nt.nodes.new("ShaderNodeTexCoord")
    space = nt.nodes.new("ShaderNodeTexCoord")
    space.object = noise_space
    g2 = nt.nodes.new("ShaderNodeVectorMath")
    g2.operation = "MULTIPLY_ADD"
    g2.inputs[1].default_value, g2.inputs[2].default_value = (2, 2, 2), (-1, -1, -1)
    L(gen.outputs["Generated"], g2.inputs[0])
    rl = nt.nodes.new("ShaderNodeVectorMath")
    rl.operation = "LENGTH"
    L(g2.outputs[0], rl.inputs[0])
    nN = nt.nodes.new("ShaderNodeTexNoise")
    nN.inputs["Scale"].default_value, nN.inputs["Detail"].default_value, nN.inputs["Roughness"].default_value = 0.7, 3, 0.65
    nF = nt.nodes.new("ShaderNodeTexNoise")
    nF.inputs["Scale"].default_value, nF.inputs["Detail"].default_value, nF.inputs["Roughness"].default_value = 4, 2, 0.6
    L(space.outputs["Object"], nN.inputs["Vector"])
    L(space.outputs["Object"], nF.inputs["Vector"])
    n2 = math("MULTIPLY_ADD", nN.outputs["Fac"], 2.0)          # 2N - 1
    nt.nodes[-1].inputs[2].default_value = -1.0
    edge = math("ADD", math("SUBTRACT", 0.80, rl.outputs["Value"]), math("MULTIPLY", n2, 0.15))
    t = math("DIVIDE", edge, 0.25)
    nt.nodes[-1].use_clamp = True
    smooth = math("MULTIPLY", math("MULTIPLY", t, t), math("SUBTRACT", 3.0, math("MULTIPLY", t, 2.0)))
    fine = math("MULTIPLY_ADD", nF.outputs["Fac"], 0.3)
    nt.nodes[-1].inputs[2].default_value = 0.7
    density = math("MULTIPLY", math("MULTIPLY", smooth, fine), 1.0)
    L(density, vol.inputs["Density"])
    L(vol.outputs[0], out.inputs["Volume"])
    m.diffuse_color = (0.95, 0.95, 0.97, 0.5)
    return m


def _cloud_tex(name, scale, depth=4):
    t = bpy.data.textures.get(name) or bpy.data.textures.new(name, "CLOUDS")
    t.noise_scale, t.noise_depth = scale, depth
    return t


def realistic_sky(scene, origin):
    """Cloud deck + cumulus at the sky set, world lit by the sunset HDRI."""
    mat = cloud_material()
    sea = bpy.data.objects.get("cloud_sea")
    if sea:
        bm = bmesh.new()
        bmesh.ops.create_grid(bm, x_segments=240, y_segments=480, size=1.0)
        bm.to_mesh(sea.data)
        bm.free()
        from mathutils import Matrix
        sea.data.transform(Matrix.Diagonal((*sea.scale, 1.0)))   # bake the 240 x 900 stretch, or the
        sea.scale = (1, 1, 1)                                     # displaced normals shear into shards
        sea.data.materials.clear()
        sea.data.materials.append(mat)
        for p in sea.data.polygons:
            p.use_smooth = True
        d = sea.modifiers.new("billows", "DISPLACE")
        d.texture, d.strength, d.texture_coords = _cloud_tex("cloud_billows", 14.0), 5.0, "GLOBAL"
        d2 = sea.modifiers.new("puffs", "DISPLACE")
        d2.texture, d2.strength, d2.texture_coords = _cloud_tex("cloud_puffs", 3.0, 6), 1.4, "GLOBAL"
        d3 = sea.modifiers.new("swell", "DISPLACE")       # broad rises and troughs: no even carpet from above
        d3.texture, d3.strength, d3.texture_coords = _cloud_tex("cloud_swell", 70.0, 2), 9.0, "GLOBAL"
    import random
    rnd = random.Random(21)
    puffs = [o for o in bpy.data.objects if o.name.startswith("cloud_") and o.name[6:].isdigit()]
    for ob in puffs:            # every cumulus a cluster of 3-5 lobes, each squashed and turned differently
        sx, sy, sz = ob.scale
        ob.scale = (sx * rnd.uniform(0.7, 1.4), sy * rnd.uniform(0.6, 1.5), sz * rnd.uniform(0.7, 1.6))
        ob.rotation_euler = (0, 0, rnd.uniform(0, 2 * math.pi))
        for k in range(rnd.randint(2, 4)):
            lobe = ob.copy()
            lobe.name = f"{ob.name}_lobe{k}"
            ob.users_collection[0].objects.link(lobe)
            a = rnd.uniform(0, 2 * math.pi)
            r = rnd.uniform(0.4, 0.9) * max(sx, sy)
            lobe.location = ob.location + Vector((math.cos(a) * r, math.sin(a) * r, rnd.uniform(-0.2, 0.6) * sz))
            f = rnd.uniform(0.45, 0.8)
            lobe.scale = (ob.scale[0] * f, ob.scale[1] * f * rnd.uniform(0.8, 1.2), ob.scale[2] * f * rnd.uniform(0.9, 1.4))
            lobe.rotation_euler = (0, 0, rnd.uniform(0, 2 * math.pi))
    space = bpy.data.objects.get("cloud_noise_space") or bpy.data.objects.new("cloud_noise_space", None)
    if space.name not in puffs[0].users_collection[0].objects:
        puffs[0].users_collection[0].objects.link(space)          # shared unit-scale noise anchor (cached with the set)
    for ob in [o for o in bpy.data.objects if o.name.startswith("cloud_") and o.name[6:8].isdigit()]:
        ob.data = ob.data.copy() if ob.data.users > 1 else ob.data
        from mathutils import Matrix
        ob.data.transform(Matrix.Diagonal((*(1.2 * v for v in ob.scale), 1.0)))  # bake the squash; +20% so the
        ob.scale = (1, 1, 1)                                                     # soft edge never meets the hull
        ob.data.materials.clear()
        ob.data.materials.append(cloud_volume_material(space))   # a volume: the mesh is only its container
        ob.visible_shadow = True
        for p in ob.data.polygons:
            p.use_smooth = True
    sun = bpy.data.objects.get("Sun")
    if sun:                                  # low golden sun: warm key, long soft shadows on the cloud tops
        sun.data.energy, sun.data.color = 3.2, (1.0, 0.68, 0.42)
        sun.rotation_euler = (math.radians(78), 0, math.radians(60))


def sky_world(scene):
    """Scene-level part of the sky (not cached with the set): HDRI world light and the film look."""
    scene.cycles.volume_bounces = 2              # light scattering inside the cumulus (bright, soft)
    hdri = LIB / "hdri" / "qwantani_sunset_puresky_2k.exr"
    if hdri.exists():
        w = scene.world
        nt = w.node_tree
        env = nt.nodes.new("ShaderNodeTexEnvironment")
        env.image = bpy.data.images.load(str(hdri), check_existing=True)
        mapping = nt.nodes.new("ShaderNodeMapping")
        mapping.inputs["Rotation"].default_value = (0, 0, math.radians(150))
        coord = nt.nodes.new("ShaderNodeTexCoord")
        nt.links.new(coord.outputs["Generated"], mapping.inputs["Vector"])
        nt.links.new(mapping.outputs["Vector"], env.inputs["Vector"])
        nt.links.new(env.outputs["Color"], nt.nodes["Background"].inputs["Color"])
        nt.nodes["Background"].inputs["Strength"].default_value = 0.7
    scene.view_settings.look = "AgX - Medium High Contrast"
