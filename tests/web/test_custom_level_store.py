# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

import json
from types import SimpleNamespace

from synthride.web.custom_level_store import CustomLevelStore
from tests.level_json import level_json

LEVEL = level_json(".. .. N1 N1 N1 N1 .. ..", name="Mine")


class FakeStorage:
    def __init__(self, items: dict[str, str] | None = None) -> None:
        self.items = items or {}

    def getItem(self, key: str) -> str | None:  # noqa: N802
        return self.items.get(key)

    def setItem(self, key: str, value: str) -> None:  # noqa: N802
        self.items[key] = value


class BlockedWindow:
    @property
    def localStorage(self) -> object:  # noqa: N802
        raise PermissionError


def test_levels_are_saved_and_read_back() -> None:
    storage = FakeStorage()
    store = CustomLevelStore(SimpleNamespace(localStorage=storage))
    assert store.texts == ()
    assert store.put(None, LEVEL) == 0
    assert store.put(None, level_json("N1 " * 8, name="Other")) == 1
    assert store.put(0, level_json("N1 " * 8, name="Renamed")) == 0
    again = CustomLevelStore(SimpleNamespace(localStorage=storage))
    assert [level.name for level in again.levels()] == ["Renamed", "Other"]
    assert again.persistent


def test_remove_deletes_a_slot() -> None:
    store = CustomLevelStore(SimpleNamespace(localStorage=FakeStorage()))
    store.put(None, LEVEL)
    store.remove(0)
    store.remove(5)
    assert store.texts == ()


def test_unreadable_entries_are_skipped() -> None:
    storage = FakeStorage({CustomLevelStore.KEY: json.dumps([LEVEL, 3, "{broken"])})
    assert CustomLevelStore(SimpleNamespace(localStorage=storage)).texts == (LEVEL,)
    storage = FakeStorage({CustomLevelStore.KEY: "{not json"})
    assert CustomLevelStore(SimpleNamespace(localStorage=storage)).texts == ()


def test_blocked_storage_keeps_levels_in_memory() -> None:
    store = CustomLevelStore(BlockedWindow())
    assert not store.persistent
    store.put(None, LEVEL)
    assert store.texts == (LEVEL,)
    assert not store.persistent


def test_failing_storage_keeps_levels_in_memory() -> None:
    class FailingStorage(FakeStorage):
        def getItem(self, key: str) -> str | None:  # noqa: N802, ARG002
            raise OSError

        def setItem(self, key: str, value: str) -> None:  # noqa: N802, ARG002
            raise OSError

    store = CustomLevelStore(SimpleNamespace(localStorage=FailingStorage()))
    assert not store.persistent
    store.put(None, LEVEL)
    assert not store.persistent
    assert store.texts == (LEVEL,)
    assert not CustomLevelStore(SimpleNamespace(localStorage=None)).persistent
