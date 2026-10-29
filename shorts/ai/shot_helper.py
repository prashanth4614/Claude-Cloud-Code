#!/usr/bin/env python3
"""Hands-on helper for generating shots in the ChatGPT / Gemini apps (macOS).

You stay in control of the app; this only removes the busywork:
  1. copies the next prompt to the clipboard (just paste it into ChatGPT),
  2. watches ~/Downloads, and when you save the generated image/clip it is
     moved into the shots folder as NN.png / NN.mp4,
  3. moves on to the next shot.

  python3 shorts/ai/shot_helper.py                 # all missing shots, images
  python3 shorts/ai/shot_helper.py --only 1 2 3    # just these shots
  python3 shorts/ai/shot_helper.py --motion        # Veo motion prompts for the starred shots
Press Enter to skip a shot, Ctrl+C to stop (progress is kept).
"""
import argparse
import json
import select
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent
MEDIA = {".png", ".jpg", ".jpeg", ".webp", ".mp4", ".mov"}


def copy(text):
    try:
        subprocess.run(["pbcopy"], input=text.encode(), check=True)
    except FileNotFoundError:  # not on macOS: show the prompt instead
        print(text)


def wait_for_download(folder, since):
    """Block until a finished media file newer than `since` appears, or Enter is pressed."""
    while True:
        for p in sorted(folder.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
            if p.suffix.lower() in MEDIA and p.stat().st_mtime > since:
                size = p.stat().st_size
                time.sleep(1.0)  # make sure the browser/app finished writing it
                if p.exists() and p.stat().st_size == size:
                    return p
        if select.select([sys.stdin], [], [], 1.0)[0]:
            sys.stdin.readline()
            return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompts", default=str(HERE / "ear_pop" / "prompts.json"))
    ap.add_argument("--shots", default=str(HERE / "ear_pop" / "shots"))
    ap.add_argument("--downloads", default=str(Path.home() / "Downloads"))
    ap.add_argument("--only", type=int, nargs="*")
    ap.add_argument("--motion", action="store_true", help="Veo pass: animate the starred stills")
    a = ap.parse_args()
    data = json.loads(Path(a.prompts).read_text())
    shots, downloads = Path(a.shots), Path(a.downloads)
    shots.mkdir(parents=True, exist_ok=True)

    sheet = shots.parent / "max_sheet.png"
    if not a.motion and not sheet.exists() and not a.only:
        copy(data["character_sheet"])
        print("\n=== STEP 0: character sheet ===\nPrompt copied. Paste it into ChatGPT, then download the image.")
        got = wait_for_download(downloads, time.time())
        if got:
            shutil.move(str(got), sheet.with_suffix(got.suffix.lower()))
            print(f"saved {sheet.name}")

    for s in data["shots"]:
        n = s["n"]
        if a.only and n not in a.only:
            continue
        if a.motion:
            if not s["animate"] or (shots / f"{n:02d}.mp4").exists():
                continue
            prompt = f"Animate this image: {s['motion_prompt']} Vertical 9:16, smooth, subtle motion."
            what = f"upload shots/{n:02d}.png to Veo (Gemini app or Flow), paste, download the clip"
        else:
            if any((shots / f"{n:02d}{e}").exists() for e in MEDIA):
                continue
            prompt = s["image_prompt"]
            what = "attach max_sheet.png, paste, download the image" if s["attach_sheet"] else "paste, download the image"
        copy(prompt)
        print(f"\n=== SHOT {n:02d} ===  \"{s['line']}\"\nPrompt copied -> {what}.  (Enter = skip)")
        got = wait_for_download(downloads, time.time())
        if got:
            dest = shots / f"{n:02d}{got.suffix.lower()}"
            shutil.move(str(got), dest)
            print(f"saved {dest}")
    print("\nDone. Assemble with:  python3 shorts/ear_pop_ai.py --voice <joe voice .onnx>")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped; finished shots are kept.")
