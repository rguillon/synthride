# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable


class FakePromise:
    """A promise the test settles by hand, after ``then`` and ``catch`` have been given their callbacks."""

    def __init__(self) -> None:
        self.on_value: Callable[[object], object] | None = None
        self.on_error: Callable[[object], object] | None = None

    def then(self, callback: Callable[[object], object]) -> FakePromise:
        self.on_value = callback
        return self

    def catch(self, callback: Callable[[object], object]) -> FakePromise:
        self.on_error = callback
        return self

    def resolve(self, value: object) -> None:
        assert self.on_value is not None
        self.on_value(value)

    def reject(self, error: object) -> None:
        assert self.on_error is not None
        self.on_error(error)


class FakeFetch:
    """The browser's ``fetch``: it records each request, and the test answers them."""

    def __init__(self) -> None:
        self.requests: list[SimpleNamespace] = []

    def __call__(self, url: str, options: dict) -> FakePromise:
        promise = FakePromise()
        self.requests.append(SimpleNamespace(url=url, options=options, promise=promise))
        return promise

    def answer(self, status: int = 200, text: str = "") -> None:
        """Answer the last request with an HTTP ``status`` and a body of ``text``."""
        body = FakePromise()
        response = SimpleNamespace(ok=200 <= status < 300, status=status, text=lambda: body)
        self.requests[-1].promise.resolve(response)
        if body.on_value is not None:
            body.resolve(text)
