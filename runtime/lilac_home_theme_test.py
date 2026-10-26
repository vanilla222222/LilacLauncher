#!/usr/bin/env python3
from pathlib import Path
import struct
import tempfile
import unittest
import zipfile
import zlib

import lilac_home_theme as theme


def chunk(kind, payload):
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)


def indexed_png():
    header = struct.pack(">IIBBBBB", 1, 1, 8, 3, 0, 0, 0)
    return theme.PNG_SIGNATURE + chunk(b"IHDR", header) + chunk(b"PLTE", bytes((0, 110, 220))) + chunk(b"tRNS", bytes((128,))) + chunk(b"IDAT", zlib.compress(b"\0\0")) + chunk(b"IEND", b"")


class PngTests(unittest.TestCase):
    def test_rgba_round_trip_preserves_transparency(self):
        pixels = bytearray((0, 0, 0, 0, 255, 255, 255, 255))
        encoded = theme.encode_png(2, 1, pixels)
        width, height, decoded = theme.decode_png(encoded)
        self.assertEqual((width, height), (2, 1))
        self.assertEqual(decoded, pixels)

    def test_blue_becomes_lilac_without_changing_white_text(self):
        blue = theme.lilac_pixel(0, 110, 220, 255)
        white = theme.lilac_pixel(255, 255, 255, 255)
        self.assertGreater(blue[0], blue[1])
        self.assertGreater(blue[2], blue[1])
        self.assertEqual(white, (255, 255, 255, 255))

    def test_dark_neutral_gets_a_subtle_lilac_cast(self):
        red, green, blue, alpha = theme.lilac_pixel(31, 32, 35, 255)
        self.assertGreater(blue, green)
        self.assertGreater(red, green)
        self.assertEqual(alpha, 255)

    def test_indexed_transparency_is_decoded(self):
        width, height, pixels = theme.decode_png(indexed_png())
        self.assertEqual((width, height), (1, 1))
        self.assertEqual(tuple(pixels), (0, 110, 220, 128))

    def test_corrupt_checksum_is_rejected(self):
        encoded = bytearray(theme.encode_png(1, 1, bytearray((0, 0, 0, 0))))
        encoded[29] ^= 1
        with self.assertRaises(ValueError):
            theme.decode_png(encoded)


class OverlayTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.apk = self.root / "base.apk"
        ui = theme.encode_png(1, 1, bytearray((0, 110, 220, 255)))
        with zipfile.ZipFile(self.apk, "w") as archive:
            archive.writestr("assets/content/textures/ui/button.png", ui)
            archive.writestr("assets/content/textures/UniversalApp/panel.png", ui)
            archive.writestr("assets/content/textures/grass.png", ui)
            archive.writestr("assets/ExtraContent/models/UniversalApp/UniversalApp.rbxm", b"signed bytecode stays untouched")

    def tearDown(self):
        self.temporary.cleanup()

    def test_only_ui_textures_are_overlaid(self):
        overlay = self.root / "overlay"
        stats, rebuilt = theme.generate(self.apk, overlay, self.root / "manifest.json")
        self.assertTrue(rebuilt)
        self.assertEqual(stats["written"], 2)
        self.assertEqual(stats["scanned"], 2)
        self.assertTrue((overlay / "content/textures/ui/button.png").is_file())
        self.assertTrue((overlay / "content/textures/UniversalApp/panel.png").is_file())
        self.assertFalse((overlay / "content/textures/grass.png").exists())
        with zipfile.ZipFile(self.apk) as archive:
            self.assertEqual(archive.read("assets/ExtraContent/models/UniversalApp/UniversalApp.rbxm"), b"signed bytecode stays untouched")

    def test_archive_paths_cannot_escape_the_generated_root(self):
        escaped = self.root / "escaped.apk"
        with zipfile.ZipFile(escaped, "w") as archive:
            archive.writestr("assets/content/textures/ui/../../outside.png", theme.encode_png(1, 1, bytearray((0, 110, 220, 255))))
        stats, _ = theme.generate(escaped, self.root / "safe", self.root / "safe-manifest.json")
        self.assertEqual(stats["scanned"], 0)
        self.assertFalse((self.root / "outside.png").exists())

    def test_unchanged_build_reuses_overlay(self):
        overlay = self.root / "overlay"
        manifest = self.root / "manifest.json"
        theme.generate(self.apk, overlay, manifest)
        marker = overlay / "marker"
        marker.write_text("still here")
        stats, rebuilt = theme.generate(self.apk, overlay, manifest)
        self.assertFalse(rebuilt)
        self.assertTrue(marker.exists())
        self.assertEqual(stats["written"], 2)

    def test_new_build_removes_stale_generated_files(self):
        overlay = self.root / "overlay"
        manifest = self.root / "manifest.json"
        theme.generate(self.apk, overlay, manifest)
        with zipfile.ZipFile(self.apk, "w") as archive:
            archive.writestr("assets/content/textures/ui/new.png", theme.encode_png(1, 1, bytearray((31, 32, 35, 255))))
        stats, rebuilt = theme.generate(self.apk, overlay, manifest)
        self.assertTrue(rebuilt)
        self.assertEqual(stats["written"], 1)
        self.assertFalse((overlay / "content/textures/ui/button.png").exists())
        self.assertTrue((overlay / "content/textures/ui/new.png").exists())

    def test_latest_complete_build_is_selected_numerically(self):
        builds = self.root / "data/cordial/builds"
        for version in ("2.99.0.1", "2.738.0.1397"):
            entry = builds / version
            entry.mkdir(parents=True)
            (entry / "base.apk").write_bytes(b"apk")
            (entry / "libroblox.so").write_bytes(b"engine")
            (entry / ".signer").write_text("checked")
        selected = theme.find_apk(self.root / "data")
        self.assertEqual(selected.parent.name, "2.738.0.1397")


if __name__ == "__main__":
    unittest.main()
