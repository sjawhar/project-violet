"""THROWAWAY Phase 1 bake-off: renders all sixteen desert-kit pieces as a side-scroller camera 32 m away sees them.

    blender -b --factory-startup --python assets/bakeoff/desert-kit-3d/preview/render_scene.py -- KIT_DIR OUT_PNG

KIT_DIR holds the GLBs that build_kit.py writes. The frame is 1920x1080 and 30 m wide at the tile row, which is
the lanes' 30 x 17 tile view. The render uses Cycles on the CPU.
"""

import math
import sys
from pathlib import Path

import bpy

SKY_HORIZON, SKY_TOP = "f2c49b", "3f7f8c"  # the brief's sky, peach to teal


def srgb_to_linear(hex_color):
    def channel(c):
        c = c / 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    return tuple(channel(int(hex_color[i : i + 2], 16)) for i in (0, 2, 4)) + (1.0,)


def place(kit, name, x, y, z=0.0, turn=0.0):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(kit / f"{name}.glb"))
    for obj in set(bpy.data.objects) - before:
        if obj.parent is None:
            obj.location = (x, y, z)
            obj.rotation_euler[2] = turn


def main():
    args = sys.argv[sys.argv.index("--") + 1 :]
    kit, out = Path(args[0]), Path(args[1])
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene

    # the playfield: a sand-topped ground of rock tiles, one tile deep, and the cell pieces on it
    for x in range(-17, 18):
        place(kit, "sand-tile", x, 0, -1)
        for z in (-2, -3, -4, -5):
            place(kit, "rock-tile", x, 0, z)
    for x in range(3, 7):
        for z in (0, 1):
            place(kit, "rock-tile", x, 0, z)
    for x in (-6, -5):
        place(kit, "tag-block", x, 0, 0)
    for x in (-4, -3):
        place(kit, "tag-block", x, 0, 2)
    place(kit, "hazard-spikes", -1, 0)
    place(kit, "hazard-spikes", 0, 0)
    place(kit, "orb-pedestal", -9, 0)
    place(kit, "goal-gate", 10, 0)

    # props just behind the playfield, and the background
    place(kit, "boulder-a", 1.8, 2.5)
    place(kit, "saguaro", -12, 4)
    place(kit, "acacia", 14, 6)
    place(kit, "ruin-column", -14.5, 3)
    place(kit, "ruin-wall", 7, 5)
    place(kit, "boulder-b", -7, 6)
    place(kit, "dune-ridge", -8, 22, -0.5)
    place(kit, "dune-ridge", 25, 35, -0.5)
    place(kit, "mesa-small", 12, 30)
    place(kit, "arch", -16, 40)
    place(kit, "mesa-large", 18, 70)
    place(kit, "mesa-large", -40, 90, turn=2.5)

    bpy.ops.mesh.primitive_plane_add(size=400, location=(0, 200.5, 0))  # desert floor behind the playfield
    floor = bpy.context.object
    floor_mat = bpy.data.materials.new("floor")
    floor_mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = srgb_to_linear("d9b27c")
    floor_mat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 1.0
    floor.data.materials.append(floor_mat)

    world = bpy.data.worlds.new("sky")
    tree = world.node_tree
    coords = tree.nodes.new("ShaderNodeTexCoord")
    split = tree.nodes.new("ShaderNodeSeparateXYZ")
    ramp = tree.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position, ramp.color_ramp.elements[0].color = 0.45, srgb_to_linear(SKY_HORIZON)
    ramp.color_ramp.elements[1].position, ramp.color_ramp.elements[1].color = 1.0, srgb_to_linear(SKY_TOP)
    tree.links.new(coords.outputs["Window"], split.inputs[0])
    tree.links.new(split.outputs["Y"], ramp.inputs[0])
    tree.links.new(ramp.outputs[0], tree.nodes["Background"].inputs["Color"])
    tree.nodes["Background"].inputs["Strength"].default_value = 0.9
    scene.world = world

    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
    sun.data.energy = 3.0
    sun.data.color = (1.0, 0.85, 0.7)
    sun.rotation_euler = (math.radians(60), 0.0, math.radians(40))
    scene.collection.objects.link(sun)

    camera = bpy.data.objects.new("camera", bpy.data.cameras.new("camera"))
    scene.collection.objects.link(camera)
    scene.camera = camera
    camera.location = (0.0, -32.0, 3.5)
    camera.rotation_euler = (math.radians(90), 0.0, 0.0)
    camera.data.sensor_fit = "HORIZONTAL"
    camera.data.angle = 2 * math.atan(15 / 32)  # 30 m wide at the tile row
    camera.data.clip_end = 1000

    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 64
    scene.cycles.seed = 0
    scene.render.resolution_x, scene.render.resolution_y = 1920, 1080
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(out)
    bpy.ops.render.render(write_still=True)


main()
