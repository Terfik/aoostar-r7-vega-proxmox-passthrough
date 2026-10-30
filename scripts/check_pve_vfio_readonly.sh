#!/usr/bin/env bash
# Read-only check. No sudo, driver resets, disk mounts, VM starts, or writes.
set -eu
printf '=== Host and boot ===\n'
hostname
cat /proc/cmdline
printf '=== GPU function ===\n'
lspci -nnk -s 05:00.0
printf '=== HDMI audio function ===\n'
lspci -nnk -s 05:00.1
for dev in 0000:05:00.0 0000:05:00.1; do
  path="/sys/bus/pci/devices/$dev/iommu_group"
  if [ -e "$path" ]; then
    printf '%s iommu_group: %s\n' "$dev" "$(readlink -f "$path")"
  fi
done
printf '=== VFIO idle D3 (if loaded) ===\n'
[ ! -r /sys/module/vfio_pci/parameters/disable_idle_d3 ] || cat /sys/module/vfio_pci/parameters/disable_idle_d3
if command -v qm >/dev/null 2>&1; then
  printf '=== Sample VM state (change IDs for your host) ===\n'
  for vm in 100 101 103; do qm status "$vm" 2>&1 || :; done
  printf '=== VM103 display/PCI configuration ===\n'
  qm config 103 --current | grep -E '^(bios|machine|vga|hostpci[0-9]+|audio[0-9]+):' || :
fi
printf '=== Host USB enumeration (does not wake disks) ===\n'
if command -v lsusb >/dev/null 2>&1; then lsusb | grep -Ei '10c4:ea60|0a12:0001' || :; fi
