# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

from synthride.core.gameplay.game_phase import GamePhase
from synthride.core.gameplay.game_session import GameSession
from synthride.core.gameplay.ship_input import ShipInput
from synthride.core.world.level_catalog import LevelCatalog


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


def test_tunnel_vision_can_be_ridden_without_jumping() -> None:
    """An autopilot holding full throttle and steering for the centre finishes the level."""
    levels = LevelCatalog().load_all()
    session = GameSession(levels)
    session.selected_level = next(index for index, level in enumerate(levels) if level.name == "Tunnel Vision")
    session.start()
    for _ in range(60 * 60):
        x = session.ship.position.x
        session.update(1 / 60, ShipInput(accelerate=True, left=x > 4.15, right=x < 3.85))
        if session.phase is not GamePhase.PLAYING:
            break
    assert session.phase is GamePhase.LEVEL_WON
