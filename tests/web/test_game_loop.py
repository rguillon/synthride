# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

from types import SimpleNamespace

import pytest

from synthride.core.game_phase import GamePhase
from synthride.core.game_session import GameSession
from synthride.web.browser_keyboard import BrowserKeyboard
from synthride.web.game_loop import GameLoop
from synthride.web.hud import Hud
from synthride.web.menu_screen import MenuScreen
from synthride.web.neon_lines import NeonLines
from synthride.web.neon_sparks import NeonSparks
from synthride.web.scene_renderer import SceneRenderer
from synthride.web.ship_model import ShipModel
from synthride.web.sound_effects import SoundEffects
from synthride.web.space_backdrop import SpaceBackdrop
from synthride.web.synth_music import SynthMusic
from synthride.web.synth_voices import SynthVoices
from synthride.web.track_mesh_builder import TrackMeshBuilder
from tests.level_factory import make_level
from tests.web.fakes.fake_audio_context import FakeAudioContext
from tests.web.fakes.fake_js_bridge import FakeJsBridge
from tests.web.fakes.fake_js_object import FakeJsObject
from tests.web.fakes.fake_key_event import FakeKeyEvent

FLAT = "N1 N1 N1 N1 N1 N1 N1 N1"


@pytest.fixture
def game() -> SimpleNamespace:
    bridge = FakeJsBridge()
    levels = [make_level(*[FLAT] * 5, name=f"L{n}") for n in (1, 2)]
    context = FakeAudioContext()
    voices = SynthVoices(bridge, context, FakeJsObject("destination"))
    lines = NeonLines(bridge)
    renderer = SceneRenderer(bridge, bridge.document.getElementById("stage"), lines)
    loop = GameLoop(
        bridge,
        session=GameSession(levels),
        keyboard=BrowserKeyboard(bridge),
        renderer=renderer,
        track_builder=TrackMeshBuilder(bridge, lines),
        ship_model=ShipModel(bridge, lines),
        sparks=NeonSparks(bridge),
        backdrop=SpaceBackdrop(bridge),
        hud=Hud(bridge),
        menu=MenuScreen(bridge),
        music=SynthMusic(voices),
        sound_effects=SoundEffects(voices),
    )
    return SimpleNamespace(bridge=bridge, loop=loop, session=loop.session, context=context, renderer=renderer)


def press(game: SimpleNamespace, *codes: str) -> None:
    for code in codes:
        game.bridge.window.dispatch("keydown", FakeKeyEvent(code))
        game.bridge.window.dispatch("keyup", FakeKeyEvent(code))
    game.loop.tick(1 / 60)


def menu_html(game: SimpleNamespace) -> str:
    return game.bridge.document.getElementById("menu").innerHTML


def test_frames_keep_requesting_themselves(game: SimpleNamespace) -> None:
    window = game.bridge.window
    game.loop.start()
    window.frame_callbacks.pop()(1000.0)
    window.frame_callbacks.pop()(1016.0)
    assert len(window.frame_callbacks) == 1
    assert game.renderer.composer.render.calls == [(), ()]


def test_title_shows_menu_and_track(game: SimpleNamespace) -> None:
    game.loop.tick(0.016)
    assert "SYNTHRIDE" in menu_html(game)
    assert game.bridge.document.getElementById("hud").hidden
    assert len(game.renderer.scene.add.calls) == 7  # 2 lights, sky, dust, ship, sparks, track


def test_menu_navigation_to_playing_and_back(game: SimpleNamespace) -> None:
    press(game, "Enter")
    assert game.session.phase is GamePhase.LEVEL_SELECT
    assert game.context.resume.calls == [()]
    press(game, "ArrowDown")
    assert '<li class="selected">02' in menu_html(game)
    press(game, "ArrowUp", "ArrowUp")
    assert game.session.selected_level == 1
    press(game, "Enter")
    assert game.session.phase is GamePhase.PLAYING
    assert game.session.level_index == 1
    assert not game.bridge.document.getElementById("hud").hidden
    assert game.bridge.document.getElementById("menu").hidden
    assert len(game.renderer.scene.remove.calls) == 1  # level 1 track swapped for level 2
    press(game, "Escape")
    assert game.session.phase is GamePhase.LEVEL_SELECT
    press(game, "Escape")
    assert game.session.phase is GamePhase.TITLE


def test_level_select_left_and_right_change_column(game: SimpleNamespace) -> None:
    game.session.levels = game.session.levels * MenuScreen.LEVELS_PER_COLUMN
    press(game, "Enter", "ArrowDown", "ArrowRight")
    assert game.session.selected_level == MenuScreen.LEVELS_PER_COLUMN + 1
    press(game, "ArrowLeft")
    assert game.session.selected_level == 1


def test_each_level_brings_its_own_sky(game: SimpleNamespace) -> None:
    backdrop = game.loop._backdrop  # noqa: SLF001
    sky = backdrop._sky_material.uniforms  # noqa: SLF001
    game.loop.tick(1 / 60)
    first = sky.uNebula.value.setHex.calls[-1]
    press(game, "Enter", "ArrowDown", "Enter")
    assert sky.uNebula.value.setHex.calls[-1] != first


def test_level_select_ignores_other_keys(game: SimpleNamespace) -> None:
    press(game, "Enter", "KeyX")
    assert game.session.phase is GamePhase.LEVEL_SELECT
    assert game.session.selected_level == 0


def test_mute_toggle(game: SimpleNamespace) -> None:
    press(game, "KeyM")
    assert game.loop._music.muted  # noqa: SLF001


@pytest.mark.parametrize("phase", [GamePhase.GAME_OVER, GamePhase.VICTORY])
def test_end_screens_return_to_level_select(game: SimpleNamespace, phase: GamePhase) -> None:
    game.session.phase = phase
    game.loop.tick(0.016)
    assert "PRESS ENTER" in menu_html(game)
    press(game, "Enter")
    assert game.session.phase is GamePhase.LEVEL_SELECT


def play_until(game: SimpleNamespace, phase: GamePhase, *codes: str) -> None:
    for code in codes:
        game.bridge.window.dispatch("keydown", FakeKeyEvent(code))
    for _ in range(600):
        game.loop.tick(1 / 60)
        if game.session.phase is phase:
            return
    pytest.fail(f"never reached {phase}")


def test_level_won_banner(game: SimpleNamespace) -> None:
    game.session.start()
    play_until(game, GamePhase.LEVEL_WON, "ArrowUp")
    assert "LEVEL CLEAR" in menu_html(game)


def test_camera_freezes_while_dying(game: SimpleNamespace) -> None:
    game.session.start()
    play_until(game, GamePhase.DYING, "ArrowRight")
    calls = len(game.renderer.camera.position.set.calls)
    game.loop.tick(0.016)
    assert len(game.renderer.camera.position.set.calls) == calls
