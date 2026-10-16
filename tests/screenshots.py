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
GAME_LEVEL = 23  # Static Storm, counted from 1: pushers, kill strips and refuel tiles from the start
GAME_PROGRESS = 6.3  # percent of the track ridden: row 28 of 448
EDITOR_LEVEL = 22  # Prism Cascade: heights and colours from the start


def snap(page: Page, name: str) -> None:
    """Save the page as a JPEG in ``OUT``."""
    path = OUT / name
    page.screenshot(path=path, type="jpeg", quality=QUALITY)
    print(f"{path} ({path.stat().st_size // 1024} KB)")  # noqa: T201


def press(page: Page, *codes: str) -> None:
    """Press and release the keys at ``codes`` in a single round trip.

    Each Playwright key press waits for a frame, which takes long with software WebGL; the game queues presses, so
    sending them all at once lands them in order on the next frame.
    """
    page.evaluate(
        """codes => {
            for (const code of codes) {
                const key = code.startsWith("Key") ? code.slice(3).toLowerCase() : code;
                for (const type of ["keydown", "keyup"]) {
                    window.dispatchEvent(new KeyboardEvent(type, {code, key, cancelable: true}));
                }
            }
        }""",
        codes,
    )


def take(url: str) -> None:
    """Ride ``GAME_LEVEL``, then edit ``EDITOR_LEVEL``, taking a screenshot of each."""
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(args=["--enable-unsafe-swiftshader"])
        page = browser.new_page(viewport=VIEWPORT)
        page.goto(url)
        page.wait_for_selector("#loading", state="detached", timeout=60_000)
        page.add_style_tag(content="#hud-fps { visibility: hidden; }")  # software WebGL makes it read ~10 FPS
        press(page, "Enter")  # title -> level select
        # The editor keeps the sky of the last level ridden, so start the edited level first
        press(page, *["ArrowDown"] * (EDITOR_LEVEL - 1), "Enter")
        page.wait_for_timeout(500)
        press(page, "Escape")  # back to the level select
        page.wait_for_timeout(500)
        press(page, "KeyE")  # edit the level
        page.wait_for_timeout(1000)
        press(page, *["ArrowUp"] * EDITOR_SCROLL)  # move along the track
        page.wait_for_timeout(1500)
        snap(page, "screenshot-editor.jpg")
        press(page, "Escape")  # back to the level select
        page.wait_for_timeout(500)
        press(page, *["ArrowDown"] * (GAME_LEVEL - EDITOR_LEVEL), "Enter")  # ride the other level
        page.keyboard.down("ArrowUp")
        # Frame times vary too much to ride for a set time: wait for the progress bar to reach the second pushers,
        # with a kill strip alongside
        page.wait_for_function(f"parseFloat(document.getElementById('hud-progress').style.width) >= {GAME_PROGRESS}")
        snap(page, "screenshot-game.jpg")
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
