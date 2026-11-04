# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""The procedural background music."""

from __future__ import annotations

from typing import TYPE_CHECKING

from synthride.web.audio.music_section import Chord, MusicSection

if TYPE_CHECKING:
    from synthride.web.audio.synth_voices import SynthVoices

_bar = MusicSection.melody_bar

A_MINOR = (57, 60, 64)
F_MAJOR = (53, 57, 60)
C_MAJOR = (48, 52, 55)
G_MAJOR = (55, 59, 62)
D_MINOR = (50, 53, 57)
E_MAJOR = (52, 56, 59)
BB_MAJOR = (46, 50, 53)
D_MAJOR = (50, 54, 57)
E_MINOR = (52, 55, 59)
A_MAJOR = (57, 61, 64)
B_MAJOR = (47, 51, 54)

DRIVING_BASS = (0, 12, 0, 12, 7, 12, 0, 12, 0, 12, 0, 12, 7, 12, 10, 12)
GALLOP_BASS = (0, None, 0, 12, 0, None, 0, 12, 0, None, 0, 12, 7, None, 10, 12)
PULSE_BASS = (0, None, 0, None, 0, None, 0, None, 0, None, 0, None, 0, None, 7, None)
SPARSE_BASS = (0, None, None, None, None, None, 12, None, 7, None, None, None, None, None, None, None)

CHORUS_MELODY = (
    _bar("A4 - C5 - F5 - - - E5 - C5 - A4 - - -"),
    _bar("B4 - D5 - G5 - - - F5 - E5 - D5 - - -"),
    _bar("C5 - E5 - A5 - - - G5 - E5 - - - C5 -"),
    _bar("E5 - - - - - - - . . D5 - C5 - B4 -"),
    _bar("A4 - C5 - F5 - - - E5 - C5 - A4 - - -"),
    _bar("B4 - D5 - G5 - - - A5 - B5 - - - - -"),
    _bar("C6 - - - B5 - G5 - E5 - - - G5 - - -"),
    _bar("G#5 - - - - - - - E5 - - - B4 - D5 -"),
)
DREAM_MELODY = (
    _bar("D5 - - - - - - - F5 - - - E5 - - -"),
    _bar("C5 - - - - - - - - - - - . . . ."),
    _bar("A4 - - - C5 - - - F5 - - - E5 - - -"),
    _bar("D5 - - - - - - - B4 - - - . . . ."),
)
COUNTER_MELODY = (
    _bar("E5 . E5 . A5 . E5 . G5 - E5 - D5 . C5 ."),
    _bar("C5 . C5 . F5 . C5 . E5 - C5 - A4 . G4 ."),
    _bar("G4 . C5 . E5 . G5 . E5 - D5 - C5 . D5 ."),
    _bar("D5 - - - B4 - - - G4 - - - . . . ."),
)

# Second part, in D minor
BRIDGE_MELODY = (
    _bar("D5 - - F5 - - A5 - - F5 - D5 - - - -"),
    _bar("D5 - - F5 - - A#5 - - A5 - F5 - - - -"),
    _bar("C5 - - F5 - - A5 - - C6 - A5 - - - -"),
    _bar("G5 - - E5 - - C5 - - E5 - G5 - - - -"),
)
BRIDGE_RIFF = (
    _bar("A5 . A5 . F5 . D5 . F5 - A5 - D6 - - -"),
    _bar("A#5 . A#5 . F5 . D5 . F5 - A#5 - D6 - - -"),
    _bar("A5 . A5 . F5 . C5 . F5 - A5 - C6 - - -"),
    _bar("G5 . G5 . E5 . C5 . E5 - G5 - E5 - D5 -"),
)
BRIDGE_DREAM = (
    _bar("F5 - - - - - - - D5 - - - C5 - - -"),
    _bar("A5 - - - - - - - - - - - . . . ."),
    _bar("G5 - - - - - - - E5 - - - D5 - - -"),
    _bar("F5 - - - - - - - . . . . . . . ."),
)
BRIDGE_CHORUS = (
    _bar("D5 - F5 - A#5 - - - A5 - F5 - D5 - - -"),
    _bar("E5 - G5 - C6 - - - A#5 - G5 - E5 - - -"),
    _bar("F5 - A5 - D6 - - - C6 - A5 - - - F5 -"),
    _bar("A5 - - - - - - - . . G5 - F5 - E5 -"),
    _bar("D5 - F5 - A#5 - - - A5 - F5 - D5 - - -"),
    _bar("E5 - G5 - C6 - - - D6 - E6 - - - - -"),
    _bar("F6 - - - E6 - C6 - A5 - - - C6 - - -"),
    _bar("C#6 - - - - - - - A5 - - - E5 - G5 -"),
)

# Third part, lifted to E minor
LIFT_MELODY = (
    _bar("E5 - - G5 - - B5 - - G5 - E5 - - - -"),
    _bar("E5 - - G5 - - C6 - - B5 - G5 - - - -"),
    _bar("D5 - - G5 - - B5 - - D6 - B5 - - - -"),
    _bar("A5 - - F#5 - - D5 - - F#5 - A5 - - - -"),
)
LIFT_CHORUS = (
    _bar("G5 - E5 - C6 - - - B5 - G5 - E5 - - -"),
    _bar("A5 - F#5 - D6 - - - B5 - A5 - F#5 - - -"),
    _bar("B5 - G5 - E6 - - - D6 - B5 - - - G5 -"),
    _bar("B5 - - - - - - - . . A5 - G5 - F#5 -"),
    _bar("G5 - E5 - C6 - - - B5 - G5 - E5 - - -"),
    _bar("A5 - F#5 - D6 - - - E6 - F#6 - - - - -"),
    _bar("G6 - - - F#6 - D6 - B5 - - - D6 - - -"),
    _bar("D#6 - - - - - - - B5 - - - F#5 - A5 -"),
)
LIFT_DREAM = (
    _bar("E5 - - - - - - - G5 - - - F#5 - - -"),
    _bar("D5 - - - - - - - F#5 - - - A5 - - -"),
    _bar("B5 - - - - - - - G5 - - - E5 - - -"),
    _bar("B4 - - - - - - - . . . . . . . ."),
)
LIFT_COUNTER = (
    _bar("B5 . B5 . E6 . B5 . D6 - B5 - A5 . G5 ."),
    _bar("G5 . G5 . C6 . G5 . B5 - G5 - E5 . D5 ."),
    _bar("D5 . G5 . B5 . D6 . B5 - A5 - G5 . A5 ."),
    _bar("A5 - - - F#5 - - - D5 - - - . . . ."),
)

# Fourth part, back to A minor
HOME_MELODY = (
    _bar("A5 - - C6 - - E6 - - C6 - A5 - - - -"),
    _bar("G5 - - B5 - - D6 - - B5 - G5 - - - -"),
    _bar("F5 - - A5 - - C6 - - A5 - F5 - - - -"),
    _bar("E5 - - G#5 - - B5 - - G#5 - E5 - - - -"),
)
HOME_DREAM = (
    _bar("A5 - - - - - - - C6 - - - B5 - - -"),
    _bar("A5 - - - - - - - F5 - - - . . . ."),
    _bar("G5 - - - - - - - E5 - - - D5 - - -"),
    _bar("E5 - - - G#5 - - - B5 - - - . . . ."),
)


class SynthMusic:
    """A synthwave song sequenced live: saw bass, detuned pad, lead, and drums, looping over its sections.

    Notes are scheduled slightly ahead of the audio clock every frame, so timing stays tight regardless of
    the frame rate.
    """

    BPM = 104
    STEPS_PER_BAR = 16
    LOOKAHEAD = 0.2
    VOLUME = 0.55
    LEAD_PATTERN = (0, None, 1, None, 2, None, 1, None, 2, None, 1, None, 0, None, None, None)
    VERSE = (A_MINOR, F_MAJOR, C_MAJOR, G_MAJOR)
    BRIDGE = (D_MINOR, BB_MAJOR, F_MAJOR, C_MAJOR)
    LIFT = (E_MINOR, C_MAJOR, G_MAJOR, D_MAJOR)
    CADENCE = (A_MINOR, G_MAJOR, F_MAJOR, E_MAJOR)
    SONG = (
        MusicSection(4, VERSE, PULSE_BASS, snare=False, bass_cutoff_hz=500),  # intro
        MusicSection(8, VERSE, DRIVING_BASS, arpeggio=True),  # verse
        MusicSection(
            8,
            (F_MAJOR, G_MAJOR, A_MINOR, A_MINOR, F_MAJOR, G_MAJOR, C_MAJOR, E_MAJOR),
            GALLOP_BASS,
            CHORUS_MELODY,
            open_hats=True,
        ),  # chorus
        MusicSection(
            8,
            (D_MINOR, A_MINOR, F_MAJOR, G_MAJOR),
            SPARSE_BASS,
            DREAM_MELODY,
            kick=False,
            snare=False,
            bass_cutoff_hz=600,
        ),  # breakdown
        MusicSection(4, VERSE, PULSE_BASS, hats=False, roll=True),  # build-up
        MusicSection(
            8,
            (F_MAJOR, G_MAJOR, A_MINOR, A_MINOR, F_MAJOR, G_MAJOR, C_MAJOR, E_MAJOR),
            DRIVING_BASS,
            CHORUS_MELODY,
            arpeggio=True,
            open_hats=True,
        ),  # chorus, fuller
        MusicSection(8, VERSE, GALLOP_BASS, COUNTER_MELODY),  # second verse
        # Part 2: D minor
        MusicSection(8, BRIDGE, DRIVING_BASS, BRIDGE_MELODY, arpeggio=True),  # bridge
        MusicSection(8, BRIDGE, GALLOP_BASS, BRIDGE_RIFF, open_hats=True),  # riff
        MusicSection(
            8,
            (BB_MAJOR, F_MAJOR, C_MAJOR, D_MINOR),
            SPARSE_BASS,
            BRIDGE_DREAM,
            kick=False,
            snare=False,
            bass_cutoff_hz=600,
        ),  # breakdown
        MusicSection(4, BRIDGE, PULSE_BASS, hats=False, roll=True),  # build-up
        MusicSection(
            8,
            (BB_MAJOR, C_MAJOR, D_MINOR, D_MINOR, BB_MAJOR, C_MAJOR, F_MAJOR, A_MAJOR),
            GALLOP_BASS,
            BRIDGE_CHORUS,
            open_hats=True,
        ),  # chorus
        MusicSection(
            8,
            (BB_MAJOR, C_MAJOR, D_MINOR, D_MINOR, BB_MAJOR, C_MAJOR, F_MAJOR, A_MAJOR),
            DRIVING_BASS,
            BRIDGE_CHORUS,
            arpeggio=True,
            open_hats=True,
        ),  # chorus, fuller
        MusicSection(4, BRIDGE, PULSE_BASS, kick=False, snare=False, hats=False, bass_cutoff_hz=500),  # drop
        # Part 3: a tone up, in E minor
        MusicSection(4, LIFT, PULSE_BASS, snare=False, bass_cutoff_hz=500),  # lift
        MusicSection(8, LIFT, DRIVING_BASS, LIFT_MELODY, arpeggio=True),  # verse
        MusicSection(
            8,
            (C_MAJOR, D_MAJOR, E_MINOR, E_MINOR, C_MAJOR, D_MAJOR, G_MAJOR, B_MAJOR),
            GALLOP_BASS,
            LIFT_CHORUS,
            open_hats=True,
        ),  # chorus
        MusicSection(
            8,
            (C_MAJOR, D_MAJOR, E_MINOR, E_MINOR),
            SPARSE_BASS,
            LIFT_DREAM,
            kick=False,
            snare=False,
            bass_cutoff_hz=600,
        ),  # breakdown
        MusicSection(4, LIFT, PULSE_BASS, hats=False, roll=True),  # build-up
        MusicSection(
            8,
            (C_MAJOR, D_MAJOR, E_MINOR, E_MINOR, C_MAJOR, D_MAJOR, G_MAJOR, B_MAJOR),
            DRIVING_BASS,
            LIFT_CHORUS,
            arpeggio=True,
            open_hats=True,
        ),  # chorus, fuller
        MusicSection(8, LIFT, GALLOP_BASS, LIFT_COUNTER),  # verse, answered
        # Part 4: home in A minor
        MusicSection(8, CADENCE, DRIVING_BASS, HOME_MELODY, arpeggio=True),  # verse
        MusicSection(8, VERSE, GALLOP_BASS, COUNTER_MELODY, open_hats=True),  # verse, answered
        MusicSection(
            8,
            (D_MINOR, F_MAJOR, C_MAJOR, E_MAJOR),
            SPARSE_BASS,
            HOME_DREAM,
            kick=False,
            snare=False,
            bass_cutoff_hz=600,
        ),  # breakdown
        MusicSection(4, VERSE, PULSE_BASS, hats=False, roll=True),  # build-up
        MusicSection(
            8,
            (F_MAJOR, G_MAJOR, A_MINOR, A_MINOR, F_MAJOR, G_MAJOR, C_MAJOR, E_MAJOR),
            DRIVING_BASS,
            CHORUS_MELODY,
            arpeggio=True,
            open_hats=True,
        ),  # finale, the first chorus again
        MusicSection(8, CADENCE, DRIVING_BASS, HOME_MELODY, arpeggio=True, open_hats=True),  # finale, last verse
        MusicSection(4, VERSE, PULSE_BASS, snare=False, bass_cutoff_hz=500),  # outro, back into the intro
    )

    def __init__(self, voices: SynthVoices) -> None:
        """Play the music on ``voices``, stopped and unmuted."""
        self._voices = voices
        voices.output.gain.value = self.VOLUME
        self.playing = False
        self.muted = False
        self._step = 0
        self._next_time = 0.0

    @property
    def step_seconds(self) -> float:
        """The duration of one sixteenth note."""
        return 60 / self.BPM / 4

    @classmethod
    def song_bars(cls) -> int:
        """Return the length of the song, in bars, before it loops."""
        return sum(section.bars for section in cls.SONG)

    @classmethod
    def section_at(cls, bar: int) -> tuple[MusicSection, int]:
        """Return the section playing at song bar ``bar`` and the bar's index within it."""
        bar %= cls.song_bars()
        for section in cls.SONG[:-1]:
            if bar < section.bars:
                return section, bar
            bar -= section.bars
        return cls.SONG[-1], bar

    def start(self) -> None:
        """Resume the audio context and start the music, if not already playing."""
        self._voices.context.resume()
        if not self.playing:
            self.playing = True
            self._step = 0
            self._next_time = self._voices.now + 0.1

    def pause(self) -> None:
        """Freeze the audio clock, and with it the music and every sound still playing."""
        self._voices.context.suspend()

    def resume(self) -> None:
        """Let the audio clock run again after :meth:`pause`."""
        self._voices.context.resume()

    def toggle_mute(self) -> None:
        """Mute or unmute the music."""
        self.muted = not self.muted
        self._voices.output.gain.value = 0 if self.muted else self.VOLUME

    def update(self) -> None:
        """Schedule the notes due within the look-ahead window."""
        if not self.playing:
            return
        horizon = self._voices.now + self.LOOKAHEAD
        if self._next_time < self._voices.now:  # the tab was hidden: skip ahead instead of bursting notes
            self._next_time = self._voices.now + 0.05
        while self._next_time < horizon:
            self.schedule_step(self._step, self._next_time)
            self._step += 1
            self._next_time += self.step_seconds

    def schedule_step(self, step: int, time: float) -> None:
        """Schedule the notes of sixteenth note ``step`` at ``time``."""
        beat = step % self.STEPS_PER_BAR
        section, bar = self.section_at(step // self.STEPS_PER_BAR)
        chord = section.chord(bar)
        self._schedule_bass(section, chord, beat, time)
        self._schedule_drums(section, bar, beat, time)
        if beat == 0:
            self._schedule_pad(chord, time)
        self._schedule_lead(section, chord, bar, beat, time)

    def _schedule_bass(self, section: MusicSection, chord: Chord, beat: int, time: float) -> None:
        offset = section.bass[beat]
        if offset is not None:
            frequency = self._voices.frequency(chord[0] - 24 + offset)
            self._voices.tone("sawtooth", frequency, time, 0.16, 0.22, cutoff_hz=section.bass_cutoff_hz)

    def _schedule_drums(self, section: MusicSection, bar: int, beat: int, time: float) -> None:
        voices = self._voices
        if section.kick and beat % 4 == 0:
            voices.tone("sine", 140, time, 0.3, 0.7, end_hz=40)
        if section.roll:
            interval = 4 >> max(0, bar - section.bars + 3)
            if beat % interval == 0:
                voices.noise(time, 0.12, 0.08 + 0.17 * (bar * 16 + beat) / (section.bars * 16), highpass_hz=1200)
        elif section.snare:
            fill = bar == section.bars - 1 and beat >= 12
            if beat in (4, 12) or fill:
                voices.noise(time, 0.18, 0.25 if beat in (4, 12) else 0.12 + 0.03 * (beat - 12), highpass_hz=1200)
        if section.hats and beat % 2 == 1:
            voices.noise(time, 0.04, 0.08, highpass_hz=7000)
        if section.open_hats and beat % 4 == 2:
            voices.noise(time, 0.12, 0.06, highpass_hz=6000)

    def _schedule_pad(self, chord: Chord, time: float) -> None:
        bar_seconds = self.step_seconds * self.STEPS_PER_BAR
        for note in chord:
            for detune in (-9, 9):
                self._voices.tone(
                    "sawtooth",
                    self._voices.frequency(note),
                    time,
                    bar_seconds,
                    0.035,
                    cutoff_hz=1600,
                    detune=detune,
                    attack=0.4,
                )

    def _schedule_lead(self, section: MusicSection, chord: Chord, bar: int, beat: int, time: float) -> None:
        voices = self._voices
        arpeggio = self.LEAD_PATTERN[beat]
        if section.arpeggio and bar % 4 >= 2 and arpeggio is not None:
            volume = 0.03 if section.melody else 0.05
            voices.tone("square", voices.frequency(chord[arpeggio] + 12), time, 0.22, volume, cutoff_hz=3000)
        note = section.melody_note(bar, beat)
        if note is not None:
            midi, length = note
            duration = length * self.step_seconds * 0.9
            voices.tone("square", voices.frequency(midi), time, duration, 0.05, cutoff_hz=2600, attack=0.01)
            voices.tone("sawtooth", voices.frequency(midi), time, duration, 0.025, cutoff_hz=2000, detune=7)
