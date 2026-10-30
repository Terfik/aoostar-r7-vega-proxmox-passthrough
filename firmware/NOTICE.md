# Firmware provenance and redistribution notice

**File:** `vbios_1002_15e7_aoostar_vfct.bin`  
**Public repository path:** `firmware/vbios_1002_15e7_aoostar_vfct.bin`  
**Source:** AOOSTAR R7 mini PC, own ACPI VFCT image, supplied by the system owner on 2026-10-30.  
**GPU vendor/device:** AMD / ATI `1002:15e7` (Barcelo / Vega integrated GPU).  
**ROM size:** 55,296 bytes (108 × 512-byte blocks).  
**SHA-256:** `7a699baf6337efb289c5f2f1d64c481d4933bd34328c0037a89f4007088d115c`  
**Git blob SHA-1 (over the Git blob object):** `fe9e053131fe160bddb673344351a94c33de2042`.

## Owner authorization and scope

The hardware owner and source-file provider **explicitly represents that the right to publicly distribute this image has been verified**, and authorized publication of the original ROM in this public GitHub repository. This is the provider's representation; the repository's documentation authors **have not independently audited the underlying legal permissions**. If you redistribute this OEM binary, you are responsible for verifying that you have permission to do so. The `LICENSE` file's MIT license applies only to the separately authored guide, configuration examples and scripts; it **does not purport to grant an MIT license to this AMD/OEM firmware**.

## Technical provenance and limitations

- The ROM is an **AMD ATOM VBIOS**, not the AOOSTAR system BIOS and **not a flashing image**. Its observed internal ID is `113-BARCELO-004` (build string `Barcelo Generic VBIOS`).
- It was loaded as a **QEMU/Proxmox `romfile`** for a Debian 13 VM and resulted in hardware AMD OpenGL 4.6 graphics and HDMI output on the verified host after full PVE reboot.
- The image is **legacy / no UEFI GOP**; absence of an early UEFI splash is expected in this documented guest. Compatibility with different APU IDs, motherboards, BIOS revisions, Batocera or Windows is **not established**.
- The uploaded original was checked for the exact historical SHA-256 and ROM/PCI signatures. A basic printable-string search found generic AMD BIOS text but no obvious exposed password or MAC address. This is **not** a comprehensive confidential-metadata audit and does not prove the absence of non-printable per-device identifiers.
- The ROM is **not to be flashed** onto any GPU or motherboard. Keep an independent verified backup of the working host and guest before using GPU passthrough.

## Integrity verification

Run `sha256sum firmware/vbios_1002_15e7_aoostar_vfct.bin` after cloning. The output must match the SHA-256 above. Do not trust a file with only the same name. This VBIOS is an optional artifact for the specific demonstrated use, not an installation requirement for all systems.
