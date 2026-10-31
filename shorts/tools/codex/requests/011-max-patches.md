IMAGES: assets/characters/max/review/max_v5_hair_closeup.jpg assets/characters/max/review/max_v5_ear_pop_closeup.jpg assets/characters/max/review/max_v5_expressions.jpg

# Max v5: write ready-to-apply patches for three items (we work in parallel)

The owner asked Claude and Codex to work the remaining Max list **in parallel**. You're read-only, so your
output is **patches**: unified diffs, or complete new functions with the exact file and insertion point,
that Claude applies, renders on the Mac and verifies. Claude is doing the teeth and the ear-rim light
at the same time, so don't touch those.

Read first:
- `shorts/blender/max_look.py` (`upgrade()`, `upgrade_eyes()`, `paint_zones()`, `studio()`);
- `shorts/blender/max_expressions.py` and `shorts/blender/build_max.py` (`set_expression`, `pose_head`,
  `aim_bone`, `_key_bones`, `thumbs_up`);
- `shorts/pilot_ear_pop/real_max.py` (how a film animates Max: `face()`, `hand_to_ear`, beats);
- `shorts/blender/max_hair.py` (`follow_face`, the face shapes driven from the body);
- `assets/characters/max/review/max_v5_notes.md`.

Max is MPFB2 2.0.18:
- `Max.body` has 81 shape keys, among them the 52 ARKit units (names as in `FACE_UNITS`); only
  those may be set for expressions;
- the default MPFB rig is the armature `Max` (bones include `head`, `neck01-03`, `jaw`, the `eye`
  bones, fingers);
- the eye mesh is `Max.high-poly` (one material: a textured Principled with a coat);
- clothing is `Max.male_casualsuit06` (a recoloured teal tee and jeans);
- Blender 5.2, Cycles.

## 1. Eyes: tear meniscus and caruncle (`max_look.py`)
- A thin wet strip along the lower lid margin (0.15-0.25 mm, roughness 0.03, IOR 1.336,
  transmission 1) that follows the eyelid shape keys (blink, squint, wide).
- A moist pink caruncle at the inner corners.
- Build them procedurally from the existing geometry: e.g. select the body's lid-margin vertices by
  position relative to `Max.high-poly`'s bounds, make a tube or ribbon, skin it with the same armature
  and shape keys via `max_hair.follow_face`-style drivers.
- Say how to find the vertices robustly. No new asset downloads.

## 2. Chew and swallow motion, so they stop looking like neutral
- Chew: visible jaw motion with sealed lips (jaw bone or jawOpen plus mouthClose/mouthPress
  combinations), and cheek movement. Give a 3-chew keyframe cycle (frames and values) usable from
  `real_max.py`.
- Swallow: a 2-3 mm throat (larynx) rise and return. MPFB has no larynx shape: propose the cleanest
  way (a neck bone nudge, a corrective shape key built by script on `Max.body` from neck vertices
  selected by position, or a displacement/hook). Keyframe it (frames and values).
- Also a static "best single frame" for the expression sheet, so the sheet tiles read as chew and
  swallow.

## 3. Shirt realism (`max_look.py`)
The tee reads flat. Give a procedural upgrade:
- thickness (Solidify about 1.5 mm, only where it shows: collar and sleeve hems);
- a fabric material (roughness about 0.65, sheen 0.15, a fine knit bump about 0.03 mm);
- tension folds at the shoulders and armpits and gentle drape at the belly, without a cloth sim (e.g.
  a procedural normal/bump driven by masks from positions, or a shape key sculpted by script).

It must survive posing (thumbs-up, arm to ear).

## Answer format
For each item:
1. **Patch:** a diff or exact code.
2. **Verification:** one test render per item (camera, frame and what to look for).
3. **Risks.**

Under 1500 words plus code. Correct, runnable Blender 5.2 Python matters more than prose.
