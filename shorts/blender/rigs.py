"""Shared Blender helpers for the production pipeline (runs inside Blender's Python).

Cameras are physically based (real focal length in mm, f-stop depth of field, 9:16
sensor fit). A camera move is a function t -> (position, target[, lens, roll]) for
t in 0..1; bake_move() samples it into eased keyframes, so any move (dolly, crane,
orbit, drone path, fly-through) is a few lines and stays hand-editable in Blender.
"""
import math

import bpy
from mathutils import Quaternion, Vector


# ------------------------------------------------------------------ basics --
def ease(t):
    """Smooth in/out (cinematic acceleration and deceleration)."""
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def lerp(a, b, t):
    return Vector(a).lerp(Vector(b), t) if not isinstance(a, (int, float)) else a + (b - a) * t


def bezier(p0, p1, p2, p3, t):
    """Cubic Bezier point: smooth drone and crane paths."""
    p0, p1, p2, p3 = map(Vector, (p0, p1, p2, p3))
    u = 1 - t
    return u ** 3 * p0 + 3 * u * u * t * p1 + 3 * u * t * t * p2 + t ** 3 * p3


def collection(name, parent=None):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    parent = parent or bpy.context.scene.collection
    if c.name not in parent.children:
        parent.children.link(c)
    return c


def material(name, color, rough=0.5, emission=0.0, alpha=1.0, metal=0.0):
    """Principled material; also sets the viewport colour so Solid view matches."""
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emission:
        b.inputs["Emission Color"].default_value = (*color, 1)
        b.inputs["Emission Strength"].default_value = emission
    if alpha < 1:
        b.inputs["Alpha"].default_value = alpha
        if hasattr(m, "surface_render_method"):
            m.surface_render_method = "BLENDED"
    m.diffuse_color = (*color, alpha)
    return m


def prim(kind, name, coll, loc=(0, 0, 0), scale=(1, 1, 1), rot=(0, 0, 0), mat=None, parent=None, **kw):
    """Add a primitive (cube, uv_sphere, cylinder, cone, torus, plane, circle, ico_sphere) to a collection."""
    op = getattr(bpy.ops.mesh, f"primitive_{kind}_add")
    op(location=(0, 0, 0), **kw)
    ob = bpy.context.active_object
    ob.name = name
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    coll.objects.link(ob)
    ob.location, ob.scale = Vector(loc), Vector(scale)
    ob.rotation_euler = [math.radians(a) for a in rot]
    if mat:
        ob.data.materials.append(mat)
    if parent:
        ob.parent = parent
    if kind in ("uv_sphere", "ico_sphere", "cylinder", "torus"):
        for p in ob.data.polygons:
            p.use_smooth = True
    return ob


def empty(name, coll, loc=(0, 0, 0), parent=None):
    ob = bpy.data.objects.new(name, None)
    coll.objects.link(ob)
    ob.location = Vector(loc)
    ob.parent = parent
    return ob


def fcurves(idblock):
    """F-curves of an ID's action on Blender 4.x and 5.x (5.x stores them in layered-action channelbags)."""
    ad = getattr(idblock, "animation_data", None)
    if not ad or not ad.action:
        return []
    act = ad.action
    if hasattr(act, "fcurves"):
        return list(act.fcurves)
    from bpy_extras import anim_utils
    bag = anim_utils.action_get_channelbag_for_slot(act, ad.action_slot)
    return list(bag.fcurves) if bag else []


def key(ob, path, frame, value, index=-1, interp=None):
    """Set a property and keyframe it. value may be a scalar or a vector."""
    target, attr = (ob, path) if "." not in path else (ob.path_resolve(path.rsplit(".", 1)[0]), path.rsplit(".", 1)[1])
    setattr(target, attr, value)
    target.keyframe_insert(attr, frame=frame, index=index)
    if interp:
        ad = (ob.id_data if hasattr(ob, "id_data") else ob).animation_data
        if ad and ad.action:
            for fc in fcurves(ob.id_data if hasattr(ob, "id_data") else ob):
                for kp in fc.keyframe_points:
                    if int(round(kp.co.x)) == frame:
                        kp.interpolation = interp


def output_format(image_settings, fmt):
    """Set a render output format on Blender 4.x and 5.x (5.x first needs the media type)."""
    if hasattr(image_settings, "media_type"):
        image_settings.media_type = "VIDEO" if fmt == "FFMPEG" else "IMAGE"
    image_settings.file_format = fmt


# ----------------------------------------------------------------- cameras --
def camera(name, coll, lens=50, fstop=4.0, sensor_fit="VERTICAL"):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_fit, cd.sensor_height = sensor_fit, 24.0  # 9:16 frame: vertical 24 mm, like a phone-held cine camera
    cd.dof.use_dof = True
    cd.dof.aperture_fstop = fstop
    cd.clip_start, cd.clip_end = 0.02, 2000
    ob = bpy.data.objects.new(name, cd)
    coll.objects.link(ob)
    ob.rotation_mode = "QUATERNION"
    return ob


def look_at(pos, target, roll_deg=0.0):
    q = (Vector(target) - Vector(pos)).to_track_quat("-Z", "Y")
    if roll_deg:
        q = q @ Quaternion((0, 0, 1), math.radians(roll_deg))
    return q


def bake_move(cam, f0, f1, move, step=3, focus=True):
    """Keyframe a camera move. move(t) -> dict(pos, target, lens=?, roll=?, focus=?)."""
    prev = None
    frames = list(range(f0, f1 + 1, step))
    if frames[-1] != f1:
        frames.append(f1)
    for fr in frames:
        t = (fr - f0) / max(1, f1 - f0)
        m = move(t)
        pos, tgt = Vector(m["pos"]), Vector(m["target"])
        q = look_at(pos, tgt, m.get("roll", 0.0))
        if prev is not None and prev.dot(q) < 0:  # keep quaternions continuous (no flips)
            q.negate()
        prev = q
        key(cam, "location", fr, pos)
        key(cam, "rotation_quaternion", fr, q)
        if "lens" in m:
            key(cam.data, "lens", fr, m["lens"])
        if focus:
            key(cam.data, "dof.focus_distance", fr, m.get("focus", (tgt - pos).length))


def handheld(cam, f0, f1, strength=0.2):
    """Subtle operator shake on rotation, limited to the shot's frames."""
    for fc in fcurves(cam):
        if fc.data_path == "rotation_quaternion" and fc.array_index in (1, 2, 3):
            mod = fc.modifiers.new("NOISE")
            mod.scale, mod.strength = 18, 0.012 * strength * 5
            mod.phase = fc.array_index * 7.3
            mod.use_restricted_range = True
            mod.frame_start, mod.frame_end = f0, f1
            mod.blend_in = mod.blend_out = 4


def impulse_shake(cam, frame, frames=10, amp=0.05):
    """Camera jolt (e.g. on 'POP!'): decaying jitter added to the baked location."""
    import random
    rnd = random.Random(frame)
    base = {}
    fc_loc = [fc for fc in fcurves(cam) if fc.data_path == "location"]
    for i in range(frames + 1):
        f = frame + i
        decay = (1 - i / frames) ** 2
        for fc in fc_loc:
            v = fc.evaluate(f)
            base.setdefault((fc.array_index, f), v)
            fc.keyframe_points.insert(f, v + (rnd.uniform(-1, 1) * amp * decay))
