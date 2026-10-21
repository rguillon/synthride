# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

from __future__ import annotations


class FakeJsNull:
    """JavaScript ``null`` as Pyodide hands it over: ``pyodide.ffi.jsnull``, falsy but not None."""

    def __bool__(self) -> bool:
        return False

    def __repr__(self) -> str:
        return "jsnull"


JS_NULL = FakeJsNull()
