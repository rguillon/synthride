# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""The levels the editor saved in the browser."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from synthride.web.browser.js_bridge import JsBridge


class LocalLevels:
    """The level files saved in the browser's local storage, by file name, for a game served without dev mode.

    The storage can be missing or refuse writes (a private window, blocked site data): then nothing is loaded
    and saves report failure.
    """

    KEY = "synthride.levels"

    def __init__(self, bridge: JsBridge) -> None:
        """Keep the levels in the local storage of ``bridge``'s window."""
        self._window = bridge.window

    def load(self) -> dict[str, str]:
        """Return the saved level files' text by file name, empty when there are none or they can't be read."""
        try:
            text = self._window.localStorage.getItem(self.KEY)
            files = json.loads(text) if isinstance(text, str) else {}
        except Exception:  # noqa: BLE001  # Pyodide raises a JsException, unknown outside the browser
            return {}
        if not isinstance(files, dict):
            return {}
        return {name: text for name, text in files.items() if isinstance(name, str) and isinstance(text, str)}

    def save(self, name: str, text: str) -> bool:
        """Save the level file ``name``, replacing any saved before; return whether it was stored."""
        files = self.load()
        files[name] = text
        try:
            self._window.localStorage.setItem(self.KEY, json.dumps(files))
        except Exception:  # noqa: BLE001  # quota exceeded or storage blocked
            return False
        return True
