# synthride

[![Release](https://img.shields.io/github/v/release/rguillon/synthride)](https://img.shields.io/github/v/release/rguillon/synthride)
[![Build status](https://img.shields.io/github/actions/workflow/status/rguillon/synthride/main.yml?branch=main)](https://github.com/rguillon/synthride/actions/workflows/main.yml?query=branch%3Amain)
[![codecov](https://codecov.io/gh/rguillon/synthride/branch/main/graph/badge.svg)](https://codecov.io/gh/rguillon/synthride)
[![Commit activity](https://img.shields.io/github/commit-activity/m/rguillon/synthride)](https://img.shields.io/github/commit-activity/m/rguillon/synthride)
[![License](https://img.shields.io/github/license/rguillon/synthride)](https://img.shields.io/github/license/rguillon/synthride)

**SynthRide** is a SkyRoads (1993)-inspired 3D sky racer with a synthwave / cyberpunk look. The whole game is
written in Python and **runs entirely in the browser**: a tiny Python server packages the game into an HTML5
page that boots [Pyodide](https://pyodide.org) (CPython compiled to WebAssembly) and renders with
[Three.js](https://threejs.org).

- **Github repository**: <https://github.com/rguillon/synthride/>
- **Documentation** <https://rguillon.github.io/synthride/>

## Play

```bash
make install        # once: create the virtual environment
make serve          # then open http://127.0.0.1:8000
```

`make site` (or `uv run synthride build --out dist/web`) writes a static `index.html` + `synthride.zip` that can be
hosted anywhere, GitHub Pages included.

| Key | Action |
| --- | --- |
| `↑` / `W` | accelerate |
| `↓` / `S` | brake |
| `←` `→` / `A` `D` | strafe |
| `Space` | jump |
| `Esc` | back to level select |
| `M` | mute music |

### Rules

- The track is 8 blocks wide and made of blocks of different heights and effects:
  **cyan** normal, **pink** boost, **violet** slow down, **red** kill, **green** refuel, **gold** finish.
- Falling off the track, hitting a block head-on, riding a kill block, or running out of fuel or oxygen costs a life
  and restarts the level. Clipping a block with only a corner of the ship nudges you sideways instead.
- Finish the track to unlock the next level. You have 3 lives.

## Levels

Levels are plain text files in `src/synthride/levels/`, picked up automatically in file-name order:

```text
name: Neon Highway
gravity: 18        # optional, these are the defaults
oxygen: 90         # seconds of air
fuel: 100          # 1 unit of fuel per 4 blocks travelled
---
.. .. N1 N1 N1 N1 .. ..      # first row = start of the track
.. .. N1 B1 B1 N1 .. ..
.. N2 N2 .. .. N2 N2 ..
```

Each row has 8 cells: `..` is a gap, otherwise a type letter (`N`ormal, `B`oost, `S`low, `K`ill, `R`efuel,
`F`inish) followed by a height from 1 to 4.

## Architecture

| Package | Role |
| --- | --- |
| `synthride.core` | Pure Python game logic: tracks, physics, collisions, tile effects, lives, phases. No browser code. |
| `synthride.web` | Browser adapters: Three.js rendering, keyboard, HUD/menus, procedural WebAudio music and SFX. Every browser object is injected through `JsBridge`, so it is unit-tested with fakes. |
| `synthride.server` | Desktop tooling: zips `core` + `web` + `levels`, generates the HTML5 page, serves both. |

The code has one class per file, and each source file has a matching test file under `tests/`.

## Development

```bash
make test    # pytest with coverage
make check   # ruff, ty, deptry, lock-file check
make docs    # serve the documentation
```

---

Repository initiated with [fpgmaas/cookiecutter-uv](https://github.com/fpgmaas/cookiecutter-uv).
