#!/usr/bin/env python3
"""Extract a PCI-ID-matched GPU BIOS image from a local ACPI VFCT table.

Uses AMD/Linux VFCT header layout. Does not touch firmware or devices;
only reads an existing table and creates a new output file (mode 0600).
Never publish an extracted VBIOS without redistribution rights.
"""
import argparse
import hashlib
import os
import struct
from pathlib import Path

IMAGE = struct.Struct('<IIIHHHHII')
VFCT_MIN = 0x4C


def parse_vfct(data, vendor, device):
    if len(data) < VFCT_MIN or data[:4] != b'VFCT':
        raise ValueError('Not a valid VFCT header')
    declared = struct.unpack_from('<I', data, 4)[0]
    if declared < VFCT_MIN or declared > len(data):
        raise ValueError('Invalid VFCT declared length')
    offset = struct.unpack_from('<I', data, 0x34)[0]
    if not VFCT_MIN <= offset <= declared - IMAGE.size:
        raise ValueError('Invalid VBIOS offset')
    while offset + IMAGE.size <= declared:
        bus, slot, fn, vid, did, ssvid, ssid, rev, n = IMAGE.unpack_from(data, offset)
        start = offset + IMAGE.size
        end = start + n
        if n == 0 or end > declared:
            raise ValueError('Invalid VFCT image size')
        if (vid, did) == (vendor, device):
            return bytes(data[start:end]), (bus, slot, fn, ssvid, ssid, rev)
        offset = end
    raise ValueError('Requested PCI vendor:device not present in VFCT')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--input', type=Path, default=Path('/sys/firmware/acpi/tables/VFCT'))
    ap.add_argument('--vendor', type=lambda s: int(s, 16), default=0x1002)
    ap.add_argument('--device', type=lambda s: int(s, 16), default=0x15E7)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    if not 0 <= args.vendor <= 0xffff or not 0 <= args.device <= 0xffff:
        ap.error('PCI vendor/device ID must be a 16-bit hex number')
    bios, meta = parse_vfct(args.input.read_bytes(), args.vendor, args.device)
    fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'wb') as out:
        out.write(bios)
    print(f'VBIOS bytes: {len(bios)}; SHA256: {hashlib.sha256(bios).hexdigest()}')
    print(f'VFCT PCI bus:slot.function: {meta[0]}:{meta[1]}.{meta[2]}')
    print('This extraction is LOCAL. Inspect the file and obtain legal permission before redistribution.')


if __name__ == '__main__':
    main()
