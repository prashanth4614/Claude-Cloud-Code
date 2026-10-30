# Codex answer: 005-final-render-plan

_model: gpt-6.1-sol, reasoning effort: high, read-only, cap 600s_

**All-Cycles: agree. Multi-GPU first: disagree. Recovery matters more than saving two hours on this pilot.**

1. **Arithmetic:** your frame timings total **2.66–3.76 GPU-hours**, costing **$0.91–1.28 community / $2.37–3.35 secure**, at your quoted rates, before overhead. Your stated M4 scaling actually predicts ear **12–15 s**, map **6–7.5 s**, Max **3.2–4 s**, sky **5.2–6.5 s**. City remains unmeasured. Plausible estimates; weakest assumptions are uniform GPU speedup, hair/BVH CPU work, and startup amortization. EEVEE arithmetic is correct: **24–47 minutes, $0.13–0.27**; its speed remains unproven.

2. **Look:** keep Cycles for tissue, eardrum and Max. Nothing requires EEVEE; ear_map could tolerate it after comparison. Saving roughly $0.70–1 doesn’t justify material retuning. **64 samples is a candidate, not a quality guarantee**: hair shimmer and denoised SSS need animation review.

3. **Hardware:** one 4090 is cheapest in engineering time. Two/four ideally yield **80–113 / 40–56 minutes**, plus overhead and contention. Same-pod workers share upload but duplicate RAM and compete for CPU/disk; several pods duplicate provisioning and uploads. Availability cannot be assumed. At your rates, 5090 must exceed **2.03×** 4090 throughput to win dollars/frame; L40S **2.32×**. L40S mainly buys memory.

4. **Benchmark:** use **8–16 adjacent frames per set**, including POP, translucent drum and moving hair. Record cold/warm total time, peak RAM/VRAM and PNG size. Your $0.10 buys ~17.6 minutes on one community 4090. Guard = measured workload ×1.3 **plus boot/upload/download**.

5. **Settings to test:** adaptive threshold **0.01**, minimum **16**, maximum **64**; raise difficult shots to 128–256. Compare GPU OIDN with OptiX using albedo+normal inputs ([sampling docs](https://docs.blender.org/manual/id/5.2/render/cycles/render_settings/sampling.html)). Start total/diffuse/glossy/transmission/transparent bounces **8/3/4/8/8**, caustics off; avoid aggressive clamping or bounce cuts around tissue ([light paths](https://docs.blender.org/manual/sr/latest/render/cycles/render_settings/light_paths.html)). Persistent data on; tile **2048** initially ([performance](https://docs.blender.org/manual/id/5.2/render/cycles/render_settings/performance.html)). Preserve close-up hair; test children **70→35** only on wider shots.

6. **Runner blockers:** [render_runpod.py:81](/Users/prashanthmogili/Claude-Cloud-Code-codex/cloud/render_runpod.py:81) defaults to Blender 4.5; pin matching 5.2 patch/checksum. Explicitly set Cycles. Bundle untracked blends/textures/fonts. Verify OptiX actually renders; [5.2 requires driver ≥575](https://docs.blender.org/manual/es/5.2/render/cycles/gpu_rendering.html). Size disk from measurements. [Result-only download then deletion](/Users/prashanthmogili/Claude-Cloud-Code-codex/cloud/render_runpod.py:143) loses partial frames: checkpoint atomic, validated PNGs externally. Client death defeats `finally`; add an independent deletion watchdog. Multi-GPU needs explicit device pinning: [current selector enables every GPU](/Users/prashanthmogili/Claude-Cloud-Code-codex/shorts/blender/review_render.py:48).

**Rank:** benchmark → one community 4090; secure fallback. Deadline-driven: two same-pod 4090s with balanced contiguous chunks; separate pods next. Encode/mux locally after retrieval.

Unresolved: deadline? Benchmark results?
_took 136 s_
STATUS: OK
