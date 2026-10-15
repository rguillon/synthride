# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

from synthride.core.tile_type import TileType
from synthride.web.menu_screen import MenuScreen
from synthride.web.palette import Palette
from tests.web.fakes.fake_element import FakeElement
from tests.web.fakes.fake_js_bridge import FakeJsBridge


def make_menu() -> tuple[FakeElement, MenuScreen]:
    bridge = FakeJsBridge()
    return bridge.document.getElementById("menu"), MenuScreen(bridge)


def test_title() -> None:
    container, menu = make_menu()
    menu.show_title()
    assert "SYNTHRIDE" in container.innerHTML
    assert not container.hidden
    assert menu.current == "title"


def test_level_select_highlights_and_escapes_names() -> None:
    container, menu = make_menu()
    menu.show_level_select(["One", "<b>Two</b>"], selected=1)
    assert '<li class="selected">02 · &lt;B&gt;TWO&lt;/B&gt;</li>' in container.innerHTML
    assert '<li class="">01 · ONE</li>' in container.innerHTML


def test_level_select_lays_levels_out_in_columns() -> None:
    container, menu = make_menu()
    menu.show_level_select([f"L{n}" for n in range(MenuScreen.LEVELS_PER_COLUMN + 1)], selected=0)
    columns = [column.split("</ul>")[0] for column in container.innerHTML.split('<ul class="level-list">')[1:]]
    assert len(columns) == 2
    assert columns[0].count("<li") == MenuScreen.LEVELS_PER_COLUMN
    assert columns[1].count("<li") == 1


def test_does_not_rewrite_unchanged_screen() -> None:
    container, menu = make_menu()
    menu.show_game_over()
    container.innerHTML = "sentinel"
    menu.show_game_over()
    assert container.innerHTML == "sentinel"


def test_other_screens_and_hide() -> None:
    container, menu = make_menu()
    menu.show_level_won("Neon")
    assert "LEVEL CLEAR" in container.innerHTML
    menu.show_victory()
    assert "YOU WIN" in container.innerHTML
    menu.hide()
    assert container.hidden
    assert menu.current is None


def test_level_select_explains_every_block() -> None:
    legend = MenuScreen.legend()
    explained = {tile_type for types, _, _ in MenuScreen.LEGEND for tile_type in types}
    assert explained == set(TileType)
    assert legend.count("<li>") == len(MenuScreen.LEGEND) + 1
    assert Palette.css(Palette.tile_color(TileType.JUMP)) in legend
    assert "TUNNELS" in legend
