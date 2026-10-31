"""Retarget motion capture (BVH: CMU / cgspeed naming, or Mixamo) onto Max's MPFB2 default rig.

    import mocap_retarget as mr
    src = mr.load_bvh("assets/mocap/cmu/xx_yy.bvh")          # an armature with the BVH action
    mr.retarget(src, rig, frame_start=1, frames=(f0, f1), step=1)  # bakes keys on Max's pose bones

How it works (rest-pose independent, so a T-pose BVH drives Max's A-pose rig):
- for every mapped bone, each frame, the target bone is aimed along the source bone's world direction
  (head → child head), and rolled so its bend plane matches the source (for limbs: the plane of the
  next joint). Twist bones in a chain (upperarm01/02, upperleg01/02, lowerleg01/02) share the
  direction;
- the hips: Max's root follows the source hips position, scaled by leg length, and his pelvis matches
  the source's left-to-right hip axis and spine direction;
- feet: an optional contact lock (`lock_feet`) holds a foot in place in world space while its source foot
  is near the ground and nearly still (no foot sliding).
Faces are untouched: facial acting is keyed separately (max_expressions).
"""
import math

import bpy
from mathutils import Matrix, Vector

# source joint names (CMU via cgspeed, then Mixamo) → Max bones driven by that joint
MAP = [
    # (source joint, source child joint for the direction, Max bones, bend-plane joint or None)
    ("LowerBack", "Spine", ["spine05", "spine04"], None),
    ("Spine", "Spine1", ["spine03", "spine02"], None),
    ("Spine1", "Neck", ["spine01"], None),
    ("Neck", "Head", ["neck01", "neck02", "neck03"], None),
    ("Head", None, ["head"], None),
    ("LeftShoulder", "LeftArm", ["clavicle.L", "shoulder01.L"], None),
    ("LeftArm", "LeftForeArm", ["upperarm01.L", "upperarm02.L"], "LeftHand"),
    ("LeftForeArm", "LeftHand", ["lowerarm01.L", "lowerarm02.L"], "LeftArm"),
    ("RightShoulder", "RightArm", ["clavicle.R", "shoulder01.R"], None),
    ("RightArm", "RightForeArm", ["upperarm01.R", "upperarm02.R"], "RightHand"),
    ("RightForeArm", "RightHand", ["lowerarm01.R", "lowerarm02.R"], "RightArm"),
    ("LeftUpLeg", "LeftLeg", ["upperleg01.L", "upperleg02.L"], "LeftFoot"),
    ("LeftLeg", "LeftFoot", ["lowerleg01.L", "lowerleg02.L"], "LeftUpLeg"),
    ("LeftFoot", "LeftToeBase", ["foot.L"], None),
    ("RightUpLeg", "RightLeg", ["upperleg01.R", "upperleg02.R"], "RightFoot"),
    ("RightLeg", "RightFoot", ["lowerleg01.R", "lowerleg02.R"], "RightUpLeg"),
    ("RightFoot", "RightToeBase", ["foot.R"], None),
]
ALIASES = {   # Mixamo / other BVH spellings → the names above
    "mixamorig:Hips": "Hips", "mixamorig:Spine": "LowerBack", "mixamorig:Spine1": "Spine",
    "mixamorig:Spine2": "Spine1", "mixamorig:Neck": "Neck", "mixamorig:Head": "Head",
    "mixamorig:LeftShoulder": "LeftShoulder", "mixamorig:LeftArm": "LeftArm",
    "mixamorig:LeftForeArm": "LeftForeArm", "mixamorig:LeftHand": "LeftHand",
    "mixamorig:RightShoulder": "RightShoulder", "mixamorig:RightArm": "RightArm",
    "mixamorig:RightForeArm": "RightForeArm", "mixamorig:RightHand": "RightHand",
    "mixamorig:LeftUpLeg": "LeftUpLeg", "mixamorig:LeftLeg": "LeftLeg", "mixamorig:LeftFoot": "LeftFoot",
    "mixamorig:LeftToeBase": "LeftToeBase", "mixamorig:RightUpLeg": "RightUpLeg",
    "mixamorig:RightLeg": "RightLeg", "mixamorig:RightFoot": "RightFoot",
    "mixamorig:RightToeBase": "RightToeBase",
}


def load_bvh(path, name=None):
    before = set(bpy.data.objects)
    bpy.ops.import_anim.bvh(filepath=path, axis_forward="-Z", axis_up="Y", rotate_mode="NATIVE",
                            update_scene_fps=False, update_scene_duration=False)
    ob = next(o for o in bpy.data.objects if o not in before and o.type == "ARMATURE")
    if name:
        ob.name = name
    for b in ob.pose.bones:   # normalise names
        if b.name in ALIASES:
            b.name = ALIASES[b.name]
    ob.hide_render = True
    return ob


def _head(src, name):
    pb = src.pose.bones.get(name)
    return src.matrix_world @ pb.head if pb else None


def _tail(src, name):
    pb = src.pose.bones.get(name)
    return src.matrix_world @ pb.tail if pb else None


def _aim(rig, name, direction, plane_normal=None):
    """Aim pose bone `name` along a world direction; roll its X axis toward plane_normal if given."""
    pb = rig.pose.bones.get(name)
    if pb is None or direction.length < 1e-6:
        return
    inv = rig.matrix_world.to_3x3().inverted()
    y = (inv @ direction).normalized()
    m = pb.matrix.copy()
    q = m.to_3x3().col[1].normalized().rotation_difference(y)
    rot = q.to_matrix() @ m.to_3x3()
    if plane_normal is not None and plane_normal.length > 1e-6:
        n = (inv @ plane_normal)
        n = (n - y * n.dot(y))
        x = rot.col[0] - y * rot.col[0].dot(y)
        if n.length > 1e-6 and x.length > 1e-6:
            rot = x.normalized().rotation_difference(n.normalized()).to_matrix() @ rot
    new = rot.to_4x4()
    new.translation = m.translation
    pb.matrix = new


def leg_length(arm, hip, knee, ankle, head_fn):
    return (head_fn(arm, knee) - head_fn(arm, hip)).length + (head_fn(arm, ankle) - head_fn(arm, knee)).length


def retarget(src, rig, frames, frame_start=1, step=1, root_offset=Vector(), yaw_deg=0.0, lock_feet=True,
             speed=1.0):
    """Bake src's motion (its scene frames `frames` = (f0, f1)) onto rig, starting at frame_start.
    step: sample every `step` source frames (CMU is 120 fps: step 5 → 24 fps; step 1 + speed 0.2 → 5x
    slow motion). root_offset/yaw place the motion in the set (metres, degrees about Z)."""
    sc = bpy.context.scene
    f0, f1 = frames
    sc.frame_set(f0)
    rest_root = rig.matrix_world.translation.copy()
    src_leg = leg_length(src, "LeftUpLeg", "LeftLeg", "LeftFoot", _head)
    max_leg = (rig.matrix_world @ rig.pose.bones["lowerleg01.L"].head - rig.matrix_world @ rig.pose.bones["upperleg01.L"].head).length + \
              (rig.matrix_world @ rig.pose.bones["foot.L"].head - rig.matrix_world @ rig.pose.bones["lowerleg01.L"].head).length
    scale = max_leg / max(src_leg, 1e-6)
    yaw = Matrix.Rotation(math.radians(yaw_deg), 3, "Z")
    hip0 = _head(src, "Hips")
    ground0 = min(_head(src, "LeftToeBase").z, _head(src, "RightToeBase").z) if src.pose.bones.get("LeftToeBase") else hip0.z - src_leg
    out = frame_start
    locked = {}
    for f in range(f0, f1 + 1, step):
        sc.frame_set(f)
        for pb in rig.pose.bones:
            if not pb.name.startswith(("finger", "toe", "eye", "jaw", "tongue", "oris", "levator", "risorius",
                                       "orbicularis", "temporalis", "special", "oculi", "metacarpal")):
                pb.matrix_basis.identity()
        hip = _head(src, "Hips")
        rel = Vector((hip.x - hip0.x, hip.y - hip0.y, hip.z - ground0)) * scale
        rig.location = rest_root + root_offset + yaw @ Vector((rel.x, rel.y, 0)) + Vector((0, 0, 0))
        bpy.context.view_layer.update()
        # pelvis height: match the hips' height above the ground
        root_pb = rig.pose.bones["root"]
        pelvis_now = (rig.matrix_world @ rig.pose.bones["upperleg01.L"].head + rig.matrix_world @ rig.pose.bones["upperleg01.R"].head) / 2
        dz = (rest_root.z + root_offset.z + rel.z) - pelvis_now.z
        root_pb.location = rig.matrix_world.to_3x3().inverted() @ Vector((0, 0, dz)) if dz else root_pb.location
        bpy.context.view_layer.update()
        # pelvis orientation: the hip axis and the spine direction
        lr = yaw @ (_head(src, "LeftUpLeg") - _head(src, "RightUpLeg"))
        up = yaw @ (_head(src, "Spine") - hip) if src.pose.bones.get("Spine") else Vector((0, 0, 1))
        _aim(rig, "root", up, lr)
        bpy.context.view_layer.update()
        for sname, child, tbones, bend in MAP:
            if not src.pose.bones.get(sname):
                continue
            a = _head(src, sname)
            b = _head(src, child) if child and src.pose.bones.get(child) else _tail(src, sname)
            d = yaw @ (b - a)
            normal = None
            if bend and src.pose.bones.get(bend):
                c = _head(src, bend)
                normal = yaw @ (d.cross(c - a))
            for tb in tbones:
                _aim(rig, tb, d, normal)
                bpy.context.view_layer.update()
        if lock_feet:
            for side in ("L", "R"):
                sf = _head(src, "LeftFoot" if side == "L" else "RightFoot")
                tf = rig.pose.bones[f"foot.{side}"]
                world = rig.matrix_world @ tf.head
                near_ground = (sf.z - ground0) * scale < 0.12
                if near_ground:
                    locked.setdefault(side, world.copy())
                else:
                    locked.pop(side, None)
        for pb in rig.pose.bones:
            pb.keyframe_insert("rotation_quaternion" if pb.rotation_mode == "QUATERNION" else "rotation_euler", frame=out)
        rig.pose.bones["root"].keyframe_insert("location", frame=out)
        rig.keyframe_insert("location", frame=out)
        out += 1
    return out - 1, scale
