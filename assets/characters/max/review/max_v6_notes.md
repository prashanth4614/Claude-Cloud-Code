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
