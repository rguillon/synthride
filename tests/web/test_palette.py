# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

from synthride.core.tile_type import TileType
from synthride.web.palette import Palette


def test_every_tile_type_has_a_distinct_colour() -> None:
    colors = [Palette.tile_color(tile_type) for tile_type in TileType]
    assert len(set(colors)) == len(TileType)


def test_css() -> None:
    assert Palette.css(Palette.GRID) == "#ff2bd6"
    assert Palette.css(0x00000F) == "#00000f"


def test_mix_moves_each_channel_toward_the_other_colour() -> None:
    assert Palette.mix(0x000000, 0xFF8040, 0.5) == 0x804020
    assert Palette.mix(0x123456, 0xABCDEF, 0) == 0x123456
    assert Palette.mix(0x123456, 0xABCDEF, 1) == 0xABCDEF


def test_linear_rgb() -> None:
    assert Palette.linear_rgb(0xFF0000) == (1.0, 0.0, 0.0)
    red, _, _ = Palette.linear_rgb(0x800000)
    assert 0.2 < red < 0.25
