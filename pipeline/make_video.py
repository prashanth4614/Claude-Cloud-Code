#!/usr/bin/env python3
"""Build a long-form "cozy anime-style" relax video from still images + music.

Pipeline (all ffmpeg, no editor needed):
  1. Each image becomes a slow Ken Burns clip (zoom in / zoom out / pan),
     with optional film grain, vignette and procedural rain.
  2. Clips are chained with crossfades into one visual "cycle".
  3. Music tracks are crossfaded together, a rain/ambience bed is mixed
     underneath, and the result is loudness-normalised for YouTube (-14 LUFS).
  4. The visual cycle is looped (stream copy, no re-encode) to the audio length.
  5. A timestamped tracklist is written for the video description.

Example:
  python3 pipeline/make_video.py --images scenes/ --music music/ \
      --rain-audio --rain-visual --out out/rainy_roadtrip.mp4
"""
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp"}
VIDEO_EXT = {".mp4", ".mov", ".webm", ".mkv"}
AUDIO_EXT = {".mp3", ".wav", ".m4a", ".flac", ".ogg", ".aac"}
MOTIONS = ["zoom_in", "pan_right", "zoom_out", "pan_left"]


def run(cmd):
    print("+", " ".join(str(c) for c in cmd[:6]), "...", flush=True)
    subprocess.run([str(c) for c in cmd], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "json", str(path)], check=True, capture_output=True, text=True)
    return float(json.loads(out.stdout)["format"]["duration"])


def files(folder, exts):
    return sorted(p for p in Path(folder).iterdir() if p.suffix.lower() in exts)


def motion_filter(motion, frames, w, h, fps, zoom):
    """zoompan expression for one Ken Burns move. Input is pre-scaled to 2x
    output size so the sub-pixel motion stays smooth instead of jittering."""
    inc = (zoom - 1) / frames
    center = "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
    if motion == "zoom_in":
        z, xy = f"min(1+{inc}*on,{zoom})", center
    elif motion == "zoom_out":
        z, xy = f"max({zoom}-{inc}*on,1)", center
    elif motion == "pan_right":
        z, xy = f"{zoom}", f"x='(iw-iw/zoom)*on/{frames}':y='ih/2-(ih/zoom/2)'"
    else:  # pan_left
        z, xy = f"{zoom}", f"x='(iw-iw/zoom)*(1-on/{frames})':y='ih/2-(ih/zoom/2)'"
    return (f"scale={w*2}:{h*2}:force_original_aspect_ratio=increase,"
            f"crop={w*2}:{h*2},zoompan=z='{z}':{xy}:d={frames}:s={w}x{h}:fps={fps}")


def rain_overlay_filter(w, h, fps, frames, intensity):
    """Procedural rain: sparse random dots smeared vertically into streaks,
    screen-blended over the scene. Cheap, royalty-free, no stock footage."""
    thresh = int(255 - 255 * intensity)
    # Rendered oversized then cropped so the slant leaves no empty corners.
    bw, bh = int(w * 1.2) // 2 * 2, int(h * 1.2) // 2 * 2
    return (f"color=black:s={bw}x{bh}:r={fps},trim=end_frame={frames},format=gray,"
            f"noise=alls=100:allf=t,lutyuv=y='if(gt(val,{thresh}),255,0)',"
            f"avgblur=sizeX=1:sizeY={max(6, h // 90)},"
            f"rotate=0.12,crop={w}:{h},lutyuv=y='val*0.55',format=gbrp")


def render_segment(src, dst, idx, a):
    frames = int(a.seconds_per_image * a.fps)
    vf = []
    is_video = src.suffix.lower() in VIDEO_EXT
    if is_video:
        # Pre-animated clip (Kling/Runway/etc): just fit, slow down if short.
        clip_len = duration(src)
        speed = min(1.0, clip_len / a.seconds_per_image)
        vf.append(f"scale={a.width}:{a.height}:force_original_aspect_ratio=increase,"
                  f"crop={a.width}:{a.height},setpts=PTS/{speed},fps={a.fps},"
                  f"tpad=stop_mode=clone:stop_duration={a.seconds_per_image}")
    else:
        vf.append(motion_filter(MOTIONS[idx % len(MOTIONS)], frames,
                                a.width, a.height, a.fps, a.zoom))
    if a.vignette:
        vf.append("vignette=PI/5")
    if a.grain:
        vf.append(f"noise=alls={a.grain}:allf=t")
    base = ",".join(vf) + f",trim=end_frame={frames},format=gbrp"

    inputs = ["-i", src] if is_video else ["-loop", "1", "-framerate", a.fps, "-i", src]
    if a.rain_visual:
        graph = (f"[0:v]{base}[bg];"
                 f"{rain_overlay_filter(a.width, a.height, a.fps, frames, a.rain_visual)}[rain];"
                 f"[bg][rain]blend=all_mode=screen,format=yuv420p[v]")
    else:
        graph = f"[0:v]{base},format=yuv420p[v]"
    run(["ffmpeg", "-y", *inputs, "-filter_complex", graph, "-map", "[v]",
         "-frames:v", frames, "-an", "-c:v", "libx264", "-preset", a.preset,
         "-crf", a.crf, dst])


def build_cycle(segments, dst, a):
    """Crossfade all segments into one visual loop."""
    if len(segments) == 1:
        run(["ffmpeg", "-y", "-i", segments[0], "-c", "copy", dst])
        return
    inputs, chain, prev = [], [], "0:v"
    for s in segments:
        inputs += ["-i", s]
    step = a.seconds_per_image - a.crossfade
    for i in range(1, len(segments)):
        out = f"v{i}"
        chain.append(f"[{prev}][{i}:v]xfade=transition={a.transition}:"
                     f"duration={a.crossfade}:offset={i * step:.3f}[{out}]")
        prev = out
    run(["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(chain),
         "-map", f"[{prev}]", "-c:v", "libx264", "-preset", a.preset,
         "-crf", a.crf, "-pix_fmt", "yuv420p", "-g", a.fps * 2, dst])


def build_audio(tracks, dst, total, a):
    """Crossfade music tracks, loop to length, mix ambience, normalise."""
    inputs, graph = [], []
    for t in tracks:
        inputs += ["-i", t]
    if len(tracks) == 1:
        graph.append("[0:a]aformat=sample_rates=48000:channel_layouts=stereo[m]")
    else:
        prev = "0:a"
        for i in range(1, len(tracks)):
            graph.append(f"[{prev}][{i}:a]acrossfade=d={a.audio_crossfade}:c1=tri:c2=tri[x{i}]")
            prev = f"x{i}"
        graph.append(f"[{prev}]aformat=sample_rates=48000:channel_layouts=stereo[m]")
    # Loop the music bed to the target length.
    graph.append(f"[m]aloop=loop=-1:size=2e9,atrim=0:{total:.2f}[music]")
    mix_in = "[music]"
    n = len(tracks)
    if a.ambience:
        inputs += ["-stream_loop", "-1", "-i", a.ambience]
        graph.append(f"[{n}:a]aformat=sample_rates=48000:channel_layouts=stereo,"
                     f"atrim=0:{total:.2f},volume={a.ambience_volume}[amb]")
        mix_in += "[amb]"
        n += 1
    if a.rain_audio:
        # Brown noise (low rumble) + band-passed pink noise (drops) = rain bed.
        graph.append(f"anoisesrc=c=brown:r=48000:a=0.5:d={total:.2f},lowpass=f=900[r1];"
                     f"anoisesrc=c=pink:r=48000:a=0.3:d={total:.2f},highpass=f=1500,"
                     f"lowpass=f=9000,tremolo=f=6:d=0.15[r2];"
                     f"[r1][r2]amix=inputs=2:normalize=0,aformat=channel_layouts=stereo,"
                     f"volume={a.rain_volume}[rain]")
        mix_in += "[rain]"
    count = mix_in.count("[")
    graph.append(f"{mix_in}amix=inputs={count}:duration=first:normalize=0,"
                 f"afade=t=in:d=3,afade=t=out:st={max(0, total - 6):.2f}:d=6[out]")
    raw = Path(dst).with_suffix(".wav")
    run(["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(graph),
         "-map", "[out]", "-c:a", "pcm_s24le", "-ar", "48000", raw])
    # Two-pass loudnorm: measure, then apply linearly so the music keeps its
    # dynamics and lands on YouTube's -14 LUFS playback target.
    target = "I=-14:TP=-1.5:LRA=11"
    probe = subprocess.run(["ffmpeg", "-i", str(raw), "-af",
                            f"loudnorm={target}:print_format=json", "-f", "null", "-"],
                           check=True, capture_output=True, text=True).stderr
    m = json.loads(probe[probe.rindex("{"):probe.rindex("}") + 1])
    run(["ffmpeg", "-y", "-i", raw, "-af",
         f"loudnorm={target}:linear=true:measured_I={m['input_i']}:"
         f"measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:"
         f"measured_thresh={m['input_thresh']}:offset={m['target_offset']}",
         "-c:a", "aac", "-b:a", "192k", "-ar", "48000", dst])


def tracklist(tracks, a):
    lines, t = [], 0.0
    for tr in tracks:
        m, s = divmod(int(t), 60)
        h, m = divmod(m, 60)
        stamp = f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"
        lines.append(f"{stamp} {tr.stem.replace('_', ' ')}")
        t += duration(tr) - a.audio_crossfade
    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--images", required=True, help="folder of scene images or short clips")
    p.add_argument("--music", required=True, help="folder of licensed music tracks")
    p.add_argument("--out", required=True)
    p.add_argument("--minutes", type=float,
                   help="target length (default: total music length). 8+ allows mid-rolls")
    p.add_argument("--ambience", help="optional ambience file (rain, fire, cafe) to loop")
    p.add_argument("--ambience-volume", type=float, default=0.35)
    p.add_argument("--rain-audio", action="store_true", help="add procedural rain sound")
    p.add_argument("--rain-volume", type=float, default=0.25)
    p.add_argument("--rain-visual", type=float, default=0.0, metavar="0-0.05",
                   help="procedural rain streak density, e.g. 0.015 (0 = off)")
    p.add_argument("--seconds-per-image", type=float, default=20)
    p.add_argument("--crossfade", type=float, default=2.0)
    p.add_argument("--transition", default="fade", help="xfade transition name")
    p.add_argument("--audio-crossfade", type=float, default=4.0)
    p.add_argument("--zoom", type=float, default=1.12, help="max Ken Burns zoom")
    p.add_argument("--grain", type=int, default=4, help="film grain strength (0 = off)")
    p.add_argument("--vignette", action=argparse.BooleanOptionalAction, default=True)
    p.add_argument("--width", type=int, default=1920)
    p.add_argument("--height", type=int, default=1080)
    p.add_argument("--fps", type=int, default=30)
    p.add_argument("--crf", type=int, default=18)
    p.add_argument("--preset", default="medium")
    a = p.parse_args()

    scenes = files(a.images, IMAGE_EXT | VIDEO_EXT)
    tracks = files(a.music, AUDIO_EXT)
    if not scenes or not tracks:
        sys.exit("need at least one image/clip and one music track")
    music_len = sum(duration(t) for t in tracks) - a.audio_crossfade * (len(tracks) - 1)
    total = a.minutes * 60 if a.minutes else music_len

    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        segs = []
        for i, src in enumerate(scenes):
            seg = tmp / f"seg{i:03d}.mp4"
            render_segment(src, seg, i, a)
            segs.append(seg)
        cycle = tmp / "cycle.mp4"
        build_cycle(segs, cycle, a)
        audio = tmp / "audio.m4a"
        build_audio(tracks, audio, total, a)
        run(["ffmpeg", "-y", "-stream_loop", "-1", "-i", cycle, "-i", audio,
             "-map", "0:v", "-map", "1:a", "-c", "copy", "-t", f"{total:.2f}",
             "-movflags", "+faststart", out])

    desc = out.with_suffix(".tracklist.txt")
    desc.write_text(tracklist(tracks, a) + "\n")
    print(f"\nDone: {out} ({total / 60:.1f} min)\nTracklist for description: {desc}")


if __name__ == "__main__":
    main()
