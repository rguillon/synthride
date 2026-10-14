from __future__ import annotations

from typing import Any


class FakeJsObject:
    """Stands in for any JavaScript object: unknown attributes spring into existence, calls are recorded.

    ``Klass.new(*args)`` records the instance in ``created`` so tests can find what was constructed.
    """

    def __init__(self, name: str = "js", args: tuple = ()) -> None:
        self._name = name
        self.args = args
        self.calls: list[tuple] = []
        self.created: list[FakeJsObject] = []

    def __getattr__(self, attribute: str) -> Any:
        if attribute.startswith("__"):
            raise AttributeError(attribute)
        child = FakeJsObject(f"{self._name}.{attribute}")
        setattr(self, attribute, child)
        return child

    def __call__(self, *args: Any) -> FakeJsObject:
        self.calls.append(args)
        return FakeJsObject(f"{self._name}()", args)

    def new(self, *args: Any) -> FakeJsObject:
        instance = FakeJsObject(self._name, args)
        self.created.append(instance)
        return instance

    def __repr__(self) -> str:
        return f"<FakeJsObject {self._name}>"
