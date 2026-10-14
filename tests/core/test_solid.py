# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

from synthride.core.bounding_box import BoundingBox
from synthride.core.slope import Slope
from synthride.core.solid import Solid
from synthride.core.tile import Tile
from synthride.core.tile_type import TileType
from synthride.core.vector3 import Vector3


def test_tile_block_and_bare_shell() -> None:
    tile = Tile(TileType.NORMAL, 1, 2, 1)
    assert Solid(tile.bounding_box, tile).tile is tile
    assert Solid(tile.bounding_box).tile is None


def test_top_is_the_slope_under_the_footprint() -> None:
    footprint = BoundingBox(Vector3(1.2, 0, 4.0), Vector3(1.8, 1, 5.0))
    flat = Tile(TileType.NORMAL, 1, 2, 1)
    ramp = Tile(TileType.NORMAL, 1, 2, 1, slope=Slope.FRONT)
    assert Solid(flat.bounding_box, flat).top_over(footprint) == 0.5
    assert Solid(ramp.bounding_box, ramp).top_over(footprint) == 0.75
    assert Solid(ramp.bounding_box).top_over(footprint) == 1.0
