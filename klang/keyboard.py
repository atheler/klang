import collections

from pynput.keyboard import Listener, Key, KeyCode

from klang.blocks import Block
from klang.connections import MessageOutput
from klang.constants import REF_OCTAVE, DODE
from klang.math import clip
from klang.messages import Note
from klang.music.tunings import EQUAL_TEMPERAMENT


KEYS = []

SILENT = 0.
LOUDER = .1
QUIETER = -.1


class Keyboard(Block):
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
        self.on_event(key)

    def on_release(self, key):
        """On key release event handler with debouncing."""
        key.pressed = False
        if not self.keyState[key]:
            return

        self.keyState[key] = False
        self.on_event(key)

    def on_event(self, key):
        self.output.send(key)

    def start(self):
        self.keyWorker.start()

    def stop(self):
        self.keyWorker.stop()

    def update(self):
        pass

    def __str__(self):
        return '%s(%s)' % (
            self.__class__.__name__,
            'running' if self.keyWorker.isAlive() else 'not running'
        )


class MusicalKeyboard(Keyboard):

    """Musical keyboard.

    Main output outputs Notes. Octaves can be changed with the 'y' and 'x' keys,
    velocity can be changed via 'c', 'v'.  If others=True remaining key events
    will be send to secondary output.
    """

    CHAR_2_BASE_PITCH = {
        'a': 0, 'w': 1, 's': 2, 'e': 3, 'd': 4, 'f': 5, 't': 6, 'g': 7, 'z': 8,
        'h': 9, 'u': 10, 'j': 11, 'k': 12, 'o': 13, 'l': 14, 'p': 15,
    }
    """dict: Keyboard character (str) -> Pitch number."""

    def __init__(self, suppress=False, others=False):
        """Kwargs:
            others (bool): Send remaining key events to secondary message
                output.
        """
        super().__init__(suppress=suppress)
        self.others = others

        if others:
            self.outputs.append(MessageOutput(self))  # Secondary output

        self.octave = REF_OCTAVE
        self.velocity = 1.

    def on_event(self, key):
        KEYS.append(key)
        try:
            char = key.char
        except AttributeError:
            char = None

        if char in self.CHAR_2_BASE_PITCH:
            pitch = self.CHAR_2_BASE_PITCH[char] + self.octave * DODE
            velocity = self.velocity if key.pressed else SILENT
            note = Note(pitch, velocity)
            self.output.send(note)
            return

        if key.pressed:
            if char in {'y', 'x'}:
                if char == 'y':
                    fmt = 'One octave down to %d'
                    self.octave -= 1
                else:
                    fmt = 'One octave up to %d'
                    self.octave += 1

                print(fmt % self.octave)
                return

            elif char in {'c', 'v'}:
                if char == 'c':
                    fmt = 'Decrease velocity to %.1f'
                    vel = self.velocity + QUIETER
                else:
                    fmt = 'Increased velocity to %.1f'
                    vel = self.velocity + LOUDER

                self.velocity = clip(vel, .1, 1.)
                print(fmt % self.velocity)
                return

        if self.others:
            print('Other key', key)
            self.outputs[1].send(key)
