"""Assemble the realistic sets into the film scene, each through the per-set cache.

Every builder call that shapes a set lives here (not in the shot builder), and this file is part
of every set's cache key: change how a set is built and that set is rebuilt; change a camera in
build_previz.py and nothing is.
"""
from pathlib import Path

import bpy

from greybox import CITY, EAR, EAR_MAP, SKY, CABIN, build_city, build_ear, build_sky

from . import airliner, cache, city, ear
from .cabin import build_cabin

SETS_DIR = Path(__file__).resolve().parent
BLENDER_DIR = SETS_DIR.parent
COMMON = [BLENDER_DIR / "greybox.py", BLENDER_DIR / "rigs.py", SETS_DIR / "pbr.py", SETS_DIR / "cache.py",
          Path(__file__).resolve()]


def realistic_sets(film):
    """Each set comes from out/sets/*.blend unless its source changed: only the set you are working
    on is rebuilt."""
    cache.get("sky", ["SET_sky", "ASSET_jet"], COMMON + [SETS_DIR / "airliner.py"],
              lambda: (build_sky(film), airliner.build_airliner(film), airliner.realistic_sky(film, SKY)))
    airliner.sky_world(film)
    cache.get("cabin", ["SET_cabin"], COMMON + [SETS_DIR / "cabin.py"], lambda: build_cabin(film, CABIN))
    cache.get("ear_in", ["SET_ear_in"], COMMON + [SETS_DIR / "ear.py"],
              lambda: ear.apply(build_ear(film, EAR, inside=True)))
    cache.get("ear_map", ["SET_ear_map"], COMMON + [SETS_DIR / "ear.py"],
              lambda: ear.apply(build_ear(film, EAR_MAP, inside=False)))
    cache.get("city", ["SET_city"], COMMON + [SETS_DIR / "city.py"],
              lambda: (build_city(film, blocks=False), city.build_city(film, CITY)))


def ear_dict(tag, origin):
    """The handles the ear animation needs, found by name in a (possibly cached) ear set."""
    obs = bpy.data.collections[f"SET_ear_{tag}"].all_objects

    def named(prefix):
        return sorted((o for o in obs if o.name.startswith(prefix) and o.name.endswith(f"_{tag}")), key=lambda o: o.name)
    return {"drum": obs[f"Eardrum_{tag}"], "tube": obs[f"Eustachian_tube_{tag}"], "outside": named("air_out_"),
            "inside": named("air_in_"), "flow": named("air_flow_"), "flash": obs[f"pop_flash_{tag}"],
            "ring": obs[f"pop_ring_{tag}"], "origin": origin, "tag": tag}
