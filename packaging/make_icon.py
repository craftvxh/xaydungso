"""Regenerate packaging/xaydungso.ico from the app logo SVG.

Run: uv run python packaging/make_icon.py  (needs only PyQt6; PNG-in-ICO).
"""

import struct
import sys
from pathlib import Path

from PyQt6.QtCore import QBuffer, QByteArray, QIODevice, Qt
from PyQt6.QtGui import QGuiApplication, QImage, QPainter
from PyQt6.QtSvg import QSvgRenderer

ROOT = Path(__file__).resolve().parents[1]
SVG = ROOT / "src" / "xaydungso" / "presentation" / "logo.svg"
ICO = ROOT / "packaging" / "xaydungso.ico"
SIZES = (16, 20, 24, 32, 40, 48, 64, 128, 256)


def png(renderer: QSvgRenderer, size: int) -> bytes:
    image = QImage(size, size, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    renderer.render(painter)
    painter.end()
    data = QByteArray()
    buffer = QBuffer(data)
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    image.save(buffer, "PNG")
    return bytes(data)


def main() -> None:
    QGuiApplication(sys.argv[:1])
    renderer = QSvgRenderer(str(SVG))
    images = [png(renderer, size) for size in SIZES]
    header = struct.pack("<HHH", 0, 1, len(images))
    offset = 6 + 16 * len(images)
    entries = b""
    for size, data in zip(SIZES, images):
        side = 0 if size == 256 else size  # 0 means 256 in ICO entries.
        entries += struct.pack("<BBBBHHII", side, side, 0, 0, 1, 32, len(data), offset)
        offset += len(data)
    ICO.write_bytes(header + entries + b"".join(images))
    print(f"wrote {ICO} ({len(SIZES)} sizes)")


if __name__ == "__main__":
    main()
