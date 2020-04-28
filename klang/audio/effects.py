"""Audio effects blocks."""
import math

import numpy as np
import scipy.signal
import samplerate

from config import BUFFER_SIZE, SAMPLING_RATE, KAMMERTON
from klang.audio import NYQUIST_FREQUENCY
from klang.block import Block
from klang.constants import TAU, MONO, STEREO
from klang.math import clip
from klang.audio.oscillators import Lfo
from klang.util import convert_samples_to_int, convert_samples_to_float
from klang.ring_buffer import RingBuffer


def blend(a, b, x):
    """Dry / wet blend two signals together.

    Usage:
        >>> blend(np.zeros(4), np.ones(4), .5)
        array([0.5, 0.5, 0.5, 0.5])
    """
    return (1. - x) * a + x * b


def sub_sample(array, skip):
    """Sub / downsample sample array.

    Usage:
        >>> samples = np.arange(6)
        ... sub_sample(samples, 2)
        array([0, 0, 2, 2, 4, 4])
    """
    return np.repeat(array[..., ::skip], skip, axis=-1)


def bit_crush(samples, nBits):
    """Bit crush samples.

    Usage:
        >>> bit_crush(np.arange(-4, 4), nBits=1)
        array([-4, -4, -2, -2,  0,  0,  2,  2])
    """
    return (samples >> nBits) << nBits


def octave_distortion(samples):
    """Non-linear octaver distortion."""
    return 2. * samples ** 2 - 1.


def tanh_distortion(samples, drive=1.):
    """Tanh distorition. Only odd harmonics."""
    return np.tanh(drive * samples)



class Tremolo(Block):

    """LFO controlled amplitude modulation (AM)."""

    def __init__(self, rate=5., intensity=1.):
        super().__init__(nInputs=3, nOutputs=1)
        _, self.rate, self.intensity = self.inputs
        self.rate.set_value(rate)
        self.intensity.set_value(intensity)

        self.lfo = Lfo(frequency=rate)
        self.lfo.currentPhase = TAU / 4.  # Start from zero

    def update(self):
        # Fetch inputs
        samples = self.input.get_value()
        rate = self.rate.get_value()
        intensity = self.intensity.get_value()

        # Update LFO
        self.lfo.frequency.set_value(rate)
        self.lfo.update()

        # Calculate tremolo envelope in [0., 1.].
        mod = self.lfo.output.get_value()
        env = 1. - clip(intensity, 0., 1.) * mod

        # Set output
        self.output.value = env * samples


class Delay(Block):

    """Simple digital delay."""

    MAX_DELAY = 2.
    """float: Max delay duration / max buffer size."""

    def __init__(self, delay=1., feedback=.1, drywet=.5):
        assert delay <= self.MAX_DELAY
        super().__init__(nInputs=1, nOutputs=1)
        self.feedback = feedback
        self.drywet = drywet

        maxlen = int(self.MAX_DELAY * SAMPLING_RATE)
        delayOffset = int(delay * SAMPLING_RATE)
        self.buffers = {
            MONO: RingBuffer.from_shape(maxlen, offset=delayOffset),
            STEREO: RingBuffer.from_shape((maxlen, STEREO), offset=delayOffset),
        }

    def update(self):
        new = self.input.get_value()
        buf = self.buffers[new.ndim]
        old = buf.read(BUFFER_SIZE).T
        buf.write((new + self.feedback * old).T)
        self.output.set_value(blend(new, old, self.drywet))


class FilterCoefficients:

    """Cache result of filter design function for different frequencies."""

    F_MIN = 20.
    F_MAX = 20000.

    def __init__(self, design_func, *args, **kwargs):
        self.design_func = design_func
        self.args = args
        self.kwargs = kwargs
        self.frequencies = np.logspace(
            np.log2(self.F_MIN),
            np.log2(self.F_MAX),
            num=1000,
            base=2,
        )
        self.coefficients = [
            design_func(*args, Wn=f / NYQUIST_FREQUENCY, **kwargs)
            for f in self.frequencies
        ]

    def get_coefficients(self, frequency):
        i = np.searchsorted(self.frequencies, frequency)
        length = self.frequencies.shape[0]
        return self.coefficients[i.clip(0, length-1)]

    def __str__(self):
        infos = [self.coefficients.design_func.__name__]
        infos.extend('%s' % arg for arg in self.coefficients.args)
        infos.extend('%s=%s' % keyvalue for keyvalue in self.coefficients.kwargs.items())
        return '%s(%s)' % (type(self).__name__, ', '.join(infos))


class _Filter:

    """Chunk filterer. Wrapper for scipy.signal.lfilter functions. Chunk-wise
    filtering with state preservation. Also possible to change filter frequency
    (via FilterCoefficients).

    Notes:
      - We use scipy.signal ba coefficients and not sos (10x faster).
    """

    def __init__(self, design_func, *args, **kwargs):
        self.coefficients = FilterCoefficients(design_func, *args, **kwargs)
        self.currentCoeffs = ([], [])
        self.state = []
        freq = kwargs.get('Wn', .5) * NYQUIST_FREQUENCY
        self.set_frequency(freq)
        self.reset()

    def set_frequency(self, frequency):
        """Set filter cutoff frequency."""
        self.currentCoeffs = self.coefficients.get_coefficients(frequency)

    def reset(self):
        """Reset filter state."""
        self.state = scipy.signal.lfiltic(*self.currentCoeffs, y=[])

    def filter(self, signal):
        """Filter some signal chunk."""
        filteredSignal, self.state = scipy.signal.lfilter(
            *self.currentCoeffs,
            x=signal,
            zi=self.state,
        )
        return filteredSignal

    def __str__(self):
        ret = str(self.coefficients)
        return ret.replace('FilterCoefficients', '_Filter')


class Observer:

    """Check if value of connection changed."""

    def __init__(self, connection):
        assert hasattr(connection, '_value')
        self.connection = connection
        self.prevValue = None

    def did_change(self):
        """Did the value of the connection change?"""
        value = self.connection.get_value()
        if self.prevValue == value:
            return False

        self.prevValue = value
        return True


class Filter(Block):

    """Butterworth filter block."""

    MAX_CHANNELS = STEREO
    """int: Maximum number of channels (for filter initialization)."""

    def __init__(self, *args, frequency=KAMMERTON,
                 design_func=scipy.signal.butter, N=2, btype='lowpass',
                 **kwargs):
        super().__init__(nInputs=2, nOutputs=1)
        _, self.frequency = self.inputs
        self.frequency.set_value(frequency)
        self.filters = [
            _Filter(design_func, *args, N=N, btype=btype, *args, **kwargs)
            for _ in range(self.MAX_CHANNELS)
        ]
        self.listener = Observer(connection=self.frequency)

    def update_frequency(self):
        """Update all internal frequencies to a new cutoff frequency."""
        freq = float(self.frequency.value)  # Assure scalar
        for fil in self.filters:
            fil.set_frequency(freq)

    def update(self):
        if self.listener.did_change():
            self.update_frequency()

        signal = self.input.get_value()
        if signal.ndim == MONO:
            fil = self.filters[0]
            out = fil.filter(signal)
        else:
            out = np.array([
                fil.filter(chunk)
                for fil, chunk in zip(self.filters, signal)
            ])

        self.output.set_value(out)


class Subsampler(Block):

    """Sub sample audio buffer. Soft bit crusher effect."""

    VALID_FACTORS = set(2**i for i in range(1, int(math.log2(BUFFER_SIZE))))

    def __init__(self, factor):
        assert factor in self.VALID_FACTORS
        super().__init__(nInputs=1, nOutputs=1)
        self.factor = factor

    def update(self):
        samples = self.input.get_value()
        subSamples = sub_sample(samples, self.factor)
        self.output.set_value(subSamples)


class Bitcrusher(Block):

    """Bit crusher effect.

    Reduce bit depth resolution.
    """

    def __init__(self, nBits=16):
        assert  0 <= nBits < 16
        super().__init__(nInputs=1, nOutputs=1)
        self.nBits = nBits

    def update(self):
        samples = self.input.get_value()
        samples = convert_samples_to_int(samples)
        samples = bit_crush(samples, self.nBits)
        samples = convert_samples_to_float(samples)
        self.output.set_value(samples)


class OctaveDistortion(Block):

    """Non-linear octaver like distortion."""

    def __init__(self):
        super().__init__(nInputs=1, nOutputs=1)

    def update(self):
        samples = self.input.get_value()
        self.output.set_value(octave_distortion(samples))


class TanhDistortion(Block):
    def __init__(self, drive=1.):
        super().__init__(nInputs=1, nOutputs=1)
        self.drive = drive

    def update(self):
        samples = self.input.get_value()
        self.output.set_value(tanh_distortion(samples, self.drive))


class PitchShifter(Block):

    WINDOW = np.hanning(BUFFER_SIZE)

    def __init__(self, shift=2., dryWet=.5, mode='sinc_fastest'):
        super().__init__(nInputs=1, nOutputs=1)
        self.dryWet = dryWet
        self.resampler = samplerate.CallbackResampler(
            self.callback,
            ratio=1. / shift,
            converter_type=mode,
            channels=1,
        )

    def callback(self):
        return self.input.value * self.WINDOW

    def update(self):
        orig = self.input.value
        shifted = self.resampler.read(BUFFER_SIZE)
        self.output.set_value(blend(orig, shifted, self.dryWet))


class Transformer(Block):

    """Linear signal transformer (scale and offset)."""

    def __init__(self, scale, offset):
        """Args:
            scale (float): Scale factor.
            offset (float): Offset value.
        """
        super().__init__(nInputs=1, nOutputs=1)
        self.scale = scale
        self.offset = offset

    @classmethod
    def from_limits(cls, lower, upper):
        """Create transformer instance from output value boundaries."""
        assert lower < upper
        width = upper - lower
        return cls(scale=width, offset=lower)

    def update(self):
        x = self.input.value
        y = self.scale * x + self.offset
        self.output.set_value(y)
