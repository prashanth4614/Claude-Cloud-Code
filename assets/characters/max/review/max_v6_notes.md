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

## v6e Mac review

Render of `max_v6.blend` at f50a157: same Metal wrapper (Apple M4 GPU, 10 cores), 128 spp (chew 32 spp).
- `max_v6e_expressions.jpg` (16 tiles).
- `max_v6e_hair_poses.jpg`: the 4 v6c poses plus a 5th, neutral side/temple view
  (head_point + 0.05 z + (-0.45,-0.40,0.06), 85 mm).
- `max_v6e_shirt.jpg`: the same chest and armpit tiles as v6d.
- `max_v6e_chew.mp4`: 40 frames, 24 fps, 640x640, 130 KB.
- `max_v6e_chew_frames.jpg`: every 3rd frame, 7-46.
- Times: expression tiles 3.7-4.3 s; hair poses 7.2-9.3 s, side view 14.0 s; shirt 11.0 / 13.2 s;
  chew 5.0 s/frame. Total 384 s. Peak footprint 7.2 GB, max RSS 3.4 GB.

### Temples / sideburns
- **Better:** the temples and sides are now covered down to a sideburn in front of the ear, so the
  bare high-fade look is gone. From the front tiles he reads as having a normal, full, short haircut.
  All 4 head poses still pass: no band, fringe attached, no strands through skin.
- **Still off:**
  - In the side/temple view the parting is a wide pale patch. Scalp shows through in a fan-shaped
    whorl at the front-left of the part. A narrower part line, or denser hair either side of it,
    would fix it.
  - The same pale part shows as a light streak on his right side in most front tiles; acceptable
    at phone size.
  - The top looks a little flat / helmet-like now that the sides are fuller.

### Seam and folds
- **Seam line:** visible as a thin dark sewn line around the armhole, down from the shoulder. Reads
  as a real seam.
- **Folds:** soft pull folds now fan out from the armpit toward the chest. Natural, not lumpy, but
  still low-contrast at chest distance.
- **New artefact:** in the armpit close-up, a small **square, blocky darker patch** sits just below
  the seam in the hollow (looks like a texture/normal tile edge or a shape-key crease), plus a
  faint vertical line inside it. Only visible close up, but it's geometric, not cloth-like.
- The small dark notch under the raised sleeve hem is still there.
- Chest: calmer, smooth; no clipping of the tee into the body.

### Expressions at thumbnail size
- Clear and distinct: amazed, surprised (big O), disgusted (head turn + sneer, much stronger),
  ear pop, laughing, wince (both eyes squeezed), relief smile (eyes closed + smile), yawn, thinking.
- chew: now clearly chewing (jaw shifted, cheek full), different from neutral.
- swallow: pressed lips and lowered lids. Distinct from neutral, though still subtle.
- curious / puzzled: distinct from each other (raised brow + half-smile vs asymmetric brow and
  mouth twist).
- scared: now reads more **worried/sad** than scared (eyes not widened, brows up in the middle).
  Wider eyes and a pulled-back mouth would read as scared.
- thumbs up: unchanged, fine.

### Chew in motion and lip gap
- Reads as chewing now: clear peaks at frames ~13, 25 and 37 (jaw down and to one side, cheek
  bulge), alternating sides, eased back to neutral between chews. Much stronger than v6d.
- **Lip gap:** none; the lips stay sealed in all 14 frames on the sheet.
## v6f (owner: "the raised left arm's shoulder looks trimmed, not natural")

- **Cause:** only the upper-arm bone rotated, so when the arm went up, the top of the shoulder collapsed into a
  straight, flat line from the neck to the arm.
- **Fixes:**
  - **Shoulder rise** (`build_max.lift_shoulder`, called automatically by `aim_bone` for any
    `upperarm01.*`): the collarbone lifts with the arm, at 0.33° per degree of arm elevation above 35°,
    capped at 32°. This is the shoulder's natural rhythm.
  - **Volume-preserving skinning** (`max_look.preserve_volume`): dual quaternion skinning on all 10 objects
    skinned to Max, including the hair surface, so they still deform alike. The raised shoulder stays round.
  - **Sleeve insides:** the back faces of the tee get a faint glow of their own colour
    (`INSIDE_GLOW` 0.35), so the hem no longer shows a pitch-black ring.
- **Checks:**
  - hair roots unchanged in all head poses (p95 0.38 mm);
  - shirt correctives still 0 at rest and 1.0 at a 90° lift;
  - rest and thumbs-up poses look normal.
- **Images:**
  - `max_v6f_shoulder_before_after_cpu.jpg`: front before | after, side before | after (the first fix only);
  - `max_v6f_shoulder_poses_cpu.jpg`: with both fixes, raised front, raised side, rest, thumbs-up.

## v6f Mac review

Render of `max_v6.blend` at 6de1eb8 (contains aa49aff v6f): same Metal wrapper (Apple M4 GPU), 128 spp,
900x1000 tiles. `max_v6f_shoulder.jpg` has 5 tiles:
- a: the v6d/v6e shirt pose, chest camera;
- b: front close-up on the raised left shoulder (sh+(0.15,-0.9,0.05) -> sh+(-0.05,0,-0.03), 50 mm);
- c: side view (sh+(0.85,-0.45,0.15) -> sh, 50 mm);
- d: both arms straight overhead, chest camera;
- e: the v6e armpit close-up, re-rendered.

Times: 7.2-12.4 s per tile, 55 s total. Peak footprint 7.6 GB, max RSS 3.5 GB.

### Raised shoulder (a, b, c): fixed
- The shoulder top is **rounded and natural now**: the collarbone and deltoid rise with the arm and
  the line from neck to arm is a smooth slope, with no flat "trimmed" top. In the side view (c) the
  deltoid bulge under the sleeve looks anatomical.
- No candy-wrapper twisting on the upper arm or at the elbow in any tile.

### Arms overhead (d): NEW PROBLEM, the tee balloons
- With both arms straight up, the **shirt balloons out hugely at both shoulders/armpits**: two big
  inflated lobes stick out sideways past the body, wider than the head-to-shoulder width, with the
  seam arcing across them. It reads as a puffed-up costume, not cloth.
- The body/arms underneath look OK. It's the shirt deform: likely the pit correctives
  (max_pit_L/R) at full value stacking with the volume-preserving skinning, or the sleeve/side
  vertices following the arm too far. Needs clamping, or a separate overhead corrective, before any
  arms-up shot.

### Sleeve hem inner ring
- **Mostly fixed:** no pure black ring. In (c) the underside of the raised sleeve's hem still shows
  a dark brown band (the sleeve interior in shadow), noticeable but believable as a shadowed inside.
  In (a/b) it's no longer visible.

### Blocky patch (e) and a new chest line
- **Blocky square patch: still there.** In the armpit hollow below the seam there's a lighter
  rectangular block with straight edges. Same as v6e.
- **New, small:** a thin jagged/stepped crease line runs across the upper chest from the collar
  toward the seam (visible in b and e). It looks like a shape-key or fold-map boundary, not a real
  fabric fold. Close-up only.

## v6g (the Mac v6f review: "with both arms overhead the tee balloons into two big lobes")

- **Cause:** v6f's volume-preserving (dual quaternion) skinning. With MPFB's weights it inflates the
  **body's** shoulders at extreme arm angles, and the tee followed. See
  `max_v6g_overhead_body_cause_cpu.jpg` (body only, tee hidden): with it | without it | without the
  collarbone lift | without both. Only removing it fixes the balloon.
- **Fix:** volume preservation is removed (back to linear skinning everywhere). The collarbone lift alone
  keeps the raised shoulder round; Codex 014 had also called the volume-preserved shoulder "padded".
- **Also new:** `max_overhead_L/R`, a second tee corrective driven from 95° to 165° of arm lift. It is
  sampled with the arm overhead and pulls fabric that floats more than 6 mm off the skin back to it
  (up to 15 mm, about 950 vertices per side, smoothed). The arm drivers are now one helper,
  `arm_angle_driver`.
- **Checks:** pit key 0 at rest, 0.47 at 60° and 1 at 90°; overhead key 0 up to 95°, 0.48 at 120° and 1
  at 175°. Hair roots are unchanged.
- **Image:** `max_v6g_overhead_shoulder_cpu.jpg` shows arms overhead, the raised shoulder from the
  front, and from the side.

## v6g Mac review

Render of `max_v6.blend` at dbfeaf4 (v6g): the same 5-tile shoulder sheet as v6f
(`max_v6g_shoulder.jpg`), Metal on the Apple M4 GPU, 128 spp, 900x1000 tiles. Times 6.7-10.3 s per tile,
51 s total. Peak footprint 7.5 GB, max RSS 3.7 GB.

- **Overhead balloon: gone (d).** With both arms up the tee now follows the torso: sleeves
  stand up with the arms, and the sides taper down to the waist. A slight natural fullness remains
  where the sleeve meets the side, but nothing sticks out past the body. A tiny dark notch at the
  outer edge of his right sleeve is only visible at full size.
- **Raised shoulder (a, b, c): still natural.** Rounded top with the collarbone lift, a smooth
  slope from neck to arm, not trimmed and not padded. Practically the same as v6f, minus the extra
  fullness. No candy-wrapper twist.
- **Armpit blocky patch (e): fainter, not gone.** The rectangular lighter block in the armpit hollow
  is softer-edged and lower in contrast than v6e/v6f. You still see its straight edges at full size;
  invisible at phone size.
- **Chest crease line (b, e): still there.** The thin stepped/jagged line from the collar toward the
  armhole seam is unchanged. Close-up only.
- Sleeve hem inner ring: unchanged from v6f (dark-brown shadowed underside in the side view, no
  black ring).

## v6h (Codex 014 fixes; cloud CPU checks)

- **Pale parting / "thinning":** a test with the scalp under the hair darkened to black proved the
  patch was skin showing between the strands. The scalp tint is now full strength in a deep root brown
  (`SCALP_TINT` 1.0, `SCALP_COLOR`; it was 0.85 toward a light brown). Near the part, strands also
  lean up to 45% across it (`PART_SOFT`/`PART_BLEND`), so it closes to a line.
  `max_v6h_hair_cpu.jpg` shows the temple, the front and a tilt.
- **Expressions:**
  - scared: wide eyes, lips apart, corners pulled sideways and down, recoil;
  - amazed: a dropped-jaw "wow" with high brows and smiling cheeks;
  - curious: a directed gaze, one brow high, leaning in;
  - puzzled: one brow hard down and one up, narrowed eyes;
  - chew: more jaw travel (jawOpen 0.52 with mouthClose 0.47, jawLeft 0.6).

  `max_v6h_expressions_cpu.jpg` also has the temple before and after the part blend only.

## v6h Mac review

Render of `max_v6.blend` at 55f35cf (v6h): same Metal wrapper (Apple M4 GPU), 128 spp (chew 32 spp).
- `max_v6h_expressions.jpg` (16).
- `max_v6h_hair_poses.jpg`: 4 head poses + temple view, as v6e.
- `max_v6h_chew.mp4`: 40 frames, 24 fps, 640x640, 130 KB.
- `max_v6h_chew_frames.jpg`: every 3rd frame, 7-46.
- Times: expression tiles 3.0-4.5 s; hair poses 7.2-8.7 s, temple 12.7 s; chew 5.0 s/frame. Total 353 s.
  Peak footprint 6.9 GB, max RSS 2.9 GB.

### Parting and hairline
- **Parting: fixed.** No pale scalp patch in the temple view any more. The part reads as a soft
  darker parting line with hair density either side; in the front tiles the light streak on his
  right side is gone.
- **Hairline: fine, not harsh.** The front edge keeps its soft, fuzzy break-up. The darker scalp
  shows as a slight shadow right at the roots, which reads as natural density, not a painted dark
  line.
- All 4 head poses still pass (no band, fringe attached, no strands through skin).

### Expressions at thumbnail size
- **amazed:** clearer (brows up, eyes wide, open mouth with teeth). Reads as amazed, not just talking.
- **curious:** clearer. A slight head dip with eyes up and a small half-smile; distinct from neutral.
- **puzzled:** clear (asymmetric brow, mouth twisted to one side).
- **scared:** better than v6e. Eyes wider, mouth pulled back showing teeth. Reads as
  scared/anxious now, though still a little "worried"; more brow-raise in the middle would push it.
- Unchanged and fine: surprised, disgusted, ear pop, laughing, wince, relief smile, yawn, thinking,
  thumbs up. swallow is still subtle.
- **chew tile:** cheek bulge and jaw shift visible; reads as chewing.

### Chew in motion and lip gap
- Reads as chewing: peaks at ~13, 25 and 37, alternating sides, sealed lips.
- **"Bigger chew": I can't see a difference from v6e in the clip.** Measured rest-vs-peak (f7 vs
  f13) SSIM is 0.847 for v6h and 0.843 for v6e, and v6e vs v6h at the same peak frame is 0.976. The
  motion amplitude is essentially the same as v6e. Maybe `chew_cycle` keys don't pick up the bigger
  chew shapes, or the change only affects the static `chew` tile.
- **Lip gap:** none in any of the 14 frames.

## v6i (chew amplitude; the Mac v6h review measured no visible change from v6e)

- The keys were applied correctly; v6h's step (jawOpen 0.44 to 0.52) was just too small to see.
- Now: jawOpen 0.68 with mouthClose 0.62 (lips still sealed), jawLeft/Right 0.75, and a 7° chin bob on
  each chew (HEAD_POSE `chew` (7,-5,0)).
- `max_v6i_chew_cpu.jpg` shows neutral | chew | chew_r: the chin clearly drops and swings, with no lip gap.
- Shape keys only; `max_v6.blend` doesn't change (expressions are read from code).

## v6i Mac review

Chew only, at b9bbe04: `chew_cycle(rig, 10)`, frames 7-46, 640x640, 32 spp, Metal on the Apple M4
(4.8 s/frame, 216 s total).
`max_v6i_chew.mp4` (40 frames, 24 fps, 140 KB) and `max_v6i_chew_frames.jpg` (every 3rd frame).

- **Reads as chewing at phone size: yes.** The peaks (~13, 25, 37) show a clearly longer lower face,
  jaw dropped and swung to alternating sides, with a cheek bulge. Visibly bigger than v6e/v6h:
  rest-vs-peak SSIM f7/f13 is 0.824 (v6h 0.847, v6e 0.843).
- **Lip gap:** none; the lips stay sealed through every frame on the sheet, including the deepest peaks.
- **Jaw popping:** none found. The biggest frame-to-frame changes (SSIM 0.87-0.89 at 35-36, 11-12,
  23-24, 15-16) cluster evenly on the way into and out of each peak, with no single outlier jump. The
  motion eases rather than snapping between keys.
- **Chin bob:** looks natural. The head dips slightly on each chew peak (more top of head visible
  at 25 and 37) and returns between chews; small enough not to look like nodding.

## v6j (Codex 015: "good enough to start the pilot"; facial performance pass)

- **neutral:** a calm baseline (a hint of smile, settled brows); the bare mesh read slightly worried.
- **laughing:** the cheeks push up into the lower lids (squint 0.8, not blink), with dimples and a nose
  crinkle. Before, it read as "sleepy eyes".
- **amazed / surprised separated:** amazed is delighted wonder (a big open smile, lifted cheeks, soft
  brows); surprised is startled (maxed brows, wide eyes, dropped jaw, no smile, head back).
- **chew:** jaw-led with relaxed lips (no press or shrug bunching, so no "lip-pursing"), and a real
  in-between `chew_b` (jaw half up), so the cycle moves continuously.
- `max_v6j_expressions_cpu.jpg` shows neutral, laughing, amazed, surprised, chew and chew_b.

## v6j Mac review

At f341804: expression sheet (128 spp, 4.4 s/tile) and chew clip (40 frames, 32 spp, 5.2 s/frame),
Metal on the Apple M4, 320 s total.
`max_v6j_expressions.jpg`, `max_v6j_chew.mp4` (137 KB), `max_v6j_chew_frames.jpg`.

- **Neutral: mostly calm.** Relaxed mouth, level gaze. A faint hint of inner-brow lift still gives
  him a slightly tired/concerned look at thumbnail size, much less than before. Acceptable.
- **Laughing: yes, cheeks lift into the eyes.** The lower lids push up into a smiling squint with
  raised cheeks and an open, toothy smile; not sleepy. It reads as a big happy grin more than a
  belly laugh, which is fine.
- **Amazed vs surprised: clearly different now.** amazed = delighted (brows up, bright eyes, open
  smile with teeth); surprised = startled (very wide eyes, round O mouth, tense). No confusion
  at phone size.
- **Chew: jaw-led, yes, but there's a lip gap at the peaks.** The jaw clearly drops and swings
  (frames ~13, 25, 37) and the cheek fills; it reads as chewing, not lip-pursing. **But at the
  peaks the lips part slightly**: at full size f013 shows a small dark opening between the lips
  (also visible at 37 and faintly at 25 on the sheet). Between peaks the lips are sealed. The
  bigger jaw drop seems to outrun the lip-seal shape. It needs a stronger seal (or a lip press
  corrective driven by jaw open) at the peak values.
