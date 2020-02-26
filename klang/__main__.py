#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Had to run as root!"""
import collections
import string

from pynput.keyboard import Listener, Key

from config import TEMPERAMENT_NAME
from klang.old_synthesizer import CHAR_2_BASE_PITCH, Synthesizer
from klang.temperaments import TEMPERAMENTS, get_temperament_by_name


DIGITS = set(string.digits)
"""set: String digits. We use this since '' in string.digits would return
true.
"""


class App:

    """Synthesizer application object. Handles keyboard listener (with
    debouncing), user input and thread managment.
    """

    def __init__(self, synthesizer):
        self.synthesizer = synthesizer

        self.keyWorker = Listener(
            on_press=self.on_press,
            on_release=self.on_release,
            suppress=True,
        )
        self.keyState = collections.defaultdict(bool)

    def do_stuff(self, key, down=True):
        """Relay debounced key events to functionality."""
        try:
            char = key.char
        except AttributeError:
            char = ''

        if key == Key.esc or char == '\x03':  # 'c' + ctrl (left)
            return self.stop()

        if char in CHAR_2_BASE_PITCH:
            return self.synthesizer.play_key_note(char.lower(), noteOn=down)

        if not down:
            return

        if char in DIGITS:
            # Switch temperament
            temps = list(TEMPERAMENTS.items())
            idx = int(char)
            if idx < len(temps):
                name, temperament = temps[idx]
                self.synthesizer.temperament = temperament
                print('Switched to %s temperament' % temperament)
        else:
            # TODO: Volumen? Octave?
            pass

    def on_press(self, key):
        """On key press event handler with debouncing."""
        if self.keyState[key]:
            return

        self.keyState[key] = True
        self.do_stuff(key, down=True)

    def on_release(self, key):
        """On key release event handler with debouncing."""
        if not self.keyState[key]:
            return

        self.keyState[key] = False
        self.do_stuff(key, down=False)

    def run(self):
        """Main loop."""
        self.keyWorker.start()
        self.synthesizer.start()

    def start(self):
        """Start application."""
        self.run()

    def stop(self):
        """Shutdown application."""
        self.synthesizer.stop()


if __name__ == '__main__':
    temperament = get_temperament_by_name(TEMPERAMENT_NAME)
    synthesizer = Synthesizer(temperament)
    app = App(synthesizer)
    app.start()
