import pytest

from synthride.core.bounding_box import BoundingBox
from synthride.core.tile import Tile
from synthride.core.tile_type import TileType
from synthride.core.track import Track
from synthride.core.vector3 import Vector3


def make_track() -> Track:
    first = [None] * 3 + [Tile(TileType.NORMAL, 3, 0, 1), Tile(TileType.BOOST, 4, 0, 2)] + [None] * 3
    second = [Tile(TileType.KILL, column, 1, 1) for column in range(8)]
    return Track([first, second])


def test_dimensions():
    track = make_track()
    assert track.row_count == 2
    assert track.length == 2
    assert track.width == 8


def test_rejects_rows_of_wrong_width():
    with pytest.raises(ValueError):
        Track([[None] * 7])


def test_tile_at():
    track = make_track()
    boost = track.tile_at(4, 0)
    assert boost is not None
    assert boost.tile_type is TileType.BOOST
    assert track.tile_at(0, 0) is None
    assert track.tile_at(-1, 0) is None
    assert track.tile_at(0, 9) is None


def test_tiles_iterates_non_empty_cells():
    assert len(list(make_track().tiles())) == 10


def test_tiles_under_box_footprint():
    box = BoundingBox(Vector3(3.5, 0, 0.2), Vector3(4.5, 1, 0.8))
    assert {tile.column for tile in make_track().tiles_under(box)} == {3, 4}


def test_surface_height_at():
    track = make_track()
    assert track.surface_height_at(4.5, 0.5) == 1.0
    assert track.surface_height_at(0.5, 0.5) is None
