# Viewing the grey-box previz in Blender

`pilot_ear_pop_previz.blend` (built by `build_previz.py` with Blender 4.5 LTS; opens in 4.5 and 5.x). Voice and
SFX are packed inside, so the file works on its own.

## Watch the whole film (Blender 5.x and 4.5)
**Easiest: the FILM scene**, which has every shot, camera cut, voice and SFX:
1. Top right, make sure the **Scene** is **`FILM`**.
2. Hover over the 3D viewport: **View ▸ Cameras ▸ Active Camera** (or Numpad 0).
3. Viewport shading: **Material Preview** (third sphere icon, top right of the viewport).
4. Set the frame to 1 and press **Space**. The cameras cut at the markers `S01`…`S13`.
   If it stutters: Playback ▸ Sync ▸ **Frame Dropping**.

**With captions and the dissolve: the EDIT scene.** In a Video Sequencer area
(Sequencer & Preview), pick **`EDIT`** as the sequencer's scene. In Blender 5 the sequencer
has its own scene selector in its header, separate from the window's scene. Then play.

## Inspect or tweak the 3D shots
- Scene **`FILM`**: press **Numpad 0** (camera view) and play. The timeline markers `S01`…`S13`
  switch cameras, so you see every cut in the real 3D scene.
- Each shot's camera is `CAM_Sxx` (collection `CAMERAS`). Every move is baked keyframes, so
  you can move or re-time keys freely.
- Word markers in `EDIT` (`happening`, `bulges`, `pop`…) show where the beats land.

## Audio and picture in sync
Both scenes play with **Sync to Audio**, so on a slower machine Blender skips frames rather
than letting the picture drift behind the voice. For a perfectly smooth, synced copy, make a movie:

## Quick synced movie (free, on your Mac)
In `FILM`, camera view, Material Preview: **View ▸ Viewport Render Animation**. Blender writes
`pilot_ear_pop_previz_0001-1566.mp4` next to the .blend, with the voice and SFX mixed in at exact
frame timing. It takes a few minutes and costs nothing.

## Max (the real character)
The cabin shots use the real rigged Max (`assets/characters/max/max_v2.blend`), seated in his seat,
with his acting hand-keyed to the voice (`real_max.py`):
- S02 "happening": puzzled, touches his ear; the camera then pushes into his real ear (ends black).
- S07 "muffled": wince, hand cupping the ear.
- S12 "swallowing" / "yawning" / "chewing" / "open": swallow, a big yawn revealed as the camera
  pulls out of his ear, chewing, then a relief smile.
- S13 "Follow": grin and thumbs-up to the lens.
- Natural blinks throughout.

His expressions are named face shapes (`shorts/blender/max_expressions.py`), so you can retime or
tweak any of them in Blender: select `Max.body` ▸ Shape Keys, or the `Max` armature in Pose Mode.
In Material Preview the hair shows as guide strands; switch to Rendered shading for the full head of hair.
`--standin` builds the old grey-box Max instead.

## Giving feedback
- Say it by shot: *"S06 start closer"*, *"S10 drone from the left"*.
- Or change it in Blender and tell Claude which shots you touched, so those are kept.

What's final: camera angles and moves, timing, shot order, transitions, animation beats.
What's stand-in: all geometry and materials. The realistic stage replaces the sets and Max under
the same names, so the cameras and timing carry over.
