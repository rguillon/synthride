# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

import pytest

from synthride.core.world.slope import Slope

Point = tuple[float, float]


def test_letters_name_the_raised_side() -> None:
    assert Slope("f") is Slope.FRONT
    assert Slope("br") is Slope.BACK_RIGHT
    assert Slope.FRONT.direction == (0, 1)
    assert Slope.LEFT.direction == (-1, 0)
    assert Slope.BACK_RIGHT.direction == (1, -1)


@pytest.mark.parametrize(
    ("slope", "low", "high"),
    [
        (Slope.FRONT, (0.5, 0.0), (0.5, 1.0)),
        (Slope.BACK, (0.5, 1.0), (0.5, 0.0)),
        (Slope.LEFT, (1.0, 0.5), (0.0, 0.5)),
        (Slope.RIGHT, (0.0, 0.5), (1.0, 0.5)),
        (Slope.FRONT_RIGHT, (0.0, 0.0), (1.0, 1.0)),
        (Slope.BACK_LEFT, (1.0, 1.0), (0.0, 0.0)),
    ],
)
def test_rises_from_the_low_side_to_the_raised_one(
    slope: Slope, low: tuple[float, float], high: tuple[float, float]
) -> None:
    assert slope.rise(*low) == 0
    assert slope.rise(*high) == 1


def test_a_corner_only_rises_toward_its_corner() -> None:
    """A corner slope meets the side ramps on either side of it, and is low along its other two edges."""
    assert Slope.FRONT_RIGHT.rise(1.0, 0.3) == pytest.approx(Slope.FRONT.rise(1.0, 0.3))
    assert Slope.FRONT_RIGHT.rise(0.3, 1.0) == pytest.approx(Slope.RIGHT.rise(0.3, 1.0))
    assert Slope.FRONT_RIGHT.rise(0.0, 0.7) == 0
    assert Slope.FRONT_RIGHT.rise(0.7, 0.0) == 0
    assert Slope.FRONT_LEFT.rise(0.0, 1.0) == 1
    assert Slope.FRONT_LEFT.rise(1.0, 1.0) == 0


def test_gradient_points_up_the_slope() -> None:
    assert Slope.BACK.gradient(0.3, 0.3) == (0, -1)
    assert Slope.FRONT_RIGHT.gradient(0.2, 0.8) == (1, 0)
    assert Slope.FRONT_RIGHT.gradient(0.8, 0.2) == (0, 1)
