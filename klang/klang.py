from klang.audio import INTERVAL
from klang.audio.klanggeber import KlangGeber
from klang.constants import STEREO
from klang.execution import Executor


class Clock:

    """Clock giver."""

    def __init__(self, startTime=0.):
        self.currentTime = startTime

    def __call__(self):
        return self.currentTime

    def step(self, dt):
        self.currentTime += dt


class Klang:

    """Main klang object."""

    def __init__(self, nInputs=0, nOutputs=STEREO, filepath=''):
        self.geber = KlangGeber(nInputs, nOutputs, self.callback, filepath)
        self.executor = Executor(blocks=[
            self.geber.adc,
            self.geber.dac,
        ])
        self.clock = Clock()

        # TODO: How to do message inputs / outputs?

    @property
    def adc(self):
        """Audio input block from KlangGeber."""
        return self.geber.adc

    @property
    def dac(self):
        """Audio output block from KlangGeber."""
        return self.geber.dac

    def callback(self):
        self.executor.execute()
        self.clock.step(dt=INTERVAL)

    def start(self):
        self.executor.update_exec_order()
        self.geber.start()
