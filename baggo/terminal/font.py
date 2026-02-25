from abc import abstractmethod
from pathlib import Path
from typing import Protocol

class Font(Protocol):

    _width: int
    _height: int

    _tile_width: int
    _tile_height: int

    _image_path: Path

    def __init__(self, tile_width: int, tile_height: int, image: Path):
        self._tile_width = tile_width
        self._tile_height = tile_height
        self._image_path = image

    @property
    def width(self) -> int:
        return self._width

    @width.setter
    def width(self, value: int) -> None:
        raise RuntimeError("Changing the size of a Font is not supported")

    @property
    def height(self) -> int:
        return self._height

    @height.setter
    def height(self, value: int) -> None:
        raise RuntimeError("Changing the size of a Font is not supported")

    @property
    def tile_width(self) -> int:
        return self._tile_width

    @tile_width.setter
    def tile_width(self, value: int) -> None:
        raise RuntimeError("Changing the size of a Font is not supported")

    @property
    def tile_height(self) -> int:
        return self._tile_height

    @tile_height.setter
    def tile_height(self, value: int) -> None:
        raise RuntimeError("Changing the size of a Font is not supported")

    @abstractmethod
    def load(self) -> None:
        raise NotImplementedError("Font loading not implemented")