"""Klang Library."""
import os
import logging
import matplotlib  # Avoid a lot of DEBUG log messages from matplotlib before switching logging level.


__author__ = 'atheler'
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
logging.basicConfig(level=logging.DEBUG)
