from __future__ import annotations

from collections.abc import Callable
from types import SimpleNamespace

from tests.web.fakes.fake_audio_context import FakeAudioContext
from tests.web.fakes.fake_document import FakeDocument
from tests.web.fakes.fake_js_object import FakeJsObject


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

    def addEventListener(self, event_type: str, listener: Callable) -> None:
        self.listeners.setdefault(event_type, []).append(listener)

    def dispatch(self, event_type: str, event=None) -> None:
        for listener in self.listeners.get(event_type, []):
            listener(event)

    def requestAnimationFrame(self, callback: Callable) -> None:
        self.frame_callbacks.append(callback)
