#!/usr/bin/env python3
"""Check a narration take against the shorts-craft voice gates before animating to it.

  python3 .claude/skills/shorts-craft/scripts/voice_check.py VOICE.wav [--hook "ears pop"] [--runtime 34]

Transcribes the take (faster-whisper small.en, word timings), then measures:
- speaking pace (wpm while speaking) and voice coverage of the runtime;
- gaps between phrases;
- pitch span p5-p95 in semitones (librosa pyin on syllable medians, so octave errors count less), per
  phrase and overall;
- the pitch jump on each phrase's most stressed word (its loudest word vs the phrase median);
- whether the ASR hears the hook phrase unprompted (e.g. "ears pop", not "ears poke").
Each gate prints PASS/WARN. The numbers are a check, never a reason to keep an unnatural take: listen on a
phone too.
"""
import sys

import numpy as np

GATES = {"wpm": (165, 185), "coverage": 0.90, "gap_max": 0.25, "span_all": 8.0, "span_phrase": 6.0,
         "stress": 4.0}


def main():
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    import librosa
    from faster_whisper import WhisperModel
    y, sr = librosa.load(a[0], sr=16000, mono=True)
    runtime = float(a[a.index("--runtime") + 1]) if "--runtime" in a else len(y) / sr
    hook = a[a.index("--hook") + 1].lower() if "--hook" in a else None
    segs, _ = WhisperModel("small.en", device="cpu", compute_type="int8").transcribe(
        y, language="en", word_timestamps=True)
    words = [(w.word.strip(), w.start, w.end) for s in segs for w in s.words]
    text = " ".join(w for w, _, _ in words)
    # phrases: split where the gap between words is > 0.12 s or at sentence punctuation
    phrases, cur = [], [words[0]]
    for prev, w in zip(words, words[1:]):
        if w[1] - prev[2] > 0.12 or prev[0][-1:] in ".?!":
            phrases.append(cur)
            cur = []
        cur.append(w)
    phrases.append(cur)
    speak = sum(p[-1][2] - p[0][1] for p in phrases)
    wpm = len(words) / speak * 60
    gaps = [b[0][1] - a_[-1][2] for a_, b in zip(phrases, phrases[1:])]
    f0, _, _ = librosa.pyin(y, fmin=60, fmax=400, sr=sr, frame_length=1024)
    t = librosa.times_like(f0, sr=sr, hop_length=256)
    rms = librosa.feature.rms(y=y, frame_length=1024, hop_length=256)[0]
    ref = np.nanmedian(f0)

    def word_pitch(w):
        m = (t >= w[1]) & (t <= w[2]) & ~np.isnan(f0)
        return 12 * np.log2(np.median(f0[m]) / ref) if m.any() else np.nan

    def word_loud(w):
        m = (t >= w[1]) & (t <= w[2])
        return rms[m].max() if m.any() else 0

    syl = np.array([word_pitch(w) for w in words])
    syl = syl[~np.isnan(syl)]
    span_all = np.percentile(syl, 95) - np.percentile(syl, 5)
    ok = lambda c: "PASS" if c else "WARN"   # noqa: E731
    print(f"transcript: {text}\n")
    print(f"[{ok(GATES['wpm'][0] <= wpm <= GATES['wpm'][1])}] pace {wpm:.0f} wpm while speaking (target {GATES['wpm']})")
    print(f"[{ok(speak / runtime >= GATES['coverage'])}] voice covers {speak / runtime:.0%} of {runtime:.1f} s (>= {GATES['coverage']:.0%})")
    big = [g for g in gaps if g > GATES["gap_max"]]
    print(f"[{ok(len(big) <= 1)}] gaps {', '.join(f'{g:.2f}' for g in gaps)} s (<= {GATES['gap_max']} s, one payoff beat allowed)")
    print(f"[{ok(span_all >= GATES['span_all'])}] pitch span {span_all:.1f} st over word medians (>= {GATES['span_all']})")
    print("\nphrase                                         span   stress jump")
    for p in phrases:
        ps = np.array([word_pitch(w) for w in p])
        ps_ok = ps[~np.isnan(ps)]
        if len(ps_ok) < 2:
            continue
        span = np.percentile(ps_ok, 95) - np.percentile(ps_ok, 5)
        k = int(np.argmax([word_loud(w) for w in p]))
        jump = (ps[k] - np.median(ps_ok)) if not np.isnan(ps[k]) else np.nan
        flag = ok(span >= GATES["span_phrase"] and (np.isnan(jump) or jump >= GATES["stress"]))
        print(f"[{flag}] {' '.join(w for w, _, _ in p)[:44]:44s} {span:5.1f} st  {p[k][0]} {jump:+.1f} st")
    if hook:
        print(f"\n[{ok(hook in text.lower())}] ASR hears the hook \"{hook}\" unprompted")


if __name__ == "__main__":
    main()
