# Touch Controls Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make SynthRide playable on a phone in landscape by touch alone: on-screen pads to ride, tappable menus,
a mute button everywhere, a rotate prompt in portrait.

**Architecture:** A new `TouchControls` turns pad touches into the key codes `BrowserKeyboard` already tracks, so the
game loop and physics stay keyboard-shaped. `MenuScreen` queues menu clicks (touch or mouse) as taps that `GameLoop`
maps onto its existing key handling. All touch layout is CSS under `body.touch`, a class set on the first touch.

**Tech Stack:** Python 3 run in Pyodide, Three.js, plain DOM/CSS; pytest with the fakes in `tests/web/fakes`;
Playwright for the phone smoke test.

**Spec:** `docs/superpowers/specs/2026-10-21-mobile-touch-controls-design.md`

## Global Constraints

- Desktop without a touch must look and play exactly as before: every new rule in the page is under `body.touch`.
- Landscape only; portrait on touch shows `#rotate` ("ROTATE YOUR PHONE ⟲").
- Pad codes: ◀ `ArrowLeft`, ▶ `ArrowRight`, ▲ `ArrowUp`, ▼ `ArrowDown`, JUMP `Space`; ⏸ presses `Escape`, 🔇 presses
  `KeyM`.
- Pads about 64–72 px, JUMP the widest; level rows at least 44 px tall on touch.
- Rendering is not changed.
- Code style as in the repo: copyright header, module docstring, a docstring on every public method, `ruff` and `ty`
  clean (`make check`), fakes named `Fake*` in `tests/web/fakes`, camelCase fake methods marked `# noqa: N802`.
- Every commit message ends with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Review Focus

1. A thumb lifted off the screen edge (no `pointerup`, only `pointercancel`, or none and the app goes to the
   background) must not leave the ship strafing: covered in Task 2 (`test_cancel_and_hidden_page_release_everything`).
2. Two thumbs on two pads, then one lifted: the other pad must stay held. Task 2 (`test_two_pointers_hold_two_pads`).
3. Two pointers on the same pad, one lifted: the code stays held until both are up. Task 2
   (`test_a_code_stays_held_while_another_pointer_holds_it`).
4. A level index out of range from stale markup (levels list changed under the menu): ignored, no crash. Task 4
   (`test_taps_out_of_place_are_ignored`).
5. Tapping the GitHub link in level select must open the link, not start a ride. Task 3
   (`test_clicks_on_links_are_not_taps`).

---

### Task 1: `BrowserKeyboard` public hold/release/press API

**Files:**
- Modify: `src/synthride/web/browser/browser_keyboard.py`
- Test: `tests/web/browser/test_browser_keyboard.py`

**Interfaces:**
- Produces: `BrowserKeyboard.hold(code: str) -> None`, `release(code: str) -> None`, `release_all() -> None`,
  `press(code: str) -> None`.

- [ ] **Step 1: Write the failing tests**

```python
def test_other_inputs_hold_release_and_press_keys() -> None:
    _, keyboard = make_keyboard()
    keyboard.hold("ArrowLeft")
    keyboard.hold("ArrowLeft")  # already held: not a fresh press
    keyboard.hold("Space")
    assert keyboard.ship_input() == ShipInput(left=True, jump=True)
    assert keyboard.consume_presses() == ["ArrowLeft", "Space"]
    keyboard.release("ArrowLeft")
    assert keyboard.ship_input() == ShipInput(jump=True)
    keyboard.press("Escape")
    assert keyboard.consume_presses() == ["Escape"]
    assert keyboard.ship_input() == ShipInput(jump=True)
    keyboard.release_all()
    assert keyboard.ship_input() == ShipInput()
```

- [ ] **Step 2: Run it to see it fail**

Run: `uv run python -m pytest tests/web/browser/test_browser_keyboard.py -v`
Expected: the new test FAILS with `AttributeError: ... 'hold'`.

- [ ] **Step 3: Implement the four methods**

`hold` adds to `_held` and appends to `_presses` only when the code was not held; `press` only appends; `release`
discards; `release_all` clears. Rewrite `on_key_down` to call `hold` when `not event.repeat` (a repeat changes
nothing: the key is already held), `on_key_up` to call `release`, and the `blur` listener to call `release_all`.

- [ ] **Step 4: Run the keyboard tests and the whole suite**

Run: `uv run python -m pytest tests -q`
Expected: all PASS (the existing keyboard tests prove keys behave as before).

- [ ] **Step 5: Commit**

```bash
git add src/synthride/web/browser/browser_keyboard.py tests/web/browser/test_browser_keyboard.py
git commit -m "Let other inputs hold, release and press keys"
```

---

### Task 2: `TouchControls`

**Files:**
- Create: `src/synthride/web/browser/touch_controls.py`
- Create: `tests/web/fakes/fake_pointer_event.py`
- Modify: `tests/web/fakes/fake_document.py`, `tests/web/fakes/fake_element.py`, `tests/web/fakes/fake_window.py`
- Test: `tests/web/browser/test_touch_controls.py`

**Interfaces:**
- Consumes: Task 1's `hold`, `release`, `release_all`, `press`.
- Produces: `TouchControls(bridge: JsBridge, keyboard: BrowserKeyboard, unlock_audio: Callable[[], object])`;
  property `active -> bool` (a touch was seen). It finds `#touch` with `document.getElementById("touch")`.

Behaviour (from the spec, with one correction): `pointerleave`/`pointerenter` do not bubble, so delegation on
`#touch` uses their bubbling twins `pointerout`/`pointerover`.

- `window` `touchstart`: the first time, `document.body.classList.toggle("touch", True)` and, if
  `document.documentElement` has `requestFullscreen`, call it and `.catch(...)` the returned promise with a proxy
  that ignores the error.
- `window` `touchend`: the first time, call `unlock_audio()`.
- `#touch` `pointerdown` on `event.target.closest("[data-code]")`: `event.preventDefault()`,
  `pad.releasePointerCapture(event.pointerId)` (touch pointers are captured implicitly, which would stop
  `pointerout` on sliding), remember the pointer as down, hold the pad's code.
- `#touch` `pointerover` on a pad by a pointer that is down: hold that pad's code for the pointer.
- `#touch` `pointerout` from a pad, `pointerup`, `pointercancel`: release the pointer's code; `pointerup` and
  `pointercancel` also forget the pointer. A code is released on the keyboard only when no other pointer holds it.
- While a pad is held by any pointer it carries the class `held` (`classList.toggle("held", ...)`) so CSS can glow it.
- `document.body` `click` on `event.target.closest("[data-press]")`: `keyboard.press(<data-press>)`.
- `document` `visibilitychange` with `document.visibilityState == "hidden"`: forget all pointers, un-glow pads,
  `keyboard.release_all()`.

State: `dict[int, str | None]`, pointer id to the code it holds (None: down but over no pad).

- [ ] **Step 1: Extend the fakes**

- `FakePointerEvent(target, pointer_id=1)` with `target`, `pointerId`, `prevented`, `preventDefault()`.
- `FakeElement`: `dataset` (a `SimpleNamespace`, empty by default; constructor keyword `**dataset`), `closest(selector)`
  that returns `self` when `selector` is `"[data-<name>]"` and `dataset` has `<name>`, `"a"` and `tag == "a"`, else
  None; `releasePointerCapture(pointer_id)` recording into `released`; `requestFullscreen()` counting into
  `fullscreen_requests` and returning a `FakePromise`.
- `FakeDocument`: `body = FakeElement("body", tag="body")`, `documentElement = FakeElement("html", tag="html")`,
  `visibilityState = "visible"`, `addEventListener` / `dispatch` like `FakeWindow`.
- `FakeWindow.addEventListener` accepts and ignores extra option arguments (`*_options: object`), as `FakeElement`'s
  does.

- [ ] **Step 2: Write the failing tests** in `tests/web/browser/test_touch_controls.py`

Helper `make_touch()` returns a `SimpleNamespace(bridge, keyboard, touch, unlocks, pads)` where `pads` maps each code
to a `FakeElement(tag="button", code=<code>)` and `unlocks` counts `unlock_audio` calls. Helpers `down(t, code, pid)`,
`up(t, code, pid)` dispatch `pointerdown`/`pointerup` on `bridge.document.getElementById("touch")`.

```python
def test_the_first_touch_turns_touch_mode_on_and_asks_for_full_screen() -> None:
    t = make_touch()
    assert not t.touch.active
    t.bridge.window.dispatch("touchstart")
    t.bridge.window.dispatch("touchstart")
    body = t.bridge.document.body
    assert body.classList.contains("touch")
    assert t.touch.active
    assert t.bridge.document.documentElement.fullscreen_requests == 1

def test_the_first_touchend_unlocks_audio_once() -> None:
    t = make_touch()
    t.bridge.window.dispatch("touchend")
    t.bridge.window.dispatch("touchend")
    assert t.unlocks == 1

def test_pads_hold_their_keys_while_pressed() -> None:
    t = make_touch()
    event = down(t, "ArrowLeft", 1)
    assert event.prevented
    assert t.pads["ArrowLeft"].released == [1]
    assert t.keyboard.ship_input() == ShipInput(left=True)
    assert t.pads["ArrowLeft"].classList.contains("held")
    up(t, "ArrowLeft", 1)
    assert t.keyboard.ship_input() == ShipInput()
    assert not t.pads["ArrowLeft"].classList.contains("held")

def test_two_pointers_hold_two_pads() -> None:
    t = make_touch()
    down(t, "ArrowRight", 1)
    down(t, "Space", 2)
    assert t.keyboard.ship_input() == ShipInput(right=True, jump=True)
    up(t, "Space", 2)
    assert t.keyboard.ship_input() == ShipInput(right=True)

def test_a_code_stays_held_while_another_pointer_holds_it() -> None:
    t = make_touch()
    down(t, "ArrowUp", 1)
    down(t, "ArrowUp", 2)
    up(t, "ArrowUp", 1)
    assert t.keyboard.ship_input() == ShipInput(accelerate=True)
    up(t, "ArrowUp", 2)
    assert t.keyboard.ship_input() == ShipInput()

def test_sliding_a_thumb_moves_the_hold_to_the_next_pad() -> None:
    t = make_touch()
    down(t, "ArrowLeft", 1)
    dispatch(t, "pointerout", "ArrowLeft", 1)
    dispatch(t, "pointerover", "ArrowRight", 1)
    assert t.keyboard.ship_input() == ShipInput(right=True)
    dispatch(t, "pointerover", "ArrowUp", 7)  # a pointer that is not down holds nothing
    assert t.keyboard.ship_input() == ShipInput(right=True)

def test_each_jump_tap_is_a_fresh_press() -> None:
    t = make_touch()
    down(t, "Space", 1)
    up(t, "Space", 1)
    down(t, "Space", 1)
    assert t.keyboard.consume_presses() == ["Space", "Space"]

def test_cancel_and_hidden_page_release_everything() -> None:
    t = make_touch()
    down(t, "ArrowLeft", 1)
    dispatch(t, "pointercancel", "ArrowLeft", 1)
    assert t.keyboard.ship_input() == ShipInput()
    down(t, "ArrowRight", 2)
    t.bridge.document.visibilityState = "hidden"
    t.bridge.document.dispatch("visibilitychange", None)
    assert t.keyboard.ship_input() == ShipInput()
    assert not t.pads["ArrowRight"].classList.contains("held")

def test_menu_and_mute_buttons_press_their_keys() -> None:
    t = make_touch()
    for code in ("Escape", "KeyM"):
        t.bridge.document.body.dispatch("click", SimpleNamespace(target=FakeElement(tag="button", press=code)))
    t.bridge.document.body.dispatch("click", SimpleNamespace(target=FakeElement()))
    assert t.keyboard.consume_presses() == ["Escape", "KeyM"]

def test_touches_off_the_pads_do_nothing() -> None:
    t = make_touch()
    t.bridge.document.getElementById("touch").dispatch("pointerdown", FakePointerEvent(FakeElement(), 1))
    assert t.keyboard.ship_input() == ShipInput()
```

- [ ] **Step 3: Run them to see them fail**

Run: `uv run python -m pytest tests/web/browser/test_touch_controls.py -v`
Expected: FAIL with `ModuleNotFoundError: ... touch_controls`.

- [ ] **Step 4: Implement `TouchControls`** in `src/synthride/web/browser/touch_controls.py` as described above,
  reading `data-` attributes the way `EditorScreen._data` does (`getattr(element.dataset, name, None)`).

- [ ] **Step 5: Run the whole suite and the checks**

Run: `uv run python -m pytest tests -q && make check`
Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
git add src/synthride/web/browser/touch_controls.py tests/web
git commit -m "Add touch controls that hold the ship's keys"
```

---

### Task 3: Tappable `MenuScreen`

**Files:**
- Modify: `src/synthride/web/ui/menu_screen.py`
- Test: `tests/web/ui/test_menu_screen.py`, and fix the markup asserted in `tests/web/test_game_loop.py:111`

**Interfaces:**
- Consumes: Task 2's `FakeElement(dataset/closest)`.
- Produces: `MenuScreen.BACK = "back"`, `MenuScreen.ANYWHERE = "anywhere"`,
  `MenuScreen.consume_taps() -> list[int | str]` (a level index, `BACK` or `ANYWHERE`, oldest first).

Markup:
- Level items: `<li class="selected" data-level="1">02 · TWO</li>` (class first, then `data-level`).
- The prompt on title, game over and victory:
  `<p class="prompt"><span class="key-text">PRESS ENTER</span><span class="touch-text">TAP TO START</span></p>`.
- Level select starts with `<button class="menu-back" data-back>◀ BACK</button>`.

The `click` listener on `#menu`, in order: inside an `a` → nothing; inside `[data-level]` → `int(level)`; inside
`[data-back]` → `BACK`; otherwise `ANYWHERE`. (`FakeElement.closest("[data-back]")` matches a `dataset.back` of `""`.)

- [ ] **Step 1: Write the failing tests** (and update the two `<li class=...>` assertions in
  `test_level_select_highlights_and_escapes_names` to the new markup, and `test_game_loop.py:111` to
  `'<li class="selected" data-level="1">02'`)

```python
def click(container: FakeElement, target: FakeElement) -> None:
    container.dispatch("click", SimpleNamespace(target=target))

def test_level_items_and_back_button_carry_their_taps() -> None:
    container, menu = make_menu()
    menu.show_level_select(["One", "Two"], selected=0)
    assert '<li class="" data-level="1">02 · TWO</li>' in container.innerHTML
    assert 'data-back' in container.innerHTML

def test_clicks_queue_taps() -> None:
    container, menu = make_menu()
    click(container, FakeElement(tag="li", level="3"))
    click(container, FakeElement(tag="button", back=""))
    click(container, FakeElement())
    assert menu.consume_taps() == [3, MenuScreen.BACK, MenuScreen.ANYWHERE]
    assert menu.consume_taps() == []

def test_clicks_on_links_are_not_taps() -> None:
    container, menu = make_menu()
    click(container, FakeElement(tag="a"))
    assert menu.consume_taps() == []

def test_prompts_have_a_key_and_a_touch_text() -> None:
    container, menu = make_menu()
    for show in (menu.show_title, menu.show_game_over, menu.show_victory):
        show()
        assert '<span class="key-text">PRESS ENTER</span><span class="touch-text">TAP TO START</span>' in container.innerHTML
```

- [ ] **Step 2: Run them to see them fail**

Run: `uv run python -m pytest tests/web/ui/test_menu_screen.py -v`
Expected: the new tests FAIL.

- [ ] **Step 3: Implement** the markup, the listener (registered in `__init__` with `bridge.proxy`) and
  `consume_taps`.

- [ ] **Step 4: Run the whole suite**

Run: `uv run python -m pytest tests -q`
Expected: all PASS (including the updated `test_game_loop.py` assertion and the existing `"PRESS ENTER"` one).

- [ ] **Step 5: Commit**

```bash
git add src/synthride/web/ui/menu_screen.py tests/web
git commit -m "Make the menus tappable"
```

---

### Task 4: `GameLoop` handles menu taps

**Files:**
- Modify: `src/synthride/web/game_loop.py`
- Test: `tests/web/test_game_loop.py`

**Interfaces:**
- Consumes: Task 3's `MenuScreen.consume_taps`, `BACK`, `ANYWHERE`.
- Produces: `GameLoop.handle_tap(tap: int | str) -> None`.

In `tick`, right after the key presses loop: `for tap in self._menu.consume_taps(): self.handle_tap(tap)`.
`handle_tap`, by phase:
- `LEVEL_SELECT`, an `int` in `range(len(session.levels))`: `session.selected_level = tap`, then
  `self.handle_key("Enter")`;
- `LEVEL_SELECT`, `BACK`: `self.handle_key("Escape")`;
- `TITLE`, `GAME_OVER`, `VICTORY`, `ANYWHERE`: `self.handle_key("Enter")`;
- anything else: nothing.

- [ ] **Step 1: Write the failing tests**

Helper `tap(game, target: FakeElement)` dispatches `click` on the `menu` element with that target, then
`game.loop.tick(1 / 60)`.

```python
def test_taps_walk_the_menus(game: SimpleNamespace) -> None:
    tap(game, FakeElement())
    assert game.session.phase is GamePhase.LEVEL_SELECT
    assert game.context.resume.calls == [()]
    tap(game, FakeElement(tag="button", back=""))
    assert game.session.phase is GamePhase.TITLE
    tap(game, FakeElement())
    tap(game, FakeElement(tag="li", level="1"))
    assert game.session.phase is GamePhase.PLAYING
    assert game.session.level_index == 1

@pytest.mark.parametrize("phase", [GamePhase.GAME_OVER, GamePhase.VICTORY])
def test_a_tap_on_an_end_screen_opens_the_level_select(game: SimpleNamespace, phase: GamePhase) -> None:
    game.session.phase = phase
    tap(game, FakeElement())
    assert game.session.phase is GamePhase.LEVEL_SELECT

def test_taps_out_of_place_are_ignored(game: SimpleNamespace) -> None:
    tap(game, FakeElement())  # level select
    tap(game, FakeElement(tag="li", level="9"))  # no such level
    tap(game, FakeElement())  # anywhere on the level select
    assert game.session.phase is GamePhase.LEVEL_SELECT
    assert game.session.selected_level == 0
```

Check how `test_end_screens_return_to_level_select` puts the session in an end phase and do the same if setting
`phase` directly is not how it does it.

- [ ] **Step 2: Run them to see them fail**

Run: `uv run python -m pytest tests/web/test_game_loop.py -v`
Expected: the new tests FAIL.

- [ ] **Step 3: Implement** the loop over taps and `handle_tap`.

- [ ] **Step 4: Run the whole suite**

Run: `uv run python -m pytest tests -q`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add src/synthride/web/game_loop.py tests/web/test_game_loop.py
git commit -m "Let menu taps drive the game"
```

---

### Task 5: Page markup and touch CSS, wired in `Main`

**Files:**
- Modify: `src/synthride/server/html_page_builder.py`, `src/synthride/web/main.py`
- Test: `tests/server/test_html_page_builder.py`, `tests/web/test_main.py`

**Interfaces:**
- Consumes: Task 2's `TouchControls(bridge, keyboard, unlock_audio)`.
- Produces: page elements `#touch` (after `#hud`, so `#hud:not([hidden]) ~ #touch` works), `#mute` (before
  `#loading`), `#rotate`.

Markup, in the body after `#hud`:

```html
<div id="touch">
  <div class="pad-group pad-left">
    <button class="pad" data-code="ArrowLeft" aria-label="Left">◀</button>
    <button class="pad" data-code="ArrowRight" aria-label="Right">▶</button>
  </div>
  <div class="pad-group pad-right">
    <button class="pad" data-code="ArrowDown" aria-label="Brake">▼</button>
    <button class="pad" data-code="ArrowUp" aria-label="Accelerate">▲</button>
    <button class="pad pad-jump" data-code="Space">JUMP</button>
  </div>
  <button class="touch-button touch-menu" data-press="Escape" aria-label="Menu">⏸</button>
</div>
<button id="mute" class="touch-button" data-press="KeyM" aria-label="Mute">🔇</button>
<div id="rotate" class="overlay"><h2 class="headline">ROTATE YOUR PHONE ⟲</h2></div>
```

CSS (the values the spec pins; the rest is the implementer's, in the page's neon style):
- Hidden by default: `#touch, #mute, #rotate, .menu-back, .touch-text { display: none; }`.
- `body.touch #hud:not([hidden]) ~ #touch { display: block; }` with `#touch` fixed, `inset: 0`, `z-index: 2`,
  `pointer-events: none` and its buttons `pointer-events: auto`; `touch-action: none; user-select: none;
  -webkit-user-select: none; -webkit-touch-callout: none` on `#touch` and its buttons.
- `.pad` 68 px square, transparent fill, cyan neon outline; `.pad.held` pink glow; `.pad-jump` twice as wide.
  `.pad-left` bottom-left, `.pad-right` bottom-right, inside
  `calc(16px + env(safe-area-inset-left|right|bottom))`.
- `body.touch #mute { display: block; }`, fixed top right (inside the safe area), `z-index: 4`, and `.touch-menu`
  just left of it.
- `body.touch .hud-bottom { top: 3.2rem; bottom: auto; }` (the gauges move under the top bar).
- `body.touch .keys, body.touch .key-text { display: none; } body.touch .touch-text, body.touch .menu-back
  { display: inline-block; }`; `.menu-back` at the top left of the overlay.
- `.level-list li { cursor: pointer; }` and `body.touch .level-list li:active` takes the `.selected` look.
- `@media (orientation: portrait) { body.touch #rotate { display: flex; z-index: 6; } }`.
- `@media (max-height: 500px) { body.touch .level-columns { display: grid;
  grid-template-columns: repeat(auto-fill, minmax(11rem, 1fr)); width: 100%; } body.touch .level-list
  { display: contents; } body.touch .level-list li { min-height: 44px; display: flex; align-items: center;
  margin: 0; } body.touch .legend { grid-template-columns: repeat(3, minmax(0, 1fr)); } body.touch .logo,
  body.touch .subtitle { font-size: smaller; } }` (the `display: contents` lets the per-column `<ul>`s melt into one
  grid).
- The viewport meta tag becomes `width=device-width, initial-scale=1, viewport-fit=cover`.

`Main.build` creates the keyboard once, then `TouchControls(bridge, keyboard, context.resume)` before the `GameLoop`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/server/test_html_page_builder.py
def test_page_has_the_touch_controls() -> None:
    page = HtmlPageBuilder().build()
    for code in ("ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "Space"):
        assert f'data-code="{code}"' in page
    for element_id in ("touch", "mute", "rotate"):
        assert f'id="{element_id}"' in page
    assert page.index('id="hud"') < page.index('id="touch"')
    assert "viewport-fit=cover" in page
```

In `tests/web/test_main.py`, extend `test_build_wires_a_game_loop_with_bundled_levels` (or add a test beside it):
after `build()`, dispatching `touchend` on the fake window calls the audio context's `resume`
(`FakeAudioContext().resume.calls == [()]`; reach the context the same way the existing test reaches what it
checks).

- [ ] **Step 2: Run them to see them fail**

Run: `uv run python -m pytest tests/server/test_html_page_builder.py tests/web/test_main.py -v`
Expected: the new tests FAIL.

- [ ] **Step 3: Implement** the markup, CSS and wiring.

- [ ] **Step 4: Run the suite and the checks**

Run: `uv run python -m pytest tests -q && make check`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add src/synthride/server/html_page_builder.py src/synthride/web/main.py tests
git commit -m "Lay the touch controls out on the page"
```

---

### Task 6: Phone smoke test and screenshots

**Files:**
- Create: `tests/phone_screenshots.py`
- Modify: `Makefile` (new target `screenshots-phone`), `README.md` (a "On a phone" line in the Play section)

**Interfaces:**
- Consumes: Task 5's page; `snap`, `OUT` and the server start-up pattern from `tests/screenshots.py`.

The script serves the game (not dev mode: no editor) on a free port as `tests/screenshots.py` `main()` does, opens
Chromium with `viewport=ViewportSize(width=844, height=390)`, `device_scale_factor=2`, `is_mobile=True`,
`has_touch=True`, then:
1. waits for `#loading` to detach, hides `#hud-fps` as the other script does;
2. `page.tap("#menu")` and checks `document.body.classList.contains('touch')`;
3. waits 500 ms, `snap(page, "screenshot-mobile-menu.jpg")`;
4. `page.tap('[data-level="0"]')`, then holds ▲ by dispatching a `pointerdown` `PointerEvent` (`pointerId: 1`,
   `bubbles: true`) on `[data-code="ArrowUp"]` through `page.evaluate`;
5. waits until `#hud-progress` width is at least 2 %, `snap(page, "screenshot-mobile.jpg")`.

Make target:

```make
.PHONY: screenshots-phone
screenshots-phone: ## Take phone-sized level select and in-game screenshots into data/ (844x390, touch)
	@uv run playwright install chromium-headless-shell
	@uv run python -m tests.phone_screenshots
```

- [ ] **Step 1: Write the script and the target**

- [ ] **Step 2: Run it**

Run: `make screenshots-phone`
Expected: prints both JPEG paths. Open both and check: level select fits the width with tappable rows and the
BACK button; in game the pads sit in the bottom corners, the gauges under the top bar, ⏸ and 🔇 top right, and
nothing overlaps.

- [ ] **Step 3: Fix any layout problem the screenshots show** in the CSS from Task 5, re-run until both look right,
  then run `uv run python -m pytest tests -q && make check`.

- [ ] **Step 4: Commit**

```bash
git add tests/phone_screenshots.py Makefile README.md data/screenshot-mobile-menu.jpg data/screenshot-mobile.jpg src
git commit -m "Add a phone smoke test with screenshots"
```
