"""
Scenery props for the beach parking lot.

Run from this folder:
  /Applications/Blender.app/Contents/MacOS/Blender --background --python build_props.py -- [--fbx] [--render]

--fbx writes one model per prop to Assets/Models/Props/<Name>.fbx.
Origins sit at the base center, except Prop_Lantern, whose origin is its hanging hook.
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402
import blender_kit as K  # noqa: E402

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def materials():
    m = K.mat
    return dict(
        wood=m("Wood", (0.55, 0.33, 0.16), rough=0.75),
        wood_dark=m("Wood_Dark", (0.3, 0.18, 0.09), rough=0.8),
        wood_light=m("Wood_Light", (0.72, 0.52, 0.3), rough=0.75),
        iron=m("Iron_Dark", (0.1, 0.1, 0.11), rough=0.45, metal=0.5),
        chalkboard=m("Chalkboard", (0.06, 0.08, 0.07), rough=0.9),
        chalk=m("Chalk", (0.93, 0.93, 0.9), rough=0.9),
        paper=m("Lantern_Paper", (0.88, 0.22, 0.09), rough=0.6, emit=0.35),
        rib=m("Lantern_Rib", (0.5, 0.1, 0.05), rough=0.6),
        ink=m("Lantern_Ink", (0.03, 0.03, 0.03), rough=0.6),
        board=m("Surf_Deck", (0.55, 0.78, 0.92), rough=0.3, coat=0.8),
        rail=m("Surf_Rail", (0.16, 0.38, 0.7), rough=0.3, coat=0.8),
        stripe=m("Surf_Stripe", (0.97, 0.97, 0.95), rough=0.3, coat=0.8),
        soil=m("Soil", (0.18, 0.11, 0.06), rough=1.0),
        leaf=m("Leaf", (0.24, 0.48, 0.2), rough=0.7),
        leaf_light=m("Leaf_Light", (0.36, 0.6, 0.25), rough=0.7),
        cone=m("Cone_Orange", (0.95, 0.36, 0.06), rough=0.45),
        reflect=m("Reflective_White", (0.95, 0.95, 0.93), rough=0.25),
        bollard=m("Bollard_Gray", (0.17, 0.17, 0.19), rough=0.5, metal=0.3),
        band=m("Bollard_Band", (0.75, 0.75, 0.72), rough=0.25, metal=0.6),
        bulb=m("Bulb_Warm", (1.0, 0.82, 0.5), rough=0.2, emit=4.0),
    )


FLOWER_COLORS = [(0.96, 0.5, 0.62), (0.98, 0.58, 0.22), (0.98, 0.86, 0.32), (0.97, 0.95, 0.92)]


# ---------------------------------------------------------------- props
def bench(M, col, root):
    p = K.Part()
    for s in (-1, 1):
        x0, x1 = s * 0.6 - 0.03, s * 0.6 + 0.03
        p.add(M["wood_dark"], K.box, (x0, -0.19, 0), (x1, -0.13, 0.42), 0.012)
        p.add(M["wood_dark"], K.box, (x0, 0.13, 0), (x1, 0.19, 0.86), 0.012)
        p.add(M["wood_dark"], K.box, (x0, -0.21, 0.36), (x1, 0.19, 0.42), 0.012)
        p.add(M["wood_dark"], K.box, (x0, -0.15, 0.1), (x1, 0.15, 0.15), 0.01)
    for y0 in (-0.22, -0.075, 0.07):
        p.add(M["wood"], K.box, (-0.74, y0, 0.42), (0.74, y0 + 0.13, 0.47), 0.015, 3)
    for z0 in (0.56, 0.7):
        p.add(M["wood"], K.box, (-0.74, 0.19, z0), (0.74, 0.23, z0 + 0.11), 0.015, 3)
    return p.build("Bench", col, root, smooth_angle=50)


def menu_board(M, col, root):
    length, tilt = 0.97, math.radians(12)
    hinge = Vector((0, 0, length * math.cos(tilt)))
    font = K.load_font(K.CHALK_FONT)
    for side, sign in (("Front", -1), ("Back", 1)):
        p = K.Part()
        z0, z1 = hinge.z - length, hinge.z
        for s in (-1, 1):
            p.add(M["wood"], K.box, (s * 0.28 - 0.025, -0.012, z0), (s * 0.28 + 0.025, 0.012, z1), 0.008)
        p.add(M["wood"], K.box, (-0.3, -0.015, z1 - 0.08), (0.3, 0.015, z1), 0.01)
        p.add(M["wood"], K.box, (-0.26, -0.01, z0 + 0.12), (0.26, 0.01, z0 + 0.17), 0.006)
        face_y = (-0.013, -0.003) if sign < 0 else (0.003, 0.013)
        p.add(M["chalkboard"], K.box, (-0.255, face_y[0], z0 + 0.17), (0.255, face_y[1], z1 - 0.08))
        panel = p.build(f"MenuBoard_{side}", col, root, pivot=hinge, smooth_angle=50)
        panel.rotation_euler.x = sign * tilt
        if sign < 0:
            fz = lambda z: z - hinge.z  # noqa: E731
            K.text_mesh("Menu_Title", "MENU", font, 0.1, col, M["chalk"], panel, (0, -0.0135, fz(0.69)))
            p2 = K.Part()
            p2.add(M["chalk"], K.box, (-0.12, -0.0136, fz(0.635)), (0.12, -0.0132, fz(0.642)))
            p2.build("Menu_Underline", col, panel)
            for i, item in enumerate(("Soba", "Tempura", "Onigiri", "Green Tea")):
                K.text_mesh(f"Menu_Item_{i}", item, font, 0.055, col, M["chalk"], panel,
                            (0, -0.0135, fz(0.575 - i * 0.07)))
    p = K.Part()
    p.add(M["iron"], K.cyl, hinge, 0.012, 0.62, "X", 12)
    return p.build("MenuBoard_Hinge", col, root)


def lantern(M, col, root):
    c, rx, rz = Vector((0, 0, -0.33)), 0.15, 0.2
    p = K.Part()
    p.add(M["paper"], K.sphere, c, (rx, rx, rz), 32, 20)
    body = p.build("Lantern_Body", col, root, smooth_angle=70)
    p = K.Part()
    for k in range(-4, 5):
        dz = rz * k / 5.0
        p.add(M["rib"], K.torus, c + Vector((0, 0, dz)), rx * math.sqrt(1 - (dz / rz) ** 2) + 0.001, 0.0035, "Z", 40, 6)
    for dz in (0.185, -0.185):
        p.add(M["ink"], K.cyl, c + Vector((0, 0, dz)), 0.085, 0.045, "Z", 28)
    p.add(M["ink"], K.cyl, (0, 0, -0.07), 0.006, 0.07, "Z", 8)
    p.add(M["iron"], K.torus, (0, 0, -0.02), 0.02, 0.004, "Y", 16, 6)
    p.build("Lantern_Frame", col, root, smooth_angle=60)
    font = K.load_font(K.JP_FONTS)
    text = K.text_mesh("Lantern_Text", "そ\nば", font, 0.14, col, M["ink"], root,
                       (0, -rx - 0.01, c.z), line_spacing=0.9, subdivide=3)
    K.shrinkwrap(text, body, 0.003)
    return body


def surfboard(M, col, root):
    p = K.Part()
    half_len, half_w, half_t = 1.0, 0.27, 0.036

    def board(bm):
        verts = K.sphere(bm, (0, 0, 0), (half_w, half_t, half_len), 64, 40)
        for v in verts:
            t = v.co.z / half_len
            v.co.x *= (1 - 0.6 * t * t) if t > 0 else (1 - 0.3 * t * t)
            v.co.y *= 1 - 0.35 * abs(t)
            v.co.y += 0.03 * t * t  # rocker
            v.co.z += half_len
        return verts

    p.add(M["board"], board)
    for f in p.bm.faces:
        n, cen = f.normal, f.calc_center_median()
        if abs(n.x) > 0.55 or n.y > 0.2:
            f.material_index = 1
        elif abs(cen.x) < 0.02 and 0.08 < cen.z < 1.9:
            f.material_index = 2
    p.mats += [M["rail"], M["stripe"]]
    p.add(M["rail"], K.oriented_disc, (0, 0.05, 0.16), (0, 1, 0.25), (0.08, 0.06, 0.006), 16, 8)
    return p.build("Surfboard", col, root, smooth_angle=60)


def planter(M, col, root, seed=3):
    p = K.Part()
    hx, hy = 0.45, 0.19
    for i in range(3):
        z0 = 0.02 + i * 0.1
        for s in (-1, 1):
            p.add(M["wood"], K.box, (-hx, s * hy - 0.015, z0), (hx, s * hy + 0.015, z0 + 0.092), 0.01)
            p.add(M["wood"], K.box, (s * hx - 0.015, -hy, z0), (s * hx + 0.015, hy, z0 + 0.092), 0.01)
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * (hx + 0.005), sy * (hy + 0.005)
            p.add(M["wood_dark"], K.box, (x - 0.03, y - 0.03, 0), (x + 0.03, y + 0.03, 0.34), 0.01)
    p.add(M["soil"], K.box, (-hx + 0.02, -hy + 0.02, 0.2), (hx - 0.02, hy - 0.02, 0.29))
    rng = random.Random(seed)
    bushes = []
    for i in range(8):
        cpos = Vector((rng.uniform(-0.34, 0.34), rng.uniform(-0.08, 0.08), rng.uniform(0.3, 0.36)))
        r = rng.uniform(0.09, 0.13)
        bushes.append((cpos, r))
        p.add(M["leaf"] if i % 2 else M["leaf_light"], K.sphere, cpos, (r, r, r * 0.85), 16, 10)
    for i in range(18):
        cpos, r = rng.choice(bushes)
        d = Vector((rng.uniform(-1, 1), rng.uniform(-1, 0.6), rng.uniform(0.35, 1))).normalized()
        pos = cpos + Vector((d.x * r, d.y * r, d.z * r * 0.85))
        color = K.mat(f"Flower_{i % len(FLOWER_COLORS)}", FLOWER_COLORS[i % len(FLOWER_COLORS)], rough=0.6)
        side = d.cross(Vector((0, 0, 1))).normalized() if abs(d.z) < 0.99 else Vector((1, 0, 0))
        up = d.cross(side)
        for k in range(5):
            a = 2 * math.pi * k / 5
            off = (side * math.cos(a) + up * math.sin(a)) * 0.03
            p.add(color, K.oriented_disc, pos + off + d * 0.004, d, (0.03, 0.02, 0.007), 10, 5)
        p.add(K.mat("Flower_Center", (0.98, 0.8, 0.2), rough=0.6), K.sphere, pos + d * 0.012, 0.016, 8, 6)
    return p.build("Planter", col, root, smooth_angle=55)


def crate(M, col, root):
    p = K.Part()
    hx, hy, h = 0.27, 0.2, 0.38
    p.add(M["wood_dark"], K.box, (-hx + 0.02, -hy + 0.02, 0.01), (hx - 0.02, hy - 0.02, h - 0.01))
    for i in range(3):
        z0 = 0.015 + i * 0.12
        for s in (-1, 1):
            p.add(M["wood"], K.box, (-hx + 0.03, s * hy - 0.012, z0), (hx - 0.03, s * hy + 0.012, z0 + 0.105), 0.008)
            p.add(M["wood"], K.box, (s * hx - 0.012, -hy + 0.03, z0), (s * hx + 0.012, hy - 0.03, z0 + 0.105), 0.008)
    for i in range(3):
        x0 = -hx + 0.02 + i * (2 * hx - 0.04) / 3
        p.add(M["wood"], K.box, (x0 + 0.005, -hy + 0.01, h - 0.012), (x0 + (2 * hx - 0.04) / 3 - 0.005, hy - 0.01, h + 0.012), 0.008)
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * hx, sy * hy
            p.add(M["wood_light"], K.box, (x - 0.03, y - 0.03, 0), (x + 0.03, y + 0.03, h + 0.015), 0.01)
    return p.build("Crate", col, root, smooth_angle=50)


def bollard(M, col, root):
    p = K.Part()
    p.add(M["bollard"], K.cyl, (0, 0, 0.015), 0.125, 0.03, "Z", 32)
    p.add(M["bollard"], K.cyl, (0, 0, 0.44), 0.09, 0.82, "Z", 32)
    p.add(M["bollard"], K.sphere, (0, 0, 0.85), (0.09, 0.09, 0.06), 32, 12)
    for z in (0.7, 0.62):
        p.add(M["band"], K.cyl, (0, 0, z), 0.093, 0.035, "Z", 32)
    return p.build("Bollard", col, root, smooth_angle=40)


def cone(M, col, root):
    p = K.Part()
    p.add(M["cone"], K.box, (-0.19, -0.19, 0), (0.19, 0.19, 0.035), 0.025, 2)
    z_base, z_top, r_base, r_top = 0.035, 0.68, 0.15, 0.035

    def r(z):
        return r_base + (r_top - r_base) * (z - z_base) / (z_top - z_base)

    bands = [(0.035, 0.3, "cone"), (0.3, 0.4, "reflect"), (0.4, 0.5, "cone"), (0.5, 0.58, "reflect"), (0.58, 0.68, "cone")]
    for a, b, key in bands:
        p.add(M[key], K.cyl, (0, 0, (a + b) / 2), r(a), b - a, "Z", 32, r(b))
    p.add(M["cone"], K.sphere, (0, 0, z_top), (r_top, r_top, 0.015), 32, 8)
    return p.build("TrafficCone", col, root, smooth_angle=40)


def string_lights(M, col, root):
    p = K.Part()
    span, top, sag = 1.5, 2.45, 0.35
    for s in (-1, 1):
        x = s * span
        p.add(M["wood"], K.box, (x - 0.05, -0.05, 0), (x + 0.05, 0.05, 2.6), 0.012)
        p.add(M["wood_dark"], K.box, (x - 0.065, -0.065, 2.6), (x + 0.065, 0.065, 2.64), 0.01)
        p.add(M["iron"], K.box, (x - 0.1, -0.1, 0), (x + 0.1, 0.1, 0.02), 0.005)
    p.build("StringLights_Posts", col, root, smooth_angle=50)

    w = K.Part()
    x0 = span - 0.05

    def wire_z(x):
        return top - sag * (1 - (x / x0) ** 2)

    pts = [Vector((-x0 + 2 * x0 * i / 30, 0, wire_z(-x0 + 2 * x0 * i / 30))) for i in range(31)]
    for a, b in zip(pts, pts[1:]):
        w.add(M["iron"], K.capsule, a, b, 0.005, 6, 3)
    for i in range(7):
        x = -1.2 + i * 0.4
        z = wire_z(x)
        w.add(M["iron"], K.cyl, (x, 0, z - 0.03), 0.012, 0.035, "Z", 12)
        w.add(M["bulb"], K.sphere, (x, 0, z - 0.075), (0.028, 0.028, 0.038), 16, 10)
    return w.build("StringLights_Wire", col, root, smooth_angle=60)


PROPS = [
    ("Prop_Bench", bench, 1.6),
    ("Prop_MenuBoard", menu_board, 0.8),
    ("Prop_Lantern", lantern, 0.6),
    ("Prop_Surfboard", surfboard, 0.8),
    ("Prop_Planter", planter, 1.1),
    ("Prop_Crate", crate, 0.8),
    ("Prop_Bollard", bollard, 0.5),
    ("Prop_TrafficCone", cone, 0.6),
    ("Prop_StringLights", string_lights, 3.4),
]


def main():
    K.reset_scene()
    M = materials()
    col = K.collection("Props")
    roots = []
    x = 0.0
    for name, fn, width in PROPS:
        root = K.empty(name, col, size=0.3, kind="ARROWS")
        fn(M, col, root)
        roots.append((root, width))
    total = sum(w for _, w in roots) + 0.3 * (len(roots) - 1)
    x = -total / 2
    for root, width in roots:
        root.location.x = x + width / 2
        x += width + 0.3
    lan = bpy.data.objects["Prop_Lantern"]
    lan.location.z = 1.3

    stage = K.setup_stage(ground_color=(0.6, 0.58, 0.54))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "props.blend"))
    if "--fbx" in ARGS:
        for root, _ in roots:
            K.export_fbx(root, os.path.join(K.UNITY_MODELS, "Props", root.name + ".fbx"))
    if "--render" in ARGS:
        out = os.path.join(HERE, "renders")
        K.render(K.camera("Cam_All", stage, (0, -14.5, 4.5), (0, 0, 0.9), lens=40),
                 os.path.join(out, "props_lineup.png"), res=(2000, 800))
        mid = bpy.data.objects["Prop_MenuBoard"].location.x
        K.render(K.camera("Cam_Close", stage, (mid + 0.4, -3.6, 1.6), (mid + 0.4, 0, 0.75), lens=40),
                 os.path.join(out, "props_closeup.png"), res=(1600, 900))


main()
