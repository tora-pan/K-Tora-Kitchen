"""
Shared helpers for the K-Tora Blender build scripts (customers, props).

Conventions: meters, Z up, models face -Y (which becomes Unity +Z after export),
origin at the base center unless a script says otherwise.
"""
import bpy
import bmesh
import math
import os
from mathutils import Vector, Matrix

PROJECT_ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
UNITY_MODELS = os.path.join(PROJECT_ROOT, "Assets", "Models")

JP_FONTS = ["/System/Library/Fonts/Hiragino Sans GB.ttc", "/System/Library/Fonts/AquaKana.ttc"]
CHALK_FONT = "/System/Library/Fonts/Supplemental/Chalkboard.ttc"


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    _materials.clear()


# ---------------------------------------------------------------- materials
_materials = {}


def mat(name, color, rough=0.6, metal=0.0, coat=0.0, emit=0.0):
    """Cached Principled material; the same name always returns the same material."""
    if name in _materials:
        return _materials[name]
    m = bpy.data.materials.new(name)
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1.0)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if coat:
        b.inputs["Coat Weight"].default_value = coat
    if emit:
        b.inputs["Emission Color"].default_value = (*color, 1.0)
        b.inputs["Emission Strength"].default_value = emit
    m.diffuse_color = (*color, 1.0)
    _materials[name] = m
    return m


# ---------------------------------------------------------------- scene objects
def collection(name, parent=None):
    c = bpy.data.collections.new(name)
    (parent or bpy.context.scene.collection).children.link(c)
    return c


def empty(name, col, loc=(0, 0, 0), parent=None, size=0.2, kind="PLAIN_AXES"):
    e = bpy.data.objects.new(name, None)
    e.empty_display_type = kind
    e.empty_display_size = size
    col.objects.link(e)
    e.parent = parent
    e.location = loc
    return e


# ---------------------------------------------------------------- bmesh primitives (all return new verts)
def _dir_matrix(direction):
    d = Vector(direction).normalized()
    return Vector((0, 0, 1)).rotation_difference(d).to_matrix().to_4x4()


AXES = {"X": (1, 0, 0), "Y": (0, 1, 0), "Z": (0, 0, 1)}


def _old_layers(bm):
    v = bm.verts.layers.int.get("kit_old") or bm.verts.layers.int.new("kit_old")
    f = bm.faces.layers.int.get("kit_old") or bm.faces.layers.int.new("kit_old")
    return v, f


def _tag_all(bm):
    """Mark existing elements. bmesh ops use the built-in tag flag internally, so a custom layer is used."""
    lv, lf = _old_layers(bm)
    for v in bm.verts:
        v[lv] = 1
    for f in bm.faces:
        f[lf] = 1


def _untagged_verts(bm):
    lv, _ = _old_layers(bm)
    return [v for v in bm.verts if v[lv] == 0]


def _untagged_faces(bm):
    _, lf = _old_layers(bm)
    return [f for f in bm.faces if f[lf] == 0]


def box(bm, mn, mx, round_r=0.0, round_segs=2):
    _tag_all(bm)
    c = Vector([(a + b) / 2 for a, b in zip(mn, mx)])
    s = [b - a for a, b in zip(mn, mx)]
    verts = bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation(c) @ Matrix.Diagonal((*s, 1.0)))["verts"]
    if round_r > 0:
        edges = list({e for v in verts for e in v.link_edges})
        r = min(round_r, min(s) * 0.49)
        bmesh.ops.bevel(bm, geom=edges, offset=r, segments=round_segs, affect="EDGES", profile=0.5, clamp_overlap=True)
    return _untagged_verts(bm)


def cyl(bm, center, r, depth, axis="Z", segs=24, r2=None):
    d = AXES.get(axis, axis)
    m = Matrix.Translation(Vector(center)) @ _dir_matrix(d)
    return bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segs, radius1=r,
                                 radius2=r if r2 is None else r2, depth=depth, matrix=m)["verts"]


def sphere(bm, center, radii, segs=24, rings=12):
    if isinstance(radii, (int, float)):
        radii = (radii, radii, radii)
    m = Matrix.Translation(Vector(center)) @ Matrix.Diagonal((*radii, 1.0))
    return bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=rings, radius=1.0, matrix=m)["verts"]


def capsule(bm, a, b, r, segs=16, rings=9, scale=(1, 1)):
    """Capsule between points a and b. rings is odd so no ring sits on the equator."""
    a, b = Vector(a), Vector(b)
    half = (b - a).length / 2
    verts = bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=rings, radius=r)["verts"]
    for v in verts:
        v.co.x *= scale[0]
        v.co.y *= scale[1]
        v.co.z += half if v.co.z > 0 else -half
    m = Matrix.Translation((a + b) / 2) @ _dir_matrix(b - a if half > 1e-6 else (0, 0, 1))
    bmesh.ops.transform(bm, matrix=m, verts=verts)
    return verts


def torus(bm, center, R, r, axis="Z", segs=32, rsegs=10, arc=2 * math.pi, start=0.0):
    _tag_all(bm)
    ring = []
    for i in range(rsegs):
        t = 2 * math.pi * i / rsegs
        ring.append(bm.verts.new((R + r * math.cos(t), 0, r * math.sin(t))))
    edges = [bm.edges.new((ring[i], ring[(i + 1) % rsegs])) for i in range(rsegs)]
    bmesh.ops.rotate(bm, verts=ring, cent=(0, 0, 0), matrix=Matrix.Rotation(start, 3, "Z"))
    bmesh.ops.spin(bm, geom=ring + edges, cent=(0, 0, 0), axis=(0, 0, 1), angle=arc,
                   steps=max(3, int(segs * arc / (2 * math.pi))), use_duplicate=False)
    verts = _untagged_verts(bm)
    if arc >= 2 * math.pi - 1e-4:
        bmesh.ops.remove_doubles(bm, verts=verts, dist=1e-5)
        verts = _untagged_verts(bm)
    m = Matrix.Translation(Vector(center)) @ _dir_matrix(AXES.get(axis, axis))
    bmesh.ops.transform(bm, matrix=m, verts=verts)
    return verts


def oriented_disc(bm, pos, normal, radii, segs=12, rings=6):
    """Ellipsoid flattened along its local Z, then turned so that Z points along normal."""
    verts = sphere(bm, (0, 0, 0), radii, segs, rings)
    transform(bm, verts, Matrix.Translation(Vector(pos)) @ _dir_matrix(normal))
    return verts


def poly(bm, pts):
    vs = [bm.verts.new(p) for p in pts]
    bm.faces.new(vs)
    return vs


def transform(bm, verts, matrix):
    bmesh.ops.transform(bm, matrix=matrix, verts=verts)


# ---------------------------------------------------------------- multi-material mesh builder
class Part:
    """Accumulates primitives into one mesh with per-primitive materials."""

    def __init__(self):
        self.bm = bmesh.new()
        _old_layers(self.bm)
        self.mats = []

    def add(self, material, fn, *args, **kwargs):
        _tag_all(self.bm)
        verts = fn(self.bm, *args, **kwargs)
        if material not in self.mats:
            self.mats.append(material)
        idx = self.mats.index(material)
        for f in _untagged_faces(self.bm):
            f.material_index = idx
        return verts

    def build(self, name, col, parent=None, pivot=(0, 0, 0), smooth_angle=50, bevel=0.0, bevel_segs=2):
        pv = Vector(pivot)
        for v in self.bm.verts:
            v.co -= pv
        bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces)
        lv, lf = _old_layers(self.bm)
        self.bm.verts.layers.int.remove(lv)
        self.bm.faces.layers.int.remove(lf)
        me = bpy.data.meshes.new(name)
        self.bm.to_mesh(me)
        self.bm.free()
        for m in self.mats:
            me.materials.append(m)
        ob = bpy.data.objects.new(name, me)
        col.objects.link(ob)
        ob.parent = parent
        ob.location = pv
        if bevel > 0:
            md = ob.modifiers.new("Bevel", "BEVEL")
            md.width, md.segments, md.limit_method, md.angle_limit = bevel, bevel_segs, "ANGLE", math.radians(30)
            apply_modifiers(ob)
        smooth_by_angle(ob, smooth_angle)
        return ob


def apply_modifiers(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    old = ob.data
    ob.modifiers.clear()
    ob.data = me
    me.name = ob.name
    if old.users == 0:
        bpy.data.meshes.remove(old)


def smooth_by_angle(ob, angle_deg):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    th = math.radians(angle_deg)
    for f in bm.faces:
        f.smooth = True
    for e in bm.edges:
        e.smooth = len(e.link_faces) == 2 and e.calc_face_angle(0.0) < th
    bm.to_mesh(ob.data)
    bm.free()


# ---------------------------------------------------------------- text
def load_font(paths):
    for p in ([paths] if isinstance(paths, str) else paths):
        if os.path.exists(p):
            return bpy.data.fonts.load(p, check_existing=True)
    return None


def text_mesh(name, body, font, size, col, material, parent=None, loc=(0, 0, 0), rot=(0, 0, 0),
              extrude=0.0, line_spacing=1.0, subdivide=0):
    """Flat text mesh facing -Y (readable from the front), centered on loc."""
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body
    if font:
        cu.font = font
    cu.size = size
    cu.align_x, cu.align_y = "CENTER", "CENTER"
    cu.space_line = line_spacing
    cu.extrude = extrude
    tmp = bpy.data.objects.new(name + "_tmp", cu)
    col.objects.link(tmp)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg))
    bpy.data.objects.remove(tmp)
    bpy.data.curves.remove(cu)
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, "X"))
    if subdivide:
        bmesh.ops.triangulate(bm, faces=bm.faces)
        bmesh.ops.subdivide_edges(bm, edges=bm.edges, cuts=subdivide, use_grid_fill=True)
    bm.to_mesh(me)
    bm.free()
    me.name = name
    me.materials.append(material)
    ob = bpy.data.objects.new(name, me)
    col.objects.link(ob)
    ob.parent = parent
    ob.location = loc
    ob.rotation_euler = rot
    return ob


def shrinkwrap(ob, target, offset):
    md = ob.modifiers.new("Wrap", "SHRINKWRAP")
    md.target = target
    md.wrap_method = "NEAREST_SURFACEPOINT"
    md.offset = offset
    apply_modifiers(ob)


# ---------------------------------------------------------------- stage, render, export
def setup_stage(ground_color=(0.42, 0.42, 0.41)):
    sc = bpy.context.scene
    world = bpy.data.worlds.new("World")
    sc.world = world
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.62, 0.68, 0.78, 1)
    bg.inputs["Strength"].default_value = 0.9
    col = collection("Stage")
    me = bpy.data.meshes.new("Ground")
    bm = bmesh.new()
    box(bm, (-30, -30, -0.01), (30, 30, 0))
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat("Stage_Ground", ground_color, rough=0.9))
    col.objects.link(bpy.data.objects.new("Ground", me))
    sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
    sun.data.energy = 3.5
    sun.data.angle = math.radians(4)
    sun.rotation_euler = (math.radians(48), 0, math.radians(-40))
    col.objects.link(sun)
    return col


def camera(name, col, loc, target, lens=50, ortho=None):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    if ortho:
        cd.type, cd.ortho_scale = "ORTHO", ortho
    cam = bpy.data.objects.new(name, cd)
    cam.location = loc
    col.objects.link(cam)
    t = empty(name + "_Target", col, target)
    con = cam.constraints.new("TRACK_TO")
    con.target, con.track_axis, con.up_axis = t, "TRACK_NEGATIVE_Z", "UP_Y"
    return cam


def render(cam, path, res=(1600, 900), samples=64):
    sc = bpy.context.scene
    for e in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        try:
            sc.render.engine = e
            break
        except TypeError:
            continue
    sc.eevee.taa_render_samples = samples
    try:
        sc.view_settings.look = "AgX - Punchy"
    except TypeError:
        pass
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.camera = cam
    os.makedirs(os.path.dirname(path), exist_ok=True)
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)


def export_fbx(root, path):
    """Export root and its children for Unity: meters, Y up, -Y forward becomes Unity +Z."""
    bpy.ops.object.select_all(action="DESELECT")
    for o in [root, *root.children_recursive]:
        o.select_set(True)
    bpy.context.view_layer.objects.active = root
    saved = root.location.copy()
    root.location = (0, 0, 0)
    bpy.context.view_layer.update()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.export_scene.fbx(
        filepath=path, use_selection=True, object_types={"MESH", "EMPTY"},
        apply_scale_options="FBX_SCALE_UNITS", axis_forward="-Z", axis_up="Y",
        bake_space_transform=True, mesh_smooth_type="FACE", use_mesh_modifiers=True,
        add_leaf_bones=False, bake_anim=False, path_mode="AUTO",
    )
    root.location = saved
