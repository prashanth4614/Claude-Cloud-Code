# Character motion and facial acting: research and the pipeline we adopt (2026-10-31)

Owner's brief: "No compromise in character motion and facial expression." It must be at Zack D Films
level: natural hands, legs and body, physically right falls, and the face acting every beat.
Claude's web research is below. The web helper adds YouTube tutorials and tool tests in
`character_motion.md`, and the Zack frame-by-frame study in `shorts/train_step_off/motion_research.md`.

## What exists (checked)

| Need | Best option | Licence / cost | Notes |
|---|---|---|---|
| Claude skills or plugins for character animation | **None** in the catalogue (searched: blender, animation, motion capture, facial) | — | Animation-adjacent plugins are 2D, code or motion-graphics; Meshy's plugin rigs and animates generated models, not ours. We write our own skill (§5b in shorts-craft, plus this doc) |
| Mocap retargeting onto Max | **Diffeomorphic BVH Retargeter** (ex-MakeWalk), GitHub `Diffeomorphic/retarget-bvh` | GPL add-on (our output is ours) | Built for **MakeHuman** rigs, and MPFB2's default rig is the MakeHuman rig. It has source presets for CMU/Mixamo, foot locks, loop/edit tools. Our `mocap_retarget.py` (world-direction matching) is the fallback |
| Body motion data | **CMU Mocap** (BVH, 120 fps); **Mixamo** (stumbles, trips, falls, slips, step-downs) | CMU: free for any use. Mixamo: free with an Adobe login; royalty-free in videos | CMU's 120 fps is ideal for 8× slow motion. Mixamo has the best ready-made falls |
| Stunt-quality falls | Marketplace "trips and falls" mocap packs (stunt performers) | Paid; check the licence | Only if CMU and Mixamo fall short |
| Video → body motion (the owner acting a safe step or stumble) | **MediaPipe Pose** (3D world landmarks), **FreeMoCap** | MediaPipe: Apache-2.0. FreeMoCap: AGPL software, our output is ours | GVHMR, WHAM and TRAM are the best quality but **non-commercial** (research licences plus SMPL terms): not usable for the channel |
| Face from an ordinary phone video | **MediaPipe Face Landmarker**: outputs the **52 ARKit blendshape** scores per frame | Apache-2.0, free, runs locally | Max's face *is* the ARKit 52, so this maps 1:1. The owner (or anyone) films himself acting each beat on a phone; no iPhone depth camera needed. Commercial add-ons (MoCap AI) wrap the same thing |
| Face from audio (talking) | **NVIDIA Audio2Face-3D** (open models, Aug 2025): outputs ARKit blendshapes | NVIDIA Open Model License (the HF card says commercial use OK; the NGC container says non-commercial: check before use) | Max doesn't talk in this Short (voice-over), so not needed now |
| Lip sync, simple | Rhubarb Lip Sync (+ Blender add-ons) | Rhubarb reportedly MIT | For future talking shots |
| Physics-based character research (PDP, UniPhys, PhysMoDPO) | Research only | Mostly no code or licence | Not production-ready for us; we use the physics as timing and direction constraints instead |

## Biomechanics we animate to (sources: Park 2023 review of 64 fall-recovery studies; Chun's systematic review of trip and slip recovery; Lee-Confer 2022 on arm use in slips)

- **Slips:** recovery depends on a rapid compensatory step of the **unperturbed** leg within a narrow
  window. The **arm opposite the slipping foot** does the most balance work (it flings out).
- **Trips:** the response depends on timing. Early-swing trips get an "elevating" step (the foot lifts
  over); late-swing trips get a "lowering" one (the foot plants short).
- **Arms** stabilise the trunk; protective reach starts early in the fall. Shoulder-flexion latency
  (about 100-150 ms in healthy adults) is in the primary literature (Marigold 2003, Pijnappels 2010).
  Use about 120 ms.
- **Our own physics:** with the feet stopped at 10 km/h, a stiff body pivots about the foot: 15° at
  0.10 s, 45° at 0.27 s, the ground at about 0.42 s (an inverted pendulum, COM 0.98 m). Real people
  buckle the knees and step, so it takes longer, but **falls are fast**: show them in about 8× slow motion
  from 120 fps mocap; never slow the physics itself.

## The pipeline we adopt

1. **Body:**
   - CMU/Mixamo clips → Diffeomorphic BVH Retargeter onto Max's MakeHuman (MPFB default) rig, or
     `mocap_retarget.py` as the fallback.
   - Then edit:
     - foot-contact IK locks (no sliding);
     - the root (hips) path re-timed to the physics (train speed at contact, then the pendulum
       timing);
     - NLA blends between clips (walk → step off → stumble → fall).
2. **Reflex layer, hand-keyed on top in the NLA:**
   - an arm fling about 120 ms after the perturbation (the arm opposite the slipping foot first);
   - the knees unlock;
   - head counter-rotation (a chin tuck when falling backward);
   - hands reaching before impact.
3. **Face:**
   - The owner films each beat's reaction on his phone (5-10 s each): surprise → fear → the
     pre-impact squeeze, etc.
   - MediaPipe Face Landmarker → 52 ARKit curves → Max's shape keys, smoothed (One-Euro filter),
     amplified about 1.2-1.5× for phone-size readability.
   - Procedural eye saccades toward the danger, and blinks.
   - Fallback without the owner's video: the hand-keyed expression timeline (surprise at +150 ms,
     etc., §5b).
4. **Secondary motion:**
   - a cloth sim on the tee for close-ups (pinned at the collar and shoulders);
   - a light spring or jiggle on the hair curves;
   - fabric settles after the body stops.
5. **Review:**
   - the G5b motion test (two angles, real speed plus slow motion) on the Mac;
   - Codex frame review for robotic or floaty motion, contacts and the face per phase;
   - the owner approves before any key frames.

## Needs from the owner

1. **Mixamo:** a sign-in (free Adobe account) in the helper Chrome on the Mac, so the web helper can
   download the stumble, trip, fall and slip clips. (Optional: CMU alone works, with more editing.)
2. **Face acting videos:** about 6 short phone selfies of the owner acting each beat (no iPhone depth
   needed). This gives truly human facial timing.
3. Optional: a phone video of someone doing a **safe** "brisk walk, sudden stop, catch your balance"
   on flat ground, for the stumble body motion (MediaPipe Pose).
