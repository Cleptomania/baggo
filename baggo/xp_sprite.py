"""Loading support for REXPaint ``.xp`` sprite files.

REXPaint is a CP437 ASCII art editor that saves its work as gzip-compressed
``.xp`` files. Each file contains one or more layers of cells; every cell
holds a CP437 glyph index plus RGB foreground and background colors. A cell
whose background is pure magenta ``(255, 0, 255)`` is treated as transparent
so layers underneath can show through.
"""

from __future__ import annotations

import gzip
import struct
from dataclasses import dataclass
from pathlib import Path

from baggo.color import Color


TRANSPARENT_BACKGROUND: Color = Color(255, 0, 255)


@dataclass
class XPCell:
    glyph: int
    foreground: Color
    background: Color


@dataclass
class XPLayer:
    width: int
    height: int
    cells: list[XPCell]

    def at(self, x: int, y: int) -> XPCell:
        return self.cells[x * self.height + y]


_HEADER = struct.Struct("<iI")
_LAYER_HEADER = struct.Struct("<II")
_CELL = struct.Struct("<IBBBBBB")


class XPSprite:
    """A sprite loaded from a REXPaint ``.xp`` file."""

    width: int
    height: int
    version: int
    layers: list[XPLayer]

    def __init__(self, path: Path):
        with gzip.open(path, "rb") as f:
            data = f.read()

        offset = 0
        self.version, layer_count = _HEADER.unpack_from(data, offset)
        offset += _HEADER.size

        self.layers = []
        for _ in range(layer_count):
            width, height = _LAYER_HEADER.unpack_from(data, offset)
            offset += _LAYER_HEADER.size

            cells: list[XPCell] = []
            for _ in range(width * height):
                glyph, fr, fg, fb, br, bg, bb = _CELL.unpack_from(data, offset)
                offset += _CELL.size
                cells.append(
                    XPCell(
                        glyph=glyph,
                        foreground=Color(fr, fg, fb),
                        background=Color(br, bg, bb),
                    )
                )
            self.layers.append(XPLayer(width=width, height=height, cells=cells))

        self.width = max((layer.width for layer in self.layers), default=0)
        self.height = max((layer.height for layer in self.layers), default=0)
