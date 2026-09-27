"""Render a turntable of one 3D model. Runs inside Blender, not in the preview tool's Python:

    blender -b --factory-startup --python-exit-code 1 --python turntable.py -- \
        MODEL OUTDIR SECONDS FPS SIZE SAMPLES DEVICE
    blender -b --factory-startup --python-exit-code 1 --python turntable.py -- --probe

The first writes OUTDIR/000001.png, 000002.png, ... (SECONDS * FPS frames) of a camera orbiting the model once,
with Cycles, on DEVICE (optix, cuda, or cpu). The second prints `preview-probe: optix|cuda|cpu`, the best backend
that has a device, so the caller can time out a probe that hangs in the GPU driver.
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


def bounds(model: Path) -> tuple[Vector, float]:
    """Centre and radius of what renders: evaluated instances (collection instances included) of visible,
    renderable geometry; excluded collections are absent from the depsgraph."""
    depsgraph = bpy.context.evaluated_depsgraph_get()
    corners = []
    for instance in depsgraph.object_instances:
        obj = instance.object
        if obj.type not in GEOMETRY or obj.original.hide_render:
            continue
        corners += [instance.matrix_world @ Vector(corner) for corner in obj.bound_box]
    if not corners:
        raise RuntimeError(f"{model}: no renderable geometry")
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

    world = bpy.data.worlds.new("preview_world")  # never the file's own world, whose nodes may be anything
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.11, 0.11, 0.13, 1.0)
    scene.world = world

    bpy.context.preferences.edit.keyframe_new_interpolation_type = "LINEAR"
    scene.frame_start, scene.frame_end, scene.frame_step = 1, frames, 1
    pivot.rotation_euler = (0.0, 0.0, 0.0)
    pivot.keyframe_insert("rotation_euler", index=2, frame=1)
    pivot.rotation_euler = (0.0, 0.0, 2 * math.pi)
    pivot.keyframe_insert("rotation_euler", index=2, frame=frames + 1)


def available_backend() -> str:
    preferences = bpy.context.preferences.addons["cycles"].preferences
    for kind in ("OPTIX", "CUDA"):
        try:
            preferences.compute_device_type = kind
        except TypeError:
            continue
        preferences.refresh_devices()
        if any(d.type == kind for d in preferences.devices):
            return kind.lower()
    return "cpu"


def use_device(scene: bpy.types.Scene, device: str) -> str:
    if device == "cpu":
        scene.cycles.device = "CPU"
        return "CPU"
    kind = device.upper()
    preferences = bpy.context.preferences.addons["cycles"].preferences
    preferences.compute_device_type = kind
    preferences.refresh_devices()
    gpus = [d for d in preferences.devices if d.type == kind]
    if not gpus:
        raise RuntimeError(f"no {kind} device available")
    for d in preferences.devices:
        d.use = d.type == kind
    scene.cycles.device = "GPU"
    # The default denoiser runs on the CPU and dominated render time (about 21 CPU-seconds per 720px frame).
    scene.cycles.denoiser = "OPTIX" if kind == "OPTIX" else "OPENIMAGEDENOISE"
    scene.cycles.denoising_use_gpu = True
    return f"{kind} ({gpus[0].name})"


def render(argv: list[str]) -> None:
    model, outdir, seconds, fps, size, samples, device = argv
    model_path = Path(model)
    frames = round(float(seconds) * int(fps))
    scene = load(model_path)
    center, radius = bounds(model_path)
    rig(scene, center, radius, frames)

    render_settings = scene.render
    render_settings.engine = "CYCLES"
    render_settings.fps, render_settings.fps_base = int(fps), 1.0
    render_settings.resolution_x = render_settings.resolution_y = int(size)
    render_settings.resolution_percentage = 100
    render_settings.pixel_aspect_x = render_settings.pixel_aspect_y = 1.0
    render_settings.use_border = False
    render_settings.film_transparent = False
    render_settings.use_compositing = False
    render_settings.use_sequencer = False
    render_settings.use_persistent_data = True  # keep the scene and BVH between frames; only the camera moves
    render_settings.image_settings.file_format = "PNG"
    render_settings.image_settings.color_mode = "RGB"
    render_settings.filepath = str(Path(outdir) / "######")
    scene.cycles.samples = int(samples)
    scene.cycles.use_denoising = True
    used = use_device(scene, device)
    print(f"preview: rendered {frames} frames at {size}px on {used}", flush=True)
    bpy.ops.render.render(animation=True)


arguments = sys.argv[sys.argv.index("--") + 1 :]
if arguments == ["--probe"]:
    print(f"preview-probe: {available_backend()}", flush=True)
else:
    render(arguments)
