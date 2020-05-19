from klang.config import BUFFER_SIZE
from klang.audio.helpers import get_silence, get_time
from klang.audio.oscillators import Phasor
from klang.block import Block
from klang.constants import TAU


class Clock(Block):

    """Audio clock signal generator."""

    def __init__(self, frequency, dutyCycle=.1, edge='rising'):
        """Args:
            frequency (float): Clock frequency.

        Kwargs:
            dutyCycle (float): Duty cycle of period (0 < dutyCycle < 1).
            edge (str): Rising or falling signal edge.
        """
        assert 0 < dutyCycle < 1.
        assert edge in {'rising', 'falling'}
        super().__init__(nOutputs=1)
        self.duty = dutyCycle * TAU
        self.edge = edge
        self.output.set_value(get_silence(BUFFER_SIZE))
        self.phasor = Phasor(frequency)

    @property
    def frequency(self):
        """Clock frequency."""
        return self.phasor.frequency

    def update(self):
        t = get_time(BUFFER_SIZE)
        currentPhase = self.phasor.currentPhase
        phase = (TAU * self.frequency * t + currentPhase) % TAU
        if self.edge == 'rising':
            active = (phase < self.duty)
        else:
            active = (phase > self.duty)

        clockSignal = active.astype(int)
        self.output.set_value(clockSignal)
        self.phasor.update()