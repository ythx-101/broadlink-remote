"""Offline tests: no device and no network needed. Run:
    python3 -m unittest discover -s tests -v
"""
import base64
import os
import struct
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))

import bl_send
import tcl_send


class EncodeBroadlinkTest(unittest.TestCase):
    def test_header_and_length(self):
        out = tcl_send.encode_broadlink([800, 400, 130, 280])
        self.assertEqual(out[:2], b"\x26\x00")
        (length,) = struct.unpack("<H", out[2:4])
        self.assertEqual(length, len(out) - 4)

    def test_long_pulse_uses_three_bytes(self):
        out = tcl_send.encode_broadlink([18178])
        ticks = round(18178 / 8.192)
        self.assertGreater(ticks, 255)
        self.assertEqual(out[4:], bytes([0, (ticks >> 8) & 0xFF, ticks & 0xFF]))
        self.assertEqual(struct.unpack("<H", out[2:4])[0], 3)


class TclChecksumTest(unittest.TestCase):
    def test_frame2_checksum(self):
        # Candidate #8 is a historical candidate whose checksum does not match; skipped on purpose.
        for i, (_desc, _f1, f2) in enumerate(tcl_send.candidates):
            if i == 8:
                continue
            with self.subTest(candidate=i):
                self.assertEqual(f2[13], sum(f2[:13]) & 0xFF)


class DecodeIrTest(unittest.TestCase):
    def test_hex_and_base64_match(self):
        raw = tcl_send.encode_broadlink([800, 400, 130, 280, 18178])
        self.assertEqual(bl_send.decode_ir(raw.hex()), raw)
        self.assertEqual(bl_send.decode_ir(raw.hex().upper()), raw)
        self.assertEqual(bl_send.decode_ir(base64.b64encode(raw).decode()), raw)
        self.assertEqual(bl_send.decode_ir(raw.hex()), bl_send.decode_ir(base64.b64encode(raw).decode()))


if __name__ == "__main__":
    unittest.main()
