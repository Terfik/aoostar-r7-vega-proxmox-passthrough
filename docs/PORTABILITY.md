# Using the same physical GPU in another VM — future plan, not tested

**Scope:** The working setup was **Debian 13 VM103 only**. A future second guest (e.g., Batocera) requires a new controlled experiment, not a clone of a production config. The original system has other important VMs and host-owned USB devices.

## Non-negotiable hardware boundaries

- **Single owner:** The iGPU cannot be passed through to Debian and Batocera simultaneously.
- **PCI function precision:** Host `05:00.0` is GPU, `05:00.1` is audio; **05:00.3 and 05:00.4 are USB controllers**. Use individual functions, never shorthand `05:00` or "All Functions".
- **Independent IOMMU groups** 15 and 16 were observed for video/audio *on this AOOSTAR*. Recheck grouping and bus IDs on every other machine/firmware.
- Host's persistent `vfio-pci.ids=1002:15e7` remains valid for the same GPU; there is no proven need to rebuild GRUB merely to switch the guest owner.
- Keep the original working VM103 untouched, backed up and available to restore. Storage must stay on the intended SSD/NVMe. Do not wake or mount standby HDDs for GPU experiments.

## Proposed change procedure

1. **Before touching the owner VM:** confirm host identity, current PVE kernel/bootloader, working SSH or other out-of-band management, off-host backups, recovery method, VM configs and USB/Zigbee health.
2. Provision the **new** guest independently with its own disk/backup. Test its image/installer with a virtual display first and configure some headless or local access, where possible.
3. Schedule an outage window, then gracefully shut down **the current GPU owner VM103** and verify its state. If shutdown hangs, do not force a GPU reset.
4. Confirm the host, other VMs, USB enumeration and at least one real Zigbee operation before and after the transition.
5. On the new guest only, experiment with individually assigned GPU and optional audio functions and a verified local `romfile`. The demonstrated `q35` / `OVMF` / `vga: none` Debian shape is a hypothesis for another guest, **not proof** of compatibility.
6. Start the new VM **once**. Collect QEMU warning, guest driver data, physical HDMI image, AMD acceleration and audio playback. Do not do rapid start/stop/reset loops.
7. On success, assess input pads, game engines, temperatures and long-term stability. On failure, stop; inspect the host PCI owner, USB/Zigbee and VM state before any rollback. **Do not** change the working VM103 configuration or host USB unless explicitly approved.
8. Never enable autostart for both GPU-owning VMs. In the verified October 2026 test VM103 had **no autostart**, while NAS and HA VMs did.

## Batocera-specific caveats

Batocera's official wiki states VM use is **not officially supported**, and labels the Proxmox path **untested**. See [official Batocera documentation](https://wiki.batocera.org/run_batocera_in_vm).

- Batocera's disk image, kernel, amdgpu/Mesa firmware, init, graphics mode and audio routing are not equivalent to Debian 13.
- Do not presume availability of `apt-get`, Debian `firmware-amd-graphics`, QEMU Guest Agent, XFCE/X11 or PulseAudio.
- Absence of UEFI GOP in the *working Debian* ROM may prevent a visible EFI boot menu in another guest.
- Gamepads and USB receivers require their own *per-device* mapping; never take the host's entire 05:00.3/05:00.4 USB controllers.
- For gaming, begin with **1080p** instead of the measured 4K desktop; no game FPS data is claimed.

**No Batocera installation or GPU guest switching has been tested or authorized by this document.** It is a safe starting plan and a set of recovery constraints, not a ready-to-apply VM template.
