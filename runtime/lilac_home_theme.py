#!/usr/bin/env python3
"""Generate LilacRuntime's read-only Roblox UI texture overlay.

Only local PNG assets below Roblox's UI texture directories are considered.
The APK, extracted assets, signed UniversalApp bytecode and game content are
never modified. Python's standard library is sufficient on a fresh Mint install.
"""

import argparse
import colorsys
import json
from pathlib import Path
import shutil
import struct
import sys
import zipfile
import zlib

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
UI_PREFIXES = ("content/textures/ui/", "content/textures/universalapp/")
PALETTE_VERSION = 1


def paeth(a, b, c):
    estimate = a + b - c
    distances = (abs(estimate - a), abs(estimate - b), abs(estimate - c))
    return (a, b, c)[distances.index(min(distances))]


def decode_png(data):
    """Decode non-interlaced, eight-bit PNGs into straight RGBA pixels."""
    if not data.startswith(PNG_SIGNATURE):
        raise ValueError("not a PNG")
    offset = len(PNG_SIGNATURE)
    header = None
    compressed = bytearray()
    palette = []
    transparency = []
    while offset + 12 <= len(data):
        length = struct.unpack_from(">I", data, offset)[0]
        kind = data[offset + 4:offset + 8]
        start = offset + 8
        end = start + length
        if end + 4 > len(data):
            raise ValueError("truncated PNG chunk")
        payload = data[start:end]
        expected = struct.unpack_from(">I", data, end)[0]
        if zlib.crc32(data[offset + 4:end]) & 0xFFFFFFFF != expected:
            raise ValueError("PNG checksum mismatch")
        if kind == b"IHDR":
            header = struct.unpack(">IIBBBBB", payload)
        elif kind == b"PLTE":
            palette = [tuple(payload[i:i + 3]) for i in range(0, len(payload), 3)]
        elif kind == b"tRNS":
            transparency = payload
        elif kind == b"IDAT":
            compressed.extend(payload)
        elif kind == b"IEND":
            break
        offset = end + 4
    if header is None:
        raise ValueError("PNG has no header")
    width, height, depth, colour, compression, filtering, interlace = header
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}.get(colour)
    if not width or not height or depth != 8 or channels is None or compression or filtering or interlace:
        raise ValueError("unsupported PNG layout")
    raw = zlib.decompress(compressed)
    stride = width * channels
    if len(raw) != height * (stride + 1):
        raise ValueError("unexpected PNG data length")
    rows = []
    previous = bytearray(stride)
    cursor = 0
    for _ in range(height):
        mode = raw[cursor]
        cursor += 1
        source = raw[cursor:cursor + stride]
        cursor += stride
        row = bytearray(stride)
        for x, value in enumerate(source):
            left = row[x - channels] if x >= channels else 0
            above = previous[x]
            diagonal = previous[x - channels] if x >= channels else 0
            if mode == 0:
                predictor = 0
            elif mode == 1:
                predictor = left
            elif mode == 2:
                predictor = above
            elif mode == 3:
                predictor = (left + above) // 2
            elif mode == 4:
                predictor = paeth(left, above, diagonal)
            else:
                raise ValueError("unknown PNG filter")
            row[x] = (value + predictor) & 255
        rows.append(row)
        previous = row
    rgba = bytearray(width * height * 4)
    for y, row in enumerate(rows):
        for x in range(width):
            source = x * channels
            target = (y * width + x) * 4
            if colour == 6:
                values = row[source:source + 4]
            elif colour == 2:
                values = (*row[source:source + 3], 255)
            elif colour == 0:
                grey = row[source]
                values = (grey, grey, grey, 255)
            elif colour == 4:
                grey, alpha = row[source:source + 2]
                values = (grey, grey, grey, alpha)
            else:
                index = row[source]
                if index >= len(palette):
                    raise ValueError("PNG palette index is out of range")
                alpha = transparency[index] if index < len(transparency) else 255
                values = (*palette[index], alpha)
            rgba[target:target + 4] = bytes(values)
    return width, height, rgba


def encode_png(width, height, rgba):
    """Encode RGBA with filter None; deterministic output keeps rebuilds stable."""
    scanlines = bytearray()
    stride = width * 4
    for y in range(height):
        scanlines.append(0)
        scanlines.extend(rgba[y * stride:(y + 1) * stride])

    def chunk(kind, payload):
        return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)

    header = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return PNG_SIGNATURE + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(bytes(scanlines), 9)) + chunk(b"IEND", b"")


def lilac_pixel(red, green, blue, alpha):
    """Recolour blue accents and dark neutrals while preserving light text."""
    if alpha == 0:
        return red, green, blue, alpha
    hue, lightness, saturation = colorsys.rgb_to_hls(red / 255, green / 255, blue / 255)
    changed = False
    if 0.50 <= hue <= 0.72 and saturation >= 0.18 and lightness < 0.82:
        hue = 0.755
        saturation = max(0.38, min(0.72, saturation * 0.88))
        changed = True
    elif saturation < 0.16 and lightness < 0.58:
        hue = 0.755
        saturation = 0.20 if lightness < 0.34 else 0.11
        changed = True
    if not changed:
        return red, green, blue, alpha
    r, g, b = colorsys.hls_to_rgb(hue, lightness, saturation)
    return round(r * 255), round(g * 255), round(b * 255), alpha


def recolour_png(data):
    width, height, pixels = decode_png(data)
    changed = False
    for index in range(0, len(pixels), 4):
        original = tuple(pixels[index:index + 4])
        themed = lilac_pixel(*original)
        if themed != original:
            pixels[index:index + 4] = bytes(themed)
            changed = True
    return encode_png(width, height, pixels) if changed else None


def version_key(version):
    try:
        return tuple(int(part) for part in version.split("."))
    except ValueError:
        return ()


def find_apk(data_home, explicit=""):
    if explicit:
        path = Path(explicit).expanduser()
        return path if path.is_file() else None
    builds = data_home / "cordial" / "builds"
    candidates = []
    if builds.is_dir():
        for entry in builds.iterdir():
            if version_key(entry.name) and (entry / "base.apk").is_file() and (entry / "libroblox.so").is_file() and (entry / ".signer").is_file():
                candidates.append(entry)
    if not candidates:
        return None
    return max(candidates, key=lambda path: version_key(path.name)) / "base.apk"


def generate(apk, overlay, manifest):
    identity = {
        "palette": PALETTE_VERSION,
        "size": apk.stat().st_size,
        "mtime_ns": apk.stat().st_mtime_ns,
    }
    if manifest.is_file():
        try:
            saved = json.loads(manifest.read_text())
            if saved.get("identity") == identity and overlay.is_dir():
                return saved.get("stats", {}), False
        except (OSError, ValueError):
            pass
    # This directory is dedicated to generated files, never a user's overlay.
    if overlay.exists():
        shutil.rmtree(overlay)
    overlay.mkdir(parents=True)
    stats = {"scanned": 0, "written": 0, "unchanged": 0, "unsupported": 0}
    with zipfile.ZipFile(apk) as archive:
        for info in archive.infolist():
            if not info.filename.startswith("assets/") or not info.filename.lower().endswith(".png"):
                continue
            name = info.filename[len("assets/"):]
            parts = name.split("/")
            if not name.lower().startswith(UI_PREFIXES) or any(part in ("", ".", "..") for part in parts):
                continue
            stats["scanned"] += 1
            try:
                themed = recolour_png(archive.read(info))
            except (ValueError, zlib.error):
                stats["unsupported"] += 1
                continue
            if themed is None:
                stats["unchanged"] += 1
                continue
            destination = overlay.joinpath(*parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(themed)
            stats["written"] += 1
    manifest.parent.mkdir(parents=True, exist_ok=True)
    temporary = manifest.with_suffix(".tmp")
    temporary.write_text(json.dumps({"identity": identity, "stats": stats}, indent=2) + "\n")
    temporary.replace(manifest)
    return stats, True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-home", type=Path, required=True)
    parser.add_argument("--config-home", type=Path, required=True)
    parser.add_argument("--apk", default="")
    args = parser.parse_args()
    apk = find_apk(args.data_home, args.apk)
    if apk is None:
        print("[lilac-home] No imported Roblox build found yet; the UI overlay will be created on a later run.")
        return 0
    cordial_config = args.config_home / "cordial"
    try:
        stats, rebuilt = generate(apk, cordial_config / "lilac-home-overlay", cordial_config / "lilac-home-theme.json")
    except (OSError, zipfile.BadZipFile) as error:
        print(f"[lilac-home] Could not prepare UI textures: {error}", file=sys.stderr)
        return 0
    action = "generated" if rebuilt else "ready"
    print(f"[lilac-home] Lilac UI overlay {action} for {apk.parent.name}: {stats.get('written', 0)} recoloured, {stats.get('scanned', 0)} UI textures scanned.")
    if not stats.get("written"):
        print("[lilac-home] This Roblox build exposed no recolourable eight-bit UI PNGs; compiled UI colours are not changed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
