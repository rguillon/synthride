# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

from __future__ import annotations

from tests.web.fakes.fake_element import FakeElement


class FakeDocument:
    """A DOM document whose ``getElementById`` returns one stable element per id, and which records created elements."""

    def __init__(self) -> None:
        self.elements: dict[str, FakeElement] = {}
        self.created: list[FakeElement] = []

    def getElementById(self, element_id: str) -> FakeElement:  # noqa: N802
        return self.elements.setdefault(element_id, FakeElement(element_id))

    def createElement(self, tag: str) -> FakeElement:  # noqa: N802
        element = FakeElement(tag=tag)
        self.created.append(element)
        return element
