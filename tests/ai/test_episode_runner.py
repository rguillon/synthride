# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

import pytest

from synthride.ai.episode_runner import EpisodeRunner
from synthride.ai.pilot import Pilot
from tests.ai.networks import constant_network
from tests.level_factory import make_level

FLAT = "N1 N1 N1 N1 N1 N1 N1 N1"
LEVELS = [
    make_level(*[FLAT] * 6, "F1 F1 F1 F1 F1 F1 F1 F1"),
    make_level(*[FLAT] * 6, *[".. .. .. .. .. .. .. .."] * 4, FLAT),
]


def test_wins_by_reaching_the_finish() -> None:
    result = EpisodeRunner(LEVELS).run(Pilot(constant_network(throttle=2)), 0, seed=1)
    assert result.won
    assert result.progress == 1.0
    assert 0 < result.seconds < 5


def test_loses_by_falling() -> None:
    result = EpisodeRunner(LEVELS).run(Pilot(constant_network(throttle=2)), 1, seed=1)
    assert not result.won
    assert 0.4 < result.progress < 0.9


def test_gives_up_when_the_ship_stalls() -> None:
    result = EpisodeRunner(LEVELS).run(Pilot(constant_network(throttle=-2)), 0, seed=1)
    assert not result.won
    assert result.progress < 0.1
    assert result.seconds == pytest.approx(EpisodeRunner.STALL_SECONDS, abs=0.1)


def test_seeds_give_reproducible_attempts() -> None:
    runner, pilot = EpisodeRunner(LEVELS), Pilot(constant_network(throttle=2, steering=2))
    assert runner.run(pilot, 1, seed=3) == runner.run(pilot, 1, seed=3)
    assert runner.run(pilot, 1, seed=3) != runner.run(pilot, 1, seed=4)
