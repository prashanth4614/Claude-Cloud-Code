#!/usr/bin/env python3
"""Pilot audio: voice take (Gate A), SFX + ambience beds, music, per PIPELINE.md.

  python3 shorts/pilot_ear_pop/audio.py voice        # one ElevenLabs v3 take of the whole script
  python3 shorts/pilot_ear_pop/audio.py sfx          # generate missing SFX cues + beds (cached)
  python3 shorts/pilot_ear_pop/audio.py music-test   # 3 s probe: does the plan include ElevenLabs Music?

Outputs go to shorts/pilot_ear_pop/audio/. Every generation is cached, so re-runs never re-spend.
"""
import json
import sys
import wave
from pathlib import Path

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from engine import SR, decode, elevenlabs_post, elevenlabs_script, ffmpeg_filter  # noqa: E402

OUT = HERE / "audio"
WORK = HERE.parent.parent / "out" / "pilot_ear_pop_work"  # caches + alignment (gitignored)
SCRIPT = yaml.safe_load((HERE / "script.yaml").read_text())
# Gentle narration polish: rumble cut, soft de-ess, light compression, streaming level.
VOICE_CHAIN = ("highpass=f=80,deesser=i=0.35:m=0.5:f=0.5,"
               "acompressor=threshold=-21dB:ratio=2.2:attack=12:release=180:makeup=1.5,"
               "loudnorm=I=-16:TP=-1.5:LRA=8")


def write_wav(path, x):
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype("<i2").tobytes())


def speech_match(audio, script_text):
    """Fraction of script words Whisper hears in the audio, in order (0..1)."""
    import difflib
    import re

    from faster_whisper import WhisperModel
    a16 = np.interp(np.linspace(0, len(audio) - 1, int(len(audio) * 16000 / SR)),
                    np.arange(len(audio)), audio).astype(np.float32)
    segs, _ = WhisperModel("small.en", device="cpu", compute_type="int8").transcribe(a16, language="en")
    words = lambda t: re.sub(r"[^a-z ]", "", t.lower()).split()  # noqa: E731
    return difflib.SequenceMatcher(None, words(script_text), words(" ".join(x.text for x in segs))).ratio()


def take_parts(voice_id):
    """Audio + word spans for every script line, from the takes named in its `take:` field.
    Take 1 is the approved recording (takes/take1.json; its ElevenLabs response is cached, so it
    costs nothing); take 2 holds only the rewritten lines, so a rewrite never re-records the rest."""
    take1 = json.loads((HERE / "takes" / "take1.json").read_text())
    new = [(ln["spoken"], ln["caption"]) for ln in SCRIPT["lines"] if ln["take"] == [2]]
    t1 = elevenlabs_script([(x["spoken"], x["caption"]) for x in take1], voice_id, WORK)
    t2 = iter(elevenlabs_script(new, voice_id, WORK / "take2") if new else [])
    parts = []
    for ln in SCRIPT["lines"]:
        a, spans = t1[ln["take"][1] - 1] if ln["take"][0] == 1 else next(t2)
        if "until" in ln:   # keep the line only up to that word (plus a short breath)
            k = next(i for i, (w, _, _) in enumerate(spans) if w.strip(".,!?").lower() == ln["until"].lower())
            spans = spans[:k + 1]
            a = a[: int((spans[-1][2] + 0.12) * SR)]
            fade = min(len(a), int(0.03 * SR))
            a = a.copy()
            a[-fade:] *= np.linspace(1, 0, fade)
        if [w for w, _, _ in spans] != ln["caption"].split():
            raise SystemExit(f"caption doesn't match its take's words: {ln['caption']}")
        parts.append((a, spans))
    return parts


def voice():
    lines = [(ln["spoken"], ln["caption"]) for ln in SCRIPT["lines"]]
    voice_id = SCRIPT["voice"].split(":", 1)[1]
    WORK.mkdir(parents=True, exist_ok=True)
    (WORK / "take2").mkdir(exist_ok=True)
    parts = take_parts(voice_id)
    gap = np.zeros(int(0.28 * SR), dtype=np.float32)  # breath between lines, like the edit
    pauses = [np.zeros(int(ln.get("pause_after", 0) * SR), dtype=np.float32) for ln in SCRIPT["lines"]]
    take = np.concatenate([p for (a, _), extra in zip(parts, pauses) for p in (a, gap, extra)])
    polished = ffmpeg_filter(take, VOICE_CHAIN)
    score = speech_match(polished, " ".join(cap for _, cap in lines))
    if score < 0.9:  # never hand over a take that isn't the script (e.g. a broken filter)
        raise SystemExit(f"QA failed: transcript matches the script only {score:.0%}; not writing voice_take.wav")
    print(f"QA: transcript matches script {score:.0%}")
    write_wav(OUT / "voice_take.wav", polished)
    report = []
    for i, ((a, spans), ln) in enumerate(zip(parts, SCRIPT["lines"]), 1):
        d = len(a) / SR
        report.append({"line": i, "seconds": round(d, 2), "words": len(spans), "caption": ln["caption"]})
        print(f"{i:2d}  {d:5.2f}s  {len(spans):2d} words  {ln['caption']}")
    (OUT / "voice_take.json").write_text(json.dumps(report, indent=1))
    # Absolute timing of every line and word inside voice_take.wav (drives the Blender build).
    t, timing = 0.0, []
    for (a, spans), ln, extra in zip(parts, SCRIPT["lines"], pauses):
        timing.append({"start": round(t, 3), "end": round(t + len(a) / SR, 3), "caption": ln["caption"],
                       "words": [[w, round(t + s, 3), round(t + e, 3)] for w, s, e in spans]})
        t += (len(a) + len(gap) + len(extra)) / SR
    (OUT / "voice_timing.json").write_text(json.dumps({"total": round(len(take) / SR, 3), "lines": timing}, indent=1))
    print(f"total {len(take) / SR:.1f}s -> {OUT / 'voice_take.wav'}")


def sfx():
    jobs = [(f"sfx/{k}", v, False) for k, v in SCRIPT["sfx_cues"].items()] + \
           [(f"beds/{k}", v, bool(v.get("loop"))) for k, v in SCRIPT["beds"].items()]
    for name, spec, loop in jobs:
        dest = OUT / f"{name}.mp3"
        if dest.exists():
            print(f"cached  {name}")
            continue
        body = {"text": spec["prompt"], "duration_seconds": spec["seconds"], "prompt_influence": 0.45}
        if loop:
            body["loop"] = True
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(elevenlabs_post("/v1/sound-generation?output_format=mp3_44100_128", body))
        a = decode(dest)
        peak = 20 * np.log10(np.abs(a).max() + 1e-9)
        print(f"made    {name:18s} {len(a) / SR:5.2f}s  peak {peak:5.1f} dBFS")


def music_test():
    dest = OUT / "music_test.mp3"
    body = {"prompt": SCRIPT["music"]["prompt"], "music_length_ms": 3000}
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(elevenlabs_post("/v1/music", body))
    print(f"music available: {len(decode(dest)) / SR:.1f}s test clip -> {dest}")


if __name__ == "__main__":
    {"voice": voice, "sfx": sfx, "music-test": music_test}[sys.argv[1]]()
