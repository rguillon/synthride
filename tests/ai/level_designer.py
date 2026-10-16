# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""Grows a level from a straight line, adding obstacles until the network fails it as often as asked."""

from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from tests.ai.level_generator import LevelGenerationError, Obstacle

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from tests.ai.episode_result import EpisodeResult
    from tests.ai.level_generator import LevelGenerator

    Play = Callable[[str, Sequence[int]], Sequence[EpisodeResult]]
    Candidate = tuple["Trial", dict[str, Any], list[Obstacle | None]]


@dataclass(frozen=True)
class Trial:
    """One measure: how many of the network's attempts at a level it won."""

    attempts: int
    wins: int

    @property
    def failure(self) -> float:
        """The share of the attempts that failed."""
        return 1.0 - self.wins / self.attempts

    def pooled(self, other: Trial) -> Trial:
        """Return this measure and ``other`` counted together."""
        return Trial(self.attempts + other.attempts, self.wins + other.wins)


@dataclass(frozen=True)
class DesignResult:
    """The level designed, its obstacles, its failure rate measured afresh, and whether that is on target."""

    level: dict[str, Any]
    slots: list[Obstacle | None]
    validation: Trial
    on_target: bool
    steps: int = 0
    history: list[Trial] = field(default_factory=list)

    @property
    def obstacles(self) -> int:
        """How many slots hold an obstacle."""
        return sum(slot is not None for slot in self.slots)


class LevelDesigner:
    """Starts from a straight line of ``length`` plain slots and makes it harder until it hits the target.

    Each step plays the level ``attempts`` times. While the network fails it less than ``target``, the designer
    tries a harder level: an obstacle in a plain slot, or a harder version of an obstacle already there. The change
    is kept when the level is still too easy. When it overshoots the target, it is undone and the next changes are
    smaller. A level within ``tolerance`` of the target is played ``attempts`` more times with fresh seeds: the design
    is done if that measure lands within ``tolerance`` too, so the difficulty reported was not tuned on the attempts
    that measure it. Only levels the network won at least once count: that proves them finishable.
    """

    FIRST_STEP = 0.6
    SMALLEST_STEP = 0.1
    STEP_DECAY = 0.6
    NEW_OBSTACLE_ODDS = 0.7

    def __init__(  # noqa: PLR0913
        self,
        play: Play,
        *,
        rng: random.Random | None = None,
        report: Callable[[str], None] = print,
        length: int = 16,
        attempts: int = 80,
        tolerance: float = 0.07,
        steps: int = 60,
    ) -> None:
        """Measure levels with ``play``, which plays a level file once per seed and returns the results."""
        self._play = play
        self._rng = rng or random.Random()
        self._report = report
        self._length = length
        self._attempts = attempts
        self._tolerance = tolerance
        self._steps = steps

    def design(self, generator: LevelGenerator, target: float) -> DesignResult | None:
        """Return the level of ``generator`` failed closest to ``target`` of the time, None if none was ever won."""
        if not 0.0 <= target < 1.0:
            msg = f"the target failure rate goes from 0 up to 1 excluded, got {target}"
            raise ValueError(msg)
        slots: list[Obstacle | None] = [None] * self._length
        level = generator.build(slots)
        trial = self._measure(level)
        history = [trial]
        self._report(f"  straight line: failed {trial.failure:4.0%}")
        best = self._closer(None, (trial, level, list(slots)), target)
        size = self.FIRST_STEP
        step = 0
        while step < self._steps:
            step += 1
            if self._on_target(trial, target):
                validation = self._measure(level)
                self._report(f"    validation: failed {validation.failure:4.0%} of {validation.attempts} fresh ones")
                if self._on_target(validation, target):
                    return DesignResult(level, list(slots), validation, on_target=True, steps=step, history=history)
                trial = trial.pooled(validation)
            if trial.failure > target:
                break
            candidate = self._harder(generator, slots, size)
            if candidate is None:
                break
            candidate_level = self._build(generator, candidate, step)
            if candidate_level is None:
                continue
            measured = self._measure(candidate_level)
            history.append(measured)
            obstacles = sum(slot is not None for slot in candidate)
            best = self._closer(best, (measured, candidate_level, list(candidate)), target)
            if measured.wins and measured.failure <= target + self._tolerance:
                slots, level, trial = candidate, candidate_level, measured
                self._report(f"  step {step}: {obstacles} obstacles, failed {measured.failure:4.0%}: kept")
            else:
                size = max(self.SMALLEST_STEP, size * self.STEP_DECAY)
                self._report(f"  step {step}: {obstacles} obstacles, failed {measured.failure:4.0%}: too hard, undone")
        if best is None:
            return None
        trial, level, slots = best
        validation = self._measure(level)
        return DesignResult(level, slots, validation, self._on_target(validation, target), step, history)

    def _closer(self, best: Candidate | None, candidate: Candidate, target: float) -> Candidate | None:
        """Return whichever of ``best`` and ``candidate`` was measured closer to ``target``, among levels won once."""
        if not candidate[0].wins or (
            best is not None and self._miss(best[0], target) <= self._miss(candidate[0], target)
        ):
            return best
        return candidate

    def _build(self, generator: LevelGenerator, slots: list[Obstacle | None], step: int) -> dict[str, Any] | None:
        """Return the level of ``slots``, None if it breaks the rules that make it finishable."""
        try:
            return generator.build(slots)
        except LevelGenerationError as error:
            self._report(f"  step {step}: skipped, {error}")
            return None

    def _on_target(self, trial: Trial, target: float) -> bool:
        """Return True if ``trial`` was won at least once and lands within the tolerance of ``target``."""
        return trial.wins > 0 and self._miss(trial, target) <= self._tolerance

    def _harder(
        self, generator: LevelGenerator, slots: Sequence[Obstacle | None], size: float
    ) -> list[Obstacle | None] | None:
        """Return ``slots`` with one change making them harder, by about ``size``, None if nothing can get harder."""
        rng = self._rng
        plain = [index for index, slot in enumerate(slots) if slot is None]
        raisable = [index for index, slot in enumerate(slots) if slot is not None and slot.intensity < 1.0]
        candidate = list(slots)
        if plain and (not raisable or rng.random() < self.NEW_OBSTACLE_ODDS):
            candidate[rng.choice(plain)] = generator.obstacle(rng, rng.uniform(0.0, size))
        elif raisable:
            index = rng.choice(raisable)
            obstacle = candidate[index]
            assert obstacle is not None
            candidate[index] = obstacle.harder(rng.uniform(self.SMALLEST_STEP, max(self.SMALLEST_STEP, size)))
        else:
            return None
        return candidate

    def _measure(self, level: dict[str, Any]) -> Trial:
        seeds = [self._rng.randrange(2**31) for _ in range(self._attempts)]
        results = self._play(json.dumps(level), seeds)
        return Trial(self._attempts, sum(result.won for result in results))

    @staticmethod
    def _miss(trial: Trial, target: float) -> float:
        return abs(trial.failure - target)
