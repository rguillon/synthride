from __future__ import annotations

from synthride.web.synth_voices import SynthVoices


class SynthMusic:
    """A looping synthwave track sequenced live: saw bass arpeggio, detuned pad, lead, and drums.

    Notes are scheduled slightly ahead of the audio clock every frame, so timing stays tight regardless of
    the frame rate.
    """

    BPM = 104
    STEPS_PER_BAR = 16
    LOOKAHEAD = 0.2
    VOLUME = 0.55
    # Am - F - C - G, as MIDI notes.
    CHORDS = ((57, 60, 64), (53, 57, 60), (48, 52, 55), (55, 59, 62))
    BASS_PATTERN = (0, 12, 0, 12, 7, 12, 0, 12, 0, 12, 0, 12, 7, 12, 10, 12)
    LEAD_PATTERN = (0, None, 1, None, 2, None, 1, None, 2, None, 1, None, 0, None, None, None)

    def __init__(self, voices: SynthVoices) -> None:
        self._voices = voices
        voices.output.gain.value = self.VOLUME
        self.playing = False
        self.muted = False
        self._step = 0
        self._next_time = 0.0

    @property
    def step_seconds(self) -> float:
        return 60 / self.BPM / 4

    def start(self) -> None:
        self._voices.context.resume()
        if not self.playing:
            self.playing = True
            self._step = 0
            self._next_time = self._voices.now + 0.1

    def toggle_mute(self) -> None:
        self.muted = not self.muted
        self._voices.output.gain.value = 0 if self.muted else self.VOLUME

    def update(self) -> None:
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
        voices, beat = self._voices, step % self.STEPS_PER_BAR
        bar = step // self.STEPS_PER_BAR
        chord = self.CHORDS[bar % len(self.CHORDS)]
        root = chord[0] - 24
        voices.tone("sawtooth", voices.frequency(root + self.BASS_PATTERN[beat]), time, 0.16, 0.22, cutoff_hz=900)
        if beat % 4 == 0:
            voices.tone("sine", 140, time, 0.3, 0.7, end_hz=40)
        if beat in (4, 12):
            voices.noise(time, 0.18, 0.25, highpass_hz=1200)
        if beat % 2 == 1:
            voices.noise(time, 0.04, 0.08, highpass_hz=7000)
        if beat == 0:
            bar_seconds = self.step_seconds * self.STEPS_PER_BAR
            for note in chord:
                for detune in (-9, 9):
                    voices.tone(
                        "sawtooth",
                        voices.frequency(note),
                        time,
                        bar_seconds,
                        0.035,
                        cutoff_hz=1600,
                        detune=detune,
                        attack=0.4,
                    )
        lead = self.LEAD_PATTERN[beat]
        if bar % 4 >= 2 and lead is not None:
            voices.tone("square", voices.frequency(chord[lead] + 12), time, 0.22, 0.05, cutoff_hz=3000)
