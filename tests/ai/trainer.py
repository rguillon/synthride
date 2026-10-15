# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""The learning loop."""

from __future__ import annotations

import random
import time
from typing import TYPE_CHECKING, ClassVar

from tests.ai.brain import Brain
from tests.ai.pilot import Pilot
from tests.ai.ship_observer import ShipObserver

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from tests.ai.brain_store import BrainStore
    from tests.ai.episode_result import EpisodeResult
    from tests.ai.evolution import Evolution
    from tests.ai.level_evaluator import LevelEvaluator


class Trainer:
    """Evolves networks generation after generation, saving the best one to the store after each generation.

    Every generation plays the training levels (all of them by default) ``attempts`` times with fresh seeds, the same
    for every network, so networks are compared fairly within a generation but must cope with changing conditions.
    A network's fitness is its total score over the levels, averaged over the attempts, so a network that wins
    reliably beats one that won by luck.
    """

    LAYER_SIZES: ClassVar[tuple[int, ...]] = (ShipObserver.SIZE, 16, Pilot.OUTPUTS)

    def __init__(  # noqa: PLR0913
        self,
        store: BrainStore,
        evaluator: LevelEvaluator,
        evolution: Evolution,
        *,
        rng: random.Random | None = None,
        report: Callable[[str], None] = print,
        levels: Sequence[int] | None = None,
        attempts: int = 4,
    ) -> None:
        """Train with ``evaluator`` and ``evolution`` on the levels at ``levels``, keeping the best one in ``store``.

        Each network plays each level ``attempts`` times per generation.
        """
        self._store = store
        self._evaluator = evaluator
        self._evolution = evolution
        self._rng = rng or random.Random()
        self._report = report
        self._levels = levels
        self._attempts = attempts

    def run(self, generations: int | None = None) -> Brain | None:
        """Train for ``generations`` generations, or forever if None, and return the last brain saved, if any."""
        brain = self._store.load()
        if brain is None:
            population = self._evolution.seed(self.LAYER_SIZES)
            generation = 0
            self._report(f"Starting from scratch: {len(population)} random networks of {self.LAYER_SIZES}")
        elif brain.network.layer_sizes != self.LAYER_SIZES:
            msg = (
                f"{self._store.path} holds a network of {brain.network.layer_sizes}, but the trainer now builds "
                f"{self.LAYER_SIZES}: move that file away to start afresh"
            )
            raise ValueError(msg)
        else:
            population = self._evolution.seed(brain.network.layer_sizes, brain.network)
            generation = brain.generation
            self._report(f"Resuming from generation {generation} (fitness {brain.fitness:.2f})")
        last = generation + generations if generations is not None else None
        while last is None or generation < last:
            generation += 1
            started = time.perf_counter()
            seeds = [self._rng.randrange(2**31) for _ in range(self._attempts)]
            results = self._evaluator.score(population, seeds, self._levels)
            fitness = [sum(result.score for result in runs) / self._attempts for runs in results]
            best = max(range(len(population)), key=fitness.__getitem__)
            brain = Brain(population[best], generation, fitness[best])
            self._store.save(brain)
            self._report(
                f"generation {generation:5d}  best {fitness[best]:7.2f}  mean {sum(fitness) / len(fitness):7.2f}  "
                f"best network wins {self._win_rate(results[best : best + 1])}  "
                f"all networks win {self._win_rate(results)}  ({time.perf_counter() - started:.1f}s)"
            )
            population = self._evolution.next_generation(population, fitness)
        return brain

    @staticmethod
    def _win_rate(results: Sequence[Sequence[EpisodeResult]]) -> str:
        runs = [result for by_network in results for result in by_network]
        return f"{sum(result.won for result in runs) / len(runs):6.1%} of {len(runs):4d} runs"
