# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""Keyboard input from the browser."""

from __future__ import annotations

from typing import TYPE_CHECKING

from synthride.core.ship_input import ShipInput

if TYPE_CHECKING:
    from synthride.web.js_bridge import JsBridge, JsObject


class BrowserKeyboard:
    """Tracks held keys for ship control and queues fresh presses for menus."""

    ACCELERATE = frozenset({"ArrowUp", "KeyW"})
    BRAKE = frozenset({"ArrowDown", "KeyS"})
    LEFT = frozenset({"ArrowLeft", "KeyA"})
    RIGHT = frozenset({"ArrowRight", "KeyD"})
    JUMP = frozenset({"Space"})
    CAPTURED = ACCELERATE | BRAKE | LEFT | RIGHT | JUMP | {"Enter", "Escape"}

    def __init__(self, bridge: JsBridge) -> None:
        """Listen to the window's key events."""
        self._held: set[str] = set()
        self._presses: list[str] = []
        window = bridge.window
        window.addEventListener("keydown", bridge.proxy(self.on_key_down))
        window.addEventListener("keyup", bridge.proxy(self.on_key_up))
        window.addEventListener("blur", bridge.proxy(lambda _event: self._held.clear()))

    def on_key_down(self, event: JsObject) -> None:
        """Record a pressed key, keeping the page from scrolling on game keys."""
        code = event.code
        if code in self.CAPTURED:
            event.preventDefault()
        if not event.repeat:
            self._presses.append(code)
        self._held.add(code)

    def on_key_up(self, event: JsObject) -> None:
        """Record a released key."""
        self._held.discard(event.code)

    def ship_input(self) -> ShipInput:
        """Return the ship commands for the keys held right now."""
        held = self._held
        return ShipInput(
            accelerate=bool(held & self.ACCELERATE),
            brake=bool(held & self.BRAKE),
            left=bool(held & self.LEFT),
            right=bool(held & self.RIGHT),
            jump=bool(held & self.JUMP),
        )

    def consume_presses(self) -> list[str]:
        """Return the keys pressed since the last call, oldest first."""
        presses, self._presses = self._presses, []
        return presses
