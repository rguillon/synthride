# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""The ``python -m synthride.ai`` command line."""

from __future__ import annotations

import argparse
import os
import random
from pathlib import Path
from typing import TYPE_CHECKING

from synthride.ai.brain_store import BrainStore
from synthride.ai.evolution import Evolution
from synthride.ai.level_evaluator import LevelEvaluator
from synthride.ai.trainer import Trainer
from synthride.core.level_catalog import LevelCatalog

if TYPE_CHECKING:
    from collections.abc import Sequence

    from synthride.ai.brain import Brain


class AiCli:
    """Command line entry point: ``learn`` to train the network, ``play`` to measure its win rate on each level."""

    DEFAULT_BRAIN = Path("data/brain.json")

    def parser(self) -> argparse.ArgumentParser:
        """Return the argument parser."""
        parser = argparse.ArgumentParser(prog="synthride.ai", description="A neural network that plays SynthRide.")
        parser.add_argument("--brain", type=Path, default=self.DEFAULT_BRAIN, help="the network file")
        parser.add_argument("--workers", type=int, default=os.cpu_count() or 1, help="parallel processes")
        commands = parser.add_subparsers(dest="command", required=True)
        learn = commands.add_parser("learn", help="train the network, until interrupted by default")
        learn.add_argument("--generations", type=int, default=None, help="stop after this many generations")
        learn.add_argument("--population", type=int, default=64, help="networks per generation")
        learn.add_argument("--elites", type=int, default=8, help="best networks kept in each generation")
        learn.add_argument("--sigma", type=float, default=0.05, help="mutation strength")
        play = commands.add_parser("play", help="show the network's win rate on each level")
        play.add_argument("--attempts", type=int, default=20, help="attempts per level")
        return parser

    def run(self, argv: Sequence[str] | None = None) -> int:
        """Run the command given in ``argv`` and return the exit code."""
        arguments = self.parser().parse_args(argv)
        store = BrainStore(arguments.brain)
        if arguments.command == "learn":
            evolution = Evolution(arguments.population, arguments.elites, arguments.sigma, random.Random())  # noqa: S311
            return self.learn(store, evolution, arguments.workers, arguments.generations)
        return self.play(store, arguments.workers, arguments.attempts)

    @staticmethod
    def learn(store: BrainStore, evolution: Evolution, workers: int, generations: int | None) -> int:
        """Train the network in ``store``, until interrupted unless ``generations`` is given."""
        print(f"Learning with {workers} workers, saving to {store.path} (Ctrl+C to stop)")  # noqa: T201
        try:
            with LevelEvaluator(workers) as evaluator:
                Trainer(store, evaluator, evolution).run(generations)
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
