# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT


class FakeKeyEvent:
    """A keyboard event."""

    def __init__(self, code: str, *, repeat: bool = False) -> None:
        self.code = code
        self.repeat = repeat
        self.prevented = False

    def preventDefault(self) -> None:  # noqa: N802
        self.prevented = True
