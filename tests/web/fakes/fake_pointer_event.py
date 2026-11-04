# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

from __future__ import annotations


class FakePointerEvent:
    """A pointer event on ``target`` by the pointer ``pointer_id``, at the client position (``x``, ``y``)."""

    def __init__(self, target: object, pointer_id: int = 1, x: float = 0, y: float = 0) -> None:
        self.target = target
        self.pointerId = pointer_id
        self.clientX = x
        self.clientY = y
        self.prevented = False

    def preventDefault(self) -> None:  # noqa: N802
        self.prevented = True
