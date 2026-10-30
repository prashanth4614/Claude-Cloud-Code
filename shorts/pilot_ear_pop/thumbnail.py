#!/usr/bin/env python3
"""The pilot's thumbnail: Max wincing + a magnifier into his ear showing the bulging eardrum + a headline.

  python3 shorts/pilot_ear_pop/thumbnail.py              # render the two frames (if missing) + compose
  python3 shorts/pilot_ear_pop/thumbnail.py --compose    # compose only, from the renders already there

Run it on the Mac: it renders two clean frames of the FILM scene (no captions or labels) at 2x
(2160x3840) with Cycles on the Mac's GPU (Metal), then composes the thumbnail with Pillow.
Out (gitignored): out/thumbnail/thumbnail.png (2160x3840) and thumbnail.jpg (1080x1920, < 2 MB, upload).
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
HEADLINE = ("WHY EARS", "POP?!")

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


def font(size, names=("Inter-Black.otf", "Inter-ExtraBold.otf")):
    from PIL import ImageFont
    for d in (ROOT / "fonts", Path.home() / "Library" / "Fonts", Path("/Library/Fonts"),
              Path("/usr/share/fonts/opentype/inter")):
        for n in names:
            if (d / n).exists():
                return ImageFont.truetype(str(d / n), size)
    sys.exit("Inter font not found (fonts/Inter-Black.otf or ~/Library/Fonts)")


def compose(face_path=None, drum_path=None, out=None):
    from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
    face = Image.open(face_path or OUT / f"film_{FACE:04d}.png").convert("RGB")
    drum = Image.open(drum_path or OUT / f"film_{DRUM:04d}.png").convert("RGB")
    W, H = 2160, 3840
    face = face.resize((W, H), Image.LANCZOS)
    drum = drum.resize((W, H), Image.LANCZOS)
    # base: a touch more contrast and colour, and a soft vignette, so it reads small in the feed
    base = ImageEnhance.Contrast(ImageEnhance.Color(face).enhance(1.15)).enhance(1.08)
    vig = Image.new("L", (W, H), 0)
    ImageDraw.Draw(vig).ellipse([-0.25 * W, -0.1 * H, 1.25 * W, 1.1 * H], fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(W * 0.12))
    base = Image.composite(base, Image.new("RGB", (W, H), (8, 10, 18)), vig)
    # top band darkened behind the headline
    grad = Image.new("L", (1, H))
    for y in range(H):
        grad.putpixel((0, y), int(200 * max(0.0, 1 - y / (0.30 * H)) ** 1.6))
    base = Image.composite(Image.new("RGB", (W, H), (0, 0, 0)), base, grad.resize((W, H)))
    # the magnifier: the bulging eardrum, cropped round its dome, in a ring below his ear
    ear = (0.82 * W, 0.60 * H)
    cx, cy, r = 0.70 * W, 0.795 * H, 0.235 * W
    s = int(0.95 * W)                                 # crop size in the drum frame: the whole dome
    dx, dy = int(0.45 * W), int(0.44 * H)
    crop = drum.crop((dx - s // 2, dy - s // 2, dx + s // 2, dy + s // 2)).resize((int(2 * r), int(2 * r)), Image.LANCZOS)
    crop = ImageEnhance.Color(crop).enhance(1.2)
    mask = Image.new("L", crop.size, 0)
    ImageDraw.Draw(mask).ellipse([0, 0, crop.size[0] - 1, crop.size[1] - 1], fill=255)
    d = ImageDraw.Draw(base)
    # callout: two lines from the ear to the ring's sides, then the ring over them
    import math
    ang = math.atan2(cy - ear[1], cx - ear[0])
    for k in (-1, 1):
        a = ang + math.pi / 2 * k
        d.line([ear, (cx + r * math.cos(a), cy + r * math.sin(a))], fill=(255, 255, 255), width=10)
    d.ellipse([ear[0] - 40, ear[1] - 40, ear[0] + 40, ear[1] + 40], outline=(255, 214, 10), width=14)
    shadow = Image.new("L", (W, H), 0)
    ImageDraw.Draw(shadow).ellipse([cx - r + 20, cy - r + 30, cx + r + 20, cy + r + 30], fill=170)
    base = Image.composite(Image.new("RGB", (W, H), (0, 0, 0)), base, shadow.filter(ImageFilter.GaussianBlur(40)))
    base.paste(crop, (int(cx - r), int(cy - r)), mask)
    d = ImageDraw.Draw(base)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(255, 255, 255), width=22)
    # a red arrow on the dome: "this is what's pushing out"
    ax, ay = cx - 0.075 * W, cy
    d.line([(ax + 0.13 * W, ay), (ax - 0.02 * W, ay)], fill=(235, 40, 40), width=34)
    d.polygon([(ax - 0.07 * W, ay), (ax - 0.01 * W, ay - 0.035 * W), (ax - 0.01 * W, ay + 0.035 * W)], fill=(235, 40, 40))
    # headline
    for text, size, y, col in ((HEADLINE[0], 250, 0.085 * H, (255, 255, 255)), (HEADLINE[1], 470, 0.185 * H, (255, 214, 10))):
        f = font(size)
        d.text((W / 2 + 12, y + 16), text, font=f, fill=(0, 0, 0), anchor="mm")          # drop shadow
        d.text((W / 2, y), text, font=f, fill=col, anchor="mm", stroke_width=int(size * 0.07), stroke_fill=(0, 0, 0))
    out = Path(out or OUT / "thumbnail.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    base.save(out)
    base.resize((1080, 1920), Image.LANCZOS).save(out.with_suffix(".jpg"), quality=92)
    print(f"-> {out} (2160x3840), {out.with_suffix('.jpg')} (1080x1920)")


if __name__ == "__main__":
    if "--compose" not in sys.argv:
        render()
    compose()
