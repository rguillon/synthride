# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""Laser Lattice."""

from synthride.core.level import Level
from synthride.core.track_parser import TrackParser

LEVEL = Level(
    name="Laser Lattice",
    gravity=21.0,
    oxygen_seconds=52.0,
    fuel_capacity=72.0,
    track=TrackParser().parse([
        # first row = start of the track
        (12, ".. .. N1 N1 N1 N1 .. .."),
        (6, ".. N1 N1 N1 N1 N1 N1 .."),
        # the lattice
        (6, ".. K1 N1 N1 K1 N1 N1 .."),
        (6, ".. N1 N1 K1 N1 N1 K1 .."),
        (6, ".. N1 K1 N1 N1 K1 N1 .."),
        (6, ".. K1 N1 N1 K1 N1 N1 .."),
        (6, ".. N1 N1 N1 N1 N1 N1 .."),
        (4, ".. .. .. .. .. .. .. .."),
        (8, ".. N1 N1 N1 N1 N1 N1 .."),
        # narrowing slalom
        (6, ".. K1 K1 K1 K1 N1 N1 .."),
        (8, ".. N1 N1 N1 N1 N1 N1 .."),
        (6, ".. N1 N1 K1 K1 K1 K1 .."),
        (8, ".. N1 N1 N1 N1 N1 N1 .."),
        (6, ".. K1 K1 K1 K1 N1 N1 .."),
        (8, ".. N1 N1 N1 N1 N1 N1 .."),
        (6, ".. N1 N1 K1 K1 K1 K1 .."),
        (6, ".. N1 N1 N1 N1 N1 N1 .."),
        (2, ".. R1 R1 R1 R1 R1 R1 .."),
        # stepping stones
        (3, ".. .. .. .. .. .. .. .."),
        (6, ".. .. N1 N1 N1 N1 .. .."),
        (3, ".. .. .. .. .. .. .. .."),
        (6, ".. .. N1 N1 N1 N1 .. .."),
        (3, ".. .. .. .. .. .. .. .."),
        (6, ".. .. N1 N1 N1 N1 .. .."),
        (3, ".. .. .. .. .. .. .. .."),
        (6, ".. .. N1 N1 N1 N1 .. .."),
        (6, ".. N1 N1 N1 N1 N1 N1 .."),
        # up the lattice
        (3, ".. .. .. .. .. .. .. .."),
        (8, ".. N2 N2 N2 N2 N2 N2 .."),
        (3, ".. .. .. .. .. .. .. .."),
        (8, ".. N3 N3 N3 N3 N3 N3 .."),
        (6, ".. K3 N3 N3 K3 N3 N3 .."),
        (6, ".. N3 N3 K3 N3 N3 K3 .."),
        (4, ".. N3 K3 N3 N3 K3 N3 .."),
        (6, ".. N3 N3 N3 N3 N3 N3 .."),
        (2, ".. O3 O3 O3 O3 O3 O3 .."),
        (4, ".. N3 N3 N3 N3 N3 N3 .."),
        # ice with pushers both ways
        (8, ".. I3 I3 I3 I3 I3 I3 .."),
        (8, ".. I3 >3 >3 >3 >3 I3 .."),
        (8, ".. I3 <3 <3 <3 <3 I3 .."),
        (1, ".. I3fl I3 I3 I3 I3 I3fr .."),
        (6, ".. I3l I3 I3 I3 I3 I3r .."),
        (1, ".. I3bl I3 I3 I3 I3 I3br .."),
        (6, ".. N3 N3 N3 N3 N3 N3 .."),
        (2, ".. R3 R3 R3 R3 R3 R3 .."),
        (6, ".. N3 N3 N3 N3 N3 N3 .."),
        # round tunnel
        (6, ".. N3A N3A K3A K3A K3A K3A .."),
        (8, ".. N3A N3A N3A N3A N3A N3A .."),
        (6, ".. K3A K3A K3A K3A N3A N3A .."),
        (8, ".. N3A N3A N3A N3A N3A N3A .."),
        (6, ".. N3A N3A K3A K3A K3A K3A .."),
        (6, ".. N3 N3 N3 N3 N3 N3 .."),
        # drop and zigzag
        (4, ".. .. .. .. .. .. .. .."),
        (8, ".. .. N2 N2 N2 N2 .. .."),
        (6, ".. .. .. N2 N2 N2 .. .."),
        (6, ".. .. .. .. N2 N2 N2 .."),
        (6, ".. .. .. N2 N2 N2 .. .."),
        (6, ".. .. N2 N2 N2 .. .. .."),
        (6, ".. N2 N2 N2 .. .. .. .."),
        (6, ".. .. N2 N2 N2 .. .. .."),
        (3, ".. .. .. .. .. .. .. .."),
        (8, ".. .. N1 N1 N1 N1 .. .."),
        # second lattice
        (4, ".. N1 N1 N1 N1 N1 N1 .."),
        (2, ".. R1 R1 R1 R1 R1 R1 .."),
        # lift into the second lattice, kick out of it
        (1, ".. O1f O1f O1f O1f O1f O1f .."),
        (1, ".. O2 O2 O2 O2 O2 O2 .."),
        (6, ".. K2 N2 N2 K2 N2 N2 .."),
        (6, ".. N2 N2 K2 N2 N2 K2 .."),
        (6, ".. N2 K2 N2 N2 K2 N2 .."),
        (6, ".. K2 N2 N2 K2 N2 N2 .."),
        (5, ".. N2 N2 N2 N2 N2 N2 .."),
        (1, ".. N2f N2f N2f N2f N2f N2f .."),
        (4, ".. .. .. .. .. .. .. .."),
        (14, ".. .. N1 N1 N1 N1 .. .."),
        # finish line
        (10, ".. .. N1 N1 N1 N1 .. .."),
        (3, ".. .. F1 F1 F1 F1 .. .."),
    ]),
)
