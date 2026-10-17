# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

from __future__ import annotations


class FakeLocalStorage:
    """The browser's ``localStorage``: string items, which can be made to refuse writes."""

    def __init__(self, items: dict[str, str] | None = None, *, full: bool = False) -> None:
        self.items = dict(items or {})
        self.full = full

    def getItem(self, key: str) -> str | None:  # noqa: N802
        return self.items.get(key)

    def setItem(self, key: str, value: str) -> None:  # noqa: N802
        if self.full:
            message = "QuotaExceededError"
            raise RuntimeError(message)
        self.items[key] = value
