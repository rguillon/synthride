# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

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
