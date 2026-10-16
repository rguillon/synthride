# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

import json

import pytest

from synthride.core.world.level_catalog import LevelCatalog
from synthride.core.world.level_parser import LevelFormatError, LevelParser
from synthride.core.world.tile_type import TileType
from synthride.editor.track_grid import Brush, BrushKind, LevelSettings, Rect, TrackGrid

NORMAL = Brush(BrushKind.TILE, "N")
ICE = Brush(BrushKind.TILE, "I")


def test_a_rect_covers_its_corners_in_any_order() -> None:
    rect = Rect(3, 5, 1, 4)
    assert list(rect.columns) == [1, 2, 3]
    assert list(rect.rows) == [4, 5]
    assert len(list(rect.cells())) == 6


def test_the_starter_is_a_finishable_looking_straight() -> None:
    grid = TrackGrid.starter()
    assert grid.length == 33
    track = grid.track()
    assert track.tile_at(3, 0) is not None
    finish = track.tile_at(3, 32)
    assert finish is not None
    assert finish.tile_type is TileType.FINISH


def test_painting_a_gap_lays_tiles_at_the_brush_height() -> None:
    grid = TrackGrid()
    assert grid.paint(Rect(0, 0, 1, 2), NORMAL, height=3)
    assert grid.cell(1, 2) == "N3"
    assert grid.row_count == 3


def test_painting_a_tile_keeps_its_height_and_shape() -> None:
    grid = TrackGrid([["N2f", "N4T", None, None, None, None, None, None]])
    grid.paint(Rect(0, 0, 1, 0), ICE, height=1)
    assert [grid.cell(0, 0), grid.cell(1, 0)] == ["I2f", "I4T"]


def test_painting_past_the_end_makes_the_track_longer() -> None:
    grid = TrackGrid.starter()
    grid.paint(Rect(2, 40, 5, 45), NORMAL)
    assert grid.length == 46
    assert grid.cell(3, 36) is None


def test_the_track_never_grows_past_its_limit() -> None:
    grid = TrackGrid()
    grid.paint(Rect(0, TrackGrid.MAX_ROWS - 5, 0, TrackGrid.MAX_ROWS + 60), NORMAL)
    assert grid.row_count == TrackGrid.MAX_ROWS
    assert not grid.paint(Rect(0, TrackGrid.MAX_ROWS + 50, 0, TrackGrid.MAX_ROWS + 60), ICE)


def test_erasing_raising_lowering_and_shaping_only_touch_tiles() -> None:
    grid = TrackGrid([["N1", "N8", None, "N3", "N3", None, None, None]])
    grid.paint(Rect(0, 0, 7, 0), Brush(BrushKind.RAISE))
    assert [grid.cell(column, 0) for column in range(4)] == ["N2", "N8", None, "N4"]
    grid.paint(Rect(0, 0, 7, 0), Brush(BrushKind.LOWER))
    grid.paint(Rect(0, 0, 0, 0), Brush(BrushKind.LOWER))
    assert grid.cell(0, 0) == "N1"
    grid.paint(Rect(3, 0, 4, 0), Brush(BrushKind.SHAPE, "f"))
    assert grid.cell(3, 0) == "N3f"
    grid.paint(Rect(3, 0, 3, 0), Brush(BrushKind.SHAPE, "T"))
    assert grid.cell(3, 0) == "N3T"
    grid.paint(Rect(3, 0, 3, 0), Brush(BrushKind.SHAPE, ""))
    assert grid.cell(3, 0) == "N3"
    grid.paint(Rect(0, 0, 7, 0), Brush(BrushKind.ERASE))
    assert grid.length == 0
    assert not grid.paint(Rect(0, 5, 3, 9), Brush(BrushKind.RAISE))
    assert grid.row_count == 1


def test_undo_reverts_one_paint_at_a_time() -> None:
    grid = TrackGrid.starter()
    assert not grid.paint(Rect(2, 0, 2, 0), NORMAL)
    assert not grid.can_undo
    grid.paint(Rect(0, 0, 0, 0), ICE)
    grid.paint(Rect(1, 0, 1, 0), ICE)
    grid.undo()
    assert grid.cell(0, 0) == "I1"
    assert grid.cell(1, 0) is None
    grid.undo()
    assert grid.cell(0, 0) is None
    grid.undo()


def test_rows_drop_the_gaps_at_the_end_and_merge_runs() -> None:
    grid = TrackGrid.starter()
    grid.paint(Rect(0, 50, 7, 50), NORMAL)
    grid.paint(Rect(0, 50, 7, 50), Brush(BrushKind.ERASE))
    assert grid.length == 33
    assert grid.encoded() == [[30, ".. .. N1 N1 N1 N1 .. .."], [3, ".. .. F1 F1 F1 F1 .. .."]]


def test_an_empty_grid_still_makes_a_track() -> None:
    assert TrackGrid().track().row_count == 1


@pytest.mark.parametrize("file_name", LevelCatalog().file_names())
def test_every_bundled_level_survives_a_round_trip(file_name: str) -> None:
    level = LevelCatalog().load(file_name)
    settings = LevelSettings.of(level)
    grid = TrackGrid.from_track(level.track)
    again = LevelParser().parse(settings.write(grid))
    assert again == level or (again.name, again.track.row_count) == (level.name, level.track.row_count)
    for row in range(level.track.row_count):
        for column in range(8):
            assert again.track.tile_at(column, row) == level.track.tile_at(column, row)


def test_settings_read_a_level_file() -> None:
    text = json.dumps({"name": "Mine", "gravity": 20, "track": [[3, ".. .. N1 N1 N1 N1 .. .."]]})
    settings, grid = LevelSettings.read(text)
    assert settings == LevelSettings("Mine", 20.0)
    assert grid.length == 3
    level = settings.level(grid)
    assert (level.name, level.gravity, level.track.row_count) == ("Mine", 20.0, 3)
    with pytest.raises(LevelFormatError):
        LevelSettings.read("{")
