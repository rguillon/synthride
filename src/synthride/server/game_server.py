# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""The local HTTP server for the game."""

from __future__ import annotations

from http.server import ThreadingHTTPServer

from synthride.server.bundle_builder import BundleBuilder
from synthride.server.game_request_handler import GameRequestHandler
from synthride.server.html_page_builder import HtmlPageBuilder
from synthride.server.level_folder import LevelFolder


class GameServer(ThreadingHTTPServer):
    """A small HTTP server delivering the HTML5 page and the Python bundle it runs.

    In dev mode the level editor's saves are written into the level files; otherwise they stay in the browser.
    """

    daemon_threads = True

    def __init__(  # noqa: PLR0913
        self,
        host: str = "127.0.0.1",
        port: int = 8000,
        page_builder: HtmlPageBuilder | None = None,
        bundle_builder: BundleBuilder | None = None,
        *,
        dev: bool = False,
        levels: LevelFolder | None = None,
    ) -> None:
        """Listen on ``host:port``, serving what the two builders produce.

        With ``dev``, levels posted by the editor are saved in ``levels``, by default the bundled level files.
        """
        self.levels = (levels or LevelFolder()) if dev else None
        self.page_builder = page_builder or HtmlPageBuilder(dev=dev)
        self.bundle_builder = bundle_builder or BundleBuilder()
        super().__init__((host, port), GameRequestHandler)

    @property
    def url(self) -> str:
        """The URL the game is served at."""
        host, port = self.server_address[:2]
        return f"http://{host}:{port}/"
