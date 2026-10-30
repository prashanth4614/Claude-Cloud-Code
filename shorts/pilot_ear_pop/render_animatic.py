"""Render the previz animatic to MP4 (run inside Blender), with captions, voice and SFX in sync:

  blender -b out/pilot_ear_pop/pilot_ear_pop_previz.blend -P shorts/pilot_ear_pop/render_animatic.py -- OUT.mp4 [PERCENT] [FRAMES]

Renders the EDIT scene, whose shot strips draw FILM through each shot's camera, at low resolution
(EEVEE by default, which needs a GPU; ANIMATIC_ENGINE=WORKBENCH for a fast flat preview,
ANIMATIC_ENGINE=CYCLES for CPU). The sequencer mixes the audio
into the same file, so sync is exact. On RunPod: cloud/render_runpod.py ... -- blender -b ... -P this.
"""
import os
import sys

import bpy

args = sys.argv[sys.argv.index("--") + 1:]
out, pct = args[0], int(args[1]) if len(args) > 1 else 20
film, ed = bpy.data.scenes["FILM"], bpy.data.scenes["EDIT"]
# EEVEE: the real look, ~85 min for the whole film on the M4. WORKBENCH: a flat preview in minutes.
# Cycles on CPU works anywhere but is slow.
engine = os.environ.get("ANIMATIC_ENGINE", "EEVEE")
if engine == "WORKBENCH":
    # Preview animatic for story/timing/transition reviews: flat studio shading, a few minutes for the
    # whole film. Hair keeps 8 children per guide (it's the slowest thing to evaluate every frame).
    film.render.engine = "BLENDER_WORKBENCH"
    sh = film.display.shading
    sh.light, sh.color_type, sh.show_shadows, sh.show_cavity = "STUDIO", "TEXTURE", True, True
    film.display.render_aa = "FXAA"
    for mat in bpy.data.materials:   # Workbench shows a material's viewport colour, not its nodes
        bsdf = mat.node_tree and next((n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if bsdf and not bsdf.inputs["Base Color"].is_linked:
            mat.diffuse_color = bsdf.inputs["Base Color"].default_value
    for ps in bpy.data.particles:
        if ps.type == "HAIR" and ps.child_type != "NONE":
            ps.rendered_child_count = min(ps.rendered_child_count, 8)
elif engine == "CYCLES":
    film.render.engine = "CYCLES"
    film.cycles.device, film.cycles.samples, film.cycles.use_denoising = "CPU", 6, True
else:
    for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
        try:
            film.render.engine = eng
            break
        except TypeError:
            continue
    film.eevee.taa_render_samples = int(os.environ.get("ANIMATIC_SAMPLES", "8"))   # 4 = ~2x faster, softer edges
film.render.use_sequencer = False  # FILM's own audio strips must not replace its picture
ed.render.resolution_percentage = pct
if len(args) > 2:
    ed.frame_end = ed.frame_start + int(args[2]) - 1
r = ed.render
if hasattr(r.image_settings, "media_type"):   # Blender 5.x: pick the media type first
    r.image_settings.media_type = "VIDEO"
r.image_settings.file_format = "FFMPEG"
r.ffmpeg.format, r.ffmpeg.codec, r.ffmpeg.constant_rate_factor = "MPEG4", "H264", "MEDIUM"
r.ffmpeg.audio_codec, r.ffmpeg.audio_bitrate, r.ffmpeg.audio_channels = "AAC", 192, "STEREO"
r.filepath = out
bpy.ops.render.render(animation=True, scene="EDIT")
print(f"[animatic] {out}")
