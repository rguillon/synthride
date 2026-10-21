# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

from types import SimpleNamespace

from synthride.core.world.tile_type import TileType
from synthride.web.rendering.palette import Palette
from synthride.web.ui.menu_screen import MenuScreen
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
    assert '<li class="selected" data-level="1">02 · &lt;B&gt;TWO&lt;/B&gt;</li>' in container.innerHTML
    assert '<li class="" data-level="0">01 · ONE</li>' in container.innerHTML


def test_level_select_lays_levels_out_in_columns() -> None:
    container, menu = make_menu()
    menu.show_level_select([f"L{n}" for n in range(MenuScreen.LEVELS_PER_COLUMN + 1)], selected=0)
    columns = [column.split("</ul>")[0] for column in container.innerHTML.split('<ul class="level-list">')[1:]]
    assert len(columns) == 2
    assert columns[0].count("<li") == MenuScreen.LEVELS_PER_COLUMN
    assert columns[1].count("<li") == 1


def test_the_editor_key_is_told_when_there_is_an_editor() -> None:
    container, menu = make_menu()
    menu.show_level_select(["One"], selected=0)
    assert "E edit" not in container.innerHTML
    menu.show_level_select(["One"], selected=0, editor=True)
    assert "E edit" in container.innerHTML


def test_level_select_redraws_when_the_levels_change() -> None:
    container, menu = make_menu()
    menu.show_level_select(["One"], selected=0)
    menu.show_level_select(["One", "Two"], selected=0)
    assert "TWO" in container.innerHTML


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


def test_level_select_links_to_the_repo() -> None:
    container, menu = make_menu()
    menu.show_level_select(["One"], selected=0)
    assert f'href="{MenuScreen.REPO_URL}"' in container.innerHTML
    assert 'target="_blank" rel="noopener"' in container.innerHTML


def click(container: FakeElement, target: FakeElement) -> None:
    container.dispatch("click", SimpleNamespace(target=target))


def test_level_select_has_a_back_button() -> None:
    container, menu = make_menu()
    menu.show_level_select(["One", "Two"], selected=0)
    assert '<button class="menu-back" data-back>◀ BACK</button>' in container.innerHTML


def test_clicks_queue_taps() -> None:
    container, menu = make_menu()
    click(container, FakeElement(tag="li", level="3"))
    click(container, FakeElement(tag="button", back=""))
    click(container, FakeElement())
    assert menu.consume_taps() == [3, MenuScreen.BACK, MenuScreen.ANYWHERE]
    assert menu.consume_taps() == []


def test_clicks_on_links_are_not_taps() -> None:
    container, menu = make_menu()
    click(container, FakeElement(tag="a"))
    assert menu.consume_taps() == []


def test_prompts_have_a_key_and_a_touch_text() -> None:
    container, menu = make_menu()
    for show in (menu.show_title, menu.show_game_over, menu.show_victory):
        show()
        assert (
            '<span class="key-text">PRESS ENTER</span><span class="touch-text">TAP TO START</span>'
            in container.innerHTML
        )
