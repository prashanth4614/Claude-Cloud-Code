"""Final render of the pilot (run inside Blender 5.2, on a RunPod GPU):

  blender -b film_packed.blend -P shorts/pilot_ear_pop/render_final.py -- OUT_DIR [RANGES]

Renders the EDIT scene (the cut, with captions and fades; each shot strip draws FILM through its
camera) at full 1080x1920 with Cycles on the GPU, to JPEG frames OUT_DIR/f_0001.jpg ...
RANGES like "1-1421" or "100-107,915-922" (default: the whole film).

Resumable and shareable: existing files are skipped and a placeholder is written before each frame,
so several Blender processes (one per GPU) can work through the same ranges without repeating
frames, and a restarted pod skips what is already done.

Env: FINAL_SAMPLES (max samples, default 64), FINAL_MIN_SAMPLES (16), FINAL_NOISE (adaptive
threshold, 0.01), FINAL_DENOISER (OPENIMAGEDENOISE | OPTIX), FINAL_PERCENT (100).
"""
import os
import sys
import time

import bpy

args = sys.argv[sys.argv.index("--") + 1:]
out_dir = args[0].rstrip("/")
ranges = [tuple(int(x) for x in r.split("-")) for r in (args[1] if len(args) > 1 else "").split(",") if r]
film, ed = bpy.data.scenes["FILM"], bpy.data.scenes["EDIT"]


def gpu():
    """OptiX, else CUDA. Prints what it got, so the log shows the real device."""
    prefs = bpy.context.preferences.addons["cycles"].preferences
    for kind in ("OPTIX", "CUDA"):
        try:
            prefs.compute_device_type = kind
            prefs.get_devices()
        except TypeError:
            continue
        devs = [d for d in prefs.devices if d.type == kind]
        if devs:
            for d in prefs.devices:
                d.use = d.type == kind
            print(f"[final] device {kind}: {', '.join(d.name for d in devs)}", flush=True)
            return kind
    if not os.environ.get("FINAL_ALLOW_CPU"):     # a GPU pod that can't use its GPU: fail now, don't bill for CPU
        print("[final] ERROR: no OptiX/CUDA device (driver too old for this Blender?)", flush=True)
        sys.exit(3)
    print("[final] WARNING: no GPU device, rendering on CPU", flush=True)
    return None


kind = gpu()
c = film.cycles
film.render.engine = "CYCLES"
c.device = "GPU" if kind else "CPU"
c.use_adaptive_sampling = True
c.adaptive_threshold = float(os.environ.get("FINAL_NOISE", "0.01"))
c.adaptive_min_samples = int(os.environ.get("FINAL_MIN_SAMPLES", "16"))
c.samples = int(os.environ.get("FINAL_SAMPLES", "64"))
c.use_denoising = True
try:
    c.denoiser = os.environ.get("FINAL_DENOISER", "OPENIMAGEDENOISE")
except TypeError:                              # OptiX denoising needs an OptiX device
    print(f"[final] WARNING: denoiser {os.environ.get('FINAL_DENOISER')} unavailable, using OIDN", flush=True)
    c.denoiser = "OPENIMAGEDENOISE"
if hasattr(c, "denoising_use_gpu"):
    c.denoising_use_gpu = True
c.max_bounces, c.diffuse_bounces, c.glossy_bounces = 8, 3, 4
c.transmission_bounces, c.transparent_max_bounces = 8, 8
c.caustics_reflective = c.caustics_refractive = False
film.render.use_persistent_data = True
film.render.use_sequencer = False          # FILM's own sound strips must not replace its picture
for sc in (film, ed):
    sc.render.resolution_percentage = int(os.environ.get("FINAL_PERCENT", "100"))
r = ed.render
if hasattr(r.image_settings, "media_type"):   # Blender 5.x: pick the media type first
    r.image_settings.media_type = "IMAGE"
r.image_settings.file_format = "JPEG"
r.image_settings.quality = 95
r.use_overwrite, r.use_placeholder = False, True
r.filepath = f"{out_dir}/f_####"

if os.environ.get("FINAL_SETUP_ONLY"):        # check the settings without rendering
    print(f"[final] setup ok: {film.render.engine} {c.device} samples {c.adaptive_min_samples}-{c.samples} "
          f"noise {c.adaptive_threshold} denoiser {c.denoiser} {ed.render.resolution_x}x{ed.render.resolution_y}"
          f"@{ed.render.resolution_percentage}% -> {r.filepath} ({r.image_settings.file_format})", flush=True)
    sys.exit(0)
t = [time.time()]


def done(scene, *_):
    now = time.time()
    print(f"[final] frame {scene.frame_current} {now - t[0]:.1f}s", flush=True)
    t[0] = now


bpy.app.handlers.render_post.append(done)

# (the black-frame check runs outside Blender, in final_pod.sh: loading images inside a render
# handler crashes Blender during an animation render)

if os.environ.get("FINAL_DIAG"):              # one frame of FILM straight through its camera, to compare with EDIT
    n = int(os.environ["FINAL_DIAG"])
    film.frame_set(n)
    live = [m for m in film.timeline_markers if m.frame <= n and m.camera]
    cam = max(live, key=lambda m: m.frame).camera if live else None
    if cam:
        film.camera = cam
    film.render.filepath = f"{out_dir}/diag_film_{n:04d}"
    if hasattr(film.render.image_settings, "media_type"):
        film.render.image_settings.media_type = "IMAGE"
    film.render.image_settings.file_format = "JPEG"
    t0 = time.time()
    bpy.ops.render.render(write_still=True, scene="FILM")
    img = bpy.data.images.load(bpy.path.abspath(film.render.filepath + ".jpg"))
    px = img.pixels[:]
    print(f"[final] DIAG film frame {n} via {cam and cam.name}: {time.time() - t0:.1f}s, mean level "
          f"{sum(px[i] for i in range(0, len(px), 4 * 97)) / len(range(0, len(px), 4 * 97)):.3f}", flush=True)
for a, b in ranges or [(ed.frame_start, ed.frame_end)]:
    ed.frame_start, ed.frame_end = a, b
    t[0] = time.time()
    bpy.ops.render.render(animation=True, scene="EDIT")
print("[final] worker finished", flush=True)
