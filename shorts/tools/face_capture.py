"""Turn an ordinary video of a face into Max's ARKit-52 face curves (MediaPipe Face Landmarker).

    python3 shorts/tools/face_capture.py VIDEO.mp4 --out shorts/train_step_off/face/<beat>.json \
        [--start 1.2 --end 4.0] [--mirror] [--gain 1.3] [--sheet preview.jpg]

Writes {"fps": .., "frames": [{name: weight}, ...]} with the 52 ARKit names Max's shape keys use, smoothed
with a One-Euro filter (no jitter, fast moves kept). --gain exaggerates for phone-size readability (clamped
to 1.0). --mirror swaps Left/Right; use it for a selfie clip, so the actor's left is Max's left.
The model file is fetched once into ~/.cache/face_landmarker.task (Apache-2.0).
Sources must allow it: free stock (Pexels, Pixabay, Mixkit licences), or our own footage; never ripped
YouTube.
"""
import argparse
import json
import math
import os
import urllib.request

MODEL_URL = ("https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/"
             "face_landmarker.task")


def model_path():
    p = os.path.expanduser("~/.cache/face_landmarker.task")
    if not os.path.exists(p):
        os.makedirs(os.path.dirname(p), exist_ok=True)
        urllib.request.urlretrieve(MODEL_URL, p)
    return p


class OneEuro:
    def __init__(self, freq, mincutoff=1.5, beta=0.6, dcutoff=1.0):
        self.f, self.mc, self.b, self.dc = freq, mincutoff, beta, dcutoff
        self.x = self.dx = None

    def _a(self, cutoff):
        tau = 1.0 / (2 * math.pi * cutoff)
        return 1.0 / (1.0 + tau * self.f)

    def __call__(self, x):
        if self.x is None:
            self.x, self.dx = x, 0.0
            return x
        dx = (x - self.x) * self.f
        self.dx += self._a(self.dc) * (dx - self.dx)
        cutoff = self.mc + self.b * abs(self.dx)
        self.x += self._a(cutoff) * (x - self.x)
        return self.x


def mirror(name):
    if name.endswith("Left"):
        return name[:-4] + "Right"
    if name.endswith("Right"):
        return name[:-5] + "Left"
    return name


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--out", required=True)
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--end", type=float, default=1e9)
    ap.add_argument("--mirror", action="store_true")
    ap.add_argument("--gain", type=float, default=1.0)
    ap.add_argument("--sheet")
    a = ap.parse_args()

    import cv2
    import mediapipe as mp
    from mediapipe.tasks import python as mpt
    from mediapipe.tasks.python import vision

    opts = vision.FaceLandmarkerOptions(
        base_options=mpt.BaseOptions(model_asset_path=model_path()),
        running_mode=vision.RunningMode.VIDEO, output_face_blendshapes=True, num_faces=1)
    lm = vision.FaceLandmarker.create_from_options(opts)
    cap = cv2.VideoCapture(a.video)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    frames, thumbs, filt, i = [], [], {}, 0
    while True:
        ok, img = cap.read()
        if not ok:
            break
        t = i / fps
        i += 1
        if t < a.start or t > a.end:
            continue
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        res = lm.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb), int(t * 1000))
        if not res.face_blendshapes:
            frames.append(frames[-1] if frames else {})
            continue
        w = {}
        for c in res.face_blendshapes[0]:
            if c.category_name == "_neutral":
                continue
            n = mirror(c.category_name) if a.mirror else c.category_name
            f = filt.setdefault(n, OneEuro(fps))
            w[n] = round(min(1.0, max(0.0, f(c.score) * a.gain)), 4)
        frames.append(w)
        if a.sheet and len(frames) % max(1, int(fps / 2)) == 1:
            thumbs.append((cv2.resize(img, (240, int(240 * img.shape[0] / img.shape[1]))), w))
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump({"source": os.path.basename(a.video), "fps": fps, "start": a.start, "gain": a.gain,
               "mirror": a.mirror, "frames": frames}, open(a.out, "w"))
    found = sum(1 for f in frames if f)
    print(f"{a.out}: {len(frames)} frames at {fps:.2f} fps, face found in {found}")
    if a.sheet and thumbs:
        import numpy as np
        rows = []
        for img, w in thumbs[:12]:
            top = sorted(w.items(), key=lambda kv: -kv[1])[:3]
            cv2.putText(img, " ".join(f"{k[:10]}{v:.1f}" for k, v in top), (4, 14), cv2.FONT_HERSHEY_SIMPLEX,
                        0.33, (255, 255, 255), 1)
            rows.append(img)
        h = max(r.shape[0] for r in rows)
        rows = [cv2.copyMakeBorder(r, 0, h - r.shape[0], 0, 0, cv2.BORDER_CONSTANT) for r in rows]
        cv2.imwrite(a.sheet, np.hstack(rows))


if __name__ == "__main__":
    main()
