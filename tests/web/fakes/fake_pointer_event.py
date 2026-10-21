# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

from __future__ import annotations


class FakePointerEvent:
    """A pointer event on ``target`` by the pointer ``pointer_id``."""

    def __init__(self, target: object, pointer_id: int = 1) -> None:
        self.target = target
        self.pointerId = pointer_id
        self.prevented = False

    def preventDefault(self) -> None:  # noqa: N802
        self.prevented = True
