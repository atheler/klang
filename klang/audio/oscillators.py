"""Oscillator audio blocks."""
import numpy as np
from scipy.signal.waveforms import _chirp_phase

from klang.audio.helpers import DT, INTERVAL, get_time
from klang.audio.waves import sine
from klang.block import Block
from klang.config import BUFFER_SIZE
from klang.constants import TAU
from klang.music.tempo import compute_rate


__all__ = ['Phasor', 'Lfo', 'Oscillator', 'FmOscillator']


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


def sample_phase(frequency, startPhase=0., length=BUFFER_SIZE, dt=DT):
    """Get phase values for a given frequency and a starting phase. Also
    supports an array of frequencies (varying frequency). If so has to be
    BUFFER_SIZE long.

    Args:
        frequency (float or array): Frequency value(s). If varying frequency
            these have to correspond to the length argument.

    Kwargs:
        startPhase (float): Starting phase.
        length (int): Length of returned phase array.
        dt (float): Time interval.

    Returns:
        tuple: Phase array and next starting phase.
    """
    constFrequency = (np.ndim(frequency) == 0)
    if constFrequency:
        t = get_time(length + 1, dt)
        phase = TAU * frequency * t + startPhase
    else:
        phase = np.empty(length + 1)
        phase[0] = startPhase
        phase[1:] = TAU * dt * np.cumsum(frequency) + startPhase

    return phase[:-1], phase[-1] % TAU


class Phasor(Block):

    """Scalar phase oscillator. Outputs a scalar phase value per buffer."""

    def __init__(self, frequency=1., startPhase=0.):
        """Kwargs:
            frequency (float): Initial frequency.
            startPhase (float): Initial phase.
        """
        super().__init__(nInputs=1, nOutputs=1)
        self.frequency, = self.inputs
        self.frequency.set_value(frequency)
        self.currentPhase = startPhase

    def sample(self):
        """Get the next sample."""
        phase = self.currentPhase
        freq = compute_rate(self.frequency.value)
        delta = TAU * freq * INTERVAL
        self.currentPhase = (self.currentPhase + delta) % TAU
        return phase

    def update(self):
        self.output.set_value(self.sample())


class Lfo(Phasor):

    """Simple low frequency oscillator (LFO). Output value range [0., 1.].
    Outputs scalar and not arrays like Oscillator.
    """

    def __init__(self, frequency=1., wave_func=sine, startPhase=0.):
        """Kwargs:
            frequency (float): Initial frequency.
            wave_func (function): Waveform function.
            startPhase (float): Initial phase.
        """
        super().__init__(frequency, startPhase)
        self.wave_func = wave_func

    def sample(self):
        phase = super().sample()
        sample = self.wave_func(phase)
        return .5 * (sample + 1.)


class Oscillator(Block):

    """Audio signal oscillator. Generates an array of audio each buffer. Also
    supports an array as frequency input for varying frequencies (has to be
    BUFFER_SIZE long).
    """

    def __init__(self, frequency=440., wave_func=sine, startPhase=0.):
        """Kwargs:
            frequency (float): Initial frequency.
            wave_func (function): Wave function. Phase -> waveform sample lookup.
            startPhase (float): Start phase.
        """
        super().__init__(nInputs=1, nOutputs=1)
        self.frequency, = self.inputs
        self.frequency.set_value(frequency)
        self.wave_func = wave_func
        self.currentPhase = startPhase

    def sample(self):
        """Get next samples of oscillator and step further."""
        freq = compute_rate(self.frequency.value)
        phase, self.currentPhase = sample_phase(freq, startPhase=self.currentPhase)
        return self.wave_func(phase)

    def update(self):
        self.output.set_value(self.sample())

    def __str__(self):
        return '%s(%.1f Hz)' % (type(self).__name__, self.frequency.value)

    def __deepcopy__(self, memo):
        return type(self)(
            frequency=self.frequency.value,
            wave_func=self.wave_func,
            startPhase=self.currentPhase,
        )


class FmOscillator(Oscillator):

    """Frequency modulation oscillator."""

    def __init__(self, frequency=440., intensity=1., modFrequency=10.,
                 wave_func=sine, startPhase=0.):
        """Kwargs:
            frequency (float): Initial frequency (carrier frequency).
            intensity (float): Modulation intensity.
            modFrequency (float): Modulator frequency.
            wave_func (function): Wave form function.
            startPhase (float): Initial phase.
        """
        super().__init__(frequency, wave_func, startPhase)
        self.intensity = intensity
        self.modulator = Oscillator(modFrequency, wave_func=wave_func)

    def sample(self):
        """Get next samples of oscillator and step further."""
        frequency = self.frequency.value
        phase, self.currentPhase = sample_phase(frequency, startPhase=self.currentPhase)
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
