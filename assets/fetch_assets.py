"""Download the free CC0 assets the sets use into assets/library/ (cached, not committed).

    python3 assets/fetch_assets.py            # everything in MANIFEST
    python3 assets/fetch_assets.py --list     # show what's there

Sources: Poly Haven (polyhaven.com) and ambientCG (ambientcg.com), both CC0, so no credit is
required (we credit them anyway in assets/LICENSES.md). Builders load files from
assets/library/<kind>/<id>/..., and pack them into the .blend before it goes to RunPod.
"""
import io
import json
import sys
import urllib.request
import zipfile
from pathlib import Path

LIB = Path(__file__).resolve().parent / "library"
UA = {"User-Agent": "claude-shorts-pipeline/1.0"}

MANIFEST = {
    "hdri": {   # Poly Haven HDRIs (2k EXR): sky light + background
        "qwantani_sunset_puresky": "golden-hour climb (S01)",
        "syferfontein_6d_clear_puresky": "high cruise above the clouds (S05a)",
        "qwantani_dusk_2_puresky": "dusk descent over the city (S10)",
    },
    "polyhaven_tex": {   # Poly Haven PBR textures (1k JPG)
        "poly_wool_herringbone": "airline seat upholstery",
        "leather_white": "seat headrest covers",
        "fabric_leather_02": "armrest pads",
    },
    "ambientcg_tex": {   # ambientCG PBR textures (1K JPG)
        "Carpet012": "cabin aisle carpet",
        "Plastic010": "cabin wall/bin panels (fine texture)",
    },
}


def _get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=300) as r:
        return r.read()


def _save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    print(f"  {path.relative_to(LIB)}  ({len(data) // 1024} KB)")


def hdri(asset_id, res="2k"):
    out = LIB / "hdri" / f"{asset_id}_{res}.exr"
    if out.exists():
        return out
    files = json.loads(_get(f"https://api.polyhaven.com/files/{asset_id}"))
    _save(out, _get(files["hdri"][res]["exr"]["url"]))
    return out


def polyhaven_tex(asset_id, res="1k"):
    d = LIB / "textures" / asset_id
    if d.exists() and any(d.iterdir()):
        return d
    files = json.loads(_get(f"https://api.polyhaven.com/files/{asset_id}"))
    for key, name in (("Diffuse", "color"), ("nor_gl", "normal"), ("Rough", "rough"), ("AO", "ao"), ("Displacement", "disp")):
        if key in files and res in files[key]:
            fmt = files[key][res].get("jpg") or files[key][res].get("png")
            if fmt:
                _save(d / f"{name}.{fmt['url'].rsplit('.', 1)[1]}", _get(fmt["url"]))
    return d


def ambientcg_tex(asset_id, res="1K"):
    d = LIB / "textures" / asset_id
    if d.exists() and any(d.iterdir()):
        return d
    z = zipfile.ZipFile(io.BytesIO(_get(f"https://ambientcg.com/get?file={asset_id}_{res}-JPG.zip")))
    names = {"Color": "color", "NormalGL": "normal", "Roughness": "rough", "AmbientOcclusion": "ao", "Displacement": "disp"}
    for n in z.namelist():
        for key, name in names.items():
            if n.endswith(f"_{key}.jpg"):
                _save(d / f"{name}.jpg", z.read(n))
    return d


def fetch_all():
    for kind, items in MANIFEST.items():
        for asset_id in items:
            print(f"{kind}: {asset_id}")
            {"hdri": hdri, "polyhaven_tex": polyhaven_tex, "ambientcg_tex": ambientcg_tex}[kind](asset_id)


if __name__ == "__main__":
    if "--list" in sys.argv:
        for p in sorted(LIB.rglob("*")):
            if p.is_file():
                print(p.relative_to(LIB))
    else:
        fetch_all()
