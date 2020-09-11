"""Klang

Block based synthesis and music library.
"""
import logging


__author__ = 'atheler'
__version__ = '0.1.3'
logging.basicConfig(level=logging.DEBUG)


# Surpress parse loggers
for name in logging.root.manager.loggerDict:
    if 'parso' in name or 'matplotlib' in name:
        logging.getLogger(name).disabled = True
