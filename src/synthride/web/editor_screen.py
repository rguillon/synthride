# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""The 3D level editor: brushes painting the track under the mouse."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, replace
from html import escape
from typing import TYPE_CHECKING, ClassVar

from synthride.core.tile import Tile
from synthride.core.tile_type import TileType
from synthride.core.track import Track
from synthride.core.track_parser import TrackParser
from synthride.editor.track_grid import Brush, BrushKind, LevelSettings, Rect, TrackGrid
from synthride.editor.track_picker import TrackPicker
from synthride.web.palette import Palette

if TYPE_CHECKING:
    from synthride.core.level import Level
    from synthride.web.custom_level_store import CustomLevelStore
    from synthride.web.js_bridge import JsBridge, JsObject


@dataclass(frozen=True)
class Tool:
    """A brush as the toolbar shows it: its icon, its colour and what it does."""

    name: str
    glyph: str
    color: int
    label: str
    brush: Brush


def _tile(tile_type: TileType, glyph: str, label: str) -> Tool:
    color = Palette.tile_color(tile_type)
    return Tool(tile_type.name.lower(), glyph, color, label, Brush(BrushKind.TILE, tile_type.value))


class EditorScreen:
    """The level editor, over the 3D view of the track being edited.

    The mouse wheel moves the camera along the track. Pressing on the track and releasing paints the rectangle between
    the two cells with the selected brush; the right button erases. New tiles stand at the selected height. The
    toolbar holds the brushes, the heights and the track's settings. Starting a test ride and leaving the editor are
    left to the game loop, as actions it collects with :meth:`consume_actions`.
    """

    RIDE: ClassVar[str] = "ride"
    BACK: ClassVar[str] = "back"
    ERASER: ClassVar[Tool] = Tool("erase", "⌫", 0xFF6D6D, "Erase: leave a gap", Brush(BrushKind.ERASE))
    TOOLS: ClassVar[tuple[Tool, ...]] = (
        _tile(TileType.NORMAL, "■", "Solid ground"),
        _tile(TileType.BOOST, "︿", "Boost: speed burst"),
        _tile(TileType.SLOW, "﹀", "Slow: brakes you"),
        _tile(TileType.ICE, "✳", "Ice: no grip"),
        _tile(TileType.KILL, "▨", "Kill: burns"),
        _tile(TileType.JUMP, "⇡", "Jump pad: launches you"),
        _tile(TileType.REFUEL, "+", "Refuel"),
        _tile(TileType.AIR, "○", "Oxygen refill"),
        _tile(TileType.PUSH_LEFT, "◂", "Pushes left"),
        _tile(TileType.PUSH_RIGHT, "▸", "Pushes right"),
        _tile(TileType.FINISH, "▚", "Finish line"),
        ERASER,
        Tool("raise", "⬆", 0xFFFFFF, "Raise one height", Brush(BrushKind.RAISE)),
        Tool("lower", "⬇", 0xFFFFFF, "Lower one height", Brush(BrushKind.LOWER)),
        Tool("ramp_up", "◢", 0xFFB347, "Ramp rising ahead", Brush(BrushKind.SHAPE, "f")),
        Tool("ramp_down", "◣", 0xFFB347, "Ramp falling ahead", Brush(BrushKind.SHAPE, "b")),
        Tool("tunnel", "∩", Palette.TUNNEL, "Square tunnel", Brush(BrushKind.SHAPE, "T")),
        Tool("round_tunnel", "◠", Palette.TUNNEL, "Round tunnel", Brush(BrushKind.SHAPE, "A")),
        Tool("flat", "▬", 0xFFFFFF, "Flat and open: no ramp, no tunnel", Brush(BrushKind.SHAPE, "")),
    )
    # (action, label): the buttons acting on the whole track
    ACTIONS: ClassVar[tuple[tuple[str, str], ...]] = (
        ("undo", "↶ Undo"),
        (RIDE, "▶ Test ride"),
        ("save", "Save"),
        ("export", "Export"),
        ("import", "Import"),
        ("new", "New"),
        ("remove", "Delete"),
        (BACK, "Back"),
    )
    # (field, label, low, high): the track's settings
    SETTINGS: ClassVar[tuple[tuple[str, str, int, int], ...]] = (
        ("gravity", "GRAVITY", 5, 40),
        ("fuel", "FUEL", 10, 999),
        ("oxygen", "OXYGEN", 10, 999),
    )
    KEYS: ClassVar[str] = (
        "WHEEL / ↑ ↓ move &nbsp;·&nbsp; DRAG paint &nbsp;·&nbsp; RIGHT DRAG erase &nbsp;·&nbsp; 1-8 height"
        " &nbsp;·&nbsp; Q E brush &nbsp;·&nbsp; Z undo &nbsp;·&nbsp; T test ride &nbsp;·&nbsp; ESC back"
    )
    SCROLL_KEYS: ClassVar[dict[str, float]] = {"ArrowUp": 4.0, "KeyW": 4.0, "ArrowDown": -4.0, "KeyS": -4.0}
    ROWS_PER_WHEEL: ClassVar[float] = 0.04  # rows per pixel of wheel travel
    SCROLL_RATE: ClassVar[float] = 12.0
    VIEW_ROWS: ClassVar[int] = 6  # how far ahead of the camera's point the ground height is judged
    MARGIN_ROWS: ClassVar[int] = 40  # how far past the end of the track the camera may go
    CURSOR_LIFT: ClassVar[float] = 0.04
    GUIDE_BEHIND: ClassVar[int] = 6  # rows of the guide grid behind the camera's point
    GUIDE_ROWS: ClassVar[int] = 80
    GUIDE_COLOR: ClassVar[int] = 0x00F0FF
    GUIDE_LIFT: ClassVar[float] = 0.01

    def __init__(self, bridge: JsBridge, store: CustomLevelStore, surface: JsObject, camera: JsObject) -> None:
        """Render the toolbar into the ``editor`` element and paint with the mouse on ``surface``, seen by ``camera``.

        Levels are saved in ``store``.
        """
        self._bridge = bridge
        self._document = bridge.document
        self._container = self._document.getElementById("editor")
        self._store = store
        self._surface = surface
        self._camera = camera
        self.grid = TrackGrid.starter()
        self.settings = LevelSettings()
        self.slot: int | None = None
        self.tool = self.TOOLS[0]
        self.height = 1
        self.row = 0.0  # where the camera looks, in rows from the start
        self._target_row = 0.0
        self.message = ""
        self.hover: tuple[int, int] | None = None
        self._anchor: tuple[int, int] | None = None
        self._dragging: Tool | None = None
        self._pointer: tuple[float, float] | None = None
        self._level: Level | None = None
        self._actions: list[str] = []
        self._mounted = False
        self._active = False
        self._shown: dict[str, str] = {}
        self.cursor = self._make_cursor()
        self.guide = self._make_guide()
        self._read_file = bridge.proxy(self.on_file_text)
        container = self._container
        container.addEventListener("click", bridge.proxy(self.on_click))
        container.addEventListener("change", bridge.proxy(self.on_change))
        surface.addEventListener("pointerdown", bridge.proxy(self.on_pointer_down))
        surface.addEventListener("pointermove", bridge.proxy(self.on_pointer_move))
        surface.addEventListener("pointerup", bridge.proxy(self.on_pointer_up))
        surface.addEventListener("pointerleave", bridge.proxy(self.on_pointer_leave))
        surface.addEventListener("contextmenu", bridge.proxy(self.on_context_menu))
        surface.addEventListener("wheel", bridge.proxy(self.on_wheel), bridge.obj(passive=False))

    # The track being edited

    @property
    def level(self) -> Level:
        """The level the grid makes, built again after each change."""
        if self._level is None:
            self._level = self.settings.level(self.grid)
        return self._level

    def open(self, settings: LevelSettings, grid: TrackGrid, slot: int | None = None) -> None:
        """Edit ``grid`` with ``settings``, saved in ``slot`` if it is a saved level."""
        self.settings, self.grid, self.slot = settings, grid, slot
        self.row = self._target_row = 0.0
        self.message = ""
        self._changed()
        self._sync_fields()
        self.refresh()

    def open_level(self, level: Level, slot: int | None = None) -> None:
        """Edit ``level``: the custom level saved in ``slot``, or a copy of a bundled level when None."""
        self.open(LevelSettings.of(level), TrackGrid.from_track(level.track), slot)

    def levels(self) -> list[Level]:
        """Return the saved levels, for the level select."""
        return self._store.levels()

    def consume_actions(self) -> list[str]:
        """Return the actions for the game loop since the last call: :attr:`RIDE` or :attr:`BACK`."""
        actions, self._actions = self._actions, []
        return actions

    @property
    def focus(self) -> tuple[float, float, float]:
        """The point the camera looks at, ``(x, z, ground)`` in world coordinates."""
        first = max(0, math.floor(self.row))
        levels = [
            int(cell[1])
            for row in range(first, first + self.VIEW_ROWS)
            for column in range(Track.COLUMNS)
            if (cell := self.grid.cell(column, row)) is not None
        ]
        ground = max(levels, default=self.height) * Tile.HEIGHT_UNIT
        return Track.COLUMNS * Tile.WIDTH / 2, -self.row * Tile.LENGTH, ground

    # Showing

    def show(self) -> None:
        """Show the editor and let the mouse paint."""
        if not self._mounted:
            self._mount()
        if not self._active:
            self._active = True
            self._container.hidden = False
            self.refresh()

    def hide(self) -> None:
        """Hide the editor and stop painting."""
        self._active = False
        self._container.hidden = True
        self.cursor.visible = self.guide.visible = False
        self._dragging = self._anchor = None

    def update(self, dt: float) -> None:
        """Ease the camera along the track and keep the cursor under the mouse, once a frame."""
        self.row += (self._target_row - self.row) * (1 - math.exp(-self.SCROLL_RATE * dt))
        if self._pointer is not None:
            self.hover = self._pick(*self._pointer)
        self._place_cursor()
        self._place_guide()

    def scroll(self, rows: float) -> None:
        """Move the camera ``rows`` along the track, toward the finish when positive."""
        top = max(self.grid.row_count, self.grid.length) + self.MARGIN_ROWS
        self._target_row = min(top, max(0.0, self._target_row + rows))

    # Keys and buttons

    def handle_key(self, code: str) -> None:
        """React to a key pressed in the editor."""
        if code in self.SCROLL_KEYS:
            self.scroll(self.SCROLL_KEYS[code])
        elif code.startswith("Digit") and code[5:].isdigit() and 1 <= int(code[5:]) <= TrackParser.MAX_LEVEL:
            self.act("height", value=code[5:])
        elif code in ("KeyQ", "KeyE"):
            index = self.TOOLS.index(self.tool) + (1 if code == "KeyE" else -1)
            self.act("tool", value=self.TOOLS[index % len(self.TOOLS)].name)
        elif code == "KeyZ":
            self.act("undo")
        elif code == "KeyT":
            self.act(self.RIDE)
        elif code == "Escape":
            self.act(self.BACK)

    def act(self, action: str, value: str = "") -> None:  # noqa: C901  (one branch per button)
        """Carry out ``action``, from a button or a key."""
        match action:
            case self.RIDE | self.BACK:
                self._actions.append(action)
                return
            case "tool":
                self.tool = next(tool for tool in self.TOOLS if tool.name == value)
            case "height":
                self.height = min(TrackParser.MAX_LEVEL, max(1, int(value)))
            case "undo":
                if self.grid.can_undo:
                    self.grid.undo()
                    self._changed()
            case "save":
                self._save()
            case "export":
                self._export()
            case "import":
                self._document.getElementById("editor-file").click()
            case "new":
                self.open(LevelSettings(), TrackGrid.starter())
            case "remove":
                self._remove()
            case _:
                return
        self.refresh()

    def on_click(self, event: JsObject) -> None:
        """Carry out the action of the clicked button."""
        element = event.target.closest("[data-action]")
        if element is not None:
            self.act(self._data(element, "action"), self._data(element, "value"))

    def on_change(self, event: JsObject) -> None:
        """Take in a changed setting, or read the level file picked to import."""
        target = event.target
        field = self._data(target, "field")
        if field == "file":
            file = target.files.item(0)
            if file is not None:
                file.text().then(self._read_file)
            target.value = ""
            return
        if field == "name":
            self.settings = replace(self.settings, name=str(target.value).strip() or "My track")
        elif field in ("gravity", "fuel", "oxygen"):
            try:
                value = float(target.value)
            except ValueError:
                self._sync_fields()
                return
            _, _, low, high = next(setting for setting in self.SETTINGS if setting[0] == field)
            value = min(high, max(low, value))
            key = {"gravity": "gravity", "fuel": "fuel_capacity", "oxygen": "oxygen_seconds"}[field]
            self.settings = replace(self.settings, **{key: value})
        else:
            return
        self._level = None
        self._sync_fields()
        self.refresh()

    def on_file_text(self, text: str) -> None:
        """Import the level file ``text``."""
        try:
            settings, grid = LevelSettings.read(str(text))
        except ValueError as error:
            self.message = f"Import failed: {error}"
        else:
            self.open(settings, grid)
            self.message = f"Imported “{settings.name}”"
        self.refresh()

    @staticmethod
    def _data(element: JsObject, name: str) -> str:
        """Return the ``data-`` attribute ``name`` of ``element``, empty when it has none."""
        value = getattr(getattr(element, "dataset", None), name, None)
        return "" if value is None else str(value)

    # The mouse

    def on_pointer_down(self, event: JsObject) -> None:
        """Start a paint stroke where the mouse presses: the left button paints, the right one erases."""
        if not self._active or event.button not in (0, 2):
            return
        self._pointer = self._ndc(event)
        cell = self._pick(*self._pointer)
        if cell is None:
            return
        self._anchor = self.hover = cell
        self._dragging = self.ERASER if event.button == 2 else self.tool
        self._surface.setPointerCapture(event.pointerId)
        self._place_cursor()

    def on_pointer_move(self, event: JsObject) -> None:
        """Follow the mouse with the cursor, stretching the stroke's rectangle while a button is down."""
        if not self._active:
            return
        self._pointer = self._ndc(event)
        self.hover = self._pick(*self._pointer)
        self._place_cursor()

    def on_pointer_up(self, event: JsObject) -> None:
        """Paint the stroke's rectangle."""
        if self._dragging is None or self._anchor is None:
            return
        self._pointer = self._ndc(event)
        end = self._pick(*self._pointer) or self.hover or self._anchor
        tool, anchor = self._dragging, self._anchor
        self._dragging = self._anchor = None
        if self.grid.paint(Rect(*anchor, *end), tool.brush, self.height):
            self._changed()
            self.refresh()
        self._place_cursor()

    def on_pointer_leave(self, _event: JsObject) -> None:
        """Hide the cursor when the mouse leaves the view."""
        if self._dragging is None:
            self._pointer = self.hover = None
            self._place_cursor()

    def on_context_menu(self, event: JsObject) -> None:
        """Keep the browser's menu from opening on a right click, which erases."""
        event.preventDefault()

    def on_wheel(self, event: JsObject) -> None:
        """Move along the track with the mouse wheel."""
        if not self._active:
            return
        event.preventDefault()
        self.scroll(-float(event.deltaY) * self.ROWS_PER_WHEEL)

    def _ndc(self, event: JsObject) -> tuple[float, float]:
        """Return where ``event`` happened on the view, from -1 to 1 across and up."""
        width = max(1.0, float(self._surface.clientWidth or 1))
        height = max(1.0, float(self._surface.clientHeight or 1))
        return float(event.offsetX) / width * 2 - 1, 1 - float(event.offsetY) / height * 2

    def _pick(self, x: float, y: float) -> tuple[int, int] | None:
        """Return the cell under the view point ``(x, y)``."""
        three, camera = self._bridge.three, self._camera
        point = three.Vector3.new(x, y, 0.5).unproject(camera)
        eye = camera.position
        origin = (float(eye.x), float(eye.y), float(eye.z))
        direction = (float(point.x) - origin[0], float(point.y) - origin[1], float(point.z) - origin[2])
        return TrackPicker.pick(self.grid, origin, direction, self.height, clamp=self._dragging is not None)

    def _make_cursor(self) -> JsObject:
        """Return the box showing the cells the brush will paint."""
        three, bridge = self._bridge.three, self._bridge
        box = three.BoxGeometry.new(1, 1, 1)
        box.translate(0.5, 0.5, -0.5)  # from the origin toward +x, +y and -z, like the track
        self._cursor_fill = three.MeshBasicMaterial.new(
            bridge.obj(color=0xFFFFFF, transparent=True, opacity=0.22, depthWrite=False)
        )
        self._cursor_edge = three.LineBasicMaterial.new(bridge.obj(color=0xFFFFFF))
        cursor = three.Group.new()
        cursor.add(three.Mesh.new(box, self._cursor_fill))
        cursor.add(three.LineSegments.new(three.EdgesGeometry.new(box), self._cursor_edge))
        cursor.visible = False
        return cursor

    @property
    def objects(self) -> tuple[JsObject, ...]:
        """The editor's own objects in the 3D scene: the brush cursor and the guide grid."""
        return self.cursor, self.guide

    def _make_guide(self) -> JsObject:
        """Return the faint grid showing where new tiles land, at the brush height, around the camera's point."""
        three, bridge = self._bridge.three, self._bridge
        length = self.GUIDE_ROWS * Tile.LENGTH
        positions: list[float] = []
        for column in range(Track.COLUMNS + 1):
            x = column * Tile.WIDTH
            positions += [x, 0.0, 0.0, x, 0.0, -length]
        for row in range(self.GUIDE_ROWS + 1):
            z = -row * Tile.LENGTH
            positions += [0.0, 0.0, z, Track.COLUMNS * Tile.WIDTH, 0.0, z]
        geometry = three.BufferGeometry.new()
        geometry.setAttribute("position", three.BufferAttribute.new(bridge.float32_array(positions), 3))
        material = three.LineBasicMaterial.new(
            bridge.obj(color=self.GUIDE_COLOR, transparent=True, opacity=0.18, depthWrite=False)
        )
        guide = three.LineSegments.new(geometry, material)
        guide.visible = False
        return guide

    def _place_guide(self) -> None:
        """Move the guide grid under the camera's point, at the brush height."""
        first = max(0, math.floor(self.row) - self.GUIDE_BEHIND)
        self.guide.position.set(0, self.height * Tile.HEIGHT_UNIT + self.GUIDE_LIFT, -first * Tile.LENGTH)
        self.guide.visible = self._active

    def _place_cursor(self) -> None:
        """Stretch the cursor over the cell under the mouse, or over the stroke's rectangle."""
        cell = self.hover
        if not self._active or cell is None:
            self.cursor.visible = False
            return
        rect = Rect(*(self._anchor or cell), *cell)
        tool = self._dragging or self.tool
        levels = [int(found[1]) for column, row in rect.cells() if (found := self.grid.cell(column, row)) is not None]
        gaps = len(levels) < len(rect.columns) * len(rect.rows)
        top = max([*levels, *([self.height] if gaps else [])]) * Tile.HEIGHT_UNIT + self.CURSOR_LIFT
        columns, rows = rect.columns, rect.rows
        self.cursor.position.set(columns.start * Tile.WIDTH, 0, -rows.start * Tile.LENGTH)
        self.cursor.scale.set(len(columns) * Tile.WIDTH, top, len(rows) * Tile.LENGTH)
        self._cursor_fill.color.setHex(tool.color)
        self._cursor_edge.color.setHex(tool.color)
        self.cursor.visible = True

    # The toolbar

    def refresh(self) -> None:
        """Bring the toolbar up to date."""
        if not self._mounted:
            return
        self._set("editor-tools", self._tools_markup())
        self._set("editor-status", self._status_markup())

    def _set(self, element_id: str, markup: str) -> None:
        if self._shown.get(element_id) != markup:
            self._shown[element_id] = markup
            self._document.getElementById(element_id).innerHTML = markup

    def _mount(self) -> None:
        settings = "".join(
            f'<label>{label} <input type="number" id="editor-{field}" data-field="{field}"'
            f' min="{low}" max="{high}" step="1"></label>'
            for field, label, low, high in self.SETTINGS
        )
        actions = "".join(
            f'<button type="button" data-action="{action}">{escape(label)}</button>' for action, label in self.ACTIONS
        )
        self._container.innerHTML = (
            '<div class="editor-top">'
            '<input id="editor-name" class="editor-name" maxlength="40" data-field="name" aria-label="Track name">'
            f'<div class="editor-settings">{settings}</div>'
            '<div id="editor-status" class="editor-status"></div></div>'
            '<div class="editor-bottom"><div id="editor-tools" class="editor-tools"></div>'
            f'<div class="editor-actions">{actions}</div><p class="keys">{self.KEYS}</p></div>'
            '<input type="file" id="editor-file" accept=".json,application/json" data-field="file" hidden>'
        )
        self._mounted = True
        self._shown.clear()
        self._sync_fields()

    def _sync_fields(self) -> None:
        """Show the level's name and settings in their fields."""
        if not self._mounted:
            return
        document, settings = self._document, self.settings
        document.getElementById("editor-name").value = settings.name
        document.getElementById("editor-gravity").value = f"{settings.gravity:g}"
        document.getElementById("editor-fuel").value = f"{settings.fuel_capacity:g}"
        document.getElementById("editor-oxygen").value = f"{settings.oxygen_seconds:g}"

    def _tools_markup(self) -> str:
        tools = "".join(
            f'<button type="button" class="tool{" selected" if tool is self.tool else ""}" data-action="tool"'
            f' data-value="{tool.name}" title="{escape(tool.label)}" style="color:{Palette.css(tool.color)}">'
            f"{tool.glyph}</button>"
            for tool in self.TOOLS
        )
        heights = "".join(
            f'<button type="button" class="height{" selected" if level == self.height else ""}"'
            f' data-action="height" data-value="{level}" title="New tiles at height {level}">{level}</button>'
            for level in range(1, TrackParser.MAX_LEVEL + 1)
        )
        return (
            f'<div class="tool-group">{tools}</div>'
            f'<div class="tool-group"><span class="tool-caption">HEIGHT</span>{heights}</div>'
            f'<div class="tool-name">{escape(self.tool.label.upper())}</div>'
        )

    def _status_markup(self) -> str:
        track = self.level.track
        warnings = []
        if any(track.tile_at(column, 0) is None for column in (3, 4)):
            warnings.append("THE START NEEDS TILES UNDER THE MIDDLE COLUMNS")
        if not any(tile.tile_type is TileType.FINISH for tile in track.tiles()):
            warnings.append("NO FINISH LINE: THE LEVEL ENDS AT THE LAST ROW")
        status = f"{self.grid.length} ROWS"
        if not self._store.persistent:
            status += " · NOT SAVED IN THIS BROWSER"
        markup = escape(status)
        markup += "".join(f'<span class="editor-warning">⚠ {escape(warning)}</span>' for warning in warnings)
        if self.message:
            markup += f'<span class="editor-message">{escape(self.message)}</span>'
        return markup

    # Saving

    def _changed(self) -> None:
        self._level = None

    def _save(self) -> None:
        self.slot = self._store.put(self.slot, self.settings.write(self.grid))
        stored = "Saved" if self._store.persistent else "Kept until you close the page"
        self.message = f"{stored}: “{self.settings.name}”"

    def _remove(self) -> None:
        if self.slot is None:
            self.message = "This track is not saved"
            return
        if not self._bridge.window.confirm(f"Delete the saved track “{self.settings.name}”?"):
            return
        self._store.remove(self.slot)
        self.slot = None
        self.message = "Deleted from the saved tracks"

    def _export(self) -> None:
        window, bridge = self._bridge.window, self._bridge
        text = self.settings.write(self.grid)
        blob = window.Blob.new(bridge.array([text]), bridge.obj(type="application/json"))
        url = window.URL.createObjectURL(blob)
        link = self._document.createElement("a")
        link.href = url
        link.download = f"{self.file_name(self.settings.name)}.json"
        link.click()
        window.URL.revokeObjectURL(url)
        self.message = f"Exported {link.download}"

    @staticmethod
    def file_name(name: str) -> str:
        """Return a file name for a track called ``name``."""
        return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_") or "track"
