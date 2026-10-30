#!/usr/bin/env python3
"""The pilot's sound mix: a clear voice, a score, room tone and Foley synced to the picture (no render needed).

  python3 shorts/pilot_ear_pop/mix.py OUT.wav [--stems DIR]      # MUSIC=0 leaves the score out

- Voice: rebuilt from the RAW ElevenLabs take (the cached takes, same timing as voice_take.wav),
  denoised (the clone's steady hiss came and went with every line), then VOICE_CHAIN: rumble filter, a
  little presence, a gentle 2:1 compressor. No de-esser and no dynamic loudness rider: voice_take.wav
  carries both (audio.py polish), and the owner heard them as a "buffering" sound under every line.
- Flow: continuous room tone per world (cabin, ear, sky, city), crossfaded across each change of world,
  and one score (audio/bgm/v6_music_d.mp3, ElevenLabs Music) under everything, looping back into its
  opening at the end.
- Pressure: the blocked ear builds as the eardrum bulges, peaks on "muffled, blocked feeling" and lets
  go on the POP; music and room tone go dull with it (muffle); the voice and Foley stay clear.
- Foley: clean ElevenLabs cues (audio/sfx), each placed by its ANCHOR (the moment of its hit, measured
  from the file) on the frame where the action happens on screen: the eardrum's shape keys, the tube
  opening, the camera reaching the ear, Max's face keys (swallow, yawn, chew; see real_max.py).
Levels, timings and cue choices follow Codex's sound-design review (shorts/tools/codex/answers/007-*).
Loudness: one fixed gain to -14 LUFS (measured), a peak limiter only above -1.9 dBFS (-1.5 dB true peak
after AAC): nothing rides the level. --stems also writes each stem for checking against the picture.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from engine import SR, decode, ffmpeg_filter  # noqa: E402

PLAN = json.loads((HERE / "plan.json").read_text())
FPS = PLAN["fps"]
SHOT = {s["id"]: s for s in PLAN["shots"]}
# Clarity without artefacts: static EQ and a slow, gentle compressor only (no de-esser, no loudnorm,
# no auto-level limiter: each of those can pump or "gurgle" on synthetic speech).
VOICE_CHAIN = ("highpass=f=75,equalizer=f=300:t=q:w=1:g=-1.5,equalizer=f=3000:t=q:w=0.9:g=2.5,"
               "highshelf=f=9000:g=1,acompressor=threshold=-18dB:ratio=2:attack=20:release=200:makeup=1:knee=6")
MUSIC_FILE, LOOP_AT = "v6_music_d", 40.0   # the score; where it crossfades back into its opening
MUSIC_UNDER = 21          # dB below the voice's speech level (Codex 007)
# room tone per set, and each bed's level in dB below the speech (Codex 007)
BEDS = {"cabin": ("v6b_cabin",), "sky_golden_hour": ("v6b_cabin", "v6b_sky"), "sky_high": ("v6b_sky",),
        "ear_inside": ("v6b_ear",), "ear_map": ("v6b_ear",), "city_dusk": ("v6b_city",)}
BED_UNDER = {"v6b_cabin": 30, "v6b_ear": 32, "v6b_sky": 32, "v6b_city": 34}
PRESSURE_UNDER = 24       # the blocked-ear texture at its fullest
XFADE = 0.7               # seconds


def t_of(frame):
    return (frame - 1) / FPS


def beat(sid, key):
    return next(b["frame"] for b in SHOT[sid]["beats"] if key in (b.get("word"), b.get("key")))


def db(x):
    return 10 ** (x / 20)


def rms(a):
    return np.sqrt(np.mean(a ** 2)) + 1e-12


class Cue:
    """A Foley file, normalised by its LOUDNESS (its loudest 100 ms), with its anchor (the hit) measured
    once. Peak-normalising made short hits (a chew, a click) 25-35 dB quieter than the voice: inaudible."""

    def __init__(self, name, anchor="peak"):
        a = decode(HERE / "audio" / "sfx" / f"{name}.mp3")
        w = int(0.01 * SR)
        env = np.sqrt(np.convolve(a ** 2, np.ones(w) / w, mode="same"))
        self.anchor = (np.argmax(env > env.max() * 0.25) if anchor == "onset" else np.argmax(env)) / SR
        w = int(0.1 * SR)
        self.audio = a / (np.sqrt(np.convolve(a ** 2, np.ones(w) / w, mode="same")).max() + 1e-9)
        self.name = name


def place(bus, cue, frame, gain_db, offset=0.0):
    """Put the cue's hit on `frame` (+ offset seconds), its loudest 100 ms `gain_db` against the speech level."""
    i = int((t_of(frame) + offset - cue.anchor) * SR)
    a = cue.audio * db(gain_db)
    if i < 0:
        a, i = a[-i:], 0
    a = a[: max(0, len(bus) - i)]
    bus[i:i + len(a)] += a
    PLACED.append((cue.name, t_of(frame) + offset, gain_db))


PLACED = []


def foley(n):
    """Codex's cue sheet (request 007): an accent only where something physical happens on screen. Gains
    are each cue's loudest 100 ms against the speech level: about -10 dB is clearly heard under the
    voice (the owner, on v6: the jet at -13 was right, cues at -25 to -34 were "barely audible")."""
    c = {k: Cue(k) for k in ("v3_whoosh_in", "v3_whoosh_pass", "v3_whip", "v3_pop", "v3_stretch", "v3_valve",
                             "v3_air", "v3_thud", "v3_swallow", "v3_chew", "jet_climb", "outro_chime", "ear_pop",
                             "v6_jet_swell", "v6_plane_descend", "v6_exhale", "v6_release")}
    c["v3_yawn"] = Cue("v3_yawn", anchor="onset")
    fx = np.zeros(n)
    S = lambda sid: SHOT[sid]["start"]   # noqa: E731
    E = lambda sid: SHOT[sid]["end"]     # noqa: E731
    place(fx, c["jet_climb"], S("S01"), -12, 0.45)              # the jet sweeps past the camera
    place(fx, c["v3_whoosh_in"], E("S02"), -10, -0.12)          # the camera dives into his ear
    place(fx, c["v3_whoosh_pass"], S("S03"), -13, 0.35)         # on down the canal
    place(fx, c["v3_whoosh_pass"], beat("S04", "ground"), -12, -0.05)  # through the eardrum
    place(fx, c["v6_jet_swell"], S("S05a"), -12, 0.8)           # the jet climbs past
    place(fx, c["v3_air"], beat("S05b", "drops"), -13)          # outside air thins
    place(fx, c["v3_stretch"], beat("S06a", "pushes"), -12, 0.2)
    place(fx, c["v3_stretch"], beat("S06b", "bulges") - 2, -9)  # mid-bulge (measured: steady swell, frames 517-547)
    place(fx, c["v3_valve"], beat("S08b", "cracks") + 3, -9)   # the valve parts (measured: motion peaks 789-791)
    place(fx, c["v3_air"], beat("S09a", "escapes"), -11)        # air escapes down the tube
    place(fx, c["v3_whip"], E("S09a") - 3, -12)                 # whip up into the POP shot
    fpop = beat("S09b", "pop")
    place(fx, c["v3_pop"], fpop + 1, -2)                        # POP: the eardrum snaps flat (keys pop-1 -> pop+3)
    place(fx, c["ear_pop"], fpop + 1, -10)                      #   with the softer generated pop under it
    place(fx, c["v6_release"], fpop + 3, -12)                   #   and the pressure letting go
    place(fx, c["v6_exhale"], beat("S09c", "relief") + 3, -11)  # Max's relief (relief_smile at relief+8)
    place(fx, c["v6_plane_descend"], S("S10"), -13, 0.9)        # the plane comes down over the city
    place(fx, c["v3_thud"], beat("S11a", "shut") + 8, -11)      # the tube clamps shut, turns red
    place(fx, c["v3_stretch"], beat("S11b", "inward") + 2, -10)  # eardrum pushed in (measured: peak motion word+2)
    fs, fy, fc = (beat("S12a", w) for w in ("swallowing", "yawning", "chewing"))
    place(fx, c["v3_swallow"], fs + 4, -10)                     # swallow face key at word+4
    place(fx, c["v3_yawn"], fy - 2, -12)                        # yawn opens from word-2 to word+10
    for i in range(4):                                          # the bites: jaw closes on chew_b, word+11+8i
        place(fx, c["v3_chew"], fc + 11 + i * 8, -13)           # (real_max.perform; jawOpen 0.04 vs 0.22)
    fu, fr = beat("S12b", "pull"), beat("S12b", "open")
    place(fx, c["v3_valve"], fu + 1, -11)                       # the tube opens again
    place(fx, c["v3_air"], fu + 4, -14)                         # cabin air rises into the middle ear
    place(fx, c["v3_pop"], fr + 2, -8)                         # the eardrum settles flat
    place(fx, c["outro_chime"], S("S13") + 8, -16)              # follow card
    return fx


def lines():
    return json.loads((HERE / "audio" / "voice_timing.json").read_text())["lines"]


def smooth(g, seconds):
    k = max(1, int(seconds * SR))
    return np.convolve(g, np.ones(k) / k, mode="same")


def level(x):
    """Loudness of a signal while it plays: the 70th percentile of 0.4 s RMS windows, in dB."""
    w = int(0.4 * SR)
    return 20 * np.log10(np.percentile(np.sqrt(np.convolve(x ** 2, np.ones(w) / w, mode="valid")), 70) + 1e-12)


def loop(name, n, folder="beds"):
    a = decode(HERE / "audio" / folder / f"{name}.mp3")
    return np.tile(a, n // len(a) + 1)[:n]


def keyed(n, keys):
    """A gain curve through (seconds, dB) keys, straight lines in dB; silent (-80 dB) outside them."""
    t, d = zip(*sorted(keys))
    return db(np.interp(np.arange(n) / SR, t, d, left=-80, right=-80))


def duck(n, depth_db, attack=0.15, release=0.6, bridge=0.5):
    """depth_db for each spoken line, ramping in `attack` s BEFORE the line (anticipatory) and back out
    over `release` s after it; lines less than `bridge` s apart are one span, so the score doesn't
    bob up between them."""
    spans = []
    for ln in lines():
        if spans and ln["start"] - spans[-1][1] < bridge:
            spans[-1][1] = ln["end"]
        else:
            spans.append([ln["start"], ln["end"]])
    t = np.arange(n) / SR
    g = np.zeros(n)
    for a, b in spans:
        g = np.maximum(g, np.interp(t, [a - attack, a, b, b + release], [0, 1, 1, 0], left=0, right=0))
    return db(depth_db * g)


def pop_dip(n):
    """Music and room tone drop 9 dB for the last 250 ms before the POP and recover over 350 ms."""
    p = t_of(beat("S09b", "pop"))
    return db(np.interp(np.arange(n) / SR, [p - 0.3, p - 0.25, p, p + 0.35], [0, -9, -9, 0]))


def music(n, speech_db):
    """The score (ElevenLabs Music, Codex's brief: wonder, gentle tension, a suspended hold, a soft
    release on the POP, warm clarity) from the first frame, MUSIC_UNDER dB under the speech, ducked
    3 dB under the lines. Near its end it crossfades back into its own opening, so the Short loops
    seamlessly: no ending fade."""
    src = decode(HERE / "audio" / "bgm" / f"{MUSIC_FILE}.mp3")
    m = np.zeros(n)
    m[: min(n, len(src))] = src[:n]
    a, x = int(LOOP_AT * SR), int(1.5 * SR)
    head = src[int(1.0 * SR):]                       # the opening, past its soft first second
    head = np.pad(head, (0, max(0, n - a - len(head))))[: n - a]
    m[a:] = m[a:] * np.r_[np.linspace(1, 0, x), np.zeros(n - a - x)] + head * np.r_[np.linspace(0, 1, x), np.ones(n - a - x)]
    m *= db(speech_db - MUSIC_UNDER - level(m))
    m[-int(0.03 * SR):] *= np.linspace(1, 0, int(0.03 * SR))   # no click at the very end
    return m * duck(n, -3)


def beds(n, speech_db):
    """Continuous room tone per world, so the picture's cuts don't cut the sound: the diagram (ear_map)
    shares the ear's tone, the cabin runs on under the first exterior; at a change of world the beds
    cross over 0.7 s (equal power) centred 0.1 s after the cut, so the new world leads in ~0.25 s
    and the old one trails ~0.45 s."""
    shots = PLAN["shots"]
    edges = [0] + [int((t_of(s["start"]) + 0.1) * SR) for s in shots[1:]] + [n]
    out = np.zeros(n)
    for name, under in BED_UNDER.items():
        g = np.zeros(n)
        for s, a, b in zip(shots, edges, edges[1:]):
            if name in BEDS[s["set"]]:
                g[a:b] = 1
        bed = ffmpeg_filter(loop(name, n), "highpass=f=60")
        env = np.sqrt(smooth(bed ** 2, 1.0)) + 1e-9      # even it out: a room tone mustn't come and go
        bed *= np.clip(np.median(env) / env, 0.5, db(24))
        bed *= db(speech_db - under - level(bed))
        out += bed * np.sqrt(np.clip(smooth(g, XFADE), 0, 1))
    return out


def pressure(n, speech_db):
    """The blocked ear, heard: a soft 350-650 Hz fullness (audible on a phone) over a low drone. It is
    there in the cold open, builds while the eardrum bulges, is full on "muffled, blocked feeling",
    holds under the tube's explanation and lets go on the POP; on the way down it builds again while
    the tube stays shut and lets go when swallowing pulls it open."""
    T = lambda f: t_of(f)   # noqa: E731
    pop, s0 = beat("S09b", "pop"), SHOT["S00"]["end"]
    keys = [(0, 0), (T(s0 - 3), 0), (T(s0 + 1), -80),
            (T(beat("S06a", "pushes") - 15), -80), (T(beat("S06a", "pushes")), -14), (T(beat("S06b", "bulges")), -5),
            (T(beat("S07", "muffled")) - 0.15, 0), (T(SHOT["S07"]["end"]), 0), (T(SHOT["S08a"]["start"] + 8), -3),
            (T(pop - 1), -3), (T(pop + 6), -80),
            (T(beat("S11a", "rises") - 15), -80), (T(beat("S11a", "rises")), -14), (T(beat("S11a", "shut")), -6),
            (T(beat("S11b", "inward")), -2), (T(SHOT["S12a"]["start"]), -3), (T(beat("S12b", "pull")), -3),
            (T(beat("S12b", "open") + 6), -80)]
    tex = ffmpeg_filter(loop("v6b_cabin", n), "highpass=f=350,highpass=f=350,lowpass=f=650,lowpass=f=650")
    drone = ffmpeg_filter(loop("v6_blocked", n), "highpass=f=45,lowpass=f=650")
    p = tex / db(level(tex)) + 0.7 * drone / db(level(drone))
    return p * db(speech_db - PRESSURE_UNDER - level(p)) * keyed(n, keys)


def muffle(bus, n):
    """Music and room tone go dull, as if through a blocked ear: fully in the cold open (easing out by
    its cut) and from just before "muffled", then half-dull until the POP restores the brightness over
    200 ms. The voice and the Foley stay clear."""
    dull = ffmpeg_filter(bus, "lowpass=f=800,lowpass=f=800")      # 24 dB/oct
    s0, s7, pop = SHOT["S00"]["end"], beat("S07", "muffled"), beat("S09b", "pop")
    t = np.arange(n) / SR
    wet = np.interp(t, [0, t_of(s0 - 3), t_of(s0 + 1),
                        t_of(s7) - 0.27, t_of(s7) - 0.15, t_of(SHOT["S07"]["end"] + 1), t_of(SHOT["S08a"]["start"]) + 0.2,
                        t_of(pop + 1), t_of(pop + 1) + 0.2],
                    [1, 1, 0, 0, 1, 1, 0.55, 0.55, 0], left=0, right=0)
    return bus * (1 - wet) + dull * wet


def raw_voice():
    """The voice as ElevenLabs delivered it, assembled exactly as audio.py does (same gaps and pauses,
    so every word keeps its time), but without the polish chain baked into voice_take.wav."""
    sys.argv, argv = ["audio"], sys.argv
    import audio
    sys.argv = argv
    parts = audio.take_parts(audio.SCRIPT["voice"].split(":", 1)[1])
    gap = np.zeros(int(0.28 * SR))
    pauses = [np.zeros(int(ln.get("pause_after", 0) * SR)) for ln in audio.SCRIPT["lines"]]
    return np.concatenate([p for (a, _), e in zip(parts, pauses) for p in (a, gap, e)])


def denoise(v):
    """The clone carries a steady hiss + hum about 27 dB under the speech, inside every line but not
    between lines (digital silence), so it switched on and off with the voice. A stationary spectral
    gate (noisereduce) learns it from the pauses between words and takes off 80% of it (100% made the
    voice watery); 20 ms fades at each line's edges."""
    import noisereduce as nr
    w = int(0.4 * SR)
    sp = 20 * np.log10(np.percentile(np.sqrt(np.convolve(v ** 2, np.ones(w) / w, mode="valid")), 85))
    prof = []
    for ln in lines():
        for (_, _, e0), (_, s1, _) in zip(ln["words"], ln["words"][1:]):
            seg = v[int((e0 + 0.04) * SR):int((s1 - 0.04) * SR)]
            if len(seg) > 0.08 * SR and 20 * np.log10(rms(seg)) < sp - 18:
                prof.append(seg)
    out = nr.reduce_noise(y=v, sr=SR, y_noise=np.concatenate(prof), stationary=True, prop_decrease=0.8,
                          n_std_thresh_stationary=1.5, n_fft=2048, time_mask_smooth_ms=80, freq_mask_smooth_hz=500)
    f = int(0.02 * SR)
    for ln in lines():
        a, b = int(ln["start"] * SR), min(len(out), int(ln["end"] * SR))
        out[a:a + f] *= np.linspace(0, 1, f)
        out[b - f:b] *= np.linspace(1, 0, f)
    print(f"[mix] voice noise profile: {sum(map(len, prof)) / SR:.2f} s from {len(prof)} pauses")
    return out


def write(path, mono, two_pass=True):
    raw = Path(str(path) + ".f32")
    raw.write_bytes(np.repeat(mono.astype(np.float32)[:, None], 2, axis=1).tobytes())
    af = "aresample=48000"
    if two_pass:   # one fixed gain to -14 LUFS (measured); a limiter catches only peaks above -1.9 dBFS
        r = subprocess.run(["ffmpeg", "-hide_banner", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", str(raw),
                            "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
        lufs = float(r[r.rindex("I:"):].split()[1])
        af = (f"volume={-14 - lufs:.2f}dB,aresample=192000,"          # limit at 4x: catches true peaks
              "alimiter=limit=0.8:attack=1:release=50:level=false,aresample=48000")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", str(raw),
                    "-af", af, "-c:a", "pcm_s16le", str(path)], check=True)
    raw.unlink()


def main():
    a = sys.argv[1:]
    out = Path(a[0] if a else HERE.parent.parent / "out" / "final" / "mix.wav")
    n = int(t_of(PLAN["frame_end"] + 1) * SR)
    voice = ffmpeg_filter(denoise(raw_voice()), VOICE_CHAIN)
    vo = np.zeros(n)
    vo[: min(n, len(voice))] = voice[:n]
    w = int(0.4 * SR)
    speech_db = 20 * np.log10(np.percentile(np.sqrt(np.convolve(vo ** 2, np.ones(w) / w, mode="valid")), 85))
    fx = ffmpeg_filter(foley(n) * db(speech_db), "lowpass=f=12000")   # cue gains are against the speech level
    dip = pop_dip(n)
    mus = muffle(music(n, speech_db) * dip, n) if os.environ.get("MUSIC", "1") == "1" else np.zeros(n)
    amb = muffle(beds(n, speech_db) * dip, n)
    prs = pressure(n, speech_db)
    write(out, vo + mus + amb + fx + prs)
    if "--stems" in a:
        d = Path(a[a.index("--stems") + 1])
        d.mkdir(parents=True, exist_ok=True)
        for name, x in (("voice", vo), ("music", mus), ("foley", fx), ("beds", amb), ("pressure", prs)):
            write(d / f"{name}.wav", x, two_pass=False)
    print(f"[mix] {out}: {n / SR:.1f} s; denoised voice + {len(PLACED)} Foley hits on picture beats + "
          f"world beds + pressure{' + ' + MUSIC_FILE if mus.any() else ''}")

if __name__ == "__main__":
    main()
