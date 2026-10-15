# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""The look of the space around one level."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

from synthride.web.palette import Palette

Vector = tuple[float, float, float]


@dataclass(frozen=True)
class SpaceTheme:
    """The colours of one corner of space: the sky, its nebula and the planet hanging in it."""

    space: int
    nebula: int
    nebula_glow: int
    planet_dark: int
    planet_light: int
    planet_rim: int


@dataclass(frozen=True)
class SpaceScenery:
    """Everything that makes one level's sky its own: colours, the planet's kind and place, and an optional moon."""

    THEMES = (
        SpaceTheme(
            Palette.SPACE,
            Palette.NEBULA,
            Palette.NEBULA_GLOW,
            Palette.PLANET_DARK,
            Palette.PLANET_LIGHT,
            Palette.PLANET_RIM,
        ),  # synthwave
        SpaceTheme(0x090204, 0x9A1B3A, 0xFF7A1A, 0x4A0E0E, 0xE0662A, 0xFFC46B),  # ember
        SpaceTheme(0x010608, 0x0B5E6B, 0x39FFB0, 0x062C40, 0x2FA7C9, 0x9AFFF0),  # deep ocean
        SpaceTheme(0x030802, 0x2E6B12, 0xD4FF33, 0x1B3A10, 0x8BC34A, 0xF0FF8A),  # toxic
        SpaceTheme(0x02040A, 0x1E3A8A, 0xB3E5FF, 0x3A4A6B, 0xDDE8FF, 0x8FD3FF),  # ice giant
        SpaceTheme(0x080110, 0xB0127A, 0xFF4FD8, 0x3D0A3A, 0xFF7BC8, 0xFFD1F0),  # magenta
        SpaceTheme(0x070502, 0x6B4A12, 0xFFB347, 0x5A3A12, 0xF2C46B, 0xFF6D00),  # dune
        SpaceTheme(0x04020A, 0x3F1D9A, 0xFF2BD6, 0x1A0E3A, 0x6A5ACD, 0xFF2BD6),  # violet storm
    )
    # Band counts across the planet: few for a rocky world, many for a gas giant.
    BANDS = (2.0, 5.0, 9.0, 13.0, 20.0)
    PLANET_DEPTH = -430.0
    MOON_DEPTH = -400.0

    theme: SpaceTheme
    planet_size: float
    planet_position: Vector
    bands: float
    mottle: float  # 0 for smooth bands, up to 1 for a cratered, cloudy surface
    ring: bool
    sun: Vector  # the direction light falls on the planet from, toward the viewer
    band_axis: Vector  # the direction the nebula's bright band runs across
    sky_offset: Vector  # where in the noise the nebula's clouds are sampled
    moon_size: float  # 0 for no moon
    moon_position: Vector

    @classmethod
    def for_level(cls, index: int) -> SpaceScenery:
        """Return the scenery of the level at ``index``: neighbouring levels never share a theme."""
        rng = random.Random(index)  # noqa: S311
        side = rng.choice((-1.0, 1.0))
        bands = rng.choice(cls.BANDS)
        has_moon = rng.random() < 0.6
        return cls(
            theme=cls.THEMES[index % len(cls.THEMES)],
            planet_size=rng.uniform(110.0, 200.0),
            planet_position=(side * rng.uniform(110.0, 210.0), rng.uniform(25.0, 105.0), cls.PLANET_DEPTH),
            bands=bands,
            mottle=rng.uniform(0.4, 1.0) if bands < 6 else rng.uniform(0.0, 0.35),
            ring=rng.random() < 0.5,
            sun=cls._normalized((-side * rng.uniform(0.3, 1.0), rng.uniform(-0.2, 0.6), rng.uniform(0.2, 0.8))),
            band_axis=cls._normalized((rng.uniform(-0.8, 0.8), 1.0, rng.uniform(-0.4, 0.4))),
            sky_offset=(rng.uniform(0, 50), rng.uniform(0, 50), rng.uniform(0, 50)),
            moon_size=rng.uniform(32.0, 60.0) if has_moon else 0.0,
            moon_position=(-side * rng.uniform(60.0, 160.0), rng.uniform(40.0, 120.0), cls.MOON_DEPTH),
        )

    @staticmethod
    def _normalized(vector: Vector) -> Vector:
        length = math.sqrt(sum(c * c for c in vector))
        x, y, z = (c / length for c in vector)
        return x, y, z
