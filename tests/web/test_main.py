import sys
from types import SimpleNamespace

from synthride.web import main as main_module
from synthride.web.game_loop import GameLoop
from synthride.web.main import Main
from tests.web.fakes.fake_js_bridge import FakeJsBridge
from tests.web.fakes.fake_js_object import FakeJsObject
from tests.web.fakes.fake_window import FakeWindow


def test_build_wires_a_game_loop_with_bundled_levels():
    bridge = FakeJsBridge()
    loop = Main(bridge).build()
    assert isinstance(loop, GameLoop)
    assert len(loop.session.levels) >= 3


def test_main_boots_from_pyodide_modules(monkeypatch):
    window = FakeWindow()
    ffi = SimpleNamespace(create_proxy=lambda function: function, to_js=lambda value, **_: value)
    monkeypatch.setitem(sys.modules, "js", SimpleNamespace(window=window, THREE=FakeJsObject("THREE")))
    monkeypatch.setitem(sys.modules, "pyodide", SimpleNamespace(ffi=ffi))
    monkeypatch.setitem(sys.modules, "pyodide.ffi", ffi)
    loop = main_module.main()
    assert isinstance(loop, GameLoop)
    assert len(window.frame_callbacks) == 1
