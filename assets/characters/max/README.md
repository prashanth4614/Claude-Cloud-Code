# Max, the recurring host

- `max_reference.png`: the look we match (teal tee, dark jeans, white sneakers, messy dark-brown hair,
  light stubble, big brown eyes, stylized-realistic).
- `max_v4.blend` (current): the rigged 3D Max, everything packed, saved with Blender 5.2. Open it in Blender 5.2 or later; no add-ons needed.
  v4 = v3 + `shorts/blender/max_look.py`: pores, a varied-gloss skin and softer subsurface; wet eyes; finer, denser hair
  (a neat side part since the owner's note: no spikes); 17 expressions. `max_v3.blend` stays for the published pilot.
- `review/`: turnaround and expression sheets for each version (v1: first pass; v2: groomed hair, stubble).
- `textures/max_outfit_diffuse.png`: the CC0 MakeHuman casual suit, recoloured by `shorts/blender/max_textures.py`.

## How Max is built (free)
`shorts/blender/build_max.py` builds him from CC0 MakeHuman assets through the free MPFB2 add-on:
body and phenotype, a stylized push (bigger eyes, defined jaw), skin, brown eyes, brows, lashes, teeth,
the recoloured tee and jeans, white shoes05 sneakers, and the default
skeleton (fingers, jaw, neck, eyes).

Hair and stubble are particle grooms combed from code (`shorts/blender/max_hair.py`): ~3k guide
strands with interpolated children for a neat dark-brown side part (v4: the top combed back and over with a
low quiff, short tidy sides and back, strands kept close to the skull, no spiky clumps), very short stubble on the jaw, chin and upper lip that moves with the face shapes, and a dark
scalp cap underneath. Change the look with the constants at the top of that file.

His face has the **52 ARKit face shapes** (faceunits01 pack) on the body (brows, lashes, teeth and tongue
follow it through drivers), so every expression is hand-keyed by name. The expressions live in `shorts/blender/max_expressions.py`
(neutral, puzzled, curious, thinking, surprised, amazed, scared, wince, ear_pop, disgusted, laughing,
relief smile, swallow, yawn, chew, thumbs-up), asymmetric and at thumbnail strength since v4, each a set of face-shape weights plus a
small head and neck tilt. Change a number there and rebuild, and every shot picks it up.

To rebuild (only needed when changing him):
1. Blender 4.5+, then Edit ▸ Preferences ▸ Get Extensions ▸ install **MPFB**.
2. In MPFB's asset-pack panel, install the CC0 packs: makehuman_system_assets, skins01, hair01,
   eyebrows01, eyelashes01, faceunits01 (static.makehumancommunity.org/assets/assetpacks).
3. `python3 shorts/blender/max_textures.py`
4. `blender -b -P shorts/blender/build_max.py -- --out assets/characters/max/max_v4.blend --sheet out/characters/max/sheet`
   (build_max applies `max_look.upgrade()`; to upgrade an existing file instead:
   `blender -b max_v3.blend -P shorts/blender/max_look.py -- --out max_v4.blend [--sheet DIR]`)

## Posing him by hand in Blender
- Select **Max.body** ▸ Object Data properties ▸ **Shape Keys**: drag `jawOpen`, `eyeBlinkLeft`,
  `mouthSmileLeft`… and press **I** over a slider to keyframe it. The brows, lashes, teeth and tongue
  follow automatically, and the stubble rides on the skin.
- Select the **Max** armature ▸ Pose Mode for the head, neck, arms and fingers.
- The hair shows a few guide strands in the viewport; the full head of hair appears in renders (and in
  Rendered viewport shading). Particle children are set lower in the viewport to keep it fast.
