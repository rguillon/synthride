# Playable on a phone: touch controls design

Date: 2026-10-21 · Branch: `mobile`

## Goal

Someone opening <https://rguillon.github.io/synthride/> on a phone can go from the title screen through level
select to a full ride with touch alone, holding the phone in landscape.

Success: a level can be completed comfortably with touch on a mid-range phone in landscape; desktop play is
unchanged.

## Decisions

| Topic | Decision |
| --- | --- |
| Control scheme | On-screen buttons: ◀ ▶ under the left thumb; ▼ ▲ and a wide JUMP under the right |
| Orientation | Landscape only; portrait shows a "rotate your phone" overlay |
| When controls appear | On the first `touchstart` the page sees, for the rest of the session |
| Rendering performance | Unchanged in this iteration; revisit after trying a real phone |
| Architecture | Touch feeds the existing keyboard model (held key codes and press queue) |

Out of scope: the level editor stays desktop-only; no PWA manifest; no tilt or swipe controls; no adaptive quality.

## Components

### `BrowserKeyboard` (changed)

Gains a public API so any input source can drive the same state the key handlers drive:

- `hold(code)`: add `code` to the held keys and queue it as a fresh press, unless it is already held.
- `release(code)`: remove `code` from the held keys.
- `release_all()`: clear the held keys (the existing `blur` handler uses it).
- `press(code)`: queue `code` as a fresh press without holding it.

`on_key_down` / `on_key_up` are rewritten on top of these. Nothing else changes.

### `TouchControls` (new, `src/synthride/web/browser/touch_controls.py`)

`TouchControls(bridge, keyboard, unlock_audio)`:

- Listens to `touchstart` on `window` (passive). On the first one it adds the `touch` class to `<body>` and asks
  for full screen (`document.documentElement.requestFullscreen()`, if present; failure is ignored). Later
  touches do nothing more.
- Calls `unlock_audio()` from inside a `touchend` handler on `window`, until it has been called once. iOS Safari only
  lets an `AudioContext` resume inside such a gesture handler, while the game resumes it later, from the animation
  frame (`SynthMusic.start`); `Main` passes the context's `resume`.
- Finds the `#touch` overlay in the page and listens on it (delegated) for `pointerdown`, `pointerup`,
  `pointercancel` and `pointerleave` (the last on each pad). Each pad is a `<button data-code="…">`:
  ◀ `ArrowLeft`, ▶ `ArrowRight`, ▲ `ArrowUp`, ▼ `ArrowDown`, JUMP `Space`.
- Tracks which code each `pointerId` holds. `pointerdown` on a pad holds its code; `pointerup`, `pointercancel` and
  `pointerleave` release the pointer's code unless another pointer still holds it. Pointer capture is
  released on `pointerdown` so a thumb sliding onto the neighbouring pad leaves the first (`pointerleave`) and
  enters the second (`pointerenter`, also handled as a hold while the pointer is down).
- Two small buttons, `data-press="Escape"` (⏸) and `data-press="KeyM"` (🔇), call `keyboard.press`. For `KeyM`
  this goes through `BrowserKeyboard.letter`, which falls back to the QWERTY letter `m`, so mute works.
- Releases every pointer and held code on `visibilitychange` to hidden. (The keyboard's `blur` handler already
  covers focus loss.)
- Calls `preventDefault()` on pad `pointerdown` events; the CSS sets `touch-action: none` and
  `user-select: none` on the overlay so pads never scroll, zoom or open the long-press menu.

### `MenuScreen` (changed)

- Each level `<li>` carries `data-level="<index>"`.
- The title, game over and victory screens contain both texts, `<span class="key-text">PRESS ENTER</span>` and
  `<span class="touch-text">TAP TO START</span>`; CSS shows one according to `body.touch`.
- Listens once for `click` on `#menu` and queues a tap: the level index when the click is inside a
  `[data-level]` item, otherwise "anywhere". Clicks on links (the GitHub link) are left alone and not queued.
- `consume_taps()` returns the queued taps, oldest first, and empties the queue.

Mouse clicks go through the same path, so desktop menus become clickable too.

### `GameLoop` (changed)

In `tick`, after consuming key presses, it consumes the menu taps:

- tap on a level `i` in `LEVEL_SELECT`: `session.selected_level = i`, then start the ride as `Enter` does;
- tap anywhere in `TITLE`, `GAME_OVER` or `VICTORY`: handled as `Enter`;
- any other tap is ignored.

### `Main` (changed)

Builds `TouchControls(bridge, keyboard, context.resume)` around the keyboard it passes to `GameLoop`. `GameLoop` never learns about
touch.

### Page (`html_page_builder.py`, changed)

- The viewport meta tag gains `viewport-fit=cover`.
- New markup: a `#touch` overlay holding the pad buttons and the ⏸ / 🔇 buttons, and a `#rotate` overlay
  ("ROTATE YOUR PHONE ⟲").
- New CSS, all under `body.touch` so desktop is unchanged:
  - `#touch` is shown only while the HUD is shown (`body.touch #hud:not([hidden]) ~ #touch`), so pads never cover the
    menus or the editor.
  - Pads are about 64–72 px, semi-transparent neon outlines that glow pink while pressed; JUMP is the widest. They
    sit inside `env(safe-area-inset-*)` margins.
  - The HUD gauges (`.hud-bottom`) move from the bottom to a strip under the top bar; ⏸ and 🔇 sit at the top right.
  - `.keys` help lines and `.key-text` are hidden; `.touch-text` is shown.
  - `@media (orientation: portrait)` shows `#rotate` above everything.
  - Level items get `cursor: pointer`.

## Data flow

```text
pad pointerdown ─► TouchControls ─► keyboard.hold("ArrowLeft") ─┐
key keydown ────────────────────► keyboard.hold("ArrowLeft") ──┤
                                                                ▼
                       GameLoop.tick ─► keyboard.ship_input() / consume_presses()
menu click ─► MenuScreen queue ─► GameLoop.tick ─► consume_taps()
```

## Edge cases

- Lost releases: `pointercancel`, `pointerleave`, `blur` and a hidden page all release; a ship never keeps strafing
  after a notification or app switch.
- Ghost clicks: pads use pointer events only and the menus `click` only. The pads are hidden in menus and the menus
  hidden while riding, so one tap never does both.
- Double jump: each new `pointerdown` on JUMP is a fresh hold, as two Space presses are.
- Audio: the game resumes the `AudioContext` from the animation frame, which iOS Safari does not accept;
  `TouchControls` therefore resumes it inside the first `touchend` handler. Checked on a real phone.
- Desktop: with no `touchstart`, the page looks and plays as before.

## Testing

- Unit tests with the existing fakes (`FakeJsBridge`, `FakeWindow`, `FakeElement`, plus a new fake pointer event):
  - `BrowserKeyboard.hold` / `release` / `release_all` / `press`;
  - `TouchControls`: first touch adds `body.touch`; the first `touchend` unlocks audio, once; pad down/up maps to `ShipInput`; two pointers on two pads;
    sliding from one pad to the other; cancel and hidden page release; ⏸ / 🔇 queue `Escape` / `KeyM`;
  - `MenuScreen`: `data-level` markup, `click` inside a level or elsewhere queues the right tap, link clicks don't;
  - `GameLoop`: tap on the title opens level select; tap on level `i` rides level `i`; tap on game over returns.
- Phone smoke test: a Playwright script beside `tests/screenshots.py`, with a landscape phone viewport
  (`has_touch=True`, `is_mobile=True`), taps title → level select → a level, holds ▲, and saves
  `data/screenshot-mobile.jpg` for checking the layout.
- Real device: after merging, Pages redeploys and the game is tried on a phone.
