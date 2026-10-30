# VBIOS provenance, verification and safe handling

The successful GPU was an **AMD Barcelo/Vega 1002:15e7** on an **AOOSTAR R7**. The ROM image was extracted from this owner's **ACPI VFCT** table and supplied to Proxmox QEMU as `romfile`. It was **not flashed** to the motherboard or GPU.

| Property | Verified case |
|---|---|
| ROM filename | `vbios_1002_15e7_aoostar_vfct.bin` |
| QEMU search location | `/usr/share/kvm/vbios_1002_15e7_aoostar_vfct.bin` |
| Byte length | **55,296** |
| SHA-256 | `7a699baf6337efb289c5f2f1d64c481d4933bd34328c0037a89f4007088d115c` |
| BIOS identity in guest log | `ATOM BIOS: 113-BARCELO-004` |
| Format | Legacy ATOM image; **no UEFI GOP** in the extracted image |
| Tested guest | Existing Debian 13, Proxmox q35 + OVMF, `amdgpu` initialized and output HDMI |

## Public binary status

The operator **states that they have verified rights to publicly distribute this firmware**, but no source binary is available to the ChatGPT/GitHub publication process at present. **Therefore this repository does not yet include any VBIOS binary.** Do not confuse the recorded SHA-256 with a downloadable BIOS.

Before a binary is included:
1. Obtain the **original 55,296-byte** file, not a reconstructed placeholder; never generate fake bytes from the hash.
2. Independently calculate `sha256sum` (or SHA-256 with an equivalent trusted tool) and compare the exact digest above.
3. Inspect whether the binary contains any embedded unit identifiers or sensitive metadata; do not publish full ACPI dumps by default.
4. Record provenance, hardware/board revision where independently known, the scope of the owner's redistribution authorization and an explicit **firmware-specific** redistribution notice. **The MIT license of this repository does not automatically license OEM firmware.**
5. If the image has a different checksum or size, do **not** label it as the tested ROM. Provide a separate verified variant and compatibility status.
6. Do not flash this file; the successful use was a **QEMU romfile**, not replacement of the host firmware.

## Non-destructive local extraction helper

`scripts/extract_vfct_vbios.py` parses the publicly documented AMD/Linux ACPI VFCT image header, looks for a matching PCI vendor/device pair and writes the selected image to a **new local file** with mode 0600. It does not modify firmware or PCI devices. It is only unit-tested against **five synthetic VFCT records**, **not yet against the physical AOOSTAR R7**; do not describe it as the exact extraction method used successfully in October 2026.

On a host where the VFCT table is available and readable:

~~~bash
python3 scripts/extract_vfct_vbios.py \
  --input /sys/firmware/acpi/tables/VFCT \
  --vendor 1002 --device 15e7 \
  --output ./my-local-vbios.bin
sha256sum ./my-local-vbios.bin
~~~

Verify that your system exposes `/sys/firmware/acpi/tables/VFCT`, and obtain privileged read access **only if specifically permitted**. On another board, matching PCI IDs alone does **not** guarantee compatible board-specific ROM contents. The extractor refuses to overwrite an existing output. If extraction fails or differs, stop; don't flash or force an untested ROM.

The successful owner-host had a local source file `/root/vbios_1002_15e7_aoostar_vfct.bin`, and installed a copy in `/usr/share/kvm/`. These are documentation paths, **not** shared files or download links.

References: [Linux AMD atomfirmware.h](https://github.com/torvalds/linux/blob/master/drivers/gpu/drm/amd/include/atomfirmware.h), [amdgpu_bios.c](https://github.com/torvalds/linux/blob/master/drivers/gpu/drm/amd/amdgpu/amdgpu_bios.c). Legacy ROM without GOP can still produce Linux output when `amdgpu` initializes **in this specific observed case**; this is not a guarantee for Windows, Batocera or every UEFI firmware.
