from synthride.core.ship_input import ShipInput


def test_defaults_to_no_command():
    assert ShipInput() == ShipInput(False, False, False, False, False)
