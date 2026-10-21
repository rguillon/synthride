# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import TYPE_CHECKING

from tests.web.fakes.fake_element import FakeElement

if TYPE_CHECKING:
    from collections.abc import Callable


class FakeDocument:
    """A DOM document whose ``getElementById`` returns one stable element per id, and which records created elements.

    Its listeners can be triggered by tests.
    """

    def __init__(self) -> None:
        self.elements: dict[str, FakeElement] = {}
        self.created: list[FakeElement] = []
        self.body = FakeElement("body", tag="body")
        self.documentElement = FakeElement("html", tag="html")
        self.visibilityState = "visible"
        self.listeners: dict[str, list[Callable]] = {}

    def addEventListener(self, event_type: str, listener: Callable, *_options: object) -> None:  # noqa: N802
        self.listeners.setdefault(event_type, []).append(listener)

    def dispatch(self, event_type: str, event: object = None) -> None:
        for listener in self.listeners.get(event_type, []):
            listener(event)

    def getElementById(self, element_id: str) -> FakeElement:  # noqa: N802
        return self.elements.setdefault(element_id, FakeElement(element_id))

    def createElement(self, tag: str) -> FakeElement:  # noqa: N802
        element = FakeElement(tag=tag)
        self.created.append(element)
        return element
