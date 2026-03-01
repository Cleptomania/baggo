import baggo


class Game(baggo.App):
    def __init__(self):
        builder = baggo.TerminalBuilder.simple(
            80, 50, "Baggo Tutorial", 12, 12, baggo.res.CP437_12X12
        )
        super().__init__(builder.build())

    def tick(self, delta: float) -> None:
        self.console.clear()
        self.console.print(1, 1, "Hello, World!")


def main():
    Game().run()


if __name__ == "__main__":
    main()
