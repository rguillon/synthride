# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""Frostbyte."""

from synthride.core.level import Level
from synthride.core.track_parser import TrackParser

LEVEL = Level(
    name="Frostbyte",
    gravity=22.0,
    oxygen_seconds=50.0,
    fuel_capacity=70.0,
    track=TrackParser().parse([
        # first row = start of the track
        (18, ".. .. N1 N1 N1 N1 .. .."),
        # black ice
        (8, ".. I1 I1 I1 I1 I1 I1 .."),
        # frozen waves
        (1, ".. I1f I1f I1f I1f I1f I1f .."),
        (1, ".. I1b I1b I1b I1b I1b I1b .."),
        (1, ".. I1f I1f I1f I1f I1f I1f .."),
        (1, ".. I1b I1b I1b I1b I1b I1b .."),
        (1, ".. I1f I1f I1f I1f I1f I1f .."),
        (1, ".. I1b I1b I1b I1b I1b I1b .."),
        (1, ".. I1f I1f I1f I1f I1f I1f .."),
        (1, ".. I1b I1b I1b I1b I1b I1b .."),
        (8, ".. I1 I1 I1 I1 I1 I1 .."),
        (4, ".. N1 N1 N1 N1 N1 N1 .."),
        (3, ".. .. .. .. .. .. .. .."),
        (8, ".. N1 N1 N1 N1 N1 N1 .."),
        # ice zigzag
        (8, ".. .. I1 I1 I1 .. .. .."),
        (8, ".. .. .. I1 I1 I1 .. .."),
        (8, ".. .. I1 I1 I1 .. .. .."),
        (8, ".. I1 I1 I1 .. .. .. .."),
        (8, ".. .. I1 I1 I1 .. .. .."),
        (6, ".. .. N1 N1 N1 N1 .. .."),
        (2, ".. .. R1 R1 R1 R1 .. .."),
        # ice stairs
        (2, ".. .. .. .. .. .. .. .."),
        (8, ".. I2 I2 I2 I2 I2 I2 .."),
        (3, ".. .. .. .. .. .. .. .."),
        (8, ".. I3 I3 I3 I3 I3 I3 .."),
        (6, ".. N3 N3 N3 N3 N3 N3 .."),
        # frozen slalom
        (6, ".. N3 N3 K3 K3 K3 K3 .."),
        (8, ".. N3 N3 N3 N3 N3 N3 .."),
        (6, ".. K3 K3 K3 K3 N3 N3 .."),
        (8, ".. N3 N3 N3 N3 N3 N3 .."),
        (6, ".. N3 N3 K3 K3 K3 K3 .."),
        (6, ".. N3 N3 N3 N3 N3 N3 .."),
        (2, ".. O3 O3 O3 O3 O3 O3 .."),
        (6, ".. N3 N3 N3 N3 N3 N3 .."),
        # pushers on ice
        (1, ".. I3fl <3 <3 <3 <3 I3fr .."),
        (6, ".. I3l <3 <3 <3 <3 I3r .."),
        (7, ".. I3l I3 I3 I3 I3 I3r .."),
        (7, ".. I3l >3 >3 >3 >3 I3r .."),
        (7, ".. I3l I3 I3 I3 I3 I3r .."),
        (6, ".. I3l <3 <3 <3 <3 I3r .."),
        (1, ".. I3bl <3 <3 <3 <3 I3br .."),
        (6, ".. N3 N3 N3 N3 N3 N3 .."),
        (2, ".. R3 R3 R3 R3 R3 R3 .."),
        (4, ".. N3 N3 N3 N3 N3 N3 .."),
        # frozen tunnel
        (24, ".. .. I3T I3T I3T I3T .. .."),
        (6, ".. .. N3T N3T N3T N3T .. .."),
        # icy islands
        (3, ".. .. .. .. .. .. .. .."),
        (6, ".. N3 N3 N3 N3 .. .. .."),
        (3, ".. .. .. .. .. .. .. .."),
        (6, ".. .. .. N2 N2 N2 N2 .."),
        (3, ".. .. .. .. .. .. .. .."),
        (6, ".. N2 N2 N2 N2 .. .. .."),
        (3, ".. .. .. .. .. .. .. .."),
        (6, ".. .. .. N1 N1 N1 N1 .."),
        (6, ".. .. N1 N1 N1 N1 .. .."),
        # glacier switchbacks
        (4, ".. N1 N1 N1 N1 N1 N1 .."),
        (2, ".. R1 R1 R1 R1 R1 R1 .."),
        (2, ".. O1 O1 O1 O1 O1 O1 .."),
        (7, ".. I1 I1 I1 .. .. .. .."),
        (7, ".. .. I1 I1 I1 .. .. .."),
        (7, ".. .. .. I1 I1 I1 .. .."),
        (7, ".. .. .. .. I1 I1 I1 .."),
        (7, ".. .. .. I1 I1 I1 .. .."),
        (7, ".. .. I1 I1 I1 .. .. .."),
        (4, ".. .. N1 N1 N1 N1 .. .."),
        (3, ".. .. .. .. .. .. .. .."),
        (8, ".. N1 N1 N1 N1 N1 N1 .."),
        (10, ".. I1 >1 >1 >1 >1 I1 .."),
        (10, ".. I1 I1 I1 I1 I1 I1 .."),
        (10, ".. I1 <1 <1 <1 <1 I1 .."),
        # last climb
        (1, ".. N1f N1f N1f N1f N1f N1f .."),
        (5, ".. N2 N2 N2 N2 N2 N2 .."),
        (6, ".. K2 K2 K2 K2 N2 N2 .."),
        (8, ".. N2 N2 N2 N2 N2 N2 .."),
        (6, ".. N2 N2 K2 K2 K2 K2 .."),
        (5, ".. .. N2 N2 N2 N2 .. .."),
        (1, ".. .. N1b N1b N1b N1b .. .."),
        # finish line
        (10, ".. .. N1 N1 N1 N1 .. .."),
        (3, ".. .. F1 F1 F1 F1 .. .."),
    ]),
)
