"""Synthesizer audio blocks."""
import collections
import itertools

from klang.blocks import Block
from klang.audio.envelope import EnvelopeGenerator
from klang.audio.oscillators import Oscillator
from klang.music.tunings import EQUAL_TEMPERAMENT
from klang.math import clip
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
        super().__init__(nInputs=0, nOutputs=1)
        self.amplitude = 0.
        self.oscillator = oscillator or Oscillator()
        self.envelope = envelope or EnvelopeGenerator()

    @property
    def frequency(self):
        return self.oscillator.frequency.get_value()

    @property
    def active(self):
        triggered = self.envelope.trigger.get_value()
        env = self.envelope.output.get_value()

        return not triggered and env[-1] == 0.

    def process_note(self, frequency, velocity):
        if velocity != 0.:
            self.amplitude = clip(velocity, 0., 1.)
            self.oscillator.frequency.set_value(frequency)
            self.envelope.trigger.set_value(True)
        else:
            self.envelope.trigger.set_value(False)
    
    def update(self):
        self.oscillator.update()
        osc = self.oscillator.output.get_value()

        self.envelope.update()
        env = self.envelope.output.get_value()

        signal = self.amplitude * env * osc
        self.output.set_value(signal)


class Synthesiser(Block):

    MAX_VOICES = 24

    def __init__(self, temperament=EQUAL_TEMPERAMENT):
        super().__init__(nInputs=1, nOutputs=1)
        self.temperament = temperament

        self.input.set_value(collections.deque())
        self.output.set_value(np.zeros(BUFFER_SIZE))

        self.voices = [Voice() for _  in range(self.MAX_VOICES)]
        self.freeVoice = itertools.cycle(self.voices)

    def play_note(self, note):
        queue = self.input.get_value()
        queue.append(note)

    def process_note(self, note):
        freq = self.temperament.pitch_2_frequency(note.pitch)
        if note.velocity != 0:
            print('Play new note')
            voice = next(self.freeVoice)
            voice.process_note(freq, note.velocity)
        else:
            print('Kill old note')
            for voice in self.voices:
                if voice.frequency == freq:
                    voice.process_note(freq, note.velocity)

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
    import numpy as np
    import matplotlib.pyplot as plt

    from config import SAMPLING_RATE
    from klang.music.chords import CHORDS



    DT = 1. / SAMPLING_RATE
    major = CHORDS['major']


    synthesiser = Synthesiser()

    for pitch in 60 + major:
        note = Note(pitch, velocity=.5)
        synthesiser.play_note(note)

    chunks = []
    for _ in range(10):
        synthesiser.update()
        samples = synthesiser.output.get_value()
        print(len(samples))
        chunks.append(samples)

    signal = np.concatenate(chunks)

    t = DT * np.arange(len(signal))
    plt.plot(t, signal)
    plt.show()
