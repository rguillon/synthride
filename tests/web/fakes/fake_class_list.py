# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT


class FakeClassList:
    """A DOM ``classList``."""

    def __init__(self) -> None:
        self.names: set[str] = set()

    def toggle(self, name: str, force: bool) -> None:  # noqa: FBT001
        if force:
            self.names.add(name)
        else:
            self.names.discard(name)

    def contains(self, name: str) -> bool:
        return name in self.names
