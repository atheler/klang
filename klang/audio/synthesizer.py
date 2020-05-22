"""Synthesizer audio blocks."""
import abc
import copy
import heapq
import itertools
import math

import numpy as np

from klang.audio.envelopes import D
from klang.audio.helpers import DT, MONO_SILENCE, T
from klang.audio.waves import sample_wave
from klang.block import Block
from klang.config import BUFFER_SIZE
from klang.connections import MessageInput
from klang.constants import PI


__all__ = ['MonophonicSynthesizer', 'PolyphonicSynthesizer', 'HiHat', 'Kick']


def sample_exponential_decay(decay, t0=0.):
    """Sample exponential curve decay.

    Args:
        decay (float): Decay time.

    Kwargs:
        t0 (float): Start time.

    Returns:
        tuple: Curve samples and new start time.
    """
    amp = math.exp(-PI / decay * t0)
    signal = amp * np.exp(-PI / decay * T)
    return signal, t0 + DT * BUFFER_SIZE


def sample_pitch_decay(frequency, decay, intensity, t0=0.):
    """Sample decaying pitch curve.

    Args:
        frequency (float): Start frequency.
        decay (float): Decay time.
        intensity (float): Amount of pitch decay.

    Kwargs:
        t0 (float): Start time.

    Returns:
        tuple: Curve samples and new start time.
    """
    env, t1 = sample_exponential_decay(decay, t0)
    pitch = frequency * (1. + intensity * env)
    return pitch, t1


def duplicate_voice(voice, number):
    """Duplicate voice for polyphony."""
    return [copy.deepcopy(voice, memo=None) for _ in range(number)]


class Synthesizer(Block):

    """Synthesizer base class."""

    def __init__(self):
        super().__init__(nOutputs=1)
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


class NoteScheduler:

    """Note scheduling for monophonic synthesizers. Manages the active note-ons.
    Notes get inserted-sorted according to chosen policy.
    """

    def __init__(self, policy='newest'):
        """Kwargs:
            policy (str): Note scheduling policy.
        """
        assert policy in {'newest', 'oldest', 'lowest', 'highest'}
        self.policy = policy
        self.counter = itertools.count()
        self.notes = list()
        heapq.heapify(self.notes)

    def get_key(self, note):
        """Note key function. Get key for note according to scheduling
        policy.
        """
        if self.policy == 'newest':
            key = next(self.counter)
        elif self.policy == 'oldest':
            key = -next(self.counter)
        elif self.policy == 'highest':
            key = note.pitch
        elif self.policy == 'lowest':
            key = -note.pitch

        return -key  # Min-heap -> Reverse key

    def add_note(self, note):
        """Add new note-on to note scheduler."""
        key = self.get_key(note)
        item = (key, note)
        heapq.heappush(self.notes, item)

    def remove_note(self, note):
        """Remove turned off note from note scheduler."""
        for item in self.notes:
            _, oldNote = item
            if oldNote.pitch == note.pitch:
                break
        else:  # If no break
            return

        # pylint: disable=undefined-loop-variable
        self.notes.remove(item)
        heapq.heapify(self.notes)

    def get_next_note(self, note):
        """Given a new note, get the current note which needs to be played."""
        if note.on:
            self.add_note(note)
        else:
            self.remove_note(note)

        if not self.notes:
            return note

        _, note = self.notes[0]
        return note


class MonophonicSynthesizer(Synthesizer):

    """Monophonic synthesizer with a single voice.

    TODO:
      - Glissando
    """

    def __init__(self, voice, policy='newest'):
        """Args:
            voice (Voice): Synthesizer voice.

        Kwargs:
            policy (str): Note scheduling policy.
        """
        super().__init__()
        self.voice = voice
        self.noteScheduler = NoteScheduler(policy)

    def process_note(self, note):
        note = self.noteScheduler.get_next_note(note)
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
    """int: Maximum number of voices."""

    def __init__(self, voice):
        """Args:
            voice (Voice): Synthesizer voice to use as a template for all the
                polyphonic voices.
        """
        super().__init__()
        self.voices = duplicate_voice(voice, self.MAX_VOICES)
        self.freeVoice = itertools.cycle(self.voices)

    def process_note(self, note):
        if note.on:
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
        """Kwargs:
            decay (float): Decay time.
            loopedNoise (bool): Loop noise / constant noise samples. Will be
                tonal.
        """
        super().__init__(nOutputs=1)
        self.inputs = [MessageInput(self)]
        if loopedNoise:
            noise = 2 * np.random.random(BUFFER_SIZE) - 1.
            self.noise_generator = lambda: noise
        else:
            self.noise_generator = lambda: 2 * np.random.random(BUFFER_SIZE) - 1.

        self.envelope = D(decay)

    def update(self):
        triggered = False
        for note in self.input.receive():
            self.envelope.input.push(note)

        self.envelope.update()
        env = self.envelope.output.get_value()
        noise = self.noise_generator()
        self.output.set_value(env * noise)


class Kick(Block):

    """Kick drum synthesizer."""

    def __init__(self, frequency=40., decay=.8, intensity=2, pitchDecay=.3):
        """Kwargs:
            frequency (float): Base frequency.
            decay (float): Kick drum decay time.
            intensity (float): Pitch decay intensity.
            pitchDecay (float): Pitch decay time.
        """
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
            if note.pitch > 0 and note.on:
                self.currentTime = 0.
                self.currentPhase = 0.

        frequency, _ = sample_pitch_decay(self.frequency, self.pitchDecay, self.intensity, self.currentTime)
        env, self.currentTime = sample_exponential_decay(self.decay, self.currentTime)
        signal, self.currentPhase = sample_wave(frequency, startPhase=self.currentPhase)
        self.output.set_value(env * signal)
