# Observed failures and what actually resolved them

| Symptom | Verified root cause in this specific installation | Treatment and limitations |
|---|---|---|
| Guest can see AMD PCI but GPU driver doesn't initialize | Missing Debian `green_sardine_*.bin` firmware | Install correct Debian 13 `firmware-amd-graphics` from non-free-firmware, then clean guest boot or controlled probe. |
| `glxinfo -B` shows `llvmpipe` although PCI GPU is attached | X11 initially rendered on the VirtIO/SPICE adapter | Verified AMD EGL hardware, then used `vga: none` to render physical X11 on AMD HDMI; no more SPICE frame display. |
| QEMU error `Cannot use spice audio without -spice` | Old virtual `audio0 ... driver=spice` after disabling SPICE with `vga: none` | Clean VM shutdown, backup config, remove only the stale virtual SPICE audio; HDMI audio remains a separate physical function. |
| `...05:00.0/reset: Inappropriate ioctl for device` | Sysfs PCI reset unavailable on this GPU | **Not fixed**. VM booted anyway. Avoid forced resets and repeated hot cycles. |
| TV displays `No signal` after inactivity | X11 DPMS, `Monitor is Off`, off after 900 seconds | Use guest agent/SSH for `xset q`, then `DISPLAY=:0 xset dpms force on` without VM/host reboot. |
| GPU image works but no HDMI sound | Proxmox retained host audio `05:00.1` via `snd_hda_intel` | Assign that individual function as `hostpci1` while VM stopped; verify ELD/card/playback and live sound. |
| Proxmox HDMI is black/stuck after boot | Early host VFIO capture of its only iGPU | Use SSH/Tailscale, check VM and network; do not infer host failure from TV alone. |
| GPU works until Proxmox reboots | Boot parameters initially edited in GRUB for **one boot** | After full rescue preflight, persist two flags in `/etc/default/grub`, run `update-grub`; the first full PVE reboot succeeded. |
| QEMU guest boots but physical TV shows no early firmware menu | VFCT legacy ATOM ROM has **no UEFI GOP** | This Debian guest displayed once `amdgpu` initialized; other OS/OVMF revisions may differ. |

## Diagnostic commands (do not run outside authorized host/guest)

~~~bash
# On Proxmox, only after checking host identity:
cat /proc/cmdline
lspci -nnk -s 05:00.0
lspci -nnk -s 05:00.1
qm config 103 --current | grep -E '^(bios|machine|vga|hostpci[0-9]+|audio[0-9]+):'
qm status 103
# Inside Debian's active X11 session:
DISPLAY=:0 glxinfo -B
DISPLAY=:0 xrandr --query
cat /proc/asound/cards
aplay -l
~~~

The optional [read-only PVE checklist](../scripts/check_pve_vfio_readonly.sh) prints actual GPU binding and selected VM status. It does **not** perform mount/PCI operations. The [VFCT extractor](../scripts/extract_vfct_vbios.py) is a file parser, not a firmware flashing or GPU reset tool.

**Safety:** A `qm status` check is not an application health check. After a disruptive change validate real SSH, Tailscale, Home Assistant Zigbee, and service availability; avoid waking standby HDDs. Hardware reset warning remains open — no vendor-reset patch is endorsed.
