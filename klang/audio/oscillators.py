"""Oscillator audio blocks."""
from config import BUFFER_SIZE
from klang.audio import DT, get_silence, get_time
from klang.audio.waves import sine
from klang.block import Block
from klang.constants import TAU


class Phasor(Block):

    """Oscillating phase driver."""

    def __init__(self, frequency=1., startPhase=0.):
        """Kwargs:
            frequency (float): Phasor frequency.
            startPhase (float): Starting phase.
        """
        super().__init__(nOutputs=1)
        self.frequency = frequency
        self.output.set_value(startPhase)

    @property
    def currentPhase(self):
        """Current phase of the phasor."""
        return self.output.value

    def update(self):
        delta = TAU * self.frequency * DT * BUFFER_SIZE
        self.output._value += delta
        self.output._value %= TAU

    def __deepcopy__(self, memo):
        return type(self)(
            frequency=self.frequency,
            startPhase=self.currentPhase,
        )


class Oscillator(Block):

    """Wave function oscillator."""

    def __init__(self, frequency=440., wave_func=sine, startPhase=0.,
                 shape=BUFFER_SIZE):
        """Kwargs:
            frequency (float): Oscillator frequency.
            wave_func (function): Wave function: wave_func(phases) -> values.
            startPhase (float): Starting phase.
            shape (int): Output value shape.
        """
        assert shape in {1, BUFFER_SIZE}
        super().__init__(nOutputs=1)
        self.wave_func = wave_func
        self.shape = shape

        silence = get_silence(shape)
        self.output.set_value(silence)
        self.phasor = Phasor(frequency, startPhase)

    @property
    def frequency(self):
        """Get current frequency."""
        return self.phasor.frequency

    @frequency.setter
    def frequency(self, frequency):
        """Set frequency."""
        self.phasor.frequency = frequency

    def sample(self):
        """Calculate current samples."""
        t = get_time(self.shape)
        phase = TAU * self.frequency * t + self.phasor.currentPhase
        return self.wave_func(phase)

    def update(self):
        values = self.sample()
        self.output.set_value(values)
        self.phasor.update()

    def __deepcopy__(self, memo):
        return type(self)(
            frequency=self.frequency,
            wave_func=self.wave_func,
            startPhase=self.phasor.currentPhase,
            shape=self.shape,
        )


class Lfo(Oscillator):

    """Simple low frequency oscillator (LFO). Same as Oscillator but output
    value range is [0., 1.].
    """

    def update(self):
        samples = self.sample()
        self.output.set_value((samples + 1.) / 2.)


class FmOscillator(Oscillator):
    # TODO(atheler): Make me!
    pass


class WavetableOscillator(Oscillator):
    # TODO(atheler): Make me!
    pass


class OvertoneOscillator(Oscillator):
    # TODO(atheler): Make me!
    pass
