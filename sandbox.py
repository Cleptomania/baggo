from pathlib import Path

import baggo

SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50

TILE_WIDTH = 8
TILE_HEIGHT = 8
FONT_FILE = Path(__file__).parent / "baggo/res/terminal8x8.png"


class Sandbox(baggo.App):

    def __init__(self):
        tb = baggo.TerminalBuilder.simple(SCREEN_WIDTH, SCREEN_HEIGHT, "Baggo Sandbox", TILE_WIDTH, TILE_HEIGHT, FONT_FILE)
        super().__init__(tb.build())

        self.player_x = 40
        self.player_y = 25

    def tick(self, delta_time: float) -> None:
        self.console.clear()
        self.console.print(2, 0, "Hello, World!", baggo.colors.RED, baggo.colors.BLUE)
        self.console.set(self.player_x, self.player_y, baggo.to_cp437("@"), baggo.colors.YELLOW)


def main():
    Sandbox().run()


if __name__ == "__main__":
    main()
