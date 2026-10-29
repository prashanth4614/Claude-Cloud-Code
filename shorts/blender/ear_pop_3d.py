"""Blender plate renderer for the 3D ear-pop short.

Builds every shot procedurally (no downloaded assets) and renders one
narration line as a PNG sequence:

  blender -b -P shorts/blender/ear_pop_3d.py -- --line N --out DIR \
          --res 540x960 --fps 30 --seconds S [--words W.json] [--samples 32] [--stills K]

Shots (see ear_states.SHOTS):
  plane  a chubby stylised airliner climbing through clouds (the hook)
  cabin  original character "Max" in a window seat, sky + clouds outside
  ear    stylised ear cross-section: canal, eardrum (shape keys bulge in/out),
         middle-ear chamber, ossicles, Eustachian tube that opens/closes,
         glowing air particles, pressure arrows, sound rings

--words is a JSON {"start": line start in seconds, "words": [[w, s, e], ...]}
written by shorts/ear_pop_3d.py, so visual beats land on spoken words.
DIR also gets anchors.json: per-frame screen positions (0-1, top-left) of
labelled 3D points, used by the 2D HUD for labels, rings and the POP! burst.
"""
import argparse
import json
import math
import os
import sys
from pathlib import Path

import bmesh
import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Euler, Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ear_states import SHOTS, clamp, ease, ear_state, lerp, word_at  # noqa: E402


# --------------------------------------------------------------- helpers ---
def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def lin(h, a=1.0):
    """sRGB hex -> linear RGBA (Blender colours are scene-linear)."""
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return (*c, a)


def rand(seed):
    """Tiny deterministic LCG (Blender's Python has no numpy guarantee)."""
    state = [seed * 2654435761 % 2**32 or 1]

    def r(a=0.0, b=1.0):
        state[0] = (1103515245 * state[0] + 12345) % 2**31
        return a + (b - a) * state[0] / 2**31
    return r


def setin(node, name, value):
    if name in node.inputs:
        node.inputs[name].default_value = value


def principled(name, hex_, rough=0.5, sss=0.0, sss_radius=(1.0, 0.35, 0.2), sss_scale=0.1,
               coat=0.0, sheen=0.0, spec=0.5, emit=None, emit_s=0.0, obj_color=False, bump=0.0,
               bump_scale=6.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    setin(b, "Base Color", lin(hex_))
    setin(b, "Roughness", rough)
    setin(b, "Subsurface Weight", sss)
    setin(b, "Subsurface Radius", sss_radius)
    setin(b, "Subsurface Scale", sss_scale)
    setin(b, "Coat Weight", coat)
    setin(b, "Sheen Weight", sheen)
    setin(b, "Specular IOR Level", spec)
    if emit:
        setin(b, "Emission Color", lin(emit))
        setin(b, "Emission Strength", emit_s)
    if obj_color:  # per-object tint via Object Info (so one material serves many states)
        oi = nt.nodes.new("ShaderNodeObjectInfo")
        nt.links.new(oi.outputs["Color"], b.inputs["Base Color"])
        if emit_s:
            nt.links.new(oi.outputs["Color"], b.inputs["Emission Color"])
            mul = nt.nodes.new("ShaderNodeMath")
            mul.operation = "MULTIPLY"
            mul.inputs[1].default_value = emit_s
            nt.links.new(oi.outputs["Alpha"], mul.inputs[0])
            nt.links.new(mul.outputs[0], b.inputs["Emission Strength"])
    if bump:
        tc = nt.nodes.new("ShaderNodeTexCoord")
        nz = nt.nodes.new("ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value = bump_scale
        nz.inputs["Detail"].default_value = 4.0
        bp = nt.nodes.new("ShaderNodeBump")
        bp.inputs["Strength"].default_value = bump
        nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
        nt.links.new(nz.outputs["Fac"], bp.inputs["Height"])
        nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m


def glow_mat(name, strength):
    """Emission tinted by object colour; object alpha fades it out (transparent)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    oi = nt.nodes.new("ShaderNodeObjectInfo")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = strength
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(oi.outputs["Color"], em.inputs["Color"])
    nt.links.new(oi.outputs["Alpha"], mix.inputs["Fac"])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    if hasattr(m, "surface_render_method"):
        m.surface_render_method = "BLENDED"
    return m


def gradient_emission(name, stops, strength=1.0, axis="Z", coord="Generated"):
    """Emission shader driven by a colour ramp along a texture axis (skies)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = strength
    _ramp(ramp, stops)
    nt.links.new(tc.outputs[coord], sep.inputs[0])
    nt.links.new(sep.outputs[axis], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], em.inputs["Color"])
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    return m


def _ramp(ramp, stops):
    els = ramp.color_ramp.elements
    while len(els) > 1:
        els.remove(els[-1])
    els[0].position, els[0].color = stops[0][0], lin(stops[0][1])
    for pos, hx in stops[1:]:
        e = els.new(pos)
        e.color = lin(hx)


def smooth(obj):
    for p in obj.data.polygons:
        p.use_smooth = True


def prim(kind, name, loc=(0, 0, 0), scale=(1, 1, 1), rot=(0, 0, 0), mat=None, sub=0,
         bevel=0.0, seg=32, flat=False):
    ops = bpy.ops.mesh
    if kind == "sphere":
        ops.primitive_uv_sphere_add(segments=seg, ring_count=max(8, seg // 2), radius=1)
    elif kind == "ico":
        ops.primitive_ico_sphere_add(subdivisions=2, radius=1)
    elif kind == "cube":
        ops.primitive_cube_add(size=2)
    elif kind == "cyl":
        ops.primitive_cylinder_add(vertices=seg, radius=1, depth=2)
    elif kind == "cone":
        ops.primitive_cone_add(vertices=seg, radius1=1, radius2=0, depth=2)
    elif kind == "torus":
        ops.primitive_torus_add(major_radius=1, minor_radius=0.25, major_segments=seg, minor_segments=12)
    elif kind == "plane":
        ops.primitive_plane_add(size=2)
    o = bpy.context.active_object
    o.name = name
    o.location, o.scale, o.rotation_euler = loc, scale, Euler([math.radians(a) for a in rot])
    if mat:
        o.data.materials.append(mat)
    if bevel:
        m = o.modifiers.new("bevel", "BEVEL")
        m.width, m.segments, m.limit_method = bevel, 4, "NONE"
    if sub:
        m = o.modifiers.new("sub", "SUBSURF")
        m.levels = m.render_levels = sub
    if not flat:
        smooth(o)
    return o


def new_obj(name, data, mat=None):
    o = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(o)
    if mat and hasattr(data, "materials") and not data.materials:
        data.materials.append(mat)
    return o


def seg_place(obj, a, b, r):
    """Stretch a unit primitive (z from -1 to 1) between points a and b."""
    a, b = Vector(a), Vector(b)
    d = b - a
    obj.location = (a + b) / 2
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d.normalized() if d.length else Vector((0, 0, 1)))
    obj.scale = (r, r, max(d.length, 1e-4) / 2)


def poly_curve(name, pts, bevel, mat):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth, cu.bevel_resolution, cu.use_fill_caps = bevel, 6, True
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for p, c in zip(sp.points, pts):
        p.co = (*c, 1)
    o = new_obj(name, cu, mat)
    return o


def metaball(name, balls, mat, res=0.08):
    """balls: [(co, radius, (sx, sy, sz))]; ellipsoid elements blend into blobs."""
    mb = bpy.data.metaballs.new(name)
    mb.resolution, mb.render_resolution = res, res * 0.6
    for co, r, size in balls:
        el = mb.elements.new(type="ELLIPSOID")
        el.co, el.radius = co, r
        el.size_x, el.size_y, el.size_z = size
    o = new_obj(name, mb)
    mb.materials.append(mat)
    return o


def area_light(name, loc, target, power, size, hex_="#ffffff"):
    ld = bpy.data.lights.new(name, "AREA")
    ld.energy, ld.size, ld.color, ld.shape = power, size, lin(hex_)[:3], "DISK"
    o = new_obj(name, ld)
    o.location = loc
    look_at(o, target)
    return o


def look_at(obj, target):
    d = Vector(target) - obj.location
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = d.to_track_quat("-Z", "Y")


def orbit(cam, target, dist, yaw, pitch, roll=0.0):
    """Camera on a sphere around target; yaw 0 looks along +Y, +yaw swings to +X."""
    y, p = math.radians(yaw), math.radians(pitch)
    target = Vector(target)
    cam.location = target + dist * Vector((math.sin(y) * math.cos(p), -math.cos(y) * math.cos(p), math.sin(p)))
    look_at(cam, target)
    if roll:
        cam.rotation_quaternion = cam.rotation_quaternion @ Euler((0, 0, math.radians(roll))).to_quaternion()


def world(stops=None, color="#000000", strength=1.0):
    w = bpy.data.worlds.new("world")
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes["Background"]
    bg.inputs["Strength"].default_value = strength
    if stops:  # vertical sky gradient by view elevation
        tc = nt.nodes.new("ShaderNodeTexCoord")
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        mr = nt.nodes.new("ShaderNodeMapRange")
        mr.inputs["From Min"].default_value, mr.inputs["From Max"].default_value = -0.4, 0.8
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        _ramp(ramp, stops)
        nt.links.new(tc.outputs["Generated"], sep.inputs[0])
        nt.links.new(sep.outputs["Z"], mr.inputs["Value"])
        nt.links.new(mr.outputs["Result"], ramp.inputs["Fac"])
        nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    else:
        bg.inputs["Color"].default_value = lin(color)


# ------------------------------------------------------------- the shots ---
class Shot:
    """Base: builds a set, owns a camera, sets per-frame state, reports anchors."""
    anchors = {}

    def __init__(self, cfg, words, start, dur):
        self.cfg, self.words, self.start, self.dur = cfg, words, start, dur
        cd = bpy.data.cameras.new("cam")
        cd.sensor_fit, cd.sensor_width, cd.lens = "VERTICAL", 36, 40
        cd.clip_start, cd.clip_end = 0.05, 500
        self.cam = new_obj("cam", cd)
        bpy.context.scene.camera = self.cam
        self.build()

    def anchor_points(self):
        return {}


# ------------------------------------------------------------------ plane --
class PlaneShot(Shot):
    def build(self):
        world([(0.0, "#a9d6ff"), (0.45, "#3a86d1"), (1.0, "#0b3d91")], strength=1.0)
        sun = bpy.data.lights.new("sun", "SUN")
        sun.energy, sun.angle, sun.color = 4.0, math.radians(8), lin("#fff1d6")[:3]
        so = new_obj("sun", sun)
        so.rotation_euler = Euler((math.radians(50), math.radians(10), math.radians(150)))
        self.rig = new_obj("plane_rig", None)
        body = principled("body", "#ffffff", rough=0.25, coat=0.4)
        # white top, red cheat-line, light grey belly: a ramp on the generated Z
        nt = body.node_tree
        tc, sep, ramp = (nt.nodes.new(t) for t in ("ShaderNodeTexCoord", "ShaderNodeSeparateXYZ", "ShaderNodeValToRGB"))
        ramp.color_ramp.interpolation = "CONSTANT"
        _ramp(ramp, [(0.0, "#c3ccd6"), (0.40, "#e63946"), (0.47, "#f7f9fb")])
        nt.links.new(tc.outputs["Generated"], sep.inputs[0])
        nt.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
        nt.links.new(ramp.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
        red = principled("red", "#e63946", rough=0.3, coat=0.3)
        grey = principled("grey", "#c9d1dc", rough=0.35)
        glass = principled("glass", "#14213d", rough=0.08, coat=1.0)
        dark = principled("dark", "#2b2d42", rough=0.4)
        parts = [prim("sphere", "fuselage", (0, 0, 0), (3.6, 0.62, 0.62), mat=body, seg=64)]
        # cockpit + cabin windows sit just outside the ellipsoid surface
        parts.append(prim("sphere", "cockpit", (3.22, 0, 0.17), (0.32, 0.42, 0.14), (0, -18, 0), glass))
        for i in range(12):
            x = 2.5 - i * 0.38
            yy = 0.62 * math.sqrt(max(0.0, 1 - (x / 3.6) ** 2)) * 0.985
            for s in (-1, 1):
                parts.append(prim("sphere", f"win{i}{s}", (x, s * yy, 0.16), (0.09, 0.03, 0.12), mat=glass, seg=16))
        parts.append(_wing_mesh("wingL", -1, grey))
        parts.append(_wing_mesh("wingR", 1, grey))
        for s in (-1, 1):
            parts.append(prim("cyl", f"eng{s}", (0.55, s * 1.45, -0.55), (0.26, 0.26, 0.55), (0, 90, 0), grey, seg=32))
            parts.append(prim("cyl", f"engc{s}", (1.07, s * 1.45, -0.55), (0.27, 0.27, 0.05), (0, 90, 0), red, seg=32))
            parts.append(prim("sphere", f"engf{s}", (1.1, s * 1.45, -0.55), (0.04, 0.2, 0.2), mat=dark, seg=24))
            parts.append(_fin("stab", (-3.0, s * 0.0, 0.1), [(0, 0), (0.7, 0), (0.25, s * 1.2), (-0.05, s * 1.2)],
                              grey, plane="xy"))
        parts.append(_fin("tail", (-3.05, 0, 0.2), [(0, 0), (1.0, 0), (0.1, 1.35), (-0.35, 1.35)], red, plane="xz"))
        for p in parts:
            p.parent = self.rig
        self.clouds = []
        cloud_mat = principled("cloud", "#ffffff", rough=1.0, sss=0.6, sss_radius=(1, 1, 1), sss_scale=0.5, spec=0.1)
        r = rand(11)
        for i in range(26):
            balls = [((r(-1.5, 1.5), r(-0.8, 0.8), r(-0.3, 0.4)), r(0.9, 1.5), (1.4, 1, 0.8)) for _ in range(7)]
            balls.append(((0, 0, -0.2), 1.6, (2.2, 1.3, 0.6)))
            o = metaball(f"cloud{i}", balls, cloud_mat, res=0.18)
            o.scale = [r(1.2, 2.6)] * 3
            self.clouds.append((o, Vector((r(-45, 45), r(4, 45), r(-14, 5)))))  # kept clear of the camera
        self.cam.data.lens = 38

    def update(self, t, now):
        k = ease_out(t / 0.8)
        self.rig.location = (lerp(-3.5, 0, k), lerp(-1, 0, k), math.sin(now * 2.2) * 0.12)
        self.rig.rotation_euler = Euler((math.radians(-6 + 2 * math.sin(now * 1.3)), math.radians(-11), math.radians(6)))
        for o, base in self.clouds:
            x = (base.x - now * 16 + 45) % 90 - 45
            o.location = (x, base.y, base.z)
        u = ease(t / self.dur)
        orbit(self.cam, (0.9, 0, 0.3), lerp(19, 17, u), lerp(50, 40, u), lerp(-9, -5, u), roll=-4)


def _wing_mesh(name, side, mat):
    """Swept, tapered wing (side -1 left, +1 right) with a little thickness."""
    root, tip = [(1.0, 0.0), (-0.8, 0.0)], [(-1.1, 3.4), (-1.6, 3.4)]
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    vs = []
    for z in (-0.06, 0.06):
        for (x, y) in root + tip[::-1]:
            vs.append(bm.verts.new((x, side * y, z - 0.18 + (0.0 if y == 0 else 0.25))))
    bm.faces.new(vs[:4])
    bm.faces.new(vs[4:][::-1])
    for i in range(4):
        bm.faces.new((vs[i], vs[(i + 1) % 4], vs[4 + (i + 1) % 4], vs[4 + i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    o = new_obj(name, me, mat)
    m = o.modifiers.new("bevel", "BEVEL")
    m.width, m.segments = 0.05, 3
    return o


def _fin(name, base, outline, mat, plane="xz"):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    vs = []
    for d in (-0.05, 0.05):
        for a, b in outline:
            co = (a, d, b) if plane == "xz" else (a, b, d)
            vs.append(bm.verts.new(co))
    n = len(outline)
    bm.faces.new(vs[:n])
    bm.faces.new(vs[n:][::-1])
    for i in range(n):
        bm.faces.new((vs[i], vs[(i + 1) % n], vs[n + (i + 1) % n], vs[n + i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    o = new_obj(name, me, mat)
    o.location = base
    m = o.modifiers.new("bevel", "BEVEL")
    m.width, m.segments = 0.04, 3
    return o


# ------------------------------------------------------------------ cabin --
HEAD = Vector((0, 0, 1.65))
EYE_C = [Vector((s * 0.37, -0.64, 1.72)) for s in (-1, 1)]
EAR_L = Vector((1.08, 0.05, 1.6))  # the ear we fly into (viewer's right)


class CabinShot(Shot):
    def build(self):
        world(color="#1a2238", strength=0.6)
        skin = principled("skin", "#ffc9a3", rough=0.45, sss=0.35, sss_radius=(1.0, 0.4, 0.25), sss_scale=0.25,
                          spec=0.35)
        skin_d = principled("skin_d", "#f0a888", rough=0.5, sss=0.3, sss_scale=0.2)
        blush = principled("blush", "#ff8fa3", rough=0.6, sss=0.3, sss_scale=0.2)
        hair = principled("hair", "#5a3620", rough=0.4, sheen=0.6, coat=0.2, bump=0.08, bump_scale=10)
        hoodie = principled("hoodie", "#2ec4b6", rough=0.8, sheen=0.8, bump=0.15, bump_scale=40)
        sclera = principled("sclera", "#ffffff", rough=0.15, coat=1.0, sss=0.1)
        iris = principled("iris", "#7a4a26", rough=0.2, coat=1.0, emit="#3d2412", emit_s=0.2)
        pupil = principled("pupil", "#0d0705", rough=0.1, coat=1.0)
        glint = principled("glint", "#ffffff", emit="#ffffff", emit_s=8.0)
        mouth = principled("mouth", "#5c1a1a", rough=0.5)
        tongue = principled("tongue", "#e07a7a", rough=0.5, sss=0.3)
        brow = principled("brow", "#3b2213", rough=0.6)
        seat = principled("seat", "#2f4b94", rough=0.85, sheen=0.7, bump=0.25, bump_scale=60)
        cover = principled("cover", "#eef1f5", rough=0.9, sheen=0.5)
        wall = principled("wall", "#e8ebf0", rough=0.5, coat=0.2)
        trim = principled("trim", "#b9c2cf", rough=0.4)

        # seat, headrest cover, armrest
        prim("cube", "seatback", (0, 0.8, 0.9), (1.3, 0.32, 1.9), mat=seat, bevel=0.25, sub=2)
        prim("cube", "headrest", (0, 0.42, 2.45), (0.95, 0.12, 0.45), mat=cover, bevel=0.1, sub=2)
        for s in (-1, 1):
            prim("cube", f"arm{s}", (s * 1.42, 0.0, -0.55), (0.16, 0.8, 0.12), mat=seat, bevel=0.08, sub=2)
        # body
        prim("sphere", "torso", (0, 0.12, -0.5), (1.18, 0.72, 1.12), mat=hoodie, seg=48)
        prim("torus", "hood", (0, 0.2, 0.42), (0.78, 0.62, 1.4), mat=hoodie, seg=48)
        prim("cyl", "neck", (0, 0, 0.62), (0.3, 0.3, 0.3), mat=skin_d)
        for s in (-1, 1):
            arm = prim("sphere", f"upper{s}", (s * 1.08, -0.05, -0.55), (0.33, 0.36, 0.85), (0, s * -8, 0), hoodie)
            arm.name = f"arm_sleeve{s}"
        # head
        self.head = prim("sphere", "head", HEAD, (1.0, 0.92, 0.95), mat=skin, seg=64)
        for s in (-1, 1):
            prim("sphere", f"ear{s}", HEAD + Vector((s * 0.97, 0.05, -0.05)), (0.15, 0.2, 0.29), (0, 0, s * 15), skin_d)
            prim("sphere", f"earin{s}", HEAD + Vector((s * 1.05, 0.02, -0.05)), (0.06, 0.12, 0.18), (0, 0, s * 15),
                 blush)
            # helix rim + dark opening, so the close-up reads as an ear
            prim("torus", f"helix{s}", HEAD + Vector((s * 1.0, 0.05, -0.05)), (0.3, 0.21, 0.45), (0, 90, s * 15), skin_d)
            prim("sphere", f"earhole{s}", HEAD + Vector((s * 1.08, 0.03, -0.1)), (0.03, 0.06, 0.08), (0, 0, s * 15), mouth)
            prim("sphere", f"blush{s}", (s * 0.6, -0.66, 1.38), (0.2, 0.08, 0.12), mat=blush)
        prim("sphere", "nose", (0, -0.9, 1.5), (0.13, 0.1, 0.11), mat=skin_d)
        hair_balls = [((0, 0.15, 0.32), 1.0, (1.04, 0.98, 0.86)),   # cap over the crown
                      ((0.05, -0.5, 0.62), 0.5, (1.5, 0.7, 0.55)),  # fringe
                      ((0.45, -0.55, 0.8), 0.45, (1.0, 0.7, 0.8)),  # quiff swoop
                      ((0.2, -0.3, 1.02), 0.45, (0.9, 0.9, 0.9)),
                      ((-0.55, -0.45, 0.6), 0.42, (0.9, 0.7, 0.6)),
                      ((0.88, 0.0, 0.2), 0.38, (0.5, 1.0, 1.0)),
                      ((-0.88, 0.0, 0.2), 0.38, (0.5, 1.0, 1.0))]
        h = metaball("hair", hair_balls, hair, res=0.05)
        h.data.threshold = 0.05  # low threshold: elements render near their full size
        h.location = HEAD
        # eyes: sclera + a gaze rig (iris, pupil, glints) + an eyelid that blinks
        self.gaze, self.lids = [], []
        for i, c in enumerate(EYE_C):
            prim("sphere", f"sclera{i}", c, (0.27, 0.25, 0.33), mat=sclera, seg=48)
            g = new_obj(f"gaze{i}", None)
            g.location = c
            for nm, off, sc, m in (("iris", 0.235, (0.17, 0.05, 0.21), iris), ("pupil", 0.27, (0.09, 0.03, 0.12), pupil),
                                   ("glint", 0.29, (0.045, 0.02, 0.05), glint)):
                o = prim("sphere", f"{nm}{i}", (0, -off, 0), sc, mat=m, seg=24)
                if nm == "glint":
                    o.location = (0.06, -off, 0.08)
                o.parent = g
            o = prim("sphere", f"glint2{i}", (-0.05, -0.27, -0.08), (0.022, 0.01, 0.025), mat=glint, seg=12)
            o.parent = g
            self.gaze.append(g)
            lid = _hemisphere(f"lid{i}", skin)
            lid.location, lid.scale = c, (0.29, 0.27, 0.35)
            lid.rotation_mode = "XYZ"
            self.lids.append(lid)
            b = prim("sphere", f"brow{i}", c + Vector((0, -0.1, 0.42)), (0.2, 0.06, 0.055), mat=brow, seg=24)
            b.rotation_mode = "XYZ"
            self.lids.append(b)
        # mouths (flat shapes shrink-wrapped onto the face; one visible at a time)
        self.mouths = {k: _face_shape(k, mat, self.head) for k, mat in
                       (("neutral", mouth), ("smile", mouth), ("smile_t", tongue), ("yawn", mouth),
                        ("yawn_t", tongue), ("wince", mouth))}
        # cabin wall with a window, overhead bin, sky + clouds outside
        n = Vector((-0.87, -0.5, 0))
        w0 = Vector((1.85, 0.75, 0))
        rot_z = math.degrees(math.atan2(n.y, n.x)) + 180
        wl = prim("cube", "wall", w0 - n * 0.15 + Vector((0, 0, 1.4)), (0.15, 4.5, 4.0), (0, 0, rot_z), wall, flat=True)
        cut = prim("cube", "wincut", w0 + Vector((0, 0, 2.0)), (0.6, 0.55, 0.8), (0, 0, rot_z), flat=True)
        cut.modifiers.new("b", "BEVEL").width = 0.4
        cut.modifiers["b"].segments = 8
        cut.hide_render = cut.hide_viewport = True
        bo = wl.modifiers.new("win", "BOOLEAN")
        bo.object, bo.operation, bo.solver = cut, "DIFFERENCE", "EXACT"
        frame = prim("cube", "winframe", w0 + n * 0.02 + Vector((0, 0, 2.0)), (0.05, 0.62, 0.86), (0, 0, rot_z), trim,
                     bevel=0.3, sub=2)
        fb = frame.modifiers.new("hole", "BOOLEAN")
        fb.object, fb.operation, fb.solver = cut, "DIFFERENCE", "EXACT"
        prim("cube", "shade", w0 - n * 0.06 + Vector((0, 0, 2.95)), (0.04, 0.5, 0.18), (0, 0, rot_z), cover, bevel=0.05)
        prim("cube", "bin", (0.2, 0.9, 4.15), (2.6, 1.6, 0.55), (0, 0, -6), wall, bevel=0.3, sub=2)
        prim("cube", "binlip", (0.2, -0.65, 3.62), (2.6, 0.08, 0.06), (0, 0, -6), trim, bevel=0.03)
        sky = gradient_emission("sky", [(0.0, "#a9d6ff"), (1.0, "#2f6fd1")], strength=2.2, coord="Object")
        sk = prim("plane", "sky", w0 - n * 3.5 + Vector((0, 0, 2.0)), (6, 6, 6), (90, 0, rot_z + 90), sky, flat=True)
        self.out_t, self.out_n = Vector((n.y, -n.x, 0)), n
        cloud_mat = principled("cloud", "#ffffff", rough=1.0, emit="#ffffff", emit_s=1.2, sss=0.5, sss_scale=0.3)
        r = rand(5)
        self.clouds = []
        for i in range(7):
            o = metaball(f"cloud{i}", [((r(-0.4, 0.4), r(-0.2, 0.2), r(-0.1, 0.2)), r(0.35, 0.55), (1.4, 1, 0.8))
                                       for _ in range(5)], cloud_mat, res=0.08)
            self.clouds.append((o, r(0, 6), r(-0.9, 0.6), r(1.0, 2.6)))
        self.sky_origin = w0 - n * 1.6 + Vector((0, 0, 2.0))
        # soft studio lighting: warm key, cool window fill, rim, bounce
        area_light("key", (-3.5, -5.0, 4.5), HEAD, 900, 4.0, "#fff1e0")
        area_light("window", w0 - n * 0.8 + Vector((0, 0, 2.0)), HEAD, 260, 1.4, "#cfe6ff")
        area_light("rim", (-2.5, 2.5, 4.0), HEAD, 500, 2.0, "#ffd6b0")
        area_light("fill", (1.5, -6.0, 0.5), HEAD, 200, 5.0, "#dfe8ff")
        self.cam.data.dof.use_dof = True
        self.cam.data.dof.aperture_fstop = 2.8

    def anchor_points(self):
        return {"ear": EAR_L, "ear_top": EAR_L + Vector((0, 0, 0.3))}

    def expr(self, t):
        e = self.cfg.get("expr", "neutral")
        if e == "tips":
            e = "yawn" if t < word_at(self.words, "chewing") + 0.6 else "smile"
        return e

    def update(self, t, now):
        e = self.expr(t)
        for k, o in self.mouths.items():
            o.hide_render = k.split("_")[0] != e
        if e == "yawn":
            open_ = 0.6 + 0.4 * math.sin(now * 3) ** 2
            for k in ("yawn", "yawn_t"):
                self.mouths[k].scale = (1, 1, open_)
        blink = ((now + 1.7) % 3.3) < 0.12
        closed = e in ("yawn", "wince") or blink
        look = self.cfg.get("look", (0, 0))
        for g in self.gaze:
            g.rotation_euler = Euler((math.radians(-look[1] * 14), 0, math.radians(look[0] * 18)))
        tilt = {"wince": 16, "smile": -8}.get(e, 0)
        for i in range(2):
            lid, brow = self.lids[2 * i], self.lids[2 * i + 1]
            lid.rotation_euler = Euler((math.radians(85 if closed else -110), 0, 0))
            s = 1 if i else -1
            brow.rotation_euler = Euler((0, math.radians(s * tilt * 0.8), 0))
            brow.location.z = EYE_C[i].z + 0.42 + (0.04 if e == "smile" else 0) - (0.03 if e == "wince" else 0)
        for o, ph, z, sc in self.clouds:
            u = ((now * 0.35 + ph / 6) % 1) * 2 - 1
            o.location = self.sky_origin + self.out_t * (u * 2.4) + Vector((0, 0, z))
            o.scale = (sc * 0.5,) * 3
        cam = self.cfg["cam"]
        u = ease(t / self.dur)
        if cam == "zoom_ear":
            k = ease(clamp((t - self.dur * 0.35) / (self.dur * 0.65)))
            tgt = Vector((0.45, 0, 1.25)).lerp(EAR_L, k)
            orbit(self.cam, tgt, lerp(lerp(9.0, 8.4, u), 2.2, k), lerp(-10, 45, k), lerp(5, 4, k))
            self.cam.data.dof.focus_distance = (self.cam.location - EAR_L).length
        else:
            tgt = Vector((0.3, 0, 1.35))
            if cam == "tips":
                orbit(self.cam, tgt, lerp(8.4, 7.6, u), lerp(-8, -3, u), 5)
            else:
                orbit(self.cam, tgt, lerp(7.8, 7.0, u), lerp(5, -4, u), lerp(3, 6, u))
            self.cam.data.dof.focus_distance = (self.cam.location - HEAD).length - 0.8


def _hemisphere(name, mat):
    """Upper half of a unit sphere, slightly larger than the eye: the eyelid.
    Rotating it about X sweeps the lid open (-72 deg) or shut (~-8 deg)."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=40, v_segments=20, radius=1.0)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -0.02], context="VERTS")
    bm.to_mesh(me)
    o = new_obj(name, me, mat)
    sol = o.modifiers.new("thick", "SOLIDIFY")
    sol.thickness = 0.06
    smooth(o)
    return o


def _face_shape(kind, mat, head):
    """2D mouth outline in the XZ plane, projected onto the face."""
    pts = []
    if kind in ("smile", "smile_t"):
        w, d = (0.3, 0.22) if kind == "smile" else (0.17, 0.09)
        z0 = 1.12 if kind == "smile" else 1.0
        for i in range(25):
            a = math.pi * i / 24
            pts.append((-w * math.cos(a), z0 - d * math.sin(a)))
        pts += [(w * 0.6, z0 + 0.03), (-w * 0.6, z0 + 0.03)] if kind == "smile" else []
    elif kind in ("yawn", "yawn_t"):
        rx, rz, zc = (0.17, 0.2, 1.05) if kind == "yawn" else (0.11, 0.07, 0.92)
        pts = [(rx * math.cos(2 * math.pi * i / 32), zc + rz * math.sin(2 * math.pi * i / 32)) for i in range(32)]
    elif kind == "neutral":
        for i in range(17):
            a = math.pi * (0.15 + 0.7 * i / 16)
            pts.append((-0.2 * math.cos(a), 1.12 - 0.08 * math.sin(a)))
        for i in range(16, -1, -1):
            a = math.pi * (0.15 + 0.7 * i / 16)
            pts.append((-0.19 * math.cos(a), 1.12 - 0.08 * math.sin(a) + 0.045))
    else:  # wince zig-zag
        top = [(-0.24 + i * 0.08, 1.08 + (0.04 if i % 2 else -0.04)) for i in range(7)]
        pts = top + [(x, z - 0.05) for x, z in top[::-1]]
    me = bpy.data.meshes.new(kind)
    bm = bmesh.new()
    vs = [bm.verts.new((x, -1.2, z)) for x, z in pts]
    bm.faces.new(vs)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges, cuts=2, use_grid_fill=True)
    bm.to_mesh(me)
    o = new_obj(f"mouth_{kind}", me, mat)
    if kind.endswith("_t"):
        o.location.y -= 0.01
    sw = o.modifiers.new("wrap", "SHRINKWRAP")
    sw.target, sw.wrap_method = head, "PROJECT"
    sw.use_project_y, sw.use_negative_direction, sw.use_positive_direction = True, False, True
    sw.offset = 0.012 if kind.endswith("_t") else 0.006
    sol = o.modifiers.new("thick", "SOLIDIFY")
    sol.thickness = 0.01
    return o


# -------------------------------------------------------------------- ear --
def P(x, y, depth=0.0):
    """2D diagram pixels (shorts/ear_pop.py) -> 3D units on the cut face (y=0)."""
    return Vector(((x - 480) / 100, depth, -(y - 850) / 100))


TUBE2D = ((700, 865), (725, 1010), (520, 1040), (455, 1200))


def bez(u):
    (x0, y0), (x1, y1), (x2, y2), (x3, y3) = TUBE2D
    a, b, c, d = (1 - u) ** 3, 3 * u * (1 - u) ** 2, 3 * u * u * (1 - u), u ** 3
    return a * x0 + b * x1 + c * x2 + d * x3, a * y0 + b * y1 + c * y2 + d * y3


def tube_pts(n=48, depth=0.0):
    return [P(*bez(i / (n - 1)), depth) for i in range(n)]


CANAL_Z = P(0, 700).z
DRUM_X = P(482, 0).x
DRUM_R = 0.95


class EarShot(Shot):
    def build(self):
        world(color="#2a0d14", strength=0.5)
        tissue = principled("tissue", "#e8907c", rough=0.42, sss=0.45, sss_radius=(1.0, 0.3, 0.2), sss_scale=0.3,
                            coat=0.25, bump=0.25, bump_scale=3.5)
        cavity = principled("cavity", "#3a1426", rough=0.6, sss=0.3, sss_scale=0.2, coat=0.15, bump=0.15,
                            bump_scale=5)
        bone = principled("bone", "#f4e6cc", rough=0.35, sss=0.3, sss_radius=(1, 0.8, 0.6), sss_scale=0.1, coat=0.3)
        drum = principled("drum", "#f6e7d7", rough=0.2, sss=0.5, sss_scale=0.2, coat=0.6, obj_color=True,
                          emit_s=0.6)
        lining = principled("lining", "#f2a090", rough=0.35, sss=0.5, sss_scale=0.25, coat=0.4, obj_color=True,
                            emit_s=1.2)
        self.glow = glow_mat("glow", 7.0)
        self.glow_soft = glow_mat("glow_soft", 3.0)
        # the slab of tissue, cut open: canal, middle-ear chamber, tube groove, throat
        slab = prim("cube", "slab", (0.6, 1.6, -0.6), (9.5, 1.6, 12), mat=tissue, bevel=0.6, flat=True)
        smooth(slab)
        cutters = [prim("cyl", "c_canal", ((P(-500, 0).x + DRUM_X) / 2, 0, CANAL_Z), (0.8, 0.8, (DRUM_X - P(-500, 0).x) / 2),
                        (0, 90, 0), cavity, seg=64),
                   prim("sphere", "c_mid", P(646, 707), (1.6, 1.15, 1.68), mat=cavity, seg=64),
                   prim("sphere", "c_throat", P(450, 1240), (1.6, 1.0, 0.7), mat=cavity, seg=64)]
        tc = poly_curve("tubecut", tube_pts(), 0.36, cavity)
        dg = bpy.context.evaluated_depsgraph_get()
        me = bpy.data.meshes.new_from_object(tc.evaluated_get(dg))
        bpy.data.objects.remove(tc)
        cutters.append(new_obj("c_tube", me))
        for c in cutters:
            c.hide_render = c.hide_viewport = True
            m = slab.modifiers.new(c.name, "BOOLEAN")
            m.object, m.operation, m.solver = c, "DIFFERENCE", "EXACT"
            if hasattr(m, "material_mode"):
                m.material_mode = "TRANSFER"
        # eardrum: a half disc spanning the canal end, with Out/In shape keys
        self.drum = _drum_mesh(drum)
        self.drum.location = (DRUM_X, 0, CANAL_Z)
        # ossicles: three tiny bones, the first rides on the eardrum
        self.bones = [prim("cyl", f"bone{i}", mat=bone, seg=24) for i in range(3)]
        self.joints = [prim("sphere", f"joint{i}", mat=bone, seg=24) for i in range(3)]
        # Eustachian tube: two soft walls in the groove, pressed shut or pulled apart
        self.walls = [poly_curve(f"wall{s}", tube_pts(), 0.18, lining) for s in (-1, 1)]
        # air particles, arrows, sound rings
        sph = bpy.data.meshes.new("p")
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=8, radius=1.0)
        bm.to_mesh(sph)
        sph.materials.append(self.glow)
        for p in sph.polygons:
            p.use_smooth = True
        self.p_out = [new_obj(f"po{i}", sph) for i in range(34)]
        self.p_in = [new_obj(f"pi{i}", sph) for i in range(24)]
        self.p_flow = [new_obj(f"pf{i}", sph) for i in range(14)]
        r = rand(1)
        self.po_seed = [(r(0, 4.6), r(-0.6, 0.6), r(0.2, 0.6), r(0, 6), r(0.15, 0.5)) for _ in self.p_out]
        r = rand(2)
        self.pi_seed = [(r(0, 6), r(0, 6), r(0.6, 1.4), r(0.6, 1.4), r(0.2, 0.75)) for _ in self.p_in]
        self.arrows = []
        for i in range(6):
            shaft = prim("cyl", f"ash{i}", mat=self.glow_soft, seg=16)
            head = prim("cone", f"ahd{i}", mat=self.glow_soft, seg=24)
            self.arrows.append((shaft, head))
        self.rings = []
        for i in range(4):
            o = prim("torus", f"ring{i}", rot=(0, 90, 0), mat=self.glow, seg=48)
            self.rings.append(o)
        # soft studio lights
        area_light("key", (-6, -12, 9), (0, 0, 0), 9000, 10, "#fff0e6")
        area_light("fill", (9, -10, -4), (0, 0, 0), 3500, 10, "#ffd2dc")
        area_light("top", (0, -2, 14), (0, 0, 0), 2500, 8, "#ffffff")
        self.cam.data.lens = 35

    def anchor_points(self):
        bx, _ = bez(0.45)
        return {"canal": P(200, 690), "drum": P(478, 770), "drum_c": Vector((DRUM_X, 0, CANAL_Z)),
                "middle": P(700, 590), "tube": P(*bez(0.5)), "tube_x": P(bez(0.45)[0] + 90, bez(0.45)[1]),
                "throat": P(360, 1235)}

    def update(self, t, now):
        st, pw = ear_state(self.cfg, t, self.dur, self.words)
        self.state, self.pop_t = st, pw
        b = st["bulge"]
        keys = self.drum.data.shape_keys.key_blocks
        keys["Out"].value, keys["In"].value = max(0.0, b), max(0.0, -b)
        strain = abs(b)
        self.drum.color = lin("#ffb3a7") if strain > 0.5 else lin("#f6e7d7")
        self.drum.color = (*self.drum.color[:3], 0.6 * strain)
        # ossicle chain
        mid = Vector((DRUM_X - 0.6 * b, 0.3, CANAL_Z))
        pts = [mid, P(590, 640, 0.3), P(655, 632, 0.3), P(720, 690, 0.3)]
        for i, o in enumerate(self.bones):
            seg_place(o, pts[i], pts[i + 1], 0.085)
        for o, p in zip(self.joints, pts[1:]):
            o.location, o.scale = p, (0.13,) * 3
        # tube walls: closed = touching in the middle, open = pressed to the sides
        k = st["tube"]
        off, rad = lerp(0.17, 0.27, k), lerp(0.19, 0.085, k)
        centre = tube_pts(48, 0.0)
        for s, wall in zip((-1, 1), self.walls):
            sp = wall.data.splines[0]
            for i, p in enumerate(sp.points):
                a = centre[max(i - 1, 0)]
                c = centre[min(i + 1, len(centre) - 1)]
                tang = (c - a).normalized()
                nrm = Vector((-tang.z, 0, tang.x))
                q = centre[i] + nrm * s * off + Vector((0, 0.04, 0))
                p.co = (*q, 1)
            wall.data.bevel_depth = rad
            red = st["red"]
            col = Vector(lin("#f2a090")[:3]).lerp(Vector(lin("#ff2a2a")[:3]), red)
            wall.color = (*col, 0.35 * red)
        # air outside (in the canal) thins with altitude; inside keeps bouncing
        n_out = int(round(34 * st["p_out"]))
        for i, (o, (x0, z0, v, ph, dep)) in enumerate(zip(self.p_out, self.po_seed)):
            o.hide_render = i >= n_out
            x = P(-60, 0).x + (x0 + now * v) % 4.5
            z = CANAL_Z + z0 + math.sin(now * 3 + ph) * 0.08
            o.location = (min(x, DRUM_X - 0.15 - max(0.0, b) * 0.9 * (1 - (z - CANAL_Z) ** 2 / 0.64)), dep, z)
            o.scale = (0.085,) * 3
            o.color = lin("#8ecae6", 1.0)
        c = P(646, 707)
        for o, (a, bb, f1, f2, dep) in zip(self.p_in, self.pi_seed):
            o.location = (c.x + 1.15 * math.sin(now * f1 + a), dep, c.z + 1.2 * math.sin(now * f2 + bb))
            o.scale = (0.085,) * 3
            o.color = lin("#bde0fe", 1.0)
        for i, o in enumerate(self.p_flow):
            u = (now * 0.7 + i / len(self.p_flow)) % 1
            o.location = P(*bez(u), 0.12)
            o.scale = (0.08,) * 3
            o.color = lin("#bde0fe", clamp(st["flow"]))
            o.hide_render = st["flow"] < 0.01
        # pressure arrows: blue = outside air pushing in, orange = inside air pushing out
        a = st["arrows"]
        lo = lerp(0.4, 1.7, clamp(st["p_out"] / 1.5))
        for j, y2 in enumerate((655, 700, 745)):
            f = 1 - abs(y2 - 700) / 110
            end = P(470 - b * 120 * f * 0.9, y2, 0.15)
            _arrow(self.arrows[j], end - Vector((lo, 0, 0)), end - Vector((0.08, 0, 0)), "#4cc9f0", a)
            tip = P(500 - b * 120 * 0.6 + 14, y2, 0.15)
            _arrow(self.arrows[3 + j], P(620, y2, 0.15), tip, "#ffb703", a)
        for i, o in enumerate(self.rings):
            ph = (now * 0.9 + i * 0.25) % 1
            o.location = (P(lerp(40, 380, ph), 0).x, 0.25, CANAL_Z)
            o.scale = (0.55, 0.55, 0.55)
            o.color = lin("#ffffff", st["waves"] * (1 - ph) ** 2)
            o.hide_render = st["waves"] < 0.01
        self.camera(t)

    def camera(self, t):
        cam, u, d = self.cfg["cam"], ease(t / self.dur), self.dur
        base = P(540, 720)  # keeps the canal clear of the HUD pills at the top
        if cam == "intro":
            orbit(self.cam, base, lerp(21, 17, u), lerp(14, 4, u), lerp(9, 3, u))
        elif cam == "drift_l":
            orbit(self.cam, base, lerp(17, 16.2, u), lerp(5, -5, u), lerp(3, 5, u))
        elif cam == "drift_r":
            orbit(self.cam, base, lerp(16.8, 16, u), lerp(-5, 6, u), lerp(5, 3, u))
        elif cam == "push_drum":
            orbit(self.cam, base.lerp(P(470, 640), u), lerp(17, 12.5, u), lerp(0, -12, u), lerp(3, 6, u))
        elif cam == "canal":
            orbit(self.cam, P(470, 640).lerp(P(330, 640), u), lerp(12.5, 12, u), lerp(-12, -16, u), 6)
        elif cam == "tube":
            orbit(self.cam, P(330, 640).lerp(P(560, 860), u), lerp(13, 15, u), lerp(-10, 2, u), lerp(5, 12, u))
        elif cam == "pop":
            k = ease_out(clamp((t - self.pop_t) / 0.5)) if self.pop_t is not None and t >= self.pop_t else 0
            dist = lerp(lerp(15, 13.2, ease(t / max(self.pop_t or d, 0.1))), 16.5, k)
            orbit(self.cam, P(560, 840).lerp(base, k), dist, lerp(2, -2, u), lerp(12, 5, k))


def _arrow(parts, a, b, hex_, alpha):
    shaft, head = parts
    a, b = Vector(a), Vector(b)
    d = b - a
    hl = min(0.28, d.length * 0.6)
    tip_base = b - d.normalized() * hl if d.length else b
    seg_place(shaft, a, tip_base, 0.06)
    seg_place(head, tip_base, b, 0.0)
    head.scale = (0.15, 0.15, hl / 2)
    for o in parts:
        o.color = lin(hex_, alpha)
        o.hide_render = alpha < 0.01


def _drum_mesh(mat):
    me = bpy.data.meshes.new("drum")
    bm = bmesh.new()
    nr, ns = 10, 24
    centre = bm.verts.new((0, 0, 0))
    rings = []
    for i in range(1, nr + 1):
        r = DRUM_R * i / nr
        rings.append([bm.verts.new((0, r * math.cos(a), r * math.sin(a)))
                      for a in (math.pi * (j / ns - 0.5) for j in range(ns + 1))])
    for j in range(ns):
        bm.faces.new((centre, rings[0][j], rings[0][j + 1]))
    for i in range(nr - 1):
        for j in range(ns):
            bm.faces.new((rings[i][j], rings[i + 1][j], rings[i + 1][j + 1], rings[i][j + 1]))
    bm.to_mesh(me)
    o = new_obj("drum", me, mat)
    o.shape_key_add(name="Basis")
    for name, sgn in (("Out", -1), ("In", 1)):
        k = o.shape_key_add(name=name)
        for v, kv in zip(me.vertices, k.data):
            r2 = (v.co.y ** 2 + v.co.z ** 2) / DRUM_R ** 2
            kv.co = (sgn * 1.0 * (1 - r2), v.co.y, v.co.z)
    sol = o.modifiers.new("thick", "SOLIDIFY")
    sol.thickness, sol.offset = 0.07, 0
    smooth(o)
    return o


# ---------------------------------------------------------------- render ---
def setup_render(res, fps, samples):
    sc = bpy.context.scene
    w, h = (int(x) for x in res.split("x"))
    r = sc.render
    r.resolution_x, r.resolution_y, r.resolution_percentage = w, h, 100
    r.fps = fps
    r.image_settings.file_format, r.image_settings.color_mode = "PNG", "RGB"
    r.image_settings.compression = 15
    if os.environ.get("SHORTS_ENGINE", "").upper() == "CYCLES":
        # Fallback for cloud GPUs without an EGL/graphics driver: Cycles + OptiX/CUDA + denoise.
        r.engine = "CYCLES"
        prefs = bpy.context.preferences.addons["cycles"].preferences
        for backend in ("OPTIX", "CUDA", "HIP", "METAL"):
            try:
                prefs.compute_device_type = backend
                prefs.get_devices()
                if any(d.type == backend for d in prefs.devices):
                    break
            except TypeError:
                continue
        for d in prefs.devices:
            d.use = d.type != "CPU"
        sc.cycles.device = "GPU"
        sc.cycles.samples = max(16, samples * 2)
        sc.cycles.use_denoising = True
        print(f"[render] Cycles on {prefs.compute_device_type}: {[d.name for d in prefs.devices if d.use]}")
    else:
        for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
            try:
                r.engine = eng
                break
            except TypeError:
                continue
    ee = sc.eevee
    for k, v in (("taa_render_samples", samples), ("use_shadows", True), ("shadow_ray_count", 1),
                 ("shadow_step_count", 4), ("shadow_resolution_scale", 0.5), ("use_raytracing", False), ("use_gtao", True)):
        if hasattr(ee, k):
            setattr(ee, k, v)
    vs = sc.view_settings
    try:
        vs.view_transform, vs.look = "AgX", "AgX - Punchy"
    except TypeError:
        pass
    # bloom-like glow on bright emitters (EEVEE Next has no built-in bloom)
    sc.use_nodes = True
    nt = sc.node_tree
    nt.nodes.clear()
    rl = nt.nodes.new("CompositorNodeRLayers")
    gl = nt.nodes.new("CompositorNodeGlare")
    gl.glare_type, gl.quality = "FOG_GLOW", "MEDIUM"
    if hasattr(gl, "threshold"):
        gl.threshold, gl.mix = 1.0, 0.0
        gl.size = 8
    comp = nt.nodes.new("CompositorNodeComposite")
    nt.links.new(rl.outputs["Image"], gl.inputs["Image"])
    nt.links.new(gl.outputs["Image"], comp.inputs["Image"])


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--line", type=int, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--res", default="540x960")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--seconds", type=float, required=True)
    ap.add_argument("--words", help="JSON with line start + word timings")
    ap.add_argument("--samples", type=int, default=32)
    ap.add_argument("--stills", type=int, default=0, help="render only K evenly spaced frames (preview)")
    ap.add_argument("--force", action="store_true", help="re-render frames that already exist")
    a = ap.parse_args(argv)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    setup_render(a.res, a.fps, a.samples)
    start, words = 0.0, []
    if a.words:
        j = json.loads(Path(a.words).read_text())
        start, words = j["start"], j["words"]
    cfg = SHOTS[a.line]
    shot = {"plane": PlaneShot, "cabin": CabinShot, "ear": EarShot}[cfg["shot"]](cfg, words, start, a.seconds)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    n = max(1, math.ceil(a.seconds * a.fps - 1e-6))
    frames = range(n)
    if a.stills:
        frames = sorted({round(i * (n - 1) / max(1, a.stills - 1)) for i in range(a.stills)})
    sc = bpy.context.scene
    anchors = {k: [] for k in shot.anchor_points()}
    import time
    t_start, rendered = time.time(), 0
    for f in range(n):  # anchors for every frame; pixels only where needed
        t = f / a.fps
        shot.update(t, start + t)
        if anchors:
            bpy.context.view_layer.update()
            for k, p in shot.anchor_points().items():
                v = world_to_camera_view(sc, shot.cam, p)
                anchors[k].append([round(v.x, 5), round(1 - v.y, 5)])
        path = out / f"{f:05d}.png"
        if f in frames and (a.force or not path.exists()):
            sc.render.filepath = str(path)
            bpy.ops.render.render(write_still=True)
            rendered += 1
    (out / "anchors.json").write_text(json.dumps({"frames": n, "fps": a.fps, "anchors": anchors}))
    el = time.time() - t_start
    print(f"[plate] line {a.line}: {rendered} frames in {el:.1f}s ({el / max(rendered, 1):.2f}s/frame)")


if __name__ == "__main__":
    main()
