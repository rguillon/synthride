from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any


class JsBridge:
    """The single gateway to the browser: window, document, Three.js and Pyodide's conversion helpers."""

    def __init__(self, window: Any, three: Any, create_proxy: Callable[[Any], Any], to_js: Callable[..., Any]) -> None:
        self.window = window
        self.document = window.document
        self.three = three
        self._create_proxy = create_proxy
        self._to_js = to_js

    def obj(self, **properties: Any) -> Any:
        """A plain JavaScript object literal, nested dictionaries included."""
        return self._to_js(properties, dict_converter=self.window.Object.fromEntries)

    def proxy(self, function: Callable[..., Any]) -> Any:
        """A persistent JavaScript callable wrapping ``function`` (for listeners and frame callbacks)."""
        return self._create_proxy(function)

    def float32_array(self, values: Sequence[float]) -> Any:
        return self.window.Float32Array.new(self._to_js(list(values)))
