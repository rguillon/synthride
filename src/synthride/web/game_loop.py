# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""The per-frame game loop."""

from __future__ import annotations

from typing import TYPE_CHECKING

from synthride.core.game_event import GameEvent
from synthride.core.game_phase import GamePhase
from synthride.web.scene_renderer import SceneRenderer

if TYPE_CHECKING:
    from synthride.core.game_session import GameSession
    from synthride.core.level import Level
    from synthride.web.browser_keyboard import BrowserKeyboard
    from synthride.web.hud import Hud
    from synthride.web.js_bridge import JsBridge, JsObject
    from synthride.web.menu_screen import MenuScreen
    from synthride.web.neon_sparks import NeonSparks
    from synthride.web.ship_model import ShipModel
    from synthride.web.sound_effects import SoundEffects
    from synthride.web.space_backdrop import SpaceBackdrop
    from synthride.web.synth_music import SynthMusic
    from synthride.web.track_mesh_builder import TrackMeshBuilder


class GameLoop:
    """Drives everything once per animation frame: menu keys, simulation, audio, visuals and overlays."""

    MAX_FRAME_SECONDS = 0.1
    CONFIRM = frozenset({"Enter", "Space"})
    UP = frozenset({"ArrowUp", "KeyW"})
    DOWN = frozenset({"ArrowDown", "KeyS"})
    HUD_PHASES = frozenset({GamePhase.PLAYING, GamePhase.DYING, GamePhase.LEVEL_WON})
    # The stretch of track whose tunnel roofs the chase camera ducks under: from where it sits behind
    # the ship to a little ahead, so it is already low when the ship enters a tunnel.
    CAMERA_REACH_BEHIND = SceneRenderer.CAMERA_DISTANCE + 0.5
    CAMERA_REACH_AHEAD = 5.0

    def __init__(  # noqa: PLR0913
        self,
        bridge: JsBridge,
        *,
        session: GameSession,
        keyboard: BrowserKeyboard,
        renderer: SceneRenderer,
        track_builder: TrackMeshBuilder,
        ship_model: ShipModel,
        sparks: NeonSparks,
        backdrop: SpaceBackdrop,
        hud: Hud,
        menu: MenuScreen,
        music: SynthMusic,
        sound_effects: SoundEffects,
    ) -> None:
        """Wire the loop to the session and every browser-side component."""
        self._bridge = bridge
        self.session = session
        self._keyboard = keyboard
        self._renderer = renderer
        self._track_builder = track_builder
        self._ship_model = ship_model
        self._sparks = sparks
        self._hud = hud
        self._menu = menu
        self._music = music
        self._sound_effects = sound_effects
        self._backdrop = backdrop
        self._shown_level: Level | None = None
        self._track_group: JsObject = None
        self._last_timestamp: float | None = None
        self._time = 0.0
        self._frame_proxy = bridge.proxy(self.on_frame)
        backdrop.add_to(renderer.scene)
        renderer.add(ship_model.group)
        renderer.mirror(ship_model.body, ship_model.explosion)  # not the shadow: it would hide the mirror image
        renderer.add(sparks.points)

    def start(self) -> None:
        """Request the first animation frame."""
        self._bridge.window.requestAnimationFrame(self._frame_proxy)

    def on_frame(self, timestamp: float) -> None:
        """Advance by the time since the last frame, then request the next one."""
        dt = 0.0 if self._last_timestamp is None else (timestamp - self._last_timestamp) / 1000
        self._last_timestamp = timestamp
        self.tick(min(max(dt, 0.0), self.MAX_FRAME_SECONDS))
        self._bridge.window.requestAnimationFrame(self._frame_proxy)

    def tick(self, dt: float) -> None:
        """Advance the whole game by ``dt`` seconds and render a frame."""
        self._time += dt
        session = self.session
        for key in self._keyboard.consume_presses():
            self.handle_key(key)
        events = session.update(dt, self._keyboard.ship_input())
        self._sound_effects.play(events)
        self._renderer.react(events)
        self._sparks.react(events, session.ship)
        self._sparks.update(dt)
        self._hud.announce(events)
        self._hud.fade(dt)
        self._hud.count_frame(dt)
        self._music.update()
        snap = self._show_current_level() or GameEvent.LEVEL_STARTED in events
        self._ship_model.sync(session.ship, session.phase, dt)
        if session.phase is not GamePhase.DYING:
            ship = session.ship
            speed_fraction = ship.speed / session.config.max_speed
            ceiling = session.level.track.ceiling_over(
                ship.position.x, ship.position.z - self.CAMERA_REACH_BEHIND, ship.position.z + self.CAMERA_REACH_AHEAD
            )
            self._renderer.follow(ship, min(speed_fraction, 1.3), dt, snap=snap, ceiling=ceiling)
            self._renderer.reflect_on(ship, session.level.track.surface_height_at(ship.position.x, ship.position.z))
        self._backdrop.update(self._renderer.camera_z, self._time)
        self._track_builder.animate(self._time)
        self._update_overlays()
        self._renderer.render()

    def handle_key(self, key: str) -> None:
        """React to a fresh key press in the menus."""
        session, phase = self.session, self.session.phase
        if key == "KeyM":
            self._music.toggle_mute()
        elif phase is GamePhase.TITLE and key in self.CONFIRM:
            self._music.start()
            session.open_level_select()
        elif phase is GamePhase.LEVEL_SELECT:
            if key in self.UP:
                session.select_previous_level()
            elif key in self.DOWN:
                session.select_next_level()
            elif key in self.CONFIRM:
                self._sound_effects.play(session.start())
            elif key == "Escape":
                session.return_to_title()
        elif (phase in (GamePhase.PLAYING, GamePhase.DYING) and key == "Escape") or (
            phase in (GamePhase.GAME_OVER, GamePhase.VICTORY) and key in self.CONFIRM
        ):
            session.open_level_select()

    def _show_current_level(self) -> bool:
        """Rebuilds the track meshes when the level changes. Returns True when it did."""
        level = self.session.level
        if level is self._shown_level:
            return False
        if self._track_group is not None:
            self._renderer.remove(self._track_group)
        self._track_group = self._track_builder.build(level.track)
        self._renderer.add(self._track_group)
        self._shown_level = level
        return True

    def _update_overlays(self) -> None:
        session, phase = self.session, self.session.phase
        self._hud.show(visible=phase in self.HUD_PHASES)
        if phase in self.HUD_PHASES:
            self._hud.update(session)
        match phase:
            case GamePhase.TITLE:
                self._menu.show_title()
            case GamePhase.LEVEL_SELECT:
                self._menu.show_level_select([level.name for level in session.levels], session.selected_level)
            case GamePhase.LEVEL_WON:
                self._menu.show_level_won(session.level.name)
            case GamePhase.GAME_OVER:
                self._menu.show_game_over()
            case GamePhase.VICTORY:
                self._menu.show_victory()
            case _:
                self._menu.hide()
