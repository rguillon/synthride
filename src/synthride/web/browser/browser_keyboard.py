# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""Keyboard input from the browser."""

from __future__ import annotations

from typing import TYPE_CHECKING

from synthride.core.gameplay.ship_input import ShipInput

if TYPE_CHECKING:
    from synthride.web.browser.js_bridge import JsBridge, JsObject


class BrowserKeyboard:
    """Tracks held keys for ship control and queues fresh presses for menus.

    Keys are known by where they sit (``event.code``), so that steering keys stay in place on any layout. Shortcuts
    named after a letter ask :meth:`letter` what the key types on the player's layout instead.
    """

    ACCELERATE = frozenset({"ArrowUp", "KeyW"})
    BRAKE = frozenset({"ArrowDown", "KeyS"})
    LEFT = frozenset({"ArrowLeft", "KeyA"})
    RIGHT = frozenset({"ArrowRight", "KeyD"})
    JUMP = frozenset({"Space"})
    CAPTURED = ACCELERATE | BRAKE | LEFT | RIGHT | JUMP | {"Enter", "Escape"}
    FIELDS = frozenset({"INPUT", "SELECT", "TEXTAREA"})

    def __init__(self, bridge: JsBridge) -> None:
        """Listen to the window's key events."""
        self._held: set[str] = set()
        self._presses: list[str] = []
        self._characters: dict[str, str] = {}  # what each key typed when last pressed, by code
        window = bridge.window
        window.addEventListener("keydown", bridge.proxy(self.on_key_down))
        window.addEventListener("keyup", bridge.proxy(self.on_key_up))
        window.addEventListener("blur", bridge.proxy(lambda _event: self.release_all()))

    def on_key_down(self, event: JsObject) -> None:
        """Record a pressed key, keeping the page from scrolling on game keys.

        Keys typed in a form field, such as the level editor's, are left to the field; Escape leaves the field.
        """
        code = event.code
        target = getattr(event, "target", None)
        if target is not None and getattr(target, "tagName", None) in self.FIELDS:
            if code == "Escape":
                target.blur()
            return
        if code in self.CAPTURED:
            event.preventDefault()
        character = getattr(event, "key", None)
        if isinstance(character, str):
            self._characters[code] = character
        if not event.repeat:
            self.hold(code)

    def on_key_up(self, event: JsObject) -> None:
        """Record a released key."""
        self.release(event.code)

    def hold(self, code: str) -> None:
        """Hold the key at ``code``, queueing it as a fresh press unless it is already held."""
        if code not in self._held:
            self._held.add(code)
            self._presses.append(code)

    def release(self, code: str) -> None:
        """Release the key at ``code``."""
        self._held.discard(code)

    def release_all(self) -> None:
        """Release every key."""
        self._held.clear()

    def press(self, code: str) -> None:
        """Queue the key at ``code`` as a fresh press without holding it."""
        self._presses.append(code)

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

    def letter(self, code: str) -> str:
        """Return the letter, in lower case, the key at ``code`` types on the player's layout, or "" if none.

        A letter key not pressed yet is taken to type its QWERTY letter.
        """
        character = self._characters.get(code)
        if character is None:
            character = code[3:] if code.startswith("Key") and len(code) == len("KeyA") else ""
        return character.lower() if len(character) == 1 and character.isalpha() else ""

    def consume_presses(self) -> list[str]:
        """Return the keys pressed since the last call, oldest first."""
        presses, self._presses = self._presses, []
        return presses
