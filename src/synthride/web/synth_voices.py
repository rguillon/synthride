# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""Procedural WebAudio instruments."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from synthride.web.js_bridge import JsBridge, JsObject


class SynthVoices:
    """Procedural WebAudio instruments: enveloped oscillators and filtered noise bursts."""

    SILENCE = 0.0001
    NOISE_SECONDS = 0.5

    def __init__(self, bridge: JsBridge, context: JsObject, destination: JsObject, seed: int = 7) -> None:
        """Play on ``context``, into ``destination``, with noise seeded by ``seed``."""
        self.context = context
        self.output = context.createGain()
        self.output.connect(destination)
        rng = random.Random(seed)  # noqa: S311
        frames = int(context.sampleRate * self.NOISE_SECONDS)
        self._noise = context.createBuffer(1, frames, context.sampleRate)
        self._noise.getChannelData(0).set(bridge.float32_array([rng.uniform(-1, 1) for _ in range(frames)]))

    @property
    def now(self) -> float:
        """The audio context's current time, in seconds."""
        return self.context.currentTime

    @staticmethod
    def frequency(midi_note: float) -> float:
        """Return the frequency of a MIDI note, in hertz."""
        return 440.0 * 2 ** ((midi_note - 69) / 12)

    def tone(  # noqa: PLR0913
        self,
        wave: str,
        start_hz: float,
        start: float,
        duration: float,
        volume: float,
        *,
        end_hz: float | None = None,
        cutoff_hz: float | None = None,
        detune: float = 0.0,
        attack: float = 0.005,
    ) -> None:
        """Play an enveloped oscillator note, optionally sliding to ``end_hz`` and low-pass filtered."""
        context = self.context
        oscillator = context.createOscillator()
        oscillator.type = wave
        oscillator.detune.value = detune
        oscillator.frequency.setValueAtTime(start_hz, start)
        if end_hz is not None:
            oscillator.frequency.exponentialRampToValueAtTime(end_hz, start + duration)
        envelope = self._envelope(start, duration, volume, attack)
        if cutoff_hz is None:
            oscillator.connect(envelope)
        else:
            oscillator.connect(self._filter("lowpass", cutoff_hz)).connect(envelope)
        oscillator.start(start)
        oscillator.stop(start + duration + 0.05)

    def noise(self, start: float, duration: float, volume: float, highpass_hz: float = 0.0) -> None:
        """Play an enveloped noise burst, optionally high-pass filtered."""
        source = self.context.createBufferSource()
        source.buffer = self._noise
        envelope = self._envelope(start, duration, volume, attack=0.001)
        if highpass_hz:
            source.connect(self._filter("highpass", highpass_hz)).connect(envelope)
        else:
            source.connect(envelope)
        source.start(start, 0, min(duration + 0.05, self.NOISE_SECONDS))

    def _envelope(self, start: float, duration: float, volume: float, attack: float) -> JsObject:
        gain = self.context.createGain()
        gain.gain.setValueAtTime(self.SILENCE, start)
        gain.gain.exponentialRampToValueAtTime(volume, start + attack)
        gain.gain.exponentialRampToValueAtTime(self.SILENCE, start + duration)
        gain.connect(self.output)
        return gain

    def _filter(self, kind: str, frequency_hz: float) -> JsObject:
        biquad = self.context.createBiquadFilter()
        biquad.type = kind
        biquad.frequency.value = frequency_hz
        return biquad
