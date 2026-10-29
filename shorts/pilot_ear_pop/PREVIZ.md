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

## Quick movie without RunPod
View ▸ **Viewport Render Animation** (in FILM, camera view) writes an MP4 of exactly what the
viewport shows, in a few minutes, for free.

## Giving feedback
- Say it by shot: *"S06 start closer"*, *"S10 drone from the left"*.
- Or change it in Blender and tell Claude which shots you touched, so those are kept.

What's final: camera angles and moves, timing, shot order, transitions, animation beats.
What's stand-in: all geometry and materials. The realistic stage replaces the sets and Max under
the same names, so the cameras and timing carry over.
