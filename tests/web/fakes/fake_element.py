# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import TYPE_CHECKING

from tests.web.fakes.fake_class_list import FakeClassList
from tests.web.fakes.fake_js_object import FakeJsObject

if TYPE_CHECKING:
    from collections.abc import Callable


class FakeElement:
    """A DOM element with the properties the game touches."""

    def __init__(self, element_id: str = "", tag: str = "div") -> None:
        self.id = element_id
        self.tag = tag
        self.width = self.height = 0
        self.context = FakeJsObject("context")
        self.hidden = False
        self.innerHTML = ""
        self.textContent = ""
        self.style = FakeJsObject("style")
        self.classList = FakeClassList()
        self.children: list = []
        self.value = ""
        self.clientWidth = self.clientHeight = 0
        self.captured: list[int] = []
        self.clicks = 0
        self.listeners: dict[str, list[Callable]] = {}

    def appendChild(self, child: object) -> None:  # noqa: N802
        self.children.append(child)

    def getContext(self, _kind: str) -> FakeJsObject:  # noqa: N802
        return self.context

    def addEventListener(self, event_type: str, listener: Callable, *_options: object) -> None:  # noqa: N802
        self.listeners.setdefault(event_type, []).append(listener)

    def dispatch(self, event_type: str, event: object) -> None:
        for listener in self.listeners.get(event_type, []):
            listener(event)

    def setPointerCapture(self, pointer_id: int) -> None:  # noqa: N802
        self.captured.append(pointer_id)

    def click(self) -> None:
        self.clicks += 1
