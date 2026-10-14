from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DecalStyle:
    """How one layer of markings looks and moves.

    ``drift`` is how many tiles the pattern slides per second, sideways and forward (or up, on a vertical
    sheet). ``pulse`` is the angular frequency of an opacity throb, 0 for a steady glow.
    """

    pattern: str
    drift: tuple[float, float] = (0.0, 0.0)
    opacity: float = 0.8
    pulse: float = 0.0
