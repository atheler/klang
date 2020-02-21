import time

import numpy as np
import pyaudio

from config import SAMPLING_RATE, ATTACK_RELEASE
from rhesuton.constants import TAU, REF_OCTAVE, DODE
from rhesuton.math import wrap
from rhesuton.temperaments import get_temperament_by_name


DT = 1. / SAMPLING_RATE
"""float: Sampling interval."""


CHAR_2_BASE_PITCH = {
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

PITCH_NAMES = [
    'C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B',
]
"""list: Pitch index -> Note name (str)."""

EQUAL_TEMPERAMENT = get_temperament_by_name('Equal')
"""Temperament: Equal temperament (for default)."""


def char_2_pitch(char):
    """Keyboard character -> frequency."""
    try:
        return CHAR_2_BASE_PITCH[char.lower()] + REF_OCTAVE * DODE
    except KeyError:
        raise ValueError('Invalid char %r' % char)


def pitch_2_name(pitch):
    """Pitch number -> note name."""
    return PITCH_NAMES[pitch % DODE]


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
        """Signal end of oscillator (fade-out envelope) when next sampled."""
        self.last = True

    def sample(self, nSamples):
        """Get the next `nSamples` from oscillator."""
        # Note that we sample one more for last phase / starting phase of next
        # sample cycle (self.currentPhase).
        t = DT * np.arange(nSamples + 1)
        phase = TAU * self.frequency * t + self.currentPhase
        signal = np.sin(phase[:-1])
        self.currentPhase = wrap(phase[-1])

        # Crude linear one-shot envelope
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
    def __init__(self, temperament=EQUAL_TEMPERAMENT):
        self.temperament = temperament

        self.running = False
        self.oscillators = {}

    def play_key_note(self, char, noteOn=True):
        """Play keyboard note. Note on or note off."""
        try:
            pitch = char_2_pitch(char)
        except ValueError:
            return

        frequency = self.temperament(pitch)
        msg = 'Note %s' % (pitch_2_name(pitch), )
        if noteOn:
            print(msg, 'on')
            osc = Oscillator(frequency)
            self.oscillators[char] = osc
        elif char in self.oscillators:
            print(msg, 'off')
            self.oscillators[char].terminate()

    def stream_callback(self, inData, frameCount, timeInfo, status):
        """Audio stream callback for pyaudio."""
        data = np.zeros(frameCount, dtype=np.float32)
        for char, osc in dict(self.oscillators).items():
            data += .1 * osc.sample(frameCount)
            if not osc.active:
                del self.oscillators[char]

        return data, pyaudio.paContinue

    def run(self):
        """Synthesizer main loop."""
        print('Starting synthesizer with temperament %s' % self.temperament)

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
            while self.running and stream.is_active():
                time.sleep(0.1)

        finally:
            stream.stop_stream()
            stream.close()
            pa.terminate()

    def start(self):
        """Start synthesizer."""
        self.running = True
        self.run()

    def stop(self):
        """Signal synthesizer shutdown."""
        self.running = False
