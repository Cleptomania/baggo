import baggo


class Game(baggo.App):
    def __init__(self):
        builder = baggo.TerminalBuilder.simple(
            80, 50, "Baggo Tutorial", 8, 8, baggo.res.TERMINAL_8X8
        )
        super().__init__(builder.build())

    def tick(self, delta: float) -> None:
        self.console.clear()
        self.console.print(1, 1, "Hello, World!")


def main():
    Game().run()


if __name__ == "__main__":
    main()
