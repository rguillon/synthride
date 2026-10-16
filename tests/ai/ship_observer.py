# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""What the neural network sees of the game."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, ClassVar

import numpy as np

from synthride.core.tile import Tile
from synthride.core.tile_type import TileType

if TYPE_CHECKING:
    from synthride.core.game_session import GameSession
    from synthride.core.track import Track


class _TrackMap:
    """A track's tiles as one table, so that many points of it can be looked up at once.

    Each cell's row holds its features, the height of its base and its slope as ``a + b * t`` along each axis, ``t``
    going from 0 to 1 across the cell: how far up the slope a point is is the lower of the two, infinite along an axis
    the slope does not rise along, and both are 0 for a flat cell. A border of empty cells, all zeros, surrounds the
    track, and points off the track look up that border.
    """

    def __init__(self, track: Track, features: int) -> None:
        self.rows, self.columns = track.row_count, track.COLUMNS
        self.features = features
        self.table = np.zeros((self.rows + 2, self.columns + 2, features + 5))
        for tile in track.tiles():
            cell = self.table[tile.row + 1, tile.column + 1]
            cell[:features] = ShipObserver.cell(tile)
            cell[features] = tile.base
            if tile.slope is not None:
                for axis, sign in enumerate(tile.slope.direction):
                    cell[features + 1 + 2 * axis : features + 3 + 2 * axis] = self._ramp(sign)
        self.table = self.table.reshape(-1, features + 5)

    def look(self, x: np.ndarray, z: np.ndarray, height: float) -> np.ndarray:
        """Return the features of the points ``(x, z)``, with heights relative to ``height``, zero off the track."""
        u, v = x / Tile.WIDTH, z / Tile.LENGTH
        column, row = np.floor(u).astype(int), np.floor(v).astype(int)
        u, v = u - column, v - row
        # np.minimum and np.maximum rather than np.clip, which costs several times more on arrays this small.
        row = np.minimum(np.maximum(row, -1), self.rows) + 1
        index = row * (self.columns + 2) + np.minimum(np.maximum(column, -1), self.columns) + 1
        table = self.table.take(index, axis=0)
        features = self.features
        cells = table[..., :features]
        rise = np.minimum(
            table[..., features + 1] + table[..., features + 2] * u,
            table[..., features + 3] + table[..., features + 4] * v,
        )
        top = table[..., features] + Tile.HEIGHT_UNIT * rise
        cells[..., 1] = np.minimum(np.maximum((top - height) / 2, -1.0), 1.0) * cells[..., 0]
        return cells

    @staticmethod
    def _ramp(sign: int) -> tuple[float, float]:
        """Return ``(a, b)`` such that ``a + b * t`` is how far up a slope rising toward ``sign`` the point ``t`` is."""
        return (0.0, 1.0) if sign > 0 else (1.0, -1.0) if sign < 0 else (math.inf, 0.0)


class ShipObserver:
    """Turns the session into the network's inputs: the ship's state and the track around and ahead of it.

    The track view covers ``COLUMNS`` tiles across, centred on the ship, and ``ROWS`` tiles ahead, starting at the
    ship. It samples each tile's area at ``SAMPLES`` x ``SAMPLES`` points laid out around the ship's exact position
    rather than on the tile grid, so tile borders move through the view as the ship moves. Each point gives whether
    a tile is under it, the height of its top there relative to the ship and its kind.
    """

    COLUMNS: ClassVar[int] = 5
    ROWS: ClassVar[int] = 12
    SAMPLES: ClassVar[int] = 2
    SHIP_FEATURES: ClassVar[int] = 10
    CELL_FEATURES: ClassVar[int] = 7
    SIZE: ClassVar[int] = SHIP_FEATURES + COLUMNS * ROWS * SAMPLES * SAMPLES * CELL_FEATURES
    PUSH: ClassVar[dict[TileType, float]] = {TileType.PUSH_LEFT: -1.0, TileType.PUSH_RIGHT: 1.0}
    # The arrays of every track seen so far, shared by all observers since a track never changes.
    _maps: ClassVar[dict[int, tuple[Track, _TrackMap]]] = {}
    # Where the sample points are relative to the ship: one row of points across per step ahead.
    OFFSETS: ClassVar[tuple[np.ndarray, np.ndarray]] = np.meshgrid(
        (np.arange(COLUMNS * SAMPLES) - (COLUMNS * SAMPLES - 1) / 2) * Tile.WIDTH / SAMPLES,
        np.arange(ROWS * SAMPLES) * Tile.LENGTH / SAMPLES,
    )

    def observe(self, session: GameSession) -> np.ndarray:
        """Return the ``SIZE`` inputs describing the session's current state."""
        ship, track, config = session.ship, session.level.track, session.config
        position, velocity = ship.position, ship.velocity
        column, row = math.floor(position.x / Tile.WIDTH), math.floor(position.z / Tile.LENGTH)
        inputs = np.empty(self.SIZE)
        inputs[: self.SHIP_FEATURES] = (
            position.x / track.width * 2 - 1,
            position.x / Tile.WIDTH - column - 0.5,
            position.z / Tile.LENGTH - row - 0.5,
            velocity.z / config.max_speed,
            velocity.x / config.min_strafe_speed / 2,
            velocity.y / config.jump_velocity,
            float(ship.grounded),
            float(ship.air_jump_ready),
            session.fuel.fraction,
            session.oxygen.fraction,
        )
        across, ahead = self.OFFSETS
        points = self._map(track).look(position.x + across, position.z + ahead, position.y)
        inputs[self.SHIP_FEATURES :] = points.ravel()
        return inputs

    def _map(self, track: Track) -> _TrackMap:
        """Return the arrays of ``track``, built the first time it is seen."""
        if id(track) not in self._maps:
            self._maps[id(track)] = (track, _TrackMap(track, self.CELL_FEATURES))
        return self._maps[id(track)][1]

    @classmethod
    def forget(cls, track: Track) -> None:
        """Drop the arrays of ``track``, which will not be observed any more."""
        cls._maps.pop(id(track), None)

    @classmethod
    def cell(cls, tile: Tile) -> tuple[float, ...]:
        """Return the features of a point on ``tile``, its height left at 0."""
        kind = tile.tile_type
        return (
            1.0,
            0.0,
            float(kind is TileType.KILL),
            float(tile.tunnel is not None),
            float(kind is TileType.JUMP),
            cls.PUSH.get(kind, 0.0),
            float(kind in (TileType.REFUEL, TileType.AIR, TileType.BOOST))
            - float(kind in (TileType.SLOW, TileType.ICE)),
        )
