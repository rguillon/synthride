# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""The browser entry point of the game played by the neural network."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from synthride.web.js_bridge import JsBridge
from synthride.web.main import Main
from tests.ai.ai_keyboard import AiKeyboard
from tests.ai.brain_store import BrainStore

if TYPE_CHECKING:
    from synthride.core.game_session import GameSession
    from synthride.core.level_catalog import LevelCatalog
    from synthride.web.browser_keyboard import BrowserKeyboard
    from synthride.web.game_loop import GameLoop
    from tests.ai.neural_network import NeuralNetwork


class AiMain(Main):
    """Wires the game like :class:`Main`, with the network at the ship's controls."""

    def __init__(self, bridge: JsBridge, network: NeuralNetwork, catalog: LevelCatalog | None = None) -> None:
        """Build the game on ``bridge``, steered by ``network``."""
        super().__init__(bridge, catalog)
        self._network = network

    def keyboard(self, session: GameSession) -> BrowserKeyboard:
        """Return the menu keys with the network steering the ship."""
        return AiKeyboard(self._bridge, session, self._network)


def main(brain: Path = Path("data/brain.json")) -> GameLoop:
    """Browser entry point, the bundle holding the brain at ``brain``."""
    import js  # noqa: PLC0415  # ty: ignore[unresolved-import]  (these modules only exist inside Pyodide)
    from pyodide.ffi import create_proxy, to_js  # noqa: PLC0415  # ty: ignore[unresolved-import]

    stored = BrainStore(brain).load()
    if stored is None:
        msg = f"no brain in {brain}"
        raise FileNotFoundError(msg)
    loop = AiMain(JsBridge(js.window, js.THREE, create_proxy, to_js), stored.network).build()
    loop.start()
    return loop
