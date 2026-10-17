# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

from synthride.core.world.level_catalog import LevelCatalog
from synthride.core.world.tile_type import TileType


def test_lists_bundled_levels_in_order() -> None:
    names = LevelCatalog().file_names()
    assert len(names) >= 3
    assert all(name.startswith("level_") and name.endswith(".json") for name in names)
    assert names == sorted(names)


def test_all_bundled_levels_parse_and_are_finishable_in_principle() -> None:
    for level in LevelCatalog().load_all():
        assert level.name
        assert level.track.row_count > 50
        first_row = [level.track.tile_at(column, 0) for column in range(8)]
        assert any(first_row), f"{level.name} has no tile to start on"


def test_every_slope_joins_a_neighbour_flush() -> None:
    """A slope is a connector: along at least one of its edges it meets a neighbour at exactly its own heights."""
    sides = {(-1, 0): ((0, 0), (0, 1)), (1, 0): ((1, 0), (1, 1)), (0, -1): ((0, 0), (1, 0)), (0, 1): ((0, 1), (1, 1))}
    for level in LevelCatalog().load_all():
        track = level.track
        for tile in (tile for tile in track.tiles() if tile.slope is not None):
            flush = [
                [tile.corner_height(cx, cz) for cx, cz in corners]
                == [neighbour.corner_height(cx - dc, cz - dr) for cx, cz in corners]
                for (dc, dr), corners in sides.items()
                if (neighbour := track.tile_at(tile.column + dc, tile.row + dr)) is not None
            ]
            assert any(flush), f"{level.name}: lone slope at row {tile.row}, column {tile.column}"


def test_levels_get_longer_as_they_get_harder() -> None:
    lengths = [level.track.row_count for level in LevelCatalog().load_all()]
    assert lengths == sorted(lengths)


def test_every_level_uses_every_kind_of_tile_tunnels_and_slopes() -> None:
    for level in LevelCatalog().load_all():
        tiles = list(level.track.tiles())
        kinds = {tile.tile_type for tile in tiles} | {TileType.PUSH_LEFT, TileType.PUSH_RIGHT}
        assert kinds == set(TileType), f"{level.name} misses {set(TileType) - kinds}"
        assert any(tile.tile_type in (TileType.PUSH_LEFT, TileType.PUSH_RIGHT) for tile in tiles), level.name
        assert any(tile.tunnel for tile in tiles), f"{level.name} has no tunnel"
        assert any(tile.slope for tile in tiles), f"{level.name} has no slope"
