# Codex answer: 010-max-realism

_model: gpt-6.1-sol, reasoning effort: high, read-only, cap 600s_

**Verdict: hair is the biggest gap, but fix the existing groom before converting it.** More strands won’t solve its geometry. Max’s reference also has fuller, wavier hair, rounder facial contours, and warmer coloration; pores alone won’t recover that identity.

Ranked below by expected realism gained/hour; values are starting settings, assuming **1 Blender unit = 1 metre**. All asset spend: **₹0**. Estimates exclude review iterations. I inspected code and supplied renders; Blender startup crashed inside this sandbox, so saved-scene settings remain unverified.

1. **Correct strand width and scalp edge — 30–60 min.**  
   [max_look.py:33](/Users/prashanthmogili/Claude-Cloud-Code-codex/shorts/blender/max_look.py:33) overrides the groom to **3000 × 150 ≈450k children**, with `radius_scale=0.00034`. Particle `root_radius` actually specifies **diameter**: at unit scale, that’s **0.34 mm**. Start `root_radius=1`, `radius_scale=0.00007`, `tip_radius=0.15`, `use_close_tip=True`; retain density for the first comparison. Separately reduce the scalp cap’s **1.5 mm** offset to **0.2 mm**, inset its boundary **5–8 mm**, and blend its color toward scalp skin. The exposed cap likely explains the notch behind the ear. [Particle settings](https://docs.blender.org/api/5.0/bpy.types.ParticleSettings.html)

2. **Fix groom clearance, then silhouette — 2–4 h.**  
   [max_hair.py:270](/Users/prashanthmogili/Claude-Cloud-Code-codex/shorts/blender/max_hair.py:270) grows clearance by **key index**. With 65 keys and `top=1`, its minimum reaches **117.4 mm**, exceeding the intended **72 mm** strand length. Normalize using `t=k/(nk-1)`; start minimum clearance **0.2 mm**, maximum **3+25·sin(πt) mm** on top, **5 mm** on sides. Replace the hard forehead Z clamp with graduated strand lengths. Feather density over **8–12 mm**; add **5–15 mm** baby hairs. For reference matching, try top **90–110 mm**, sides/back **35–50 mm**, rather than the current undercut.

3. **Give skin anatomical variation — 1–2 h.**  
   The current `Noise Texture → Map Range → Roughness` makes random patches, not an oily T-zone. Add painted masks: nose/central forehead **0.35–0.42**, cheeks **0.48–0.56**, with noise only **±0.025**. Apply redness locally to ears, nostrils, and cheeks at **3–8%** blend. Use MPFB’s existing lip zone: roughness **0.32**, restrained coat **0.1**, subtle vertical creases. `upgrade()` currently targets only the exact body material name; audit other slots explicitly.

4. **Make expressions anatomically coherent — 2–4 h.**  
   Relief reads sleepy: reduce `eyeBlink` **0.45→0.1**, smiles **0.85/0.8→0.55/0.5**. Laughing already includes cheeks and squint; adding more won’t fix it. A Duchenne smile needs **mouth-corner pull plus cheek raise**, with convincing lower-lid movement. For puzzled/curious, reduce opposing brow weights toward **0.45–0.65**, head tilt **13°→6°**. Scared/amazed/surprised need distinct lip contours, not just different jaw opening. Add corrective shapes for `jawOpen×smile`, `blink×squint`, and lip seal; start drivers with the **product** of participating weights. Animate swallow through a **2–3 mm** throat rise and return; chewing needs jaw motion under sealed lips.

5. **Improve eyelid contact before rebuilding eyes — 1–2 h.**  
   Catchlights already read clearly. Add a **0.15–0.25 mm** tear meniscus, Principled roughness **0.03**, IOR **1.336**, transmission **1**; make it follow eyelid shapes. Add a moist pink caruncle and actual upper-lid contact shadow. Avoid a fixed black eye-occlusion crescent. Separate corneal refraction is worthwhile for hero close-ups, but first inspect existing eye geometry: don’t accidentally add a second cornea. For a single textured shell, budget another **2–3 h** for iris depth, corneal bulge, and gaze/blink validation.

6. **Repair teeth placement before replacing assets — 1–2 h.**  
   The images establish gaps, but cannot distinguish geometry, texture, or jaw-follow errors. Inspect teeth with a plain clay material at `jawOpen=0/0.5/0.95`. Check lower teeth follow the mandible. Close unwanted visible anterior gaps toward **0–0.2 mm** while preserving individual crowns and gums. Audition `teeth_shape01…05`; these are verified **CC0**, but not guaranteed upgrades. Start enamel roughness **0.25**, coat **0.15**; retain warm off-white coloration. [MakeHuman system assets](https://download.makehumancommunity.org/assets/assetpacks/makehuman_system_assets.html)

7. **Calibrate SSS and pore scale — 1–2 h.**  
   Increasing SSS strength does **not** inherently reduce waxiness. Trace MPFB’s group to its actual BSDF before changing `SSS radius scale=0.12`. For a direct Principled setup, trial **Random Walk (Skin)**, radius **(1, 0.45, 0.2)**, scale **0.0015 m**, weight **1**; judge ears and nostrils. Keep specular tint **white**, IOR **1.4**, IOR Level **0.5**. Target pore spacing **0.15–0.4 mm**, bump distance **0.01–0.03 mm**, masked off eyelids/lips. I found no verified CC0 facial micro-normal worth making a dependency; existing procedural pores suffice initially. Skip baked AO darkening. [Principled controls](https://docs.blender.org/manual/sr/5.2/render/shader_nodes/shader/principled.html)

8. **Improve light direction and lens discipline — 30–60 min.**  
   Trial key **1 m wide, 1.5 m from face**, **35°** sideways, **25°** above; start **150 W**, near-neutral warm color. Reduce cyan rim **140→70 W**, kicker **55→25 W**; keep cyan primarily at silhouette. Existing eye light is adequate. Trial **AgX Medium High→Medium High’s gentler alternative, Medium High disabled via Medium High-to-Medium High?** Use **AgX Base Contrast** for diagnosis. At **85 mm/1 m**, start **f/8**, focus between eyes; full-frame DOF is only roughly **6 cm**. Grain: **0 during diagnosis**, optional **0.3–0.5% luminance** in finishing.

9. **Improve silhouette and clothing geometry — 2–4 h.**  
   Trial face render subdivision **2**, viewport **1**; retain topology and shape keys. Don’t blindly reduce enlarged eyes—the reference also has large eyes. Compare eyelid opening, iris size, cheek volume, and chin length first. Shirt: add **1.5 mm** collar/sleeve thickness, seam geometry, shoulder/armpit tension folds; roughness **0.65**, sheen **0.15**, fine fabric bump **0.03 mm**. Larger folds matter more than weave.

10. **Migrate to Curves after groom repair — 4–8 h.**  
    Convert **guides only**. Use interpolation → small clumps → **0.2–0.5 mm** frizz → profile → attachment/deformation. Start **100–150k strands**, **16–24 points**; profile **radius 0.035→0.005 mm**, not diameter. Bind against neutral, shaped Max with stable UVs; store `surface_uv_coordinate`, then **Attach Hair Curves to Surface before Deform Curves on Surface**, deformation once. Avoid double armature deformation; test ±30° head rotation and brow raise. Set subdivision **UV Smooth=None**. Explicitly choose **Huang**, melanin **0.85**, redness **0.12**, roughness **0.3**, random color **0.1**, random roughness **0.2**; Chiang’s radial roughness/coat controls don’t transfer directly. [Deformation](https://docs.blender.org/manual/en/5.2/modeling/geometry_nodes/curve/operations/deform_curves_on_surface.html), [hair shader](https://docs.blender.org/manual/en/5.0/render/shader_nodes/shader/hair_principled.html)

**First verification:** change strand width only; render the existing **900², 35°, 85 mm, 0.95 m** close-up at **256 samples**, DOF off, lights unchanged. Inspect hairline, ear edge, and strand highlights. Existing baseline: **9.8 s at 64 samples**; allow roughly **40 s** if sampling dominates. Curves speedups remain unmeasured; benchmark MetalRT Auto/On and peak memory before finals.

Unresolved questions: none.
_took 259 s_
STATUS: OK
