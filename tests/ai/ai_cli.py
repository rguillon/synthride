# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""The ``python -m tests.ai`` command line."""

from __future__ import annotations

import argparse
import json
import os
import random
from pathlib import Path
from typing import TYPE_CHECKING

from synthride.core.level_catalog import LevelCatalog
from synthride.server.game_server import GameServer
from synthride.server.html_page_builder import HtmlPageBuilder
from synthride.server.server_cli import ServerCli
from tests.ai.ai_bundle_builder import AiBundleBuilder
from tests.ai.brain_store import BrainStore
from tests.ai.evolution import Evolution
from tests.ai.evolution_strategy import EvolutionStrategy
from tests.ai.level_designer import LevelDesigner
from tests.ai.level_evaluator import LevelEvaluator
from tests.ai.level_generator import LevelGenerator
from tests.ai.trainer import Trainer

if TYPE_CHECKING:
    from collections.abc import Sequence

    from tests.ai.brain import Brain
    from tests.ai.breeder import Breeder
    from tests.ai.level_designer import DesignResult


class AiCli:
    """Command line entry point: ``learn`` to train the network, ``play`` to measure its win rate on each level.

    ``serve`` serves the game in the browser with the network at the ship's controls, and ``generate`` generates
    levels the network fails as often as asked.
    """

    DEFAULT_BRAIN = Path("data/brain.json")
    DEFAULT_GENERATED = Path("data/generated")

    def parser(self) -> argparse.ArgumentParser:
        """Return the argument parser."""
        parser = argparse.ArgumentParser(prog="tests.ai", description="A neural network that plays SynthRide.")
        parser.add_argument("--brain", type=Path, default=self.DEFAULT_BRAIN, help="the network file")
        parser.add_argument("--workers", type=int, default=os.cpu_count() or 1, help="parallel processes")
        commands = parser.add_subparsers(dest="command", required=True)
        learn = commands.add_parser("learn", help="train the network, until interrupted by default")
        learn.add_argument("--generations", type=int, default=None, help="stop after this many generations")
        learn.add_argument(
            "--strategy",
            choices=("es", "ga"),
            default="es",
            help="es: evolution strategy (default), ga: genetic algorithm keeping elites",
        )
        learn.add_argument("--population", type=int, default=129, help="networks per generation (odd for es)")
        learn.add_argument("--elites", type=int, default=8, help="ga: best networks kept in each generation")
        learn.add_argument("--sigma", type=float, default=0.02, help="mutation strength")
        learn.add_argument("--learning-rate", type=float, default=0.01, help="es: step size of the centre")
        learn.add_argument("--attempts", type=int, default=4, help="attempts per network and level each generation")
        learn.add_argument("--levels", type=int, nargs="+", default=None, help="train only on these level numbers")
        play = commands.add_parser("play", help="show the network's win rate on each level")
        play.add_argument("--attempts", type=int, default=20, help="attempts per level")
        generate = commands.add_parser(
            "generate", help="generate finishable levels that the network fails a given percentage of the time"
        )
        generate.add_argument(
            "--difficulty", type=float, required=True, help="percentage of attempts the network should fail"
        )
        generate.add_argument("--count", type=int, default=1, help="levels to generate")
        generate.add_argument(
            "--tries",
            type=int,
            default=10,
            help="most seeds tried per level (designs missing the target are skipped)",
        )
        generate.add_argument("--seed", type=int, default=None, help="seed of the first level (random by default)")
        generate.add_argument(
            "--length", type=int, default=16, help="track length, in slots that may each take an obstacle"
        )
        generate.add_argument("--gravity", type=float, default=18.0, help="gravity of the levels")
        generate.add_argument("--tolerance", type=float, default=7.0, help="accepted miss, in percentage points")
        generate.add_argument("--attempts", type=int, default=80, help="attempts per measure")
        generate.add_argument("--steps", type=int, default=60, help="most changes tried per level")
        generate.add_argument("--out", type=Path, default=self.DEFAULT_GENERATED, help="directory to write to")
        serve = commands.add_parser("serve", help="serve the game in the browser, played by the network")
        serve.add_argument("--host", default="127.0.0.1")
        serve.add_argument("--port", type=int, default=8000)
        return parser

    def run(self, argv: Sequence[str] | None = None) -> int:
        """Run the command given in ``argv`` and return the exit code."""
        parser = self.parser()
        arguments = parser.parse_args(argv)
        store = BrainStore(arguments.brain)
        if arguments.command == "learn":
            evolution: Breeder
            if arguments.strategy == "es":
                evolution = EvolutionStrategy(
                    arguments.population, arguments.sigma, random.Random(), learning_rate=arguments.learning_rate
                )
            else:
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
        if arguments.command == "serve":
            return self.serve(store, arguments.host, arguments.port)
        if arguments.command == "generate":
            if not 0 <= arguments.difficulty < 100:
                parser.error("the difficulty goes from 0 up to 100 excluded")
            return self.generate(store, arguments.workers, arguments)
        return self.play(store, arguments.workers, arguments.attempts)

    @staticmethod
    def learn(  # noqa: PLR0913
        store: BrainStore,
        evolution: Breeder,
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
    def generate(store: BrainStore, workers: int, arguments: argparse.Namespace) -> int:
        """Generate ``arguments.count`` levels the stored network fails ``arguments.difficulty`` percent of the time.

        Each level grows from a straight line, obstacle by obstacle, until the network fails it as often as asked.
        Seeds are tried one after the other, ``arguments.tries`` per level at most: a design that misses the target is
        skipped. Each level is written to ``arguments.out``, named after its target difficulty and its seed, with a
        comment on how often the network failed it.
        """
        brain = store.load()
        if brain is None:
            print(f"No network in {store.path}: run 'make learn' first.")  # noqa: T201
            return 1
        target = arguments.difficulty / 100
        first = arguments.seed if arguments.seed is not None else random.randrange(10**6)
        arguments.out.mkdir(parents=True, exist_ok=True)
        written = 0
        with LevelEvaluator(workers) as evaluator:
            for seed in range(first, first + arguments.count * arguments.tries):
                if written == arguments.count:
                    break
                generator = LevelGenerator(seed, arguments.gravity)
                print(f"Level seed {seed}, {generator.name!r}, target failure {target:.0%}")  # noqa: T201
                designer = LevelDesigner(
                    lambda text, seeds: evaluator.play_level(brain.network, text, seeds),
                    rng=random.Random(seed),
                    length=arguments.length,
                    attempts=arguments.attempts,
                    tolerance=arguments.tolerance / 100,
                    steps=arguments.steps,
                )
                result = designer.design(generator, target)
                if result is None:
                    print("  skipped: the network never finished it")  # noqa: T201
                elif not result.on_target:
                    print(f"  skipped: failed {result.validation.failure:.0%} of fresh attempts, off target")  # noqa: T201
                else:
                    path = arguments.out / f"gen_d{arguments.difficulty:02.0f}_s{seed}.json"
                    AiCli.write_level(path, result, seed, target, brain)
                    print(f"  on target: failed {result.validation.failure:.0%} of fresh attempts, written to {path}")  # noqa: T201
                    written += 1
        print(f"{written} of {arguments.count} levels generated")  # noqa: T201
        return 0 if written == arguments.count else 1

    @staticmethod
    def write_level(path: Path, result: DesignResult, seed: int, target: float, brain: Brain) -> None:
        """Write the level of ``result`` to ``path``, with a first comment row on how it was made and measured."""
        validation = result.validation
        note = (
            f"# generated from seed {seed} with {result.obstacles} obstacles for {target:.0%} failure: brain of "
            f"generation {brain.generation} failed {validation.failure:.0%} of {validation.attempts} fresh attempts"
        )
        level = {**result.level, "track": [note, *result.level["track"]]}
        path.write_text(json.dumps(level, indent=2) + "\n", encoding="utf-8")

    @staticmethod
    def serve(store: BrainStore, host: str, port: int) -> int:
        """Serve the game on ``host:port``, the stored network steering the ship, until interrupted."""
        if not store.path.exists():
            print(f"No network in {store.path}: run 'make learn' first.")  # noqa: T201
            return 1
        page = HtmlPageBuilder(packages=("numpy",), entry="from tests.ai.ai_main import main; main()")
        bundle = AiBundleBuilder(store.path)
        return ServerCli(lambda host, port: GameServer(host, port, page, bundle)).serve(host, port)

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
