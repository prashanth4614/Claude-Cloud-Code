# Production pipeline: Blender 3D Shorts (v1, agreed 2026-10)

The goal is production-grade 3D explainers and stories: a realistic-stylized look, your own
voice, and rendering on RunPod. Claude writes and assembles everything in code. You approve at
the gates and supply any AI images Claude asks for.

```
 1 IDEA ─► 2 SCRIPT ─► 3 VOICE ─► 4 SHOT PLAN ─► 5 ASSETS ─► 6 SCENE BUILD ─► 7 ANIMATIC ─► 8 FINAL RENDER ─► 9 EDIT/MIX ─► 10 QA ─► 11 UPLOAD
   you+Claude  Claude   ElevenLabs  Claude        library+you  Claude (bpy)    RunPod EEVEE   RunPod Cycles    Claude (code)  Claude   you
                         ▲ gate A                                                ▲ gate B                         ▲ gate C
```

Gates are the points where **you approve before money or time is spent**:
- **Gate A:** the voice take.
- **Gate B:** the low-res animatic (motion, timing, framing).
- **Gate C:** the final cut.

---

## 1–2. Idea and script (Claude drafts, you approve)
- 35–55 s Short structure:
  - a **hook in the first second**;
  - one idea per line;
  - a visual payoff moment;
  - a twist;
  - a takeaway;
  - a CTA.
- The script is written **for the ear**: short sentences, deliberate punctuation for pauses,
  and delivery tags for emotion (see §3).
- Output: `shorts/<video>/script.yaml`. It holds the lines, the delivery tags, the shot
  intent per line, and the SFX cues anchored to words.

## 3. Voice: your ElevenLabs clone, natural and energetic
- **One request for the whole script, not one per line.** The model then keeps breath, pitch
  contour and pacing across sentences, which is where most of the "AI voice" feel comes
  from. Character timestamps split it back into lines and words, giving exact caption and
  animation timing. This replaces the current per-line synthesis.
- **Model:** `eleven_v3` (expressive). It supports audio tags such as `[excited]`,
  `[curious]`, `[whispers]`, `[sighs]` and `[short pause]`. Ellipses `…` and em dashes `—`
  create natural pauses, and a new paragraph gives a longer beat.
- **"Higher pitch / more energy":** ElevenLabs has no pitch knob. Pitch and energy come from:
  1. the clone's source audio. A **Professional Voice Clone**, trained on ~30+ min of you
     speaking in the energetic register you want, is far more natural than an Instant clone.
     This is the single biggest quality upgrade.
  2. delivery tags and punctuation in the script.
  3. settings: stability 0.35–0.5 (lower = more expressive), similarity 0.85,
     style 0.2–0.4, speed 1.0–1.1.
  4. only if still needed, a gentle +0.5 to +1 semitone formant-preserving shift
     (rubberband) in post. Larger shifts sound artificial, so avoid them.
- **Post-processing (automatic):** high-pass 80 Hz, light de-ess, gentle compression,
  then −14 LUFS.
- **Gate A:** you listen to the take before anything is rendered. Re-takes of single
  sentences are cheap and cached.

## 4. Shot plan (Claude)
- For every line: camera move, set, characters and action, the animation beats that land
  on specific words, and the effects.
- Output: `shorts/<video>/shots.yaml`. It drives both the scene build and the edit.

## 5. Assets: where realism comes from

Realism comes from **good assets + PBR materials + real lighting + Cycles**, not from
modelling with Python primitives. The early prototypes looked like toys because they
were built from spheres and capsules. The fix is a reusable, licensed asset library:
`assets/` (large files, kept out of git or in Git LFS) plus `assets/LICENSES.md`, a manifest
recording every asset's source and licence.

| Need | Source | Licence notes |
|---|---|---|
| HDRI lighting and skies, PBR textures (skin, fabric, metal, tissue) | **Poly Haven**, **ambientCG** | CC0, free for anything |
| Props and sets (plane cabin, kitchen, street…) | **BlenderKit**, **Sketchfab** (CC0/CC-BY), Fab, CGTrader/TurboSquid | Check each one. CC-BY needs a credit in the description. Buy "royalty-free" for paid models. |
| Human anatomy (ear, heart, lungs, brain…) | **Z-Anatomy** (Blender-native, full body), BodyParts3D | CC-BY-SA 4.0: credit it, and keep our modified anatomy files under the same licence. Or buy royalty-free anatomy models. |
| Characters (realistic or stylized humans) | **MPFB2** (MakeHuman for Blender, free, CC0 output) for most cases; **Character Creator 4** (paid) for top-tier realism | Rig with **Rigify** (built into Blender) |
| Body animation | **Mixamo** (free mocap library and auto-rigger), ActorCore (paid) | Retarget onto our rigs |
| Facial animation and lip-sync | **Rhubarb Lip Sync** (open source), reading our voice audio → mouth-shape keys | Fully automatic from the ElevenLabs audio |
| Hero objects that don't exist anywhere | **Your AI image → image-to-3D** (Meshy, Tripo, Hunyuan3D) → cleanup in Blender | Claude gives you the concept prompt, you generate the image (CLAUDE.md rule) |

**Reuse is what makes this affordable.** Each recurring set (airplane cabin, inside the
body, kitchen…) and each recurring character is built once at high quality. After that, a
new video is mostly scene assembly.

## 6. Scene build (Claude, Blender Python)
- `shorts/blender/build.py` reads `shots.yaml` plus the word timestamps and:
  - links assets from the library;
  - places the cameras (with easing, depth of field and motion blur);
  - keys the animation to spoken words, so the POP happens on "pop";
  - sets up lighting (an HDRI plus 3-point key/fill/rim lights per shot);
  - adds geometry-nodes effects (air molecules, particles, glows);
  - saves one `.blend` per shot.
- **You can open any `.blend` in Blender** and tweak it by hand. Claude re-reads your
  changes, so this works both ways.

## 7. Animatic: Gate B (RunPod, cheap)
- EEVEE at 540×960 with low samples, around ₹5 per video. You review motion, timing and
  framing before the expensive render.

## 8. Final render (RunPod)
- **Cycles** with OptiX on an RTX 4090. Path tracing gives the realistic look: subsurface
  skin and tissue, volumetrics and real reflections. Use adaptive sampling
  (64–256 samples) + the OptiX denoiser, 1080×1920, 30 fps.
- **Expected:** ~2–6 s per frame → ~45–130 GPU-min per 45 s Short. Split across 3–4 pods in
  parallel, that's about 15–35 min wall time, for roughly **₹15–90 per video** depending on
  the community/secure price. Measure on the first video.
- **Render passes** (beauty, AO, mist, cryptomatte) are written as EXR. This allows grading
  and fixes without re-rendering.

## 9. Edit and mix: Claude in code, not the Blender editor
- **Recommended: Claude's code-based editor** (`shorts/engine.py` grown into an edit
  module). It is driven by the script and timestamps, and handles:
  - cuts and transitions;
  - captions with exact word sync;
  - SFX on words;
  - a music bed ducked under the voice;
  - colour grade (a LUT);
  - mastering to −14 LUFS.

  It's fully reproducible: change a line, re-run, and everything re-times.
- **Blender's built-in video editor (VSE):** good for compositing render passes, but
  clumsy as the main editor and hard to automate well.
- **DaVinci Resolve (free):** use it only if you want to hand-polish a special video.
  Claude can export an edit decision list for it.

## 10. QA (Claude, automatic + visual)
- Duration, loudness, true peak, no black or frozen frames, caption/voice sync at the SFX
  anchors, and safe areas (captions clear of the YouTube Shorts UI).
- A frame contact sheet that Claude reviews before sending you the video.

## 11. Upload (you)
- Title, description, hashtags and a pinned comment are generated per video.
- Credits for CC-BY assets go in the description.

---

## Costs per video (estimate)
| Item | ₹ |
|---|---|
| ElevenLabs voice (~700 characters + a few re-takes) | covered by your plan |
| RunPod animatic + final Cycles render | ~₹20–100 |
| Assets | ₹0 with CC0 / free libraries. Paid hero assets are a one-time cost, reused across videos. |

## Open decisions
1. **Look:** stylized-realistic (Zack D-like, recommended) or near-photoreal (much more
   asset and render cost).
2. **Character:** one recurring host character (recommended for channel identity) or
   anonymous people.
3. **Professional Voice Clone:** worth recording ~30–60 min of energetic narration.
4. **First pilot topic:** remake the ear-pop Short with the new pipeline, so it can be
   compared against the old versions.
