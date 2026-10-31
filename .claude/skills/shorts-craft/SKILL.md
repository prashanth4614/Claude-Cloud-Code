---
name: shorts-craft
description: The channel's playbook for making a new 3D-animated science Short (Zack D Films level, with our own identity), covering story and script, the opening, transitions, camera, the host Max's acting, voice delivery and its gates, captions, explanation visuals, the house look and colour grade, the ending, the thumbnail and the pre-render checklist. Use when planning, writing, storyboarding, animating, voicing or reviewing ANY new Short, or when asked how to make a video "better", "more engaging" or "more like Zack D Films". Sound mixing details live in the sfx-design skill.
---

# Shorts craft: how we make a Short

Distilled from the pilot (`shorts/pilot_ear_pop`, v2-v11) and a measured study of Zack D Films:
- `shorts/reference/zack_style_study.md`: sound, animation and thumbnails, measured;
- `shorts/reference/zack_vs_ours.md`: a frame-by-frame comparison with our pilot;
- Codex reviews 008 and 009 in `shorts/tools/codex/answers/`.

Don't re-edit a published video to apply these: they are for the **next** one. Sound: the
`sfx-design` skill. Images and AI clips: CLAUDE.md (the user generates them; we write prompts).

## 0. Our identity: match Zack's clarity, look like ourselves

Zack D Films is bright, high-key sky-blue/teal, with a skin-peel entry and no music. We stand out with
these signatures, used in **every** video:

1. **House look "ink & amber"** (dark-mode science):
   - deep ink-teal worlds (backgrounds around `#0F2433`→`#16384A`);
   - warm amber/peach key light on the subject, with a cool cyan rim (`#5FD3E6`);
   - matte lifted blacks and fine grain.

   The warm subject glows out of a cool, dark world, which is the opposite of Zack's bright frames, so we
   read as ours in the feed. The alternate look `clay_sky` (warm, matte, light) is there if a topic
   needs daylight.
   - **The palette is 80% art direction, 20% grade.** Light and colour the scenes this way in Blender;
     the grade only finishes them.
   - Finish every render with `shorts/look/house_grade.py` (`frames ink_amber`, or the `.cube` LUT).
2. **Colour code, the same in every video:**
   - **cyan** = the outside world and its forces (outside air, sound, light, germs coming in);
   - **amber** = what's inside the body;
   - **coral** = tissue;
   - a **white flash** = the moment of change (the POP).

   Viewers learn it across videos; keep it consistent.
3. **Signature transition, the "lens dive":** a thin glowing ring (our POP-ring motif) opens on the body
   part, and the camera dives through it into the cutaway. Reverse it to come back out. It replaces
   Zack's skin peel. Use it once in and once out per video; never a dip through black.
4. **Signature sound, the "hear it" moment:** every video makes the viewer *feel* the phenomenon through
   sound. The pilot's muffle → clear on the POP is the model. Plan it in the script, not the mix.
5. **Max, the recurring host:**
   - exaggerated, readable reactions (thumbnail-strength, see `EAR_POP` in
     `shorts/pilot_ear_pop/thumbnail.py`);
   - pain or surprise at the start, relief and a thumbs-up at the end.
6. **The useful tip:** end on something the viewer can *do* (swallow, yawn…). Zack rarely does.
7. **Captions:** white Inter ExtraBold, at most **one amber keyword** (`#FFB547`) per chunk, centred at
   about 78% height. Never colour a whole chunk.

## 1. Story and script (lock it before any animation)

**Target:** 30-35 s, about 85-95 words, 4-7 sentences, voice over at least 90% of the runtime.

| Beat | Seconds | What |
|---|---|---|
| Hook | 0-3 | The situation **and** the felt problem, in one line. A question, or an order ("Hold open your eyelids…"). |
| Stakes | 3-6 | One felt-consequence line, true and not alarmist ("That tight, blocked feeling can really hurt"). |
| Cause | 6-14 | "That's because…": the mechanism, shown on the cutaway. |
| Twist / payoff | 14-24 | "But…/Then…": the body's fix, landing the payoff at about 65-75%. |
| Reverse or extension | 24-30 | The flip case (going down), or what goes wrong. |
| Tip + button | 30-34 | The useful tip, then a short line that loops back into the hook. |

**Writing rules:**
- Second person and present tense ("your eardrum").
- Chain the sentences with cause-and-effect connectors ("That's because", "But before it does",
  "And when").
- No definitions ("Behind your eardrum sits…"), no "Ever wondered", no call to action at the end.
- One concrete metaphor per video (a balloon, a valve), shown on screen.
- Facts checked: cite a source (MedlinePlus or similar) in the shot notes.

## 2. Opening (the first 2 s decide everything)

- **Frame 0 is already mid-action,** and the voice starts on frame 0.
- By 2 s the viewer has seen: the place (a plane climbing), the person, the felt problem (Max's
  exaggerated pain, with **hand, ear and face in frame**), and the dive inside (the lens dive).
- Hold the pain for at least 1 s; don't cut away to calm Max. The first cut comes by about 1 s.
- **Pilot lessons:**
  - the 0.6 s wince read as "sleepy";
  - by 3 s a calm Max undid the hook;
  - the tight crop hid the hand.

## 3. Transitions

- Hard cuts on the beat for most changes (about 3-4 cuts per 10 s overall).
- The **lens dive** in and out (§0.3).
- Whip pans (0.2-0.3 s, motion blur) for jumps sideways.
- A 0.5 s dissolve only for a change of **time** (landing).
- Never a dip through black. Never a tunnel with no landmarks: the viewer must always know where they
  are.

## 4. Camera

- **Look at the process from outside; don't fly through it.** Use one **persistent cross-section** of
  the anatomy, the same orientation every time (outside on screen-left).
- Slow push-ins or orbits, about 5-10% of the framing per shot. Fast motion only inside transitions.
- **One long anchor shot of 6-10 s** carries the core mechanism: bulge → release → POP in one take.
- No handheld shake, no 180° turnarounds (S04 in the pilot flipped the viewer's orientation).
- Depth of field on Max's close-ups only. The anatomy stays sharp.
- Aim for about 9-12 shots per video (the pilot had 22: too choppy, too many worlds).

## 5. Max's acting (`shorts/blender/max_expressions.py`, `real_max.py`)

- One strong expression per shot, eased in over 6-10 frames, then held with small life (blinks, a head
  drift).
- Expressions at thumbnail strength:
  - **asymmetry** reads as real (one eye shut, the other open);
  - the brows and the mouth carry the emotion.
- Only touch the 52 ARKit face units. The body's other shape keys shape Max: zeroing them broke him in
  the thumbnail tests.
- Act the hook (pain), the payoff (relief: brows up, an exhale, shoulders drop) and the tip (show the
  swallow or yawn clearly).

## 6. Voice (ElevenLabs v3, the owner's clone)

- **Record the whole script as one take** after the script is locked; don't stitch repairs.
- **Audition first:** stability 0.0 against 0.5 on about 10 s, with similarity 0.85. Then generate the
  full script with the winner.
- **Delivery:**
  - sparse tags (`[curious]`, `[warm]`, `[serious]`);
  - CAPS on the 3-5 stressed words (POP, DROPS, INWARD…);
  - commas and dashes for run-ons, not full stops.
- **Gaps:** remove the double padding (`audio.py` adds its gap on top of each take's own silence). Aim
  for 0.10-0.25 s between phrases, and one ≤0.4 s beat before the payoff.
- **Gates (check before animating):**
  ```
  python3 .claude/skills/shorts-craft/scripts/voice_check.py VOICE.wav --hook "ears pop" --runtime 34
  ```
  - pace 165-185 wpm;
  - coverage ≥ 90%;
  - pitch span ≥ 8 st overall and ≥ 6 st per phrase;
  - stressed words +4 st or more;
  - the ASR hears the hook phrase.
- The numbers are a check, not a target: also listen on a phone. The pilot measured 6.4 st, 74%
  coverage and gaps of 0.3-0.7 s, which fail the gates.

## 7. Explaining things

- **One cutaway, reused:** a side cross-section of the body part, in a medical-model look:
  - cream bone, coral tissue, against our ink-teal background;
  - **cyan** outside air, **amber** inside air (§0.2);
  - few particles.
- Animate the process **on** the cutaway (it bulges, opens, flows). Show a faint resting outline so the
  change reads.
- At most 2-3 in-world labels, plus at most one gauge or meter graphic (pressure, a timer). Translucent
  arrows for the direction of forces.
- Don't switch to a separate "diagram world": the pilot's navy diagram taught well but felt like another
  film. Fold its clarity into the cutaway.

## 8. Ending

- End on the payoff or the tip, with Max's thumbs-up or relief **within 0.5 s of the last word**.
- No "Follow" card and no silent tail: the Short should loop.
- The last line or frame should flow back into the opening (match the opening framing for a clean loop).

## 9. Thumbnail (`shorts/pilot_ear_pop/thumbnail.py` is the template)

- One clean frame in the house look:
  - Max at a thumbnail-strength reaction, as a pose for this render only;
  - or the most physical moment of the process.
- **The owner wants the question as a headline** ("WHY DO YOUR EARS POP?"): heavy caps, white plus one
  amber line, an outline and shadow, kept inside 90% of the width and within the top 25%.
- Render it locally on the Mac (Metal, 2160×3840), and output a 1080×1920 JPG for upload.

## 10. Pre-render checklist (before spending RunPod credits)

1. The script is locked and fact-checked, about 30-35 s.
2. The voice take passes `voice_check.py`, and the owner has heard it.
3. The shot list has 9-12 shots, including the hook beat (§2), one anchor shot of 6-10 s, the lens dive
   in and out, and no dip to black.
4. The scenes are lit in the house palette; the colour code is applied; the cutaway is readable at phone
   size.
5. Captions are white with one amber keyword, about 78% up, not over faces.
6. The Mac animatic (Workbench) has been reviewed by the owner. Then a RunPod `--dry-run`, then the
   render (CLAUDE.md).
7. Grade with `house_grade.py ink_amber`. The mix is done with the `sfx-design` skill and
   `audit_mix.py`. The end has no tail.
8. The thumbnail (§9) and the upload text (title, description, hashtags) are ready.
