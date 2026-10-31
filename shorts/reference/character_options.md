# Free host-character options for Blender (Cycles) Shorts — licence check (2026-10-31)

This is web research only: no installs, downloads or spending. I read the official pages where they
could be reached; where I only had forum or press sources, the table says so.

| Option | Licence for monetised renders | Mac (Apple silicon) | Path into Blender and face rig | Verdict |
|---|---|---|---|---|
| **Epic MetaHuman** (UE 5.6+) | **Allowed.** MetaHumans may be used "with any engine or creative software", free under $1M revenue, with UE standard terms above that [1][2]. *Ambiguous:* the official page needs a login; the exact "render outside UE" wording (a UE seat above $1M) comes from a quoted FAQ, not Epic's text [2]. | **Weak.** Creator in the editor works on Mac only from **UE 5.7** (not 5.6) [3][4]. Recommended: 16 cores, **32 GB RAM**, M2 Ultra-class GPU; M1 can't render hair strands [5]. Install size isn't official (third-party sites say 50 GB; users advise 200 GB free) [6]. A MacBook Air is below spec. | Poly Hammer **Character DNA** (free base edition, GPLv3, ARM macOS, Blender 4.5–5.2, still in open beta) imports the DNA files with the real rig logic and face board [7]. **Not ARKit:** the face is a rig-logic board. ARKit 52 needs a mapping or a third-party exporter (Fab plugins; unverified) [8]. | Best quality, but the Mac and hardware route is risky. |
| **Daz Genesis 9** | **Allowed.** The EULA lets you "use, copy and modify the Content in the creation… of two-dimensional animations and renderings" and "publish… sell… distribute" them [9]. Exporting the 3D content is fine for your own use; redistributing it isn't [9]. *Ambiguous:* there is an AI clause that excludes feeding the content into AI tools that generate derivatives [9]; driving the face with MediaPipe should be outside it, but that is not stated. | Daz Studio runs on Apple silicon, apparently not natively (Rosetta, slow); no official native build found [10]. | Diffeomorphic is recommended over the official bridge for Blender 5 [11]. FACS morphs are ARKit-compatible per users, with gaps (eyelashes, eye bones) [12]. | Good realism, but a heavy pipeline and Windows-leaning. |
| **MPFB2** (current) | **CC0** core assets ("do what you like") [13]. Some asset packs are **CC-BY**, so check each one [14]. | Native: it's a Blender extension. | Latest **v2.0.18** [15]. Since 2.0.15–2.0.16 it ships **54 ARKit face-unit shape keys**, visemes and a MakeExpression panel; the release notes say the shape keys still need polish [16]. | Already ours; fully clear legally. |
| **Blender Studio characters** | **CC-BY**: credit the rig and the Blender Foundation [17][18]. | Native. | Rigged and render-ready, but **stylised** (e.g. Vincent, Alpha), not realistic humans [17][18]. | Good for a cartoon host only. |
| **Mixamo** (Adobe) | Royalty-free for commercial projects; the assets can't be redistributed on their own [19]. | Web. | FBX bodies, **no face rig**. | Body animation only. |
| **MediaPipe Face Landmarker** | **Apache 2.0** (code samples and model card) [20][21]. | Python/Web; runs on Mac. | Outputs **52 blendshape scores** (ARKit naming) from IMAGE, VIDEO or LIVE_STREAM [20]. | Use it to drive ARKit keys on MPFB or Daz. |

## Recommendation

Stay on **MPFB2**, and upgrade the face rather than the character: use MPFB's 54 ARKit units, driven
by MediaPipe from a webcam take, then fix the weak units. That is free, CC0 and Mac-native.

Treat MetaHuman as a later upgrade, once there is a Windows box or a 32 GB+ Mac on UE 5.7+.

Daz is legal for our use, but adds a slow Mac app and an unclear AI clause.

## Sources

1. https://www.metahuman.com/license (redirects to a login)
2. https://forums.unrealengine.com/t/can-i-render-metahumans-in-a-3rd-party-dcc/483958 and https://digitalproduction.com/2026/07/22/character-dna-goes-free/
3. https://forums.unrealengine.com/t/unable-to-access-metahuman-on-mac-5-6/2557332
4. https://dev.epicgames.com/documentation/metahuman/hardware-requirements
5. https://dev.epicgames.com/documentation/metahuman/metahuman-hardware-requirements-in-unreal-engine
6. https://dev.epicgames.com/documentation/unreal-engine/macos-development-requirements-for-unreal-engine and https://www.systemrequirementslab.com/cyri/requirements/unreal-engine-mac/23529
7. https://digitalproduction.com/2026/07/22/character-dna-goes-free/ and https://www.cgchannel.com/2026/03/metahuman-dna-add-on-for-blender-gets-new-rbf-editor/
8. https://forums.unrealengine.com/t/metahuman-dcc-blender-or-fbx-export/2544434/3 and https://www.fab.com/listings/88fa82af-3210-42e1-81f0-9a613da436ef
9. https://www.daz3d.com/eula
10. https://www.daz3d.com/forums/discussion/comment/9056276
11. https://www.daz3d.com/forums/discussion/589181/
12. https://www.daz3d.com/forums/discussion/comment/8867521
13. https://static.makehumancommunity.org/about/license.html
14. https://static.makehumancommunity.org/assets/assetpacks.html
15. https://github.com/makehumancommunity/mpfb2/releases
16. https://static.makehumancommunity.org/mpfb/releases/release_2015.html and https://static.makehumancommunity.org/mpfb/releases/release_2016.html
17. https://studio.blender.org/characters/alpha/
18. https://studio.blender.org/blog/new-the-character-library
19. https://helpx.adobe.com/en/creative-cloud/faq/mixamo-faq.html
20. https://developers.google.com/edge/mediapipe/solutions/vision/face_landmarker
21. https://storage.googleapis.com/mediapipe-assets/Model%20Card%20Blendshape%20V2.pdf
