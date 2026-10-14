from __future__ import annotations

from http import HTTPStatus
from http.server import BaseHTTPRequestHandler
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from synthride.server.game_server import GameServer


class GameRequestHandler(BaseHTTPRequestHandler):
    """Serves the game page and the Python bundle, rebuilt on every request so edits show on reload."""

    def do_GET(self) -> None:
        server = cast("GameServer", self.server)
        path = self.path.split("?", 1)[0]
        if path in ("/", "/index.html"):
            self._send(server.page_builder.build().encode("utf-8"), "text/html; charset=utf-8")
        elif path == "/synthride.zip":
            self._send(server.bundle_builder.build(), "application/zip")
        else:
            self.send_error(HTTPStatus.NOT_FOUND)

    def _send(self, body: bytes, content_type: str) -> None:
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)
