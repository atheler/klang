import numpy as np

from config import SAMPLING_RATE, BUFFER_SIZE
from klang.blocks import Block


DT = 1. / SAMPLING_RATE


def sample_linear_envelope(nSamples, slope, start=0.):
    """Sample linear envelope."""
    if slope == np.inf:
        return np.ones(nSamples), 1.

    if slope == -np.inf:
        return np.zeros(nSamples), 0.

    t = DT * np.arange(nSamples + 1)
    signal = (slope * t + start).clip(min=0., max=1.)
    return signal[:-1], signal[-1]


def calculate_slope(duration):
    """Linear slope for given duration."""
    if duration == 0:
        return np.inf

    return 1. / duration


class EnvelopeGenerator(Block):

    """Envelope base class.

    Trigger -> Envelope samples. EnvelopeGenerator implements a rectangular envelope.
    """

    def __init__(self):
        super().__init__(nInputs=1, nOutputs=1)
        self.trigger = self.input
        self.currentLevel = 0.

    def sample(self, nSamples):
        triggered = self.trigger.get_value()
        self.currentLevel = float(triggered)
        return self.currentLevel * np.ones(nSamples)

    def update(self):
        env = self.sample(BUFFER_SIZE)
        self.output.set_value(env)

    @property
    def active(self):
        triggered = self.trigger.get_value()
        return not triggered and self.currentLevel == 0


class AR(EnvelopeGenerator):

    """Linear attack / release envelope."""

    def __init__(self, attackTime, releaseTime):
        super().__init__()
        self.attackTime = attackTime
        self.releaseTime = releaseTime

        self.attackSlope = calculate_slope(attackTime)
        self.releaseSlope = -calculate_slope(releaseTime)

    def sample(self, nSamples):
        triggered = self.trigger.get_value()
        slope = self.attackSlope if triggered else self.releaseSlope
        envelope, self.currentLevel = sample_linear_envelope(
            nSamples,
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
