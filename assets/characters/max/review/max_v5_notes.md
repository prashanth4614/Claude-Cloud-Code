# Max v5 review (Mac render, 2026-10-31)

Files: `max_v5_expressions.jpg` (16 tiles), `max_v5_turnaround.jpg` (3),
`max_v5_hair_closeup.jpg` and `max_v5_ear_pop_closeup.jpg` (900x900, 3/4 front at 35°, 85 mm,
0.95 m from the head).
Source: `max_v5.blend` (e166667) + `max_look.py --sheet` (no --regroom / --curves).
Blender 5.2.3 LTS, Cycles, **128 samples**, denoised.

## Render
- GPU: Apple M4 (GPU - 10 cores), METAL (CPU device off), via the same wrapper outside the repo.
- Per image: turnarounds 4.7 / 3.7 / 3.2 s; expressions 3.5-4.4 s (avg ~3.7 s);
  close-ups 8.9 s (neutral) and 9.9 s (ear pop). Whole run 98 s incl. load.
  That's faster than v4b at 64 spp: strand curves are cheaper than the old transparent cards.
- Memory (`/usr/bin/time -l`, whole Blender process): peak footprint 7.4 GB, max RSS 3.3 GB.
  OK on this 16 GB Mac, but leave headroom when the film scene loads around him.

## Hair: real strands now, but the hairline went too far back
- Good: it finally reads as real hair. Fine individual strands, soft natural highlights along the
  combed direction, no cards, scales or spikes. The close-up looks like actual hair.
- Biggest problem: **the hairline sits far too high and recedes at the temples** (a deep "M" with
  a widow's peak). Forehead and temples are bare up to about 2 cm above the brow tail, so at phone
  size he reads as a receding / thinning hairline and looks older. Bring the front edge down and
  fill in the temple corners.
- At the front edge there's a warm orange/translucent band on the skin under the first strands.
  The scalp or root colour shows through; it looks like a scalp tint, not hair. Darken the scalp
  under the hair or add a sparse short-hair fringe there.
- Sides: hard undercut line with bare skin above the ear and behind it. It reads as shaved, not a
  short taper. A short-stubble fade (very short, dense curves) would soften it.
- Volume: flat, close to the skull. Neat, but a little plastered at phone size; slightly more lift
  over the crown/fringe would read more "stylish".
- Highlights: soft and believable, no harsh anisotropic band. Slight warm/brown tint at the tips.

## Skin
- Zones show subtly: pinker forehead/nose, more stubble on the jaw and upper lip; stubble reads
  well in the close-ups. Much less waxy than v4.
- The forehead and temple area still look smooth and a bit shiny, made more obvious by the high
  hairline.
- A thin bright white line along the top rim of the ear in both close-ups: probably the rim light
  on a sharp ear edge. Minor, but visible at 900 px.

## Expressions
- Same reads as v4b: curious, puzzled, thinking, relief smile and disgusted are distinct;
  neutral / chew / swallow still look alike. Thumbs up is chest-up, with the hand near the left edge.
- Ear pop close-up: clear, one eye squeezed and the mouth pulled. Reads well.
- Teeth still sparse/gappy in surprised, scared, yawn and ear pop.

## Broken / artefacts
- No hair through skin, no floating or stray strands, no fireflies seen at 128 spp.
- No mesh tearing at eyelids or mouth corners.
- Only artefacts: the orange scalp band at the hairline and the white ear-rim line (above).
