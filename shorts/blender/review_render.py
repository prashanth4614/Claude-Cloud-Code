"""Render review frames from a film .blend and tile them into one contact sheet (+ a .txt legend).

    blender -b FILM.blend -P shorts/blender/review_render.py -- \\
        --shots S02:happening,S07:0.5 [--all] [--quality draft|look] --sheet out/review/sheet.jpg

Shot specs: "<shot>:<word>" (that spoken word's frame + 8) or "<shot>:<0..1>" (fraction through
the shot). --all = the middle of every shot. Uses the GPU when there is one (Metal on a Mac,
OptiX/CUDA on RunPod), else the CPU.

Quality:
  draft  bug-hunting: 12% size, 6 samples, simplified (subdivision and hair capped), ~8-12 s/frame on CPU
  look   judging the look: 25% size, 24 samples (CPU) / 50% size, 64 samples (GPU)
Persistent data keeps the scene loaded between frames, so only what moves is re-synced.
"""
import json
import sys
import time
from pathlib import Path

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[2]


def args():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    get = lambda k, d=None: a[a.index(k) + 1] if k in a else d  # noqa: E731
    return {"shots": get("--shots", ""), "all": "--all" in a, "quality": get("--quality", "draft"),
            "sheet": get("--sheet", str(ROOT / "out" / "review" / "sheet.jpg")),
            "plan": get("--plan", str(ROOT / "shorts" / "pilot_ear_pop" / "plan.json"))}


def use_gpu(sc):
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
    except KeyError:
        return False
    for kind in ("OPTIX", "CUDA", "METAL", "HIP", "ONEAPI"):
        try:
            prefs.compute_device_type = kind
        except TypeError:
            continue
        prefs.get_devices()
        gpus = [d for d in prefs.devices if d.type != "CPU"]
        if gpus:
            for d in prefs.devices:
                d.use = d.type != "CPU"
            sc.cycles.device = "GPU"
            print(f"[review] GPU: {kind} ({', '.join(d.name for d in gpus)})")
            return True
    sc.cycles.device = "CPU"
    print("[review] CPU render")
    return False


def setup(sc, quality):
    sc.render.engine = "CYCLES"
    gpu = use_gpu(sc)
    sc.render.use_persistent_data = True
    sc.render.use_sequencer = False
    sc.render.image_settings.file_format = "PNG"
    sc.cycles.use_denoising = True
    sc.cycles.use_adaptive_sampling = True
    if quality == "draft":
        sc.render.resolution_percentage, sc.cycles.samples = 12, 6
        sc.render.use_simplify = True
        sc.render.simplify_subdivision_render = 1
        sc.render.simplify_child_particles_render = 0.15
        sc.cycles.max_bounces = 4
    else:
        sc.render.resolution_percentage, sc.cycles.samples = (50, 64) if gpu else (25, 24)
        sc.render.use_simplify = False


def frames(plan, spec, all_shots):
    shots = {s["id"]: s for s in plan["shots"]}
    items = [f"{s['id']}:0.55" for s in plan["shots"]] if all_shots else [x for x in spec.split(",") if x]
    out = []
    for item in items:
        sid, at = item.split(":")
        sh = shots[sid]
        try:
            f = int(sh["start"] + (sh["end"] - sh["start"]) * float(at))
        except ValueError:
            f = next(b["frame"] for b in sh["beats"] if b.get("word") == at) + 8
        out.append((item, sid, f))
    return out


def sheet(paths, labels, out, cols=6):
    imgs = [bpy.data.images.load(str(p)) for p in paths]
    w, h = imgs[0].size
    cols = min(cols, len(imgs))
    rows = (len(imgs) + cols - 1) // cols
    canvas = np.zeros((rows * h, cols * w, 4), dtype=np.float32)
    canvas[..., 3] = 1
    for k, im in enumerate(imgs):
        px = np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4)
        r, c = k // cols, k % cols
        canvas[(rows - 1 - r) * h:(rows - r) * h, c * w:(c + 1) * w] = px   # Blender images are bottom-up
    out_img = bpy.data.images.new("review_sheet", cols * w, rows * h)
    out_img.pixels = canvas.ravel()
    out_img.filepath_raw = str(out)
    out_img.file_format = "JPEG" if str(out).lower().endswith((".jpg", ".jpeg")) else "PNG"
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    out_img.save()
    (Path(out).with_suffix(".txt")).write_text("\n".join(f"{i + 1:2d} (row {i // cols + 1}, col {i % cols + 1}): {l}"
                                                         for i, l in enumerate(labels)))


def main():
    a = args()
    plan = json.loads(Path(a["plan"]).read_text())
    sc = bpy.data.scenes.get("FILM") or bpy.context.scene
    setup(sc, a["quality"])
    out_dir = Path(a["sheet"]).parent / "frames"
    out_dir.mkdir(parents=True, exist_ok=True)
    paths, labels, t0 = [], [], time.time()
    for item, sid, f in frames(plan, a["shots"], a["all"]):
        sc.camera = bpy.data.objects[f"CAM_{sid}"]
        sc.frame_set(f)
        p = out_dir / f"{item.replace(':', '_')}.png"
        sc.render.filepath = str(p)
        t = time.time()
        bpy.ops.render.render(write_still=True, scene=sc.name)
        print(f"[review] {item} (frame {f}) {time.time() - t:.1f}s")
        paths.append(p)
        labels.append(f"{item} f{f}")
    sheet(paths, labels, a["sheet"])
    print(f"[review] {len(paths)} frames in {time.time() - t0:.0f}s -> {a['sheet']}")


main()
