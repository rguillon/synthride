# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

import json
import random
from collections.abc import Callable, Sequence

import pytest

from tests.ai.episode_result import EpisodeResult
from tests.ai.level_designer import LevelDesigner, Trial
from tests.ai.level_generator import LevelGenerationError, Obstacle


class FakeGenerator:
    """Makes "levels" that only carry how hard their obstacles add up to."""

    def __init__(self, *, broken: bool = False) -> None:
        self.broken = broken

    def obstacle(self, rng: random.Random, intensity: float) -> Obstacle:
        return Obstacle("gap", intensity, (rng.random(),))

    def build(self, slots: Sequence[Obstacle | None]) -> dict:
        if self.broken and any(slots):
            msg = "broken"
            raise LevelGenerationError(msg)
        return {"hardness": sum(0.1 + slot.intensity for slot in slots if slot is not None), "slots": len(slots)}


def player(failure: Callable[[float], float]) -> Callable[[str, Sequence[int]], list[EpisodeResult]]:
    """Return a play function failing each level ``failure(hardness)`` of the time, give or take a little noise."""

    def play(text: str, seeds: Sequence[int]) -> list[EpisodeResult]:
        hardness = json.loads(text)["hardness"]
        return [
            EpisodeResult(1.0, won=random.Random(seed).random() >= failure(hardness), seconds=10.0) for seed in seeds
        ]

    return play


def design(failure: Callable[[float], float], target: float, generator: FakeGenerator | None = None, **options):  # noqa: ANN003, ANN201
    designer = LevelDesigner(player(failure), rng=random.Random(1), report=lambda _: None, **options)
    return designer.design(generator or FakeGenerator(), target)  # ty: ignore[invalid-argument-type]


@pytest.mark.parametrize("target", [0.1, 0.3, 0.5, 0.8])
def test_adds_obstacles_until_failed_as_often_as_asked(target: float) -> None:
    result = design(lambda hardness: min(1.0, hardness / 8), target)
    assert result is not None
    assert result.on_target
    assert abs(result.validation.failure - target) <= 0.07
    assert result.obstacles > 0
    assert result.level["slots"] == 16


def test_a_target_the_straight_line_meets_needs_no_obstacle() -> None:
    result = design(lambda _: 0.0, 0.0)
    assert result is not None
    assert result.on_target
    assert result.obstacles == 0


def test_stops_when_nothing_can_get_harder() -> None:
    result = design(lambda hardness: min(0.2, hardness / 100), 0.9, length=2, steps=200)
    assert result is not None
    assert not result.on_target
    assert result.steps < 200


def test_skips_levels_that_break_the_rules() -> None:
    result = design(lambda hardness: hardness, 0.5, FakeGenerator(broken=True), steps=5)
    assert result is not None
    assert result.obstacles == 0
    assert not result.on_target


def test_never_keeps_a_level_the_network_never_won() -> None:
    assert design(lambda _: 1.0, 0.5) is None


def test_the_target_must_be_a_rate() -> None:
    with pytest.raises(ValueError, match="target failure rate"):
        design(lambda hardness: hardness, 1.0)


def test_pooled_trials_add_up() -> None:
    assert Trial(10, 4).pooled(Trial(20, 5)) == Trial(30, 9)
    assert Trial(10, 4).failure == pytest.approx(0.6)
