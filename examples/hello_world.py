#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Klang hello world.

Output a A440 sine wave.
"""
from klang.audio.oscillators import Oscillator
from klang.klang import Dac, run_klang

run_klang(Oscillator(frequency=444.) | Dac(nChannels=1))
