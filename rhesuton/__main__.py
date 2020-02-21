#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Had to run as root!"""
import collections
import threading
import string

import pynput.keyboard

from config import TEMPERAMENT_NAME
from rhesuton.synthesizer import CHAR_2_BASE_PITCH, Synthesizer
from rhesuton.temperaments import TEMPERAMENTS, get_temperament_by_name


class App:

    """Synthesizer application object.

    Debounce key inputs.
    """

    def __init__(self, synthesizer):
        self.synthesizer = synthesizer
        self.keyState = collections.defaultdict(bool)

    def do_stuff(self, key, down=True):
        """Relay debounced key events to functionality."""
        try:
            char = key.char
        except AttributeError:
            return

        if char in CHAR_2_BASE_PITCH:
            self.synthesizer.play_key_note(char.lower(), noteOn=down)

        if not down:
            return

        if char in string.digits:
            # Switch temperament
            temps = list(TEMPERAMENTS.items())
            idx = int(char)
            if idx < len(temps):
                name, temperament = temps[idx]
                self.synthesizer.temperament = temperament

                print('Switched to %s temperament' % temperament)
        else:
            # TODO: Switch temperament? Volumen?
            pass

    def on_press(self, key):
        """On key press event handler with debouncing."""
        if self.keyState[key]:
            return

        self.keyState[key] = True
        print(key, 'pressed')

        self.do_stuff(key, down=True)

    def on_release(self, key):
        """On key release event handler with debouncing."""
        if not self.keyState[key]:
            return

        self.keyState[key] = False
        print(key, 'released')

        self.do_stuff(key, down=False)

    def process_key_events(self):
        """pynput main loop. Can be used as thread target function."""
        with pynput.keyboard.Listener(
                on_press=self.on_press,
                on_release=self.on_release) as listener:
            listener.join()

    def run(self):
        keyWorker = threading.Thread(target=self.process_key_events)
        keyWorker.start()
        self.synthesizer.start()

    def start(self):
        """Start application."""
        self.run()


if __name__ == '__main__':
    temperament = get_temperament_by_name(TEMPERAMENT_NAME)
    synthesizer = Synthesizer(temperament)
    app = App(synthesizer)
    app.start()
