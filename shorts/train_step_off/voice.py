"""Voice for "Why you fall stepping off a slow train" (G4): the owner's ElevenLabs clone, one take.

    python3 shorts/train_step_off/voice.py audition      # lines 1-2 at stability 0.0 and 0.5 (2 x 169 chars)
    python3 shorts/train_step_off/voice.py full 0.5      # the whole locked script in ONE take (668 chars)

Writes shorts/train_step_off/voice/<name>.mp3 (a review copy for the owner's phone) and, for the full
take, take_<stab>.wav plus timings_<stab>.json (per-line word spans) in out/train_step_off/voice/.
Responses are cached (engine.elevenlabs_script), so re-running costs no credits.
The script text is LOCKED at G2 (script.md); change it only by reopening G2.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "shorts"))
import engine  # noqa: E402

VOICE = "x5ld1ovD8agu3EPB7Qpj"     # the owner's clone (CLAUDE.md)
# (spoken with v3 tags and stress caps, caption text)
LINES = [
    ("[curious] Getting off a slow train looks EASY. Physics disagrees.",
     "Getting off a slow train looks easy. Physics disagrees."),
    ("At ten kilometres an hour it looks like a crawl, but that's more than twice a comfortable walking pace.",
     "At ten kilometres an hour it looks like a crawl, but that's more than twice a comfortable walking pace."),
    ("That's because when your shoe grips, your foot slows sharply, while your upper body keeps moving.",
     "That's because when your shoe grips, your foot slows sharply, while your upper body keeps moving."),
    ("So facing backward, you can tip backward, the way you can't see.",
     "So facing backward, you can tip backward, the way you can't see."),
    ("Facing sideways, you're still moving along the platform, which can throw you off balance.",
     "Facing sideways, you're still moving along the platform, which can throw you off balance."),
    ("[serious] Facing forward, a few quick steps can spread out the slowdown, but you can still lose your BALANCE.",
     "Facing forward, a few quick steps can spread out the slowdown, but you can still lose your balance."),
    ("One wet patch, one bag, one crowded step, and the GAP is right there.",
     "One wet patch, one bag, one crowded step, and the gap is right there."),
    ("[warm] So wait until the train has completely STOPPED, even if...",
     "So wait until the train has completely stopped, even if"),
]
OUT = ROOT / "out" / "train_step_off" / "voice"
REVIEW = ROOT / "shorts" / "train_step_off" / "voice"


def take(lines, stab, name):
    os.environ["ELEVENLABS_STABILITY"] = str(stab)
    work = OUT / name
    work.mkdir(parents=True, exist_ok=True)
    parts = engine.elevenlabs_script(lines, VOICE, work)
    REVIEW.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(work / "take.mp3"), "-b:a", "96k",
                    str(REVIEW / f"{name}.mp3")], check=True)
    return work, parts


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "audition"
    print("characters per full take:", len(" ".join(sp for sp, _ in LINES)))
    if mode == "audition":
        for stab in (0.0, 0.5):
            take(LINES[:2], stab, f"audition_stab{stab}")
        print("auditions written to", REVIEW)
    elif mode == "full":
        stab = float(sys.argv[2])
        work, parts = take(LINES, stab, f"full_stab{stab}")
        audio = __import__("numpy").concatenate([a for a, _ in parts])
        import soundfile as sf
        sf.write(str(work / "take.wav"), audio, engine.SR)
        spans = [[(w, round(s, 3), round(e, 3)) for w, s, e in sp] for _, sp in parts]
        (work / "timings.json").write_text(json.dumps({"lines": [c for _, c in LINES], "spans": spans,
                                                        "line_seconds": [round(len(a) / engine.SR, 3) for a, _ in parts]}, indent=1))
        print("full take:", work, "lines (s):", [round(len(a) / engine.SR, 2) for a, _ in parts])
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
