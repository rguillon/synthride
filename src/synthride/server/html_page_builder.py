# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""The HTML5 page that boots the game."""

from __future__ import annotations

from string import Template


class HtmlPageBuilder:
    """Builds the HTML5 page that boots Pyodide, loads Three.js and hands control to the Python game."""

    PYODIDE_VERSION = "0.29.5"
    THREE_VERSION = "0.170.0"

    TEMPLATE = Template("""\
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SynthRide</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Orbitron:wght@500;800&display=swap">
<style>
:root {
  --night: #0b0014;
  --violet: #2a0845;
  --pink: #ff2bd6;
  --cyan: #00f0ff;
  --sun: #ffb347;
  --text: #f6e9ff;
}
* { box-sizing: border-box; }
html, body { margin: 0; height: 100%; overflow: hidden; background: var(--night); color: var(--text);
  font-family: "Orbitron", system-ui, sans-serif; }
body::after { content: ""; position: fixed; inset: 0; pointer-events: none; z-index: 5;
  background: repeating-linear-gradient(to bottom, rgba(0,0,0,0) 0 2px, rgba(0,0,0,0.18) 2px 3px); }
#stage, #stage canvas { position: fixed; inset: 0; width: 100%; height: 100%; display: block; }
.overlay { position: fixed; inset: 0; z-index: 3; display: flex; flex-direction: column; align-items: center;
  justify-content: safe center; gap: 1.2rem; text-align: center; padding: 16px; overflow-y: auto;
  background: radial-gradient(ellipse at center, rgba(42,8,69,0.55), rgba(11,0,20,0.85)); }
.overlay[hidden] { display: none; }
.logo { font-size: clamp(2.6rem, 11vw, 7rem); font-weight: 800; letter-spacing: 0.08em; margin: 0;
  background: linear-gradient(180deg, var(--sun) 0%, var(--pink) 60%, #7b2cff 100%);
  -webkit-background-clip: text; background-clip: text; color: transparent;
  filter: drop-shadow(0 0 18px rgba(255,43,214,0.7)); }
.subtitle { color: var(--cyan); letter-spacing: 0.4em; text-shadow: 0 0 10px var(--cyan); margin: 0; }
.prompt { animation: blink 1.1s steps(2, start) infinite; color: var(--text); text-shadow: 0 0 8px var(--pink); }
.keys { font-size: 0.75rem; opacity: 0.75; line-height: 1.8; }
.level-list { list-style: none; padding: 0; margin: 0; min-width: min(420px, 90vw); }
.level-list li { padding: 0.7rem 1rem; margin: 0 0 0.6rem; border: 1px solid rgba(0,240,255,0.25);
  letter-spacing: 0.15em; break-inside: avoid; }
@media (min-width: 900px) { .level-list { columns: 2; column-gap: 1.2rem; min-width: 820px; } }
.level-list li.selected { border-color: var(--pink); color: var(--pink); box-shadow: 0 0 16px var(--pink);
  text-shadow: 0 0 8px var(--pink); }
.headline { font-size: clamp(1.8rem, 7vw, 4rem); margin: 0; color: var(--pink); text-shadow: 0 0 20px var(--pink); }
#hud { position: fixed; inset: 0; z-index: 2; pointer-events: none; padding: 16px; font-size: 0.8rem;
  text-shadow: 0 0 6px var(--cyan); }
#hud[hidden] { display: none; }
.hud-top { display: flex; justify-content: space-between; gap: 1rem; letter-spacing: 0.15em; }
.hud-fps { opacity: 0.6; letter-spacing: 0.1em; }
.hud-lives { color: var(--pink); text-shadow: 0 0 8px var(--pink); letter-spacing: 0.3em; }
.hud-bottom { position: absolute; left: 16px; right: 16px; bottom: 16px; display: grid;
  grid-template-columns: repeat(3, 1fr); gap: 0.8rem; }
.gauge-label { display: block; margin-bottom: 0.3rem; letter-spacing: 0.2em; }
.gauge { height: 10px; border: 1px solid currentColor; box-shadow: 0 0 8px currentColor; }
.gauge-fill { height: 100%; width: 100%; background: currentColor; transition: width 0.1s linear; }
.gauge-speed { color: var(--cyan); }
.gauge-fuel { color: var(--sun); }
.gauge-oxygen { color: #7dff9b; }
.gauge.low .gauge-fill { animation: blink 0.4s steps(2, start) infinite; }
.progress { margin-top: 0.6rem; height: 4px; background: rgba(255,255,255,0.12); }
.progress-fill { height: 100%; width: 0; background: linear-gradient(90deg, var(--cyan), var(--pink)); }
.legend { list-style: none; padding: 0; margin: 0; display: grid; grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.35rem 1.4rem; font-size: 0.7rem; letter-spacing: 0.12em; text-align: left; opacity: 0.9; }
.legend li { display: flex; align-items: center; gap: 0.6rem; white-space: nowrap; }
.swatch { display: inline-block; min-width: 2.4em; text-align: center; font-weight: 800;
  text-shadow: 0 0 8px currentColor; }
.hud-callout { position: absolute; top: 26%; left: 0; right: 0; text-align: center; opacity: 0;
  font-size: clamp(1.3rem, 5vw, 2.6rem); font-weight: 800; letter-spacing: 0.25em;
  text-shadow: 0 0 14px currentColor, 0 0 30px currentColor; }
#loading { z-index: 4; }
@keyframes blink { to { visibility: hidden; } }
@media (max-width: 600px) { .hud-bottom, .legend { grid-template-columns: 1fr; } }
</style>
<script type="importmap">
{"imports": {"three": "$three_url/build/three.module.js", "three/addons/": "$three_url/examples/jsm/"}}
</script>
<script src="$pyodide_url/pyodide.js"></script>
</head>
<body>
<div id="stage"></div>
<div id="hud" hidden></div>
<div id="menu" class="overlay" hidden></div>
<div id="loading" class="overlay">
  <h1 class="logo">SYNTHRIDE</h1>
  <p class="subtitle" id="loading-status">Booting Python&hellip;</p>
</div>
<script type="module">
import * as THREE from "three";
import { EffectComposer } from "three/addons/postprocessing/EffectComposer.js";
import { RenderPass } from "three/addons/postprocessing/RenderPass.js";
import { UnrealBloomPass } from "three/addons/postprocessing/UnrealBloomPass.js";
import { OutputPass } from "three/addons/postprocessing/OutputPass.js";
import { LineSegments2 } from "three/addons/lines/LineSegments2.js";
import { LineSegmentsGeometry } from "three/addons/lines/LineSegmentsGeometry.js";
import { LineMaterial } from "three/addons/lines/LineMaterial.js";

globalThis.THREE = {
  ...THREE, EffectComposer, RenderPass, UnrealBloomPass, OutputPass, LineSegments2, LineSegmentsGeometry, LineMaterial,
};
const status = document.getElementById("loading-status");
try {
  const pyodide = await loadPyodide();
  status.textContent = "Loading the cyberspace\\u2026";
  const response = await fetch("$bundle_url", { cache: "no-store" });
  pyodide.unpackArchive(await response.arrayBuffer(), "zip");
  pyodide.runPython("from synthride.web.main import main; main()");
  document.getElementById("loading").remove();
} catch (error) {
  status.textContent = "Failed to start: " + error.message;
  console.error(error);
}
</script>
</body>
</html>
""")

    def __init__(
        self,
        pyodide_version: str = PYODIDE_VERSION,
        three_version: str = THREE_VERSION,
        bundle_url: str = "synthride.zip",
    ) -> None:
        """Use the given library versions and load the bundle from ``bundle_url``."""
        self._pyodide_version = pyodide_version
        self._three_version = three_version
        self._bundle_url = bundle_url

    @property
    def pyodide_url(self) -> str:
        """The CDN folder Pyodide is loaded from."""
        return f"https://cdn.jsdelivr.net/pyodide/v{self._pyodide_version}/full"

    @property
    def three_url(self) -> str:
        """The CDN folder Three.js is loaded from."""
        return f"https://cdn.jsdelivr.net/npm/three@{self._three_version}"

    def build(self) -> str:
        """Return the page's HTML."""
        return self.TEMPLATE.substitute(
            pyodide_url=self.pyodide_url, three_url=self.three_url, bundle_url=self._bundle_url
        )
