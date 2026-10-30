# Cloud GPU rendering (RunPod)

Renders a Short on a rented GPU, typically an RTX 4090, in about 10–15 minutes instead
of ~77 minutes on a MacBook Air, for about **$0.10–0.15 (₹10–15) per video**. The pod is
**always deleted** at the end: on success, on failure, on Ctrl+C, and when the
`--max-minutes` limit is hit. The bill is printed when it finishes.

```
cloud/render_runpod.py   driver: bundle job -> create pod -> wait for boot -> upload -> stream log -> download -> delete
cloud/bootstrap.sh       runs on the pod (ubuntu:24.04): ffmpeg, Inter fonts, Python deps, Blender 4.5 LTS
cloud/pod_agent.py       tiny token-protected job server on the pod (port 8000, via RunPod's HTTPS proxy)
```

## Measured (first real run, 2026-10-29)

Blender 3D ear-pop Short with the Piper voice, 1080×1920, 30 fps, 24 EEVEE samples:

| | |
|---|---|
| GPU | RTX 4090 24 GB, **secure** cloud at $0.89/hr (community had no 4090 free) |
| Engine | EEVEE (the NVIDIA EGL driver was present, so no Cycles fallback) |
| Boot (apt + pip + Blender 4.5.15 download) | 0.7 min |
| Render | 1299 frames in 9.3 min, **0.43 s/frame** including Blender startup per line |
| Composite + encode | 45 s → 43.3 s MP4, 20.7 MB, −15.0 LUFS |
| Billed | ~11.1 min, **~$0.165 (~₹15)** |

At community-cloud prices ($0.34/hr) the same run is about $0.06 (≈ ₹6). If no GPU in the
list is free, `POST /pods` returns HTTP 500 "no instances currently available" and no pod
is created; retry with `--cloud SECURE`.

## One-time setup

1. Create a RunPod account and add credit. $10 (≈ ₹1,050 incl. GST) covers roughly 60–80 videos.
2. RunPod console → Settings → **API Keys** → create a key.
3. Add it as an environment secret named `RUNPOD_API_KEY`, never in the repo or chat:
   - **Cloud session:** environment settings → secrets. Allow `rest.runpod.io` and `*.proxy.runpod.net`.
   - **Mac:** `echo "export RUNPOD_API_KEY='...'" >> ~/.zshrc`.

## Render the Blender 3D version

Generate the voice once locally (it's cached), so the pod never needs your ElevenLabs key:

```bash
# 1) voice + timing only (fast, cached in out/ear_pop_3d_work/tts_cache)
python3 shorts/ear_pop_3d.py --voice elevenlabs:<VOICE_ID> --lines 0 --res 108x192 --samples 1 --out /tmp/warm.mp4
# 2) render everything on the cloud GPU
python3 cloud/render_runpod.py --out out/ear_pop_3d_cloud.mp4 \
    --include out/ear_pop_3d_work/tts_cache -- \
    python3 shorts/ear_pop_3d.py --voice elevenlabs:<VOICE_ID> --out out/ear_pop_3d_cloud.mp4
```

Step 1 synthesises all 13 lines; `--lines 0` limits only the plate render. With the free
Piper voice, put the `.onnx`/`.onnx.json` inside the repo (for example `voices/`, which is
gitignored) and `--include voices`.

Useful flags:
- `--dry-run`: build the bundle and show the command, without starting a pod.
- `--engine auto|eevee|cycles`: auto uses EEVEE when the pod exposes the NVIDIA graphics
  (EGL) driver, otherwise Cycles with OptiX + denoising. Both were tested with Blender 4.5.
- `--gpu "NVIDIA GeForce RTX 4090" "NVIDIA GeForce RTX 5090"`: preference list.
  `--cloud SECURE` gives more reliable hosts at about 2× the price.
- `--max-minutes 45`: hard cost guard.

Any other command works too. Everything after `--` runs on the pod from the repo root,
for example the 2D or Three.js versions.

## Final render of the Blender pilot (Blender 5.2, all Cycles)

```bash
shorts/pilot_ear_pop/final_render.sh bench --dry-run   # plan only, no pod
shorts/pilot_ear_pop/final_render.sh bench             # 64 frames (8 per set) on 1x 4090: s/frame, look check
FINAL_SAMPLES=64 shorts/pilot_ear_pop/final_render.sh full   # every frame on 2x 4090 (falls back to 1x)
shorts/pilot_ear_pop/final_render.sh assemble          # frames + the EDIT scene's voice/SFX mix -> MP4
```

- The film is built here and packed into one .blend (~105 MB), uploaded in chunks (the HTTPS proxy
  caps request bodies at ~100 MB). The job bundle holds only the two pod scripts.
- One Blender per GPU (`CUDA_VISIBLE_DEVICES`) works through the same frame ranges; Blender's
  placeholders stop them repeating frames. No GPU usable (driver < 575 for Blender 5.2): it fails at once.
- Frames (JPEG q95) stream back to `out/final/<mode>/frames` every minute, so a lost pod costs only
  unfinished frames. Running the same mode again skips every frame already downloaded (`done.txt`).
- Three deletes: the driver's `finally`, `--max-minutes`, and a self-delete timer inside the pod
  (`POD_MAX_SECONDS`, RunPod's pod-scoped key), so the pod goes even if this session dies.
- Render settings come from `FINAL_*` env vars (see `shorts/pilot_ear_pop/render_final.py`).

## If something goes wrong

- If the driver prints `could not delete pod`, delete it in the RunPod console right away.
  A forgotten 4090 costs about $8 a day.
- Boot problems show up as `[boot] ...` lines (apt, pip and Blender download progress).
