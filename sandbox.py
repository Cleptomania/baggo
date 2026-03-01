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

        self.left_pressed = False
        self.right_pressed = False
        self.up_pressed = False
        self.down_pressed = False

        self.time = 0.0
        self.tick_interval = (
            0.1  # Run game logic every 0.1 seconds (10 times per second)
        )

    def tick(self, delta_time: float) -> None:
        self.time += delta_time
        if self.time < self.tick_interval:
            return

        self.time = 0

        # Process Inputs
        if self.left_pressed:
            self.player_x -= 1
        if self.right_pressed:
            self.player_x += 1
        if self.up_pressed:
            self.player_y -= 1
        if self.down_pressed:
            self.player_y += 1

        self.console.clear()
        self.console.print(2, 0, "Hello, World!", baggo.colors.RED, baggo.colors.BLUE)
        self.console.print(2, 5, "This is a test", baggo.colors.RED, baggo.colors.BLUE)
        self.console.set(
            self.player_x, self.player_y, baggo.to_cp437("@"), baggo.colors.YELLOW
        )

    def on_key_down(self, key: baggo.Keys, modifiers: int) -> None:
        match key:
            case baggo.Keys.LEFT:
                self.left_pressed = True
            case baggo.Keys.RIGHT:
                self.right_pressed = True
            case baggo.Keys.UP:
                self.up_pressed = True
            case baggo.Keys.DOWN:
                self.down_pressed = True

    def on_key_up(self, key: baggo.Keys, modifiers: int) -> None:
        match key:
            case baggo.Keys.LEFT:
                self.left_pressed = False
            case baggo.Keys.RIGHT:
                self.right_pressed = False
            case baggo.Keys.UP:
                self.up_pressed = False
            case baggo.Keys.DOWN:
                self.down_pressed = False


def main():
    Sandbox().run()


if __name__ == "__main__":
    main()
