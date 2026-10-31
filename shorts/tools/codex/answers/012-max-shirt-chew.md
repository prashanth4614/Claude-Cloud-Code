# Codex answer: 012-max-shirt-chew

_model: gpt-6.1-sol, reasoning effort: high, read-only, cap 1200s_

**Verdict: add two geometric shirt correctives; strengthen chewing and patch its actual pilot call site.** Bump strength alone cannot shorten the stretched armpit. True independent cheek inflation is impossible with these 52 units; opposite-side squint/press can suggest it.

Proposed code below; unrendered here. Blender crashed during Metal initialization before inspection. No files changed.

**1. Shirt: sample the actual skin deformation, then invert it.**

This avoids assuming linear skinning or hard-coding Euler channels. Temporary probes disappear after building; only two shape keys and their drivers remain.

In [max_look.py:557](/Users/prashanthmogili/Claude-Cloud-Code-codex/shorts/blender/max_look.py:557), replace the early return:

```python
    shaded = ob.get("max_shirt_upgrade") == 1
```

Immediately after existing `mesh = ob.data`, insert:

```python
    add_shirt_correctives(
        rig, ob, shirt, positions, shoulders, metres, transform)
    if shaded:
        return
```

Add this function before `upgrade_shirt()`:

```python
def add_shirt_correctives(rig, ob, shirt, positions,
                         shoulders, metres, transform):
    import math
    from mathutils import Matrix, Vector
    from build_max import aim_bone

    if ob.get("max_shirt_correctives") == 1:
        return
    if not any(m.type == "ARMATURE" and m.object == rig
               and m.show_viewport for m in ob.modifiers):
        raise ValueError("Expected active Max armature modifier")

    if not ob.data.shape_keys:
        ob.shape_key_add(name="Basis", from_mix=False)
    keys = ob.data.shape_keys
    if not keys.use_relative:
        raise ValueError("Expected relative shirt shape keys")

    names = ["max_pit_L", "max_pit_R"]
    # Safe retry after an interrupted build.
    for name in names + ["__pit_probe"]:
        old = keys.key_blocks.get(name)
        if old:
            ob.shape_key_remove(old)

    basis = keys.reference_key
    probe = ob.shape_key_add(name="__pit_probe", from_mix=False)
    saved_pose = [(p, p.matrix_basis.copy()) for p in rig.pose.bones]
    saved_mods = [(m, m.show_viewport) for m in ob.modifiers]
    saved_position = rig.data.pose_position
    to_local = transform.to_3x3().inverted() / metres
    centre_x = sum(p.x for p in shoulders.values()) / 2
    made = []
    eps = 0.001                       # one millimetre in rig/metre coordinates

    def evaluated_positions():
        bpy.context.view_layer.update()
        ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh = ev.to_mesh()
        try:
            if len(mesh.vertices) != len(positions):
                raise ValueError("Probe requires unchanged vertex indices")
            return [transform @ v.co * metres for v in mesh.vertices]
        finally:
            ev.to_mesh_clear()

    try:
        rig.data.pose_position = "POSE"
        # Probe only skinning; subdivision must not mix neighbouring vertices.
        for m, _ in saved_mods:
            if m.type != "ARMATURE":
                m.show_viewport = False

        for side, name in zip(("L", "R"), names):
            for p, _ in saved_pose:
                p.matrix_basis.identity()
            bpy.context.view_layer.update()

            shoulder = shoulders[side]
            sign = 1 if shoulder.x > centre_x else -1
            a = math.radians(70)
            direction = rig.matrix_world.to_3x3() @ Vector(
                (sign * math.sin(a), -0.25, -math.cos(a)))
            for bone in ("upperarm01", "upperarm02"):
                aim_bone(rig, f"{bone}.{side}", direction)

            probe.value = 0
            base = evaluated_positions()
            columns = []
            for axis in range(3):
                step = Vector((0, 0, 0))
                step[axis] = eps
                local_step = to_local @ step
                for i in shirt:
                    probe.data[i].co = basis.data[i].co + local_step
                probe.value = 1
                moved = evaluated_positions()
                columns.append([(q - p) / eps
                                for p, q in zip(base, moved)])
            probe.value = 0

            pit = shoulder + Vector((-sign * 0.03, 0, -0.12))
            weights = {}
            for i in shirt:
                p = positions[i]
                if sign * (p.x - centre_x) <= 0:
                    continue
                d = p - pit
                w = 1.0
                for component, width in zip(d, (0.10, 0.18, 0.13)):
                    w *= max(0.0, 1.0 - (component / width) ** 2) ** 2
                # Protect shoulder cap and sleeve.
                w *= min(1.0, max(0.0,
                    (shoulder.z - 0.045 - p.z) / 0.04))
                if w > 1e-4:
                    weights[i] = w
            if not weights:
                raise ValueError(f"No armpit vertices: {side}")

            centre = sum((base[i] * w for i, w in weights.items()),
                         Vector()) / sum(weights.values())
            key = ob.shape_key_add(name=name, from_mix=False)
            key.relative_key = basis
            key.value = 0
            made.append((side, key))

            for i, w in weights.items():
                q = base[i]
                # Remove part of the skin-driven lift; cap at 22 mm.
                drop = max(-0.022, min(0.008,
                    -0.35 * (q.z - positions[i].z)))
                u = q.z + drop - centre.z - (
                    0.55 * sign * (q.x - centre.x))
                relief = 0.006 * sum(
                    math.exp(-((u - offset) / 0.012) ** 2)
                    for offset in (-0.04, 0.0, 0.04))
                outward = Vector((q.x - centre_x,
                                   q.y - shoulder.y, 0)).normalized()
                desired = w * (outward * relief + Vector((0, 0, drop)))
                jacobian = Matrix(
                    [column[i] for column in columns]).transposed()
                if abs(jacobian.determinant()) < 1e-8:
                    raise ValueError(f"Singular skinning at vertex {i}")
                key.data[i].co = basis.data[i].co + (
                    to_local @ (jacobian.inverted() @ desired))
    finally:
        probe.value = 0
        ob.shape_key_remove(probe)
        for p, matrix in saved_pose:
            p.matrix_basis = matrix
        for m, enabled in saved_mods:
            m.show_viewport = enabled
        rig.data.pose_position = saved_position
        bpy.context.view_layer.update()

    torso = max(
        (b for b in rig.data.bones if b.name.startswith("spine")),
        key=lambda b: (b.head_local.z + b.tail_local.z) / 2)
    up_sign = 1 if torso.tail_local.z > torso.head_local.z else -1

    for side, key in made:
        driver = key.driver_add("value").driver
        driver.type = "SCRIPTED"
        # Evaluated world quaternions: independent of pose rotation mode,
        # armature heading, and upper-arm axial twist.
        for prefix, bone in (("a", f"upperarm01.{side}"),
                             ("t", torso.name)):
            for component in "wxyz":
                v = driver.variables.new()
                v.name = prefix + component
                v.type = "TRANSFORMS"
                target = v.targets[0]
                target.id = rig
                target.bone_target = bone
                target.transform_space = "WORLD_SPACE"
                target.rotation_mode = "QUATERNION"
                target.transform_type = "ROT_" + component.upper()
        # Dot product of each bone's world +Y axis.
        dot = (
            "4*(ax*ay-aw*az)*(tx*ty-tw*tz)"
            "+(1-2*(ax*ax+az*az))*(1-2*(tx*tx+tz*tz))"
            "+4*(ay*az+aw*ax)*(ty*tz+tw*tx)"
        )
        onset = math.cos(math.radians(15))
        span = onset - math.cos(math.radians(70))
        driver.expression = (
            f"min(1,max(0,({up_sign}*({dot})+{onset:.6f})/"
            f"{span:.6f}))")

    ob.data.update()
    ob["max_shirt_correctives"] = 1
```

World-transform quaternion targets include parenting/rest orientation, matching this driver’s construction. [Blender DriverTarget reference](https://docs.blender.org/api/2.90/bpy.types.DriverTarget.html)

**Verification render:** existing shirt framing: 900×1000, 55 mm, 2.45 m, chest target. Right `thumbs_up(..., raised=True)`; left actual S07 hand-to-ear pose, applied afterward because `thumbs_up()` resets both arms. Expect three short diagonal ridges, less upward drag, intact sleeve cap and jeans. Separately sweep each arm down→overhead in viewport; corresponding key should progress 0→1 without twist-induced changes.

**Risks:** sampled at one representative pose; not universal cloth. Sparse base topology may soften the 12 mm ridges. Check body penetration and overhead silhouette. If tuning, delete `max_shirt_correctives` before rebuilding. Existing bump remains; increase nothing until geometry passes.

**2. Chew: three jaw openings, alternating suggested cheek fullness.**

Replace `chew`/`chew_b` in [max_expressions.py:108](/Users/prashanthmogili/Claude-Cloud-Code-codex/shorts/blender/max_expressions.py:108):

```python
    "chew": {
        "jawOpen": 0.34, "mouthClose": 0.30,
        "jawLeft": 0.42, "jawForward": 0.10,
        "mouthLeft": 0.16, "cheekPuff": 0.82,
        "cheekSquintRight": 0.55,
        "mouthPressRight": 0.38, "mouthPressLeft": 0.12,
        "mouthShrugLower": 0.16,
    },
    "chew_b": {
        "jawOpen": 0.06, "mouthClose": 0.08,
        "jawLeft": 0.10, "mouthLeft": 0.05,
        "cheekPuff": 0.38, "cheekSquintRight": 0.30,
        "mouthPressLeft": 0.30, "mouthPressRight": 0.38,
    },
```

After `HEAD_POSE`, add:

```python
HEAD_POSE.update(chew=(3, -3, 0), chew_b=(1, -2, 0))

def _mirror_chew(units):
    def opposite(name):
        if name.endswith("Left"):
            return name[:-4] + "Right"
        if name.endswith("Right"):
            return name[:-5] + "Left"
        return name
    return {opposite(k): v for k, v in units.items()}

for _name in ("chew", "chew_b"):
    EXPRESSIONS[_name + "_r"] = _mirror_chew(EXPRESSIONS[_name])
    x, y, z = HEAD_POSE[_name]
    HEAD_POSE[_name + "_r"] = (x, -y, -z)
    assert set(EXPRESSIONS[_name]) <= FACE_UNITS
```

Replace [build_max.py:221](/Users/prashanthmogili/Claude-Cloud-Code-codex/shorts/blender/build_max.py:221):

```python
def chew_keys(start, chews=3, period=12):
    """24 fps: three chews over 36 frames; opening peaks +3,+15,+27."""
    if chews < 1 or period < 8:
        raise ValueError("Chewing needs >=1 chew and >=8 frames/chew")
    yield start - 3, "neutral"
    for i in range(chews):
        t = start + i * period
        suffix = "_r" if i % 2 else ""
        yield t, "chew_b" + suffix
        yield t + round(period * 0.25), "chew" + suffix
        yield t + round(period * 0.58), "chew_b" + suffix
    yield start + chews * period, "neutral"


def ease_chew(rig, first, last):
    from rigs import fcurves
    body = next(o for o in rig.children if o.name.endswith(".body"))
    face_paths = {k.path_from_id("value")
                  for k in body.data.shape_keys.key_blocks if _unit(k.name)}
    head_paths = {
        rig.pose.bones[n].path_from_id("rotation_euler")
        for n in ("neck01", "neck02", "head") if n in rig.pose.bones
    }
    for owner, paths in ((body.data.shape_keys, face_paths),
                         (rig, head_paths)):
        for curve in fcurves(owner):
            if curve.data_path not in paths:
                continue
            for point in curve.keyframe_points:
                if first <= point.co.x <= last:
                    point.interpolation = "BEZIER"
                    point.handle_left_type = "AUTO_CLAMPED"
                    point.handle_right_type = "AUTO_CLAMPED"


def chew_cycle(rig, start, chews=3, period=12):
    for frame, name in chew_keys(start, chews, period):
        set_expression(rig, name, frame=frame)
    ease_chew(rig, start - 3, start + chews * period)
```

**Required pilot integration:** its current four-cycle loop bypasses this function. In [real_max.py:197](/Users/prashanthmogili/Claude-Cloud-Code-codex/shorts/pilot_ear_pop/real_max.py:197), replace `face(fc + 4, ...)` and that loop:

```python
    from build_max import chew_keys, ease_chew
    chew_start = fc + 4
    chew_period = min(12, (rng("S12a")[1] - chew_start) // 3)
    if chew_period < 8:
        raise ValueError("Extend S12a: insufficient room for three chews")
    for f, name in chew_keys(chew_start, 3, chew_period):
        face(f, name)
```

After the sorted timeline is keyed, before `_blinks(...)`:

```python
    ease_chew(rig, chew_start - 3, chew_start + 3 * chew_period)
```

**Verification render:** render `chew`—the best sheet still—at 85 mm, 1.25 m, camera 10° toward Max’s left cheek; retain existing lighting. Expect lowered/offset chin, fuller left cheek, displaced sealed mouth, no teeth. Then inspect frames 0–36 at 24 fps: exactly three openings, left→right→left fullness.

**Risks:** `mouthClose` response is asset-specific. If a lip gap appears, increase it in 0.02 steps; inspect quarter-cycle frames too. Squint suggests cheek compression, not independent inflation.

**Cost:** ₹0 assets/services. Estimate 60–90 minutes integration/tuning; two stills roughly 20 seconds plus loading at recorded Mac baselines. A 36-frame face check roughly three minutes at 128 spp. Render overhead from two shirt keys unbenchmarked; no simulation.
_took 414 s_
STATUS: OK
