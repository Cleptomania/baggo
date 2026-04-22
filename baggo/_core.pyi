from typing import Any, Callable

class Algorithm2D:
    @property
    def width(self) -> int: ...
    @property
    def height(self) -> int: ...
    def in_bounds(self, x: int, y: int) -> bool: ...
    def index(self, x: int, y: int) -> int: ...
    def point(self, index: int) -> tuple[int, int]: ...

def field_of_view(
    x: int,
    y: int,
    radius: int,
    fov_check: Algorithm2D,
    opaque_check: Callable[[int, int], bool],
) -> list[tuple[int, int]]: ...

class WgpuTerminal:
    def __init__(
        self,
        title: str,
        pixel_width: int,
        pixel_height: int,
        grid_width: int,
        grid_height: int,
        tile_width: int,
        tile_height: int,
        font_image_path: str,
    ) -> None: ...
    def run(self, app: Any, console: Any) -> None: ...
