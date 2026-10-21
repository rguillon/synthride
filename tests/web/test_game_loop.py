# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

from types import SimpleNamespace

import pytest

from synthride.core.gameplay.game_phase import GamePhase
from synthride.core.gameplay.game_session import GameSession
from synthride.editor.track_grid import Brush, BrushKind, Rect
from synthride.web.audio.sound_effects import SoundEffects
from synthride.web.audio.synth_music import SynthMusic
from synthride.web.audio.synth_voices import SynthVoices
from synthride.web.browser.browser_keyboard import BrowserKeyboard
from synthride.web.game_loop import GameLoop
from synthride.web.rendering.neon_lines import NeonLines
from synthride.web.rendering.neon_sparks import NeonSparks
from synthride.web.rendering.scene_renderer import SceneRenderer
from synthride.web.rendering.ship_model import ShipModel
from synthride.web.rendering.space_backdrop import SpaceBackdrop
from synthride.web.track_meshes.track_mesh_builder import TrackMeshBuilder
from synthride.web.ui.editor_screen import EditorScreen
from synthride.web.ui.hud import Hud
from synthride.web.ui.menu_screen import MenuScreen
from tests.level_factory import make_level
from tests.web.fakes.fake_audio_context import FakeAudioContext
from tests.web.fakes.fake_element import FakeElement
from tests.web.fakes.fake_fetch import FakeFetch
from tests.web.fakes.fake_js_bridge import FakeJsBridge
from tests.web.fakes.fake_js_object import FakeJsObject
from tests.web.fakes.fake_key_event import FakeKeyEvent

FLAT = "N1 N1 N1 N1 N1 N1 N1 N1"


@pytest.fixture
def game() -> SimpleNamespace:
    return build_game()


@pytest.fixture
def edited() -> SimpleNamespace:
    return build_game(with_editor=True)


def build_game(*, with_editor: bool = False) -> SimpleNamespace:
    bridge = FakeJsBridge()
    levels = [make_level(*[FLAT] * 5, name=f"L{n}") for n in (1, 2)]
    context = FakeAudioContext()
    voices = SynthVoices(bridge, context, FakeJsObject("destination"))
    lines = NeonLines(bridge)
    renderer = SceneRenderer(bridge, bridge.document.getElementById("stage"), lines)
    bridge.window.fetch = FakeFetch()
    session = GameSession(levels)
    files = ["level_01.json", "level_02.json"]
    editor = None
    if with_editor:
        editor = EditorScreen(bridge, FakeJsObject("canvas"), renderer.camera, files, session.put_level)
    loop = GameLoop(
        bridge,
        session=session,
        keyboard=BrowserKeyboard(bridge),
        renderer=renderer,
        track_builder=TrackMeshBuilder(bridge, lines),
        ship_model=ShipModel(bridge, lines),
        sparks=NeonSparks(bridge),
        backdrop=SpaceBackdrop(bridge),
        hud=Hud(bridge),
        menu=MenuScreen(bridge, editor=with_editor),
        music=SynthMusic(voices),
        sound_effects=SoundEffects(voices),
        editor=editor,
    )
    return SimpleNamespace(
        bridge=bridge, loop=loop, session=loop.session, context=context, renderer=renderer, editor=editor
    )


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
    assert '<li class="selected" data-level="1">02' in menu_html(game)
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


def tap(game: SimpleNamespace, target: FakeElement) -> None:
    game.bridge.document.getElementById("menu").dispatch("click", SimpleNamespace(target=target))
    game.loop.tick(1 / 60)


def test_taps_walk_the_menus(game: SimpleNamespace) -> None:
    tap(game, FakeElement())
    assert game.session.phase is GamePhase.LEVEL_SELECT
    assert game.context.resume.calls == [()]
    tap(game, FakeElement(tag="button", back=""))
    assert game.session.phase is GamePhase.TITLE
    tap(game, FakeElement())
    tap(game, FakeElement(tag="li", level="1"))
    assert game.session.phase is GamePhase.PLAYING
    assert game.session.level_index == 1


@pytest.mark.parametrize("phase", [GamePhase.GAME_OVER, GamePhase.VICTORY])
def test_a_tap_on_an_end_screen_opens_the_level_select(game: SimpleNamespace, phase: GamePhase) -> None:
    game.session.phase = phase
    tap(game, FakeElement())
    assert game.session.phase is GamePhase.LEVEL_SELECT


def test_taps_out_of_place_are_ignored(game: SimpleNamespace) -> None:
    tap(game, FakeElement())  # level select
    tap(game, FakeElement(tag="li", level="9"))  # no such level
    tap(game, FakeElement())  # anywhere on the level select
    assert game.session.phase is GamePhase.LEVEL_SELECT
    assert game.session.selected_level == 0
    game.session.start()
    tap(game, FakeElement())  # a stray tap while riding
    assert game.session.phase is GamePhase.PLAYING


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


def editor_element(game: SimpleNamespace) -> FakeElement:
    return game.bridge.document.getElementById("editor")


def test_without_an_editor_e_does_nothing(game: SimpleNamespace) -> None:
    press(game, "KeyE")
    assert game.session.phase is GamePhase.TITLE


def test_e_on_the_title_opens_the_editor_over_its_track(edited: SimpleNamespace) -> None:
    edited.loop.tick(1 / 60)
    assert "E level editor" in menu_html(edited)
    press(edited, "KeyE")
    assert edited.session.phase is GamePhase.EDITOR
    assert edited.bridge.document.getElementById("menu").hidden
    assert not editor_element(edited).hidden
    assert edited.bridge.document.getElementById("hud").hidden
    assert edited.loop._shown_level is edited.editor.level  # noqa: SLF001
    assert not edited.loop._ship_model.group.visible  # noqa: SLF001
    assert edited.editor.cursor in [call[0] for call in edited.renderer.scene.add.calls]
    press(edited, "Escape")
    assert edited.session.phase is GamePhase.LEVEL_SELECT
    assert editor_element(edited).hidden
    assert edited.loop._ship_model.group.visible  # noqa: SLF001


def test_editor_keys_go_to_the_editor(edited: SimpleNamespace) -> None:
    press(edited, "KeyE", "Digit4")
    assert edited.editor.height == 4
    press(edited, "KeyM")
    assert edited.loop._music.muted  # noqa: SLF001


def test_a_test_ride_returns_to_the_editor(edited: SimpleNamespace) -> None:
    press(edited, "KeyE", "KeyT")
    session = edited.session
    assert session.phase is GamePhase.PLAYING
    assert session.riding
    assert session.level is edited.editor.level
    assert not edited.bridge.document.getElementById("hud").hidden
    assert editor_element(edited).hidden
    press(edited, "Escape")
    assert session.phase is GamePhase.EDITOR
    assert not editor_element(edited).hidden


def test_e_on_the_level_select_edits_the_selected_level(edited: SimpleNamespace) -> None:
    press(edited, "Enter", "ArrowDown", "KeyE")
    assert edited.editor.settings.name == "L2"
    assert edited.editor.grid.length == 5
    assert edited.editor.file == "level_02.json"


def test_saved_levels_join_the_level_select(edited: SimpleNamespace) -> None:
    press(edited, "KeyE")
    edited.editor.on_change(
        SimpleNamespace(target=SimpleNamespace(dataset=SimpleNamespace(field="name"), value="Mine"))
    )
    edited.editor.act("save")
    edited.bridge.window.fetch.answer()
    press(edited, "Escape")
    assert [level.name for level in edited.session.levels] == ["L1", "L2", "Mine"]
    assert edited.session.selected_level == 2
    assert "MINE" in menu_html(edited)
    assert "E edit" in menu_html(edited)
    press(edited, "KeyE")
    assert edited.editor.file == "level_03.json"
    assert edited.editor.settings.name == "Mine"


def test_editor_actions_outside_the_editor_are_dropped(edited: SimpleNamespace) -> None:
    edited.editor.act(EditorScreen.RIDE)
    edited.loop.tick(1 / 60)
    assert edited.session.phase is GamePhase.TITLE


def test_letter_keys_follow_the_layout(edited: SimpleNamespace) -> None:
    window = edited.bridge.window
    window.dispatch("keydown", FakeKeyEvent("Semicolon", key="m"))
    window.dispatch("keydown", FakeKeyEvent("KeyE", key="e"))
    edited.loop.tick(1 / 60)
    assert edited.loop._music.muted  # noqa: SLF001
    assert edited.session.phase is GamePhase.EDITOR
    edited.editor.grid.paint(Rect(0, 0, 0, 0), Brush(BrushKind.TILE, "I"))
    window.dispatch("keydown", FakeKeyEvent("KeyW", key="z"))
    edited.loop.tick(1 / 60)
    assert not edited.editor.grid.can_undo
