# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""Plays many episodes, in parallel worker processes."""

from __future__ import annotations

import multiprocessing
import signal
from typing import TYPE_CHECKING, Any

from synthride.core.level_catalog import LevelCatalog
from tests.ai.episode_runner import EpisodeRunner
from tests.ai.neural_network import NeuralNetwork
from tests.ai.pilot import Pilot

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence
    from types import TracebackType

    from tests.ai.episode_result import EpisodeResult

_runner: EpisodeRunner | None = None


def _load_levels() -> None:
    """Load the levels once per process."""
    global _runner  # noqa: PLW0603
    _runner = EpisodeRunner(LevelCatalog().load_all())


def _start_worker() -> None:
    """Load the levels in a worker process, leaving Ctrl+C to the parent process."""
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    _load_levels()


def _play(task: tuple[tuple[int, ...], list[float], int, int]) -> EpisodeResult:
    layer_sizes, weights, level_index, seed = task
    assert _runner is not None
    return _runner.run(Pilot(NeuralNetwork(layer_sizes, weights)), level_index, seed)


class LevelEvaluator:
    """Plays episodes of the bundled levels, spread over ``workers`` processes (in this process if 1).

    Use it as a context manager so the worker processes are shut down afterwards.
    """

    def __init__(self, workers: int = 1) -> None:
        """Play on ``workers`` processes."""
        self.level_count = len(LevelCatalog().file_names())
        self._workers = workers
        self._pool: Any = None

    def __enter__(self) -> LevelEvaluator:  # noqa: PYI034
        """Start the worker processes."""
        if self._workers > 1:
            self._pool = multiprocessing.get_context("spawn").Pool(self._workers, initializer=_start_worker)
        else:
            _load_levels()
        return self

    def __exit__(
        self, exc_type: type[BaseException] | None, exc: BaseException | None, traceback: TracebackType | None
    ) -> None:
        """Stop the worker processes."""
        if self._pool is not None:
            self._pool.terminate()
            self._pool.join()
            self._pool = None

    def play(self, tasks: Iterable[tuple[NeuralNetwork, int, int]]) -> list[EpisodeResult]:
        """Play every ``(network, level_index, seed)`` task and return the results in the same order."""
        work = [(network.layer_sizes, network.weights, level_index, seed) for network, level_index, seed in tasks]
        if self._pool is None:
            return [_play(task) for task in work]
        return self._pool.map(_play, work, chunksize=4)

    def score(
        self, networks: Sequence[NeuralNetwork], seeds: Sequence[int], levels: Sequence[int] | None = None
    ) -> list[list[EpisodeResult]]:
        """Play the levels at ``levels`` (all by default) once per seed of ``seeds`` with each network.

        Every network plays the same attempts. Return the results by network, each list running level by level and,
        within a level, seed by seed.
        """
        levels = range(self.level_count) if levels is None else levels
        runs = len(levels) * len(seeds)
        results = self.play((network, level, seed) for network in networks for level in levels for seed in seeds)
        return [results[index : index + runs] for index in range(0, len(results), runs)]
