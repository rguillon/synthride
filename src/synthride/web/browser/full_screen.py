# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""The full screen button and its F shortcut."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from synthride.web.browser.js_bridge import JsBridge, JsObject


class FullScreen:
    """Switches the page in and out of full screen from the ``#fullscreen`` button or the F key.

    Browsers only grant full screen inside a user gesture, so both are handled in their own event listeners rather
    than by the game loop, which reads key presses in the next animation frame. The ``fullscreen`` class on ``<body>``
    follows the browser, which also leaves full screen on Escape.
    """

    KEY = "f"
    FIELDS = frozenset({"INPUT", "SELECT", "TEXTAREA"})
    MODIFIERS = ("ctrlKey", "metaKey", "altKey")  # Ctrl+F finds in the page
    ACTIVE = "fullscreen"
    UNSUPPORTED = "no-fullscreen"
    REQUESTS = ("requestFullscreen", "webkitRequestFullscreen")  # Safari on iPad only has the prefixed one
    # A document out of full screen has a null ``fullscreenElement``, which Pyodide hands over as the falsy ``jsnull``

    def __init__(self, bridge: JsBridge) -> None:
        """Listen to the button, the window's key presses and the document's full screen changes."""
        self._bridge = bridge
        document = bridge.document
        self._button = document.getElementById("fullscreen")
        if self._request_method() is None:  # iPhones, Safari and Firefox alike, have no full screen for pages
            document.body.classList.add(self.UNSUPPORTED)
        self._button.addEventListener("click", bridge.proxy(self.on_click))
        bridge.window.addEventListener("keydown", bridge.proxy(self.on_key_down))
        document.addEventListener("fullscreenchange", bridge.proxy(self.on_change))

    def on_click(self, _event: JsObject) -> None:
        """Toggle full screen, and give the focus back: a focused button would be pressed again by Space or Enter."""
        self.toggle()
        self._button.blur()

    def toggle(self) -> None:
        """Enter full screen, or leave it when the page is already full screen."""
        document = self._bridge.document
        catch = self._bridge.proxy(lambda _error: None)  # refused, or not supported: the page stays as it is
        if document.fullscreenElement:
            document.exitFullscreen().catch(catch)
        else:
            request = self._request_method()
            if request is not None:
                result = request()
                if result:  # the prefixed version may return nothing
                    result.catch(catch)

    def _request_method(self) -> JsObject | None:
        root = self._bridge.document.documentElement
        for name in self.REQUESTS:
            request = getattr(root, name, None)
            if request is not None:
                return request
        return None

    def on_key_down(self, event: JsObject) -> None:
        """Toggle full screen on F, whatever the layout puts under it, unless typed in a form field or as a shortcut."""
        if any(getattr(event, modifier, False) for modifier in self.MODIFIERS):
            return
        target = getattr(event, "target", None)
        if target is not None and getattr(target, "tagName", None) in self.FIELDS:
            return
        key = getattr(event, "key", None)
        if isinstance(key, str) and key.lower() == self.KEY and not event.repeat:
            self.toggle()

    def on_change(self, _event: JsObject) -> None:
        """Mark the body while the page is full screen, so the button can show which way it goes."""
        self._bridge.document.body.classList.toggle(self.ACTIVE, bool(self._bridge.document.fullscreenElement))
