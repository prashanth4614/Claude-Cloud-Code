#!/usr/bin/env python3
"""The pilot's thumbnail: one clean frame of the film + the question "WHY DO YOUR EARS POP?" on top.

  python3 shorts/pilot_ear_pop/thumbnail.py              # render the two frames (if missing) + compose
  python3 shorts/pilot_ear_pop/thumbnail.py --compose    # compose only, from the renders already there

Run it on the Mac: it renders two clean frames of the FILM scene (no captions or labels) at 2x
(2160x3840) with Cycles on the Mac's GPU (Metal), then composes the thumbnail with Pillow.
Two variants for an A/B test: A = Max the moment his ear pops (a stronger, thumbnail-only face) (main),
B = the bulging eardrum. (Zack's Shorts thumbnails carry only a caption chunk; the owner asked for the
question as a headline.)
Out (gitignored): out/thumbnail/thumbnail_A.png / _B.png (2160x3840) and .jpg (1080x1920, for upload).
Env: BLENDER (default: the macOS app, else `blender`), THUMB_SAMPLES (256), THUMB_PERCENT (200),
THUMB_BLEND (the .blend to render; default the previz build).
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
OUT = ROOT / "out" / "thumbnail"
BLEND = Path(os.environ.get("THUMB_BLEND", ROOT / "out" / "pilot_ear_pop" / "pilot_ear_pop_previz.blend"))
FACE, DRUM = 15, 547          # S00: Max wincing; S06b: the eardrum bulging (diagram)

# Thumbnail-only expression (the film keeps its own wince): the moment his ear pops. His left ear (screen
# right) is the one that pops, so that eye is squeezed shut, the other half open; brows pinched up in
# pain, nose wrinkled, a teeth-showing grimace pulled to that side. ARKit units, as max_expressions.py.
EAR_POP = {
    "browDownLeft": 0.95, "browDownRight": 0.75, "browInnerUp": 0.85,
    "eyeBlinkLeft": 0.88, "eyeSquintLeft": 0.7, "cheekSquintLeft": 0.9,
    "eyeBlinkRight": 0.18, "eyeSquintRight": 0.5, "cheekSquintRight": 0.55, "eyeWideRight": 0.12,
    "noseSneerLeft": 0.85, "noseSneerRight": 0.6,
    "jawOpen": 0.16, "mouthStretchLeft": 0.85, "mouthStretchRight": 0.6, "mouthLeft": 0.25,
    "mouthUpperUpLeft": 0.7, "mouthUpperUpRight": 0.45, "mouthLowerDownLeft": 0.55,
    "mouthLowerDownRight": 0.4, "mouthFrownLeft": 0.35, "mouthFrownRight": 0.2,
}

RENDER = r'''
import json, os, sys, bpy
frame, out, samples, pose = int(sys.argv[-4]), sys.argv[-3], int(sys.argv[-2]), json.loads(sys.argv[-1])
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
film.render.resolution_percentage = int(os.environ.get("THUMB_PERCENT", "200"))
film.frame_set(frame)
if pose:                                   # a thumbnail-only face: unhook the keyed face, set the units
    sk = bpy.data.objects["Max.body"].data.shape_keys
    if sk.animation_data:
        sk.animation_data.action = None
    sys.path.insert(0, os.environ["THUMB_SHORTS"])
    from blender.max_expressions import FACE_UNITS   # only the 52 face units: the body's other keys shape Max
    for kb in sk.key_blocks:
        if kb.name in FACE_UNITS:
            kb.value = pose.get(kb.name, 0.0)
    print("[thumb] face pose", len(pose), "units")
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
    import json
    os.environ["THUMB_SHORTS"] = str(HERE.parent)
    for f, pose in ((FACE, EAR_POP), (DRUM, {})):
        dest = OUT / f"film_{f:04d}{'_pop' if pose else ''}.png"     # the posed face renders to its own file
        if not dest.exists():
            subprocess.run([b, "-b", str(BLEND), "-P", str(script), "--", str(f), str(dest),
                            os.environ.get("THUMB_SAMPLES", "256"), json.dumps(pose)], check=True)


def font(size, names=("Inter-Black.otf", "Inter-ExtraBold.otf")):
    from PIL import ImageFont
    for d in (ROOT / "fonts", Path.home() / "Library" / "Fonts", Path("/Library/Fonts"),
              Path("/usr/share/fonts/opentype/inter")):
        for n in names:
            if (d / n).exists():
                return ImageFont.truetype(str(d / n), size)
    sys.exit("Inter-Black.otf / Inter-ExtraBold.otf not found (fonts/ or ~/Library/Fonts)")


def headline(img, lines):
    """The question as a headline across the top (the owner wants it on the thumbnail): heavy caps, a
    thick black outline and drop shadow, over a soft dark gradient so it reads on the light ceiling."""
    from PIL import Image, ImageDraw, ImageFilter
    W, H = img.size
    k = W / 1080
    grad = Image.linear_gradient("L").resize((W, int(0.34 * H))).transpose(Image.FLIP_TOP_BOTTOM)
    shade = Image.new("L", (W, H), 0)
    shade.paste(grad.point(lambda v: int(v * 0.72)), (0, 0))
    img = Image.composite(Image.new("RGB", (W, H), (0, 0, 0)), img, shade)
    y = 0.085 * H
    for text, size, col in lines:
        f = font(int(size * k))
        fit = 0.9 * W / ImageDraw.Draw(img).textlength(text, font=f)   # each line within 90% of the width
        if fit < 1:
            size *= fit
            f = font(int(size * k))
        sh = Image.new("L", (W, H), 0)
        ImageDraw.Draw(sh).text((W / 2 + 8 * k, y + 10 * k), text, font=f, fill=200, anchor="mm",
                                stroke_width=int(size * k * 0.08), stroke_fill=200)
        img = Image.composite(Image.new("RGB", (W, H), (0, 0, 0)), img, sh.filter(ImageFilter.GaussianBlur(8 * k)))
        ImageDraw.Draw(img).text((W / 2, y), text, font=f, fill=col, anchor="mm",
                                 stroke_width=int(size * k * 0.08), stroke_fill=(0, 0, 0))
        y += size * k * 1.08
    return img


HEADLINE = [("WHY DO YOUR", 118, (255, 255, 255)), ("EARS POP?", 205, (255, 214, 10))]
# A = Max at the moment his ear pops (thumbnail-only face, EAR_POP) + the question; B = the bulging
# eardrum + the question (the moment of action), for an A/B test.
VARIANTS = {"A": (FACE, "film_0015_pop.png"), "B": (DRUM, "film_0547.png")}


def compose(frames=None, out_dir=None):
    from PIL import Image
    out_dir = Path(out_dir or OUT)
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, (f, file) in VARIANTS.items():
        src = (frames or {}).get(f, OUT / file)
        img = Image.open(src).convert("RGB").resize((2160, 3840), Image.LANCZOS)
        img = headline(img, HEADLINE)
        png = out_dir / f"thumbnail_{name}.png"
        img.save(png)
        img.resize((1080, 1920), Image.LANCZOS).save(png.with_suffix(".jpg"), quality=92)
        print(f"-> {png} (2160x3840), {png.with_suffix('.jpg')} (1080x1920)")


if __name__ == "__main__":
    if "--compose" not in sys.argv:
        render()
    compose()
