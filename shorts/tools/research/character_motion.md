# Character motion research: mocap, falls, face, lip sync

Researched 2026-11-01 (web search only; videos not watched, so summaries come from descriptions, chapters and companion pages). Target: Max (MPFB2 + ARKit 52 keys), Blender 5.2, M4 Mac, all motion from bpy scripts, monetised channel.
**Legend:** OK = commercial use looks fine; NC = non-commercial only; ? = unverified or ambiguous. Not legal advice: re-read each licence before shipping.

## Top 5 to adopt

1. **Own bpy retarget script (Copy Rotation/Location constraints + `bpy.ops.nla.bake`)**: no add-on lock-in, works headless, and gives full control over MPFB2 bone maps. Free. Effort: medium (1-2 days incl. bone map + rest-pose fix).
2. **Mixamo + CMU + Rokoko free clips as the fall/stumble source**: commercial use in videos is allowed (Mixamo: no raw-file redistribution; CMU: "no restrictions" per secondary sources ?). Free. Effort: low once (1) exists.
3. **Scripted foot/hand contact lock (IK targets keyed in world space + hip correction)**: fixes sliding on the platform and the moment of ground impact. Free (DIY), or Mocap Bone Lock (paid, tested 4.2-5.0). Effort: medium.
4. **MediaPipe Face Landmarker (Apache-2.0) to ARKit 52 to shape-key F-curves**: gives real facial reactions from a phone/webcam video of the owner, with no iPhone needed. Free. Effort: medium (offline script, write JSON, bpy keys it). Faceit's free "Face Landmark Link" is an alternative ?.
5. **Rhubarb Lip Sync (MIT, mac builds) to viseme map to ARKit jaw/mouth keys**: script-driven lip sync from the ElevenLabs WAV. Free. Effort: low. (Shorts are mostly VO-over-action; use only when Max talks on camera.)

Runner-up: **Rokoko Vision** (free single-cam, FBX, browser so Mac OK) to capture the owner acting a custom stumble. Commercial terms for the free tier are ?: check the ToS. Avoid SMPL-based research models (WHAM/4D-Humans/GVHMR) for monetised output.

## 1. Tutorials

### Retargeting

| Title | Link | Len | Takeaways | Apply in code |
|---|---|---|---|---|
| Rokoko: Ultimate Blender retargeting guide (written) | rokoko.com/insights/ace-retargeting... | article | Free add-on; manual bone-map list; match frame-0 pose to source T-pose; Rokoko sign-in needed ? | Copy its idea: a JSON bone map (source to MPFB2) and a rest-pose match step before bake. |
| BlenderNation: simplest Mocap to Rigify (Rokoko add-on) | blendernation.com/2023/01/14/... | video+post | Retarget onto Rigify ORG/FK bones, then bake | If Max gets a Rigify control rig, target FK ctrls, then convert to IK for contact fixes. |
| CGDive: Expy Kit, Mixamo to Rigify | classcentral (YouTube) | about 1 h ? | Free (GitHub pKrime/Expy-Kit); batch-retargets many Mixamo actions; good for Rigify IK | Read its source for bone-name presets; batch loop pattern for our action library. |
| Dikko: free mocap files + retarget tools | classcentral (YouTube) | ? | Rokoko retarget to Mixamo/Rigify; cleanup with AnimAide | AnimAide-style smoothing = our own F-curve filter in bpy. |
| Auto-Rig Pro Remap (vendor docs + BVH guide) | superhivemarket.com/products/auto-rig-pro; jac307.github.io/... | docs | Paid; name + orientation matching; set hip as root; BVH scale 0.1; custom bones need manual map | Only if we move Max to ARP; ops are scriptable but proprietary. |
| Manual constraint method | (pattern; several guides) | - | Copy Rotation per bone (world/local), Copy Location on hips only, then bake visual keys | `pose.bones[b].constraints.new('COPY_ROTATION')`, `bpy.ops.nla.bake(visual_keying=True, clear_constraints=True, bake_types={'POSE'})`. Fix rest-pose mismatch with a per-bone offset (store source vs target rest quaternions). |

### Foot sliding / contact

| Title | Link | Takeaways | Apply in code |
|---|---|---|---|
| Blender Artists: fix sliding feet | blenderartists.org/t/.../1620939 | Plant IK foot ctrl, move hips; key IK parent or Child Of to toggle lock | Detect contact (foot height < h and speed < v), key IK target constant through window, blend in/out over 2-3 frames. |
| Foot Flow (free extension) | foot-flow.pages.dev | Contact jitter + floor penetration cleanup; preview then bake | Same algorithm, DIY: clamp foot z >= floor z, lock xy during contact. |
| Mocap Bone Lock (paid) | superhivemarket.com/products/mocap-bone-lock | Non-destructive NLA lock layer; auto contact on flat ground; tested 4.2/4.5/5.0 | NLA layer idea: put correction in a separate additive strip so raw mocap stays untouched. |
| Inverse Lock Bone (paid) | superhivemarket.com/products/inverse-lock-bone | Locks foot by moving hips; both feet need IK rig | For the fall: lock the *hand* on the platform at impact the same way. |

### Falls and stumbles (body mechanics)

| Title | Link | Takeaways | Apply in code |
|---|---|---|---|
| Animation Mentor: fall and recovery (J. Milgate, Nov 2025) | animationmentor.com/blog/2025/11/ | Reference first; block, refine, polish | Shoot owner reference from the shot camera angle. |
| Animation Mentor: slips and recoveries (Sep 2025) | animationmentor.com (?p=86786/88639) | Weight, balance, character drive it | Script COM over the support base: fall starts when COM leaves foot support. |
| Game Developer: centre of mass techniques | gamedeveloper.com/design/center-of-mass-... | COM path drives believability | Compute COM from bone heads weighted by mass; plot it as a debug empty. |
| Fall breakdowns (blogs) | cassiersbitanime.blogspot.com/... | 3 phases: balance loss, gravity descent, impact; stumble = short catch-step near other foot; arc the body | Phases as keyed segments: catch-step(s), ballistic drop (parabolic hips, g = 9.81 in train frame + train velocity), impact with arms out (protective reflex), overlap on head/arms 2-4 frames late. |

Train-specific physics note (our derivation, not from sources): stepping off at speed v, the feet stop on the platform while the torso keeps v, so facing forward = run-out steps; facing backward = fall onto the back/buttocks; sideways = spin. Script the torso keeping train velocity and feet decelerating to 0.

### Zack D Films style

| Title | Link | Len | Takeaways | Apply |
|---|---|---|---|---|
| "How To Make a Zack D. Films Video" (Gapa Vision) | recapio.com/digest/... | ? | Asset sourcing, Mixamo rigging, Track-To camera | We already use code cameras; Track To = `constraints.new('TRACK_TO')`. |
| "Animating a Zack D Films Style Short: COMPLETE Process" (OsasArt) | recapio.com/digest/... | ? | Assets (Sketchfab), char anim, cloth sim, camera, post | Cloth sim for the shirt flap on the fall (bake on Mac). |
| "Create Shorts Like Zack D Film in Blender" (Zyck Wealth) | recapio.com/digest/... | ? | Beginner; Mixamo; keyframe duplication | Low value for us. |

Tools: **Blender is likely but not confirmed.** The Zack D Films LLC job posting says "Blender proficiency is a major plus", and vendors say they made episodes in Blender. There's no first-party interview, so Mixamo use is a **rumour** (only tutorial makers claim it).

### Facial acting from video

| Tool | Link | Cost/licence | Mac | Notes / apply |
|---|---|---|---|---|
| MediaPipe Face Landmarker | ai.google.dev (mediapipe) | Free, Apache-2.0 | Yes (Python, CPU) | Outputs 52 ARKit-named blendshape scores per frame. Run in a separate venv (MediaPipe vs Blender 5.x Python 3.13 compatibility ?), write JSON, and bpy keys `shape_key.key_blocks[name].value`. Smooth plus gain per key. |
| Faceit | superhivemarket.com/products/faceit | Paid, about $78+ ? | Yes | Builds ARKit keys and retargets ARKit/A2F data; docs list free **Face Landmark Link** (MediaPipe, video/webcam to ARKit) ?. |
| BlendArMocap | github.com/cgtinker/BlendArMocap | Free, GPL-3.0 | ? | **Discontinued**; Rigify body/hands; face to shape keys unclear. Don't rely on it. |
| Rokoko face | rokoko.com | needs iPhone app | - | iPhone-only ARKit; not our case. |
| NVIDIA Audio2Face-3D | github.com/NVIDIA/Audio2Face-3D | SDK MIT; models "NVIDIA Open Model" licence (commercial OK per HF card) | **Unlikely** (NVIDIA GPU, CPU fallback mentioned; macOS not listed ?) | Open-sourced Sep 2025; plugins Maya/UE5 only; no Blender plugin. Could run on a RunPod GPU to output blendshape CSV and then bpy. Old Omniverse app is being deprecated. |

### Lip sync

| Tool | Link | Licence | Mac | Apply |
|---|---|---|---|---|
| Rhubarb Lip Sync | github.com/DanielSWolf/rhubarb-lip-sync | MIT (per listings ?) | Yes (mac builds) | CLI on WAV gives 6-9 mouth shapes plus times (TSV/JSON); map to ARKit `jawOpen`, `mouthFunnel`, `mouthPucker`, `mouthClose`… and key with ease. |
| Rhubarb Lipsync NG add-on | github.com/Premik/blender_rhubarb_lipsync_ng | MIT | mac download (tested Win only ?) | Blender 4.2+ extension; we can skip it and call the CLI ourselves. |
| Papagayo-NG | github.com/morevnaproject-org/papagayo-ng | GPL | mac builds partly broken ? | Manual phoneme timing; Moho export only. Skip it, because Rhubarb is better for us. |
| Audio2Face | see above | see above | no ? | Most natural result, but GPU-only. |

## 2. Markerless video-to-mocap

| Tool | Cost | Commercial licence | Output | Apple-silicon | Falls quality (expected) |
|---|---|---|---|---|---|
| FreeMoCap | Free | AGPL-3.0 (OK for output ?; paid licence offered) | Blender scene, CSV/npy | Yes (CPU) | Medium; multi-cam best, fast motion and ground contact jittery |
| MediaPipe Pose | Free | Apache-2.0 OK | 33 landmarks (no rotations) | Yes | Low-medium; depth weak, lying poses unstable |
| 4D-Humans (HMR2) | Free | Code MIT but **needs SMPL, NC** | SMPL params | CUDA expected; Mac ? | Good per-frame, jittery |
| WHAM | Free | Code MIT ? but **needs SMPL, NC** | SMPL params, world traj | CUDA (Colab) | Good, world-grounded |
| GVHMR | Free | **NC** (edu/research only) + SMPL | SMPL params | CUDA | Very good, world-grounded |
| Meta SAM 3D Body (Nov 2025) | Free | SAM Licence, commercial OK ? (use restrictions); MHR rig Apache-2.0 ? | MHR mesh/rig, single image | GPU likely ? | Per-image; video needs smoothing |
| Rokoko Vision | Free single-cam; dual-cam = Plus (about $20/mo ?) | Free-tier commercial ? | FBX (free); BVH paid | Yes (browser) | Medium |
| Move.ai (Move One) | Free: 30 one-off credits, 30 s clips | Free tier commercial **not confirmed**; paid plan likely needed | FBX/BVH ? | iPhone app + web | Good on Gen2 (paid) |
| DeepMotion Animate 3D | Free about 60 s/month ? | **Free = personal only**; paid plan needed | FBX/BVH/GLB | Yes (browser) | Medium; has physics filter / foot lock |
| Plask | Free about 15 s/day ? | Paid plans for commercial ? | FBX/GLB/BVH | Yes (browser) | Medium |
| Cascadeur (keyframe + AutoPhysics, video mocap) | Free = **NC**; Indie (<$100k rev) paid | Indie/Pro OK | FBX/DAE (Indie+) | Yes (macOS 13.3+) | Best tool for *physically plausible* falls; not bpy-scriptable |

SMPL note: the SMPL licence bans commercial use, including "production of other artefacts for commercial purposes". A commercial licence comes from Meshcapade. So treat any SMPL-output model as off-limits for monetised Shorts unless we buy one.

## 3. Free motion libraries

| Library | Licence | Format | Falls/stumbles/step-down? |
|---|---|---|---|
| CMU Graphics Lab | Free incl. commercial (secondary sources; confirm on mocap.cs.cmu.edu) ? | BVH (conversions), ASF/AMC | Some falls / stumbles (subject list needs a check ?) |
| Mixamo | Free; OK in videos; no raw redistribution ? | FBX | Several fall/trip/stumble clips (names to check ?) |
| Rokoko Motion Library (free set, about 150) | Free clips OK commercial (check per-clip tag) | FBX/BVH/CSV | Unknown; browse |
| ActorCore free motions | Commercial video OK (older staff post ?) | FBX/iMotion | Paid "Falling Motion Pack" exists; free falls ? |
| Bandai Namco Research Motiondataset | **CC BY-NC 4.0 (NC)**; older articles say BY-NC-ND | BVH | Daily, fight, dance, locomotion; falls not listed |
| LAFAN1 (Ubisoft) | **CC BY-NC-ND 4.0 (NC)** | BVH | Yes: fall+get-up (6), push+fall (2), push+stumble (3); reference only |
| SFU Mocap DB | Licence not found ? (assume NC) | BVH/C3D | ? |
| Motorica | Paid cloud generator (MoGen); no free library found | FBX | n/a |

Use LAFAN1/Bandai only as **study reference** (watch, then re-key in our own script), never shipped data.

## Sources

- https://www.rokoko.com/insights/ace-retargeting-in-blender-with-this-simple-workflow-i-the-ultimate-retargeting-guide
- https://www.blendernation.com/2023/01/14/the-simplest-way-to-retarget-mocap-to-a-rigify-rig-free-and-easy
- https://www.blendernation.com/2022/06/04/blender-expy-kit-addon-easy-mixamo-to-rigify-retargeting/
- https://classcentral.com/course/youtube-blender-expy-kit-addon-mixamo-to-rigify-208798
- https://classcentral.com/course/youtube-how-to-use-free-mocap-files-animation-retargeting-tools-and-rigs-in-blender-209417
- https://cgtrader.com/tutorials/9383-how-to-use-mixamo-animations-in-blender-rigify-rig
- https://superhivemarket.com/products/auto-rig-pro
- https://jac307.github.io/MediaArtTutorials/MOCAP/4_Retargeting_Blender.html
- https://blenderartists.org/t/fix-sliding-feet-in-blender/1620939
- https://foot-flow.pages.dev/
- https://superhivemarket.com/products/mocap-bone-lock/
- https://superhivemarket.com/products/inverse-lock-bone
- https://www.animationmentor.com/blog/2025/11/
- https://gamedeveloper.com/design/center-of-mass-tools-and-techniques-for-animating-natural-human-movement
- https://cassiersbitanime.blogspot.com/2015/04/how-does-human-fall.html
- https://recapio.com/digest/how-to-make-a-zack-d-films-video-by-gapa-vision
- https://recapio.com/digest/animating-a-zack-d-films-style-youtube-short-complete-process-by-osasart-1
- https://recapio.com/digest/create-youtube-shorts-like-zack-d-film-in-blender-absolute-beginner-tutorial-by-zyck-wealth
- https://remotive.com/remote/jobs/design/3d-generalist-5291866
- https://faceit-doc.readthedocs.io/en/latest/mocap_general/
- https://superhivemarket.com/products/faceit
- https://github.com/cgtinker/BlendArMocap
- https://github.com/NVIDIA/Audio2Face-3D
- https://huggingface.co/nvidia/Audio2Face-3D-v2.3-Mark
- https://www.opensourceforu.com/2025/09/nvidia-moves-audio2face-technology-to-open-source/
- https://github.com/Premik/blender_rhubarb_lipsync_ng
- https://superhivemarket.com/products/lipsync-studio--audio-driven-mouth-animation-for-blender
- https://github.com/morevnaproject-org/papagayo-ng
- https://github.com/freemocap/freemocap
- https://github.com/yohanshin/WHAM
- https://github.com/zju3dv/GVHMR (LICENSE)
- https://github.com/shubham-goel/4d-humans
- https://smpl.is.tue.mpg.de/modellicense.html
- https://dev.to/arkadiuss/a-3d-body-scan-for-nine-cents-without-smpl-4me1
- https://comfyui-wiki.com/en/models/sam/sam-3d-body
- https://www.rokoko.com/pricing ; https://www.rokoko.com/products/video
- https://docs.move.ai/knowledge/move-one-pricing
- https://www.deepmotion.com/faq
- https://aitoolsatlas.ai/tools/plask-motion/free-vs-paid
- https://cascadeur.com/education ; https://cascadeur.com/ru/plans ; https://www.cgchannel.com/2025/04/nekki-releases-cascadeur-2025-1-with-ai-based-inbetweening/
- https://github.com/BandaiNamcoResearchInc/Bandai-Namco-Research-Motiondataset
- https://automaton-media.com/en/news/20220430-12213/
- https://github.com/ubisoft/ubisoft-laforge-animation-dataset
- https://cgpress.org/archives/carnegie-mellon-university-motion-capture-database.html
- https://community.adobe.com/t5/mixamo-discussions/mixamo-faq-licensing-royalties-ownership-eula-and-tos/td-p/13234775
- https://www.cgchannel.com/2020/03/get-150-free-mocap-moves-from-rokokos-motion-library
- https://marketplace.reallusion.com/falling-motion-pack ; https://actorcore.reallusion.com/motion/free
