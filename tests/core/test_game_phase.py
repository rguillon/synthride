from synthride.core.game_phase import GamePhase


def test_phases():
    assert GamePhase.TITLE in GamePhase
    assert len(GamePhase) == 7
