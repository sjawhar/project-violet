"""THROWAWAY (lane G-A): writes placeholder.reference.json, every slot's placement in every frame `spinerig render`
draws for placeholder.rig.json, from render.py's own functions (the reference implementation of
docs/bakeoff/character-rig.md). tests/rig_test.gd checks Rig.pose against it. Run by make-fixture.sh:
uv run --project <spinerig with render.py> python reference_poses.py SKELETON.json OUT.json"""

import json
import math
import sys
from pathlib import Path

from spinerig import render

FPS = 30  # spinerig render's default --fps

spine = json.loads(Path(sys.argv[1]).read_text())
skin = spine["skins"][0]["attachments"]
animations = {}
for name, animation in spine["animations"].items():
    frames = []
    for i in range(max(1, round(render.animation_duration(animation) * FPS))):
        world = render.bone_world_transforms(spine["bones"], animation, i / FPS)
        frame = []
        for slot in spine["slots"]:
            # render.render_frame's placement: the bone's world transform applied to the attachment's x/y.
            bone, att = world[slot["bone"]], skin[slot["name"]][slot["attachment"]]
            cos_b, sin_b = math.cos(math.radians(bone.rotation)), math.sin(math.radians(bone.rotation))
            frame.append([
                round(bone.x + att["x"] * cos_b - att["y"] * sin_b, 5),
                round(bone.y + att["x"] * sin_b + att["y"] * cos_b, 5),
                round(bone.rotation + att["rotation"], 5),
            ])
        frames.append(frame)
    animations[name] = frames
out = {"fps": FPS, "slots": [slot["name"] for slot in spine["slots"]], "animations": animations}
Path(sys.argv[2]).write_text(json.dumps(out, separators=(",", ":")) + "\n")
