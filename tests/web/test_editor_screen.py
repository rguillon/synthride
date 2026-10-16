# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

import json
from types import SimpleNamespace

import pytest

from synthride.core.slope import Slope
from synthride.editor.track_grid import LevelSettings, TrackGrid
from synthride.web.custom_level_store import CustomLevelStore
from synthride.web.editor_screen import EditorScreen
from tests.level_factory import make_level
from tests.web.fakes.fake_element import FakeElement
from tests.web.fakes.fake_js_bridge import FakeJsBridge
from tests.web.fakes.fake_js_object import FakeJsObject


class Target:
    """A clicked or changed element: its ``data-`` attributes and its value."""

    def __init__(self, field_value: str = "", **dataset: str) -> None:
        self.dataset = SimpleNamespace(**dataset)
        self.value = field_value

    def closest(self, _selector: str) -> "Target | None":
        return self if hasattr(self.dataset, "action") else None


class Storage:
    def __init__(self) -> None:
        self.items: dict[str, str] = {}

    def getItem(self, key: str) -> str | None:  # noqa: N802
        return self.items.get(key)

    def setItem(self, key: str, value: str) -> None:  # noqa: N802
        self.items[key] = value


@pytest.fixture
def ed(monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    bridge = FakeJsBridge()
    bridge.window.localStorage = Storage()
    store = CustomLevelStore(bridge.window)
    surface = FakeElement("canvas", "canvas")
    surface.clientWidth, surface.clientHeight = 800, 400
    camera = SimpleNamespace(position=SimpleNamespace(x=0.0, y=10.0, z=0.0))
    screen = EditorScreen(bridge, store, surface, camera)
    # A view straight down: across the screen spans the eight columns, up the screen the first 20 rows.
    monkeypatch.setattr(screen, "_pick", lambda x, y: (min(7, max(0, int((x + 1) * 4))), max(0, int((y + 1) * 10))))
    screen.show()
    return SimpleNamespace(bridge=bridge, store=store, screen=screen, element=bridge.document.getElementById)


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


def test_save_then_reopen_and_delete(ed: SimpleNamespace) -> None:
    click(ed, "save")
    assert ed.screen.slot == 0
    assert "Saved" in html(ed, "editor-status")
    stroke(ed, (0, 0), (0, 0))
    click(ed, "save")
    assert len(ed.store.texts) == 1
    assert [level.name for level in ed.screen.levels()] == ["My track"]
    click(ed, "new")
    assert ed.screen.slot is None
    click(ed, "remove")
    assert "not saved" in html(ed, "editor-status")
    ed.screen.open_level(ed.store.levels()[0], 0)
    assert ed.screen.grid.cell(0, 0) == "N1"
    ed.bridge.window.confirm = lambda _message: False
    click(ed, "remove")
    assert len(ed.store.texts) == 1
    ed.bridge.window.confirm = lambda _message: True
    click(ed, "remove")
    assert ed.store.texts == ()


def test_export_downloads_the_level_file(ed: SimpleNamespace) -> None:
    ed.screen.open(LevelSettings("Neon Run!"), TrackGrid.starter())
    click(ed, "export")
    window = ed.bridge.window
    (blob,) = window.Blob.created
    assert json.loads(blob.args[0][0])["name"] == "Neon Run!"
    link = ed.bridge.document.created[-1]
    assert link.download == "neon_run.json"
    assert link.clicks == 1
    assert window.URL.revokeObjectURL.calls


def test_import_reads_the_picked_file(ed: SimpleNamespace) -> None:
    click(ed, "import")
    file_input = ed.element("editor-file")
    assert file_input.clicks == 1
    text = json.dumps({"name": "Mine", "track": [[12, ".. .. N1 N1 N1 N1 .. .."]]})
    promise = SimpleNamespace(then=lambda callback: callback(text))
    file_input.files = SimpleNamespace(item=lambda _index: SimpleNamespace(text=lambda: promise))
    file_input.dataset = SimpleNamespace(field="file")
    ed.element("editor").dispatch("change", SimpleNamespace(target=file_input))
    assert ed.screen.settings.name == "Mine"
    assert "Imported" in html(ed, "editor-status")
    assert ed.element("editor-name").value == "Mine"
    file_input.files = SimpleNamespace(item=lambda _index: None)
    ed.element("editor").dispatch("change", SimpleNamespace(target=file_input))


def test_a_broken_file_is_reported(ed: SimpleNamespace) -> None:
    ed.screen.on_file_text("{nope")
    assert "Import failed" in html(ed, "editor-status")


def test_warnings_for_a_missing_start_or_finish(ed: SimpleNamespace) -> None:
    ed.screen.open_level(make_level(".. N1 .. .. .. .. .. ..", name="Odd"))
    status = html(ed, "editor-status")
    assert "THE START NEEDS TILES" in status
    assert "NO FINISH LINE" in status


def test_without_storage_saving_says_so(ed: SimpleNamespace) -> None:
    ed.bridge.window.localStorage = None
    click(ed, "save")
    assert "NOT SAVED IN THIS BROWSER" in html(ed, "editor-status")
    assert "Kept until you close the page" in html(ed, "editor-status")


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
    screen = EditorScreen(bridge, CustomLevelStore(SimpleNamespace(localStorage=None)), FakeJsObject(), camera)
    assert screen._pick(0.0, 0.0) == (3, 2)  # noqa: SLF001


def test_file_names() -> None:
    assert EditorScreen.file_name("Neon  Run #2") == "neon_run_2"
    assert EditorScreen.file_name("★★") == "track"
