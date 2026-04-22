from abc import abstractmethod
from dataclasses import dataclass
from typing import Protocol, Set

from baggo import colors, Color
from baggo.xp_sprite import XPSprite


@dataclass
class Tile:
    glyph: int
    foreground: Color
    background: Color


class Console(Protocol):
    width: int
    height: int

    # This could actually be typed with just set[int], but type checkers get confused because there
    # is a method called set, and they seem to think that's what's being used.
    dirty_tiles: Set[int]

    @abstractmethod
    def at(self, x: int, y: int) -> Tile | None:
        raise NotImplementedError

    @abstractmethod
    def clear(self, color: Color = colors.BLACK) -> None:
        raise NotImplementedError

    @abstractmethod
    def print(
        self,
        x: int,
        y: int,
        text: str,
        foreground: Color = colors.WHITE,
        background: Color = colors.BLACK,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def set(
        self,
        x: int,
        y: int,
        glyph: int,
        foreground: Color = colors.WHITE,
        background: Color = colors.BLACK,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def draw_xp_sprite(self, x: int, y: int, sprite: XPSprite) -> None:
        raise NotImplementedError

    @abstractmethod
    def clear_dirty(self) -> None:
        raise NotImplementedError
