# Codex answer: 001-cache-review

_model: gpt-6.1-sol, reasoning effort: high, read-only_

- **[shorts/blender/sets/cache.py:42](/Users/prashanthmogili/Claude-Cloud-Code-codex/shorts/blender/sets/cache.py:42) — Render subdivision lost.** `ear.relief()` sets its final subdivision to `levels=0`, `render_levels=1` (`ear.py:169`). Baking evaluates the viewport mesh, then clears every modifier. Consequently, both ear sets permanently lose their render smoothing, including on the initial build. Blender distinguishes [viewport and render evaluation](https://docs.blender.org/api/5.0/bpy.types.Depsgraph.html). **Smallest fix:** skip baking objects whose subdivision viewport/render levels differ.

- **[shorts/pilot_ear_pop/build_previz.py:508](/Users/prashanthmogili/Claude-Cloud-Code-codex/shorts/pilot_ear_pop/build_previz.py:508) — Builder configuration excluded from key.** Cache the cabin, then change its lambda at line 519 to pass `CABIN + Vector((0, 0, 1))`. Only `build_previz.py` changes; every hashed dependency remains identical. The cache serves the cabin at its previous position. Equivalent failures affect changes to the other builder calls. **Smallest fix:** include `Path(__file__)` in `COMMON`.

Static review; installed Blender 5.2.3 crashed during GPU initialization before runtime checks.

Verdict: two actionable bugs; fix render-detail baking and builder-input invalidation.

_took 196 s_
STATUS: OK
