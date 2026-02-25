from baggo.terminal import Console, Terminal

class App:

    terminal: Terminal
    console: Console

    def __init__(self, terminal: Terminal):
        self.terminal = terminal
        self.terminal.register_app(self)
        self.console = terminal.console

    def run(self) -> None:
        self.terminal.run()

    def tick(self, delta_time: float) -> None:
        pass