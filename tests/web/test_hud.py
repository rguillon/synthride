# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

from synthride.core.game_event import GameEvent
from synthride.core.game_session import GameSession
from synthride.core.tile_type import TileType
from synthride.web.hud import Hud
from synthride.web.palette import Palette
from tests.level_factory import make_level
from tests.web.fakes.fake_document import FakeDocument
from tests.web.fakes.fake_js_bridge import FakeJsBridge


def make_hud() -> tuple[FakeDocument, Hud, GameSession]:
    bridge = FakeJsBridge()
    session = GameSession([make_level("N1 " * 8, "N1 " * 8, name="Grid Zero")])
    return bridge.document, Hud(bridge), session


def test_renders_layout_into_hud_container() -> None:
    document, hud, _ = make_hud()
    assert hud.container is document.getElementById("hud")
    assert 'id="hud-fuel-fill"' in hud.container.innerHTML


def test_update_shows_level_lives_and_gauges() -> None:
    document, hud, session = make_hud()
    session.fuel.drain(session.fuel.capacity / 2)
    session.oxygen.drain(session.oxygen.capacity * 0.9)
    hud.update(session)
    element = document.getElementById
    assert element("hud-level").textContent == "01 · GRID ZERO"
    assert element("hud-lives").textContent == Hud.LIFE_ICON * 3
    assert element("hud-fuel-fill").style.transform == "scaleX(0.500)"
    assert element("hud-speed-fill").style.transform == "scaleX(0.000)"
    assert element("hud-speed-label").textContent == "SPEED   0 KM/H"
    assert element("hud-oxygen").classList.contains("low")
    assert not element("hud-fuel").classList.contains("low")


def test_show_and_hide() -> None:
    _, hud, _ = make_hud()
    hud.show(visible=False)
    assert hud.container.hidden
    hud.show(visible=True)
    assert not hud.container.hidden


def test_announces_block_effects_then_fades_out() -> None:
    document, hud, _ = make_hud()
    callout = document.getElementById("hud-callout")
    hud.announce([GameEvent.LANDED])
    assert callout.textContent == ""
    hud.announce([GameEvent.LANDED, GameEvent.BOOSTED])
    assert callout.textContent == "BOOST"
    assert callout.style.color == Palette.css(Palette.tile_color(TileType.BOOST))
    assert callout.style.opacity == "1.00"
    hud.fade(Hud.CALLOUT_SECONDS)
    assert callout.style.opacity == "0.00"


def test_every_effect_event_has_a_callout() -> None:
    effects = {GameEvent.BOOSTED, GameEvent.SLOWED, GameEvent.REFUELED, GameEvent.REFILLED_AIR}
    effects |= {GameEvent.LAUNCHED, GameEvent.SKIDDED, GameEvent.PUSHED, GameEvent.BUMPED}
    assert set(Hud.CALLOUTS) == effects


def test_counts_frames_into_a_frame_rate_readout() -> None:
    document, hud, _ = make_hud()
    fps = document.getElementById("hud-fps")
    for _ in range(31):
        hud.count_frame(1 / 64)
    assert fps.textContent == ""
    hud.count_frame(1 / 64)
    assert fps.textContent == "64 FPS"


def test_a_test_ride_is_labelled_as_such() -> None:
    document, hud, session = make_hud()
    session.ride(make_level("N1 " * 8, name="Mine"))
    hud.update(session)
    assert document.getElementById("hud-level").textContent == "TEST RIDE · MINE"
