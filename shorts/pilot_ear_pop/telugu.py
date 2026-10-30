#!/usr/bin/env python3
"""Telugu version of the pilot, on the already rendered picture (no re-render).

  python3 shorts/pilot_ear_pop/telugu.py voice     # Telugu narration, each line fitted to its English slot
  python3 shorts/pilot_ear_pop/telugu.py video     # mix + Telugu captions over the English ones -> MP4

The text is in telugu.yaml (one line per English script line). The owner's cloned voice reads each
line (ElevenLabs v3, cached per line, so re-runs don't re-spend). The picture is locked to the English
timing, so each line is placed at its English line's start and, if longer than the slot up to the next
line, sped up (at most MAX_TEMPO). The line marked land_last_word_on puts its last word on the English
word's time (the POP frame), starting early if it must. Captions: the English ones are burned into the frames, so each frame gets
a caption box over them with the Telugu chunk (Noto Sans Telugu, fonts/; OFL), and the end card too.
The ear-diagram labels and badges stay English.
Outputs (gitignored): out/pilot_ear_pop_work/telugu/, out/final/pilot_ear_pop_telugu.mp4.
"""
import base64
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE.parent))
from engine import SR, decode, elevenlabs_post, ffmpeg_filter  # noqa: E402

CFG = yaml.safe_load((HERE / "telugu.yaml").read_text())
EN = json.loads((HERE / "audio" / "voice_timing.json").read_text())["lines"]
PLAN = json.loads((HERE / "plan.json").read_text())
WORK = ROOT / "out" / "pilot_ear_pop_work" / "telugu"
FRAMES = ROOT / "out" / "final" / "full" / "frames"
MAX_TEMPO = 1.22          # faster than this sounds rushed
END = PLAN["frame_end"] / PLAN["fps"] - 0.2
TAG = re.compile(r"\[[^\]]*\]")


def tts(text):
    """One line in the owner's voice, with ElevenLabs' character timings; cached by text + settings."""
    voice = CFG["voice"].split(":", 1)[1]
    body = {"text": text, "model_id": CFG["model"],
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.85, "style": 0.4, "use_speaker_boost": True}}
    key = hashlib.sha256(json.dumps([voice, body], sort_keys=True).encode()).hexdigest()[:16]
    f = WORK / "tts" / f"{key}.json"
    if not f.exists():
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_bytes(elevenlabs_post(f"/v1/text-to-speech/{voice}/with-timestamps?output_format=mp3_44100_128",
                                      body, timeout=600))
    res = json.loads(f.read_text())
    mp3 = f.with_suffix(".mp3")
    if not mp3.exists():
        mp3.write_bytes(base64.b64decode(res["audio_base64"]))
    al = res["alignment"]
    words, cur = [], None                       # words (tags dropped) with their start/end times
    for ch, a, b in zip(al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"]):
        if ch.isspace():
            cur = None
            continue
        if cur is None:
            cur = [ch, a, b]
            words.append(cur)
        else:
            cur[0] += ch
            cur[2] = b
    words = [(w, a, b) for w, a, b in words if not TAG.fullmatch(w)]
    return decode(mp3), words


def speech_span(a, words):
    """Where the speech is: from the first word to the end of the last word's sound (energy based)."""
    w = int(0.02 * SR)
    env = np.sqrt(np.convolve(a ** 2, np.ones(w) / w, mode="same"))
    loud = np.where(env > env.max() * 0.03)[0]
    s0 = max(0, min(loud[0] / SR, words[0][1]) - 0.04)
    s1 = min(len(a) / SR, loud[-1] / SR + 0.1)
    return s0, s1


def caption_words(caption, words, t0, scale, at):
    """The caption's words with absolute times: matched to the spoken words in order (punctuation and
    '...' differ), else spread over the line by length."""
    cap = caption.split()
    key = lambda w: re.sub(r"[^\w]", "", w)   # noqa: E731
    spoken = [w for w in words if key(w[0])]
    if [key(w) for w in cap] == [key(w[0]) for w in spoken]:
        return [[c, round(at + (s - t0) / scale, 3), round(at + (e - t0) / scale, 3)] for c, (_, s, e) in zip(cap, spoken)]
    s, e = at + (words[0][1] - t0) / scale, at + (words[-1][2] - t0) / scale
    wt = np.array([len(c) + 2 for c in cap], float)
    edges = s + np.r_[0, np.cumsum(wt)] / wt.sum() * (e - s)
    return [[c, round(edges[i], 3), round(edges[i + 1], 3)] for i, c in enumerate(cap)]


def voice():
    n = int((PLAN["frame_end"] / PLAN["fps"]) * SR)
    out = np.zeros(n)
    timing, report, prev_end = [], [], 0.0
    for i, (ln, en) in enumerate(zip(CFG["lines"], EN)):
        a, words = tts(ln["spoken"])
        s0, s1 = speech_span(a, words)
        a = a[int(s0 * SR):int(s1 * SR)].copy()
        dur = len(a) / SR
        slot_end = EN[i + 1]["start"] - 0.12 if i + 1 < len(EN) else END
        start = en["start"] - ln.get("lead", 0)
        if ln.get("land_last_word_on"):           # its last word lands on the English word's time
            target = next(w[1] for w in en["words"] if w[0] == ln["land_last_word_on"])
            start = max(prev_end + 0.25, target - (words[-1][1] - s0))   # may start early, after a breath
        scale = max(1.0, dur / (slot_end - start))
        if scale > 1.0:
            a = ffmpeg_filter(a, f"atempo={min(scale, MAX_TEMPO):.4f}")
        scale = min(scale, MAX_TEMPO)
        f = int(0.015 * SR)
        a[:f] *= np.linspace(0, 1, f)
        a[-f:] *= np.linspace(1, 0, f)
        i0 = int(start * SR)
        seg = a[: max(0, n - i0)]
        out[i0:i0 + len(seg)] += seg
        end = start + len(a) / SR
        prev_end = end
        cw = caption_words(ln["caption"], words, s0, scale, start)
        timing.append({"start": round(start, 3), "end": round(end, 3), "caption": ln["caption"], "words": cw})
        over = end - slot_end
        report.append(f"{i + 1:2d} {dur:5.2f}s in {slot_end - start:4.2f}s slot  x{scale:.2f}"
                      + (f"  OVER by {over:.2f}s: shorten this line" if over > 0.07 else ""))
    WORK.mkdir(parents=True, exist_ok=True)
    with open(WORK / "voice.f32", "wb") as fh:
        fh.write(out.astype(np.float32).tobytes())
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", str(WORK / "voice.f32"),
                    "-c:a", "pcm_s16le", str(WORK / "voice.wav")], check=True)
    (WORK / "voice.f32").unlink()
    (WORK / "timing.json").write_text(json.dumps({"total": round(n / SR, 3), "lines": timing}, ensure_ascii=False, indent=1))
    print("\n".join(report))
    print(f"-> {WORK / 'voice.wav'}, {WORK / 'timing.json'}")


FPS = PLAN["fps"]
W, H = PLAN["resolution"] if "resolution" in PLAN else (1080, 1920)
CAP_CY = H * (1 - 0.2)                 # build_previz CAPTION_Y: captions are centred 20% up from the bottom
EN_FONT = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"   # the English captions' font (92 px)
TE_FONT = ROOT / "fonts" / "NotoSansTelugu-ExtraBold.ttf"
TE_SIZE, TE_CHARS = 78, 22             # Telugu caption size, and ~characters per chunk (one or two lines)


def wrap(draw, text, font, width):
    lines, cur = [], ""
    for w in text.split():
        t = f"{cur} {w}".strip()
        if cur and draw.textlength(t, font=font) > width:
            lines.append(cur)
            cur = w
        else:
            cur = t
    return lines + ([cur] if cur else [])


def chunks(timing):
    """Telugu caption chunks: whole words up to ~TE_CHARS characters, each on screen from its first
    word to the next chunk (or its line's end + 0.25 s)."""
    out = []
    for ln in timing:
        cur = []
        for w in ln["words"]:
            if cur and len(" ".join(x[0] for x in cur + [w])) > TE_CHARS:
                out.append([" ".join(x[0] for x in cur), cur[0][1]])
                cur = []
            cur.append(w)
        out.append([" ".join(x[0] for x in cur), cur[0][1]])
        out[-1].append(ln["end"] + 0.25)
    for i, c in enumerate(out):
        if len(c) == 2:
            c.append(out[i + 1][1])
        c[2] = min(c[2], out[i + 1][1]) if i + 1 < len(out) else c[2]
    return out


def video():
    from PIL import Image, ImageDraw, ImageFont
    timing = json.loads((WORK / "timing.json").read_text())["lines"]
    mix = ROOT / "out" / "final" / "mix_telugu.wav"
    subprocess.run([sys.executable, str(HERE / "mix.py"), str(mix), "--voice", str(WORK / "voice.wav"),
                    "--timing", str(WORK / "timing.json")], check=True)
    en_font, te_font = ImageFont.truetype(EN_FONT, 92), ImageFont.truetype(str(TE_FONT), TE_SIZE)
    probe = ImageDraw.Draw(Image.new("RGB", (W, H)))

    def box_of(text, font, line_h):
        ls = wrap(probe, text, font, 0.9 * W)
        w = max(probe.textlength(x, font=font) for x in ls)
        return ls, w, line_h * len(ls)

    en = [(c["start"], c["end"], box_of(c["text"], en_font, 125)) for c in PLAN["captions"]]
    # the follow card (build_previz overlays(): S13 start+8 to its end, centred 27% up, 64 px)
    s13 = next(s for s in PLAN["shots"] if s["id"] == "S13")
    card = (s13["start"] + 8, s13["end"] + 1, H * (1 - 0.27), box_of("Follow for more weird body facts",
            ImageFont.truetype(EN_FONT, 64), 88), box_of(CFG["follow_card"], ImageFont.truetype(str(TE_FONT), 52), 80))
    card_font = ImageFont.truetype(str(TE_FONT), 52)
    te = [(int(round(a * FPS)) + 1, int(round(b * FPS)), box_of(t, te_font, 120)) for t, a, b in chunks(timing)]
    out = ROOT / "out" / "final" / "pilot_ear_pop_telugu.mp4"
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-i", str(mix), "-map", "0:v", "-map", "1:a",
                            "-c:v", "libx264", "-preset", "slow", "-crf", "14", "-profile:v", "high", "-pix_fmt", "yuv420p",
                            "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
                            "-c:a", "aac", "-b:a", "320k", "-shortest", "-movflags", "+faststart", str(out)],
                           stdin=subprocess.PIPE)
    for f in range(1, PLAN["frame_end"] + 1):
        im = Image.open(FRAMES / f"f_{f:04d}.jpg").convert("RGB")
        e = [b for a, z, b in en if a <= f <= z]
        t = [b for a, z, b in te if a <= f <= z]
        if card[0] <= f <= card[1]:
            _, ew, eh = card[3]
            ls, tw, th = card[4]
            bw, bh = max(ew, tw) + 60, max(eh, th) + 40
            ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(ov).rounded_rectangle([W / 2 - bw / 2, card[2] - bh / 2, W / 2 + bw / 2, card[2] + bh / 2],
                                                 radius=28, fill=(14, 16, 24, 255))
            im = Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB")
            d = ImageDraw.Draw(im)
            y = card[2] - th / 2 + 40
            for x in ls:
                d.text((W / 2, y), x, font=card_font, fill=(255, 255, 255), anchor="mm", stroke_width=3, stroke_fill=(0, 0, 0))
                y += 80
        if e or t:
            # one opaque box over the English caption (its black outline showed through 98%) and the
            # Telugu one; it grows to fit both, and sits over the end card's box
            bw = max([b[1] for b in e + t]) + 70
            bh = max([b[2] for b in e + t]) + 56
            ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            d = ImageDraw.Draw(ov)
            d.rounded_rectangle([W / 2 - bw / 2, CAP_CY - bh / 2, W / 2 + bw / 2, CAP_CY + bh / 2],
                                radius=34, fill=(14, 16, 24, 255))
            im = Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB")
            if t:
                ls, _, th = t[0]
                d = ImageDraw.Draw(im)
                y = CAP_CY - th / 2 + 60
                for x in ls:
                    d.text((W / 2, y), x, font=te_font, fill=(255, 255, 255), anchor="mm",
                           stroke_width=4, stroke_fill=(0, 0, 0))
                    y += 120
        enc.stdin.write(im.tobytes())
    enc.stdin.close()
    enc.wait()
    print(f"-> {out}")


if __name__ == "__main__":
    {"voice": voice, "video": video}[sys.argv[1]]()
