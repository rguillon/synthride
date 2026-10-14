from synthride.core.game_event import GameEvent
from synthride.core.game_session import GameSession
from synthride.core.level_parser import LevelParser
from synthride.core.tile_type import TileType
from synthride.web.hud import Hud
from synthride.web.palette import Palette
from tests.web.fakes.fake_js_bridge import FakeJsBridge


def make_hud():
    bridge = FakeJsBridge()
    session = GameSession([LevelParser().parse("name: Grid Zero\n---\n" + "N1 " * 8 + "\n" + "N1 " * 8)])
    return bridge.document, Hud(bridge), session


def test_renders_layout_into_hud_container():
    document, hud, _ = make_hud()
    assert hud.container is document.getElementById("hud")
    assert 'id="hud-fuel-fill"' in hud.container.innerHTML


def test_update_shows_level_lives_and_gauges():
    document, hud, session = make_hud()
    session.fuel.drain(session.fuel.capacity / 2)
    session.oxygen.drain(session.oxygen.capacity * 0.9)
    hud.update(session)
    element = document.getElementById
    assert element("hud-level").textContent == "01 · GRID ZERO"
    assert element("hud-lives").textContent == Hud.LIFE_ICON * 3
    assert element("hud-fuel-fill").style.width == "50.0%"
    assert element("hud-speed-fill").style.width == "0.0%"
    assert element("hud-speed-label").textContent == "SPEED   0 KM/H"
    assert element("hud-oxygen").classList.contains("low")
    assert not element("hud-fuel").classList.contains("low")


def test_show_and_hide():
    _, hud, _ = make_hud()
    hud.show(False)
    assert hud.container.hidden
    hud.show(True)
    assert not hud.container.hidden


def test_announces_block_effects_then_fades_out():
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


def test_every_effect_event_has_a_callout():
    effects = {GameEvent.BOOSTED, GameEvent.SLOWED, GameEvent.REFUELED, GameEvent.REFILLED_AIR}
    effects |= {GameEvent.LAUNCHED, GameEvent.SKIDDED, GameEvent.PUSHED, GameEvent.BUMPED}
    assert set(Hud.CALLOUTS) == effects
