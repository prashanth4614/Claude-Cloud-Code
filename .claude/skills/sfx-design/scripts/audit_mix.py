#!/usr/bin/env python3
"""Audit a Short's sound mix against the picture and the house targets (see ../SKILL.md).

  python3 .claude/skills/sfx-design/scripts/audit_mix.py STEMS_DIR [--plan PLAN.json] [--mix MIX.wav]

STEMS_DIR holds the stems that mix.py --stems writes: voice.wav plus any of music.wav, beds.wav,
foley.wav, pressure.wav (16-bit WAV, any rate). PLAN.json (default: shorts/pilot_ear_pop/plan.json)
gives the shots (id, start frame) and fps. Reports, each with a PASS/WARN verdict:
  1. loudness of the mix (integrated LUFS, true peak), if --mix is given;
  2. music + beds vs voice (LU), and whether the bed dips under the words (it shouldn't);
  3. each Foley hit: its loudest 100 ms vs the speech level and vs the bed under it;
  4. transitions: for every cut with a sound within 0.2 s, how far its peak is from the cut frame;
  5. sounds ringing on across a cut (a vehicle tail under the next world);
  6. clicks: short sharp transients in everything but the voice, with the shot they're in.
"""
import json
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

# targets (from the Zack D Films study, shorts/reference/zack_style_study.md, and the owner's notes)
BED_UNDER = (-21.0, -17.0)     # music + beds vs voice, LU (studied Shorts: -19 to -20)
DUCK_MAX = 1.0                 # bed under words vs gaps, dB (studied: <= 0.3; no ducking)
CUE_RANGE = (-17.0, 0.0)       # a cue's loudest 100 ms vs the speech level (owner: -13 heard, -25 "barely")
CUE_OVER_BED = 6.0             # dB a cue must clear the bed under it
SYNC_MS = 34                   # a transition peak within ~1 frame of its cut


def read(path):
    with wave.open(str(path)) as w:
        sr, ch = w.getframerate(), w.getnchannels()
        a = np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(np.float64) / 32768
    return a.reshape(-1, ch).mean(axis=1), sr


def lufs(x, sr):
    raw = np.repeat(x.astype(np.float32)[:, None], 2, axis=1).tobytes()
    r = subprocess.run(["ffmpeg", "-nostats", "-f", "f32le", "-ar", str(sr), "-ac", "2", "-i", "-",
                        "-af", "ebur128=peak=true", "-f", "null", "-"], input=raw, capture_output=True).stderr.decode()
    s = r[r.rindex("Summary"):]
    return float(s.split("I:")[1].split()[0]), float(s.split("Peak:")[1].split()[0])


def win_rms(x, n):
    return np.sqrt(np.convolve(x ** 2, np.ones(n) / n, mode="same")) + 1e-12


def db(x):
    return 20 * np.log10(x + 1e-12)


def verdict(ok):
    return "PASS" if ok else "WARN"


def main():
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    d = Path(a[0])
    plan = json.loads(Path(a[a.index("--plan") + 1] if "--plan" in a else "shorts/pilot_ear_pop/plan.json").read_text())
    fps, shots = plan["fps"], plan["shots"]
    cuts = [((s["start"] - 1) / fps, s["id"]) for s in shots[1:]]
    shot_at = lambda t: next((s["id"] for s in reversed(shots) if (s["start"] - 1) / fps <= t), shots[0]["id"])  # noqa: E731
    v, sr = read(d / "voice.wav")
    st = {k: read(d / f"{k}.wav")[0] for k in ("music", "beds", "foley", "pressure") if (d / f"{k}.wav").exists()}
    z = np.zeros_like(v)
    bed = st.get("music", z) + st.get("beds", z)
    fo = st.get("foley", z)
    w4 = int(0.4 * sr)
    speech = db(np.percentile(np.sqrt(np.convolve(v ** 2, np.ones(w4) / w4, mode="valid")), 85))
    print(f"speech level {speech:.1f} dBFS (85th pct of 0.4 s RMS)")

    if "--mix" in a:
        i, tp = lufs(read(a[a.index("--mix") + 1])[0], sr)
        print(f"[{verdict(abs(i + 14) <= 0.5 and tp <= -1.0)}] mix {i:.1f} LUFS, true peak {tp:.1f} dBTP (target -14, <= -1)")

    if bed.any():
        bl = lufs(bed, sr)[0] - lufs(v, sr)[0]
        print(f"[{verdict(BED_UNDER[0] <= bl <= BED_UNDER[1])}] music+beds {bl:.1f} LU vs voice (target {BED_UNDER})")
        talk = win_rms(v, int(0.05 * sr)) > db_to_lin(speech - 20)
        duck = db(np.sqrt(np.mean(bed[~talk] ** 2))) - db(np.sqrt(np.mean(bed[talk] ** 2)))
        print(f"[{verdict(duck <= DUCK_MAX)}] bed is {duck:.1f} dB lower under words than in the gaps (no ducking: <= {DUCK_MAX})")

    if fo.any():
        e = win_rms(fo, int(0.1 * sr))
        b = win_rms(bed, int(0.5 * sr)) if bed.any() else np.full_like(fo, 1e-9)
        hits, i = [], 0
        thr = e.max() * 10 ** (-40 / 20)
        while i < len(e):                               # one hit per burst of Foley energy
            if e[i] > thr:
                j = i
                while j < len(e) and e[j] > thr:
                    j += 1
                k = i + int(np.argmax(e[i:j]))
                if db(e[k]) > speech - 30:              # skip faint tails of a louder hit
                    hits.append(k)
                i = j + int(0.05 * sr)
            else:
                i += int(0.01 * sr)
        print(f"\nFoley hits ({len(hits)}): loudest 100 ms vs speech, vs bed")
        for k in hits:
            vs, ob = db(e[k]) - speech, db(e[k]) - db(b[k])
            ok = CUE_RANGE[0] <= vs <= CUE_RANGE[1] and (ob >= CUE_OVER_BED or not bed.any())
            print(f"  [{verdict(ok)}] {k / sr:6.2f}s {shot_at(k / sr):5s} {vs:+6.1f} dB vs speech, {ob:+5.1f} dB over bed")

        print("\nTransitions: Foley peak near each cut (only cuts with a sound on them)")
        e2 = win_rms(fo, int(0.02 * sr))
        for t, sid in cuts:
            lo, hi = int((t - 0.6) * sr), int((t + 0.6) * sr)
            seg = e2[max(0, lo):hi]
            if seg.size == 0 or db(seg.max()) < speech - 30:
                continue
            pk = (max(0, lo) + int(np.argmax(seg))) / sr
            off = 1000 * (pk - t)
            if abs(off) <= SYNC_MS:
                print(f"  [PASS] cut to {sid:5s} at {t:6.2f}s: transition peaks {off:+4.0f} ms from the cut")
            elif abs(off) <= 200:
                print(f"  [WARN] cut to {sid:5s} at {t:6.2f}s: transition misses the cut by {off:+4.0f} ms")
            else:
                print(f"  [info] cut to {sid:5s} at {t:6.2f}s: no transition sound (nearest Foley {off:+4.0f} ms)")

        print("\nTails across cuts (Foley still sounding 0.3 s after a cut, from before it)")
        for t, sid in cuts:
            before, after = e2[int((t - 0.25) * sr)], e2[min(len(e2) - 1, int((t + 0.3) * sr))]
            if db(after) > speech - 30 and db(before) > speech - 30:
                print(f"  [WARN] {t:6.2f}s into {sid}: sound runs across the cut ({db(after) - speech:+.0f} dB vs speech);"
                      " fine only if the same world continues (e.g. a match cut)")

    bg = sum(st.values()) if st else z
    hp = np.diff(bg)
    e = np.sqrt(np.convolve(hp ** 2, np.ones(int(0.002 * sr)) / int(0.002 * sr), mode="same"))
    loc = np.sqrt(np.convolve(hp ** 2, np.ones(int(0.1 * sr)) / int(0.1 * sr), mode="same")) + 1e-9
    idx = np.where((e > loc * 6) & (e > 1e-3))[0]
    clicks = [i for n, i in enumerate(idx) if n == 0 or i - idx[n - 1] > int(0.05 * sr)]
    print(f"\n[{verdict(not clicks)}] clicks in music/beds/Foley: " +
          (", ".join(f"{i / sr:.2f}s {shot_at(i / sr)}" for i in clicks) or "none"))


def db_to_lin(x):
    return 10 ** (x / 20)


if __name__ == "__main__":
    main()
