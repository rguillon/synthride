from synthride.web.js_bridge import JsBridge
from tests.web.fakes.fake_js_object import FakeJsObject


def make_bridge(conversions: list):
    window = FakeJsObject("window")

    def to_js(value, **options):
        conversions.append((value, options))
        return ("js", value)

    return window, JsBridge(window, FakeJsObject("THREE"), lambda function: ("proxy", function), to_js)


def test_exposes_window_document_and_three():
    window, bridge = make_bridge([])
    assert bridge.window is window
    assert bridge.document is window.document
    assert bridge.three is not None


def test_obj_converts_dicts_to_object_literals():
    conversions = []
    window, bridge = make_bridge(conversions)
    assert bridge.obj(color=1, nested={"a": 2}) == ("js", {"color": 1, "nested": {"a": 2}})
    assert conversions[0][1] == {"dict_converter": window.Object.fromEntries}


def test_proxy_and_float32_array():
    window, bridge = make_bridge([])
    assert bridge.proxy(print) == ("proxy", print)
    bridge.float32_array((1.0, 2.0))
    assert window.Float32Array.created[0].args == (("js", [1.0, 2.0]),)
