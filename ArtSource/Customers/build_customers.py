"""
Chibi customer models.

Run from this folder:
  /Applications/Blender.app/Contents/MacOS/Blender --background --python build_customers.py -- [--fbx] [--render]

--fbx writes one model per customer to Assets/Models/Customers/<Name>.fbx.
Each customer is a root empty with Body, Head, Arm_L/R and Leg_L/R children. Head pivots at the
neck, arms at the shoulders and legs at the hips, so Unity can swing them for a simple walk.
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402
import blender_kit as K  # noqa: E402

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

HEAD_C = Vector((0, 0, 1.06))
HEAD_R = (0.20, 0.185, 0.19)
NECK = (0, 0, 0.84)
SHOULDER_X, SHOULDER_Z = 0.155, 0.775
HIP_X, HIP_Z = 0.07, 0.50
TORSO_HALF_W, TORSO_HALF_D = 0.135, 0.097

SKIN = {"light": (0.93, 0.74, 0.60), "tan": (0.80, 0.56, 0.40), "deep": (0.55, 0.36, 0.24)}
HAIR = {"black": (0.035, 0.03, 0.03), "brown": (0.2, 0.11, 0.05), "dark": (0.09, 0.055, 0.04)}

ARM_POSES = {
    "down": ((0.20, 0.0, 0.62), (0.215, -0.01, 0.48)),
    "hold": ((0.20, 0.02, 0.62), (0.165, -0.13, 0.62)),
    "strap": ((0.21, 0.0, 0.63), (0.11, -0.12, 0.73)),
    "point": ((0.20, -0.12, 0.79), (0.22, -0.26, 0.9)),
}


def m(name, color, **kw):
    return K.mat(name, color, **kw)


def face_point(x, z, out=0.0):
    """Point on the front of the head ellipsoid, pushed out along its normal."""
    rx, ry, rz = HEAD_R
    dz = z - HEAD_C.z
    y = -ry * math.sqrt(max(1 - (x / rx) ** 2 - (dz / rz) ** 2, 0.0))
    n = Vector((x / rx ** 2, y / ry ** 2, dz / rz ** 2)).normalized()
    return Vector((x, y, z)) + n * out


def shell(bm, center, radii, keep):
    """Sphere with faces removed where keep(local_center) is False (hair caps, hat domes)."""
    verts = K.sphere(bm, center, radii, segs=32, rings=16)
    faces = list({f for v in verts for f in v.link_faces})
    c = Vector(center)
    drop = [f for f in faces if not keep(f.calc_center_median() - c)]

    bmesh.ops.delete(bm, geom=drop, context="FACES")
    return [v for v in verts if v.is_valid]


# ---------------------------------------------------------------- head
def build_head(c, col, root):
    p = K.Part()
    skin = m(f"Skin_{c['skin']}", SKIN[c["skin"]], rough=0.55)
    hair = m(f"Hair_{c['hair_color']}", HAIR[c["hair_color"]], rough=0.45)
    ink = m("Face_Ink", (0.03, 0.025, 0.03), rough=0.3)
    white = m("Face_Highlight", (1, 1, 1), rough=0.2)
    blush = m("Face_Blush", (0.95, 0.5, 0.48), rough=0.6)
    lip = m("Face_Mouth", (0.45, 0.12, 0.1), rough=0.5)

    p.add(skin, K.sphere, HEAD_C, HEAD_R, 32, 16)
    p.add(skin, K.sphere, face_point(0, 1.02, -0.004), (0.016, 0.014, 0.014), 12, 6)
    for s in (-1, 1):
        p.add(skin, K.sphere, (s * 0.195, 0.01, 1.04), (0.03, 0.025, 0.042), 12, 8)
        p.add(ink, K.sphere, face_point(s * 0.072, 1.05, -0.006), (0.026, 0.014, 0.036), 16, 8)
        p.add(white, K.sphere, face_point(s * 0.072 - 0.008, 1.062, 0.006), 0.009, 8, 6)
        p.add(hair, K.capsule, face_point(s * 0.045, 1.112, 0.002), face_point(s * 0.1, 1.106, 0.002), 0.008, 8, 5)
        p.add(blush, K.sphere, face_point(s * 0.118, 1.0, 0.0), (0.03, 0.006, 0.017), 12, 6)
    a, b, cc = face_point(-0.022, 0.99, 0.002), face_point(0, 0.984, 0.002), face_point(0.022, 0.99, 0.002)
    p.add(lip, K.capsule, a, b, 0.0065, 8, 5)
    p.add(lip, K.capsule, b, cc, 0.0065, 8, 5)

    ry = HEAD_R[1] * 1.07

    def cap_keep(front, back):
        return lambda d: d.z > front + (back - front) * ((d.y / ry + 1) / 2)

    hc = HEAD_C + Vector((0, 0.008, 0.012))
    hr = tuple(r * 1.07 for r in HEAD_R)
    style = c["hair"]
    if style == "short":
        p.add(hair, shell, hc, hr, cap_keep(0.075, -0.19))
        for x in (-0.07, 0.0, 0.07):
            p.add(hair, K.sphere, face_point(x, 1.17, 0.012), (0.05, 0.03, 0.035), 12, 6)
    elif style == "long":
        p.add(hair, shell, hc, hr, cap_keep(0.085, -0.12))
        p.add(hair, K.box, (-0.17, 0.0, 0.82), (0.17, 0.17, 1.1), 0.07, 3)
        for s in (-1, 1):
            p.add(hair, K.capsule, (s * 0.175, -0.03, 1.1), (s * 0.165, -0.0, 0.86), 0.042, 12, 7)
    elif style == "bun":
        p.add(hair, shell, hc, hr, cap_keep(0.08, -0.18))
        p.add(hair, K.sphere, (0, 0.1, 1.27), 0.078, 16, 10)
    elif style == "under_hat":
        p.add(hair, shell, hc, hr, cap_keep(0.03, -0.19))

    hat = c.get("hat")
    if hat:
        hat_mat = m(f"Hat_{hat[0]}_{hat[1]}", hat[1], rough=0.7)
        trim = m(f"HatTrim_{hat[0]}_{hat[2]}", hat[2], rough=0.6)
        kind = hat[0]
        if kind == "cap":
            dome = tuple(r * 1.1 for r in HEAD_R)
            p.add(hat_mat, shell, HEAD_C + Vector((0, 0.005, 0.02)), dome, lambda d: d.z > 0.035)
            p.add(trim, K.box, (-0.13, -0.33, 1.1), (0.13, -0.13, 1.117), 0.06, 3)
            p.add(trim, K.sphere, HEAD_C + Vector((0, 0.005, 0.23)), 0.017, 10, 6)
        else:
            tall = 0.19 if kind == "bucket" else 0.18
            p.add(hat_mat, shell, (0, 0.0, 1.12), (0.21, 0.2, tall), lambda d: d.z > 0)
            p.add(trim, K.cyl, (0, 0, 1.14), 0.212, 0.035, "Z", 32)
            if kind == "sunhat":
                p.add(hat_mat, K.cyl, (0, 0, 1.115), 0.35, 0.025, "Z", 40, 0.21)
            else:
                p.add(hat_mat, K.cyl, (0, 0, 1.1), 0.28, 0.06, "Z", 32, 0.205)

    eyes = c.get("eyewear")
    frame = m("Glasses_Frame", (0.03, 0.03, 0.035), rough=0.3)
    if eyes == "sunglasses":
        lens = m("Sunglass_Lens", (0.02, 0.02, 0.025), rough=0.05, coat=1.0)
        for s in (-1, 1):
            p.add(lens, K.sphere, face_point(s * 0.074, 1.05, 0.012), (0.05, 0.012, 0.036), 16, 8)
            p.add(frame, K.capsule, face_point(s * 0.12, 1.07, 0.01), (s * 0.19, 0.02, 1.07), 0.006, 6, 5)
        p.add(frame, K.capsule, face_point(-0.03, 1.065, 0.014), face_point(0.03, 1.065, 0.014), 0.007, 6, 5)
    elif eyes == "glasses":
        for s in (-1, 1):
            p.add(frame, K.torus, face_point(s * 0.074, 1.05, 0.014), 0.042, 0.0055, "Y", 24, 6)
            p.add(frame, K.capsule, face_point(s * 0.115, 1.06, 0.01), (s * 0.19, 0.02, 1.06), 0.005, 6, 5)
        p.add(frame, K.capsule, face_point(-0.033, 1.06, 0.016), face_point(0.033, 1.06, 0.016), 0.005, 6, 5)

    if c.get("headphones"):
        hp = m("Headphones", (0.06, 0.06, 0.07), rough=0.4)
        p.add(hp, K.torus, HEAD_C + Vector((0, 0.01, 0.0)), 0.222, 0.017, "Y", 40, 8, math.pi, math.pi)
        for s in (-1, 1):
            p.add(hp, K.cyl, (s * 0.21, 0.01, 1.04), 0.06, 0.05, "X", 24)

    return p.build("Head", col, root, pivot=NECK, smooth_angle=60)


# ---------------------------------------------------------------- body
def build_body(c, col, root):
    p = K.Part()
    skin = m(f"Skin_{c['skin']}", SKIN[c["skin"]], rough=0.55)
    top = m(f"Top_{c['name']}", c["top_color"], rough=0.75)
    bottom = m(f"Bottom_{c['name']}", c["bottom_color"], rough=0.75)

    p.add(top, K.capsule, (0, 0, 0.6), (0, 0, 0.73), TORSO_HALF_W, 20, 11, (1, 0.72))
    p.add(skin, K.cyl, (0, 0, 0.83), 0.045, 0.08, "Z", 16)
    if c["bottom"] in ("skirt", "dress"):
        skirt = top if c["bottom"] == "dress" else bottom
        p.add(skirt, K.cyl, (0, 0, 0.44), 0.2, 0.24, "Z", 28, 0.13)
        p.add(skirt, K.capsule, (0, 0, 0.55), (0, 0, 0.56), 0.13, 20, 9, (1, 0.74))
    else:
        p.add(bottom, K.capsule, (0, 0, 0.52), (0, 0, 0.56), 0.117, 20, 9, (1, 0.7))

    if c["top"] == "aloha":
        flower = m("Aloha_Flower", (0.95, 0.55, 0.15), rough=0.6)
        leaf = m("Aloha_Leaf", (0.25, 0.55, 0.45), rough=0.6)
        rng = random.Random(7)
        for i in range(22):
            th = math.radians(rng.uniform(-105, 105)) + (math.pi if i % 3 == 0 else 0)
            z = rng.uniform(0.56, 0.78)
            n = Vector((math.sin(th) / TORSO_HALF_W, -math.cos(th) / TORSO_HALF_D, 0)).normalized()
            pos = Vector((TORSO_HALF_W * math.sin(th), -TORSO_HALF_D * math.cos(th), z)) + n * 0.004
            p.add(flower if i % 2 else leaf, K.oriented_disc, pos, n, (0.022, 0.016, 0.005))
        for s in (-1, 1):
            p.add(top, K.oriented_disc, Vector((s * 0.035, -0.085, 0.8)), Vector((s * 0.4, -1, 0.6)), (0.04, 0.028, 0.008))
    elif c["top"] == "hoodie":
        cord = m("Hoodie_Cord", (0.9, 0.9, 0.88), rough=0.6)
        p.add(top, K.torus, (0, 0.035, 0.83), 0.095, 0.04, "Z", 24, 10)
        p.add(top, K.box, (-0.08, -0.108, 0.55), (0.08, -0.09, 0.63), 0.01, 2)
        for s in (-1, 1):
            p.add(cord, K.capsule, (s * 0.03, -0.1, 0.8), (s * 0.032, -0.105, 0.7), 0.006, 6, 5)
    elif c["top"] == "tank":
        for s in (-1, 1):
            p.add(skin, K.sphere, (s * 0.12, 0.0, 0.765), (0.05, 0.06, 0.045), 12, 8)

    bag = c.get("backpack")
    if bag:
        pack = m(f"Backpack_{c['name']}", bag, rough=0.7)
        strap = m("Strap_Dark", (0.08, 0.08, 0.09), rough=0.7)
        p.add(pack, K.box, (-0.12, 0.08, 0.5), (0.12, 0.22, 0.83), 0.045, 3)
        p.add(pack, K.box, (-0.085, 0.2, 0.53), (0.085, 0.25, 0.66), 0.025, 2)
        for s in (-1, 1):
            p.add(strap, K.capsule, (s * 0.075, -0.1, 0.8), (s * 0.085, -0.105, 0.57), 0.017, 8, 5)
            p.add(strap, K.capsule, (s * 0.075, -0.095, 0.805), (s * 0.075, 0.09, 0.82), 0.017, 8, 5)
    tote = c.get("tote")
    if tote:
        canvas = m(f"Tote_{c['name']}", tote, rough=0.8)
        p.add(canvas, K.box, (0.2, -0.1, 0.36), (0.26, 0.1, 0.58), 0.02, 2)
        for y in (-0.05, 0.05):
            p.add(canvas, K.capsule, (0.23, y, 0.58), (0.13, y * 0.6, 0.8), 0.012, 6, 5)
    if c.get("camera"):
        black = m("Camera_Body", (0.05, 0.05, 0.055), rough=0.35)
        glass = m("Camera_Lens", (0.2, 0.3, 0.4), rough=0.05, metal=0.5)
        p.add(black, K.box, (-0.06, -0.15, 0.6), (0.06, -0.1, 0.67), 0.012, 2)
        p.add(black, K.cyl, (0.0, -0.17, 0.635), 0.026, 0.04, "Y", 16)
        p.add(glass, K.cyl, (0.0, -0.19, 0.635), 0.019, 0.004, "Y", 16)
        p.add(black, K.capsule, (-0.06, -0.12, 0.66), (-0.1, -0.05, 0.8), 0.007, 6, 5)
        p.add(black, K.capsule, (0.06, -0.12, 0.66), (0.1, -0.05, 0.8), 0.007, 6, 5)

    return p.build("Body", col, root, smooth_angle=60)


# ---------------------------------------------------------------- limbs
def build_arm(c, col, root, side):
    s = 1 if side == "R" else -1
    pose = c["arms"][side]
    elbow, hand = (Vector((s * x, y, z)) for x, y, z in ARM_POSES[pose])
    shoulder = Vector((s * SHOULDER_X, 0, SHOULDER_Z))
    p = K.Part()
    skin = m(f"Skin_{c['skin']}", SKIN[c["skin"]], rough=0.55)
    top = m(f"Top_{c['name']}", c["top_color"], rough=0.75)
    sleeve = c["top"] != "tank"
    long_sleeve = c["top"] == "hoodie"
    p.add(skin, K.capsule, shoulder, elbow, 0.04, 12, 7)
    p.add(top if long_sleeve else skin, K.capsule, elbow, hand, 0.037, 12, 7)
    if sleeve:
        p.add(top, K.capsule, shoulder, shoulder.lerp(elbow, 0.55 if not long_sleeve else 1.0), 0.05, 14, 7)
    p.add(skin, K.sphere, hand, 0.043, 14, 8)

    held = c.get("held", {}).get(side)
    if held == "drink":
        cup = m("Drink_MilkTea", (0.8, 0.62, 0.44), rough=0.25, coat=0.6)
        lid = m("Drink_Lid", (0.95, 0.95, 0.95), rough=0.3)
        straw = m("Drink_Straw", (0.1, 0.35, 0.3), rough=0.4)
        base = hand + Vector((0, -0.035, 0.0))
        p.add(cup, K.cyl, base + Vector((0, 0, 0.02)), 0.036, 0.12, "Z", 20, 0.044)
        p.add(lid, K.cyl, base + Vector((0, 0, 0.085)), 0.047, 0.012, "Z", 20)
        p.add(straw, K.capsule, base + Vector((0, 0, 0.08)), base + Vector((0.01, 0.0, 0.16)), 0.007, 6, 5)
    elif held == "phone":
        case = m("Phone_Case", (0.06, 0.06, 0.07), rough=0.3)
        screen = m("Phone_Screen", (0.35, 0.55, 0.75), rough=0.1, emit=0.4)
        p.add(case, K.box, hand + Vector((-0.035, -0.04, -0.01)), hand + Vector((0.035, -0.028, 0.12)), 0.006, 2)
        p.add(screen, K.box, hand + Vector((-0.03, -0.0415, 0.0)), hand + Vector((0.03, -0.039, 0.11)))
    return p.build(f"Arm_{side}", col, root, pivot=shoulder, smooth_angle=60)


def build_leg(c, col, root, side):
    s = 1 if side == "R" else -1
    hip = Vector((s * HIP_X, 0, HIP_Z))
    p = K.Part()
    skin = m(f"Skin_{c['skin']}", SKIN[c["skin"]], rough=0.55)
    bottom = m(f"Bottom_{c['name']}", c["bottom_color"], rough=0.75)
    shoe = m(f"Shoe_{c['shoes']}", c["shoes"], rough=0.6)
    sole = m("Shoe_Sole", (0.92, 0.91, 0.88), rough=0.7)

    ankle = Vector((s * HIP_X, 0, 0.09))
    p.add(skin, K.capsule, hip - Vector((0, 0, 0.03)), ankle, 0.043, 12, 7)
    if c["bottom"] == "shorts":
        p.add(bottom, K.capsule, hip, Vector((s * 0.072, 0, 0.35)), 0.056, 14, 7)
    elif c["bottom"] == "jeans":
        p.add(bottom, K.capsule, hip, Vector((s * HIP_X, 0, 0.11)), 0.058, 14, 9)
    x0, x1 = sorted((s * (HIP_X - 0.05), s * (HIP_X + 0.05)))
    p.add(shoe, K.box, (x0, -0.12, 0.012), (x1, 0.055, 0.08), 0.032, 3)
    p.add(sole, K.box, (x0 + 0.002, -0.118, 0.0), (x1 - 0.002, 0.053, 0.02), 0.008, 2)
    return p.build(f"Leg_{side}", col, root, pivot=hip, smooth_angle=60)


# ---------------------------------------------------------------- cast
CUSTOMERS = [
    dict(name="Customer_CapBackpack", skin="light", hair="under_hat", hair_color="brown",
         hat=("cap", (0.86, 0.86, 0.82), (0.16, 0.22, 0.34)), top="tee", top_color=(0.55, 0.6, 0.55),
         bottom="shorts", bottom_color=(0.17, 0.24, 0.38), shoes=(0.92, 0.92, 0.9), backpack=(0.2, 0.3, 0.22),
         arms={"L": "down", "R": "hold"}, held={"R": "drink"}),
    dict(name="Customer_SunHat", skin="light", hair="long", hair_color="dark",
         hat=("sunhat", (0.86, 0.73, 0.5), (0.35, 0.22, 0.12)), eyewear="sunglasses", top="tee",
         top_color=(0.96, 0.93, 0.86), bottom="dress", bottom_color=(0.96, 0.93, 0.86), shoes=(0.55, 0.35, 0.2),
         tote=(0.78, 0.6, 0.38), arms={"L": "hold", "R": "strap"}, held={"L": "drink"}),
    dict(name="Customer_Aloha", skin="tan", hair="short", hair_color="black", eyewear="sunglasses", top="aloha",
         top_color=(0.12, 0.17, 0.3), bottom="shorts", bottom_color=(0.72, 0.64, 0.46), shoes=(0.92, 0.92, 0.9),
         arms={"L": "down", "R": "hold"}, held={"R": "drink"}),
    dict(name="Customer_Bun", skin="light", hair="bun", hair_color="black", top="tee", top_color=(0.95, 0.95, 0.93),
         bottom="jeans", bottom_color=(0.26, 0.36, 0.55), shoes=(0.75, 0.75, 0.73), backpack=(0.62, 0.47, 0.32),
         arms={"L": "strap", "R": "hold"}, held={"R": "drink"}),
    dict(name="Customer_Kid", scale=0.8, skin="light", hair="under_hat", hair_color="brown",
         hat=("cap", (0.2, 0.4, 0.7), (0.15, 0.25, 0.5)), top="tee", top_color=(0.6, 0.62, 0.62), bottom="shorts",
         bottom_color=(0.25, 0.4, 0.6), shoes=(0.85, 0.3, 0.2), backpack=(0.9, 0.55, 0.2),
         arms={"L": "down", "R": "point"}),
    dict(name="Customer_Tote", skin="light", hair="bun", hair_color="dark", top="tank",
         top_color=(0.97, 0.96, 0.92), bottom="skirt", bottom_color=(0.3, 0.45, 0.68), shoes=(0.5, 0.33, 0.2),
         tote=(0.86, 0.79, 0.64), arms={"L": "down", "R": "strap"}),
    dict(name="Customer_Hiker", skin="tan", hair="under_hat", hair_color="black",
         hat=("bucket", (0.82, 0.76, 0.6), (0.4, 0.33, 0.22)), top="tee", top_color=(0.45, 0.5, 0.32),
         bottom="shorts", bottom_color=(0.3, 0.4, 0.52), shoes=(0.45, 0.38, 0.3), backpack=(0.42, 0.3, 0.2),
         camera=True, arms={"L": "strap", "R": "down"}),
    dict(name="Customer_Headphones", skin="light", hair="short", hair_color="black", eyewear="glasses",
         headphones=True, top="hoodie", top_color=(0.13, 0.16, 0.27), bottom="jeans",
         bottom_color=(0.36, 0.37, 0.39), shoes=(0.94, 0.94, 0.92), arms={"L": "down", "R": "hold"},
         held={"R": "phone"}),
]


def build_customer(c, col):
    root = K.empty(c["name"], col, size=0.3, kind="ARROWS")
    build_body(c, col, root)
    build_head(c, col, root)
    for side in ("L", "R"):
        build_arm(c, col, root, side)
        build_leg(c, col, root, side)
    s = c.get("scale", 1.0)
    if s != 1.0:
        for ch in root.children:
            ch.data.transform(Matrix.Scale(s, 4))
            ch.location *= s
    return root


def main():
    K.reset_scene()
    col = K.collection("Customers")
    spacing = 0.75
    roots = []
    for i, c in enumerate(CUSTOMERS):
        r = build_customer(c, col)
        r.location.x = (i - (len(CUSTOMERS) - 1) / 2) * spacing
        roots.append(r)

    stage = K.setup_stage(ground_color=(0.55, 0.54, 0.52))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "customers.blend"))
    if "--fbx" in ARGS:
        for r in roots:
            K.export_fbx(r, os.path.join(K.UNITY_MODELS, "Customers", r.name + ".fbx"))
    if "--render" in ARGS:
        out = os.path.join(HERE, "renders")
        K.render(K.camera("Cam_Lineup", stage, (0, -6.8, 2.0), (0, 0, 0.62), lens=42),
                 os.path.join(out, "customers_lineup.png"), res=(1800, 800))
        K.render(K.camera("Cam_Faces", stage, (roots[0].location.x + 0.9, -2.2, 1.25),
                          (roots[0].location.x + 0.9, 0, 0.85), lens=50),
                 os.path.join(out, "customers_closeup.png"), res=(1400, 900))
        K.render(K.camera("Cam_Back", stage, (1.5, 5.5, 2.0), (0, 0, 0.62), lens=42),
                 os.path.join(out, "customers_back.png"), res=(1800, 800))


main()
