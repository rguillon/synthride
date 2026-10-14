from __future__ import annotations

from synthride.core.game_config import GameConfig
from synthride.core.game_event import GameEvent
from synthride.core.gauge import Gauge
from synthride.core.ship import Ship
from synthride.core.tile import Tile
from synthride.core.tile_type import TileType


class TileEffectApplier:
    """Applies the effect of the tile the ship is riding on."""

    def __init__(self, config: GameConfig) -> None:
        self._config = config

    def apply(self, tile: Tile, ship: Ship, fuel: Gauge) -> GameEvent | None:
        """Returns the event produced by the effect, or None when nothing changed."""
        match tile.tile_type:
            case TileType.BOOST:
                return self._boost(ship)
            case TileType.SLOW:
                return self._slow(ship)
            case TileType.KILL:
                return GameEvent.BURNED
            case TileType.REFUEL:
                return self._refuel(fuel)
            case TileType.FINISH:
                return GameEvent.LEVEL_WON
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

    def _refuel(self, fuel: Gauge) -> GameEvent | None:
        if fuel.is_full:
            return None
        fuel.refill()
        return GameEvent.REFUELED
