"""Render a turntable of one 3D model. Runs inside Blender, not in the preview tool's Python:

    blender -b --factory-startup --python-exit-code 1 --python turntable.py -- \
        MODEL OUTDIR SECONDS FPS SIZE SAMPLES DEVICE

Writes OUTDIR/000001.png, 000002.png, ... (SECONDS * FPS frames) of a camera orbiting the model once,
with Cycles. DEVICE is auto (OptiX, then CUDA, then CPU), optix, cuda, or cpu.
"""

import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

GEOMETRY = {"MESH", "CURVE", "SURFACE", "META", "FONT"}


def load(model: Path) -> bpy.types.Scene:
    extension = model.suffix.lower()
    if extension == ".blend":
        bpy.ops.wm.open_mainfile(filepath=str(model))
        return bpy.context.scene
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if extension in (".glb", ".gltf"):
        bpy.ops.import_scene.gltf(filepath=str(model))
    elif extension == ".fbx":
        bpy.ops.import_scene.fbx(filepath=str(model))
    else:
        raise RuntimeError(f"{model}: unsupported model type {extension}")
    return bpy.context.scene


def bounds(scene: bpy.types.Scene, model: Path) -> tuple[Vector, float]:
    geometry = [obj for obj in scene.objects if obj.type in GEOMETRY and not obj.hide_render]
    if not geometry:
        raise RuntimeError(f"{model}: no renderable geometry")
    corners = [obj.matrix_world @ Vector(corner) for obj in geometry for corner in obj.bound_box]
    low = Vector(min(c[i] for c in corners) for i in range(3))
    high = Vector(max(c[i] for c in corners) for i in range(3))
    return (low + high) / 2, max((high - low).length / 2, 1e-3)


def rig(scene: bpy.types.Scene, center: Vector, radius: float, frames: int) -> None:
    """A camera and key light on a pivot at the model's centre; the pivot turns once over the frames."""
    pivot = bpy.data.objects.new("preview_pivot", None)
    scene.collection.objects.link(pivot)
    pivot.location = center

    camera_data = bpy.data.cameras.new("preview_camera")
    camera = bpy.data.objects.new("preview_camera", camera_data)
    scene.collection.objects.link(camera)
    camera.parent = pivot
    distance = radius / math.sin(camera_data.angle / 2) * 1.1
    elevation = math.radians(20)
    camera.location = (0.0, -distance * math.cos(elevation), distance * math.sin(elevation))
    camera_data.clip_start = distance / 1000
    camera_data.clip_end = distance * 10
    aim = camera.constraints.new("TRACK_TO")
    aim.target = pivot
    aim.track_axis = "TRACK_NEGATIVE_Z"
    aim.up_axis = "UP_Y"
    scene.camera = camera

    key = bpy.data.objects.new("preview_key", bpy.data.lights.new("preview_key", "SUN"))
    key.data.energy = 3.0
    scene.collection.objects.link(key)
    key.parent = pivot
    key.rotation_euler = (math.radians(50), 0.0, math.radians(-30))

    world = scene.world or bpy.data.worlds.new("preview_world")
    scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.11, 0.11, 0.13, 1.0)

    bpy.context.preferences.edit.keyframe_new_interpolation_type = "LINEAR"
    scene.frame_start, scene.frame_end = 1, frames
    pivot.rotation_euler = (0.0, 0.0, 0.0)
    pivot.keyframe_insert("rotation_euler", index=2, frame=1)
    pivot.rotation_euler = (0.0, 0.0, 2 * math.pi)
    pivot.keyframe_insert("rotation_euler", index=2, frame=frames + 1)


def choose_device(scene: bpy.types.Scene, device: str) -> str:
    preferences = bpy.context.preferences.addons["cycles"].preferences
    for kind in {"auto": ["OPTIX", "CUDA"], "optix": ["OPTIX"], "cuda": ["CUDA"], "cpu": []}[device]:
        try:
            preferences.compute_device_type = kind
        except TypeError:
            continue
        preferences.refresh_devices()
        gpus = [d for d in preferences.devices if d.type == kind]
        if gpus:
            for d in preferences.devices:
                d.use = d.type == kind
            scene.cycles.device = "GPU"
            # The default denoiser runs on the CPU and dominated render time (about 21 CPU-seconds per 720px frame).
            scene.cycles.denoiser = "OPTIX" if kind == "OPTIX" else "OPENIMAGEDENOISE"
            scene.cycles.denoising_use_gpu = True
            return f"{kind} ({gpus[0].name})"
    if device in ("optix", "cuda"):
        raise RuntimeError(f"no {device.upper()} device available")
    scene.cycles.device = "CPU"
    return "CPU"


def main(argv: list[str]) -> None:
    model, outdir, seconds, fps, size, samples, device = argv
    model_path = Path(model)
    frames = round(float(seconds) * int(fps))
    scene = load(model_path)
    center, radius = bounds(scene, model_path)
    rig(scene, center, radius, frames)

    scene.render.engine = "CYCLES"
    scene.cycles.samples = int(samples)
    scene.cycles.use_denoising = True
    scene.render.use_persistent_data = True  # keep the scene and BVH between frames; only the camera moves
    scene.render.fps = int(fps)
    scene.render.resolution_x = scene.render.resolution_y = int(size)
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = False
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.filepath = str(Path(outdir) / "######")
    used = choose_device(scene, device)
    print(f"preview: rendered {frames} frames at {size}px on {used}", flush=True)
    bpy.ops.render.render(animation=True)


main(sys.argv[sys.argv.index("--") + 1 :])
