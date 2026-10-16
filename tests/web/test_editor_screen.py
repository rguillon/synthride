# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

import json
from types import SimpleNamespace

import pytest

from synthride.core.slope import Slope
from synthride.web.editor_screen import EditorScreen
from tests.level_factory import make_level
from tests.web.fakes.fake_element import FakeElement
from tests.web.fakes.fake_fetch import FakeFetch
from tests.web.fakes.fake_js_bridge import FakeJsBridge
from tests.web.fakes.fake_js_object import FakeJsObject


class Target:
    """A clicked or changed element: its ``data-`` attributes and its value."""

    def __init__(self, field_value: str = "", **dataset: str) -> None:
        self.dataset = SimpleNamespace(**dataset)
        self.value = field_value

    def closest(self, _selector: str) -> "Target | None":
        return self if hasattr(self.dataset, "action") else None


@pytest.fixture
def ed(monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    bridge = FakeJsBridge()
    bridge.window.fetch = FakeFetch()
    saved: list[tuple[int, object]] = []
    surface = FakeElement("canvas", "canvas")
    surface.clientWidth, surface.clientHeight = 800, 400
    camera = SimpleNamespace(position=SimpleNamespace(x=0.0, y=10.0, z=0.0))
    files = ["level_01.json", "level_02.json"]
    screen = EditorScreen(bridge, surface, camera, files, lambda index, level: saved.append((index, level)))
    # A view straight down: across the screen spans the eight columns, up the screen the first 20 rows.
    monkeypatch.setattr(screen, "_pick", lambda x, y: (min(7, max(0, int((x + 1) * 4))), max(0, int((y + 1) * 10))))
    screen.show()
    return SimpleNamespace(
        bridge=bridge, fetch=bridge.window.fetch, saved=saved, screen=screen, element=bridge.document.getElementById
    )


def at(column: int, row: int, button: int = 0) -> SimpleNamespace:
    """Return a pointer event over the middle of ``(column, row)`` in the fixture's view."""
    return SimpleNamespace(
        offsetX=(column + 0.5) / 8 * 800, offsetY=400 - (row + 0.5) / 20 * 400, button=button, pointerId=1
    )


def stroke(ed: SimpleNamespace, start: tuple[int, int], end: tuple[int, int], button: int = 0) -> None:
    ed.screen.on_pointer_down(at(*start, button))
    ed.screen.on_pointer_move(at(*end, button))
    ed.screen.on_pointer_up(at(*end, button))


def click(ed: SimpleNamespace, action: str, value: str = "") -> None:
    ed.element("editor").dispatch("click", SimpleNamespace(target=Target(action=action, value=value)))


def html(ed: SimpleNamespace, element_id: str) -> str:
    return ed.element(element_id).innerHTML


def test_showing_mounts_the_toolbar(ed: SimpleNamespace) -> None:
    assert not ed.element("editor").hidden
    tools = html(ed, "editor-tools")
    assert all(f'data-value="{tool.name}"' in tools for tool in EditorScreen.TOOLS)
    assert 'class="height selected"' in tools
    assert "33 ROWS" in html(ed, "editor-status")
    assert ed.element("editor-name").value == "My track"
    assert ed.element("editor-gravity").value == "18"
    ed.screen.hide()
    assert ed.element("editor").hidden
    assert not ed.screen.cursor.visible


def test_every_slope_has_a_brush(ed: SimpleNamespace) -> None:
    values = {tool.brush.value for tool in EditorScreen.TOOLS if tool.group == "slopes"}
    assert values == {slope.value for slope in Slope}
    click(ed, "tool", "ramp_front_left")
    stroke(ed, (2, 3), (3, 3))
    assert ed.screen.grid.cell(2, 3) == "N1fl"
    click(ed, "tool", "ramp_right")
    stroke(ed, (4, 3), (4, 3))
    assert ed.screen.grid.cell(4, 3) == "N1r"
    assert html(ed, "editor-tools").count('class="tool-group"') == 5


def test_a_drag_paints_the_rectangle_with_the_brush(ed: SimpleNamespace) -> None:
    click(ed, "tool", "ice")
    stroke(ed, (2, 3), (5, 6))
    grid = ed.screen.grid
    assert grid.cell(2, 3) == "I1"
    assert grid.cell(5, 6) == "I1"
    assert grid.cell(3, 7) == "N1"
    assert ed.screen.level.track.tile_at(4, 4).tile_type.value == "I"


def test_new_tiles_stand_at_the_chosen_height(ed: SimpleNamespace) -> None:
    click(ed, "height", "3")
    stroke(ed, (0, 0), (0, 2))
    assert ed.screen.grid.cell(0, 1) == "N3"
    assert 'data-value="3" title' in html(ed, "editor-tools")


def test_the_right_button_erases_and_z_undoes(ed: SimpleNamespace) -> None:
    stroke(ed, (2, 0), (5, 1), button=2)
    assert ed.screen.grid.cell(3, 1) is None
    ed.screen.handle_key("KeyZ")
    assert ed.screen.grid.cell(3, 1) == "N1"
    ed.screen.handle_key("KeyZ")
    click(ed, "undo")


def test_other_buttons_and_strokes_off_the_track_do_nothing(
    ed: SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    ed.screen.on_pointer_down(SimpleNamespace(button=1, offsetX=0, offsetY=0, pointerId=1))
    ed.screen.on_pointer_up(at(0, 0))
    monkeypatch.setattr(ed.screen, "_pick", lambda _x, _y: None)
    ed.screen.on_pointer_down(at(0, 0))
    ed.screen.on_pointer_move(at(0, 0))
    assert not ed.screen.cursor.visible
    assert not ed.screen.grid.can_undo


def test_the_cursor_covers_the_stroke(ed: SimpleNamespace) -> None:
    ed.screen.on_pointer_down(at(1, 2))
    ed.screen.on_pointer_move(at(3, 5))
    cursor = ed.screen.cursor
    assert cursor.visible
    assert cursor.position.set.calls[-1] == (1.0, 0, -4.0)
    width, _, length = cursor.scale.set.calls[-1]
    assert (width, length) == (3.0, 8.0)
    ed.screen.on_pointer_leave(None)
    ed.screen.on_pointer_up(at(3, 5))
    ed.screen.on_pointer_leave(None)
    assert not cursor.visible


def test_the_wheel_and_keys_move_the_camera_along_the_track(ed: SimpleNamespace) -> None:
    prevented = []
    ed.screen.on_wheel(SimpleNamespace(deltaY=-250.0, preventDefault=lambda: prevented.append(True)))
    assert prevented
    for _ in range(120):
        ed.screen.update(1 / 60)
    assert ed.screen.row == pytest.approx(10.0)
    _, z, ground = ed.screen.focus
    assert z == pytest.approx(-20.0)
    assert ground == pytest.approx(0.5)
    ed.screen.handle_key("ArrowDown")
    ed.screen.handle_key("ArrowDown")
    ed.screen.handle_key("ArrowDown")
    ed.screen.scroll(-100)
    for _ in range(120):
        ed.screen.update(1 / 60)
    assert ed.screen.row == pytest.approx(0.0, abs=1e-3)
    ed.screen.scroll(10_000)
    for _ in range(300):
        ed.screen.update(1 / 60)
    assert ed.screen.row == pytest.approx(33 + EditorScreen.MARGIN_ROWS, abs=1e-3)
    assert ed.screen.guide.visible


def test_the_cursor_follows_the_mouse_as_the_camera_moves(ed: SimpleNamespace, monkeypatch: pytest.MonkeyPatch) -> None:
    ed.screen.on_pointer_move(at(2, 2))
    monkeypatch.setattr(ed.screen, "_pick", lambda _x, _y: (6, 9))
    ed.screen.update(1 / 60)
    assert ed.screen.hover == (6, 9)


def test_keys_pick_brushes_and_heights_and_ask_for_a_ride_or_to_leave(ed: SimpleNamespace) -> None:
    ed.screen.handle_key("KeyE")
    assert ed.screen.tool is EditorScreen.TOOLS[1]
    ed.screen.handle_key("KeyQ")
    ed.screen.handle_key("KeyQ")
    assert ed.screen.tool is EditorScreen.TOOLS[-1]
    ed.screen.handle_key("Digit5")
    ed.screen.handle_key("Digit9")
    ed.screen.handle_key("KeyX")
    assert ed.screen.height == 5
    ed.screen.handle_key("KeyT")
    ed.screen.handle_key("Escape")
    assert ed.screen.consume_actions() == [EditorScreen.RIDE, EditorScreen.BACK]
    assert ed.screen.consume_actions() == []


def test_letter_shortcuts_follow_the_layout(ed: SimpleNamespace) -> None:
    stroke(ed, (0, 0), (0, 0))
    ed.screen.handle_key("KeyW", "z")  # AZERTY Z: undo, not a scroll
    assert not ed.screen.grid.can_undo
    assert ed.screen._target_row == 0  # noqa: SLF001
    ed.screen.handle_key("KeyA", "q")  # AZERTY Q: previous brush
    assert ed.screen.tool is EditorScreen.TOOLS[-1]
    ed.screen.handle_key("KeyZ", "w")  # AZERTY W does nothing
    ed.screen.handle_key("Numpad3")
    assert ed.screen.height == 3
    assert ed.screen.consume_actions() == []


def test_settings_fields(ed: SimpleNamespace) -> None:
    container = ed.element("editor")
    container.dispatch("change", SimpleNamespace(target=Target(" Neon Run ", field="name")))
    container.dispatch("change", SimpleNamespace(target=Target("99", field="gravity")))
    container.dispatch("change", SimpleNamespace(target=Target("250", field="fuel")))
    container.dispatch("change", SimpleNamespace(target=Target("lots", field="oxygen")))
    container.dispatch("change", SimpleNamespace(target=Target("x", field="other")))
    level = ed.screen.level
    assert (level.name, level.gravity, level.fuel_capacity, level.oxygen_seconds) == ("Neon Run", 40.0, 250.0, 90.0)
    assert ed.element("editor-oxygen").value == "90"
    container.dispatch("change", SimpleNamespace(target=Target("", field="name")))
    assert ed.screen.settings.name == "My track"


def test_clicks_outside_buttons_and_unknown_actions_do_nothing(ed: SimpleNamespace) -> None:
    ed.element("editor").dispatch("click", SimpleNamespace(target=Target()))
    click(ed, "nothing")
    assert ed.screen.consume_actions() == []


def test_saving_a_new_track_posts_it_as_the_next_level_file(ed: SimpleNamespace) -> None:
    assert "level_03.json (NEW)" in html(ed, "editor-status")
    click(ed, "save")
    (request,) = ed.fetch.requests
    assert request.url == "levels/level_03.json"
    assert request.options["method"] == "POST"
    assert json.loads(request.options["body"])["name"] == "My track"
    assert "Saving level_03.json" in html(ed, "editor-status")
    click(ed, "save")
    assert len(ed.fetch.requests) == 1
    assert "Still saving" in html(ed, "editor-status")
    ed.fetch.answer(200, "Saved level_03.json")
    assert ed.screen.index == 2
    assert ed.screen.files[-1] == "level_03.json"
    assert [(index, level.name) for index, level in ed.saved] == [(2, "My track")]
    assert "Saved level_03.json" in html(ed, "editor-status")
    assert "(NEW)" not in html(ed, "editor-status")
    click(ed, "save")
    assert ed.fetch.requests[-1].url == "levels/level_03.json"


def test_saving_a_level_overwrites_its_file(ed: SimpleNamespace) -> None:
    ed.screen.open_level(make_level("N1 N1 N1 N1 N1 N1 N1 N1", name="Second"), 1)
    click(ed, "save")
    assert ed.fetch.requests[-1].url == "levels/level_02.json"
    ed.fetch.answer()
    assert [index for index, _level in ed.saved] == [1]
    assert ed.screen.files == ["level_01.json", "level_02.json"]


def test_saving_without_a_listener(ed: SimpleNamespace) -> None:
    screen = EditorScreen(ed.bridge, FakeElement("canvas", "canvas"), ed.screen._camera)  # noqa: SLF001
    screen.act("save")
    ed.fetch.answer()
    assert screen.files == ["level_01.json"]
    assert screen.index == 0


def test_a_stroke_that_changes_nothing_is_not_undoable(ed: SimpleNamespace) -> None:
    stroke(ed, (2, 0), (3, 1))
    assert not ed.screen.grid.can_undo


def test_a_track_opened_while_saving_stays_new(ed: SimpleNamespace) -> None:
    click(ed, "save")
    click(ed, "new")
    ed.fetch.answer()
    assert ed.screen.index is None
    assert "level_04.json (NEW)" in html(ed, "editor-status")


def test_a_refused_or_failed_save_is_reported(ed: SimpleNamespace) -> None:
    click(ed, "save")
    ed.fetch.answer(403, "The levels are read-only")
    assert "Not saved: The levels are read-only" in html(ed, "editor-status")
    assert ed.saved == []
    assert ed.screen.index is None
    click(ed, "save")
    ed.fetch.requests[-1].promise.reject("TypeError: Failed to fetch")
    assert "server is unreachable" in html(ed, "editor-status")
    ed.screen.on_save_response(SimpleNamespace(ok=True))
    assert ed.saved == []


def test_warnings_for_a_missing_start_or_finish(ed: SimpleNamespace) -> None:
    ed.screen.open_level(make_level(".. N1 .. .. .. .. .. ..", name="Odd"))
    status = html(ed, "editor-status")
    assert "THE START NEEDS TILES" in status
    assert "NO FINISH LINE" in status


def test_hidden_editor_ignores_the_mouse(ed: SimpleNamespace) -> None:
    ed.screen.hide()
    ed.screen.on_pointer_down(at(0, 0))
    ed.screen.on_pointer_move(at(0, 0))
    ed.screen.on_wheel(SimpleNamespace(deltaY=-100.0))
    ed.screen.on_pointer_up(at(0, 0))
    assert not ed.screen.grid.can_undo


def test_the_context_menu_is_kept_closed(ed: SimpleNamespace) -> None:
    prevented = []
    ed.screen.on_context_menu(SimpleNamespace(preventDefault=lambda: prevented.append(True)))
    assert prevented


def test_picking_casts_a_ray_from_the_camera() -> None:
    bridge = FakeJsBridge()
    point = SimpleNamespace(x=3.5, y=9.0, z=-5.0)
    bridge.three.Vector3 = SimpleNamespace(new=lambda *_: SimpleNamespace(unproject=lambda _camera: point))
    camera = SimpleNamespace(position=SimpleNamespace(x=3.5, y=10.0, z=-5.0))
    screen = EditorScreen(bridge, FakeJsObject(), camera)
    assert screen._pick(0.0, 0.0) == (3, 2)  # noqa: SLF001
