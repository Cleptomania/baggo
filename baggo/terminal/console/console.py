from abc import abstractmethod
from dataclasses import dataclass
from typing import Protocol

from baggo import colors, Color


@dataclass
class Tile:
    glyph: int
    foreground: Color
    background: Color


class Console(Protocol):
    width: int
    height: int

    dirty: bool

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
        foreground: Color | None = None,
        background: Color | None = None,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def set(
        self,
        x: int,
        y: int,
        glyph: int,
        foreground: Color,
        background: Color | None = None,
    ) -> None:
        raise NotImplementedError
