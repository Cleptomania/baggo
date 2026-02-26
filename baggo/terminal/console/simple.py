from .console import Console, Tile

from baggo import Color, colors, to_cp437


class SimpleConsole(Console):
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height

        num_tiles = width * height
        self.tiles = [Tile(0, colors.WHITE, colors.BLACK) for _ in range(num_tiles)]

    def at(self, x: int, y: int) -> Tile | None:
        index = self.try_index(x, y)
        if index is not None:
            return self.tiles[index]
        return None

    def clear(self, color: Color = colors.BLACK) -> None:
        for tile in self.tiles:
            tile.glyph = 32
            tile.foreground = colors.WHITE
            tile.background = color

        self.dirty = True

    def print(
        self,
        x: int,
        y: int,
        text: str,
        foreground: Color = colors.WHITE,
        background: Color = colors.BLACK,
    ) -> None:
        changed = False
        for char in text:
            cp = to_cp437(char)
            index = self.try_index(x, y)
            if index is not None:
                self.tiles[index].glyph = cp
                self.tiles[index].foreground = foreground
                self.tiles[index].background = background
                changed = True
            x += 1

        if changed:
            self.dirty = True

    def set(
        self,
        x: int,
        y: int,
        glyph: int,
        foreground: Color = colors.WHITE,
        background: Color = colors.BLACK,
    ) -> None:
        index = self.try_index(x, y)
        if index is not None:
            self.tiles[index].glyph = glyph
            self.tiles[index].foreground = foreground
            self.tiles[index].background = background
            self.dirty = True

    def index(self, x: int, y: int) -> int:
        return (self.height - 1 - y * self.width) + x

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def try_index(self, x: int, y: int) -> int | None:
        if self.in_bounds(x, y):
            return self.index(x, y)

        return None
