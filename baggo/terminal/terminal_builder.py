from enum import Enum
from pathlib import Path

from .console import Console, SimpleConsole
from .font import Font
from .terminal import Terminal

class TerminalBackends(Enum):
    ARCADE = 1
    PYGLET = 2
    PYGAME = 3


DEFAULT_TERMINAL_BACKEND = TerminalBackends.ARCADE


class TerminalBuilder:
    backend: TerminalBackends

    width: int
    height: int

    title: str

    console: Console
    font: Font

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height

    @classmethod
    def simple(cls, width: int, height: int, title: str, tile_width: int, tile_height: int, font_file: Path, backend: TerminalBackends = DEFAULT_TERMINAL_BACKEND) -> TerminalBuilder:
        con = SimpleConsole(width, height)
        tb = cls(width, height)
        tb.title = title
        tb.console = con
        tb.backend = backend
        tb.font = TerminalBuilder.create_font(tb.backend, tile_width, tile_height, Path(font_file))
        return tb

    @staticmethod
    def create_font(backend: TerminalBackends, tile_width: int, tile_height: int, font_file: Path):
        match backend:
            case TerminalBackends.ARCADE:
                from .backends.arcade import FontArcade

                return FontArcade(tile_width, tile_height, font_file)

        raise RuntimeError(f"Unable to create font for current backend {backend.name}")

    def build(self) -> Terminal:
        match self.backend:
            case TerminalBackends.ARCADE:
                from .backends.arcade import FontArcade, TerminalArcade
                assert(isinstance(self.font, FontArcade))
                return TerminalArcade(self.width * self.font.tile_width, self.height * self.font.tile_height, self.title, self.console, self.font)

        raise RuntimeError(
            f"Unable to create terminal for current backend {self.backend.name}"
        )
