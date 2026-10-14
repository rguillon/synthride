from __future__ import annotations

from tests.web.fakes.fake_class_list import FakeClassList
from tests.web.fakes.fake_js_object import FakeJsObject


class FakeElement:
    """A DOM element with the properties the game touches."""

    def __init__(self, element_id: str = "") -> None:
        self.id = element_id
        self.hidden = False
        self.innerHTML = ""
        self.textContent = ""
        self.style = FakeJsObject("style")
        self.classList = FakeClassList()
        self.children: list = []

    def appendChild(self, child) -> None:
        self.children.append(child)
