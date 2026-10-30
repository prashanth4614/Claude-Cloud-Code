#!/usr/bin/env python3
"""The pilot's sound mix: voice + ambience beds + sound effects, timed to the plan (no picture needed).

  python3 shorts/pilot_ear_pop/mix.py OUT.wav

- Voice: audio/voice_take.wav, as is.
- Beds, per shot set: cabin hum in the cabin, the soft body bed inside the ear (quieter on the x-ray
  map), wind for the sky and city. Crossfaded at the cuts and ducked while the voice speaks.
- Effects: the ElevenLabs cues in audio/sfx (each normalised first: some were generated at -37 dB
  peak) plus procedural ones from engine.sfx (whooshes, pop, gulp, thud, ding), on the shots' beats.
- Muffle: in the cold open and the "muffled" shot the beds and effects go dull (low-pass) under a
  faint pressure hum, while the voice stays clear.
Loudness: -14 LUFS integrated, -1.5 dBTP (YouTube's reference), 48 kHz stereo.
"""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from engine import SR, decode, ffmpeg_filter, rng, sfx  # noqa: E402

PLAN = json.loads((HERE / "plan.json").read_text())
FPS = PLAN["fps"]
SHOT = {s["id"]: s for s in PLAN["shots"]}
BED_DB = {"cabin": -27, "ear_inside": -25, "ear_map": -31, "sky_golden_hour": -24, "sky_high": -24, "city_dusk": -26}
MUFFLED = ("S00", "S07")


def sec(frame):
    return (frame - 1) / FPS


def beat(sid, key):
    return next(b["frame"] for b in SHOT[sid]["beats"] if key in (b.get("word"), b.get("key")))


def start(sid):
    return SHOT[sid]["start"]


def end(sid):
    return SHOT[sid]["end"]


def db(x):
    return 10 ** (x / 20)


def norm(a, peak=0.9):
    return a / (np.abs(a).max() + 1e-9) * peak


def loop(a, n):
    return np.tile(a, n // len(a) + 1)[:n]


PLACED = []


def place(bus, a, t, gain_db=0.0):
    PLACED.append(t)
    i = int(t * SR)
    if i >= len(bus):
        return
    a = a[: len(bus) - i]
    bus[i:i + len(a)] += a * db(gain_db)


def cue(name):
    if (HERE / "audio" / "sfx" / f"{name}.mp3").exists():
        return norm(decode(HERE / "audio" / "sfx" / f"{name}.mp3"))
    return norm(sfx(name, rng(abs(hash(name)) % 2**31)))


def wind(n):
    """Airy high-altitude wind: band-passed noise with a slow swell."""
    a = ffmpeg_filter(rng(11).standard_normal(n), "highpass=f=180,lowpass=f=1800,lowpass=f=1800")
    t = np.arange(n) / SR
    return norm(a * (0.75 + 0.25 * np.sin(2 * np.pi * t / 3.1)))


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else str(HERE.parent.parent / "out" / "final" / "mix.wav")
    n = int(sec(PLAN["frame_end"] + 1) * SR)
    voice = decode(HERE / PLAN["voice"])
    vo = np.zeros(n)
    vo[: min(n, len(voice))] = voice[:n]

    # ---- beds: per shot, 0.15 s crossfades, ducked 6 dB under the voice
    sources = {"cabin": loop(norm(decode(HERE / "audio/beds/cabin.mp3")), n),
               "body": loop(norm(decode(HERE / "audio/beds/body.mp3")), n), "wind": wind(n)}
    pick = {"cabin": "cabin", "ear_inside": "body", "ear_map": "body"}
    beds = np.zeros(n)
    xf = int(0.15 * SR)
    for s in PLAN["shots"]:
        a, b = int(sec(s["start"]) * SR), min(n, int(sec(s["end"] + 1) * SR))
        if s is PLAN["shots"][-1]:
            b = n
        env = np.ones(b - a + 2 * xf)
        ramp = np.linspace(0, 1, xf)
        env[:xf], env[-xf:] = ramp, ramp[::-1]
        lo, hi = max(0, a - xf), min(n, b + xf)
        seg = env[lo - (a - xf): len(env) - ((b + xf) - hi)]
        src = sources[pick.get(s["set"], "wind")]
        beds[lo:hi] += src[lo:hi] * seg * db(BED_DB.get(s["set"], -26))
    speech = np.convolve(np.abs(vo), np.ones(int(0.05 * SR)) / int(0.05 * SR), mode="same")
    duck = 1 - 0.5 * np.clip(speech / 0.04, 0, 1)                    # up to -6 dB while he talks
    duck = np.convolve(duck, np.ones(int(0.2 * SR)) / int(0.2 * SR), mode="same")
    beds *= duck

    # ---- effects (each normalised; gains in dB below full scale)
    fx = np.zeros(n)
    whoosh = cue("whoosh")
    place(fx, cue("jet_climb"), sec(start("S01")), -9)                       # the jet flies past
    place(fx, whoosh, sec(end("S02")) - 0.45, -6)                            # push into his ear
    place(fx, cue("into_ear"), sec(start("S03")), -9)                        # glide down the canal
    place(fx, whoosh, sec(start("S04")), -11)                                # through the eardrum
    place(fx, cue("card_soft"), sec(start("S04m")) + 0.15, -14)              # the map's labels
    place(fx, cue("jet_climb"), sec(start("S05a")), -11)                     # the climb
    place(fx, cue("air_release"), sec(beat("S05b", "drops")), -18)           # outside air thins
    place(fx, cue("stretch"), sec(beat("S06a", "pushes")), -14)              # air crowds the drum
    place(fx, cue("stretch"), sec(beat("S06b", "bulges")), -8)               # the bulge
    place(fx, cue("card_soft"), sec(beat("S06b", "bulges")), -16)            # badge
    place(fx, cue("tube_open"), sec(beat("S08b", "cracks")), -5)             # the tube cracks open
    place(fx, cue("air_release"), sec(beat("S09a", "escapes")), -7)          # air escapes
    place(fx, whoosh, sec(end("S09a")) - 0.3, -9)                            # whip up
    fpop = sec(beat("S09b", "pop"))
    place(fx, cue("ear_pop"), fpop, -2)                                      # POP: the generated pop...
    place(fx, cue("pop"), fpop, -5)                                          # ...with a firmer thump
    place(fx, cue("ding"), fpop + 0.03, -20)                                 # the light ring's shimmer
    place(fx, cue("gear_down"), sec(start("S10")), -9)                       # landing gear
    place(fx, cue("jet_climb")[::-1].copy(), sec(start("S10")), -15)         # the jet, descending
    place(fx, cue("thud"), sec(beat("S11a", "shut")), -14)                   # the tube stays shut
    place(fx, cue("squeeze"), sec(beat("S11b", "inward")), -7)               # eardrum pushed in
    place(fx, cue("card_soft"), sec(beat("S11b", "inward")), -16)            # badge
    place(fx, cue("gulp"), sec(beat("S12a", "swallowing")) + 0.1, -6)        # swallow
    place(fx, cue("card_soft"), sec(beat("S12a", "yawning")), -15)
    place(fx, cue("gulp"), sec(beat("S12a", "chewing")) + 0.35, -14)         # chewing
    place(fx, cue("air_release"), sec(beat("S12b", "pull")), -13)            # air flows up the tube
    place(fx, cue("pop"), sec(beat("S12b", "open")) + 0.1, -9)               # ears equalise again
    place(fx, cue("outro_chime"), sec(start("S13")) + 0.27, -12)             # follow card

    # ---- muffle: beds + effects go dull in the cold open and the "muffled" shot, under a faint hum
    bus = beds + fx
    dull = ffmpeg_filter(bus, "lowpass=f=420,lowpass=f=420")
    wet = np.zeros(n)
    hum_t = np.arange(n) / SR
    hum = (np.sin(2 * np.pi * 96 * hum_t) + 0.4 * np.sin(2 * np.pi * 192 * hum_t)) * 0.02
    fade = int(0.12 * SR)
    for sid in MUFFLED:
        a, b = int(sec(start(sid)) * SR), int(sec(end(sid) + 1) * SR)
        w = np.ones(b - a)
        w[:fade] = np.linspace(0, 1, fade)
        w[-fade:] = np.linspace(1, 0, fade)
        wet[a:b] = w
    bus = bus * (1 - wet) + dull * wet * 1.6 + hum * wet

    mix = vo + bus
    stereo = np.repeat(mix.astype(np.float32)[:, None], 2, axis=1)
    import subprocess
    tmp = Path(out).with_suffix(".raw.f32")
    tmp.write_bytes(stereo.tobytes())
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", str(tmp),
                    "-af", "loudnorm=I=-14:TP=-1.5:LRA=9,aresample=48000", "-c:a", "pcm_s16le", out], check=True)
    tmp.unlink()
    print(f"[mix] {out}: {n / SR:.1f} s, voice + beds + {len(PLACED)} effects, muffle in {', '.join(MUFFLED)}")


if __name__ == "__main__":
    main()
