# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""Checks that a level can surely be finished, from its tiles and the physics alone."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar, TypeGuard

from synthride.core.game_config import GameConfig
from synthride.core.tile import Tile
from synthride.core.tile_type import TileType
from tests.ai.track_reach import TrackReach

if TYPE_CHECKING:
    from synthride.core.level import Level
    from synthride.core.track import Track


@dataclass(frozen=True)
class Requirements:
    """The fuel and oxygen a level surely needs, refills on the safe path included."""

    fuel: float
    oxygen_seconds: float


@dataclass(frozen=True)
class _Survey:
    """The cells of each row the ship can surely reach, its top speed on each row, and the row the run ends on."""

    reachable: list[set[int]]
    speeds: list[float]
    end_row: int | None


class FinishabilityChecker:
    """Finds the cells a ship can surely reach, row after row, and the fuel and oxygen the trip needs.

    From a safe tile (any tile but a kill tile) the ship can ride onto the tile ahead when it does not rise above
    the step tolerance, slide onto a flat neighbour of the same height and tunnel, or jump, without a tunnel roof
    above, to a tile up to one column aside further on, as :class:`TrackReach` allows, over tiles no higher than its
    take-off, or drop to any lower tile. A jump pad always launches the ship. In a tunnel, the ship can only jump
    once out of it, so its jumps out of a tunnel's last row reach one ship length less. The ship's top speed is
    followed row by row, from standstill at the start, accelerating on every row and capped on rows where it can only
    ride slow tiles. The fuel and oxygen are judged at a cautious ``CRUISE_RATIO`` of the top speed, between refills
    on the path.
    """

    START_COLUMNS: ClassVar[tuple[int, int]] = (3, 4)
    CRUISE_RATIO: ClassVar[float] = 0.5

    def __init__(self, config: GameConfig | None = None, margin: float = 0.65) -> None:
        """Judge with the tunables of ``config``, counting only ``margin`` of the ship's jumps."""
        self._config = config or GameConfig()
        self._margin = margin

    def reach(self, gravity: float) -> TrackReach:
        """Return the jump limits on a level of gravity ``gravity``."""
        return TrackReach(self._config, gravity, self._margin)

    def check(self, level: Level) -> list[str]:
        """Return what makes ``level`` unfinishable, nothing if it can surely be finished."""
        track = level.track
        start = [track.tile_at(column, 0) for column in self.START_COLUMNS]
        if not self._sideways(start[0], start[1]):
            return [f"the ship starts over columns {self.START_COLUMNS}: they need flat safe tiles of one height"]
        requirements = self.requirements(level)
        if requirements is None:
            return ["no safe path reaches the end of the track"]
        problems = []
        if level.fuel_capacity < requirements.fuel:
            problems.append(f"needs {requirements.fuel:.1f} fuel, has {level.fuel_capacity:.1f}")
        if level.oxygen_seconds < requirements.oxygen_seconds:
            problems.append(f"needs {requirements.oxygen_seconds:.1f}s of oxygen, has {level.oxygen_seconds:.1f}s")
        return problems

    def requirements(self, level: Level) -> Requirements | None:
        """Return the fuel and oxygen ``level`` surely needs, or None when no safe path reaches its end."""
        survey = self._survey(level)
        if survey.end_row is None:
            return None
        config, track = self._config, level.track
        cruise = config.max_speed * self.CRUISE_RATIO
        slow_cruise = min(cruise, self.reach(level.gravity).slow_speed)
        fuel_rows = most_fuel_rows = 0
        seconds = most_seconds = 0.0
        for row in range(survey.end_row + 1):
            types = self._types(track, row, survey.reachable[row])
            pace = slow_cruise if types == {TileType.SLOW} else cruise
            fuel_rows += 1
            seconds += Tile.LENGTH / min(pace, survey.speeds[row])
            most_fuel_rows, most_seconds = max(most_fuel_rows, fuel_rows), max(most_seconds, seconds)
            if TileType.REFUEL in types:
                fuel_rows = 0
            if TileType.AIR in types:
                seconds = 0.0
        return Requirements(most_fuel_rows * Tile.LENGTH * config.fuel_per_unit, most_seconds)

    def _survey(self, level: Level) -> _Survey:
        track, reach = level.track, self.reach(level.gravity)
        rows = track.row_count
        reachable: list[set[int]] = [set() for _ in range(rows)]
        reachable[0].update(self.START_COLUMNS)
        speeds: list[float] = []
        speed = 0.0
        for row in range(rows):
            cells = reachable[row]
            self._spread(track, row, cells)
            types = self._types(track, row, cells)
            speed = reach.next_speed(speed, reach.slow_speed if types == {TileType.SLOW} else self._config.max_speed)
            speeds.append(speed)
            if TileType.FINISH in types or (cells and row == rows - 1):
                return _Survey(reachable, speeds, row)
            for column in cells:
                tile = track.tile_at(column, row)
                assert tile is not None
                if tile.tile_type is not TileType.JUMP and self._can_ride(track, tile, track.tile_at(column, row + 1)):
                    reachable[row + 1].add(column)
                self._jump(track, reach, tile, speed, reachable)
        return _Survey(reachable, speeds, None)

    def _spread(self, track: Track, row: int, cells: set[int]) -> None:
        """Add to ``cells`` every cell of ``row`` the ship can slide to from them."""
        pending = list(cells)
        while pending:
            column = pending.pop()
            for neighbour in (column - 1, column + 1):
                if neighbour not in cells and self._sideways(track.tile_at(column, row), track.tile_at(neighbour, row)):
                    cells.add(neighbour)
                    pending.append(neighbour)

    def _sideways(self, tile: Tile | None, neighbour: Tile | None) -> bool:
        """Return True if the ship can slide from ``tile`` onto ``neighbour``, beside it."""
        return (
            self._safe(tile)
            and self._safe(neighbour)
            and tile.slope is None
            and neighbour.slope is None
            and tile.tunnel is neighbour.tunnel
            and abs(tile.top - neighbour.top) <= self._config.step_tolerance
        )

    def _can_ride(self, track: Track, tile: Tile, ahead: Tile | None) -> bool:
        """Return True if the ship can ride from ``tile`` onto ``ahead``, the tile in front of it."""
        if not self._safe(ahead):
            return False
        x = (tile.column + 0.5) * Tile.WIDTH
        rise = ahead.height_at(x, ahead.row * Tile.LENGTH) - tile.height_at(x, ahead.row * Tile.LENGTH)
        if rise > self._config.step_tolerance:
            return False
        entering = ahead.tunnel is not None and (tile.tunnel is not ahead.tunnel or tile.level != ahead.level)
        return not entering or self._tunnel_width(track, ahead) >= 2

    def _jump(self, track: Track, reach: TrackReach, tile: Tile, speed: float, reachable: list[set[int]]) -> None:
        """Add the cells the ship can jump to from ``tile`` at ``speed`` to ``reachable``."""
        config = self._config
        if tile.tunnel is not None and self._covered(track, tile.column, tile.row + 1):
            return
        launch = config.launch_velocity if tile.tile_type is TileType.JUMP else config.jump_velocity
        # A jump off a ramp keeps the ramp's climb.
        launch += max(0.0, tile.gradient((tile.column + 0.5) * Tile.WIDTH, (tile.row + 1) * Tile.LENGTH)[1]) * speed
        if tile.tile_type is TileType.SLOW:
            speed = min(speed, reach.slow_speed)
        extra = config.ship_length if tile.tunnel is not None else 0.0
        furthest = reach.max_gap(launch, speed, Tile.HEIGHT_UNIT - tile.top)
        columns = [column for column in (tile.column - 1, tile.column, tile.column + 1) if 0 <= column < track.COLUMNS]
        clear = dict.fromkeys(columns, True)
        for target in range(tile.row + 1, min(track.row_count, tile.row + 2 + furthest)):
            gap = target - tile.row - 1
            for column in columns:
                landing = track.tile_at(column, target)
                if (
                    clear[tile.column]
                    and clear[column]
                    and self._safe(landing)
                    and landing.tunnel is None
                    and reach.can_jump(launch, speed, gap, landing.top - tile.top, extra)
                ):
                    reachable[target].add(column)
            for column in columns:
                below = track.tile_at(column, target)
                clear[column] = clear[column] and (below is None or (below.tunnel is None and below.top <= tile.top))

    @staticmethod
    def _covered(track: Track, column: int, row: int) -> bool:
        """Return True if a tunnel covers the cell at ``column`` and ``row``."""
        tile = track.tile_at(column, row)
        return tile is not None and tile.tunnel is not None

    @staticmethod
    def _tunnel_width(track: Track, tile: Tile) -> int:
        """Return how many columns wide the tunnel over ``tile`` is."""
        span = [
            span
            for span in track.tunnels
            if span.row == tile.row and span.first_column <= tile.column <= span.last_column
        ]
        return span[0].last_column - span[0].first_column + 1 if span else 0

    @staticmethod
    def _types(track: Track, row: int, columns: set[int]) -> set[TileType]:
        """Return the kinds of the tiles at ``columns`` of ``row``."""
        return {tile.tile_type for tile in (track.tile_at(column, row) for column in columns) if tile is not None}

    @staticmethod
    def _safe(tile: Tile | None) -> TypeGuard[Tile]:
        """Return True if the ship can ride ``tile``."""
        return tile is not None and tile.tile_type is not TileType.KILL
