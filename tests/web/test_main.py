# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

import sys
from types import SimpleNamespace

import pytest

from synthride.web import main as main_module
from synthride.web.game_loop import GameLoop
from synthride.web.main import Main
from tests.web.fakes.fake_js_bridge import FakeJsBridge
from tests.web.fakes.fake_js_object import FakeJsObject
from tests.web.fakes.fake_window import FakeWindow


def test_build_wires_a_game_loop_with_bundled_levels() -> None:
    bridge = FakeJsBridge()
    loop = Main(bridge).build()
    assert isinstance(loop, GameLoop)
    assert len(loop.session.levels) >= 3
    assert loop._editor is None  # noqa: SLF001


def test_dev_mode_adds_the_editor_saving_to_the_level_files() -> None:
    loop = Main(FakeJsBridge(), dev=True).build()
    editor = loop._editor  # noqa: SLF001
    assert editor is not None
    assert editor.files[0] == "level_01.json"
    assert len(editor.files) == len(loop.session.levels)


def test_main_boots_from_pyodide_modules(monkeypatch: pytest.MonkeyPatch) -> None:
    window = FakeWindow()
    ffi = SimpleNamespace(create_proxy=lambda function: function, to_js=lambda value, **_: value)
    monkeypatch.setitem(sys.modules, "js", SimpleNamespace(window=window, THREE=FakeJsObject("THREE")))
    monkeypatch.setitem(sys.modules, "pyodide", SimpleNamespace(ffi=ffi))
    monkeypatch.setitem(sys.modules, "pyodide.ffi", ffi)
    loop = main_module.main()
    assert isinstance(loop, GameLoop)
    assert len(window.frame_callbacks) == 1
