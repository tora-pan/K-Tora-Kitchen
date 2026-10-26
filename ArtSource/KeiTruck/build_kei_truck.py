"""
Procedural kei truck (cab-over mini truck in the style of a Suzuki Carry / Honda Acty).

Run:
  /Applications/Blender.app/Contents/MacOS/Blender --background --python build_kei_truck.py -- [--fbx] [--render]

--fbx writes the Unity model straight to Assets/Models/KeiTruck.fbx.

Conventions: meters, Z up, the truck's front faces -Y, X is the width axis.
The model is split into collections so the bed can be swapped later:
  KT_Chassis  frame, axles, wheels, bumpers, lights below the bed
  KT_Cab      cab body, glass, lights, mirrors, trim
  KT_Bed      flat deck, drop-side gates (hinged), guard frame
Empties named Mount_* mark attachment points for future modules (food-truck box, stall canopy...).
"""
import bpy
import bmesh
import math
import os
import sys
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
UNITY_FBX = os.path.join(HERE, "..", "..", "Assets", "Models", "KeiTruck.fbx")
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

# ---------------------------------------------------------------- dimensions
L, W, H = 3.395, 1.475, 1.765        # kei class maximum length / width, typical height
HW = W / 2
FRONT_Y, REAR_Y = -L / 2, L / 2
WHEEL_R, TIRE_W = 0.27, 0.145         # 145R12-ish
TRACK_HALF = 0.645
FRONT_AXLE_Y, REAR_AXLE_Y = -1.00, 0.905   # 1905 mm wheelbase
CAB_FRONT_Y = -1.70
CAB_REAR_Y = -0.30
CAB_BOTTOM_Z = 0.40
TAPER_Z, TAPER = 1.05, 0.05           # cab sides lean inward above the beltline
BED_FRONT_Y = -0.25
FLOOR_BOTTOM_Z, FLOOR_TOP_Z = 0.62, 0.67
GATE_BOTTOM_Z, GATE_TOP_Z = 0.655, 0.97
GUARD_TOP_Z = 1.80

# windshield line in the side profile (y as a function of z)
WS_BOTTOM = (-1.665, 1.08)
WS_TOP = (-1.425, 1.715)
WS_SLOPE = (WS_TOP[0] - WS_BOTTOM[0]) / (WS_TOP[1] - WS_BOTTOM[1])


def ws_y(z):
    return WS_BOTTOM[0] + (z - WS_BOTTOM[1]) * WS_SLOPE


def taper_scale(z):
    t = max(0.0, min(1.0, (z - TAPER_Z) / (H - TAPER_Z)))
    return 1.0 - TAPER * t


def side_x(z):
    return HW * taper_scale(z)


# ---------------------------------------------------------------- helpers
def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def material(name, color, rough=0.5, metal=0.0, coat=0.0, emit=0.0):
    m = bpy.data.materials.new(name)
    try:
        m.use_nodes = True
    except Exception:
        pass
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
    return m


def collection(name):
    c = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(c)
    return c


def empty(name, col, loc=(0, 0, 0), parent=None, size=0.2, kind="PLAIN_AXES"):
    e = bpy.data.objects.new(name, None)
    e.empty_display_type = kind
    e.empty_display_size = size
    col.objects.link(e)
    e.parent = parent
    e.location = loc
    return e


def bm_box(bm, mn, mx):
    c = Vector(((mn[0] + mx[0]) / 2, (mn[1] + mx[1]) / 2, (mn[2] + mx[2]) / 2))
    s = (mx[0] - mn[0], mx[1] - mn[1], mx[2] - mn[2])
    bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation(c) @ Matrix.Diagonal((*s, 1.0)))


def axis_matrix(axis):
    if axis == "X":
        return Matrix.Rotation(math.pi / 2, 4, "Y")
    if axis == "Y":
        return Matrix.Rotation(math.pi / 2, 4, "X")
    return Matrix.Identity(4)


def bm_cyl(bm, loc, r, depth, axis="X", segs=32, r2=None):
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segs,
                          radius1=r, radius2=r if r2 is None else r2, depth=depth,
                          matrix=Matrix.Translation(Vector(loc)) @ axis_matrix(axis))


def bm_poly(bm, pts):
    bm.faces.new([bm.verts.new(p) for p in pts])


def rounded(pts2d, r, segs=4):
    """Round the corners of a convex 2D polygon (approximate, quadratic bezier per corner)."""
    pts = [Vector(p) for p in pts2d]
    out = []
    n = len(pts)
    for i in range(n):
        p, a, b = pts[i], pts[i - 1], pts[(i + 1) % n]
        d1, d2 = (a - p), (b - p)
        rr = min(r, d1.length * 0.45, d2.length * 0.45)
        p0, p2 = p + d1.normalized() * rr, p + d2.normalized() * rr
        for k in range(segs + 1):
            t = k / segs
            out.append((1 - t) ** 2 * p0 + 2 * (1 - t) * t * p + t ** 2 * p2)
    return out


def apply_modifiers(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    old = ob.data
    ob.modifiers.clear()
    ob.data = me
    me.name = ob.name
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


def mesh_obj(name, bm, col, mat, parent=None, loc=(0, 0, 0), bevel=0.0, segs=2, limit=30, smooth=True):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    col.objects.link(ob)
    if mat:
        me.materials.append(mat)
    ob.parent = parent
    ob.location = loc
    if bevel > 0:
        md = ob.modifiers.new("Bevel", "BEVEL")
        md.width = bevel
        md.segments = segs
        md.limit_method = "ANGLE"
        md.angle_limit = math.radians(limit)
        apply_modifiers(ob)
    if smooth:
        smooth_by_angle(ob, (90 / segs + 5) if bevel > 0 else 30)
    return ob


def box(name, mn, mx, col, mat, parent=None, bevel=0.0, segs=2):
    bm = bmesh.new()
    bm_box(bm, mn, mx)
    return mesh_obj(name, bm, col, mat, parent, bevel=bevel, segs=segs)


def boolean_cut(ob, cutters):
    for c in cutters:
        md = ob.modifiers.new("Cut", "BOOLEAN")
        md.operation = "DIFFERENCE"
        md.object = c
        md.solver = "EXACT"
    apply_modifiers(ob)
    for c in cutters:
        bpy.data.objects.remove(c)


# ---------------------------------------------------------------- materials
def make_materials():
    return dict(
        body=material("KT_Body_White", (0.82, 0.83, 0.83), rough=0.28, coat=0.6),
        glass=material("KT_Glass", (0.015, 0.02, 0.025), rough=0.04, coat=1.0),
        trim=material("KT_Trim_Black", (0.025, 0.025, 0.027), rough=0.55),
        plastic=material("KT_Bumper_Gray", (0.09, 0.095, 0.1), rough=0.6),
        frame=material("KT_Frame_Dark", (0.04, 0.04, 0.045), rough=0.7),
        rubber=material("KT_Tire", (0.018, 0.018, 0.018), rough=0.85),
        steel=material("KT_Steel_Wheel", (0.62, 0.63, 0.64), rough=0.35, metal=0.6),
        chrome=material("KT_Chrome", (0.9, 0.9, 0.9), rough=0.12, metal=1.0),
        lamp=material("KT_Headlamp", (0.85, 0.88, 0.9), rough=0.05, metal=0.3, coat=1.0),
        red=material("KT_Taillight", (0.55, 0.02, 0.02), rough=0.1, coat=1.0),
        amber=material("KT_Indicator", (0.95, 0.42, 0.02), rough=0.1, coat=1.0),
        plate=material("KT_Plate_Yellow", (0.95, 0.78, 0.08), rough=0.4),
        mirror=material("KT_Mirror", (0.7, 0.75, 0.8), rough=0.02, metal=1.0),
    )


# ---------------------------------------------------------------- cab
def build_cab(col, parent, M):
    # Side profile (y, z), extruded across the width.
    profile = [
        (CAB_REAR_Y, CAB_BOTTOM_Z),
        (CAB_REAR_Y, H),
        (-1.36, H),
        WS_TOP,
        WS_BOTTOM,
        (CAB_FRONT_Y, 1.00),
        (CAB_FRONT_Y, CAB_BOTTOM_Z),
    ]
    bm = bmesh.new()
    face = bm.faces.new([bm.verts.new((-HW, y, z)) for y, z in profile])
    ext = bmesh.ops.extrude_face_region(bm, geom=[face])
    bmesh.ops.translate(bm, verts=[g for g in ext["geom"] if isinstance(g, bmesh.types.BMVert)], vec=(W, 0, 0))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
    bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, 0, TAPER_Z), plane_no=(0, 0, 1))
    for v in bm.verts:
        v.co.x *= taper_scale(v.co.z)
    # generous radius on the front corners and A-pillars, like the real trucks
    bm.normal_update()
    corner = [e for e in bm.edges if len(e.link_faces) == 2
              and any(abs(f.normal.x) > 0.9 for f in e.link_faces)
              and any(f.normal.y < -0.3 for f in e.link_faces)]
    bmesh.ops.bevel(bm, geom=corner, offset=0.11, segments=6, affect="EDGES", profile=0.5)
    cab = mesh_obj("Cab_Body", bm, col, M["body"], parent, smooth=False)

    # front wheel arches
    cutters = []
    for s in (-1, 1):
        cbm = bmesh.new()
        bm_cyl(cbm, (s * (HW + 0.05), FRONT_AXLE_Y, WHEEL_R), 0.335, 0.5, "X", segs=64)
        cutters.append(mesh_obj("cutter", cbm, col, None, smooth=False))
    boolean_cut(cab, cutters)
    md = cab.modifiers.new("Bevel", "BEVEL")
    md.width, md.segments, md.limit_method, md.angle_limit = 0.065, 4, "ANGLE", math.radians(17)
    apply_modifiers(cab)
    smooth_by_angle(cab, 27)

    # windshield
    n = Vector((0, -(WS_TOP[1] - WS_BOTTOM[1]), WS_TOP[0] - WS_BOTTOM[0])).normalized() * 0.004
    z0, z1 = 1.10, 1.655
    pts = rounded([(-side_x(z0) + 0.13, z0), (side_x(z0) - 0.13, z0),
                   (side_x(z1) - 0.14, z1), (-side_x(z1) + 0.14, z1)], 0.05)
    bm = bmesh.new()
    bm_poly(bm, [Vector((x, ws_y(z), z)) + n for x, z in pts])
    mesh_obj("Cab_Windshield", bm, col, M["glass"], parent)

    # side windows, door seams, handles, mirrors
    win = [(-1.505, 1.13), (-0.64, 1.13), (-0.64, 1.655), (-1.31, 1.655)]
    seam = [(-1.57, 0.43), (-1.57, 1.08), (-1.345, 1.69), (-0.57, 1.69), (-0.57, 0.43)]
    for s, tag in ((-1, "L"), (1, "R")):
        bm = bmesh.new()
        pts = rounded(win, 0.045)
        if s < 0:
            pts = pts[::-1]
        bm_poly(bm, [(s * (side_x(z) + 0.003), y, z) for y, z in pts])
        mesh_obj(f"Cab_Window_{tag}", bm, col, M["glass"], parent)

        bm = bmesh.new()
        hw = 0.003
        for (ya, za), (yb, zb) in zip(seam, seam[1:]):
            d = Vector((yb - ya, zb - za)).normalized()
            p = Vector((-d.y, d.x)) * hw
            quad = [(ya + p.x, za + p.y), (yb + p.x, zb + p.y), (yb - p.x, zb - p.y), (ya - p.x, za - p.y)]
            bm_poly(bm, [(s * (side_x(z) + 0.0015), y, z) for y, z in quad])
        mesh_obj(f"Cab_DoorSeam_{tag}", bm, col, M["trim"], parent)

        x = s * HW
        box(f"Cab_DoorHandle_{tag}", (min(x, x + s * 0.014), -0.74, 1.005), (max(x, x + s * 0.014), -0.63, 1.03),
            col, M["trim"], parent, bevel=0.004)
        # mirror arm + housing (cab-over trucks mount them at the front door corner)
        x0 = side_x(1.12)
        box(f"Cab_MirrorArm_{tag}", (min(s * x0, s * (x0 + 0.11)), -1.53, 1.12),
            (max(s * x0, s * (x0 + 0.11)), -1.50, 1.145), col, M["trim"], parent, bevel=0.006)
        xa, xb = s * (x0 + 0.075), s * (x0 + 0.135)
        box(f"Cab_MirrorHousing_{tag}", (min(xa, xb), -1.56, 1.06), (max(xa, xb), -1.48, 1.27),
            col, M["trim"], parent, bevel=0.015)
        xa, xb = s * (x0 + 0.08), s * (x0 + 0.13)
        box(f"Cab_MirrorGlass_{tag}", (min(xa, xb), -1.481, 1.07), (max(xa, xb), -1.478, 1.26),
            col, M["mirror"], parent)
        # drip rail above the door
        bm = bmesh.new()
        bm_box(bm, (-0.006, -1.33, 1.695), (0.006, -0.36, 1.71))
        rail = mesh_obj(f"Cab_DripRail_{tag}", bm, col, M["body"], parent, bevel=0.004)
        rail.location.x = s * (side_x(1.70) + 0.004)

    # rear window
    bm = bmesh.new()
    pts = rounded([(-0.52, 1.17), (0.52, 1.17), (0.52, 1.63), (-0.52, 1.63)], 0.05)
    bm_poly(bm, [(x, CAB_REAR_Y + 0.003, z) for x, z in pts])
    mesh_obj("Cab_RearWindow", bm, col, M["glass"], parent)

    # front face: headlamps, garnish, indicators, bumper, plate, wipers
    fy = CAB_FRONT_Y
    for s, tag in ((-1, "L"), (1, "R")):
        xa, xb = sorted((s * 0.37, s * 0.60))
        box(f"Cab_HeadlampBezel_{tag}", (xa, fy - 0.012, 0.795), (xb, fy + 0.01, 0.985), col, M["trim"], parent, bevel=0.02, segs=3)
        box(f"Cab_Headlamp_{tag}", (xa + 0.012, fy - 0.02, 0.807), (xb - 0.012, fy, 0.973), col, M["lamp"], parent, bevel=0.018, segs=3)
        xa, xb = sorted((s * 0.44, s * 0.59))
        box(f"Cab_Indicator_{tag}", (xa, fy - 0.012, 0.715), (xb, fy + 0.01, 0.765), col, M["amber"], parent, bevel=0.01)
    box("Cab_FrontGarnish", (-0.355, fy - 0.01, 0.82), (0.355, fy + 0.01, 0.96), col, M["trim"], parent, bevel=0.012)
    for i in range(3):
        z = 0.85 + i * 0.04
        box(f"Cab_GarnishSlat_{i}", (-0.33, fy - 0.016, z), (0.33, fy - 0.008, z + 0.012), col, M["plastic"], parent)
    box("Cab_FrontBumper", (-HW + 0.005, fy - 0.045, 0.30), (HW - 0.005, fy + 0.04, 0.49), col, M["plastic"], parent, bevel=0.035, segs=3)
    box("Cab_FrontPlate", (-0.165, fy - 0.052, 0.315), (0.165, fy - 0.044, 0.48), col, M["plate"], parent, bevel=0.004)
    box("Cab_UnderPanel", (-HW + 0.05, -1.66, 0.36), (HW - 0.05, CAB_REAR_Y - 0.03, CAB_BOTTOM_Z + 0.01), col, M["frame"], parent)
    for i, x0 in enumerate((-0.60, -0.08)):
        bm = bmesh.new()
        bm_box(bm, (0, -0.006, -0.006), (0.46, 0.006, 0.006))
        wiper = mesh_obj(f"Cab_Wiper_{i}", bm, col, M["trim"], parent, bevel=0.003)
        wiper.location = (x0, ws_y(1.12) - 0.012, 1.12)
        wiper.rotation_euler = (math.atan(WS_SLOPE) * -1 + 0.0, 0.0, 0.0)
        wiper.rotation_euler.y = math.radians(-8)


# ---------------------------------------------------------------- bed
def build_bed(col, parent, M):
    box("Bed_Floor", (-HW, BED_FRONT_Y, FLOOR_BOTTOM_Z), (HW, REAR_Y, FLOOR_TOP_Z), col, M["body"], parent, bevel=0.01)
    bm = bmesh.new()
    for i in range(7):
        x = -0.54 + i * 0.18
        bm_box(bm, (x - 0.02, BED_FRONT_Y + 0.08, FLOOR_TOP_Z), (x + 0.02, REAR_Y - 0.08, FLOOR_TOP_Z + 0.007))
    mesh_obj("Bed_FloorRibs", bm, col, M["body"], parent, bevel=0.003)

    def gate(name, mn, mx, hinge, ribs_axis, outward):
        bm = bmesh.new()
        bm_box(bm, mn, mx)
        # pressed horizontal ribs on the outside face
        for z in (0.745, 0.855):
            a, b = list(mn), list(mx)
            a[2], b[2] = z, z + 0.022
            if ribs_axis == "X":
                o = mx[0] if outward > 0 else mn[0]
                a[0], b[0] = sorted((o, o + outward * 0.008))
                a[1], b[1] = mn[1] + 0.05, mx[1] - 0.05
            else:
                o = mx[1]
                a[1], b[1] = o, o + 0.008
                a[0], b[0] = mn[0] + 0.05, mx[0] - 0.05
            bm_box(bm, a, b)
        hv = Vector(hinge)
        for v in bm.verts:
            v.co -= hv
        return mesh_obj(name, bm, col, M["body"], parent, loc=hinge, bevel=0.006)

    # Gate origins sit on their hinge line, so rotating them drops the sides.
    y0, y1 = BED_FRONT_Y + 0.05, REAR_Y - 0.05
    gate("Bed_Gate_L", (-HW, y0, GATE_BOTTOM_Z), (-HW + 0.03, y1, GATE_TOP_Z), (-HW, (y0 + y1) / 2, GATE_BOTTOM_Z), "X", -1)
    gate("Bed_Gate_R", (HW - 0.03, y0, GATE_BOTTOM_Z), (HW, y1, GATE_TOP_Z), (HW, (y0 + y1) / 2, GATE_BOTTOM_Z), "X", 1)
    gate("Bed_Gate_Tail", (-HW + 0.05, REAR_Y - 0.03, GATE_BOTTOM_Z), (HW - 0.05, REAR_Y, GATE_TOP_Z), (0, REAR_Y, GATE_BOTTOM_Z), "Y", 1)

    for s, tag in ((-1, "L"), (1, "R")):
        xa, xb = sorted((s * HW, s * (HW - 0.05)))
        box(f"Bed_RearPost_{tag}", (xa, REAR_Y - 0.05, FLOOR_BOTTOM_Z), (xb, REAR_Y, GATE_TOP_Z + 0.02), col, M["body"], parent, bevel=0.008)
        box(f"Bed_TailLatch_{tag}", (s * 0.66 - 0.02, REAR_Y, 0.93), (s * 0.66 + 0.02, REAR_Y + 0.015, 0.96), col, M["trim"], parent, bevel=0.003)
        # rope hooks under the deck edge
        for y in (-0.05, 0.6, 1.25):
            xa, xb = sorted((s * HW, s * (HW + 0.02)))
            box(f"Bed_RopeHook_{tag}_{y}", (xa, y - 0.015, 0.585), (xb, y + 0.015, 0.625), col, M["trim"], parent, bevel=0.004)

    # guard frame ("torii") behind the cab, with the overhang over the roof
    gy0, gy1 = BED_FRONT_Y, BED_FRONT_Y + 0.035
    box("Bed_Headboard", (-HW, gy0, FLOOR_BOTTOM_Z), (HW, gy1, GATE_TOP_Z + 0.02), col, M["body"], parent, bevel=0.008)
    bm = bmesh.new()
    t = 0.035
    for s in (-1, 1):
        x = s * (HW - t / 2 - 0.005)
        bm_box(bm, (x - t / 2, gy0, GATE_TOP_Z), (x + t / 2, gy0 + t, GUARD_TOP_Z))
        bm_box(bm, (x - t / 2, CAB_REAR_Y - 0.22, GUARD_TOP_Z - t), (x + t / 2, gy0 + t, GUARD_TOP_Z))
    bm_box(bm, (-HW + 0.005, gy0, GUARD_TOP_Z - t), (HW - 0.005, gy0 + t, GUARD_TOP_Z))
    bm_box(bm, (-HW + 0.005, CAB_REAR_Y - 0.22, GUARD_TOP_Z - t), (HW - 0.005, CAB_REAR_Y - 0.22 + t, GUARD_TOP_Z))
    mesh_obj("Bed_GuardFrame", bm, col, M["body"], parent, bevel=0.006)
    bm = bmesh.new()
    for i in range(9):
        x = -0.6 + i * 0.15
        bm_box(bm, (x - 0.009, gy0 + 0.008, GATE_TOP_Z), (x + 0.009, gy0 + 0.026, GUARD_TOP_Z - t))
    mesh_obj("Bed_GuardBars", bm, col, M["plastic"], parent, bevel=0.003)


# ---------------------------------------------------------------- chassis
def build_wheel(name, col, parent, side, M):
    hub = empty(name, col, (side * TRACK_HALF, 0, 0), parent, size=0.3, kind="CIRCLE")
    hub.rotation_euler = (0, math.pi / 2, 0)  # circle display around X axis
    hub.rotation_euler = (0, 0, 0)
    # tire: rounded cross-section spun around the axle, open in the middle for the rim
    hw, r0 = TIRE_W / 2, 0.165
    sect = rounded([(-hw + 0.012, r0), (hw - 0.012, r0), (hw, WHEEL_R - 0.03), (hw - 0.03, WHEEL_R),
                    (-hw + 0.03, WHEEL_R), (-hw, WHEEL_R - 0.03)], 0.03, segs=4)
    bm = bmesh.new()
    vs = [bm.verts.new((x, 0, r)) for x, r in sect]
    es = [bm.edges.new((vs[i], vs[(i + 1) % len(vs)])) for i in range(len(vs))]
    bmesh.ops.spin(bm, geom=vs + es, cent=(0, 0, 0), axis=(1, 0, 0), angle=2 * math.pi, steps=64, use_duplicate=False)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    tire = mesh_obj(f"{name}_Tire", bm, col, M["rubber"], hub, smooth=False)
    smooth_by_angle(tire, 50)
    bm = bmesh.new()
    bm_cyl(bm, (0, 0, 0), r0 + 0.005, TIRE_W - 0.03, "X", segs=48)
    mesh_obj(f"{name}_RimBarrel", bm, col, M["steel"], hub)
    o = side * (TIRE_W / 2 - 0.035)
    bm = bmesh.new()
    bm_cyl(bm, (o, 0, 0), 0.175, 0.02, "X", segs=48)
    mesh_obj(f"{name}_Rim", bm, col, M["steel"], hub, bevel=0.006, segs=2)
    bm = bmesh.new()
    for i in range(6):
        a = i * math.pi / 3
        bm_cyl(bm, (o + side * 0.006, 0.122 * math.cos(a), 0.122 * math.sin(a)), 0.022, 0.012, "X", segs=16)
    mesh_obj(f"{name}_RimHoles", bm, col, M["frame"], hub)
    bm = bmesh.new()
    bm_cyl(bm, (o + side * 0.02, 0, 0), 0.078, 0.03, "X", segs=32, r2=0.065)
    if side < 0:
        bmesh.ops.scale(bm, vec=(-1, 1, 1), verts=bm.verts)
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
    mesh_obj(f"{name}_HubCap", bm, col, M["chrome"], hub, bevel=0.008, segs=3)
    return hub


def build_chassis(col, parent, M):
    for axle_y, tag in ((FRONT_AXLE_Y, "Front"), (REAR_AXLE_Y, "Rear")):
        axle = empty(f"Axle_{tag}", col, (0, axle_y, WHEEL_R), parent, size=0.15)
        build_wheel(f"Wheel_{tag}_L", col, axle, -1, M)
        build_wheel(f"Wheel_{tag}_R", col, axle, 1, M)

    bm = bmesh.new()
    for s in (-1, 1):
        bm_box(bm, (s * 0.39 - 0.03, -1.55, 0.47), (s * 0.39 + 0.03, REAR_Y - 0.06, 0.59))
    for y in (-0.15, 0.35, 1.25, 1.6):
        bm_box(bm, (-0.5, y - 0.025, 0.59), (0.5, y + 0.025, FLOOR_BOTTOM_Z))
    mesh_obj("Chassis_Frame", bm, col, M["frame"], parent, bevel=0.005)

    bm = bmesh.new()
    bm_cyl(bm, (0, REAR_AXLE_Y, WHEEL_R), 0.045, 2 * TRACK_HALF - 0.12, "X", segs=24)
    bm_cyl(bm, (0, REAR_AXLE_Y - 0.03, WHEEL_R), 0.12, 0.16, "Y", segs=24)
    bm_cyl(bm, (0, REAR_AXLE_Y - 0.5, WHEEL_R + 0.05), 0.03, 0.9, "Y", segs=12)  # prop shaft
    for s in (-1, 1):
        bm_box(bm, (s * 0.39 - 0.03, REAR_AXLE_Y - 0.5, WHEEL_R + 0.05), (s * 0.39 + 0.03, REAR_AXLE_Y + 0.5, WHEEL_R + 0.09))
    mesh_obj("Chassis_RearAxle", bm, col, M["frame"], parent, bevel=0.004)

    box("Chassis_FuelTank", (-0.33, 0.05, 0.36), (0.33, 0.45, 0.58), col, M["frame"], parent, bevel=0.03, segs=3)
    bm = bmesh.new()
    bm_cyl(bm, (0.24, 0.6, 0.30), 0.024, 1.4, "Y", segs=12)
    bm_cyl(bm, (0.24, 0.55, 0.30), 0.07, 0.4, "Y", segs=20)
    mesh_obj("Chassis_Exhaust", bm, col, M["steel"], parent, bevel=0.01, segs=2)

    # rear wheel housings tucked under the deck
    for s, tag in ((-1, "L"), (1, "R")):
        bm = bmesh.new()
        bm_cyl(bm, (s * TRACK_HALF, REAR_AXLE_Y, WHEEL_R), WHEEL_R + 0.05, 0.2, "X", segs=48)
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:],
                               plane_co=(0, 0, 0.47), plane_no=(0, 0, 1), clear_inner=True)
        mesh_obj(f"Chassis_WheelHouse_{tag}", bm, col, M["frame"], parent, smooth=False)
        xa, xb = sorted((s * (TRACK_HALF - 0.09), s * (TRACK_HALF + 0.09)))
        box(f"Chassis_MudFlap_{tag}", (xa, REAR_AXLE_Y + 0.31, 0.16), (xb, REAR_AXLE_Y + 0.32, 0.6), col, M["rubber"], parent)

    # rear bumper, lamps, plate
    ry = REAR_Y
    box("Chassis_RearBumper", (-0.56, ry - 0.07, 0.44), (0.56, ry + 0.015, 0.52), col, M["plastic"], parent, bevel=0.015)
    for s, tag in ((-1, "L"), (1, "R")):
        xa, xb = sorted((s * 0.49, s * 0.725))
        box(f"Chassis_TailHousing_{tag}", (xa, ry - 0.09, 0.45), (xb, ry + 0.005, 0.605), col, M["plastic"], parent, bevel=0.012)
        xa, xb = sorted((s * 0.585, s * 0.71))
        box(f"Chassis_TailLamp_{tag}", (xa, ry, 0.465), (xb, ry + 0.015, 0.59), col, M["red"], parent, bevel=0.008)
        xa, xb = sorted((s * 0.505, s * 0.575))
        box(f"Chassis_RearIndicator_{tag}", (xa, ry, 0.465), (xb, ry + 0.015, 0.59), col, M["amber"], parent, bevel=0.008)
    box("Chassis_RearPlate", (-0.165, ry + 0.015, 0.44), (0.165, ry + 0.023, 0.605), col, M["plate"], parent, bevel=0.004)


# ---------------------------------------------------------------- scene / render
def setup_stage():
    sc = bpy.context.scene
    world = bpy.data.worlds.new("World")
    sc.world = world
    try:
        world.use_nodes = True
    except Exception:
        pass
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.62, 0.68, 0.78, 1)
    bg.inputs["Strength"].default_value = 0.9

    col = collection("Stage")
    bpy.ops.mesh.primitive_plane_add(size=60)
    ground = bpy.context.active_object
    ground.name = "Ground"
    for c in ground.users_collection:
        c.objects.unlink(ground)
    col.objects.link(ground)
    ground.data.materials.append(material("Ground", (0.42, 0.42, 0.41), rough=0.9))

    sun_data = bpy.data.lights.new("Sun", "SUN")
    sun_data.energy = 3.5
    sun_data.angle = math.radians(4)
    sun = bpy.data.objects.new("Sun", sun_data)
    sun.rotation_euler = (math.radians(48), 0, math.radians(-40))
    col.objects.link(sun)

    target = empty("CamTarget", col, (0, -0.15, 0.85))
    cams = {}
    for name, loc, lens, ortho in (
        ("front34", (-4.4, -5.6, 2.1), 50, None),
        ("rear34", (4.6, 5.2, 2.6), 50, None),
        ("side", (-8, -0.0, 0.95), 50, 3.9),
        ("front", (0, -8, 0.95), 50, 2.5),
    ):
        cd = bpy.data.cameras.new(name)
        cd.lens = lens
        if ortho:
            cd.type = "ORTHO"
            cd.ortho_scale = ortho
        cam = bpy.data.objects.new(f"Cam_{name}", cd)
        cam.location = loc
        col.objects.link(cam)
        con = cam.constraints.new("TRACK_TO")
        con.target = target
        con.track_axis = "TRACK_NEGATIVE_Z"
        con.up_axis = "UP_Y"
        cams[name] = cam
    sc.camera = cams["front34"]
    return cams


def render_views(cams, engine):
    sc = bpy.context.scene
    if engine == "cycles":
        sc.render.engine = "CYCLES"
        sc.cycles.samples = 96
        sc.cycles.use_denoising = True
    else:
        for e in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
            try:
                sc.render.engine = e
                break
            except TypeError:
                continue
        sc.eevee.taa_render_samples = 64
    sc.render.resolution_x, sc.render.resolution_y = 1400, 875
    out = os.path.join(HERE, "renders")
    os.makedirs(out, exist_ok=True)
    for name, cam in cams.items():
        sc.camera = cam
        sc.render.filepath = os.path.join(out, f"kei_truck_{name}.png")
        bpy.ops.render.render(write_still=True)


def export_unity_fbx(root_col):
    """FBX for Unity: meters, Y up, truck front along Unity +Z, hierarchy kept (wheels/gates stay separate)."""
    bpy.ops.object.select_all(action="DESELECT")
    objs = [o for o in root_col.all_objects if o.type in {"MESH", "EMPTY"}]
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects["KeiTruck"]
    bpy.ops.export_scene.fbx(
        filepath=os.path.normpath(UNITY_FBX),
        use_selection=True,
        object_types={"MESH", "EMPTY"},
        apply_scale_options="FBX_SCALE_UNITS",
        axis_forward="-Z",
        axis_up="Y",
        bake_space_transform=True,
        mesh_smooth_type="FACE",
        use_mesh_modifiers=True,
        add_leaf_bones=False,
        bake_anim=False,
        path_mode="AUTO",
    )


def main():
    reset_scene()
    M = make_materials()
    root_col = collection("KeiTruck")
    c_chassis, c_cab, c_bed = (bpy.data.collections.new(n) for n in ("KT_Chassis", "KT_Cab", "KT_Bed"))
    for c in (c_chassis, c_cab, c_bed):
        root_col.children.link(c)

    root = empty("KeiTruck", root_col, size=0.5, kind="ARROWS")
    g_chassis = empty("Chassis", c_chassis, parent=root)
    g_cab = empty("Cab", c_cab, parent=root)
    g_bed = empty("Bed", c_bed, parent=root)

    build_chassis(c_chassis, g_chassis, M)
    build_cab(c_cab, g_cab, M)
    build_bed(c_bed, g_bed, M)

    # attachment points for future conversions
    empty("Mount_BedFloor", root_col, (0, (BED_FRONT_Y + REAR_Y) / 2, FLOOR_TOP_Z), root, size=0.3, kind="CUBE")
    empty("Mount_CabRoof", root_col, (0, (CAB_REAR_Y - 1.36) / 2, H), root, size=0.2, kind="CUBE")
    empty("Mount_GuardTop", root_col, (0, BED_FRONT_Y, GUARD_TOP_Z), root, size=0.2, kind="CUBE")

    cams = setup_stage()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "kei_truck.blend"))
    if "--fbx" in ARGS:
        export_unity_fbx(root_col)
    if "--render" in ARGS:
        render_views(cams, "cycles" if "--cycles" in ARGS else "eevee")


main()
