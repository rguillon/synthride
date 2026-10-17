# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""The browser entry point and composition root."""

from __future__ import annotations

from typing import TYPE_CHECKING

from synthride.core.gameplay.game_session import GameSession
from synthride.core.world.level_catalog import LevelCatalog
from synthride.core.world.level_parser import LevelParser
from synthride.web.audio.sound_effects import SoundEffects
from synthride.web.audio.synth_music import SynthMusic
from synthride.web.audio.synth_voices import SynthVoices
from synthride.web.browser.browser_keyboard import BrowserKeyboard
from synthride.web.browser.js_bridge import JsBridge
from synthride.web.browser.local_levels import LocalLevels
from synthride.web.game_loop import GameLoop
from synthride.web.rendering.neon_lines import NeonLines
from synthride.web.rendering.neon_sparks import NeonSparks
from synthride.web.rendering.scene_renderer import SceneRenderer
from synthride.web.rendering.ship_model import ShipModel
from synthride.web.rendering.ship_reflection import ShipReflection
from synthride.web.rendering.space_backdrop import SpaceBackdrop
from synthride.web.track_meshes.track_mesh_builder import TrackMeshBuilder
from synthride.web.ui.editor_screen import EditorScreen
from synthride.web.ui.hud import Hud
from synthride.web.ui.menu_screen import MenuScreen

if TYPE_CHECKING:
    from synthride.core.world.level import Level


class Main:
    """Composition root: wires the game together from a browser bridge."""

    MASTER_VOLUME = 0.6

    def __init__(self, bridge: JsBridge, catalog: LevelCatalog | None = None, *, dev: bool = False) -> None:
        """Build the game on ``bridge``, with the levels from ``catalog``.

        In ``dev`` mode the editor saves to the server's level files; otherwise it saves in the browser, and the levels
        saved there replace or follow the bundled ones.
        """
        self._bridge = bridge
        self._catalog = catalog or LevelCatalog()
        self._dev = dev

    def build(self) -> GameLoop:
        """Create the game loop and everything it drives."""
        bridge = self._bridge
        context = bridge.window.AudioContext.new()
        master = context.createGain()
        master.gain.value = self.MASTER_VOLUME
        master.connect(context.destination)
        lines = NeonLines(bridge)
        reflection = ShipReflection(bridge)
        local = None if self._dev else LocalLevels(bridge)
        files, levels = self._levels(local)
        session = GameSession(levels)
        renderer = SceneRenderer(bridge, bridge.document.getElementById("stage"), lines, reflection=reflection)
        surface = renderer.renderer.domElement
        editor = EditorScreen(bridge, surface, renderer.camera, files, session.put_level, local=local)
        return GameLoop(
            bridge,
            session=session,
            keyboard=BrowserKeyboard(bridge),
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

    def _levels(self, local: LocalLevels | None) -> tuple[list[str], list[Level]]:
        """Return the level files and their levels: the bundled ones, with those saved in ``local`` over them."""
        catalog = self._catalog
        files = catalog.file_names()
        levels = [catalog.load(name) for name in files]
        if local is None:
            return files, levels
        parser = LevelParser()
        for name, text in sorted(local.load().items()):
            try:
                level = parser.parse(text)
            except ValueError:
                continue  # a file saved by an older version of the game
            if name in files:
                levels[files.index(name)] = level
            else:
                files.append(name)
                levels.append(level)
        return files, levels


def main(*, dev: bool = False) -> GameLoop:
    """Browser entry point, run by the page once Pyodide has unpacked the bundle; ``dev`` saves edits to the server."""
    import js  # noqa: PLC0415  # ty: ignore[unresolved-import]  (these modules only exist inside Pyodide)
    from pyodide.ffi import create_proxy, to_js  # noqa: PLC0415  # ty: ignore[unresolved-import]

    loop = Main(JsBridge(js.window, js.THREE, create_proxy, to_js), dev=dev).build()
    loop.start()
    return loop
