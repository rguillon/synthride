# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

import random
from pathlib import Path

import pytest

from synthride.ai.brain import Brain
from synthride.ai.brain_store import BrainStore
from synthride.ai.neural_network import NeuralNetwork


def test_loads_nothing_before_the_first_save(tmp_path: Path) -> None:
    assert BrainStore(tmp_path / "brain.json").load() is None


def test_saves_and_loads_a_brain(tmp_path: Path) -> None:
    store = BrainStore(tmp_path / "data" / "brain.json")
    store.save(Brain(NeuralNetwork.random((3, 2), random.Random(1)), generation=7, fitness=12.345678))
    store.save(Brain(NeuralNetwork.random((3, 2), random.Random(2)), generation=8, fitness=13.0))
    brain = store.load()
    assert brain is not None
    assert (brain.generation, brain.fitness) == (8, 13.0)
    assert brain.network.weights == pytest.approx(NeuralNetwork.random((3, 2), random.Random(2)).weights, abs=1e-6)
    assert [path.name for path in (tmp_path / "data").iterdir()] == ["brain.json"]
