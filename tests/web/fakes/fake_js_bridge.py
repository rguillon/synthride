from __future__ import annotations

from collections.abc import Callable
from typing import Any

from synthride.web.js_bridge import JsBridge
from tests.web.fakes.fake_js_object import FakeJsObject
from tests.web.fakes.fake_window import FakeWindow


class FakeJsBridge(JsBridge):
    """A bridge onto fake browser objects: JS literals are plain dicts and proxies are the functions."""

    def __init__(self) -> None:
        super().__init__(FakeWindow(), FakeJsObject("THREE"), lambda function: function, lambda value, **_: value)

    def obj(self, **properties: Any) -> dict:
        return properties

    def proxy(self, function: Callable[..., Any]) -> Callable[..., Any]:
        return function

    def float32_array(self, values) -> list[float]:
        return list(values)
