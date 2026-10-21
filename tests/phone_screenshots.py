# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT
"""Ride the game by touch on a landscape phone and take screenshots: ``python -m tests.phone_screenshots``."""

from __future__ import annotations

import threading

from playwright.sync_api import Page, ViewportSize, sync_playwright

from synthride.server.game_server import GameServer
from tests.screenshots import OUT, snap

VIEWPORT = ViewportSize(width=844, height=390)  # a phone held sideways
PROGRESS = 2.0  # percent of the track to ride before the in-game screenshot


def hold_pad(page: Page, code: str) -> None:
    """Put a finger down on the pad for ``code`` and leave it there."""
    page.evaluate(
        """code => document.querySelector(`[data-code="${code}"]`).dispatchEvent(
            new PointerEvent("pointerdown", {pointerId: 1, pointerType: "touch", bubbles: true, cancelable: true}))""",
        code,
    )


def take(url: str) -> None:
    """Tap through the title to the level select, then ride the first level, taking a screenshot of each."""
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(args=["--enable-unsafe-swiftshader"])
        page = browser.new_page(viewport=VIEWPORT, device_scale_factor=2, is_mobile=True, has_touch=True)
        page.goto(url)
        page.wait_for_selector("#loading", state="detached", timeout=60_000)
        page.add_style_tag(content="#hud-fps { visibility: hidden; }")  # software WebGL makes it read ~10 FPS
        page.tap("#menu")  # title -> level select
        page.wait_for_function("document.body.classList.contains('touch')")  # the tap turned touch mode on
        page.wait_for_selector('[data-level="0"]')
        page.wait_for_timeout(500)
        snap(page, "screenshot-mobile-menu.jpg")
        page.tap('[data-level="0"]')
        page.wait_for_selector("#hud:not([hidden])")
        hold_pad(page, "ArrowUp")
        page.wait_for_function(f"parseFloat(document.getElementById('hud-progress').style.width) >= {PROGRESS}")
        snap(page, "screenshot-mobile.jpg")
        browser.close()


def main() -> None:
    """Serve the game on a free port and take the screenshots."""
    OUT.mkdir(exist_ok=True)
    with GameServer(port=0) as server:
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            take(server.url)
        finally:
            server.shutdown()


if __name__ == "__main__":
    main()
