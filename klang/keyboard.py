"""Keyboard input."""
import collections
import string

from pynput.keyboard import Listener

from klang.block import Block
from klang.connections import MessageOutput
from klang.constants import REF_OCTAVE, DODE
from klang.math import clip
from klang.messages import Note
from klang.music.tunings import EQUAL_TEMPERAMENT, TEMPERAMENTS


class Keyboard(Block):

    """Base version of keyboard input."""

    def __init__(self, suppress=False):
        super().__init__()
        self.outputs = [MessageOutput(self)]
        self.keyWorker = Listener(
            on_press=self.on_press,
            on_release=self.on_release,
            suppress=suppress,
        )
        self.keyState = collections.defaultdict(bool)

    def on_press(self, key):
        """On key press event handler with debouncing."""
        key.pressed = True
        if self.keyState[key]:
            return

        self.keyState[key] = True
        self.on_key_event(key)

    def on_release(self, key):
        """On key release event handler with debouncing."""
        key.pressed = False
        if not self.keyState[key]:
            return

        self.keyState[key] = False
        self.on_key_event(key)

    def on_key_event(self, key):
        """On key event. What to do on key event (pressed and released)."""
        self.output.send(key)

    def start(self):
        """Start Keyboard worker thread."""
        self.keyWorker.start()

    def stop(self):
        """Stop keyboard worker thread."""
        self.keyWorker.stop()

    def __str__(self):
        return '%s(%s)' % (
            self.__class__.__name__,
            'running' if self.keyWorker.isAlive() else 'not running'
        )


class MusicalKeyboard(Keyboard):

    """Musical QWERTZ keyboard.

    Main output outputs Notes. Octaves can be changed with the 'y' and 'x' keys,
    velocity can be changed via 'c', 'v'. Current tuning temperaments can be
    switched via the number keys. If others=True remaining key events will be
    send to a secondary output.

    TODO: Support for different keyboard layouts?
    """

    CHAR_2_BASE_PITCH = {
        'a': 0, 'w': 1, 's': 2, 'e': 3, 'd': 4, 'f': 5, 't': 6, 'g': 7, 'z': 8,
        'h': 9, 'u': 10, 'j': 11, 'k': 12, 'o': 13, 'l': 14, 'p': 15,
    }
    """dict: QWERTZ keyboard character (str) -> Pitch number."""

    SILENT = 0.
    """float: Silent velocity value."""

    LOUDER = .1
    """float: Louder increment."""

    QUIETER = -.1
    """float: Quieter decrement."""

    TEMPERAMENTS = list(TEMPERAMENTS.values())
    """list: Temperament values. Makes the first 10 temperament accessible."""

    def __init__(self, suppress=False, others=False,
                 defaultTemperament=EQUAL_TEMPERAMENT):
        """Kwargs:
            others (bool): Send remaining key events to secondary message
                output.
            defaultTemperament (Temperament): Default tuning temperament.
        """
        super().__init__(suppress=suppress)
        self.others = others

        if others:
            self.outputs.append(MessageOutput(self))  # Secondary output

        self.octave = REF_OCTAVE
        self.velocity = 1.
        self.temperament = defaultTemperament

    def play_note(self, char, noteOn=True):
        """Play music note (note-on and note-off)."""
        pitch = self.CHAR_2_BASE_PITCH[char] + self.octave * DODE
        frequency = self.temperament.pitch_2_frequency(pitch)
        velocity = self.velocity if noteOn else self.SILENT
        note = Note(pitch, velocity=velocity, frequency=frequency)
        self.output.send(note)

    def change_octave(self, char):
        """Change current octave up / down."""
        if char == 'y':
            fmt = 'One octave down to %d'
            self.octave -= 1
        else:
            fmt = 'One octave up to %d'
            self.octave += 1

        print(fmt % self.octave)

    def change_velocity(self, char):
        """Increase / decrease current velocity."""
        if char == 'c':
            fmt = 'Decrease velocity to %.1f'
            vel = self.velocity + self.QUIETER
        else:
            fmt = 'Increased velocity to %.1f'
            vel = self.velocity + self.LOUDER

        self.velocity = clip(vel, .1, 1.)
        print(fmt % self.velocity)

    def change_temperament(self, char):
        """Change to another tuning temperament."""
        try:
            nr = int(char)
        except ValueError:
            return

        if 0 <= nr < len(TEMPERAMENTS):
            self.temperament = TEMPERAMENTS[nr]
            print('Switched to %s' % self.temperament)

    def bypass_other_keys(self, key):
        """Relays remaining keys to outputs[1]."""
        print('Other key', key)
        self.outputs[1].send(key)

    def on_key_event(self, key):
        try:
            char = key.char
        except AttributeError:
            char = None

        if char in self.CHAR_2_BASE_PITCH:
            return self.play_note(char, noteOn=key.pressed)

        if key.pressed:
            if char in {'y', 'x'}:
                return self.change_octave(char)

            if char in {'c', 'v'}:
                return self.change_velocity(char)

            if char in set(string.digits):
                return self.change_temperament(char)

        if self.others:
            return self.bypass_other_keys(key)
