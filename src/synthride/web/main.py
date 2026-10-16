# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""The browser entry point and composition root."""

from __future__ import annotations

from synthride.core.game_session import GameSession
from synthride.core.level_catalog import LevelCatalog
from synthride.web.browser_keyboard import BrowserKeyboard
from synthride.web.custom_level_store import CustomLevelStore
from synthride.web.editor_screen import EditorScreen
from synthride.web.game_loop import GameLoop
from synthride.web.hud import Hud
from synthride.web.js_bridge import JsBridge
from synthride.web.menu_screen import MenuScreen
from synthride.web.neon_lines import NeonLines
from synthride.web.neon_sparks import NeonSparks
from synthride.web.scene_renderer import SceneRenderer
from synthride.web.ship_model import ShipModel
from synthride.web.ship_reflection import ShipReflection
from synthride.web.sound_effects import SoundEffects
from synthride.web.space_backdrop import SpaceBackdrop
from synthride.web.synth_music import SynthMusic
from synthride.web.synth_voices import SynthVoices
from synthride.web.track_mesh_builder import TrackMeshBuilder


class Main:
    """Composition root: wires the game together from a browser bridge."""

    MASTER_VOLUME = 0.6

    def __init__(self, bridge: JsBridge, catalog: LevelCatalog | None = None) -> None:
        """Build the game on ``bridge``, with the levels from ``catalog``."""
        self._bridge = bridge
        self._catalog = catalog or LevelCatalog()

    def build(self) -> GameLoop:
        """Create the game loop and everything it drives."""
        bridge = self._bridge
        context = bridge.window.AudioContext.new()
        master = context.createGain()
        master.gain.value = self.MASTER_VOLUME
        master.connect(context.destination)
        lines = NeonLines(bridge)
        reflection = ShipReflection(bridge)
        session = GameSession(self._catalog.load_all())
        renderer = SceneRenderer(bridge, bridge.document.getElementById("stage"), lines, reflection=reflection)
        store = CustomLevelStore(bridge.window)
        editor = EditorScreen(bridge, store, renderer.renderer.domElement, renderer.camera)
        session.set_custom_levels(editor.levels())
        return GameLoop(
            bridge,
            session=session,
            keyboard=self.keyboard(session),
            renderer=renderer,
            track_builder=TrackMeshBuilder(bridge, lines, reflection=reflection),
            ship_model=ShipModel(bridge, lines),
            sparks=NeonSparks(bridge),
            backdrop=SpaceBackdrop(bridge),
            hud=Hud(bridge),
            menu=MenuScreen(bridge, editor=True),
            music=SynthMusic(SynthVoices(bridge, context, master)),
            sound_effects=SoundEffects(SynthVoices(bridge, context, master)),
            editor=editor,
        )

    def keyboard(self, session: GameSession) -> BrowserKeyboard:  # noqa: ARG002  (used by subclasses)
        """Return what steers the ship in ``session``: the player's keyboard."""
        return BrowserKeyboard(self._bridge)


def main() -> GameLoop:
    """Browser entry point, called by the page once Pyodide has unpacked the bundle."""
    import js  # noqa: PLC0415  # ty: ignore[unresolved-import]  (these modules only exist inside Pyodide)
    from pyodide.ffi import create_proxy, to_js  # noqa: PLC0415  # ty: ignore[unresolved-import]

    loop = Main(JsBridge(js.window, js.THREE, create_proxy, to_js)).build()
    loop.start()
    return loop
