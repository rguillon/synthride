class FakeKeyEvent:
    """A keyboard event."""

    def __init__(self, code: str, repeat: bool = False) -> None:
        self.code = code
        self.repeat = repeat
        self.prevented = False

    def preventDefault(self) -> None:
        self.prevented = True
