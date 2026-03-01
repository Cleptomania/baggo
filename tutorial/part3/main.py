from dataclasses import dataclass
from enum import Enum
import random

import baggo
import esper

from baggo import to_cp437

SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50
TILE_WIDTH = 12
TILE_HEIGHT = 12
FONT_FILE = baggo.res.CP437_12X12


class TileType(Enum):
    FLOOR = (0,)
    WALL = 1


@dataclass
class Position:
    x: int
    y: int


@dataclass
class Renderable:
    glyph: int
    fg: baggo.Color
    bg: baggo.Color


def level_index(x: int, y: int) -> int:
    return (y * SCREEN_WIDTH) + x


class RenderProcessor(esper.Processor):
    def __init__(self, console: baggo.Console):
        self._console = console

    def process(self):
        for ent, (position, renderable) in esper.get_components(Position, Renderable):
            self._console.set(
                position.x, position.y, renderable.glyph, renderable.fg, renderable.bg
            )


class GameState:
    player: int
    level: list[TileType]

    def __init__(self):
        self.level = generate_level()

        self.player = esper.create_entity()
        esper.add_component(self.player, Position(40, 25))
        esper.add_component(
            self.player,
            Renderable(to_cp437("@"), baggo.colors.YELLOW, baggo.colors.BLACK),
        )


class Game(baggo.App):
    def __init__(self):
        builder = baggo.TerminalBuilder.simple(
            SCREEN_WIDTH,
            SCREEN_HEIGHT,
            "Baggo Tutorial",
            TILE_WIDTH,
            TILE_HEIGHT,
            FONT_FILE,
        )
        super().__init__(builder.build())

        self.state = GameState()

        render_processor = RenderProcessor(self.console)
        esper.add_processor(render_processor)

    def tick(self, delta: float) -> None:
        self.console.clear()
        self.draw_level()
        esper.process()

    def on_key_down(self, key: baggo.Keys, modifiers: int) -> None:
        match key:
            case baggo.Keys.LEFT | baggo.Keys.A:
                self.move_player(-1, 0)
            case baggo.Keys.RIGHT | baggo.Keys.D:
                self.move_player(1, 0)
            case baggo.Keys.UP | baggo.Keys.W:
                self.move_player(0, -1)
            case baggo.Keys.DOWN | baggo.Keys.S:
                self.move_player(0, 1)

    def move_player(self, dx: int, dy: int):
        position = esper.component_for_entity(self.state.player, Position)
        position.x += dx
        position.y += dy

    def draw_level(self):
        x = 0
        y = 0
        for tile in self.state.level:
            match tile:
                case TileType.FLOOR:
                    self.console.set(
                        x, y, to_cp437("."), baggo.colors.GRAY, baggo.colors.BLACK
                    )
                case TileType.WALL:
                    self.console.set(
                        x, y, to_cp437("#"), baggo.colors.GREEN, baggo.colors.BLACK
                    )
            x += 1
            if x >= SCREEN_WIDTH:
                x = 0
                y += 1


def generate_level() -> list[TileType]:
    # First populate the level with floor
    level = [TileType.FLOOR] * (SCREEN_WIDTH * SCREEN_HEIGHT)

    # Then add in walls around the borders
    for x in range(SCREEN_WIDTH):
        level[level_index(x, 0)] = TileType.WALL
        level[level_index(x, SCREEN_HEIGHT - 1)] = TileType.WALL

    for y in range(SCREEN_HEIGHT):
        level[level_index(0, y)] = TileType.WALL
        level[level_index(SCREEN_WIDTH - 1, y)] = TileType.WALL

    # Lastly place some walls randomly throughout the level
    for i in range(400):
        x = random.randint(1, SCREEN_WIDTH - 1)
        y = random.randint(1, SCREEN_HEIGHT - 1)
        index = level_index(x, y)
        if index != level_index(40, 25):  # Don't put a wall where the player spawn is
            level[index] = TileType.WALL

    return level


def main():
    Game().run()


if __name__ == "__main__":
    main()
