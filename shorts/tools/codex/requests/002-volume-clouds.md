Read-only. Blender 5.2 Cycles, bpy. Short answer (under 350 words), concrete settings.

Context: `shorts/blender/sets/airliner.py` (realistic_sky) makes cumulus as solid subdivided ellipsoid
"lobes" (3-5 per cloud, ~80 clouds, sizes 3-9 m) with a Principled BSDF + displacement. Surface clouds
look like marshmallows/bean bags. I'm switching the lobes to VOLUMES: each lobe mesh keeps its closed
ellipsoid shape but gets a material with only a Volume output: Principled Volume, density =
clamp(1 - |generated_coords - 0.5| * 2, 0, 1) shaped by a 3D noise (detail ~8), anisotropy ~0.6, white,
plus scene.cycles.volume_bounces = 2. The distant cloud deck stays a displaced surface. Shots: a jet
flying just above the deck at golden hour (camera 2-30 m from clouds), and a high aerial (~80 m above).
Renders: Mac M4 Metal for review (needs ~15-30 s/frame at 540x960, 64 samples) and RTX 4090 final.

Answer:
1. Is this the right approach, or is there a clearly better cheap one in Cycles 5.x (e.g. one big
   domain with a density texture, VDB, the Blender 5 "cloud" generators / geometry-nodes volume)?
2. Exact node setup to get soft wispy edges + dense bright cores (falloff shaping, noise scale vs a
   3-9 m lobe, density value) without the lobe's ellipsoid silhouette showing.
3. Render settings that keep cost sane: volume_bounces, volume step rate / max steps, homogeneous vs
   heterogeneous, light tree, anything Metal-specific.
4. Pitfalls (generated coords on scaled/rotated objects, overlapping lobes doubling density, shadows on
   the deck, the sun lamp vs HDRI).
