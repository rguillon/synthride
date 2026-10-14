from synthride.core.ship_input import ShipInput
from synthride.web.browser_keyboard import BrowserKeyboard
from tests.web.fakes.fake_js_bridge import FakeJsBridge
from tests.web.fakes.fake_key_event import FakeKeyEvent


def make_keyboard():
    bridge = FakeJsBridge()
    return bridge.window, BrowserKeyboard(bridge)


def test_held_keys_map_to_ship_input():
    window, keyboard = make_keyboard()
    for code in ("ArrowUp", "KeyA", "Space"):
        window.dispatch("keydown", FakeKeyEvent(code))
    assert keyboard.ship_input() == ShipInput(accelerate=True, left=True, jump=True)
    window.dispatch("keyup", FakeKeyEvent("KeyA"))
    window.dispatch("keydown", FakeKeyEvent("KeyD"))
    window.dispatch("keydown", FakeKeyEvent("ArrowDown"))
    assert keyboard.ship_input() == ShipInput(accelerate=True, brake=True, right=True, jump=True)


def test_game_keys_do_not_scroll_the_page():
    window, _ = make_keyboard()
    arrow, letter = FakeKeyEvent("ArrowDown"), FakeKeyEvent("KeyM")
    window.dispatch("keydown", arrow)
    window.dispatch("keydown", letter)
    assert arrow.prevented
    assert not letter.prevented


def test_presses_are_queued_once_without_auto_repeat():
    window, keyboard = make_keyboard()
    window.dispatch("keydown", FakeKeyEvent("Enter"))
    window.dispatch("keydown", FakeKeyEvent("Enter", repeat=True))
    assert keyboard.consume_presses() == ["Enter"]
    assert keyboard.consume_presses() == []


def test_losing_focus_releases_keys():
    window, keyboard = make_keyboard()
    window.dispatch("keydown", FakeKeyEvent("ArrowUp"))
    window.dispatch("blur")
    assert keyboard.ship_input() == ShipInput()
