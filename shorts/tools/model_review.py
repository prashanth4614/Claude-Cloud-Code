"""Review render for an imported 3D model (Meshy, Sketchfab, ...): next to Max, in the house light rig.

    blender -b assets/characters/max/max_v6.blend -P shorts/tools/model_review.py -- \
        MODEL.glb --height 0.45 --out out/model_review/bench [--samples 64] [--res 720]

Imports the model, scales it to --height metres (its real-world size), stands it on the floor 0.9 m to
Max's left, and renders: a wide shot with Max for scale, a 3/4 view, a side view and a close-up, plus a
contact sheet (<out>_sheet.jpg) and a report (<out>_report.txt: triangles, materials, textures, size).
"""
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "blender"))
import build_max  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:]
path = os.path.abspath(argv[0])
height = float(argv[argv.index("--height") + 1]) if "--height" in argv else 1.0
out = os.path.abspath(argv[argv.index("--out") + 1]) if "--out" in argv else os.path.splitext(path)[0]
samples = int(argv[argv.index("--samples") + 1]) if "--samples" in argv else 64
res = int(argv[argv.index("--res") + 1]) if "--res" in argv else 720
os.makedirs(os.path.dirname(out), exist_ok=True)

before = set(bpy.data.objects)
ext = os.path.splitext(path)[1].lower()
if ext in (".glb", ".gltf"):
    bpy.ops.import_scene.gltf(filepath=path)
elif ext == ".fbx":
    bpy.ops.import_scene.fbx(filepath=path)
elif ext == ".obj":
    bpy.ops.wm.obj_import(filepath=path)
else:
    raise SystemExit(f"unsupported format: {ext}")
new = [o for o in bpy.data.objects if o not in before]
meshes = [o for o in new if o.type == "MESH"]
if not meshes:
    raise SystemExit("no mesh in the file")
roots = [o for o in new if o.parent is None]
bpy.context.view_layer.update()

def bounds():
    pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi

lo, hi = bounds()
raw = hi - lo
scale = height / max(raw.z, 1e-6)
for r in roots:
    r.scale *= scale
bpy.context.view_layer.update()
lo, hi = bounds()
centre = (lo + hi) / 2
shift = Vector((-0.9 - centre.x, -centre.y, -lo.z))       # Max stands at the origin facing -Y
for r in roots:
    r.location += shift
bpy.context.view_layer.update()
lo, hi = bounds()
size = hi - lo
centre = (lo + hi) / 2

# report
tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in meshes)
mats = {m.name for o in meshes for m in o.data.materials if m}
imgs = {(n.image.name, tuple(n.image.size)) for o in meshes for m in o.data.materials if m and m.use_nodes
        for n in m.node_tree.nodes if n.type == "TEX_IMAGE" and n.image}
with open(out + "_report.txt", "w") as f:
    f.write(f"file: {os.path.basename(path)}\n")
    f.write(f"raw size (m): {raw.x:.3f} x {raw.y:.3f} x {raw.z:.3f}; scaled x{scale:.3f} to height {height} m\n")
    f.write(f"final size (m): {size.x:.3f} x {size.y:.3f} x {size.z:.3f}\n")
    f.write(f"objects: {len(meshes)} meshes; triangles: {tris:,}\n")
    f.write(f"materials: {sorted(mats)}\n")
    f.write("textures: " + ", ".join(f"{n} {w}x{h}" for n, (w, h) in sorted(imgs)) + "\n")
    f.write(f"armature: {any(o.type == 'ARMATURE' for o in new)}\n")
print(open(out + "_report.txt").read())

# camera set-ups: wide with Max, 3/4, side, close-up
rig = bpy.data.objects.get("Max")
cam = build_max.setup_render((res, res), samples=samples)
span = max(size.x, size.y, size.z, 0.3)
shots = []
mid = Vector(((centre.x + 0) / 2, centre.y, max(0.9, size.z / 2)))
shots.append(("wide", mid + Vector((0.4, -3.6 - span, 0.25)), mid, 40))
for name, ang, dist in (("three_quarter", -35, 2.4), ("side", -90, 2.4), ("close", -20, 1.1)):   # outer side: Max never blocks
    a = math.radians(ang)
    d = span * dist + 0.4
    tgt = centre if name != "close" else centre + Vector((0, 0, size.z * 0.15))
    shots.append((name, tgt + Vector((d * math.sin(a), -d * math.cos(a), span * 0.35)), tgt, 50))
paths = []
for name, pos, tgt, lens in shots:
    build_max.aim(cam, pos, tgt, lens)
    p = f"{out}_{name}.png"
    build_max.render(p)
    paths.append(p)

try:
    from PIL import Image, ImageDraw
    ims = [Image.open(p).convert("RGB") for p in paths]
    w, h = ims[0].size
    sheet = Image.new("RGB", (w * len(ims), h + 28), (10, 14, 20))
    d = ImageDraw.Draw(sheet)
    for i, (im, (name, *_)) in enumerate(zip(ims, shots)):
        sheet.paste(im, (i * w, 0))
        d.text((i * w + 10, h + 7), name, fill="white")
    sheet.save(out + "_sheet.jpg", quality=88)
except ImportError:
    pass   # Blender's Python may lack PIL: the four PNGs are the review
print("review written:", out)
