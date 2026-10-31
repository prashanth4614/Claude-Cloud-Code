IMAGES: assets/characters/max/review/max_v4_expressions.jpg assets/characters/max/review/max_v4_turnaround.jpg assets/characters/max/review/max_v4_hair_closeup.jpg assets/characters/max/max_reference.png

# Make Max, our recurring host, as real as possible (Zack D Films level and beyond)

The owner wants Max "as real as possible", worked to the core. Max is built for free in Blender 5.2 (Cycles):
- the MPFB2 2.0.18 (MakeHuman) body, CC0 assets, the ARKit 52 face units;
- particle hair combed from code;
- the house light rig "ink & amber" (warm key, cool fill, cyan rim, ink-teal world).

Sheets attached:
- v4b expressions;
- the turnaround;
- a hair close-up, after a restyle to a neat side part;
- `max_reference.png`, the target look.

Code, for you to read:
- `shorts/blender/build_max.py`: the build, the materials restyle, the sheet camera;
- `shorts/blender/max_look.py`: skin, eye, teeth and hair tuning, and the light rig;
- `shorts/blender/max_hair.py`: the groom;
- `shorts/blender/max_expressions.py`: the expression library;
- `assets/characters/max/review/max_v4_notes.md`: the render worker's review.

**Constraints:**
- free, commercially usable assets only;
- no image or video generation;
- renders on an M4 MacBook Air (Metal) for reviews, and on RunPod 4090s for finals;
- must stay riggable and animatable (the face units drive everything).

**Answer in under 1200 words, concrete numbers and node names, ranked by realism gained per hour.**

## What I (Claude) think, to argue with
1. **Hair is the biggest gap.**
   - Plan: convert the combed particle guides to a Curves object and build the groom with Blender's
     bundled hair node assets (`procedural_hair_node_assets.blend`):
     Interpolate Hair Curves (≈80-150k strands from the guides) → Clump (subtle, many small clumps) →
     Frizz (tiny) → Set Hair Curve Profile (root 0.06 mm → tip 0.02 mm) → Deform / Attach Hair Curves to
     Surface (so it follows the body with the rig).
   - Principled Hair BSDF, Huang model (or Chiang?), with melanin ~0.85 and redness 0.1-0.15.
   - Is this right? What fails (deformation with the armature, render cost on Metal)?
2. **Skin:** MPFB's ENHANCED_SSS group with pores (strength 0.55), noise-varied roughness 0.40-0.60,
   subsurface 0.32. What else matters most?
   - a real skin detail normal (is any free/CC0 micro-normal suitable?);
   - Random Walk subsurface radius per channel;
   - specular tint;
   - cavity and AO darkening in the creases;
   - a redness map (nose, ears, cheeks);
   - a separate lip material;
   - the eyelid/eye wetness line.
3. **Eyes:** the MPFB high-poly eye is one textured Principled material with a coat added. Is a separate
   cornea bulge plus refraction worth it? What about a limbal ring, an eye-occlusion shadow and caruncle
   wetness?
4. **Teeth** look sparse and gappy (`teeth_base`). Is there a better free option?
5. **Expressions:** FACS realism. Combined units that sell emotion (e.g. the Duchenne smile =
   cheekSquint + eyeSquint, with the lower lid up); which of our expressions look fake and why;
   corrective shapes MPFB lacks.
6. **Lighting and lens** for realism in close-ups:
   - key size and distance;
   - rim strength;
   - eye light;
   - AgX look;
   - depth of field (f-stop for 85 mm at 1 m);
   - film grain.
7. **Anything structural:**
   - the subdivision level;
   - face proportions vs the reference (big eyes from STYLE_TARGETS);
   - the body or clothes look (the shirt reads flat).

Give the top 10 changes with exact values, the order to do them in, and which you'd verify first with a
single close-up render.
