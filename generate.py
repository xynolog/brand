"""Writes every derivative of src/mark.svg: the favicons and the app icons.

Run by generate.sh inside its pinned container, which supplies rsvg-convert.
It owns favicons/ and app-icon/ whole: both are emptied and written again, so
an output nobody writes any more disappears with them.
"""

import json
import pathlib
import shutil
import struct
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

SVG = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG)

ROOT = pathlib.Path(sys.argv[1])
SOURCE = ROOT / "src" / "mark.svg"
FAVICONS = ROOT / "favicons"
APP_ICON = ROOT / "app-icon"

FAVICON_SIZES = (16, 32, 48, 64, 96, 128)
FAVICON_ICO_SIZES = (16, 32, 48)
APPLE_TOUCH_SIZE = 180
ANDROID_SIZES = (192, 512)
APP_ICON_SIZE = 1024
# Apple's macOS icon grid: the tile is 824 of the 1024 canvas, centred.
APP_TILE_SIZE = 824
APP_ICO_SIZES = (16, 24, 32, 48, 64, 128, 256)
# Each ICNS slot and the pixel size of the PNG it holds.
ICNS_SLOTS = (
    ("icp4", 16), ("ic11", 32), ("icp5", 32), ("ic12", 64), ("ic07", 128),
    ("ic13", 256), ("ic08", 256), ("ic14", 512), ("ic09", 512), ("ic10", 1024),
)


def mark():
    tree = ET.parse(SOURCE)
    root = tree.getroot()
    if root.get("viewBox") != "0 0 64 64":
        raise SystemExit(f"{SOURCE}: the viewBox must be 0 0 64 64")
    return root


def tile(root):
    found = root.find(f"{{{SVG}}}rect[@id='tile']")
    if found is None:
        raise SystemExit(f"{SOURCE}: no <rect id=\"tile\">")
    return found


def write_svg(root, path):
    path.write_bytes(ET.tostring(root, encoding="utf-8", xml_declaration=False) + b"\n")


def square(root):
    """The mark on a square tile, for platforms that round the corners themselves."""
    copy = ET.fromstring(ET.tostring(root))
    tile(copy).attrib.pop("rx")
    return copy


def app_icon(root):
    """The mark at the size and inset of a desktop application icon."""
    scale = APP_TILE_SIZE / 64
    inset = (APP_ICON_SIZE - APP_TILE_SIZE) / 2
    canvas = ET.Element(f"{{{SVG}}}svg", {
        "viewBox": f"0 0 {APP_ICON_SIZE} {APP_ICON_SIZE}",
        "width": str(APP_ICON_SIZE),
        "height": str(APP_ICON_SIZE),
    })
    canvas.extend(child for child in root if child.tag == f"{{{SVG}}}title")
    group = ET.SubElement(canvas, f"{{{SVG}}}g", {"transform": f"translate({inset:g} {inset:g}) scale({scale:g})"})
    group.extend(child for child in root if child.tag != f"{{{SVG}}}title")
    return canvas


def render(svg_path, size, png_path):
    subprocess.run(["rsvg-convert", "-w", str(size), "-h", str(size), "-o", str(png_path), str(svg_path)], check=True)


def write_ico(payloads, path):
    header_size = 6 + 16 * len(payloads)
    offset = header_size
    entries = []
    for size, payload in payloads:
        dimension = 0 if size == 256 else size
        entries.append(struct.pack("<BBBBHHII", dimension, dimension, 0, 0, 1, 32, len(payload), offset))
        offset += len(payload)
    path.write_bytes(struct.pack("<HHH", 0, 1, len(payloads)) + b"".join(entries) + b"".join(p for _, p in payloads))


def write_icns(slots, path):
    chunks = b"".join(kind.encode("ascii") + struct.pack(">I", 8 + len(payload)) + payload for kind, payload in slots)
    path.write_bytes(b"icns" + struct.pack(">I", 8 + len(chunks)) + chunks)


def main():
    root = mark()
    background = tile(root).get("fill")
    for directory in (FAVICONS, APP_ICON):
        shutil.rmtree(directory, ignore_errors=True)
        directory.mkdir()

    with tempfile.TemporaryDirectory() as scratch:
        scratch = pathlib.Path(scratch)
        rendered = {}

        def png(svg_path, size):
            key = (svg_path, size)
            if key not in rendered:
                out = scratch / f"{svg_path.stem}-{size}.png"
                render(svg_path, size, out)
                rendered[key] = out.read_bytes()
            return rendered[key]

        favicon_svg = FAVICONS / "favicon.svg"
        shutil.copyfile(SOURCE, favicon_svg)
        for size in FAVICON_SIZES:
            (FAVICONS / f"favicon-{size}x{size}.png").write_bytes(png(favicon_svg, size))
        write_ico([(size, png(favicon_svg, size)) for size in FAVICON_ICO_SIZES], FAVICONS / "favicon.ico")

        square_svg = scratch / "square.svg"
        write_svg(square(root), square_svg)
        (FAVICONS / "apple-touch-icon.png").write_bytes(png(square_svg, APPLE_TOUCH_SIZE))

        for size in ANDROID_SIZES:
            (FAVICONS / f"android-chrome-{size}x{size}.png").write_bytes(png(favicon_svg, size))
        manifest = {
            "name": "Xynolog",
            "short_name": "Xynolog",
            "icons": [
                {"src": f"android-chrome-{size}x{size}.png", "sizes": f"{size}x{size}", "type": "image/png"}
                for size in ANDROID_SIZES
            ],
            "theme_color": background,
            "background_color": background,
            "display": "standalone",
        }
        (FAVICONS / "site.webmanifest").write_text(json.dumps(manifest, indent=2) + "\n")

        app_svg = APP_ICON / "app-icon.svg"
        write_svg(app_icon(mark()), app_svg)
        (APP_ICON / "icon.png").write_bytes(png(app_svg, APP_ICON_SIZE))
        write_ico([(size, png(app_svg, size)) for size in APP_ICO_SIZES], APP_ICON / "icon.ico")
        write_icns([(kind, png(app_svg, size)) for kind, size in ICNS_SLOTS], APP_ICON / "icon.icns")


main()
