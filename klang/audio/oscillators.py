"""Oscillator audio blocks."""
from klang.audio import MONO_SILENCE
from klang.block import Block
from klang.audio.waves import sample_wave


class Oscillator(Block):
    def __init__(self, frequency=440.):
        super().__init__(nInputs=1, nOutputs=1)
        self.frequency = self.input
        self.frequency.set_value(frequency)
        self.output.set_value(MONO_SILENCE)
        self.currentPhase = 0.

    def sample(self):
        freq = self.frequency.get_value()
        samples, self.currentPhase = sample_wave(
            freq,
            self.currentPhase,
        )
        return samples

    def update(self):
        samples = self.sample()
        self.output.set_value(samples)


class Lfo(Oscillator):
    def __init__(self, frequency=1.):
        super().__init__(frequency)

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
