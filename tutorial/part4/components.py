from dataclasses import dataclass

from baggo import Color

@dataclass
class Position:
    x: int
    y: int

@dataclass
class Renderable:
    glyph: int
    fg: Color
    bg: Color