# CMU motion capture clips (BVH) for the train step-off Short

**Source:**
- Data: the CMU Graphics Lab Motion Capture Database, http://mocap.cs.cmu.edu
- BVH conversion: by Bruce Hahne (cgspeed), via the GitHub mirror
  https://github.com/una-dinosauria/cmu-mocap (`data/<subject>/<trial>.bvh`).

**Licence:** the conversion's READMEFIRST says "This data is free for use in research and commercial
[projects]" (CMU's terms: any use, including commercial; don't resell the raw data as such). Credit is
appreciated: "The data used in this project was obtained from mocap.cs.cmu.edu."

**Format:** 120 fps (frame time 0.0083333 s). Root `Hips`, Y up. Units are cgspeed's scale (hips at
about 17 units ≈ 0.95 m, so 1 unit ≈ 5.6 cm). Scale the armature on import in Blender, or set
`global_scale` in `import_anim.bvh`.

| File | Subject_trial | CMU description | Length | What's in it (hip trajectory) | Use for |
|---|---|---|---|---|---|
| `02_01.bvh` | 02_01 | walk | 2.9 s | level walk, about 60 units of travel | Max walking along the coach to the door |
| `40_07.bvh` | 40_07 | climb, step over, jump over stepstool | 57.4 s | long take with several step-ups and **step-downs** off a stool; hips drop about 3.5 units at the step-downs | stepping down from the coach floor to the platform (trim the step-down) |
| `91_59.bvh` | 91_59 | 360 smallStumble | 2.6 s | a small stumble with a turn, hips dip 1.6 units | a light wobble or loss of balance |
| `104_13.bvh` | 104_13 | StumbleWalk | 4.6 s | walk with a stumble; hips dip about 3 units at 3.5 s | a stumble while carrying speed |
| `22_12.bvh` | 22_12 | A stumbles into B (subject A) | 2.5 s | a stumble forward into another person | a forward stumble (the partner is not included) |
| `90_16.bvh` | 90_16 | fall on face | 6.0 s | hips fall from 20.6 to 4.1 units between 2.4 and 3.8 s (1.3 s, controlled) | **fall forward** onto the hands and face |
| `90_18.bvh` | 90_18 | RugPullFall | 3.3 s | hips drop from 21 to 3 units in **0.35 s** (0.7–1.06 s) | **fall backward** (the feet go out from under him, like the facing-backward case) |
| `16_08.bvh` | 16_08 | run/jog, sudden stop | 2.0 s | jog, then a stop | run to a stop (the "run it out" case) |
| `127_05.bvh` | 127_05 | Run to Quick Stop | 3.2 s | run with a low braking crouch (hips to 11.8 at 1.0 s) | a hard braking stop after stepping off |
| `104_56.bvh` | 104_56 | RunStop | 3.1 s | run, then stop | an alternative run-to-stop |

**Total:** 7.8 MB.

**Not included:** `15_02` (has stool step-downs, but 16.5 MB) and `86_13` (step down from a ladder).
The CMU search found no "curb" or "kerb" clips; "fall" turns up acrobatics (85_15, 88_04, 90_12/13)
that aren't useful here.

The directions (forward or backward) are inferred from the trial names and the hip drop; check each
one in Blender before use.
