from abc import abstractmethod
from typing import Any, Protocol, TYPE_CHECKING

from .console import Console

if TYPE_CHECKING:
    from baggo import App

class Terminal(Protocol):
    _app: App
    _width: int
    _height: int

    console: Console

    @abstractmethod
    def register_app(self, app: App):
        raise NotImplementedError

    @abstractmethod
    def run(self) -> None:
        raise NotImplementedError

    @property
    def app(self) ->Any:
        return self._app

    @app.setter
    def app(self, value: App) -> None:
        raise RuntimeError("Changing the app of a Terminal is not supported")

    @property
    def width(self) -> int:
        return self._width

    @width.setter
    def width(self, value: int) -> None:
        raise RuntimeError("Changing the size of a Terminal is not supported")

    @property
    def height(self) -> int:
        return self._height

    @height.setter
    def height(self, value: int) -> None:
        raise RuntimeError("Changing the size of a Terminal is not supported")

