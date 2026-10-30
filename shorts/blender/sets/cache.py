"""Per-set build cache: build a set once, save it to out/sets/<name>.blend, and load it next time.

A set is rebuilt only when one of its source files (or the fetched asset library) changes, so
tweaking the cabin no longer rebuilds the ear, the sky and the city. Heavy static modifiers
(window booleans, tissue and cloud displacement, subdivision) are baked into plain meshes before
saving, so loading is instant and renders skip re-evaluating them on every frame.

    coll = cache.get("cabin", deps, build_fn)   # build_fn() builds it into the open scene, returns nothing
"""
import hashlib
import json
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[3]
CACHE = ROOT / "out" / "sets"
LIB = ROOT / "assets" / "library"
VERSION = 2      # bump to invalidate every cached set (2: bake at render subdivision levels)


def _key(deps):
    h = hashlib.sha256()
    h.update(f"{VERSION} {bpy.app.version_string}".encode())
    for d in sorted(str(p) for p in deps):
        p = Path(d)
        h.update(d.encode())
        h.update(p.read_bytes() if p.exists() else b"-")
    if LIB.exists():                                   # which CC0 assets were available when it was built
        h.update(" ".join(sorted(str(p.relative_to(LIB)) for p in LIB.rglob("*") if p.is_file())).encode())
    return h.hexdigest()[:16]


def bake_modifiers(coll):
    """Replace static modifier stacks with their result (keeps shape-keyed and rigged meshes live)."""
    todo = []
    for ob in list(coll.all_objects):
        if ob.type != "MESH" or not ob.modifiers:
            continue
        if ob.data.shape_keys or any(m.type in {"ARMATURE", "PARTICLE_SYSTEM"} for m in ob.modifiers):
            continue
        for m in ob.modifiers:          # bake what the RENDER sees (subdivision often renders finer)
            if hasattr(m, "render_levels"):
                m.levels = m.render_levels
            m.show_viewport = m.show_render
        todo.append(ob)
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    for ob in todo:
        me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
        old = ob.data
        ob.modifiers.clear()
        ob.data = me
        if old.users == 0:
            bpy.data.meshes.remove(old)
    for ob in list(coll.all_objects):           # boolean cutters are no longer needed once baked
        if ob.type == "MESH" and ob.hide_render:
            bpy.data.objects.remove(ob, do_unlink=True)


def get(name, colls, deps, build, scene=None, bake=True):
    """Return the set's top-level collections, building and caching them if needed.
    colls: names of the collections the builder creates (all are cached together)."""
    scene = scene or bpy.context.scene
    CACHE.mkdir(parents=True, exist_ok=True)
    blend, meta = CACHE / f"{name}.blend", CACHE / f"{name}.json"
    key = _key(deps)
    if blend.exists() and meta.exists() and json.loads(meta.read_text()).get("key") == key:
        with bpy.data.libraries.load(str(blend), link=False) as (src, dst):
            dst.collections = [c for c in src.collections if c in colls]
        for c in dst.collections:
            scene.collection.children.link(c)
        print(f"[sets] {name}: cached ({blend.name})")
        return {c.name: c for c in dst.collections}
    build()
    out = {n: bpy.data.collections[n] for n in colls}
    if bake:
        for c in out.values():
            bake_modifiers(c)
    bpy.data.libraries.write(str(blend), set(out.values()), fake_user=True, compress=True)
    meta.write_text(json.dumps({"key": key, "collections": colls}))
    print(f"[sets] {name}: built and cached")
    return out
