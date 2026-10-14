# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING

from tests.web.fakes.fake_audio_context import FakeAudioContext
from tests.web.fakes.fake_document import FakeDocument
from tests.web.fakes.fake_js_object import FakeJsObject

if TYPE_CHECKING:
    from collections.abc import Callable


class FakeWindow(FakeJsObject):
    """A browser window: listeners and animation frames can be triggered by tests."""

    def __init__(self) -> None:
        super().__init__("window")
        self.document = FakeDocument()
        self.innerWidth = 800
        self.innerHeight = 400
        self.devicePixelRatio = 3
        self.listeners: dict[str, list[Callable]] = {}
        self.frame_callbacks: list[Callable] = []
        self.AudioContext = SimpleNamespace(new=FakeAudioContext)

    def addEventListener(self, event_type: str, listener: Callable) -> None:  # noqa: N802
        self.listeners.setdefault(event_type, []).append(listener)

    def dispatch(self, event_type: str, event: object = None) -> None:
        for listener in self.listeners.get(event_type, []):
            listener(event)

    def requestAnimationFrame(self, callback: Callable) -> None:  # noqa: N802
        self.frame_callbacks.append(callback)
