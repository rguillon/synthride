# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""The per-frame game loop."""

from __future__ import annotations

from typing import TYPE_CHECKING

from synthride.core.gameplay.game_event import GameEvent
from synthride.core.gameplay.game_phase import GamePhase
from synthride.web.rendering.scene_renderer import SceneRenderer
from synthride.web.rendering.space_scenery import SpaceScenery

if TYPE_CHECKING:
    from synthride.core.gameplay.game_session import GameSession
    from synthride.core.world.level import Level
    from synthride.web.audio.sound_effects import SoundEffects
    from synthride.web.audio.synth_music import SynthMusic
    from synthride.web.browser.browser_keyboard import BrowserKeyboard
    from synthride.web.browser.js_bridge import JsBridge, JsObject
    from synthride.web.rendering.neon_sparks import NeonSparks
    from synthride.web.rendering.ship_model import ShipModel
    from synthride.web.rendering.space_backdrop import SpaceBackdrop
    from synthride.web.track_meshes.track_mesh_builder import TrackMeshBuilder
    from synthride.web.ui.editor_screen import EditorScreen
    from synthride.web.ui.hud import Hud
    from synthride.web.ui.menu_screen import MenuScreen


class GameLoop:
    """Drives everything once per animation frame: menu keys, simulation, audio, visuals and overlays."""

    MAX_FRAME_SECONDS = 0.1
    CONFIRM = frozenset({"Enter", "Space"})
    UP = frozenset({"ArrowUp", "KeyW"})
    DOWN = frozenset({"ArrowDown", "KeyS"})
    LEFT = frozenset({"ArrowLeft", "KeyA"})
    RIGHT = frozenset({"ArrowRight", "KeyD"})
    HUD_PHASES = frozenset({GamePhase.PLAYING, GamePhase.DYING, GamePhase.LEVEL_WON})
    TAP_TO_GO_ON = frozenset({GamePhase.VICTORY})
    EDIT = "e"
    NEW = "n"
    MUTE = "m"
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
        editor: EditorScreen | None = None,
    ) -> None:
        """Wire the loop to the session and every browser-side component, the level editor if there is one."""
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
        self._editor = editor
        self._shown_level: Level | None = None
        self._track_group: JsObject = None
        self._last_timestamp: float | None = None
        self._time = 0.0
        self.paused = False
        self._music_started = False
        self._frame_proxy = bridge.proxy(self.on_frame)
        bridge.window.addEventListener("blur", bridge.proxy(lambda _event: self.pause()))
        bridge.document.addEventListener("visibilitychange", bridge.proxy(self.on_visibility_change))
        backdrop.add_to(renderer.scene)
        renderer.add(ship_model.group)
        renderer.mirror(ship_model.body)  # not the shadow: it would hide the mirror image
        renderer.add(sparks.points)
        if editor is not None:
            for item in editor.objects:
                renderer.add(item)

    def start(self) -> None:
        """Request the first animation frame."""
        self._bridge.window.requestAnimationFrame(self._frame_proxy)

    def on_frame(self, timestamp: float) -> None:
        """Advance by the time since the last frame, then request the next one."""
        dt = 0.0 if self._last_timestamp is None else (timestamp - self._last_timestamp) / 1000
        self._last_timestamp = timestamp
        self.tick(min(max(dt, 0.0), self.MAX_FRAME_SECONDS))
        self._bridge.window.requestAnimationFrame(self._frame_proxy)

    def on_visibility_change(self, _event: JsObject) -> None:
        """Pause when the page is hidden: another tab, or the phone's screen off."""
        if self._bridge.document.visibilityState == "hidden":
            self.pause()

    def pause(self) -> None:
        """Freeze the ride, if one is on, behind the pause screen, and release the keys held."""
        if self.paused or self.session.phase not in (GamePhase.PLAYING, GamePhase.DYING):
            return
        self.paused = True
        self._keyboard.release_all()
        self._music.pause()

    def resume(self) -> None:
        """Go on with a paused ride."""
        if self.paused:
            self.paused = False
            self._music.resume()

    def leave(self) -> None:
        """Quit a paused ride, back to the editor it was started from or to the level select."""
        self.resume()
        if self.session.riding:
            self.session.open_editor()
        else:
            self.session.open_level_select()

    def tick(self, dt: float) -> None:
        """Advance the whole game by ``dt`` seconds and render a frame, or only redraw while paused."""
        session = self.session
        for key in self._keyboard.consume_presses():
            self.handle_key(key)
        for tap in self._menu.consume_taps():
            self.handle_tap(tap)
        if self.paused:
            self._update_overlays()
            self._renderer.render()
            return
        self._time += dt
        self._handle_editor_actions()
        events = session.update(dt, self._keyboard.ship_input())
        self._sound_effects.play(events)
        self._renderer.react(events)
        self._sparks.react(events, session.ship)
        self._sparks.update(dt)
        self._hud.announce(events)
        self._hud.fade(dt)
        self._hud.count_frame(dt)
        self._music.update()
        editor = self._editor if session.phase is GamePhase.EDITOR else None
        snap = self._show_level(session.level if editor is None else editor.level)
        snap = snap or GameEvent.LEVEL_STARTED in events
        self._ship_model.sync(session.ship, session.phase, dt)
        self._ship_model.group.visible = editor is None
        if editor is not None:
            editor.update(dt)
            self._renderer.overlook(*editor.focus)
        elif session.phase is not GamePhase.DYING:
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
        """React to a fresh key press in the menus. The first one starts the music: browsers wait for a gesture."""
        session, phase = self.session, self.session.phase
        self._start_music()
        letter = self._keyboard.letter(key)
        if letter == self.MUTE:
            self._music.toggle_mute()
        elif self.paused:
            self._handle_pause_key(key)
        elif phase is GamePhase.EDITOR and self._editor is not None:
            self._editor.handle_key(key, letter)
        elif letter in (self.EDIT, self.NEW) and phase is GamePhase.LEVEL_SELECT and self._editor is not None:
            self._open_editor(self._editor, selected=letter == self.EDIT)
        elif phase in (GamePhase.PLAYING, GamePhase.DYING) and key == "Escape":
            self.pause()
        elif phase is GamePhase.LEVEL_SELECT:
            self._handle_level_select_key(key)
        elif phase is GamePhase.VICTORY and key in self.CONFIRM:
            session.open_level_select()

    def _start_music(self) -> None:
        if not self._music_started:
            self._music_started = True
            self._music.start()

    def _handle_pause_key(self, key: str) -> None:
        if key in ("Escape", "Enter"):
            self.resume()
        elif key == "Backspace":
            self.leave()

    def handle_tap(self, tap: int | str) -> None:
        """React to a tap on the menus, as the key it stands for: a level rides it, back is Escape, else Enter."""
        session, phase = self.session, self.session.phase
        self._start_music()
        if self.paused:
            if tap == self._menu.RESUME:
                self.resume()
            elif tap == self._menu.MAIN_MENU:
                self.leave()
        elif phase is GamePhase.LEVEL_SELECT:
            if isinstance(tap, int) and 0 <= tap < len(session.levels):
                session.selected_level = tap
                self.handle_key("Enter")
        elif phase in self.TAP_TO_GO_ON and tap == self._menu.ANYWHERE:
            self.handle_key("Enter")

    def _open_editor(self, editor: EditorScreen, *, selected: bool) -> None:
        """Open the editor on the level selected in the level select, or else on the last track it had."""
        session = self.session
        if selected:
            index = session.selected_level
            editor.open_level(session.levels[index], index)
        session.open_editor()

    def _handle_editor_actions(self) -> None:
        if self._editor is None:
            return
        session = self.session
        for action in self._editor.consume_actions():
            if session.phase is not GamePhase.EDITOR:
                continue
            if action == self._editor.RIDE:
                self._sound_effects.play(session.ride(self._editor.level))
            else:  # BACK
                if self._editor.index is not None:
                    session.selected_level = self._editor.index
                session.open_level_select()

    def _handle_level_select_key(self, key: str) -> None:
        session = self.session
        if key in self.UP:
            session.select_previous_level()
        elif key in self.DOWN:
            session.select_next_level()
        elif key in self.LEFT:
            session.select_level_column(-1, self._menu.LEVELS_PER_COLUMN)
        elif key in self.RIGHT:
            session.select_level_column(1, self._menu.LEVELS_PER_COLUMN)
        elif key in self.CONFIRM:
            self._sound_effects.play(session.start())

    def _show_level(self, level: Level) -> bool:
        """Rebuilds the track meshes and redresses the sky when ``level`` is not the one shown. Returns True if so."""
        if level is self._shown_level:
            return False
        if self._track_group is not None:
            self._renderer.remove(self._track_group)
        self._track_group = self._track_builder.build(level.track)
        self._renderer.add(self._track_group)
        self._backdrop.show(SpaceScenery.for_level(self.session.level_index))
        self._shown_level = level
        return True

    def _update_overlays(self) -> None:
        session, phase = self.session, self.session.phase
        self._hud.show(visible=phase in self.HUD_PHASES)
        if phase in self.HUD_PHASES:
            self._hud.update(session)
        if self.paused:
            self._menu.show_pause(riding=session.riding)
            return
        match phase:
            case GamePhase.LEVEL_SELECT:
                names = [level.name for level in session.levels]
                self._menu.show_level_select(names, session.selected_level, editor=self._editor is not None)
            case GamePhase.LEVEL_WON:
                self._menu.show_level_won(session.level.name)
            case GamePhase.VICTORY:
                self._menu.show_victory()
            case _:
                self._menu.hide()
        if self._editor is not None:
            if phase is GamePhase.EDITOR:
                self._editor.show()
            else:
                self._editor.hide()
