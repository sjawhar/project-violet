#!/usr/bin/env bash
# oryx only: loads the NVIDIA driver after a reboot, without switching graphics modes (which needs another reboot).
# system76-power's integrated mode blacklists nvidia at boot (/etc/modprobe.d/system76-power.conf aliases it to "off"),
# so this loads it through a copy of the modprobe config without that one file. nvidia_uvm then takes
# uvm_disable_hmm=1 from /etc/modprobe.d/nvidia-uvm.conf: the HMM path crashed the kernel on 2026-09-27.
# Idempotent. Needs sudo. Prove the result with scripts/oryx-gpu-check.sh.
set -euo pipefail
grep -qx 'options nvidia_uvm uvm_disable_hmm=1' /etc/modprobe.d/nvidia-uvm.conf ||
  { echo "oryx-gpu-load: /etc/modprobe.d/nvidia-uvm.conf must contain: options nvidia_uvm uvm_disable_hmm=1" >&2; exit 1; }
conf=$(mktemp -d)
trap 'rm -rf "$conf"' EXIT
for dir in /lib/modprobe.d /usr/lib/modprobe.d /usr/local/lib/modprobe.d /run/modprobe.d /etc/modprobe.d; do
  [ -d "$dir" ] || continue
  for f in "$dir"/*.conf; do [ -e "$f" ] && cp -f "$f" "$conf"/; done
done
rm -f "$conf/system76-power.conf"
sudo modprobe -C "$conf" nvidia
sudo modprobe -C "$conf" nvidia_uvm
echo "oryx-gpu-load: nvidia loaded, uvm_disable_hmm=$(cat /sys/module/nvidia_uvm/parameters/uvm_disable_hmm)"
