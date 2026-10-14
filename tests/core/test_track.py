# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

import pytest

from synthride.core.bounding_box import BoundingBox
from synthride.core.tile import Tile
from synthride.core.tile_type import TileType
from synthride.core.track import Track
from synthride.core.tunnel_kind import TunnelKind
from synthride.core.tunnel_span import TunnelSpan
from synthride.core.vector3 import Vector3
from tests.level_factory import make_level


def make_track() -> Track:
    first = [None] * 3 + [Tile(TileType.NORMAL, 3, 0, 1), Tile(TileType.BOOST, 4, 0, 2)] + [None] * 3
    second = [Tile(TileType.KILL, column, 1, 1) for column in range(8)]
    return Track([first, second])


def test_dimensions() -> None:
    track = make_track()
    assert track.row_count == 2
    assert track.length == 4
    assert track.width == 8


def test_rejects_rows_of_wrong_width() -> None:
    with pytest.raises(ValueError, match="must have 8 cells"):
        Track([[None] * 7])


def test_tile_at() -> None:
    track = make_track()
    boost = track.tile_at(4, 0)
    assert boost is not None
    assert boost.tile_type is TileType.BOOST
    assert track.tile_at(0, 0) is None
    assert track.tile_at(-1, 0) is None
    assert track.tile_at(0, 9) is None


def test_tiles_iterates_non_empty_cells() -> None:
    assert len(list(make_track().tiles())) == 10


def test_tiles_under_box_footprint() -> None:
    box = BoundingBox(Vector3(3.5, 0, 0.2), Vector3(4.5, 1, 0.8))
    assert {tile.column for tile in make_track().tiles_under(box)} == {3, 4}


def test_surface_height_at() -> None:
    track = make_track()
    assert track.surface_height_at(4.5, 0.5) == 1.0
    assert track.surface_height_at(0.5, 0.5) is None


def test_surface_height_follows_a_slope() -> None:
    track = make_level("N1 N1 N1 N1 N1f N1 N1 N1").track
    assert track.surface_height_at(4.5, 0.5) == 0.625


def test_neighbouring_tunnel_tiles_merge_into_spans() -> None:
    track = make_level("N1T N1T N2T N1A N1A .. N1T N1").track
    spans = [(span.kind, span.first_column, span.last_column, span.deck) for span in track.tunnels]
    assert spans == [
        (TunnelKind.SQUARE, 0, 1, 0.5),
        (TunnelKind.SQUARE, 2, 2, 1.0),
        (TunnelKind.ROUND, 3, 4, 0.5),
        (TunnelKind.SQUARE, 6, 6, 0.5),
    ]


def test_solids_under_include_tunnel_shells_once() -> None:
    track = make_level(".. .. N1T N1T .. .. .. ..").track
    box = BoundingBox(Vector3(2.5, 0, 0.2), Vector3(3.5, 1, 0.8))
    solids = track.solids_under(box)
    assert len([solid for solid in solids if solid.tile is not None]) == 2
    assert len([solid for solid in solids if solid.tile is None]) == 1  # the roof spans both tiles
    assert track.tiles_under(box) == [track.tile_at(2, 0), track.tile_at(3, 0)]


def test_ceiling_over_finds_the_lowest_tunnel_roof_in_range() -> None:
    track = make_level("N1 " * 8, "N1T " * 8, "N2T " * 8).track
    assert track.ceiling_over(4, 0.0, 1.9) is None
    assert track.ceiling_over(4, 0.0, 3.0) == 0.5 + TunnelSpan.CLEARANCE
    assert track.ceiling_over(4, 4.0, 5.0) == 1.0 + TunnelSpan.CLEARANCE
    assert track.ceiling_over(-1, 0.0, 6.0) is None
