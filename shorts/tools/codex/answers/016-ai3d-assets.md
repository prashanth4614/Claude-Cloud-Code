# Codex answer: 016-ai3d-assets

_model: gpt-6.1-sol, reasoning effort: high, read-only, cap 1200s_

**Verdict: Higgsfield can generate Blender meshes, but I wouldn’t buy it for this Short.** The helper’s “cannot make 3D” headline is misleading: its Blender plugin uses **Meshy 5**, importing geometry and materials. That proves capability, not production quality. Useful optional roles: owner-made lighting concepts, composition boards and approved background props. Keep final shots in Cycles. [Official plugin guide](https://higgsfield.ai/blog/higgsfield-blender-plugin)

My recommendation: source the train, build the contact geometry, reuse our character ecosystem. No generated assets have been tested here; quality risks below are production judgments.

| Asset | Best route | Quality risk; estimated artist time |
|---|---|---|
| **EMU exterior, open doorway, interior** | Inspect the Bhaktraj coach listed in the research; use as a base if suitable. Rebuild the visible doorway, threshold, handrails and nearby interior. Instance simpler coaches for the drone opener. | **High:** warped panels, missing interiors, wrong proportions or flat textures become obvious beside Max. **6–12 h** if usable; **1–2 additional days** if replacement modelling is needed. I couldn’t independently verify its download/licence page. |
| **Platform, edge, gap** | Model in Blender; use licensed concrete/metal textures. Make platform height, threshold and gap consistent with one chosen train reference. | **Critical:** floating shoes or an implausible gap undermine the physics. **2–4 h**, including contact checks. Don’t generate this geometry. |
| **Cab speedometer** | Model the visible console section, dial, glass and separate animated needle. Follow the white-dial/blue-console reference noted in `research.md`. | **Medium:** unreadable ticks, excessive reflections, needle inconsistent with train motion. **1–2 h**; no whole cab needed. |
| **Crowd extras** | Reuse MPFB/MakeHuman bodies with varied faces, clothing and poses. Quaternius only for distant figures. | **High near camera:** different proportions and faceted faces break the shared world. **3–5 h** assuming usable clothing. Quaternius is CC0, but that doesn’t establish a visual match. [Asset page](https://quaternius.com/packs/universalbasecharacters.html) |

**AI close-up failures, ranked by damage:**

1. **Wrong structure:** fused door openings, invented backsides, uneven repeated windows. Rebuild hero surfaces; remeshing cannot recover missing design.
2. **Baked lighting:** shadows and highlights painted into colour textures fight our moving lights. Replace with clean base colour and consistent roughness/normal maps.
3. **Topology:** dense irregular surfaces produce lumpy reflections; automatic quads don’t guarantee useful deformation around shoulders or hands.
4. **UVs and scale:** stretched seams, inconsistent texture detail, arbitrary dimensions. Rescale against Max, repair UVs and rebake.
5. **Asset inconsistency:** unify materials and ink-and-amber lighting **before** grading. Distance, occlusion and modest depth of field can hide background defects; never hide the foot-contact explanation.

Meshy, Tripo or local generators remain candidates for incidental props—not the train doorway, gauge or acting characters. Cleanup can erase generation’s time saving.

**Licensing/monetisation:** record each downloaded licence. CC-BY requires attribution, licence link and modification notice; uploader rights still matter. [CC-BY terms](https://creativecommons.org/licenses/by/4.0/) Meshy currently permits free-tier commercial use with attribution; paid outputs are private. [Meshy licensing](https://docs.meshy.ai/en/webapp/pricing) AI itself isn’t the decisive YouTube risk: repetitive production and dangerous-act glorification are. Keep original explanation, non-graphic falls and “wait for a full stop.” [Monetisation](https://support.google.com/youtube/answer/1311392), [ad guidelines](https://support.google.com/youtube/answer/6162278)

**Plan/cost:** cap coach inspection at one hour; then commit to sourcing or rebuilding. Validate doorway/contact, dial and crowd test frames before animation. Estimate **14–26 artist hours**, excluding fallback modelling and animation; **₹0 assets/tools**. Benchmark representative Cycles frames before paid rendering; ₹15–90 is the existing pipeline estimate, not a train-scene quote.

Unresolved: coach suitability/licence; render benchmark.
_took 103 s_
STATUS: OK
