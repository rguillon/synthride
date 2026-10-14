# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

import pytest

from synthride.core.bounding_box import BoundingBox
from synthride.core.slope import Slope
from synthride.core.tile import Tile
from synthride.core.tile_type import TileType
from synthride.core.vector3 import Vector3


def test_top_depends_on_level() -> None:
    assert Tile(TileType.NORMAL, 0, 0, 3).top == 1.5


def test_bounding_box_spans_its_cell_from_the_abyss() -> None:
    box = Tile(TileType.NORMAL, column=2, row=5, level=2).bounding_box
    assert box.minimum == Vector3(2, Tile.BOTTOM, 5)
    assert box.maximum == Vector3(3, 1.0, 6)


def test_a_flat_tile_is_level_everywhere() -> None:
    tile = Tile(TileType.NORMAL, 2, 5, 2)
    assert tile.base == tile.top == tile.height_at(2.5, 5.5) == tile.corner_height(1, 1) == 1.0


def test_a_slope_rises_one_height_unit_from_its_level() -> None:
    ramp = Tile(TileType.NORMAL, column=2, row=5, level=2, slope=Slope.FRONT)
    assert (ramp.base, ramp.top) == (1.0, 1.5)
    assert ramp.bounding_box.maximum.y == 1.5
    assert ramp.height_at(2.5, 5.0) == 1.0
    assert ramp.height_at(2.5, 5.25) == pytest.approx(1.125)
    assert ramp.height_at(2.5, 9.0) == 1.5  # clamped to the tile
    assert (ramp.corner_height(0, 0), ramp.corner_height(1, 1)) == (1.0, 1.5)


def test_top_over_is_the_highest_point_under_a_footprint() -> None:
    corner = Tile(TileType.NORMAL, column=0, row=0, level=1, slope=Slope.FRONT_RIGHT)
    box = BoundingBox(Vector3(0.2, 0, 0.1), Vector3(0.6, 1, 0.8))
    assert corner.top_over(box) == pytest.approx(0.5 + 0.5 * 0.6)
    assert Tile(TileType.NORMAL, 0, 0, 1).top_over(box) == 0.5


def test_gradient_is_the_steepness_of_the_slope() -> None:
    assert Tile(TileType.NORMAL, 0, 0, 1).gradient(0.5, 0.5) == (0.0, 0.0)
    assert Tile(TileType.NORMAL, 0, 0, 1, slope=Slope.LEFT).gradient(0.5, 0.5) == (-0.5, 0.0)
    assert Tile(TileType.NORMAL, 0, 0, 1, slope=Slope.FRONT).gradient(0.5, 7.0) == (0.0, 0.5)
