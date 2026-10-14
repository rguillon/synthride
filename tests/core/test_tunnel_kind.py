from synthride.core.tunnel_kind import TunnelKind


def test_letters():
    assert TunnelKind("T") is TunnelKind.SQUARE
    assert TunnelKind("A") is TunnelKind.ROUND
