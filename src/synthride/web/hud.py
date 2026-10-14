from __future__ import annotations

from typing import Any

from synthride.core.game_session import GameSession
from synthride.web.js_bridge import JsBridge


class Hud:
    """The in-game overlay: level name, lives, progress, and speed / fuel / oxygen gauges."""

    LAYOUT = """
      <div class="hud-top">
        <span id="hud-level"></span>
        <span id="hud-lives" class="hud-lives"></span>
      </div>
      <div class="progress"><div id="hud-progress" class="progress-fill"></div></div>
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
    )
    LOW = 0.2
    LIFE_ICON = "▲"
    KMH_PER_UNIT = 20

    def __init__(self, bridge: JsBridge) -> None:
        document = bridge.document
        self._container = document.getElementById("hud")
        self._container.innerHTML = self.LAYOUT
        self._elements = {name: document.getElementById(f"hud-{name}") for name in self.ELEMENT_NAMES}

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

    def _set_gauge(self, name: str, fraction: float, warn: bool = True) -> None:
        self._elements[f"{name}-fill"].style.width = self._percent(fraction)
        self._elements[name].classList.toggle("low", warn and fraction < self.LOW)

    @staticmethod
    def _percent(fraction: float) -> str:
        return f"{max(0.0, min(1.0, fraction)) * 100:.1f}%"

    @property
    def container(self) -> Any:
        return self._container
