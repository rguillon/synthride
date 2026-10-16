# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT
"""Take a light in-game and a level editor screenshot of the game: ``python -m tests.screenshots``."""

from __future__ import annotations

import threading
from pathlib import Path

from playwright.sync_api import Page, ViewportSize, sync_playwright

from synthride.server.game_server import GameServer

OUT = Path("data")
VIEWPORT = ViewportSize(width=1600, height=900)
QUALITY = 88
EDITOR_SCROLL = 12  # rows the editor moves forward
LEVEL = 22  # Prism Cascade, counted from 1: heights and colours from the start


def snap(page: Page, name: str) -> None:
    """Save the page as a JPEG in ``OUT``."""
    path = OUT / name
    page.screenshot(path=path, type="jpeg", quality=QUALITY)
    print(f"{path} ({path.stat().st_size // 1024} KB)")  # noqa: T201


def take(url: str) -> None:
    """Ride ``LEVEL``, then edit it, taking a screenshot of each."""
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(args=["--enable-unsafe-swiftshader"])
        page = browser.new_page(viewport=VIEWPORT)
        page.goto(url)
        page.wait_for_selector("#loading", state="detached", timeout=60_000)
        page.keyboard.press("Enter")  # title -> level select
        for _ in range(LEVEL - 1):
            page.keyboard.press("ArrowDown")
        page.keyboard.press("Enter")  # ride the level
        page.keyboard.down("ArrowUp")
        page.wait_for_timeout(2500)
        snap(page, "screenshot-game.jpg")
        page.keyboard.up("ArrowUp")
        page.keyboard.press("Escape")  # back to the level select
        page.wait_for_timeout(500)
        page.keyboard.press("KeyE")  # edit the selected level
        page.wait_for_timeout(1000)
        for _ in range(EDITOR_SCROLL):
            page.keyboard.press("ArrowUp")  # move along the track
        page.wait_for_timeout(1500)
        snap(page, "screenshot-editor.jpg")
        browser.close()


def main() -> None:
    """Serve the game in dev mode on a free port and take the screenshots."""
    OUT.mkdir(exist_ok=True)
    with GameServer(port=0, dev=True) as server:
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            take(server.url)
        finally:
            server.shutdown()


if __name__ == "__main__":
    main()
