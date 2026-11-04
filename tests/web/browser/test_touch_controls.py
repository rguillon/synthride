# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

from types import SimpleNamespace

from synthride.core.gameplay.ship_input import ShipInput
from synthride.web.browser.browser_keyboard import BrowserKeyboard
from synthride.web.browser.touch_controls import TouchControls
from tests.web.fakes.fake_element import FakeElement
from tests.web.fakes.fake_js_bridge import FakeJsBridge
from tests.web.fakes.fake_js_null import JS_NULL
from tests.web.fakes.fake_pointer_event import FakePointerEvent

CODES = ("ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "Space")  # the arrows are pads of their own in tests


def make_touch() -> SimpleNamespace:
    bridge = FakeJsBridge()
    keyboard = BrowserKeyboard(bridge)
    t = SimpleNamespace(bridge=bridge, keyboard=keyboard, unlocks=0)

    def unlock() -> None:
        t.unlocks += 1

    t.touch = TouchControls(bridge, keyboard, unlock)
    t.pads = {code: FakeElement(tag="button", code=code) for code in CODES}
    return t


def dispatch(t: SimpleNamespace, event_type: str, code: str, pointer_id: int) -> FakePointerEvent:
    event = FakePointerEvent(t.pads[code], pointer_id)
    if event_type in ("pointerup", "pointercancel"):  # they bubble up to the window, which listens for them
        t.bridge.window.dispatch(event_type, event)
    else:
        t.bridge.document.getElementById("touch").dispatch(event_type, event)
    return event


def down(t: SimpleNamespace, code: str, pointer_id: int) -> FakePointerEvent:
    return dispatch(t, "pointerdown", code, pointer_id)


def up(t: SimpleNamespace, code: str, pointer_id: int) -> FakePointerEvent:
    return dispatch(t, "pointerup", code, pointer_id)


def test_the_first_touch_turns_touch_mode_on() -> None:
    t = make_touch()
    assert not t.touch.active
    t.bridge.window.dispatch("touchstart")
    assert t.bridge.document.body.classList.contains("touch")
    assert t.touch.active
    t.bridge.window.dispatch("touchstart")  # later touches change nothing
    assert t.touch.active


def test_full_screen_is_asked_for_once_on_a_touchend() -> None:
    t = make_touch()  # browsers only grant it inside a gesture's end, not its start
    t.bridge.window.dispatch("touchstart")
    assert t.bridge.document.documentElement.fullscreen_requests == 0
    t.bridge.window.dispatch("touchend")
    t.bridge.window.dispatch("touchend")
    assert t.bridge.document.documentElement.fullscreen_requests == 1


def test_every_touchend_unlocks_audio() -> None:
    t = make_touch()  # iOS suspends audio again when the app is left
    t.bridge.window.dispatch("touchend")
    t.bridge.window.dispatch("touchend")
    assert t.unlocks == 2


def test_pads_hold_their_keys_while_pressed() -> None:
    t = make_touch()
    event = down(t, "ArrowLeft", 1)
    assert event.prevented
    assert t.pads["ArrowLeft"].released == [1]
    assert t.keyboard.ship_input() == ShipInput(left=True)
    assert t.pads["ArrowLeft"].classList.contains("held")
    up(t, "ArrowLeft", 1)
    assert t.keyboard.ship_input() == ShipInput()
    assert not t.pads["ArrowLeft"].classList.contains("held")


def test_two_pointers_hold_two_pads() -> None:
    t = make_touch()
    down(t, "ArrowRight", 1)
    down(t, "Space", 2)
    assert t.keyboard.ship_input() == ShipInput(right=True, jump=True)
    up(t, "Space", 2)
    assert t.keyboard.ship_input() == ShipInput(right=True)


def test_a_code_stays_held_while_another_pointer_holds_it() -> None:
    t = make_touch()
    down(t, "ArrowUp", 1)
    down(t, "ArrowUp", 2)
    up(t, "ArrowUp", 1)
    assert t.keyboard.ship_input() == ShipInput(accelerate=True)
    assert t.pads["ArrowUp"].classList.contains("held")
    up(t, "ArrowUp", 2)
    assert t.keyboard.ship_input() == ShipInput()


def test_sliding_a_thumb_moves_the_hold_to_the_next_pad() -> None:
    t = make_touch()
    down(t, "ArrowLeft", 1)
    dispatch(t, "pointerout", "ArrowLeft", 1)
    dispatch(t, "pointerover", "ArrowRight", 1)
    assert t.keyboard.ship_input() == ShipInput(right=True)
    dispatch(t, "pointerover", "ArrowUp", 7)  # a pointer that is not down holds nothing
    assert t.keyboard.ship_input() == ShipInput(right=True)


def test_each_jump_tap_is_a_fresh_press() -> None:
    t = make_touch()
    down(t, "Space", 1)
    up(t, "Space", 1)
    down(t, "Space", 1)
    assert t.keyboard.consume_presses() == ["Space", "Space"]


def test_cancel_and_hidden_page_release_everything() -> None:
    t = make_touch()
    down(t, "ArrowLeft", 1)
    dispatch(t, "pointercancel", "ArrowLeft", 1)
    assert t.keyboard.ship_input() == ShipInput()
    down(t, "ArrowRight", 2)
    t.bridge.document.visibilityState = "hidden"
    t.bridge.document.dispatch("visibilitychange")
    assert t.keyboard.ship_input() == ShipInput()
    assert not t.pads["ArrowRight"].classList.contains("held")
    dispatch(t, "pointerover", "ArrowUp", 2)  # the pointer was forgotten
    assert t.keyboard.ship_input() == ShipInput()


def test_a_page_shown_again_keeps_what_is_held() -> None:
    t = make_touch()
    down(t, "ArrowLeft", 1)
    t.bridge.document.dispatch("visibilitychange")
    assert t.keyboard.ship_input() == ShipInput(left=True)


def test_menu_and_mute_buttons_press_their_keys() -> None:
    t = make_touch()
    for code in ("Escape", "KeyM"):
        t.bridge.document.body.dispatch("click", SimpleNamespace(target=FakeElement(tag="button", press=code)))
    t.bridge.document.body.dispatch("click", SimpleNamespace(target=FakeElement()))
    assert t.keyboard.consume_presses() == ["Escape", "KeyM"]


def test_touches_off_the_pads_do_nothing() -> None:
    t = make_touch()
    element = t.bridge.document.getElementById("touch")
    for event_type in ("pointerdown", "pointerover", "pointerout"):
        element.dispatch(event_type, FakePointerEvent(FakeElement(), 1))
    t.bridge.window.dispatch("pointerup", FakePointerEvent(FakeElement(), 1))
    assert t.keyboard.ship_input() == ShipInput()
    assert t.keyboard.consume_presses() == []


def test_pads_are_told_apart_by_their_code_not_their_proxy() -> None:
    t = make_touch()  # Pyodide hands each event a new proxy for the same element
    element = t.bridge.document.getElementById("touch")
    element.dispatch("pointerdown", FakePointerEvent(FakeElement(tag="button", code="ArrowUp"), 1))
    element.dispatch("pointerdown", FakePointerEvent(FakeElement(tag="button", code="ArrowUp"), 2))
    t.bridge.window.dispatch("pointerup", FakePointerEvent(FakeElement(tag="button", code="ArrowUp"), 1))
    assert t.keyboard.ship_input() == ShipInput(accelerate=True)


def test_a_finger_lifted_off_the_pads_still_releases_its_pad() -> None:
    t = make_touch()  # the menu can cover the pads before the finger is lifted
    down(t, "ArrowUp", 1)
    t.bridge.window.dispatch("pointerup", FakePointerEvent(FakeElement("menu"), 1))
    assert t.keyboard.ship_input() == ShipInput()
    assert not t.pads["ArrowUp"].classList.contains("held")


def test_losing_focus_forgets_the_pointers() -> None:
    t = make_touch()
    down(t, "ArrowLeft", 1)
    t.bridge.window.dispatch("blur")
    assert not t.pads["ArrowLeft"].classList.contains("held")
    down(t, "ArrowLeft", 2)  # no stale pointer keeps the pad held after this one is lifted
    up(t, "ArrowLeft", 2)
    assert t.keyboard.ship_input() == ShipInput()


def make_stick() -> tuple[SimpleNamespace, FakeElement]:
    t = make_touch()
    stick = FakeElement(tag="div", stick="")  # a 100 px wide joystick whose center is at (50, 50)
    return t, stick


def stick_event(
    t: SimpleNamespace, stick: FakeElement, event_type: str, point: tuple[float, float], pointer_id: int = 1
) -> None:
    event = FakePointerEvent(stick, pointer_id, *point)
    target = t.bridge.window if event_type != "pointerdown" else t.bridge.document.getElementById("touch")
    target.dispatch(event_type, event)


def test_the_stick_holds_the_arrows_it_points_at() -> None:
    t, stick = make_stick()
    expected = {
        (50, 5): ShipInput(accelerate=True),
        (50, 95): ShipInput(brake=True),
        (5, 50): ShipInput(left=True),
        (95, 50): ShipInput(right=True),
        (80, 20): ShipInput(accelerate=True, right=True),
        (20, 80): ShipInput(brake=True, left=True),
        (50, 55): ShipInput(),  # the dead zone around the center
    }
    stick_event(t, stick, "pointerdown", (50, 50))
    for (x, y), ship_input in expected.items():
        stick_event(t, stick, "pointermove", (x, y))
        assert t.keyboard.ship_input() == ship_input, (x, y)


def test_the_stick_follows_the_thumb_and_lets_go() -> None:
    t, stick = make_stick()
    stick_event(t, stick, "pointerdown", (50, 50))
    assert stick.classList.contains("held")
    stick_event(t, stick, "pointermove", (250, 50))
    assert stick.knob.style.transform == "translate(50.0px, 0.0px)"  # the knob stays on the ring
    assert t.keyboard.ship_input() == ShipInput(right=True)
    stick_event(t, stick, "pointermove", (0, 0), 2)  # another pointer does not steer it
    assert t.keyboard.ship_input() == ShipInput(right=True)
    stick_event(t, stick, "pointerup", (250, 50))
    assert t.keyboard.ship_input() == ShipInput()
    assert not stick.classList.contains("held")
    assert stick.knob.style.transform == "translate(0px, 0px)"


def test_the_stick_and_jump_work_together() -> None:
    t, stick = make_stick()
    stick_event(t, stick, "pointerdown", (50, 5))
    down(t, "Space", 2)
    assert t.keyboard.ship_input() == ShipInput(accelerate=True, jump=True)
    t.bridge.window.dispatch("blur")
    assert t.keyboard.ship_input() == ShipInput()
    assert not stick.classList.contains("held")


def test_a_browser_without_full_screen_is_not_asked() -> None:
    t = make_touch()
    t.bridge.document.documentElement = SimpleNamespace()  # iPhone Safari has no requestFullscreen
    t.bridge.window.dispatch("touchend")
    assert t.unlocks == 1


def test_a_stick_without_a_knob_still_steers() -> None:
    t, stick = make_stick()
    stick.knob = JS_NULL
    stick_event(t, stick, "pointerdown", (95, 50))
    assert t.keyboard.ship_input() == ShipInput(right=True)
    stick_event(t, stick, "pointerup", (95, 50))
    assert t.keyboard.ship_input() == ShipInput()
    assert not stick.classList.contains("held")
