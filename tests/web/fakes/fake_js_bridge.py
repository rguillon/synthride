# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import TYPE_CHECKING

from synthride.web.js_bridge import JsBridge
from tests.web.fakes.fake_js_object import FakeJsObject
from tests.web.fakes.fake_window import FakeWindow

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence


class FakeJsBridge(JsBridge):
    """A bridge onto fake browser objects: JS literals are plain dicts and proxies are the functions."""

    def __init__(self) -> None:
        super().__init__(FakeWindow(), FakeJsObject("THREE"), lambda function: function, lambda value, **_: value)

    def obj(self, **properties: object) -> dict:
        return properties

    def proxy(self, function: Callable[..., object]) -> Callable[..., object]:
        return function

    def float32_array(self, values: Sequence[float]) -> list[float]:
        return list(values)
