# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""What the neural network sees of the game."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, ClassVar

from synthride.core.tile import Tile
from synthride.core.tile_type import TileType

if TYPE_CHECKING:
    from synthride.core.game_session import GameSession


class ShipObserver:
    """Turns the session into the network's inputs: the ship's state and the track around and ahead of it.

    The track view covers ``COLUMNS`` tiles across, centred on the ship, and ``ROWS`` tiles ahead, starting at the
    ship. It samples each tile's area at ``SAMPLES`` x ``SAMPLES`` points laid out around the ship's exact position
    rather than on the tile grid, so tile borders move through the view as the ship moves. Each point gives whether
    a tile is under it, the height of its top there relative to the ship and its kind.
    """

    COLUMNS: ClassVar[int] = 5
    ROWS: ClassVar[int] = 12
    SAMPLES: ClassVar[int] = 4
    SHIP_FEATURES: ClassVar[int] = 10
    CELL_FEATURES: ClassVar[int] = 7
    SIZE: ClassVar[int] = SHIP_FEATURES + COLUMNS * ROWS * SAMPLES * SAMPLES * CELL_FEATURES
    PUSH: ClassVar[dict[TileType, float]] = {TileType.PUSH_LEFT: -1.0, TileType.PUSH_RIGHT: 1.0}
    EMPTY: ClassVar[tuple[float, ...]] = (0.0,) * CELL_FEATURES

    def observe(self, session: GameSession) -> list[float]:
        """Return the ``SIZE`` inputs describing the session's current state."""
        ship, track, config = session.ship, session.level.track, session.config
        position, velocity = ship.position, ship.velocity
        column, row = math.floor(position.x / Tile.WIDTH), math.floor(position.z / Tile.LENGTH)
        inputs = [
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
        ]
        across, step_x, step_z = self.COLUMNS * self.SAMPLES, Tile.WIDTH / self.SAMPLES, Tile.LENGTH / self.SAMPLES
        for ahead in range(self.ROWS * self.SAMPLES):
            z = position.z + ahead * step_z
            for side in range(across):
                x = position.x + (side - (across - 1) / 2) * step_x
                tile = track.tile_at(math.floor(x / Tile.WIDTH), math.floor(z / Tile.LENGTH))
                inputs.extend(self._cell(tile, x, z, position.y))
        return inputs

    def _cell(self, tile: Tile | None, x: float, z: float, height: float) -> tuple[float, ...]:
        if tile is None:
            return self.EMPTY
        kind = tile.tile_type
        return (
            1.0,
            max(-1.0, min(1.0, (tile.height_at(x, z) - height) / 2)),
            float(kind is TileType.KILL),
            float(tile.tunnel is not None),
            float(kind is TileType.JUMP),
            self.PUSH.get(kind, 0.0),
            float(kind in (TileType.REFUEL, TileType.AIR, TileType.BOOST))
            - float(kind in (TileType.SLOW, TileType.ICE)),
        )
