# Train step-off: AI 3D tools and free assets (research 2026-10-31)

Web research only. Nothing signed up for, generated, downloaded or bought. Prices change often; check them again before paying.

## Bottom line
- **Higgsfield cannot make 3D itself.** Its official Blender add-on does have a "3D Model" tab (text or image to mesh, placed in the open scene), but that tab runs **Meshy 5** in Higgsfield's cloud and spends Higgsfield credits [1][2]. Installing the add-on costs nothing extra (no separate subscription), but every generation uses credits. Its Scene Builder adds editable geometry, not an AI re-render of the viewport. Buying Meshy directly is cheaper and has a clearer licence.
- **Coach:** start from a free **CC-BY Mumbai local model on Sketchfab** (Bhaktraj's coaches, see §4), then clean it up and re-texture it in Blender. Model the cab and the speedometer dial by hand (or procedurally). AI meshes are weak at straight, repeated hard-surface detail.
- **Platform:** build the slab, canopy and benches by hand from primitives (quick and clean). Use CC0 Poly Haven props and textures for dressing. AI tools (Meshy Pro, or local TRELLIS.2) only for odd props.
- **Crowds:** CC0 **Quaternius Universal Base Characters** (already rigged and animated) or Blender Studio's CC0 Human Base Meshes, dressed in Indian clothes. Meshy's rigging (0 credits) can rig AI-made one-off people.
- **Licence traps:** free tiers of Meshy and Tripo are CC-BY or public; Hunyuan3D bars the EU, UK and South Korea (India is allowed); TRELLIS.2 is MIT, but its background-removal dependency is non-commercial.

## 1) Higgsfield and 3D

| Item | Finding |
|---|---|
| Standalone image/text-to-3D on site | None found; the site is image and video tools. 3D only via the add-on |
| Blender add-on | **Real.** Official page live [1]. The blog says "Introducing Higgsfield in Blender" on 25 Aug 2026 (third-party [4][5]); the blog page metadata says 28 Oct 2026 [2]. Needs Blender 5.1+ [1] (one guide says 4.2–5.1 [5], unverified) |
| What it does | Tabs: Scene Builder (objects, layout and lights as editable geometry), 3D Model (prompt or photo → mesh at the 3D cursor; vendor claims "quad topology, unwrapped UVs", PBR), Character Animation (rigged characters with keyframes), Image, Video, Camera, Asset. Has an MCP "Bridge" [1][2] |
| Restyle or AI render of viewport | Not on the official pages |
| 3D engine | Meshy 5 [1] |
| File formats | Results come in as Blender objects; formats not named [1][2] |
| Cost | The add-on is free to install, but every generation spends account credits; "unlimited" plans do not cover integrations (press [3]) |

## 2) Higgsfield plans and commercial use

| Plan | $/mo | Credits/mo | Commercial |
|---|---|---|---|
| Free | 0 | none (limited image models) | **No** per pricing page; files are watermarked |
| Starter | 15 | 200 | Yes |
| Plus | 49 | 1,000 | Yes |
| Ultra | 129 | 3,000 | Yes |
| Team | 79/seat | 1,000/seat | not stated |
| Scale | 215/seat | 2,500/seat | not stated |

Source: the official pricing explainer, dated 24 Oct 2026 [6]. Prices vary by region.

Terms of Use (updated 23 Oct 2026) [7], §4.4: *"Company does not claim ownership of any of your Inputs or Outputs, nor does it restrict your commercial use of Outputs"*; *"Your rights in Outputs you have generated and exported survive cancellation of your subscription."* Also in §4.4: outputs *"may be used by Company to train…"* and may be used in Higgsfield's own marketing (you stop this going forward by deleting the content or the account). §5.5 requires AI disclosure where the law requires it.
**Ambiguity:** the Terms contain no free-plan restriction, but the pricing page says the free plan has no commercial use, and free files carry a watermark [6][8]. For monetised work, use a paid plan.

## 3) Real 3D generators

| Tool | Hard-surface (coach/bench/sign/dial) | People | Topology/UV | Auto-rig | Commercial licence | Cost | Local on M4? |
|---|---|---|---|---|---|---|---|
| **Hunyuan3D 2.1** (latest open weights; Omni = controllable variant; 3.x appears to be cloud-only, unverified) | Good shapes, soft edges, no crisp grilles or text | OK as statues | Dense triangles, needs remesh | No | Community licence: Territory *excludes EU, UK, South Korea*; India OK; >1M MAU needs a Tencent licence; no claim on outputs [9] | Free | Community MPS port works (~12 GB weights); texturing reportedly needs ~38 GB RAM [10] |
| **TRELLIS.2-4B** (Microsoft, Dec 2025) | Among the best open models; PBR GLB | OK | ~200k triangles after decimation, auto-unwrapped (xatlas) | No | Code and weights MIT; **RMBG-2.0 is CC-BY-NC** (supply pre-masked images or swap it out); DINOv3 has a Meta licence [11][12] | Free | Official repo needs Linux + 24 GB NVIDIA [11]. Community `trellis-mac` port: ~5 min per asset on M4 Pro 24 GB, ~18 GB peak [12] |
| **Meshy** (7.1 / 6) | Good; best UI and remesh | Good, plus rigging | Remesh to quads (0 credits) | **Yes, 0 credits** (humanoid) | **Free = CC BY 4.0** (credit required); Pro and up = private, full commercial [13] | Free 100 credits/mo; image-to-3D 20 credits; Pro ~$20/mo (third-party) | Cloud only |
| **Tripo** | Good, sharp | Good | Smart low-poly / quad options | Yes (vendor; not checked here) | Free = public models; official help says commercial use needs a paid plan (others say CC-BY) [14] | Free ~300 credits; Pro ~$19.90 (third-party) | Cloud only |
| **Rodin (Hyper3D)** | Strongest detail and quads (reputation) | Good | Quad mode | Not confirmed | Paid plans get "broader usage rights"; free plan unclear [15] | Free = pay per result ($1.50/credit); Creator $30 ($24/yr); Business $120 | Cloud only |

Quality notes come from vendor claims and community reputation, not our own tests. None of these tools gives a correct Mumbai EMU livery, grilles or text; plan to fix those in Blender.

## 4) Free assets

| Asset | Link | Licence | Notes |
|---|---|---|---|
| Mumbai local train coach with interior 2 (Bhaktraj) | https://sketchfab.com/3d-models/c58746c869564749a372cd6b93670740 | CC-BY | 467k faces, has interior, uploaded Oct 2026. Best lead |
| Mumbai Local Train Coaches (Bhaktraj) | https://sketchfab.com/3d-models/08265ee100074880887cf80d7c60a48c | CC-BY | 183k faces, textured; no seats, grilles, doors, pantograph or cab |
| free indian train EMU coach (routestore6) | https://sketchfab.com/3d-models/164ca0dfbc40491a9c489bac047b22b3 | CC-BY | 23k faces, low-poly |
| mumbai local train (rmihir560) / old local (sunnykhude) | …/9f540a6af4bf4b379f5d30000c63ff44, …/15c8b2a8f9ee41a1835b34dae5d9d736 | CC-BY | 2.8k and 336 faces; blockout only |
| Indian railway station platform (vigneshmsj) | https://sketchfab.com/3d-models/08e24117bfb24212b10721284f4d0ba2 | CC-BY | 1k faces, made on mobile; reference only |
| PSX Indian railway station | https://sketchfab.com/3d-models/36eb6355d3454e3bb16a970dc8c3237c | CC-BY | 12.6k faces, stylised |
| Indian Railway Track Terrain (modular) | https://sketchfab.com/3d-models/d28410e9954a4221b630b0f9ab3f2fb8 | CC-BY | 874 faces |
| Kenney Train Kit | https://opengameart.org/content/train-kit | CC0 | ~50 low-poly trains plus spline track; not Indian |
| Poly Haven models and textures | https://polyhaven.com/models | CC0 | No benches found; has lights, crates, signs, plus concrete and metal textures |
| Quaternius Universal Base Characters | https://quaternius.com/packs/universalbasecharacters.html | CC0 | 6 rigged, animated bodies; FBX, glTF, .blend |
| Blender Studio Human Base Meshes v1.4.1 | https://www.blender.org/download/demo-files/ | CC0 | 17 meshes; need clothes and rigging |

Avoid these (non-commercial): "Indian Train Guard Coach" (CC-BY-NC-ND) and Sketchfab "Railway Platform" by Cribbleclouds (CC-BY-NC). I found no CC-BY Sketchfab Mumbai EMU that is clearly broadcast quality; inspect the Bhaktraj models before relying on them. BlendSwap had no Indian EMU in these searches. Speedometer dials on Sketchfab are car gauges; model ours by hand.

**Sketchfab licences:** the brief assumed Sketchfab "Standard" licences are not free for commercial use. That looks wrong. Sketchfab's help centre says Standard (including "Free Standard" downloads) allows commercial use in all media but bans reselling the model; **Editorial** is news and public-interest only, with no commercial use [16]. I saw this in search snippets only; the licence page would not load, so read it before use. The Sketchfab Store has closed [16]. Every CC-BY asset needs credit in the YouTube description.

## Sources
1. https://higgsfield.ai/plugins/blender
2. https://higgsfield.ai/blog/higgsfield-blender-plugin
3. https://digitalproduction.com/2026/09/23/higgsfield-brings-ai-generation-into-blender-oh-goodey/ (press)
4. https://explainx.ai/blog/higgsfield-blender-mcp-ai-blockout-august-2026 (third-party)
5. https://rar.design/posts/higgsfield-blender-plugin-guide (third-party)
6. https://higgsfield.ai/blog/higgsfield-pricing-explained
7. https://higgsfield.ai/terms
8. https://higgsfield.ai/creator-hub/help-center/account-and-privacy/who-owns-my-generations-and-can-i-use-them-commercially
9. https://huggingface.co/tencent/Hunyuan3D-2.1/blob/main/LICENSE ; https://github.com/orgs/Tencent-Hunyuan/repositories?q=3D
10. https://raw.githubusercontent.com/VladimirTalyzin/hunyuan3d-2.1-mac/main/README.md ; https://eliteaiadvantage.com/blog/run-ai-3d-model-generation-locally-mac (community)
11. https://github.com/microsoft/TRELLIS.2
12. https://github.com/shivampkumar/trellis-mac (community)
13. https://docs.meshy.ai/en/webapp/pricing
14. https://www.tripo3d.ai/help/privacy-policy/how-to-use-tripo-models-commercially ; https://costbench.com/software/ai-3d-generation/tripo-ai/ (third-party)
15. https://hyper3d.ai/pricing?lang=en
16. https://help.sketchfab.com/en/articles/16152221-choosing-your-model-s-license ; https://help.sketchfab.com/en/articles/16152225-store-license-usage-faq
17. https://quaternius.itch.io/universal-base-characters ; https://opengameart.org/content/train-kit ; https://polyhaven.com
