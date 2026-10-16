# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""HTTP request handling for the local game server."""

from __future__ import annotations

from http import HTTPStatus
from http.server import BaseHTTPRequestHandler
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from synthride.server.game_server import GameServer


class GameRequestHandler(BaseHTTPRequestHandler):
    """Serves the game page and the Python bundle, rebuilt on every request so edits show on reload.

    In dev mode, a ``POST /levels/<file>`` saves a level file from the editor. Otherwise the levels are read-only and
    every ``POST`` is refused.
    """

    LEVELS = "/levels/"

    def do_GET(self) -> None:
        """Serve the page, the bundle, or a 404."""
        server = cast("GameServer", self.server)
        path = self.path.split("?", 1)[0]
        if path in ("/", "/index.html"):
            self._send(server.page_builder.build().encode("utf-8"), "text/html; charset=utf-8")
        elif path == "/synthride.zip":
            self._send(server.bundle_builder.build(), "application/zip")
        else:
            self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        """Save the level file in the body, in dev mode only."""
        server = cast("GameServer", self.server)
        path = self.path.split("?", 1)[0]
        levels = server.levels
        if levels is None:
            self._send_text(HTTPStatus.FORBIDDEN, "The levels are read-only: run `synthride serve --dev` to edit them.")
            return
        if not path.startswith(self.LEVELS):
            self._send_text(HTTPStatus.NOT_FOUND, f"Nothing to post to at {path}")
            return
        length = int(self.headers.get("Content-Length") or 0)
        if not 0 < length <= levels.MAX_BYTES:
            self._send_text(HTTPStatus.BAD_REQUEST, "Send a level file of at most 2 MB.")
            return
        name = path.removeprefix(self.LEVELS)
        try:
            saved = levels.save(name, self.rfile.read(length).decode("utf-8"))
        except (ValueError, UnicodeDecodeError) as error:
            self._send_text(HTTPStatus.BAD_REQUEST, f"Not saved: {error}")
            return
        self.log_message("saved %s", saved)
        self._send_text(HTTPStatus.OK, f"Saved {name}")

    def _send_text(self, status: HTTPStatus, text: str) -> None:
        self._send(text.encode("utf-8"), "text/plain; charset=utf-8", status)

    def _send(self, body: bytes, content_type: str, status: HTTPStatus = HTTPStatus.OK) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)
