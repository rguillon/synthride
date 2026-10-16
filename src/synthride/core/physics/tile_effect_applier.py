# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""The effects of the tiles the ship rides on."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from synthride.core.gameplay.game_event import GameEvent
from synthride.core.world.tile_type import TileType

if TYPE_CHECKING:
    from synthride.core.gameplay.game_config import GameConfig
    from synthride.core.gameplay.gauge import Gauge
    from synthride.core.gameplay.ship import Ship
    from synthride.core.world.tile import Tile


class TileEffectApplier:
    """Applies the effect of the tile the ship is riding on.

    It runs on every step the ship touches a tile, before ``ship.surface`` is updated, so ``ship.surface``
    still tells which tile the ship rode on before. Effects keep acting while the ship rides a patch, but
    the ones that would otherwise fire on every step (slowing, refills, ice, pushers) only report an
    event when the ship gets onto it.
    """

    RIDING_EVENTS: ClassVar[dict[TileType, GameEvent]] = {
        TileType.ICE: GameEvent.SKIDDED,
        TileType.PUSH_LEFT: GameEvent.PUSHED,
        TileType.PUSH_RIGHT: GameEvent.PUSHED,
    }
    ONCE_PER_PATCH = frozenset({GameEvent.SLOWED, GameEvent.REFUELED, GameEvent.REFILLED_AIR, *RIDING_EVENTS.values()})

    def __init__(self, config: GameConfig) -> None:
        """Use the tunables from ``config``."""
        self._config = config

    def apply(self, tile: Tile, ship: Ship, fuel: Gauge, oxygen: Gauge) -> GameEvent | None:
        """Return the event produced by the effect, or None when nothing worth reporting happened."""
        event = self._effect(tile, ship, fuel, oxygen)
        if event in self.ONCE_PER_PATCH and ship.surface is tile.tile_type:
            return None
        return event

    def _effect(self, tile: Tile, ship: Ship, fuel: Gauge, oxygen: Gauge) -> GameEvent | None:  # noqa: PLR0911
        match tile.tile_type:
            case TileType.BOOST:
                return self._boost(ship)
            case TileType.SLOW:
                return self._slow(ship)
            case TileType.KILL:
                return GameEvent.BURNED
            case TileType.REFUEL:
                return self._refill(fuel, GameEvent.REFUELED)
            case TileType.AIR:
                return self._refill(oxygen, GameEvent.REFILLED_AIR)
            case TileType.JUMP:
                return self._launch(ship)
            case TileType.FINISH:
                return GameEvent.LEVEL_WON
            case tile_type if tile_type in self.RIDING_EVENTS:
                return self.RIDING_EVENTS[tile_type]
            case _:
                return None

    def _boost(self, ship: Ship) -> GameEvent | None:
        boosted = self._config.max_speed * self._config.boost_factor
        if ship.speed >= boosted:
            return None
        was_boosting = ship.speed > self._config.max_speed
        ship.velocity = ship.velocity.with_z(boosted)
        return None if was_boosting else GameEvent.BOOSTED

    def _slow(self, ship: Ship) -> GameEvent | None:
        limit = self._config.max_speed * self._config.slow_factor
        if ship.speed <= limit:
            return None
        ship.velocity = ship.velocity.with_z(limit)
        return GameEvent.SLOWED

    def _launch(self, ship: Ship) -> GameEvent:
        ship.velocity = ship.velocity.with_y(self._config.launch_velocity)
        ship.grounded = False
        return GameEvent.LAUNCHED

    @staticmethod
    def _refill(gauge: Gauge, event: GameEvent) -> GameEvent | None:
        if gauge.is_full:
            return None
        gauge.refill()
        return event
