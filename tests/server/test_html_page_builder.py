# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

import re
import subprocess

import pytest

from synthride.server.html_page_builder import HtmlPageBuilder


def test_page_references_pinned_runtimes_and_bundle() -> None:
    page = HtmlPageBuilder(pyodide_version="1.2.3", three_version="0.1.0", bundle_url="game.zip").build()
    assert "https://cdn.jsdelivr.net/pyodide/v1.2.3/full/pyodide.js" in page
    assert "https://cdn.jsdelivr.net/npm/three@0.1.0/build/three.module.js" in page
    assert 'fetch("game.zip"' in page
    assert "from synthride.web.main import main; main()" in page


def test_page_has_the_game_containers() -> None:
    page = HtmlPageBuilder().build()
    assert page.startswith("<!doctype html>")
    for element_id in ("stage", "hud", "menu", "loading"):
        assert f'id="{element_id}"' in page
    for name in ("UnrealBloomPass", "LineSegments2", "LineSegmentsGeometry", "LineMaterial"):
        assert name in page


def test_page_carries_the_commit() -> None:
    assert 'data-commit="abc1234"' in HtmlPageBuilder(commit="abc1234").build()


def test_commit_comes_from_ci(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GITHUB_SHA", "0123456789abcdef")
    assert HtmlPageBuilder.current_commit() == "0123456"


def test_commit_comes_from_git(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GITHUB_SHA", raising=False)
    sha = HtmlPageBuilder.current_commit()
    assert sha == "unknown" or re.fullmatch(r"[0-9a-f]{7,}", sha)


@pytest.mark.parametrize("failure", [OSError(), subprocess.CalledProcessError(1, "git")])
def test_commit_is_unknown_without_git(monkeypatch: pytest.MonkeyPatch, failure: Exception) -> None:
    def fail(*_args: object, **_kwargs: object) -> None:
        raise failure

    monkeypatch.delenv("GITHUB_SHA", raising=False)
    monkeypatch.setattr(subprocess, "run", fail)
    assert HtmlPageBuilder.current_commit() == "unknown"


def test_dev_page_turns_the_editor_on() -> None:
    assert "main(dev=True)" in HtmlPageBuilder(dev=True).build()
    assert "main(dev=True)" not in HtmlPageBuilder().build()


def test_page_has_the_touch_controls() -> None:
    page = HtmlPageBuilder().build()
    assert 'data-code="Space"' in page
    assert "data-stick" in page
    assert "data-knob" in page
    for code in ("Escape", "KeyM"):
        assert f'data-press="{code}"' in page
    for element_id in ("touch", "mute"):
        assert f'id="{element_id}"' in page
    assert page.index('id="hud"') < page.index('id="touch"')  # the pads show with the HUD: #hud ~ #touch
    assert page.index('id="mute"') < page.index('id="loading"')  # the loading screen covers it
    assert "viewport-fit=cover" in page


def test_page_has_the_full_screen_button() -> None:
    page = HtmlPageBuilder().build()
    assert 'id="fullscreen"' in page
    assert page.index('id="fullscreen"') < page.index('id="loading"')  # the loading screen covers it
