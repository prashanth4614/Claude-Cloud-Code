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


def _norm(w):
    return "".join(ch for ch in w.lower() if ch.isalnum())


def strip_tags(text):
    """Drop [audio tags] (ElevenLabs v3 delivery directions) from a line."""
    import re
    return re.sub(r"\s+", " ", re.sub(r"\[[^\]]*\]", "", text)).strip()


def align_words(audio, script_words, prompt):
    """Word spans for script_words in audio: Whisper word timestamps matched
    to the script, then starts snapped forward to the actual speech onset
    (Whisper starts tend to absorb the silence before a word)."""
    import difflib

    from faster_whisper import WhisperModel

    model = WhisperModel(os.environ.get("WHISPER_MODEL", "small.en"), device="cpu", compute_type="int8")
    segs, _ = model.transcribe(audio.astype(np.float32) if SR == 16000 else _resample16(audio),
                               word_timestamps=True, initial_prompt=prompt, language="en")
    heard = [(w.word.strip(), w.start, w.end) for sg in segs for w in sg.words if _norm(w.word)]
    want = [_norm(w) for w in script_words]
    times = [None] * len(want)
    sm = difflib.SequenceMatcher(None, want, [_norm(w) for w, _, _ in heard], autojunk=False)
    for op, i0, i1, j0, j1 in sm.get_opcodes():
        if op == "equal" or (op == "replace" and i1 - i0 == j1 - j0):
            for k in range(i1 - i0):
                times[i0 + k] = heard[j0 + k][1:]
        elif op == "replace":  # e.g. "Eustachian" heard as two words: share the span
            t0, t1 = heard[j0][1], heard[j1 - 1][2]
            wts = np.cumsum([0] + [len(want[k]) + 1 for k in range(i0, i1)]) / (sum(len(want[k]) + 1 for k in range(i0, i1)))
            for k in range(i1 - i0):
                times[i0 + k] = (t0 + (t1 - t0) * wts[k], t0 + (t1 - t0) * wts[k + 1])
    # words Whisper missed: spread over the gap between their neighbours
    k = 0
    while k < len(times):
        if times[k] is None:
            j = k
            while j < len(times) and times[j] is None:
                j += 1
            lo = times[k - 1][1] if k else 0.0
            hi = times[j][0] if j < len(times) else len(audio) / SR
            step = (hi - lo) / (j - k)
            for m in range(k, j):
                times[m] = (lo + step * (m - k), lo + step * (m - k + 1))
            k = j
        k += 1
    # snap to speech energy
    hop = int(0.01 * SR)
    fr = audio[: len(audio) // hop * hop].reshape(-1, hop)
    rms = np.convolve(np.sqrt((fr ** 2).mean(1)), np.ones(3) / 3, mode="same")
    voiced = rms > rms.max() * 0.06
    spans = []
    for k, (s, e) in enumerate(times):
        nxt = times[k + 1][0] if k + 1 < len(times) else len(audio) / SR
        f0, f1 = int(s * 100), int(min(e, nxt) * 100)
        on = np.flatnonzero(voiced[f0:max(f0 + 1, f1 - 4)])
        s2 = (f0 + on[0]) / 100 if len(on) else s
        off = np.flatnonzero(voiced[int(s2 * 100):f1 + 1])
        e2 = (int(s2 * 100) + off[-1] + 1) / 100 if len(off) else e
        spans.append((s2, max(e2, s2 + 0.05)))
    return spans


def _resample16(audio):
    n = int(len(audio) * 16000 / SR)
    return np.interp(np.linspace(0, len(audio) - 1, n), np.arange(len(audio)), audio).astype(np.float32)


def compress_pauses(audio, spans, max_gap):
    """Shorten silences between words to max_gap seconds (cut from the middle
    with a short crossfade) and shift the word spans to match."""
    xf = int(0.01 * SR)
    pieces, shift, last, new = [], 0.0, 0, []
    for k, (s, e) in enumerate(spans):
        if k:
            gap = s - spans[k - 1][1]
            if gap > max_gap:
                mid = (spans[k - 1][1] + s) / 2
                c0, c1 = int((mid - (gap - max_gap) / 2) * SR), int((mid + (gap - max_gap) / 2) * SR)
                seg = audio[last:c0 + xf].copy()
                pieces.append(seg)
                last = c1
                shift += (c1 - c0) / SR
        new.append((s - shift, e - shift))
    pieces.append(audio[last:])
    out = pieces[0]
    ramp = np.linspace(1, 0, xf)
    for pc in pieces[1:]:
        head = out[-xf:] * ramp + pc[:xf] * (1 - ramp) if len(pc) >= xf else out[-xf:]
        out = np.concatenate([out[:-xf], head, pc[xf:]])
    return out, new


def elevenlabs_post(path, body, timeout=300):
    """POST to the ElevenLabs API and return the raw response bytes.

    Uses ELEVENLABS_API_KEY when set. Cloud sessions may instead have the key
    attached by the network proxy as a secret, so a missing variable is not an
    error; a 401 then means no key reached ElevenLabs."""
    import urllib.error
    import urllib.request

    headers = {"Content-Type": "application/json"}
    if os.environ.get("ELEVENLABS_API_KEY"):
        headers["xi-api-key"] = os.environ["ELEVENLABS_API_KEY"]
    req = urllib.request.Request("https://api.elevenlabs.io" + path, data=json.dumps(body).encode(),
                                 method="POST", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        raise SystemExit(f"ElevenLabs {path.split('?')[0]} -> HTTP {e.code}: {e.read().decode()[:400]}")


def elevenlabs_script(lines, voice_id, workdir):
    """Whole script in ONE ElevenLabs take, split back into lines.

    lines: [(spoken, caption)]. spoken may carry v3 audio tags ([curious],
    [excited], ...) and pacing punctuation (..., dashes); captions show the
    caption text. One take keeps the voice consistent while the tags give
    real pitch/energy swings. Word timings come from local Whisper alignment
    snapped to speech onsets (v3's own timestamps drift 0.2-0.5 s). Long
    silences are shortened, then each line is sliced at its words plus a
    breath either side. Returns [(audio, word_spans)].
    The response is cached by text + voice + settings: re-renders are free.
    Env: ELEVENLABS_MODEL (default eleven_v3), ELEVENLABS_STABILITY."""
    import base64
    import hashlib
    import urllib.request

    model = os.environ.get("ELEVENLABS_MODEL", "eleven_v3")
    v3 = model.startswith("eleven_v3")
    spoken = [sp if v3 else strip_tags(sp) for sp, _ in lines]
    text = " ".join(spoken)
    settings = {"stability": float(os.environ.get("ELEVENLABS_STABILITY", "0.5")), "similarity_boost": 0.85,
                "style": 0.4, "use_speaker_boost": True}
    if not v3:
        settings["speed"] = 1.0
    body = {"text": text, "model_id": model, "voice_settings": settings}
    key = hashlib.sha256(json.dumps([voice_id, body], sort_keys=True).encode()).hexdigest()[:16]
    cache = Path(workdir) / "tts_cache" / f"script_{key}.json"
    if cache.exists():
        res = json.loads(cache.read_text())
    else:
        res = json.loads(elevenlabs_post(
            f"/v1/text-to-speech/{voice_id}/with-timestamps?output_format=mp3_44100_128", body))
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(res))
    take = Path(workdir) / "take.mp3"
    take.write_bytes(base64.b64decode(res["audio_base64"]))
    audio = decode(take)
    captions = [cap.split() for _, cap in lines]
    words = [w for cap in captions for w in cap]
    times = Path(workdir) / f"align_{key}.json"  # Whisper is slow-ish: cache it too
    if times.exists():
        spans = [tuple(x) for x in json.loads(times.read_text())]
    else:
        spans = align_words(audio, words, " ".join(cap for _, cap in lines))
        times.write_text(json.dumps(spans))
    audio, spans = compress_pauses(audio, spans, float(os.environ.get("MAX_PAUSE", "0.4")))
    out, k, pad = [], 0, int(0.12 * SR)
    bounds = []
    for cap in captions:
        bounds.append((spans[k][0], spans[k + len(cap) - 1][1], k, len(cap)))
        k += len(cap)
    for i, (s0, e0, k, n) in enumerate(bounds):
        # line = its words plus a breath either side, never into a neighbour
        lo = int(s0 * SR) - pad if not i else max(int(s0 * SR) - pad, int((bounds[i - 1][1] + s0) / 2 * SR))
        hi = int(e0 * SR) + pad if i + 1 == len(bounds) else \
            min(int(e0 * SR) + pad, int((e0 + bounds[i + 1][0]) / 2 * SR))
        lo = max(0, lo)
        c0 = lo / SR
        out.append((audio[lo:hi].copy(), [(w, st - c0, en - c0) for w, (st, en) in zip(captions[i], spans[k:k + n])]))
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


def _lowpass(x, k):
    """One-pole lowpass (k in 0..1, higher = brighter). For short SFX only."""
    y, out = 0.0, np.empty(len(x))
    for i, v in enumerate(x):
        y += k * (v - y)
        out[i] = y
    return out


def ffmpeg_filter(x, af):
    """Run a mono float signal through an ffmpeg audio filter chain.

    The output is forced back to SR: some filters (loudnorm) silently upsample to
    192 kHz, which would otherwise be read back as 4x-stretched noise."""
    r = subprocess.run(["ffmpeg", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-",
                        "-af", af, "-ar", str(SR), "-f", "f32le", "-"], input=x.astype(np.float32).tobytes(),
                       capture_output=True, check=True).stdout
    y = np.frombuffer(r, dtype=np.float32).astype(float)
    return np.pad(y, (0, max(0, len(x) - len(y))))[: len(x)]


def cabin_ambience(total, seed=3):
    """Airliner cabin bed: brown-ish air noise + engine hum with slow drift."""
    r = rng(seed)
    n = int(total * SR)
    t = np.arange(n) / SR
    air = ffmpeg_filter(r.standard_normal(n), "lowpass=f=420,lowpass=f=420,highpass=f=40")
    hum = sum(a * np.sin(2 * np.pi * f * t + r.random() * 6) for f, a in ((92, 1), (184, 0.4), (276, 0.15)))
    drift = 1 + 0.15 * np.sin(2 * np.pi * t / 7.3)
    out = air / (np.std(air) + 1e-9) + 0.25 * hum * drift
    return out / (np.std(out) + 1e-9)


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
    if name == "pop":  # ear pop: soft click + low thump + a breath of released air
        n = int(0.35 * SR)
        t = np.arange(n) / SR
        thump = np.sin(2 * np.pi * (75 + 160 * np.exp(-t * 60)) * t) * _env(n, 0.001, 0.045)
        click = _lowpass(r.standard_normal(n), 0.35) * _env(n, 0.0003, 0.004)
        air = _lowpass(r.standard_normal(n), 0.08) * _env(n, 0.01, 0.09) * 2.5
        return (thump + 0.8 * click + 0.5 * air) * 0.8
    if name == "gulp":  # swallow: wet low blip
        n = int(0.22 * SR)
        t = np.arange(n) / SR
        f = 380 * np.exp(-t * 9) + 110
        body = np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(n, 0.006, 0.05)
        return (body + 0.3 * _lowpass(r.standard_normal(n), 0.1) * _env(n, 0.002, 0.02)) * 0.55
    if name == "chime":  # cabin seatbelt chime: bing-bong
        n = int(1.6 * SR)
        t = np.arange(n) / SR
        out = np.zeros(n)
        for t0, f in ((0, 784), (0.42, 622)):
            s0 = int(t0 * SR)
            tt = t[: n - s0]
            out[s0:] += sum(a * np.sin(2 * np.pi * f * m * tt) for m, a in ((1, 1), (2, 0.25), (3, 0.08))) \
                * _env(n - s0, 0.004, 0.45)
        return out * 0.22
    if name == "ding":
        n = int(0.9 * SR)
        t = np.arange(n) / SR
        tone = sum(a * np.sin(2 * np.pi * f * t) for f, a in ((1568, 1), (3136, 0.35), (4704, 0.12)))
        return tone * _env(n, 0.002, 0.25) * 0.18
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
    say: str = ""                          # what the voice says (ElevenLabs v3 tags ok); default: text


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
            takes = elevenlabs_script([(ln.say or ln.text, ln.text) for ln in self.lines],
                                      str(self.model).split(":", 1)[1], self.work)
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
        fx, muffle_cues = np.zeros(n), []
        for t, name in self.events:
            if name in ("muffle_on", "muffle_off"):  # blocked-ear effect on music + ambience
                muffle_cues.append((t, name == "muffle_on"))
                continue
            a = sfx(name)
            s = int(max(0, t) * SR)
            fx[s:s + len(a)] += a[: n - s]
        db = lambda x: 10 ** (x / 20)
        music = music_bed(self.total)
        music *= db(-31) / (np.std(music[np.abs(music) > 1e-4]) + 1e-9)
        amb = cabin_ambience(self.total) * db(-40)
        bed = music + amb
        if muffle_cues:
            m = np.zeros(n)
            for t, on in sorted(muffle_cues):
                m[int(max(0, t) * SR):] = 1.0 if on else 0.0
            m = np.convolve(m, np.ones(int(0.12 * SR)) / (0.12 * SR), mode="same")  # quick open/close
            bed = bed * (1 - m) + ffmpeg_filter(bed, "lowpass=f=380,lowpass=f=380") * db(3) * m
        # Duck the bed under the voice (smoothed sidechain): ~ -9 dB while speaking.
        env = np.convolve(np.abs(voice), np.ones(int(0.2 * SR)) / (0.2 * SR), mode="same")
        duck = 1 - 0.65 * np.clip(env / (np.percentile(env[env > 1e-4], 60) + 1e-9), 0, 1)
        duck = np.convolve(duck, np.ones(int(0.08 * SR)) / (0.08 * SR), mode="same")
        fade = np.minimum(1, (n - np.arange(n)) / (0.8 * SR))
        mix = voice + fx * 0.45 + bed * duck * fade
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
