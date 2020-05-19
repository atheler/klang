"""Klang Library."""
import os
import logging
import matplotlib  # Avoid a lot of DEBUG log messages from matplotlib before switching logging level.


__author__ = 'atheler'
__version__ = '0.1.2'
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
logging.basicConfig(level=logging.DEBUG)
