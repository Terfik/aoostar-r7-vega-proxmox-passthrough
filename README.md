# AOOSTAR R7 — AMD Vega iGPU PCI Passthrough on Proxmox VE 9

**Working, independently testable configuration for physical HDMI video, hardware-accelerated graphics, and HDMI audio in an existing Debian 13 gaming VM.**

[![Proxmox VE](https://img.shields.io/badge/Proxmox_VE-9.1.2-E57000)](https://www.proxmox.com/) [![Debian](https://img.shields.io/badge/Guest-Debian_13-A81D33)](https://www.debian.org/) [![GPU](https://img.shields.io/badge/AMD_Vega-VFIO_passing-2E8B57)](#verified-results) [![Documentation](https://img.shields.io/badge/Status-reproduced_once-blue)](#limits-and-open-issues)

> **Scope:** A real-world success on one AOOSTAR R7 with Ryzen 7 5825U (Barcelo/Vega). This is **not** a generic installer, a Batocera success report, or proof that every BIOS revision will work. A PCI reset warning is **still unresolved**. The procedure can remove your Proxmox host's HDMI console. Prepare tested rescue access and backups before changing anything.

## Navigation

- [Verified results and benchmarks](#verified-results)
- [Hardware topology — why USB preservation matters](#hardware-topology)
- [Safety and preflight](#before-you-start)
- [Step 1 — Persistent VFIO binding (UEFI GRUB)](#1-persistent-vfio-on-the-host)
- [Step 2 — VBIOS from your own ACPI VFCT](#2-vbios-and-firmware)
- [Step 3 — Configure the Debian gaming VM](#3-configure-the-vm)
- [Step 4 — Fix guest firmware](#4-get-real-gpu-acceleration)
- [Step 5 — HDMI audio and TV output](#5-hdmi-sound-and-display-power-management)
- [Post-reboot acceptance and diagnostic commands](#6-validate-after-a-full-host-reboot)
- [Recovery, other VMs, Batocera](#recovery-and-other-vms)
- [Scripts, examples, source references](#repository-contents)

## Verified results

This was observed on **29–30 October 2026** on host `r7`, Proxmox **9.1.2** with Linux `6.17.2-2-pve`, Debian 13 Trixie guest Linux `6.12.57+deb13-amd64`, Mesa `25.0.7-2`.

| Test | Observed evidence |
|---|---|
| Physical PCI GPU passthrough | Host GPU `1002:15e7` bound to `vfio-pci`, guest `amdgpu` |
| Physical picture | Debian XFCE desktop visible over **AOOSTAR HDMI** on LG TV (`3840×2160 @ 60 Hz`) |
| Hardware OpenGL | `direct rendering: Yes`, `Accelerated: yes`, AMD Radeon (radeonsi, renoir, ACO), OpenGL 4.6 |
| Vulkan | RADV adapter enumerated; **no Vulkan game FPS test** |
| Physical HDMI sound | AMD audio `1002:1637` passed to guest separately, TV detected, `speaker-test` and PulseAudio `paplay` **audible** |
| Full host reboot | Proxmox booted with persistent VFIO command line; GPU rebound to VFIO; Debian GPU/HDMI/audio worked again |
| Other services | NAS and Home Assistant VMs running; host SSH/Tailscale active; **real Zigbee control confirmed** after host reboot |
| Safety caveat | `.../05:00.0/reset: Inappropriate ioctl for device` on VM start, but QEMU continued; reset warning **not fixed** |

### Performance evidence — glmark2

Three selected `glmark2 2023.01` scenes, **1920×1080 windowed**, 5 seconds per scene, same VM/session; software baseline explicitly forced with `LIBGL_ALWAYS_SOFTWARE=1`.

| Scene | AMD Vega GPU | Mesa llvmpipe CPU | Speed-up |
|---|---:|---:|---:|
| Terrain | **187 FPS** | 5 FPS | 37.4× |
| Shadow | **3122 FPS** | 94 FPS | 33.2× |
| Refract | **374 FPS** | 16 FPS | 23.4× |
| **glmark2 score** | **1226** | **37** | **33.1×** |

The 33.1× score ratio is **not** an estimate of game FPS or of the old VirtIO-only setup. A separate lightweight 1280×720 run scored 5654 with different scenes; it is **not comparable** with the 1080p score.

## Hardware topology

~~~mermaid
flowchart TD
  A["AOOSTAR R7 — Ryzen 7 5825U"] --> P["Proxmox VE 9.1.2 / headless"]
  P --> G["05:00.0 — AMD Vega VGA [1002:15e7] / IOMMU 15"]
  P --> H["05:00.1 — AMD HDMI Audio [1002:1637] / IOMMU 16"]
  P --> U["05:00.3 + 05:00.4 — xHCI USB / KEEP ON HOST"]
  G --> V["VM103 Debian 13 / amdgpu + OpenGL"]
  H --> V
  V --> TV["Physical HDMI → LG TV: picture + sound"]
  U --> HA["Host USB / Zigbee, Bluetooth / Home Assistant"]
  P --> NAS["Other VMs — NAS / Home Assistant"]
~~~

**Never pass all functions with `05:00` or use "All Functions" on this APU!** That may capture `05:00.3` and `05:00.4` USB controllers used by the host and Home Assistant. Only individual functions `05:00.0` and `05:00.1` were assigned. On this exact machine, groups 15 and 16 each contained only the respective PCI function. Confirm your own IOMMU groups: PCI addresses and grouping can differ.

## Before you start

1. Confirm **local physical access**, a **boot-tested** rescue USB, reliable **SSH or Tailscale**, off-host backups, and a rollback route. A SHA checksum alone is *not* a tested VM restore.
2. Inspect existing bootloader. The tested PVE uses **UEFI GRUB**, an LVM/ext4 root and mounted `/boot/efi`. Its `proxmox-boot-tool status` indicated no `/etc/kernel/proxmox-boot-uuids`. **Do not follow the GRUB procedure** for a systemd-boot or different PVE installation.
3. Map every PCI function and USB dependency. Keep host-critical USB controllers on Proxmox. Do not wake standby hard drives for GPU diagnostics.
4. Preserve the **entire existing VM configuration and disk**. The INI snippet below is only a partial config and must not replace another VM's full file.
5. Plan for a **black or stale host HDMI console** after VFIO binds the only GPU. Remote SSH proves more than a static boot message.
6. Avoid global blacklist of AMD modules, arbitrary root shells via MCP, flashing BIOS, `vendor-reset` forks or forced GPU PCI resets.

## 1. Persistent VFIO on the host

On the *tested* host, an interactive **one-shot GRUB** modification established that the following two parameters work without stealing USB:

~~~text
vfio-pci.ids=1002:15e7 vfio-pci.disable_idle_d3=1
~~~

Only after a backup and a matching preflight, the operator changed this existing line in `/etc/default/grub`:

~~~ini
GRUB_CMDLINE_LINUX_DEFAULT="quiet vfio-pci.ids=1002:15e7 vfio-pci.disable_idle_d3=1"
GRUB_CMDLINE_LINUX=""
~~~

This is **not** a copy-paste command to overwrite your entire `/etc/default/grub`; preserve your own existing kernel options. On the tested GRUB host, `GRUB_DISABLE_OS_PROBER=true update-grub` completed, and `/boot/grub/grub.cfg` contained both flags for the installed PVE kernel. **After a full host reboot**, the actual `/proc/cmdline` again contained both flags, and `lspci -nnk -s 05:00.0` reported `Kernel driver in use: vfio-pci`.

Recorded host backup locations (examples, **not included** in repo):

~~~text
/root/vm103-grub-before-vfio-20261030/grub
/root/vm103-grub-before-vfio-20261030/grub.cfg
~~~

No `amd_iommu=on`, global AMD blacklist, separate VFIO boot module override or BIOS flash was proven necessary on this machine. `vfio-pci.ids` binds only GPU `1002:15e7`. The HDMI audio PCI function was attached to VFIO **at guest startup**, rather than via an additional GRUB vendor/device ID.

## 2. VBIOS and firmware

The working ROM came from the **unit's own ACPI VFCT table**. It is **legacy AMD ATOM**, **not a UEFI GOP ROM**. Nevertheless, this specific OVMF Debian setup started and began displaying output when the guest `amdgpu` driver initialized; a visible EFI/OVMF splash was **not** required.

| Verified artifact metadata | Value |
|---|---|
| GPU PCI device | `1002:15e7` |
| Host ROM filename | `/usr/share/kvm/vbios_1002_15e7_aoostar_vfct.bin` |
| Size | **55,296 bytes** |
| SHA-256 | `7a699baf6337efb289c5f2f1d64c481d4933bd34328c0037a89f4007088d115c` |
| Observed guest log | `ATOM BIOS: 113-BARCELO-004` |

**ROM binary status:** the owner reports that public redistribution is authorized, but the actual binary bytes **have not been supplied to this publication process**, so they are **not bundled yet**. Metadata is not firmware. Before any binary is added, it must be compared byte-for-byte/hash to the verified 55,296-byte file and reviewed for incidental machine identifiers. The project MIT license applies to the documentation and scripts, **not automatically to OEM firmware**. See [firmware provenance, extraction and limitations](docs/FIRMWARE.md).

A **non-destructive local extraction script** exists at [`scripts/extract_vfct_vbios.py`](scripts/extract_vfct_vbios.py), with synthetic tests. It has **not been validated against the actual AOOSTAR ROM**, so it is not a guaranteed way to recreate this particular working image.

## 3. Configure the VM

The existing VM103 (Debian Gaming) was **not recreated**. Working **partial** Proxmox config after passing GPU and HDMI audio:

~~~ini
bios: ovmf
machine: q35
hostpci0: 0000:05:00.0,pcie=1,romfile=vbios_1002_15e7_aoostar_vfct.bin
hostpci1: 0000:05:00.1,pcie=1
vga: none
~~~

`romfile` is resolved **relative to the Proxmox host `/usr/share/kvm/` directory**. Install/copy **your own verified ROM** there first.

- `hostpci0`: **GPU 05:00.0 only**. No `x-vga=1` used.
- `hostpci1`: **HDMI audio 05:00.1 only**. The two functions were separate IOMMU groups on this machine.
- `vga: none`: display is on **physical HDMI**, **not** in the Proxmox SPICE/noVNC console. Keep QEMU Guest Agent and SSH/physical access.
- The VM originally had `vga: virtio`. AMD worked for independent headless EGL rendering, but its X11 desktop initially used `llvmpipe` via VirtIO. In the final setup, the physical AMD display provider became primary and X11 used `radeonsi`.
- A leftover `audio0: device=ich9-intel-hda,driver=spice` made QEMU fail with `Cannot use spice audio without -spice` when `vga: none` disabled SPICE. That virtual audio entry was removed while VM was stopped; the AMD controller was passed separately.
- An old VM USB passthrough (`20bc:5500`) was removed during the original staged change. This is a historical fact, **not** a recommendation to remove an unrelated USB device from your own VM.

Example config: [`examples/working-partial-vm103.conf`](examples/working-partial-vm103.conf).

## 4. Get real GPU acceleration

On its first boot, the Debian guest recognized AMD PCI `1002:15e7` but `amdgpu` failed due to missing `green_sardine_*.bin` firmware. After enabling Debian 13's `non-free-firmware` repository component, the operator installed:

~~~bash
apt-get install --no-install-recommends firmware-amd-graphics
~~~

The guest installed the version available at the time (`20250410-2`), and a controlled driver probe eventually initialized `amdgpu`. **A PCI driver reprobe interrupted the X11 session**, even though it did not reboot the guest. Prefer a planned guest boot on new installations instead of copying live driver-reset commands.

With the final `vga: none` config, test from the guest's X11 session:

~~~bash
DISPLAY=:0 glxinfo -B
DISPLAY=:0 xrandr --query
~~~

Expected from this case: `OpenGL renderer string: AMD Radeon Graphics (radeonsi, renoir, ACO...)`, `Accelerated: yes`, `direct rendering: Yes`, `HDMI-A-0 connected 3840x2160+0+0`. This setup also enumerated Vulkan RADV, but **a Vulkan game was not tested**.

The QEMU Guest Agent provided non-interactive checks from the PVE SSH terminal, e.g.:

~~~bash
qm guest exec 103 -- /usr/sbin/runuser -u <guest-user> -- /usr/bin/env DISPLAY=:0 /usr/bin/glxinfo -B
~~~

Guest account, display, VM ID and application paths must be adjusted per machine.

## 5. HDMI sound and display power management

Passing GPU alone did **not** pass the sound. Proxmox initially owned `05:00.1` with `snd_hda_intel`. After separately assigning `hostpci1`, the guest saw `02:00.0` AMD Renoir HDMI Audio with `snd_hda_intel`, and ALSA reported:

~~~text
card 1: Generic [HD-Audio Generic], device 3: HDMI 0 [LG TV SSCR2]
ELD: monitor_present=1, eld_valid=1, sad_count=4
~~~

The TV **audibly played** `speaker-test -D plughw:1,3 -c 2 -t sine -f 440 -l 1`. Later PulseAudio automatically selected:

~~~text
alsa_output.pci-0000_02_00.0.hdmi-stereo
~~~

`paplay /usr/share/sounds/alsa/Front_Center.wav` was audible **both before and after a full Proxmox reboot**. Idle state `SUSPENDED` is normal. Never assume ALSA card `1,3` will be identical on another VM.

**TV "No signal" after inactivity:** this was X11 DPMS, **not GPU failure**. `xset q` reported `Monitor is Off` (DPMS off after 900 s). `DISPLAY=:0 xset dpms force on` restored picture without restarting VM or resetting GPU.

## 6. Validate after a full host reboot

The original test sequence was deliberately staged:

1. VM103 was shut down **cleanly**; backup of its config and GRUB had been checked.
2. Proxmox host rebooted; other critical VMs used existing `onboot: 1` while GPU guest **did not autostart**.
3. After regaining SSH: check `/proc/cmdline`, `vfio-pci` binding, USB enumeration, running NAS/Home Assistant VM status and real Zigbee control.
4. Start VM103 **once**. The known PCI reset warning recurred but startup succeeded; check physical LG TV display.
5. Inside guest: check `glxinfo -B` with AMD renderer and hardware acceleration, `pactl get-default-sink` and audible `paplay`.

Read-only host sample (verify host identity and adapt IDs):

~~~bash
cat /proc/cmdline
cat /sys/module/vfio_pci/parameters/disable_idle_d3
lspci -nnk -s 05:00.0
lspci -nnk -s 05:00.1
qm status 103
lsusb
systemctl is-active ssh tailscaled
~~~

Do **not** infer all services or storage health merely from `qm status: running`. This test confirmed only reported VM state and selected functional USB/Zigbee, display and audio checks. A full restore and long-duration stress tests **were not performed**.

## Recovery and other VMs

**Known open issue:** at every tested GPU start, QEMU reported:

~~~text
error writing '1' to '/sys/bus/pci/devices/0000:05:00.0/reset': Inappropriate ioctl for device
failed to reset PCI device '0000:05:00.0', but trying to continue as not all devices need a reset
~~~

This is **not resolved**. Never interpret `running` or one successful cold boot as proof of reliable unlimited GPU hot-resets. Avoid repeated start/stop loops, `vendor-reset` experiments and forced PCI resets until a separate, safe validation exists.

If host graphics disappear, verify **SSH/network first**, then use the physical UEFI/GRUB recovery path. If needed, remove both VFIO flags temporarily in GRUB and later restore the previous `/etc/default/grub` from a verified off-host backup. A rescue USB boot was tested by the operator; a **full image/VM restore was not tested**.

To use another VM with GPU (including potential Batocera), keep the existing successful VM and its disk backups, stop the current GPU owner, assign only the two individual PCI functions to **one** VM, and test its **own** drivers/firmware/boot/audio. Never autostart two VMs owning the same GPU. **Batocera was not installed or tested**; the [Batocera official wiki](https://wiki.batocera.org/run_batocera_in_vm) warns that running it in a VM is not officially supported. See [portability plan](docs/PORTABILITY.md) and [troubleshooting](docs/TROUBLESHOOTING.md).

## Repository contents

| File | Purpose |
|---|---|
| [Firmware notes](docs/FIRMWARE.md) | ROM identity, legal scope, local extraction and validation |
| [Portability](docs/PORTABILITY.md) | Safe single-owner GPU switching and Batocera limitations |
| [Troubleshooting](docs/TROUBLESHOOTING.md) | Failure modes that were actually observed |
| [GRUB example](examples/grub-cmdline.txt) | Verified kernel flags, **not** a full GRUB config |
| [Partial VM config](examples/working-partial-vm103.conf) | Verified q35/OVMF GPU/audio fragment |
| [Read-only host checklist](scripts/check_pve_vfio_readonly.sh) | No PCI reset, no mounts, no writes |
| [VFCT extraction helper](scripts/extract_vfct_vbios.py) | Local parser, **not tested on actual AOOSTAR VFCT** |
| [Parser unit tests](tests/test_extract_vfct_vbios.py) | Five synthetic VFCT cases |

### Testing the included scripts

~~~bash
python3 -m unittest discover -s tests -v
bash -n scripts/check_pve_vfio_readonly.sh
~~~

The synthetic parser tests and Bash syntax check passed offline on **30 October 2026**. They are **not** production hardware acceptance tests.

## Primary technical references and attribution

- [Proxmox official PCI(e) passthrough guide](https://github.com/proxmox/pve-docs/blob/master/qm-pci-passthrough.adoc)
- [Linux kernel AMD ACPI VFCT structures](https://github.com/torvalds/linux/blob/master/drivers/gpu/drm/amd/include/atomfirmware.h)
- [Linux AMD BIOS handling](https://github.com/torvalds/linux/blob/master/drivers/gpu/drm/amd/amdgpu/amdgpu_bios.c)
- [Batocera VM warnings](https://wiki.batocera.org/run_batocera_in_vm)

Hardware and outcomes were reported by the AOOSTAR operator, with command outputs and functional TV/Zigbee tests dated October 2026. Documentation/scripts copyright © 2026 Contributors; [MIT license](LICENSE). **Not affiliated with AOOSTAR, AMD, Proxmox, Debian or Batocera.** Any separately published OEM firmware must carry its own provenance and redistribution notice; it is **not** automatically MIT-licensed.
