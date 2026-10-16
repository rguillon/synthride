# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

import json
from pathlib import Path

import pytest

from synthride.server.level_folder import LevelFolder

LEVEL = json.dumps({"name": "Mine", "track": [[12, ".. .. N1 N1 N1 N1 .. .."]]})


def test_defaults_to_the_bundled_levels() -> None:
    assert (LevelFolder().root / "level_01.json").is_file()


def test_saves_a_level_file(tmp_path: Path) -> None:
    path = LevelFolder(tmp_path).save("level_07.json", LEVEL)
    assert path == tmp_path / "level_07.json"
    assert path.read_text() == LEVEL + "\n"
    LevelFolder(tmp_path).save("level_07.json", LEVEL + "\n")
    assert path.read_text() == LEVEL + "\n"


@pytest.mark.parametrize("name", ["level_7.json", "../level_07.json", "level_07.txt", "other.json", "level_07.json/x"])
def test_refuses_other_file_names(tmp_path: Path, name: str) -> None:
    with pytest.raises(ValueError, match="not a level file name"):
        LevelFolder(tmp_path).save(name, LEVEL)


def test_refuses_what_is_not_a_level(tmp_path: Path) -> None:
    with pytest.raises(ValueError):  # noqa: PT011
        LevelFolder(tmp_path).save("level_07.json", "{nope")
    assert list(tmp_path.iterdir()) == []
