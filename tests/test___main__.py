# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

import runpy
from pathlib import Path

import pytest


def test_module_runs_the_cli(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr("sys.argv", ["synthride", "build", "--out", str(tmp_path)])
    with pytest.raises(SystemExit) as exit_info:
        runpy.run_module("synthride", run_name="__main__")
    assert exit_info.value.code == 0
    assert (tmp_path / "index.html").exists()
