from typing import ClassVar

import pytest

from synthride.server import server_cli
from synthride.server.server_cli import ServerCli


class StubServer:
    instances: ClassVar[list["StubServer"]] = []

    def __init__(self, host, port):
        self.host, self.port, self.url = host, port, f"http://{host}:{port}/"
        StubServer.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def serve_forever(self):
        raise KeyboardInterrupt


def test_build_writes_static_site(tmp_path, capsys):
    assert ServerCli().run(["build", "--out", str(tmp_path / "site")]) == 0
    assert (tmp_path / "site" / "index.html").read_text().startswith("<!doctype html>")
    assert (tmp_path / "site" / "synthride.zip").read_bytes().startswith(b"PK")
    assert "site" in capsys.readouterr().out


def test_serve_runs_until_interrupted(capsys):
    assert ServerCli(StubServer).run(["serve", "--host", "localhost", "--port", "9000"]) == 0
    assert (StubServer.instances[-1].host, StubServer.instances[-1].port) == ("localhost", 9000)
    assert "http://localhost:9000/" in capsys.readouterr().out


def test_requires_a_command():
    with pytest.raises(SystemExit):
        ServerCli().run([])


def test_main_uses_process_arguments(monkeypatch, tmp_path):
    monkeypatch.setattr("sys.argv", ["synthride", "build", "--out", str(tmp_path)])
    assert server_cli.main() == 0
