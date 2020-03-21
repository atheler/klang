"""Synthesizer audio blocks."""
import copy
import itertools
import abc

import numpy as np

from config import BUFFER_SIZE
from klang.audio import MONO_SILENCE
from klang.audio.envelope import sample_exponential_decay, D
from klang.audio.oscillators import sample_wave
from klang.block import Block
from klang.connections import MessageInput


def sample_pitch_decay(frequency, decay, intensity, t0=0.):
    """Sample decaying pitch curve."""
    env, t1 = sample_exponential_decay(decay, t0)
    pitch = frequency * (1. + intensity * env)
    return pitch, t1


def duplicate_voice(voice, number):
    """Duplicate voice for polyphony."""
    return [copy.deepcopy(voice) for _ in range(number)]


class Synthesizer(Block):

    """Synthesizer base class."""

    def __init__(self):
        super().__init__(nInputs=0, nOutputs=1)
        self.inputs = [MessageInput(owner=self)]
        self.output.set_value(MONO_SILENCE)

    def play_note(self, *notes):
        """Play some note(s) directly."""
        for note in notes:
            self.process_note(note)

    @abc.abstractmethod
    def process_note(self, note):
        """Process single note."""
        raise NotImplementedError

    def update(self):
        for note in self.input.receive():
            self.process_note(note)


class MonophonicSynthesizer(Synthesizer):

    """Monophonic synthesizer with a single voice.

    TODO:
      - Glissando
    """

    def __init__(self, voice):
        super().__init__()
        self.voice = voice
        self.noteStack = []

    def get_note_to_play(self, note):
        """Get current note to play. Access to the note stack. Imitates the
        behavior of monophonic synthesizer. On a monophonic a new note overrules
        the previously played note(s). When the new note gets release, we fall
        back to the previously played note (if it is still on).
        Otherwise we release.

        TODO:
          - Implement different note priority schemes found on old, monophonic
            synthesizer. E.g.:
              - Newest note (currently implemented)
              - Highest pitch
              - Lowest pitch
        """
        if note.velocity > 0:  # Note on
            self.noteStack.append(note)
            return note

        # Remove notes with note.pitch from noteStack
        for oldNote in list(self.noteStack):
            if oldNote.pitch == note.pitch:
                self.noteStack.remove(oldNote)

        # Get previously played note
        if self.noteStack:
            latestNote = self.noteStack[-1]
        else:
            latestNote = note  # No note left on stack. Release (note.velocity = 0).

        return latestNote

    def process_note(self, note):
        note = self.get_note_to_play(note)
        self.voice.input.push(note)

    def update(self):
        super().update()
        samples = MONO_SILENCE
        if self.voice.active:
            self.voice.update()
            samples = self.voice.output.value

        self.output.set_value(samples)


class PolyphonicSynthesizer(Synthesizer):

    """Polyphonic synthesizer with multiple voices."""

    MAX_VOICES = 24

    def __init__(self, voice):
        super().__init__()
        self.voices = duplicate_voice(voice, self.MAX_VOICES)
        self.freeVoice = itertools.cycle(self.voices)

    def process_note(self, note):
        if note.velocity > 0:
            #print('Play new note', note)
            voice = next(self.freeVoice)
            voice.input.push(note)
        else:
            #print('Kill old note', note)
            for voice in self.voices:
                if voice.currentPitch == note.pitch:
                    voice.input.push(note)

    def update(self):
        super().update()
        samples = MONO_SILENCE.copy()
        for voice in self.voices:
            if voice.active:
                voice.update()
                samples += voice.output.value

        self.output.set_value(samples / self.MAX_VOICES)


class HiHat(Block):

    """White noise / exponential decay hi hat synthesizer."""

    def __init__(self, decay=.05, loopedNoise=False):
        super().__init__(nOutputs=1)
        self.inputs = [MessageInput(self)]
        if loopedNoise:
            noise = 2 * np.random.random(BUFFER_SIZE) - 1.
            self.noise_generator = lambda: noise
        else:
            self.noise_generator = lambda: 2 * np.random.random(BUFFER_SIZE) - 1.

        self.envelope = D(decay, mode='exp')

    def update(self):
        triggered = False
        for note in self.input.receive():
            self.envelope.input.push(note)

        self.envelope.update()
        env = self.envelope.output.get_value()
        noise = self.noise_generator()
        self.output.set_value(env * noise)


class Kick(Block):
    def __init__(self, frequency=40., decay=.8, intensity=2, pitchDecay=.3):
        super().__init__(nInputs=0, nOutputs=1)
        self.frequency = frequency
        self.decay = decay
        self.intensity = intensity
        self.pitchDecay = pitchDecay

        self.inputs = [MessageInput(self)]
        self.currentTime = 0.
        self.currentPhase = 0.


    def update(self):
        for note in self.input.receive():
            if note.pitch > 0 and note.velocity > 0:
                self.currentTime = 0.
                self.currentPhase = 0.

        frequency, _ = sample_pitch_decay(self.frequency, self.pitchDecay, self.intensity, self.currentTime)
        env, self.currentTime = sample_exponential_decay(self.decay, self.currentTime)
        signal, self.currentPhase = sample_wave(frequency, startPhase=self.currentPhase)
        self.output.set_value(env * signal)
