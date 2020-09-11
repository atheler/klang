"""Oscillator audio blocks."""
import numpy as np
from scipy.signal.waveforms import _chirp_phase

from klang.audio.helpers import DT, INTERVAL, get_time
from klang.audio.waves import sine
from klang.connections import Input
from klang.block import Block
from klang.config import BUFFER_SIZE
from klang.constants import TAU, SCALAR
from klang.math import linear_mapping
from klang.music.tempo import compute_rate


__all__ = ['FmOscillator', 'Lfo', 'Oscillator', 'Phasor', 'PwmOscillator']


def chirp_phase(t, freqStart, tEnd, freqEnd, method='linear', vertex_zero=True):
    """Create chirp phase. Ascending and descending. Same as
    scipy.signal.waveforms._chirp_phase with constant frequency extension for
    t >= tEnd.
    """
    if (tEnd <= t[0]) or (freqStart == freqEnd):
        # Only constant frequency
        return TAU * freqEnd * t

    phase = _chirp_phase(t, f0=freqStart, t1=tEnd, f1=freqEnd, method=method,
                         vertex_zero=vertex_zero)
    if t[-1] < tEnd:
        # Only chirping
        return phase

    # Mixture between chirp and constant frequency
    constFreq = (t >= tEnd)
    mid = constFreq.argmax()
    phaseOffset = phase[mid] - TAU * freqEnd * t[mid]
    phase[mid:] = TAU * freqEnd * t[mid:] + phaseOffset
    return phase


def sample_phase(frequency, startPhase=0.):
    """Get BUFFER_SIZE many phase samples for a given frequency. Also supports
    an array of frequencies (varying frequency). If so has to be BUFFER_SIZE
    long.

    Args:
        frequency (float or array): Frequency value(s). Scalar -> assuming
            constant frequency over the whole buffer. If an array / varying
            frequency has to be BUFFER_SIZE long.

    Kwargs:
        startPhase (float): Value of first phase sample.

    Returns:
        tuple: Phase array and next starting phase.
    """
    constFrequency = (np.ndim(frequency) == 0)
    if constFrequency:
        t = get_time(BUFFER_SIZE + 1, DT)
        phase = TAU * frequency * t + startPhase
    else:
        phase = np.empty(BUFFER_SIZE + 1)
        phase[0] = startPhase
        phase[1:] = TAU * DT * np.cumsum(frequency) + startPhase

    phase = np.mod(phase, TAU)
    return phase[:-1], phase[-1]


class Phasor(Block):

    """Scalar phase oscillator. Outputs a scalar phase value per buffer [0.,
    TAU). Base class of all oscillator. Child classes should overwrite the
    sample(frequency) method.

    Attributes:
        frequency (Input): Frequency input connection.
        currentPhase (float): Current phase state of the phasor.
    """

    def __init__(self, frequency=1., startPhase=0.):
        """Kwargs:
            frequency (float): Initial frequency value..
            startPhase (float): Initial phase value.
        """
        super().__init__(nInputs=1, nOutputs=1)
        self.frequency, = self.inputs
        self.frequency.set_value(frequency)
        self.currentPhase = startPhase

    def sample(self):
        """Get next sample and step phasor further."""
        phase = self.currentPhase
        freq = compute_rate(self.frequency.value)
        self.currentPhase = (TAU * freq * INTERVAL + self.currentPhase) % TAU
        return phase

    def update(self):
        self.output.set_value(self.sample())

    def __str__(self):
        return '%s(%.1f Hz)' % (type(self).__name__, self.frequency.value)

    def __deepcopy__(self, memo):
        return type(self)(
            frequency=self.frequency.value,
            startPhase=self.currentPhase,
        )


class Oscillator(Phasor):

    """Audio signal oscillator. Generates an array of audio each buffer. Also
    supports an array as frequency input for varying frequencies (has to be
    BUFFER_SIZE long).

    Attributes:
        wave_func (function): Circular phase -> value wave from function.
    """

    def __init__(self, frequency=440., wave_func=sine, startPhase=0.):
        """Kwargs:
            frequency (float): Initial frequency value..
            wave_func (function): Wave shape function. Phase -> waveform sample lookup.
            startPhase (float): Initial phase value.
        """
        super().__init__(frequency, startPhase)
        self.wave_func = wave_func

    def sample(self):
        freq = compute_rate(self.frequency.value)
        phase, self.currentPhase = sample_phase(freq, self.currentPhase)
        return self.wave_func(phase)

    def __deepcopy__(self, memo):
        return type(self)(
            frequency=self.frequency.value,
            wave_func=self.wave_func,
            startPhase=self.currentPhase,
        )


class Lfo(Phasor):

    """Simple low frequency oscillator (LFO). Can output scalar or vectorial
    values. Output value range can be controlled with outputRange (ymin, ymax).

    Attributes:
        wave_func (function): Circular phase -> value wave from function.
        shape (int): Number of output samples per buffer.
        outputRange (tuple): Output value range (ymin, ymax).
        scale (float): Linear output transform.
        offset (float): Linear output transform.
    """

    def __init__(self, frequency=1., wave_func=sine, shape=1,
                 outputRange=(0, 1), startPhase=0.):
        """Kwargs:
            frequency (float): Initial frequency value.
            wave_func (function): Wave shape function. Phase -> waveform sample lookup.
            shape (int): Sample output shape. Either 1 (scalar / one sample per
                buffer) or BUFFER_SIZE (full buffer of samples).
            outputRange (tuple): Output value range (ymin, ymax).
            startPhase (float): Initial phase value.
        """
        assert shape in {SCALAR, BUFFER_SIZE}
        super().__init__(frequency, startPhase)
        self.wave_func = wave_func
        self.shape = shape
        self.outputRange = outputRange
        self.scale, self.offset = linear_mapping(xRange=(-1, 1), yRange=outputRange)

    def sample(self):
        freq = compute_rate(self.frequency.value)
        if self.shape == SCALAR:
            phase = self.currentPhase
            self.currentPhase = (TAU * freq * INTERVAL + self.currentPhase) % TAU
        else:
            phase, self.currentPhase = sample_phase(freq, self.currentPhase)

        return self.scale * self.wave_func(phase) + self.offset

    def __deepcopy__(self, memo):
        return type(self)(
            frequency=self.frequency.value,
            wave_func=self.wave_func,
            shape=self.shape,
            outputRange=self.outputRange,
            startPhase=self.currentPhase,
        )


class FmOscillator(Oscillator):

    """Frequency modulation oscillator.

    Attributes:
        intensity (float): FM intensity.
        modulator (Oscillator): Frequency modulator oscillator.
    """

    def __init__(self, frequency=440., intensity=1., modFrequency=10.,
                 wave_func=sine, startPhase=0.):
        """Kwargs:
            frequency (float): Initial frequency value (carrier frequency).
            intensity (float): Modulation intensity.
            modFrequency (float): Modulator frequency.
            wave_func (function): Wave shape function. Phase -> waveform sample lookup.
            startPhase (float): Initial phase value.
        """
        super().__init__(frequency, wave_func, startPhase)
        self.intensity = intensity
        self.modulator = Oscillator(modFrequency, wave_func=wave_func)

    def sample(self):
        """Get next samples of oscillator and step further."""
        freq = compute_rate(self.frequency.value)
        phase, self.currentPhase = sample_phase(freq, startPhase=self.currentPhase)
        modSamples = self.modulator.output.value
        return self.wave_func(phase + self.intensity * modSamples)

    def update(self):
        self.modulator.update()
        samples = self.sample()
        self.output.set_value(samples)

    def __deepcopy__(self, memo):
        return type(self)(
            frequency=self.frequency.value,
            intensity=self.intensity,
            modFrequency=self.modulator.frequency.value,
            wave_func=self.wave_func,
            startPhase=self.currentPhase,
        )


class PwmOscillator(Phasor):

    """Pulse width modulation oscillator.

    Attributes:
        dutyCycle (Input): Duty cycle value input.
    """

    def __init__(self, frequency=440., dutyCycle=.5, startPhase=0.):
        """Kwargs:
            frequency (float): Initial frequency value (carrier frequency).
            dutyCycle (float): Initial duty cycle value.
            startPhase (float): Initial phase value.
        """
        super().__init__(frequency, startPhase)
        self.dutyCycle = Input(owner=self)
        self.dutyCycle.set_value(dutyCycle)
        self.inputs.append(self.dutyCycle)

    def sample(self):
        freq = compute_rate(self.frequency.value)
        phase, self.currentPhase = sample_phase(freq, startPhase=self.currentPhase)
        active = (phase < TAU * self.dutyCycle.value)
        return 2. * active - 1.

    def __deepcopy__(self, memo):
        return type(self)(
            frequency=self.frequency.value,
            dutyCycle=self.dutyCycle.value,
            startPhase=self.currentPhase,
        )


class WavetableOscillator(Oscillator):
    # TODO(atheler): Make me!
    pass


class OvertoneOscillator(Oscillator):
    # TODO(atheler): Make me!
    pass


class Chirper(Block):

    """Chirp oscillator. Frequency ascend or descend."""

    def __init__(self, startFrequency, duration, endFrequency, method='linear',
                 wave_func=sine):
        super().__init__(nOutputs=1)
        self.startFrequency = startFrequency
        self.duration = duration
        self.endFrequency = endFrequency
        self.method = method
        self.wave_func = wave_func
        self.t = get_time(BUFFER_SIZE).copy()

    def reset(self):
        """Reset chirper to start state."""
        self.t = get_time(BUFFER_SIZE).copy()

    def update(self):
        phase = chirp_phase(
            self.t,
            self.startFrequency,
            self.duration,
            self.endFrequency,
            self.method,
        )
        values = self.wave_func(phase)
        self.output.set_value(values)
        self.t += DT * BUFFER_SIZE
