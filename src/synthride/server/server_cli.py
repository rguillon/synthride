# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""The ``synthride`` command line."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import TYPE_CHECKING, Any

from synthride.server.bundle_builder import BundleBuilder
from synthride.server.game_server import GameServer
from synthride.server.html_page_builder import HtmlPageBuilder

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence


class ServerCli:
    """Command line entry point: ``serve`` the game locally or ``build`` a static site."""

    def __init__(self, server_factory: Callable[..., Any] = GameServer) -> None:
        """Use ``server_factory`` to create the server for ``serve``."""
        self._server_factory = server_factory

    def parser(self) -> argparse.ArgumentParser:
        """Return the argument parser."""
        parser = argparse.ArgumentParser(prog="synthride", description="SynthRide, a synthwave sky racer.")
        commands = parser.add_subparsers(dest="command", required=True)
        serve = commands.add_parser("serve", help="serve the game on a local web server")
        serve.add_argument("--host", default="127.0.0.1")
        serve.add_argument("--port", type=int, default=8000)
        serve.add_argument("--dev", action="store_true", help="turn the level editor on, saving to the level files")
        build = commands.add_parser("build", help="write a static site (index.html + synthride.zip)")
        build.add_argument("--out", type=Path, default=Path("dist/web"))
        return parser

    def run(self, argv: Sequence[str] | None = None) -> int:
        """Run the command given in ``argv`` and return the exit code."""
        arguments = self.parser().parse_args(argv)
        if arguments.command == "build":
            return self.build(arguments.out)
        return self.serve(arguments.host, arguments.port, dev=arguments.dev)

    def build(self, out: Path) -> int:
        """Write a static site into ``out``."""
        out.mkdir(parents=True, exist_ok=True)
        (out / "index.html").write_text(HtmlPageBuilder().build(), encoding="utf-8")
        (out / "synthride.zip").write_bytes(BundleBuilder().build())
        print(f"Static site written to {out}")  # noqa: T201
        return 0

    def serve(self, host: str, port: int, *, dev: bool = False) -> int:
        """Serve the game until interrupted, with the level editor when ``dev``."""
        with self._server_factory(host, port, dev=dev) as server:
            mode = ", level editor on" if dev else ""
            print(f"SynthRide running at {server.url}{mode} (Ctrl+C to stop)")  # noqa: T201
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                print("Stopped.")  # noqa: T201
        return 0


def main() -> int:
    """Run the command line with the process arguments."""
    return ServerCli().run()
