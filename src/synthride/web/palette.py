from __future__ import annotations

from typing import ClassVar

from synthride.core.tile_type import TileType


class Palette:
    """The synthwave colour scheme, as 0xRRGGBB integers."""

    NIGHT = 0x0B0014
    HORIZON = 0x5A189A
    FOG = 0x2A0845
    GRID = 0xFF2BD6
    TILE_BODY = 0x12001F
    SHIP_BODY = 0x1B1035
    SHIP_EDGE = 0x00F0FF
    SHIP_GLOW = 0xFF2BD6
    EXPLOSION = 0xFF6D00
    TILE_COLORS: ClassVar[dict[TileType, int]] = {
        TileType.NORMAL: 0x00F0FF,
        TileType.BOOST: 0xFF2BD6,
        TileType.SLOW: 0x9D4EDD,
        TileType.KILL: 0xFF1744,
        TileType.REFUEL: 0x7DFF9B,
        TileType.FINISH: 0xFFE066,
    }

    @classmethod
    def tile_color(cls, tile_type: TileType) -> int:
        return cls.TILE_COLORS[tile_type]

    @staticmethod
    def css(color: int) -> str:
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
