Final-render plan for the ear-pop pilot on RunPod (owner's decision: final render on RunPod only).
Answer under 450 words. Check my numbers and argue where the plan is weak.

## The job
- 1,420 frames (47.4 s, 30 fps), 1080x1920, Blender 5.2 file built by `shorts/pilot_ear_pop/build_previz.py`.
- Frames per set: ear_inside 660 (wet SSS tissue, translucent eardrum, glowing beads, POP flash);
  ear_map 270 (x-ray map, simple); cabin with Max 327 (particle hair 1800 guides x 70 children, skin,
  ARKit face); sky 105 (airliner + displaced cloud deck, no volumes); city 58 (dusk, emissive windows).
- Pipeline facts: `cloud/render_runpod.py` (one pod, gpuCount 1 today, bundles the repo + uploads,
  bootstrap ~0.7 min, `--max-minutes` guard, pod always deleted). Existing per-set cache of .blend files.

## Measured data
- Old simpler ear-pop film on RunPod RTX 4090 (secure $0.89/h): EEVEE 24 spp, 1080x1920: 0.43 s/frame.
- This film on the owner's Mac M4 10-core GPU, Cycles "look" (50% res, 64 spp, Metal), per frame incl.
  startup share: Max close-ups ~8 s; sky ~13 s; ear_map ~15 s; ear_inside ~30 s.
- This film, Mac EEVEE 50% res 4 spp: 3.4 s/frame average (hair-heavy shots slowest).
- RunPod community today: RTX 4090 $0.34/h, RTX 5090 $0.69/h, L40S $0.79/h; secure 4090 $0.89/h.

## My estimate (4090 ~ 8-10x the M4 in Cycles OptiX; full res = 4x pixels)
- Cycles 64 spp + adaptive + OptiX denoise, full res: ear_inside ~10-15 s, ear_map ~5 s, Max ~3-4 s,
  sky/city ~4-6 s per frame => ~2.5-3.5 GPU-hours => ~$1.0-1.2 community, ~$2.5-3 secure.
- EEVEE full res 32 spp: ~1-2 s/frame => 25-50 min, ~$0.15-0.3.
- Hybrid (Max + sky in Cycles, ear in EEVEE) saves only ~$0.7 vs all-Cycles.

## My draft recommendation
1. All-Cycles (consistent look across cuts within a set; the ear tissue, eardrum and Max's hair/skin are
   exactly where Cycles wins; the saving from a hybrid is under $1, not worth the mismatch risk).
2. One pod with 2-4x RTX 4090 (community), one Blender process per GPU on interleaved frame ranges
   (not one Blender using all GPUs), PNG frames (resumable: skip existing), encode + audio mux at the end.
   ~45-90 min wall clock, ~$1-1.5. Fallback 1x 4090 (~3 h, same cost) or secure if community is empty.
3. Before the full run: a ~$0.10 benchmark pod rendering 1 frame per set at final settings, to replace
   the estimates with measured s/frame and set `--max-minutes` with 30% margin.

## Questions
(1) Are the s/frame estimates plausible for these scene types? Where am I most likely wrong?
(2) All-Cycles vs hybrid: agree? Any shot that must be one or the other?
(3) Multi-GPU single pod vs several 1-GPU pods vs one big GPU (5090/L40S): which is cheapest and
    fastest overall, counting boot/upload overhead and community availability risk?
(4) Settings that cut Cycles time without visible loss (samples, light paths, hair, denoiser, caustics,
    persistent data, tile size), and which to avoid for hair and SSS.
(5) Failure modes on RunPod to guard against (pod loss mid-render, disk, fonts, GPU OptiX/driver,
    Blender 5.2 download), and your final ranked plan.
