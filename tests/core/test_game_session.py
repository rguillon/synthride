import pytest

from synthride.core.game_config import GameConfig
from synthride.core.game_event import GameEvent
from synthride.core.game_phase import GamePhase
from synthride.core.game_session import GameSession
from synthride.core.level import Level
from synthride.core.level_parser import LevelParser
from synthride.core.ship_input import ShipInput

FLAT = "N1 N1 N1 N1 N1 N1 N1 N1"
FORWARD = ShipInput(accelerate=True)
CONFIG = GameConfig()


def make_level(*rows: str, header: str = "") -> Level:
    return LevelParser().parse(header + "---\n" + "\n".join(rows))


def started(*levels: Level) -> GameSession:
    session = GameSession(levels)
    session.start()
    return session


def run(session: GameSession, seconds: float, ship_input: ShipInput = FORWARD) -> list[GameEvent]:
    events = []
    for _ in range(round(seconds * 60)):
        events.extend(session.update(1 / 60, ship_input))
    return events


def run_until(session: GameSession, phase: GamePhase, ship_input: ShipInput = FORWARD) -> list[GameEvent]:
    events = []
    for _ in range(60 * 30):
        events.extend(session.update(1 / 60, ship_input))
        if session.phase is phase:
            return events
    pytest.fail(f"never reached {phase}")


def test_requires_levels():
    with pytest.raises(ValueError):
        GameSession([])


def test_menu_flow():
    session = GameSession([make_level(FLAT), make_level(FLAT)])
    assert session.phase is GamePhase.TITLE
    assert session.update(1, FORWARD) == []
    session.open_level_select()
    assert session.phase is GamePhase.LEVEL_SELECT
    session.select_next_level()
    assert session.selected_level == 1
    session.select_next_level()
    assert session.selected_level == 0
    session.select_previous_level()
    assert session.selected_level == 1
    assert session.start() == [GameEvent.LEVEL_STARTED]
    assert session.phase is GamePhase.PLAYING
    assert session.level_index == 1
    session.return_to_title()
    assert session.phase is GamePhase.TITLE


def test_ship_starts_grounded_at_track_start():
    session = started(make_level(FLAT))
    assert session.ship.grounded
    assert session.ship.position.y == 0.5
    assert session.ship.position.x == 4


def test_idle_ship_stays_put_and_grounded():
    session = started(make_level(FLAT, FLAT))
    assert run(session, 1, ShipInput()) == []
    assert session.ship.grounded
    assert session.ship.position.y == 0.5


def test_reaching_track_end_wins_then_next_level_then_victory():
    session = started(make_level(*[FLAT] * 10), make_level(*[FLAT] * 10))
    events = run(session, 3)
    assert GameEvent.LEVEL_WON in events
    assert session.progress == 1
    events = run(session, CONFIG.level_won_seconds + 0.1, ShipInput())
    assert events == [GameEvent.LEVEL_STARTED]
    assert session.level_index == 1
    assert session.progress < 0.1
    run(session, 3)
    events = run(session, CONFIG.level_won_seconds + 0.1, ShipInput())
    assert events == [GameEvent.GAME_COMPLETED]
    assert session.phase is GamePhase.VICTORY


def test_falling_in_a_gap_costs_a_life_and_restarts_level():
    session = started(make_level(FLAT, *[".. .. .. .. .. .. .. .."] * 30))
    events = run_until(session, GamePhase.DYING)
    assert events[-2:] == [GameEvent.FELL, GameEvent.LIFE_LOST]
    assert session.lives == CONFIG.lives - 1
    assert session.phase is GamePhase.DYING
    assert run(session, CONFIG.dying_seconds + 0.1, ShipInput()) == [GameEvent.LEVEL_STARTED]
    assert session.ship.position.z < 1


def test_losing_all_lives_is_game_over():
    session = started(make_level(FLAT, *[".. .. .. .. .. .. .. .."] * 30))
    events = []
    for _ in range(CONFIG.lives):
        events += run_until(session, GamePhase.DYING)
        events += run(session, CONFIG.dying_seconds + 0.1)
    assert session.lives == 0
    assert events[-1] is GameEvent.GAME_OVER
    assert session.phase is GamePhase.GAME_OVER
    session.start()
    assert session.lives == CONFIG.lives


def test_frontal_wall_crashes():
    session = started(make_level(FLAT, FLAT, "N3 N3 N3 N3 N3 N3 N3 N3"))
    assert GameEvent.CRASHED in run(session, 2)


def test_kill_tile_burns():
    session = started(make_level(FLAT, "K1 K1 K1 K1 K1 K1 K1 K1", FLAT))
    assert GameEvent.BURNED in run(session, 2)


def test_finish_tile_wins_immediately():
    session = started(make_level(FLAT, "F1 F1 F1 F1 F1 F1 F1 F1", *[FLAT] * 20))
    assert GameEvent.LEVEL_WON in run(session, 2)
    assert session.progress < 0.5


def test_boost_slow_and_refuel_events():
    rows = [FLAT] * 2 + ["B1 B1 B1 B1 B1 B1 B1 B1"] + [FLAT] * 3 + ["S1 S1 S1 S1 S1 S1 S1 S1"] + [FLAT] * 3
    rows += ["R1 R1 R1 R1 R1 R1 R1 R1"] + [FLAT] * 3
    events = run(started(make_level(*rows)), 4)
    assert GameEvent.BOOSTED in events
    assert GameEvent.SLOWED in events
    assert GameEvent.REFUELED in events


def test_corner_hit_nudges():
    session = started(make_level(FLAT, FLAT, "N1 N1 N1 N1 N2 N1 N1 N1", *[FLAT] * 5))
    session.ship.position = session.ship.position.with_x(3.75)
    events = run(session, 1.5)
    assert GameEvent.NUDGED in events
    assert GameEvent.CRASHED not in events


def test_jump_and_land():
    session = started(make_level(*[FLAT] * 20))
    events = run(session, 0.05, ShipInput(jump=True)) + run(session, 1.5, ShipInput())
    assert events[:1] == [GameEvent.JUMPED]
    assert GameEvent.LANDED in events


def test_running_out_of_oxygen():
    session = started(make_level(FLAT, header="oxygen: 0.5\n"))
    assert GameEvent.OUT_OF_OXYGEN in run(session, 1, ShipInput())


def test_running_out_of_fuel():
    session = started(make_level(*[FLAT] * 50, header="fuel: 0.5\n"))
    assert GameEvent.OUT_OF_FUEL in run(session, 3)
