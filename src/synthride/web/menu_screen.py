from __future__ import annotations

from collections.abc import Sequence
from html import escape
from typing import ClassVar

from synthride.core.tile_type import TileType
from synthride.web.js_bridge import JsBridge
from synthride.web.palette import Palette


class MenuScreen:
    """Full-screen overlays: title, level select, level clear, game over and victory."""

    KEYS = "↑ ↓ accelerate / brake &nbsp;·&nbsp; ← → strafe &nbsp;·&nbsp; SPACE jump"
    KEYS_EXTRA = "ESC menu &nbsp;·&nbsp; M mute"
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

    def __init__(self, bridge: JsBridge) -> None:
        self._container = bridge.document.getElementById("menu")
        self._current: str | None = None

    @property
    def current(self) -> str | None:
        return self._current

    def show_title(self) -> None:
        self._show(
            "title",
            '<h1 class="logo">SYNTHRIDE</h1><p class="subtitle">RIDE THE NEON GRID</p>'
            '<p class="prompt">PRESS ENTER</p>'
            f'<p class="keys">{self.KEYS}<br>{self.KEYS_EXTRA}</p>',
        )

    def show_level_select(self, names: Sequence[str], selected: int) -> None:
        items = "".join(
            f'<li class="{"selected" if index == selected else ""}">{index + 1:02d} · {escape(name.upper())}</li>'
            for index, name in enumerate(names)
        )
        self._show(
            f"select:{selected}",
            '<p class="subtitle">SELECT LEVEL</p>'
            f'<ul class="level-list">{items}</ul>{self.legend()}'
            '<p class="keys">↑ ↓ choose &nbsp;·&nbsp; ENTER ride &nbsp;·&nbsp; ESC back</p>',
        )

    @classmethod
    def legend(cls) -> str:
        """A key to the blocks: each one's colour, marking and effect, and a word about tunnels."""
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
        self._show(
            f"won:{name}", f'<h2 class="headline">LEVEL CLEAR</h2><p class="subtitle">{escape(name.upper())}</p>'
        )

    def show_game_over(self) -> None:
        self._show("game-over", '<h2 class="headline">GAME OVER</h2><p class="prompt">PRESS ENTER</p>')

    def show_victory(self) -> None:
        self._show(
            "victory",
            '<h1 class="logo">YOU WIN</h1><p class="subtitle">ALL GRIDS CONQUERED</p><p class="prompt">PRESS ENTER</p>',
        )

    def hide(self) -> None:
        self._current = None
        self._container.hidden = True

    def _show(self, key: str, markup: str) -> None:
        if key == self._current:
            return
        self._current = key
        self._container.innerHTML = markup
        self._container.hidden = False
