# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""The learning loop."""

from __future__ import annotations

import random
import time
from typing import TYPE_CHECKING, ClassVar

from synthride.ai.brain import Brain
from synthride.ai.pilot import Pilot
from synthride.ai.ship_observer import ShipObserver

if TYPE_CHECKING:
    from collections.abc import Callable

    from synthride.ai.brain_store import BrainStore
    from synthride.ai.evolution import Evolution
    from synthride.ai.level_evaluator import LevelEvaluator


class Trainer:
    """Evolves networks generation after generation, saving the best one to the store after each generation.

    Every generation plays all the levels with a fresh seed, the same for every network, so networks are
    compared fairly within a generation but must cope with changing conditions across generations.
    """

    LAYER_SIZES: ClassVar[tuple[int, ...]] = (ShipObserver.SIZE, 16, Pilot.OUTPUTS)

    def __init__(
        self,
        store: BrainStore,
        evaluator: LevelEvaluator,
        evolution: Evolution,
        rng: random.Random | None = None,
        report: Callable[[str], None] = print,
    ) -> None:
        """Train with ``evaluator`` and ``evolution``, keeping the best network in ``store``."""
        self._store = store
        self._evaluator = evaluator
        self._evolution = evolution
        self._rng = rng or random.Random()  # noqa: S311
        self._report = report

    def run(self, generations: int | None = None) -> Brain | None:
        """Train for ``generations`` generations, or forever if None, and return the last brain saved, if any."""
        brain = self._store.load()
        if brain is None:
            population = self._evolution.seed(self.LAYER_SIZES)
            generation = 0
            self._report(f"Starting from scratch: {len(population)} random networks of {self.LAYER_SIZES}")
        else:
            population = self._evolution.seed(brain.network.layer_sizes, brain.network)
            generation = brain.generation
            self._report(f"Resuming from generation {generation} (fitness {brain.fitness:.2f})")
        last = generation + generations if generations is not None else None
        while last is None or generation < last:
            generation += 1
            started = time.perf_counter()
            results = self._evaluator.score(population, self._rng.randrange(2**31))
            fitness = [sum(result.score for result in by_level) for by_level in results]
            best = max(range(len(population)), key=fitness.__getitem__)
            brain = Brain(population[best], generation, fitness[best])
            self._store.save(brain)
            wins = sum(result.won for result in results[best])
            self._report(
                f"generation {generation:5d}  best {fitness[best]:7.2f}  mean {sum(fitness) / len(fitness):7.2f}  "
                f"levels won {wins:2d}/{len(results[best])}  ({time.perf_counter() - started:.1f}s)"
            )
            population = self._evolution.next_generation(population, fitness)
        return brain
