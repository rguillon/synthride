from synthride.core.game_phase import GamePhase
from synthride.core.game_session import GameSession
from synthride.core.level_catalog import LevelCatalog
from synthride.core.ship_input import ShipInput


def test_lists_bundled_levels_in_order():
    names = LevelCatalog().file_names()
    assert len(names) >= 3
    assert names == sorted(names)


def test_all_bundled_levels_parse_and_are_finishable_in_principle():
    for level in LevelCatalog().load_all():
        assert level.name
        assert level.track.row_count > 50
        first_row = [level.track.tile_at(column, 0) for column in range(8)]
        assert any(first_row), f"{level.name} has no tile to start on"


def test_tunnel_vision_can_be_ridden_without_jumping():
    """An autopilot holding full throttle and steering for the centre finishes the level."""
    levels = LevelCatalog().load_all()
    session = GameSession(levels)
    session.selected_level = next(index for index, level in enumerate(levels) if level.name == "Tunnel Vision")
    session.start()
    for _ in range(60 * 60):
        x = session.ship.position.x
        session.update(1 / 60, ShipInput(accelerate=True, left=x > 4.15, right=x < 3.85))
        if session.phase is not GamePhase.PLAYING:
            break
    assert session.phase is GamePhase.LEVEL_WON
