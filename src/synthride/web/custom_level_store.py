# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""The custom levels saved in the browser."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, ClassVar

from synthride.core.level_parser import LevelParser

if TYPE_CHECKING:
    from synthride.core.level import Level
    from synthride.web.js_bridge import JsObject


class CustomLevelStore:
    """Keeps the custom levels, as level file texts, in the browser's ``localStorage``.

    Storage can be missing or refuse access, in a private window or with site data blocked: the store then keeps the
    levels in memory for the session, and ``persistent`` tells so. A saved level that cannot be read is skipped.
    """

    KEY: ClassVar[str] = "synthride.custom"

    def __init__(self, window: JsObject) -> None:
        """Read and write the storage of ``window``."""
        self._window = window
        self.persistent = True
        self._texts: list[str] = self._read()

    @property
    def texts(self) -> tuple[str, ...]:
        """The saved level files, in the order they were first saved."""
        return tuple(self._texts)

    def levels(self) -> list[Level]:
        """Return the saved levels."""
        parser = LevelParser()
        return [parser.parse(text) for text in self._texts]

    def put(self, slot: int | None, text: str) -> int:
        """Save the level file ``text`` in ``slot``, or in a new slot when None, and return the slot."""
        if slot is None or not 0 <= slot < len(self._texts):
            self._texts.append(text)
            slot = len(self._texts) - 1
        else:
            self._texts[slot] = text
        self._write()
        return slot

    def remove(self, slot: int) -> None:
        """Delete the level in ``slot``."""
        if 0 <= slot < len(self._texts):
            del self._texts[slot]
            self._write()

    def _storage(self) -> JsObject | None:
        try:
            return self._window.localStorage
        except Exception:  # noqa: BLE001  (browsers throw a SecurityError when storage is blocked)
            return None

    def _read(self) -> list[str]:
        storage = self._storage()
        text = None
        if storage is None:
            self.persistent = False
        else:
            try:
                text = storage.getItem(self.KEY)
            except Exception:  # noqa: BLE001
                self.persistent = False
        try:
            entries = json.loads(text) if isinstance(text, str) else []
        except json.JSONDecodeError:
            entries = []
        parser = LevelParser()
        texts = []
        for entry in entries if isinstance(entries, list) else []:
            if not isinstance(entry, str):
                continue
            try:
                parser.parse(entry)
            except ValueError:
                continue
            texts.append(entry)
        return texts

    def _write(self) -> None:
        storage = self._storage()
        self.persistent = False
        if storage is None:
            return
        try:
            storage.setItem(self.KEY, json.dumps(self._texts))
        except Exception:  # noqa: BLE001  (full or blocked storage: keep the levels for this session)
            return
        self.persistent = True
