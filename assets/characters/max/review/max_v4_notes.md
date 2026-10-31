# Max v4 review (Mac render, 2026-10-31)

Sheets: `max_v4_expressions.jpg` (16 tiles), `max_v4_turnaround.jpg` (3 tiles).
Source: `max_v4.blend` + `max_look.py --sheet` (Blender 5.2.3 LTS), Cycles 48 samples, denoised.

## Render
- GPU: Apple M4 (GPU - 10 cores), Cycles METAL (CPU device disabled). Forced via a wrapper outside
  the repo that sets `cycles.device = "GPU"` after `build_max.setup_render` (build_max.py untouched).
- Per image: turnarounds 540x960 9.4 / 6.6 / 9.3 s (front / side / three-quarter);
  expressions 600x600 5.3-6.2 s each (avg ~5.7 s). Whole run 119 s incl. load + upgrade.

## Hair: biggest problem
- Doesn't read as hair. Chunky flat "scales" / brush-stroke cards, like a pinecone or feathers,
  most visible in close-ups (neutral, ear pop, yawn).
- Volume sits off-centre: piled high on his left, like a lopsided pompadour. Flat and thin on the
  right temple.
- Hairline is a hard dark line across the forehead. Skin shows through above the ears and at the
  temples (dark gaps near the right temple in neutral / ear pop).
- Side turnaround: the back of the hair is a dark lump, with no strand detail.

## Skin
- Fairly natural at phone size, but smooth and slightly waxy on forehead, nose and cheeks
  (little pore or roughness break-up).
- No cyan glare patches from the rim. The rim mostly catches ear and neck edges. Warm speculars on
  forehead and nose bridge are acceptable.

## Eyes
- Small catchlights present; the eyes look wet at 600 px. At phone size they read a bit flat:
  a larger/brighter catchlight would help.

## Expressions (phone-size read)
- Clear: amazed, surprised, scared, yawn, ear pop, wince, laughing.
- Weak, look alike: neutral, curious, puzzled, thinking, swallow, chew, relief smile,
  disgusted. These need bigger brow/mouth shapes (or a head tilt) to tell apart.
- thumbs up: rendered full-body / wide, not head-and-shoulders. The thumb is tiny at phone size;
  frame chest-up.
- Teeth: few, small, sparse lower teeth in surprised / scared / yawn. They look gappy.
- Tearing: none seen at eyelids or mouth corners (closed eyes in yawn / wince / ear pop are clean).
- Count: the brief says 17 expressions; the sheet has 16 `expr_*` images (15 heads + thumbs up).

## Turnaround
- A-pose reads cleanly; clothes and shoes fine. Tile order is front / side / three quarter
  (alphabetical glob).

## v4b (neat hair)

Re-render of the rebuilt `max_v4.blend` (8736cc3): same Metal wrapper, **64 samples**, plus
`max_v4_hair_closeup.jpg` (900x900, 3/4 front at 35°, 85 mm, 0.95 m from the head, neutral).
- GPU: Apple M4 (GPU - 10 cores), METAL. Turnarounds 6.9-8.9 s, expressions 6.5-8.3 s (avg ~6.8 s),
  close-up 9.8 s. Whole run 146 s.

### Hair: much better, not done yet
- No more scales, spikes or lopsided pile. At phone size it reads as a short, neat, tidy cut.
  Volume is balanced left/right, and the sides are short and close to the skull.
- Close-up issues:
  - The fringe edge is a hard, jagged line straight across the forehead (a "helmet" edge),
    not a soft hairline. It needs a thinner, sparser edge or shorter tips feathering into skin.
  - Strands read as painted strokes / flat cards rather than individual strands, especially on top.
    They have no sheen variation.
  - Behind the ear the hair ends in a dark shell edge with a small notch and a bluish, shiny patch.
    It looks like a cap rim, not a taper.
  - The side part isn't visible from 3/4 front. It reads as combed forward / a crop.
- Skin showing through: no bald gaps at the temples now. The back/sides (side turnaround) look like
  a clean undercut. That's fine if intended.

### Expressions (phone size)
- Clearly better: curious (raised brow + half-smile), puzzled (asymmetric brow/mouth),
  thinking (head tilt, eyes up), relief smile (soft eyes + smile), disgusted (lowered brow,
  raised lip). All distinct now.
- Still alike: neutral / chew / swallow. Chew and swallow need a visible jaw or throat cue.
- thumbs up: chest-up now and the thumb reads. The hand is close to the left frame edge;
  frame slightly tighter / more centred.
- Teeth: still sparse/gappy lower teeth in surprised, scared and yawn.
- Tearing: none seen at eyelids or mouth corners.

### Eyes and skin
- Catchlights: clear and bright in both eyes now; the eyes read wet and alive.
- Skin: pores and stubble visible in the close-up; much less waxy. The forehead is still a little
  smooth and shiny. No cyan rim glare.
