from __future__ import annotations

import argparse
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from synthride.server.bundle_builder import BundleBuilder
from synthride.server.game_server import GameServer
from synthride.server.html_page_builder import HtmlPageBuilder


class ServerCli:
    """Command line entry point: ``serve`` the game locally or ``build`` a static site."""

    def __init__(self, server_factory: Callable[[str, int], Any] = GameServer) -> None:
        self._server_factory = server_factory

    def parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(prog="synthride", description="SynthRide, a synthwave sky racer.")
        commands = parser.add_subparsers(dest="command", required=True)
        serve = commands.add_parser("serve", help="serve the game on a local web server")
        serve.add_argument("--host", default="127.0.0.1")
        serve.add_argument("--port", type=int, default=8000)
        build = commands.add_parser("build", help="write a static site (index.html + synthride.zip)")
        build.add_argument("--out", type=Path, default=Path("dist/web"))
        return parser

    def run(self, argv: Sequence[str] | None = None) -> int:
        arguments = self.parser().parse_args(argv)
        if arguments.command == "build":
            return self.build(arguments.out)
        return self.serve(arguments.host, arguments.port)

    def build(self, out: Path) -> int:
        out.mkdir(parents=True, exist_ok=True)
        (out / "index.html").write_text(HtmlPageBuilder().build(), encoding="utf-8")
        (out / "synthride.zip").write_bytes(BundleBuilder().build())
        print(f"Static site written to {out}")
        return 0

    def serve(self, host: str, port: int) -> int:
        with self._server_factory(host, port) as server:
            print(f"SynthRide running at {server.url} (Ctrl+C to stop)")
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                print("Stopped.")
        return 0


def main() -> int:
    return ServerCli().run()
