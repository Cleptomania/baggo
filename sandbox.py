import baggo

SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50

TILE_WIDTH = 8
TILE_HEIGHT = 8
FONT_FILE = baggo.res.TERMINAL_8X8


class Sandbox(baggo.App):
    def __init__(self):
        tb = baggo.TerminalBuilder.simple(
            SCREEN_WIDTH,
            SCREEN_HEIGHT,
            "Baggo Sandbox",
            TILE_WIDTH,
            TILE_HEIGHT,
            FONT_FILE,
        )
        super().__init__(tb.build())

        self.player_x = 40
        self.player_y = 25

    def tick(self, delta_time: float) -> None:
        self.console.clear()
        self.console.print(2, 0, "Hello, World!", baggo.colors.RED, baggo.colors.BLUE)
        self.console.set(
            self.player_x, self.player_y, baggo.to_cp437("@"), baggo.colors.YELLOW
        )

    def on_key_down(self, key: baggo.Keys, modifiers: int) -> None:
        match key:
            case baggo.Keys.LEFT:
                self.player_x -= 1
            case baggo.Keys.RIGHT:
                self.player_x += 1
            case baggo.Keys.UP:
                self.player_y -= 1
            case baggo.Keys.DOWN:
                self.player_y += 1


def main():
    Sandbox().run()


if __name__ == "__main__":
    main()
