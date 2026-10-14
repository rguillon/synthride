from __future__ import annotations

from tests.web.fakes.fake_element import FakeElement


class FakeDocument:
    """A DOM document whose ``getElementById`` returns one stable element per id."""

    def __init__(self) -> None:
        self.elements: dict[str, FakeElement] = {}

    def getElementById(self, element_id: str) -> FakeElement:
        return self.elements.setdefault(element_id, FakeElement(element_id))
