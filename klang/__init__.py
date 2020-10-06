"""Klang

Block based synthesis and music library.
"""
import logging


__author__ = 'atheler'
__version__ = '0.2.1'
logging.basicConfig(level=logging.DEBUG)


# Surpress some other loggers
for name in logging.root.manager.loggerDict:
    if 'parso' in name or 'matplotlib' in name:
        logging.getLogger(name).disabled = True
