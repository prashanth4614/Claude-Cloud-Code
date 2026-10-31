IMAGES: assets/characters/max/review/max_v5_turnaround.jpg assets/characters/max/review/max_v5_expressions.jpg

# Max: a patch for shirt realism (011 split: shirt only, patch only)

The earlier request 011 timed out while exploring. **Answer with the patch, not exploration.** Read
`shorts/blender/max_look.py` (`upgrade()`). The shirt is `Max.male_casualsuit06` (an MPFB clothing proxy,
a recoloured teal tee plus jeans; its material is a textured Principled with a normal map). It reads flat.
Blender 5.2, Cycles.

**Write one function, `upgrade_shirt(rig)`, to be called from `upgrade()`:**
- a fabric material: roughness about 0.65, sheen about 0.15, a fine knit bump about 0.03 mm (procedural);
- tension folds at the shoulders and armpits and a gentle drape at the belly, with no cloth sim: masks
  from object-space positions relative to the armature's bones (`upperarm`, `spine`, ...) driving a
  procedural fold normal or bump;
- hem and collar thickness, about 1.5 mm, if it's cheap (Solidify on a vertex group, or skip it with a
  reason).

It must survive posing (thumbs-up, arm to ear) and keep the teal colour and the existing texture.

Give the complete Python code, the exact insertion point, one verification render, and the risks. Under
600 words plus code.
