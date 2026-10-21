# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""On-screen touch pads that drive the ship through the keyboard."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

    from synthride.web.browser.browser_keyboard import BrowserKeyboard
    from synthride.web.browser.js_bridge import JsBridge, JsObject


class TouchControls:
    """Turns touches on the page's pads into the keys the keyboard tracks, so the game never learns about touch.

    Each pad in ``#touch`` names its key in ``data-code`` and is held while a pointer is down on it; buttons naming a
    key in ``data-press`` press it once when clicked. The first touch turns touch mode on: it adds the ``touch`` class
    to ``<body>``, which shows the pads and the touch layout, and asks for full screen.
    """

    PAD = "[data-code]"
    BUTTON = "[data-press]"
    HELD = "held"
    # A lookup that finds nothing gives JavaScript null, which Pyodide hands over as the falsy ``jsnull``, not None:
    # found elements are tested for truth.

    def __init__(self, bridge: JsBridge, keyboard: BrowserKeyboard, unlock_audio: Callable[[], object]) -> None:
        """Listen to touches on the window and pointers on the pads, calling ``unlock_audio`` on the first touchend.

        iOS Safari only lets audio start inside a touch handler, while the game starts it from an animation frame.
        """
        self._bridge = bridge
        self._keyboard = keyboard
        self._unlock_audio: Callable[[], object] | None = unlock_audio
        self.active = False
        self._pointers: dict[int, JsObject] = {}  # each pointer that is down, and the pad under it (None: no pad)
        window, document = bridge.window, bridge.document
        passive = bridge.obj(passive=True)
        window.addEventListener("touchstart", bridge.proxy(self.on_touch_start), passive)
        window.addEventListener("touchend", bridge.proxy(self.on_touch_end), passive)
        pads = document.getElementById("touch")
        pads.addEventListener("pointerdown", bridge.proxy(self.on_pointer_down))
        pads.addEventListener("pointerover", bridge.proxy(self.on_pointer_over))
        pads.addEventListener("pointerout", bridge.proxy(self.on_pointer_out))
        pads.addEventListener("pointerup", bridge.proxy(self.on_pointer_end))
        pads.addEventListener("pointercancel", bridge.proxy(self.on_pointer_end))
        document.body.addEventListener("click", bridge.proxy(self.on_click))
        document.addEventListener("visibilitychange", bridge.proxy(self.on_visibility_change))

    def on_touch_start(self, _event: JsObject) -> None:
        """Turn touch mode on at the first touch, and ask for full screen where the browser allows it."""
        if self.active:
            return
        self.active = True
        document = self._bridge.document
        document.body.classList.toggle("touch", True)  # noqa: FBT003
        request = getattr(document.documentElement, "requestFullscreen", None)
        if request is not None:
            request().catch(self._bridge.proxy(lambda _error: None))

    def on_touch_end(self, _event: JsObject) -> None:
        """Unlock audio, the first time."""
        if self._unlock_audio is not None:
            unlock, self._unlock_audio = self._unlock_audio, None
            unlock()

    def on_pointer_down(self, event: JsObject) -> None:
        """Hold the pad under a new pointer, letting the pointer go on to the next pad if the thumb slides."""
        pad = event.target.closest(self.PAD)
        if not pad:
            return
        event.preventDefault()
        pad.releasePointerCapture(event.pointerId)  # touch pointers are captured by their first element
        self._pointers[event.pointerId] = None
        self._enter(event.pointerId, pad)

    def on_pointer_over(self, event: JsObject) -> None:
        """Hold the pad a pointer that is down slides onto."""
        pad = event.target.closest(self.PAD)
        if pad and event.pointerId in self._pointers:
            self._enter(event.pointerId, pad)

    def on_pointer_out(self, event: JsObject) -> None:
        """Let go of the pad a pointer slides off."""
        if event.pointerId in self._pointers:
            self._leave(event.pointerId)

    def on_pointer_end(self, event: JsObject) -> None:
        """Let go of the pad under a lifted or cancelled pointer, and forget the pointer."""
        if event.pointerId in self._pointers:
            self._leave(event.pointerId)
            del self._pointers[event.pointerId]

    def on_click(self, event: JsObject) -> None:
        """Press the key of a clicked ``data-press`` button."""
        button = event.target.closest(self.BUTTON)
        if button:
            self._keyboard.press(str(button.dataset.press))

    def on_visibility_change(self, _event: JsObject) -> None:
        """Let go of everything when the page is hidden: the pointers' ends would never arrive."""
        if self._bridge.document.visibilityState != "hidden":
            return
        for pointer_id in list(self._pointers):
            self._leave(pointer_id)
        self._pointers.clear()
        self._keyboard.release_all()

    def _enter(self, pointer_id: int, pad: JsObject) -> None:
        self._leave(pointer_id)
        self._pointers[pointer_id] = pad
        pad.classList.toggle(self.HELD, True)  # noqa: FBT003
        self._keyboard.hold(str(pad.dataset.code))

    def _leave(self, pointer_id: int) -> None:
        pad = self._pointers.get(pointer_id)
        if pad is None:
            return
        self._pointers[pointer_id] = None
        # Compared by code: Pyodide hands each event a new proxy, even for the same element
        code = str(pad.dataset.code)
        if all(other is None or str(other.dataset.code) != code for other in self._pointers.values()):
            pad.classList.toggle(self.HELD, False)  # noqa: FBT003
            self._keyboard.release(code)
