# Viewing the grey-box previz in Blender

`pilot_ear_pop_previz.blend` (built by `build_previz.py`, Blender 4.5 LTS or newer). Voice and
SFX are packed inside, so the file works on its own.

## Watch the whole film (with voice, cuts, captions)
1. Open the file. Top right, switch the **Scene** from `FILM` to **`EDIT`**.
2. Change the big 3D viewport into a **Video Sequencer** (editor-type menu, top-left of the area)
   and choose **Sequencer & Preview**.
3. Press **Space** to play. The preview uses Material Preview shading. If playback stutters,
   set Playback ▸ Sync to **Frame Dropping** so the picture stays locked to the voice.

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
