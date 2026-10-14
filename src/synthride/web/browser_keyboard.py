from __future__ import annotations

from typing import Any

from synthride.core.ship_input import ShipInput
from synthride.web.js_bridge import JsBridge


class BrowserKeyboard:
    """Tracks held keys for ship control and queues fresh presses for menus."""

    ACCELERATE = frozenset({"ArrowUp", "KeyW"})
    BRAKE = frozenset({"ArrowDown", "KeyS"})
    LEFT = frozenset({"ArrowLeft", "KeyA"})
    RIGHT = frozenset({"ArrowRight", "KeyD"})
    JUMP = frozenset({"Space"})
    CAPTURED = ACCELERATE | BRAKE | LEFT | RIGHT | JUMP | {"Enter", "Escape"}

    def __init__(self, bridge: JsBridge) -> None:
        self._held: set[str] = set()
        self._presses: list[str] = []
        window = bridge.window
        window.addEventListener("keydown", bridge.proxy(self.on_key_down))
        window.addEventListener("keyup", bridge.proxy(self.on_key_up))
        window.addEventListener("blur", bridge.proxy(lambda _event: self._held.clear()))

    def on_key_down(self, event: Any) -> None:
        code = event.code
        if code in self.CAPTURED:
            event.preventDefault()
        if not event.repeat:
            self._presses.append(code)
        self._held.add(code)

    def on_key_up(self, event: Any) -> None:
        self._held.discard(event.code)

    def ship_input(self) -> ShipInput:
        held = self._held
        return ShipInput(
            accelerate=bool(held & self.ACCELERATE),
            brake=bool(held & self.BRAKE),
            left=bool(held & self.LEFT),
            right=bool(held & self.RIGHT),
            jump=bool(held & self.JUMP),
        )

    def consume_presses(self) -> list[str]:
        presses, self._presses = self._presses, []
        return presses
