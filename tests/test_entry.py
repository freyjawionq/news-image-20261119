"""Tests for the 19 November 2026 news front page generator.

Run from the repository root:  python3 -m unittest discover -s tests -v
Standard library only.
"""

import binascii
import hashlib
import importlib.util
import os
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_main():
    spec = importlib.util.spec_from_file_location("entry_main", os.path.join(ROOT, "main.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_program(out_dir):
    env = dict(os.environ, MAKEFUN_OUTPUT_DIR=out_dir)
    proc = subprocess.run(
        [sys.executable, os.path.join(ROOT, "main.py")],
        env=env, capture_output=True, text=True, timeout=60,
    )
    assert proc.returncode == 0, proc.stderr
    path = os.path.join(out_dir, "entry.png")
    with open(path, "rb") as fh:
        return fh.read()


def parse_png(data):
    """Return (width, height, chunk_tags) after verifying every CRC."""
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "bad PNG signature"
    pos = 8
    tags = []
    width = height = None
    idat = bytearray()
    while pos < len(data):
        (length,) = struct.unpack(">I", data[pos:pos + 4])
        tag = data[pos + 4:pos + 8]
        payload = data[pos + 8:pos + 8 + length]
        (crc,) = struct.unpack(">I", data[pos + 8 + length:pos + 12 + length])
        assert crc == binascii.crc32(tag + payload) & 0xFFFFFFFF, f"bad CRC in {tag}"
        tags.append(tag.decode("ascii"))
        if tag == b"IHDR":
            width, height = struct.unpack(">II", payload[:8])
        if tag == b"IDAT":
            idat += payload
        pos += 12 + length
    raw = zlib.decompress(bytes(idat))
    assert len(raw) == height * (1 + width * 3), "image data size mismatch"
    return width, height, tags


class EntryTests(unittest.TestCase):
    def test_program_writes_valid_png(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = run_program(tmp)
        width, height, tags = parse_png(data)
        self.assertEqual(tags[0], "IHDR")
        self.assertEqual(tags[-1], "IEND")
        self.assertIn("IDAT", tags)

    def test_two_runs_byte_identical(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            first = run_program(a)
            second = run_program(b)
        self.assertEqual(hashlib.sha256(first).hexdigest(), hashlib.sha256(second).hexdigest())
        self.assertEqual(first, second)

    def test_size_and_dimension_limits(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = run_program(tmp)
        width, height, _ = parse_png(data)
        self.assertLessEqual(len(data), 1024 * 1024)
        self.assertLessEqual(width, 1024)
        self.assertLessEqual(height, 1024)

    def test_date_and_stories_in_program_data(self):
        mod = load_main()
        self.assertEqual(mod.DATE_LINE, "THURSDAY 19 NOVEMBER 2026")
        self.assertIn("19 NOVEMBER 2026", mod.DATE_LINE)
        self.assertTrue(mod.LEAD["headline"])
        # The footer must not claim every story was reported on 19 Nov:
        # the source map includes reporting published 17-18 Nov.
        self.assertNotIn("EVERY STORY ABOVE WAS REPORTED ON", mod.FOOTER)
        self.assertIn("ON OR AROUND THAT DATE", mod.FOOTER)
        self.assertGreaterEqual(len(mod.PANELS), 4)
        for panel in mod.PANELS:
            self.assertTrue(panel["headline"])
            self.assertTrue(panel["sub"])

    def test_committed_entry_matches_program_output(self):
        committed_path = os.path.join(ROOT, "entry.png")
        if not os.path.exists(committed_path):
            self.skipTest("entry.png not committed yet")
        with open(committed_path, "rb") as fh:
            committed = fh.read()
        with tempfile.TemporaryDirectory() as tmp:
            fresh = run_program(tmp)
        self.assertEqual(committed, fresh)


if __name__ == "__main__":
    unittest.main()
