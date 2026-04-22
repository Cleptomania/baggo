from __future__ import annotations

from typing import TYPE_CHECKING

from baggo._core import WgpuTerminal as _CoreWgpuTerminal
from baggo.terminal import Console, Terminal

from .font_wgpu import FontWgpu

if TYPE_CHECKING:
    from baggo import App


class TerminalWgpu(Terminal):
    """Terminal backend driven by a Rust winit/wgpu event loop."""

    _font: FontWgpu

    def __init__(
        self,
        width: int,
        height: int,
        title: str,
        console: Console,
        font: FontWgpu,
    ):
        self._width = width
        self._height = height
        self.console = console
        self._font = font

        if not self._font.initialized:
            self._font.load()

        self._inner = _CoreWgpuTerminal(
            title,
            width,
            height,
            console.width,
            console.height,
            font.tile_width,
            font.tile_height,
            str(font._image_path),
        )

    def register_app(self, app: App) -> None:
        self._app = app

    def run(self) -> None:
        self._inner.run(self._app, self.console)
