# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

import json

import pytest

from synthride.web.browser.local_levels import LocalLevels
from tests.web.fakes.fake_js_bridge import FakeJsBridge
from tests.web.fakes.fake_local_storage import FakeLocalStorage


def make_levels(storage: object) -> LocalLevels:
    bridge = FakeJsBridge()
    bridge.window.localStorage = storage
    return LocalLevels(bridge)


def test_saved_levels_are_loaded_back() -> None:
    storage = FakeLocalStorage()
    levels = make_levels(storage)
    assert levels.load() == {}
    assert levels.save("level_01.json", "one")
    assert levels.save("level_29.json", "new")
    assert levels.save("level_01.json", "again")
    assert make_levels(storage).load() == {"level_01.json": "again", "level_29.json": "new"}


@pytest.mark.parametrize("stored", ["not json", "[1, 2]", json.dumps({"level_01.json": 3})])
def test_unreadable_storage_loads_nothing(stored: str) -> None:
    assert make_levels(FakeLocalStorage({LocalLevels.KEY: stored})).load() == {}


def test_missing_or_full_storage_refuses_saves() -> None:
    assert not make_levels(FakeLocalStorage(full=True)).save("level_01.json", "one")
    assert make_levels(None).load() == {}
    assert not make_levels(None).save("level_01.json", "one")
