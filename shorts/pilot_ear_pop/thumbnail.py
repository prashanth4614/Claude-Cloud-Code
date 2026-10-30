#!/usr/bin/env python3
"""The pilot's thumbnail, the Zack D Films Shorts way: one clean frame of the film + its own caption chunk.

  python3 shorts/pilot_ear_pop/thumbnail.py              # render the two frames (if missing) + compose
  python3 shorts/pilot_ear_pop/thumbnail.py --compose    # compose only, from the renders already there

Run it on the Mac: it renders two clean frames of the FILM scene (no captions or labels) at 2x
(2160x3840) with Cycles on the Mac's GPU (Metal), then composes the thumbnail with Pillow.
Two variants for an A/B test: A = Max wincing + "your ears pop" (main), B = the bulging eardrum + "bulges,".
Out (gitignored): out/thumbnail/thumbnail_A.png / _B.png (2160x3840) and .jpg (1080x1920, for upload).
Env: BLENDER (default: the macOS app, else `blender`), THUMB_SAMPLES (256).
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
OUT = ROOT / "out" / "thumbnail"
BLEND = ROOT / "out" / "pilot_ear_pop" / "pilot_ear_pop_previz.blend"
FACE, DRUM = 15, 547          # S00: Max wincing; S06b: the eardrum bulging (diagram)

RENDER = r'''
import sys, bpy
frame, out, samples = int(sys.argv[-3]), sys.argv[-2], int(sys.argv[-1])
film = bpy.data.scenes["FILM"]
prefs = bpy.context.preferences.addons["cycles"].preferences
for kind in ("METAL", "OPTIX", "CUDA"):
    try:
        prefs.compute_device_type = kind
        prefs.get_devices()
    except TypeError:
        continue
    if any(d.type == kind for d in prefs.devices):
        for d in prefs.devices:
            d.use = d.type == kind
        print("[thumb] device", kind)
        break
else:
    kind = None
film.render.engine = "CYCLES"
c = film.cycles
c.device = "GPU" if kind else "CPU"
c.samples, c.use_adaptive_sampling, c.adaptive_threshold = samples, True, 0.005
c.use_denoising, c.denoiser = True, "OPENIMAGEDENOISE"
c.max_bounces, c.diffuse_bounces, c.glossy_bounces = 8, 3, 4
c.transmission_bounces, c.transparent_max_bounces = 8, 8
film.render.use_sequencer = False
film.render.resolution_percentage = 200
film.frame_set(frame)
live = [m for m in film.timeline_markers if m.frame <= frame and m.camera]
if live:
    film.camera = max(live, key=lambda m: m.frame).camera
r = film.render
if hasattr(r.image_settings, "media_type"):
    r.image_settings.media_type = "IMAGE"
r.image_settings.file_format, r.image_settings.color_depth = "PNG", "16"
r.filepath = out
bpy.ops.render.render(write_still=True, scene="FILM")
print("[thumb] wrote", out)
'''


def blender():
    for b in (os.environ.get("BLENDER"), "/Applications/Blender.app/Contents/MacOS/Blender", shutil.which("blender")):
        if b and Path(b).exists():
            return b
    sys.exit("Blender not found: set BLENDER=/path/to/blender")


def render():
    OUT.mkdir(parents=True, exist_ok=True)
    b = blender()
    if not BLEND.exists():
        subprocess.run([b, "-b", "--factory-startup", "-P", str(HERE / "build_previz.py")], check=True)
    script = OUT / "render_frame.py"
    script.write_text(RENDER)
    for f in (FACE, DRUM):
        dest = OUT / f"film_{f:04d}.png"
        if not dest.exists():
            subprocess.run([b, "-b", str(BLEND), "-P", str(script), "--", str(f), str(dest),
                            os.environ.get("THUMB_SAMPLES", "256")], check=True)


def font(size, names=("Inter-ExtraBold.otf",)):
    from PIL import ImageFont
    for d in (ROOT / "fonts", Path.home() / "Library" / "Fonts", Path("/Library/Fonts"),
              Path("/usr/share/fonts/opentype/inter")):
        for n in names:
            if (d / n).exists():
                return ImageFont.truetype(str(d / n), size)
    sys.exit("Inter-ExtraBold.otf not found (fonts/ or ~/Library/Fonts)")


def caption(img, text, hot):
    """The video's own caption, drawn exactly as build_previz styles it: Inter ExtraBold 92 px (at
    1080 wide), centred 20% up from the bottom, yellow for a keyword chunk else white, thin black
    outline and a soft shadow."""
    from PIL import Image, ImageDraw, ImageFilter
    W, H = img.size
    k = W / 1080
    f = font(int(92 * k))
    x, y = W / 2, H * (1 - 0.2)
    col = (202, 178, 96) if hot else (197, 197, 197)   # as they come out of the render (measured)
    sh = Image.new("L", img.size, 0)
    ImageDraw.Draw(sh).text((x + 5 * k, y + 6 * k), text, font=f, fill=150, anchor="mm",
                            stroke_width=int(5 * k), stroke_fill=150)
    img = Image.composite(Image.new("RGB", img.size, (0, 0, 0)), img, sh.filter(ImageFilter.GaussianBlur(5 * k)))
    ImageDraw.Draw(img).text((x, y), text, font=f, fill=col, anchor="mm", stroke_width=int(5 * k),
                             stroke_fill=(0, 0, 0))
    return img


# Zack D Films' Shorts thumbnails are one frame of the video with its own caption chunk, nothing added
# (shorts/reference/zack_style_study.md, "Thumbnails": 33 of 35). A is the hook, B the moment of action.
VARIANTS = {"A": (FACE, "your ears pop", True),     # S00: Max wincing; the hook's caption chunk
            "B": (DRUM, "bulges,", True)}           # S06b: the eardrum bulging, its caption chunk


def compose(frames=None, out_dir=None):
    from PIL import Image
    out_dir = Path(out_dir or OUT)
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, (f, text, hot) in VARIANTS.items():
        src = (frames or {}).get(f, OUT / f"film_{f:04d}.png")
        img = Image.open(src).convert("RGB").resize((2160, 3840), Image.LANCZOS)
        img = caption(img, text, hot)
        png = out_dir / f"thumbnail_{name}.png"
        img.save(png)
        img.resize((1080, 1920), Image.LANCZOS).save(png.with_suffix(".jpg"), quality=92)
        print(f"-> {png} (2160x3840), {png.with_suffix('.jpg')} (1080x1920)")


if __name__ == "__main__":
    if "--compose" not in sys.argv:
        render()
    compose()
