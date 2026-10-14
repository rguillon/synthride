# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""Synthesised sound effects for game events."""

from __future__ import annotations

from typing import TYPE_CHECKING

from synthride.core.game_event import GameEvent

if TYPE_CHECKING:
    from collections.abc import Iterable

    from synthride.web.synth_voices import SynthVoices


class SoundEffects:
    """Synthesised sound effects, one recipe per game event."""

    def __init__(self, voices: SynthVoices) -> None:
        """Play the effects on ``voices``."""
        self._voices = voices
        self._recipes = {
            GameEvent.JUMPED: self._jump,
            GameEvent.DOUBLE_JUMPED: self._double_jump,
            GameEvent.LANDED: self._land,
            GameEvent.NUDGED: self._nudge,
            GameEvent.BOOSTED: self._boost,
            GameEvent.SLOWED: self._slow,
            GameEvent.REFUELED: self._refuel,
            GameEvent.REFILLED_AIR: self._refill_air,
            GameEvent.LAUNCHED: self._launch,
            GameEvent.SKIDDED: self._skid,
            GameEvent.PUSHED: self._push,
            GameEvent.BUMPED: self._bump,
            GameEvent.CRASHED: self._explode,
            GameEvent.BURNED: self._explode,
            GameEvent.FELL: self._fall,
            GameEvent.OUT_OF_FUEL: self._power_down,
            GameEvent.OUT_OF_OXYGEN: self._power_down,
            GameEvent.LEVEL_WON: self._fanfare,
            GameEvent.GAME_COMPLETED: self._fanfare,
            GameEvent.GAME_OVER: self._game_over,
        }

    def play(self, events: Iterable[GameEvent]) -> None:
        """Play the sound of each event that has one."""
        for event in dict.fromkeys(events):
            recipe = self._recipes.get(event)
            if recipe is not None:
                recipe(self._voices.now)

    def _jump(self, now: float) -> None:
        self._voices.tone("square", 220, now, 0.18, 0.12, end_hz=660, cutoff_hz=2500)

    def _double_jump(self, now: float) -> None:
        self._voices.tone("square", 440, now, 0.16, 0.1, end_hz=1320, cutoff_hz=3500)

    def _land(self, now: float) -> None:
        self._voices.tone("sine", 120, now, 0.12, 0.35, end_hz=50)

    def _nudge(self, now: float) -> None:
        self._voices.noise(now, 0.06, 0.25, highpass_hz=2500)

    def _boost(self, now: float) -> None:
        self._voices.tone("sawtooth", 300, now, 0.45, 0.14, end_hz=1400, cutoff_hz=4000)

    def _slow(self, now: float) -> None:
        self._voices.tone("sawtooth", 500, now, 0.4, 0.14, end_hz=120, cutoff_hz=1800)

    def _refuel(self, now: float) -> None:
        for index, note in enumerate((72, 76, 79, 84)):
            self._voices.tone("triangle", self._voices.frequency(note), now + index * 0.06, 0.12, 0.18)

    def _refill_air(self, now: float) -> None:
        self._voices.noise(now, 0.35, 0.12, highpass_hz=1200)
        for index, note in enumerate((79, 76, 83)):
            self._voices.tone("sine", self._voices.frequency(note), now + index * 0.07, 0.16, 0.16)

    def _launch(self, now: float) -> None:
        self._voices.tone("square", 110, now, 0.5, 0.14, end_hz=1320, cutoff_hz=3000)
        self._voices.tone("sine", 70, now, 0.25, 0.35, end_hz=40)

    def _skid(self, now: float) -> None:
        self._voices.noise(now, 0.4, 0.14, highpass_hz=5000)
        self._voices.tone("sine", 2400, now, 0.3, 0.05, end_hz=3200)

    def _push(self, now: float) -> None:
        self._voices.tone("triangle", 330, now, 0.18, 0.15, end_hz=440)
        self._voices.tone("triangle", 330, now + 0.1, 0.18, 0.12, end_hz=440)

    def _bump(self, now: float) -> None:
        self._voices.tone("square", 160, now, 0.1, 0.18, end_hz=90, cutoff_hz=900)

    def _explode(self, now: float) -> None:
        self._voices.noise(now, 0.5, 0.6)
        self._voices.tone("sawtooth", 180, now, 0.7, 0.3, end_hz=30, cutoff_hz=900)

    def _fall(self, now: float) -> None:
        self._voices.tone("triangle", 880, now, 1.0, 0.2, end_hz=60)

    def _power_down(self, now: float) -> None:
        self._voices.tone("square", 440, now, 1.2, 0.15, end_hz=40, cutoff_hz=1500)

    def _fanfare(self, now: float) -> None:
        for index, note in enumerate((69, 73, 76, 81, 85, 88)):
            self._voices.tone("square", self._voices.frequency(note), now + index * 0.09, 0.3, 0.1, cutoff_hz=3500)

    def _game_over(self, now: float) -> None:
        for index, note in enumerate((64, 60, 57, 52)):
            self._voices.tone("sawtooth", self._voices.frequency(note), now + index * 0.25, 0.4, 0.15, cutoff_hz=1200)
