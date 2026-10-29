# Animated explainer Shorts

Narrated, captioned 9:16 Shorts, generated fully in code: original character
and art (skia), offline neural voice (Piper), procedural music and sound
effects. There are no stock assets, so nothing can trigger a Content ID claim.

```
shorts/engine.py    reusable engine: TTS, word-timed captions, audio mix + ducking,
                    -14 LUFS mastering, frame rendering -> ffmpeg
shorts/ear_pop.py   Short #1 "Why do your ears pop on a plane?" (script + scenes)
```

## Run

```bash
pip install piper-tts skia-python numpy      # skia needs libegl1 on Linux
# Voice: en_US-joe-medium (dataset licence CC0, safe for monetized videos)
curl -LO https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/joe/medium/en_US-joe-medium.onnx
curl -LO https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/joe/medium/en_US-joe-medium.onnx.json

python3 shorts/ear_pop.py --voice en_US-joe-medium.onnx --out out/ear_pop.mp4
python3 shorts/ear_pop.py --voice en_US-joe-medium.onnx --preview 1 10 28   # PNG stills only
```

Render time is about 2.5 minutes on 4 CPU cores for the 42-second short.

> **Voice licences matter.** Many Piper voices (e.g. `ryan`, `lessac`,
> `hfc_male`) are trained on **non-commercial** datasets. Check the
> `MODEL_CARD` before using a voice on a monetized channel.
> `joe` (CC0) and `john`/`norman` (public-domain LibriVox) are safe.

### ElevenLabs voice (natural narration, your own cloned voice)

Every script accepts `--voice elevenlabs:<VOICE_ID>` in place of a Piper model:

```bash
export ELEVENLABS_API_KEY=...            # better: an environment secret, never commit it
python3 shorts/ear_pop.py --voice elevenlabs:<VOICE_ID> --out out/ear_pop_11labs.mp4
```

- **Voice ID:** ElevenLabs → Voices → your voice → copy the voice ID.
- **Captions sync exactly:** the API's character timestamps replace the estimated word timings.
- **One take:** the whole script is one request, split back into lines at the pauses, so pitch and
  pacing stay consistent (per-line requests drifted, e.g. a much higher-pitched first line).
- **Level-matched:** speech is normalized to -18 dBFS RMS before mixing, so music sits the same under any voice.
- **No double spending:** responses are cached in `<work>/tts_cache/`, so re-renders cost nothing.
- **Tuning:** `ELEVENLABS_MODEL` (default `eleven_multilingual_v2`) and `ELEVENLABS_SPEED` (default `1.05`).
- **Rights:** use a paid ElevenLabs plan for commercial (monetized) use.

## 3D version (Blender)

```
shorts/blender/ear_pop_3d.py   headless Blender plate renderer: plane, cabin + character, ear cross-section
shorts/blender/ear_states.py   shot list + ear states, shared by Blender and the 2D HUD
shorts/ear_pop_3d.py           TTS -> Blender plates per line -> plates + HUD + captions + audio -> MP4
```

Everything in the 3D scenes is built procedurally (no downloaded models or
textures). Each line's plate is a PNG sequence exactly as long as that line;
`engine.plate_scene` / `engine.Plate` play it back under the usual HUD and
captions. Blender also writes `anchors.json` (screen positions of 3D points)
so 2D labels and the POP! burst follow the camera.

```bash
brew install ffmpeg && brew install --cask blender   # macOS; Blender 4.2+ (EEVEE Next)
python3 -m venv .venv && .venv/bin/pip install piper-tts skia-python numpy
# Inter font (OFL) in <repo>/fonts on macOS: Inter-Black.otf, Inter-ExtraBold.otf
.venv/bin/python shorts/ear_pop_3d.py --voice voices/en_US-joe-medium.onnx \
    --res 540x960 --samples 16 --lines 0 1 8 --out out/test.mp4      # quick low-res test
.venv/bin/python shorts/ear_pop_3d.py --voice voices/en_US-joe-medium.onnx --out out/ear_pop_3d.mp4
# one line by hand:
blender -b -P shorts/blender/ear_pop_3d.py -- --line 5 --out out/l5 --res 540x960 --seconds 3 --stills 3
```

Plates are cached in `out/ear_pop_3d_work/plates/<res>/` and re-rendered only
when a line's length changes. Set `BLENDER=/path/to/blender` if it isn't on PATH.

## Making the next short

Copy `ear_pop.py` and change two things:
1. **The script:** a list of `Line(text, scene, sfx)`. Keep each line to one
   idea of 1–4 seconds. The first line is the hook and must land within 1 second.
2. **The scenes:** `scene(canvas, t, dur, ctx)` draws one frame. `t` is the
   time into the line, and `word_at(ctx, "word")` gives the moment a word is
   spoken, so visuals and sound effects can hit exactly on it.

Formula that works in this niche: **hook question → "here's what happens
inside" → step-by-step visual change per sentence → payoff moment (POP!) →
twist ("landing is worse") → practical takeaway → follow CTA**, in 35–50 s.

## Upload metadata for Short #1

- **Title:** `Why Your Ears Pop on a Plane ✈️👂 #shorts`
- **Description:**
  ```
  That "pop" is your Eustachian tube equalizing the air pressure behind your eardrum.
  Here's exactly what happens on takeoff - and why landing is worse.

  Animation & narration: original, made by [channel]. Educational content.
  #shorts #science #humanbody #didyouknow #airplane
  ```
- **Pinned comment:** `Which is worse for you - takeoff or landing? 👇`
- **Not "made for kids"**, and no altered/synthetic disclosure needed (it's a
  stylised cartoon, not realistic footage).
