# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""The full-screen menus."""

from __future__ import annotations

from html import escape
from typing import TYPE_CHECKING, ClassVar

from synthride.core.world.tile_type import TileType
from synthride.web.rendering.palette import Palette

if TYPE_CHECKING:
    from collections.abc import Sequence

    from synthride.web.browser.js_bridge import JsBridge, JsObject


class MenuScreen:
    """Full-screen overlays: title, level select, level clear, game over and victory.

    Clicks on them, by touch or mouse, are queued as taps: a level's index, :attr:`BACK` or :attr:`ANYWHERE`.
    """

    KEYS = "↑ ↓ accelerate / brake &nbsp;·&nbsp; ← → strafe &nbsp;·&nbsp; SPACE jump, again in mid-air"
    KEYS_EXTRA = "ESC menu &nbsp;·&nbsp; M mute"
    EDITOR_KEY = " &nbsp;·&nbsp; E level editor"
    LEVELS_PER_COLUMN = 7
    REPO_URL = "https://github.com/rguillon/synthride"
    # The prompt to go on, in words for the keyboard and for touch: the page shows the one that fits
    PROMPT = (
        '<p class="prompt"><span class="key-text">PRESS ENTER</span><span class="touch-text">TAP TO START</span></p>'
    )
    BACK = "back"
    ANYWHERE = "anywhere"
    # (tile types sharing a line, the pattern drawn on them, what they do)
    LEGEND: ClassVar[tuple[tuple[tuple[TileType, ...], str, str], ...]] = (
        ((TileType.NORMAL,), "■", "solid ground"),
        ((TileType.BOOST,), "︿︿", "speed burst"),
        ((TileType.SLOW,), "﹀﹀", "brakes you"),
        ((TileType.KILL,), "▨", "burns · avoid"),
        ((TileType.JUMP,), "⇡", "launches you"),
        ((TileType.ICE,), "✳", "no grip · you slide"),
        ((TileType.PUSH_LEFT, TileType.PUSH_RIGHT), "◂ ▸", "pushes sideways"),
        ((TileType.REFUEL,), "+", "refills fuel"),
        ((TileType.AIR,), "○", "refills oxygen"),
        ((TileType.FINISH,), "▚", "finish line"),
    )

    def __init__(self, bridge: JsBridge, *, editor: bool = False) -> None:
        """Render into the ``menu`` element, telling of the level editor's key if the game has an ``editor``."""
        self._container = bridge.document.getElementById("menu")
        self._current: str | None = None
        self._editor_key = self.EDITOR_KEY if editor else ""
        self._taps: list[int | str] = []
        self._container.addEventListener("click", bridge.proxy(self.on_click))

    @property
    def current(self) -> str | None:
        """A key naming the screen on show, or None when hidden."""
        return self._current

    def show_title(self) -> None:
        """Show the title screen."""
        self._show(
            "title",
            '<h1 class="logo">SYNTHRIDE</h1><p class="subtitle">RIDE THE NEON GRID</p>'
            f'{self.PROMPT}<p class="keys">{self.KEYS}<br>{self.KEYS_EXTRA}{self._editor_key}</p>',
        )

    def show_level_select(self, names: Sequence[str], selected: int, *, editor: bool = False) -> None:
        """Show the level list, in columns of ``LEVELS_PER_COLUMN``, with ``selected`` highlighted.

        With an ``editor``, the keys tell how to edit the selected level.
        """
        items = [
            f'<li class="{"selected" if index == selected else ""}" data-level="{index}">'
            f"{index + 1:02d} · {escape(name.upper())}</li>"
            for index, name in enumerate(names)
        ]
        columns = "".join(
            f'<ul class="level-list">{"".join(items[start : start + self.LEVELS_PER_COLUMN])}</ul>'
            for start in range(0, len(items), self.LEVELS_PER_COLUMN)
        )
        edit = " &nbsp;·&nbsp; E edit" if editor else ""
        self._show(
            f"select:{selected}:{editor}:{'|'.join(names)}",
            '<button class="menu-back" data-back>◀ BACK</button><p class="subtitle">SELECT LEVEL</p>'
            f'<div class="level-columns">{columns}</div>{self.legend()}'
            f'<p class="keys">↑ ↓ ← → choose &nbsp;·&nbsp; ENTER ride{edit} &nbsp;·&nbsp; ESC back</p>'
            f'<a class="repo-link" href="{self.REPO_URL}" target="_blank" rel="noopener">SOURCE ON GITHUB</a>',
        )

    @classmethod
    def legend(cls) -> str:
        """Return a key to the blocks: each one's colour, marking and effect, and a word about tunnels."""
        entries = "".join(
            f'<li><span class="swatch" style="color:{Palette.css(Palette.tile_color(types[0]))}">{glyph}</span>'
            f"{escape(effect.upper())}</li>"
            for types, glyph, effect in cls.LEGEND
        )
        tunnels = (
            f'<li><span class="swatch" style="color:{Palette.css(Palette.TUNNEL)}">∩</span>TUNNELS · MIND THE ROOF</li>'
        )
        return f'<ul class="legend">{entries}{tunnels}</ul>'

    def show_level_won(self, name: str) -> None:
        """Show the level clear screen for level ``name``."""
        self._show(
            f"won:{name}", f'<h2 class="headline">LEVEL CLEAR</h2><p class="subtitle">{escape(name.upper())}</p>'
        )

    def show_game_over(self) -> None:
        """Show the game over screen."""
        self._show("game-over", f'<h2 class="headline">GAME OVER</h2>{self.PROMPT}')

    def show_victory(self) -> None:
        """Show the victory screen."""
        self._show(
            "victory",
            f'<h1 class="logo">YOU WIN</h1><p class="subtitle">ALL GRIDS CONQUERED</p>{self.PROMPT}',
        )

    def on_click(self, event: JsObject) -> None:
        """Queue the tap a click makes: on a level, on the back button or anywhere else; links are left to open."""
        target = event.target
        if target.closest("a") is not None:
            return
        level = target.closest("[data-level]")
        if level is not None:
            self._taps.append(int(level.dataset.level))
        elif target.closest("[data-back]") is not None:
            self._taps.append(self.BACK)
        else:
            self._taps.append(self.ANYWHERE)

    def consume_taps(self) -> list[int | str]:
        """Return the taps made since the last call, oldest first."""
        taps, self._taps = self._taps, []
        return taps

    def hide(self) -> None:
        """Hide the menus."""
        self._current = None
        self._container.hidden = True

    def _show(self, key: str, markup: str) -> None:
        if key == self._current:
            return
        self._current = key
        self._container.innerHTML = markup
        self._container.hidden = False
