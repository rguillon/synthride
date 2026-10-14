import runpy

import pytest


def test_module_runs_the_cli(monkeypatch, tmp_path):
    monkeypatch.setattr("sys.argv", ["synthride", "build", "--out", str(tmp_path)])
    with pytest.raises(SystemExit) as exit_info:
        runpy.run_module("synthride", run_name="__main__")
    assert exit_info.value.code == 0
    assert (tmp_path / "index.html").exists()
