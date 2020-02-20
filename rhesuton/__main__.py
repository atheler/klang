#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Had to run as root!"""
import threading

import pynput.keyboard

from config import TEMPERAMENT_NAME
from rhesuton.synthesizer import Synthesizer
from rhesuton.temperaments import get_temperament_by_name


def process_key_events(app):
    # Register keyboard events
    with pynput.keyboard.Listener(on_press=app.on_press, on_release=app.on_release) as listener:
        listener.join()


if __name__ == '__main__':
    temperament = get_temperament_by_name(TEMPERAMENT_NAME)
    app = Synthesizer(temperament)
    keyWorker = threading.Thread(target=process_key_events, args=(app, ))
    keyWorker.start()
    app.start()
