# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

import threading
import urllib.error
import urllib.request
from collections.abc import Iterator

import pytest

from synthride.server.game_server import GameServer


@pytest.fixture
def server() -> Iterator[GameServer]:
    server = GameServer(port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server
    server.shutdown()
    server.server_close()


def fetch(url: str) -> tuple[str, bytes]:
    with urllib.request.urlopen(url, timeout=5) as response:  # noqa: S310
        return response.headers["Content-Type"], response.read()


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
