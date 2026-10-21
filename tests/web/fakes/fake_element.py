# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING

from tests.web.fakes.fake_class_list import FakeClassList
from tests.web.fakes.fake_fetch import FakePromise
from tests.web.fakes.fake_js_object import FakeJsObject

if TYPE_CHECKING:
    from collections.abc import Callable


class FakeElement:
    """A DOM element with the properties the game touches; keywords become its ``data-`` attributes."""

    def __init__(self, element_id: str = "", tag: str = "div", **dataset: str) -> None:
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
        self.dataset = SimpleNamespace(**dataset)
        self.captured: list[int] = []
        self.released: list[int] = []
        self.fullscreen_requests = 0
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

    def releasePointerCapture(self, pointer_id: int) -> None:  # noqa: N802
        self.released.append(pointer_id)

    def requestFullscreen(self) -> FakePromise:  # noqa: N802
        self.fullscreen_requests += 1
        return FakePromise()

    def closest(self, selector: str) -> FakeElement | None:
        """Match ``[data-<name>]`` against the own ``data-`` attributes, or a tag name; ancestors are not modelled."""
        if selector.startswith("[data-"):
            return self if hasattr(self.dataset, selector[len("[data-") : -1]) else None
        return self if selector == self.tag else None

    def click(self) -> None:
        self.clicks += 1
