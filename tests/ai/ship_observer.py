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
    """A track's tiles as arrays, so that many points of it can be looked up at once."""

    def __init__(self, track: Track, features: int) -> None:
        self.rows, self.columns = track.row_count, track.COLUMNS
        self.cells = np.zeros((self.rows, self.columns, features))
        self.base = np.zeros((self.rows, self.columns))
        self.slope_x = np.zeros((self.rows, self.columns))
        self.slope_z = np.zeros((self.rows, self.columns))
        for tile in track.tiles():
            self.cells[tile.row, tile.column] = ShipObserver.cell(tile)
            self.base[tile.row, tile.column] = tile.base
            if tile.slope is not None:
                self.slope_x[tile.row, tile.column], self.slope_z[tile.row, tile.column] = tile.slope.direction

    def look(self, x: np.ndarray, z: np.ndarray, height: float) -> np.ndarray:
        """Return the features of the points ``(x, z)``, with heights relative to ``height``, zero off the track."""
        u, v = x / Tile.WIDTH, z / Tile.LENGTH
        column, row = np.floor(u).astype(int), np.floor(v).astype(int)
        u, v = u - column, v - row
        inside = (column >= 0) & (column < self.columns) & (row >= 0) & (row < self.rows)
        column, row = np.where(inside, column, 0), np.where(inside, row, 0)
        cells = self.cells[row, column] * inside[..., np.newaxis]
        slope_x, slope_z = self.slope_x[row, column], self.slope_z[row, column]
        rise = np.minimum(self._ramp(slope_x, u), self._ramp(slope_z, v))
        top = self.base[row, column] + Tile.HEIGHT_UNIT * np.where(np.isinf(rise), 0.0, rise)
        cells[..., 1] = np.clip((top - height) / 2, -1.0, 1.0) * cells[..., 0]
        return cells

    @staticmethod
    def _ramp(sign: np.ndarray, t: np.ndarray) -> np.ndarray:
        """Return how far up a slope rising toward ``sign`` the points ``t`` are, infinite where it is flat."""
        return np.where(sign > 0, t, np.where(sign < 0, 1 - t, np.inf))


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
