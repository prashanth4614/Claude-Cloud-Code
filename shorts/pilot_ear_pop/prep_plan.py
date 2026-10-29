#!/usr/bin/env python3
"""shots.yaml + script.yaml + audio/voice_timing.json -> plan.json (frame-exact, for Blender).

Runs with normal Python (Blender's bundled Python has no PyYAML). The plan holds, per shot,
the film frame range (cut a few frames before the line is spoken) and the frame of every word,
so beats in the build snap to speech.
"""
import json
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
LEAD = 0.10  # cut this long before the first word of a shot


def norm(w):
    return "".join(c for c in w.lower() if c.isalnum())


def main():
    shots = yaml.safe_load((HERE / "shots.yaml").read_text())
    script = yaml.safe_load((HERE / "script.yaml").read_text())
    timing = json.loads((HERE / "audio" / "voice_timing.json").read_text())
    fps = shots["fps"]
    f = lambda sec: int(round(sec * fps)) + 1  # noqa: E731  (frame 1 = t 0)
    words = []  # (line, norm word, start sec, end sec)
    for i, ln in enumerate(timing["lines"], 1):
        words += [(i, norm(w), s, e) for w, s, e in ln["words"]]

    def word_time(line, w, which=1):
        hits = [s for li, nw, s, e in words if li == line and nw == norm(w)]
        if not hits:
            raise SystemExit(f"word '{w}' not found in line {line}")
        return hits[which - 1]

    starts = []
    for sh in shots["shots"]:
        ln = timing["lines"][sh["line"] - 1]
        t = word_time(sh["line"], sh["from_word"]) if "from_word" in sh else ln["start"]
        starts.append(0.0 if not starts else max(0.0, t - LEAD))
    end_total = timing["total"] + 0.6
    plan = {"fps": fps, "resolution": shots["resolution"], "frame_end": f(end_total), "handles": 10,
            "voice": "audio/voice_take.wav", "motifs": shots.get("motifs", {}), "shots": [],
            "captions": [{"text": ln["caption"], "start": f(ln["start"]), "end": f(ln["end"])}
                         for ln in timing["lines"]],
            "words": [{"line": li, "word": nw, "frame": f(s), "end": f(e)} for li, nw, s, e in words],
            "sfx": []}
    for k, sh in enumerate(shots["shots"]):
        t0 = starts[k]
        t1 = starts[k + 1] if k + 1 < len(starts) else end_total
        beats = []
        for b in sh.get("beats", []):
            if "word" in b:
                beats.append({"frame": f(word_time(sh["line"], b["word"])), "word": norm(b["word"]), "do": b["do"]})
            elif isinstance(b.get("at"), str):  # e.g. "pop-0.5"
                w, off = b["at"].split("-")
                beats.append({"frame": f(word_time(sh["line"], w) - float(off)), "do": b["do"]})
            else:
                beats.append({"frame": f(t0 + b["at"]), "do": b["do"]})
        plan["shots"].append({**{k2: v for k2, v in sh.items() if k2 != "beats"},
                              "start": f(t0), "end": f(t1) - 1, "beats": beats})
    for i, ln in enumerate(script["lines"], 1):
        for c in ln.get("sfx", []):
            t = word_time(i, c["word"]) if "word" in c else timing["lines"][i - 1]["start"] + c["at"]
            plan["sfx"].append({"cue": c["cue"], "frame": f(t), "file": f"audio/sfx/{c['cue']}.mp3"})
    plan["beds"] = [{"line": i, "bed": ln.get("bed", "none")} for i, ln in enumerate(script["lines"], 1)]
    (HERE / "plan.json").write_text(json.dumps(plan, indent=1))
    for s in plan["shots"]:
        print(f"{s['id']:4s} frames {s['start']:4d}-{s['end']:4d} ({(s['end'] - s['start'] + 1) / fps:4.1f}s) "
              f"{s['move']:14s} {len(s['beats'])} beats")
    print(f"film: {plan['frame_end']} frames, {len(plan['sfx'])} sfx, {len(plan['captions'])} captions -> plan.json")


if __name__ == "__main__":
    main()
