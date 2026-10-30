"""Catch scene bugs without rendering: what each shot's camera actually sees, plus static checks.

    blender -b FILM.blend -P shorts/blender/qa_scene.py [-- --plan PATH] [--rays 18x32]

For every shot it casts a grid of rays from the camera at the start, middle and end, and reports:
  - FOREIGN  geometry from another set in frame (e.g. the sky's cloud plane seen through an opening)
  - GAP      an interior shot seeing the backdrop dome or nothing at all (a hole in the set)
  - INSIDE   the camera is inside a surface (most rays hit within a few cm)
Static checks: sets whose bounding boxes overlap, displaced meshes with a stretched object scale
(their relief shears into shards), and lights that are visible to the camera inside small spaces.
Exit code 1 if anything is flagged, so builds can stop before a render is wasted.
"""
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]

# shot set (shots.yaml) -> collections allowed in frame, and whether the backdrop/background is fine
SETS = {
    "sky_golden_hour": ({"SET_sky", "ASSET_jet"}, True),
    "sky_high": ({"SET_sky", "ASSET_jet"}, True),
    "cabin": ({"SET_cabin", "CHAR_max"}, False),
    "ear_inside": ({"SET_ear_in"}, False),
    "ear_map": ({"SET_ear_map"}, True),
    "city_dusk": ({"SET_city", "ASSET_jet"}, True),
}
BACKDROPS = {"ear_dome_in", "ear_dome_map", "dusk_dome", "cabin_outside_sky"}
LEGIT_BACKDROP = {"cabin": {"cabin_outside_sky"}}     # the sky through the cabin windows is meant to show


def top_collection(ob, scene):
    tops = {c.name: c for c in scene.collection.children}
    for name, c in tops.items():
        if ob.name in c.all_objects:
            return name
    return "?"


def cast(scene, cam, frame, nx, ny):
    scene.frame_set(frame)
    dg = bpy.context.evaluated_depsgraph_get()
    fr = cam.data.view_frame(scene=scene)
    mw = cam.matrix_world
    o = mw.translation.copy()
    hits = []
    for i in range(nx):
        for j in range(ny):
            u, v = (i + 0.5) / nx, (j + 0.5) / ny
            local = fr[2].lerp(fr[1], u).lerp(fr[3].lerp(fr[0], u), v)
            d = (mw @ local - o).normalized()
            ok, loc, _n, _i, ob, _m = scene.ray_cast(dg, o, d, distance=5000)
            hits.append((ob if ok else None, (loc - o).length if ok else None, u, v))
    return hits


def check_shots(scene, plan, nx, ny):
    problems = []
    for sh in plan["shots"]:
        cam = bpy.data.objects.get(f"CAM_{sh['id']}")
        allowed, bg_ok = SETS.get(sh["set"], (set(), True))
        if cam is None:
            continue
        for tag, f in (("start", sh["start"] + 1), ("mid", (sh["start"] + sh["end"]) // 2), ("end", sh["end"] - 1)):
            hits = cast(scene, cam, f, nx, ny)
            n = len(hits)
            foreign, gap, near, gap_uv = {}, 0, 0, []
            legit = LEGIT_BACKDROP.get(sh["set"], set())
            for ob, dist, u, v in hits:
                if ob is None or ob.name in BACKDROPS:
                    if ob is None or ob.name not in legit:
                        gap += 1
                        gap_uv.append((u, v))
                    continue
                if dist is not None and dist < max(0.02, cam.data.clip_start * 3):
                    near += 1
                top = top_collection(ob, scene)
                if allowed and top not in allowed:
                    foreign[f"{top}/{ob.name}"] = foreign.get(f"{top}/{ob.name}", 0) + 1
            for name, k in sorted(foreign.items(), key=lambda kv: -kv[1]):
                if k / n > 0.005:
                    problems.append(f"{sh['id']} {tag} f{f}: FOREIGN {name} fills {100 * k / n:.0f}% of frame")
            designed_black = tag == "end" and sh.get("out") == "push_through"   # cuts through darkness
            if not bg_ok and gap / n > 0.005 and not designed_black:
                us, vs = [p[0] for p in gap_uv], [p[1] for p in gap_uv]
                where = f"x {min(us):.2f}-{max(us):.2f}, y {min(vs):.2f}-{max(vs):.2f} (0,0 = bottom left)"
                problems.append(f"{sh['id']} {tag} f{f}: GAP backdrop/void visible in {100 * gap / n:.0f}% of frame at {where}")
            if near / n > 0.6 and not sh["move"].startswith("push_through") and sh["id"] not in ("S02", "S12b"):
                problems.append(f"{sh['id']} {tag} f{f}: INSIDE camera is inside a surface ({100 * near / n:.0f}% of rays)")
    return problems


def world_bbox(coll):
    pts = [ob.matrix_world @ Vector(c) for ob in coll.all_objects if ob.type == "MESH" and ob.name not in BACKDROPS
           for c in ob.bound_box]
    if not pts:
        return None
    return (Vector(min(p[i] for p in pts) for i in range(3)), Vector(max(p[i] for p in pts) for i in range(3)))


def check_static(scene):
    problems = []
    boxes = {c.name: world_bbox(c) for c in scene.collection.children if c.name.startswith(("SET_", "ASSET_", "CHAR_"))}
    names = [n for n, b in boxes.items() if b]
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            if {a, b} <= {"SET_sky", "ASSET_jet"} or {a, b} <= {"SET_cabin", "CHAR_max"}:
                continue
            if "ASSET_jet" in (a, b) and "SET_city" in (a, b):
                continue
            (a0, a1), (b0, b1) = boxes[a], boxes[b]
            if all(a0[k] < b1[k] and b0[k] < a1[k] for k in range(3)):
                problems.append(f"STATIC sets overlap: {a} and {b} (one can show up in the other's shots)")
    for ob in scene.objects:
        if ob.type == "MESH" and any(m.type == "DISPLACE" for m in ob.modifiers):
            s = ob.scale
            if max(s) > 1.5 * min(s):
                problems.append(f"STATIC {ob.name}: displaced mesh with stretched scale {tuple(round(x, 1) for x in s)} "
                                "(relief will shear; bake the scale first)")
        if ob.type == "LIGHT" and ob.visible_camera and ob.data.type in {"POINT", "SPOT"} and ob.data.shadow_soft_size > 0.2:
            top = top_collection(ob, scene)
            if top in ("SET_ear_in", "SET_cabin"):
                problems.append(f"STATIC {ob.name}: {ob.data.shadow_soft_size:.2f} m light visible to camera in {top} "
                                "(renders as a glowing ball)")
    return problems


def main():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    plan_path = a[a.index("--plan") + 1] if "--plan" in a else ROOT / "shorts" / "pilot_ear_pop" / "plan.json"
    nx, ny = (int(x) for x in (a[a.index("--rays") + 1] if "--rays" in a else "18x32").split("x"))
    scene = bpy.data.scenes.get("FILM") or bpy.context.scene
    plan = json.loads(Path(plan_path).read_text())
    problems = check_static(scene) + check_shots(scene, plan, nx, ny)
    print("[qa] " + ("\n[qa] ".join(problems) if problems else "all shots clean"))
    print(f"[qa] {len(problems)} problem(s)")
    sys.exit(1 if problems else 0)


main()
