from dataclasses import dataclass

import baggo
import esper

from baggo import to_cp437


@dataclass
class Position:
    x: int
    y: int


@dataclass
class Renderable:
    glyph: int
    fg: baggo.Color
    bg: baggo.Color


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

    def __init__(self):
        self.player = esper.create_entity()
        esper.add_component(self.player, Position(40, 25))
        esper.add_component(
            self.player,
            Renderable(to_cp437("@"), baggo.colors.YELLOW, baggo.colors.BLACK),
        )

        for i in range(10):
            entity = esper.create_entity()
            esper.add_component(entity, Position(i * 7, 20))
            esper.add_component(
                entity, Renderable(to_cp437("@"), baggo.colors.RED, baggo.colors.BLACK)
            )


class Game(baggo.App):
    def __init__(self):
        builder = baggo.TerminalBuilder.simple(
            80, 50, "Baggo Tutorial", 12, 12, baggo.res.CP437_12X12
        )
        super().__init__(builder.build())

        self.state = GameState()

        render_processor = RenderProcessor(self.console)
        esper.add_processor(render_processor)

    def tick(self, delta: float) -> None:
        self.console.clear()
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


def main():
    Game().run()


if __name__ == "__main__":
    main()
