---
name: sfx-design
description: Sound design and mixing for this repo's YouTube Shorts (Zack D Films style), covering sound effects, transitions, room tone, music, voice clean-up, loudness and sync to picture. Use whenever a Short needs its sound mix built or fixed, e.g. "SFX not audible", "transition sounds off", "a tick/swish/noise at 0:16", "add music", "voice has background noise", "make the sound more professional", or when starting the mix for a new video. Not for image or video generation (paused, see CLAUDE.md).
---

# SFX design for the Shorts

The reference implementation is `shorts/pilot_ear_pop/mix.py`; for a new video, copy it next to that
video's `plan.json`. Measured targets come from `shorts/reference/zack_style_study.md` (3 Zack D
Films Shorts, measured). The pilot took mixes v2 to v11 to get here. Each rule below is a mistake the
owner caught, so don't relearn them.

## Workflow

1. **Read the picture first.** Take shot cuts from `plan.json` (`start` frames, fps) and
   action frames from the beats / shape keys / face keys (`real_max.py`, `build_previz.py`).
   - Measure motion on the rendered frames when in doubt (`out/final/full/frames`).
   - Sync a sound to what is *seen*, never to the spoken word.
2. **Build the mix with `mix.py OUT.wav --stems DIR`.**
   - It needs no re-render: mux the result onto the existing picture with
     `ffmpeg -i film.mp4 -i mix.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 256k`.
3. **Audit before the owner listens:**
   ```
   python3 .claude/skills/sfx-design/scripts/audit_mix.py DIR --mix OUT.wav --plan <video>/plan.json
   ```
   - Fix every WARN, or know why it's fine. For example, a tail across a match cut into the same world is fine.
   - Then measure the muxed MP4 too (`ebur128=peak=true`): AAC adds true-peak overshoot.
4. **Get a second opinion if needed** from Codex (`shorts/tools/ask_codex.sh`, a request in
   `shorts/tools/codex/requests/`), but check its numbers against the measured targets. Its peak-based
   levels made v6 inaudible.
5. **Deliver.**
   - Name the version and send the MP4.
   - Report what changed in plain words, with the measured numbers.
   - Commit `mix.py`, the new cue files and the prompts in `script.yaml`.
   - Never commit `out/`.

## Targets (measured; the audit checks these)

| what | target |
|---|---|
| mix loudness | -14 LUFS integrated, true peak <= -1.5 dBTP after AAC |
| music + room tone vs voice | about -19 to -20 LU, **steady: no ducking** (bed under words = bed in gaps) |
| a routine SFX (its loudest 100 ms vs the speech level) | -10 to -15 dB, and >= 6 dB over the bed under it |
| the payoff (POP) | about level with the speech; peaks a little over the voice peaks |
| transition whoosh | peak **on the cut frame** (within 1 frame); about -11 dB |
| dip before each payoff | music + bed -8 to -10 dB for the last 250 ms, back over 350 ms |
| voice share | >= 85 % of the runtime, gaps between lines 0.1-0.25 s (an edit/timing matter) |

## Rules (each one was a bug)

**Levels**
- **Normalise cues by loudness, not by peak.** Give each cue's gain against its loudest 100 ms RMS
  relative to the speech level (`Cue` in `mix.py`).
  - Peak-normalised short hits (chews, clicks, stretches) came out 25-35 dB under the voice, and the
    owner called them "barely audible".
  - The jet at -13 dB was "right"; use it as the yardstick.
- **No ducking under words.** Zack's beds stay constant. Our 3 dB duck read as "pumping".

**Sync**
- **Place every cue by its anchor:** the measured peak (or onset, for yawns and booms) inside the file,
  never the file start. ElevenLabs files put their hits 0.4-1.1 s in.

**Clean cues**
- **Give every cue a 4 ms fade-in and fade-out.** Eight generated files start mid-waveform, and each
  clicked ("tick").
- **Scan new cue files for internal clicks** before using one (`v6_swish` had a click at its peak).
  Use the audit's click scan, or the diff-spike test in it.
- **No "valve click" or "UI pluck" ticks.** Small clicky accents read as glitches, not detail. Let an
  air or swell sound carry the moment.
- **No rubbery creaks for membranes.** The owner heard "a tickle". Use a slow low pressure swell
  timed to the shape keys: `Designed(rise≈0.6-1.0, lo 200, hi 700-900)`.

**Transitions**
- **A transition is a designed swell, not a stock blip.** `Designed` in `mix.py` shapes our clean airy
  room tone (`audio/beds/v6b_ear.mp3`): it swells for `rise` s while a low-pass opens lo→hi, peaks on
  the anchor, then closes over `fall`. Presets used in v11:
  - change of world: `0.45 / 0.3 s, 500→6000 Hz`, -11 dB;
  - dive into the body: `0.7 / 0.35, 400→5000`;
  - whip pan: `0.22 / 0.2, 700→7000`;
  - descent (darker, sinks after the cut): `0.5 / 0.55, 300→2500`;
  - in-shot camera move: `0.35 / 0.3, 400→3000`, -15/-16 dB.
  - The stock ElevenLabs whooshes were 0.15 s blips; new ones came back as 70 Hz sub thumps, inaudible
    on a phone.
- **Whoosh only where the film travels to another world.** Leave out cuts to a diagram, to the host
  talking, a relief beat, the end card or a "muffled" moment. The owner called those "unnecessary swish".

**Keep sounds inside their shot**
- **Keep vehicles and long sounds inside their shot:** `place(..., since=cut, until=next_cut, fade=…)`.
  - A jet ringing 0.4 s past the cut under the whoosh sounded like "two sounds, delayed".
  - A sound entering mid-swell at full level sounds cut-and-pasted. Use `anchor="onset"` so it starts
    from its own fade-in just after the whoosh peak, and ease it out over about 0.5 s into the next cut.
  - High-pass and low-pass a roar (`filt="highpass=f=160,lowpass=f=3000"`) and keep it about 20 dB
    under the voice, so it doesn't muddy the line it sits under.

**Flow and blocked-ear moments**
- **Run room tone continuously per world** (cabin, inside the body, sky, city), crossfaded 0.7 s at
  each change of world, with high-pass 35 Hz to keep the low rumble.
  - Even out the loop (a 1 s gain rider) so the bed never "comes and goes".
  - This also masks the voice's residual hiss, which used to switch on and off with every line
    ("cut-paste feel").
- **For "muffled/blocked" moments,** low-pass the music and room tone (800 Hz, 24 dB/oct) and build a
  350-650 Hz pressure texture. Hold half-dull until the payoff, then restore over 200 ms. Keep the voice
  and Foley clear, and add no tinnitus ring.

**Voice and music**
- **Voice:** start from the raw ElevenLabs take.
  - The polish chain baked into `voice_take.wav` (de-esser plus dynamic loudnorm) made a "buffering" sound.
  - Spectral-gate the clone's steady hiss with `noisereduce`: stationary, profile from in-line word
    pauses, `prop_decrease` 0.8, `n_std_thresh_stationary` 1.5, smoothing 80 ms / 500 Hz.
  - Then a static EQ and a gentle 2:1 compressor only.
- **Music:** ElevenLabs Music, `force_instrumental`, about the video's length.
  - Brief it with timestamps: wonder, tension, suspended hold, release on the payoff, warm clarity, a
    return to the opening for a seamless loop.
  - Crossfade the end back into its opening; no ending fade.
- **Limiter at 4x oversampling** (`aresample=192000` before `alimiter`), or the POP overshoots true peak
  after AAC.

## Generating cues (ElevenLabs; the owner approved SFX/music credits, but keep it small)

- Use the endpoint `/v1/sound-generation` and record the prompt in the video's `script.yaml`
  (`sfx_cues`, `beds`). Cached files are never re-bought.
- Prompt prefix for clean hits: "Isolated close-miked dry Foley, silent studio, distinct attack, short
  decay; no music, speech, ambience or reverb."
- For beds, ask for "constant, mid-range" plus `loop: true`; plain "ambience" prompts came back as
  near-silent sub rumble (-53 to -69 LUFS).
- Measure every new file before using it:
  - length, peak, onset and anchor;
  - spectral centroid (under 150 Hz is inaudible on phones);
  - internal clicks.
- Don't use a file that fails these checks; design the sound instead (`Designed`).
- Never call image or video generation APIs (CLAUDE.md), and never print or commit a key.

## When the owner reports a problem at a timestamp

1. Convert the time to a frame and shot (`plan.json`), and list every cue audible in ±1 s: the
   `PLACED` list in `mix.py`, plus each cue's audible span.
2. Look for these, in order:
   - a tail crossing the cut;
   - a sound entering mid-swell;
   - a stock blip used as a transition;
   - a clicky file or a missing fade;
   - a level too low or too high vs the speech and the bed;
   - a sound in the voice's frequency range.
3. Fix that, rebuild, re-audit, and report the measured before and after.
