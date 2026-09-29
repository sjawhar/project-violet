#!/usr/bin/env bash
# oryx only: proves the RTX 3070 is usable before a GPU job. GPU jobs run one at a time: flock /tmp/oryx-gpu.lock <cmd>.
set -euo pipefail
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader | grep -q "RTX 3070" || { echo "no RTX 3070 in nvidia-smi" >&2; exit 1; }
# sysfs prints a bool module parameter as Y or N.
[ "$(cat /sys/module/nvidia_uvm/parameters/uvm_disable_hmm 2>/dev/null)" = "Y" ] || { echo "nvidia_uvm is not loaded with uvm_disable_hmm=1" >&2; exit 1; }
# CUDA smoke: a real CUDA process (Cycles) that allocates on the device and exits. The exit path is what crashed before.
since=$(date '+%Y-%m-%d %H:%M:%S')
rm -f /tmp/oryx-gpu-smoke.png
flock /tmp/oryx-gpu.lock blender --background --factory-startup --python-exit-code 1 --python-expr "
import bpy; p=bpy.context.preferences.addons['cycles'].preferences; p.compute_device_type='CUDA'; p.get_devices()
cuda=[d for d in p.devices if d.type == 'CUDA']
assert cuda, 'Cycles found no CUDA device'
for d in p.devices: d.use = d.type == 'CUDA'
s=bpy.context.scene; s.render.engine='CYCLES'; s.cycles.device='GPU'; s.cycles.samples=8; s.render.resolution_percentage=10
s.render.filepath='/tmp/oryx-gpu-smoke.png'; bpy.ops.render.render(write_still=True)"
test -s /tmp/oryx-gpu-smoke.png
# Read the log first: if journalctl can't read it, set -e stops here instead of reading "no fault".
klog=$(journalctl -k --since "$since" --no-pager)
if grep -qiE 'BUG:|Oops|nvidia_uvm.*fault|recursive fault' <<<"$klog"; then
  echo "kernel fault after the CUDA process exited" >&2; exit 1
fi
echo "oryx GPU OK"
