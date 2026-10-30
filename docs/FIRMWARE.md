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

**The actual original ROM is now published:** [`firmware/vbios_1002_15e7_aoostar_vfct.bin`](../firmware/vbios_1002_15e7_aoostar_vfct.bin), **55,296 bytes**, with the SHA-256 shown above. The operator personally confirms that their authorization to distribute the ROM publicly has been verified; the maintainers of this documentation have **not independently reviewed legal title documents**. The uploaded bytes were compared to the historical digest, and the Git blob SHA is `fe9e053131fe160bddb673344351a94c33de2042`. A simple readable-strings scan showed generic AMD/Barcelo BIOS text and no obvious exposed passwords or MAC addresses; **it cannot rule out all opaque embedded device identifiers**.

The published binary is **firmware supplied by the hardware owner**, not software authored under this repository's MIT license. Read the separate [firmware notice](../firmware/NOTICE.md) before redistributing. The ROM is only known to work as a **QEMU/Proxmox romfile** for the tested AMD Barcelo GPU. **Do not flash it** and do not assume all AOOSTAR R7 hardware revisions or OS guests are compatible.

To verify your downloaded copy and use it **only for a compatible VM**:

```bash
sha256sum vbios_1002_15e7_aoostar_vfct.bin
# Expected: 7a699baf6337efb289c5f2f1d64c481d4933bd34328c0037a89f4007088d115c
```

1. Do not flash this file or treat it as a system motherboard BIOS. It was successfully loaded using the QEMU **romfile** parameter.
2. Verify both byte length (55,296) and SHA-256 **before copying it to a Proxmox host**.
3. Inspect compatibility on *your* hardware; the same PCI ID does not guarantee matching board firmware, and different BIOS revisions are **not tested**.
4. Keep working host and VM backups, out-of-band access and a rollback path; passthrough can eliminate host HDMI console output.
5. Don't publish full ACPI tables or arbitrary ROM dumps; the committed file is a single GPU VBIOS image.
6. The MIT license of this repository **does not automatically cover the firmware binary**; see its [NOTICE](../firmware/NOTICE.md).

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
