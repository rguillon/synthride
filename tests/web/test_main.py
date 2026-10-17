# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

import json
import sys
from types import SimpleNamespace

import pytest

from synthride.web import main as main_module
from synthride.web.browser.local_levels import LocalLevels
from synthride.web.game_loop import GameLoop
from synthride.web.main import Main
from tests.level_json import level_json
from tests.web.fakes.fake_js_bridge import FakeJsBridge
from tests.web.fakes.fake_js_object import FakeJsObject
from tests.web.fakes.fake_local_storage import FakeLocalStorage
from tests.web.fakes.fake_window import FakeWindow


def browser_saves(**files: str) -> FakeJsBridge:
    bridge = FakeJsBridge()
    bridge.window.localStorage = FakeLocalStorage({LocalLevels.KEY: json.dumps(files)})
    return bridge


def test_build_wires_a_game_loop_with_bundled_levels_and_the_editor_saving_in_the_browser() -> None:
    loop = Main(FakeJsBridge()).build()
    assert isinstance(loop, GameLoop)
    assert len(loop.session.levels) >= 3
    editor = loop._editor  # noqa: SLF001
    assert editor is not None
    assert editor._local is not None  # noqa: SLF001
    assert editor.files[0] == "level_01.json"
    assert len(editor.files) == len(loop.session.levels)


def test_levels_saved_in_the_browser_replace_or_follow_the_bundled_ones() -> None:
    bundled = Main(FakeJsBridge()).build().session.levels
    saves = {
        "level_01.json": level_json("N1 N1 N1 N1 N1 N1 N1 N1", name="Mine"),
        "level_99.json": level_json("N1 N1 N1 N1 N1 N1 N1 N1", name="New"),
        "level_98.json": "broken",
    }
    loop = Main(browser_saves(**saves)).build()
    levels = loop.session.levels
    assert [levels[0].name, levels[-1].name] == ["Mine", "New"]
    assert [level.name for level in levels[1:-1]] == [level.name for level in bundled[1:]]
    editor = loop._editor  # noqa: SLF001
    assert editor is not None
    assert editor.files[-1] == "level_99.json"


def test_dev_mode_saves_to_the_level_files_and_ignores_the_browser() -> None:
    bridge = browser_saves(**{"level_01.json": level_json("N1 N1 N1 N1 N1 N1 N1 N1", name="Mine")})
    loop = Main(bridge, dev=True).build()
    editor = loop._editor  # noqa: SLF001
    assert editor is not None
    assert editor._local is None  # noqa: SLF001
    assert loop.session.levels[0].name != "Mine"
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
