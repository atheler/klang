"""Envelop generator blocks."""
import abc
import itertools
import math

import numpy as np
import scipy.signal

from config import BUFFER_SIZE, SAMPLING_RATE
from klang.audio import DT, MONO_SILENCE, T, T1, ONES
from klang.block import Block
from klang.connections import MessageInput
from klang.constants import PI


EXP_EPS = 1e-3
"""float: Epsilon precision for exponential envelope curves."""


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


def smoothing_factor(tau, dt):
    """Exponential smoothing factor for FIR low pass filter.

    Args:
        tau (float): Time constant.
        dt (float): Sampling interval.

    Returns:
        float: Smoothing factor.

    Resources:
      - https://en.wikipedia.org/wiki/Low-pass_filter
    """
    return 1. - math.exp(-dt / tau)


def lpf_coefficients(decay, dt):
    """Low pass filter coefficients.

    Args:
        decay (float): Exponential decay time.
        dt (float): Sampling interval.

    Returns:
        tuple: Transfer function coefficients.
    """
    alpha = smoothing_factor(decay, dt)
    numerator = (alpha, )
    denominator = (1., alpha - 1.)
    return numerator, denominator


def filter_low_pass(signal, tau, start=0.):
    """First order low pass filter with initial condition.

    Args:
        signal (array): Signal samples.
        tau (float): Time constant.

    Kwargs:
        start (float): Initial value.

    Returns:
        array: Filtered signal.

    Resources:
      - https://en.wikipedia.org/wiki/Time_constant
      - https://en.wikipedia.org/wiki/Exponential_decay
    """
    coeffs = lpf_coefficients(tau, DT)
    zi = scipy.signal.lfiltic(*coeffs, y=[start], x=[start])
    filteredSignal, _ = scipy.signal.lfilter(*coeffs, signal, zi=zi)
    return filteredSignal


def envelope_curve(target, duration, start=0., mode='exp'):
    """Envelop slope samples. Linear and exponential curve from
    start -> target. Exponential envelope with precision up to EXP_EPS.

    Args:
        target (float): Target value.
        duration (float): Transition duration.

    Kwargs:
        start (float): Initial value.
        mode (str): Envelop curve mode.

    Returns:
        array: Envelop samples.
    """
    assert mode in {'lin', 'exp'}
    deviation = abs(target - start)
    if deviation == 0 or duration <= 0:
        return np.array([target])

    if mode == 'lin':
        #length = int(SAMPLING_RATE * duration)
        length = int(SAMPLING_RATE * duration * min(1., deviation))
        return np.linspace(start, target, length, endpoint=False)

    elif mode == 'exp':
        length = int(SAMPLING_RATE * duration)
        x = target * np.ones(length)
        tau = -duration / math.log(EXP_EPS / deviation)
        return filter_low_pass(x, tau, start)


assert envelope_curve(1., 1., start=0., mode='lin')[0] == 0.


def ads_envelope(attack, decay, sustain=0., start=0., mode='exp'):
    """Attack-decay-sustain phase samples."""
    attackPhase = envelope_curve(
        target=1.,
        duration=attack,
        start=start,
        mode=mode,
    )

    decayPhase = envelope_curve(
        target=sustain,
        duration=decay,
        start=1.,
        mode=mode,
    )

    return np.concatenate([
        attackPhase,
        decayPhase,
    ])


def r_envelope(release, start=0., mode='exp'):
    """Release envelope samples."""
    return envelope_curve(
        target=0.,
        duration=release,
        start=start,
        mode=mode,
    )


def continue_after_end(samples, fill_value, chunkSize=BUFFER_SIZE):
    """Wrap samples into a generator which spits out chunkSize many samples each
    iteration. Continue with fill_value after all samples are depleted.

    Args:
        samples (array): Data samples to wrap.
        fill_value (number): Chunk values after all samples are processed.

    Kwargs:
        chunkSize (int): Size of yielded array chunks.

    Yields:
        array: Chunks.

    Usage:
        >>> samples = [0, 1, 2, 3, 4]
        ... sampleGenerator = continue_after_end(samples, fill_value=9, chunkSize=3)
        ... for i in range(4):
        ...     print(next(sampleGenerator))
        [0 1 2]
        [3 4 9]
        [9 9 9]
        [9 9 9]

    Alternatives:
      - Using itertools.chain instead? Small performance gain...
    """
    samples = np.asarray(samples)
    filler = np.full(chunkSize, fill_value)

    # "Split" `samples` into n chunks of size `chunkSize`
    length = samples.shape[0]
    nChunks = length // chunkSize
    chunks = samples[:nChunks*chunkSize].reshape((nChunks, chunkSize))

    # Go through sample chunks
    yield from chunks

    # Some samples < chunkSize remaining
    rest = length % chunkSize
    if rest > 0:
        crossover = np.array(filler)
        crossover[:rest] = samples[-rest:]
        yield crossover

    # Repeat filler indefinitely
    yield from itertools.repeat(filler)


_CONT = continue_after_end([], 42, 2)
np.testing.assert_equal(next(_CONT), [42, 42])
np.testing.assert_equal(next(_CONT), [42, 42])
np.testing.assert_equal(next(_CONT), [42, 42])

_CONT = continue_after_end([0, 1, 2, 3], 42, 3)
np.testing.assert_equal(next(_CONT), [0, 1, 2])
np.testing.assert_equal(next(_CONT), [3, 42, 42])
np.testing.assert_equal(next(_CONT), [42, 42, 42])

_CONT = continue_after_end([0, 1, 2], 42, 4)
np.testing.assert_equal(next(_CONT), [0, 1, 2, 42])
np.testing.assert_equal(next(_CONT), [42, 42, 42, 42])
np.testing.assert_equal(next(_CONT), [42, 42, 42, 42])


class EnvelopeGenerator(Block):

    """Envelope base class. Trigger messages -> envelope signal. Current
    envelope samples have to be stored in sampleGenerator. EnvelopeGenerator
    implements a simple on-off envelope.
    """

    def __init__(self):
        super().__init__(nInputs=0, nOutputs=1)
        self.inputs = [MessageInput(owner=self)]
        self.output.set_value(MONO_SILENCE)
        self.triggered = False
        self.sampleGenerator = itertools.repeat(MONO_SILENCE)

    @property
    def current_level(self):
        """Get current / latest envelope level."""
        return self.output.get_value()[-1]

    @property
    def active(self):
        """Check if envelope is active."""
        if self.triggered:
            return True

        return self.current_level > 0.

    def dirty(self):
        """Envelope triggered state changed."""
        note = self.input.receive_latest()
        if not note:
            return False

        changed = (note.on != self.triggered)
        self.triggered = note.on
        return changed

    def update_sample_generator(self):
        """Generate new envelope samples."""
        self.sampleGenerator = itertools.repeat(
            ONES if self.triggered else MONO_SILENCE
        )

    def update(self):
        if self.dirty():
            self.update_sample_generator()

        self.output.set_value(next(self.sampleGenerator))

    @abc.abstractmethod
    def __deepcopy__(self, memo):
        pass


class AR(EnvelopeGenerator):

    """Attack-release envelope generator."""

    def __init__(self, attack, release, mode='exp'):
        super().__init__()
        self.attack = attack
        self.release = release
        self.mode = mode

    def update_sample_generator(self):
        if self.triggered:
            rising = envelope_curve(1., self.attack, start=self.current_level, mode=self.mode)
            self.sampleGenerator = continue_after_end(rising, fill_value=1.)
        else:
            falling = r_envelope(
                self.release,
                start=self.current_level,
                mode=self.mode,
            )
            self.sampleGenerator = continue_after_end(falling, fill_value=0.)

    def __str__(self):
        fmt = '{}(attack={attack}, release={release}, mode={mode})'
        return fmt.format(self.__class__.__name__, **self.__dict__)

    def __deepcopy__(self, memo):
        return type(self)(self.attack, self.release, self.mode)


class ADSR(EnvelopeGenerator):

    """Attack-decay-sustain-release envelope generator."""

    def __init__(self, attack, decay, sustain, release, mode='exp'):
        super().__init__()
        self.attack = attack
        self.decay = decay
        self.sustain = sustain
        self.release = release
        self.mode = mode

    def update_sample_generator(self):
        if self.triggered:
            rising = ads_envelope(
                self.attack,
                self.decay,
                self.sustain,
                start=self.current_level,
                mode=self.mode,
            )
            self.sampleGenerator = continue_after_end(rising, fill_value=self.sustain)
        else:
            falling = r_envelope(
                self.release,
                start=self.current_level,
                mode=self.mode,
            )
            self.sampleGenerator = continue_after_end(falling, fill_value=0.)

    def __str__(self):
        fmt = '{}(attack={attack}, decay={decay}, sustain={sustain}, release={release}, mode={mode})'
        return fmt.format(self.__class__.__name__, **self.__dict__)

    def __deepcopy__(self, memo):
        return type(self)(self.attack, self.decay, self.sustain, self.release, self.mode)


class D(EnvelopeGenerator):

    """Decay to zero only envelope generator."""

    def __init__(self, decay, mode='exp'):
        super().__init__()
        self.decay = decay
        self.mode = mode

    def update_sample_generator(self):
        if not self.triggered:
            return

        self.triggered = False
        pulseEnv = envelope_curve(target=0., duration=self.decay, start=1., mode=self.mode)
        self.sampleGenerator = continue_after_end(pulseEnv, fill_value=0.)

    def __str__(self):
        fmt = '{}(decay={decay}, mode={mode})'
        return fmt.format(self.__class__.__name__, **self.__dict__)

    def __deepcopy__(self, memo):
        return type(self)(self.decay, self.mode)
