"""Tiny engine for narrated, captioned, animated YouTube Shorts.

A short is a list of narration lines. Each line has a scene function that
draws one frame with skia: scene(canvas, t, dur, ctx), where t is seconds
into the line and dur is the line's on-screen length. The engine:

  1. synthesises each line with Piper TTS (offline neural voice),
  2. times every scene to its line and every caption word to the speech,
  3. renders frames and pipes them straight into ffmpeg,
  4. builds the soundtrack: voice + procedural music bed (ducked under the
     voice) + procedural sound effects, mastered to -14 LUFS.

Everything is generated locally, so there are no stock assets that could
trigger a Content ID claim.
"""
import json
import math
import os
import subprocess
import sys
import wave
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import skia

W, H, FPS, SR = 1080, 1920, 30, 48000
# Inter (OFL). Linux: fonts-inter package. Mac: drop the .otf files in <repo>/fonts.
FONT_DIR = next(p for p in (Path(os.environ.get("SHORTS_FONT_DIR", "/nonexistent")),
                            Path(__file__).resolve().parent.parent / "fonts",
                            Path("/usr/share/fonts/opentype/inter")) if (p / "Inter-Black.otf").exists())
_typefaces = {}


def font(size, weight="ExtraBold"):
    if weight not in _typefaces:
        _typefaces[weight] = skia.Typeface.MakeFromFile(str(FONT_DIR / f"Inter-{weight}.otf"))
    return skia.Font(_typefaces[weight], size)


# ---------------------------------------------------------------- easing ---
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease(x):  # smooth in-out
    x = clamp(x)
    return x * x * (3 - 2 * x)


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def back_out(x, s=1.9):  # overshoot then settle: the "pop-in" feel
    x = clamp(x) - 1
    return x * x * ((s + 1) * x + s) + 1


def elastic_out(x):
    x = clamp(x)
    if x in (0, 1):
        return x
    return 2 ** (-10 * x) * math.sin((x * 10 - 0.75) * (2 * math.pi) / 3) + 1


def lerp(a, b, x):
    return a + (b - a) * x


def color(hex_, alpha=255):
    hex_ = hex_.lstrip("#")
    return skia.Color(int(hex_[0:2], 16), int(hex_[2:4], 16), int(hex_[4:6], 16), int(alpha))


def paint(c="#ffffff", alpha=255, stroke=0, blur=0, shader=None, cap=None):
    p = skia.Paint(AntiAlias=True, Color=color(c, alpha))
    if stroke:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(stroke)
        p.setStrokeCap(cap or skia.Paint.kRound_Cap)
        p.setStrokeJoin(skia.Paint.kRound_Join)
    if blur:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    if shader is not None:
        p.setShader(shader)
    return p


def linear(x0, y0, x1, y1, colors):
    return skia.GradientShader.MakeLinear(
        [skia.Point(x0, y0), skia.Point(x1, y1)], [color(*c) if isinstance(c, tuple) else color(c) for c in colors])


def radial(x, y, r, colors):
    return skia.GradientShader.MakeRadial(
        skia.Point(x, y), r, [color(*c) if isinstance(c, tuple) else color(c) for c in colors])


def text(canvas, s, x, y, size, fill="#ffffff", stroke="#000000", stroke_w=0,
         weight="ExtraBold", align="center", alpha=255, scale=1.0):
    f = font(size, weight)
    w = f.measureText(s)
    canvas.save()
    canvas.translate(x, y)
    canvas.scale(scale, scale)
    ox = {"center": -w / 2, "left": 0, "right": -w}[align]
    if stroke_w:
        canvas.drawString(s, ox, 0, f, paint(stroke, alpha, stroke=stroke_w))
    canvas.drawString(s, ox, 0, f, paint(fill, alpha))
    canvas.restore()
    return w


def pill(canvas, s, x, y, size=44, fill="#ffffff", fg="#111111", alpha=255, scale=1.0, pad=26):
    """Rounded label centred on (x, y)."""
    f = font(size)
    w = f.measureText(s)
    canvas.save()
    canvas.translate(x, y)
    canvas.scale(scale, scale)
    r = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-w / 2 - pad, -size * 0.85, w + pad * 2, size * 1.6),
                              size * 0.8, size * 0.8)
    canvas.drawRRect(r.makeOffset(0, 8), paint("#000000", alpha * 0.35, blur=10))
    canvas.drawRRect(r, paint(fill, alpha))
    canvas.drawString(s, -w / 2, size * 0.33, f, paint(fg, alpha))
    canvas.restore()


def rng(seed):
    """Deterministic per-particle randomness, so renders are reproducible."""
    return np.random.default_rng(seed)


# ----------------------------------------------------------------- voice ---
def tts(line_text, out_wav, model, length_scale=0.9):
    """Synthesise one line with Piper. Returns trimmed audio."""
    subprocess.run([sys.executable, "-m", "piper", "-m", str(model), "-f", str(out_wav),
                    "--length-scale", str(length_scale), "--sentence-silence", "0"],
                   input=line_text.encode(), check=True, capture_output=True)
    return trim(decode(out_wav))[0]


def decode(path):
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "f32le",
                          "-ac", "1", "-ar", str(SR), "-"], check=True, capture_output=True).stdout
    return np.frombuffer(pcm, dtype=np.float32).copy()


def trim(audio, spans=None):
    """Trim leading/trailing silence so scenes and captions sit tight on speech."""
    loud = np.flatnonzero(np.abs(audio) > 0.02)
    if len(loud):
        lead = max(0, loud[0] - int(0.03 * SR))
        audio = audio[lead: loud[-1] + int(0.08 * SR)]
        if spans:
            # Provider end times can run into trailing silence; clamp to the
            # trimmed audio so a line's last word doesn't overlap the next line.
            d = len(audio) / SR
            spans = [(w, min(d, max(0.0, s - lead / SR)), min(d, max(0.0, e - lead / SR)))
                     for w, s, e in spans]
    return audio, spans


def elevenlabs_script(texts, voice_id, workdir):
    """Whole script in ONE ElevenLabs take, split back into lines.

    One take keeps pitch, energy and pacing consistent (per-line requests
    drift, e.g. a much higher-pitched first line). The character timestamps
    give exact word spans; lines are cut at the quietest point between them.
    Returns [(audio, word_spans)] per line. The response is cached by text +
    voice + settings, so re-renders never spend credits twice. Tunables via
    env: ELEVENLABS_MODEL (default eleven_multilingual_v2), ELEVENLABS_SPEED."""
    import base64
    import hashlib
    import os
    import urllib.request

    text = " ".join(texts)
    model = os.environ.get("ELEVENLABS_MODEL", "eleven_multilingual_v2")
    settings = {"stability": 0.55, "similarity_boost": 0.85, "style": 0.1, "use_speaker_boost": True,
                "speed": float(os.environ.get("ELEVENLABS_SPEED", "1.05"))}
    body = {"text": text, "model_id": model, "voice_settings": settings}
    key = hashlib.sha256(json.dumps([voice_id, body], sort_keys=True).encode()).hexdigest()[:16]
    cache = Path(workdir) / "tts_cache" / f"script_{key}.json"
    if cache.exists():
        res = json.loads(cache.read_text())
    else:
        api_key = os.environ.get("ELEVENLABS_API_KEY")
        if not api_key:
            raise SystemExit("ELEVENLABS_API_KEY is not set (add it as an environment secret)")
        req = urllib.request.Request(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/with-timestamps?output_format=mp3_44100_128",
            data=json.dumps(body).encode(), method="POST",
            headers={"xi-api-key": api_key, "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=300) as r:
            res = json.loads(r.read())
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(res))
    take = Path(workdir) / "take.mp3"
    take.write_bytes(base64.b64decode(res["audio_base64"]))
    audio = decode(take)
    al = res["alignment"]
    chars, starts, ends = al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"]
    if "".join(chars) != text:
        raise RuntimeError("ElevenLabs alignment does not match the script text")
    # word spans over the whole take, grouped per line
    words, cur, s0 = [], "", None
    for ch, s, e in zip(chars + [" "], starts + [0], ends + [0]):
        if ch.isspace():
            if cur:
                words.append((cur, s0, last))
            cur, s0 = "", None
            continue
        if s0 is None:
            s0 = s
        cur, last = cur + ch, e
    per_line, k = [], 0
    for t in texts:
        n = len(t.split())
        per_line.append(words[k:k + n])
        k += n
    assert k == len(words) and all([w for w, _, _ in pl] == t.split() for pl, t in zip(per_line, texts))
    # cut at the quietest point of the gap between a line's last word and the next line
    win = int(0.04 * SR)
    energy = np.convolve(np.abs(audio), np.ones(win) / win, mode="same")
    cuts = [0]
    for a, b in zip(per_line, per_line[1:]):
        lo, hi = int((a[-1][2] - 0.03) * SR), int(b[0][1] * SR)
        cuts.append(lo + int(np.argmin(energy[lo:hi])) if hi > lo else hi)
    cuts.append(len(audio))
    out = []
    for i, pl in enumerate(per_line):
        c0 = cuts[i] / SR
        spans = [(w, s - c0, e - c0) for w, s, e in pl]
        out.append(trim(audio[cuts[i]:cuts[i + 1]], spans))
    return out


def word_times(words, start, dur):
    """Spread words over the spoken duration, weighted by length.
    Piper gives no word timestamps; length-weighting is close enough for
    2-3 word caption chunks."""
    weights = np.array([len(w.strip(",.!?;:")) + 2.5 for w in words], dtype=float)
    edges = np.concatenate([[0], np.cumsum(weights)]) / weights.sum() * dur + start
    return [(w, edges[i], edges[i + 1]) for i, w in enumerate(words)]


# ----------------------------------------------------------------- audio ---
def _env(n, attack, decay):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(attack, 1e-4)) * np.exp(-t / decay)


def sfx(name, rand=None):
    """Procedural sound effects (royalty-free by construction)."""
    r = rand or rng(hash(name) % 2**32)
    if name == "whoosh":
        n = int(0.55 * SR)
        noise = r.standard_normal(n)
        t = np.linspace(0, 1, n)
        # sweep a one-pole lowpass from dark to bright and back
        cutoff = 0.02 + 0.25 * np.sin(np.pi * t) ** 2
        y, out = 0.0, np.empty(n)
        for i in range(n):
            y += cutoff[i] * (noise[i] - y)
            out[i] = y
        return out * np.sin(np.pi * t) ** 1.5 * 1.6
    if name == "pop":
        n = int(0.25 * SR)
        t = np.arange(n) / SR
        freq = 900 * np.exp(-t * 18) + 140
        body = np.sin(2 * np.pi * np.cumsum(freq) / SR) * _env(n, 0.001, 0.05)
        click = r.standard_normal(n) * _env(n, 0.0005, 0.006)
        return (body + 0.6 * click) * 0.9
    if name == "ding":
        n = int(0.9 * SR)
        t = np.arange(n) / SR
        tone = sum(a * np.sin(2 * np.pi * f * t) for f, a in ((1568, 1), (3136, 0.35), (4704, 0.12)))
        return tone * _env(n, 0.002, 0.25) * 0.28
    if name == "tick":
        n = int(0.04 * SR)
        return r.standard_normal(n) * _env(n, 0.0003, 0.004) * 0.35
    if name == "thud":
        n = int(0.4 * SR)
        t = np.arange(n) / SR
        return np.sin(2 * np.pi * (60 + 80 * np.exp(-t * 30)) * t) * _env(n, 0.002, 0.12) * 0.9
    if name == "rumble":  # 4 s of jet-cabin drone
        n = int(4 * SR)
        noise = r.standard_normal(n)
        y, out = 0.0, np.empty(n)
        for i in range(n):
            y += 0.015 * (noise[i] - y)
            out[i] = y
        fade = np.minimum(1, np.minimum(np.arange(n), n - np.arange(n)) / (0.6 * SR))
        return out / (np.abs(out).max() + 1e-9) * fade * 0.35
    raise ValueError(name)


def music_bed(total, bpm=100, seed=7):
    """Curious, light pluck arpeggio + pad in A minor. Quiet by design:
    it sits under the narration, never competes with it."""
    r = rng(seed)
    n = int(total * SR)
    out = np.zeros(n)
    beat = 60 / bpm
    chords = [(57, 60, 64, 69), (53, 57, 60, 65), (48, 52, 55, 60), (55, 59, 62, 67)]  # Am F C G
    hz = lambda m: 440 * 2 ** ((m - 69) / 12)
    step, i = beat / 2, 0
    while i * step < total:
        chord = chords[int(i * step / (beat * 4)) % 4]
        note = chord[[0, 2, 1, 3, 2, 1, 3, 2][i % 8]] + 12
        s0, ln = int(i * step * SR), int(0.6 * SR)
        t = np.arange(min(ln, n - s0)) / SR
        f = hz(note)
        tone = (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t)) * np.exp(-t * 6)
        out[s0:s0 + len(t)] += tone * (0.10 + 0.03 * r.random())
        i += 1
    bar = beat * 4
    for b in range(int(total / bar) + 1):
        chord = chords[b % 4]
        s0 = int(b * bar * SR)
        t = np.arange(min(int(bar * SR), n - s0)) / SR
        if not len(t):
            break
        env = np.minimum(1, t / 0.4) * np.minimum(1, (bar - t) / 0.4)
        pad = sum(np.sin(2 * np.pi * hz(m) * t) for m in chord) / 4
        sub = np.sin(2 * np.pi * hz(chord[0] - 12) * t) * 0.6
        out[s0:s0 + len(t)] += (pad * 0.07 + sub * 0.08) * env
    return out


# ---------------------------------------------------------------- plates ---
class Plate:
    """A pre-rendered PNG sequence (e.g. a Blender render) played back as a
    scene background. Frame i is the image at t = i / FPS into the line."""

    def __init__(self, frames_dir):
        self.dir, self.files = Path(frames_dir), None  # listed lazily: plates may render after layout
        self._idx, self._img = None, None

    def image(self, t):
        if self.files is None:
            self.files = sorted(self.dir.glob("*.png"))
            if not self.files:
                raise FileNotFoundError(f"no PNG frames in {self.dir}")
        i = int(clamp(math.floor(t * FPS + 1e-6), 0, len(self.files) - 1))
        if i != self._idx:
            self._idx, self._img = i, skia.Image.open(str(self.files[i]))
        return self._img

    def draw(self, canvas, t):
        canvas.drawImageRect(self.image(t), skia.Rect.MakeWH(W, H),
                             skia.SamplingOptions(skia.FilterMode.kLinear))


def plate_scene(frames_dir, overlay=None):
    """Scene that plays a PNG sequence, then draws overlay(canvas, t, dur, ctx) on top."""
    plate = Plate(frames_dir)

    def scene(canvas, t, dur, ctx):
        plate.draw(canvas, t)
        if overlay:
            overlay(canvas, t, dur, ctx)
    return scene


# ----------------------------------------------------------------- short ---
@dataclass
class Line:
    text: str
    scene: callable
    sfx: list = field(default_factory=list)  # (seconds | "word", name)
    pause: float = 0.18                     # silence after the line


class Short:
    def __init__(self, lines, voice_model, workdir, length_scale=0.9):
        self.lines, self.model, self.ls = lines, voice_model, length_scale
        self.work = Path(workdir)
        self.work.mkdir(parents=True, exist_ok=True)

    def _layout(self):
        if hasattr(self, "timeline"):  # already laid out (TTS is the slow part)
            return
        t, self.timeline, self.words, self.events = 0.25, [], [], []
        self.voice, self.line_words = [], []
        if str(self.model).startswith("elevenlabs:"):  # one take, exact word timings
            takes = elevenlabs_script([ln.text for ln in self.lines], str(self.model).split(":", 1)[1], self.work)
        else:
            takes = [(tts(ln.text, self.work / f"line{i:02d}.wav", self.model, self.ls), None)
                     for i, ln in enumerate(self.lines)]
        for (audio, spans), ln in zip(takes, self.lines):
            d = len(audio) / SR
            span = d + ln.pause
            self.timeline.append((t, span, ln))
            self.voice.append((t, audio))
            if spans:  # exact word timings from the TTS provider
                wt = [(w, t + s, t + max(e, s + 0.05)) for w, s, e in spans]
            else:
                wt = word_times(ln.text.split(), t, d)
            self.words.extend(wt)
            self.line_words.append([(w.strip(",.!?").lower(), ws - t, we - t) for w, ws, we in wt])
            for when, name in ln.sfx:
                if isinstance(when, str):  # anchor to a spoken word
                    when = next(s for w, s, e in wt if w.strip(",.!?").lower() == when.strip(",.!?").lower()) - t
                self.events.append((t + when, name))
            t += span
        self.total = t + 0.6

    def spans(self):
        """(start, on-screen length, words) per line; the last line runs to the end."""
        self._layout()
        out = []
        for i, (s, span, _) in enumerate(self.timeline):
            if i == len(self.timeline) - 1:
                span = self.total - s
            out.append((s, span, self.line_words[i]))
        return out

    def _captions(self, canvas, now):
        """2-3 word chunks, current word in yellow, chunk pops in."""
        chunks, cur = [], []
        for w in self.words:
            if cur and len(" ".join(x[0] for x in cur + [w])) > 15:
                chunks.append(cur)
                cur = []
            cur.append(w)
            if len(cur) == 3 or w[0][-1] in ".,!?":
                chunks.append(cur)
                cur = []
        if cur:
            chunks.append(cur)
        for ch in chunks:
            s, e = ch[0][1], ch[-1][2]
            if s <= now < e + 0.05:
                k = back_out((now - s) / 0.14)
                f = font(92, "Black")
                words = [w.upper() for w, *_ in ch]
                widths = [f.measureText(w + " ") for w in words]
                total = sum(widths) - f.measureText(" ")
                x = 540 - total / 2
                fit = min(1.0, 960 / total)  # never run off the screen edges
                canvas.save()
                canvas.translate(540, 1480)
                canvas.scale((0.82 + 0.18 * k) * fit, (0.82 + 0.18 * k) * fit)
                canvas.translate(-540, -1480)
                for (w, ws, we), word, wd in zip(ch, words, widths):
                    active = ws <= now < we
                    canvas.drawString(word, x, 1480 + 6, f, paint("#000000", 160, blur=6))
                    canvas.drawString(word, x, 1480, f, paint("#000000", stroke=16))
                    canvas.drawString(word, x, 1480, f, paint("#ffd60a" if active else "#ffffff"))
                    x += wd
                canvas.restore()
                return

    def _audio(self, path):
        n = int(self.total * SR)
        voice = np.zeros(n)
        for t, a in self.voice:
            s = int(t * SR)
            voice[s:s + len(a)] += a[: n - s]
        # Voices arrive at different levels (ElevenLabs ~9 dB under Piper), and
        # music/SFX gains below are fixed: bring speech to -18 dBFS RMS first.
        hop = int(0.01 * SR)
        fr = voice[: n // hop * hop].reshape(-1, hop)
        rms = np.sqrt((fr ** 2).mean(1))
        speech = fr[rms > rms.max() * 0.05]
        voice *= 10 ** (-18 / 20) / (np.sqrt((speech ** 2).mean()) + 1e-9)
        fx = np.zeros(n)
        for t, name in self.events:
            a = sfx(name)
            s = int(max(0, t) * SR)
            fx[s:s + len(a)] += a[: n - s]
        music = music_bed(self.total)
        # Duck music under the voice (smoothed envelope sidechain).
        env = np.convolve(np.abs(voice), np.ones(int(0.25 * SR)) / (0.25 * SR), mode="same")
        duck = 1 - 0.55 * np.clip(env / (env.max() + 1e-9) * 4, 0, 1)
        fade = np.minimum(1, (n - np.arange(n)) / (0.8 * SR))
        mix = voice * 1.0 + fx * 0.55 + music * duck * fade * 0.9
        mix = np.stack([mix, mix], axis=1)
        raw = self.work / "mix_raw.wav"
        with wave.open(str(raw), "wb") as wv:
            wv.setnchannels(2)
            wv.setsampwidth(2)
            wv.setframerate(SR)
            wv.writeframes((np.clip(mix / (np.abs(mix).max() + 1e-9) * 0.9, -1, 1) * 32767).astype("<i2").tobytes())
        target = "I=-14:TP=-1.5:LRA=11"
        probe = subprocess.run(["ffmpeg", "-i", str(raw), "-af", f"loudnorm={target}:print_format=json",
                                "-f", "null", "-"], capture_output=True, text=True, check=True).stderr
        m = json.loads(probe[probe.rindex("{"):probe.rindex("}") + 1])
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(raw), "-af",
                        f"loudnorm={target}:linear=true:measured_I={m['input_i']}:measured_TP={m['input_tp']}"
                        f":measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}"
                        f":offset={m['target_offset']}", "-ar", str(SR), str(path)], check=True)

    def render(self, out, preview=None):
        """preview: list of timestamps -> write PNG stills instead of video."""
        self._layout()
        audio = self.work / "mix.wav"
        surface = skia.Surface(W, H)
        canvas = surface.getCanvas()
        ctx = {}

        def frame(now):
            idx = max(i for i, (s, _, _) in enumerate(self.timeline) if s <= max(now, self.timeline[0][0]))
            s, span, ln = self.timeline[idx]
            canvas.clear(skia.ColorBLACK)
            ctx.update(now=now, index=idx, words=self.line_words[idx])
            local = now - s
            if idx == len(self.timeline) - 1:
                span = self.total - s
            canvas.save()
            ln.scene(canvas, local, span, ctx)
            canvas.restore()
            self._captions(canvas, now)
            return surface.makeImageSnapshot()

        if preview:
            for ts in preview:
                frame(ts).save(str(Path(out).with_name(f"{Path(out).stem}_{ts:05.2f}.png")), skia.kPNG)
            return
        self._audio(audio)
        ff = subprocess.Popen(
            ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}",
             "-r", str(FPS), "-i", "-", "-i", str(audio), "-map", "0:v", "-map", "1:a",
             "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
             "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(out)],
            stdin=subprocess.PIPE)
        for n in range(int(self.total * FPS)):
            ff.stdin.write(frame(n / FPS).toarray(colorType=skia.kRGBA_8888_ColorType).tobytes())
        ff.stdin.close()
        if ff.wait():
            raise RuntimeError("ffmpeg failed")
        # Sidecar with caption timings, used for SRT upload / review.
        (Path(out).with_suffix(".json")).write_text(json.dumps(
            {"duration": self.total, "lines": [[s, d, ln.text] for s, d, ln in self.timeline]}, indent=1))
