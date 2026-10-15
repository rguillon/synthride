# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

import runpy
from pathlib import Path

import pytest

from synthride.ai import ai_cli
from synthride.ai.ai_cli import AiCli
from synthride.ai.brain import Brain
from synthride.ai.brain_store import BrainStore
from synthride.ai.episode_result import EpisodeResult
from synthride.ai.trainer import Trainer
from synthride.core.level_catalog import LevelCatalog
from tests.ai.networks import constant_network


def test_learn_then_play(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    brain = str(tmp_path / "brain.json")
    options = ["--brain", brain, "--workers", "1"]
    assert AiCli().run([*options, "learn", "--generations", "1", "--population", "2", "--elites", "1"]) == 0
    assert "generation     1" in capsys.readouterr().out
    assert AiCli().run([*options, "play", "--attempts", "1"]) == 0
    out = capsys.readouterr().out
    assert "generation 1" in out
    assert LevelCatalog().load_all()[0].name in out
    assert "overall" in out


def test_learn_on_chosen_levels(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    options = ["--brain", str(tmp_path / "brain.json"), "--workers", "1", "learn", "--generations", "1"]
    assert AiCli().run([*options, "--population", "2", "--elites", "1", "--attempts", "1", "--levels", "1", "3"]) == 0
    assert "best network wins   0.0% of    2 runs  all networks win   0.0% of    4 runs" in capsys.readouterr().out


@pytest.mark.parametrize("number", ["0", "99"])
def test_learn_rejects_unknown_levels(tmp_path: Path, number: str) -> None:
    with pytest.raises(SystemExit):
        AiCli().run(["--brain", str(tmp_path / "brain.json"), "learn", "--levels", number])


def test_play_needs_a_brain(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert AiCli().run(["--brain", str(tmp_path / "none.json"), "play"]) == 1
    assert "make learn" in capsys.readouterr().out


def test_learn_stops_on_ctrl_c(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def interrupt(*_: object) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr(Trainer, "run", interrupt)
    assert AiCli().run(["--brain", str(tmp_path / "brain.json"), "--workers", "1", "learn"]) == 0
    assert "Stopped." in capsys.readouterr().out


def test_report_shows_win_rates() -> None:
    brain = Brain(constant_network(), generation=4, fitness=9.5)
    won, lost = EpisodeResult(1.0, won=True, seconds=20), EpisodeResult(0.5, won=False, seconds=5)
    report = AiCli.report(brain, ["One", "Two"], [[won, lost], [won, won]])
    assert "generation 4 (fitness 9.50)" in report
    assert "  1  One                        50%       75%" in report
    assert "  2  Two                       100%      100%" in report
    assert "overall                  75.0%" in report


def test_main_uses_process_arguments(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    BrainStore(tmp_path / "brain.json").save(Brain(constant_network(throttle=2)))
    monkeypatch.setattr("sys.argv", ["synthride.ai", "--brain", str(tmp_path / "brain.json"), "--workers", "1", "play"])
    assert ai_cli.main() == 0
    assert "overall" in capsys.readouterr().out


def test_module_runs_the_cli(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr("sys.argv", ["synthride.ai", "--brain", str(tmp_path / "none.json"), "play"])
    with pytest.raises(SystemExit) as exit_info:
        runpy.run_module("synthride.ai", run_name="__main__")
    assert exit_info.value.code == 1
