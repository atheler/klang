import collections
import time

import numpy as np
import pyaudio

from config import SAMPLING_RATE, ATTACK_RELEASE
from rhesuton.constants import TAU, REF_OCTAVE, DODE
from rhesuton.math import wrap
from rhesuton.temperaments import EQUAL_TEMPERAMENT


DT = 1. / SAMPLING_RATE
"""float: Sampling interval."""


KEY_2_PTICH = {
    'a': 0,
    'w': 1,
    's': 2,
    'e': 3,
    'd': 4,
    'f': 5,
    't': 6,
    'g': 7,
    'z': 8,
    'h': 9,
    'u': 10,
    'j': 11,
    'k': 12,
    'o': 13,
    'l': 14,
    'p': 15,
}
"""dict: Keyboard character (str) -> Pitch number."""


def key_2_pitch(char):
    """Keyboard character -> frequency."""
    try:
        return KEY_2_PTICH[char.lower()] + REF_OCTAVE * DODE
    except KeyError:
        raise ValueError('Invalid char %r' % char)


def create_envelope(attack, nSamples):
    """Create simple linear fade in envelope."""
    envelope = np.ones(nSamples)
    end = min(int(attack * SAMPLING_RATE), nSamples)
    envelope[:end] = np.linspace(0., 1., end)
    return envelope


class Oscillator:

    """Single Oscillator job.

    TODO:
      - Proper ADSR Envelope.
    """

    def __init__(self, frequency, amplitude=1.):
        self.frequency = frequency
        self.amplitude = amplitude

        self.currentPhase = 0.
        self.first = True
        self.last = False
        self.active = True

    def terminate(self):
        self.last = True

    def sample(self, nSamples):
        t = DT * np.arange(nSamples + 1)
        phase = TAU * self.frequency * t + self.currentPhase
        self.currentPhase = wrap(phase[-1])
        signal = np.sin(phase[:-1])

        if self.first:
            self.first = False
            fadeIn = create_envelope(ATTACK_RELEASE, nSamples)
            return fadeIn * signal

        if self.last:
            if self.active:
                self.active = False
                fadeOut = create_envelope(ATTACK_RELEASE, nSamples)[::-1]
                return fadeOut * signal

            else:
                return 0. * signal

        return signal


class Synthesizer:
    def __init__(self, temperament):
        self.temperament = temperament

        self.keyState = collections.defaultdict(bool)
        self.oscillators = {}

    def on_press(self, key):
        try:
            char = key.char
        except AttributeError:
            return

        if self.keyState[char]:
            # Debounce
            return

        self.keyState[char] = True
        self.process_key(char, down=True)

    def on_release(self, key):
        try:
            char = key.char
        except AttributeError:
            return

        if not self.keyState[char]:
            # Debounce
            return

        self.keyState[char] = False
        self.process_key(char, down=False)

    def process_key(self, char, down=True):
        try:
            pitch = key_2_pitch(char)
        except ValueError:
            return

        frequency = self.temperament(pitch)

        if down:
            # New note
            osc = Oscillator(frequency)
            self.oscillators[frequency] = osc
        elif frequency in self.oscillators:
            # Erase old note
            #del self.oscillators[frequency]
            self.oscillators[frequency].terminate()

    def stream_callback(self, inData, frameCount, timeInfo, status):
        data = np.zeros(frameCount, dtype=np.float32)
        for freq, osc in dict(self.oscillators).items():
            data += .1 * osc.sample(frameCount)
            if not osc.active:
                del self.oscillators[freq]

        return data, pyaudio.paContinue

    def run(self):
        print('Starting Synthesizer Engine with temperament %s' % self.temperament)

        # Example: Callback Mode Audio I/O from
        # https://people.csail.mit.edu/hubert/pyaudio/docs/
        pa = pyaudio.PyAudio()
        stream = pa.open(
            format=pyaudio.paFloat32,
            channels=1,
            rate=SAMPLING_RATE,
            output=True,
            stream_callback=self.stream_callback,
        )
        stream.start_stream()

        try:
            while stream.is_active():
                time.sleep(0.1)

        finally:
            stream.stop_stream()
            stream.close()
            pa.terminate()

    def start(self):
        self.run()
