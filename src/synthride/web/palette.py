# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""The synthwave colour scheme."""

from __future__ import annotations

from typing import ClassVar

from synthride.core.tile_type import TileType


class Palette:
    """The synthwave colour scheme, as 0xRRGGBB integers."""

    SPACE = 0x020109
    NEBULA = 0x6A1B9A
    NEBULA_GLOW = 0x00A3C4
    PLANET_DARK = 0x2A1458
    PLANET_LIGHT = 0x8E4FB8
    PLANET_RIM = 0x4DD9FF
    STARS = (0xFFFFFF, 0xBFD4FF, 0xFFD9F2, 0x9FE8FF, 0xFFE9B8)
    DUST = 0x8C7BFF
    FOG = 0x060418
    GRID = 0xFF2BD6
    TILE_BODY = 0x12001F
    SHIP_BODY = 0x1B1035
    SHIP_EDGE = 0x00F0FF
    SHIP_GLOW = 0xFF2BD6
    EXPLOSION = 0xFF6D00
    TUNNEL = 0xFF2BD6
    TILE_COLORS: ClassVar[dict[TileType, int]] = {
        TileType.NORMAL: 0x00F0FF,
        TileType.BOOST: 0xFF2BD6,
        TileType.SLOW: 0x9D4EDD,
        TileType.KILL: 0xFF1744,
        TileType.REFUEL: 0x7DFF9B,
        TileType.AIR: 0x4D8CFF,
        TileType.JUMP: 0xFF8A00,
        TileType.ICE: 0xD9FBFF,
        TileType.PUSH_LEFT: 0xC6FF00,
        TileType.PUSH_RIGHT: 0xD4FF33,  # the pushers are one family: their arrows tell them apart
        TileType.FINISH: 0xFFE066,
    }

    @classmethod
    def tile_color(cls, tile_type: TileType) -> int:
        """Return the colour of a tile type."""
        return cls.TILE_COLORS[tile_type]

    @staticmethod
    def css(color: int) -> str:
        """Return ``color`` as a CSS hex colour."""
        return f"#{color:06x}"

    @staticmethod
    def mix(color: int, other: int, amount: float) -> int:
        """``color`` moved ``amount`` (0..1) of the way toward ``other``, channel by channel."""
        mixed = 0
        for shift in (16, 8, 0):
            a, b = color >> shift & 0xFF, other >> shift & 0xFF
            mixed |= round(a + (b - a) * amount) << shift
        return mixed

    @staticmethod
    def linear_rgb(color: int) -> tuple[float, float, float]:
        """Channels as 0..1 floats in linear space, as Three.js expects for vertex colours."""
        red, green, blue = (((color >> shift & 0xFF) / 255) ** 2.2 for shift in (16, 8, 0))
        return red, green, blue
