# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

from pathlib import Path
from typing import ClassVar, NoReturn, final

import pytest

from synthride.server import server_cli
from synthride.server.server_cli import ServerCli


@final
class StubServer:
    instances: ClassVar[list["StubServer"]] = []

    def __init__(self, host: str, port: int, *, dev: bool = False) -> None:
        self.host, self.port, self.dev, self.url = host, port, dev, f"http://{host}:{port}/"
        StubServer.instances.append(self)

    def __enter__(self) -> "StubServer":
        return self

    def __exit__(self, *exc: object) -> bool:
        return False

    def serve_forever(self) -> NoReturn:
        raise KeyboardInterrupt


def test_build_writes_static_site(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert ServerCli().run(["build", "--out", str(tmp_path / "site")]) == 0
    assert (tmp_path / "site" / "index.html").read_text().startswith("<!doctype html>")
    assert (tmp_path / "site" / "synthride.zip").read_bytes().startswith(b"PK")
    assert "site" in capsys.readouterr().out


def test_serve_runs_until_interrupted(capsys: pytest.CaptureFixture[str]) -> None:
    assert ServerCli(StubServer).run(["serve", "--host", "localhost", "--port", "9000"]) == 0
    assert (StubServer.instances[-1].host, StubServer.instances[-1].port) == ("localhost", 9000)
    assert not StubServer.instances[-1].dev
    assert "http://localhost:9000/" in capsys.readouterr().out


def test_serve_dev_saves_the_editor_tracks_to_the_level_files(capsys: pytest.CaptureFixture[str]) -> None:
    assert ServerCli(StubServer).run(["serve", "--dev"]) == 0
    assert StubServer.instances[-1].dev
    assert "level editor saving to the level files" in capsys.readouterr().out


def test_requires_a_command() -> None:
    with pytest.raises(SystemExit):
        ServerCli().run([])


def test_main_uses_process_arguments(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr("sys.argv", ["synthride", "build", "--out", str(tmp_path)])
    assert server_cli.main() == 0
