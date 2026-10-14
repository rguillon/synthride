from __future__ import annotations

from typing import Any, ClassVar

from synthride.core.game_event import GameEvent
from synthride.core.game_session import GameSession
from synthride.core.tile_type import TileType
from synthride.web.js_bridge import JsBridge
from synthride.web.palette import Palette


class Hud:
    """The in-game overlay: level name, lives, progress, speed / fuel / oxygen gauges, and effect callouts."""

    LAYOUT = """
      <div class="hud-top">
        <span id="hud-level"></span>
        <span id="hud-lives" class="hud-lives"></span>
      </div>
      <div class="progress"><div id="hud-progress" class="progress-fill"></div></div>
      <div class="hud-callout" id="hud-callout"></div>
      <div class="hud-bottom">
        <div class="gauge-speed"><span class="gauge-label" id="hud-speed-label">SPEED</span>
          <div class="gauge" id="hud-speed"><div class="gauge-fill" id="hud-speed-fill"></div></div></div>
        <div class="gauge-fuel"><span class="gauge-label">FUEL</span>
          <div class="gauge" id="hud-fuel"><div class="gauge-fill" id="hud-fuel-fill"></div></div></div>
        <div class="gauge-oxygen"><span class="gauge-label">OXYGEN</span>
          <div class="gauge" id="hud-oxygen"><div class="gauge-fill" id="hud-oxygen-fill"></div></div></div>
      </div>
    """
    ELEMENT_NAMES = (
        "level",
        "lives",
        "progress",
        "speed",
        "speed-label",
        "speed-fill",
        "fuel",
        "fuel-fill",
        "oxygen",
        "oxygen-fill",
        "callout",
    )
    LOW = 0.2
    CALLOUT_SECONDS = 1.1
    CALLOUTS: ClassVar[dict[GameEvent, tuple[str, int]]] = {
        GameEvent.BOOSTED: ("BOOST", Palette.tile_color(TileType.BOOST)),
        GameEvent.SLOWED: ("SLOWED DOWN", Palette.tile_color(TileType.SLOW)),
        GameEvent.REFUELED: ("FUEL REFILLED", Palette.tile_color(TileType.REFUEL)),
        GameEvent.REFILLED_AIR: ("OXYGEN REFILLED", Palette.tile_color(TileType.AIR)),
        GameEvent.LAUNCHED: ("LAUNCH", Palette.tile_color(TileType.JUMP)),
        GameEvent.SKIDDED: ("ICE · NO GRIP", Palette.tile_color(TileType.ICE)),
        GameEvent.PUSHED: ("SIDE PUSH", Palette.tile_color(TileType.PUSH_LEFT)),
        GameEvent.BUMPED: ("MIND THE ROOF", Palette.TUNNEL),
    }
    LIFE_ICON = "▲"
    KMH_PER_UNIT = 20

    def __init__(self, bridge: JsBridge) -> None:
        document = bridge.document
        self._container = document.getElementById("hud")
        self._container.innerHTML = self.LAYOUT
        self._elements = {name: document.getElementById(f"hud-{name}") for name in self.ELEMENT_NAMES}
        self._callout_left = 0.0

    def show(self, visible: bool) -> None:
        self._container.hidden = not visible

    def update(self, session: GameSession) -> None:
        config, ship = session.config, session.ship
        speed_fraction = min(1.0, ship.speed / (config.max_speed * config.boost_factor))
        self._elements["level"].textContent = f"{session.level_index + 1:02d} · {session.level.name.upper()}"
        self._elements["lives"].textContent = self.LIFE_ICON * session.lives
        self._elements["progress"].style.width = self._percent(session.progress)
        self._elements["speed-label"].textContent = f"SPEED {round(ship.speed * self.KMH_PER_UNIT):>3} KM/H"
        self._set_gauge("speed", speed_fraction, warn=False)
        self._set_gauge("fuel", session.fuel.fraction)
        self._set_gauge("oxygen", session.oxygen.fraction)

    def announce(self, events: list[GameEvent]) -> None:
        """Flashes a word naming the effect a block just had, in that block's colour."""
        callouts = [self.CALLOUTS[event] for event in events if event in self.CALLOUTS]
        if not callouts:
            return
        text, color = callouts[-1]
        callout = self._elements["callout"]
        callout.textContent = text
        callout.style.color = Palette.css(color)
        self._callout_left = self.CALLOUT_SECONDS
        self.fade(0.0)

    def fade(self, dt: float) -> None:
        """Fades the callout out, growing it slightly as it goes."""
        self._callout_left = max(0.0, self._callout_left - dt)
        life = self._callout_left / self.CALLOUT_SECONDS
        style = self._elements["callout"].style
        style.opacity = f"{min(1.0, life * 2.5):.2f}"
        style.transform = f"scale({1.25 - 0.25 * life:.3f})"

    def _set_gauge(self, name: str, fraction: float, warn: bool = True) -> None:
        self._elements[f"{name}-fill"].style.width = self._percent(fraction)
        self._elements[name].classList.toggle("low", warn and fraction < self.LOW)

    @staticmethod
    def _percent(fraction: float) -> str:
        return f"{max(0.0, min(1.0, fraction)) * 100:.1f}%"

    @property
    def container(self) -> Any:
        return self._container
