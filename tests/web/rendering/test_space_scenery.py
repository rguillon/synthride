# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

import math

from synthride.web.rendering.space_scenery import SpaceScenery


def test_each_level_has_its_own_scenery_and_keeps_it() -> None:
    sceneries = [SpaceScenery.for_level(index) for index in range(26)]
    assert sceneries == [SpaceScenery.for_level(index) for index in range(26)]
    assert len(set(sceneries)) == len(sceneries)


def test_neighbouring_levels_never_share_a_theme() -> None:
    for index in range(40):
        assert SpaceScenery.for_level(index).theme != SpaceScenery.for_level(index + 1).theme


def test_the_planet_hangs_ahead_off_to_one_side() -> None:
    for index in range(40):
        scenery = SpaceScenery.for_level(index)
        x, y, z = scenery.planet_position
        assert abs(x) >= 110
        assert y > 0
        assert z < 0
        assert all(math.isclose(math.hypot(*vector), 1.0) for vector in (scenery.sun, scenery.band_axis))


def test_rocky_worlds_are_mottled_and_gas_giants_banded() -> None:
    for scenery in map(SpaceScenery.for_level, range(40)):
        assert (scenery.mottle >= 0.4) == (scenery.bands < 6)
