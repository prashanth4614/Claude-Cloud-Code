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

## If something goes wrong

- If the driver prints `could not delete pod`, delete it in the RunPod console right away.
  A forgotten 4090 costs about $8 a day.
- Boot problems show up as `[boot] ...` lines (apt, pip and Blender download progress).
