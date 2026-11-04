# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT
"""Ride the game by touch on a landscape phone and take screenshots: ``python -m tests.phone_screenshots``."""

from __future__ import annotations

import threading

from playwright.sync_api import Browser, Page, ViewportSize, sync_playwright

from synthride.server.game_server import GameServer
from tests.screenshots import OUT, snap

VIEWPORTS = {
    "": ViewportSize(width=844, height=390),
    "-portrait": ViewportSize(width=390, height=844),
}  # held both ways
PROGRESS = 2.0  # percent of the track to ride before the in-game screenshot


def push_stick(page: Page, dx: float, dy: float) -> None:
    """Put a finger down on the joystick, ``dx`` and ``dy`` radii from its center."""
    page.evaluate(
        """([dx, dy]) => {
            const stick = document.querySelector("[data-stick]"), r = stick.getBoundingClientRect();
            stick.dispatchEvent(new PointerEvent("pointerdown", {pointerId: 1, pointerType: "touch", bubbles: true,
                cancelable: true, clientX: r.left + r.width / 2 * (1 + dx), clientY: r.top + r.height / 2 * (1 + dy)}))
        }""",
        [dx, dy],
    )


def take(url: str) -> None:
    """Tap through the title to the level select, then ride the first level, taking a screenshot of each, per way."""
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(args=["--enable-unsafe-swiftshader"])
        for suffix, viewport in VIEWPORTS.items():
            ride(browser, url, viewport, suffix)
        browser.close()


def ride(browser: Browser, url: str, viewport: ViewportSize, suffix: str) -> None:
    """Take the level select and in-game screenshots on a phone of ``viewport``."""
    page = browser.new_page(viewport=viewport, device_scale_factor=2, is_mobile=True, has_touch=True)
    page.goto(url)
    page.wait_for_selector("#loading", state="detached", timeout=60_000)
    page.add_style_tag(content="#hud-fps { visibility: hidden; }")  # software WebGL makes it read ~10 FPS
    page.tap("#menu")  # title -> level select
    page.wait_for_function("document.body.classList.contains('touch')")  # the tap turned touch mode on
    page.wait_for_selector('[data-level="0"]')
    page.wait_for_timeout(500)
    snap(page, f"screenshot-mobile{suffix}-menu.jpg")
    page.tap('[data-level="0"]')
    page.wait_for_selector("#hud:not([hidden])")
    push_stick(page, 0.6, -0.8)  # accelerating, steering right
    page.wait_for_function(f"parseFloat(document.getElementById('hud-progress').style.width) >= {PROGRESS}")
    snap(page, f"screenshot-mobile{suffix}.jpg")
    page.evaluate("window.dispatchEvent(new Event('blur'))")  # losing focus pauses the ride
    page.wait_for_selector("[data-resume]")
    page.wait_for_timeout(300)
    snap(page, f"screenshot-mobile{suffix}-pause.jpg")
    page.close()


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
