IMAGES: assets/characters/max/review/max_v5_hair_closeup.jpg assets/characters/max/review/max_v5_ear_pop_closeup.jpg

# Max: a patch for a tear meniscus and caruncle (011 split: eyes only, patch only)

The earlier request 011 timed out while exploring. **Answer with the patch, not exploration**: at most a
few quick reads. Read `shorts/blender/max_look.py` (`upgrade()`, `upgrade_eyes()`) and
`shorts/blender/max_hair.py` (`follow_face()`, which copies body face shapes onto a mesh built from body
vertices and drives them from the body's sliders).

Max is MPFB2: the body is `Max.body` (81 shape keys including the ARKit 52; armature `Max`), and the eyes
are `Max.high-poly` (one textured Principled with a coat). Blender 5.2, Cycles.

**Write one function, `add_eye_wetness(rig, body)`, to be called at the end of `upgrade()`:**
- **Tear meniscus:** a thin wet ribbon (0.15-0.25 mm) along each lower lid margin, where lid meets
  eyeball. Material: Principled, roughness 0.03, IOR 1.336, transmission 1.
- **Caruncle:** a small moist pink patch at each inner corner, made of pink wet tissue, roughness 0.2.
- Both built from body vertices selected robustly (say how: e.g. body vertices within X mm of the
  `Max.high-poly` eyeball surface and below its centre for the lower lid), skinned with the body's
  armature weights, and following the blink, squint and wide shapes via `follow_face`.
- They must not show as a hard line at phone size, nor z-fight with the eye.

Give the complete Python code, the exact insertion point, one verification render (camera, expression),
and the risks. Under 600 words plus code.
