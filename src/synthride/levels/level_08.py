# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""Final Frequency."""

from synthride.core.level import Level
from synthride.core.track_parser import TrackParser

LEVEL = Level(
    name="Final Frequency",
    gravity=21.0,
    oxygen_seconds=55.0,
    fuel_capacity=75.0,
    track=TrackParser().parse([
        # first row = start of the track
        (12, ".. .. N1 N1 N1 N1 .. .."),
        (2, ".. .. B1 B1 B1 B1 .. .."),
        (8, ".. N1 N1 N1 N1 N1 N1 .."),
        (4, ".. .. .. .. .. .. .. .."),
        (10, ".. N1 N1 N1 N1 N1 N1 .."),
        # into the tunnel, then up
        (4, ".. .. N1T N1T N1T N1T .. .."),
        (2, ".. .. N1T I1T I1T N1T .. .."),
        (8, ".. .. N1T N1T N1T N1T .. .."),
        (4, ".. .. N1 N1 N1 N1 .. .."),
        (1, ".. .. N1f N1f N1f N1f .. .."),
        (9, ".. .. N2 N2 N2 N2 .. .."),
        (1, ".. .. N2f N2f N2f N2f .. .."),
        (7, ".. .. N3 N3 N3 N3 .. .."),
        (2, ".. .. R3 R3 R3 R3 .. .."),
        (8, ".. .. N3 N3 N3 N3 .. .."),
        # split path over the void
        (10, ".. N3 N3 .. .. N3 N3 .."),
        (8, ".. K3 N3 .. .. N3 K3 .."),
        (10, ".. N3 N3 .. .. N3 N3 .."),
        (6, ".. N3 N3 N3 N3 N3 N3 .."),
        (3, ".. .. .. .. .. .. .. .."),
        (10, ".. .. N2 N2 N2 N2 .. .."),
        # ice and pushers
        (8, ".. I2 I2 I2 I2 I2 I2 .."),
        (8, ".. I2 >2 >2 >2 >2 I2 .."),
        (8, ".. I2 I2 I2 I2 I2 I2 .."),
        (8, ".. I2 <2 <2 <2 <2 I2 .."),
        (6, ".. N2 N2 N2 N2 N2 N2 .."),
        (2, ".. N2 O2 O2 O2 O2 N2 .."),
        (6, ".. N2 N2 N2 N2 N2 N2 .."),
        # jump pad to the high wire
        (2, ".. .. J2 J2 J2 J2 .. .."),
        (4, ".. .. .. .. .. .. .. .."),
        (16, ".. .. .. N4 N4 .. .. .."),
        (8, ".. .. .. .. N4 N4 .. .."),
        (8, ".. .. .. N4 N4 .. .. .."),
        (8, ".. .. N4 N4 .. .. .. .."),
        (8, ".. .. .. N4 N4 .. .. .."),
        (2, ".. .. .. R4 R4 .. .. .."),
        (6, ".. .. N4 N4 N4 N4 .. .."),
        (5, ".. .. .. .. .. .. .. .."),
        (12, ".. N2 N2 N2 N2 N2 N2 .."),
        # round tunnel slalom
        (6, ".. N2A N2A N2A N2A N2A N2A .."),
        (6, ".. K2A N2A N2A N2A N2A N2A .."),
        (6, ".. N2A N2A N2A N2A N2A K2A .."),
        (6, ".. N2A N2A K2A K2A N2A N2A .."),
        (6, ".. N2A N2A N2A N2A N2A N2A .."),
        (4, ".. N2 N2 N2 N2 N2 N2 .."),
        # the furnace stairs
        (8, ".. K1 N1 N1 N1 N1 K1 .."),
        (1, ".. K1f N1f N1f N1f N1f K1f .."),
        (7, ".. K2 N2 N2 N2 N2 K2 .."),
        (1, ".. K2f N2f N2f N2f N2f K2f .."),
        (7, ".. K3 N3 N3 N3 N3 K3 .."),
        (2, ".. K3 B3 B3 B3 B3 K3 .."),
        (8, ".. K3 N3 N3 N3 N3 K3 .."),
        (6, ".. .. .. .. .. .. .. .."),
        (10, ".. N1 N1 N1 N1 N1 N1 .."),
        (2, ".. N1 R1 R1 R1 R1 N1 .."),
        (6, ".. N1 N1 N1 N1 N1 N1 .."),
        # square tunnel run with a slow patch
        (4, ".. N1T N1T N1T N1T N1T N1T .."),
        (2, ".. N1T S1T S1T S1T S1T N1T .."),
        (4, ".. N1T N1T N1T N1T N1T N1T .."),
        (2, ".. N1T N1T B1T B1T N1T N1T .."),
        (10, ".. N1T N1T N1T N1T N1T N1T .."),
        (4, ".. N1 N1 N1 N1 N1 N1 .."),
        # narrow ice ridge
        (8, ".. .. .. I1 I1 .. .. .."),
        (8, ".. .. .. .. I1 I1 .. .."),
        (8, ".. .. .. I1 I1 .. .. .."),
        (6, ".. .. N1 N1 N1 N1 .. .."),
        (2, ".. .. O1 O1 O1 O1 .. .."),
        (6, ".. .. N1 N1 N1 N1 .. .."),
        # stepping stones to the finale
        (6, ".. .. N2 N2 N2 N2 .. .."),
        (3, ".. .. .. .. .. .. .. .."),
        (6, ".. .. N3 N3 N3 N3 .. .."),
        (3, ".. .. .. .. .. .. .. .."),
        (6, ".. .. N4 N4 N4 N4 .. .."),
        (3, ".. .. .. .. .. .. .. .."),
        (2, ".. N4 N4 N4 N4 N4 N4 .."),
        # up to the transmitter, then kick for the finish
        (1, ".. N4f N4f N4f N4f N4f N4f .."),
        (1, ".. N5f N5f N5f N5f N5f N5f .."),
        (6, ".. N6 N6 N6 N6 N6 N6 .."),
        (8, ".. N6 K6 N6 N6 K6 N6 .."),
        (8, ".. K6 N6 N6 N6 N6 K6 .."),
        (2, ".. .. B6 B6 B6 B6 .. .."),
        (7, ".. .. N6 N6 N6 N6 .. .."),
        (1, ".. .. N6f N6f N6f N6f .. .."),
        (6, ".. .. .. .. .. .. .. .."),
        (12, ".. .. N2 N2 N2 N2 .. .."),
        (3, ".. .. F2 F2 F2 F2 .. .."),
    ]),
)
