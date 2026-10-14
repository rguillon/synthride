# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""The game session: phase machine, lives and level simulation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from synthride.core.collision_outcome import CollisionOutcome
from synthride.core.collision_resolver import CollisionResolver
from synthride.core.game_config import GameConfig
from synthride.core.game_event import GameEvent
from synthride.core.game_phase import GamePhase
from synthride.core.gauge import Gauge
from synthride.core.ship import Ship
from synthride.core.ship_physics import ShipPhysics
from synthride.core.tile import Tile
from synthride.core.tile_effect_applier import TileEffectApplier
from synthride.core.vector3 import Vector3

if TYPE_CHECKING:
    from collections.abc import Sequence

    from synthride.core.collision_report import CollisionReport
    from synthride.core.level import Level
    from synthride.core.ship_input import ShipInput


class GameSession:
    """The whole game state: phase machine, lives, current level and its fixed-step simulation."""

    MAX_STEPS_PER_UPDATE = 30

    def __init__(self, levels: Sequence[Level], config: GameConfig | None = None) -> None:
        """Create a session on the title screen, with the first level loaded."""
        if not levels:
            msg = "a session needs at least one level"
            raise ValueError(msg)
        self.config = config or GameConfig()
        self.levels = tuple(levels)
        self.phase = GamePhase.TITLE
        self.lives = self.config.lives
        self.selected_level = 0
        self._physics = ShipPhysics(self.config)
        self._effects = TileEffectApplier(self.config)
        self._accumulator = 0.0
        self._phase_timer = 0.0
        self._load_level(0)

    @property
    def level(self) -> Level:
        """The level being played."""
        return self.levels[self.level_index]

    @property
    def progress(self) -> float:
        """How far along the track the ship is, from 0 to 1."""
        return min(1.0, max(0.0, self.ship.position.z / self.level.track.length))

    def open_level_select(self) -> None:
        """Switch to the level selection screen."""
        self.phase = GamePhase.LEVEL_SELECT

    def select_next_level(self) -> None:
        """Select the next level, wrapping around to the first."""
        self.selected_level = (self.selected_level + 1) % len(self.levels)

    def select_previous_level(self) -> None:
        """Select the previous level, wrapping around to the last."""
        self.selected_level = (self.selected_level - 1) % len(self.levels)

    def start(self) -> list[GameEvent]:
        """Start a new game with full lives at the selected level."""
        self.lives = self.config.lives
        return self._begin_level(self.selected_level)

    def return_to_title(self) -> None:
        """Go back to the title screen."""
        self.phase = GamePhase.TITLE

    def update(self, dt: float, ship_input: ShipInput) -> list[GameEvent]:
        """Advance the session by ``dt`` seconds and return the events that happened."""
        if self.phase is GamePhase.PLAYING:
            return self._simulate(dt, ship_input)
        if self.phase in (GamePhase.DYING, GamePhase.LEVEL_WON):
            self._phase_timer -= dt
            if self._phase_timer <= 0:
                return self._finish_transition()
        return []

    def _simulate(self, dt: float, ship_input: ShipInput) -> list[GameEvent]:
        step = self.config.fixed_step
        self._accumulator = min(self._accumulator + dt, step * self.MAX_STEPS_PER_UPDATE)
        events: list[GameEvent] = []
        while self._accumulator >= step and self.phase is GamePhase.PLAYING:
            self._accumulator -= step
            events.extend(self._step(ship_input, step))
        return events

    def _step(self, ship_input: ShipInput, dt: float) -> list[GameEvent]:
        ship = self.ship
        was_grounded = ship.grounded
        start_z = ship.position.z
        jump = self._physics.apply(ship, ship_input, self.level.gravity, dt)
        events = [] if jump is None else [jump]
        events += self._handle_collisions(self._resolver.move(ship, dt), was_grounded=was_grounded)
        if self.phase is not GamePhase.PLAYING:
            return events
        self.fuel.drain((ship.position.z - start_z) * self.config.fuel_per_unit)
        self.oxygen.drain(dt)
        if self.fuel.is_empty:
            return [*events, *self._die(GameEvent.OUT_OF_FUEL)]
        if self.oxygen.is_empty:
            return [*events, *self._die(GameEvent.OUT_OF_OXYGEN)]
        if ship.position.z >= self.level.track.length:
            return [*events, *self._win()]
        return events

    def _handle_collisions(self, reports: list[CollisionReport], *, was_grounded: bool) -> list[GameEvent]:
        events: list[GameEvent] = []
        surface = None
        for report in reports:
            match report.outcome:
                case CollisionOutcome.CRASHED:
                    return [*events, *self._die(GameEvent.CRASHED)]
                case CollisionOutcome.FELL:
                    return [*events, *self._die(GameEvent.FELL)]
                case CollisionOutcome.NUDGED:
                    events.append(GameEvent.NUDGED)
                case CollisionOutcome.BUMPED:
                    events.append(GameEvent.BUMPED)
                case CollisionOutcome.SCRAPED_LEFT:
                    events.append(GameEvent.SCRAPED_LEFT)
                case CollisionOutcome.SCRAPED_RIGHT:
                    events.append(GameEvent.SCRAPED_RIGHT)
                case _:  # CollisionOutcome.LANDED
                    if not was_grounded:
                        events.append(GameEvent.LANDED)
                    if report.tile is not None:
                        events.extend(self._apply_tile(report.tile))
                        surface = report.tile.tile_type
        self.ship.surface = surface
        return events

    def _apply_tile(self, tile: Tile) -> list[GameEvent]:
        event = self._effects.apply(tile, self.ship, self.fuel, self.oxygen)
        if event is GameEvent.BURNED:
            return self._die(event)
        if event is GameEvent.LEVEL_WON:
            return self._win()
        return [] if event is None else [event]

    def _die(self, cause: GameEvent) -> list[GameEvent]:
        self.lives -= 1
        self.phase = GamePhase.DYING
        self._phase_timer = self.config.dying_seconds
        return [cause, GameEvent.LIFE_LOST]

    def _win(self) -> list[GameEvent]:
        self.phase = GamePhase.LEVEL_WON
        self._phase_timer = self.config.level_won_seconds
        return [GameEvent.LEVEL_WON]

    def _finish_transition(self) -> list[GameEvent]:
        if self.phase is GamePhase.DYING:
            if self.lives > 0:
                return self._begin_level(self.level_index)
            self.phase = GamePhase.GAME_OVER
            return [GameEvent.GAME_OVER]
        if self.level_index + 1 < len(self.levels):
            return self._begin_level(self.level_index + 1)
        self.phase = GamePhase.VICTORY
        return [GameEvent.GAME_COMPLETED]

    def _begin_level(self, index: int) -> list[GameEvent]:
        self._load_level(index)
        self.phase = GamePhase.PLAYING
        return [GameEvent.LEVEL_STARTED]

    def _load_level(self, index: int) -> None:
        self.level_index = index
        level = self.levels[index]
        track = level.track
        start_x, start_z = track.width / 2, self.config.ship_length / 2 + 0.1
        start_y = max(
            (tile.top for tile in (track.tile_at(column, 0) for column in range(track.COLUMNS)) if tile is not None),
            default=Tile.HEIGHT_UNIT,
        )
        self.ship = Ship.from_config(Vector3(start_x, start_y, start_z), self.config)
        self.ship.grounded = track.surface_height_at(start_x, start_z) == start_y
        self.fuel = Gauge(level.fuel_capacity)
        self.oxygen = Gauge(level.oxygen_seconds)
        self._resolver = CollisionResolver(track, self.config)
        self._accumulator = 0.0
