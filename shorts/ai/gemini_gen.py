#!/usr/bin/env python3
"""Generate the AI shots with the Gemini API: images (Gemini image model) and clips (Veo).

Reads shorts/ai/ear_pop/prompts.json, writes into shorts/ai/ear_pop/:
  max_sheet.png        character sheet (generated first, then used as reference)
  shots/NN.png         one still per narration line
  shots/NN.mp4         Veo clip for the starred shots (image-to-video from NN.png)
Existing files are never regenerated, so re-runs only fill gaps (and never re-spend).

  export GEMINI_API_KEY=...                      # environment secret, never commit it
  python3 shorts/ai/gemini_gen.py --list-models  # see which image/Veo models your key can use
  python3 shorts/ai/gemini_gen.py --plan         # what would be generated, no API calls
  python3 shorts/ai/gemini_gen.py --images       # character sheet + 13 stills
  python3 shorts/ai/gemini_gen.py --videos --max-videos 7
  python3 shorts/ai/gemini_gen.py --images --only 6 --force   # redo one shot
Models are configurable: GEMINI_IMAGE_MODEL, GEMINI_VEO_MODEL.
"""
import argparse
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
API = os.environ.get("GEMINI_API_BASE", "https://generativelanguage.googleapis.com/v1beta")
IMAGE_MODEL = os.environ.get("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image")
VEO_MODEL = os.environ.get("GEMINI_VEO_MODEL", "veo-3.0-fast-generate-001")


def key():
    k = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not k:
        sys.exit("GEMINI_API_KEY is not set (add it as an environment secret)")
    return k


def call(method, url, body=None, raw=False, timeout=300):
    req = urllib.request.Request(url, method=method, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"x-goog-api-key": key(), "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = r.read()
    except urllib.error.HTTPError as e:
        sys.exit(f"{method} {url.split('?')[0]} -> HTTP {e.code}: {e.read().decode()[:600]}")
    return data if raw else json.loads(data)


def b64(path):
    mime = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}[path.suffix.lower()]
    return mime, base64.b64encode(path.read_bytes()).decode()


def gen_image(prompt, out, refs=(), aspect="9:16"):
    parts = [{"text": prompt}]
    for r in refs:
        mime, data = b64(r)
        parts.append({"inline_data": {"mime_type": mime, "data": data}})
    body = {"contents": [{"parts": parts}],
            "generationConfig": {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": aspect}}}
    res = call("POST", f"{API}/models/{IMAGE_MODEL}:generateContent", body)
    for cand in res.get("candidates", []):
        for p in cand.get("content", {}).get("parts", []):
            blob = p.get("inlineData") or p.get("inline_data")
            if blob:
                out.write_bytes(base64.b64decode(blob["data"]))
                return out
    sys.exit(f"no image returned for {out.name}: {json.dumps(res)[:500]}")


def gen_video(prompt, still, out, aspect="9:16"):
    mime, data = b64(still)
    body = {"instances": [{"prompt": prompt, "image": {"bytesBase64Encoded": data, "mimeType": mime}}],
            "parameters": {"aspectRatio": aspect}}
    op = call("POST", f"{API}/models/{VEO_MODEL}:predictLongRunning", body)
    name, t0 = op["name"], time.time()
    while not op.get("done"):
        time.sleep(float(os.environ.get("GEMINI_POLL", "10")))
        op = call("GET", f"{API}/{name}")
        print(f"   ...{int(time.time() - t0)} s", flush=True)
    if "error" in op:
        sys.exit(f"Veo failed for {out.name}: {op['error']}")
    samples = op["response"]["generateVideoResponse"]["generatedSamples"]
    out.write_bytes(call("GET", samples[0]["video"]["uri"], raw=True))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--prompts", default=str(HERE / "ear_pop" / "prompts.json"))
    ap.add_argument("--out", default=str(HERE / "ear_pop"))
    ap.add_argument("--images", action="store_true")
    ap.add_argument("--videos", action="store_true")
    ap.add_argument("--max-videos", type=int, default=7, help="cost guard for Veo")
    ap.add_argument("--only", type=int, nargs="*")
    ap.add_argument("--force", action="store_true", help="regenerate even if the file exists")
    ap.add_argument("--plan", action="store_true", help="print what would be generated, no API calls")
    ap.add_argument("--list-models", action="store_true")
    a = ap.parse_args()

    if a.list_models:
        res = call("GET", f"{API}/models?pageSize=200")
        for m in res.get("models", []):
            n = m["name"].split("/")[-1]
            if any(k in n for k in ("image", "veo", "imagen")):
                print(n, m.get("supportedGenerationMethods", []))
        return

    data = json.loads(Path(a.prompts).read_text())
    out = Path(a.out)
    shots = out / "shots"
    shots.mkdir(parents=True, exist_ok=True)
    sheet = out / "max_sheet.png"
    want = [s for s in data["shots"] if not a.only or s["n"] in a.only]

    todo_img = [s for s in want if a.force or not (shots / f"{s['n']:02d}.png").exists()]
    todo_vid = [s for s in want if s["animate"] and (a.force or not (shots / f"{s['n']:02d}.mp4").exists())]
    todo_vid = todo_vid[: a.max_videos]
    if a.plan or not (a.images or a.videos):
        print(f"image model: {IMAGE_MODEL}   veo model: {VEO_MODEL}")
        print(f"character sheet: {'exists' if sheet.exists() else 'to generate'}")
        print("images to generate:", [s["n"] for s in todo_img])
        print("clips to generate: ", [s["n"] for s in todo_vid], f"(max {a.max_videos})")
        return

    if a.images:
        if not sheet.exists() or (a.force and not a.only):
            print("character sheet ...", flush=True)
            gen_image(data["character_sheet"], sheet, aspect="16:9")
        for s in todo_img:
            dest = shots / f"{s['n']:02d}.png"
            print(f"shot {s['n']:02d} ...", flush=True)
            gen_image(s["image_prompt"], dest, refs=[sheet] if s["attach_sheet"] else [])
    if a.videos:
        for s in todo_vid:
            still = shots / f"{s['n']:02d}.png"
            if not still.exists():
                print(f"shot {s['n']:02d}: no still yet, skipping clip")
                continue
            print(f"clip {s['n']:02d} (Veo) ...", flush=True)
            gen_video(s["motion_prompt"] + " Smooth, subtle motion, no text.", still, shots / f"{s['n']:02d}.mp4")
    print("done -> assemble with: python3 shorts/ear_pop_ai.py --voice <voice>")


if __name__ == "__main__":
    main()
