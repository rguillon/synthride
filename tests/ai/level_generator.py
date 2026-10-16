# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""Generates levels of a chosen difficulty that can surely be finished."""

from __future__ import annotations

import json
import math
import random
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Any, ClassVar

from synthride.core.game_config import GameConfig
from synthride.core.level_parser import LevelParser
from synthride.core.tile import Tile
from synthride.core.track import Track
from tests.ai.difficulty_knobs import DifficultyKnobs
from tests.ai.finishability_checker import FinishabilityChecker
from tests.ai.track_builder import TrackBuilder

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from synthride.core.level import Level

Draws = list[float]


class LevelGenerationError(RuntimeError):
    """Raised when a generated level breaks the rules that make it finishable, a bug of the generator."""


@dataclass(frozen=True)
class Obstacle:
    """One obstacle of a level: its kind, how hard it is from 0 to 1, and the random numbers shaping it."""

    kind: str
    intensity: float
    draws: tuple[float, ...]

    def harder(self, step: float) -> Obstacle:
        """Return the same obstacle, ``step`` harder, at most 1."""
        return replace(self, intensity=min(1.0, self.intensity + step))


class LevelGenerator:
    """Builds levels as a row of slots along a straight line, each slot plain road or an :class:`Obstacle`.

    With every slot plain, the level is a simple straight line from the start to the finish.
    :class:`~tests.ai.level_designer.LevelDesigner` then fills slots with obstacles and makes them harder, one at a
    time. Each obstacle keeps a safe lane going, sized within what :class:`~tests.ai.track_reach.TrackReach` allows,
    and every level is checked by :class:`FinishabilityChecker` before it is returned. Some obstacles fork the track
    into two side-by-side routes, each with its own obstacle, and the rest after an obstacle may spread the track wide
    or strew it with blocks. The seed picks the level's name.
    """

    KINDS: ClassVar[tuple[str, ...]] = (
        "bend",
        "narrow",
        "gap",
        "gap",
        "climb",
        "drop",
        "step",
        "ice",
        "push",
        "kill",
        "tunnel",
        "pad",
        "slow",
        "fork",
        "fork",
        "slalom",
        "slalom",
        "hops",
        "hops",
    )
    ROUTES: ClassVar[tuple[str, ...]] = ("kill", "gap", "ice", "push", "narrow", "tunnel", "raised")
    DRAWS: ClassVar[int] = 16
    WIDE_REST: ClassVar[float] = 0.3
    NAME_PREFIX: ClassVar[str] = "dev - "
    ADJECTIVES: ClassVar[tuple[str, ...]] = (
        "Neon",
        "Chrome",
        "Laser",
        "Static",
        "Velvet",
        "Ultra",
        "Retro",
        "Cobalt",
        "Plasma",
        "Phantom",
        "Electric",
        "Infra",
    )
    NOUNS: ClassVar[tuple[str, ...]] = (
        "Causeway",
        "Circuit",
        "Drift",
        "Overpass",
        "Spiral",
        "Mirage",
        "Gauntlet",
        "Pulse",
        "Horizon",
        "Relay",
        "Run",
        "Sprawl",
    )

    START_WIDTH: ClassVar[int] = 4
    PLAIN_ROWS: ClassVar[int] = 10

    def __init__(self, seed: int, gravity: float = 18.0, config: GameConfig | None = None) -> None:
        """Build levels named from ``seed``, of gravity ``gravity``."""
        self.seed = seed
        self.gravity = gravity
        self._checker = FinishabilityChecker(config or GameConfig())
        self._parser = LevelParser()
        layout = random.Random(seed)
        self.name = f"{self.NAME_PREFIX}{layout.choice(self.ADJECTIVES)} {layout.choice(self.NOUNS)}"

    def obstacle(self, rng: random.Random, intensity: float) -> Obstacle:
        """Return a random obstacle of ``intensity``."""
        return Obstacle(rng.choice(self.KINDS), intensity, tuple(rng.random() for _ in range(self.DRAWS)))

    def build(self, slots: Sequence[Obstacle | None]) -> dict[str, Any]:
        """Return the level of ``slots``, from the start, as the JSON object of a level file."""
        builder = TrackBuilder(self._checker.reach(self.gravity))
        builder.low, builder.high = TrackBuilder.lane_around(3.5, self.START_WIDTH)
        builder.lane(count=self.PLAIN_ROWS)
        segments: dict[str, Callable[[TrackBuilder, DifficultyKnobs, Draws], None]] = {
            kind: getattr(self, f"_{kind}") for kind in set(self.KINDS)
        }
        for slot in slots:
            if slot is None:
                builder.lane(count=self.PLAIN_ROWS)
                continue
            knobs = DifficultyKnobs(slot.intensity)
            segments[slot.kind](builder, knobs, list(slot.draws))
            self._rest(builder, knobs, list(slot.draws))
        builder.move_to(*TrackBuilder.lane_around(builder.center, max(2, builder.width)), 2)
        builder.lane(count=3)
        builder.lane("F", count=4)
        intensities = [0.0 if slot is None else slot.intensity for slot in slots]
        return self._with_resources(builder.encoded(), DifficultyKnobs(sum(intensities) / max(1, len(intensities))))

    def check(self, document: dict[str, Any]) -> list[str]:
        """Return what makes the level of ``document`` unfinishable, nothing if it can surely be finished."""
        return self._checker.check(self._parse(document))

    def _with_resources(self, track: Sequence[Sequence[int | str]], knobs: DifficultyKnobs) -> dict[str, Any]:
        """Return the level file of ``track``, with the fuel and oxygen it surely needs plus the slack of ``knobs``."""
        document: dict[str, Any] = {"name": self.name, "gravity": self.gravity, "track": [list(row) for row in track]}
        requirements = self._checker.requirements(self._parse(document))
        if requirements is None:
            msg = f"{self.name!r}: no safe path reaches the end of the track"
            raise LevelGenerationError(msg)
        document = {
            "name": self.name,
            "gravity": self.gravity,
            "oxygen": math.ceil(requirements.oxygen_seconds * knobs.oxygen_slack),
            "fuel": math.ceil(requirements.fuel * knobs.fuel_slack),
            "track": document["track"],
        }
        problems = self.check(document)
        if problems:
            msg = f"{self.name!r}: {'; '.join(problems)}"
            raise LevelGenerationError(msg)
        return document

    def _parse(self, document: dict[str, Any]) -> Level:
        return self._parser.parse(json.dumps(document))

    @staticmethod
    def _shifted(builder: TrackBuilder, offset: float, width: int) -> tuple[int, int]:
        return TrackBuilder.lane_around(builder.center + offset, width)

    def _rest(self, builder: TrackBuilder, knobs: DifficultyKnobs, draws: Draws) -> None:
        """Ride a short straight after a segment, maybe wide, with a boost, a refill or pillars beside it."""
        if draws[10] < self.WIDE_REST:
            builder.move_to(*self._shifted(builder, 0, 6 + int(draws[11] * 3)), knobs.shift_rows())
        rows = knobs.rest_rows(draws[1])
        if draws[13] < 0.3:
            builder.lane("B")
            rows -= 1
        elif draws[13] < 0.5:
            builder.lane("R" if draws[14] < 0.5 else "O")
            rows -= 1
        if draws[12] < 0.5 and builder.width >= 3:
            self._scatter(builder, knobs, max(1, rows), random.Random(draws[15]))
        elif draws[12] < 0.8 and builder.width < Track.COLUMNS:
            self._pillars(builder, max(1, rows), draws[15])
        elif rows > 0:
            builder.lane(count=rows)

    @staticmethod
    def _scatter(builder: TrackBuilder, knobs: DifficultyKnobs, rows: int, rng: random.Random) -> None:
        """Ride ``rows`` rows strewn with single tall blocks or kill tiles to steer around."""
        level = builder.level
        density = 0.35 + 0.35 * knobs.level
        for _ in range(rows):
            cells = dict.fromkeys(range(builder.low, builder.high + 1), f"N{level}")
            if rng.random() < density:
                hazard = f"K{level}" if rng.random() < 0.4 else f"N{min(8, level + 2)}"
                cells[builder.low + int(rng.random() * builder.width)] = hazard
            builder.row(cells)

    @staticmethod
    def _pillars(builder: TrackBuilder, rows: int, draw: float) -> None:
        """Ride ``rows`` rows with tall blocks standing beside the lane, every other pair of rows."""
        level = builder.level
        pillar = f"N{min(8, level + 2 + int(draw * 3))}"
        lane = dict.fromkeys(range(builder.low, builder.high + 1), f"N{level}")
        sides = {column: pillar for column in (builder.low - 1, builder.high + 1) if 0 <= column < Track.COLUMNS}
        for index in range(rows):
            builder.row({**lane, **sides} if index % 4 < 2 else lane)

    def _bend(self, builder: TrackBuilder, knobs: DifficultyKnobs, draws: Draws) -> None:
        """Snake sideways one way, then back the other way."""
        direction = 1 if draws[3] < 0.5 else -1
        for _ in range(2):
            target = self._shifted(builder, direction * knobs.bend(draws[4]), builder.width)
            if target == (builder.low, builder.high):
                direction = -direction
                target = self._shifted(builder, direction * knobs.bend(draws[4]), builder.width)
            builder.move_to(*target, knobs.shift_rows())
            builder.lane(count=max(1, knobs.section_rows(draws[5]) // 4))
            direction = -direction

    def _narrow(self, builder: TrackBuilder, knobs: DifficultyKnobs, draws: Draws) -> None:
        """Squeeze through a narrow lane between pillars."""
        builder.move_to(*self._shifted(builder, 0, knobs.lane_width(draws[2])), knobs.shift_rows())
        self._pillars(builder, knobs.section_rows(draws[5]), draws[6])

    def _slalom(self, builder: TrackBuilder, knobs: DifficultyKnobs, draws: Draws) -> None:
        """Weave between gates, kill tiles or tall blocks closing one side of the lane then the other."""
        width = min(Track.COLUMNS, max(3, knobs.lane_width(draws[2]) + 2))
        builder.move_to(*self._shifted(builder, 0, width), knobs.shift_rows())
        width, level = builder.width, builder.level
        opening = max(1, round((width - 1) * (1 - knobs.level) * 0.7))
        hazard = f"K{level}" if draws[4] < 0.5 else f"N{min(8, level + 2)}"
        left = draws[5] < 0.5
        builder.lane(count=2)
        for _ in range(2 + int(draws[3] * (2 + 3 * knobs.level))):
            closed = (
                range(builder.low, builder.high - opening + 1)
                if left
                else range(builder.low + opening, builder.high + 1)
            )
            cells = dict.fromkeys(range(builder.low, builder.high + 1), f"N{level}")
            cells.update(dict.fromkeys(closed, hazard))
            builder.row(cells, count=1 + (draws[6] < knobs.level))
            builder.lane(count=min(6, 1 + knobs.shift_rows() * (width - opening)))
            left = not left

    def _hops(self, builder: TrackBuilder, knobs: DifficultyKnobs, draws: Draws) -> None:
        """Hop across a chain of small platforms, each a little aside from the last."""
        rng = random.Random(draws[7])
        launch = builder.reach.config.jump_velocity
        platform = max(1, round(4 - 3 * knobs.level))
        builder.lane(count=2)
        for _ in range(3 + int(draws[3] * (1 + 3 * knobs.level))):
            longest = builder.reach.max_gap(launch, builder.speed, 0.0)
            if longest < 1:
                builder.lane(count=2)
                continue
            builder.gap(min(longest, 1 + int(rng.random() * (1 + 2 * knobs.level))))
            width = min(builder.width, knobs.lane_width(rng.random()))
            builder.low, builder.high = self._shifted(builder, round(2 * rng.random() - 1), width)
            builder.lane(count=platform)
        builder.lane(count=2)

    def _gap(self, builder: TrackBuilder, knobs: DifficultyKnobs, draws: Draws) -> None:
        """Leave a gap to jump, landing a little aside, maybe higher or lower."""
        builder.lane(count=2)
        change = 0
        if knobs.rises(draws[3]) and builder.level < TrackBuilder.TOP_LEVEL:
            change = 1
        elif draws[3] > 0.75 and builder.level > 1:
            change = -min(builder.level - 1, knobs.height_change(draws[4]))
        self._jump_over(builder, knobs, draws, builder.reach.config.jump_velocity, change)

    def _jump_over(
        self, builder: TrackBuilder, knobs: DifficultyKnobs, draws: Draws, launch: float, change: int
    ) -> None:
        """Leave a gap after the last row, to jump with ``launch`` to a landing ``change`` levels higher."""
        reach = builder.reach
        longest = reach.max_gap(launch, builder.speed, change * Tile.HEIGHT_UNIT)
        if longest < 1:
            change = 0
            longest = reach.max_gap(launch, builder.speed, 0.0)
        if longest < 1:
            return
        builder.gap(min(longest, 1 + round(knobs.gap_share(draws[5]) * (longest - 1))))
        builder.low, builder.high = self._shifted(builder, round(2 * draws[6] - 1), knobs.lane_width(draws[2]))
        builder.level += change
        builder.lane(count=2)

    def _climb(self, builder: TrackBuilder, knobs: DifficultyKnobs, draws: Draws) -> None:
        """Climb or go down ramps, one level per row."""
        levels = knobs.height_change(draws[3])
        if builder.level + levels <= TrackBuilder.TOP_LEVEL and (draws[4] < 0.6 or builder.level - levels < 1):
            for _ in range(levels):
                builder.lane(suffix="f")
                builder.level += 1
        else:
            for _ in range(min(levels, builder.level - 1)):
                builder.level -= 1
                builder.lane(suffix="b")
        builder.lane(count=2)

    def _drop(self, builder: TrackBuilder, knobs: DifficultyKnobs, draws: Draws) -> None:
        """Drop to a lower lane, or climb ramps when already at the bottom."""
        if builder.level == 1:
            self._climb(builder, knobs, draws)
            return
        builder.level -= min(builder.level - 1, knobs.height_change(draws[3]))
        builder.low, builder.high = self._shifted(builder, round(2 * draws[6] - 1), knobs.lane_width(draws[2]))
        builder.lane(count=2)

    def _step(self, builder: TrackBuilder, knobs: DifficultyKnobs, draws: Draws) -> None:
        """Raise the lane by one level, to jump onto."""
        if builder.level >= TrackBuilder.TOP_LEVEL:
            self._drop(builder, knobs, draws)
            return
        builder.lane(count=2)
        if not builder.reach.can_jump(builder.reach.config.jump_velocity, builder.speed, 0, Tile.HEIGHT_UNIT):
            return
        builder.level += 1
        builder.lane(count=2)

    def _ice(self, builder: TrackBuilder, knobs: DifficultyKnobs, draws: Draws) -> None:
        """Ride a stretch of ice, which may bend slowly."""
        builder.move_to(*self._shifted(builder, 0, knobs.lane_width(draws[2])), knobs.shift_rows())
        rows = knobs.section_rows(draws[5])
        builder.lane("I", count=rows // 2)
        if draws[3] < knobs.level:
            direction = 1 if draws[4] < 0.5 else -1
            builder.move_to(*self._shifted(builder, direction, builder.width), max(3, knobs.shift_rows()), "I")
        builder.lane("I", count=rows - rows // 2)

    def _push(self, builder: TrackBuilder, knobs: DifficultyKnobs, draws: Draws) -> None:
        """Ride a crosswind of pushers."""
        builder.move_to(*self._shifted(builder, 0, max(2, knobs.lane_width(draws[2]))), knobs.shift_rows())
        builder.lane("<" if draws[3] < 0.5 else ">", count=min(knobs.section_rows(draws[5]), 10))

    def _kill(self, builder: TrackBuilder, knobs: DifficultyKnobs, draws: Draws) -> None:
        """Cross a strip of kill tiles through a safe window."""
        window = min(builder.width, knobs.lane_width(draws[2]))
        first = builder.low + int(draws[3] * (builder.width - window + 1))
        level = builder.level
        around = range(max(0, builder.low - 1), min(Track.COLUMNS, builder.high + 2))
        cells = dict.fromkeys(around, f"K{level}")
        cells.update(dict.fromkeys(range(first, first + window), f"N{level}"))
        builder.row(cells, count=knobs.kill_rows(draws[4]))

    def _tunnel(self, builder: TrackBuilder, knobs: DifficultyKnobs, draws: Draws) -> None:
        """Ride through a tunnel, square or round."""
        builder.move_to(*self._shifted(builder, 0, max(2, knobs.lane_width(draws[2]))), knobs.shift_rows())
        builder.lane(count=1)
        builder.lane(suffix="T" if draws[3] < 0.5 else "A", count=knobs.section_rows(draws[5]))

    def _pad(self, builder: TrackBuilder, knobs: DifficultyKnobs, draws: Draws) -> None:
        """Hit a jump pad over a chasm, to land up to two levels higher."""
        builder.lane(count=2)
        builder.lane("J")
        change = min(TrackBuilder.TOP_LEVEL - builder.level, int(draws[3] * 3))
        self._jump_over(builder, knobs, draws, builder.reach.config.launch_velocity, change)

    def _slow(self, builder: TrackBuilder, knobs: DifficultyKnobs, draws: Draws) -> None:
        """Ride slow tiles, maybe up to a gap to jump at slow speed."""
        builder.lane("S", count=knobs.section_rows(draws[5]))
        if draws[3] < knobs.level:
            self._jump_over(builder, knobs, draws, builder.reach.config.jump_velocity, 0)

    def _fork(self, builder: TrackBuilder, knobs: DifficultyKnobs, draws: Draws) -> None:
        """Split the track into two routes side by side, each with its own obstacle, then join them again."""
        widths = [min(3, knobs.lane_width(draws[2])), min(3, knobs.lane_width(draws[4]))]
        separation = 1 if draws[5] < 0.5 else 2
        low = (Track.COLUMNS - sum(widths) - separation) // 2
        lanes = [(low, low + widths[0] - 1), (low + widths[0] + separation, low + sum(widths) + separation - 1)]
        builder.move_to(lanes[0][0], lanes[1][1], knobs.shift_rows())
        builder.lane(count=2)
        routes = [
            self._route(
                builder,
                knobs,
                self.ROUTES[int(draws[6 + side] * len(self.ROUTES))],
                lanes[side],
                random.Random(draws[8 + side]),
            )
            for side in (0, 1)
        ]
        length = max(len(route) for route in routes)
        plain = [dict.fromkeys(range(first, last + 1), f"N{builder.level}") for first, last in lanes]
        for index in range(length):
            cells: dict[int, str] = {}
            for side, route in enumerate(routes):
                cells.update(route[index] if index < len(route) else plain[side])
            builder.row(cells)
        builder.lane(count=2)

    def _route(
        self,
        builder: TrackBuilder,
        knobs: DifficultyKnobs,
        kind: str,
        lane: tuple[int, int],
        rng: random.Random,
    ) -> list[dict[int, str]]:
        """Return the rows of one route of a fork over the columns of ``lane``, an obstacle of ``kind`` on it.

        The route starts and ends with plain rows at the lane's height. It cannot see the other route, so its gaps
        are sized to the speed the ship surely has when the fork starts.
        """
        low, high = lane
        width, level = high - low + 1, builder.level

        def flat(letter: str = "N", height: int = level, suffix: str = "", columns: range | None = None) -> dict:
            return dict.fromkeys(columns or range(low, high + 1), f"{letter}{height}{suffix}")

        rows = [flat()]
        section = min(10, knobs.section_rows(rng.random()))
        longest = builder.reach.max_gap(builder.reach.config.jump_velocity, builder.speed, 0.0)
        match kind:
            case "kill" if width > 1:
                window = max(1, round((width - 1) * (1 - knobs.level)))
                first = low + int(rng.random() * (width - window + 1))
                strip = {**flat("K"), **flat(columns=range(first, first + window))}
                rows += [strip] * knobs.kill_rows(rng.random())
            case "kill" if longest >= 1:
                rows += [flat("K")]
            case "gap" if longest >= 1:
                rows += [flat(), *[{}] * min(longest, 1 + round(knobs.gap_share(rng.random()) * (longest - 1))), flat()]
            case "ice":
                rows += [flat("I")] * section
            case "push":
                rows += [flat("<" if rng.random() < 0.5 else ">")] * section
            case "narrow":
                column = low + int(rng.random() * width)
                rows += [flat(columns=range(column, column + 1))] * section
            case "tunnel" if width > 1:
                rows += [flat(suffix="T" if rng.random() < 0.5 else "A")] * section
            case "raised" if level < TrackBuilder.TOP_LEVEL:
                rows += [flat(suffix="f"), *[flat(height=level + 1)] * section, flat(suffix="b")]
            case _:
                rows += [flat()] * section
        return [*rows, flat()]
