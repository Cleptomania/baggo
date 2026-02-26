from pathlib import Path

import arcade
from arcade.gl import Texture2D

from baggo.terminal import Font


class FontArcade(Font):
    _initialized: bool = False
    _image_path: Path

    _texture: Texture2D
    _columns: int
    _rows: int

    def __init__(self, tile_width: int, tile_height: int, image: Path):
        super().__init__(tile_width, tile_height, image)
        self._image_path = image

    def load(self) -> None:
        self._texture = arcade.get_window().ctx.load_texture(self._image_path)
        self._texture.filter = (arcade.gl.NEAREST, arcade.gl.NEAREST)
        self._columns = self._texture.width // self._tile_width
        self._rows = self._texture.height // self._tile_height
        self._initialized = True

    @property
    def initialized(self):
        return self._initialized

    @property
    def texture(self) -> Texture2D:
        return self._texture

    @property
    def columns(self) -> int:
        return self._columns

    @property
    def rows(self) -> int:
        return self._rows
