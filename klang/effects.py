"""Audio effects blocks."""
import numpy as np
import scipy.signal

from config import BUFFER_SIZE, SAMPLING_RATE
from klang.blocks import Block
from klang.constants import TAU
from klang.math import clip
from klang.oscillators import Oscillator


NYQUIST_FREQUENCY = SAMPLING_RATE // 2


def blend(a, b, x):
    """Dry / wet blend two signals together."""
    return (1. - x) * a + x * b


class Tremolo(Block):

    """LFO controlled amplitude modulation (AM)."""

    def __init__(self, rate=5., intensity=1.):
        super().__init__(nInputs=3, nOutputs=1)
        _, self.rate, self.intensity = self.inputs
        self.rate.set_value(rate)
        self.intensity.set_value(intensity)

        self.lfo = Oscillator(frequency=rate)
        self.lfo.currentPhase = TAU / 4.  # Start from zero

    def update(self):
        # Fetch inputs
        samples = self.input.get_value()
        rate = self.rate.get_value()
        intensity = self.intensity.get_value()

        # Update LFO
        self.lfo.frequency.set_value(rate)
        self.lfo.update()

        # Calculate tremolo envelope. [-1, +1] mod signal gets mapped onto
        # [0., 1.] and then used to subtract from unity. Depending on intensity
        # level.
        mod = self.lfo.output.get_value()
        env = 1. - clip(intensity, 0., 1.) * ((1. + mod) / 2.)

        # Set output
        self.output.value = env * samples


class DelayBuffer:

    """Ring buffer a-like for delaying sample blocks."""

    def __init__(self, shape):
        self.data = np.zeros(shape)
        self.index = 0
        self._cycleLength = shape[0]

    @property
    def cycleLength(self):
        return self._cycleLength

    @cycleLength.setter
    def cycleLength(self, length):
        assert 0 < length <= self.data.shape[0]
        self._cycleLength = length
        self.index %= length

    def peek(self):
        return self.data[self.index].copy()

    def push(self, value):
        self.data[self.index] = value
        self.index = (self.index + 1) % self.cycleLength


class Delay(Block):

    """Simple 2 second delay.

    Untested.

    Todo:
      - Very small delay times
    """

    MAX_DELAY = 2.

    def __init__(self, delay=1., feedback=.1, drywet=.5):
        assert delay <= self.MAX_DELAY
        super().__init__(nInputs=4, nOutputs=1)
        _, self.delay, self.feedback, self.drywet = self.inputs
        self.delay.set_value(delay)
        self.feedback.set_value(feedback)
        self.drywet.set_value(drywet)

        maxlen = self.delay_2_buffer_index(delay)
        self.buffer = DelayBuffer((maxlen, BUFFER_SIZE))

    @staticmethod
    def delay_2_buffer_index(duration):
        """Time duration -> buffer index."""
        return int(duration * SAMPLING_RATE / BUFFER_SIZE)

    def update(self):
        new = self.input.get_value()
        delay = self.delay.get_value()
        feedback = self.feedback.get_value()
        drywet = self.drywet.get_value()

        length = self.delay_2_buffer_index(delay)
        self.buffer.cycleLength = length
        old = self.buffer.peek()
        self.buffer.push(new + feedback * old)

        self.output.set_value(blend(new, old, drywet))


class Filter(Block):

    """Second order Butterworth low pass filter.

    Not tested.
    """

    def __init__(self, frequency=1243., order=2):
        super().__init__(nInputs=2, nOutputs=1)
        _, self.frequency = self.inputs
        self.frequency.set_value(frequency)
        self.order = order

        self.coefficients = None, None

        self.update_coefficients()

    def update_coefficients(self):
        freq = self.frequency.get_value()
        self.coefficients = scipy.signal.butter(
            N=self.order,
            Wn=freq / NYQUIST_FREQUENCY,
            btype='lowpass',
        )
        self.zi = np.zeros(self.order)

    def update(self):
        samples = self.input.get_value()

        out, self.zi = scipy.signal.lfilter(*self.coefficients, x=samples, zi=self.zi)

        self.output.set_value(out)