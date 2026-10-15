# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

import signal

from synthride.ai import level_evaluator
from synthride.ai.level_evaluator import LevelEvaluator
from synthride.core.level_catalog import LevelCatalog
from tests.ai.networks import constant_network

LEVEL_COUNT = len(LevelCatalog().file_names())


def test_scores_every_level_for_every_network() -> None:
    networks = [constant_network(throttle=2), constant_network(throttle=-2)]
    with LevelEvaluator() as evaluator:
        results = evaluator.score(networks, seed=1)
    assert [len(by_level) for by_level in results] == [LEVEL_COUNT, LEVEL_COUNT]
    assert sum(result.progress for result in results[0]) > sum(result.progress for result in results[1])


def test_scores_only_the_chosen_levels() -> None:
    with LevelEvaluator() as evaluator:
        results = evaluator.score([constant_network(throttle=2)] * 2, seed=1, levels=[0, 2])
        expected = evaluator.play([(constant_network(throttle=2), 2, 1)])
    assert [len(by_level) for by_level in results] == [2, 2]
    assert results[0][1] == expected[0]


def test_worker_processes_give_the_same_results() -> None:
    tasks = [(constant_network(throttle=2, steering=level - 1), level, 5) for level in range(3)]
    with LevelEvaluator() as evaluator:
        expected = evaluator.play(tasks)
    with LevelEvaluator(workers=2) as evaluator:
        assert evaluator.play(tasks) == expected


def test_workers_leave_ctrl_c_to_the_parent() -> None:
    previous = signal.getsignal(signal.SIGINT)
    try:
        level_evaluator._start_worker()  # noqa: SLF001
        assert signal.getsignal(signal.SIGINT) is signal.SIG_IGN
    finally:
        signal.signal(signal.SIGINT, previous)
