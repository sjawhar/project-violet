"""THROWAWAY Phase 1 bake-off: builds the low-poly 3D desert kit (docs/bakeoff/desert-biome-brief.md).

    blender -b --factory-startup --python assets/bakeoff/desert-kit-3d/build_kit.py -- OUT_DIR

Writes OUT_DIR/<piece>.glb for every piece in PIECES: glTF binary, +Y up, meters, origin at the base center, no
cameras or lights. Every piece is built from SEED alone, so a rebuild is byte-identical.

Blender axes while building: +Z up, and the side-scroller camera looks along +Y, so a piece's front faces -Y
(glTF +Z). Colors are named Principled BSDF materials in the biome palette; a neutral gray vertex color multiplies
the base color for painterly variation (glTF COLOR_0 times baseColorFactor), so tinting a material still works.
"""

import math
import random
import sys
import zlib
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector

SEED = 20260927
MAX_TRIANGLES = 5000
TAU = 2 * math.pi

# sRGB hex. sand, rock, shadow and the sky teal are the brief's; the rest are mixes of them.
PALETTE = {
    "sand": "d9b27c",
    "sand_deep": "cda16e",  # sand 75% + rock 25%
    "sand_shade": "b3927b",  # sand 70% + shadow 30%
    "rock": "a86f46",
    "rock_light": "bc8a5c",  # rock 60% + sand 40%
    "rock_dark": "916456",  # rock 70% + shadow 30%
    "shadow": "5a4a7a",
    "stone": "c89b69",  # sand 65% + rock 35%
    "tag": "d4d4d4",  # untinted neutral light gray: lanes tint it red, green or gray
    "orb": "d4d4d4",  # untinted, as tag
    "portal": "3f7f8c",  # sky teal
}
EMISSION = {"portal": ("4fb8c8", 1.2)}
# Materials that carry no vertex variation, in order of preference for a mesh's first material slot.
FLAT_FIRST = ("shadow", "sand_deep", "sand_shade")


def srgb_to_linear(hex_color):
    def channel(c):
        c = c / 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    return tuple(channel(int(hex_color[i : i + 2], 16)) for i in (0, 2, 4)) + (1.0,)


def material(name):
    existing = bpy.data.materials.get(name)
    if existing is not None:
        return existing
    mat = bpy.data.materials.new(name)
    mat.use_backface_culling = True
    tree = mat.node_tree
    bsdf = tree.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 1.0
    bsdf.inputs["Specular IOR Level"].default_value = 0.2
    vertex_color = tree.nodes.new("ShaderNodeVertexColor")
    vertex_color.layer_name = "Color"
    mix = tree.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 1.0
    tree.links.new(vertex_color.outputs["Color"], mix.inputs[6])
    mix.inputs[7].default_value = srgb_to_linear(PALETTE[name])
    tree.links.new(mix.outputs[2], bsdf.inputs["Base Color"])
    if name in EMISSION:
        color, strength = EMISSION[name]
        bsdf.inputs["Emission Color"].default_value = srgb_to_linear(color)
        bsdf.inputs["Emission Strength"].default_value = strength
    return mat


class Geo:
    """Vertices with a gray shade, faces with a material name and a per-face shade (the painterly variation)."""

    def __init__(self, rng):
        self.rng = rng
        self.co = []
        self.shade = []
        self.faces = []
        self.mats = []
        self.fvar = []

    def v(self, co, shade=1.0):
        self.co.append(Vector(co))
        self.shade.append(shade)
        return len(self.co) - 1

    def f(self, idx, mat, var=None):
        self.faces.append(tuple(idx))
        self.mats.append(mat)
        self.fvar.append(self.rng.uniform(0.9, 1.0) if var is None else var)
        return len(self.faces) - 1

    def band(self, a, b, mat, var=None):
        """Quads joining closed loops a and b; a loop counter-clockwise seen from b's side faces outward."""
        n = len(a)
        return [self.f((a[i], a[(i + 1) % n], b[(i + 1) % n], b[i]), mat, var) for i in range(n)]

    def fan(self, loop, apex, mat, var=None):
        n = len(loop)
        return [self.f((loop[i], loop[(i + 1) % n], apex), mat, var) for i in range(n)]

    def box(self, lo, hi, mat, var=None, transform=None, jitter=0.0):
        corners = [
            (lo[0], lo[1], lo[2]), (hi[0], lo[1], lo[2]), (hi[0], hi[1], lo[2]), (lo[0], hi[1], lo[2]),
            (lo[0], lo[1], hi[2]), (hi[0], lo[1], hi[2]), (hi[0], hi[1], hi[2]), (lo[0], hi[1], hi[2]),
        ]
        idx = []
        for c in corners:
            p = Vector(c) + Vector([self.rng.uniform(-jitter, jitter) for _ in range(3)])
            p = transform @ p if transform is not None else p
            idx.append(self.v((p.x, p.y, max(p.z, 0.0))))
        quads = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
        var = self.rng.uniform(0.9, 1.0) if var is None else var
        return [self.f([idx[q] for q in quad], mat, var) for quad in quads]

    def hull(self, points, mat, shade_fn=None, flat_faces=False):
        """Convex hull of points. flat_faces merges coplanar triangles into single faces of one shade."""
        bm = bmesh.new()
        for p in points:
            bm.verts.new(p)
        bmesh.ops.convex_hull(bm, input=list(bm.verts))
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        if flat_faces:
            bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(0.5), verts=list(bm.verts), edges=list(bm.edges))
        bm.verts.index_update()
        remap = {}
        start = len(self.faces)
        for face in bm.faces:
            idx = []
            for vert in face.verts:
                if vert.index not in remap:
                    remap[vert.index] = self.v(vert.co, shade_fn(vert.co) if shade_fn else 1.0)
                idx.append(remap[vert.index])
            self.f(idx, mat, 1.0 if flat_faces else None)
        bm.free()
        return range(start, len(self.faces))

    def normal(self, fi):
        pts = [self.co[i] for i in self.faces[fi]]
        n = Vector((0.0, 0.0, 0.0))
        for i, p in enumerate(pts):
            q = pts[(i + 1) % len(pts)]
            n += Vector(((p.y - q.y) * (p.z + q.z), (p.z - q.z) * (p.x + q.x), (p.x - q.x) * (p.y + q.y)))
        return n.normalized() if n.length > 1e-12 else Vector((0.0, 0.0, 1.0))

    def center(self, fi):
        pts = [self.co[i] for i in self.faces[fi]]
        return sum(pts, Vector()) / len(pts)

    def recolor(self, fn, faces=None):
        for fi in faces if faces is not None else range(len(self.faces)):
            self.mats[fi] = fn(self.center(fi), self.normal(fi), self.mats[fi])

    def slice(self, levels, normal=(0.0, 0.0, 1.0)):
        """Cut every face along parallel planes at the given heights, so strata can be colored along clean lines."""
        bm = bmesh.new()
        shade = bm.verts.layers.float.new("shade")
        mat = bm.faces.layers.int.new("mat")
        var = bm.faces.layers.float.new("var")
        names = sorted(set(self.mats))
        verts = []
        for c, s in zip(self.co, self.shade):
            vert = bm.verts.new(c)
            vert[shade] = s
            verts.append(vert)
        for idx, m, fv in zip(self.faces, self.mats, self.fvar):
            face = bm.faces.new([verts[i] for i in idx])
            face[mat] = names.index(m)
            face[var] = fv
        for z in levels:
            geom = list(bm.verts) + list(bm.edges) + list(bm.faces)
            bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0.0, 0.0, z), plane_no=normal)
        bm.verts.index_update()
        self.co = [vert.co.copy() for vert in bm.verts]
        self.shade = [vert[shade] for vert in bm.verts]
        self.faces = [tuple(vert.index for vert in face.verts) for face in bm.faces]
        self.mats = [names[face[mat]] for face in bm.faces]
        self.fvar = [face[var] for face in bm.faces]
        bm.free()

    def merge(self, other):
        base = len(self.co)
        self.co += other.co
        self.shade += other.shade
        self.faces += [tuple(i + base for i in f) for f in other.faces]
        self.mats += other.mats
        self.fvar += other.fvar

    def bounds(self):
        return (
            Vector(min(c[i] for c in self.co) for i in range(3)),
            Vector(max(c[i] for c in self.co) for i in range(3)),
        )

    def to_base_center(self):
        lo, hi = self.bounds()
        offset = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
        self.co = [c - offset for c in self.co]

    def build(self, name, smooth_angle=None):
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata([tuple(c) for c in self.co], [], self.faces)
        slots = []
        for m in self.mats:
            if m not in slots:
                slots.append(m)
        # Godot 4.7's glTF importer never applies COLOR_0 to the first primitive's material, so the first
        # material slot is one whose faces carry no vertex variation: it then looks the same either way.
        flat = next((m for m in FLAT_FIRST if m in slots), None)
        if flat is not None:
            slots.remove(flat)
            slots.insert(0, flat)
        for m in slots:
            mesh.materials.append(material(m))
        mesh.polygons.foreach_set("material_index", [slots.index(m) for m in self.mats])
        colors = mesh.color_attributes.new("Color", "BYTE_COLOR", "CORNER")
        values = []
        for poly, var, m in zip(mesh.polygons, self.fvar, self.mats):
            for li in poly.loop_indices:
                s = 1.0 if m == flat else min(1.0, self.shade[mesh.loops[li].vertex_index] * var)
                values += (s, s, s, 1.0)
        colors.data.foreach_set("color", values)
        if smooth_angle is None:
            mesh.shade_flat()
        else:
            mesh.shade_smooth()
            mesh.set_sharp_from_angle(angle=math.radians(smooth_angle))
        if mesh.validate():
            raise RuntimeError(f"{name}: mesh needed repairs")
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.scene.collection.objects.link(obj)
        return obj


def shade_by_normal(top="rock_light", side="rock", under="shadow", up=0.6, down=-0.25):
    def fn(c, n, current):
        if n.z < down:
            return under
        if n.z > up:
            return top
        return side if current is None else current

    return fn


def frames(path):
    """Parallel-transport frames (tangent, normal, binormal) along a polyline."""
    tangents = []
    for i in range(len(path)):
        a = path[max(i - 1, 0)]
        b = path[min(i + 1, len(path) - 1)]
        tangents.append((b - a).normalized())
    t0 = tangents[0]
    helper = Vector((0, 0, 1)) if abs(t0.z) < 0.9 else Vector((1, 0, 0))
    n = t0.cross(helper).normalized()
    out = []
    for i, t in enumerate(tangents):
        if i:
            n = tangents[i - 1].rotation_difference(t) @ n
            n = (n - t * n.dot(t)).normalized()
        out.append((t, n, t.cross(n)))
    return out


def tube(g, path, radii, section, mat, shade_fn=None, tip=None, var=None):
    """Sweep a closed 2D section (list of (x, y) scale pairs) along path; optionally close the end at tip."""
    rings = []
    for p, r, (t, n, b) in zip(path, radii, frames(path)):
        ring = []
        for sx, sy, shade in section:
            q = p + (n * sx + b * sy) * r
            ring.append(g.v(q, shade_fn(q, shade) if shade_fn else shade))
        rings.append(ring)
    faces = []
    for a, b in zip(rings, rings[1:]):
        faces += g.band(a, b, mat, var)
    if tip is not None:
        apex = g.v(tip, shade_fn(tip, 1.0) if shade_fn else 1.0)
        faces += g.fan(rings[-1], apex, mat, var)
    return faces


# ---------------------------------------------------------------- rock formations


def outline(rng, n, a, b, rough=0.12, bumps=5):
    """An irregular closed outline around the origin: harmonics, a few buttresses and bays, and jitter."""
    phases = [rng.uniform(0, TAU) for _ in range(4)]
    amps = [rough * 0.9, rough * 0.6, rough * 0.35, rough * 0.25]
    features = [(rng.uniform(0, TAU), rng.uniform(0.15, 0.35), rng.uniform(-0.2, 0.14)) for _ in range(bumps)]
    pts = []
    for i in range(n):
        th = TAU * i / n
        r = 1 + sum(amp * math.sin((k + 2) * th + ph) for k, (amp, ph) in enumerate(zip(amps, phases)))
        for center, width, amp in features:
            dist = (th - center + math.pi) % TAU - math.pi
            r += amp * math.exp(-((dist / width) ** 2))
        r += rng.uniform(-rough * 0.3, rough * 0.3)
        pts.append(Vector((a * r * math.cos(th), b * r * math.sin(th))))
    return pts


def mesa_body(g, rng, cx, a, b, n, z0, apron_scale, apron_h, bands, apron_mat="sand", caprock=0.0):
    """Layered sandstone: a talus apron, fluted cliff bands split by recessed strata grooves, a cap.
    Returns the height of the cap's rim."""
    pts = outline(rng, n, a, b)
    flute = [rng.uniform(-1.0, 1.0) * 0.12 * min(a, b) for _ in range(n)]
    groove_depth = 0.06 * min(a, b) + 0.15
    groove_h = 0.3 + 0.06 * min(a, b)
    height_guess = apron_h + sum(bands) + groove_h * len(bands)

    def ring(z, scale=1.0, inset=0.0, jitter=0.1, fluted=True):
        idx = []
        for i, p in enumerate(pts):
            d = p.normalized()
            q = p * scale - d * (inset + (flute[i] if fluted else 0.0))
            q += Vector((rng.uniform(-jitter, jitter), rng.uniform(-jitter, jitter)))
            shade = 0.84 + 0.16 * min(1.0, (z - z0) / height_guess)
            idx.append(g.v((cx + q.x, q.y, z), shade))
        return idx

    foot = ring(z0, apron_scale, jitter=0.06 * min(a, b), fluted=False)
    knee = ring(z0 + apron_h * 0.4, 1 + (apron_scale - 1) * 0.4, jitter=0.04 * min(a, b), fluted=False)
    g.band(foot, knee, apron_mat)
    z = z0 + apron_h
    inset = 0.0
    prev = ring(z, 1.0, inset)
    for fi in g.band(knee, prev, "rock_light"):  # scree
        g.mats[fi] = rng.choice(["rock_light", "sand_deep", "rock_light"])
    choices = ["rock", "rock_light", "rock", "rock_dark"]
    last_mat = "rock_light"
    for k, h in enumerate(bands):
        mat = rng.choice([m for m in choices if m != last_mat])
        last_mat = mat
        top_inset = inset + 0.2 + rng.uniform(-0.1, 0.4)
        if k == len(bands) - 1 and caprock:
            top_inset = inset - caprock
            bottom = ring(z, 1.0, top_inset)
            g.band(prev, bottom, "shadow")  # soffit under the overhanging cap rock
            prev = bottom
        top = ring(z + h, 1.0, top_inset)
        g.band(prev, top, mat)
        z += h
        inset = top_inset
        if k < len(bands) - 1:
            ledge = ring(z, 1.0, inset + groove_depth, jitter=0.05)
            g.band(top, ledge, "rock_light")
            recess = ring(z + groove_h, 1.0, inset + groove_depth, jitter=0.05)
            g.band(ledge, recess, "shadow")
            nxt_inset = inset + rng.uniform(-0.1, 0.25)
            back = ring(z + groove_h, 1.0, nxt_inset, jitter=0.05)
            g.band(recess, back, "shadow")
            z += groove_h
            inset = nxt_inset
            prev = back
        else:
            prev = top
    lip = ring(z, 1.0, inset + groove_depth * 0.8, jitter=0.05)
    g.band(prev, lip, "rock_light")
    inner = ring(z + rng.uniform(0.05, 0.2), 0.55, jitter=0.2, fluted=False)
    g.band(lip, inner, "rock_light")
    apex = g.v((cx + rng.uniform(-0.5, 0.5), rng.uniform(-0.3, 0.3), z + 0.15), 1.0)
    g.fan(inner, apex, "rock_light")
    return z


def mesa_large(rng):
    g = Geo(rng)
    top = mesa_body(g, rng, 0.0, 13.0, 6.0, 48, 0.0, 1.35, 3.0, [2.2, 1.6, 2.6, 1.8])
    mesa_body(g, rng, 3.0, 5.2, 3.2, 32, top - 0.25, 1.35, 1.6, [2.6, 2.2], apron_mat="rock_light", caprock=0.4)
    g.recolor(lambda c, n, m: "shadow" if n.z < -0.3 else m)
    g.to_base_center()
    return [g.build("mesa-large")]


def mesa_small(rng):
    """A butte: taller than its cap is wide, with an overhanging cap rock."""
    g = Geo(rng)
    mesa_body(g, rng, 0.0, 3.8, 3.0, 30, 0.0, 1.5, 2.0, [1.6, 1.4, 1.8, 1.3], caprock=0.5)
    g.recolor(lambda c, n, m: "shadow" if n.z < -0.3 else m)
    g.to_base_center()
    return [g.build("mesa-small")]


def arch(rng):
    """A wind-cut arch on a slickrock base, its strata cut along slightly dipping planes."""
    g = Geo(rng)
    base_top = mesa_body(g, rng, 0.0, 9.5, 4.6, 32, 0.0, 1.25, 1.0, [1.4])
    span = Geo(rng)
    rx, rz, zb = 5.8, 9.0, base_top - 1.2
    samples, sides = 36, 12
    profile = [rng.uniform(0.82, 1.12) for _ in range(sides)]
    wobble = [rng.uniform(0, TAU) for _ in range(3)]
    rings = []
    for s in range(samples + 1):
        t = s / samples
        phi = math.pi * (1 - t)
        p = Vector((rx * math.cos(phi), 0.35 * math.sin(3 * t + wobble[0]), zb + rz * math.sin(phi)))
        tangent = Vector((rx * math.sin(phi), 0.0, -rz * math.cos(phi))).normalized()
        normal = Vector((tangent.z, 0.0, -tangent.x))
        binormal = Vector((0.0, 1.0, 0.0))
        u = abs(2 * t - 1)
        w_leg = 5.2 if t < 0.5 else 4.2
        w = (2.4 + (w_leg - 2.4) * u**2.6) * (1 + 0.08 * math.sin(7 * t + wobble[1]))
        d = (3.4 + 2.4 * u**1.6) * (1 + 0.08 * math.sin(5 * t + wobble[2]))
        ring = []
        for k in range(sides):
            al = TAU * k / sides
            r = profile[k] * rng.uniform(0.93, 1.07)
            q = p + normal * (math.cos(al) * w / 2 * r) + binormal * (math.sin(al) * d / 2 * r)
            ring.append(span.v(q, 0.84 + 0.16 * min(1.0, q.z / 12)))
        rings.append(ring)
    for a, b in zip(rings, rings[1:]):
        for k, fi in enumerate(span.band(a, b, "rock")):
            # the section's normal axis points into the opening: its inner rim is the recess
            inner = math.cos(TAU * (k + 0.5) / sides)
            span.mats[fi] = "shadow" if inner > 0.6 else "rock_dark" if inner > 0.2 else "rock"
    dip = Vector((0.04, 0.02, 1.0)).normalized()
    levels, z = [], zb + 0.8
    while z < zb + rz + 2.0:
        levels.append(z)
        z += rng.uniform(0.9, 1.7)
    span.slice(levels, dip)
    strata = ["rock", "rock_light", "rock", "rock_dark", "rock_light", "rock_light", "rock"]

    def color(c, n, m):
        if m != "rock" or n.z < -0.3:
            return "shadow" if n.z < -0.3 else m
        band = sum(1 for level in levels if (c - Vector((0.0, 0.0, level))).dot(dip) > 0)
        return strata[band % len(strata)]

    span.recolor(color)
    g.merge(span)
    g.recolor(lambda c, n, m: "shadow" if n.z < -0.3 else m)
    g.to_base_center()
    return [g.build("arch")]


def boulder_a(rng):
    g = Geo(rng)
    pts = []
    for _ in range(48):
        th, u = rng.uniform(0, TAU), rng.uniform(-1, 1)
        s = math.sqrt(1 - u * u)
        r = rng.uniform(0.72, 1.1)
        pts.append(Vector((1.3 * r * s * math.cos(th), 1.0 * r * s * math.sin(th), 0.75 + 0.95 * r * u)))
    pts = [Vector((p.x, p.y, max(p.z, 0.0))) for p in pts]
    faces = g.hull(pts, None, shade_fn=lambda p: 0.82 + 0.18 * min(1.0, p.z / 1.6))
    g.recolor(shade_by_normal(down=-0.45), faces)
    g.to_base_center()
    return [g.build("boulder-a")]


def boulder_b(rng):
    """A tabular sandstone slab with chipped edges, tipped up on a smaller rock."""
    g = Geo(rng)
    half, chamfer = Vector((1.15, 0.7, 0.42)), 0.2
    pts = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            for sz in (-1, 1):
                corner = Vector((sx * half.x, sy * half.y, sz * half.z))
                for axis in range(3):
                    p = corner.copy()
                    p[axis] -= (sx, sy, sz)[axis] * chamfer * rng.uniform(0.4, 2.2)
                    p.z *= 1 + 0.3 * p.x / half.x  # a wedge, thicker at the grounded end
                    pts.append(p + Vector([rng.uniform(-0.09, 0.09) for _ in range(3)]))
    tilt = Matrix.Rotation(math.radians(20), 4, "Y") @ Matrix.Rotation(math.radians(6), 4, "X")
    pts = [tilt @ p for p in pts]
    low = min(p.z for p in pts)
    pts = [p - Vector((0.0, 0.0, low)) for p in pts]
    slab = g.hull(pts, "rock", shade_fn=lambda p: 0.82 + 0.18 * min(1.0, p.z / 1.8))
    g.recolor(shade_by_normal(down=-0.45), slab)
    support = []
    for _ in range(14):
        th = rng.uniform(0, TAU)
        support.append(Vector((-0.75 + 0.42 * math.cos(th), 0.1 + 0.36 * math.sin(th), rng.uniform(0.0, 0.72))))
    g.recolor(shade_by_normal(side="rock_dark", down=-0.45), g.hull(support, "rock_dark"))
    g.to_base_center()
    return [g.build("boulder-b")]


# ---------------------------------------------------------------- vegetation silhouettes (shadow violet, no green)


def rib_section(sides=16, groove=0.8):
    return [
        (math.cos(TAU * k / sides) * (1.0 if k % 2 == 0 else groove),
         math.sin(TAU * k / sides) * (1.0 if k % 2 == 0 else groove),
         1.0 if k % 2 == 0 else 0.8)
        for k in range(sides)
    ]


def domed(path_end, direction, radius, steps=4):
    """Points and radii that round off a tube end."""
    pts, radii = [], []
    for i in range(1, steps + 1):
        a = (math.pi / 2) * i / (steps + 1)
        pts.append(path_end + direction * radius * math.sin(a))
        radii.append(radius * math.cos(a))
    return pts, radii, path_end + direction * radius


def saguaro(rng):
    g = Geo(rng)
    section = rib_section()
    height, r = 5.0, 0.36

    def shade(q, s):
        return s * (0.8 + 0.2 * min(1.0, q.z / height))

    path = [Vector((0.02 * math.sin(i), 0.0, height * i / 10 - 0.05)) for i in range(11)]
    radii = [r * (1.0 + 0.06 * math.sin(i * 0.9)) for i in range(11)]
    dome_pts, dome_r, tip = domed(path[-1], Vector((0, 0, 1)), r)
    tube(g, path + dome_pts, radii + dome_r, section, "shadow", shade, tip=tip)
    arms = [(0.05, 2.1, 1.7, 0.55), (math.pi - 0.1, 2.7, 1.3, 0.5), (math.pi * 0.62, 1.7, 0.9, 0.45)]
    for angle, h0, rise, reach in arms:
        out = Vector((math.cos(angle), math.sin(angle) * 0.6, 0.0)).normalized()
        up = Vector((0, 0, 1))
        start = Vector((0, 0, h0))
        pts = [start, start + out * reach * 0.6 + up * 0.05]
        elbow = pts[-1]
        bend = 0.32
        for i in range(1, 6):
            be = (math.pi / 2) * i / 5
            pts.append(elbow + out * bend * math.sin(be) + up * bend * (1 - math.cos(be)))
        top = pts[-1]
        for i in range(1, 4):
            pts.append(top + up * rise * i / 3 + out * 0.03 * i)
        ar = 0.25 + rng.uniform(-0.02, 0.02)
        dome_pts, dome_r, tip = domed(pts[-1], (pts[-1] - pts[-2]).normalized(), ar)
        tube(g, pts + dome_pts, [ar] * len(pts) + dome_r, section, "shadow", shade, tip=tip)
    g.to_base_center()
    return [g.build("saguaro")]


def acacia(rng):
    g = Geo(rng)
    round8 = [(math.cos(TAU * k / 7), math.sin(TAU * k / 7), 1.0) for k in range(7)]

    def shade(q, s):
        return 0.78 + 0.22 * min(1.0, q.z / 4.5)

    def limb(a, ctrl, b, r0, r1, steps=6):
        pts = []
        for i in range(steps + 1):
            t = i / steps
            pts.append(a * (1 - t) ** 2 + ctrl * 2 * t * (1 - t) + b * t * t)
        tube(g, pts, [r0 + (r1 - r0) * i / steps for i in range(steps + 1)], round8, "shadow", shade,
             tip=pts[-1] + (pts[-1] - pts[-2]).normalized() * r1)

    base, fork = Vector((0, 0, -0.05)), Vector((0.15, 0.0, 1.55))
    limb(base, Vector((-0.05, 0.0, 0.8)), fork, 0.2, 0.15)
    tips = [Vector((-1.9, 0.25, 3.45)), Vector((1.75, -0.2, 3.55)), Vector((0.35, 0.55, 3.75)), Vector((-0.6, -0.4, 3.5))]
    for tip in tips:
        ctrl = fork + (tip - fork) * 0.5 + Vector((0, 0, -0.35))
        limb(fork, ctrl, tip, 0.13, 0.06)
    limb(Vector((-1.0, 0.1, 2.6)), Vector((-1.9, 0.0, 2.9)), Vector((-2.6, 0.0, 3.35)), 0.07, 0.04, 4)
    blobs = [(-1.6, 0.15, 3.75, 1.8), (1.4, -0.1, 3.85, 1.7), (0.1, 0.3, 4.0, 1.6), (-0.2, -0.4, 3.7, 1.4),
             (-2.8, 0.05, 3.6, 1.0), (2.7, 0.1, 3.7, 0.95)]
    for x, y, z, r in blobs:  # a flat-topped, layered umbrella canopy
        pts = []
        for _ in range(22):
            th = rng.uniform(0, TAU)
            rr = r * math.sqrt(rng.uniform(0.3, 1.0))
            zz = z + rng.uniform(-0.5, 0.25) * (1.1 - 0.6 * rr / r)
            pts.append(Vector((x + rr * math.cos(th), y + rr * 0.8 * math.sin(th), min(zz, z + 0.22))))
        g.hull(pts, "shadow", shade_fn=lambda p, z=z: 0.72 if p.z < z - 0.1 else 1.0)
    g.to_base_center()
    return [g.build("acacia")]


# ---------------------------------------------------------------- dune


def dune_ridge(rng):
    g = Geo(rng)
    half_w, front_d, back_d = 20.0, 7.0, 8.0
    cols, rows_front, rows_back = 44, 12, 7
    ph = [rng.uniform(0, TAU) for _ in range(5)]
    grid = []
    for i in range(cols + 1):
        x = -half_w + 2 * half_w * i / cols
        env = max(0.0, 1 - (x / half_w) ** 2) ** 0.7
        yc = 1.6 * math.sin(0.16 * x + ph[0]) + 0.7 * math.sin(0.41 * x + ph[1])
        h = 5.6 * env * (0.72 + 0.28 * math.sin(0.23 * x + ph[2]))
        col = []
        for j in range(rows_front + rows_back + 1):
            if j <= rows_front:  # windward: a long rise that steepens up to the sharp crest
                s = j / rows_front
                y = -front_d + (yc + front_d) * s
                z = h * s**1.5
                ripple = 0.5 + 0.5 * math.sin(2.4 * (y + 0.25 * math.sin(0.3 * x + ph[4])))
                shade = 0.88 + 0.12 * ripple
            else:  # lee: the slip face falls away steeply behind the crest
                s = (j - rows_front) / rows_back
                y = yc + (back_d - yc) * s
                z = h * max(0.0, 1 - s / 0.85) ** 1.25
                shade = 0.95
            z += 0.08 * math.sin(0.9 * x + 1.7 * y + ph[3]) * env
            col.append(g.v((x, y, max(z, 0.0)), shade))
        grid.append(col)
    for i in range(cols):
        for j in range(rows_front + rows_back):
            quad = (grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1])
            slip_face = rows_front <= j < rows_front + round(rows_back * 0.85) and max(g.co[v].z for v in quad) > 0.05
            g.f(quad, "sand_shade" if slip_face else "sand", 1.0)
    g.to_base_center()
    return [g.build("dune-ridge", smooth_angle=35)]


# ---------------------------------------------------------------- ruins


def ruin_column(rng):
    g = Geo(rng)
    g.box((-0.55, -0.55, 0.0), (0.55, 0.55, 0.28), "stone", jitter=0.02)
    g.box((-0.47, -0.47, 0.28), (0.47, 0.47, 0.4), "rock_light", jitter=0.015)
    sides = 20
    flutes = [(math.cos(TAU * k / sides) * (1.0 if k % 2 == 0 else 0.9),
               math.sin(TAU * k / sides) * (1.0 if k % 2 == 0 else 0.9),
               1.0 if k % 2 == 0 else 0.78) for k in range(sides)]
    z = 0.4
    drums = [0.75, 0.72, 0.78, 0.7]
    radius = 0.38
    for d, h in enumerate(drums):
        cx, cy = 0.03 * d + rng.uniform(-0.02, 0.02), rng.uniform(-0.02, 0.02)  # the stack leans a little
        rot = rng.uniform(-0.15, 0.15)
        r = radius * (1 - 0.03 * d)

        def loop(zz, scale=1.0, broken=None):
            idx = []
            for k, (sx, sy, shade) in enumerate(flutes):
                c, s = math.cos(rot), math.sin(rot)
                x, y = (sx * c - sy * s) * r * scale, (sx * s + sy * c) * r * scale
                top = zz if broken is None else broken[k]
                idx.append(g.v((cx + x, cy + y, top), shade))
            return idx

        joint_lo = loop(z, 0.86)
        bottom = loop(z + 0.03)
        g.band(joint_lo, bottom, "shadow", 1.0)
        if d == len(drums) - 1:
            peaks = [z + h * (0.45 + 0.55 * abs(math.sin(k * 0.7 + rng.uniform(-0.4, 0.4)))) for k in range(sides)]
            top = loop(None, 1.0, peaks)
            g.band(bottom, top, "stone")
            dip = g.v((cx, cy, min(peaks) - 0.12), 0.8)
            g.fan(top, dip, "rock_light")
        else:
            top = loop(z + h)
            g.band(bottom, top, "stone")
            cap = g.v((cx, cy, z + h), 1.0)
            g.fan(loop(z + h, 0.86), cap, "shadow", 1.0)
            g.band(top, loop(z + h, 0.86), "shadow", 1.0)
        z += h
    # a fallen fragment of the missing drum against the plinth
    chunk = []
    for _ in range(12):
        chunk.append(Vector((0.75 + rng.uniform(-0.28, 0.28), -0.35 + rng.uniform(-0.2, 0.2), rng.uniform(0.0, 0.32))))
    g.recolor(shade_by_normal(top="rock_light", side="stone"), g.hull(chunk, "stone"))
    g.to_base_center()
    return [g.build("ruin-column")]


def ruin_wall(rng):
    g = Geo(rng)
    length, course_h, depth = 5.0, 0.46, 0.7
    profile = [(-2.5, 6), (-1.8, 6), (-1.0, 5), (-0.3, 5), (0.4, 4), (1.0, 3), (1.6, 2), (2.1, 1), (2.5, 1)]

    def courses_at(x):
        for (x0, n), (x1, _) in zip(profile, profile[1:]):
            if x0 <= x < x1:
                return n
        return 1

    window = (-1.55, -0.85, 2, 3)  # x range and course range of a window opening
    lintel = (window[0] - 0.2, window[1] + 0.2, window[3] + 1)
    for c in range(6):
        z0 = c * course_h
        edges = [-length / 2]
        x = -length / 2 + (0.0 if c % 2 == 0 else -0.45)
        while x < length / 2:
            x += rng.uniform(0.75, 1.15)
            edges.append(min(x, length / 2))
        if c == lintel[2]:
            edges = sorted([e for e in edges if not lintel[0] - 0.1 < e < lintel[1] + 0.1] + [lintel[0], lintel[1]])
        runs = []
        for x0, x1 in zip(edges, edges[1:]):
            mid = (x0 + x1) / 2
            is_lintel = c == lintel[2] and x0 == lintel[0]
            in_window = window[0] < mid < window[1] and window[2] <= c <= window[3]
            present = is_lintel or (c < courses_at(mid) and not in_window)
            if present and not is_lintel and c == courses_at(mid) - 1 and rng.random() < 0.25 and c > 0:
                present = False
            if present and x1 - x0 > 0.08:
                push = rng.uniform(-0.03, 0.04)
                mat = "rock_light" if is_lintel else rng.choices(["stone", "rock_light", "rock"], [6, 3, 1])[0]
                g.box((x0 + 0.02, -depth / 2 - push, z0 + 0.015), (x1 - 0.02, depth / 2 - push, z0 + course_h - 0.015),
                      mat, jitter=0.015)
                if runs and runs[-1][1] == x0:
                    runs[-1][1] = x1
                else:
                    runs.append([x0, x1])
        for x0, x1 in runs:  # mortar core behind each run of blocks, seen through the joints
            g.box((x0 + 0.04, -depth / 2 + 0.07, max(z0 - 0.045, 0.0)), (x1 - 0.04, depth / 2 - 0.07, z0 + course_h - 0.045),
                  "shadow", 1.0)
    for bx, by, ang in [(1.6, -1.0, 0.5), (2.35, -0.8, -0.3), (-2.1, -0.95, 1.2)]:
        m = Matrix.Translation((bx, by, 0.0)) @ Matrix.Rotation(ang, 4, "Z") @ Matrix.Rotation(rng.uniform(-0.2, 0.2), 4, "X")
        g.box((-0.42, -0.34, 0.0), (0.42, 0.34, course_h - 0.03), "stone", transform=m, jitter=0.02)
    g.recolor(lambda c, n, m: "shadow" if n.z < -0.5 and m != "shadow" else m)
    g.to_base_center()
    return [g.build("ruin-wall")]


# ---------------------------------------------------------------- 1 m cells


def cell_block(g, top_height, bands, top_mat, top_shade, n=8):
    """A 1x1x1 m block, x and y in [-0.5, 0.5], z from 0 to top_height(x, y) (periodic, so neighbours meet).
    bands: [(boundary(x, y), material below it), ...] upward; the last material runs up to the top."""
    step = 1.0 / n
    top = [[g.v((-0.5 + i * step, -0.5 + j * step, top_height(-0.5 + i * step, -0.5 + j * step)),
                top_shade(-0.5 + i * step, -0.5 + j * step)) for j in range(n + 1)] for i in range(n + 1)]
    for i in range(n):
        for j in range(n):
            g.f((top[i][j], top[i + 1][j], top[i + 1][j + 1], top[i][j + 1]), top_mat, 1.0)
    perimeter = ([(-0.5 + i * step, -0.5) for i in range(n)] + [(0.5, -0.5 + j * step) for j in range(n)]
                 + [(0.5 - i * step, 0.5) for i in range(n)] + [(-0.5, 0.5 - j * step) for j in range(n)])
    perimeter.append(perimeter[0])
    columns = []
    for x, y in perimeter:
        zs = [0.0] + [boundary(x, y) for boundary, _ in bands[1:]] + [top_height(x, y)]
        columns.append([g.v((x, y, z)) for z in zs])
    mats = [m for _, m in bands]
    for a, b in zip(columns, columns[1:]):
        for k in range(len(mats)):
            g.f((a[k], b[k], b[k + 1], a[k + 1]), mats[k], 1.0)
    bottom = [g.v(p) for p in ((-0.5, -0.5, 0), (-0.5, 0.5, 0), (0.5, 0.5, 0), (0.5, -0.5, 0))]
    g.f(bottom, bands[0][1], 1.0)


def wave(base, amp, px, py, phx=0.0, phy=0.0):
    return lambda x, y: base + amp * math.sin(TAU * px * x + phx) + amp * 0.6 * math.sin(TAU * py * y + phy)


def sand_tile(rng):
    g = Geo(rng)

    def ripple(x, y):
        return 0.5 + 0.5 * math.sin(TAU * (2 * x + 0.18 * math.sin(TAU * y)))

    cell_block(
        g,
        top_height=lambda x, y: 1.0 + 0.022 * ripple(x, y),
        bands=[(None, "sand_deep"), (wave(0.3, 0.03, 1, 1, 0.4, 1.0), "sand"),
               (wave(0.62, 0.035, 1, 1, 2.1, 0.3), "sand_deep"), (wave(0.7, 0.03, 1, 1, 2.3, 0.5), "sand")],
        top_mat="sand",
        top_shade=lambda x, y: 0.93 + 0.07 * ripple(x, y),
    )
    return [g.build("sand-tile")]


def rock_tile(rng):
    g = Geo(rng)

    def bumps(x, y):
        return 0.5 + 0.25 * math.sin(TAU * x + 0.8) * math.sin(TAU * y + 2.0) + 0.25 * math.sin(TAU * 2 * (x + y) + 0.3)

    cell_block(
        g,
        top_height=lambda x, y: 1.0 + 0.035 * bumps(x, y),
        bands=[(None, "rock_dark"), (wave(0.22, 0.03, 1, 1, 0.2, 1.4), "rock"),
               (wave(0.5, 0.035, 1, 1, 1.9, 0.6), "shadow"), (wave(0.54, 0.035, 1, 1, 1.9, 0.6), "rock_light"),
               (wave(0.78, 0.025, 1, 1, 3.0, 2.2), "rock"), (wave(0.9, 0.02, 1, 1, 0.9, 0.1), "shadow"),
               (wave(0.93, 0.02, 1, 1, 0.9, 0.1), "rock_light")],
        top_mat="rock_light",
        top_shade=lambda x, y: 0.9 + 0.1 * bumps(x, y),
        n=6,
    )
    return [g.build("rock-tile")]


def tag_block(rng):
    """A solid 1 m block of cut stone that fills its cell: flat faces flush with the cell, a slight chamfer on
    every edge, and a few corners chipped deeper as chisel facets. Untinted, so lanes tint it with the tag color."""
    g = Geo(rng)
    pts = []
    for axis in range(3):  # each face's four corners, pulled in from the edges by the chamfer
        u, v = (a for a in range(3) if a != axis)
        for side in (-1, 1):
            for su in (-1, 1):
                for sv in (-1, 1):
                    p = Vector((0.0, 0.0, 0.0))
                    p[axis] = 0.5 * side
                    p[u] = su * (0.5 - rng.uniform(0.04, 0.055))
                    p[v] = sv * (0.5 - rng.uniform(0.04, 0.055))
                    pts.append(p)
    for i in rng.sample(range(len(pts)), 4):  # chisel facets: a few corners chipped deeper
        axis = rng.choice([a for a in range(3) if abs(abs(pts[i][a]) - 0.5) > 1e-9])
        pts[i][axis] = math.copysign(0.5 - rng.uniform(0.13, 0.19), pts[i][axis])
    g.hull([p + Vector((0.0, 0.0, 0.5)) for p in pts], "tag", shade_fn=lambda p: 0.9 + 0.1 * p.z, flat_faces=True)
    return [g.build("tag-block")]


def orb_pedestal(rng):
    g = Geo(rng)
    g.box((-0.34, -0.34, 0.0), (0.34, 0.34, 0.1), "stone", jitter=0.008)
    g.box((-0.27, -0.27, 0.1), (0.27, 0.27, 0.17), "rock_light", jitter=0.006)
    sides = 8

    def loop(z, r, shade=1.0):
        return [g.v((r * math.cos(TAU * (k + 0.5) / sides), r * math.sin(TAU * (k + 0.5) / sides), z), shade)
                for k in range(sides)]

    rings = [loop(0.17, 0.17, 0.85), loop(0.36, 0.14, 0.92), loop(0.36, 0.125), loop(0.41, 0.125), loop(0.41, 0.14),
             loop(0.55, 0.15), loop(0.63, 0.26), loop(0.67, 0.26), loop(0.67, 0.2)]
    mats = ["stone", "shadow", "shadow", "shadow", "stone", "stone", "rock_light", "rock_light"]
    for (a, b), m in zip(zip(rings, rings[1:]), mats):
        g.band(a, b, m)
    g.fan(rings[-1], g.v((0.0, 0.0, 0.62), 0.8), "shadow")
    g.recolor(lambda c, n, m: "shadow" if n.z < -0.5 and c.z > 0.3 else m)
    pedestal = g.build("orb-pedestal")
    orb_geo = Geo(rng)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.14)
    remap = {}
    for face in bm.faces:
        idx = []
        for vert in face.verts:
            if vert.index not in remap:
                remap[vert.index] = orb_geo.v(vert.co, 0.85 + 0.15 * (vert.co.z / 0.28 + 0.5))
            idx.append(remap[vert.index])
        orb_geo.f(idx, "orb", rng.uniform(0.95, 1.0))
    bm.free()
    orb = orb_geo.build("orb")
    orb.parent = pedestal
    orb.location = (0.0, 0.0, 0.82)
    return [pedestal, orb]


def hazard_spikes(rng):
    g = Geo(rng)
    plate = [Vector((0.47 * math.cos(TAU * (k + 0.5) / 8), 0.47 * math.sin(TAU * (k + 0.5) / 8))) for k in range(8)]
    lo = [g.v((p.x * rng.uniform(0.94, 1.0), p.y * rng.uniform(0.94, 1.0), 0.0), 0.8) for p in plate]
    hi = [g.v((p.x * 0.88, p.y * 0.88, rng.uniform(0.07, 0.11)), 0.9) for p in plate]
    g.band(lo, hi, "rock_dark")
    g.fan(hi, g.v((0.0, 0.0, 0.1), 0.85), "shadow")
    spots = []
    for gx in (-1, 0, 1):
        for gy in (-1, 0, 1):
            spots.append((gx * 0.29 + rng.uniform(-0.05, 0.05), gy * 0.27 + rng.uniform(-0.05, 0.05), abs(gx) + abs(gy)))
    for x, y, ring_no in spots:
        h = {0: 0.95, 1: 0.72, 2: 0.52}[ring_no] * rng.uniform(0.88, 1.0)
        r = {0: 0.16, 1: 0.125, 2: 0.1}[ring_no]
        lean = Vector((x, y)) * 0.35 + Vector((rng.uniform(-0.05, 0.05), rng.uniform(-0.05, 0.05)))
        sides = 5
        base_ring, mid_ring = [], []
        twist = rng.uniform(0, TAU)
        for k in range(sides):
            a = TAU * k / sides + twist
            rr = r * rng.uniform(0.8, 1.15)
            base_ring.append(g.v((x + rr * math.cos(a), y + rr * math.sin(a), 0.05), 0.8))
            kink = Vector((rng.uniform(-0.02, 0.02), rng.uniform(-0.02, 0.02)))
            mz = h * rng.uniform(0.38, 0.5)
            mid_ring.append(g.v((x + lean.x * 0.45 + kink.x + rr * 0.55 * math.cos(a),
                                 y + lean.y * 0.45 + kink.y + rr * 0.55 * math.sin(a), mz), 0.92))
        g.band(base_ring, mid_ring, "shadow")
        g.fan(mid_ring, g.v((x + lean.x, y + lean.y, h), 1.0), "rock")
    sun = Vector((0.45, -0.55, 0.7)).normalized()
    g.recolor(lambda c, n, m: ("rock" if n.dot(sun) > -0.3 else "shadow") if m == "rock" else m)
    return [g.build("hazard-spikes")]


def goal_gate(rng):
    g = Geo(rng)
    g.box((-0.5, -0.24, 0.0), (0.5, 0.24, 0.07), "rock_light")
    for side in (-1, 1):
        x0, x1 = sorted((side * 0.26, side * 0.5))
        g.box((x0, -0.2, 0.07), (x1, 0.2, 0.3), "stone")
        z = 0.3
        for k, h in enumerate((0.48, 0.52, 0.46, 0.44)):
            g.box((x0 + 0.03, -0.16, z), (x1 - 0.03, 0.16, z + 0.025), "shadow", 1.0)
            g.box((x0 + 0.015, -0.18, z + 0.025), (x1 - 0.015, 0.18, z + h), "stone" if k % 2 == 0 else "rock_light",
                  jitter=0.006)
            z += h
        g.box((x0, -0.21, z), (x1, 0.21, z + 0.1), "rock_light")
    top = 0.3 + 0.48 + 0.52 + 0.46 + 0.44 + 0.1
    g.box((-0.5, -0.22, top), (0.5, 0.22, top + 0.24), "stone")
    g.box((-0.44, -0.18, top + 0.24), (0.44, 0.18, top + 0.3), "rock_light", jitter=0.004)
    # sun-disc emblem on the lintel, glowing like the portal
    sides = 10
    cz = top + 0.46
    ring_o = [g.v((0.2 * math.cos(TAU * k / sides), -0.05, cz + 0.2 * math.sin(TAU * k / sides))) for k in range(sides)]
    ring_b = [g.v((0.2 * math.cos(TAU * k / sides), 0.05, cz + 0.2 * math.sin(TAU * k / sides))) for k in range(sides)]
    g.band(list(reversed(ring_o)), list(reversed(ring_b)), "stone")
    g.fan(ring_o, g.v((0.0, -0.05, cz)), "stone")
    g.fan(list(reversed(ring_b)), g.v((0.0, 0.05, cz)), "stone")
    inner = [g.v((0.13 * math.cos(TAU * k / sides), -0.07, cz + 0.13 * math.sin(TAU * k / sides))) for k in range(sides)]
    g.fan(inner, g.v((0.0, -0.075, cz)), "portal", 1.0)
    # the portal: a pointed-arch panel of light between the pillars
    shape = [(-0.26, 0.07), (0.26, 0.07), (0.26, 1.6)]
    for k in range(1, 7):
        a = math.pi / 2 * k / 7
        shape.append((0.26 - 0.26 * (1 - math.cos(a)), 1.6 + 0.5 * math.sin(a)))
    shape.append((0.0, 2.2))
    shape += [(-x, z) for x, z in reversed(shape[3:-1])]
    shape.append((-0.26, 1.6))
    front = [g.v((x, -0.02, z)) for x, z in shape]
    back = [g.v((x, 0.02, z)) for x, z in shape]
    g.fan(front, g.v((0.0, -0.02, 1.1)), "portal", 1.0)
    g.fan(list(reversed(back)), g.v((0.0, 0.02, 1.1)), "portal", 1.0)
    g.band(list(reversed(front)), list(reversed(back)), "portal", 1.0)
    return [g.build("goal-gate")]


# ---------------------------------------------------------------- driver

PIECES = {
    "mesa-large": (mesa_large, None),
    "mesa-small": (mesa_small, None),
    "arch": (arch, None),
    "boulder-a": (boulder_a, None),
    "boulder-b": (boulder_b, None),
    "saguaro": (saguaro, None),
    "acacia": (acacia, None),
    "dune-ridge": (dune_ridge, None),
    "ruin-column": (ruin_column, None),
    "ruin-wall": (ruin_wall, None),
    # cell pieces: (half footprint, max height) that the 1 m grid needs
    "sand-tile": (sand_tile, (0.5, 1.03)),
    "rock-tile": (rock_tile, (0.5, 1.04)),
    "tag-block": (tag_block, (0.5, 1.0)),
    "orb-pedestal": (orb_pedestal, (0.5, 1.0)),
    "goal-gate": (goal_gate, (0.5, 3.0)),
    "hazard-spikes": (hazard_spikes, (0.5, 1.0)),
}


def world_bounds(objects):
    corners = [obj.matrix_world @ v.co for obj in objects for v in obj.data.vertices]
    return (Vector(min(c[i] for c in corners) for i in range(3)), Vector(max(c[i] for c in corners) for i in range(3)))


def main():
    out_dir = Path(sys.argv[sys.argv.index("--") + 1])
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"{'piece':16} {'tris':>5}  width x depth x height (m)")
    for name, (build, cell) in PIECES.items():
        bpy.ops.wm.read_factory_settings(use_empty=True)
        rng = random.Random(SEED * 1_000_003 + zlib.crc32(name.encode()))
        objects = build(rng)
        bpy.context.view_layer.update()
        tris = 0
        for obj in objects:
            obj.data.calc_loop_triangles()
            tris += len(obj.data.loop_triangles)
        lo, hi = world_bounds(objects)
        if tris > MAX_TRIANGLES:
            raise RuntimeError(f"{name}: {tris} triangles > {MAX_TRIANGLES}")
        if abs(lo.z) > 1e-6:
            raise RuntimeError(f"{name}: base at z={lo.z:.4f}, not 0")
        if cell is not None:
            half, max_h = cell
            if max(abs(lo.x), abs(lo.y), hi.x, hi.y) > half + 1e-6 or hi.z > max_h + 1e-6:
                raise RuntimeError(f"{name}: bounds {tuple(lo)}..{tuple(hi)} exceed its 1 m cell")
        size = hi - lo
        print(f"{name:16} {tris:5}  {size.x:.2f} x {size.y:.2f} x {size.z:.2f}")
        bpy.ops.export_scene.gltf(
            filepath=str(out_dir / f"{name}.glb"),
            export_format="GLB",
            export_yup=True,
            export_apply=True,
            export_cameras=False,
            export_lights=False,
            export_materials="EXPORT",
            export_vertex_color="MATERIAL",
            export_extras=False,
        )


main()
