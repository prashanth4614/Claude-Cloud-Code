# Codex answer: 003-asset-sourcing

_model: gpt-6.1-sol, reasoning effort: high, read-only, cap 600s_

**Verdict: mostly agree. Biggest mistake: postponing Max while spending another day on clouds.** Viewers notice facial appeal, clear reactions and convincing silhouettes within one second; polygon counts prove little.

- **A — Replace conditionally: 114k A320.** Inspect nose, engines, wing roots and shading from actual cameras. Reject dubious provenance or lengthy cleanup. Preserve `Jet`/`Jet_gear`; existing [rig assumes ~16 m length](/Users/prashanthmogili/Claude-Cloud-Code-codex/shorts/blender/sets/airliner.py:3), so a correctly scaled import requires reframing. Don’t distort aircraft proportions to fit.
- **B — Keep cabin.** Max’s contact with seat/armrest and window lighting matter more than a million-face interior. Replace only camera-visible seats if close-ups expose weak silhouettes.
- **C — Keep journey; supplement map.** Use direct BodyParts3D ossicles/membrane where helpful. Preserve animated drum/tube. Prioritize readable pressure → bulge → release. **Correction:** the official archive now specifies [CC-BY 4.0](https://dbarchive.biosciencedbc.jp/en/bodyparts3d/lic.html), updated February 2025; don’t inherit Z-Anatomy’s licence assumptions.
- **D — Benchmark free BlenderKit cloud first.** It’s [royalty-free, procedural and Cycles-oriented](https://www.blendkit.com/asset-gallery-detail/0bf13dfc-5729-4b9c-9238-94782c3b7286/). Check emission before judging lighting. Compare identical frames, samples, seconds/frame and memory. VDB isn’t automatically faster. Use distant sky imagery plus sparse foreground volumes when parallax permits.
- **E — Keep city.** At 30 m, roof shapes, street scale and lighting variation sell it. Add two reusable buildings only where repetition becomes visible.
- **F — Keep Max’s rig; upgrade hair now.** Fit licensed clumped mesh/curve hair; refine hairline, eyes and expression silhouettes. More strands won’t establish the desired style.

Bigger return: consistent lighting/material treatment across imported assets. [Poly Haven’s CC0](https://polyhaven.com/license) HDRIs/textures help immediately. [Mixamo](https://helpx.adobe.com/creative-cloud/faq/mixamo-faq.html) saves future body-animation work. Defer Character Creator/ActorCore migration until performance needs justify retargeting. [Fab permits compatible tools](https://www.fab.com/eula); don’t assume the entire Quixel library is free. Normalize approved assets into portable `.blend` collections with textures/VDB dependencies.

Licence traps: save source, author, licence/version and modification notes. “Free Standard” doesn’t mean CC0. Verify uploader ownership; reject game/simulator rips. Remove airline/government markings, but repainting doesn’t clear aircraft-shape rights: [CC grants no trademark/patent rights](https://creativecommons.org/licenses/by/4.0/legalcode.en). [ShareAlike](https://creativecommons.org/licenses/by-sa/4.0/) governs adaptations; don’t assume keeping modified meshes separately settles rendered-output obligations.

**Ranked actions; effort estimates, purchase budgets:**

1. Max hair + face close-up polish: **2–4 h; $0–40**.
2. A320 import/repaint/camera check: **1–2 h; $0**, then evaluate a $20–60 generic if needed.
3. Cloud comparison: **≤1 h; $0 on Mac**. Measure render cost before buying VDBs.

Unresolved questions: none.
_took 171 s_
STATUS: OK
