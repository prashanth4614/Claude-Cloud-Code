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

## 4. Storyboard and cinematography (Claude drafts, you approve)

The film is designed as data before anything is built: `shorts/<video>/shots.yaml`
(see `shorts/pilot_ear_pop/shots.yaml`). For every shot it records:
- **size**: EWS → MACRO;
- **angle**: low, high, aerial, Dutch, POV;
- **real lens**: focal length in mm, plus depth of field;
- **camera move**;
- **beats** keyed to spoken words;
- **effects**;
- **mood**;
- the **transition** into the next shot.

**Storytelling grammar used on every video:**
- Open on motion, never a static frame. The hook lands in the first second.
- **Establish → go inside → reveal → payoff → twist → takeaway**. Cut wide for "where we are",
  close for "what it feels like".
- Cut every ~1.5–4 s, matched to the voice. Vary shot sizes; never two identical framings in a row.
- **Max is the emotional anchor:** cut to his face when the viewer should *feel* something.
- **Visual motifs:** a consistent colour code (for example cool blue outside air, warm amber inside
  air) and consistent screen direction (the plane climbs left-to-right and lands right-to-left).
- Camera language carries emotion:
  - calm = locked-off and still;
  - tension = slow push-in plus a creeping Dutch tilt;
  - release = a speed ramp, then a snap.
- The last frame matches the first, so the Short loops into a rewatch.

**Camera rig library** (`shorts/blender/rigs.py`, physically based cameras with real focal
lengths, f-stop depth of field and motion blur):

| Move | How it's built in Blender |
|---|---|
| Dolly in/out, truck, pedestal | Camera keyframed along an axis with smooth ease-in/out |
| **Drone** reveal / track / flyover | Camera on a Bezier path (Follow Path) plus a Track-To target, with gentle banking and altitude change |
| Crane up/down | Two-level rig (arm + head) for a sweeping arc |
| Orbit / arc | Camera parented to a rotating pivot empty |
| Fly-through | Camera on a path *through* geometry (into the ear canal), wide lens |
| Handheld | Subtle noise modifiers on rotation (0–1 strength) |
| Rack focus / dolly zoom | Animated focus distance, or focal length against distance |

**Transitions** are built **in-camera** where possible, because that reads as cinematic:
- match cut (window to window);
- push-through (the camera enters the ear, and darkness bridges the cut);
- whip pan with motion blur;
- occlusion wipe (an object passes the lens);
- focus pull.

Edit-level dissolves, dips and flashes are the fallback. Every shot is rendered with
**10-frame handles** either side, so transitions can overlap.

**Effects:**
- geometry-nodes particles (air molecules, dust);
- volumetric clouds, haze and god rays;
- shape keys and drivers keyed to word timestamps (the eardrum bulge, the tube opening);
- emission plus compositor glare (glow);
- shockwave ripples;
- speed ramps;
- lens effects: soft flare, vignette, a little grain;
- one LUT colour grade for the whole film, with small per-shot mood shifts.

**Gate B0, previz (new):** before any real assets, Claude renders a quick **grey-box previz**.
Simple stand-in shapes, real cameras, real timing, EEVEE at 540×960, around ₹5 on RunPod.
You approve the *cinematography* (angles, moves, pacing, transitions) when it's cheap to change.

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

## 6. Scene build: how the .blend is prepared before it goes to RunPod

`shorts/blender/build.py` turns `script.yaml` + `shots.yaml` + the word timestamps into
**one master `.blend` per video**:
- **One Blender Scene per shot** (`S01`, `S02`, …), each with its own camera rig, light rig,
  frame range (plus handles) and render settings. RunPod renders shots in parallel, one per GPU.
- **Sets and characters are linked, not copied,** from the asset library (`assets/*.blend`):
  the cabin, the ear cutaway and Max. Improve an asset once, and every video gets it.
- **Timeline markers at every spoken word.** Drivers and keyframes snap to them, so the
  eardrum pops on "pop" even if the voice is re-taken.
- **Render layers and passes** (beauty, AO, mist, cryptomatte, glow), plus compositor nodes
  for glare, lens effects and the LUT.
- **Lighting:** an HDRI for ambient light and reflections, plus a key/fill/rim rig per shot.
- **Checks before RunPod:** missing textures, all assets packed or relative, frame ranges
  matching the voice, cameras inside the sets, and a still from every shot reviewed by Claude.
- **You can open the master `.blend` in Blender** and hand-tune any camera or animation.
  Claude keeps your changes, and the builder never overwrites anything you've marked as `locked`.

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

## Decisions (2026-10-29)
1. **Look:** stylized-realistic (Zack D-like), rendered in Cycles.
2. **Character:** one recurring host, **Max**, redesigned for the realistic-stylized look.
3. **Voice:** the user's existing ElevenLabs voice `x5ld1ovD8agu3EPB7Qpj`, as one v3 take per
   script (already in `shorts/engine.py: elevenlabs_script`).
4. **Pilot:** remake the ear-pop Short in `shorts/pilot_ear_pop/` and compare it with the old versions.

## Sound design: natural, gentle, never aggressive

The user's explicit priority. The rules:

- **Real, organic sounds, not synthesized beeps.** SFX come from ElevenLabs Sound Effects
  (text-to-SFX; available on the current plan) or CC0 libraries such as Freesound or Sonniss.
  Each cue is generated once from a written description and cached in `assets/sfx/`.
  Retired: the procedural ding, thud and whoosh synths.
- **Less is more.** At most one designed SFX accent every ~3–4 s. Accents support the picture
  (the pop, a tube opening). They're not on every word or caption.
- **A constant room-tone bed** gives continuity: cabin hum for cabin shots, a soft body-interior
  ambience for inside-the-ear shots. Crossfade between beds over ~0.5–1 s, never hard-cut.
- **Music:**
  - a sparse, warm underscore: felt piano, soft pizzicato, pads, no drums, no vocals;
  - ~80 bpm, composed to the video length, with a gentle lift into the payoff and a calm
    resolve at the end;
  - sources: ElevenLabs Music if the plan allows it, otherwise a YouTube Audio Library track
    the user downloads from search terms Claude provides;
  - never the procedural synth bed.
- **Mix targets:**
  - voice at −14 LUFS integrated for the final master, and always on top;
  - music around −28 LUFS while under speech, rising to about −22 LUFS in gaps;
  - ambience beds around −38 to −42 LUFS;
  - SFX peaks at least 6–8 dB under the voice peaks;
  - true peak ≤ −1.5 dBTP.
- **Gentle ducking:** −4 to −6 dB under the voice, with a 250 ms attack and 700 ms release.
  No pumping.
- **Taming:**
  - every SFX gets a high-shelf cut above ~8 kHz (no harshness), a low cut under 60 Hz,
    10–30 ms fades, and a short room reverb matched to the space it plays in;
  - transients are softened (no clicks);
  - nothing louder than the voice, ever.
- **QA:** loudness and peak meters per stem, plus Claude listening checks on the spectrum. The
  user signs off at Gate C.
