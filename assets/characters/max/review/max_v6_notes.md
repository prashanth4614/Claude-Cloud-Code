# Max v6 review (Mac render, 2026-10-31)

Files: `max_v6_expressions.jpg` (16), `max_v6_turnaround.jpg` (3), `max_v6_hair_closeup.jpg`,
`max_v6_ear_pop_closeup.jpg` (900x900, 3/4 at 35°, 85 mm, 0.95 m), `max_v6_eyes_closeup.jpg`
(900x500, eye level, 85 mm, 0.32 m from the eye midpoint, 15°, neutral) and `max_v6_shirt.jpg`
(900x1000, 55 mm, chest; right thumbs up, left arm raised by my wrapper).
Source: `max_v6.blend` (4c6ab92) + `max_look.py --sheet`. Blender 5.2.3 LTS, Cycles, 128 spp.

## Render
- GPU: Apple M4 (GPU - 10 cores), METAL (CPU off), via the wrapper outside the repo.
- Turnarounds 3.9-5.1 s; expressions 4.3-5.4 s (avg ~4.6 s); hair close-up 15.1 s; ear pop close-up
  18.2 s; eyes 13.0 s; shirt 13.0 s. Whole run 165 s incl. load.
- Memory: peak footprint 7.4 GB, max RSS 3.3 GB (same as v5).

## Eyes (wet line, caruncles)
- Wet lower-lid line: **not visible.** The lower lid edge reads as a dark line plus lashes, with
  no thin bright meniscus between the lid and the eyeball at 0.32 m. It either needs more
  gloss/brightness or sits hidden under the lashes.
- Pink caruncles: **barely visible.** The inner corners read slightly warm, not clearly pink, at
  15°. A more frontal or more inner-corner angle would show them better, but at film distances they
  won't read.
- Other things in the close-up:
  - The lashes are long, thick and spiky (mascara look), and the lower lashes clump into spikes.
    That reads feminine/doll-like. Shorter, thinner, sparser lower lashes would look more natural.
  - The irises are a strong orange-red brown; a darker, cooler brown would look more natural.
  - The catchlights are strong (two highlights per eye). Fine.
  - The pores and brow hairs look good.

## Teeth (surprised / yawn / ear pop)
- Better: the upper row now shows in surprised, amazed, scared and ear pop, and the ear pop
  close-up shows a fuller, even upper row, no longer gappy.
- The lower row is still hard to see in yawn and surprised. At phone size the teeth read as a small
  grey-blue strip; slightly brighter or less blue teeth would read better.

## Chew vs swallow vs neutral
- Still too alike at phone size.
  - chew: sealed lips with a tiny jaw shift. Without motion it looks almost identical to neutral.
  - swallow: pressed lips, slightly lowered lids. The throat rise is **not visible** at tile size.
- These will probably only read in motion, so judge them in an animatic. For stills: a puffed
  cheek for chew, and a chin-down tuck with a visible Adam's-apple bump for swallow.

## Shirt
- Cotton reads as matte and soft; good colour, not shiny. No knit visible at chest distance, which
  is fine.
- Folds are subtle: broad soft shading across the chest and belly, a little pull under the raised
  arm, a clean collar and hem. It looks like a real tee, but a bit "smooth CG". Some sharper
  creases at the armpit/sleeve and at the waist above the jeans would help.
- The raised-arm pose deforms acceptably (no tearing at the shoulder). The fabric under the raised
  arm stretches up with the skin rather than hanging.
- Colour: the tee is lighter and greyer teal than v5 (cotton shader). Check it still matches the
  house palette.
- Framing note: my raised-arm pose clips the left hand at the top edge. That's my wrapper's
  framing, not the asset.

## Hair
- The hairline breakup worked: the front edge is softer and fuzzier, with fine hairs, no longer a
  hard line.
- From the front a mild "M" / temple recession remains (as in v5b).
- Volume and fade unchanged from v5b (good).

## Ear rim
- Improved but not gone: a thinner, dimmer bright edge still shows along the top of the ear in both
  close-ups.

## Broken / artefacts
- None new: no hair through skin, no stray strands, no fireflies, no tearing at eyelids, mouth
  corners or shoulders.

## v6b

Re-render of `max_v6.blend` at 12a49fd: same wrapper, 128 spp, the same 6 outputs (max_v6_* overwritten).
The shirt shot is pulled back (2.45 m, aim 16 cm higher) so the raised hand is fully in frame.
- Times: turnarounds 3.9-5.1 s; expressions 4.8-14.9 s; close-ups 26.5 s (ear pop), 27.2 s (hair),
  17.2 s (eyes), 11.8 s (shirt). Whole run 255 s. Peak footprint 7.4 GB, max RSS 3.4 GB.
- The renders got slower partway through, probably because macOS `mediaanalysisd` (Photos library
  analysis) was using ~180% CPU in the background. That's not the asset; v6 times are the real baseline.

### NEW BUG (top priority): the hair lifts off the forehead in the swallow pose
- In `expr_swallow` (chin tucked down) a **pale bald band appears between the brows and the
  hairline**: the front of the hair sits up and back from the scalp, so the forehead skin shows
  through where hair should be. Visible even at phone size in the expression sheet.
- The other head poses look fine (thinking tilt, ear pop). It seems to happen when the head/neck
  bends forward: the hair curves may not follow the head deform (rest-pose surface vs posed mesh),
  or the swallow neck/throat shape key moves the scalp under the hair.
- Check before any shot where Max nods or looks down.

### Did each fix work?
- **Tear line: partly.** A faint wet sheen is now visible on the lower lid edge, especially on his
  left eye. Subtle but present; fine for film distances.
- **Lashes: yes.** Thinner and softer, no more mascara look. The lower lashes are still slightly
  clumpy, but acceptable.
- **Irises: yes.** A natural warm mid-brown, no longer red/orange.
- **Caruncles:** a little pinker in the inner corners; subtle but now reads as flesh.
- **Teeth: yes.** Brighter and warmer (no blue-grey); they read as teeth at phone size in ear pop,
  surprised, scared and yawn.
- **Ear rim: improved.** Only a very small bright edge at the top of the ear in the close-ups; it
  won't read in film.
- **Shirt folds: partly.** Somewhat stronger shading folds on the chest, belly and the side under
  the raised arm, and less sheen (good). Still fairly smooth with no crisp creases, and under the
  raised arm the shirt still stretches up with the skin instead of bunching.
- **Temples: yes.** Corners fuller; the "M" from the front is much milder (a small widow's peak
  remains, which is natural).
- **Chew / swallow stills: partly.**
  - chew: now shows a small sideways jaw/lip shift. Readable next to neutral, but still subtle.
  - swallow: clearly different now (chin down, pressed lips, lowered lids), but see the hair bug above.

### Otherwise
- No new tearing at eyelids, mouth or shoulders; no stray strands or fireflies.

## v6c (cloud fix for the v6b "hair lifts in the swallow pose" bug)

Root cause: two faults in `max_hair_curves.hair_surface()`. The second is the one that showed.
1. **UV overlap (the visible bug).** The attachment surface had a spherical UV that wrapped at the back
   of the head and swirled at the crown. The faces across the wrap overlapped the rest of the map, so
   Deform Curves on Surface attached some roots to the wrong (back-of-head) triangles. Rest pose looked
   fine, but any head bend moved those roots wrongly. Measured on 2000 sampled roots, 10° chin tuck:
   median 7.7 mm and p95 18 mm off the scalp. Fix: a seamless azimuthal (fisheye) projection from inside
   the skull (432 faces, 0 flipped). The roots now stay at a median of 0.06 mm and p95 of 0.4 mm in every
   pose tested: tuck 10°, lift −12°, 28°, 8°+20°, 15°.
2. **Rigid skinning.** The surface (and scalp cap) were 100% on the `head` bone, while the forehead skin
   also follows neck01-03 and the oculi bones (up to 8 mm apart in a pose). They now copy the body's
   own bone weights (`max_hair.copy_skin_weights`).

Cloud CPU check (24 spp): `max_v6c_hairfix_cpu.jpg`, showing neutral, swallow and a 28° tilt. No bald
band. A full-quality Mac sheet should confirm.

## v6c Mac review

Render of `max_v6.blend` at 1d8af4d+ (pulled c945323): same Metal wrapper, Apple M4 GPU (10 cores),
128 spp.
- `max_v6c_expressions.jpg`: the full expression sheet.
- `max_v6c_hair_poses.jpg`: 4 tiles, 600x600, 3/4 front at 35°, 85 mm, 0.7 m, aimed 5 cm above the
  head point (forehead/hairline). The framing crops the lower face on purpose.
- Times: expression tiles 8.5-12.9 s, hair-pose tiles 15.5-19.0 s, total 404 s. That includes an
  accidental second sheet pass from my wrapper (harmless: identical output, light rig idempotent).
  The Mac was also under background load again. Peak footprint 6.8 GB, max RSS 2.8 GB.

### Hair attachment per pose
| pose | pale band brows-hairline | fringe attached | strands through skin | result |
|---|---|---|---|---|
| swallow (`set_expression("swallow")`, chin tuck) | none | yes | none | **PASS** |
| look up (`pose_head(-12,0,0)`) | none | yes | none | **PASS** |
| turn (`pose_head(0,0,28)`) | none | yes | none | **PASS** |
| down 8 + turn 20 (`pose_head(8,0,20)`) | none | yes | none | **PASS** |

- The v6b bug is fixed: in swallow the hair now sits on the scalp, the hairline stays in place with
  its soft, fuzzy edge, and there's no bald band. The `expr_swallow` tile in the expression sheet
  also looks right now.
- Side fade and temples follow the head in all turns; the fade stays clean with no lifting at the
  sides.

### Anything new
- Nothing broken. The expression sheet matches v6b otherwise (teeth, irises, chew shift all as before).
- Still minor: a tiny bright edge on the top of the ear in the turn tiles (rim light), as noted in v6b.

## v6d (Codex 012, applied and checked by Claude in the cloud)

- **Armpit correctives** (`max_look.add_shirt_correctives`): two shape keys on the tee,
  `max_pit_L` and `max_pit_R`. They are sampled from the real skinning at a 70° arm lift, inverted, and
  then add 3 diagonal folds and remove part of the upward drag (up to 6.7 mm, about 290 vertices).
  - Driven by the upper arm's world angle. Claude moved the onset from 15° to 40° (`PIT_ONSET`), full at
    85° (`PIT_FULL`). With Codex's 15° the key sat at 0.33 in the rest A-pose.
  - Measured: 0 at rest and with the arm down, 0.47 at 60°, 1.0 at 90° and above, unaffected by a 60°
    twist; thumbs-up raised is 0.92.
  - Fixed a Codex bug: mathutils `Matrix / float` isn't supported.
  - Result (`max_v6d_armpit_cpu.jpg`, before | after): a modest gain, a few more folds gather under the
    raised arm and the stretch softens. The tee's base mesh is coarse, so it won't get much crisper
    without new geometry.
- **Chew** (`max_expressions` chew/chew_b, plus mirrored chew_r/chew_b_r; `build_max.chew_keys`,
  `ease_chew`, `chew_cycle`): 3 chews at 24 fps, 12 frames each, alternating sides, eased.
  - jawOpen peaks at 0.34 under sealed lips (mouthClose 0.30), with jawLeft ±0.42.
  - Still (`max_v6d_chew_cpu.jpg`, neutral | chew | chew_r): the jaw drops and shifts, the lips stay
    closed and the cheek fills.
  - The published pilot (`real_max.py`) is unchanged.

## v6d Mac review

Render of `max_v6.blend` at af58305: same Metal wrapper (Apple M4 GPU, 10 cores).
- `max_v6d_expressions.jpg`: expression sheet at 128 spp.
- `max_v6d_shirt.jpg`: (a) chest, 55 mm, target head_point - 0.30 z, camera +(0.28,-1.75,0.08);
  (b) armpit close-up of the raised left arm, 50 mm, ~0.7 m. Pose: `thumbs_up(raised=True)`, left
  upper arm (0.8,-0.15,0.35), forearm (-0.35,-0.2,1). Both at 128 spp, 900x1000.
- `max_v6d_chew.mp4`: `chew_cycle(rig, 10)`, frames 7-46 at 24 fps (40 frames, 1.67 s), 640x640,
  32 spp, 15° 3/4 face close-up, 85 mm. H.264 at 126 KB.
- Pit shape-key drivers (they worked without auto-exec, as simple expressions): rest L=0.01 R=0.01;
  in the shirt pose L=1.00 (raised arm) and R=0.92 (thumbs-up arm, also lifted).
- Times: expression tiles 3.2-10.5 s; shirt 28.2 s / 29.3 s; chew frames 4.9-7.7 s each (~5.7 s avg).
  Total 433 s. Peak footprint 7.5 GB, max RSS 3.6 GB.

### Shirt / armpit folds
- **Natural, not lumpy.** The raised side shows a soft diagonal pull fold from the armpit toward
  the chest and a gentle hollow under the sleeve. It reads as cotton stretched by the lifted arm,
  with no bumps or blobs.
- Still fairly subtle at chest distance (a): you see the fabric stretch, not crisp creases.
- **Clipping:** none of the tee into the body at the chest, side or armpit.
- One small thing: in (b) there's a tiny dark notch under the raised sleeve's hem where the sleeve
  meets the arm. It looks like a sliver of the sleeve's inside/back face; minor, only at close range.

### Chew
- **Expression tile:** reads as chewing now. Jaw lowered and shifted to one side, lips sealed, a
  little fuller in the cheek, clearly different from neutral.
- **In motion (mp4):** the chin goes down and side to side with alternating sides, eased in and out.
  It reads as chewing, but gently; at phone size the movement is modest. A bit more jaw drop or
  cheek bulge on the peaks would make it unmistakable.
- **Lip gap:** none. The lips stay sealed in every frame I checked (f010 / f016 / f022 and the
  10-frame strip).

### Other
- The small bright speck on the top of the ear (rim light) is still visible in the face close-up.
- Nothing else new; the expression sheet otherwise matches v6c.

## v6e (Claude, from Codex's 013 frame review; cloud CPU checks)

Codex 013 top 3: hair attachment at the temples, armpit folds, expression separation.
- **Hair** (`max_hair.py`): the ear clearance reached 35 mm above eye level (the ear tops out at 4 mm),
  so each side was bare under the long top. Now `EAR_CLEAR` is 12 mm, the side hairline comes down into
  a short sideburn, and the top blends into the sides over 30-90 mm (`TOP_BLEND`). Roots are still
  attached in every head pose (p95 0.38 mm). `max_v6e_temple_cpu.jpg` shows before, after and front.
- **Shirt** (`max_look.py`):
  - the armpit folds now fan out from the armpit at 22°, 45° and 68°, and are narrower (8° half-width);
  - less drop (0.28), so the trough is shallower;
  - a sewn armhole seam: a 1.2 mm groove with a darker line, drawn from a signed-distance attribute, so it
    stays sharp on the coarse mesh;
  - calmer belly bump (0.0012).

  `max_v6e_shirt_cpu.jpg` shows chest old | new, then armpit old | new.
- **Expressions** (`max_expressions.py`, faces and head poses):
  - puzzled is confused, not sad (knit brows, pressed frown);
  - curious is interested (brows up, parted half-smile, leaning in);
  - thinking is a furrowed "hmm";
  - surprised drops the jaw to a round open mouth, eyes less staring;
  - amazed is a smiling "wow";
  - scared has pinched brows and a flat stretched mouth with lips over the teeth, plus a recoil;
  - wince: both eyes squeezed, lips pressed, no teeth;
  - ear pop is strongly one-sided, head tilted to the ear;
  - disgusted is an "ew" with the chin pushed up;
  - relief has eyes closing and the head tipped back;
  - chew has a bigger jaw drop and shift.

  `max_v6e_expressions_cpu.jpg` is from before the last curious, surprised and amazed tweak.
