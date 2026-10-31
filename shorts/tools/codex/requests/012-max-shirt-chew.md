IMAGES: assets/characters/max/review/max_v6_expressions.jpg assets/characters/max/review/max_v6_shirt_closeup.jpg

# Max v6c: two patches (Claude applies and verifies; you're read-only)

Max v6c is on the branch (`assets/characters/max/max_v6.blend`, built by
`blender -b assets/characters/max/max_v3.blend -P shorts/blender/max_look.py -- --regroom --curves --out ...`).
Read `assets/characters/max/review/max_v6_notes.md` (sections v6b and v6c) first, then
`shorts/blender/max_look.py` (`upgrade_shirt`, from your 011b), `shorts/blender/build_max.py`
(`set_expression`, `pose_head`, `chew_cycle`, `thumbs_up`, `aim_bone`) and `shorts/blender/max_expressions.py`.
If an image above is missing, use the newest `max_v6*` jpgs in that folder.

## 1. Shirt under a raised arm
The tee still reads smooth and stretched under the raised arm (thumbs-up / hand-to-ear). The bump folds
are rest-space, so they stretch instead of bunching. Propose the cheapest robust fix, for example:
- a corrective shape key on `Max.male_casualsuit06`, built by script and driven by the upperarm01.L/.R
  pose rotation, that pulls the side and armpit vertices into 2-3 crisp diagonal folds and shortens the
  stretch;
- and/or a pose-driven strength on the bump (an attribute or driver value) so the folds deepen when the
  arm lifts.
Only the tee island (your 011b connectivity code finds it). No cloth sim. It must survive thumbs-up
and the arm-to-ear pose.

## 2. Chew that reads in a still and in motion
`chew` / `chew_b` and `chew_cycle` still look close to neutral. Give new unit values (only the 52 ARKit
FACE_UNITS plus `throatRise`), a head pose, and a 3-chew keyframe cycle (24 fps). Show the jaw working
under sealed lips, cheeks bulging alternately, and a slight mouth corner shift. Also give the single best
still for the expression sheet.

## Answer format
For each item: exact code (diff or full functions with insertion points), one verification render
(camera, pose, what to look for), risks. Under 1200 words plus code.
