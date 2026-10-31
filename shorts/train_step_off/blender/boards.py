"""G3 rough boards: one Workbench still per shot from the blockout set, plus a contact sheet.

    blender -b out/train_step_off/set.blend -P shorts/train_step_off/blender/boards.py -- out/train_step_off/boards

Max is placed and leaned per scenario. The train runs toward +X, so every fall leans toward +X, whichever
way he faces: that's the physics. The ghost is an amber capsule; the arrows are amber (motion) and teal
(grip). Minutes of work, not renders.
"""
import math
import os
import sys

import bpy
from mathutils import Euler, Matrix, Vector

out = os.path.abspath(sys.argv[sys.argv.index("--") + 1])
os.makedirs(out, exist_ok=True)
sc = bpy.context.scene
sc.render.engine = "BLENDER_WORKBENCH"
sh = sc.display.shading
sh.light, sh.color_type, sh.show_shadows, sh.show_cavity = "STUDIO", "MATERIAL", True, True
sc.render.resolution_x, sc.render.resolution_y = 540, 960
rig = bpy.data.objects["Max"]
EDGE_Y, PLAT_Z, FLOOR_Z, DOOR_X = -2.03, 0.9, 1.2, 2.3
cam = bpy.data.objects.new("board_cam", bpy.data.cameras.new("board_cam"))
sc.collection.objects.link(cam)
sc.camera = cam
kit = bpy.data.collections.new("board_kit")
sc.collection.children.link(kit)


def m(name, rgba):
    mt = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mt.diffuse_color = rgba
    return mt


AMBER, TEAL, RED = m("k_amber", (1.0, 0.62, 0.15, 1)), m("k_teal", (0.15, 0.85, 0.85, 1)), m("k_red", (0.95, 0.15, 0.1, 1))
GHOST = m("k_ghost", (1.0, 0.62, 0.15, 0.35))


def add(op, mat, **kw):
    op(**kw)
    ob = bpy.context.active_object
    ob.data.materials.append(mat)
    for c in ob.users_collection:
        c.objects.unlink(ob)
    kit.objects.link(ob)
    return ob


def arrow(start, vec, mat, r=0.025):
    v = Vector(vec)
    L = v.length
    q = v.to_track_quat("Z", "Y")
    shaft = add(bpy.ops.mesh.primitive_cylinder_add, mat, radius=r, depth=L * 0.8, location=Vector(start) + v * 0.4)
    shaft.rotation_euler = q.to_euler()
    head = add(bpy.ops.mesh.primitive_cone_add, mat, radius1=r * 2.6, depth=L * 0.25, location=Vector(start) + v * 0.88)
    head.rotation_euler = q.to_euler()
    return [shaft, head]


def ghost(x, y, z, lean=0.0):
    g = add(bpy.ops.mesh.primitive_cylinder_add, GHOST, radius=0.22, depth=1.75, location=(x, y, z + 0.88))
    g.rotation_euler = Euler((0, math.radians(lean), 0))
    return [g]


def clear():
    for ob in list(kit.objects):
        bpy.data.objects.remove(ob, do_unlink=True)


def place(x, y, z, facing, lean=0.0):
    """facing: 'out' (-Y, sideways to travel), 'back' (-X), 'fwd' (+X); lean: degrees toward +X."""
    yaw = {"out": 0.0, "fwd": 90.0, "back": -90.0}[facing]
    rig.matrix_world = (Matrix.Translation((x, y, z)) @ Matrix.Rotation(math.radians(lean), 4, "Y")
                        @ Matrix.Rotation(math.radians(yaw), 4, "Z"))


def look(pos, tgt, lens):
    cam.location = pos
    cam.rotation_euler = (Vector(tgt) - Vector(pos)).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = lens


def needle(kmh):
    p = bpy.data.objects["speedo_needle_pivot"]
    p.rotation_euler.y = -(math.radians(225 - kmh * 270 / 120) - math.pi / 2)


SHOTS = []


def shot(i, line):
    def deco(f):
        SHOTS.append((i, line, f))
        return f
    return deco


@shot(1, "Getting off a slow train looks EASY.")
def s1():
    place(DOOR_X, -1.48, FLOOR_Z, "out")
    look((-9, 2.6, 7.5), (DOOR_X, -1.8, 1.6), 26)        # above and behind the coach, diving to the door


@shot(2, "Physics disagrees.")
def s2():
    place(DOOR_X, -1.48, FLOOR_Z, "out")
    look((5.6, -5.2, 1.0), (DOOR_X, -1.6, 1.8), 32)


@shot(3, "At ten kilometres an hour… (dial)")
def s3():
    needle(10)
    look((400.03, -0.62, 1.24), (400, -0.27, 1.2), 55)


@shot(4, "…your foot slows sharply, while your upper body keeps moving.")
def s4():
    x = 3.0
    place(x, -2.65, PLAT_Z, "out", lean=8)
    ghost(x + 1.4, -2.65, PLAT_Z, lean=0)
    arrow((x, -2.65, PLAT_Z + 1.25), (0.9, 0, 0), AMBER)
    arrow((x + 0.05, -2.75, PLAT_Z + 0.05), (-0.45, 0, 0), TEAL)
    look((x + 0.5, -7.6, 1.15), (x + 0.5, -2.6, 1.15), 32)


@shot(5, "So facing backward, you can tip backward, the way you can't see.")
def s5():
    x = 3.0
    place(x, -2.7, PLAT_Z, "back", lean=22)
    ghost(x + 1.6, -2.7, PLAT_Z)
    arrow((x + 0.2, -2.7, PLAT_Z + 1.25), (0.9, 0, 0), AMBER)
    look((x - 2.4, -5.6, 1.6), (x + 0.4, -2.7, 1.2), 30)


@shot(6, "Facing sideways… which can throw you off balance.")
def s6():
    x = 3.0
    place(x, -2.7, PLAT_Z, "out", lean=20)
    ghost(x + 1.5, -2.7, PLAT_Z)
    arrow((x + 0.2, -2.9, PLAT_Z + 1.2), (0.9, 0, 0), AMBER)
    look((x + 0.3, -7.2, 1.35), (x + 0.3, -2.7, 1.1), 35)


@shot(7, "Facing forward, a few quick steps can spread out the slowdown…")
def s7():
    x = 6.0
    place(x, -3.0, PLAT_Z, "fwd", lean=10)
    for k in range(4):
        add(bpy.ops.mesh.primitive_cylinder_add, TEAL, radius=0.09, depth=0.01,
            location=(x - 0.8 - k * 0.7, -3.0 + (0.08 if k % 2 else -0.08), PLAT_Z + 0.01))
    arrow((x + 0.15, -3.0, PLAT_Z + 1.25), (0.5, 0, 0), AMBER)
    look((x - 1.0, -7.0, 1.2), (x - 0.4, -3.0, 1.0), 32)


@shot(8, "…but you can still lose your BALANCE.")
def s8():
    x = 6.0
    place(x, -3.0, PLAT_Z, "fwd", lean=18)
    arrow((x + 0.25, -3.0, PLAT_Z + 1.2), (0.45, 0, 0), AMBER)
    look((x + 0.6, -5.2, 1.4), (x + 0.2, -3.0, 1.2), 40)


@shot(9, "One wet patch, one bag, one crowded step, and the GAP is right there.")
def s9():
    x = 5.0
    place(x, -2.35, PLAT_Z, "fwd", lean=14)
    add(bpy.ops.mesh.primitive_cylinder_add, m("k_water", (0.4, 0.55, 0.65, 0.6)), radius=0.35, depth=0.005,
        location=(x, -2.4, PLAT_Z + 0.008))
    add(bpy.ops.mesh.primitive_cube_add, RED, size=1, location=(x + 1.0, EDGE_Y - 0.03, PLAT_Z + 0.04)).scale = (6, 0.05, 0.02)
    look((x + 1.6, -2.12, PLAT_Z + 0.14), (x - 0.6, -2.0, PLAT_Z + 0.05), 22)   # low, right on the edge: the gap and coach side


@shot(10, "So wait until the train has completely STOPPED… (dial at 0)")
def s10():
    needle(0)
    look((400.03, -0.62, 1.24), (400, -0.27, 1.2), 55)


@shot(11, "…even if… (calm step down; matches shot 1's end)")
def s11():
    place(DOOR_X, -2.6, PLAT_Z, "out")
    look((4.3, -5.2, 1.5), (DOOR_X, -2.2, 1.3), 35)


paths = []
for i, line, f in SHOTS:
    clear()
    f()
    bpy.context.view_layer.update()
    sc.render.filepath = os.path.join(out, f"board_{i:02d}.png")
    bpy.ops.render.render(write_still=True)
    paths.append((i, line, sc.render.filepath))
with open(os.path.join(out, "boards.txt"), "w") as fh:
    for i, line, p in paths:
        fh.write(f"{i}\t{line}\t{p}\n")
print("boards:", len(paths))
