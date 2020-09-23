"""Audio effects blocks."""
from typing import Tuple, Callable
import functools
import math

import numpy as np
import scipy.signal
import samplerate

from klang.audio.filters import BackwardCombFilter
from klang.audio.helpers import NYQUIST_FREQUENCY, get_silence
from klang.audio.oscillators import Oscillator, PwmOscillator
from klang.audio.waves import square
from klang.audio.wavfile import convert_samples_to_float, convert_samples_to_int
from klang.block import Block
from klang.composite import Composite
from klang.config import BUFFER_SIZE, SAMPLING_RATE, KAMMERTON
from klang.connections import Input, Relay
from klang.constants import PI, TAU, INF, MONO, STEREO
from klang.math import clip, blend, linear_mapping
from klang.music.tempo import compute_duration, TimeOrNoteValue
from klang.primes import find_next_primes
from klang.ring_buffer import RingBuffer


__all__ = [
    'Gain', 'Tremolo', 'Delay', 'AudioSplitter', 'AudioCombiner', 'StereoDelay',
    'Filter', 'Subsampler', 'Bitcrusher', 'OctaveDistortion', 'TanhDistortion',
    'PitchShifter', 'Transformer', 'Reverb',
]


@functools.lru_cache()
def low_pass_coefficients(frequency: float) -> Tuple[list, list]:
    """Filter coefficients for single pole low pass IIR filter. For decay use
    frequency = 1. / decay. 0 and INF are supported as well.

    Args:
        frequency: Unnormalized cutoff frequency.

    Returns:
        Numerator / denominator coefficients.

    Resources:
        - https://tomroelandts.com/articles/low-pass-single-pole-iir-filter
    """
    if frequency == 0:
        return [0.], [1., -1.]

    if frequency == INF:
        return [1.], [1., 0.]

    a1 = -math.exp(-TAU * frequency / SAMPLING_RATE)
    b0 = 1. - abs(a1)
    return [b0], [1., a1]


class Gain(Block):

    """Simple gain block."""

    def __init__(self, gain=1.):
        super().__init__(nInputs=2, nOutputs=1)
        _, self.gain = self.inputs
        self.gain.set_value(gain)

    def update(self):
        gain = self.gain.value
        samples = self.input.value
        self.output.set_value(gain * samples)


class Tremolo(Composite):

    """LFO controlled amplitude modulation.

    Support for different active phases (dutyCycle) and curve shape
    (smoothness).

    Attributes:
        rate: Frequency relays to lfo.
        depth: Value input for tremolo intensity.
        smoothness: Value input for envelope shape.
        dutyCycle: dutyCycle relays to lfo.
        lfo: Pulse width modulation lfo.
        zi: Low pass filter state.
    """

    def __init__(self, rate: TimeOrNoteValue = 3., depth: float = .8,
                 smoothness: float = 1., dutyCycle: float = .5):
        """Kwargs:
            rate: Rate of tremolo.
            depth: Intensity of amplitude modulation.
            smoothness: Curve shape. 0. -> sine-like, 1. -> square.
            dutyCycle: Active phase duration.
        """
        super().__init__(nOutputs=1)
        self.inputs = [
            Input(owner=self),
            Relay(owner=self),
            Input(owner=self),
            Input(owner=self),
            Relay(owner=self),
        ]

        _, self.rate, self.depth, self.smoothness, self.dutyCycle = self.inputs
        self.rate.set_value(rate)
        self.depth.set_value(depth)
        self.smoothness.set_value(smoothness)
        self.dutyCycle.set_value(dutyCycle)

        self.lfo = PwmOscillator(rate)
        self.rate.connect(self.lfo.frequency)
        self.dutyCycle.connect(self.lfo.dutyCycle)
        self.zi = np.zeros(1)

    def update(self):
        # Fetch input values
        depth = self.depth.value
        smoothness = self.smoothness.value
        dutyCycle = self.dutyCycle.value

        # Calculate AM-envelope
        decay = max(1e-6, smoothness * min(dutyCycle, 1. - dutyCycle))
        coeffs = low_pass_coefficients(1. / decay)
        self.lfo.update()
        pwm = self.lfo.output.value
        filteredPwm, self.zi = scipy.signal.lfilter(*coeffs, pwm, zi=self.zi)
        env = (1. - depth) + depth * (.5 + .5 * filteredPwm)

        # Apply
        x = self.input.value
        self.output.set_value(env * x)


class Delay(Block):

    """Simple digital mono delay."""

    MAX_TIME = 2.
    """float: Max delay time / max buffer size."""

    def __init__(self, time=1., feedback=.1, drywet=.5):
        """Kwargs:
            time (float or Note): Delay time.
            feedback (float): Amount of feedback.
            drywet (float): Mixture between dry and effected signal.
        """
        self.validate_delay_time(time)
        super().__init__(nInputs=1, nOutputs=1)
        self.feedback = feedback
        self.drywet = drywet

        time = compute_duration(time)
        length = int(time * SAMPLING_RATE)
        capacity = int(self.MAX_TIME * SAMPLING_RATE)

        self.ring = RingBuffer(length, capacity)

    def validate_delay_time(self, time):
        if time > self.MAX_TIME:
            fmt = 'Delay time %.3f sec to long (max %.3f)!'
            msg = fmt % (time, self.MAX_TIME)
            raise ValueError(msg)

    def update(self):
        new = self.input.get_value()
        if new.ndim != MONO:
            nChannels, _ = new.shape
            new = new.sum(axis=0) / nChannels

        old = self.ring.peek()
        self.ring.extend(new + self.feedback * old)
        self.output.set_value(blend(new, old, self.drywet))


class AudioSplitter(Block):

    """Split incoming multi channel audio to individual mono outputs."""

    def __init__(self, nOutputs):
        super().__init__(nInputs=1, nOutputs=nOutputs)

    def update(self):
        samples = self.input.value
        if samples.ndim == MONO:
            # Broadcast to all channels. No questions asked.
            for output in self.outputs:
                output.set_value(samples)
        else:
            for channel, output in zip(self.input.value, self.outputs):
                output.set_value(channel)


class AudioCombiner(Block):

    """Combine incoming mono signals to one multi channel output."""

    def __init__(self, nInputs):
        super().__init__(nInputs, nOutputs=1)
        silence = get_silence((nInputs, BUFFER_SIZE)).copy()
        self.output.set_value(silence)

    def update(self):
        for input_, buf in zip(self.inputs, self.output.value):
            buf[:] = input_.value


class StereoDelay(Composite):

    """Stereo delay."""

    def __init__(self, leftTime=1., rightTime=1., leftFeedback=.1,
                 rightFeedback=.1, drywet=.5):
        """Kwargs:
            leftTime (float): Left channel delay time.
            rightTime (float): Right channel delay time.
            leftFeedback (float): Left channel feedback amount.
            rightFeedback (float): Right channel feedback amount.
            drywet (float): Mixture between dry and effected signal.
        """
        super().__init__()
        self.inputs = [Relay(owner=self)]
        self.outputs = [Relay(owner=self)]

        splitter = AudioSplitter(nOutputs=STEREO)
        leftDelay = Delay(leftTime, leftFeedback, drywet)
        rightDelay = Delay(rightTime, rightFeedback, drywet)
        combiner = AudioCombiner(nInputs=STEREO)

        self.input.connect(splitter.input)
        splitter.outputs[0] | leftDelay | combiner.inputs[0]
        splitter.outputs[1] | rightDelay | combiner.inputs[1]
        combiner.output.connect(self.output)

        self.update_internal_exec_order()


class FilterCoefficients:

    """Cache result of filter design function for different frequencies."""

    F_MIN = 20.
    """float: Minimum frequency."""

    F_MAX = 20000.
    """float: Maximum frequency."""

    def __init__(self, design_func, *args, **kwargs):
        """Args:
            design_func (function): scipy.signal filter design function.

        *args, **kwargs:
            Arguments for the design function. All args beside Wn. This will be
            set by FilterCoefficients.
        """
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

    """Butterworth filter block.

    TODO:
      - Possible to use lfilter for multi channel audio?
    """

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
    """set: Valid skip factors. Power of 2."""

    def __init__(self, factor):
        """Args:
            factor (int): Sub-sample skip factor. Power of 2.
        """
        assert factor in self.VALID_FACTORS
        super().__init__(nInputs=1, nOutputs=1)
        self.factor = factor

    @staticmethod
    def sub_sample(array, skip):
        """Sub / downsample sample array.

        Usage:
            >>> samples = np.arange(6)
            ... sub_sample(samples, 2)
            array([0, 0, 2, 2, 4, 4])
        """
        return np.repeat(array[..., ::skip], skip, axis=-1)

    def update(self):
        samples = self.input.get_value()
        subSamples = self.sub_sample(samples, self.factor)
        self.output.set_value(subSamples)


class Bitcrusher(Block):

    """Bit crusher effect.

    Reduce bit depth resolution.
    """

    def __init__(self, nBits=16):
        """Kwargs:
            nBits (int): Bit reduction.
        """
        assert  0 <= nBits < 16
        super().__init__(nInputs=1, nOutputs=1)
        self.nBits = nBits

    @staticmethod
    def bit_crush(samples, nBits):
        """Bit crush float samples.

        Usage:
            >>> bit_crush(np.arange(-4, 4), nBits=1)
            array([-4, -4, -2, -2,  0,  0,  2,  2])
        """
        samplesI = convert_samples_to_int(samples)
        crushedSamplesI = (samplesI >> nBits) << nBits
        return convert_samples_to_float(crushedSamplesI)

    def update(self):
        samples = self.input.get_value()
        self.output.set_value(self.bit_crush(samples, self.nBits))


class OctaveDistortion(Block):

    """Non-linear octaver like distortion."""

    def __init__(self):
        super().__init__(nInputs=1, nOutputs=1)

    @staticmethod
    def octave_distortion(samples):
        """Non-linear octaver distortion."""
        return 2. * samples ** 2 - 1.

    def update(self):
        samples = self.input.get_value()
        self.output.set_value(self.octave_distortion(samples))


class TanhDistortion(Block):

    """Tanh distorter."""

    def __init__(self, drive=1.):
        """Kwargs:
            drive (float): Overdrive gain factor.
        """
        super().__init__(nInputs=1, nOutputs=1)
        self.drive = drive

    @staticmethod
    def tanh_distortion(samples, drive=1.):
        """Tanh distortion. Only odd harmonics."""
        return np.tanh(drive * samples)

    def update(self):
        samples = self.input.get_value()
        self.output.set_value(self.tanh_distortion(samples, self.drive))


class PitchShifter(Block):

    """Simple resampler based pitch shifter."""

    WINDOW = np.hanning(BUFFER_SIZE)
    """array: Window samples."""

    def __init__(self, shift=2., dryWet=.5, mode='sinc_fastest'):
        """Kwargs:
            shift (float): Pitch shift ratio.
            dryWet (float): Mixture between dry and effected signal.
            mode (str): Resampler mode.
        """
        super().__init__(nInputs=1, nOutputs=1)
        self.dryWet = dryWet
        self.resampler = samplerate.CallbackResampler(
            self.callback,
            ratio=1. / shift,
            converter_type=mode,
            channels=MONO,
        )

    def callback(self):
        """Resampler callback function."""
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
        """Create transformer instance from output value boundaries assuming
        input ranges from [0., 1.].
        """
        assert lower < upper
        width = upper - lower
        return cls(scale=width, offset=lower)

    @classmethod
    def from_limits_2(cls, lower, upper):
        """Create transformer instance from output value boundaries assuming
        input ranges from [-1., 1.].
        """
        assert lower < upper
        width = upper - lower
        return cls(scale=.5 * width, offset=lower + .5 * width)

    @classmethod
    def from_ranges(cls, xRange=(0., 1.), yRange=(0., 1.)):
        scale, offset = linear_mapping(xRange, yRange)
        return cls(scale, offset)

    def update(self):
        self.output.set_value(
            self.scale * self.input.value + self.offset
        )


class Reverb(Block):

    """Simple comb filter / echo based reverb effect.

    Prime number delay taps.

    TODO:
      - Different gain policies.
      - Bandpass in feedback path of filters
    """

    def __init__(self, decay: float = 1.5, preDelay: float = .03, dryWet: float
                 = .7, nEchos: int = 10, echoType: type = BackwardCombFilter):
        """Kwargs:
            decay: Decay value in seconds (~approx).
            preDelay: Lower bound of all delay times.
            dryWet: Amount of dry and effected audio portion.
            nEchos: Number of echo taps.
            echoType: Filter type for delay taps.
        """
        assert nEchos > 0
        super().__init__(nInputs=1, nOutputs=1)
        self.dryWet = clip(dryWet, 0., 1.)
        self.filters = [
            echoType(k, self.compute_alpha(k / SAMPLING_RATE, decay))
            for k in find_next_primes(nEchos, int(preDelay * SAMPLING_RATE))
        ]

    @staticmethod
    def compute_alpha(delayTime: float, decay: float) -> float:
        """Compute gain value alpha for comb and echo filters.

        Args:
            delayTime: Delay time in seconds.
            decay: Decay rate in seconds.

        Returns:
            alpha gain value.
        """
        if decay <= 0:
            return 0.

        return math.exp(-PI * delayTime / decay)

    def update(self):
        x = self.input.value
        y = self.filters[0].filter(x)
        for fil in self.filters[1:]:
            y += fil.filter(x)

        y /= len(self.filters)
        self.output.set_value(blend(x, y, self.dryWet))


class RingModulator(Composite):

    """LFO modulated ring modulator."""

    def __init__(self, frequency: float = 500., rate: float = 2., amount: float =
                 20, wave_func: Callable = square, dryWet: float = 1.):
        """Kwargs:
            frequency: AM base frequency.
            rate: LFO rate.
            amount: Amount of FM modulation.
            wave_func: LFO wave function.
            dryWet: Blend level.
        """
        super().__init__()
        self.inputs = [
            Input(owner=self), Input(owner=self), Relay(owner=self),
            Input(owner=self), Input(owner=self),
        ]
        self.outputs = [Relay(owner=self)]
        _, self.frequency, self.rate, self.amount, self.dryWet = self.inputs
        self.frequency.set_value(frequency)
        self.rate.set_value(rate)
        self.amount.set_value(amount)
        self.dryWet.set_value(dryWet)

        self.lfo = Oscillator(wave_func=wave_func)
        self.modulator = Oscillator()

        self.rate | self.lfo

    def update(self):
        # Frequency with modulation from lfo
        self.lfo.update()
        freqs = self.frequency.value + self.amount.value * self.lfo.output.value

        # AM envelope from modulator
        self.modulator.frequency.set_value(freqs)
        self.modulator.update()
        amSignal = self.modulator.output.value

        # Blend signals
        x = self.input.value
        y = blend(x, amSignal * x, self.dryWet.value)
        self.output.set_value(y)
