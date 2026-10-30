"""Realism pass for the ear sets built by greybox.build_ear (inside journey and x-ray map).

Keeps every object, name and animated socket the shots rely on (eardrum shape keys, the tube's
bevel and colour, the emission flashes), and replaces the look:
  - tissue: wet subsurface flesh with fine branching veins, mottling and a clear wet coat;
  - real surface relief: the canal and middle-ear walls get displaced folds and bumps;
  - ear canal: skin-toned near the entrance with a hint of wax, turning pink deeper in;
  - eardrum: a pearly, translucent membrane with radial fibres;
  - ossicles: ivory bone.
"""
import bpy

SSS_SCALE = 0.25   # scene units: the ear is scaled up ~400x, so tissue scattering is ~0.25 units deep


def _nodes(m):
    m.use_nodes = True
    return m.node_tree, m.node_tree.nodes["Principled BSDF"]


def _set(b, name, value):
    if name in b.inputs:
        b.inputs[name].default_value = value


def _bump(nt, b, strength=0.35, scale=2.2, vein_scale=1.2):
    """Bumpy wet tissue: noise lumps + a vein network raised slightly."""
    coord = nt.nodes.new("ShaderNodeTexCoord")
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = scale
    noise.inputs["Detail"].default_value = 10
    noise.inputs["Roughness"].default_value = 0.6
    nt.links.new(coord.outputs["Object"], noise.inputs["Vector"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = strength
    bump.inputs["Distance"].default_value = 0.05
    nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    return coord, noise


def _veins(nt, coord, scale=1.2):
    """0..1 mask of thin, wandering veins (distorted Voronoi cell edges)."""
    warp = nt.nodes.new("ShaderNodeTexNoise")
    warp.inputs["Scale"].default_value = 0.8
    warp.inputs["Detail"].default_value = 4
    nt.links.new(coord.outputs["Object"], warp.inputs["Vector"])
    mixv = nt.nodes.new("ShaderNodeMix")
    mixv.data_type = "VECTOR"
    mixv.inputs[0].default_value = 0.35
    nt.links.new(coord.outputs["Object"], mixv.inputs[4])
    nt.links.new(warp.outputs["Color"], mixv.inputs[5])
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    vor.feature = "DISTANCE_TO_EDGE"
    vor.inputs["Scale"].default_value = scale
    nt.links.new(mixv.outputs[1], vor.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position, ramp.color_ramp.elements[0].color = 0.0, (1, 1, 1, 1)
    ramp.color_ramp.elements[1].position, ramp.color_ramp.elements[1].color = 0.035, (0, 0, 0, 1)
    nt.links.new(vor.outputs["Distance"], ramp.inputs["Fac"])
    return ramp


def tissue(m, base=(0.72, 0.28, 0.27), vein=(0.42, 0.06, 0.1), glow=0.0, animated_color=False, wax_ramp=False,
           wet=0.6):
    """Turn a greybox Principled material into wet living tissue (in place, same node names)."""
    nt, b = _nodes(m)
    _set(b, "Roughness", 0.32 if wet > 0.4 else 0.45)
    _set(b, "Subsurface Weight", 0.55)
    _set(b, "Subsurface Radius", (1.0, 0.35, 0.25))
    _set(b, "Subsurface Scale", SSS_SCALE)
    _set(b, "Coat Weight", wet)
    _set(b, "Coat Roughness", 0.06 if wet > 0.4 else 0.15)
    _set(b, "Specular IOR Level", 0.6)
    coord, noise = _bump(nt, b)
    if animated_color:
        return m          # the shots key this material's Base Color (the tube turning red): leave it unlinked
    veins = _veins(nt, coord)
    mott = nt.nodes.new("ShaderNodeMix")              # mottled flesh: base colour varied by the bump noise
    mott.data_type, mott.blend_type = "RGBA", "MULTIPLY"
    mott.inputs[0].default_value = 0.35
    mott.inputs[6].default_value = (*base, 1)
    nt.links.new(noise.outputs["Color"], mott.inputs[7])
    col = mott.outputs[2]
    if wax_ramp:                                      # canal: skin/wax tones near the entrance -> pink inside
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        nt.links.new(coord.outputs["Generated"], sep.inputs[0])
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        cr = ramp.color_ramp
        cr.elements[0].position, cr.elements[0].color = 0.0, (0.72, 0.45, 0.36, 1)   # canal skin near the entrance
        cr.elements[1].position, cr.elements[1].color = 0.7, (*base, 1)
        e = cr.elements.new(0.3)
        e.color = (0.78, 0.5, 0.25, 1)                                                 # a little wax
        nt.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
        wax = nt.nodes.new("ShaderNodeMix")
        wax.data_type, wax.blend_type = "RGBA", "MULTIPLY"
        wax.inputs[0].default_value = 1.0
        nt.links.new(col, wax.inputs[6])
        nt.links.new(ramp.outputs["Color"], wax.inputs[7])
        col = wax.outputs[2]
    mixv = nt.nodes.new("ShaderNodeMix")
    mixv.data_type = "RGBA"
    nt.links.new(veins.outputs["Color"], mixv.inputs[0])
    nt.links.new(col, mixv.inputs[6])
    mixv.inputs[7].default_value = (*vein, 1)
    nt.links.new(mixv.outputs[2], b.inputs["Base Color"])
    if glow:
        nt.links.new(mixv.outputs[2], b.inputs["Emission Color"])
        _set(b, "Emission Strength", glow)
    return m


def eardrum(m):
    """Pearly, slightly translucent membrane with radial fibres (Emission stays free for the strain glow)."""
    nt, b = _nodes(m)
    _set(b, "Base Color", (0.86, 0.8, 0.78, 1))
    _set(b, "Roughness", 0.18)
    _set(b, "Subsurface Weight", 0.4)
    _set(b, "Subsurface Scale", 0.15)
    _set(b, "Sheen Weight", 0.2)
    _set(b, "Sheen Tint", (0.9, 0.85, 1.0, 1))
    _set(b, "Coat Weight", 0.8)
    _set(b, "Coat Roughness", 0.04)
    coord = nt.nodes.new("ShaderNodeTexCoord")
    wave = nt.nodes.new("ShaderNodeTexWave")          # radial fibres
    wave.wave_type, wave.rings_direction = "RINGS", "SPHERICAL"
    wave.inputs["Scale"].default_value = 6.0
    wave.inputs["Distortion"].default_value = 2.0
    nt.links.new(coord.outputs["Object"], wave.inputs["Vector"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.15
    nt.links.new(wave.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def bone(m):
    nt, b = _nodes(m)
    _set(b, "Base Color", (0.9, 0.84, 0.72, 1))
    _set(b, "Roughness", 0.45)
    _set(b, "Subsurface Weight", 0.3)
    _set(b, "Subsurface Scale", 0.05)
    _bump(nt, b, strength=0.25, scale=6.0)
    return m


def relief(ob, strength=0.18, scale=1.4, subdiv=2, length_cuts=0):
    """Real folds and bumps in the wall geometry (not just shading). length_cuts adds ring cuts
    along a long tube (the canal) so the displacement has geometry to work with."""
    import bmesh
    from mathutils import Matrix
    ob.data.transform(Matrix.Diagonal((*ob.scale, 1.0)))   # bake the stretch, or the relief shears
    ob.scale = (1, 1, 1)
    if length_cuts:
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        longest = max(e.calc_length() for e in bm.edges)
        long = [e for e in bm.edges if e.calc_length() > 0.6 * longest]
        bmesh.ops.subdivide_edges(bm, edges=long, cuts=length_cuts, use_grid_fill=False)
        bm.to_mesh(ob.data)
        bm.free()
    s = ob.modifiers.new("detail", "SUBSURF")
    s.subdivision_type, s.levels, s.render_levels = "SIMPLE", subdiv, subdiv
    tex = bpy.data.textures.get(f"tissue_folds_{scale}") or bpy.data.textures.new(f"tissue_folds_{scale}", "CLOUDS")
    tex.noise_scale, tex.noise_depth = scale, 3
    d = ob.modifiers.new("folds", "DISPLACE")
    d.texture, d.strength, d.mid_level, d.texture_coords = tex, strength, 0.5, "GLOBAL"
    sm = ob.modifiers.new("smooth", "SUBSURF")
    sm.levels, sm.render_levels = 0, 1
    for p in ob.data.polygons:
        p.use_smooth = True


def round_openings(chamber, o):
    """Rebuild the middle ear as a dense sphere with smooth, round openings (toward the eardrum
    and into the Eustachian tube) in place of the coarse stair-stepped holes."""
    import bmesh
    import math
    from mathutils import Vector
    from greybox import TUBE_PTS
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=160, v_segments=80, radius=1.0)
    centre = chamber.location.copy()
    holes = ((Vector((-1, 0, 0)), 36.0), ((TUBE_PTS[0] + o - centre).normalized(), 13.0))
    for d, a in holes:          # slice each cap off with a plane: a perfectly round rim, no stair-steps
        geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-5, plane_co=d * math.cos(math.radians(a)), plane_no=d,
                               clear_outer=True)
    for f in bm.faces:
        f.smooth = True
    bm.to_mesh(chamber.data)
    bm.free()


def _open_cone(name, coll, base, tip, r_base, r_tip, mat):
    """Open-ended tube/funnel between two points (no caps), for sealing gaps between parts."""
    import bmesh
    from mathutils import Vector
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=False, segments=64, radius1=r_base, radius2=r_tip, depth=1.0)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    axis = Vector(tip) - Vector(base)
    ob.rotation_mode = "QUATERNION"
    ob.rotation_quaternion = axis.to_track_quat("Z", "Y")
    ob.scale = (1, 1, axis.length)
    ob.location = (Vector(base) + Vector(tip)) / 2
    me.materials.append(mat)
    for p in me.polygons:
        p.use_smooth = True
    return ob


def seals(chamber, o, mat):
    """Tissue that closes the gaps a camera could see through: a collar from the eardrum's rim to
    the middle ear (the bony ring around the drum), and a funnel at the Eustachian tube's mouth."""
    from mathutils import Vector
    from greybox import TUBE_PTS
    coll = chamber.users_collection[0]
    centre = chamber.location.copy()
    collar = _open_cone("tympanic_collar_in", coll, o + Vector((-0.95, 0, 0)), centre + Vector((-1.9, 0, 0)),
                        1.6, 1.62, mat)
    d = (TUBE_PTS[0] + o - centre).normalized()
    funnel = _open_cone("tube_mouth_in", coll, centre + d * 2.25, centre + d * 3.3, 0.78, 0.14, mat)  # tip tucks inside the closed tube (r 0.16)
    for ob in (collar, funnel):
        relief(ob, strength=0.05, scale=1.0, length_cuts=12)
    # the tube's valve: soft lips closing the funnel's tip while the tube is shut (the build parts them
    # by scaling "tube_valve_in" to 0 when the tube cracks open)
    import bmesh as _bm
    vm = bpy.data.meshes.new("tube_valve_in")
    b = _bm.new()
    _bm.ops.create_uvsphere(b, u_segments=32, v_segments=16, radius=1.0)
    b.to_mesh(vm)
    b.free()
    valve = bpy.data.objects.new("tube_valve_in", vm)
    coll.objects.link(valve)
    valve.location = centre + d * 3.22
    valve.rotation_mode = "QUATERNION"
    valve.rotation_quaternion = d.to_track_quat("Z", "Y")
    valve.scale = (0.26, 0.26, 0.05)
    vm.materials.append(mat)
    for p in vm.polygons:
        p.use_smooth = True
    # the slit: a dark crease across the lips, so it reads as a closed opening, not a ball
    sm = bpy.data.meshes.new("tube_valve_slit_in")
    b = _bm.new()
    _bm.ops.create_cube(b, size=2.0)
    b.to_mesh(sm)
    b.free()
    slit = bpy.data.objects.new("tube_valve_slit_in", sm)
    coll.objects.link(slit)
    slit.parent = valve                       # scales away with the valve when the tube opens
    slit.scale = (0.85, 0.06, 1.15)           # in the valve's space: across it, thin, through its thickness
    dark = bpy.data.materials.new("tube_slit")
    dark.diffuse_color = (0.12, 0.02, 0.03, 1)
    dark.use_nodes = True
    dark.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.12, 0.02, 0.03, 1)
    sm.materials.append(dark)
    # the tympanic annulus: the fibrous ring that holds the eardrum's edge. It also closes the seam
    # where the drum (r 1.55), the canal's end (r 1.5) and the collar (r 1.6) meet.
    import bmesh
    import math
    bm = bmesh.new()
    segs, ring_segs, major, minor = 96, 12, 1.57, 0.13
    rings = []
    for i in range(segs):
        a = 2 * math.pi * i / segs
        rings.append([bm.verts.new((minor * math.cos(2 * math.pi * j / ring_segs),
                                    (major + minor * math.sin(2 * math.pi * j / ring_segs)) * math.cos(a),
                                    (major + minor * math.sin(2 * math.pi * j / ring_segs)) * math.sin(a)))
                      for j in range(ring_segs)])
    for i in range(segs):
        r0, r1 = rings[i], rings[(i + 1) % segs]
        for j in range(ring_segs):
            k = (j + 1) % ring_segs
            bm.faces.new((r0[j], r0[k], r1[k], r1[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new("tympanic_annulus_in")
    bm.to_mesh(me)
    bm.free()
    ring = bpy.data.objects.new("tympanic_annulus_in", me)
    coll.objects.link(ring)
    ring.location = o + Vector((-0.8, 0, 0))
    me.materials.append(mat)
    for p in me.polygons:
        p.use_smooth = True


def exit_glow(o, coll):
    """Warm light at the ear canal's opening (the lit cabin outside), so flying back out of the canal
    heads toward light instead of a black hole."""
    import bmesh
    from mathutils import Vector
    m = bpy.data.materials.new("ear_exit_glow")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (1.0, 0.84, 0.66, 1)
    clear = nt.nodes.new("ShaderNodeBsdfTransparent")
    coord = nt.nodes.new("ShaderNodeTexCoord")
    grad = nt.nodes.new("ShaderNodeTexGradient")               # 1 at the centre -> 0 at the rim
    grad.gradient_type = "SPHERICAL"
    scale = nt.nodes.new("ShaderNodeMapping")
    scale.inputs["Scale"].default_value = (1 / 2.4, 1 / 2.4, 1 / 2.4)
    nt.links.new(coord.outputs["Object"], scale.inputs["Vector"])
    nt.links.new(scale.outputs["Vector"], grad.inputs["Vector"])
    soft = nt.nodes.new("ShaderNodeMath")                      # soft falloff: glow ** 1.8
    soft.operation, soft.inputs[1].default_value = "POWER", 1.8
    nt.links.new(grad.outputs["Fac"], soft.inputs[0])
    strength = nt.nodes.new("ShaderNodeMath")
    strength.operation, strength.inputs[1].default_value = "MULTIPLY", 5.0
    nt.links.new(soft.outputs[0], strength.inputs[0])
    nt.links.new(strength.outputs[0], em.inputs["Strength"])
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(soft.outputs[0], mix.inputs["Fac"])
    nt.links.new(clear.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    if hasattr(m, "surface_render_method"):
        m.surface_render_method = "BLENDED"
    bm = bmesh.new()
    bmesh.ops.create_circle(bm, cap_ends=True, segments=64, radius=2.4)
    me = bpy.data.meshes.new("ear_exit_glow_in")
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("ear_exit_glow_in", me)
    coll.objects.link(ob)
    ob.location, ob.rotation_euler = o + Vector((-17.6, 0, 0)), (0, 1.5708, 0)
    me.materials.append(m)
    ob.visible_shadow = False
    return ob


def xray(name, color=(0.45, 0.85, 1.0)):
    """X-ray scan look: walls glow at grazing angles (outlines), nearly clear face-on."""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.35
    edge = nt.nodes.new("ShaderNodeMath")
    edge.operation, edge.inputs[1].default_value = "POWER", 1.6
    nt.links.new(lw.outputs["Facing"], edge.inputs[0])
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*color, 1)
    st = nt.nodes.new("ShaderNodeMath")
    st.operation, st.inputs[1].default_value = "MULTIPLY", 3.0
    nt.links.new(edge.outputs[0], st.inputs[0])
    nt.links.new(st.outputs[0], em.inputs["Strength"])
    clear = nt.nodes.new("ShaderNodeBsdfTransparent")
    alpha = nt.nodes.new("ShaderNodeMapRange")
    alpha.inputs["To Min"].default_value, alpha.inputs["To Max"].default_value = 0.12, 1.0
    nt.links.new(edge.outputs[0], alpha.inputs["Value"])
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(alpha.outputs["Result"], mix.inputs["Fac"])
    nt.links.new(clear.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    if hasattr(m, "surface_render_method"):
        m.surface_render_method = "BLENDED"
    m.diffuse_color = (*color, 0.4)
    return m


def xray_backdrop(dome):
    """Deep navy scan backdrop, a little brighter at the centre of view."""
    m = bpy.data.materials.new("xray_backdrop")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    lw = nt.nodes.new("ShaderNodeLayerWeight")       # facing the camera = centre of the dome in view
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.035, 0.07, 0.14, 1)
    ramp.color_ramp.elements[1].color = (0.005, 0.01, 0.03, 1)
    nt.links.new(lw.outputs["Facing"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], em.inputs["Color"])
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    dome.data.materials.clear()
    dome.data.materials.append(m)


def trim_tube_start(tube, o, chamber_centre, start_dist=3.15):
    """Start the Eustachian tube's visible surface where the mouth funnel ends, so no tube end
    sits inside the funnel. The tube's path (and the camera ride along it) is unchanged."""
    from greybox import tube_point
    u = 0.0
    while u < 0.5 and (tube_point(u, o) - chamber_centre).length < start_dist:
        u += 0.002
    tube.data.bevel_factor_mapping_start = "SPLINE"
    tube.data.bevel_factor_start = u
    return u


def ossicle_knobs(e):
    """The three tiny bones read as a pencil when they're plain rods: give the chain its silhouette
    (the malleus head, the incus body, the stapes footplate) with rounded knobs at the joints.
    Stand-in until the real BodyParts3D bones."""
    import bmesh
    from mathutils import Vector
    tag, o = e["tag"], e["origin"]
    k = 1.0 if tag == "in" else 1.4                    # the map's bones are drawn thicker
    coll = e["drum"].users_collection[0]
    bone_mat = bpy.data.materials["ossicle"]
    for name, at, size in (("malleus_head", (0.6, 0.2, 0.9), (0.24, 0.2, 0.3)),
                           ("incus_body", (1.4, 0.3, 0.8), (0.2, 0.17, 0.22)),
                           ("stapes_foot", (2.2, 0.3, 0.1), (0.07, 0.2, 0.16))):
        me = bpy.data.meshes.new(f"ossicle_{name}_{tag}")
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=1.0)
        bm.to_mesh(me)
        bm.free()
        ob = bpy.data.objects.new(f"ossicle_{name}_{tag}", me)
        ob.location, ob.scale = o + Vector(at), [s * k for s in size]
        me.materials.append(bone_mat)
        coll.objects.link(ob)


def apply(e):
    """Realism pass on one ear set (the dict build_ear returned)."""
    tag = e["tag"]
    inside = tag == "in"
    glow = 0.12 if inside else 0.0
    get = bpy.data.objects.get
    canal, chamber, throat = get(f"ear_canal_{tag}"), get(f"middle_ear_{tag}"), get(f"throat_{tag}")
    if inside:
        canal_mat = bpy.data.materials.new(f"canal_skin_{tag}")
        tissue(canal_mat, base=(0.74, 0.32, 0.29), glow=glow * 0.5, wax_ramp=True, wet=0.2)  # canal skin: drier
        _set(canal_mat.node_tree.nodes["Principled BSDF"], "Specular IOR Level", 0.3)
        tissue(bpy.data.materials[f"tissue_dark_{tag}"], base=(0.6, 0.18, 0.2), vein=(0.35, 0.03, 0.08), glow=glow)
    else:                       # the map (S04m) is an x-ray diagram: glowing outlines on navy
        canal_mat = xray("xray_canal", (0.5, 0.85, 1.0))
        for ob in (chamber, throat):
            ob.data.materials.clear()
            ob.data.materials.append(xray("xray_cavity", (0.75, 0.9, 1.0)))
        xray_backdrop(bpy.data.objects[f"ear_dome_{tag}"])
    canal.data.materials.clear()
    canal.data.materials.append(canal_mat)
    tissue(bpy.data.materials[f"tube_{tag}"], glow=0.0, animated_color=True)
    eardrum(bpy.data.materials[f"eardrum_{tag}"])
    bone(bpy.data.materials["ossicle"])
    if inside:
        round_openings(chamber, e["origin"])
        seals(chamber, e["origin"], bpy.data.materials[f"tissue_dark_{tag}"])
        e["tube"].data.use_fill_caps = False      # hollow: you look down into the tube, not at a cap
        exit_glow(e["origin"], e["drum"].users_collection[0])
        trim_tube_start(e["tube"], e["origin"], chamber.location.copy())
    for ob in e["drum"].users_collection[0].objects:   # light the tissue, but never show up as glowing balls
        if ob.type == "LIGHT":
            ob.visible_camera = False
            if ob.name.startswith("tube_"):            # inside a 0.16-0.55 tube: small and soft, no hotspots
                ob.data.energy, ob.data.shadow_soft_size = 6.0, 0.08
    relief(canal, strength=0.14 if inside else 0.09, length_cuts=48)
    relief(chamber, strength=0.12 if inside else 0.08, subdiv=0 if inside else 2)  # dense already
    relief(throat, strength=0.12 if inside else 0.08)
    # air molecules: smooth, softly glowing beads (cool blue outside, warm amber inside)
    for name, col in (("air_outside", (0.25, 0.62, 1.0)), ("air_inside", (1.0, 0.5, 0.12))):
        m = bpy.data.materials.get(name)
        if m:
            nt, b = _nodes(m)
            _set(b, "Base Color", (*col, 1))
            _set(b, "Emission Color", (*col, 1))
            _set(b, "Emission Strength", 1.2)
            _set(b, "Coat Weight", 1.0)
            _set(b, "Roughness", 0.1)
    for ob in bpy.data.objects:
        if ob.name.startswith("air_") and ob.name.endswith(tag) and ob.type == "MESH":
            for p in ob.data.polygons:
                p.use_smooth = True
            if not ob.modifiers.get("smooth"):
                sm = ob.modifiers.new("smooth", "SUBSURF")
                sm.levels = sm.render_levels = 1
    ossicle_knobs(e)
    for ob in bpy.data.objects:
        if ob.name.startswith(f"ossicle_") and ob.name.endswith(tag):
            s = ob.modifiers.new("smooth", "SUBSURF")
            s.levels = s.render_levels = 2
            for p in ob.data.polygons:
                p.use_smooth = True
