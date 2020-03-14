"""Envelop generator blocks."""
import math

import numpy as np

from config import BUFFER_SIZE
from klang.audio import DT, MONO_SILENCE, T, T1
from klang.blocks import Block
from klang.constants import PI


ONES = np.ones(BUFFER_SIZE)


def calculate_slope(duration):
    """Linear slope for given duration."""
    if duration == 0:
        return np.inf

    return 1. / duration


def sample_linear_envelope(slope, start=0.):
    """Sample linear envelope."""
    if slope == np.inf:
        return ONES, 1.

    if slope == -np.inf:
        return MONO_SILENCE, 0.

    signal = (slope * T1 + start).clip(min=0., max=1.)
    return signal[:-1], signal[-1]


def sample_exponential_decay(decay, t0=0.):
    amp = math.exp(-PI / decay * t0)
    signal = amp * np.exp(-PI / decay * T)
    return signal, t0 + DT * BUFFER_SIZE


class EnvelopeGenerator(Block):

    """Envelope base class.

    Trigger -> Envelope samples. EnvelopeGenerator implements a rectangular envelope.
    """

    def __init__(self):
        super().__init__(nInputs=1, nOutputs=1)
        self.trigger = self.input
        self.currentLevel = 0.
        self.input.set_value(False)
        self.output.set_value(np.zeros(BUFFER_SIZE))

    def sample(self):
        triggered = self.trigger.get_value()
        self.currentLevel = float(triggered)
        return self.currentLevel * ONES

    def update(self):
        env = self.sample()
        self.output.set_value(env)

    @property
    def active(self):
        triggered = self.trigger.get_value()
        if triggered:
            return True

        return self.currentLevel > 0.


class AR(EnvelopeGenerator):

    """Linear attack / release envelope."""

    def __init__(self, attackTime, releaseTime):
        super().__init__()
        self.attackTime = attackTime
        self.releaseTime = releaseTime

        self.attackSlope = calculate_slope(attackTime)
        self.releaseSlope = -calculate_slope(releaseTime)

    def sample(self):
        triggered = self.trigger.get_value()
        slope = self.attackSlope if triggered else self.releaseSlope
        envelope, self.currentLevel = sample_linear_envelope(
            slope,
            self.currentLevel,
        )
        return envelope

    def __str__(self):
        return '%s(attack: %.3f sec, release: %.3f sec)' % (
            self.__class__.__name__,
            self.attackTime,
            self.releaseTime,
        )


class ExpDecay(EnvelopeGenerator):

    """Exponential decay for fast click sounds."""

    def __init__(self, decayTime):
        super().__init__()

        # Prepare data
        t = DT * np.arange(BUFFER_SIZE + 1)
        self.decay = np.exp(-PI / decayTime * t)

    def sample(self):
        triggered = self.trigger.get_value()
        if triggered:
            self.currentLevel = 1.

        samples = self.currentLevel * self.decay
        self.currentLevel = samples[-1]
        return samples[:-1]
