# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

import json
import random

import pytest

from synthride.core.level_parser import LevelParser
from tests.ai.difficulty_knobs import DifficultyKnobs
from tests.ai.level_generator import LevelGenerator, Obstacle


def lines(document: dict) -> list[str]:
    return [line for count, line in document["track"] for _ in range(count)]


def runs_of_tiles(line: str) -> int:
    cells = ["." if cell == ".." else "#" for cell in line.split()]
    return len([run for run in "".join(cells).split(".") if run])


def random_slots(seed: int, intensity: float, length: int = 16) -> list[Obstacle | None]:
    rng = random.Random(seed)
    generator = LevelGenerator(seed)
    return [generator.obstacle(rng, intensity) if rng.random() < 0.8 else None for _ in range(length)]


def test_plain_slots_make_a_straight_line() -> None:
    document = LevelGenerator(1).build([None] * 5)
    assert set(lines(document)[:-4]) == {".. .. N1 N1 N1 N1 .. .."}
    assert set(lines(document)[-4:]) == {".. .. F1 F1 F1 F1 .. .."}
    assert LevelGenerator(1).check(document) == []


def test_obstacles_fill_their_slots() -> None:
    generator = LevelGenerator(1)
    obstacle = Obstacle("gap", 0.5, tuple(0.5 for _ in range(LevelGenerator.DRAWS)))
    plain = generator.build([None] * 5)
    with_gap = generator.build([None, None, obstacle, None, None])
    assert len(lines(with_gap)) > len(lines(plain))
    assert ".. .. .. .. .. .. .. .." in lines(with_gap)


def test_the_same_slots_give_the_same_level() -> None:
    assert LevelGenerator(3).build(random_slots(3, 0.4)) == LevelGenerator(3).build(random_slots(3, 0.4))


@pytest.mark.parametrize("seed", range(40))
def test_every_level_is_finishable(seed: int) -> None:
    generator = LevelGenerator(seed)
    for intensity in (0.0, 0.5, 1.0):
        assert generator.check(generator.build(random_slots(seed, intensity))) == []


def test_mixed_intensities_are_finishable() -> None:
    rng = random.Random(7)
    for seed in range(20):
        generator = LevelGenerator(seed)
        slots = [generator.obstacle(rng, rng.random()) if rng.random() < 0.7 else None for _ in range(20)]
        assert generator.check(generator.build(slots)) == []


def test_levels_parse_with_their_settings() -> None:
    document = LevelGenerator(5, gravity=21.0).build(random_slots(5, 0.5))
    level = LevelParser().parse(json.dumps(document))
    assert level.name == LevelGenerator(5).name
    assert level.gravity == 21.0
    assert level.oxygen_seconds == document["oxygen"]


def test_generated_level_names_start_with_dev() -> None:
    assert LevelGenerator(5).name.startswith("dev - ")


def test_harder_obstacles_give_narrower_levels_and_less_oxygen() -> None:
    def mean(intensity: float, measure) -> float:  # noqa: ANN001
        return sum(measure(LevelGenerator(seed).build(random_slots(seed, intensity))) for seed in range(20)) / 20

    def tiles_per_row(document: dict) -> float:
        rows = lines(document)
        return sum(len(line.replace("..", "").split()) for line in rows) / len(rows)

    def oxygen_per_row(document: dict) -> float:
        return document["oxygen"] / len(lines(document))

    widths = [mean(intensity, tiles_per_row) for intensity in (0.0, 0.5, 1.0)]
    oxygen = [mean(intensity, oxygen_per_row) for intensity in (0.0, 0.5, 1.0)]
    assert widths == sorted(widths, reverse=True)
    assert oxygen == sorted(oxygen, reverse=True)


def test_forks_split_the_track_into_routes() -> None:
    generator = LevelGenerator(1)
    fork = Obstacle("fork", 0.5, tuple(random.Random(2).random() for _ in range(LevelGenerator.DRAWS)))
    assert any(runs_of_tiles(line) == 2 for line in lines(generator.build([fork])))


def test_harder_raises_the_intensity_up_to_1() -> None:
    obstacle = Obstacle("gap", 0.5, ())
    assert obstacle.harder(0.2).intensity == pytest.approx(0.7)
    assert obstacle.harder(0.9).intensity == 1.0


def test_the_intensity_must_lie_between_0_and_1() -> None:
    with pytest.raises(ValueError, match="from 0 to 1"):
        LevelGenerator(1).build([Obstacle("gap", 1.5, tuple([0.5] * LevelGenerator.DRAWS))])


def test_knobs_get_harder_with_the_knob() -> None:
    easy, hard = DifficultyKnobs(0.0), DifficultyKnobs(1.0)
    for draw in (0.0, 0.3, 0.7, 0.99):
        assert hard.lane_width(draw) <= easy.lane_width(draw)
        assert hard.gap_share(draw) >= easy.gap_share(draw)
        assert hard.rest_rows(draw) <= easy.rest_rows(draw)
    assert hard.oxygen_slack < easy.oxygen_slack
    assert hard.shift_rows() < easy.shift_rows()
