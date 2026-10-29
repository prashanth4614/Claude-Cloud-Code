"""PBR materials from the CC0 texture library (assets/library/textures/<id>/color|normal|rough|ao.jpg).

Textures are box-projected in object space, so nothing needs UV unwrapping, and every material
falls back to a plain colour if the library hasn't been fetched (run assets/fetch_assets.py).
"""
from pathlib import Path

import bpy

LIB = Path(__file__).resolve().parents[3] / "assets" / "library"


def _img(path, non_color=False):
    img = bpy.data.images.load(str(path), check_existing=True)
    if non_color:
        img.colorspace_settings.name = "Non-Color"
    return img


def textured(name, tex_id, tint=(1, 1, 1), scale=4.0, rough_mul=1.0, normal=1.0, sheen=0.0, base=None):
    """Principled material from a texture set. tint multiplies the colour map (recolour fabrics)."""
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    d = LIB / "textures" / tex_id
    m.diffuse_color = (*(base or tint), 1)
    if not d.exists():
        bsdf.inputs["Base Color"].default_value = (*(base or tint), 1)
        return m
    coord = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (scale, scale, scale)
    nt.links.new(coord.outputs["Object"], mapping.inputs["Vector"])

    def tex(fname, non_color):
        p = next(iter(d.glob(fname + ".*")), None)
        if p is None:
            return None
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = _img(p, non_color)
        t.projection, t.projection_blend = "BOX", 0.25
        nt.links.new(mapping.outputs["Vector"], t.inputs["Vector"])
        return t

    col = tex("color", False)
    if col:
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type, mix.blend_type = "RGBA", "MULTIPLY"
        mix.inputs[0].default_value = 1.0
        mix.inputs[7].default_value = (*tint, 1)
        nt.links.new(col.outputs["Color"], mix.inputs[6])
        ao = tex("ao", True)
        if ao:
            mao = nt.nodes.new("ShaderNodeMix")
            mao.data_type, mao.blend_type = "RGBA", "MULTIPLY"
            mao.inputs[0].default_value = 0.6
            nt.links.new(mix.outputs[2], mao.inputs[6])
            nt.links.new(ao.outputs["Color"], mao.inputs[7])
            nt.links.new(mao.outputs[2], bsdf.inputs["Base Color"])
        else:
            nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])
    r = tex("rough", True)
    if r:
        mr = nt.nodes.new("ShaderNodeMath")
        mr.operation = "MULTIPLY"
        mr.inputs[1].default_value = rough_mul
        nt.links.new(r.outputs["Color"], mr.inputs[0])
        nt.links.new(mr.outputs[0], bsdf.inputs["Roughness"])
    n = tex("normal", True)
    if n:
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nm.inputs["Strength"].default_value = normal
        nt.links.new(n.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    if sheen and "Sheen Weight" in bsdf.inputs:
        bsdf.inputs["Sheen Weight"].default_value = sheen
    return m


def plain(name, color, rough=0.5, metal=0.0, emission=0.0, coat=0.0):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if coat and "Coat Weight" in b.inputs:
        b.inputs["Coat Weight"].default_value = coat
    if emission:
        b.inputs["Emission Color"].default_value = (*color, 1)
        b.inputs["Emission Strength"].default_value = emission
    m.diffuse_color = (*color, 1)
    return m
