# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""Plays many episodes, in parallel worker processes."""

from __future__ import annotations

import multiprocessing
import signal
from typing import TYPE_CHECKING, Any

from synthride.core.level_catalog import LevelCatalog
from synthride.core.level_parser import LevelParser
from tests.ai.episode_runner import EpisodeRunner
from tests.ai.neural_network import NeuralNetwork
from tests.ai.pilot import Pilot
from tests.ai.ship_observer import ShipObserver

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence
    from types import TracebackType

    import numpy as np

    from tests.ai.episode_result import EpisodeResult

_runner: EpisodeRunner | None = None
# Runners of the levels given as text, the most recent last: the generator plays one level many times, then moves on.
_text_runners: dict[str, EpisodeRunner] = {}
_TEXT_RUNNERS = 2


def _load_levels() -> None:
    """Load the levels once per process."""
    global _runner  # noqa: PLW0603
    _runner = EpisodeRunner(LevelCatalog().load_all())


def _start_worker() -> None:
    """Load the levels in a worker process, leaving Ctrl+C to the parent process."""
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    _load_levels()


def _play(task: tuple[tuple[int, ...], np.ndarray, int, int]) -> EpisodeResult:
    layer_sizes, weights, level_index, seed = task
    assert _runner is not None
    return _runner.run(Pilot(NeuralNetwork(layer_sizes, weights)), level_index, seed)


def _text_runner(text: str) -> EpisodeRunner:
    """Return the runner of the level file ``text``, parsed once per process while it is still played."""
    runner = _text_runners.pop(text, None)
    if runner is None:
        if len(_text_runners) >= _TEXT_RUNNERS:
            oldest = next(iter(_text_runners))
            for level in _text_runners.pop(oldest).levels:
                ShipObserver.forget(level.track)
        runner = EpisodeRunner([LevelParser().parse(text)])
    _text_runners[text] = runner
    return runner


def _play_text(task: tuple[tuple[int, ...], np.ndarray, str, int]) -> EpisodeResult:
    layer_sizes, weights, text, seed = task
    return _text_runner(text).run(Pilot(NeuralNetwork(layer_sizes, weights)), 0, seed)


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

    def play_level(self, network: NeuralNetwork, text: str, seeds: Sequence[int]) -> list[EpisodeResult]:
        """Play the level file ``text`` once per seed of ``seeds`` with ``network`` and return the results in order."""
        work = [(network.layer_sizes, network.weights, text, seed) for seed in seeds]
        if self._pool is None:
            return [_play_text(task) for task in work]
        return self._pool.map(_play_text, work, chunksize=max(1, len(work) // (4 * self._workers)))

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
