# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""The gateway between the Python game and the browser."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeAlias

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

JsObject: TypeAlias = Any
"""A JavaScript object reached through Pyodide (or a test double standing in for one)."""


class JsBridge:
    """The single gateway to the browser: window, document, Three.js and Pyodide's conversion helpers."""

    def __init__(
        self, window: JsObject, three: JsObject, create_proxy: Callable[..., JsObject], to_js: Callable[..., JsObject]
    ) -> None:
        """Wrap the browser ``window``, Three.js and Pyodide's ``create_proxy`` and ``to_js``."""
        self.window = window
        self.document = window.document
        self.three = three
        self._create_proxy = create_proxy
        self._to_js = to_js

    def obj(self, **properties: object) -> JsObject:
        """Return a plain JavaScript object literal, nested dictionaries included."""
        return self._to_js(properties, dict_converter=self.window.Object.fromEntries)

    def proxy(self, function: Callable[..., object]) -> JsObject:
        """Return a persistent JavaScript callable wrapping ``function`` (for listeners and frame callbacks)."""
        return self._create_proxy(function)

    def float32_array(self, values: Sequence[float]) -> JsObject:
        """Return a JavaScript ``Float32Array`` holding ``values``."""
        return self.window.Float32Array.new(self._to_js(list(values)))
