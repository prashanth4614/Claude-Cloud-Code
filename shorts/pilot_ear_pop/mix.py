#!/usr/bin/env python3
"""The pilot's sound mix: punchy voice + music + clean Foley synced to the picture (no render needed).

  python3 shorts/pilot_ear_pop/mix.py OUT.wav [--stems DIR]

- Voice: audio/voice_take.wav through VOICE_CHAIN (presence, tight compression, de-ess, limiter).
- Music: audio/bgm/investigations.mp3 (Kevin MacLeod, CC BY 4.0), MUSIC_UNDER dB under the voice,
  ducked a further 3 dB while he speaks, dipped just before the POP, faded out on the end card.
- Foley: the clean v3 cues in audio/sfx (ElevenLabs, generated as isolated dry hits). Each cue is
  placed by its ANCHOR (the moment of its hit, measured from the file) on the frame where the action
  happens on screen: the eardrum's shape keys, the tube opening, the camera reaching the ear, Max's
  face keys (swallow, yawn, chew; see real_max.py), not on the spoken words.
- Muffle: in the cold open and the "muffled" shot, the music and Foley go dull (low-pass); the voice
  stays clear. No noise beds: the only ambience is a very low cabin tone in the cabin shots.
Loudness: two-pass -14 LUFS, -1.5 dBTP on the complete mix, 48 kHz stereo. --stems also writes the
voice, music and Foley stems for checking against the picture.
"""
import json
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
VOICE_CHAIN = ("highpass=f=90,equalizer=f=300:t=q:w=1.0:g=-3,equalizer=f=3500:t=q:w=1.2:g=4,"
               "highshelf=f=10000:g=2,acompressor=threshold=-22dB:ratio=4:attack=12:release=90:makeup=5:knee=3,"
               "deesser=i=0.4:m=0.5:f=0.5,alimiter=limit=0.9:attack=2:release=40")
MUSIC_UNDER = 21          # dB below the voice's speech level (Codex: 18-24)
MUFFLED = ("S00", "S07")


def t_of(frame):
    return (frame - 1) / FPS


def beat(sid, key):
    return next(b["frame"] for b in SHOT[sid]["beats"] if key in (b.get("word"), b.get("key")))


def db(x):
    return 10 ** (x / 20)


def rms(a):
    return np.sqrt(np.mean(a ** 2)) + 1e-12


class Cue:
    """A Foley file: normalised to a fixed loudness, with its anchor (the hit) measured once."""

    def __init__(self, name, anchor="peak"):
        a = decode(HERE / "audio" / "sfx" / f"{name}.mp3")
        w = int(0.01 * SR)
        env = np.sqrt(np.convolve(a ** 2, np.ones(w) / w, mode="same"))
        self.anchor = (np.argmax(env > env.max() * 0.25) if anchor == "onset" else np.argmax(env)) / SR
        self.audio = a / (env.max() + 1e-9) * 0.25          # same peak loudness for every cue


def place(bus, cue, frame, gain_db, offset=0.0):
    """Put the cue's hit on `frame` (+ offset seconds); a cue that would start before 0 is trimmed."""
    i = int((t_of(frame) + offset - cue.anchor) * SR)
    a = cue.audio * db(gain_db)
    if i < 0:
        a, i = a[-i:], 0
    a = a[: max(0, len(bus) - i)]
    bus[i:i + len(a)] += a
    PLACED.append((frame, offset))


PLACED = []


def foley(n):
    c = {k: Cue(k) for k in ("v3_whoosh_in", "v3_whoosh_pass", "v3_whip", "v3_pop", "v3_stretch", "v3_valve",
                             "v3_air", "v3_thud", "v3_swallow", "v3_chew", "v3_pluck", "jet_climb",
                             "gear_down", "outro_chime", "ear_pop")}
    c["v3_yawn"] = Cue("v3_yawn", anchor="onset")
    fx = np.zeros(n)
    S = lambda sid: SHOT[sid]["start"]   # noqa: E731
    E = lambda sid: SHOT[sid]["end"]     # noqa: E731
    place(fx, c["jet_climb"], S("S01"), -10, 0.45)              # the jet sweeps past the camera
    place(fx, c["v3_whoosh_in"], E("S02"), -6, -0.12)           # the camera dives into his ear
    place(fx, c["v3_whoosh_pass"], S("S03"), -12, 0.35)         # out of the dark, down the canal
    place(fx, c["v3_whoosh_pass"], S("S04"), -9, 0.45)          # through the eardrum
    place(fx, c["v3_pluck"], S("S04m"), -14, 0.15)              # the map's labels
    place(fx, c["jet_climb"], S("S05a"), -12, 0.8)              # the jet climbs past
    place(fx, c["v3_air"], beat("S05b", "drops"), -18)          # outside air thins
    place(fx, c["v3_stretch"], beat("S06a", "pushes"), -16, 0.2)
    place(fx, c["v3_stretch"], beat("S06b", "bulges") + 6, -8)  # the bulge (shape key rising to word+12)
    place(fx, c["v3_pluck"], beat("S06b", "bulges"), -16)       # badge
    fk = beat("S08b", "cracks")
    place(fx, c["v3_valve"], fk + 2, -5)                        # the valve parts (key fk-2 -> fk+10)
    place(fx, c["v3_air"], beat("S09a", "escapes"), -9)         # air escapes down the tube
    place(fx, c["v3_whip"], E("S09a") - 3, -9)                  # whip up into the POP shot
    fpop = beat("S09b", "pop")
    place(fx, c["v3_pop"], fpop + 1, -1)                        # POP: the eardrum snaps flat (keys pop-1 -> pop+3)
    place(fx, c["ear_pop"], fpop + 1, -10)                      #   with the softer generated pop under it
    place(fx, c["gear_down"], S("S10"), -9, 0.9)                # the landing gear
    place(fx, c["v3_thud"], beat("S11a", "shut") + 8, -12)      # the tube clamps shut, turns red
    place(fx, c["v3_stretch"], beat("S11b", "inward") + 4, -9)  # eardrum pushed in (keys word-6 -> word+14)
    place(fx, c["v3_pluck"], beat("S11b", "inward"), -16)       # badge
    fs, fy, fc = (beat("S12a", w) for w in ("swallowing", "yawning", "chewing"))
    place(fx, c["v3_swallow"], fs + 4, -9)                      # swallow face key at word+4
    place(fx, c["v3_yawn"], fy - 2, -12)                        # yawn opens from word-2 to word+10
    for i in range(4):                                          # chew keys at word+7+8i (real_max.perform)
        place(fx, c["v3_chew"], fc + 7 + i * 8, -14)
    fu, fr = beat("S12b", "pull"), beat("S12b", "open")
    place(fx, c["v3_valve"], fu + 1, -8)                        # the tube opens again
    place(fx, c["v3_air"], fu + 4, -14)                         # cabin air rises into the middle ear
    place(fx, c["v3_pop"], fr + 2, -8)                          # the eardrum settles flat
    place(fx, c["v3_pluck"], fr, -16)                           # badge
    place(fx, c["outro_chime"], S("S13") + 8, -14)              # follow card
    return fx


def music(n, vo, speech_db):
    m = decode(HERE / "audio" / "bgm" / "investigations.mp3")[:n]
    m = np.pad(m, (0, n - len(m)))
    w = int(0.4 * SR)                                  # loudness of the music while it plays (0.4 s windows)
    m_level = 20 * np.log10(np.percentile(np.sqrt(np.convolve(m ** 2, np.ones(w) / w, mode="valid")), 70))
    m = m * db(speech_db - MUSIC_UNDER - m_level)
    # duck 3 dB while he speaks (attack ~30 ms, release ~250 ms)
    talk = np.convolve(np.abs(vo), np.ones(int(0.03 * SR)) / int(0.03 * SR), mode="same") > 0.02
    g = np.where(talk, db(-3), 1.0)
    g = np.convolve(g, np.ones(int(0.25 * SR)) / int(0.25 * SR), mode="same")
    # dip 9 dB for 0.25 s before the POP (silence before the payoff), back up after it
    pop = int(t_of(beat("S09b", "pop")) * SR)
    dip = np.ones(n)
    a, b = pop - int(0.25 * SR), pop + int(0.35 * SR)
    dip[a:b] = db(-9)
    dip = np.convolve(dip, np.ones(int(0.06 * SR)) / int(0.06 * SR), mode="same")
    fade = np.ones(n)                                   # fade out over the end card
    f0 = int(t_of(SHOT["S13"]["start"]) * SR)
    fade[f0:] = np.linspace(1, 0, n - f0) ** 1.5
    fade[:int(0.3 * SR)] = np.linspace(0, 1, int(0.3 * SR))
    return m * g * dip * fade


def muffle(bus, n):
    dull = ffmpeg_filter(bus, "lowpass=f=450,lowpass=f=450")
    wet = np.zeros(n)
    ramp = int(0.12 * SR)
    for sid in MUFFLED:
        a, b = int(t_of(SHOT[sid]["start"]) * SR), int(t_of(SHOT[sid]["end"] + 1) * SR)
        w = np.ones(b - a)
        w[:ramp], w[-ramp:] = np.linspace(0, 1, ramp), np.linspace(1, 0, ramp)
        wet[a:b] = w
    return bus * (1 - wet) + dull * wet * 1.4


def write(path, mono, two_pass=True):
    raw = Path(str(path) + ".f32")
    raw.write_bytes(np.repeat(mono.astype(np.float32)[:, None], 2, axis=1).tobytes())
    af = "aresample=48000"
    if two_pass:   # measure, then normalise linearly to -14 LUFS / -1.5 dBTP
        r = subprocess.run(["ffmpeg", "-hide_banner", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", str(raw),
                            "-af", "loudnorm=I=-14:TP=-1.5:LRA=7:print_format=json", "-f", "null", "-"],
                           capture_output=True, text=True).stderr
        st = json.loads(r[r.rindex("{"):])
        af = (f"loudnorm=I=-14:TP=-1.5:LRA=7:measured_I={st['input_i']}:measured_TP={st['input_tp']}:"
              f"measured_LRA={st['input_lra']}:measured_thresh={st['input_thresh']}:offset={st['target_offset']}:"
              "linear=true,aresample=48000")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", str(raw),
                    "-af", af, "-c:a", "pcm_s16le", str(path)], check=True)
    raw.unlink()


def main():
    a = sys.argv[1:]
    out = Path(a[0] if a else HERE.parent.parent / "out" / "final" / "mix.wav")
    n = int(t_of(PLAN["frame_end"] + 1) * SR)
    voice = ffmpeg_filter(decode(HERE / PLAN["voice"]), VOICE_CHAIN)
    vo = np.zeros(n)
    vo[: min(n, len(voice))] = voice[:n]
    w = int(0.4 * SR)
    speech_db = 20 * np.log10(np.percentile(np.sqrt(np.convolve(vo ** 2, np.ones(w) / w, mode="valid")), 85))
    fx = foley(n) * db(speech_db - 20 * np.log10(0.25))      # cue gains are relative to the voice's speech level
    mus = music(n, vo, speech_db)
    cabin = decode(HERE / "audio/beds/cabin.mp3")
    tone = np.zeros(n)
    for s in PLAN["shots"]:                                   # a very low cabin tone in the cabin shots only
        if s["set"] == "cabin":
            i, j = int(t_of(s["start"]) * SR), min(n, int(t_of(s["end"] + 1) * SR))
            seg = np.tile(cabin, (j - i) // len(cabin) + 1)[: j - i]
            tone[i:j] = seg / rms(cabin) * db(speech_db - 34)
    bus = muffle(fx + mus + tone, n)
    write(out, vo + bus)
    if "--stems" in a:
        d = Path(a[a.index("--stems") + 1])
        d.mkdir(parents=True, exist_ok=True)
        for name, x in (("voice", vo), ("music", mus), ("foley", fx)):
            write(d / f"{name}.wav", x, two_pass=False)
    print(f"[mix] {out}: {n / SR:.1f} s; voice + music ({MUSIC_UNDER} dB under) + {len(PLACED)} Foley hits "
          f"on picture beats; muffle in {', '.join(MUFFLED)}")


if __name__ == "__main__":
    main()
