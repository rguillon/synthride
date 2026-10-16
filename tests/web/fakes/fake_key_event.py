# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT


class FakeKeyEvent:
    """A keyboard event."""

    def __init__(self, code: str, *, repeat: bool = False, key: str | None = None) -> None:
        self.code = code
        self.key = key
        self.repeat = repeat
        self.prevented = False
        self.target: object = None

    def preventDefault(self) -> None:  # noqa: N802
        self.prevented = True
