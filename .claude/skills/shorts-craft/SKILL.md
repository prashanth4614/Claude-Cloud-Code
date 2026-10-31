---
name: shorts-craft
description: The channel's playbook for making a new 3D-animated Short on ANY curious topic (science, space, animals, machines, food, history, everyday mysteries), at Zack D Films clarity with our own identity. Covers screenplay and creative presentation devices, the one-3D-world consistency rule, aligned transitions, camera, the host Max, voice delivery and its gates, captions, the "ink & amber" house look and colour code, the ending, the thumbnail and the pre-render checklist. Use when planning, writing, storyboarding, animating, voicing or reviewing any new Short, or when asked how to make a video "better", "more engaging" or "more like Zack D Films". Sound mixing details live in the sfx-design skill.
---

# Shorts craft: how we make a Short

Distilled from the pilot (`shorts/pilot_ear_pop`, v2-v11), the owner's notes and a measured study of
Zack D Films:
- `shorts/reference/zack_style_study.md`: sound, animation and thumbnails, measured;
- `shorts/reference/zack_vs_ours.md`: a frame-by-frame comparison with our pilot;
- Codex reviews 008 and 009 in `shorts/tools/codex/answers/`.

Don't re-edit a published video to apply these: they are for the **next** one. The order of work and the
approvals: the `production-process` skill. Sound: the
`sfx-design` skill. Images and AI clips: CLAUDE.md (the user generates them; we write prompts).

The channel covers **anything the mind wonders about**, not only the human body. The pilot was an
anatomy topic; everything below is written to work for any subject.

## 0. Our identity: Zack's clarity, our own look

Zack D Films is bright, high-key sky-blue/teal, with a skin-peel entry and no music. We stand out with
these signatures, used in **every** video:

1. **House look: "ink & amber" (the owner's choice, 2026-10-31).** Dark-mode science:
   - deep ink-teal worlds (backgrounds around `#0F2433`→`#16384A`);
   - a warm amber/peach key on the subject, with a cool cyan rim (`#5FD3E6`);
   - matte lifted blacks and fine grain.

   The warm subject glows out of a cool, dark world, the opposite of Zack's bright frames.
   - **80% art direction, 20% grade.** Light and colour every scene this way in Blender (sky, walls,
     space, water: all lean ink-teal). The grade only finishes it.
   - Finish every render with `shorts/look/house_grade.py frames ink_amber` (or `shorts/look/ink_amber.cube`).
   - Daylight topics still get the treatment: a dusk or blue-hour sky, warm practical lights, cool shade.
2. **Colour code, the same in every video** (viewers learn it across videos):
   - **cyan** = forces from outside, coming in or acting on the subject: air, water, sound, light,
     signals, cold, germs;
   - **amber** = the hidden mechanism inside the subject: energy, heat, the "inside air", what the thing
     is doing;
   - **coral** = living tissue or organic matter, when there is any;
   - a **white flash** = the moment of change (the POP, the spark, the snap).
3. **Signature transition, the "lens dive":** a thin glowing ring (our POP-ring motif) opens on the
   subject, whether that's an ear, a phone, a seed, a planet or an engine. The camera dives through it
   into the hidden world, and the reverse brings it back out. Use it once in and once out per video;
   it replaces Zack's skin peel.
4. **Signature sound, the "hear it" moment:** every video makes the viewer *feel* the phenomenon through
   sound (the pilot: muffled → clear on the POP; for space, silence then a rumble; for a machine,
   inside its hum). Plan it in the script, not the mix.
5. **Max, the recurring host:** he lives the phenomenon at the start and reacts at the end (§5). The
   topic decides how big his part is, but he opens and closes every video.
6. **The takeaway:** end on something the viewer can *use* (a tip) or a final fact that flips how they
   see it. Zack rarely gives a tip.
7. **Captions:** white Inter ExtraBold, at most **one amber keyword** (`#FFB547`) per chunk, centred at
   about 78% height. Never colour a whole chunk.

## 1. Screenplay (lock it before any animation)

Every topic has two worlds:
- **the everyday world** where the viewer is (a plane seat, a kitchen, a night sky, a beach);
- **the hidden world** where the answer is (inside, underneath, too small, too fast, too slow, too far,
  too long ago).

The video's job is to move between them **without the viewer ever losing their place**.

**Target:** 30-35 s, about 85-95 words, 4-7 sentences, voice over at least 90% of the runtime.

| Beat | Seconds | What |
|---|---|---|
| Hook | 0-3 | The situation **and** the felt problem or wonder, in one line. A question, or an order ("Hold your breath…"). |
| Stakes / wonder | 3-6 | One line that makes it matter: true, not alarmist ("That blocked feeling can really hurt", "It's moving faster than a bullet"). |
| Cause | 6-14 | "That's because…": the mechanism, shown in the hidden world. |
| Twist / payoff | 14-24 | "But…/Then…": the turn, with the payoff at about 65-75% of the runtime. |
| Extension | 24-30 | The flip case, what goes wrong, or the surprising scale. |
| Takeaway + button | 30-34 | A tip or a mind-flipping last fact, then a line that loops into the hook. |

**Writing rules:**
- Second person and present tense ("your ears", "your phone", "you're standing on…").
- Chain the sentences with cause-and-effect connectors ("That's because", "But before it does",
  "And when").
- No definitions, no "Ever wondered", no call to action at the end.
- One concrete metaphor per video, built as a 3D object in the scene (§7), not said in passing.
- Facts checked: cite a source in the shot notes.

### Presentation toolbox: pick the device that fits the topic

| Topic type | Hidden-world device | Example |
|---|---|---|
| Body, objects, machines | **Cutaway**: slice the object open in place and keep the outside visible around it. | ear, engine, battery, volcano |
| Very small | **Scale dive**: the lens dive shrinks the camera through 2-3 scale steps, each with a landmark. | a cell, a germ on a phone, an atom |
| Very big or far | **Scale pull-back**: from the viewer outward, with a familiar object kept as the size reference. | the Sun vs Earth, a black hole |
| Too fast | **Bullet time**: freeze and orbit the frozen instant, then release it. | lightning, a popping balloon, a snake strike |
| Too slow or too long ago | **Time-lapse in one shot**: the camera holds while time runs; a cyan clock or ring shows the rate. | erosion, tree growth, continental drift |
| Invisible forces | **Made visible**: cyan particles or streamlines for the force, amber for the thing it acts on. | air pressure, magnetism, sound, Wi-Fi |
| Animals | **Their point of view**: the creature's sense shown in our palette (heat as amber, sound as cyan rings). | bats, snakes, sharks |
| "What if" | **The same set, changed**: one variable at a time in the same scene, so the difference is the story. | what if the Moon vanished |
| How it's made / history | **Exploded view or assembly**: the parts fly apart and come together in order, in the same 3D space. | a pencil, a pyramid, a smartphone |

Pick **one** main device per video. A second device only if the story needs it, and then it must use
the same world (§2).

## 2. One 3D world: consistency is non-negotiable

The owner's note on the pilot: the navy "OUTSIDE = INSIDE" diagram looked **2D** and broke the 3D way of
showing things. Rules:

- **Everything on screen is part of one lit 3D world:** the same light rig, the same house palette, the
  same depth, the same camera language. No flat diagram backgrounds, no 2D infographic inserts, no
  separate "map world".
- **Explanations happen in the scene.** A comparison like "outside = inside" is shown physically:
  - two matching clouds of particles on either side of the membrane;
  - two 3D pressure gauges sitting in the scene as props;
  - a balance scale made of the actual objects.
- **Labels:**
  - at most 2-3 per video;
  - each attached to its object in 3D (it moves with the camera's parallax), in the caption font,
    small;
  - never a title card over the picture.
- **The camera never "jumps worlds" without a physical link** (§3). If two shots don't share a space, a
  scale, an object or a direction of motion, the cut needs a lens dive, a match cut or a whip pan.
- **Look test:** take any frame of the video, crop it to the middle 50%, and it should still be
  obviously the same film as every other frame (palette, lighting, materials, depth of field).

## 3. Transitions: aligned, motivated, invisible

Every transition must have a **reason the eye accepts**:
- **Match cut on shape or position:** the subject sits at the same spot in the frame (within about 10%
  of the frame) and has a similar shape on both sides of the cut. Examples: the round ear opening → the
  round eardrum; the plane window → the iris.
- **Continuous motion:** the camera's movement (direction and speed) carries straight across the cut. A
  push-in continues as a push-in.
- **Screen direction holds:** if outside is on screen-left, it stays left in every shot of the video.
  No 180° flips: the pilot's S04 turned around and lost the viewer.
- **The lens dive** in and out of the hidden world (§0.3).
- **Whip pans** (0.2-0.3 s, motion blur) for sideways jumps in the same world.
- **A 0.5 s dissolve** only for a change of **time**.
- **Never** a dip through black, a pop-in 2D card, or a tunnel with no landmarks.
- **Sound bridges every cut:** the room tone or whoosh of the new world leads the picture by about
  0.2 s (the `sfx-design` skill).

**Before animating,** draw the transition chain as one line, with the link for each cut:
`seat CU →(push-in, same direction) window →(lens dive on the ear) cutaway →(time dissolve) landing …`

## 4. Camera

- **Look at the process; don't fly through it.** Frame the hidden world as a readable view (a cutaway,
  frozen instant, scale step or exploded view) and keep the same orientation every time you return.
- Slow push-ins or orbits, about 5-10% of the framing per shot. Fast motion only inside transitions.
- **One long anchor shot of 6-10 s** carries the core mechanism in one take.
- No handheld shake and no turnarounds. Depth of field on Max's close-ups only; the explanation stays
  sharp.
- Aim for about 9-12 shots per video (the pilot had 22: too choppy, too many worlds).

## 5. Max, the host (`shorts/blender/max_expressions.py`, `real_max.py`)

- **His role per topic:** he lives it (pain, cold, a sneeze), uses it (holds the phone, eats the food),
  or witnesses it (looks up at the eclipse). The hook and the ending always show his reaction.
- One strong expression per shot, eased in over 6-10 frames, then held with small life (blinks, a head
  drift).
- Expressions at thumbnail strength: **asymmetry** reads as real; the brows and mouth carry it.
- Only touch the 52 ARKit face units. The body's other shape keys shape Max: zeroing them broke him in
  the thumbnail tests.
- Frame what he's reacting to **with** his face (the hand on the ear, the phone in his hand). The
  pilot's tight crop hid it.

## 5b. Body mechanics and acting (the owner's top priority, 2026-10-31)

Zack's people move like real people. Ours must too: **no plank tilts, no posed-then-rotated bodies, no
limbs aimed one at a time.** Every action (walk, step, slip, stumble, fall, reach, recover) follows these
rules.

- **Motion source: real human motion first.**
  - Use motion capture (CMU BVH, free for any use; Mixamo with the owner's account) retargeted onto Max
    (MPFB2 has `cmu_mb` and `mixamo` skeletons), then edited.
  - Hand-keying only for small acting beats (a head turn, a hand on a pole).
  - A pose that only "aims" bones is a board, never a frame.
- **Physics drives the timing and direction:**
  - The centre of mass keeps its velocity until a force changes it.
  - Feet that touch the ground stop (friction), unless a surface is slippery.
  - The body rotates about the planted foot like an inverted pendulum. At 10 km/h it reaches the ground
    in roughly 0.5-0.8 s, so falls are fast: show them in slow motion, never by slowing the physics.
  - Gravity is 9.81 m/s²; no floaty falls.
- **Reflexes, in this order:**
  1. The perturbation.
  2. ~100-150 ms later, the arms fling out toward the fall direction (a protective reach) and the knees
     unlock.
  3. A compensatory step if a foot can get under the body (facing forward).
  4. The spine and head counter-rotate (chin tucks in a backward fall; the head lifts in a forward one).
  5. Hands reach for the ground or a grab-point before the body lands.
- **Weight and contact:**
  - Feet plant flat or roll heel-to-toe, never slide unless the story says slip.
  - Knees and hips bend to absorb.
  - Shoulders and arms counter-swing when walking.
  - Contacts are checked in every frame (no floating or sinking feet).
- **Overlap and follow-through:**
  - The head lags the torso, the hands lag the forearms.
  - Clothes and hair settle after the body stops (a cloth sim on the tee for close-ups).
- **Face acts with the body, timed to it:**
  - Surprise starts ~150 ms after the perturbation (brows up, eyes wide, mouth opens).
  - It turns into fear or effort during the fall (brows pinched, teeth clenched).
  - Eyes squeeze or blink just before impact.
  - Relief or pain after, depending on the beat.
  - Eyes look where the danger is (the gap, the ground), with saccades, not a fixed stare.
  - Expressions blend over 3-6 frames, never pop.
- **Motion test before key frames:** every new action gets a short clip from two angles, at real speed
  and in slow motion, on the Mac. Codex reviews the frames (body mechanics, contacts, face); the owner
  approves it before G6.

## 6. Voice (ElevenLabs v3, the owner's clone)

- **Record the whole script as one take** after the script is locked; don't stitch repairs.
- **Audition first:** stability 0.0 against 0.5 on about 10 s, with similarity 0.85. Then generate the
  full script with the winner.
- **Delivery:**
  - sparse tags (`[curious]`, `[warm]`, `[serious]`);
  - CAPS on the 3-5 stressed words;
  - commas and dashes for run-ons, not full stops.
- **Gaps:** remove the double padding (`audio.py` adds its gap on top of each take's own silence). Aim
  for 0.10-0.25 s between phrases, and one ≤0.4 s beat before the payoff.
- **Gates (check before animating):**
  ```
  python3 .claude/skills/shorts-craft/scripts/voice_check.py VOICE.wav --hook "<hook words>" --runtime 34
  ```
  - pace 165-185 wpm;
  - coverage ≥ 90%;
  - pitch span ≥ 8 st overall and ≥ 6 st per phrase;
  - stressed words +4 st or more;
  - the ASR hears the hook phrase.
- The numbers are a check, not a target: also listen on a phone. The pilot measured 6.4 st, 74%
  coverage and gaps of 0.3-0.7 s, which fail the gates.

## 7. Explaining things

- **Use one hidden-world view, reused** (§1 toolbox), built in the house palette and colour code. Keep
  particles sparse and readable at phone size.
- **Animate the process on it:** it bulges, opens, flows, sparks. A faint resting outline or "before"
  ghost makes the change read.
- **The metaphor is a 3D object in the same world:** a balloon inflating beside the eardrum; a valve
  that clicks open. It's not a cutaway to a different style.
- **Graphics:** at most one in-world meter (a gauge, thermometer or timer as a lit prop), translucent 3D
  arrows for the direction of forces, and the 2-3 attached labels (§2).

## 8. Ending

- End on the payoff or the takeaway, with Max's reaction **within 0.5 s of the last word**.
- No "Follow" card and no silent tail: the Short should loop.
- The last frame should flow back into the opening: match its framing for a clean loop.

## 9. Thumbnail (`shorts/pilot_ear_pop/thumbnail.py` is the template)

- One clean frame in the house look:
  - Max at a thumbnail-strength reaction, as a pose for this render only;
  - or the most striking moment of the hidden world.
- The question as a headline (the owner's choice): heavy caps, white plus one amber line, an outline and
  shadow, kept inside 90% of the width and within the top 25%.
- Render it locally on the Mac (Metal, 2160×3840), and output a 1080×1920 JPG for upload.

## 11. Assets at Zack's level without building them

Zack's polish comes mostly from **good base assets, strong materials and lighting, and one art
direction**, not from modelling everything. We source, then **restyle into our house look** so
everything matches (§2).

**Where to get them** (always check the licence at download and record it in `assets/LICENSES.md`;
the web helper researches and verifies):

| Need | Sources | Notes |
|---|---|---|
| Props, sets, vehicles, furniture | Poly Haven, ambientCG (CC0); BlenderKit (a Blender add-on, free plus paid); Sketchfab (filter for CC0 or CC-BY, plus the store); CGTrader / TurboSquid (paid) | CC-BY needs a credit line in the description |
| Space, planets, spacecraft | NASA 3D Resources (generally public domain) | |
| Animals, specimens, artefacts | Smithsonian 3D (many CC0); Sketchfab | |
| Anatomy | Z-Anatomy, BodyParts3D | **CC-BY-SA**: ask the owner before using it in a published video (share-alike) |
| Skies, lighting | Poly Haven HDRIs | |
| Body motion | Mixamo (free rigs and animations, retargeted onto Max); phone-video motion capture (Rokoko Video or similar) | the owner can act the motion |
| Max's face | **an iPhone face-capture app recording ARKit's 52 blendshapes** (Live Link Face, Face Cap or similar) | Max already uses those same 52 face units, so the owner can *perform* the expressions and we import them |
| One-off props nobody sells | image-to-3D generators (open source: Hunyuan3D, TRELLIS; services: Meshy, Tripo) | **needs the owner's OK first** (CLAUDE.md pauses image and video generation); for background props only, then cleaned up and restyled |

**Upgrading Max** (the owner decides; it's a one-time investment):
- **Free path (default):** keep the MPFB/MakeHuman Max and upgrade his look:
  - a skin shader with subsurface scattering plus a skin texture set;
  - modern hair curves instead of cards;
  - better eye shaders;
  - a soft key light plus a cyan rim.
- **Paid path:** Reallusion Character Creator 4 or Human Generator (a Blender add-on). Higher-quality
  skin, hair and clothes, and ARKit-compatible faces. Check the current price and licence first.

**Restyle every asset in, before it appears in a shot:**
- swap its materials to the house set (the colour code, ink & amber palette, our roughness and
  subsurface values);
- remove baked lighting;
- rescale to real-world size;
- run it through G5 QA.

An asset that can't be made to match is not used. A mismatched style breaks the one-3D-world rule.

**Where the realism comes from** (in priority order):
1. lighting (a soft large key, rim, bounce);
2. materials (subsurface on organics, clear-coat only where real, micro-roughness);
3. depth of field and motion blur;
4. animation timing;
5. polygon detail last.

## 10. Pre-render checklist (before spending RunPod credits)

1. The script is locked and fact-checked, about 30-35 s, with one presentation device chosen (§1).
2. The voice take passes `voice_check.py`, and the owner has heard it.
3. The shot list has 9-12 shots and the transition chain is written out with a link per cut (§3). It
   includes the hook beat, one 6-10 s anchor shot, and the lens dive in and out.
4. **The one-world check (§2):** no 2D inserts; every comparison and label is in the 3D scene; the crop
   test passes; screen direction holds.
5. The scenes are lit in ink & amber, with the colour code applied.
6. Captions are white with one amber keyword, about 78% up, not over faces.
7. The Mac animatic (Workbench) has been reviewed by the owner. Then a RunPod `--dry-run`, then the
   render (CLAUDE.md).
8. Grade with `house_grade.py frames ink_amber`. The mix is done with the `sfx-design` skill and
   `audit_mix.py`. The end has no tail.
9. The thumbnail (§9) and the upload text (title, description, hashtags) are ready.
