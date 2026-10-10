# Builds the hero model: a low-poly hex island with a map pin, exported to assets/hex-island.glb.
# Run: blender -b --python tools/hex_island.py
import math
import os
import random

import bpy

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "hex-island.glb")
random.seed(7)  # deterministic island

bpy.ops.wm.read_factory_settings(use_empty=True)

mats = {}
def mat(name, hex_color, rough=0.85):
    if name in mats:
        return mats[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    r, g, b = (int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5))
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (r ** 2.2, g ** 2.2, b ** 2.2, 1)  # sRGB -> linear
    bsdf.inputs["Roughness"].default_value = rough
    mats[name] = m
    return m

def add(obj_op, material, **kw):
    obj_op(**kw)
    o = bpy.context.active_object
    o.data.materials.append(material)
    return o

# terrain by ring distance from center, with a little randomness
TILES = {
    "water": ("#67e8f9", 0.3),
    "sand":  ("#f1dfa8", 0.55),
    "grass": ("#5fbf5f", 0.85),
    "hill":  ("#3f8f4a", 1.35),
    "rock":  ("#cbd5e1", 2.0),
}
RADIUS = 2
tiles = []
for q in range(-RADIUS, RADIUS + 1):
    for r in range(max(-RADIUS, -q - RADIUS), min(RADIUS, -q + RADIUS) + 1):
        ring = max(abs(q), abs(r), abs(q + r))
        if ring == 2:
            kind = random.choice(["water", "water", "sand", "grass"])
        elif ring == 1:
            kind = random.choice(["grass", "grass", "hill", "sand"])
        else:
            kind = "grass"
        tiles.append((q, r, kind))
# guarantee one rocky peak next to the pin tile
tiles = [(q, r, "rock" if (q, r) == (1, -1) else k) for q, r, k in tiles]

SIZE = 1.0
for q, r, kind in tiles:
    color, h = TILES[kind]
    x = 1.5 * q * SIZE
    y = math.sqrt(3) * (r + q / 2) * SIZE
    t = add(bpy.ops.mesh.primitive_cylinder_add, mat(kind, color), vertices=6, radius=SIZE * 0.96, depth=h,
            location=(x, y, h / 2))
    # a few low-poly trees on grass and hill tiles
    if kind in ("grass", "hill") and (q, r) != (0, 0) and random.random() < 0.5:
        add(bpy.ops.mesh.primitive_cylinder_add, mat("trunk", "#7c5a3a"), vertices=6, radius=0.06, depth=0.25,
            location=(x + 0.25, y - 0.2, h + 0.12))
        add(bpy.ops.mesh.primitive_cone_add, mat("leaf", "#2f7d3a"), vertices=6, radius1=0.28, depth=0.6,
            location=(x + 0.25, y - 0.2, h + 0.5))

# the map pin on the center tile: cone pointing down + head sphere + white dot
top = TILES["grass"][1]
pin = mat("pin", "#2563eb", 0.4)
add(bpy.ops.mesh.primitive_cone_add, pin, vertices=24, radius1=0.45, depth=1.4,
    location=(0, 0, top + 0.7), rotation=(math.pi, 0, 0))
add(bpy.ops.mesh.primitive_uv_sphere_add, pin, segments=24, ring_count=12, radius=0.6, location=(0, 0, top + 1.6))
add(bpy.ops.mesh.primitive_uv_sphere_add, mat("dot", "#ffffff", 0.3), segments=16, ring_count=8, radius=0.24,
    location=(0, -0.5, top + 1.63))

os.makedirs(os.path.dirname(OUT), exist_ok=True)
bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", export_apply=True)
print("WROTE", OUT, os.path.getsize(OUT), "bytes")
