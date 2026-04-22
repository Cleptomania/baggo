import struct
from pathlib import Path

from baggo.terminal import Font


class FontWgpu(Font):
    """Font descriptor for the wgpu backend.

    The actual texture upload happens inside the Rust ``_core.WgpuTerminal`` when
    the window is created. ``load()`` only resolves dimensions that the
    ``TerminalBuilder`` needs before the window exists.
    """

    _initialized: bool = False
    _columns: int
    _rows: int

    def __init__(self, tile_width: int, tile_height: int, image: Path):
        super().__init__(tile_width, tile_height, image)

    def load(self) -> None:
        self._width, self._height = _read_png_dimensions(self._image_path)
        self._columns = self._width // self._tile_width
        self._rows = self._height // self._tile_height
        self._initialized = True

    @property
    def initialized(self) -> bool:
        return self._initialized

    @property
    def columns(self) -> int:
        return self._columns

    @property
    def rows(self) -> int:
        return self._rows


_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _read_png_dimensions(path: Path) -> tuple[int, int]:
    with open(path, "rb") as f:
        header = f.read(24)
    if len(header) < 24 or header[:8] != _PNG_SIGNATURE:
        raise ValueError(f"{path} is not a PNG file")
    # IHDR is the first chunk; width and height are the first two big-endian uint32s of its data.
    width, height = struct.unpack(">II", header[16:24])
    return width, height
