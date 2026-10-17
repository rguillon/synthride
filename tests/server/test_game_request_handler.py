# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

import json
import threading
import urllib.error
import urllib.request
from collections.abc import Iterator
from pathlib import Path

import pytest

from synthride.server.game_server import GameServer
from synthride.server.level_folder import LevelFolder

LEVEL = json.dumps({"name": "Mine", "track": [[12, ".. .. N1 N1 N1 N1 .. .."]]})


def running(server: GameServer) -> Iterator[GameServer]:
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server
    server.shutdown()
    server.server_close()


@pytest.fixture
def server() -> Iterator[GameServer]:
    yield from running(GameServer(port=0))


@pytest.fixture
def dev_server(tmp_path: Path) -> Iterator[GameServer]:
    yield from running(GameServer(port=0, dev=True, levels=LevelFolder(tmp_path)))


def fetch(url: str) -> tuple[str, bytes]:
    with urllib.request.urlopen(url, timeout=5) as response:  # noqa: S310
        return response.headers["Content-Type"], response.read()


def post(url: str, body: bytes) -> tuple[int, str]:
    request = urllib.request.Request(url, data=body, method="POST")  # noqa: S310
    try:
        with urllib.request.urlopen(request, timeout=5) as response:  # noqa: S310
            return response.status, response.read().decode()
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode()


def test_serves_page(server: GameServer) -> None:
    content_type, body = fetch(server.url)
    assert content_type.startswith("text/html")
    assert b"SYNTHRIDE" in body
    assert fetch(server.url + "index.html?x=1")[1] == body


def test_serves_bundle(server: GameServer) -> None:
    content_type, body = fetch(server.url + "synthride.zip")
    assert content_type == "application/zip"
    assert body.startswith(b"PK")


def test_unknown_path_is_404(server: GameServer) -> None:
    with pytest.raises(urllib.error.HTTPError) as error:
        fetch(server.url + "nope")
    assert error.value.code == 404


def test_the_page_saves_to_the_server_in_dev_mode_only(server: GameServer, dev_server: GameServer) -> None:
    assert b"main(dev=True)" not in fetch(server.url)[1]
    assert b"main(dev=True)" in fetch(dev_server.url)[1]


def test_without_dev_mode_posts_are_refused(server: GameServer) -> None:
    status, text = post(server.url + "levels/level_01.json", LEVEL.encode())
    assert status == 403
    assert "read-only" in text


def test_in_dev_mode_a_posted_level_is_saved(dev_server: GameServer) -> None:
    assert post(dev_server.url + "levels/level_42.json", LEVEL.encode()) == (200, "Saved level_42.json")
    assert dev_server.levels is not None
    assert (dev_server.levels.root / "level_42.json").read_text() == LEVEL + "\n"


@pytest.mark.parametrize(
    ("path", "body", "status"),
    [
        ("levels/../evil.json", LEVEL.encode(), 400),
        ("levels/level_01.json", b"{nope", 400),
        ("levels/level_01.json", b"\xff", 400),
        ("levels/level_01.json", b"", 400),
        ("elsewhere", LEVEL.encode(), 404),
    ],
)
def test_in_dev_mode_bad_posts_are_refused(dev_server: GameServer, path: str, body: bytes, status: int) -> None:
    assert post(dev_server.url + path, body)[0] == status
    assert dev_server.levels is not None
    assert list(dev_server.levels.root.iterdir()) == []
