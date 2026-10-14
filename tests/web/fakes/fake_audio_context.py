# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

from tests.web.fakes.fake_js_object import FakeJsObject


class FakeAudioContext(FakeJsObject):
    """A WebAudio context with a controllable clock that counts the sources it starts."""

    def __init__(self) -> None:
        super().__init__("AudioContext")
        self.currentTime = 0.0
        self.sampleRate = 100
        self.oscillators: list[FakeJsObject] = []
        self.noise_sources: list[FakeJsObject] = []

    def createOscillator(self) -> FakeJsObject:  # noqa: N802
        oscillator = FakeJsObject("oscillator")
        self.oscillators.append(oscillator)
        return oscillator

    def createBufferSource(self) -> FakeJsObject:  # noqa: N802
        source = FakeJsObject("buffer-source")
        self.noise_sources.append(source)
        return source
