import collections

import numpy as np

from klang.blocks import Block
from klang.envelope import EnvelopeGenerator
from klang.oscillators import Oscillator
from config import BUFFER_SIZE


Note = collections.namedtuple('Note', 'pitch velocity')


class MessageConverter(Block):
    def __init__(self, func):
        super().__init__(nInputs=1, nOutputs=1)
        self.func = func

        self.output.set_value(collections.deque)

    def update(self):
        qIn = self.input.get_value()
        qOut = self.output.get_value()
        while qIn:
            msg = qIn.popleft()
            qOut.append(self.func(msg))


class Voice(Block):
    def __init__(self, oscillator=None, envelope=None):
        super().__init__(nInputs=2, nOutputs=1)
        self.oscillator = oscillator or Oscillator()
        self.envelope = envelope or EnvelopeGenerator()

        self.input.set_value(collections.deque())

    def note_on(self, note):
        assert note.velocity > 0

    def note_off(self, note):
        assert note.velocity == 0
    
    def update(self):
        self.oscillator.update()
        self.envelope.update()

    @property
    def active(self):
        pass


class Synthesiser(Block):

    MAX_VOICES = 24

    def __init__(self):
        super().__init__(nInputs=1, nOutputs=1)
        self.voice
        self.voices = collections.OrderedDict()

    def process_note(self, note):
        if note.pitch not in self.voices:
            # Create new note
            while len(self.voices) > self.MAX_VOICES:
                self.voices.popitem(last=False)

        voice = self.voices.setdefault(note.pitch, Voice())
        voice.envelope.trigger.set_value(note.velocity)

    def update(self):
        queue = self.input.get_value()
        while queue:
            note = queue.popleft()
            self.process_note(note)

        samples = np.zeros(BUFFER_SIZE)
        for voice in self.voices:
            voice.update()
            samples += voice.output.get_value()

        samples /= self.MAX_VOICES
        self.output.set_value(samples)


if __name__ == '__main__':
    #synthesiser = Synthesiser()
    #pool = VoicePool(Voice)
    pool = collections.OrderedDict()
    pool[60] = Voice()
    pool[64] = Voice()
    pool[67] = Voice()

    print(pool.popitem(last=False))

    print(pool)
