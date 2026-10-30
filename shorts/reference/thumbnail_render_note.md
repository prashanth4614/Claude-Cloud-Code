# Thumbnail render note (Mac, 2026-10-31)

The thumbnail rendered, but A's wince still reads mild, and switching to another frame doesn't fix it.

## Render

- **Machine and settings:** Cycles on Metal on the Apple M4 (10-core GPU), 256 samples (adaptive),
  2160x3840.
- **Times:** frame 15 took about 10 min 1 s, frame 547 about 3 min 11 s; the whole run 13 min 18 s.
- **Scene file:** the existing `out/pilot_ear_pop/pilot_ear_pop_previz.blend` (saved 17:03 IST). The
  only scene commit after it (f4bc6f1) moved captions and the S12b/profile framing, which doesn't touch
  frames 15 or 547.
- **Outputs** (gitignored):
  - `out/thumbnail/thumbnail_{A,B}.png` (2160x3840);
  - `out/thumbnail/thumbnail_{A,B}.jpg` (1080x1920; 291 KB and 115 KB);
  - `out/thumbnail/film_0015.png` and `out/thumbnail/film_0547.png`.
- `thumbnail.py` is unchanged.

## Checks

Both frames are clean (no captions or labels baked in) and match the film's look.

**A (frame 15 + "your ears pop"): the wince reads mild.**
- Eyes shut, brows barely lowered, mouth slightly open: it looks sleepy or queasy rather than in pain.
- The face is cropped at both cheeks, and the eyes sit about 51 % from the top (the target is 30–40 %).
- The hand on his ear is never in frame.

**Another frame won't fix A.**
- S00 keys "wince" at 1.0 on frame 1 and 0.9 on frame 19, so frames 1–19 are identical.
- Low-res test renders of frames 1, 625 and 645 (S07's wince) show the same weak face, with no hand in
  shot.
- The cause is that the wince shape keys in `shorts/blender/max_expressions.py` (browDown 0.8,
  squint 0.8, sneer 0.55, jawOpen 0.06) come out weak on this mesh.

**B (frame 547 + "bulges,"): reads clearly at thumbnail size.**
- A pink dome bulges against the white membrane line on a navy background, with the ossicles on the
  right.
- The caption sits on the membrane line where it meets the bottom of the dome. Moving it 4–6 % lower
  (or the frame left) would clear it.
- It is abstract without context.

**Caption colour:** both captions use the render's measured gold, as `thumbnail.py` intends. That is
duller than Zack's clean white; the coordinating session's call.

## Verdict

Use B today. A is the stronger idea (a human hook, like the horse-fly Short) but needs a stronger wince
first, and that would change the video too.

To make A work:
1. Add a "wince_hard" expression for the thumbnail and S00: browDown 1.0, browInnerUp 0.5, squint 1.0,
   sneer 0.8, mouthStretch 0.7, jawOpen 0.15, plus a head tilt.
2. Pull the S00 camera back about 15–20 %, so the hand cupping his ear is in frame and his eyes sit at
   about 35 % from the top.
3. Re-render A (about 10 min on the Mac).
