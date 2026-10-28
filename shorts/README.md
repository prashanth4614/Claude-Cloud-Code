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
> For a more human, "storyteller" voice, swap `tts()` in `engine.py` for a
> commercial TTS API (e.g. ElevenLabs) under a plan that includes commercial rights.

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
