# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""The ``python -m tests.ai`` command line."""

from __future__ import annotations

import argparse
import os
import random
from pathlib import Path
from typing import TYPE_CHECKING

from synthride.core.level_catalog import LevelCatalog
from tests.ai.brain_store import BrainStore
from tests.ai.evolution import Evolution
from tests.ai.level_evaluator import LevelEvaluator
from tests.ai.trainer import Trainer

if TYPE_CHECKING:
    from collections.abc import Sequence

    from tests.ai.brain import Brain


class AiCli:
    """Command line entry point: ``learn`` to train the network, ``play`` to measure its win rate on each level."""

    DEFAULT_BRAIN = Path("data/brain.json")

    def parser(self) -> argparse.ArgumentParser:
        """Return the argument parser."""
        parser = argparse.ArgumentParser(prog="tests.ai", description="A neural network that plays SynthRide.")
        parser.add_argument("--brain", type=Path, default=self.DEFAULT_BRAIN, help="the network file")
        parser.add_argument("--workers", type=int, default=os.cpu_count() or 1, help="parallel processes")
        commands = parser.add_subparsers(dest="command", required=True)
        learn = commands.add_parser("learn", help="train the network, until interrupted by default")
        learn.add_argument("--generations", type=int, default=None, help="stop after this many generations")
        learn.add_argument("--population", type=int, default=128, help="networks per generation")
        learn.add_argument("--elites", type=int, default=8, help="best networks kept in each generation")
        learn.add_argument("--sigma", type=float, default=0.02, help="mutation strength")
        learn.add_argument("--attempts", type=int, default=4, help="attempts per network and level each generation")
        learn.add_argument("--levels", type=int, nargs="+", default=None, help="train only on these level numbers")
        play = commands.add_parser("play", help="show the network's win rate on each level")
        play.add_argument("--attempts", type=int, default=20, help="attempts per level")
        return parser

    def run(self, argv: Sequence[str] | None = None) -> int:
        """Run the command given in ``argv`` and return the exit code."""
        parser = self.parser()
        arguments = parser.parse_args(argv)
        store = BrainStore(arguments.brain)
        if arguments.command == "learn":
            evolution = Evolution(arguments.population, arguments.elites, arguments.sigma, random.Random())
            levels = None
            if arguments.levels is not None:
                count = len(LevelCatalog().file_names())
                if not all(1 <= number <= count for number in arguments.levels):
                    parser.error(f"level numbers go from 1 to {count}")
                levels = [number - 1 for number in arguments.levels]
            return self.learn(
                store, evolution, arguments.workers, arguments.generations, levels=levels, attempts=arguments.attempts
            )
        return self.play(store, arguments.workers, arguments.attempts)

    @staticmethod
    def learn(  # noqa: PLR0913
        store: BrainStore,
        evolution: Evolution,
        workers: int,
        generations: int | None,
        *,
        levels: Sequence[int] | None = None,
        attempts: int = 4,
    ) -> int:
        """Train the network in ``store`` on the levels at ``levels`` (all by default), ``attempts`` times each.

        Training goes on until interrupted unless ``generations`` is given.
        """
        print(f"Learning with {workers} workers, saving to {store.path} (Ctrl+C to stop)")  # noqa: T201
        try:
            with LevelEvaluator(workers) as evaluator:
                Trainer(store, evaluator, evolution, levels=levels, attempts=attempts).run(generations)
        except KeyboardInterrupt:
            print("Stopped.")  # noqa: T201
        return 0

    @staticmethod
    def play(store: BrainStore, workers: int, attempts: int) -> int:
        """Play every level ``attempts`` times with the stored network and print the win rate of each level."""
        brain = store.load()
        if brain is None:
            print(f"No network in {store.path}: run 'make learn' first.")  # noqa: T201
            return 1
        names = [level.name for level in LevelCatalog().load_all()]
        with LevelEvaluator(workers) as evaluator:
            results = evaluator.play(
                (brain.network, level, seed) for level in range(len(names)) for seed in range(attempts)
            )
        print(AiCli.report(brain, names, [results[i : i + attempts] for i in range(0, len(results), attempts)]))  # noqa: T201
        return 0

    @staticmethod
    def report(brain: Brain, names: Sequence[str], results: Sequence[Sequence]) -> str:
        """Return the table of win rates and mean progress by level."""
        lines = [
            f"Network from generation {brain.generation} (fitness {brain.fitness:.2f})",
            "",
            f"{'#':>3}  {'level':<20} {'win rate':>9} {'progress':>9}",
        ]
        total_wins = 0
        for number, (name, attempts) in enumerate(zip(names, results, strict=True), start=1):
            wins = sum(result.won for result in attempts)
            total_wins += wins
            progress = sum(result.progress for result in attempts) / len(attempts)
            lines.append(f"{number:>3}  {name:<20} {wins / len(attempts):>9.0%} {progress:>9.0%}")
        played = sum(len(attempts) for attempts in results)
        lines += ["", f"{'':>3}  {'overall':<20} {total_wins / played:>9.1%}"]
        return "\n".join(lines)


def main() -> int:
    """Run the command line with the process arguments."""
    return AiCli().run()
