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

### Level editor

`make serve-dev` (or `uv run synthride serve --dev`) serves the game with the level editor: press `E` on the title or
on a level in the level select. Paint the track with the brushes, ride it with `T`, and **Save** writes it into
`src/synthride/levels/`, over the level's own file or as a new `level_NN.json` after the last one. Without `--dev`
there is no editor, and the server refuses every `POST`, so the level files stay read-only.

`make site` (or `uv run synthride build --out dist/web`) writes a static `index.html` + `synthride.zip` that can be
hosted anywhere, GitHub Pages included.

| Key | Action |
| --- | --- |
| `↑` / `W` | accelerate |
| `↓` / `S` | brake |
| `←` `→` / `A` `D` | strafe |
| `Space` | jump; press again in mid-air for one double jump |
| `Esc` | back to level select |
| `M` | mute music |

### Rules

- The track is 8 blocks wide and made of blocks of different heights and effects. Each special block carries an
  animated marking that shows what it does, and the level select screen has a key:

  | Block | Look | Effect |
  | --- | --- | --- |
  | normal | cyan | solid ground |
  | boost | pink, chevrons racing forward | speed burst above top speed |
  | slow | violet, chevrons crawling back | caps your speed |
  | kill | red, flashing hazard stripes | burns the ship |
  | jump pad | orange, target and rising arrows | launches the ship high into the air |
  | ice | white, drifting crystals | no grip: sideways speed changes only slowly |
  | pusher | lime, arrows streaming sideways | drifts the ship left or right |
  | refuel | green, pulsing plus | refills fuel |
  | air | blue, bubbles | refills oxygen |
  | finish | gold checker | ends the level |

- Blocks can carry a **tunnel**, square or round. Side-by-side tunnel blocks merge into one wide tunnel. Its walls
  stop you, jumping inside bumps your head on the roof, flying into its front edge is a crash, and you can ride
  on top of it.
- Falling off the track, hitting a block head-on, riding a kill block, or running out of fuel or oxygen costs a life
  and restarts the level. Clipping a block with only a corner of the ship nudges you sideways instead.
- Finish the track to unlock the next level. You have 3 lives.

## Levels

Levels are JSON files named `level_*.json` in `src/synthride/levels/`, picked up automatically in file-name order:

```json
{
  "name": "Neon Highway",
  "gravity": 18,
  "oxygen": 90,
  "fuel": 100,
  "track": [
    "# first row = start of the track",
    [12, ".. .. N1 N1 N1 N1 .. .."],
    ".. .. N1 B1 B1 N1 .. ..",
    [3, ".. N2 N2 .. .. N2 N2 .."],
    [4, ".. .. N1A N1A N1A N1A .. ..  # a round tunnel four blocks wide"]
  ]
}
```

`gravity`, `oxygen` (seconds of air) and `fuel` (1 unit per 4 blocks travelled) are optional; the values above are
the defaults. `track` lists rows from the start of the track: a `[count, row]` pair repeats the row `count` times,
so a long straight is written once, and a lone row string is used once. `#` starts a comment, so a string starting
with `#` is skipped.

Each row has 8 cells: `..` is a gap, otherwise a type letter (`N`ormal, `B`oost, `S`low, `K`ill, `R`efuel,
`O` air, `J`ump pad, `I`ce, `<` / `>` pushers, `F`inish) followed by a height from 1 to 8, optionally followed by
`T` for a square tunnel or `A` for a round (arched) one: `N1T`, `B2A`.

A tile can be oblique instead: a slope suffix names its raised side, `f`ront (where the track goes), `b`ack, `l`eft
or `r`ight, or its raised corner, `fl`, `fr`, `bl` or `br`. The height digit is the low side, and the raised side is
one height higher, so `N1 N1f N2` is a ramp up and `N2 N1b N1` a ramp down. Corners join two side ramps around the
corner of a raised plateau:

```json
"# a hill: rises on all four sides",
".. N1 N1fr N1f N1f N1fl N1 ..",
[3, ".. N1 N1r  N2  N2  N1l  N1 .."],
".. N1 N1br N1b N1b N1bl N1 .."
```

A ship leaving the top of a ramp keeps its climb, so a ramp that ends over a gap is a kicker.

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
