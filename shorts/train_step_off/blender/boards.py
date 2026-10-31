"""G3 rough boards (v2, after Codex 019): Workbench stills per shot and endpoint, plus a contact sheet.

    blender -b out/train_step_off/set.blend -P shorts/train_step_off/blender/boards.py -- out/train_step_off/boards

Max is placed, leaned and roughly posed (arms down, stride or sideways step, flail) with his expression.
The train runs toward +X (screen-right), so every fall leans toward +X, whichever way he faces: that's
the physics. The ghost is an amber capsule; arrows are amber (motion) and teal (grip).
Framing rule (Codex 019): Max's head-to-shoe is about 62% of frame height, contact about 70% down.
"""
import math
import os
import sys

import bpy
from mathutils import Euler, Matrix, Vector

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "blender"))
import build_max  # noqa: E402

out = os.path.abspath(sys.argv[sys.argv.index("--") + 1])
os.makedirs(out, exist_ok=True)
sc = bpy.context.scene
sc.render.engine = "BLENDER_WORKBENCH"
sh = sc.display.shading
sh.light, sh.color_type, sh.show_shadows, sh.show_cavity = "STUDIO", "MATERIAL", True, True
sc.render.resolution_x, sc.render.resolution_y = 540, 960
rig = bpy.data.objects["Max"]
EDGE_Y, PLAT_Z, FLOOR_Z, DOOR_X = -2.03, 0.9, 1.2, 2.3
MAXDOOR_X = DOOR_X + 0.32          # Max stands beside the door pole, not through it
cam = bpy.data.objects.new("board_cam", bpy.data.cameras.new("board_cam"))
sc.collection.objects.link(cam)
sc.camera = cam
kit = bpy.data.collections.new("board_kit")
sc.collection.children.link(kit)
train = [o for o in bpy.data.objects if o.name.startswith("coach_") and o.type == "EMPTY"]
train0 = {o.name: o.location.copy() for o in train}


def m(name, rgba):
    mt = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mt.diffuse_color = rgba
    return mt


AMBER, TEAL, RED = m("k_amber", (1.0, 0.62, 0.15, 1)), m("k_teal", (0.15, 0.85, 0.85, 1)), m("k_red", (0.95, 0.15, 0.1, 1))
GHOST, WATER = m("k_ghost", (1.0, 0.62, 0.15, 0.33)), m("k_water", (0.35, 0.55, 0.70, 0.7))
PERSON = m("k_person", (0.45, 0.40, 0.36, 1))


def add(op, mat, **kw):
    op(**kw)
    ob = bpy.context.active_object
    ob.data.materials.append(mat)
    for c in ob.users_collection:
        c.objects.unlink(ob)
    kit.objects.link(ob)
    return ob


def arrow(start, vec, mat, r=0.022):
    v = Vector(vec)
    q = v.to_track_quat("Z", "Y").to_euler()
    a = add(bpy.ops.mesh.primitive_cylinder_add, mat, radius=r, depth=v.length * 0.78, location=Vector(start) + v * 0.39)
    a.rotation_euler = q
    h = add(bpy.ops.mesh.primitive_cone_add, mat, radius1=r * 2.6, depth=v.length * 0.24, location=Vector(start) + v * 0.88)
    h.rotation_euler = q


def tip_arrow(ankle, toward_x=1):
    """A curved arrow around the ankle: the 'falling pole' rotation (in the XZ plane)."""
    t = add(bpy.ops.mesh.primitive_torus_add, AMBER, major_radius=0.32, minor_radius=0.014,
            location=Vector(ankle), rotation=(math.pi / 2, 0, 0))
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="DESELECT")
    bpy.ops.object.mode_set(mode="OBJECT")
    for v in t.data.vertices:                          # keep only the upper-right quarter arc
        ang = math.atan2(v.co.y, v.co.x)               # torus local XY = world XZ after the X rotation
        v.select = not (math.radians(25) < ang < math.radians(80))
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.delete(type="VERT")
    bpy.ops.object.mode_set(mode="OBJECT")
    tipx = Vector(ankle) + Vector((0.32 * math.cos(math.radians(25)), 0, 0.32 * math.sin(math.radians(25))))
    h = add(bpy.ops.mesh.primitive_cone_add, AMBER, radius1=0.04, depth=0.09, location=tipx)
    h.rotation_euler = Vector((0.35, 0, -1)).to_track_quat("Z", "Y").to_euler()


def ghost(x, y, z, lean=0.0):
    g = add(bpy.ops.mesh.primitive_cylinder_add, GHOST, radius=0.22, depth=1.78, location=(x, y, z + 0.89))
    g.rotation_euler = Euler((0, math.radians(lean), 0))


def person(x, y, z):
    add(bpy.ops.mesh.primitive_cylinder_add, PERSON, radius=0.21, depth=1.70, location=(x, y, z + 0.85))
    add(bpy.ops.mesh.primitive_uv_sphere_add, PERSON, radius=0.12, location=(x, y, z + 1.80))


def clear():
    for ob in list(kit.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    for o in train:
        o.location = train0[o.name]
    for pb in rig.pose.bones:
        pb.matrix_basis.identity()
    build_max.set_expression(rig, "neutral")


def shift_train(dx):
    for o in train:
        o.location = train0[o.name] + Vector((dx, 0, 0))


YAW = {"out": 0.0, "fwd": 90.0, "back": -90.0}


def place(x, y, z, facing, lean=0.0, legs="stand", arms="down", expr="neutral"):
    """facing: 'out' (-Y, sideways to travel), 'back' (-X), 'fwd' (+X); lean in degrees toward +X."""
    for pb in rig.pose.bones:
        pb.matrix_basis.identity()
    rig.matrix_world = (Matrix.Translation((x, y, z)) @ Matrix.Rotation(math.radians(lean), 4, "Y")
                        @ Matrix.Rotation(math.radians(YAW[facing]), 4, "Z"))
    bpy.context.view_layer.update()
    R = rig.matrix_world.to_3x3()
    def aim(bones, local):
        for b in bones:
            build_max.aim_bone(rig, b, R @ Vector(local))
    if arms == "down":
        aim(("upperarm01.L", "upperarm02.L", "lowerarm01.L", "lowerarm02.L"), (0.18, -0.05, -1))
        aim(("upperarm01.R", "upperarm02.R", "lowerarm01.R", "lowerarm02.R"), (-0.18, -0.05, -1))
    elif arms == "flail":
        aim(("upperarm01.L", "upperarm02.L"), (1, -0.2, 0.45)); aim(("lowerarm01.L", "lowerarm02.L"), (0.6, -0.4, 0.8))
        aim(("upperarm01.R", "upperarm02.R"), (-1, -0.2, 0.3)); aim(("lowerarm01.R", "lowerarm02.R"), (-0.7, -0.5, 0.6))
    elif arms == "pole":                       # left hand on the door pole beside him
        aim(("upperarm01.L", "upperarm02.L"), (0.5, -0.3, 0.35)); aim(("lowerarm01.L", "lowerarm02.L"), (0.1, -0.2, 1))
        aim(("upperarm01.R", "upperarm02.R", "lowerarm01.R", "lowerarm02.R"), (-0.18, -0.05, -1))
    if legs == "stride":                       # left leg forward (local -Y is his front)
        aim(("upperleg01.L", "upperleg02.L"), (0.05, -0.42, -1)); aim(("lowerleg01.L", "lowerleg02.L"), (0.05, -0.30, -1))
        aim(("upperleg01.R", "upperleg02.R"), (-0.05, 0.38, -1)); aim(("lowerleg01.R", "lowerleg02.R"), (-0.05, 0.55, -1))
    elif legs == "stride_r":
        aim(("upperleg01.R", "upperleg02.R"), (-0.05, -0.42, -1)); aim(("lowerleg01.R", "lowerleg02.R"), (-0.05, -0.30, -1))
        aim(("upperleg01.L", "upperleg02.L"), (0.05, 0.38, -1)); aim(("lowerleg01.L", "lowerleg02.L"), (0.05, 0.55, -1))
    elif legs == "wide":                       # feet apart sideways (to his left and right)
        aim(("upperleg01.L", "upperleg02.L", "lowerleg01.L", "lowerleg02.L"), (0.30, 0, -1))
        aim(("upperleg01.R", "upperleg02.R", "lowerleg01.R", "lowerleg02.R"), (-0.30, 0, -1))
    elif legs == "step_down":                  # one foot reaching down and out of the door
        aim(("upperleg01.L", "upperleg02.L"), (0.05, -0.55, -1)); aim(("lowerleg01.L", "lowerleg02.L"), (0.05, -0.1, -1))
    build_max.set_expression(rig, expr)
    rig.matrix_world = (Matrix.Translation((x, y, z)) @ Matrix.Rotation(math.radians(lean), 4, "Y")
                        @ Matrix.Rotation(math.radians(YAW[facing]), 4, "Z"))   # set_expression may pose the head only
    bpy.context.view_layer.update()


def look(pos, tgt, lens):
    cam.location = pos
    cam.rotation_euler = (Vector(tgt) - Vector(pos)).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = lens


def frame_max(x, y, side=-1, lens=35, offset_x=0.25):
    """Side or front framing with Max ~62% of frame height and contact ~70% down (Codex 019)."""
    d = 1.45 * lens / 18.0
    centre_z = PLAT_Z + 0.62
    look((x + offset_x, y + side * d, centre_z), (x + offset_x, y, centre_z), lens)


def needle(kmh):
    p = bpy.data.objects["speedo_needle_pivot"]
    p.rotation_euler.y = -(math.radians(225 - kmh * 270 / 120) - math.pi / 2)


def dial_cam():
    """Hub, 0, 10, 20, 30 and km/h in frame, with a little console; identical for shots 3 and 10."""
    look((399.965, -0.50, 1.19), (399.965, -0.27, 1.19), 70)


B = []


def board(key, line):
    def deco(f):
        B.append((key, line, f))
        return f
    return deco


@board("1a", "Getting off a slow train looks EASY. (drone start: coach, doorway and Max already readable)")
def b1a():
    place(MAXDOOR_X, -1.55, FLOOR_Z, "out", arms="pole", expr="neutral")
    look((-2.4, -6.6, 4.1), (DOOR_X + 0.2, -1.8, 1.9), 30)       # under the canopy roof (5.1 m)


@board("1b", "…looks EASY. (drone lands: a 3/4 on the shoe hovering at the door edge)")
def b1b():
    place(MAXDOOR_X, -1.55, FLOOR_Z, "out", legs="step_down", arms="pole", expr="neutral")
    look((4.3, -4.4, 1.25), (DOOR_X + 0.25, -1.8, 1.55), 32)


@board("2a", "Physics disagrees. (low reverse angle; a pillar in the foreground…)")
def b2a():
    place(MAXDOOR_X, -1.55, FLOOR_Z, "out", arms="pole", expr="curious")
    look((8.9, -7.6, 1.15), (DOOR_X + 0.6, -1.8, 1.9), 42)


@board("2b", "…disagrees. (…the doorway has slid past it: the train is moving)")
def b2b():
    shift_train(1.6)
    place(MAXDOOR_X + 1.6, -1.55, FLOOR_Z, "out", arms="pole", expr="curious")
    look((8.9, -7.6, 1.15), (DOOR_X + 0.6, -1.8, 1.9), 42)


@board("3a", "At ten kilometres an hour… (the needle lands on 10)")
def b3a():
    needle(10)
    dial_cam()


@board("3b", "…more than twice a comfortable walking pace. (back at the door: a confident smirk)")
def b3b():
    place(MAXDOOR_X, -1.55, FLOOR_Z, "out", arms="pole", expr="curious")
    look((MAXDOOR_X + 0.5, -3.3, 2.75), (MAXDOOR_X, -1.55, 2.68), 50)


@board("4a", "…when your shoe grips, your foot slows sharply… (the ghost still overlaps him; the shoe on a joint)")
def b4a():
    x = 2.0
    place(x, -2.75, PLAT_Z, "out", lean=3, legs="stride", expr="surprised")
    ghost(x, -2.75, PLAT_Z)
    arrow((x + 0.05, -2.85, PLAT_Z + 0.05), (-0.45, 0, 0), TEAL)
    frame_max(x, -2.75, side=-1, lens=35, offset_x=0.5)


@board("4b", "…while your upper body keeps moving. (the ghost glides on; the foot stays on the same joint)")
def b4b():
    x = 2.0
    place(x, -2.75, PLAT_Z, "out", lean=12, legs="stride", expr="surprised")
    ghost(x + 1.3, -2.75, PLAT_Z)
    arrow((x + 0.15, -2.75, PLAT_Z + 1.3), (0.8, 0, 0), AMBER)
    arrow((x + 0.05, -2.85, PLAT_Z + 0.05), (-0.45, 0, 0), TEAL)
    tip_arrow((x, -2.5, PLAT_Z + 0.08))
    frame_max(x, -2.75, side=-1, lens=35, offset_x=0.5)


@board("5a", "So facing backward, you can tip backward… (profile: he faces left, falls right)")
def b5a():
    x = 2.0
    place(x, -2.8, PLAT_Z, "back", lean=20, legs="stride", expr="scared")
    ghost(x + 1.5, -2.8, PLAT_Z)
    arrow((x + 0.25, -2.8, PLAT_Z + 1.25), (0.8, 0, 0), AMBER)
    tip_arrow((x, -2.55, PLAT_Z + 0.08))
    frame_max(x, -2.8, side=-1, lens=35, offset_x=0.5)


@board("5b", "…the way you can't see. (orbit end: his face, eyes the wrong way; travel still projects right)")
def b5b():
    x = 2.0
    place(x, -2.8, PLAT_Z, "back", lean=24, legs="stride", expr="scared")
    ghost(x + 1.7, -2.8, PLAT_Z)
    look((x - 2.2, -4.9, 1.75), (x + 0.3, -2.8, 1.55), 35)


@board("6", "Facing sideways… can throw you off balance. (front-on; both feet planted apart; tipping right)")
def b6():
    x = 2.0
    place(x, -2.9, PLAT_Z, "out", lean=18, legs="wide", expr="wince")
    ghost(x + 1.5, -2.9, PLAT_Z)
    arrow((x + 0.25, -3.1, PLAT_Z + 1.2), (0.8, 0, 0), AMBER)
    frame_max(x, -2.9, side=-1, lens=35, offset_x=0.4)


@board("7a", "Facing forward, a few quick steps… (step 1: the arrow still long)")
def b7a():
    x = 3.0
    place(x, -3.0, PLAT_Z, "fwd", lean=10, legs="stride", expr="thinking")
    add(bpy.ops.mesh.primitive_cylinder_add, TEAL, radius=0.08, depth=0.01, location=(x - 0.4, -3.05, PLAT_Z + 0.01))
    arrow((x + 0.15, -3.0, PLAT_Z + 1.25), (0.75, 0, 0), AMBER)
    frame_max(x, -3.0, side=-1, lens=35, offset_x=0.3)


@board("7b", "…can spread out the slowdown. (step 3: further along, the arrow shorter)")
def b7b():
    x = 4.4
    place(x, -3.0, PLAT_Z, "fwd", lean=7, legs="stride_r", expr="thinking")
    for k, px in enumerate((x - 1.8, x - 1.1, x - 0.4)):
        add(bpy.ops.mesh.primitive_cylinder_add, TEAL, radius=0.08, depth=0.01,
            location=(px, -3.0 + (0.07 if k % 2 else -0.07), PLAT_Z + 0.01))
    arrow((x + 0.15, -3.0, PLAT_Z + 1.25), (0.45, 0, 0), AMBER)
    frame_max(x - 0.3, -3.0, side=-1, lens=35, offset_x=0.3)


@board("8", "…but you can still lose your BALANCE. (same lens, eased in; head, torso and feet in frame)")
def b8():
    x = 4.8
    place(x, -3.0, PLAT_Z, "fwd", lean=17, legs="stride", arms="flail", expr="scared")
    arrow((x + 0.25, -3.0, PLAT_Z + 1.2), (0.4, 0, 0), AMBER)
    frame_max(x, -3.0, side=-1, lens=40, offset_x=0.25)


@board("9a", "One wet patch… (insert: the shoe lands in a puddle and the grip arrow is gone)")
def b9a():
    x = 5.0
    place(x, -2.6, PLAT_Z, "fwd", lean=12, legs="stride", expr="scared")
    add(bpy.ops.mesh.primitive_cylinder_add, WATER, radius=0.32, depth=0.004, location=(x + 0.35, -2.6, PLAT_Z + 0.006))
    look((x + 1.4, -3.6, PLAT_Z + 0.35), (x + 0.3, -2.6, PLAT_Z + 0.15), 45)


@board("9b", "one bag… (insert: a backpack strap snags the door pole; board to come with a bag asset)")
def b9b():
    place(MAXDOOR_X, -1.55, FLOOR_Z, "out", legs="step_down", expr="scared")
    look((MAXDOOR_X + 0.9, -2.9, 2.2), (MAXDOOR_X, -1.55, 2.1), 40)


@board("9c", "one crowded step… (insert: a commuter's shoulder clips him)")
def b9c():
    x = 5.0
    place(x, -2.7, PLAT_Z, "fwd", lean=12, legs="stride", expr="scared")
    person(x + 0.55, -3.05, PLAT_Z)
    frame_max(x + 0.2, -2.8, side=-1, lens=35, offset_x=0.2)


@board("9d", "…and the GAP is right there. (low: platform lip, dark gap with depth, coach sill, his heel)")
def b9d():
    x = 5.0
    place(x, -2.32, PLAT_Z, "fwd", lean=10, legs="stride", expr="scared")
    look((x - 0.9, -2.45, PLAT_Z + 0.32), (x + 0.6, -2.0, PLAT_Z - 0.05), 24)


@board("10", "So wait until the train has completely STOPPED… (the same dial framing: the needle at 0)")
def b10():
    needle(0)
    dial_cam()


@board("11a", "…even if… (the shoe settles on the platform; a pillar stays put behind)")
def b11a():
    place(DOOR_X, -2.55, PLAT_Z, "out", legs="stride", expr="relief_smile")
    look((5.6, -4.3, 1.05), (DOOR_X, -2.7, 1.2), 32)


@board("11b", "(crane up to shot 1a's exact framing: the loop cut)")
def b11b():
    place(MAXDOOR_X, -2.55, PLAT_Z, "out", expr="relief_smile")
    look((-2.4, -6.6, 4.1), (DOOR_X + 0.2, -1.8, 1.9), 30)       # = 1a, the loop


ONLY = set(sys.argv[sys.argv.index("--") + 2:])     # optional: re-render only these keys
rows = []
for key, line, f in B:
    if ONLY and key not in ONLY:
        rows.append((key, line, os.path.join(out, f"board_{key}.png")))
        continue
    clear()
    f()
    bpy.context.view_layer.update()
    sc.render.filepath = os.path.join(out, f"board_{key}.png")
    bpy.ops.render.render(write_still=True)
    rows.append((key, line, sc.render.filepath))
with open(os.path.join(out, "boards.txt"), "w") as fh:
    for r in rows:
        fh.write("\t".join(r) + "\n")
print("boards:", len(rows))
