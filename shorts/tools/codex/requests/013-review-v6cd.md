IMAGES: assets/characters/max/review/max_v6c_hair_poses.jpg assets/characters/max/review/max_v6d_armpit_cpu.jpg assets/characters/max/review/max_v6d_chew_cpu.jpg

# Review only: Max v6c/v6d changes

**Review, don't write code.** No patches or functions: give findings as file:line, what's wrong or
risky, why, and what should change, in words.

Diff to review: `git diff 950bff5..af58305 -- shorts/blender/` (commits 1d8af4d and af58305). Read
`assets/characters/max/review/max_v6_notes.md` (sections v6c and v6d) for what was measured.

1. `max_hair_curves.hair_surface()`: the fisheye UV projection that replaced the spherical one, and
   `max_hair.copy_skin_weights()`. Could any root still map to the wrong triangle? Think of the
   projection centre `UV_CENTRE_DROP` and faces near the ears and nape. Are there poses or shapes that
   would break it?
2. `max_look.add_shirt_correctives()` (from your 012, plus my changes: onset 40° / full 85°, the matrix
   scale fix): is the driver maths right, and are there failure modes in animation (a crossing arm,
   motion blur, keyed poses)?
3. Chew (`max_expressions` mirrored chew_r, `build_max.chew_keys`/`ease_chew`/`chew_cycle`): timing at
   24 fps, any risk of a lip gap or popping between keys.

Rank the findings by severity. Under 600 words.
