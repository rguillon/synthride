# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

import random
from pathlib import Path

from synthride.ai.brain_store import BrainStore
from synthride.ai.evolution import Evolution
from synthride.ai.level_evaluator import LevelEvaluator
from synthride.ai.trainer import Trainer


def train(store: BrainStore, generations: int, messages: list[str]) -> None:
    with LevelEvaluator() as evaluator:
        evolution = Evolution(3, 1, 0.05, random.Random(1))
        Trainer(store, evaluator, evolution, rng=random.Random(2), report=messages.append).run(generations)


def test_trains_from_scratch_then_resumes(tmp_path: Path) -> None:
    store, messages = BrainStore(tmp_path / "brain.json"), []
    train(store, 2, messages)
    brain = store.load()
    assert brain is not None
    assert brain.generation == 2
    assert brain.network.layer_sizes == Trainer.LAYER_SIZES
    assert messages[0].startswith("Starting from scratch")
    assert "generation     2" in messages[-1]
    train(store, 1, messages)
    assert messages[-2].startswith("Resuming from generation 2")
    brain = store.load()
    assert brain is not None
    assert brain.generation == 3


def test_trains_on_chosen_levels(tmp_path: Path) -> None:
    messages: list[str] = []
    with LevelEvaluator() as evaluator:
        evolution = Evolution(3, 1, 0.05, random.Random(1))
        store = BrainStore(tmp_path / "brain.json")
        trainer = Trainer(store, evaluator, evolution, rng=random.Random(2), report=messages.append, levels=[0])
        trainer.run(1)
    assert "levels won  0/1" in messages[-1] or "levels won  1/1" in messages[-1]
    assert "% of 3 runs" in messages[-1]


def test_does_nothing_without_generations(tmp_path: Path) -> None:
    with LevelEvaluator() as evaluator:
        trainer = Trainer(BrainStore(tmp_path / "brain.json"), evaluator, Evolution(3, 1, 0.05, random.Random(1)))
        assert trainer.run(0) is None
