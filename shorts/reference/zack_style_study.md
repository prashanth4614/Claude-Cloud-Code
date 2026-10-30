# Zack D Films style study: sound + animation (2026-10-30)

Three @zackdfilms Shorts, played once each in Chrome via `shorts/tools/yt_reference.py`.
For each one: screenshots of the player every 0.25 s, plus the `<video>` element's own audio recorded with
MediaRecorder. The recordings were analysed locally and then deleted; nothing from YouTube is in the repo.

| id | title | length | views |
|---|---|---|---|
| XQhwDDoaBpg | Why Your Ears Pop On A Plane | 33.1 s | 11M |
| rQfkiCPT4Rg | Why Eardrums Burst From Loud Noises | 32.0 s | 28M |
| Q6Lreosjz0g | How Eyewash Stations Work | 29.0 s | 81M |

**Method.** I split voice from everything else with demucs (htdemucs, two stems). Levels use the same
measures as `mix.py`:
- **speech level**: 85th percentile of 0.4 s RMS on the voice stem;
- **voice peak**: 99.99th percentile of |voice|;
- **background level**: 70th percentile of 0.4 s RMS.

Our own mix went through the same steps (`mix.py` at HEAD 4e7c61a; music on).

Caveats:
- demucs leaks a little between stems, so treat background numbers as ±2 dB.
- All three captures measure exactly -14.0 LUFS, so YouTube's playback normalisation is in the capture.
  The real masters are -14 LUFS or louder.

## 1. Sound: numbers

| | Ears Pop | Eardrum Burst | Eyewash | **ours (pilot)** |
|---|---|---|---|---|
| Integrated (as played) | -14.0 LUFS | -14.0 | -14.0 | -14.0 |
| Share of runtime with voice | 92 % | 92 % | 91 % | **72 %** |
| Voice starts / ends before the end | 0.00 s / 0.48 s | 0.00 / 0.10 | 0.00 / 0.50 | 0.02 / **1.75 s** |
| Background (music + SFX + beds) vs speech | **-19 dB** | -7.5 dB (sub booms) | **-20 dB** | **-26 dB** |
| Background during words vs in the gaps between them (ducking) | +0.3 dB | 0.0 dB | +0.3 dB | **+2.7 dB** |
| SFX-like onsets per 10 s (background rises > 8 dB) | 7.9 | 10.6 (incl. rhythmic booms) | 5.9 (incl. music notes) | 5.9 (28 cues) |
| Typical SFX peak vs voice peak (median) | -17.5 dB | -10 to -16 dB | -17 dB | **≈ -20.5 dB** (cue gains) |
| Biggest accent vs voice peak | POP **-3 dB** | sub boom **0 dB** (hook) | water impact **-10 dB** | POP -4 dB |
| Silence (mix < -50 dBFS) | 0.1 % | 0.6 % (only the last 0.4 s) | 0.8 % (only the last 0.4 s) | – |
| Background spectrum | 20–150 Hz dominant (rumbles, whooshes) | almost all < 150 Hz | music 150–600 Hz | – |

### What the measurements show

- **Voice wall to wall.** Narration runs 91–92 % of the time, and the gaps between sentences are only
  0.1–0.25 s. The voice starts on frame 0 and stops 0.1–0.5 s before the loop point. There is no outro
  card with silence.
- **No ducking.** The background level is the same under words and in the gaps between them (≤ 0.3 dB
  difference). It is simply set about 19–20 dB under the speech and stays there.
- **Music.**
  - Ears Pop and Eardrum Burst have no musical score. Their background is sound design: low rumbles,
    whooshes and swells, plus one sustained ~1.4 kHz tone under the "pressure difference" section
    (14.6–17.5 s), and a ringing tone after the rupture (Eardrum Burst, from ~20 s).
  - Eyewash uses licensed music (the music credit is shown on screen). It sits about 20–23 dB under the
    speech, steady and melodic in the mids (150–600 Hz).
- **Dip before the payoff (all three).** The background drops about 10 dB for 0.25–0.4 s right before the
  big hit, then the hit lands:

  | Short | Dip before | Hit |
  |---|---|---|
  | Ears Pop | 25.55–25.75 s, -28…-31 dB vs speech (normally -19) | POP at 25.95 s, background jumps to -2 dB vs speech |
  | Eyewash | 4.95–5.25 s, -29…-33 dB (normally -18) | water impact at 5.5 s, -4 dB vs speech |
  | Eardrum Burst | 17.05–17.3 s, -21 dB (normally -12) | "which ruptures" at 17.4 s, -10 dB |

  Our `pop_dip` (-9 dB for 250 ms) already matches this.
- **A whoosh on almost every cut.** In Ears Pop, 9 of the 13 cuts have a whoosh, swish or rumble
  starting within ±0.3 s of the cut. In each video the loudest moments are the hook and the one physical
  payoff.
- **Loud hook.** In the first 1.8 s of Eardrum Burst, sub-bass booms (every 0.6 s, in time with the
  on-screen sound-wave rings) sit 5–7 dB above the speech RMS, and their peaks reach the voice peaks.
  Ears Pop opens with the jet passing close to camera, then a whoosh at 1.5 s at -10 dB vs the voice peak.
- **Room tone never stops.** The background floor (10th percentile per second) stays between -19 and
  -40 dB vs speech the whole time. Nothing drops out at cuts; there is only true silence in the last
  0.4 s before the loop.

## 2. Recommendations for `mix.py`

All levels are relative to the voice, in the units `mix.py` already uses.

1. **Raise the background about 5 dB overall.**
   - Ours is -26 dB vs speech; theirs is -19/-20.
   - `MUSIC_UNDER` 21 → **17**.
   - `BED_UNDER` each about 4 dB louder: cabin 26, ear 28, sky 28, city 30.
   - `PRESSURE_UNDER` 24 → **20**.
   - Check the voice still reads on a phone speaker.
2. **Remove the word ducking.** In `music()`, change `duck(n, -3)` to `duck(n, 0)` (or -1 at most). They
   don't duck; the bed stays constant and sits low enough.
3. **Raise routine SFX about 3 dB.** Their median is -17 dB under the voice peak; ours is about -20.5.
   - Cues now at -24/-26/-28 → -20/-22/-24.
   - Whoosh into the ear (`v3_whoosh_in`, end of S02) -16 → **-10**.
   - Keep the POP at -4 (theirs: -3).
4. **Hook: hit harder in the first 1–2 s.**
   - `jet_climb` at S01: -18 → about **-8**, with plenty of 40–150 Hz.
   - Optionally a low boom on frame 0 of S00 at about -6.
5. **A whoosh on every change of world** (cabin ↔ ear ↔ sky ↔ city), at -16 to -20 and low-weighted.
   This applies to cuts that don't have one yet, e.g. S04→S04m, S07, S09c, S10, S12a, S13.
6. **Keep the pre-payoff dip** (`pop_dip` -9 dB / 250 ms), and add one before the second payoff
   (S12b "open") and before the S11a thud: -8 dB for 0.25 s.
7. **Add a low end to the background.** Their beds are mostly 20–150 Hz. Ours high-pass the beds at
   60 Hz; drop that to about 35 Hz for the ear and pressure worlds.
8. **Timing (in `audio.py`/script, not `mix.py`).**
   - Gaps between lines 0.28 s → **0.12–0.15 s**, and cut most `pause_after`.
   - End the audio ≤ 0.5 s after the last word: our S13 card plus tail is 1.75 s.
   - Target voice share ≥ 85 % and a runtime of 30–35 s (ours: 47 s).
9. Keep the -14 LUFS target and the continuous beds; both already match.

## 3. Animation

### Shot length and cuts (from the 0.25 s screenshots)

| | shots | mean | range | cuts / 10 s |
|---|---|---|---|---|
| Ears Pop | ≈14 | 2.4 s | 0.5–6.3 s | 3.9 |
| Eardrum Burst | 5 | 6.4 s | 3.5–14.8 s | 1.25 |
| Eyewash | ≈12 | 2.4 s | 0.9–4.7 s | 3.8 |
| **ours** | 22 | 2.15 s | 0.6–4.1 s | 4.4 |

Each video has **one or two long anchor shots** that carry the core process with the camera moving the
whole time:
- Ears Pop: the ear cross-section 2.1–8.4 s and 16.2–21.5 s, covering the eardrum bulging.
- Eardrum Burst: 13.7–28.5 s, covering the eardrum tearing and healing in one take.

Ours has no shot longer than 4.1 s.

### Camera

- Always moving. The background of the picture changes measurably in nearly every 0.25 s step. The main
  move is a slow push-in or drift, plus slow orbits around the anatomy.
- No handheld shake anywhere.
- Fast moves happen only at transitions:
  - **whip pans** with heavy motion blur, about 0.25 s (jet → cabin window; section → pressure gauge);
  - **push-through "layer peel"**: the camera pushes into the face while skin, then muscle, then skull
    blur away, landing in the cutaway in about 0.5 s (Ears Pop 1.7–2.2 s; Eardrum Burst 13.4–13.9 s).
    The same move in reverse pulls back out to the face (Eardrum Burst 28.4–29.0 s);
  - **0.5 s cross-dissolve** for a change of place or time (section → descending jet, 26.4–27.2 s);
  - **slide wipe** with a black edge, about 0.25 s (Eardrum Burst 6.9 s).

### Characters

- One strong expression per shot, held: brows down, squint, teeth or grimace, hand pressed to the ear or
  head. The pose is exaggerated but realistic.
- Small motions only while holding the pose: head turns, blinks, the hand rubbing.
- Eardrum Burst holds the same wince for 6.5 s while sound-wave rings pass through the face.
- Actions read in under 0.5 s and are eased, not snappy; no squash and stretch.
- Endings turn to camera: Eyewash finishes on a smile and thumbs-up to the lens.

### Look

- Clean, stylised realism: soft subsurface skin, high-key soft wrap lighting, low contrast.
- No harsh rim light; light comes from the front and side.
- Saturated flat backgrounds: a sky-blue gradient, teal, or a light-blue gridded "virtual studio".
- Shallow depth of field on close-ups (blurred foreground hands and edges), and motion blur on every fast
  move.

### Inside the body

- Anatomy looks like a clean medical model: porous cream bone, glossy pink and red tissue, and yellow fat
  or nerves against the teal background, all in cross-section cutaways.
- Processes are shown literally and slowly:
  - the eardrum visibly bulges, tears and heals;
  - air is shown as rows of small translucent blue arrows;
  - the Eustachian tube glows as air travels along it;
  - a pressure-gauge graphic sits next to the ear;
  - a translucent blue arrow shows the jet's direction;
  - Eyewash shows a big green 00:00→15:00 timer.
- In-world labels are rare (one "Air pressure" label).

### Framing for 9:16

- The subject is centred and fills 60–90 % of the frame width.
- Faces sit with the eyes about 30–40 % from the top.
- Captions:
  - placement: centred at about 75 % of the height, above YouTube's own interface at the bottom;
  - style: white bold rounded sans-serif, sentence case, with a soft drop shadow, no box and no colour
    highlight;
  - chunks: 1–3 words, swapped by hard cuts 2.4–3.9 times per second, with no visible pop-in or scaling.
- Nothing important appears in the bottom 25 %.

### Hook (first 1–2 s)

The voice starts on frame 0, already mid-sentence in the topic ("As the plane climbs…", "If a super loud
noise…", "Hold open your eyelids…"). There is no title, and the picture is already mid-action:
- Ears Pop: the jet passes close to camera, then by 1.4 s a passenger grimaces with his hand to his ear;
- Eardrum Burst: a wincing face hit by sound-wave rings, with booms;
- Eyewash: an extreme close-up of chemical-burned, bleeding eyes, pulling back.

The first cut comes by 0.9–1.9 s.

### Recommendations for `build_previz.py` / `real_max.py`

1. **Merge into longer anchor shots.**
   - Merge S08a + S08b + S09a (+ S09b) into one continuous 6–8 s `ear_inside` take: bulge → tube cracks
     → air → POP. The camera does one slow push or orbit and does not cut.
   - Similarly, S06a + S06b could become one 4–5 s shot.
   - Keep quick 0.6–1.5 s cuts only for the cabin, sky and city beats.
2. **Outside → inside: replace the dip through black (S02 → S03)** with a 0.4–0.5 s push-through with
   motion blur (shutter about 0.5–1.0) where the skin and ear fade or blur away as the camera enters.
   Mirror it when coming back out (S09c, S12a).
3. **Use whip pans (0.2–0.3 s, heavy blur) for jumps sideways** (ear ↔ ear_map), and a 0.5 s
   cross-dissolve for S10 (the descent, i.e. a change of time).
4. **Camera:** a slow, constant push of about 5–10 % framing per shot. Remove `handheld`/`impulse_shake`
   except perhaps a single impulse on the POP.
5. **Max's acting.**
   - Hit a strong pained expression early in S00 (frame 0–20), with the hand to the ear, and hold it for
     the whole shot with only small head and hand motion.
   - Use eased changes of about 6–10 frames, one expression change per shot.
   - S09c relief: a big release (brows up, exhale, shoulders drop).
   - S13: Max looks to camera with a smile.
6. **Look.** Raise the key and fill (lower contrast) and use saturated plain or gradient backgrounds for
   the ear_map. Use shallow depth of field on Max close-ups (f/2–2.8 equivalent) and motion blur on.
7. **Framing.** Keep Max's eyes at 30–40 % from the top, captions at about 75 % height, and nothing key
   in the bottom 25 %.
8. **Hook.** Frame 0 should already be loud and in action: pained face plus jet boom, voice starting on
   frame 0, first cut by about 1 s.
