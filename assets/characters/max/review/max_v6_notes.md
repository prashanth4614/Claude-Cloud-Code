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
