# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

from types import SimpleNamespace

from synthride.web.browser.full_screen import FullScreen
from tests.web.fakes.fake_js_bridge import FakeJsBridge
from tests.web.fakes.fake_js_null import JS_NULL
from tests.web.fakes.fake_key_event import FakeKeyEvent


def make_full_screen() -> SimpleNamespace:
    bridge = FakeJsBridge()
    return SimpleNamespace(bridge=bridge, full_screen=FullScreen(bridge), document=bridge.document)


def press(t: SimpleNamespace, key: str, tag: str = "BODY") -> FakeKeyEvent:
    event = FakeKeyEvent(f"Key{key.upper()}", key=key)
    event.target = SimpleNamespace(tagName=tag)
    t.bridge.window.dispatch("keydown", event)
    return event


def test_the_button_asks_for_full_screen() -> None:
    t = make_full_screen()
    t.document.getElementById("fullscreen").dispatch("click", None)
    assert t.document.documentElement.fullscreen_requests == 1


def test_the_button_lets_go_of_the_focus() -> None:
    t = make_full_screen()  # or Space, which jumps, would press it again
    t.document.getElementById("fullscreen").dispatch("click", None)
    assert t.document.getElementById("fullscreen").blurs == 1


def test_the_button_leaves_full_screen() -> None:
    t = make_full_screen()
    t.document.fullscreenElement = t.document.documentElement
    t.document.getElementById("fullscreen").dispatch("click", None)
    assert t.document.documentElement.fullscreen_requests == 0
    assert t.document.exits == 1


def test_f_toggles_full_screen_inside_the_key_press() -> None:
    t = make_full_screen()  # browsers only grant it inside the gesture, not from the next animation frame
    press(t, "f")
    assert t.document.documentElement.fullscreen_requests == 1


def test_f_follows_the_layout() -> None:
    t = make_full_screen()
    press(t, "F")
    assert t.document.documentElement.fullscreen_requests == 1


def test_f_typed_in_a_field_is_left_to_the_field() -> None:
    t = make_full_screen()
    press(t, "f", tag="INPUT")
    assert t.document.documentElement.fullscreen_requests == 0


def test_ctrl_f_is_left_to_the_browser() -> None:
    t = make_full_screen()
    event = FakeKeyEvent("KeyF", key="f")
    event.ctrlKey = True
    t.bridge.window.dispatch("keydown", event)
    assert t.document.documentElement.fullscreen_requests == 0


def test_the_body_knows_when_the_page_is_full_screen() -> None:
    t = make_full_screen()  # Escape leaves full screen without the page's say: follow the browser's event
    t.document.fullscreenElement = t.document.documentElement
    t.document.dispatch("fullscreenchange")
    assert t.document.body.classList.contains("fullscreen")
    t.document.fullscreenElement = JS_NULL
    t.document.dispatch("fullscreenchange")
    assert not t.document.body.classList.contains("fullscreen")


def test_other_keys_and_repeats_leave_full_screen_alone() -> None:
    t = make_full_screen()
    press(t, "g")
    held = FakeKeyEvent("KeyF", key="f", repeat=True)
    t.bridge.window.dispatch("keydown", held)
    assert t.document.documentElement.fullscreen_requests == 0


def test_a_browser_without_full_screen_is_left_alone() -> None:
    t = make_full_screen()
    t.document.documentElement = SimpleNamespace()
    t.full_screen.toggle()
