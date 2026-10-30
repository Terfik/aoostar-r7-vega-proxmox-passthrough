"""Synthetic unit tests for local VFCT parsing; no physical device access."""
import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from extract_vfct_vbios import IMAGE, parse_vfct  # noqa: E402


def vfct(records):
    blob = bytearray(0x4c)
    blob[:4] = b'VFCT'
    struct.pack_into('<I', blob, 0x34, 0x4c)
    for vendor, device, payload in records:
        blob.extend(IMAGE.pack(5, 0, 0, vendor, device, 0x1002, 0x0123, 1, len(payload)))
        blob.extend(payload)
    struct.pack_into('<I', blob, 4, len(blob))
    return bytes(blob)


class VfctParserTest(unittest.TestCase):
    def test_matching_record(self):
        target = b'\x55\xaa' + b'ATOM' + b'0' * 100
        blob = vfct([(0x1002, 0x9999, b'foo'), (0x1002, 0x15e7, target)])
        assert parse_vfct(blob, 0x1002, 0x15e7)[0] == target

    def test_missing_device(self):
        with self.assertRaises(ValueError):
            parse_vfct(vfct([(0x1002, 0x15e7, b'abc')]), 0x1002, 0x1637)

    def test_truncated_record(self):
        broken = vfct([(0x1002, 0x15e7, b'abcd')])[:-1]
        with self.assertRaises(ValueError):
            parse_vfct(broken, 0x1002, 0x15e7)

    def test_not_vfct(self):
        with self.assertRaises(ValueError):
            parse_vfct(b'A' * 256, 0x1002, 0x15e7)

    def test_zero_length_record(self):
        blob = vfct([(0x1002, 0x15e7, b'a')])
        mutable = bytearray(blob)
        struct.pack_into('<I', mutable, 0x4c + 24, 0)
        with self.assertRaises(ValueError):
            parse_vfct(bytes(mutable), 0x1002, 0x15e7)


if __name__ == '__main__':
    unittest.main()
